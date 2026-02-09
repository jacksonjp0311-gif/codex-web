#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v7.1 — HARMONIC INTERFERENCE ENGINE (AFM SUPER-RES)     ║
# ║  Cross-harmonic Δφ geometry: core × shell interference       ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom, gaussian_filter

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_afm(path: Path):
    arr = np.load(path)
    if isinstance(arr, np.lib.npyio.NpzFile):
        key0 = arr.files[0]
        arr = arr[key0]

    arr = np.array(arr, dtype=np.float32)

    if arr.ndim == 2:
        arr = np.stack([arr]*64, axis=-1)
    elif arr.ndim == 4:
        arr = arr[arr.shape[0]//2]

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

def build_4d(vol: np.ndarray, T: int = 40):
    T0 = T
    nx, ny, nz = vol.shape
    V = np.zeros((T0, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    for t in range(T0):
        theta = 2.0 * math.pi * t / float(T0)
        mod = 1.0 + 0.30 * np.sin(theta) + 0.22 * np.cos(2.0*theta + 3.0*R)
        V[t] = vol * mod

    return V

def dphi_4d(V: np.ndarray):
    T, nx, ny, nz = V.shape
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        out[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return out

def omega(dphi: np.ndarray):
    return 1.0 / (1.0 + np.abs(dphi))

def fractal_dim(vol: np.ndarray):
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

def harmonic_decomposition(vol: np.ndarray):
    """
    Same decomposition pattern as v7.0:
      • core: smoothed harmonic kernel
      • shell: detail band around core
    """
    core_field = gaussian_filter(vol, sigma=2.0)
    shell_field = vol - core_field

    vmin = float(vol.min())
    vmax = float(vol.max())
    mid  = 0.5 * (vmin + vmax)

    core_thresh_hi  = mid + 0.15 * (vmax - mid)
    shell_thresh_lo = mid - 0.05 * (mid - vmin)
    shell_thresh_hi = mid + 0.10 * (vmax - mid)

    core_mask  = core_field >= core_thresh_hi
    shell_mask = (shell_field >= shell_thresh_lo) & (shell_field <= shell_thresh_hi)
    void_mask  = ~(core_mask | shell_mask)

    total = float(core_mask.size)
    core_n  = float(np.count_nonzero(core_mask))
    shell_n = float(np.count_nonzero(shell_mask))
    void_n  = float(np.count_nonzero(void_mask))

    if total <= 0.0:
        return core_field, shell_field, core_mask, shell_mask, void_mask, (0.0, 0.0, 0.0)

    core_ratio  = core_n  / total
    shell_ratio = shell_n / total
    void_ratio  = void_n  / total

    return core_field, shell_field, core_mask, shell_mask, void_mask, (
        core_ratio, shell_ratio, void_ratio
    )

def write_img(path: Path, arr: np.ndarray, title: str):
    plt.figure()
    plt.imshow(arr, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

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

    log_path = logs_dir / f"qim_v7_1_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    with log_path.open("w", encoding="utf-8") as lf:
        def log(msg: str):
            line = msg.encode("ascii", "replace").decode("ascii")
            print(line)
            lf.write(line + "\n")
            lf.flush()

        log("QIM v7.1 — Harmonic Interference Engine starting…")
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

            # harmonic core + shell
            core_field, shell_field, core_mask, shell_mask, void_mask, ratios = harmonic_decomposition(hi)
            core_ratio, shell_ratio, void_ratio = ratios
            log(f"Harmonic ratios (core, shell, void) = ({core_ratio:.4f}, {shell_ratio:.4f}, {void_ratio:.4f})")

            # interference volume
            interference = core_field * shell_field
            HCI = float(np.mean(interference))
            log(f"Harmonic Coupling Index (HCI) ≈ {HCI:.6f}")

            # normalized interference for Ω-weighted geometry
            inter_min = float(interference.min())
            inter_max = float(interference.max())
            inter_norm = (interference - inter_min) / (inter_max - inter_min + 1e-9)

            V = build_4d(hi, T=40)
            dphi = dphi_4d(V)
            Om = omega(dphi)
            fd = fractal_dim(hi)
            fd_int = fractal_dim(np.abs(interference))

            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam)**1.5 * (max(E * I, 0.0)**1.5)

            om_mean = float(np.mean(Om))
            om_std  = float(np.std(Om))
            curv = float(np.mean(np.abs(dphi - np.mean(dphi))))

            # Ω-weighted interference measure
            # project Ω to 3D first
            Om_max = Om.max(axis=0).max(axis=2)
            omega_interference = float(np.mean(Om_max * (1.0 + inter_norm)))
            T0, nx, ny, nz = V.shape
            tmid = T0 // 2
            zmid = nz // 2

            inter_slice = interference[:, :, zmid]
            inter_maxproj = np.max(np.abs(interference), axis=2)
            omega_weight_map = Om_max * (1.0 + inter_norm.mean(axis=2))
            phase_slice = np.sign(inter_slice)

            energy_t = np.mean(np.abs(V), axis=(1, 2, 3))

            vis = {}

            p1 = visuals / "qim_v7_1_interference_slice.png"
            write_img(p1, inter_slice, "QIM v7.1 harmonic interference (central slice)")
            vis["interference_slice"] = str(p1)

            p2 = visuals / "qim_v7_1_interference_maxproj.png"
            write_img(p2, inter_maxproj, "QIM v7.1 |core×shell| max projection")
            vis["interference_maxproj"] = str(p2)

            p3 = visuals / "qim_v7_1_omega_interference.png"
            write_img(p3, omega_weight_map, "QIM v7.1 Ω-weighted interference map")
            vis["omega_interference_map"] = str(p3)

            p4 = visuals / "qim_v7_1_phase_map.png"
            write_img(p4, phase_slice, "QIM v7.1 harmonic phase map (sign(core×shell))")
            vis["phase_map"] = str(p4)

            plt.figure()
            plt.plot(range(T0), energy_t)
            plt.xlabel("t")
            plt.ylabel("<|V|>")
            plt.title("QIM v7.1 Harmonic Interference resonance curve")
            p5 = visuals / "qim_v7_1_interference_resonance_curve.png"
            plt.savefig(p5, bbox_inches="tight")
            plt.close()
            vis["interference_resonance_curve"] = str(p5)

            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v7_1_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMHarmonicInterferenceAFMSuperRes",
                "version": "7.1",
                "timestamp": now_iso(),
                "mode": "afm-harmonic-interference",
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
                    "fractal_dim_H16B": fd,
                    "fractal_dim_H16D_interference": fd_int,
                    "harmonic_core_ratio": core_ratio,
                    "harmonic_shell_ratio": shell_ratio,
                    "harmonic_void_ratio": void_ratio,
                    "harmonic_coupling_index": HCI,
                    "omega_interference_mean": omega_interference,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface dimension",
                        "H16C": "Fractal expansion law: dim→3.0 volumetric convergence",
                        "H19": "Global Δφ integration (4D AFM field → C)",
                        "H31": "Harmonic Stability (core:shell:void ≈ 1:9:10)",
                        "H41": "Cross-harmonic coupling: core×shell interference geometry",
                    },
                    "laws": {
                        "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                        "cusp_v2_8": "ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
                        "error_geometry": "Ω = 1/(1+|ΔΦ|)",
                    },
                    "memory": {
                        "node": "QIM",
                        "current_version": "7.1",
                        "mode": "afm-harmonic-interference",
                    },
                },
                "visuals": vis,
            }

            state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
            log(f"State JSON written → {state_path}")

            ledger_path = ledger_dir / "qim_v7_1_ledger.jsonl"
            row = {
                "timestamp": now_iso(),
                "mode": "afm-harmonic-interference",
                "state_file": str(state_path),
                "E": E,
                "I": I,
                "C": C,
                "lambda_eff": lam,
                "barrier_scale": barrier,
                "omega_mean": om_mean,
                "omega_std": om_std,
                "curvature_proxy": curv,
                "fractal_dim_H16B": fd,
                "fractal_dim_H16D_interference": fd_int,
                "harmonic_core_ratio": core_ratio,
                "harmonic_shell_ratio": shell_ratio,
                "harmonic_void_ratio": void_ratio,
                "harmonic_coupling_index": HCI,
                "omega_interference_mean": omega_interference,
                "superres_factor": int(superres),
            }
            with ledger_path.open("a", encoding="utf-8") as lf2:
                lf2.write(json.dumps(row) + "\n")
            log(f"Ledger appended → {ledger_path}")
            log("QIM v7.1 Harmonic Interference AFM Super-Res run complete.")

        except Exception as e:
            err = "QIM v7.1 encountered an error: " + repr(e)
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
