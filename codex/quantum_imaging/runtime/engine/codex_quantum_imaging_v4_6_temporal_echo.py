#!/usr/bin/env python3
# QIM v4.6 — Temporal Echo Engine (All-In-One)
# Role:
#   • Load or synthesize 3D AFM-like volume
#   • Extend to 4D field V(t,x,y,z)
#   • Compute spatial dphi(t,x,y,z)
#   • Compute temporal echo metrics (neighbor + origin correlation)
#   • Emit state JSON, PNG visuals, ledger
#   • H19: global dphi       H20: temporal echo index

import argparse
import json
import math
import sys
import traceback
from pathlib import Path
from datetime import datetime

import numpy as np

# Optional deps for visuals
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

try:
    import imageio.v2 as imageio
    IMAGEIO_OK = True
except Exception:
    try:
        import imageio
        IMAGEIO_OK = True
    except Exception:
        IMAGEIO_OK = False

# ─────────────────────────────────────────────
# Utility: safe float and logging
# ─────────────────────────────────────────────
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def make_logger(log_file: Path | None):
    lf = None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        lf = log_file.open("a", encoding="utf-8")

    def log(msg: str):
        s = str(msg)
        try:
            print(s)
        except Exception:
            safe = s.encode("ascii", "replace").decode()
            print(safe)
        if lf is not None:
            try:
                lf.write(s + "\n")
                lf.flush()
            except Exception:
                safe = s.encode("ascii", "replace").decode()
                lf.write(safe + "\n")
                lf.flush()
    return log, lf

# ─────────────────────────────────────────────
# 1) LOAD OR SYNTHESIZE 3D AFM VOLUME
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=20):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    base = np.exp(-2.0 * R) * (1.0 + 0.35 * np.sin(5.0 * R))
    peaks = np.zeros_like(base)

    centers = [
        (0.0, 0.0, 0.0),
        (0.5, 0.4, -0.2),
        (-0.6, -0.3, 0.5)
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-30.0 * Rp*Rp)

    vol = base + 0.6 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol

def load_afm_stack(input_dir: Path, shape=(64, 64, 64)):
    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        vol = synthetic_volume(shape=shape)
        return vol, True, 0
    vol = synthetic_volume(shape=shape)
    return vol, False, len(pngs)

# ─────────────────────────────────────────────
# 2) 4D FIELD
# ─────────────────────────────────────────────
def build_4d_field(volume3d, T=40):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = 1.0 + 0.3 * math.sin(theta) + 0.2 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = volume3d * mod
    return V

# ─────────────────────────────────────────────
# 3) DPHI, TRIAD, H19, CUSP
# ─────────────────────────────────────────────
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return dphi

def compute_global_metrics(V, dphi):
    E = f(np.mean(np.abs(V)))
    I = f(np.mean(dphi))
    delta_phi_global = I

    lam_eff = min(0.99, delta_phi_global / (1.0 + delta_phi_global))
    barrier_scale = (1.0 - lam_eff)**1.5 * (max(E * I, 0.0)**1.5)
    C_eff = (E * I) / (1.0 + abs(delta_phi_global))

    triad = {"E": E, "I": I, "C": C_eff}
    return {
        "triad": triad,
        "delta_phi_global": delta_phi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": f(barrier_scale)
    }

def compute_harmonics(dphi):
    vals = dphi.flatten()
    positive = vals[vals > 0.0]
    if positive.size == 0:
        return {"core": 0, "shell": 0, "void": int(vals.size)}
    p95 = np.percentile(positive, 95.0)
    p50 = np.percentile(positive, 50.0)
    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())
    return {"core": core, "shell": shell, "void": void}

# ─────────────────────────────────────────────
# 4) TEMPORAL ECHO (H20)
# ─────────────────────────────────────────────
def temporal_echo_metrics(dphi):
    """
    H20: temporal echo layer.
    - neighbor_corr[t] = corr(dphi_t, dphi_{t-1})
    - origin_corr[t]   = corr(dphi_t, dphi_0)
    - echo index       = mean neighbor_corr over t>=1
    """
    T, nx, ny, nz = dphi.shape
    flat = dphi.reshape(T, -1)
    neighbor = []
    origin = []

    v0 = flat[0]
    v0_norm = np.linalg.norm(v0)
    if v0_norm == 0.0:
        v0_norm = 1.0

    for t in range(T):
        vt = flat[t]
        vt_norm = np.linalg.norm(vt)
        if vt_norm == 0.0:
            vt_norm = 1.0
        # origin correlation
        c0 = float(np.dot(vt, v0) / (vt_norm * v0_norm))
        origin.append(c0)

    for t in range(T):
        if t == 0:
            neighbor.append(1.0)
        else:
            v_prev = flat[t-1]
            n_prev = np.linalg.norm(v_prev)
            vt = flat[t]
            vt_norm = np.linalg.norm(vt)
            if n_prev == 0.0:
                n_prev = 1.0
            if vt_norm == 0.0:
                vt_norm = 1.0
            c = float(np.dot(vt, v_prev) / (n_prev * vt_norm))
            neighbor.append(c)

    neighbor = np.array(neighbor, dtype=float)
    origin = np.array(origin, dtype=float)

    echo_index = float(neighbor[1:].mean()) if neighbor.size > 1 else float(neighbor.mean())
    origin_mean = float(origin.mean())

    return {
        "neighbor_corr": neighbor.tolist(),
        "origin_corr": origin.tolist(),
        "echo_index": echo_index,
        "origin_mean_corr": origin_mean
    }

# ─────────────────────────────────────────────
# 5) VISUALS
# ─────────────────────────────────────────────
def save_visuals(V, dphi, echo_info: dict, visuals_dir: Path, prefix: str):
    visuals_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V.shape
    z_mid = nz // 2

    # Echo curves
    neighbor = np.array(echo_info.get("neighbor_corr", []), dtype=float)
    origin = np.array(echo_info.get("origin_corr", []), dtype=float)

    fig = plt.figure()
    plt.plot(range(T), neighbor, label="neighbor")
    plt.plot(range(T), origin, label="origin", linestyle="--")
    plt.xlabel("t (frame)")
    plt.ylabel("correlation")
    plt.title("QIM v4.6 Temporal Echo Correlation")
    plt.legend()
    echo_curve_path = visuals_dir / f"{prefix}_echo_curve.png"
    fig.savefig(echo_curve_path, bbox_inches="tight")
    plt.close(fig)
    paths["echo_curve"] = str(echo_curve_path)

    # Three-time-panel dphi slices
    t0 = 0
    t_mid = T // 2
    t_last = T - 1

    fig, axes = plt.subplots(1, 3, figsize=(9, 3))
    times = [t0, t_mid, t_last]
    titles = ["t=0", f"t={t_mid}", f"t={t_last}"]
    for ax, tt, title in zip(axes, times, titles):
        sl = dphi[tt, :, :, z_mid]
        im = ax.imshow(sl, origin="lower")
        ax.set_title(title)
        ax.axis("off")
    fig.suptitle("QIM v4.6 dphi central slice (temporal panels)")
    fig.tight_layout()
    panels_path = visuals_dir / f"{prefix}_dphi_panels.png"
    fig.savefig(panels_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_panels"] = str(panels_path)

    # Echo heatmap: mean over x,y for each t,z
    T, nx, ny, nz = dphi.shape
    heat = dphi.mean(axis=1).mean(axis=1)  # shape (T, nz)
    fig = plt.figure()
    plt.imshow(heat, aspect="auto", origin="lower")
    plt.xlabel("z index")
    plt.ylabel("t (frame)")
    plt.title("QIM v4.6 Echo Heatmap (mean dphi over x,y)")
    plt.colorbar()
    heatmap_path = visuals_dir / f"{prefix}_echo_heatmap.png"
    fig.savefig(heatmap_path, bbox_inches="tight")
    plt.close(fig)
    paths["echo_heatmap"] = str(heatmap_path)

    # Optional GIF of central slice
    if IMAGEIO_OK:
        frames = []
        for t in range(T):
            sl = dphi[t, :, :, z_mid]
            sl_min, sl_max = sl.min(), sl.max()
            if sl_max > sl_min:
                norm = (sl - sl_min) / (sl_max - sl_min)
            else:
                norm = np.zeros_like(sl)
            frame = (255.0 * norm).astype(np.uint8)
            frames.append(frame)
        gif_path = visuals_dir / f"{prefix}_dphi_temporal.gif"
        try:
            imageio.mimsave(gif_path, frames, duration=0.08)
            paths["dphi_temporal_gif"] = str(gif_path)
        except Exception:
            pass

    return paths

# ─────────────────────────────────────────────
# 6) STATE + LEDGER
# ─────────────────────────────────────────────
def write_state_and_ledger(state_dir: Path,
                           ledger_dir: Path,
                           input_dir: Path,
                           used_synthetic: bool,
                           png_count: int,
                           V, dphi,
                           metrics: dict,
                           harmonics: dict,
                           echo_info: dict,
                           visuals: dict):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_6_temporal_echo_state_{ts}.json"
    ledger_path = ledger_dir / "qim_v4_6_ledger.jsonl"

    T, nx, ny, nz = V.shape
    triad = metrics.get("triad", {})

    state_obj = {
        "protocol": "CodexQIMTemporalEcho",
        "version": "4.6",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": triad,
            "H19_delta_phi_global": metrics.get("delta_phi_global", 0.0),
            "cusp_lambda_eff": metrics.get("lambda_eff", 0.0),
            "cusp_barrier_scale": metrics.get("barrier_scale", 0.0),
            "harmonics": harmonics
        },
        "temporal_echo": {
            "H20_temporal_echo_index": echo_info.get("echo_index", 0.0),
            "origin_mean_corr": echo_info.get("origin_mean_corr", 0.0),
            "neighbor_corr": echo_info.get("neighbor_corr", []),
            "origin_corr": echo_info.get("origin_corr", [])
        },
        "codex": {
            "H_layer": {
                "H7": 0.70,
                "H19": "Global dphi integration layer",
                "H20": "Temporal echo / memory layer"
            },
            "laws": {
                "universal_truth": "C = (E·I)/(1 + |ΔΦ_global|)",
                "cusp_v2_8": "λ = P/P_cr → 1⁻; ΔV ∝ (1-λ)^{3/2} (EI)^{3/2}"
            }
        },
        "visuals": visuals
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "qim-v4-6-temporal-echo",
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "E": f(triad.get("E", 0.0)),
        "I": f(triad.get("I", 0.0)),
        "C_effective": f(triad.get("C", 0.0)),
        "delta_phi_global": f(metrics.get("delta_phi_global", 0.0)),
        "lambda_eff": f(metrics.get("lambda_eff", 0.0)),
        "barrier_scale": f(metrics.get("barrier_scale", 0.0)),
        "H20_temporal_echo_index": f(echo_info.get("echo_index", 0.0)),
        "origin_mean_corr": f(echo_info.get("origin_mean_corr", 0.0))
    }

    with ledger_path.open("a", encoding="utf-8") as f_ledger:
        f_ledger.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    return state_path, ledger_path

# ─────────────────────────────────────────────
# 7) MAIN
# ─────────────────────────────────────────────
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

    log_file = None
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"qim_v4_6_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"

    log, lf = make_logger(log_file)

    t0 = datetime.utcnow()
    log("QIM v4.6 — Temporal Echo Engine starting...")
    log(f"  input_dir  : {input_dir}")
    log(f"  state_dir  : {state_dir}")
    log(f"  visuals_dir: {visuals_dir}")
    log(f"  ledger_dir : {ledger_dir}")
    if log_file is not None:
        log(f"  log_file   : {log_file}")

    try:
        vol3d, used_synth, png_count = load_afm_stack(input_dir)
        log(f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, input_png_count={png_count}")

        V = build_4d_field(vol3d, T=40)
        log(f"Built 4D field with shape={V.shape}")

        dphi = compute_dphi_4d(V)
        log("Computed dphi field over 4D volume.")

        metrics = compute_global_metrics(V, dphi)
        harmonics = compute_harmonics(dphi)
        log(f"Global triad: {metrics.get('triad', {})}")
        log(f"H19 dphi_global: {metrics.get('delta_phi_global', 0.0)}")
        log(f"Cusp lambda_eff: {metrics.get('lambda_eff', 0.0)}, barrier_scale: {metrics.get('barrier_scale', 0.0)}")
        log(f"Harmonics: {harmonics}")

        echo_info = temporal_echo_metrics(dphi)
        log(f"H20 temporal echo index: {echo_info.get('echo_index', 0.0)}")
        log(f"H20 origin mean corr   : {echo_info.get('origin_mean_corr', 0.0)}")

        ts_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = f"qim_v4_6_temporal_{ts_tag}"
        visuals = save_visuals(V, dphi, echo_info, visuals_dir, prefix)
        log(f"Visuals written: {visuals}")

        state_path, ledger_path = write_state_and_ledger(
            state_dir, ledger_dir, input_dir,
            used_synth, png_count,
            V, dphi,
            metrics, harmonics,
            echo_info,
            visuals
        )
        log(f"State JSON written -> {state_path}")
        log(f"Ledger appended    -> {ledger_path}")

        t1 = datetime.utcnow()
        dt = (t1 - t0).total_seconds()
        log(f"QIM v4.6 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        msg = "QIM v4.6 encountered an error: " + repr(e)
        print(msg, file=sys.stderr)
        traceback.print_exc()
        if lf is not None:
            lf.write(msg + "\n")
            lf.write(traceback.format_exc() + "\n")
            lf.close()
        sys.exit(1)

    if lf is not None:
        lf.close()

if __name__ == "__main__":
    main()
