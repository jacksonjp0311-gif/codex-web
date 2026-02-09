#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v7.3 — HARMONIC 4D FRACTAL ENGINE (AFM SUPER-RES)       ║
# ║  AFM-bound 4D Δφ field + GEO v1.0 + H16B + H16E              ║
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

    if arr.ndim == 2:
        arr = np.stack([arr] * 64, axis=-1)
    elif arr.ndim == 4:
        arr = arr[arr.shape[0] // 2]

    m = float(arr.max() - arr.min())
    if m > 0:
        arr = (arr - arr.min()) / m
    return arr

def super_resolve(vol: np.ndarray, factor: int, max_size: int = 128):
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

def build_4d(vol: np.ndarray, T: int = 40):
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
        mod = 1.0 + 0.30 * np.sin(theta) + 0.22 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = vol * mod

    return V

def dphi_4d(V: np.ndarray):
    T, nx, ny, nz = V.shape
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
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

def fractal_dim_4d(vol4d: np.ndarray):
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

def main(root, state_d, vis_d, ledger_d, logs_d, afm_path, superres):
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

    log_path = logs_dir / f"qim_v7_3_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    with log_path.open("w", encoding="utf-8") as lf:
        def log(msg: str):
            line = msg.encode("ascii", "replace").decode("ascii")
            print(line)
            lf.write(line + "\n")
            lf.flush()

        log("QIM v7.3 — Harmonic 4D Fractal Engine starting…")
        log(f"root_dir   : {root_dir}")
        log(f"state_dir  : {state_dir}")
        log(f"visuals_dir: {visuals}")
        log(f"ledger_dir : {ledger_dir}")
        log(f"logs_dir   : {logs_dir}")
        log(f"afm_file   : {afm_file}")
        log(f"superres   : {superres}")

        try:
            afm = load_afm(afm_file)
            log("AFM cube loaded and normalized.")

            hi = super_resolve(afm, superres, max_size=128)
            log(f"Super-resolved AFM volume shape: {hi.shape}")

            V = build_4d(hi, T=40)
            dphi = dphi_4d(V)
            Om = omega(dphi)

            # H16B 3D fractal dim (AFM volume)
            fd3 = fractal_dim_3d(hi)

            # H16E 4D fractal dim on Δφ field
            fd4 = fractal_dim_4d(dphi)

            # time-resolved 3D fractal dims on |dphi(t,·)|
            T0 = V.shape[0]
            fd_t = []
            for t in range(T0):
                fd_t.append(fractal_dim_3d(dphi[t]))
            fd_t = np.array(fd_t, dtype=np.float32)
            fd_t_mean = float(fd_t.mean())
            fd_t_min  = float(fd_t.min())
            fd_t_max  = float(fd_t.max())

            # Triad metrics
            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam) ** 1.5 * (max(E * I, 0.0) ** 1.5)

            om_mean = float(np.mean(Om))
            om_std  = float(np.std(Om))
            curv = float(np.mean(np.abs(dphi - np.mean(dphi))))

            # Visual slices
            T0, nx, ny, nz = V.shape
            tmid = T0 // 2
            zmid = nz // 2
            dphi_c = dphi[tmid, :, :, zmid]
            maxp   = dphi.max(axis=0).max(axis=2)
            omega_max = Om.max(axis=0).max(axis=2)

            # Energy resonance curve
            energy_t = np.mean(np.abs(V), axis=(1, 2, 3))

            vis = {}

            p1 = visuals / "qim_v7_3_dphi_central.png"
            write_img(p1, dphi_c, "QIM v7.3 Δφ central slice (4D fractal)")
            vis["dphi_central"] = str(p1)

            p2 = visuals / "qim_v7_3_dphi_maxproj.png"
            write_img(p2, maxp, "QIM v7.3 Δφ max projection (4D fractal)")
            vis["dphi_maxproj"] = str(p2)

            p3 = visuals / "qim_v7_3_omega_maxproj.png"
            write_img(p3, omega_max, "QIM v7.3 Ω max projection (4D fractal)")
            vis["omega_maxproj"] = str(p3)

            # fractal vs time trace
            plt.figure()
            plt.plot(range(T0), fd_t)
            plt.xlabel("t")
            plt.ylabel("D_fractal(3D |Δφ_t|)")
            plt.title("QIM v7.3 3D fractal dimension vs time")
            p4 = visuals / "qim_v7_3_fractal_time_trace.png"
            plt.savefig(p4, bbox_inches="tight")
            plt.close()
            vis["fractal_time_trace"] = str(p4)

            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v7_3_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMHarmonic4DFractalAFMSuperRes",
                "version": "7.3",
                "timestamp": now_iso(),
                "mode": "afm-harmonic-4d-fractal",
                "superres_factor": int(superres),
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
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface dimension (3D)",
                        "H16E": "4D fractal harmonic geometry (t,x,y,z)",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
                    },
                    "laws": {
                        "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                        "cusp_v2_8": "ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                        "error_geometry": "Ω = 1/(1+|ΔΦ|)",
                    },
                    "memory": {
                        "node": "QIM",
                        "current_version": "7.3",
                        "mode": "afm-harmonic-4d-fractal",
                    },
                },
                "visuals": vis,
            }

            state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
            log(f"State JSON written → {state_path}")

            ledger_path = ledger_dir / "qim_v7_3_ledger.jsonl"
            row = {
                "timestamp": now_iso(),
                "mode": "afm-harmonic-4d-fractal",
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
                "superres_factor": int(superres),
            }
            with ledger_path.open("a", encoding="utf-8") as lf2:
                lf2.write(json.dumps(row) + "\n")
            log(f"Ledger appended → {ledger_path}")
            log("QIM v7.3 Harmonic 4D Fractal run complete.")

        except Exception as e:
            err = "QIM v7.3 encountered an error: " + repr(e)
            print(err, file=sys.stderr)
            lf.write(err + "\n")
            lf.write(traceback.format_exc() + "\n")
            lf.flush()
            raise

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("Usage: engine.py ROOT STATE VISUALS LEDGER LOGS AFM_FILE SUPERRES", file=sys.stderr)
        sys.exit(1)

    root = sys.argv[1]
    state = sys.argv[2]
    vis = sys.argv[3]
    led = sys.argv[4]
    logs = sys.argv[5]
    afm = sys.argv[6]
    sr = int(sys.argv[7])
    main(root, state, vis, led, logs, afm, sr)
