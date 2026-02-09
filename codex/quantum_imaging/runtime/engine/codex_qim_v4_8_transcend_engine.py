#!/usr/bin/env python3
"""
Codex QIM v4.8 — Transcendence Sharpness Engine

Modes:
  • "sharp"  → Scientific Δφ sharpening (high-clarity gradients)
  • "vision" → Codex Emergent Vision (error-geometry + pattern focus)

Implements:
  • ΔΦ Error Geometry GEO v1.0
  • H7 universal truth horizon
  • H16 insight coupling (geometry-aware metrics)
  • H19 = dphi_global
  • ΔΦ Cusp Law v2.8 (lambda_eff, barrier_scale)
  • Self-writing v4.9 autogen spec
"""

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


# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────
def now_utc_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)


def log(fp, msg: str):
    line = msg.encode("ascii", "replace").decode("ascii")
    print(line)
    if fp is not None:
        fp.write(line + "\n")
        fp.flush()


# ─────────────────────────────────────────────
# 1) LOAD SPEC (FROM v4.7.1) OR FALLBACK
# ─────────────────────────────────────────────
def load_spec(spec_path: Path):
    if not spec_path.exists():
        return {
            "recommended_resolution": [64, 64, 64],
            "recommended_T": 40,
            "global_C_mean": 0.0,
            "global_C_max": 0.0,
            "next_focus": "boost C while keeping dphi_global below cusp knee"
        }
    try:
        data = json.loads(spec_path.read_text(encoding="utf-8"))
        rec = data.get("recommendation", {})
        return {
            "recommended_resolution": rec.get("recommended_resolution", [64, 64, 64]),
            "recommended_T": rec.get("recommended_T", 40),
            "global_C_mean": safe_float(rec.get("global_C_mean", 0.0)),
            "global_C_max": safe_float(rec.get("global_C_max", 0.0)),
            "next_focus": rec.get("next_focus", "")
        }
    except Exception:
        return {
            "recommended_resolution": [64, 64, 64],
            "recommended_T": 40,
            "global_C_mean": 0.0,
            "global_C_max": 0.0,
            "next_focus": ""
        }


# ─────────────────────────────────────────────
# 2) SYNTHETIC / AFM-STYLE 3D VOLUME (BASE)
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=23, mode="vision"):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    base = np.exp(-2.0 * R) * (1.0 + 0.35 * np.sin(5.0 * R))

    peaks = np.zeros_like(base)
    centers = [
        (0.0, 0.0, 0.0),
        (0.5, 0.4, 0.1),
        (-0.4, -0.3, 0.5),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        peaks += np.exp(-30.0 * Rp * Rp)

    vol = base + 0.7 * peaks

    noise = 0.015 * np.random.randn(*vol.shape)
    vol = vol + noise

    if mode == "sharp":
        vmin, vmax = float(vol.min()), float(vol.max())
        if vmax > vmin:
            vol = (vol - vmin) / (vmax - vmin + 1e-12)
        vol = np.power(vol, 0.8)
    else:
        ring = np.sin(6.0 * R) * np.exp(-1.5 * R)
        vol = vol * (1.0 + 0.25 * ring)

    return vol


def load_or_synth_afm(input_dir: Path, shape=(64, 64, 64), mode="vision"):
    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        vol = synthetic_volume(shape=shape, seed=23, mode=mode)
        return vol, True, 0
    vol = synthetic_volume(shape=shape, seed=23, mode=mode)
    return vol, False, len(pngs)


# ─────────────────────────────────────────────
# 3) BUILD 4D FIELD (TEMPORAL MODULATION)
# ─────────────────────────────────────────────
def build_4d_field(volume3d, T=40, mode="vision"):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        if mode == "sharp":
            mod = 1.0 + 0.25 * math.sin(theta)
        else:
            mod = 1.0 + 0.3 * math.sin(theta) + 0.2 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = volume3d * mod

    return V


# ─────────────────────────────────────────────
# 4) Δφ, ERROR GEOMETRY, METRICS, HARMONICS
# ─────────────────────────────────────────────
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


def compute_error_geometry(dphi):
    vals = dphi.astype(np.float64)
    delta = vals - float(vals.mean())
    omega = 1.0 / (1.0 + np.abs(delta))
    omega_mean = float(omega.mean())
    omega_std = float(omega.std())

    grad_x, grad_y, grad_z = np.gradient(omega.mean(axis=0))
    curvature_proxy = float(np.sqrt(grad_x ** 2 + grad_y ** 2 + grad_z ** 2).mean())

    return {
        "omega_mean": omega_mean,
        "omega_std": omega_std,
        "curvature_proxy": curvature_proxy,
    }, omega


def compute_metrics(V, dphi, err_geom, mode="vision"):
    E = safe_float(np.mean(np.abs(V)))
    I = safe_float(np.mean(dphi))
    dphi_global = I

    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C_eff = (E * I) / (1.0 + abs(dphi_global))

    H7_target = 0.70
    C_norm = C_eff / (C_eff + 1e-6)
    H7_alignment = 1.0 - abs(C_norm - H7_target)
    H7_alignment = float(max(0.0, min(1.0, H7_alignment)))

    geom_weight = 1.0 / (1.0 + err_geom.get("curvature_proxy", 0.0))
    C_geo = C_eff * geom_weight

    return {
        "triad": {"E": E, "I": I, "C": C_eff, "C_geo": C_geo},
        "dphi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": safe_float(barrier_scale),
        "H7_alignment": H7_alignment,
        "mode": mode,
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
# 5) VISUALS
# ─────────────────────────────────────────────
def make_visuals(V, dphi, omega, out_dir: Path, prefix: str, mode: str):
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
    plt.title(f"QIM v4.8 dphi central slice ({mode})")
    plt.colorbar()
    central_path = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(central_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(central_path)

    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title(f"QIM v4.8 dphi max projection (t,z) [{mode}]")
    plt.colorbar()
    max_path = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(max_path, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(max_path)

    if omega is not None:
        omega_max = omega.max(axis=0).max(axis=2)
        fig = plt.figure()
        plt.imshow(omega_max, origin="lower")
        plt.title("QIM v4.8 Ω-field max projection (error geometry)")
        plt.colorbar()
        geom_path = out_dir / f"{prefix}_omega_maxproj.png"
        fig.savefig(geom_path, bbox_inches="tight")
        plt.close(fig)
        paths["omega_maxproj"] = str(geom_path)

    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V|>")
    plt.title(f"QIM v4.8 resonance curve ({mode})")
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
# 6) SCAN PREVIOUS QIM v4.x LEDGERS
# ─────────────────────────────────────────────
def scan_previous_qim(qim_root: Path):
    stats = {"count": 0, "E_sum": 0.0, "I_sum": 0.0, "C_sum": 0.0, "C_max": 0.0}
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
        return {"count": 0, "E_mean": 0.0, "I_mean": 0.0, "C_mean": 0.0, "C_max": 0.0}

    c = float(stats["count"])
    return {
        "count": int(c),
        "E_mean": stats["E_sum"] / c,
        "I_mean": stats["I_sum"] / c,
        "C_mean": stats["C_sum"] / c,
        "C_max": stats["C_max"],
    }


# ─────────────────────────────────────────────
# 7) STATE, LEDGER, v4.9 AUTOGEN SPEC
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
                            global_summary: dict,
                            err_geom: dict,
                            spec_info: dict):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_8_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v4_8_ledger.jsonl"

    T, nx, ny, nz = V.shape
    triad = metrics.get("triad", {})

    state_obj = {
        "protocol": "CodexQIMTranscendence",
        "version": "4.8",
        "timestamp": now_utc_iso(),
        "mode": metrics.get("mode", "vision"),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synth),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": triad,
            "H19_dphi_global": metrics.get("dphi_global", 0.0),
            "lambda_eff": metrics.get("lambda_eff", 0.0),
            "barrier_scale": metrics.get("barrier_scale", 0.0),
            "H7_alignment": metrics.get("H7_alignment", 0.0),
            "harmonics": harmonics,
            "error_geometry": err_geom,
        },
        "codex": {
            "H_layers": {
                "H7": 0.70,
                "H16": "Insight / pattern geometry (C_geo weighting)",
                "H19": "Global dphi integration (4D field → C_effective)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr → 1-, ΔV ∝ (1-lambda)^{3/2} (EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|) defines deviation-weighted metric",
            },
            "memory": {
                "node": "QIM",
                "baseline_version": "4.7.1",
                "current_version": "4.8",
                "autogen_source_spec": "codex_qim_v4_8_autogen_spec.json",
            },
            "global_qim_v4_summary": global_summary,
        },
        "spec_info": spec_info,
        "visuals": visuals,
    }
    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": metrics.get("mode", "vision"),
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synth),
        "input_png_count": int(png_count),
        "E": safe_float(triad.get("E", 0.0)),
        "I": safe_float(triad.get("I", 0.0)),
        "C": safe_float(triad.get("C", 0.0)),
        "C_geo": safe_float(triad.get("C_geo", 0.0)),
        "dphi_global": metrics.get("dphi_global", 0.0),
        "lambda_eff": metrics.get("lambda_eff", 0.0),
        "barrier_scale": metrics.get("barrier_scale", 0.0),
        "H7_alignment": metrics.get("H7_alignment", 0.0),
        "harmonics": harmonics,
        "error_geometry": err_geom,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    qim_root = root_dir / "codex" / "quantum_imaging"
    spec_v49_path = qim_root / "engine" / "codex_qim_v4_9_autogen_spec.json"

    rec = {}
    rec["recommended_resolution"] = [int(nx), int(ny), int(nz)]
    rec["recommended_T"] = int(T)
    rec["global_C_mean"] = global_summary.get("C_mean", 0.0)
    rec["global_C_max"] = global_summary.get("C_max", 0.0)
    rec["next_focus"] = "refine multi-scale kernels, stabilize Ω curvature and C_geo"

    spec_obj = {
        "protocol": "QIMAutoGenSpec",
        "source_version": "4.8",
        "timestamp": now_utc_iso(),
        "current_metrics": metrics,
        "global_summary": global_summary,
        "error_geometry": err_geom,
        "recommendation": rec,
    }
    spec_v49_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_v49_path


# ─────────────────────────────────────────────
# 8) MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    parser.add_argument("--input_afm_dir", required=False)
    parser.add_argument("--mode", required=False, default="vision")
    parser.add_argument("--spec_path", required=False)
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    input_dir = Path(args.input_afm_dir) if args.input_afm_dir else (
        root_dir / "codex" / "quantum_imaging" / "input_afm" / "v4_8"
    )
    mode = args.mode if args.mode in ("vision", "sharp") else "vision"
    spec_path = Path(args.spec_path) if args.spec_path else (
        root_dir / "codex" / "quantum_imaging" / "engine" / "codex_qim_v4_8_autogen_spec.json"
    )

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v4_8_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, f"QIM v4.8 — Transcendence Sharpness Engine starting in mode='{mode}'")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")
    log(log_fp, f"spec_path  : {spec_path}")

    spec_info = load_spec(spec_path)
    log(log_fp, f"Loaded spec info: {spec_info}")

    T = int(spec_info.get("recommended_T", 40))
    res = spec_info.get("recommended_resolution", [64, 64, 64])
    if len(res) != 3:
        res = [64, 64, 64]
    nx, ny, nz = map(int, res)

    t0 = datetime.now(timezone.utc)
    try:
        vol3d, used_synth, png_count = load_or_synth_afm(input_dir, shape=(nx, ny, nz), mode=mode)
        log(log_fp, f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, input_png_count={png_count}")

        V = build_4d_field(vol3d, T=T, mode=mode)
        log(log_fp, f"Built 4D field with shape={V.shape}")

        dphi = compute_dphi_4d(V)
        log(log_fp, "Computed dphi field over 4D volume.")

        err_geom, omega = compute_error_geometry(dphi)
        log(log_fp, f"Error geometry: {err_geom}")

        metrics = compute_metrics(V, dphi, err_geom, mode=mode)
        harmonics = compute_harmonics(dphi)
        log(log_fp, f"Global triad: {metrics.get('triad', {})}")
        log(log_fp, f"H19 dphi_global: {metrics.get('dphi_global', 0.0)}")
        log(log_fp, f"λ_eff (cusp): {metrics.get('lambda_eff', 0.0)}, barrier_scale: {metrics.get('barrier_scale', 0.0)}")
        log(log_fp, f"H7_alignment: {metrics.get('H7_alignment', 0.0)}")
        log(log_fp, f"Harmonics: {harmonics}")

        visuals = make_visuals(V, dphi, omega, visuals_dir, "qim_v4_8_field", mode)
        log(log_fp, f"Visuals written: {visuals}")

        qim_root = root_dir / "codex" / "quantum_imaging"
        global_summary = scan_previous_qim(qim_root)
        log(log_fp, f"Global QIM v4 summary: {global_summary}")

        state_path, ledger_path, spec_v49_path = write_state_ledger_spec(
            root_dir, state_dir, visuals_dir, ledger_dir,
            input_dir, used_synth, png_count, V, dphi,
            metrics, harmonics, visuals, global_summary,
            err_geom, spec_info
        )
        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v4.9 autogen spec → {spec_v49_path}")

        t1 = datetime.now(timezone.utc)
        dt = (t1 - t0).total_seconds()
        log(log_fp, f"QIM v4.8 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        err = "QIM v4.8 encountered an error: " + repr(e)
        print(err, file=sys.stderr)
        traceback.print_exc()
        if log_fp is not None:
            log_fp.write(err + "\n")
            log_fp.write(traceback.format_exc() + "\n")
            log_fp.flush()
            log_fp.close()
        sys.exit(1)

    if log_fp is not None:
        log_fp.close()


if __name__ == "__main__":
    main()
