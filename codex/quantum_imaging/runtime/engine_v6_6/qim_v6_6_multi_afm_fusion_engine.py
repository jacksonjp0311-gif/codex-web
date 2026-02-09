#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.6 — MULTI-AFM FUSION SUPER-RES ENGINE                ║
# ║  AFM-bound 4D Δφ field with GEO v1.0 + H16B/H16C geometry    ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_single_afm(path: Path):
    arr = np.load(path)
    if isinstance(arr, np.lib.npyio.NpzFile):
        key0 = arr.files[0]
        arr = arr[key0]

    arr = np.array(arr, dtype=np.float32)

    # 2D → extrude to 3D
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

def fuse_afm(volumes):
    """
    Bring all AFM volumes to a common shape (that of the first),
    then average them to get a single fused AFM volume.
    """
    if len(volumes) == 1:
        return volumes[0], 1.0

    ref = volumes[0]
    nx, ny, nz = ref.shape
    aligned = [ref]
    for v in volumes[1:]:
        vx, vy, vz = v.shape
        sx = nx / float(vx)
        sy = ny / float(vy)
        sz = nz / float(vz)
        v_res = zoom(v, (sx, sy, sz), order=1).astype(np.float32)
        aligned.append(v_res)

    stack = np.stack(aligned, axis=0)
    fused = np.mean(stack, axis=0).astype(np.float32)

    # simple entanglement index: mean pairwise correlation between sources
    n = stack.shape[0]
    if n == 1:
        ent = 1.0
    else:
        flat = stack.reshape(n, -1)
        corr = np.corrcoef(flat)
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        vals = corr[mask]
        ent = float(np.nanmean(vals)) if vals.size > 0 else 0.0

    return fused, ent

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
    """
    Simple 3D fractal dimension proxy using downsampled box counts.
    """
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

def write_img(path: Path, arr: np.ndarray, title: str):
    plt.figure()
    plt.imshow(arr, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def main(root, state_d, vis_d, ledger_d, logs_d, afm_dir, superres, max_afm):
    root_dir   = Path(root)
    state_dir  = Path(state_d)
    visuals    = Path(vis_d)
    ledger_dir = Path(ledger_d)
    logs_dir   = Path(logs_d)
    afm_root   = Path(afm_dir)

    state_dir.mkdir(parents=True, exist_ok=True)
    visuals.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / f"qim_v6_6_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    with log_path.open("w", encoding="utf-8") as lf:
        def log(msg: str):
            line = msg.encode("ascii", "replace").decode("ascii")
            print(line)
            lf.write(line + "\n")
            lf.flush()

        log("QIM v6.6 — Multi-AFM Fusion Super-Res Engine starting…")
        log(f"root_dir   : {root_dir}")
        log(f"state_dir  : {state_dir}")
        log(f"visuals_dir: {visuals}")
        log(f"ledger_dir : {ledger_dir}")
        log(f"logs_dir   : {logs_dir}")
        log(f"afm_dir    : {afm_root}")
        log(f"superres   : {superres}")
        log(f"max_afm    : {max_afm}")

        try:
            files = sorted(list(afm_root.glob("*.npy"))) + sorted(list(afm_root.glob("*.npz")))
            if not files:
                raise RuntimeError("No AFM .npy/.npz files found in AFM directory.")
            files = files[:max_afm]
            for f in files:
                log(f"AFM source → {f}")

            vols = [load_single_afm(f) for f in files]
            log(f"Loaded {len(vols)} AFM volumes.")

            fused_raw, ent_idx = fuse_afm(vols)
            log(f"Fused AFM volume shape: {fused_raw.shape}")
            log(f"Entanglement index (multi-AFM) = {ent_idx:.6f}")

            hi = super_resolve(fused_raw, superres, max_size=128)
            log(f"Super-resolved fused AFM volume shape: {hi.shape}")

            V = build_4d(hi, T=40)
            dphi = dphi_4d(V)
            Om = omega(dphi)
            fd = fractal_dim(hi)

            E = float(np.mean(np.abs(V)))
            I = float(np.mean(dphi))
            C = (E * I) / (1.0 + abs(I))
            lam = min(0.99, I / (1.0 + I))
            barrier = (1.0 - lam)**1.5 * (max(E * I, 0.0)**1.5)

            om_mean = float(np.mean(Om))
            om_std  = float(np.std(Om))
            curv = float(np.mean(np.abs(dphi - np.mean(dphi))))

            T0, nx, ny, nz = V.shape
            tmid = T0 // 2
            zmid = nz // 2
            dphi_c = dphi[tmid, :, :, zmid]
            maxp   = dphi.max(axis=0).max(axis=2)
            omega_max = Om.max(axis=0).max(axis=2)
            energy_t = np.mean(np.abs(V), axis=(1, 2, 3))

            vis = {}

            p1 = visuals / "qim_v6_6_dphi_central.png"
            write_img(p1, dphi_c, "QIM v6.6 Δφ central slice (multi-AFM fused)")
            vis["dphi_central"] = str(p1)

            p2 = visuals / "qim_v6_6_dphi_maxproj.png"
            write_img(p2, maxp, "QIM v6.6 Δφ max projection (multi-AFM fused)")
            vis["dphi_maxproj"] = str(p2)

            p3 = visuals / "qim_v6_6_omega_maxproj.png"
            write_img(p3, omega_max, "QIM v6.6 Ω max projection (multi-AFM fused)")
            vis["omega_maxproj"] = str(p3)

            plt.figure()
            plt.plot(range(T0), energy_t)
            plt.xlabel("t")
            plt.ylabel("<|V|>")
            plt.title("QIM v6.6 Multi-AFM Fusion resonance curve")
            p4 = visuals / "qim_v6_6_resonance_curve.png"
            plt.savefig(p4, bbox_inches="tight")
            plt.close()
            vis["resonance_curve"] = str(p4)

            ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            state_path = state_dir / f"qim_v6_6_state_{ts_tag}.json"

            state_obj = {
                "protocol": "CodexQIMAFMSuperResMultiAFM",
                "version": "6.6",
                "timestamp": now_iso(),
                "mode": "afm-multi-fusion-superres",
                "superres_factor": int(superres),
                "n_afm_sources": len(files),
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
                    "entanglement_index": ent_idx,
                },
                "codex": {
                    "H_layers": {
                        "H7": 0.70,
                        "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                        "H16B": "Fractal AFM surface dimension",
                        "H16C": "Fractal expansion law: dim→3.0 volumetric convergence",
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
                        "current_version": "6.6",
                        "mode": "afm-multi-fusion-superres",
                    },
                },
                "visuals": vis,
            }

            state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
            log(f"State JSON written → {state_path}")

            ledger_path = ledger_dir / "qim_v6_6_ledger.jsonl"
            row = {
                "timestamp": now_iso(),
                "mode": "afm-multi-fusion-superres",
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
                "entanglement_index": ent_idx,
                "superres_factor": int(superres),
                "n_afm_sources": len(files),
            }
            with ledger_path.open("a", encoding="utf-8") as lf2:
                lf2.write(json.dumps(row) + "\n")
            log(f"Ledger appended → {ledger_path}")
            log("QIM v6.6 Multi-AFM Fusion AFM Super-Res run complete.")

        except Exception as e:
            err = "QIM v6.6 encountered an error: " + repr(e)
            print(err, file=sys.stderr)
            lf.write(err + "\n")
            lf.write(traceback.format_exc() + "\n")
            lf.flush()
            raise

if __name__ == "__main__":
    if len(sys.argv) != 9:
        print("Usage: engine.py ROOT STATE VISUALS LEDGER LOGS AFM_DIR SUPERRES MAX_AFM", file=sys.stderr)
        sys.exit(1)

    root = sys.argv[1]
    state = sys.argv[2]
    vis = sys.argv[3]
    led = sys.argv[4]
    logs = sys.argv[5]
    afm_dir = sys.argv[6]
    sr = int(sys.argv[7])
    max_afm = int(sys.argv[8])
    main(root, state, vis, led, logs, afm_dir, sr, max_afm)
