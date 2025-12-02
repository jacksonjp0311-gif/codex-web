#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.3 — AFM SUPER-RESOLUTION ENGINE (12×)                ║
# ║  Real AFM Δφ, Ω (GEO v1.0), curvature, 12× super-res slices  ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
import math
import sys
import traceback
from dataclasses import dataclass, asdict
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
# Δφ GEOMETRY HELPERS
# ─────────────────────────────────────────────────────────────

def enhance_field(field, up_factor: int = 12):
    """
    Codex QIM v6.3 sharpener (GEO v1.0 aligned):
      • up_factor× cubic upsample (default 12×)
      • Gaussian blur at geometry-scaled sigma
      • Unsharp mask (0.8 gain)
    """
    try:
        field = np.asarray(field, dtype=np.float32)
        up = ndi.zoom(field, up_factor, order=3)
    except Exception:
        return field

    # Geometry-aware blur scale: keep edges crisp as resolution grows
    base = max(up.shape) / float(64 * up_factor)
    sigma = max(0.5, base)
    blurred = ndi.gaussian_filter(up, sigma=sigma)
    sharpened = up + 0.8 * (up - blurred)
    return sharpened


def load_afm_cube(path: Path) -> np.ndarray:
    arr = np.load(str(path))
    return np.asarray(arr, dtype=np.float32)


@dataclass
class QimMetrics:
    E: float
    I: float
    C: float
    lambda_eff: float


def compute_metrics(field: np.ndarray) -> QimMetrics:
    """
    Simple Δφ error-geometry metrics:
      E = mean |Δφ|
      I = std(Δφ)
      λ_eff = I / (E + ε)  (effective loading)
      C = 1 / (1 + λ_eff)  (coherence; ≈ H7 when λ_eff ~ 0.43)
    """
    dphi = field - np.mean(field)
    E = float(np.mean(np.abs(dphi)))
    I = float(np.std(dphi))
    eps = 1e-9
    lam = float(I / (E + eps))
    if lam < 0.0:
        lam = 0.0
    if lam > 1.0:
        lam = 1.0
    C = float(1.0 / (1.0 + lam))
    return QimMetrics(E=E, I=I, C=C, lambda_eff=lam)


# ─────────────────────────────────────────────────────────────
# VISUALS
# ─────────────────────────────────────────────────────────────

def make_superres_visuals(dphi: np.ndarray,
                          omega: np.ndarray,
                          out_dir: Path,
                          prefix: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    if not MATPLOTLIB_OK:
        return paths

    # Assume AFM cube is (z, y, x)
    z_dim, y_dim, x_dim = dphi.shape
    z_mid = z_dim // 2

    # Central Δφ slice (z-mid)
    central = dphi[z_mid, :, :]
    fig = plt.figure()
    sr_central = enhance_field(central, up_factor=12)
    plt.imshow(sr_central, cmap="viridis", origin="lower", interpolation="lanczos")
    plt.title("QIM v6.3 AFM Δφ central slice (12× super-res)")
    plt.colorbar()
    p_c = out_dir / f"{prefix}_dphi_central_superres.png"
    fig.savefig(str(p_c), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central_superres"] = str(p_c)

    # Δφ max projection over z
    maxproj = dphi.max(axis=0)
    fig = plt.figure()
    sr_max = enhance_field(maxproj, up_factor=12)
    plt.imshow(sr_max, cmap="viridis", origin="lower", interpolation="lanczos")
    plt.title("QIM v6.3 AFM Δφ max projection (12× super-res)")
    plt.colorbar()
    p_m = out_dir / f"{prefix}_dphi_maxproj_superres.png"
    fig.savefig(str(p_m), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj_superres"] = str(p_m)

    # Ω max projection (GEO v1.0)
    omega_max = omega.max(axis=0)
    fig = plt.figure()
    sr_omega = enhance_field(omega_max, up_factor=12)
    plt.imshow(sr_omega, cmap="viridis", origin="lower", interpolation="lanczos")
    plt.title("QIM v6.3 AFM Ω max projection (GEO v1.0, 12×)")
    plt.colorbar()
    p_o = out_dir / f"{prefix}_omega_maxproj_superres.png"
    fig.savefig(str(p_o), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["omega_maxproj_superres"] = str(p_o)

    # Curvature proxy (Laplacian of Ω max)
    curvature = np.abs(ndi.laplace(omega_max))
    fig = plt.figure()
    sr_curv = enhance_field(curvature, up_factor=12)
    plt.imshow(sr_curv, cmap="viridis", origin="lower", interpolation="lanczos")
    plt.title("QIM v6.3 AFM curvature proxy (Ω Laplace, 12×)")
    plt.colorbar()
    p_k = out_dir / f"{prefix}_curvature_superres.png"
    fig.savefig(str(p_k), dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["curvature_superres"] = str(p_k)

    return paths


# ─────────────────────────────────────────────────────────────
# STATE + LEDGER
# ─────────────────────────────────────────────────────────────

def write_state(root_dir: Path,
                state_dir: Path,
                afm_path: Path,
                metrics: QimMetrics,
                visuals: dict) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state_path = state_dir / f"qim_v6_2_state_{ts}.json"

    payload = {
        "meta": {
            "node": "QIM",
            "version": "6.3.1",
            "mode": "afm-superres-12x-entangle",
            "timestamp_utc": ts,
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
        "metrics": asdict(metrics),
        "visuals": visuals,
    }

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return state_path


def append_ledger(ledger_dir: Path,
                  metrics: QimMetrics,
                  visuals: dict) -> Path:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger_path = ledger_dir / "qim_v6_2_ledger.jsonl"

    entry = {
        "timestamp_utc": ts,
        "version": "6.3.1",
        "mode": "afm-superres-12x-entangle",
        "metrics": asdict(metrics),
        "visuals": visuals,
    }

    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return ledger_path


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="QIM v6.3 — AFM Super-Resolution Engine (12×)"
    )
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--input_afm_path", required=True)

    args = parser.parse_args(argv)

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir)
    afm_path = Path(args.input_afm_path)

    logs_dir.mkdir(parents=True, exist_ok=True)
    log_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = logs_dir / f"qim_v6_2_run_{log_ts}.log"

    log_lines = []
    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    log("QIM v6.3 · AFM Super-Resolution Engine (12×) starting…")
    log(f"root_dir   : {root_dir}")
    log(f"state_dir  : {state_dir}")
    log(f"visuals_dir: {visuals_dir}")
    log(f"ledger_dir : {ledger_dir}")
    log(f"logs_dir   : {logs_dir}")
    log(f"afm_path   : {afm_path}")

    try:
        if not afm_path.exists():
            raise FileNotFoundError(f"AFM cube not found at {afm_path}")

        afm = load_afm_cube(afm_path)
        log(f"[AFM] Real AFM cube loaded from {afm_path}")
        log(f"[AFM] Shape = {afm.shape}, dtype = {afm.dtype}")

        dphi = afm - np.mean(afm)
        omega = 1.0 / (1.0 + np.abs(dphi))

        metrics = compute_metrics(dphi)
        log(f"[Metrics] E={metrics.E:.7f}, I={metrics.I:.7f}, C={metrics.C:.6f}, λ_eff={metrics.lambda_eff:.7f}")

        visuals = make_superres_visuals(dphi, omega, visuals_dir, "qim_v6_2_afm")
        for k, v in visuals.items():
            log(f"[Visual] {k} → {v}")

        state_path = write_state(root_dir, state_dir, afm_path, metrics, visuals)
        log(f"[State] Written → {state_path}")

        ledger_path = append_ledger(ledger_dir, metrics, visuals)
        log(f"[Ledger] Appended → {ledger_path}")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")

        log("QIM v6.3 run complete.")
        return 0

    except Exception as e:
        err_msg = f"QIM v6.3 encountered an error: {repr(e)}"
        log(err_msg)
        tb = traceback.format_exc()
        log(tb)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


