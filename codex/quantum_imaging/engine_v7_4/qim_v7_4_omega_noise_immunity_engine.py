#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v7.4 — Ω-BASIN NOISE-IMMUNITY ENGINE (AFM SUPER-RES)    ║
# ║  AFM-bound 4D Δφ field + GEO v1.0 + H16B/H16E + H20          ║
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

    # ETH roughness cubes: expected [Z,X,Y] or [X,Y]
    if arr.ndim == 2:
        # stack to simple cube if given as a single height map
        arr = np.stack([arr] * 16, axis=0)
    elif arr.ndim == 4:
        # take middle time/frame if 4D
        arr = arr[arr.shape[0] // 2]

    m = float(arr.max() - arr.min())
    if m > 0:
        arr = (arr - arr.min()) / m
    else:
        arr = np.zeros_like(arr, dtype=np.float32)
    return arr

def super_resolve(vol: np.ndarray, factor: int, max_size: int = 128):
    nz, nx, ny = vol.shape  # [Z,X,Y]
    target_nz = min(max_size, int(nz * factor))
    target_nx = min(max_size, int(nx * factor))
    target_ny = min(max_size, int(ny * factor))

    sz = target_nz / float(nz)
    sx = target_nx / float(nx)
    sy = target_ny / float(ny)

    hi = zoom(vol, (sz, sx, sy), order=1)
    return hi.astype(np.float32)  # [Z',X',Y']

# ───────── 4D FIELD + Δφ + Ω ─────────

def build_4d(vol: np.ndarray, T: int = 40):
    """
    Build 4D baseline field V(t,x,y,z) from AFM cube vol[z,x,y]
    using harmonic breathing like v7.3 (for H16E continuity).
    """
    nz, nx, ny = vol.shape
    T0 = T
    V = np.zeros((T0, nz, nx, ny), dtype=np.float32)

    # radial coordinate on (x,y); z acts as layered depth
    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")
    R2 = np.sqrt(X * X + Y * Y)

    for t in range(T0):
        theta = 2.0 * math.pi * t / float(T0)
        mod = 1.0 + 0.30 * np.sin(theta) + 0.22 * np.cos(2.0 * theta + 3.0 * R2)
        # broadcast mod over z
        V[t] = vol * mod[None, :, :]

    return V  # [T,Z,X,Y]

def dphi_4d(V: np.ndarray):
    T, nz, nx, ny = V.shape
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gz, gx, gy = np.gradient(V[t])
        out[t] = np.sqrt(gz * gz + gx * gx + gy * gy)
    return out

def omega(dphi: np.ndarray):
    return 1.0 / (1.0 + np.abs(dphi))

# ───────── FRACTAL DIMENSIONS ─────────

def fractal_dim_3d(vol: np.ndarray):
    """
    Crude 3D box-counting over [Z,X,Y].
    """
    data = (vol > np.median(vol)).astype(np.float32)
    counts = []
    scales = [1, 2, 4, 8]
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

def fractal_dim_4d(vol4d: np.ndarray):
    """
    H16E-like 4D fractal dimension over [T,Z,X,Y].
    """
    data = (vol4d > np.median(vol4d)).astype(np.uint8)
    scales = [1, 2, 4]
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
            afm = load_afm(afm_file)
            log("AFM cube loaded and normalized.")

            hi = super_resolve(afm, int(superres), max_size=128)
            log(f"Super-resolved AFM volume shape: {hi.shape}")

            # Build 4D baseline field and Δφ + Ω
            V = build_4d(hi, T=40)
            dphi_base = dphi_4d(V)
            omega_base = omega(dphi_base)

            # Inject noise into Δφ field
            rng = np.random.default_rng()
            noise = rng.normal(loc=0.0, scale=float(noise_level), size=dphi_base.shape).astype(np.float32)
            dphi_noisy = dphi_base + noise
            omega_noisy = omega(dphi_noisy)

            # Triad metrics (baseline)
            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi_base))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam) ** 1.5 * (max(E * I, 0.0) ** 1.5)

            # Ω-basin stats
            om_mean_base = float(np.mean(omega_base))
            om_std_base  = float(np.std(omega_base))
            om_mean_noisy = float(np.mean(omega_noisy))
            om_std_noisy  = float(np.std(omega_noisy))

            # Correlation between Ω_base and Ω_noisy
            flat_base = omega_base.reshape(-1).astype(np.float32)
            flat_noisy = omega_noisy.reshape(-1).astype(np.float32)
            mu_b = float(flat_base.mean())
            mu_n = float(flat_noisy.mean())
            sb = float(flat_base.std() + 1e-8)
            sn = float(flat_noisy.std() + 1e-8)
            corr = float(((flat_base - mu_b) * (flat_noisy - mu_n)).mean() / (sb * sn))

            # RMS difference normalized
            rms_diff = float(np.sqrt(np.mean((flat_base - flat_noisy) ** 2)))
            norm_rms = float(rms_diff / (sb + 1e-8))

            # Define Ω-basin noise-immunity index (H20)
            omega_immunity = float(max(0.0, 1.0 - norm_rms))

            # Fractal metrics on Ω field (baseline vs noisy)
            # Use |Ω - mean| as structure field
            omg_struct_base = np.abs(omega_base - om_mean_base)
            omg_struct_noisy = np.abs(omega_noisy - om_mean_noisy)

            fd3_base = fractal_dim_3d(np.mean(omg_struct_base, axis=0))   # 3D approx via [Z,X,Y] compress
            fd3_noisy = fractal_dim_3d(np.mean(omg_struct_noisy, axis=0))

            fd4_base = fractal_dim_4d(omega_base)
            fd4_noisy = fractal_dim_4d(omega_noisy)

            # Visuals: central slices + diff
            T0, nz, nx, ny = V.shape
            tmid = T0 // 2
            zmid = nz // 2

            omega_c_base = omega_base[tmid, zmid, :, :]
            omega_c_noisy = omega_noisy[tmid, zmid, :, :]
            omega_c_diff = omega_c_noisy - omega_c_base

            # Ω max projections
            omega_max_base = omega_base.max(axis=0).max(axis=0)  # [X,Y]
            omega_max_noisy = omega_noisy.max(axis=0).max(axis=0)

            vis = {}

            p1 = visuals / "qim_v7_4_omega_central_base.png"
            write_img(p1, omega_c_base, "QIM v7.4 Ω central slice (baseline)")
            vis["omega_central_base"] = str(p1)

            p2 = visuals / "qim_v7_4_omega_central_noisy.png"
            write_img(p2, omega_c_noisy, "QIM v7.4 Ω central slice (noisy)")
            vis["omega_central_noisy"] = str(p2)

            p3 = visuals / "qim_v7_4_omega_central_diff.png"
            write_img(p3, omega_c_diff, "QIM v7.4 Ω central slice (noisy - baseline)")
            vis["omega_central_diff"] = str(p3)

            p4 = visuals / "qim_v7_4_omega_maxproj_comparison.png"
            plt.figure()
            plt.subplot(1,2,1)
            plt.imshow(omega_max_base, origin="lower")
            plt.title("Ω max-proj baseline")
            plt.colorbar()
            plt.subplot(1,2,2)
            plt.imshow(omega_max_noisy, origin="lower")
            plt.title("Ω max-proj noisy")
            plt.colorbar()
            plt.suptitle("QIM v7.4 Ω max projection (baseline vs noisy)")
            plt.savefig(p4, bbox_inches="tight")
            plt.close()
            vis["omega_maxproj_comparison"] = str(p4)

            # Noise response curve (histogram of Ω_noisy - Ω_base)
            diff_flat = flat_noisy - flat_base
            plt.figure()
            plt.hist(diff_flat, bins=100)
            plt.title("QIM v7.4 Ω-basin noise response")
            plt.xlabel("Ω_noisy - Ω_base")
            plt.ylabel("count")
            p5 = visuals / "qim_v7_4_omega_noise_response_hist.png"
            plt.savefig(p5, bbox_inches="tight")
            plt.close()
            vis["omega_noise_response_hist"] = str(p5)

            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v7_4_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMOmegaBasinNoiseImmunityAFMSuperRes",
                "version": "7.4",
                "timestamp": now_iso(),
                "mode": "afm-omega-noise-immunity",
                "superres_factor": int(superres),
                "noise_level": float(noise_level),
                "shape_4d": [int(T0), int(nz), int(nx), int(ny)],
                "metrics": {
                    "triad": {"E": E, "I": I, "C": C},
                    "H19_dphi_global": I,
                    "lambda_eff": lam,
                    "barrier_scale": barrier,
                    "omega_mean_baseline": om_mean_base,
                    "omega_std_baseline": om_std_base,
                    "omega_mean_noisy": om_mean_noisy,
                    "omega_std_noisy": om_std_noisy,
                    "omega_corr": corr,
                    "omega_rms_diff": rms_diff,
                    "omega_norm_rms_diff": norm_rms,
                    "omega_immunity_index_H20": omega_immunity,
                    "fractal_dim3_omega_base": fd3_base,
                    "fractal_dim3_omega_noisy": fd3_noisy,
                    "fractal_dim4_omega_base": fd4_base,
                    "fractal_dim4_omega_noisy": fd4_noisy,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface geometry (3D)",
                        "H16E": "4D harmonic baseline geometry (t,z,x,y)",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H20": "Ω-basin invariance and noise-immunity",
                        "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
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
                "E": E,
                "I": I,
                "C": C,
                "lambda_eff": lam,
                "barrier_scale": barrier,
                "omega_mean_baseline": om_mean_base,
                "omega_std_baseline": om_std_base,
                "omega_mean_noisy": om_mean_noisy,
                "omega_std_noisy": om_std_noisy,
                "omega_corr": corr,
                "omega_rms_diff": rms_diff,
                "omega_norm_rms_diff": norm_rms,
                "omega_immunity_index_H20": omega_immunity,
                "fractal_dim3_omega_base": fd3_base,
                "fractal_dim3_omega_noisy": fd3_noisy,
                "fractal_dim4_omega_base": fd4_base,
                "fractal_dim4_omega_noisy": fd4_noisy,
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

    root   = sys.argv[1]
    state  = sys.argv[2]
    vis    = sys.argv[3]
    led    = sys.argv[4]
    logs   = sys.argv[5]
    afm    = sys.argv[6]
    sr     = int(sys.argv[7])
    noise  = float(sys.argv[8])
    main(root, state, vis, led, logs, afm, sr, noise)
