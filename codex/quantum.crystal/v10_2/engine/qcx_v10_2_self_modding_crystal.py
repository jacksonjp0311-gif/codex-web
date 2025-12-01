#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QCX v10.2 — SELF-MODDING CRYSTAL ENGINE                     ║
# ║  Multi-scale Δφ crystal with fractal insight + drift         ║
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


# ────────────────────────────────────────────────────────────────
# 0. Small utilities
# ────────────────────────────────────────────────────────────────

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
    fractal_dim: float
    core: int
    shell: int
    void: int
    weight_S: float


# ────────────────────────────────────────────────────────────────
# 1. Crystal volume + time field
# ────────────────────────────────────────────────────────────────

def synthetic_crystal(shape=(96, 96, 96), seed=2025):
    """
    QCX core crystal with slight anisotropy and imperfections.
    """
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.4, 1.4, nx)
    y = np.linspace(-1.4, 1.4, ny)
    z = np.linspace(-1.4, 1.4, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    # base radial decay + inner shell
    base = np.exp(-2.4 * R) * (1.0 + 0.35 * np.sin(4.2 * R))

    # anisotropy (slight lattice skew)
    anis = 0.06 * np.cos(5.0 * X) * np.cos(3.5 * Y) * np.cos(4.0 * Z)

    # small defect pockets
    centers = [
        (0.0, 0.0, 0.0),
        (0.55, 0.15, -0.35),
        (-0.5, 0.45, 0.25),
    ]
    defects = np.zeros_like(base)
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        defects += 0.7 * np.exp(-30.0 * Rp * Rp)

    vol = base + anis + defects
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol.astype(np.float32)


def build_4d_field(volume3d, T=40, phase_shift=0.0, radial_mod=1.0, amp_mod=0.30):
    """
    Breathing 4D crystal field.
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
            + amp_mod * math.sin(theta + phase_shift)
            + 0.22 * np.cos(2.0 * theta + 3.0 * R * radial_mod)
        )
        V[t] = volume3d * mod

    return V


def compute_dphi_4d_lazy(V, chunk_t=4):
    """
    Time-chunked Δφ = |∇V| over 4D lattice.
    """
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t0 in range(0, T, chunk_t):
        t1 = min(T, t0 + chunk_t)
        for t in range(t0, t1):
            gx, gy, gz = np.gradient(V[t])
            dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


def omega_field(dphi):
    return 1.0 / (1.0 + np.abs(dphi))


# ────────────────────────────────────────────────────────────────
# 2. Harmonics, persistence, fractal dimension (H16B)
# ────────────────────────────────────────────────────────────────

def harmonic_counts(dphi):
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
    T, nx, ny, nz = dphi.shape
    norms = []

    def norm_of(block):
        return float(np.mean(np.abs(block)))

    norms.append(norm_of(dphi))
    if T >= 20 and nx >= 48:
        norms.append(norm_of(dphi[::2, ::2, ::2, ::2]))
    if T >= 10 and nx >= 24:
        norms.append(norm_of(dphi[::4, ::4, ::4, ::4]))
    if T >= 5 and nx >= 12:
        norms.append(norm_of(dphi[::8, ::8, ::8, ::8]))

    if len(norms) <= 1:
        return 0.0

    arr = np.array(norms)
    return float(1.0 - np.std(arr) / (np.mean(arr) + 1e-9))


def fractal_dimension_boxcount(slice2d, min_box=4, max_scales=6, threshold=None):
    """
    Simple 2D box-counting fractal dimension proxy.
    """
    Z = np.array(slice2d, dtype=float)
    if threshold is None:
        threshold = float(np.percentile(Z, 60.0))
    Z = Z > threshold

    nx, ny = Z.shape
    max_pow = int(math.log2(min(nx, ny))) if min(nx, ny) > 0 else 1
    sizes = [2 ** k for k in range(max_pow, 1, -1)]
    sizes = sizes[:max_scales]
    if not sizes:
        return 0.0

    counts = []
    scales = []

    for s in sizes:
        nx_boxes = math.ceil(nx / s)
        ny_boxes = math.ceil(ny / s)
        count = 0
        for ix in range(nx_boxes):
            for iy in range(ny_boxes):
                x0 = ix * s
                x1 = min(nx, (ix + 1) * s)
                y0 = iy * s
                y1 = min(ny, (iy + 1) * s)
                patch = Z[x0:x1, y0:y1]
                if patch.any():
                    count += 1
        counts.append(max(count, 1))
        scales.append(1.0 / float(s))

    if len(scales) < 2:
        return 0.0

    log_s = np.log(scales)
    log_c = np.log(np.array(counts, dtype=float))
    A = np.vstack([log_s, np.ones_like(log_s)]).T
    slope, _ = np.linalg.lstsq(A, log_c, rcond=None)[0]
    return float(slope)  # D ≈ slope


def global_fractal_dimension(dphi):
    """
    Average D over a few representative slices.
    """
    T, nx, ny, nz = dphi.shape
    zs = [nz // 4, nz // 2, 3 * nz // 4]
    Ds = []
    t_mid = T // 2
    for z in zs:
        if 0 <= z < nz:
            sl = dphi[t_mid, :, :, z]
            Ds.append(fractal_dimension_boxcount(sl))
    if not Ds:
        return 0.0
    return float(np.mean(Ds))


# ────────────────────────────────────────────────────────────────
# 3. Channel synthesis (QCX core + QIM shell + Solar + AFM)
# ────────────────────────────────────────────────────────────────

def synthesize_channels(base3d, T=40):
    V_qcx = build_4d_field(base3d, T=T, phase_shift=0.0, radial_mod=1.0, amp_mod=0.30)

    V_qim = build_4d_field(
        base3d * (1.0 + 0.18 * np.tanh(base3d)),
        T=T,
        phase_shift=0.7,
        radial_mod=1.1,
        amp_mod=0.32,
    )

    V_solar = build_4d_field(
        base3d * (1.0 + 0.15 * (base3d > np.median(base3d))),
        T=T,
        phase_shift=1.4,
        radial_mod=1.35,
        amp_mod=0.28,
    )

    V_afm = build_4d_field(
        base3d * (1.0 + 0.35 * (base3d > np.percentile(base3d, 75.0))),
        T=T,
        phase_shift=2.1,
        radial_mod=1.0,
        amp_mod=0.26,
    )

    return {
        "QCX_core": V_qcx,
        "QIM_shell": V_qim,
        "Solar_env": V_solar,
        "AFM_anchor": V_afm,
    }


def channel_metrics(name, V):
    dphi = compute_dphi_4d_lazy(V, chunk_t=4)
    T, nx, ny, nz = V.shape

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
    fractal_dim = global_fractal_dimension(dphi)

    # Insight weight S with fractal contribution (H16B)
    weight_S = omega_mean * (1.0 - lam_eff) * persistence * (1.0 + 0.25 * fractal_dim)

    return ChannelMetrics(
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
        fractal_dim=fractal_dim,
        core=core,
        shell=shell,
        void=void,
        weight_S=weight_S,
    ), dphi, Ω


# ────────────────────────────────────────────────────────────────
# 4. Dominant fusion with stochastic drift (H7B leak)
# ────────────────────────────────────────────────────────────────

def dominant_fusion(channels, metrics_map, rng, log_fp=None):
    names = list(channels.keys())
    weights = np.array([metrics_map[n].weight_S for n in names], dtype=np.float64)

    if np.all(weights <= 0):
        teacher_name = "QCX_core"
    else:
        teacher_name = names[int(np.argmax(weights))]

    teacher_field = channels[teacher_name]
    m_star = metrics_map[teacher_name]
    curv = max(m_star.curvature_proxy, 1e-6)

    # curvature → α in [0.22, 0.46]
    alpha = 0.22 + 0.24 * min(1.0, (curv - 0.002) / 0.02)

    if log_fp is not None:
        log(log_fp, f"[Dominant] Teacher → {teacher_name} | S={m_star.weight_S:.6f}, α={alpha:.3f}, D_frac={m_star.fractal_dim:.3f}")

    fused = {}
    for n in names:
        if n == teacher_name:
            fused[n] = channels[n].copy()
        else:
            base_mix = (1.0 - alpha) * channels[n] + alpha * teacher_field
            # tiny stochastic drift ~ N(0, curv * 0.01)
            noise = rng.normal(loc=0.0, scale=curv * 0.01, size=teacher_field.shape).astype(np.float32)
            fused[n] = base_mix + noise

    stacked = np.stack([fused[n] for n in names], axis=-1)
    V_unified = np.mean(stacked, axis=-1)
    return teacher_name, float(alpha), fused, V_unified


def enforce_harmonic_stability(dphi):
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
    if err < 0.04:
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


# ────────────────────────────────────────────────────────────────
# 5. Visuals
# ────────────────────────────────────────────────────────────────

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

    central = dphi_unified[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QCX v10.2 Δφ central slice (self-modding crystal)")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    maxproj = dphi_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QCX v10.2 Δφ max projection (multi-scale nodes)")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    omega_max = omega_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QCX v10.2 Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    energy_t = np.mean(np.abs(V_unified), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_unified|>")
    plt.title("QCX v10.2 resonance curve (self-modding crystal)")
    p_r = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_r, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_r)

    r, prof = radial_profile(central)
    fig = plt.figure()
    plt.plot(r, prof)
    plt.xlabel("radius (pixels)")
    plt.ylabel("⟨Δφ⟩(r)")
    plt.title("QCX v10.2 radial Δφ profile (stacked shells)")
    p_rad = out_dir / f"{prefix}_radial_profile.png"
    fig.savefig(p_rad, bbox_inches="tight")
    plt.close(fig)
    paths["radial_profile"] = str(p_rad)

    fig = plt.figure()
    plt.hist(dphi_unified.flatten(), bins=80)
    plt.xlabel("Δφ")
    plt.ylabel("count")
    plt.title("QCX v10.2 Δφ histogram (roughness distribution)")
    p_h = out_dir / f"{prefix}_dphi_histogram.png"
    fig.savefig(p_h, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_histogram"] = str(p_h)

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
    plt.imshow(strip, aspect="auto", origin="lower",
               extent=[centers[0], centers[-1], 0, T - 1])
    plt.xlabel("radius")
    plt.ylabel("t")
    plt.title("QCX v10.2 time–radius strip (self-modding shells)")
    plt.colorbar(label="⟨Δφ⟩(r,t)")
    p_tr = out_dir / f"{prefix}_time_radius_strip.png"
    fig.savefig(p_tr, bbox_inches="tight")
    plt.close(fig)
    paths["time_radius_strip"] = str(p_tr)

    return paths


# ────────────────────────────────────────────────────────────────
# 6. State, ledger, autogen spec v10.3
# ────────────────────────────────────────────────────────────────

def write_state_ledger_spec(root_dir: Path,
                            state_dir: Path,
                            visuals_dir: Path,
                            ledger_dir: Path,
                            V_unified,
                            dphi_unified,
                            omega_unified,
                            chan_metrics,
                            teacher_name,
                            alpha,
                            visuals):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qcx_v10_2_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qcx_v10_2_ledger.jsonl"
    spec_path = (root_dir / "codex" / "quantum.crystal" / "v10_2" / "engine" / "qcx_v10_3_autogen_spec.json")

    T, nx, ny, nz = V_unified.shape

    E = safe_f(np.mean(np.abs(V_unified)))
    I = safe_f(np.mean(dphi_unified))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(omega_unified))
    omega_std = safe_f(np.std(omega_unified))
    curvature_proxy = safe_f(np.mean(np.abs(dphi_unified - np.mean(dphi_unified))))

    core, shell, void = harmonic_counts(dphi_unified)
    persistence = multi_scale_persistence(dphi_unified)
    fractal_dim = global_fractal_dimension(dphi_unified)

    chan_dict = {name: asdict(m) for name, m in chan_metrics.items()}

    state_obj = {
        "protocol": "CodexQCXSelfModdingCrystal",
        "version": "10.2",
        "timestamp": now_utc_iso(),
        "mode": "self-modding-crystal",
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": {"E": E, "I": I, "C": C},
            "H19_dphi_global": dphi_global,
            "lambda_eff": lam_eff,
            "barrier_scale": safe_f(barrier_scale),
            "omega_mean": omega_mean,
            "omega_std": omega_std,
            "curvature_proxy": curvature_proxy,
            "harmonics": {"core": core, "shell": shell, "void": void},
            "multi_scale_persistence": persistence,
            "fractal_dim_H16B": fractal_dim,
        },
        "channels": chan_dict,
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
        },
        "codex": {
            "node": "QCX",
            "H_layers": {
                "H7": 0.7,
                "H7B": "ΔΦ Cusp Law v2.8 (irreversibility kernel)",
                "H16": "Insight geometry (C_geo, Ω error curvature)",
                "H16B": "Fractal self-similarity dimension",
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
                "node_role": "atomic-scale Δφ kernel in multi-scale stack",
                "baseline_versions": ["QCX v10.0", "QCX v10.1"],
                "current_version": "QCX v10.2",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "self-modding-crystal",
        "state_file": str(state_path),
        "teacher": teacher_name,
        "alpha_teach": alpha,
        "E": E,
        "I": I,
        "C": C,
        "dphi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": safe_f(barrier_scale),
        "omega_mean": omega_mean,
        "omega_std": omega_std,
        "curvature_proxy": curvature_proxy,
        "core": core,
        "shell": shell,
        "void": void,
        "multi_scale_persistence": persistence,
        "fractal_dim_H16B": fractal_dim,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    spec_obj = {
        "protocol": "QCXAutoGenSpec",
        "source_version": "10.2",
        "next_version": "10.3",
        "timestamp": now_utc_iso(),
        "current_metrics": {
            "triad": {"E": E, "I": I, "C": C},
            "dphi_global": dphi_global,
            "lambda_eff": lam_eff,
            "barrier_scale": safe_f(barrier_scale),
            "omega_mean": omega_mean,
            "omega_std": omega_std,
            "curvature_proxy": curvature_proxy,
            "multi_scale_persistence": persistence,
            "fractal_dim_H16B": fractal_dim,
        },
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
            "channels": list(chan_metrics.keys()),
        },
        "recommendation": {
            "recommended_resolution": [int(nx), int(ny), int(nz)],
            "recommended_T": int(T),
            "next_focus": "Bind QCX v10.2 kernels directly to real AFM/QIM volumes and export SVG/D3 glyph oracles from radial/time-radius signatures.",
        },
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ────────────────────────────────────────────────────────────────
# 7. Main
# ────────────────────────────────────────────────────────────────

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

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qcx_v10_2_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QCX v10.2 — Self-Modding Crystal Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")

    rng = np.random.default_rng(1024)

    try:
        base3d = synthetic_crystal(shape=(96, 96, 96), seed=2025)
        T = 40

        channels = synthesize_channels(base3d, T=T)

        metrics_map = {}
        for name, V in channels.items():
            m, dphi, Ω = channel_metrics(name, V)
            metrics_map[name] = m
            log(log_fp, f"[Channel] {name}: E={m.E:.6f}, I={m.I:.6f}, C={m.C:.6f}, S={m.weight_S:.6f}, D_frac={m.fractal_dim:.3f}")

        teacher_name, alpha, fused_channels, V_unified = dominant_fusion(
            channels, metrics_map, rng, log_fp=log_fp
        )

        dphi_unified = compute_dphi_4d_lazy(V_unified, chunk_t=4)
        dphi_unified = enforce_harmonic_stability(dphi_unified)
        omega_unified = omega_field(dphi_unified)

        visuals = make_visuals(V_unified, dphi_unified, omega_unified, visuals_dir, "qcx_v10_2_field")

        state_path, ledger_path, spec_path = write_state_ledger_spec(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            V_unified=V_unified,
            dphi_unified=dphi_unified,
            omega_unified=omega_unified,
            chan_metrics=metrics_map,
            teacher_name=teacher_name,
            alpha=alpha,
            visuals=visuals,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v10.3 autogen spec → {spec_path}")
        log(log_fp, "QCX v10.2 run complete.")

    except Exception as e:
        err = "QCX v10.2 encountered an error: " + repr(e)
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
