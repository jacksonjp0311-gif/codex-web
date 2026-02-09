#!/usr/bin/env python3
"""
Codex QIM v4.9 — Multi-Scale Insight Kernel Engine (mode='insight')

Role:
  • Load v4.9 autogen spec (from v4.8 Transcendence)
  • Build synthetic / AFM-style 4D field
  • Compute dphi, error geometry Ω, C_geo
  • Apply multi-scale kernels (1×,2×,4×,8× block-averages)
  • Measure cross-scale persistence + Ω curvature spectrum
  • Emit v4.9 state + ledger (insight mode)
  • Emit QIM v5.0 autogen spec (next evolution blueprint)

Codex Laws:
  • H7 = 0.70 (Coherence Threshold)
  • H16 = Insight / pattern geometry (C_geo)
  • H19 = Global dphi integration
  • ΔΦ Cusp Law v2.8 (λ = P/P_cr → 1⁻)
  • Error Geometry Layer: Ω = 1/(1+|ΔΦ|)
  • Harmonic Stability Law H31 (core:shell:void ≈ 1:9:10)
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


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def log(fp, msg: str):
    line = msg.encode("ascii", "replace").decode("ascii")
    print(line)
    if fp is not None:
        fp.write(line + "\n")
        fp.flush()


# ─────────────────────────────────────────────
# 1) LOAD SPEC + SYNTHETIC / AFM VOLUME
# ─────────────────────────────────────────────
def load_spec(spec_path: Path):
    if not spec_path.exists():
        return None
    try:
        data = json.loads(spec_path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


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
        (0.45, 0.45, 0.1),
        (-0.45, -0.30, 0.35),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-35.0 * Rp*Rp)

    vol = base + 0.6 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol


def load_or_synth_afm(input_dir: Path, resolution=(64, 64, 64)):
    # For now we always synthesize but count PNGs if present
    pngs = sorted(input_dir.glob("*.png"))
    used_synth = True
    vol = synthetic_volume(shape=resolution)
    return vol, used_synth, len(pngs)


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
        # Slightly sharper modulation than v4.8
        mod = (
            1.0
            + 0.30 * math.sin(theta)
            + 0.20 * np.cos(2.0 * theta + 3.0 * R)
            + 0.05 * np.sin(3.0 * theta + 4.0 * R)
        )
        V[t] = volume3d * mod

    return V


# ─────────────────────────────────────────────
# 3) dphi, ERROR GEOMETRY, TRIAD, HARMONICS
# ─────────────────────────────────────────────
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return dphi


def compute_error_geometry(dphi):
    vals = dphi.astype(np.float64)
    delta = vals - float(vals.mean())
    omega = 1.0 / (1.0 + np.abs(delta))
    omega_mean = float(omega.mean())
    omega_std = float(omega.std())
    curvature_proxy = float(np.mean(np.abs(omega - omega_mean)))
    return omega, {
        "omega_mean": omega_mean,
        "omega_std": omega_std,
        "curvature_proxy": curvature_proxy,
    }


def compute_metrics(V, dphi, omega_stats):
    E = safe_float(np.mean(np.abs(V)))
    I = safe_float(np.mean(dphi))
    dphi_global = I

    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C_eff = (E * I) / (1.0 + abs(dphi_global))

    # Geometric C weighted by error-geometry curvature smoothness
    curv = max(omega_stats.get("curvature_proxy", 0.0), 1e-6)
    C_geo = C_eff * (1.0 - min(curv, 1.0))

    return {
        "triad": {"E": E, "I": I, "C": C_eff, "C_geo": C_geo},
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
# 4) MULTI-SCALE KERNELS (BLOCK-AVERAGE PYRAMID)
# ─────────────────────────────────────────────
def block_reduce_4d(field, block_t, block_x, block_y, block_z):
    T, nx, ny, nz = field.shape
    T2 = T // block_t
    X2 = nx // block_x
    Y2 = ny // block_y
    Z2 = nz // block_z
    trimmed = field[:T2*block_t, :X2*block_x, :Y2*block_y, :Z2*block_z]
    reshaped = trimmed.reshape(
        T2, block_t,
        X2, block_x,
        Y2, block_y,
        Z2, block_z
    )
    return reshaped.mean(axis=(1,3,5,7))


def compute_multi_scale_insight(dphi, omega, scales=(1, 2, 4, 8)):
    """
    For each scale s, compute:
      • dphi_s: block-averaged |∇V| field
      • omega_s: block-averaged Ω field
      • active_fraction_s: fraction of voxels above median dphi_s
      • C_geo_s: proxy ~ <dphi_s> * <omega_s>
      • curvature_s: mean |omega_s - mean(omega_s)|
    Also compute cross-scale persistence:
      fraction of points that remain active from coarse→fine.
    """
    T, nx, ny, nz = dphi.shape
    results = {}
    active_masks = {}

    for s in scales:
        if s == 1:
            dphi_s = dphi.copy()
            omega_s = omega.copy()
        else:
            dphi_s = block_reduce_4d(dphi, s, s, s, s)
            omega_s = block_reduce_4d(omega, s, s, s, s)

        vals = dphi_s.flatten()
        median_val = float(np.median(vals))
        active = dphi_s >= median_val
        active_fraction = float(active.mean())

        omega_mean_s = float(omega_s.mean())
        curvature_s = float(np.mean(np.abs(omega_s - omega_mean_s)))
        C_geo_s = float(np.mean(dphi_s) * np.mean(omega_s))

        results[str(s)] = {
            "shape": list(dphi_s.shape),
            "active_fraction": active_fraction,
            "omega_mean": omega_mean_s,
            "curvature_proxy": curvature_s,
            "C_geo_scale": C_geo_s,
        }
        active_masks[str(s)] = active

    # Cross-scale persistence: from coarsest → finest
    scales_sorted = sorted(scales, reverse=True)
    base_mask = active_masks[str(scales_sorted[0])]
    for s in scales_sorted[1:]:
        # upsample coarse mask to match finer resolution by nearest neighbor
        coarse = base_mask
        target = active_masks[str(s)]
        factor_t = target.shape[0] // coarse.shape[0]
        factor_x = target.shape[1] // coarse.shape[1]
        factor_y = target.shape[2] // coarse.shape[2]
        factor_z = target.shape[3] // coarse.shape[3]
        up = np.repeat(
            np.repeat(
                np.repeat(
                    np.repeat(coarse, factor_t, axis=0),
                    factor_x, axis=1
                ),
                factor_y, axis=2
            ),
            factor_z, axis=3
        )
        base_mask = up & target

    persistence = float(base_mask.mean())

    # Aggregate coherence index: average of (1 - curvature_s) weighted by active_fraction
    num = 0.0
    den = 0.0
    for s_key, info in results.items():
        w = info["active_fraction"]
        num += w * (1.0 - min(info["curvature_proxy"], 1.0))
        den += w
    coherence_index = num / den if den > 0 else 0.0

    return results, persistence, coherence_index


# ─────────────────────────────────────────────
# 5) VISUALS
# ─────────────────────────────────────────────
def make_visuals(V, dphi, omega, out_dir: Path, prefix: str):
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
    plt.title("QIM v4.9 dphi central slice (insight)")
    plt.colorbar()
    p_central = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_central, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_central)

    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QIM v4.9 dphi max projection (t,z) [insight]")
    plt.colorbar()
    p_max = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_max, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_max)

    omega_max = omega.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QIM v4.9 Ω-field max projection (error geometry)")
    plt.colorbar()
    p_omega = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_omega, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_omega)

    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V|>")
    plt.title("QIM v4.9 resonance curve (insight)")
    p_curve = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_curve, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_curve)

    return paths


# ─────────────────────────────────────────────
# 6) SCAN PREVIOUS QIM v4.x LEDGERS
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
                    C = safe_float(obj.get("C_geo", obj.get("C", 0.0)))
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
# 7) STATE, LEDGER, AUTOGEN SPEC (v5.0)
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
                            omega_stats: dict,
                            multi_scale: dict,
                            persistence: float,
                            coherence_index: float,
                            visuals: dict,
                            global_summary: dict,
                            spec_info_in: dict,
                            spec_path_in: Path):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_9_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v4_9_ledger.jsonl"

    T, nx, ny, nz = V.shape
    triad = metrics.get("triad", {})

    state_obj = {
        "protocol": "CodexQIMMultiScaleInsight",
        "version": "4.9",
        "timestamp": now_utc_iso(),
        "mode": "insight",
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synth),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": triad,
            "H19_dphi_global": metrics.get("dphi_global", 0.0),
            "lambda_eff": metrics.get("lambda_eff", 0.0),
            "barrier_scale": metrics.get("barrier_scale", 0.0),
            "H7_alignment": None,  # optional, can be computed later if needed
            "harmonics": harmonics,
            "error_geometry": omega_stats,
            "multi_scale": multi_scale,
            "multi_scale_persistence": persistence,
            "multi_scale_coherence_index": coherence_index,
        },
        "codex": {
            "H_layers": {
                "H7": 0.70,
                "H16": "Insight / pattern geometry (C_geo weighting)",
                "H19": "Global dphi integration (4D field → C_effective)",
                "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr → 1-, ΔV ∝ (1-lambda)^{3/2} (EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|) defines deviation-weighted metric",
                "harmonic_stability": "Stable imaging fields exhibit core:shell:void ≈ 1:9:10",
            },
            "memory": {
                "node": "QIM",
                "baseline_version": "4.7.1",
                "previous_version": "4.8",
                "current_version": "4.9",
                "autogen_source_spec": str(spec_path_in.name),
            },
            "global_qim_v4_summary": global_summary,
        },
        "spec_info": spec_info_in or {},
        "visuals": visuals,
    }
    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "insight",
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
        "harmonics": harmonics,
        "error_geometry": omega_stats,
        "multi_scale_persistence": persistence,
        "multi_scale_coherence_index": coherence_index,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    # Next autogen spec: v5.0
    qim_root = root_dir / "codex" / "quantum_imaging"
    spec_out_path = qim_root / "engine" / "codex_qim_v5_0_autogen_spec.json"
    recommendation = {
        "recommended_resolution": [int(nx), int(ny), int(nz)],
        "recommended_T": int(T),
        "global_C_geo_mean": global_summary.get("C_mean", 0.0),
        "global_C_geo_max": global_summary.get("C_max", 0.0),
        "multi_scale_coherence_index": coherence_index,
        "multi_scale_persistence": persistence,
        "next_focus": "embed multi-scale kernels into coupled modules (Solar/QCX/ThirdEye) and tune insight kernels against real AFM data",
    }
    spec_obj = {
        "protocol": "QIMAutoGenSpec",
        "source_version": "4.9",
        "next_version": "5.0",
        "timestamp": now_utc_iso(),
        "current_metrics": metrics,
        "global_summary": global_summary,
        "error_geometry": omega_stats,
        "multi_scale": {
            "scales": multi_scale,
            "persistence": persistence,
            "coherence_index": coherence_index,
        },
        "recommendation": recommendation,
    }
    spec_out_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_out_path


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
    parser.add_argument("--spec_path", required=False)
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    input_dir = Path(args.input_afm_dir) if args.input_afm_dir else (root_dir / "codex" / "quantum_imaging" / "input_afm" / "v4_9")
    spec_path = Path(args.spec_path) if args.spec_path else (root_dir / "codex" / "quantum_imaging" / "engine" / "codex_qim_v4_9_autogen_spec.json")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v4_9_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QIM v4.9 — Multi-Scale Insight Kernel Engine starting (mode='insight')")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")
    log(log_fp, f"spec_path  : {spec_path}")

    spec_data = load_spec(spec_path)
    if spec_data is not None:
        rec = spec_data.get("recommendation", {})
        res = rec.get("recommended_resolution", [64, 64, 64])
        T_rec = int(rec.get("recommended_T", 40))
        log(log_fp, f"Loaded v4.9 spec recommendation: res={res}, T={T_rec}")
        resolution = (int(res[0]), int(res[1]), int(res[2]))
        T = T_rec
    else:
        resolution = (64, 64, 64)
        T = 40
        log(log_fp, "⚠ v4.9 spec not found or unreadable — using default resolution and T.")

    t0 = datetime.now(timezone.utc)

    try:
        vol3d, used_synth, png_count = load_or_synth_afm(input_dir, resolution=resolution)
        log(log_fp, f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, input_png_count={png_count}")

        V = build_4d_field(vol3d, T=T)
        log(log_fp, f"Built 4D field with shape={V.shape}")

        dphi = compute_dphi_4d(V)
        log(log_fp, "Computed dphi field over 4D volume.")

        omega, omega_stats = compute_error_geometry(dphi)
        log(log_fp, f"Error geometry stats: {omega_stats}")

        metrics = compute_metrics(V, dphi, omega_stats)
        harmonics = compute_harmonics(dphi)
        log(log_fp, f"Global triad: {metrics.get('triad', {})}")
        log(log_fp, f"H19 dphi_global: {metrics.get('dphi_global', 0.0)}")
        log(log_fp, f"Cusp lambda_eff: {metrics.get('lambda_eff', 0.0)}, barrier_scale: {metrics.get('barrier_scale', 0.0)}")
        log(log_fp, f"Harmonics: {harmonics}")

        multi_scale, persistence, coherence_index = compute_multi_scale_insight(
            dphi, omega, scales=(1, 2, 4, 8)
        )
        log(log_fp, f"Multi-scale insight metrics: persistence={persistence}, coherence_index={coherence_index}")
        log(log_fp, f"Multi-scale detail: {multi_scale}")

        visuals = make_visuals(V, dphi, omega, visuals_dir, "qim_v4_9_field")
        log(log_fp, f"Visuals written: {visuals}")

        qim_root = root_dir / "codex" / "quantum_imaging"
        global_summary = scan_previous_qim(qim_root)
        log(log_fp, f"Global QIM v4 summary: {global_summary}")

        spec_info_in = None
        if spec_data is not None:
            rec_in = spec_data.get("recommendation", {})
            spec_info_in = {
                "recommended_resolution": rec_in.get("recommended_resolution", [64, 64, 64]),
                "recommended_T": rec_in.get("recommended_T", 40),
                "global_C_mean": rec_in.get("global_C_mean", 0.0),
                "global_C_max": rec_in.get("global_C_max", 0.0),
                "next_focus": rec_in.get("next_focus", ""),
            }

        state_path, ledger_path, spec_out_path = write_state_ledger_spec(
            root_dir, state_dir, visuals_dir, ledger_dir,
            input_dir, used_synth, png_count,
            V, dphi,
            metrics, harmonics, omega_stats,
            multi_scale, persistence, coherence_index,
            visuals, global_summary,
            spec_info_in, spec_path
        )
        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v5.0 autogen spec → {spec_out_path}")

        t1 = datetime.now(timezone.utc)
        dt = (t1 - t0).total_seconds()
        log(log_fp, f"QIM v4.9 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        err = "QIM v4.9 encountered an error: " + repr(e)
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
