#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QCX v10.1 — CRYSTALLINE FUSION ENGINE (MULTI-SCALE STACK)   ║
# ║  Atomic Δφ kernel fused with QIM/Solar/AFM companion fields  ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
import math
import sys
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False


# ─────────────────────────────────────────────────────────────
# 0. SMALL UTILITIES
# ─────────────────────────────────────────────────────────────

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_f(x, default=0.0) -> float:
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


@dataclass
class ChannelMetrics:
    name: str
    E: float
    I: float
    C: float
    dphi_global: float
    lambda_eff: float
    barrier_scale: float
    omega_mean: float
    omega_std: float
    curvature_proxy: float
    persistence: float
    core: int
    shell: int
    void: int
    weight_S: float


# ─────────────────────────────────────────────────────────────
# 1. SYNTHETIC ATOMIC CRYSTAL + 4D FIELDS
# ─────────────────────────────────────────────────────────────

def synthetic_crystal(shape=(64, 64, 64), seed=3101):
    """
    Build a synthetic "quantum crystal" field:
      • radial shells (atomic-like orbitals)
      • cubic lattice modulation (crystal sites)
      • small anisotropic term to break symmetry
    """
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    # Atomic-like shells
    shells = np.exp(-2.5 * R) * (1.0 + 0.6 * np.cos(5.0 * R))

    # Simple cubic lattice modulation
    k = 3.0
    lattice = np.cos(k * X) * np.cos(k * Y) * np.cos(k * Z)

    # Slight anisotropic term
    anis = 0.25 * (np.sin(2.0 * X) + np.sin(2.0 * Y))

    base = shells * (1.0 + 0.4 * lattice) + anis
    base += 0.02 * np.random.randn(*base.shape)
    return base.astype(np.float32)


def build_4d_field(volume3d, T=40, phase_shift=0.0, radial_mod=1.0):
    """
    Build a living 4D field V(t,x,y,z) with breathing modulation.
    """
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = (
            1.0
            + 0.30 * math.sin(theta + phase_shift)
            + 0.25 * np.cos(2.2 * theta + 3.5 * R * radial_mod)
        )
        V[t] = volume3d * mod

    return V


def compute_dphi_4d(V):
    """
    Compute |∇V| for each time slice.
    """
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


def omega_field(dphi):
    """
    Ω = 1/(1+|ΔΦ|) — error geometry conformal factor.
    """
    return 1.0 / (1.0 + np.abs(dphi))


def harmonic_counts(dphi):
    """
    Partition Δφ values into:
      core  → top 5% (or 95th percentile)
      shell → 50–95%
      void  → below median
    """
    vals = dphi.flatten()
    pos = vals[vals > 0.0]
    if pos.size == 0:
        total = int(vals.size)
        return 0, 0, total
    p95 = float(np.percentile(pos, 95.0))
    p50 = float(np.percentile(pos, 50.0))
    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())
    return core, shell, void


def multi_scale_persistence(dphi):
    """
    Simple multi-scale persistence:
      • downsample at 1×, 2×, 4×, 8×
      • compare average |ΔΦ|
      • high persistence → values stable across scales
    """
    T, nx, ny, nz = dphi.shape
    norms = []

    def norm_of(slice_4d):
        return float(np.mean(np.abs(slice_4d)))

    norms.append(norm_of(dphi))
    if T >= 20 and nx >= 32:
        norms.append(norm_of(dphi[::2, ::2, ::2, ::2]))
    if T >= 10 and nx >= 16:
        norms.append(norm_of(dphi[::4, ::4, ::4, ::4]))
    if T >= 5 and nx >= 8:
        norms.append(norm_of(dphi[::8, ::8, ::8, ::8]))

    if len(norms) <= 1:
        return 0.0

    arr = np.array(norms)
    return float(1.0 - np.std(arr) / (np.mean(arr) + 1e-9))


def enforce_harmonic_stability(dphi):
    """
    Softly nudge the field toward core:shell:void ≈ 1:9:10.
    """
    core, shell, void = harmonic_counts(dphi)
    total = core + shell + void
    if total == 0:
        return dphi

    ratio_core = core / total
    ratio_shell = shell / total
    ratio_void = void / total

    t_core = 1.0 / 20.0
    t_shell = 9.0 / 20.0
    t_void = 10.0 / 20.0

    err = abs(ratio_core - t_core) + abs(ratio_shell - t_shell) + abs(ratio_void - t_void)
    if err < 0.05:
        return dphi

    vals = dphi
    pos = vals[vals > 0.0]
    if pos.size == 0:
        return dphi

    p95 = float(np.percentile(pos, 95.0))
    p50 = float(np.percentile(pos, 50.0))

    high_mask = vals >= p95
    mid_mask = (vals < p95) & (vals >= p50)
    low_mask = vals < p50

    vals = vals.copy()
    vals[high_mask] *= 1.02
    vals[mid_mask] *= 0.99
    vals[low_mask] *= 0.985
    return vals


# ─────────────────────────────────────────────────────────────
# 2. CHANNEL SYNTHESIS (QCX / QIM / SOLAR / AFM)
# ─────────────────────────────────────────────────────────────

def synthesize_channels(base3d, T=40):
    """
    Build 4D fields for:
      • QCX_core      — atomic kernel (1×)
      • QIM_shell     — molecular-like shell modulation
      • Solar_env     — slower, outer breathing envelope
      • AFM_anchor    — horizon-weighted high-amplitude regions
    """
    # QCX: atomic core
    V_qcx = build_4d_field(base3d, T=T, phase_shift=0.0, radial_mod=1.0)

    # QIM-like: slightly smoothed + semantic bump
    V_qim = build_4d_field(
        base3d * (1.0 + 0.20 * np.tanh(base3d)),
        T=T,
        phase_shift=0.9,
        radial_mod=1.1,
    )

    # Solar-like: slow, outer emphasis
    V_solar = build_4d_field(
        base3d,
        T=T,
        phase_shift=0.5,
        radial_mod=1.3,
    )

    # AFM-like: emphasize high-amplitude "surface" features
    median = float(np.median(base3d))
    V_afm = build_4d_field(
        base3d * (1.0 + 0.4 * (base3d > median)),
        T=T,
        phase_shift=1.7,
        radial_mod=1.0,
    )

    return {
        "QCX_core": V_qcx,
        "QIM_shell": V_qim,
        "Solar_env": V_solar,
        "AFM_anchor": V_afm,
    }


def channel_metrics(name, V: np.ndarray) -> tuple[ChannelMetrics, np.ndarray, np.ndarray]:
    dphi = compute_dphi_4d(V)

    E = safe_f(np.mean(np.abs(V)))
    I = safe_f(np.mean(dphi))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)

    C = (E * I) / (1.0 + abs(dphi_global))

    Ω = omega_field(dphi)
    omega_mean = safe_f(np.mean(Ω))
    omega_std = safe_f(np.std(Ω))

    curvature_proxy = safe_f(np.mean(np.abs(dphi - np.mean(dphi))))

    persistence = multi_scale_persistence(dphi)

    core, shell, void = harmonic_counts(dphi)

    # Insight weight: Ω * (1 - λ) * persistence
    weight_S = omega_mean * (1.0 - lam_eff) * persistence

    m = ChannelMetrics(
        name=name,
        E=E,
        I=I,
        C=C,
        dphi_global=dphi_global,
        lambda_eff=lam_eff,
        barrier_scale=safe_f(barrier_scale),
        omega_mean=omega_mean,
        omega_std=omega_std,
        curvature_proxy=curvature_proxy,
        persistence=persistence,
        core=core,
        shell=shell,
        void=void,
        weight_S=weight_S,
    )
    return m, dphi, Ω


def dominant_fusion(channels: dict, metrics_map: dict, log_fp=None):
    """
    Pick dominant "teacher" and fuse channels toward it.
    """
    names = list(channels.keys())
    weights = np.array([metrics_map[n].weight_S for n in names], dtype=np.float64)

    if np.all(weights <= 0):
        teacher_name = "QCX_core"
    else:
        teacher_name = names[int(np.argmax(weights))]

    teacher_field = channels[teacher_name]
    m_star = metrics_map[teacher_name]

    curv = max(m_star.curvature_proxy, 1e-6)
    # Map curvature (~0.003–0.03) into [0.18, 0.45]
    alpha = 0.18 + 0.27 * min(1.0, (curv - 0.002) / 0.03)

    if log_fp is not None:
        log(
            log_fp,
            f"[Dominant] Teacher channel → {teacher_name} (S={m_star.weight_S:.6f}, α={alpha:.3f})",
        )

    fused_channels = {}
    for n in names:
        if n == teacher_name:
            fused_channels[n] = channels[n].copy()
        else:
            fused_channels[n] = (1.0 - alpha) * channels[n] + alpha * teacher_field

    stacked = np.stack([fused_channels[n] for n in names], axis=-1)
    V_unified = np.mean(stacked, axis=-1)

    return teacher_name, float(alpha), fused_channels, V_unified


# ─────────────────────────────────────────────────────────────
# 3. VISUALS
# ─────────────────────────────────────────────────────────────

def radial_profile(slice2d):
    nx, ny = slice2d.shape
    cx = (nx - 1) / 2.0
    cy = (ny - 1) / 2.0
    Y, X = np.indices(slice2d.shape)
    R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    r = R.flatten()
    v = slice2d.flatten()
    nbins = int(max(nx, ny) / 2)
    bins = np.linspace(0, r.max(), nbins + 1)
    idx = np.digitize(r, bins) - 1
    prof = np.zeros(nbins, dtype=np.float64)
    counts = np.zeros(nbins, dtype=np.int64)
    for i, val in zip(idx, v):
        if 0 <= i < nbins:
            prof[i] += val
            counts[i] += 1
    counts[counts == 0] = 1
    prof /= counts
    centers = 0.5 * (bins[:-1] + bins[1:])
    return centers, prof


def make_visuals(V_unified, dphi_unified, omega_unified, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V_unified.shape
    t_mid = T // 2
    z_mid = nz // 2

    # 1) Δφ central slice
    central = dphi_unified[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QCX v10.1 Δφ central slice (crystalline fusion)")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # 2) Δφ max projection
    maxproj = dphi_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QCX v10.1 Δφ max projection (multi-scale nodes)")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # 3) Ω max projection
    omega_max = omega_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QCX v10.1 Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    # 4) Resonance curve
    energy_t = np.mean(np.abs(V_unified), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_unified|>")
    plt.title("QCX v10.1 resonance curve (crystal fusion breathing)")
    p_r = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_r, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_r)

    # 5) Radial profile
    r, prof = radial_profile(central)
    fig = plt.figure()
    plt.plot(r, prof)
    plt.xlabel("radius (pixels)")
    plt.ylabel("⟨Δφ⟩(r)")
    plt.title("QCX v10.1 radial Δφ profile (stacked shells)")
    p_rad = out_dir / f"{prefix}_radial_profile.png"
    fig.savefig(p_rad, bbox_inches="tight")
    plt.close(fig)
    paths["radial_profile"] = str(p_rad)

    # 6) Δφ histogram
    fig = plt.figure()
    plt.hist(dphi_unified.flatten(), bins=80)
    plt.xlabel("Δφ")
    plt.ylabel("count")
    plt.title("QCX v10.1 Δφ histogram (roughness distribution)")
    p_h = out_dir / f"{prefix}_dphi_histogram.png"
    fig.savefig(p_h, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_histogram"] = str(p_h)

    # 7) Time–radius strip
    central_t = dphi_unified[:, :, :, z_mid]
    nx2, ny2 = central_t.shape[1], central_t.shape[2]
    cx2 = (nx2 - 1) / 2.0
    cy2 = (ny2 - 1) / 2.0
    Y2, X2 = np.indices((nx2, ny2))
    R2 = np.sqrt((X2 - cx2) ** 2 + (Y2 - cy2) ** 2)
    r_flat = R2.flatten()
    nbins = int(max(nx2, ny2) / 2)
    bins = np.linspace(0, r_flat.max(), nbins + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])

    strip = np.zeros((T, nbins), dtype=np.float32)
    idx = np.digitize(r_flat, bins) - 1
    for t in range(T):
        vals = central_t[t].flatten()
        acc = np.zeros(nbins, dtype=np.float64)
        cnt = np.zeros(nbins, dtype=np.float64)
        for i, v in zip(idx, vals):
            if 0 <= i < nbins:
                acc[i] += v
                cnt[i] += 1.0
        cnt[cnt == 0] = 1.0
        strip[t] = acc / cnt

    fig = plt.figure()
    plt.imshow(
        strip,
        aspect="auto",
        origin="lower",
        extent=[centers[0], centers[-1], 0, T - 1],
    )
    plt.xlabel("radius")
    plt.ylabel("t")
    plt.title("QCX v10.1 time–radius strip (multi-scale breathing shells)")
    plt.colorbar(label="⟨Δφ⟩(r,t)")
    p_tr = out_dir / f"{prefix}_time_radius_strip.png"
    fig.savefig(p_tr, bbox_inches="tight")
    plt.close(fig)
    paths["time_radius_strip"] = str(p_tr)

    return paths


# ─────────────────────────────────────────────────────────────
# 4. STATE, LEDGER, AUTOGEN SPEC
# ─────────────────────────────────────────────────────────────

def write_state_ledger_spec(root_dir: Path,
                            state_dir: Path,
                            visuals_dir: Path,
                            ledger_dir: Path,
                            V_unified,
                            dphi_unified,
                            omega_unified,
                            channels,
                            chan_metrics,
                            teacher_name,
                            alpha,
                            visuals):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qcx_v10_1_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qcx_v10_1_ledger.jsonl"
    spec_path = (root_dir / "codex" / "quantum.crystal" / "v10_1" /
                 "engine" / "qcx_v10_2_autogen_spec.json")

    T, nx, ny, nz = V_unified.shape

    E = safe_f(np.mean(np.abs(V_unified)))
    I = safe_f(np.mean(dphi_unified))
    dphi_global = I
    lambda_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lambda_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(omega_unified))
    omega_std = safe_f(np.std(omega_unified))
    curvature_proxy = safe_f(np.mean(np.abs(dphi_unified - np.mean(dphi_unified))))

    core, shell, void = harmonic_counts(dphi_unified)
    persistence = multi_scale_persistence(dphi_unified)

    chan_dict = {name: asdict(m) for name, m in chan_metrics.items()}

    state_obj = {
        "protocol": "CodexQCXCrystallineFusion",
        "version": "10.1",
        "timestamp": now_utc_iso(),
        "mode": "crystalline-fusion",
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": {
                "E": E,
                "I": I,
                "C": C,
            },
            "H19_dphi_global": dphi_global,
            "lambda_eff": lambda_eff,
            "barrier_scale": safe_f(barrier_scale),
            "omega_mean": omega_mean,
            "omega_std": omega_std,
            "curvature_proxy": curvature_proxy,
            "harmonics": {
                "core": core,
                "shell": shell,
                "void": void,
            },
            "multi_scale_persistence": persistence,
        },
        "channels": chan_dict,
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
        },
        "codex": {
            "node": "QCX",
            "H_layers": {
                "H7": 0.70,
                "H7B": "ΔΦ Cusp Law v2.8 (irreversibility kernel)",
                "H16": "Insight geometry (pattern curvature C_geo)",
                "H19": "Global dphi integration (4D field → C)",
                "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                "cusp_v2_8": "λ = P/P_cr → 1-, ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|) defines conformal metric",
                "harmonic_stability": "Stable fields exhibit core:shell:void ≈ 1:9:10",
            },
            "memory": {
                "node_role": "atomic-scale Δφ kernel fused with QIM/Solar/AFM stack",
                "baseline_versions": [
                    "QCX v10.0",
                    "QIM v5.x",
                ],
                "current_version": "QCX v10.1",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "crystalline-fusion",
        "state_file": str(state_path),
        "teacher": teacher_name,
        "alpha_teach": alpha,
        "E": E,
        "I": I,
        "C": C,
        "dphi_global": dphi_global,
        "lambda_eff": lambda_eff,
        "barrier_scale": safe_f(barrier_scale),
        "omega_mean": omega_mean,
        "omega_std": omega_std,
        "curvature_proxy": curvature_proxy,
        "core": core,
        "shell": shell,
        "void": void,
        "multi_scale_persistence": persistence,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    spec_obj = {
        "protocol": "QCXAutoGenSpec",
        "source_version": "10.1",
        "next_version": "10.2",
        "timestamp": now_utc_iso(),
        "current_metrics": {
            "triad": {"E": E, "I": I, "C": C},
            "dphi_global": dphi_global,
            "lambda_eff": lambda_eff,
            "barrier_scale": safe_f(barrier_scale),
            "omega_mean": omega_mean,
            "omega_std": omega_std,
            "curvature_proxy": curvature_proxy,
            "multi_scale_persistence": persistence,
        },
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
            "channels": list(chan_metrics.keys()),
        },
        "recommendation": {
            "next_focus": (
                "Replace synthetic QIM/Solar/AFM channels with real QIM v5.x and AFM volumes, "
                "and cross-check QCX harmonic structure against physical data."
            ),
            "recommended_resolution": [int(nx), int(ny), int(nz)],
            "recommended_T": int(T),
        },
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ─────────────────────────────────────────────────────────────
# 5. MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    parser.add_argument("--input_dir", required=False)
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    input_dir = Path(args.input_dir) if args.input_dir else (root_dir / "codex" / "quantum.crystal" / "v10_1" / "input_v10_1")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qcx_v10_1_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QCX v10.1 — Crystalline Fusion Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")

    try:
        base3d = synthetic_crystal(shape=(64, 64, 64), seed=3101)
        T = 40

        channels = synthesize_channels(base3d, T=T)

        metrics_map: dict[str, ChannelMetrics] = {}
        for name, V in channels.items():
            m, dphi_ch, _Omega_ch = channel_metrics(name, V)
            metrics_map[name] = m
            log(
                log_fp,
                f"[Channel] {name}: E={m.E:.6f}, I={m.I:.6f}, C={m.C:.6f}, "
                f"S={m.weight_S:.6f}, core={m.core}, shell={m.shell}, void={m.void}",
            )

        teacher_name, alpha, fused_channels, V_unified = dominant_fusion(channels, metrics_map, log_fp=log_fp)

        dphi_unified = compute_dphi_4d(V_unified)
        dphi_unified = enforce_harmonic_stability(dphi_unified)
        omega_unified = omega_field(dphi_unified)

        visuals = make_visuals(V_unified, dphi_unified, omega_unified, visuals_dir, "qcx_v10_1_field")

        state_path, ledger_path, spec_path = write_state_ledger_spec(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            V_unified=V_unified,
            dphi_unified=dphi_unified,
            omega_unified=omega_unified,
            channels=fused_channels,
            chan_metrics=metrics_map,
            teacher_name=teacher_name,
            alpha=alpha,
            visuals=visuals,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v10.2 autogen spec → {spec_path}")
        log(log_fp, "QCX v10.1 run complete.")

    except Exception as e:
        err = "QCX v10.1 encountered an error: " + repr(e)
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
