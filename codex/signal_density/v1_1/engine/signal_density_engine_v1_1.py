#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  CODEX SIGNAL DENSITY ENGINE v1.1 — Ω-BASIN STABILITY NODE    ║
# ║  BH-inspired artifacts: state + summary + glyph + ledger      ║
# ╚══════════════════════════════════════════════════════════════╝

import json, math, sys, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))

# ─────────────────────────────────────────────
# Synthetic “profile-field” builder (geometry-only mode)
# Replace later with real embeddings / thread graphs / token-flow fields.
# ─────────────────────────────────────────────
def build_field(nx=64, ny=64, nz=64, T=32):
    x = np.linspace(-1.0, 1.0, nx, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, ny, dtype=np.float32)
    z = np.linspace(-1.0, 1.0, nz, dtype=np.float32)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z) + 1e-9

    V = np.zeros((T, nx, ny, nz), dtype=np.float32)
    for t in range(T):
        th = 2.0 * math.pi * t / float(T)
        # ring + mild turbulence: “structure in public”
        ring = np.exp(-0.5*((R - 0.55)/0.12)**2)
        swirl = 0.25*np.sin(3.0*th + 5.0*R) + 0.18*np.cos(2.0*th + 3.0*R)
        V[t] = (ring * (1.0 + swirl)) * np.exp(-0.8*R)

    # normalize
    mn, mx = float(V.min()), float(V.max())
    if mx > mn:
        V = (V - mn) / (mx - mn)
    return V

def super_resolve_3d(vol3: np.ndarray, factor: int, max_size: int = 128) -> np.ndarray:
    nx, ny, nz = vol3.shape
    target_nx = min(max_size, int(nx * factor))
    target_ny = min(max_size, int(ny * factor))
    target_nz = min(max_size, int(nz * factor))
    sx = target_nx / float(nx)
    sy = target_ny / float(ny)
    sz = target_nz / float(nz)
    hi = zoom(vol3, (sx, sy, sz), order=1)
    return hi.astype(np.float32)

def dphi_4d(V: np.ndarray) -> np.ndarray:
    out = np.zeros_like(V, dtype=np.float32)
    for t in range(V.shape[0]):
        gx, gy, gz = np.gradient(V[t])
        out[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return out

def omega(dphi: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.abs(dphi))

def fractal_dim_3d(vol: np.ndarray) -> float:
    data = (vol > np.median(vol)).astype(np.uint8)
    scales = [1,2,4,8,16]
    counts = []
    ks = []
    for k in scales:
        try:
            sub = data[::k, ::k, ::k]
            counts.append(float(sub.sum()))
            ks.append(k)
        except Exception:
            continue
    if len(counts) < 2:
        return 2.0
    counts = np.array(counts, dtype=np.float64) + 1e-9
    ks = np.array(ks, dtype=np.float64)
    p = np.polyfit(np.log(1.0/ks), np.log(counts), 1)
    return float(abs(p[0]))

def write_img(path: Path, arr: np.ndarray, title: str):
    plt.figure()
    plt.imshow(arr, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def main(
    root: str,
    tag: str,
    state_path: str,
    summary_path: str,
    glyph_path: str,
    visuals_dir: str,
    ledger_dir: str,
    logs_path: str,
    superres: str,
    noise_level: str,
    V_in: str,
    Qe_in: str,
    Dc_in: str,
    P_in: str,
    Nf_in: str
):
    # ── CANONICAL FIX: cast CLI args (v1.0 failure: strings caused TypeError)
    sr = int(float(superres))
    nl = float(noise_level)

    # Optional SD_social inputs
    def maybe_float(s: str):
        s = (s or "").strip()
        if s == "" or s.lower() == "null":
            return None
        return float(s)

    Vv  = maybe_float(V_in)
    Qe  = maybe_float(Qe_in)
    Dc  = maybe_float(Dc_in)
    P   = maybe_float(P_in)
    Nf  = maybe_float(Nf_in)

    root_dir    = Path(root)
    visuals_dir = Path(visuals_dir)
    ledger_dir  = Path(ledger_dir)
    logs_path   = Path(logs_path)
    state_path  = Path(state_path)
    summary_path= Path(summary_path)
    glyph_path  = Path(glyph_path)

    visuals_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    glyph_path.parent.mkdir(parents=True, exist_ok=True)
    logs_path.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = msg.encode("ascii","replace").decode("ascii")
        print(line)
        with logs_path.open("a", encoding="utf-8") as lf:
            lf.write(line + "\n")

    log(f"[𓂀] Signal Density Engine v1.1 starting… tag={tag}")
    log(f"root_dir      : {root_dir}")
    log(f"visuals_dir   : {visuals_dir}")
    log(f"ledger_dir    : {ledger_dir}")
    log(f"state_path    : {state_path}")
    log(f"summary_path  : {summary_path}")
    log(f"glyph_path    : {glyph_path}")
    log(f"superres      : {sr}")
    log(f"noise_level   : {nl}")

    # ─────────────────────────────
    # 1) Build baseline 4D field (geometry-only profile proxy)
    # ─────────────────────────────
    V4 = build_field(nx=64, ny=64, nz=64, T=32)

    # Super-resolve a central 3D snapshot, then rebuild 4D harmonic baseline
    tmid = V4.shape[0] // 2
    V3  = V4[tmid]
    V3h = super_resolve_3d(V3, factor=sr, max_size=128)

    # Rebuild 4D from the hi-res snapshot (BH/QIM-style harmonic modulation)
    T0 = 40
    nx, ny, nz = V3h.shape
    V = np.zeros((T0, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    for t in range(T0):
        th = 2.0 * math.pi * t / float(T0)
        mod = 1.0 + 0.30*np.sin(th) + 0.22*np.cos(2.0*th + 3.0*R)
        V[t] = V3h * mod

    # ─────────────────────────────
    # 2) ΔΦ + Ω (GEO v1.0)
    # ─────────────────────────────
    dphi = dphi_4d(V)
    Om   = omega(dphi)

    dphi_std = float(np.std(dphi))
    sigma = float(nl) * max(dphi_std, 1e-6)
    log(f"dphi_std      : {dphi_std:.6g}")
    log(f"noise_sigma   : {sigma:.6g}")

    noise = np.random.normal(0.0, sigma, size=dphi.shape).astype(np.float32)
    dphi_n = dphi + noise
    Om_n   = omega(dphi_n)

    # ─────────────────────────────
    # 3) Metrics (H19/H20 + signal-density proxies)
    # ─────────────────────────────
    # “global ΔΦ integration” proxy
    dphi_global = float(np.mean(dphi))
    # Ω-basin invariance proxies
    omega_diff_L1 = float(np.mean(np.abs(Om_n - Om)))
    om_mean_before = float(np.mean(Om))
    om_mean_after  = float(np.mean(Om_n))
    delta_omega_mean = float(om_mean_before - om_mean_after)

    noise_immunity_index = float(1.0 / (1.0 + max(0.0, omega_diff_L1)))
    basin_drop_index     = float(1.0 / (1.0 + max(0.0, delta_omega_mean)))

    # geometry “signal density”: structure-weighted gradient energy
    # (keeps the spirit: high structure, low noise → survives perturbation)
    sd_geom = float(np.mean(Om * dphi))

    # E–I–C (Codex UTP-style)
    E = float(np.mean(np.abs(V)))
    I = float(dphi_global)
    C = float((E * I) / (1.0 + abs(I)))  # safe proxy (keeps non-explosive)

    # Fractal geometry (H16-ish diagnostics)
    fd3 = float(fractal_dim_3d(V3h))
    fd_t = []
    for t in range(T0):
        fd_t.append(fractal_dim_3d(dphi[t]))
    fd_t = np.array(fd_t, dtype=np.float32)
    fd_t_mean = float(fd_t.mean())

    # Optional SD_social (matches the LaTeX definition)
    SD_social = None
    eps = 1e-3
    if (Vv is not None) and (Qe is not None) and (Dc is not None) and (P is not None) and (Nf is not None):
        SD_social = float((Vv * Qe * Dc) / (P * max(Nf, eps)))

    # ─────────────────────────────
    # 4) Visuals (baseline vs noisy, BH-style)
    # ─────────────────────────────
    zmid = nz // 2
    tmid = T0 // 2

    dphi_c       = dphi[tmid, :, :, zmid]
    dphi_c_noisy = dphi_n[tmid, :, :, zmid]
    om_max       = Om.max(axis=0).max(axis=2)
    om_max_noisy = Om_n.max(axis=0).max(axis=2)

    vis = {}
    p1 = visuals_dir / f"{tag}_dphi_central_baseline.png"
    write_img(p1, dphi_c, "Signal Density v1.1 — Δφ central slice (baseline)")
    vis["dphi_central_baseline"] = str(p1)

    p2 = visuals_dir / f"{tag}_dphi_central_noisy.png"
    write_img(p2, dphi_c_noisy, "Signal Density v1.1 — Δφ central slice (noisy)")
    vis["dphi_central_noisy"] = str(p2)

    p3 = visuals_dir / f"{tag}_omega_maxproj_baseline.png"
    write_img(p3, om_max, "Signal Density v1.1 — Ω max projection (baseline)")
    vis["omega_maxproj_baseline"] = str(p3)

    p4 = visuals_dir / f"{tag}_omega_maxproj_noisy.png"
    write_img(p4, om_max_noisy, "Signal Density v1.1 — Ω max projection (noisy)")
    vis["omega_maxproj_noisy"] = str(p4)

    omega_t = np.mean(Om, axis=(1,2,3))
    omega_tn= np.mean(Om_n, axis=(1,2,3))
    plt.figure()
    plt.plot(range(T0), omega_t,  label="Ω baseline")
    plt.plot(range(T0), omega_tn, label="Ω noisy", linestyle="--")
    plt.xlabel("t"); plt.ylabel("Ω(t)")
    plt.title("Signal Density v1.1 — Ω-basin noise-immunity")
    plt.legend()
    p5 = visuals_dir / f"{tag}_omega_time_noise_immunity.png"
    plt.savefig(p5, bbox_inches="tight"); plt.close()
    vis["omega_time_noise_immunity"] = str(p5)

    plt.figure()
    plt.plot(range(T0), fd_t)
    plt.xlabel("t"); plt.ylabel("D_fractal(3D |Δφ_t|)")
    plt.title("Signal Density v1.1 — fractal dimension vs time")
    p6 = visuals_dir / f"{tag}_fractal_time_trace.png"
    plt.savefig(p6, bbox_inches="tight"); plt.close()
    vis["fractal_time_trace"] = str(p6)

    # ─────────────────────────────
    # 5) State + Summary + Glyph (BH-style contracts)
    # ─────────────────────────────
    state = {
        "tag": tag,
        "version": "1.1",
        "timestamp": now_iso(),
        "mode": "signal-density-omega-basin",
        "inputs": {
            "superres_factor": sr,
            "noise_level": nl,
            "SD_social_inputs": {"V": Vv, "Qe": Qe, "Dc": Dc, "P": P, "Nf": Nf}
        },
        "shape_4d": [int(T0), int(nx), int(ny), int(nz)],
        "metrics": {
            "SD_geom": sd_geom,
            "SD_social": SD_social,
            "H19_dphi_global": dphi_global,
            "omega_mean_before": om_mean_before,
            "omega_mean_after": om_mean_after,
            "delta_omega_mean": delta_omega_mean,
            "omega_diff_L1": omega_diff_L1,
            "noise_immunity_index": noise_immunity_index,
            "basin_drop_index": basin_drop_index,
            "triad": {"E": E, "I": I, "C": C},
            "fractal_dim_H16B_3d": fd3,
            "fractal_time_mean": fd_t_mean
        },
        "codex": {
            "laws": {
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
                "error_geometry": "Ω = 1/(1+|ΔΦ|)"
            },
            "H_layers": {
                "H7": 0.70,
                "H19": "Global ΔΦ integration (comparative scalar)",
                "H20": "Ω-basin invariance / noise-immunity",
                "H44": "Boundary Algebra (extremal survival lens)",
                "H45": "Constraint Canonicalization (measurement contract)"
            }
        },
        "visuals": vis
    }
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    summary = {
        "tag": tag,
        "version": "1.1",
        "timestamp": state["timestamp"],
        "SD_geom": sd_geom,
        "SD_social": SD_social,
        "H19_dphi_global": dphi_global,
        "noise_immunity_index": noise_immunity_index,
        "basin_drop_index": basin_drop_index,
        "C_avg": C
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    glyph = {
        "tag": tag,
        "module": "SignalDensity",
        "version": "1.1",
        "timestamp": state["timestamp"],
        "geometry": {
            "layout": "triadic_pyramid",
            "layer": "SignalDensity_OmegaBasin",
            "links": {
                "state_path": str(state_path),
                "summary_path": str(summary_path)
            }
        },
        "signals": {
            "SD_geom": sd_geom,
            "noise_immunity": noise_immunity_index,
            "basin_drop": basin_drop_index,
            "C_avg": C,
            "H7_alignment": float(1.0 - abs(C - 0.70))
        },
        "tags": ["signal_density","codex","ΔΦ","Ω-basin","H19","H20","H44","H45"]
    }
    glyph_path.write_text(json.dumps(glyph, indent=2), encoding="utf-8")

    # ─────────────────────────────
    # 6) Ledger (append-only, BH-style)
    # ─────────────────────────────
    ledger_path = ledger_dir / "signal_density_ledger.jsonl"
    row = {
        "tag": tag,
        "timestamp": state["timestamp"],
        "version": "1.1",
        "SD_geom": sd_geom,
        "SD_social": SD_social,
        "H19_dphi_global": dphi_global,
        "noise_immunity_index": noise_immunity_index,
        "basin_drop_index": basin_drop_index,
        "omega_diff_L1": omega_diff_L1,
        "C_avg": C,
        "superres_factor": sr,
        "noise_level": nl,
        "state_path": str(state_path),
        "summary_path": str(summary_path),
        "glyph_path": str(glyph_path)
    }
    with ledger_path.open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(row) + "\n")

    log(f"State written   → {state_path}")
    log(f"Summary written → {summary_path}")
    log(f"Glyph written   → {glyph_path}")
    log(f"Ledger appended → {ledger_path}")

    # ─────────────────────────────
    # STDOUT contract for PS / All-One chaining
    # ─────────────────────────────
    print(json.dumps({
        "tag": tag,
        "state_path": str(state_path),
        "summary_path": str(summary_path),
        "glyph_path": str(glyph_path),
        "ledger_path": str(ledger_path),
        "visuals": vis
    }))

if __name__ == "__main__":
    try:
        if len(sys.argv) != 16:
            print("Usage: engine.py ROOT TAG STATE SUMMARY GLYPH VISUALS LEDGER LOGS SUPERRES NOISE V Qe Dc P Nf", file=sys.stderr)
            sys.exit(2)

        main(*sys.argv[1:])
    except Exception as e:
        print("Signal Density Engine v1.1 error: " + repr(e), file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
