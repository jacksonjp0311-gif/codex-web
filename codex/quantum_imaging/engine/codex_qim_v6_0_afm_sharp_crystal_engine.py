#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v5.4 — ENTANGLEMENT GEOMETRY ENGINE                     ║
# ║  Cross-channel Δφ entanglement (QIM / Solar / QCX / TE / AFM)║
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
import scipy.ndimage as ndi
try:
    import matplotlib.pyplot as plt

def enhance_field(field):
    \"\"\"Codex QIM v6.0.1 sharpener:
    • 4× cubic upsample
    • Gaussian blur
    • Unsharp mask (0.8 gain)
    \"\"\"
    try:
        up = ndi.zoom(field, 4, order=3)
    except Exception:
        return field
    blurred = ndi.gaussian_filter(up, sigma=1.0)
    sharpened = up + 0.8 * (up - blurred)
    return sharpened
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False


# ╭──────────────────────────────────────────────────────────────╮
# │  0. SMALL UTILITIES                                         │
# ╰──────────────────────────────────────────────────────────────╯

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
    core: int
    shell: int
    void: int
    weight_S: float


# ╭──────────────────────────────────────────────────────────────╮
# │  1. BASE LATTICE — REAL AFM OR SYNTHETIC                    │
# ╰──────────────────────────────────────────────────────────────╯

def load_real_afm_cube(input_dir: Path, target_shape=(64, 64, 64), log_fp=None):
    files = list(input_dir.glob("*.npy")) + list(input_dir.glob("*.npz"))
    if not files:
        return None

    try:
        f0 = files[0]
        arr = np.load(f0)
        if isinstance(arr, np.lib.npyio.NpzFile):
            arr = arr[arr.files[0]]

        arr = np.array(arr, dtype=np.float32)

        if arr.ndim == 2:
            arr = np.stack([arr] * target_shape[2], axis=-1)
        elif arr.ndim == 4:
            arr = arr[arr.shape[0] // 2]

        base = np.zeros(target_shape, dtype=np.float32)
        sx, sy, sz = arr.shape[:3]
        tx, ty, tz = target_shape

        cx = min(sx, tx)
        cy = min(sy, ty)
        cz = min(sz, tz)

        x0 = (sx - cx) // 2
        y0 = (sy - cy) // 2
        z0 = (sz - cz) // 2

        xt = (tx - cx) // 2
        yt = (ty - cy) // 2
        zt = (tz - cz) // 2

        base[xt:xt+cx, yt:yt+cy, zt:zt+cz] = arr[x0:x0+cx, y0:y0+cy, z0:z0+cz]

        m = float(base.max() - base.min())
        if m > 0:
            base = (base - base.min()) / m

        log(log_fp, f"[AFM] Real AFM cube loaded from {f0}")
        return base
    except Exception as e:
        log(log_fp, f"[AFM] Failed to bind real AFM cube: {e!r}")
        return None


def synthetic_volume(shape=(64, 64, 64), seed=541):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    base = np.exp(-2.0 * R) * (1.0 + 0.35 * np.sin(4.0 * R))
    peaks = np.zeros_like(base)

    centers = [
        (0.0, 0.0, 0.0),
        (0.6, 0.3, -0.4),
        (-0.5, 0.5, 0.3),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-32.0 * Rp*Rp)

    vol = base + 0.7 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol


def build_4d_field(volume3d, T=40, phase_shift=0.0, radial_mod=1.0):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = (
            1.0
            + 0.30 * math.sin(theta + phase_shift)
            + 0.22 * np.cos(2.0 * theta + 3.0 * R * radial_mod)
        )
        V[t] = volume3d * mod

    return V


def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
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


# ╭──────────────────────────────────────────────────────────────╮
# │  2. CHANNEL SYNTHESIS (QIM / SOLAR / QCX / TE / AFM)        │
# ╰──────────────────────────────────────────────────────────────╯

def synthesize_channels(base3d, T, log_fp=None):
    V_qim = build_4d_field(base3d, T=T, phase_shift=0.0, radial_mod=1.0)
    V_solar = build_4d_field(base3d, T=T, phase_shift=0.7, radial_mod=1.3)
    V_qcx = build_4d_field(base3d, T=T, phase_shift=1.4, radial_mod=0.8)
    V_third = build_4d_field(base3d * (1.0 + 0.2 * np.tanh(base3d)),
                             T=T, phase_shift=2.1, radial_mod=1.1)
    V_afm = build_4d_field(base3d * (1.0 + 0.4 * (base3d > np.median(base3d))),
                           T=T, phase_shift=2.8, radial_mod=1.0)

    log(log_fp, "[Base] Channels synthesized for entanglement geometry.")
    return {
        "QIM": V_qim,
        "Solar": V_solar,
        "QCX": V_qcx,
        "ThirdEye": V_third,
        "AFM": V_afm,
    }


def channel_metrics(name, V):
    dphi = compute_dphi_4d(V)
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

    weight_S = omega_mean * (1.0 - lam_eff) * persistence

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
        core=core,
        shell=shell,
        void=void,
        weight_S=weight_S,
    ), dphi, Ω


# ╭──────────────────────────────────────────────────────────────╮
# │  3. ENTANGLEMENT METRICS                                    │
# ╰──────────────────────────────────────────────────────────────╯

def pairwise_corr(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    if a.size != b.size or a.size < 8:
        return 0.0
    am = a.mean()
    bm = b.mean()
    da = a - am
    db = b - bm
    denom = (np.sqrt((da*da).sum()) * np.sqrt((db*db).sum()) + 1e-12)
    return float((da*db).sum() / denom)


def compute_entanglement_matrix(dphi_map):
    names = list(dphi_map.keys())
    n = len(names)
    mat = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            if i == j:
                mat[i, j] = 1.0
            else:
                mat[i, j] = pairwise_corr(dphi_map[names[i]], dphi_map[names[j]])
    return names, mat


def entanglement_index(mat):
    n = mat.shape[0]
    if n <= 1:
        return 0.0
    vals = []
    for i in range(n):
        for j in range(i+1, n):
            vals.append(abs(mat[i, j]))
    if not vals:
        return 0.0
    return float(np.mean(vals))


def choose_entanglement_teacher(names, mat, metrics_map):
    # Teacher = channel with highest average |corr| to others
    n = len(names)
    avg_corr = []
    for i in range(n):
        vals = []
        for j in range(n):
            if i == j:
                continue
            vals.append(abs(mat[i, j]))
        if not vals:
            avg_corr.append(0.0)
        else:
            avg_corr.append(float(np.mean(vals)))

    idx = int(np.argmax(avg_corr))
    teacher_name = names[idx]
    teacher_score = avg_corr[idx]

    # Modulate alpha by curvature of teacher
    m_star = metrics_map[teacher_name]
    curv = max(m_star.curvature_proxy, 1e-6)
    alpha = 0.20 + 0.22 * min(1.0, (curv - 0.002) / 0.02)

    return teacher_name, float(alpha), float(teacher_score)


def fuse_entangled_field(channels, teacher_name, alpha):
    names = list(channels.keys())
    teacher_field = channels[teacher_name]
    fused_channels = {}
    for n in names:
        if n == teacher_name:
            fused_channels[n] = channels[n].copy()
        else:
            fused_channels[n] = (1.0 - alpha) * channels[n] + alpha * teacher_field
    stacked = np.stack([fused_channels[n] for n in names], axis=-1)
    V_ent = np.mean(stacked, axis=-1)
    return fused_channels, V_ent


# ╭──────────────────────────────────────────────────────────────╮
# │  4. VISUALS                                                 │
# ╰──────────────────────────────────────────────────────────────╯

def make_entanglement_visuals(V_ent, dphi_ent, omega_ent, names, ent_mat, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V_ent.shape
    t_mid = T // 2
    z_mid = nz // 2

    # Central Δφ slice
    central = dphi_ent[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(enhance_field(central, origin="lower"), cmap='viridis', interpolation='lanczos')
    plt.title("QIM v5.4 entangled Δφ central slice")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # Δφ max projection
    maxproj = dphi_ent.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(enhance_field(maxproj, origin="lower"), cmap='viridis', interpolation='lanczos')
    plt.title("QIM v5.4 entangled Δφ max projection")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # Ω max projection
    omega_max = omega_ent.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(enhance_field(omega_max, origin="lower"), cmap='viridis', interpolation='lanczos')
    plt.title("QIM v5.4 entangled Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    # Resonance curve
    energy_t = np.mean(np.abs(V_ent), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_ent|>")
    plt.title("QIM v5.4 entangled resonance curve")
    p_r = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_r, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_r)

    # Entanglement matrix heatmap
    fig = plt.figure()
    im = plt.imshow(enhance_field(ent_mat, vmin=-1.0, vmax=1.0, cmap="coolwarm"), cmap='viridis', interpolation='lanczos')
    plt.colorbar(im)
    plt.xticks(range(len(names)), names, rotation=45, ha="right")
    plt.yticks(range(len(names)), names)
    plt.title("QIM v5.4 Δφ entanglement matrix")
    p_e = out_dir / f"{prefix}_entanglement_matrix.png"
    fig.savefig(p_e, bbox_inches="tight")
    plt.close(fig)
    paths["entanglement_matrix"] = str(p_e)

    # Entanglement spectrum (sorted |corr|)
    vals = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            vals.append(abs(ent_mat[i, j]))
    vals = sorted(vals, reverse=True)
    fig = plt.figure()
    plt.plot(range(len(vals)), vals, marker="o")
    plt.xlabel("pair index")
    plt.ylabel("|corr(Δφ_i, Δφ_j)|")
    plt.title("QIM v5.4 entanglement spectrum")
    p_s = out_dir / f"{prefix}_entanglement_spectrum.png"
    fig.savefig(p_s, bbox_inches="tight")
    plt.close(fig)
    paths["entanglement_spectrum"] = str(p_s)

    return paths


# ╭──────────────────────────────────────────────────────────────╮
# │  5. STATE + LEDGER                                          │
# ╰──────────────────────────────────────────────────────────────╯

def write_state_ledger(root_dir: Path,
                       state_dir: Path,
                       visuals_dir: Path,
                       ledger_dir: Path,
                       V_ent,
                       dphi_ent,
                       omega_ent,
                       channels,
                       chan_metrics,
                       names,
                       ent_mat,
                       ent_index,
                       teacher_name,
                       teacher_alpha,
                       teacher_score,
                       visuals,
                       afm_mode: str,
                       spec_path: Path | None):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v5_4_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v5_4_ledger.jsonl"

    T, nx, ny, nz = V_ent.shape

    E = safe_f(np.mean(np.abs(V_ent)))
    I = safe_f(np.mean(dphi_ent))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(omega_ent))
    omega_std = safe_f(np.std(omega_ent))
    curvature_proxy = safe_f(np.mean(np.abs(dphi_ent - np.mean(dphi_ent))))

    core, shell, void = harmonic_counts(dphi_ent)
    persistence = multi_scale_persistence(dphi_ent)

    chan_dict = {name: asdict(m) for name, m in chan_metrics.items()}
    ent_rows = []
    for i, ni in enumerate(names):
        for j, nj in enumerate(names):
            ent_rows.append({
                "i": i,
                "j": j,
                "name_i": ni,
                "name_j": nj,
                "corr_dphi": float(ent_mat[i, j]),
            })

    spec_obj = None
    if spec_path is not None and spec_path.exists():
        try:
            spec_obj = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception:
            spec_obj = None

    state_obj = {
        "protocol": "CodexQIMEntanglementGeometry",
        "version": "6.0.1",
        "timestamp": now_utc_iso(),
        "mode": "afm-entanglement-crystal-sharp",
        "afm_binding_mode": afm_mode,
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
            "entanglement": {
                "index_global": ent_index,
                "teacher": teacher_name,
                "teacher_alpha": teacher_alpha,
                "teacher_score": teacher_score,
            },
        },
        "channels": chan_dict,
        "entanglement_matrix": ent_rows,
        "codex": {
            "H_layers": {
                "H7": 0.70,
                "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                "H16": "Insight / multi-scale ΔΦ structure (C_geo)",
                "H19": "Global ΔΦ integration (4D unified field → C)",
                "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                "cusp_v2_8": "λ = P/P_cr → 1-, ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|) defines deviation-weighted metric",
                "entanglement": "Cross-channel ΔΦ coherence measured by correlation matrix + index.",
            },
            "memory": {
                "node": "QIM",
                "current_version": "6.0.1",
                "previous_version": "6.0",
                "mode": "afm-entanglement-crystal-sharp",
            },
        },
        "visuals": visuals,
        "autogen_spec_v5_4": spec_obj,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "afm-entanglement-crystal-sharp",
        "state_file": str(state_path),
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
        "entanglement_index_global": ent_index,
        "teacher": teacher_name,
        "teacher_alpha": teacher_alpha,
        "teacher_score": teacher_score,
        "afm_binding_mode": afm_mode,
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    return state_path, ledger_path


# ╭──────────────────────────────────────────────────────────────╮
# │  6. MAIN                                                     │
# ╰──────────────────────────────────────────────────────────────╯

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
    input_dir = Path(args.input_afm_dir) if args.input_afm_dir else (root_dir / "codex" / "quantum_imaging" / "input_afm" / "v5_4")
    spec_path = Path(args.spec_path) if args.spec_path else None

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v5_4_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QIM v5.4 — Entanglement Geometry Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")
    if spec_path is not None:
        log(log_fp, f"spec_path  : {spec_path}")

    try:
        afm_base = load_real_afm_cube(input_dir, target_shape=(64, 64, 64), log_fp=log_fp)
        if afm_base is not None:
            afm_mode = "real-afm-bound"
            base3d = afm_base
            log(log_fp, "[Mode] REAL AFM entanglement binding active.")
        else:
            afm_mode = "synthetic-fallback"
            base3d = synthetic_volume(shape=(64, 64, 64), seed=541)
            log(log_fp, "[Mode] No AFM detected → synthetic AFM-style entanglement volume.")

        T = 40
        channels = synthesize_channels(base3d, T=T, log_fp=log_fp)

        metrics_map = {}
        dphi_map = {}
        for name, V in channels.items():
            m, dphi, _ = channel_metrics(name, V)
            metrics_map[name] = m
            dphi_map[name] = dphi
            log(log_fp, f"[Channel] {name}: E={m.E:.6f}, I={m.I:.6f}, C={m.C:.6f}, S={m.weight_S:.6f}")

        names, ent_mat = compute_entanglement_matrix(dphi_map)
        ent_idx = entanglement_index(ent_mat)
        teacher_name, alpha, teacher_score = choose_entanglement_teacher(names, ent_mat, metrics_map)
        log(log_fp, f"[Entanglement] Index_global={ent_idx:.6f}, Teacher={teacher_name}, alpha={alpha:.3f}, score={teacher_score:.6f}")

        fused_channels, V_ent = fuse_entangled_field(channels, teacher_name, alpha)
        dphi_ent = compute_dphi_4d(V_ent)
        omega_ent = omega_field(dphi_ent)

        visuals = make_entanglement_visuals(V_ent, dphi_ent, omega_ent, names, ent_mat, visuals_dir, "qim_v5_4_ent")

        state_path, ledger_path = write_state_ledger(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            V_ent=V_ent,
            dphi_ent=dphi_ent,
            omega_ent=omega_ent,
            channels=fused_channels,
            chan_metrics=metrics_map,
            names=names,
            ent_mat=ent_mat,
            ent_index=ent_idx,
            teacher_name=teacher_name,
            teacher_alpha=alpha,
            teacher_score=teacher_score,
            visuals=visuals,
            afm_mode=afm_mode,
            spec_path=spec_path,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, "QIM v5.4 entanglement run complete.")

    except Exception as e:
        err = "QIM v5.4 encountered an error: " + repr(e)
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



