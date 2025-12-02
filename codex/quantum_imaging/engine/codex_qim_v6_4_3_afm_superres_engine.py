#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.4.3 — AFM SUPER-RES ENTANGLEMENT ENGINE              ║
# ║  AFM Δφ super-resolution + GEO v1.0 + Cusp v2.8 metrics      ║
# ╚══════════════════════════════════════════════════════════════╝

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


# ──────────────────────────────────────────────────────────────
# 0) SMALL UTILITIES
# ──────────────────────────────────────────────────────────────

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


def box_counting_dim(slice2d):
    # Very lightweight box-counting proxy
    binary = slice2d > slice2d.mean()
    dims = []
    sizes = [2, 4, 8, 16, 32]
    h, w = binary.shape
    for s in sizes:
        if h < s or w < s:
            continue
        hh = h // s
        ww = w // s
        trimmed = binary[:hh*s, :ww*s]
        blocks = trimmed.reshape(hh, s, ww, s).sum(axis=(1, 3))
        dims.append((s, np.count_nonzero(blocks)))
    if len(dims) < 2:
        return 0.0
    xs = np.log([x[0] for x in dims])
    ys = np.log([x[1] for x in dims])
    p = np.polyfit(xs, ys, 1)
    return float(-p[0])


# ──────────────────────────────────────────────────────────────
# 1) AFM BINDING + SYNTHETIC FALLBACK
# ──────────────────────────────────────────────────────────────

def load_afm_cubes(path: Path):
    files = list(path.glob("*.npy")) + list(path.glob("*.npz"))
    if not files:
        return None
    vols = []
    for f in files:
        arr = np.load(f)
        if isinstance(arr, np.lib.npyio.NpzFile):
            for k in arr.files:
                vols.append(np.array(arr[k], dtype=np.float32))
        else:
            vols.append(np.array(arr, dtype=np.float32))
    return vols


def normalize_volume(vol):
    vol = np.array(vol, dtype=np.float32)
    vmin = float(vol.min())
    vmax = float(vol.max())
    if vmax <= vmin + 1e-9:
        return np.zeros_like(vol, dtype=np.float32)
    return (vol - vmin) / (vmax - vmin)


def synthetic_afm_like(shape=(64, 64, 64), seed=777):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    base = np.exp(-2.3 * R) * (1.0 + 0.4 * np.sin(5.0 * R))
    peaks = np.zeros_like(base)

    centers = [
        (0.0, 0.0, 0.0),
        (0.6, 0.2, -0.4),
        (-0.5, 0.5, 0.3),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx)**2 + (Y - cy)**2 + (Z - cz)**2)
        peaks += np.exp(-36.0 * Rp*Rp)

    vol = base + 0.8 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return normalize_volume(vol)


def build_4d_superres_field(base3d, T=40, superres_factor=12):
    nx, ny, nz = base3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    # Sharp mask around high AFM heights
    sharp = np.exp(-((base3d - 0.75)**2) / (2.0 * (0.08**2)))

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        phase = 0.12 * math.sin(theta)
        ripple = 0.08 * np.sin(superres_factor * R + 2.3 * theta)
        V[t] = base3d + phase * sharp + ripple

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


# ──────────────────────────────────────────────────────────────
# 2) VISUALS
# ──────────────────────────────────────────────────────────────

def make_visuals(V, dphi, omega, out_dir: Path, prefix: str, log_fp=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    if not MATPLOTLIB_OK:
        log(log_fp, "[Visuals] Matplotlib not available — skipping PNG generation.")
        return paths

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    z_mid = nz // 2

    # Δφ central slice
    central = dphi[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QIM v6.4.3 AFM Δφ central slice")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    fig.savefig(p_c, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # Δφ max projection
    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QIM v6.4.3 AFM Δφ max projection")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(p_m, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # Ω max projection
    omega_max = omega.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(omega_max, origin="lower")
    plt.title("QIM v6.4.3 AFM Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    fig.savefig(p_o, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    # Resonance curve
    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("<|V_afm|>")
    plt.title("QIM v6.4.3 AFM resonance curve")
    p_r = out_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(p_r, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(p_r)

    return paths


# ──────────────────────────────────────────────────────────────
# 3) STATE + LEDGER
# ──────────────────────────────────────────────────────────────

def write_state_ledger(root_dir: Path,
                       state_dir: Path,
                       visuals_dir: Path,
                       ledger_dir: Path,
                       V,
                       dphi,
                       omega,
                       afm_mode: str,
                       superres_factor: int,
                       visuals: dict):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    T, nx, ny, nz = V.shape

    E = safe_f(np.mean(np.abs(V)))
    I = safe_f(np.mean(dphi))
    dphi_global = I
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C = (E * I) / (1.0 + abs(dphi_global))

    omega_mean = safe_f(np.mean(omega))
    omega_std = safe_f(np.std(omega))
    curvature_proxy = safe_f(np.mean(np.abs(dphi - np.mean(dphi))))

    core, shell, void = harmonic_counts(dphi)
    persistence = multi_scale_persistence(dphi)

    frac_dim = 0.0
    central = dphi[T//2, :, :, nz//2]
    frac_dim = box_counting_dim(central)

    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v6_4_3_state_{ts_tag}.json"
    ledger_path = ledger_dir / "qim_v6_4_3_ledger.jsonl"

    state_obj = {
        "protocol": "CodexQIMAFMSuperRes",
        "version": "6.4.3",
        "timestamp": now_utc_iso(),
        "mode": "afm-superres",
        "afm_binding_mode": afm_mode,
        "superres_factor": int(superres_factor),
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
            "fractal_dim_H16B": frac_dim,
        },
        "codex": {
            "H_layers": {
                "H7": 0.70,
                "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                "H16": "Insight geometry / C_geo",
                "H16B": "Fractal AFM surface dimension",
                "H19": "Global ΔΦ integration (4D AFM field → C)",
                "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                "cusp_v2_8": "λ = P/P_cr → 1-, ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                "error_geometry": "Ω = 1/(1+|ΔΦ|)",
            },
            "memory": {
                "node": "QIM",
                "current_version": "6.4.3",
                "mode": "afm-superres",
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": now_utc_iso(),
        "mode": "afm-superres",
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
        "fractal_dim_H16B": frac_dim,
        "afm_binding_mode": afm_mode,
        "superres_factor": int(superres_factor),
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    return state_path, ledger_path


# ──────────────────────────────────────────────────────────────
# 4) MAIN
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir",        required=True)
    parser.add_argument("--state_dir",       required=True)
    parser.add_argument("--visuals_dir",     required=True)
    parser.add_argument("--ledger_dir",      required=True)
    parser.add_argument("--logs_dir",        required=False)
    parser.add_argument("--afm_dir",         required=True)
    parser.add_argument("--superres_factor", type=int, default=12)
    args = parser.parse_args()

    root_dir   = Path(args.root_dir)
    state_dir  = Path(args.state_dir)
    visuals_dir= Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir   = Path(args.logs_dir) if args.logs_dir else None
    afm_dir    = Path(args.afm_dir)
    superres_factor = int(args.superres_factor)

    log_fp = None
    try:
        if logs_dir is not None:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_path = logs_dir / f"qim_v6_4_3_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            log_fp = log_path.open("w", encoding="utf-8")
    except Exception:
        log_fp = None

    log(log_fp, "QIM v6.4.3 — AFM Super-Res Entanglement Engine starting…")
    log(log_fp, f"root_dir   : {root_dir}")
    log(log_fp, f"state_dir  : {state_dir}")
    log(log_fp, f"visuals_dir: {visuals_dir}")
    log(log_fp, f"ledger_dir : {ledger_dir}")
    log(log_fp, f"logs_dir   : {logs_dir}")
    log(log_fp, f"afm_dir    : {afm_dir}")
    log(log_fp, f"superres_factor: {superres_factor}")

    try:
        vols = load_afm_cubes(afm_dir)
        if vols is not None and len(vols) > 0:
            base = normalize_volume(np.mean(np.stack(vols, axis=0), axis=0))
            afm_mode = "real-afm-bound"
            log(log_fp, f"[AFM] Loaded {len(vols)} AFM cube(s) from nc_afm_standard.")
        else:
            base = synthetic_afm_like(shape=(64, 64, 64), seed=777)
            afm_mode = "synthetic-fallback"
            log(log_fp, "[AFM] No AFM cubes found → synthetic AFM-style fallback.")

        V = build_4d_superres_field(base, T=40, superres_factor=superres_factor)
        dphi = compute_dphi_4d(V)
        omega = omega_field(dphi)

        visuals = make_visuals(V, dphi, omega, visuals_dir, "qim_v6_4_3_afm", log_fp=log_fp)

        state_path, ledger_path = write_state_ledger(
            root_dir=root_dir,
            state_dir=state_dir,
            visuals_dir=visuals_dir,
            ledger_dir=ledger_dir,
            V=V,
            dphi=dphi,
            omega=omega,
            afm_mode=afm_mode,
            superres_factor=superres_factor,
            visuals=visuals,
        )

        log(log_fp, f"State JSON written → {state_path}")
        log(log_fp, f"Ledger appended   → {ledger_path}")
        log(log_fp, "QIM v6.4.3 AFM super-res run complete.")
    except Exception as e:
        err = "QIM v6.4.3 encountered an error: " + repr(e)
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
