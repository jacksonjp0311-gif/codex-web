#!/usr/bin/env python3
"""
QCX v10.0 — Living Quantum Crystal Engine
Atomic-scale ΔΦ kernel • 4D breathing lattice • Harmonic stability

This engine:
  • Builds a synthetic atomic crystal lattice volume
  • Evolves it in time with "solar-style" breathing modulation
  • Computes Δφ, Ω geometry, and Codex triad metrics
  • Enforces approximate 1:9:10 harmonic stability
  • Writes state JSON + ledger + v10.1 autogen spec
"""

import argparse
import json
import math
import sys
import traceback
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


# ─────────────────────────────────────────────────────────────
# 1. SYNTHETIC ATOMIC CRYSTAL LATTICE
# ─────────────────────────────────────────────────────────────

def synthetic_crystal(shape=(64, 64, 64), seed=3101):
    """
    Build a synthetic "quantum crystal" field:
      • radial shells (atomic orbitals)
      • cubic lattice modulation (crystal)
      • small random noise
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
    lattice = (
        np.cos(k * X) * np.cos(k * Y) * np.cos(k * Z)
    )

    # Slight anisotropic term to break perfect symmetry
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
# 2. VISUALS
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


def make_visuals(V, dphi, omega, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    z_mid = nz // 2

    # 1) Δφ central slice
    central = dphi[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QCX v10.0 Δφ central slice (atomic ring)")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # 2) Δφ max projection
    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QCX v10.0 Δφ max projection (crystal nodes)")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # 3) Ω max projection
    omega_max = omega.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QCX v10.0 Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    # 4) Resonance curve <|V|(t)
    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V|>")
    plt.title("QCX v10.0 resonance curve (breathing crystal)")
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
    plt.title("QCX v10.0 radial Δφ profile (shells)")
    p_rad = out_dir / f"{prefix}_radial_profile.png"
    fig.savefig(p_rad, bbox_inches="tight")
    plt.close(fig)
    paths["radial_profile"] = str(p_rad)

    # 6) Δφ histogram
    fig = plt.figure()
    plt.hist(dphi.flatten(), bins=80)
    plt.xlabel("Δφ")
    plt.ylabel("count")
    plt.title("QCX v10.0 Δφ histogram (roughness)")
    p_h = out_dir / f"{prefix}_dphi_histogram.png"
    fig.savefig(p_h, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_histogram"] = str(p_h)

    # 7) Time–radius strip
    central_t = dphi[:, :, :, z_mid]
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
    plt.title("QCX v10.0 time–radius strip (breathing shells)")
    plt.colorbar(label="⟨Δφ⟩(r,t)")
    p_tr = out_dir / f"{prefix}_time_radius_strip.png"
    fig.savefig(p_tr, bbox_inches="tight")
    plt.close(fig)
    paths["time_radius_strip"] = str(p_tr)

    return paths


# ─────────────────────────────────────────────────────────────
# 3. STATE, LEDGER, AUTOGEN SPEC
# ─────────────────────────────────────────────────────────────

def write_state_ledger_spec(root_dir: Path,
                            state_dir: Path,
                            visuals_dir: Path,
                            ledger_dir: Path,
                            V,
                            dphi,
                            omega,
                            visuals):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qcx_v10_0_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qcx_v10_0_ledger.jsonl"
    spec_path = (root_dir / "codex" / "quantum.crystal" / "v10_0" /
                 "engine" / "qcx_v10_1_autogen_spec.json")

    T, nx, ny, nz = V.shape

    E = safe_f(np.mean(np.abs(V)))
    I = safe_f(np.mean(dphi))
    dphi_global = I
    lambda_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lambda_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(omega))
    omega_std = safe_f(np.std(omega))
    curvature_proxy = safe_f(np.mean(np.abs(dphi - np.mean(dphi))))

    core, shell, void = harmonic_counts(dphi)
    persistence = multi_scale_persistence(dphi)

    state_obj = {
        "protocol": "CodexQCXLivingCrystal",
        "version": "10.0",
        "timestamp": now_utc_iso(),
        "mode": "living-crystal",
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
                "node_role": "atomic-scale Δφ kernel in multi-scale stack",
                "baseline_versions": ["QCX v9.1", "QIM v5.0"],
                "current_version": "QCX v10.0",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "living-crystal",
        "state_file": str(state_path),
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
        "source_version": "10.0",
        "next_version": "10.1",
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
        "recommendation": {
            "next_focus": (
                "Bind QCX 1× kernel more explicitly into QIM/solar/AFM stack "
                "and tune lattice parameters against real AFM data."
            ),
            "recommended_resolution": [int(nx), int(ny), int(nz)],
            "recommended_T": int(T),
        },
    }
    spec_path.write_text(json.dumps(spec_obj, indent=2), encoding="utf-8")

    return state_path, ledger_path, spec_path


# ─────────────────────────────────────────────────────────────
# 4. MAIN
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
    input_dir = Path(args.input_dir) if args.input_dir else (root_dir / "codex" / "quantum.crystal" / "v10_0" / "input_v10_0")

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qcx_v10_0_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QCX v10.0 — Living Quantum Crystal Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"input_dir  : {input_dir}")

    try:
        base3d = synthetic_crystal(shape=(64, 64, 64), seed=3101)
        T = 40

        V = build_4d_field(base3d, T=T, phase_shift=0.0, radial_mod=1.0)

        dphi = compute_dphi_4d(V)
        dphi = enforce_harmonic_stability(dphi)
        omega = omega_field(dphi)

        visuals = make_visuals(V, dphi, omega, visuals_dir, "qcx_v10_0_field")

        state_path, ledger_path, spec_path = write_state_ledger_spec(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            V=V,
            dphi=dphi,
            omega=omega,
            visuals=visuals,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, f"v10.1 autogen spec → {spec_path}")
        log(log_fp, "QCX v10.0 run complete.")

    except Exception as e:
        err = "QCX v10.0 encountered an error: " + repr(e)
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
