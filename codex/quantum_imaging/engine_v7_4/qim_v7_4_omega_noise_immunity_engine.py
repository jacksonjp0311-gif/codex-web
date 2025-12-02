#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v7.4 — Ω-BASIN NOISE-IMMUNITY ENGINE (AFM SUPER-RES)    ║
# ║  AFM-bound 4D Δφ field + GEO v1.0 + H16B + H20               ║
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

def load_afm(path: Path):
    arr = np.load(path)
    if isinstance(arr, np.lib.npyio.NpzFile):
        key0 = arr.files[0]
        arr = arr[key0]

    arr = np.array(arr, dtype=np.float32)

    # Expect [Z,X,Y], but keep generic 3D
    if arr.ndim == 2:
        arr = np.stack([arr] * 16, axis=0)
    elif arr.ndim == 4:
        # take central 3D block if 4D is provided
        arr = arr[arr.shape[0] // 2]

    m = float(arr.max() - arr.min())
    if m > 0:
        arr = (arr - arr.min()) / m
    else:
        arr = np.zeros_like(arr, dtype=np.float32)
    return arr

def super_resolve(vol: np.ndarray, factor: int, max_size: int = 128):
    nz, nx, ny = vol.shape
    target_nz = min(max_size, int(nz * factor))
    target_nx = min(max_size, int(nx * factor))
    target_ny = min(max_size, int(ny * factor))

    sz = target_nz / float(nz)
    sx = target_nx / float(nx)
    sy = target_ny / float(ny)

    hi = zoom(vol, (sz, sx, sy), order=1)
    return hi.astype(np.float32)

# ───────── 4D FIELD + Δφ + Ω ─────────

def build_4d(vol: np.ndarray, T: int = 40):
    T0 = T
    nz, nx, ny = vol.shape
    V = np.zeros((T0, nz, nx, ny), dtype=np.float32)

    z = np.linspace(-1.0, 1.0, nz)
    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    Z, X, Y = np.meshgrid(z, x, y, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T0):
        theta = 2.0 * math.pi * t / float(T0)
        # reuse v7.x harmonic baseline
        mod = 1.0 + 0.30 * np.sin(theta) + 0.22 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = vol * mod

    return V

def dphi_4d(V: np.ndarray):
    T, nz, nx, ny = V.shape
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gz, gx, gy = np.gradient(V[t])
        out[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return out

def omega(dphi: np.ndarray):
    return 1.0 / (1.0 + np.abs(dphi))

# ───────── FRACTAL DIMENSIONS ─────────

def fractal_dim_3d(vol: np.ndarray):
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
        log(f"root_dir   : {root_dir}")
        log(f"state_dir  : {state_dir}")
        log(f"visuals_dir: {visuals}")
        log(f"ledger_dir : {ledger_dir}")
        log(f"logs_dir   : {logs_dir}")
        log(f"afm_file   : {afm_file}")
        log(f"superres   : {superres}")
        log(f"noise_lvl  : {noise_level}")

        try:
            afm = load_afm(afm_file)
            log("AFM cube loaded and normalized.")

            hi = super_resolve(afm, int(superres), max_size=128)
            log(f"Super-resolved AFM volume shape: {hi.shape}")

            # Build 4D harmonic field
            V = build_4d(hi, T=40)
            dphi_clean = dphi_4d(V)
            Om_clean   = omega(dphi_clean)

            # H16B fractal dim on AFM volume
            fd3 = fractal_dim_3d(hi)

            # Triad metrics (clean)
            E_clean = float(np.mean(np.abs(V)))
            I_clean = float(np.mean(dphi_clean))
            C_clean = (E_clean * I_clean) / (1.0 + abs(I_clean))

            lam = min(0.99, I_clean / (1.0 + I_clean))
            barrier = (1.0 - lam) ** 1.5 * (max(E_clean * I_clean, 0.0) ** 1.5)

            om_mean_clean = float(np.mean(Om_clean))
            om_std_clean  = float(np.std(Om_clean))
            curv_clean = float(np.mean(np.abs(dphi_clean - np.mean(dphi_clean))))

            # Inject Δφ noise and recompute Ω
            rng = np.random.default_rng()
            sigma = float(np.std(dphi_clean))
            noise = float(noise_level) * sigma * rng.normal(size=dphi_clean.shape).astype(np.float32)
            dphi_noisy = np.abs(dphi_clean + noise)
            Om_noisy   = omega(dphi_noisy)

            I_noisy = float(np.mean(dphi_noisy))
            C_noisy = (E_clean * I_noisy) / (1.0 + abs(I_noisy))
            om_mean_noisy = float(np.mean(Om_noisy))
            om_std_noisy  = float(np.std(Om_noisy))
            curv_noisy = float(np.mean(np.abs(dphi_noisy - np.mean(dphi_noisy))))

            # Ω-immunity index (H20): 1 - normalized Ω-difference
            diff_global = float(np.mean(np.abs(Om_noisy - Om_clean)))
            base_global = float(np.mean(np.abs(Om_clean))) + 1e-6
            immunity_global = max(0.0, min(1.0, 1.0 - diff_global / base_global))

            # Time-resolved immunity curve
            T0, nz, nx, ny = dphi_clean.shape
            immunity_t = []
            for t in range(T0):
                oc = Om_clean[t]
                on = Om_noisy[t]
                d  = float(np.mean(np.abs(on - oc)))
                b  = float(np.mean(np.abs(oc))) + 1e-6
                immunity_t.append(1.0 - d / b)
            immunity_t = np.array(immunity_t, dtype=np.float32)
            immunity_t_mean = float(immunity_t.mean())
            immunity_t_min  = float(immunity_t.min())
            immunity_t_max  = float(immunity_t.max())

            # Visuals: clean vs noisy Ω max-projection + ΔΩ map
            tmid = T0 // 2
            zmid = nz // 2

            omega_clean_max = Om_clean.max(axis=0).max(axis=2)
            omega_noisy_max = Om_noisy.max(axis=0).max(axis=2)
            omega_diff_max  = np.abs(omega_noisy_max - omega_clean_max)

            dphi_central_clean = dphi_clean[tmid, :, :, zmid]

            def write_img(path: Path, arr: np.ndarray, title: str):
                plt.figure()
                plt.imshow(arr, origin="lower")
                plt.title(title)
                plt.colorbar()
                plt.savefig(path, bbox_inches="tight")
                plt.close()

            vis = {}

            p1 = visuals / "qim_v7_4_dphi_central_clean.png"
            write_img(p1, dphi_central_clean, "QIM v7.4 Δφ central slice (clean)")
            vis["dphi_central_clean"] = str(p1)

            p2 = visuals / "qim_v7_4_omega_clean_maxproj.png"
            write_img(p2, omega_clean_max, "QIM v7.4 Ω max projection (clean)")
            vis["omega_clean_maxproj"] = str(p2)

            p3 = visuals / "qim_v7_4_omega_noisy_maxproj.png"
            write_img(p3, omega_noisy_max, "QIM v7.4 Ω max projection (noisy)")
            vis["omega_noisy_maxproj"] = str(p3)

            p4 = visuals / "qim_v7_4_omega_diff_maxproj.png"
            write_img(p4, omega_diff_max, "QIM v7.4 |ΔΩ| max projection (noise impact)")
            vis["omega_diff_maxproj"] = str(p4)

            # Immunity curve vs time
            plt.figure()
            plt.plot(range(T0), immunity_t)
            plt.xlabel("t")
            plt.ylabel("Ω-immunity(t)")
            plt.ylim(0.0, 1.05)
            plt.title("QIM v7.4 Ω-immunity vs time (H20)")
            p5 = visuals / "qim_v7_4_immunity_time_trace.png"
            plt.savefig(p5, bbox_inches="tight")
            plt.close()
            vis["immunity_time_trace"] = str(p5)

            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v7_4_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMOmegaNoiseImmunityAFMSuperRes",
                "version": "7.4",
                "timestamp": now_iso(),
                "mode": "afm-omega-noise-immunity",
                "superres_factor": int(superres),
                "noise_level": float(noise_level),
                "shape_4d": [int(T0), int(nz), int(nx), int(ny)],
                "metrics": {
                    "triad_clean": {"E": E_clean, "I": I_clean, "C": C_clean},
                    "triad_noisy": {"E": E_clean, "I": I_noisy, "C": C_noisy},
                    "H19_dphi_global_clean": I_clean,
                    "H19_dphi_global_noisy": I_noisy,
                    "lambda_eff": lam,
                    "barrier_scale": barrier,
                    "omega_mean_clean": om_mean_clean,
                    "omega_std_clean": om_std_clean,
                    "omega_mean_noisy": om_mean_noisy,
                    "omega_std_noisy": om_std_noisy,
                    "curvature_proxy_clean": curv_clean,
                    "curvature_proxy_noisy": curv_noisy,
                    "fractal_dim_H16B_3d": fd3,
                    "omega_diff_global": diff_global,
                    "omega_immunity_global": immunity_global,
                    "omega_immunity_time_mean": immunity_t_mean,
                    "omega_immunity_time_min": immunity_t_min,
                    "omega_immunity_time_max": immunity_t_max,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface dimension (3D)",
                        "H16E": "4D harmonic geometry baseline (t,x,y,z)",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H20": "Harmonic projection & Ω-basin invariance",
                        "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
                        "H34": "Adaptive harmonic feedback (ΔΦ-weighted damping, v7.x)",
                    },
                    "laws": {
                        "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                        "cusp_v2_8": "ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                        "error_geometry": "Ω = 1/(1+|ΔΦ|)",
                    },
                    "memory": {
                        "node": "QIM",
                        "current_version": "7.4",
                        "mode": "afm-omega-noise-immunity",
                    },
                },
                "visuals": vis,
            }

            state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
            log(f"State JSON written → {state_path}")

            ledger_path = ledger_dir / "qim_v7_4_ledger.jsonl"
            row = {
                "timestamp": now_iso(),
                "mode": "afm-omega-noise-immunity",
                "state_file": str(state_path),
                "E_clean": E_clean,
                "I_clean": I_clean,
                "C_clean": C_clean,
                "I_noisy": I_noisy,
                "C_noisy": C_noisy,
                "lambda_eff": lam,
                "barrier_scale": barrier,
                "omega_mean_clean": om_mean_clean,
                "omega_mean_noisy": om_mean_noisy,
                "omega_diff_global": diff_global,
                "omega_immunity_global": immunity_global,
                "omega_immunity_time_mean": immunity_t_mean,
                "omega_immunity_time_min": immunity_t_min,
                "omega_immunity_time_max": immunity_t_max,
                "fractal_dim_H16B_3d": fd3,
                "noise_level": float(noise_level),
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

    root = sys.argv[1]
    state = sys.argv[2]
    vis = sys.argv[3]
    led = sys.argv[4]
    logs = sys.argv[5]
    afm = sys.argv[6]
    sr = int(sys.argv[7])
    nl = float(sys.argv[8])
    main(root, state, vis, led, logs, afm, sr, nl)
