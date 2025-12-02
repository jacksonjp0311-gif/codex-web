#!/usr/bin/env python3
"""
QIM v7.4 — Ω-Basin Noise-Immunity Engine (AFM Super-Res)

• AFM-bound 4D Δφ field (baseline)
• GEO v1.0: Ω = 1/(1+|ΔΦ|)
• H16B: 3D fractal AFM geometry
• H16E: 4D harmonic baseline geometry
• H19: global Δφ integration → C
• H20: Ω-basin invariance / noise-immunity
• H34: adaptive harmonic feedback (Ω-weighted noise response)
"""

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom

# ───────── UTIL ─────────

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ───────── AFM LOAD + SUPER-RESOLVE ─────────

def load_afm(path: Path) -> np.ndarray:
    arr = np.load(path)
    # Handle .npz container
    if isinstance(arr, np.lib.npyio.NpzFile):
        key0 = arr.files[0]
        arr = arr[key0]

    arr = np.array(arr, dtype=np.float32)

    # Normalize shape to (nx, ny, nz)
    if arr.ndim == 2:
        # Repeat into a simple slab
        arr = np.stack([arr] * 64, axis=-1)
    elif arr.ndim == 3:
        pass
    elif arr.ndim == 4:
        # Take central time slice if 4D
        arr = arr[arr.shape[0] // 2]
    else:
        raise ValueError(f"Unsupported AFM shape: {arr.shape}")

    # Normalize to [0,1]
    mn = float(arr.min())
    mx = float(arr.max())
    if mx > mn:
        arr = (arr - mn) / (mx - mn)
    else:
        arr = np.zeros_like(arr, dtype=np.float32)
    return arr

def super_resolve(vol: np.ndarray, factor: int, max_size: int = 128) -> np.ndarray:
    nx, ny, nz = vol.shape
    target_nx = min(max_size, int(nx * factor))
    target_ny = min(max_size, int(ny * factor))
    target_nz = min(max_size, int(nz * factor))

    sx = target_nx / float(nx)
    sy = target_ny / float(ny)
    sz = target_nz / float(nz)

    hi = zoom(vol, (sx, sy, sz), order=1)
    return hi.astype(np.float32)

# ───────── 4D FIELD + Δφ + Ω ─────────

def build_4d(vol: np.ndarray, T: int = 40) -> np.ndarray:
    T0 = T
    nx, ny, nz = vol.shape
    V = np.zeros((T0, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T0):
        theta = 2.0 * math.pi * t / float(T0)
        # Harmonic breathing modulation, same family as v7.3
        mod = 1.0 + 0.30 * np.sin(theta) + 0.22 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = vol * mod

    return V

def dphi_4d(V: np.ndarray) -> np.ndarray:
    T, nx, ny, nz = V.shape
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        out[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return out

def omega(dphi: np.ndarray) -> np.ndarray:
    # GEO v1.0
    return 1.0 / (1.0 + np.abs(dphi))

# ───────── FRACTAL DIMENSIONS ─────────

def fractal_dim_3d(vol: np.ndarray) -> float:
    data = (vol > np.median(vol)).astype(np.float32)
    counts = []
    scales = [1, 2, 4, 8, 16]
    for k in scales:
        try:
            blk = data[::k, ::k, ::k]
            counts.append(float(np.sum(blk > 0)))
        except Exception:
            pass

    if len(counts) < 2:
        return 2.0

    counts = np.array(counts) + 1e-9
    ks = np.array(scales[:len(counts)], dtype=np.float32)
    logs = np.log(counts)
    invk = np.log(1.0 / ks)
    p = np.polyfit(invk, logs, 1)
    return float(abs(p[0]))

def fractal_dim_4d(vol4d: np.ndarray) -> float:
    """
    H16E 4D fractal dimension:
    box-counting over (t,x,y,z) using stride sampling.
    """
    data = (vol4d > np.median(vol4d)).astype(np.uint8)
    scales = [1, 2, 4, 5, 8]
    counts = []
    ks = []
    for k in scales:
        try:
            sub = data[::k, ::k, ::k, ::k]
            counts.append(float(sub.sum()))
            ks.append(k)
        except Exception:
            continue

    if len(counts) < 2:
        return 3.0

    counts = np.array(counts) + 1e-9
    ks = np.array(ks, dtype=np.float32)
    logs = np.log(counts)
    invk = np.log(1.0 / ks)
    p = np.polyfit(invk, logs, 1)
    return float(abs(p[0]))

def write_img(path: Path, arr: np.ndarray, title: str):
    plt.figure()
    plt.imshow(arr, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

# ───────── MAIN ENGINE ─────────

def main(root, state_d, vis_d, ledger_d, logs_d, afm_path, superres, noise_level):
    root_dir   = Path(root)
    state_dir  = Path(state_d)
    visuals    = Path(vis_d)
    ledger_dir = Path(ledger_d)
    logs_dir   = Path(logs_d)
    afm_file   = Path(afm_path)

    state_dir.mkdir(parents=True, exist_ok=True)
    visuals.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / f"qim_v7_4_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    with log_path.open("w", encoding="utf-8") as lf:
        def log(msg: str):
            line = msg.encode("ascii", "replace").decode("ascii")
            print(line)
            lf.write(line + "\n")
            lf.flush()

        log("QIM v7.4 — Ω-basin Noise-Immunity Engine starting…")
        log(f"root_dir    : {root_dir}")
        log(f"state_dir   : {state_dir}")
        log(f"visuals_dir : {visuals}")
        log(f"ledger_dir  : {ledger_dir}")
        log(f"logs_dir    : {logs_dir}")
        log(f"afm_file    : {afm_file}")
        log(f"superres    : {superres}")
        log(f"noise_level : {noise_level}")

        try:
            # AFM load + super-res
            afm = load_afm(afm_file)
            log(f"AFM cube loaded and normalized. shape={afm.shape}")

            hi = super_resolve(afm, int(superres), max_size=128)
            log(f"Super-resolved AFM volume shape: {hi.shape}")

            # 4D baseline field + Δφ + Ω
            V = build_4d(hi, T=40)
            dphi_base = dphi_4d(V)
            Om_base = omega(dphi_base)

            # H16B / H16E baseline
            fd3 = fractal_dim_3d(hi)
            fd4 = fractal_dim_4d(dphi_base)

            # time-resolved 3D fractal dims on |Δφ(t,·)|
            T0 = V.shape[0]
            fd_t = []
            for t in range(T0):
                fd_t.append(fractal_dim_3d(dphi_base[t]))
            fd_t = np.array(fd_t, dtype=np.float32)
            fd_t_mean = float(fd_t.mean())
            fd_t_min  = float(fd_t.min())
            fd_t_max  = float(fd_t.max())

            # Triad metrics (baseline)
            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi_base))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam) ** 1.5 * (max(E * I, 0.0) ** 1.5)

            om_mean = float(np.mean(Om_base))
            om_std  = float(np.std(Om_base))
            curv = float(np.mean(np.abs(dphi_base - np.mean(dphi_base))))

            # ───── H20: noise injection in Δφ and Ω-basin response ─────
            sigma_dphi = float(np.std(dphi_base))
            if sigma_dphi <= 0.0:
                sigma_dphi = 1e-6

            rng = np.random.default_rng()
            noise = rng.normal(loc=0.0,
                               scale=noise_level * sigma_dphi,
                               size=dphi_base.shape).astype(np.float32)

            dphi_noisy = dphi_base + noise
            dphi_noisy = np.clip(dphi_noisy, 0.0, None)

            Om_noisy = omega(dphi_noisy)

            delta_Om = Om_noisy - Om_base
            abs_delta_Om = np.abs(delta_Om)

            mean_abs_delta_omega = float(np.mean(abs_delta_Om))
            max_abs_delta_omega  = float(np.max(abs_delta_Om))
            noise_energy         = float(np.mean(noise * noise))

            # Ω-basin stability index (H20):
            # fraction of voxels with |ΔΩ| < 0.05, smoothed via exp-kernel
            eps = 0.05
            frac_stable = float(np.mean(abs_delta_Om < eps))
            omega_basin_index = float(np.mean(np.exp(-abs_delta_Om / eps)))

            # Correlation between baseline and noisy Ω
            base_flat = Om_base.ravel()
            noisy_flat = Om_noisy.ravel()
            if np.std(base_flat) > 0 and np.std(noisy_flat) > 0:
                corr = float(np.corrcoef(base_flat, noisy_flat)[0, 1])
            else:
                corr = 1.0

            # H34: adaptive harmonic feedback metric
            # Ω-weighted noise: how much noise lands in high-Ω (coherent) regions
            weight = Om_base / (np.mean(Om_base) + 1e-9)
            adaptive_feedback = float(np.mean(weight * abs_delta_Om))

            log(f"mean|ΔΩ|   : {mean_abs_delta_omega}")
            log(f"max|ΔΩ|    : {max_abs_delta_omega}")
            log(f"Ω-basin Ix : {omega_basin_index}")
            log(f"Ω-stable f : {frac_stable}")
            log(f"Ω-corr     : {corr}")
            log(f"H34 adapt  : {adaptive_feedback}")

            # Visuals
            T0, nx, ny, nz = V.shape
            tmid = T0 // 2
            zmid = nz // 2

            # baseline / noisy Ω max projections
            omega_base_max = Om_base.max(axis=0).max(axis=2)
            omega_noisy_max = Om_noisy.max(axis=0).max(axis=2)
            delta_omega_max = abs_delta_Om.max(axis=0).max(axis=2)

            vis = {}

            p1 = visuals / "qim_v7_4_omega_baseline_maxproj.png"
            write_img(p1, omega_base_max, "QIM v7.4 Ω baseline max-projection")
            vis["omega_baseline_maxproj"] = str(p1)

            p2 = visuals / "qim_v7_4_omega_noisy_maxproj.png"
            write_img(p2, omega_noisy_max, "QIM v7.4 Ω noisy max-projection")
            vis["omega_noisy_maxproj"] = str(p2)

            p3 = visuals / "qim_v7_4_delta_omega_maxproj.png"
            write_img(p3, delta_omega_max, "QIM v7.4 |ΔΩ| max-projection")
            vis["delta_omega_maxproj"] = str(p3)

            # Noise-immunity curve: fraction(|ΔΩ| < τ) vs τ
            taus = np.linspace(0.0, 0.20, 50, dtype=np.float32)
            fracs = []
            flat_abs = abs_delta_Om.ravel()
            for tau in taus:
                fracs.append(float(np.mean(flat_abs < tau)))
            fracs = np.array(fracs, dtype=np.float32)

            plt.figure()
            plt.plot(taus, fracs)
            plt.xlabel("τ")
            plt.ylabel("fraction(|ΔΩ| < τ)")
            plt.title("QIM v7.4 Ω-basin noise-immunity curve (H20)")
            p4 = visuals / "qim_v7_4_noise_immunity_curve.png"
            plt.savefig(p4, bbox_inches="tight")
            plt.close()
            vis["omega_noise_immunity_curve"] = str(p4)

            # State JSON
            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v7_4_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMOmegaBasinAFMSuperRes",
                "version": "7.4",
                "timestamp": now_iso(),
                "mode": "afm-omega-basin-noise-immunity",
                "superres_factor": int(superres),
                "noise_level": float(noise_level),
                "shape_4d": [int(T0), int(nx), int(ny), int(nz)],
                "metrics": {
                    "triad": {"E": E, "I": I, "C": C},
                    "H19_dphi_global": I,
                    "lambda_eff": lam,
                    "barrier_scale": barrier,
                    "omega_mean": om_mean,
                    "omega_std": om_std,
                    "curvature_proxy": curv,
                    "fractal_dim_H16B_3d": fd3,
                    "fractal_dim_H16E_4d": fd4,
                    "fractal_time_mean": fd_t_mean,
                    "fractal_time_min": fd_t_min,
                    "fractal_time_max": fd_t_max,
                    "noise_energy": noise_energy,
                    "mean_abs_delta_omega": mean_abs_delta_omega,
                    "max_abs_delta_omega": max_abs_delta_omega,
                    "omega_basin_index_H20": omega_basin_index,
                    "omega_fraction_stable": frac_stable,
                    "omega_correlation": corr,
                    "adaptive_feedback_H34": adaptive_feedback,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface dimension (3D)",
                        "H16E": "4D harmonic baseline geometry (t,x,y,z)",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H20": "Ω-basin invariance / noise-immunity",
                        "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
                        "H34": "Adaptive harmonic feedback (Ω-weighted noise)",
                    },
                    "laws": {
                        "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                        "cusp_v2_8": "ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                        "error_geometry": "Ω = 1/(1+|ΔΦ|)",
                    },
                    "memory": {
                        "node": "QIM",
                        "current_version": "7.4",
                        "mode": "afm-omega-basin-noise-immunity",
                    },
                },
                "visuals": vis,
            }

            state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
            log(f"State JSON written → {state_path}")

            # Ledger append
            ledger_path = ledger_dir / "qim_v7_4_ledger.jsonl"
            row = {
                "timestamp": now_iso(),
                "mode": "afm-omega-basin-noise-immunity",
                "state_file": str(state_path),
                "E": E,
                "I": I,
                "C": C,
                "lambda_eff": lam,
                "barrier_scale": barrier,
                "omega_mean": om_mean,
                "omega_std": om_std,
                "curvature_proxy": curv,
                "fractal_dim_H16B_3d": fd3,
                "fractal_dim_H16E_4d": fd4,
                "fractal_time_mean": fd_t_mean,
                "fractal_time_min": fd_t_min,
                "fractal_time_max": fd_t_max,
                "noise_level": float(noise_level),
                "noise_energy": noise_energy,
                "mean_abs_delta_omega": mean_abs_delta_omega,
                "max_abs_delta_omega": max_abs_delta_omega,
                "omega_basin_index_H20": omega_basin_index,
                "omega_fraction_stable": frac_stable,
                "omega_correlation": corr,
                "adaptive_feedback_H34": adaptive_feedback,
                "superres_factor": int(superres),
            }
            with ledger_path.open("a", encoding="utf-8") as lf2:
                lf2.write(json.dumps(row) + "\n")
            log(f"Ledger appended → {ledger_path}")
            log("QIM v7.4 Ω-basin Noise-Immunity run complete.")

        except Exception as e:
            err = "QIM v7.4 encountered an error: " + repr(e)
            print(err, file=sys.stderr)
            lf.write(err + "\n")
            lf.write(traceback.format_exc() + "\n")
            lf.flush()
            raise

if __name__ == "__main__":
    if len(sys.argv) != 9:
        print("Usage: engine.py ROOT STATE VISUALS LEDGER LOGS AFM_FILE SUPERRES NOISE_LEVEL", file=sys.stderr)
        sys.exit(1)

    root, state, vis, led, logs, afm, sr_s, noise_s = sys.argv[1:9]
    main(root,
         state,
         vis,
         led,
         logs,
         afm,
         int(sr_s),
         float(noise_s))
