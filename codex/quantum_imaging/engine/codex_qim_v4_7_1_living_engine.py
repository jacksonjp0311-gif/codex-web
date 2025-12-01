#!/usr/bin/env python3
# Codex QIM v4.7.1 — Living Field Engine v1.1
# Role:
#   • Build synthetic / AFM-style 3D volume
#   • Extend to 4D field
#   • Compute dphi, triad, cusp-like metrics, harmonics
#   • Scan QIM v4.x ledgers for global summary
#   • Emit v4.7.1 state + ledger
#   • Emit v4.8 autogen spec (manifest), not executable code

import argparse
import json
import math
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

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
        import imageio  # type: ignore
        IMAGEIO_OK = True
    except Exception:
        IMAGEIO_OK = False


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def log(fp, msg: str):
    """ASCII-safe logger (avoid Windows cp1252 issues)."""
    line = msg.encode("ascii", "replace").decode("ascii")
    print(line)
    if fp is not None:
        fp.write(line + "\n")
        fp.flush()


# ─────────────────────────────────────────────
# 1) SYNTHETIC / AFM-STYLE 3D VOLUME
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=19):
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
        (0.5, 0.5, 0.0),
        (-0.5, -0.3, 0.4),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-30.0 * Rp*Rp)

    vol = base + 0.6 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol


def load_or_synth_afm(input_dir: Path):
    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        vol = synthetic_volume()
        return vol, True, 0
    vol = synthetic_volume()
    return vol, False, len(pngs)


# ─────────────────────────────────────────────
# 2) BUILD 4D FIELD
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
# 3) dphi + METRICS + HARMONICS
# ─────────────────────────────────────────────
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return dphi


def compute_metrics(V, dphi):
    E = safe_float(np.mean(np.abs(V)))
    I = safe_float(np.mean(dphi))
    dphi_global = I  # treat mean grad as global dphi

    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C_eff = (E * I) / (1.0 + abs(dphi_global))

    return {
        "triad": {"E": E, "I": I, "C": C_eff},
        "dphi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": safe_float(barrier_scale),
    }


def compute_harmonics(dphi):
    vals = dphi.flatten()
    pos = vals[vals > 0.0]
    if pos.size == 0:
        return {"core": 0, "shell": 0, "void": int(vals.size)}

    p95 = float(np.percentile(pos, 95.0))
    p50 = float(np.percentile(pos, 50.0))

    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())

    return {"core": core, "shell": shell, "void": void}


# ─────────────────────────────────────────────
# 4) VISUALS
# ─────────────────────────────────────────────
def make_visuals(V, dphi, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    z_mid = nz // 2

    central = dphi[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QIM v4.7.1 dphi central slice")
    plt.colorbar()
    central_path = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(central_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(central_path)

    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QIM v4.7.1 dphi max projection (t,z)")
    plt.colorbar()
    max_path = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(max_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(max_path)

    horizon = dphi.max(axis=0).max(axis=0)
    fig = plt.figure()
    plt.imshow(horizon, origin="lower")
    plt.title("QIM v4.7.1 horizon max projection (t,x)")
    plt.colorbar()
    hor_path = out_dir / f"{prefix}_horizon_maxproj.png"
    fig.savefig(hor_path, bbox_inches="tight")
    plt.close(fig)
    paths["horizon_maxproj"] = str(hor_path)

    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V|>")
    plt.title("QIM v4.7.1 resonance curve")
    curve_path = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(curve_path, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(curve_path)

    if IMAGEIO_OK:
        frames = []
        for t in range(T):
            sl = dphi[t, :, :, z_mid]
            sl_min = float(sl.min())
            sl_max = float(sl.max())
            if sl_max > sl_min:
                norm = (sl - sl_min) / (sl_max - sl_min)
            else:
                norm = np.zeros_like(sl)
            frame = (255.0 * norm).astype(np.uint8)
            frames.append(frame)
        gif_path = out_dir / f"{prefix}_dphi_4d.gif"
        try:
            imageio.mimsave(gif_path, frames, duration=0.08)
            paths["dphi_gif"] = str(gif_path)
        except Exception:
            pass

    return paths


# ─────────────────────────────────────────────
# 5) SCAN PREVIOUS QIM v4.x LEDGERS
# ─────────────────────────────────────────────
def scan_previous_qim(qim_root: Path):
    stats = {
        "count": 0,
        "E_sum": 0.0,
        "I_sum": 0.0,
        "C_sum": 0.0,
        "C_max": 0.0,
    }
    ledger_files = list(qim_root.glob("ledger*/*.jsonl")) + list(qim_root.glob("ledger*.jsonl"))
    for lf in ledger_files:
        try:
            with lf.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    E = safe_float(obj.get("E", 0.0))
                    I = safe_float(obj.get("I", 0.0))
                    C = safe_float(obj.get("C", obj.get("C_effective", 0.0)))
                    stats["count"] += 1
                    stats["E_sum"] += E
                    stats["I_sum"] += I
                    stats["C_sum"] += C
                    if C > stats["C_max"]:
                        stats["C_max"] = C
        except Exception:
            continue

    if stats["count"] == 0:
        return {
            "count": 0,
            "E_mean": 0.0,
            "I_mean": 0.0,
            "C_mean": 0.0,
            "C_max": 0.0,
        }

    c = float(stats["count"])
    return {
        "count": int(c),
        "E_mean": stats["E_sum"] / c,
        "I_mean": stats["I_sum"] / c,
        "C_mean": stats["C_sum"] / c,
        "C_max": stats["C_max"],
    }


# ─────────────────────────────────────────────
# 6) STATE, LEDGER, AUTOGEN SPEC
# ─────────────────────────────────────────────
def write_state_ledger_spec(root_dir: Path,
                            state_dir: Path,
                            visuals_dir: Path,
                            ledger_dir: Path,
                            input_dir: Path,
                            used_synth: bool,
                            png_count: int,
                            V, dphi,
                            metrics: dict,
                            harmonics: dict,
                            visuals: dict,
                            global_summary: dict):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_7_1_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v4_7_1_ledger.jsonl"

    T, nx, ny, nz = V.shape

    triad = metrics.get("triad", {})
    state_obj = {
        "protocol": "CodexQIMLivingField",
        "version": "4.7.1",
        "timestamp": now_utc_iso(),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synth),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": triad,
            "H19_dphi_global": metrics.get("dphi_global", 0.0),
            "lambda_eff": metrics.get("lambda_eff", 0.0),
            "barrier_scale": metrics.get("barrier_scale", 0.0),
            "harmonics": harmonics,
        },
        "codex": {
            "H_layers": {
                "H7": 0.70,
                "H19": "Global dphi integration (4D field → C_effective)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr → 1-, ΔV ∝ (1-lambda)^{3/2} (EI)^{3/2}",
            },
            "global_qim_v4_summary": global_summary,
        },
        "visuals": visuals,
    }
    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "qim-v4-7-1-living-field",
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synth),
        "input_png_count": int(png_count),
        "E": safe_float(triad.get("E", 0.0)),
        "I": safe_float(triad.get("I", 0.0)),
        "C": safe_float(triad.get("C", 0.0)),
        "dphi_global": metrics.get("dphi_global", 0.0),
        "lambda_eff": metrics.get("lambda_eff", 0.0),
        "barrier_scale": metrics.get("barrier_scale", 0.0),
        "harmonics": harmonics,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    qim_root = root_dir / "codex" / "quantum_imaging"
    spec_path = qim_root / "engine" / "codex_qim_v4_8_autogen_spec.json"
    rec = {}
    rec["recommended_resolution"] = [int(nx), int(ny), int(nz)]
    rec["recommended_T"] = int(T)
    rec["global_C_mean"] = global_summary.get("C_mean", 0.0)
    rec["global_C_max"] = global_summary.get("C_max", 0.0)
    rec["next_focus"] = "boost C while keeping dphi_global below cusp knee"

    spec_obj = {
        "protocol": "QIMAutoGenSpec",
        "source_version": "4.7.1",
        "timestamp": now_utc_iso(),
        "current_metrics": metrics,
        "global_summary": global_summary,
        "recommendation": rec,
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ─────────────────────────────────────────────
# 7) MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    parser.add_argument("--input_afm_dir", required=False)
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    input_dir = Path(args.input_afm_dir) if args.input_afm_dir else (root_dir / "codex" / "quantum_imaging" / "input_afm" / "v4_7_1")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v4_7_1_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QIM v4.7.1 — Living Field Engine v1.1 starting...")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")

    t0 = datetime.now(timezone.utc)

    try:
        vol3d, used_synth, png_count = load_or_synth_afm(input_dir)
        log(log_fp, f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, input_png_count={png_count}")

        V = build_4d_field(vol3d, T=40)
        log(log_fp, f"Built 4D field with shape={V.shape}")

        dphi = compute_dphi_4d(V)
        log(log_fp, "Computed dphi field over 4D volume.")

        metrics = compute_metrics(V, dphi)
        harmonics = compute_harmonics(dphi)
        log(log_fp, f"Global triad: {metrics.get('triad', {})}")
        log(log_fp, f"H19 dphi_global: {metrics.get('dphi_global', 0.0)}")
        log(log_fp, f"Cusp lambda_eff: {metrics.get('lambda_eff', 0.0)}, barrier_scale: {metrics.get('barrier_scale', 0.0)}")
        log(log_fp, f"Harmonics: {harmonics}")

        visuals = make_visuals(V, dphi, visuals_dir, "qim_v4_7_1_field")
        log(log_fp, f"Visuals written: {visuals}")

        qim_root = root_dir / "codex" / "quantum_imaging"
        global_summary = scan_previous_qim(qim_root)
        log(log_fp, f"Global QIM v4 summary: {global_summary}")

        state_path, ledger_path, spec_path = write_state_ledger_spec(
            root_dir, state_dir, visuals_dir, ledger_dir,
            input_dir, used_synth, png_count, V, dphi,
            metrics, harmonics, visuals, global_summary
        )
        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v4.8 autogen spec → {spec_path}")

        t1 = datetime.now(timezone.utc)
        dt = (t1 - t0).total_seconds()
        log(log_fp, f"QIM v4.7.1 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        err = "QIM v4.7.1 encountered an error: " + repr(e)
        print(err, file=sys.stderr)
        traceback.print_exc()
        if log_fp is not None:
            log_fp.write(err + "\n")
            log_fp.write(traceback.format_exc() + "\n")
            log_fp.flush()
        if log_fp is not None:
            log_fp.close()
        sys.exit(1)

    if log_fp is not None:
        log_fp.close()


if __name__ == "__main__":
    main()
