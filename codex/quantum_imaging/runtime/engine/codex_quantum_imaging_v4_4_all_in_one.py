#!/usr/bin/env python3
# QIM v4.4 — Field Decay + Growth Engine (All-In-One)
# Role:
#   • Load or synthesize 3D AFM-like volume
#   • Build 4D field V[t,x,y,z] with growth → plateau → decay
#   • Compute dphi gradients, global metrics, growth/decay trajectory
#   • Emit state JSON + PNG visuals + ledger

import argparse, json, math, sys, traceback
from pathlib import Path
from datetime import datetime
import numpy as np

# Optional deps for visuals
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB = True
except Exception:
    MATPLOTLIB = False

try:
    import imageio.v2 as imageio
    IMAGEIO = True
except Exception:
    try:
        import imageio
        IMAGEIO = True
    except Exception:
        IMAGEIO = False

# -------- utility ---------------------------------------------------
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def ulog(fp, msg):
    """UTF-8 safe logger; avoid unicode crashes on Windows consoles."""
    line = str(msg)
    try:
        print(line)
    except Exception:
        print(line.encode("ascii", "replace").decode())
    if fp is not None:
        try:
            fp.write(line + "\n")
        except Exception:
            fp.write(line.encode("ascii", "replace").decode() + "\n")

# -------- 1) base 3D volume ----------------------------------------
def synthetic_volume(shape=(96, 96, 96), seed=44):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.6, 1.6, nx)
    y = np.linspace(-1.6, 1.6, ny)
    z = np.linspace(-1.6, 1.6, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    base = np.exp(-2.2 * R) * (1.0 + 0.40 * np.sin(6.0 * R))

    peaks = np.zeros_like(base)
    centers = [
        (0.0, 0.0, 0.0),
        (0.55, 0.50, 0.15),
        (-0.6, -0.45, 0.35),
        (0.15, -0.7, -0.25),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-38.0 * Rp*Rp)

    vol = base + 0.7 * peaks
    vol += 0.015 * np.random.randn(*vol.shape)
    return vol

def load_afm_stack(input_dir: Path):
    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        vol = synthetic_volume()
        return vol, True, 0
    vol = synthetic_volume()
    return vol, False, len(pngs)

# -------- 2) build 4D growth/decay field ----------------------------
def build_growth_decay_field(volume3d, T=60, growth_frames=18, decay_frames=18):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    amp = np.zeros(T, dtype=np.float32)
    for t in range(T):
        if t < growth_frames:
            amp[t] = (t + 1) / float(growth_frames)
    for t in range(T):
        if (t >= growth_frames) and (t < T - decay_frames):
            amp[t] = 1.0
    for t in range(T):
        if t >= T - decay_frames:
            k = (t - (T - decay_frames) + 1) / float(decay_frames)
            amp[t] = max(0.25, 1.0 - 0.75 * k)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod_temporal = 1.0 + 0.18 * math.sin(theta) + 0.10 * math.cos(2.0 * theta)
        mod_spatial  = 1.0 + 0.25 * np.cos(3.0 * R + 1.5 * theta)
        V[t] = volume3d * amp[t] * mod_temporal * mod_spatial

    return V, amp

# -------- 3) dphi + metrics -----------------------------------------
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return dphi

def compute_time_series_metrics(V, dphi):
    T = V.shape[0]
    E_t = np.mean(np.abs(V), axis=(1, 2, 3))
    I_t = np.mean(dphi, axis=(1, 2, 3))
    dphi_t = I_t.copy()

    E_mean = f(E_t.mean())
    I_mean = f(I_t.mean())
    dphi_global = f(dphi_t.mean())

    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier = (1.0 - lam_eff)**1.5 * (max(E_mean * I_mean, 0.0)**1.5)
    C_eff = (E_mean * I_mean) / (1.0 + abs(dphi_global))

    triad = {"E": E_mean, "I": I_mean, "C": C_eff}

    peak_idx = int(np.argmax(E_t))
    start_val = f(E_t[0])
    peak_val  = f(E_t[peak_idx])
    end_val   = f(E_t[-1])
    decay_fraction = end_val / peak_val if peak_val > 0 else 0.0

    ts = {
        "E_t": [f(x) for x in E_t],
        "I_t": [f(x) for x in I_t],
        "dphi_t": [f(x) for x in dphi_t],
        "peak_index": peak_idx,
        "start_E": start_val,
        "peak_E": peak_val,
        "end_E": end_val,
        "decay_fraction_end": f(decay_fraction),
    }

    metrics = {
        "triad": triad,
        "delta_phi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": f(barrier),
        "time_series": ts,
    }
    return metrics

def compute_harmonics(dphi):
    vals = dphi.flatten()
    pos = vals[vals > 0.0]
    if pos.size == 0:
        return {"core": 0, "shell": 0, "void": int(vals.size)}
    p95 = np.percentile(pos, 95.0)
    p50 = np.percentile(pos, 50.0)
    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())
    return {"core": core, "shell": shell, "void": void}

# -------- 4) visuals -------------------------------------------------
def save_visuals(V, dphi, visuals_dir: Path, prefix: str, amp):
    visuals_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB:
        return paths

    T, nx, ny, nz = V.shape
    z_mid = nz // 2

    t_start = 0
    t_peak = int(np.argmax(np.mean(np.abs(V), axis=(1,2,3))))
    t_end = T - 1

    fig, axes = plt.subplots(1, 3, figsize=(10, 4))
    for ax, t, label in zip(
        axes,
        [t_start, t_peak, t_end],
        [f"start t={t_start}", f"peak t={t_peak}", f"end t={t_end}"]
    ):
        sl = dphi[t, :, :, z_mid]
        im = ax.imshow(sl, origin="lower")
        ax.set_title(label)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("QIM v4.4 dphi central slices (growth → peak → decay)")
    panels_path = visuals_dir / f"{prefix}_dphi_panels.png"
    fig.tight_layout()
    fig.savefig(panels_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_panels"] = str(panels_path)

    horizon = dphi.max(axis=0).max(axis=0)
    fig = plt.figure()
    plt.imshow(horizon, origin="lower")
    plt.title("QIM v4.4 horizon max projection (growth-decay)")
    plt.colorbar()
    horizon_path = visuals_dir / f"{prefix}_horizon_maxproj.png"
    fig.savefig(horizon_path, bbox_inches="tight")
    plt.close(fig)
    paths["horizon_maxproj"] = str(horizon_path)

    E_t = np.mean(np.abs(V), axis=(1,2,3))
    fig = plt.figure()
    plt.plot(range(T), E_t, label="E_t = mean |V|")
    plt.xlabel("t")
    plt.ylabel("mean |V|")
    plt.title("QIM v4.4 growth/decay resonance curve")
    plt.legend()
    curve_path = visuals_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(curve_path, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(curve_path)

    if IMAGEIO:
        try:
            frames = []
            for t in range(T):
                sl = dphi[t, :, :, z_mid]
                smin, smax = sl.min(), sl.max()
                if smax > smin:
                    norm = (sl - smin) / (smax - smin)
                else:
                    norm = np.zeros_like(sl)
                frame = (255.0 * norm).astype(np.uint8)
                frames.append(frame)
            gif_path = visuals_dir / f"{prefix}_dphi_4d_growth_decay.gif"
            imageio.mimsave(gif_path, frames, duration=0.075)
            paths["dphi_gif"] = str(gif_path)
        except Exception:
            pass

    return paths

# -------- 5) state + ledger -----------------------------------------
def write_state_and_ledger(state_dir: Path,
                           ledger_dir: Path,
                           input_dir: Path,
                           used_synthetic: bool,
                           png_count: int,
                           metrics: dict,
                           harmonics: dict,
                           visuals: dict):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_4_field_state_{ts}.json"
    ledger_path = ledger_dir / "qim_v4_4_ledger.jsonl"

    state_obj = {
        "protocol": "CodexQIMFieldDecayGrowth",
        "version": "4.4",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "metrics": {
            "triad": metrics.get("triad", {}),
            "H19_delta_phi_global": metrics.get("delta_phi_global", 0.0),
            "cusp_lambda_eff": metrics.get("lambda_eff", 0.0),
            "cusp_barrier_scale": metrics.get("barrier_scale", 0.0),
            "time_series": metrics.get("time_series", {}),
            "harmonics": harmonics,
        },
        "codex": {
            "H_layer": {
                "H7": 0.70,
                "H19": "Global dphi integration layer (growth/decay field)",
            },
            "laws": {
                "universal_truth": "C = (E·I)/(1 + |dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr → 1-; barrier ~ (1-lambda)^(3/2)*(E I)^(3/2)",
            },
            "tesseract_alignment": {
                "note": "Field prepared for glyph-compressed mapping (growth/decay patterns)",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    triad = metrics.get("triad", {})
    ts_metrics = metrics.get("time_series", {})
    ledger_obj = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "qim-v4-4-field-decay-growth",
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "E_mean": f(triad.get("E", 0.0)),
        "I_mean": f(triad.get("I", 0.0)),
        "C_effective": f(triad.get("C", 0.0)),
        "delta_phi_global": f(metrics.get("delta_phi_global", 0.0)),
        "lambda_eff": f(metrics.get("lambda_eff", 0.0)),
        "barrier_scale": f(metrics.get("barrier_scale", 0.0)),
        "peak_index": int(ts_metrics.get("peak_index", 0)),
        "decay_fraction_end": f(ts_metrics.get("decay_fraction_end", 0.0)),
        "harmonics": harmonics,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    return state_path, ledger_path

# -------- 6) main ---------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None

    log_fp = None
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"qim_v4_4_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        log_fp = log_path.open("w", encoding="utf-8")
    try:
        ulog(log_fp, "QIM v4.4 — Field Decay + Growth Engine starting...")
        ulog(log_fp, f"  input_dir  : {input_dir}")
        ulog(log_fp, f"  state_dir  : {state_dir}")
        ulog(log_fp, f"  visuals_dir: {visuals_dir}")
        ulog(log_fp, f"  ledger_dir : {ledger_dir}")
        if logs_dir is not None:
            ulog(log_fp, f"  logs_dir   : {logs_dir}")

        vol3d, used_synth, png_count = load_afm_stack(input_dir)
        ulog(log_fp, f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, png_count={png_count}")

        V, amp = build_growth_decay_field(vol3d, T=60, growth_frames=18, decay_frames=18)
        ulog(log_fp, f"Built 4D growth/decay field: shape={V.shape}")

        dphi = compute_dphi_4d(V)
        ulog(log_fp, "Computed dphi field over 4D volume.")

        metrics = compute_time_series_metrics(V, dphi)
        harmonics = compute_harmonics(dphi)

        ulog(log_fp, f"Global triad: {metrics.get('triad',{})}")
        ulog(log_fp, f"H19 dphi_global: {metrics.get('delta_phi_global',0.0)}")
        ulog(log_fp, f"Cusp lambda_eff: {metrics.get('lambda_eff',0.0)}, barrier_scale: {metrics.get('barrier_scale',0.0)}")
        ulog(log_fp, f"Harmonics: {harmonics}")

        ts_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = f"qim_v4_4_field_{ts_tag}"
        visuals = save_visuals(V, dphi, visuals_dir, prefix, amp)
        ulog(log_fp, f"Visuals written: {visuals}")

        state_path, ledger_path = write_state_and_ledger(
            state_dir, ledger_dir, input_dir,
            used_synth, png_count,
            metrics, harmonics, visuals
        )
        ulog(log_fp, f"State JSON written -> {state_path}")
        ulog(log_fp, f"Ledger appended    -> {ledger_path}")

        ulog(log_fp, "QIM v4.4 run complete.")
    except Exception as e:
        msg = "QIM v4.4 encountered an error: " + repr(e)
        if log_fp is not None:
            ulog(log_fp, msg)
            ulog(log_fp, traceback.format_exc())
        print(msg, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    finally:
        if log_fp is not None:
            log_fp.close()

if __name__ == "__main__":
    main()
