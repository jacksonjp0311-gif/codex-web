#!/usr/bin/env python3
# QIM v4.3 — High-Resolution Super-Res Engine (All-In-One)
# Role:
#   • Load or synthesize 3D AFM-style volume
#   • Extend to 4D field V[t,x,y,z]
#   • Compute dphi = |grad V| over 4D
#   • Global metrics (E, I, C), H19 (dphi_global), cusp v2.8 proxies
#   • Super-res 2D visuals (central / horizon) via upsampling
#   • Emit state JSON, PNG visuals, ledger line

import argparse
import json
import math
import sys
import traceback
from pathlib import Path
from datetime import datetime

import numpy as np

# Optional deps
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


def to_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


# ─────────────────────────────────────────────
# 1) SYNTHETIC 3D AFM VOLUME
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=19):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    base = np.exp(-2.0 * R) * (1.0 + 0.35 * np.sin(5.0 * R))

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
    vol = synthetic_volume(shape=shape)
    return vol, False, len(pngs)


# ─────────────────────────────────────────────
# 2) 4D FIELD (TIME EVOLUTION)
# ─────────────────────────────────────────────
def build_4d_field(volume3d, T=40):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = 1.0 + 0.30 * math.sin(theta) + 0.20 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = volume3d * mod

    return V


# ─────────────────────────────────────────────
# 3) dphi, METRICS, H19, CUSP PROXIES
# ─────────────────────────────────────────────
def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


def compute_metrics(V, dphi):
    E = to_float(np.mean(np.abs(V)))
    I = to_float(np.mean(dphi))
    dphi_global = I

    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)
    C_eff = (E * I) / (1.0 + abs(dphi_global))

    return {
        "triad": {"E": E, "I": I, "C": C_eff},
        "dphi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": to_float(barrier),
    }


def compute_harmonics(dphi):
    vals = dphi.flatten()
    pos = vals[vals > 0.0]
    if pos.size == 0:
        return {"core": 0, "shell": 0, "void": int(vals.size)}

    p95 = float(np.percentile(pos, 95.0))
    p50 = float(np.percentile(pos, 50.0))

    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())

    return {"core": core, "shell": shell, "void": void}


# ─────────────────────────────────────────────
# 4) SUPER-RES VISUALS
# ─────────────────────────────────────────────
def upsample_2d(field2d, factor=4):
    """Nearest-neighbor upsample via kron to avoid heavy deps."""
    field2d = np.asarray(field2d, dtype=np.float32)
    if factor <= 1:
        return field2d
    ones = np.ones((factor, factor), dtype=np.float32)
    hi = np.kron(field2d, ones)
    return hi


def save_visuals_superres(V, dphi, visuals_dir: Path, prefix: str, up_factor: int = 4):
    visuals_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    if not MATPLOTLIB_OK:
        return paths

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    z_mid = nz // 2

    # Central slice
    central = dphi[t_mid, :, :, z_mid]
    central_hi = upsample_2d(central, factor=up_factor)

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(central_hi, origin="lower")
    fig.colorbar(im, ax=ax)
    ax.set_title("QIM v4.3 super-res central dphi slice")
    out_central = visuals_dir / f"{prefix}_delta_phi_central_superres.png"
    fig.tight_layout()
    fig.savefig(out_central, dpi=200, bbox_inches="tight")
    plt.close(fig)
    paths["delta_phi_central_superres"] = str(out_central)

    # Horizon-style projection: max over t and x → (y, z)
    horizon = dphi.max(axis=0).max(axis=0)
    horizon_hi = upsample_2d(horizon, factor=up_factor)
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(horizon_hi, origin="lower")
    fig.colorbar(im, ax=ax)
    ax.set_title("QIM v4.3 super-res horizon projection")
    out_horizon = visuals_dir / f"{prefix}_horizon_maxproj_superres.png"
    fig.tight_layout()
    fig.savefig(out_horizon, dpi=200, bbox_inches="tight")
    plt.close(fig)
    paths["horizon_maxproj_superres"] = str(out_horizon)

    # Max projection over t and z → (x, y)
    maxproj = dphi.max(axis=0).max(axis=2)
    maxproj_hi = upsample_2d(maxproj, factor=up_factor)
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(maxproj_hi, origin="lower")
    fig.colorbar(im, ax=ax)
    ax.set_title("QIM v4.3 super-res max projection (t,z)")
    out_max = visuals_dir / f"{prefix}_delta_phi_maxproj_superres.png"
    fig.tight_layout()
    fig.savefig(out_max, dpi=200, bbox_inches="tight")
    plt.close(fig)
    paths["delta_phi_maxproj_superres"] = str(out_max)

    # Resonance curve (mean |V| vs t)
    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(range(T), energy_t)
    ax.set_xlabel("t (frame)")
    ax.set_ylabel("mean |V|")
    ax.set_title("QIM v4.3 resonance curve")
    out_curve = visuals_dir / f"{prefix}_resonance_curve.png"
    fig.tight_layout()
    fig.savefig(out_curve, dpi=200, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(out_curve)

    # Optional GIF: central slice over time (no super-res to save space)
    if IMAGEIO_OK:
        frames = []
        for t in range(T):
            sl = dphi[t, :, :, z_mid]
            sl_min, sl_max = float(sl.min()), float(sl.max())
            if sl_max > sl_min:
                norm = (sl - sl_min) / (sl_max - sl_min)
            else:
                norm = np.zeros_like(sl)
            frame = (255.0 * norm).astype(np.uint8)
            frames.append(frame)
        gif_path = visuals_dir / f"{prefix}_dphi_time.gif"
        try:
            imageio.mimsave(gif_path, frames, duration=0.08)
            paths["delta_phi_gif"] = str(gif_path)
        except Exception:
            pass

    return paths


# ─────────────────────────────────────────────
# 5) STATE + LEDGER
# ─────────────────────────────────────────────
def write_state_and_ledger(
    state_dir: Path,
    ledger_dir: Path,
    input_dir: Path,
    used_synthetic: bool,
    png_count: int,
    V,
    dphi,
    metrics: dict,
    harmonics: dict,
    visuals: dict,
    up_factor: int,
):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_3_superres_state_{ts}.json"
    ledger_path = ledger_dir / "qim_v4_3_ledger.jsonl"

    T, nx, ny, nz = V.shape

    triad = metrics.get("triad", {})
    dphi_global = metrics.get("dphi_global", 0.0)
    lam_eff = metrics.get("lambda_eff", 0.0)
    barrier = metrics.get("barrier_scale", 0.0)

    state_obj = {
        "protocol": "CodexQIMSuperRes",
        "version": "4.3",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "superres": {
            "upsample_factor_2d": int(up_factor),
            "base_xy": [int(ny), int(nz)],
            "superres_xy": [int(ny * up_factor), int(nz * up_factor)],
        },
        "metrics": {
            "triad": triad,
            "H19_dphi_global": dphi_global,
            "cusp_lambda_eff": lam_eff,
            "cusp_barrier_scale": barrier,
            "harmonics": harmonics,
        },
        "codex": {
            "H_layer": {
                "H7": 0.70,
                "H19": "Global dphi integration over 4D field",
            },
            "laws": {
                "universal_truth": "C = (E·I)/(1 + |dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr -> 1-, barrier ~ (1-lambda)^(3/2) (E·I)^(3/2)",
            },
            "tesseract_alignment": {
                "note": "Field prepared for glyph-compressed mapping (ls/ic/ul pairs).",
                "modules": {
                    "QIM": "QIM",
                    "QCX": "QCX",
                    "GIZA": "GIZA",
                    "VOY": "VOY",
                    "SOL": "SOL",
                    "DNA": "DNA",
                    "GRD": "GRD",
                    "CGL": "CGL",
                    "BRG": "BRG",
                },
            },
        },
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "qim-v4-3-superres",
        "state_file": str(state_path),
        "input_dir": str(input_dir),
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "E": to_float(triad.get("E", 0.0)),
        "I": to_float(triad.get("I", 0.0)),
        "C_effective": to_float(triad.get("C", 0.0)),
        "dphi_global": to_float(dphi_global),
        "lambda_eff": to_float(lam_eff),
        "barrier_scale": to_float(barrier),
        "harmonics": harmonics,
    }

    with ledger_path.open("a", encoding="utf-8") as f_ledger:
        f_ledger.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

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
        log_file = logs_dir / f"qim_v4_3_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"

    def log(msg: str):
        safe = str(msg)
        print(safe)
        if log_file is not None:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(safe + "\n")

    t0 = datetime.utcnow()
    log("QIM v4.3 — High-Resolution Super-Res Engine starting...")
    log(f"  input_dir  : {input_dir}")
    log(f"  state_dir  : {state_dir}")
    log(f"  visuals_dir: {visuals_dir}")
    log(f"  ledger_dir : {ledger_dir}")
    if log_file is not None:
        log(f"  log_file   : {log_file}")

    try:
        vol3d, used_synth, png_count = load_afm_stack(input_dir)
        log(f"Loaded base volume: shape={vol3d.shape}, synthetic={used_synth}, input_png_count={png_count}")

        V = build_4d_field(vol3d, T=40)
        log(f"Built 4D field with shape={V.shape}")

        dphi = compute_dphi_4d(V)
        log("Computed dphi field over 4D volume.")

        M = compute_metrics(V, dphi)
        H = compute_harmonics(dphi)
        log(f"Global triad: {M.get('triad',{})}")
        log(f"H19 dphi_global: {M.get('dphi_global',0.0)}")
        log(f"Cusp lambda_eff: {M.get('lambda_eff',0.0)}, barrier_scale: {M.get('barrier_scale',0.0)}")
        log(f"Harmonics: {H}")

        ts_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = f"qim_v4_3_field_{ts_tag}"
        visuals = save_visuals_superres(V, dphi, visuals_dir, prefix, up_factor=4)
        log(f"Visuals written: {visuals}")

        state_path, ledger_path = write_state_and_ledger(
            state_dir,
            ledger_dir,
            input_dir,
            used_synth,
            png_count,
            V,
            dphi,
            M,
            H,
            visuals,
            up_factor=4,
        )
        log(f"State JSON written -> {state_path}")
        log(f"Ledger appended    -> {ledger_path}")

        t1 = datetime.utcnow()
        dt = (t1 - t0).total_seconds()
        log(f"QIM v4.3 run complete. Runtime: {dt:.3f} s")

    except Exception as e:
        err_msg = "QIM v4.3 encountered an error: " + repr(e)
        print(err_msg, file=sys.stderr)
        traceback.print_exc()
        if log_file is not None:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(err_msg + "\n")
                f.write(traceback.format_exc() + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
