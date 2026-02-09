#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v7.4 — Ω-BASIN NOISE-IMMUNITY ENGINE (AFM SUPER-RES)    ║
# ║  AFM-bound 4D Δφ field + GEO v1.0 + H16B + H16E + H20        ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ───────── AFM LOAD + SUPER-RESOLVE ─────────

def load_afm(path: Path) -> np.ndarray:
    arr = np.load(path)
    if isinstance(arr, np.lib.npyio.NpzFile):
        key0 = arr.files[0]
        arr = arr[key0]

    arr = np.array(arr, dtype=np.float32)

    # Accept [X,Y], [Z,X,Y], or [T,Z,X,Y] styles
    if arr.ndim == 2:
        arr = np.stack([arr] * 64, axis=-1)   # [X,Y] → [X,Y,Z]
    elif arr.ndim == 3:
        # already [X,Y,Z] or [Z,X,Y]; assume (X,Y,Z)
        pass
    elif arr.ndim == 4:
        # collapse time dimension → central snapshot
        arr = arr[arr.shape[0] // 2]

    m = float(arr.max() - arr.min())
    if m > 0:
        arr = (arr - arr.min()) / m
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

    # radial coordinate for harmonic weighting
    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T0):
        theta = 2.0 * math.pi * t / float(T0)
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
        log(f"root_dir     : {root_dir}")
        log(f"state_dir    : {state_dir}")
        log(f"visuals_dir  : {visuals}")
        log(f"ledger_dir   : {ledger_dir}")
        log(f"logs_dir     : {logs_dir}")
        log(f"afm_file     : {afm_file}")
        log(f"superres     : {superres}")
        log(f"noise_level  : {noise_level}")

        try:
            # 1) Load & super-resolve AFM volume
            afm = load_afm(afm_file)
            log("AFM cube loaded and normalized.")

            hi = super_resolve(afm, int(superres), max_size=128)
            log(f"Super-resolved AFM volume shape: {hi.shape}")

            # 2) Build baseline 4D field and Δφ, Ω
            V = build_4d(hi, T=40)
            dphi = dphi_4d(V)
            Om   = omega(dphi)

            # 3) Inject Δφ noise (H20) and compute perturbed Ω
            dphi_std = float(np.std(dphi))
            sigma = float(noise_level) * max(dphi_std, 1e-6)
            log(f"Δφ std        : {dphi_std:.6g}")
            log(f"noise sigma    : {sigma:.6g}")

            noise = np.random.normal(loc=0.0, scale=sigma, size=dphi.shape).astype(np.float32)
            dphi_noisy = dphi + noise
            Om_noisy   = omega(dphi_noisy)

            # 4) Fractal metrics
            fd3 = fractal_dim_3d(hi)
            fd4 = fractal_dim_4d(dphi)

            T0 = V.shape[0]
            fd_t = []
            for t in range(T0):
                fd_t.append(fractal_dim_3d(dphi[t]))
            fd_t = np.array(fd_t, dtype=np.float32)
            fd_t_mean = float(fd_t.mean())
            fd_t_min  = float(fd_t.min())
            fd_t_max  = float(fd_t.max())

            # 5) Triad + cusp-like metrics
            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam) ** 1.5 * (max(E * I, 0.0) ** 1.5)

            om_mean_before = float(np.mean(Om))
            om_std_before  = float(np.std(Om))
            om_mean_after  = float(np.mean(Om_noisy))
            om_std_after   = float(np.std(Om_noisy))

            # Ω-basin noise-immunity metrics (H20)
            delta_omega_mean = om_mean_before - om_mean_after
            omega_diff = np.mean(np.abs(Om_noisy - Om))
            # higher immunity → smaller drop / smaller diff
            noise_immunity_index = 1.0 / (1.0 + max(0.0, omega_diff))
            basin_drop_index     = 1.0 / (1.0 + max(0.0, delta_omega_mean))

            curv = float(np.mean(np.abs(dphi - np.mean(dphi))))

            # Visual slices (baseline vs noise)
            T0, nx, ny, nz = V.shape
            tmid = T0 // 2
            zmid = nz // 2

            dphi_c       = dphi[tmid, :, :, zmid]
            dphi_c_noisy = dphi_noisy[tmid, :, :, zmid]

            maxp        = dphi.max(axis=0).max(axis=2)
            maxp_noisy  = dphi_noisy.max(axis=0).max(axis=2)

            omega_max       = Om.max(axis=0).max(axis=2)
            omega_max_noisy = Om_noisy.max(axis=0).max(axis=2)

            vis = {}

            p1 = visuals / "qim_v7_4_dphi_central_baseline.png"
            write_img(p1, dphi_c, "QIM v7.4 Δφ central slice (baseline)")
            vis["dphi_central_baseline"] = str(p1)

            p2 = visuals / "qim_v7_4_dphi_central_noisy.png"
            write_img(p2, dphi_c_noisy, "QIM v7.4 Δφ central slice (noisy)")
            vis["dphi_central_noisy"] = str(p2)

            p3 = visuals / "qim_v7_4_dphi_maxproj_baseline.png"
            write_img(p3, maxp, "QIM v7.4 Δφ max projection (baseline)")
            vis["dphi_maxproj_baseline"] = str(p3)

            p4 = visuals / "qim_v7_4_dphi_maxproj_noisy.png"
            write_img(p4, maxp_noisy, "QIM v7.4 Δφ max projection (noisy)")
            vis["dphi_maxproj_noisy"] = str(p4)

            p5 = visuals / "qim_v7_4_omega_maxproj_baseline.png"
            write_img(p5, omega_max, "QIM v7.4 Ω max projection (baseline)")
            vis["omega_maxproj_baseline"] = str(p5)

            p6 = visuals / "qim_v7_4_omega_maxproj_noisy.png"
            write_img(p6, omega_max_noisy, "QIM v7.4 Ω max projection (noisy)")
            vis["omega_maxproj_noisy"] = str(p6)

            # Ω-basin noise-immunity curve (energy vs Ω)
            energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
            omega_t  = np.mean(omega(dphi), axis=(1, 2, 3))
            omega_t_noisy = np.mean(omega(dphi_noisy), axis=(1, 2, 3))

            plt.figure()
            plt.plot(range(T0), omega_t, label="Ω baseline")
            plt.plot(range(T0), omega_t_noisy, label="Ω noisy", linestyle="--")
            plt.xlabel("t")
            plt.ylabel("Ω(t)")
            plt.title("QIM v7.4 Ω-basin noise-immunity (baseline vs noisy)")
            plt.legend()
            p7 = visuals / "qim_v7_4_omega_time_noise_immunity.png"
            plt.savefig(p7, bbox_inches="tight")
            plt.close()
            vis["omega_time_noise_immunity"] = str(p7)

            # fractal vs time trace (3D |Δφ_t|)
            plt.figure()
            plt.plot(range(T0), fd_t)
            plt.xlabel("t")
            plt.ylabel("D_fractal(3D |Δφ_t|)")
            plt.title("QIM v7.4 3D fractal dimension vs time (baseline)")
            p8 = visuals / "qim_v7_4_fractal_time_trace.png"
            plt.savefig(p8, bbox_inches="tight")
            plt.close()
            vis["fractal_time_trace"] = str(p8)

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
                    "omega_mean_before": om_mean_before,
                    "omega_std_before": om_std_before,
                    "omega_mean_after": om_mean_after,
                    "omega_std_after": om_std_after,
                    "delta_omega_mean": float(delta_omega_mean),
                    "omega_diff_L1": float(omega_diff),
                    "noise_immunity_index": float(noise_immunity_index),
                    "basin_drop_index": float(basin_drop_index),
                    "curvature_proxy": curv,
                    "fractal_dim_H16B_3d": fd3,
                    "fractal_dim_H16E_4d": fd4,
                    "fractal_time_mean": fd_t_mean,
                    "fractal_time_min": fd_t_min,
                    "fractal_time_max": fd_t_max,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM geometry (3D)",
                        "H16E": "4D harmonic baseline (t,x,y,z)",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H20": "Ω-basin invariance / noise-immunity",
                        "H31": "Harmonic stability (core:shell:void ≈ 1:9:10)",
                        "H34": "Adaptive harmonic feedback (future v7.x)",
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
                "omega_mean_before": om_mean_before,
                "omega_std_before": om_std_before,
                "omega_mean_after": om_mean_after,
                "omega_std_after": om_std_after,
                "delta_omega_mean": float(delta_omega_mean),
                "omega_diff_L1": float(omega_diff),
                "noise_immunity_index": float(noise_immunity_index),
                "basin_drop_index": float(basin_drop_index),
                "fractal_dim_H16B_3d": fd3,
                "fractal_dim_H16E_4d": fd4,
                "fractal_time_mean": fd_t_mean,
                "fractal_time_min": fd_t_min,
                "fractal_time_max": fd_t_max,
                "superres_factor": int(superres),
                "noise_level": float(noise_level),
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

    root, state, vis, led, logs, afm, sr_s, noise_s = sys.argv[1:]
    main(root, state, vis, led, logs, afm, int(sr_s), float(noise_s))
