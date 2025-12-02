#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.1 — AFM SUPER-RESOLUTION ENGINE                      ║
# ║  Real AFM cube → Δφ, Ω (GEO v1.0), 8× super-res visuals      ║
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


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def now_utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def log(msg: str, log_path: Path | None):
    line = msg.rstrip()
    print(line)
    if log_path is not None:
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            # Logging must never crash the engine
            pass


def load_afm_cube(path: Path, log_path: Path | None):
    if not path.exists():
        raise FileNotFoundError(f"AFM cube not found: {path}")
    arr = np.load(str(path))
    log(f"[AFM] Real AFM cube loaded from {path}", log_path)
    log(f"[AFM] Shape = {arr.shape}, dtype = {arr.dtype}", log_path)
    return arr.astype(np.float32)


def compute_dphi_and_omega(afm: np.ndarray):
    """
    Δφ = field - mean(field)
    Ω  = 1 / (1 + |Δφ|)   (GEO v1.0 deviation-weighted metric)
    """
    mean_val = float(afm.mean())
    dphi = afm - mean_val
    omega = 1.0 / (1.0 + np.abs(dphi))
    return dphi, omega


def enhance_superres(field2d: np.ndarray, factor: int = 8) -> np.ndarray:
    """
    AFM Super-Resolution:
      • factor× cubic upsample (default 8×)
      • gentle Gaussian blur
      • unsharp mask (0.9 gain)
    """
    try:
        up = ndi.zoom(field2d, factor, order=3)
    except Exception:
        return field2d
    blurred = ndi.gaussian_filter(up, sigma=1.0)
    sharpened = up + 0.9 * (up - blurred)
    return sharpened


def make_superres_visuals(dphi: np.ndarray,
                          omega: np.ndarray,
                          out_dir: Path,
                          prefix: str,
                          log_path: Path | None):
    if not MATPLOTLIB_OK:
        log("[Visual] matplotlib not available; skipping visuals.", log_path)
        return {}

    out_dir.mkdir(parents=True, exist_ok=True)

    T, X, Y = dphi.shape
    t_mid = T // 2

    # central slice (time-mid)
    central = dphi[t_mid, :, :]
    central_sr = enhance_superres(central, factor=8)

    fig = plt.figure()
    plt.imshow(central_sr, origin="lower", cmap="viridis")
    plt.title("QIM v6.1 AFM Δφ central slice (8× super-res)")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_afm_dphi_central_superres.png"
    plt.savefig(str(p_c), dpi=300, bbox_inches="tight")
    plt.close(fig)
    log(f"[Visual] dphi_central_superres → {p_c}", log_path)

    # Δφ max projection
    maxproj = dphi.max(axis=0)
    maxproj_sr = enhance_superres(maxproj, factor=8)

    fig = plt.figure()
    plt.imshow(maxproj_sr, origin="lower", cmap="viridis")
    plt.title("QIM v6.1 AFM Δφ max projection (8× super-res)")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_afm_dphi_maxproj_superres.png"
    plt.savefig(str(p_m), dpi=300, bbox_inches="tight")
    plt.close(fig)
    log(f"[Visual] dphi_maxproj_superres → {p_m}", log_path)

    # Ω max projection (GEO v1.0)
    omega_max = omega.max(axis=0)
    omega_max_sr = enhance_superres(omega_max, factor=8)

    fig = plt.figure()
    plt.imshow(omega_max_sr, origin="lower", cmap="viridis")
    plt.title("QIM v6.1 AFM Ω max projection (GEO v1.0, 8× super-res)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_afm_omega_maxproj_superres.png"
    plt.savefig(str(p_o), dpi=300, bbox_inches="tight")
    plt.close(fig)
    log(f"[Visual] omega_maxproj_superres → {p_o}", log_path)

    return {
        "dphi_central_superres": str(p_c),
        "dphi_maxproj_superres": str(p_m),
        "omega_maxproj_superres": str(p_o),
    }


def compute_metrics(dphi: np.ndarray, omega: np.ndarray):
    """
    Simple Codex metrics:
      • E = mean(|Δφ|)
      • I = std(|Δφ|)
      • C = mean(ω)
      • λ_eff ~ E / (1 + C)  (proxy load ratio vs coherence)
    """
    abs_dphi = np.abs(dphi)
    E = float(abs_dphi.mean())
    I = float(abs_dphi.std())
    C = float(omega.mean())
    lambda_eff = float(E / (1.0 + C))
    return E, I, C, lambda_eff


def write_state_ledger(root_dir: Path,
                       state_dir: Path,
                       ledger_dir: Path,
                       afm_path: Path,
                       metrics: dict,
                       visuals: dict,
                       log_path: Path | None):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    tag = now_utc_tag()

    state = {
        "meta": {
            "node": "QIM",
            "version": "6.1",
            "mode": "afm-superres",
            "timestamp_utc": tag,
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

    state_path = state_dir / f"qim_v6_1_state_{tag}.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    log(f"[State] Written → {state_path}", log_path)

    ledger_record = {
        "timestamp_utc": tag,
        "version": "6.1",
        "mode": "afm-superres",
        "metrics": metrics,
        "visuals": visuals,
    }
    ledger_path = ledger_dir / "qim_v6_1_ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_record) + "\n")
    log(f"[Ledger] Appended → {ledger_path}", log_path)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="QIM v6.1 — AFM Super-Resolution Engine")
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--input_afm_dir", required=True)
    args = parser.parse_args(argv)

    root_dir = Path(args.root_dir).resolve()
    state_dir = Path(args.state_dir).resolve()
    visuals_dir = Path(args.visuals_dir).resolve()
    ledger_dir = Path(args.ledger_dir).resolve()
    logs_dir = Path(args.logs_dir).resolve()
    input_afm_dir = Path(args.input_afm_dir).resolve()

    logs_dir.mkdir(parents=True, exist_ok=True)
    run_tag = now_utc_tag()
    log_path = logs_dir / f"qim_v6_1_run_{run_tag}.log"

    try:
        log(f"QIM v6.1 · AFM Super-Resolution Engine starting…", log_path)
        log(f"root_dir   : {root_dir}", log_path)
        log(f"state_dir  : {state_dir}", log_path)
        log(f"visuals_dir: {visuals_dir}", log_path)
        log(f"ledger_dir : {ledger_dir}", log_path)
        log(f"logs_dir   : {logs_dir}", log_path)
        log(f"input_dir  : {input_afm_dir}", log_path)

        afm_path = input_afm_dir / "afm_v5_5.npy"
        afm = load_afm_cube(afm_path, log_path)

        # Expand to 3D time-lattice if needed (T, X, Y)
        if afm.ndim == 2:
            afm = afm[None, :, :]
        if afm.ndim != 3:
            raise ValueError(f"Expected AFM cube with ndim 2 or 3, got {afm.ndim}")

        dphi, omega = compute_dphi_and_omega(afm)
        E, I, C, lambda_eff = compute_metrics(dphi, omega)

        metrics = {
            "E": E,
            "I": I,
            "C": C,
            "lambda_eff": lambda_eff,
        }
        log(f"[Metrics] E={E:.6g}, I={I:.6g}, C={C:.6g}, λ_eff={lambda_eff:.6g}", log_path)

        visuals = make_superres_visuals(dphi, omega, visuals_dir, "qim_v6_1", log_path)

        write_state_ledger(root_dir, state_dir, ledger_dir, afm_path, metrics, visuals, log_path)

        log("QIM v6.1 run complete.", log_path)
        return 0

    except Exception as exc:
        log(f"QIM v6.1 encountered an error: {repr(exc)}", log_path)
        tb = traceback.format_exc()
        log(tb, log_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
