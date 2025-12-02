#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.0.2 — AFM SHARP-CRYSTAL ENGINE                       ║
# ║  REAL AFM Δφ + Ω + GEO v1.0 + SHARP VISUALS                  ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi

MATPLOTLIB_OK = False
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False


def enhance_field(field: np.ndarray) -> np.ndarray:
    """
    QIM v6.0.2 sharpener:
      • 4× cubic upsample
      • Gaussian blur
      • Unsharp mask (0.8 gain)
    """
    try:
        up = ndi.zoom(field, 4, order=3)
    except Exception:
        return field
    blurred = ndi.gaussian_filter(up, sigma=1.0)
    sharpened = up + 0.8 * (up - blurred)
    return sharpened


def compute_delta_phi(field: np.ndarray) -> np.ndarray:
    """Δφ = field - mean(field)"""
    mean_val = float(field.mean())
    return field - mean_val


def compute_omega(dphi: np.ndarray) -> np.ndarray:
    """
    GEO v1.0 deviation-weighted metric:
      Ω = 1 / (1 + |Δφ|)
    """
    return 1.0 / (1.0 + np.abs(dphi))


def compute_metrics(dphi: np.ndarray, omega: np.ndarray) -> dict:
    """
    Very simple triad:
      E ≈ ⟨dphi^2⟩
      I ≈ var(dphi)
      C ≈ ⟨omega⟩
    """
    flat = dphi.ravel()
    E = float(np.mean(flat**2))
    I = float(np.var(flat))
    C = float(np.mean(omega))
    # pseudo load ratio vs H7
    H7 = 0.70
    lambda_eff = abs(C - H7) / (1.0 + H7)
    return {
        "E": E,
        "I": I,
        "C": C,
        "lambda_eff": lambda_eff,
    }


def make_visuals(dphi: np.ndarray,
                 omega: np.ndarray,
                 out_dir: Path,
                 prefix: str) -> dict:
    """
    Generate three core sharp visuals:
      • central Δφ slice
      • max-projection Δφ
      • max-projection Ω
    """
    paths = {}
    out_dir.mkdir(parents=True, exist_ok=True)

    if not MATPLOTLIB_OK:
        return paths

    # Assume AFM volume shape (t, y, x) or (z, y, x). We treat last two as spatial.
    arr = dphi
    if arr.ndim == 3:
        t_mid = arr.shape[0] // 2
        central = arr[t_mid, :, :]
        maxproj = arr.max(axis=0)
    elif arr.ndim == 2:
        central = arr
        maxproj = arr
    else:
        # flatten weird shapes to 2D grid
        central = arr.reshape(int(math.sqrt(arr.size)), -1)
        maxproj = central

    # Ω
    om = omega
    if om.shape != central.shape:
        try:
            om_c = om
            if om_c.ndim == 3:
                t_mid = om_c.shape[0] // 2
                om_central = om_c[t_mid, :, :]
                om_max = om_c.max(axis=0)
            elif om_c.ndim == 2:
                om_central = om_c
                om_max = om_c
            else:
                om_central = om_c.reshape(central.shape)
                om_max = om_central
        except Exception:
            om_central = np.ones_like(central)
            om_max = np.ones_like(maxproj)
    else:
        om_central = om
        om_max = om

    # Central Δφ slice
    fig = plt.figure()
    sharp_c = enhance_field(central)
    plt.imshow(sharp_c, origin="lower", cmap="viridis", interpolation="lanczos")
    plt.title("QIM v6.0.2 AFM Δφ central slice")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central.png"
    plt.savefig(p_c.as_posix(), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(p_c)

    # Δφ max projection
    fig = plt.figure()
    sharp_m = enhance_field(maxproj)
    plt.imshow(sharp_m, origin="lower", cmap="viridis", interpolation="lanczos")
    plt.title("QIM v6.0.2 AFM Δφ max projection")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj.png"
    plt.savefig(p_m.as_posix(), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(p_m)

    # Ω max projection
    fig = plt.figure()
    sharp_om = enhance_field(om_max)
    plt.imshow(sharp_om, origin="lower", cmap="viridis", interpolation="lanczos")
    plt.title("QIM v6.0.2 AFM Ω max projection (GEO v1.0)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj.png"
    plt.savefig(p_o.as_posix(), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj"] = str(p_o)

    return paths


def write_state(root_dir: Path,
                state_dir: Path,
                metrics: dict,
                visuals: dict,
                afm_path: Path) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state_path = state_dir / f"qim_v6_0_2_state_{now}.json"

    payload = {
        "meta": {
            "node": "QIM",
            "version": "6.0.2",
            "mode": "afm-sharp-crystal",
            "timestamp_utc": now,
            "root_dir": str(root_dir),
        },
        "constants": {
            "H7": 0.70,
            "H7B": "ΔΦ Cusp Law v2.8",
            "H16": "Insight geometry",
            "H19": "Global Δφ integration",
            "H31": "Harmonic stability",
            "GEO_v1_0": "Ω = 1/(1+|Δφ|)",
        },
        "input": {
            "afm_path": str(afm_path),
        },
        "metrics": metrics,
        "visuals": visuals,
    }

    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return state_path


def append_log(logs_dir: Path, text: str) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = logs_dir / f"qim_v6_0_2_run_{now}.log"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(text + "\n")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="QIM v6.0.2 AFM Sharp-Crystal Engine")
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)  # reserved, not used heavily here
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--input_afm_dir", required=True)

    args = parser.parse_args(argv)

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)   # noqa: F841
    logs_dir = Path(args.logs_dir)
    input_afm_dir = Path(args.input_afm_dir)

    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("QIM v6.0.2 ? AFM Sharp-Crystal Engine starting?")
    log(f"root_dir   : {root_dir}")
    log(f"state_dir  : {state_dir}")
    log(f"visuals_dir: {visuals_dir}")
    log(f"ledger_dir : {ledger_dir}")
    log(f"logs_dir   : {logs_dir}")
    log(f"input_dir  : {input_afm_dir}")

    try:
        afm_path = input_afm_dir / "afm_v5_5.npy"
        if not afm_path.exists():
            raise FileNotFoundError(f"AFM cube not found: {afm_path}")

        afm_cube = np.load(afm_path)
        log(f"[AFM] Real AFM cube loaded from {afm_path}")
        log(f"[AFM] Shape = {afm_cube.shape}, dtype = {afm_cube.dtype}")

        dphi = compute_delta_phi(afm_cube)
        omega = compute_omega(dphi)

        metrics = compute_metrics(dphi, omega)
        log(f"[Metrics] E={metrics['E']:.6g}, I={metrics['I']:.6g}, C={metrics['C']:.6g}, λ_eff={metrics['lambda_eff']:.6g}")

        visuals = make_visuals(dphi, omega, visuals_dir, "qim_v6_0_2_afm")

        for k, v in visuals.items():
            log(f"[Visual] {k} → {v}")

        state_path = write_state(root_dir, state_dir, metrics, visuals, afm_path)
        log(f"[State] Written → {state_path}")

        append_log(logs_dir, "\n".join(log_lines))
        log("QIM v6.0.2 AFM Sharp-Crystal Engine complete.")
        return 0

    except Exception as e:
        tb = traceback.format_exc()
        log(f"QIM v6.0.2 encountered an error: {e!r}")
        log(tb)
        append_log(logs_dir, "\n".join(log_lines) + "\n" + tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
