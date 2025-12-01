#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QCX v10.3 — PHYSICAL BINDING CRYSTAL ENGINE (AFM STANDARD)  ║
# ║  Synthetic–AFM–QIM–Solar fused Δφ crystal (96³ × T=40)       ║
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
# 0. SMALL UTILITIES
# ────────────────────────────────────────────────────────────────

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_f(x, default=0.0):
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
# 1. BASE VOLUMES: AFM BINDING + SYNTHETIC BACKUP
# ────────────────────────────────────────────────────────────────

def load_afm_volume(input_dir: Path, log_fp=None):
    if not input_dir.exists():
        log(log_fp, f"[AFM] Input dir not found, fallback to synthetic: {input_dir}")
        return None

    candidates = sorted(list(input_dir.glob("*.npy")) + list(input_dir.glob("*.npz")))
    if not candidates:
        log(log_fp, f"[AFM] No .npy/.npz found in {input_dir}, using synthetic crystal.")
        return None

    path = candidates[0]
    log(log_fp, f"[AFM] Loading AFM volume → {path}")
    try:
        if path.suffix == ".npy":
            vol = np.load(path)
        else:
            data = np.load(path)
            # heuristically pick first array
            vol = data[list(data.keys())[0]]
    except Exception as e:
        log(log_fp, f"[AFM] Failed to load AFM volume ({e!r}), fallback to synthetic.")
        return None

    vol = np.asarray(vol, dtype=np.float32)
    if vol.ndim == 2:
        vol = vol[None, :, :]
    if vol.ndim != 3:
        log(log_fp, f"[AFM] Volume ndim={vol.ndim} not 3D, fallback to synthetic.")
        return None

    # normalize to [0,1]
    vmin = float(vol.min())
    vmax = float(vol.max())
    if vmax > vmin:
        vol = (vol - vmin) / (vmax - vmin + 1e-9)
    else:
        vol = np.zeros_like(vol, dtype=np.float32)

    log(log_fp, f"[AFM] Loaded AFM volume with shape {vol.shape}")
    return vol.astype(np.float32)


def synthetic_crystal(shape=(96, 96, 96), seed=2025):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    base = np.exp(-2.2 * R) * (1.0 + 0.35 * np.sin(5.0 * R))
    peaks = np.zeros_like(base)

    centers = [
        (0.0, 0.0, 0.0),
        (0.7, 0.3, -0.4),
        (-0.6, 0.5, 0.4),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        peaks += np.exp(-32.0 * Rp * Rp)

    vol = base + 0.7 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    vol = vol.astype(np.float32)
    vol -= vol.min()
    if vol.max() > 0:
        vol /= vol.max()
    return vol


def ensure_resolution(vol, target_shape=(96, 96, 96)):
    nx, ny, nz = vol.shape
    tx, ty, tz = target_shape
    sx = min(nx, tx)
    sy = min(ny, ty)
    sz = min(nz, tz)
    cx = nx // 2
    cy = ny // 2
    cz = nz // 2
    hx = sx // 2
    hy = sy // 2
    hz = sz // 2
    cropped = vol[cx - hx:cx + hx, cy - hy:cy + hy, cz - hz:cz + hz]
    out = np.zeros(target_shape, dtype=np.float32)
    ox = (tx - sx) // 2
    oy = (ty - sy) // 2
    oz = (tz - sz) // 2
    out[ox:ox + sx, oy:oy + sy, oz:oz + sz] = cropped
    return out


def smooth1d(x):
    k = np.array([1.0, 2.0, 1.0], dtype=np.float32)
    pad = np.pad(x, 1, mode="edge")
    y = (pad[:-2] * k[0] + pad[1:-1] * k[1] + pad[2:] * k[2]) / k.sum()
    return y


def smooth3d(vol, passes=1):
    out = vol.astype(np.float32)
    for _ in range(passes):
        for axis in range(3):
            out = np.apply_along_axis(smooth1d, axis, out)
    return out


# ────────────────────────────────────────────────────────────────
# 2. 4D FIELD, Δφ, Ω, HARMONICS, FRACTAL
# ────────────────────────────────────────────────────────────────

def build_4d_field(volume3d, T=40, phase_shift=0.0, radial_mod=1.0, amp=1.0):
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
            + 0.28 * math.sin(theta + phase_shift)
            + 0.22 * np.cos(2.0 * theta + 3.2 * R * radial_mod)
        )
        V[t] = amp * volume3d * mod

    return V


def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


def omega_field(dphi):
    return 1.0 / (1.0 + np.abs(dphi))


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

    def norm_of(slice_4d):
        return float(np.mean(np.abs(slice_4d)))

    norms = [norm_of(dphi)]
    if T >= 20 and nx >= 48:
        norms.append(norm_of(dphi[::2, ::2, ::2, ::2]))
    if T >= 10 and nx >= 24:
        norms.append(norm_of(dphi[::4, ::4, ::4, ::4]))

    if len(norms) <= 1:
        return 0.0

    arr = np.array(norms)
    return float(1.0 - np.std(arr) / (np.mean(arr) + 1e-9))


def fractal_dimension_boxcount(slice2d, log_fp=None):
    Z = np.asarray(slice2d, dtype=np.float32)
    thr = float(np.percentile(Z, 75.0))
    Z = Z > thr
    if Z.sum() == 0:
        return 1.0

    min_side = min(Z.shape)
    max_exp = int(np.floor(np.log2(min_side))) - 1
    if max_exp <= 1:
        return 1.0

    sizes = 2 ** np.arange(1, max_exp + 1)
    counts = []
    inv_sizes = []

    for s in sizes:
        nx = Z.shape[0] // s
        ny = Z.shape[1] // s
        if nx == 0 or ny == 0:
            continue
        view = Z[: nx * s, : ny * s].reshape(nx, s, ny, s)
        blocks = view.any(axis=(1, 3))
        N = blocks.sum()
        if N > 0:
            counts.append(float(N))
            inv_sizes.append(1.0 / float(s))

    if len(counts) < 2:
        return 1.0

    logN = np.log(counts)
    logE = np.log(inv_sizes)
    A = np.vstack([logE, np.ones_like(logE)]).T
    sol, _, _, _ = np.linalg.lstsq(A, logN, rcond=None)
    D = float(sol[0])
    if log_fp is not None:
        log(log_fp, f"[Fractal] Box-counting dimension ≈ {D:.3f}")
    return D


# ────────────────────────────────────────────────────────────────
# 3. CHANNEL SYNTHESIS (QCX / QIM / SOLAR / AFM)
# ────────────────────────────────────────────────────────────────

def build_channels(base_afm, log_fp=None, T=40):
    base96 = ensure_resolution(base_afm, (96, 96, 96))
    base_smooth = smooth3d(base96, passes=1)
    base_sharp = base96 ** 1.2

    V_qcx_core = build_4d_field(base_sharp, T=T, phase_shift=0.0, radial_mod=1.0, amp=1.0)
    V_qim_shell = build_4d_field(base_smooth, T=T, phase_shift=0.9, radial_mod=1.1, amp=1.02)
    V_solar_env = build_4d_field(base96, T=T, phase_shift=1.7, radial_mod=1.3, amp=1.03)
    V_afm_anchor = build_4d_field(base96, T=T, phase_shift=2.4, radial_mod=0.9, amp=1.05)

    channels = {
        "QCX_core": V_qcx_core,
        "QIM_shell": V_qim_shell,
        "Solar_env": V_solar_env,
        "AFM_anchor": V_afm_anchor,
    }
    log(log_fp, "[Channels] Built QCX/QIM/Solar/AFM 4D fields.")
    return channels


def channel_metrics(name, V, log_fp=None):
    dphi = compute_dphi_4d(V)
    Ω = omega_field(dphi)

    E = safe_f(np.mean(np.abs(V)))
    I = safe_f(np.mean(dphi))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))

    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(Ω))
    omega_std = safe_f(np.std(Ω))
    curvature_proxy = safe_f(np.mean(np.abs(dphi - np.mean(dphi))))

    core, shell, void = harmonic_counts(dphi)
    persistence = multi_scale_persistence(dphi)

    # fractal on central slice
    T, nx, ny, nz = dphi.shape
    t_mid = T // 2
    z_mid = nz // 2
    slice2d = dphi[t_mid, :, :, z_mid]
    fractal_dim = fractal_dimension_boxcount(slice2d, log_fp=log_fp)

    # weight S with small boost for fractal_dim near 1.8–1.9
    fractal_boost = 1.0 + 0.2 * max(0.0, min(1.0, (fractal_dim - 1.6) / 0.6))
    weight_S = omega_mean * (1.0 - lam_eff) * persistence * fractal_boost

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
        fractal_dim=fractal_dim,
        core=core,
        shell=shell,
        void=void,
        weight_S=weight_S,
    )
    if log_fp is not None:
        log(
            log_fp,
            (
                f"[Channel] {name}: E={m.E:.6f}, I={m.I:.6f}, C={m.C:.6f}, "
                f"S={m.weight_S:.6f}, D_frac={m.fractal_dim:.3f}, "
                f"core={core}, shell={shell}, void={void}"
            ),
        )
    return m, dphi, Ω


def dominant_fusion(channels, metrics_map, log_fp=None):
    names = list(channels.keys())
    weights = np.array([metrics_map[n].weight_S for n in names], dtype=np.float64)

    if np.all(weights <= 0):
        teacher_name = "QCX_core"
    else:
        teacher_name = names[int(np.argmax(weights))]

    m_star = metrics_map[teacher_name]
    curv = max(m_star.curvature_proxy, 1e-6)
    # map curvature (~0.005–0.02) into α ∈ [0.22, 0.40]
    alpha = 0.22 + 0.18 * min(1.0, (curv - 0.004) / 0.02)

    # small cusp “leak” proportional to λ_eff
    leak_sigma = 0.01 * m_star.lambda_eff

    if log_fp is not None:
        log(
            log_fp,
            f"[Dominant] Teacher → {teacher_name} | S={m_star.weight_S:.6f}, "
            f"α={alpha:.3f}, leak_sigma={leak_sigma:.4f}, D_frac={m_star.fractal_dim:.3f}",
        )

    teacher_field = channels[teacher_name]
    fused_channels = {}

    for n in names:
        base = channels[n]
        if n == teacher_name:
            fused = base.copy()
        else:
            fused = (1.0 - alpha) * base + alpha * teacher_field

        if leak_sigma > 0.0:
            noise = leak_sigma * np.random.randn(*fused.shape).astype(np.float32)
            fused = fused + noise

        fused_channels[n] = fused

    stacked = np.stack([fused_channels[n] for n in names], axis=-1)
    V_unified = np.mean(stacked, axis=-1)
    return teacher_name, float(alpha), fused_channels, V_unified


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
# 4. VISUALS + SVG/D3 ORACLES
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
    maxproj = dphi_unified.max(axis=0).max(axis=2)
    omega_max = omega_unified.max(axis=0).max(axis=2)
    energy_t = np.mean(np.abs(V_unified), axis=(1, 2, 3))

    # 1) Δφ central slice
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QCX v10.3 Δφ central slice (AFM-bound crystal)")
    plt.colorbar()
    p_c_png = out_dir / f"{prefix}_dphi_central.png"
    p_c_svg = out_dir / f"{prefix}_dphi_central.svg"
    fig.savefig(p_c_png, bbox_inches="tight")
    fig.savefig(p_c_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["dphi_central_png"] = str(p_c_png)
    paths["dphi_central_svg"] = str(p_c_svg)

    # 2) Δφ max projection
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QCX v10.3 Δφ max projection (multi-node AFM-bound)")
    plt.colorbar()
    p_m_png = out_dir / f"{prefix}_dphi_maxproj.png"
    p_m_svg = out_dir / f"{prefix}_dphi_maxproj.svg"
    fig.savefig(p_m_png, bbox_inches="tight")
    fig.savefig(p_m_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["dphi_maxproj_png"] = str(p_m_png)
    paths["dphi_maxproj_svg"] = str(p_m_svg)

    # 3) Ω max projection
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QCX v10.3 Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o_png = out_dir / f"{prefix}_omega_maxproj.png"
    p_o_svg = out_dir / f"{prefix}_omega_maxproj.svg"
    fig.savefig(p_o_png, bbox_inches="tight")
    fig.savefig(p_o_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["omega_maxproj_png"] = str(p_o_png)
    paths["omega_maxproj_svg"] = str(p_o_svg)

    # 4) Resonance curve
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_unified|>")
    plt.title("QCX v10.3 resonance curve (AFM-bound breathing)")
    p_r_png = out_dir / f"{prefix}_resonance_curve.png"
    p_r_svg = out_dir / f"{prefix}_resonance_curve.svg"
    fig.savefig(p_r_png, bbox_inches="tight")
    fig.savefig(p_r_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["resonance_curve_png"] = str(p_r_png)
    paths["resonance_curve_svg"] = str(p_r_svg)

    # 5) Radial profile
    r, prof = radial_profile(central)
    fig = plt.figure()
    plt.plot(r, prof)
    plt.xlabel("radius (pixels)")
    plt.ylabel("⟨Δφ⟩(r)")
    plt.title("QCX v10.3 radial Δφ profile (AFM-bound shells)")
    p_rad_png = out_dir / f"{prefix}_radial_profile.png"
    p_rad_svg = out_dir / f"{prefix}_radial_profile.svg"
    fig.savefig(p_rad_png, bbox_inches="tight")
    fig.savefig(p_rad_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["radial_profile_png"] = str(p_rad_png)
    paths["radial_profile_svg"] = str(p_rad_svg)

    # 6) Δφ histogram
    fig = plt.figure()
    plt.hist(dphi_unified.flatten(), bins=80)
    plt.xlabel("Δφ")
    plt.ylabel("count")
    plt.title("QCX v10.3 Δφ histogram (roughness distribution)")
    p_h_png = out_dir / f"{prefix}_dphi_histogram.png"
    fig.savefig(p_h_png, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_histogram_png"] = str(p_h_png)

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
    plt.imshow(strip, aspect="auto", origin="lower",
               extent=[centers[0], centers[-1], 0, T - 1])
    plt.xlabel("radius")
    plt.ylabel("t")
    plt.title("QCX v10.3 time–radius strip (AFM-bound shells)")
    plt.colorbar(label="⟨Δφ⟩(r,t)")
    p_tr_png = out_dir / f"{prefix}_time_radius_strip.png"
    p_tr_svg = out_dir / f"{prefix}_time_radius_strip.svg"
    fig.savefig(p_tr_png, bbox_inches="tight")
    fig.savefig(p_tr_svg, bbox_inches="tight", format="svg")
    plt.close(fig)
    paths["time_radius_strip_png"] = str(p_tr_png)
    paths["time_radius_strip_svg"] = str(p_tr_svg)

    # data export for D3 (JSON arrays)
    data_oracle = {
        "radial_r": r.tolist(),
        "radial_profile": prof.tolist(),
        "time_radius_strip": strip.tolist(),
        "resonance_curve": energy_t.tolist(),
    }
    oracle_path = out_dir / f"{prefix}_oracle_data.json"
    oracle_path.write_text(json.dumps(data_oracle), encoding="utf-8")
    paths["oracle_data_json"] = str(oracle_path)

    return paths


# ────────────────────────────────────────────────────────────────
# 5. STATE, LEDGER, AUTOGEN SPEC
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
                            D_H16B,
                            visuals):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qcx_v10_3_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qcx_v10_3_ledger.jsonl"
    spec_path = root_dir / "codex" / "quantum.crystal" / "v10_3" / "engine_v10_3" / "qcx_v10_4_autogen_spec.json"

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

    chan_dict = {name: asdict(m) for name, m in chan_metrics.items()}

    state_obj = {
        "protocol": "CodexQCXPhysicalBindingCrystal",
        "version": "10.3",
        "timestamp": now_utc_iso(),
        "mode": "physical-binding-afm-standard",
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
            "fractal_dim_H16B": D_H16B,
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
                "H16B": "Fractal self-similarity dimension (box-counting)",
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
                "node_role": "AFM-bound atomic Δφ kernel in multi-scale stack",
                "baseline_versions": ["QCX v10.1", "QCX v10.2"],
                "current_version": "QCX v10.3",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "physical-binding-afm-standard",
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
        "fractal_dim_H16B": D_H16B,
    }

    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    spec_obj = {
        "protocol": "QCXAutoGenSpec",
        "source_version": "10.3",
        "next_version": "10.4",
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
            "fractal_dim_H16B": D_H16B,
        },
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
            "channels": list(chan_metrics.keys()),
        },
        "recommendation": {
            "recommended_resolution": [int(nx), int(ny), int(nz)],
            "recommended_T": int(T),
            "next_focus": (
                "Extend physical binding across multiple AFM cubes and QIM v5.x "
                "kernels; refine SVG/D3 glyph exports into Codex Physics White Paper."
            ),
        },
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ────────────────────────────────────────────────────────────────
# 6. MAIN
# ────────────────────────────────────────────────────────────────

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
    input_afm_dir = Path(args.input_afm_dir) if args.input_afm_dir else (root_dir / "codex" / "quantum_imaging" / "input_afm" / "nc_afm_standard")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qcx_v10_3_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QCX v10.3 — Physical Binding Crystal Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_afm  : {input_afm_dir}")

    try:
        afm_vol = load_afm_volume(input_afm_dir, log_fp=log_fp)
        if afm_vol is None:
            base = synthetic_crystal(shape=(96, 96, 96), seed=2025)
            log(log_fp, "[Base] Using synthetic crystal (no AFM volume available).")
        else:
            base = ensure_resolution(afm_vol, (96, 96, 96))
            log(log_fp, "[Base] Using AFM-bound base volume (96³).")

        T = 40
        channels = build_channels(base, log_fp=log_fp, T=T)

        metrics_map = {}
        for name, V in channels.items():
            m, _, _ = channel_metrics(name, V, log_fp=log_fp)
            metrics_map[name] = m

        teacher_name, alpha, fused_channels, V_unified = dominant_fusion(channels, metrics_map, log_fp=log_fp)

        dphi_unified = compute_dphi_4d(V_unified)
        dphi_unified = enforce_harmonic_stability(dphi_unified)
        omega_unified = omega_field(dphi_unified)

        T_u, nx_u, ny_u, nz_u = V_unified.shape
        t_mid = T_u // 2
        z_mid = nz_u // 2
        central_slice = dphi_unified[t_mid, :, :, z_mid]
        D_H16B = fractal_dimension_boxcount(central_slice, log_fp=log_fp)

        visuals = make_visuals(V_unified, dphi_unified, omega_unified, visuals_dir, "qcx_v10_3_field")

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
            D_H16B=D_H16B,
            visuals=visuals,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v10.4 autogen spec → {spec_path}")
        log(log_fp, "QCX v10.3 run complete.")

    except Exception as e:
        err = "QCX v10.3 encountered an error: " + repr(e)
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
