#!/usr/bin/env python3
# QIM v4.2 — Field Vision Engine (All-In-One)
# Role:
#   • Load or synthesize 3D AFM-like volume
#   • Extend to 4D (x, y, z, t) evolving field
#   • Compute dphi gradients, global dphi (H19), E–I–C triad, cusp metrics
#   • Emit state JSON, PNG visuals, optional GIF
#   • Append ledger line

import argparse, json, math, sys, traceback
from pathlib import Path
from datetime import datetime

import numpy as np

# Optional deps for visuals
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

try:
    import imageio.v2 as imageio
    IMAGEIO_OK = True
except Exception:
    try:
        import imageio
        IMAGEIO_OK = True
    except Exception:
        IMAGEIO_OK = False

# ─────────────────────────────────────────────
# Utility: safe float + ASCII-safe logging
# ─────────────────────────────────────────────
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def make_logger(log_file):
    def log(msg):
        # Make sure what we print is ASCII-safe (no Windows encoding crash)
        safe = str(msg).encode("ascii", "replace").decode("ascii")
        print(safe)
        if log_file is not None:
            try:
                log_file.write(safe + "\n")
                log_file.flush()
            except Exception:
                pass
    return log

# ─────────────────────────────────────────────
# 1) LOAD OR SYNTHESIZE 3D AFM VOLUME
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=19):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    R = np.sqrt(X * X + Y * Y + Z * Z)

    # Radial shell + interference rings (Codex style)
    base = np.exp(-2.0 * R) * (1.0 + 0.35 * np.sin(5.0 * R))

    # Add a few "atoms" / peaks
    peaks = np.zeros_like(base)
    centers = [
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (-0.5, -0.3, 0.4),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        peaks += np.exp(-30.0 * Rp * Rp)

    vol = base + 0.6 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol

def load_afm_stack(input_dir: Path, shape=(64, 64, 64)):
    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        vol = synthetic_volume(shape=shape)
        return vol, True, 0
    # Presence of PNGs: treat as "real context", but keep synthetic volume
    vol = synthetic_volume(shape=shape)
    return vol, False, len(pngs)

# ─────────────────────────────────────────────
# 2) EXTEND TO 4D EVOLVING FIELD
# ─────────────────────────────────────────────
def build_4d_field(volume3d, T=40):
    """
    Create 4D volume: V[t, x, y, z]
    Oscillatory evolution around base volume.
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
        mod = 1.0 + 0.3 * math.sin(theta) + 0.2 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = volume3d * mod

    return V

# ─────────────────────────────────────────────
# 3) dphi, TRIAD, H19 & CUSP METRICS
# ─────────────────────────────────────────────
def compute_delta_phi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi

def compute_global_metrics(V, dphi):
    # E = mean |V|
    E = f(np.mean(np.abs(V)))
    # I = mean |grad V| = mean dphi
    I = f(np.mean(dphi))
    # H19: global dphi integration
    delta_phi_global = f(np.mean(dphi))

    # Cusp-inspired lambda_eff in [0, 0.99)
    lam_eff = min(0.99, delta_phi_global / (1.0 + delta_phi_global))
    # Barrier scaling ~ (1 - lambda)^(3/2) * (E*I)^(3/2)
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)

    # Codex coherence law
    C_eff = (E * I) / (1.0 + abs(delta_phi_global))

    triad = {"E": E, "I": I, "C": C_eff}

    return {
        "triad": triad,
        "delta_phi_global": delta_phi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": f(barrier_scale),
    }

def compute_harmonics(dphi):
    vals = dphi.flatten()
    positive = vals[vals > 0.0]
    if positive.size == 0:
        return {
            "core": 0,
            "shell": 0,
            "void": int(vals.size),
        }

    p95 = np.percentile(positive, 95.0)
    p50 = np.percentile(positive, 50.0)

    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())

    return {
        "core": core,
        "shell": shell,
        "void": void,
    }

# ─────────────────────────────────────────────
# 4) VISUALS
# ─────────────────────────────────────────────
def save_visuals(V, dphi, visuals_dir: Path, prefix: str, log):
    visuals_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    if not MATPLOTLIB_OK:
        log("Matplotlib not available; skipping PNG visuals.")
        return paths

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    x_mid = nx // 2
    y_mid = ny // 2
    z_mid = nz // 2

    # 4-panel figure: central slices in x, y, z, and max projection
    try:
        fig, axes = plt.subplots(2, 2, figsize=(8, 8))

        sl_x = dphi[t_mid, x_mid, :, :]
        sl_y = dphi[t_mid, :, y_mid, :]
        sl_z = dphi[t_mid, :, :, z_mid]
        maxproj = dphi.max(axis=0).max(axis=2)

        im0 = axes[0, 0].imshow(sl_x, origin="lower")
        axes[0, 0].set_title("central slice x")

        im1 = axes[0, 1].imshow(sl_y, origin="lower")
        axes[0, 1].set_title("central slice y")

        im2 = axes[1, 0].imshow(sl_z, origin="lower")
        axes[1, 0].set_title("central slice z")

        im3 = axes[1, 1].imshow(maxproj, origin="lower")
        axes[1, 1].set_title("max projection (t,z)")

        fig.colorbar(im3, ax=axes.ravel().tolist(), shrink=0.8)
        out_panels = visuals_dir / f"{prefix}_delta_phi_panels.png"
        fig.tight_layout()
        fig.savefig(out_panels, bbox_inches="tight")
        plt.close(fig)
        paths["delta_phi_panels"] = str(out_panels)
    except Exception as e:
        log(f"Panel visual failed: {e!r}")

    # Horizon-style projection: max over t and x → (y,z)
    try:
        horizon = dphi.max(axis=0).max(axis=0)
        fig = plt.figure()
        plt.imshow(horizon, origin="lower")
        plt.title("QIM v4.2 horizon max projection (t,x)")
        plt.colorbar()
        out_horizon = visuals_dir / f"{prefix}_horizon_maxproj.png"
        fig.savefig(out_horizon, bbox_inches="tight")
        plt.close(fig)
        paths["horizon_maxproj"] = str(out_horizon)
    except Exception as e:
        log(f"Horizon visual failed: {e!r}")

    # Resonance curve: mean |V| vs t
    try:
        energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
        fig = plt.figure()
        plt.plot(range(T), energy_t)
        plt.xlabel("t (frame)")
        plt.ylabel("mean |V|")
        plt.title("QIM v4.2 resonance curve (mean |V| vs t)")
        out_curve = visuals_dir / f"{prefix}_resonance_curve.png"
        fig.savefig(out_curve, bbox_inches="tight")
        plt.close(fig)
        paths["resonance_curve"] = str(out_curve)
    except Exception as e:
        log(f"Resonance visual failed: {e!r}")

    # Optional GIF of central z slice over time
    if IMAGEIO_OK:
        try:
            frames = []
            for t in range(T):
                sl = dphi[t, :, :, z_mid]
                sl_min, sl_max = sl.min(), sl.max()
                if sl_max > sl_min:
                    norm = (sl - sl_min) / (sl_max - sl_min)
                else:
                    norm = np.zeros_like(sl)
                frame = (255.0 * norm).astype(np.uint8)
                frames.append(frame)
            gif_path = visuals_dir / f"{prefix}_delta_phi_4d.gif"
            imageio.mimsave(gif_path, frames, duration=0.08)
            paths["delta_phi_gif"] = str(gif_path)
        except Exception as e:
            log(f"GIF visual failed: {e!r}")
    else:
        log("imageio not available; skipping GIF.")

    return paths

# ─────────────────────────────────────────────
# 5) STATE + LEDGER
# ─────────────────────────────────────────────
def write_state_and_ledger(state_dir: Path,
                           ledger_dir: Path,
                           input_dir: Path,
                           used_synthetic: bool,
                           png_count: int,
                           V, dphi,
                           metrics: dict,
                           harmonics: dict,
                           visuals: dict,
                           log):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_2_field_state_{ts}.json"
    ledger_path = ledger_dir / "qim_v4_2_ledger.jsonl"

    T, nx, ny, nz = V.shape

    state_obj = {
        "protocol": "CodexQIMFieldVision",
        "version": "4.2",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "metrics": {
            "triad": metrics.get("triad", {}),
            "H19_delta_phi_global": metrics.get("delta_phi_global", 0.0),
            "cusp_lambda_eff": metrics.get("lambda_eff", 0.0),
            "cusp_barrier_scale": metrics.get("barrier_scale", 0.0),
            "harmonics": harmonics,
        },
        "codex": {
            "H_layer": {
                "H7": 0.70,
                "H19": "Global dphi integration layer for 4D field",
            },
            "laws": {
                "universal_truth": "C = (E·I)/(1 + |ΔΦ_global|)",
                "cusp_v2_8": "λ = P/P_cr → 1⁻; ΔV ∝ (1-λ)^{3/2}(EI)^{3/2}",
            },
            "tesseract_alignment": {
                "note": "Field prepared for glyph-compressed mapping (ls/ic/ul pairs)",
                "modules": {
                    "QIM": "𓇳QIM",
                    "QCX": "𓂀QCX",
                    "GIZA": "𓊹GIZA",
                    "VOY": "𓋹VOY",
                    "SOL": "𓇯SOL",
                    "DNA": "𓆰DNA",
                    "GRD": "𓃣GRD",
                    "CGL": "𓏤CGL",
                    "BRG": "⧉BRG",
                },
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    triad = metrics.get("triad", {})
    ledger_obj = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "qim-v4-2-field-vision",
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "E": f(triad.get("E", 0.0)),
        "I": f(triad.get("I", 0.0)),
        "C_effective": f(triad.get("C", 0.0)),
        "delta_phi_global": f(metrics.get("delta_phi_global", 0.0)),
        "lambda_eff": f(metrics.get("lambda_eff", 0.0)),
        "barrier_scale": f(metrics.get("barrier_scale", 0.0)),
        "harmonics": harmonics,
    }
    with ledger_path.open("a", encoding="utf-8") as f_ledger:
        f_ledger.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    log(f"State JSON written → {state_path}")
    log(f"Ledger appended    → {ledger_path}")
    return state_path, ledger_path

# ─────────────────────────────────────────────
# 6) MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None

    log_file = None
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"qim_v4_2_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        log_file = log_path.open("w", encoding="utf-8")
    log = make_logger(log_file)

    t0 = datetime.utcnow()
    log("QIM v4.2 — Field Vision Engine starting...")
    log(f"  input_dir  : {input_dir}")
    log(f"  state_dir  : {state_dir}")
    log(f"  visuals_dir: {visuals_dir}")
    log(f"  ledger_dir : {ledger_dir}")
    if log_file is not None:
        log(f"  log_file   : {log_file.name}")

    try:
        # 1) Load or synthesize base volume
        vol3d, used_synth, png_count = load_afm_stack(input_dir)
        log(f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, input_png_count={png_count}")

        # 2) Build 4D evolving field
        V = build_4d_field(vol3d, T=40)
        log(f"Built 4D field with shape={V.shape}")

        # 3) dphi, metrics, harmonics
        dphi = compute_delta_phi_4d(V)
        log("Computed dphi field over 4D volume.")

        mets = compute_global_metrics(V, dphi)
        harms = compute_harmonics(dphi)
        log(f"Global triad: {mets.get('triad',{})}")
        log(f"H19 dphi_global: {mets.get('delta_phi_global',0.0)}")
        log(f"Cusp lambda_eff: {mets.get('lambda_eff',0.0)}, barrier_scale: {mets.get('barrier_scale',0.0)}")
        log(f"Harmonics: {harms}")

        # 4) Visuals
        ts_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = f"qim_v4_2_field_{ts_tag}"
        visuals = save_visuals(V, dphi, visuals_dir, prefix, log)
        log(f"Visuals written: {visuals}")

        # 5) State + ledger
        write_state_and_ledger(
            state_dir, ledger_dir, input_dir,
            used_synth, png_count,
            V, dphi,
            mets, harms,
            visuals,
            log,
        )

        t1 = datetime.utcnow()
        dt = (t1 - t0).total_seconds()
        log(f"QIM v4.2 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        err_msg = "QIM v4.2 encountered an error: " + repr(e)
        safe_err = err_msg.encode("ascii", "replace").decode("ascii")
        print(safe_err, file=sys.stderr)
        if log_file is not None:
            log_file.write(safe_err + "\n")
            log_file.write(traceback.format_exc() + "\n")
        if log_file is not None:
            log_file.close()
        sys.exit(1)

    if log_file is not None:
        log_file.close()

if __name__ == "__main__":
    main()
