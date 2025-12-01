#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v5.1 — CROSS-MODULE INSIGHT ENGINE (TEACHER-STABILIZED) ║
# ║  Codex ΔΦ Perception Kernel (5-Channel, Curvature-Tuned)     ║
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


# ╭──────────────────────────────────────────────────────────────╮
# │  0. SMALL EMERGENT UTILITIES                                │
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
# │  1. BASE LATTICE (REAL-AWARE WITH SYNTHETIC FALLBACK)       │
# ╰──────────────────────────────────────────────────────────────╯

def synthetic_volume(shape=(64, 64, 64), seed=151):
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
        (0.6, 0.2, -0.4),
        (-0.5, 0.5, 0.3),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-30.0 * Rp*Rp)

    vol = base + 0.7 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol


def load_or_synthesize_base(input_dir: Path, log_fp=None):
    """
    Prefer real AFM-style volume if present:
      • afm_volume_v5_1.npy  (full 3D array)
    Otherwise use synthetic_volume().
    """
    candidate = input_dir / "afm_volume_v5_1.npy"
    if candidate.exists():
        try:
            arr = np.load(candidate)
            if arr.ndim == 3:
                log(log_fp, f"[Base] Loaded real AFM volume → {candidate}")
                return arr
            else:
                log(log_fp, f"[Base] AFM volume has wrong ndim={arr.ndim}, using synthetic fallback.")
        except Exception as e:
            log(log_fp, f"[Base] Failed to load AFM volume {candidate}: {repr(e)}")
    log(log_fp, "[Base] Using synthetic AFM-style volume (v5.1).")
    return synthetic_volume(shape=(64, 64, 64), seed=151)


def build_4d_field(volume3d, T=40, phase_shift=0.0, radial_mod=1.0, amp=0.30):
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
            + amp * math.sin(theta + phase_shift)
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
    # Ω = 1 / (1 + |ΔΦ|)
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
    # Emergent but simple: downsample and compare norms
    T, nx, ny, nz = dphi.shape
    norms = []

    def norm_of(slice_4d):
        return float(np.mean(np.abs(slice_4d)))

    # Scales 1,2,4,8 if possible
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
# │  2. CHANNEL SYNTHESIS (5 MODULES)                           │
# ╰──────────────────────────────────────────────────────────────╯

def synthesize_channels(base3d, T=40):
    # QIM: neutral reference
    V_qim = build_4d_field(base3d, T=T, phase_shift=0.0, radial_mod=1.0, amp=0.28)
    # Solar: slower breathing, outward emphasis
    V_solar = build_4d_field(base3d, T=T, phase_shift=0.7, radial_mod=1.3, amp=0.30)
    # QCX: sharper inner lattice modulation
    V_qcx = build_4d_field(base3d, T=T, phase_shift=1.4, radial_mod=0.8, amp=0.26)
    # Third Eye: semantic burst; slightly asymmetric
    V_third = build_4d_field(base3d * (1.0 + 0.2 * np.tanh(base3d)),
                             T=T, phase_shift=2.1, radial_mod=1.1, amp=0.30)
    # AFM: horizon-weighted surface emphasis
    V_afm = build_4d_field(base3d * (1.0 + 0.4 * (base3d > np.median(base3d))),
                           T=T, phase_shift=2.8, radial_mod=1.0, amp=0.27)

    return {
        "QIM": V_qim,
        "Solar": V_solar,
        "QCX": V_qcx,
        "ThirdEye": V_third,
        "AFM": V_afm,
    }


def channel_metrics(name, V):
    dphi = compute_dphi_4d(V)

    E = safe_f(np.mean(np.abs(V)))
    I = safe_f(np.mean(dphi))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)

    # Core triad coherence (Codex UTP)
    C = (E * I) / (1.0 + abs(dphi_global))

    Ω = omega_field(dphi)
    omega_mean = safe_f(np.mean(Ω))
    omega_std = safe_f(np.std(Ω))

    curvature_proxy = safe_f(np.mean(np.abs(dphi - np.mean(dphi))))

    persistence = multi_scale_persistence(dphi)

    core, shell, void = harmonic_counts(dphi)

    # Insight weight S = Ω * (1 - λ) * persistence
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
# │  3. DOMINANT INSIGHT FUSION (STABILIZED TEACHER)            │
# ╰──────────────────────────────────────────────────────────────╯

def dominant_fusion(channels, metrics_map, log_fp=None):
    names = list(channels.keys())
    weights = np.array([metrics_map[n].weight_S for n in names], dtype=np.float64)

    if np.all(weights <= 0):
        teacher_idx = names.index("QIM")
    else:
        teacher_idx = int(np.argmax(weights))

    teacher_name = names[teacher_idx]
    teacher_field = channels[teacher_name]

    # α based on teacher curvature: smoother mapping, capped lower
    m_star = metrics_map[teacher_name]
    curv = max(m_star.curvature_proxy, 1e-6)
    # v5.1: keep α in [0.10, 0.32] for more stable teaching
    alpha_raw = (curv - 0.002) / 0.02
    alpha_clamped = min(1.0, max(0.0, alpha_raw))
    alpha = 0.10 + 0.22 * alpha_clamped

    if log_fp is not None:
        log(log_fp, f"[Dominant] Teacher channel → {teacher_name} (S={m_star.weight_S:.6f}, α={alpha:.3f}, curv={curv:.6f})")

    fused_channels = {}
    for n in names:
        if n == teacher_name:
            fused_channels[n] = channels[n].copy()
        else:
            fused_channels[n] = (1.0 - alpha) * channels[n] + alpha * teacher_field

    stacked = np.stack([fused_channels[n] for n in names], axis=-1)
    V_unified = np.mean(stacked, axis=-1)

    return teacher_name, float(alpha), fused_channels, V_unified


def enforce_harmonic_stability(dphi):
    # Nudge 1:9:10 if we are far away
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
        return dphi  # close enough

    vals = dphi
    pos = vals[vals > 0.0]
    if pos.size == 0:
        return dphi
    p95 = float(np.percentile(pos, 95.0))
    p50 = float(np.percentile(pos, 50.0))

    high_mask = (vals >= p95)
    mid_mask = ((vals < p95) & (vals >= p50))
    low_mask = (vals < p50)

    vals = vals.copy()
    vals[high_mask] *= 1.015
    vals[mid_mask] *= 0.992
    vals[low_mask] *= 0.985
    return vals


# ╭──────────────────────────────────────────────────────────────╮
# │  4. VISUALS                                                 │
# ╰──────────────────────────────────────────────────────────────╯

def make_visuals(V_unified, dphi_unified, omega_unified, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V_unified.shape
    t_mid = T // 2
    z_mid = nz // 2

    # Δφ central slice
    central = dphi_unified[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QIM v5.1 unified dphi central slice")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # Δφ max projection
    maxproj = dphi_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QIM v5.1 unified dphi max projection")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # Ω max projection
    omega_max = omega_unified.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QIM v5.1 unified omega max projection")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    # Resonance curve
    energy_t = np.mean(np.abs(V_unified), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_unified|>")
    plt.title("QIM v5.1 cross-module resonance curve")
    p_r = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_r, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_r)

    return paths


# ╭──────────────────────────────────────────────────────────────╮
# │  5. STATE, LEDGER, AUTOGEN SPEC                             │
# ╰──────────────────────────────────────────────────────────────╯

def write_state_ledger_spec(root_dir: Path,
                            state_dir: Path,
                            visuals_dir: Path,
                            ledger_dir: Path,
                            logs_dir: Path,
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
    state_path = state_dir / f"qim_v5_1_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v5_1_ledger.jsonl"
    spec_path = (root_dir / "codex" / "quantum_imaging" / "engine" / "codex_qim_v5_2_autogen_spec.json")

    T, nx, ny, nz = V_unified.shape

    # Global triad metrics
    E = safe_f(np.mean(np.abs(V_unified)))
    I = safe_f(np.mean(dphi_unified))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    # Error geometry
    omega_mean = safe_f(np.mean(omega_unified))
    omega_std = safe_f(np.std(omega_unified))
    curvature_proxy = safe_f(np.mean(np.abs(dphi_unified - np.mean(dphi_unified))))

    # Harmonics after enforcement
    core, shell, void = harmonic_counts(dphi_unified)

    # Multi-scale persistence for unified
    persistence = multi_scale_persistence(dphi_unified)

    chan_dict = {name: asdict(m) for name, m in chan_metrics.items()}

    state_obj = {
        "protocol": "CodexQIMCrossModuleInsight",
        "version": "5.1",
        "timestamp": now_utc_iso(),
        "mode": "teacher_stabilized",
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": {
                "E": E,
                "I": I,
                "C": C,
            },
            "H19_dphi_global": dphi_global,
            "lambda_eff": lam_eff,
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
            "H_layers": {
                "H7": 0.70,
                "H16": "Insight / pattern geometry (C_geo, cross-module)",
                "H19": "Global dphi integration (4D unified field → C)",
                "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                "cusp_v2_8": "λ = P/P_cr → 1-, ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|) defines deviation-weighted metric",
                "harmonic_stability": "Stable imaging fields exhibit core:shell:void ≈ 1:9:10",
            },
            "memory": {
                "node": "QIM",
                "baseline_version": "5.0",
                "current_version": "5.1",
                "mode": "cross-module-teacher-stabilized",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "teacher_stabilized",
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
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    spec_obj = {
        "protocol": "QIMAutoGenSpec",
        "source_version": "5.1",
        "next_version": "5.2",
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
        },
        "fusion": {
            "teacher": teacher_name,
            "alpha_teach": alpha,
            "channels": list(chan_metrics.keys()),
        },
        "recommendation": {
            "recommended_resolution": [int(nx), int(ny), int(nz)],
            "recommended_T": int(T),
            "next_focus": "stabilize cross-run teacher identity, ingest real Solar/QCX/ThirdEye fields when available, and tune Ω-curvature jointly across channels.",
        },
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ╭──────────────────────────────────────────────────────────────╮
# │  6. MAIN                                                    │
# ╰──────────────────────────────────────────────────────────────╯

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
    input_dir = Path(args.input_afm_dir) if args.input_afm_dir else (root_dir / "codex" / "quantum_imaging" / "input_afm" / "v5_1")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v5_1_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QIM v5.1 — Cross-Module Insight Engine (Teacher-Stabilized) starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")

    try:
        base3d = load_or_synthesize_base(input_dir, log_fp=log_fp)
        T = 40

        channels = synthesize_channels(base3d, T=T)

        metrics_map = {}
        for name, V in channels.items():
            m, dphi, Ω = channel_metrics(name, V)
            metrics_map[name] = m
            log(log_fp, f"[Channel] {name}: E={m.E:.6f}, I={m.I:.6f}, C={m.C:.6f}, S={m.weight_S:.6f}")

        teacher_name, alpha, fused_channels, V_unified = dominant_fusion(channels, metrics_map, log_fp=log_fp)

        dphi_unified = compute_dphi_4d(V_unified)
        dphi_unified = enforce_harmonic_stability(dphi_unified)
        omega_unified = omega_field(dphi_unified)

        visuals = make_visuals(V_unified, dphi_unified, omega_unified, visuals_dir, "qim_v5_1_field")

        state_path, ledger_path, spec_path = write_state_ledger_spec(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            logs_dir=logs_dir,
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
        log(log_fp, f"v5.2 autogen spec → {spec_path}")
        log(log_fp, "QIM v5.1 run complete.")

    except Exception as e:
        err = "QIM v5.1 encountered an error: " + repr(e)
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
