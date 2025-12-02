#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.4 — AFM↔QCX ENTANGLEMENT SUPER-RESOLUTION ENGINE     ║
# ║  REAL AFM + QCX v10.3 · Δφ + Ω + ENTANGLEMENT INDEX          ║
# ║  SHARP VISUALS (PERCENTILE CLIP + HIGH DPI)                  ║
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

EPS = 1e-8
VERSION = "6.4"


def geo_omega(dphi: np.ndarray) -> np.ndarray:
    """
    GEO v1.0 deviation-weighted metric:
      Ω = 1 / (1 + |Δφ|)
    """
    return 1.0 / (1.0 + np.abs(dphi))


def superres(field: np.ndarray, factor: int) -> np.ndarray:
    """
    Simple super-resolution via cubic zoom.
    factor = 12 by default (QIM v6.4 spec).
    """
    if factor <= 1:
        return field
    try:
        return ndi.zoom(field, factor, order=3)
    except Exception:
        return field


def enhance_2d(field2d: np.ndarray) -> np.ndarray:
    """
    2D sharpener for visuals:
      • slight Gaussian blur
      • unsharp mask (0.8 gain)
    Works on already super-res slices/projections.
    """
    blurred = ndi.gaussian_filter(field2d, sigma=1.0)
    sharpened = field2d + 0.8 * (field2d - blurred)
    return sharpened


def compute_delta_phi(field: np.ndarray) -> np.ndarray:
    """Δφ = field - mean(field)."""
    mean_val = float(field.mean())
    return field - mean_val


def compute_metrics(dphi_afm: np.ndarray,
                    dphi_qcx: np.ndarray,
                    omega_afm: np.ndarray,
                    omega_qcx: np.ndarray) -> dict:
    """
    Triad + entanglement:
      E ≈ (⟨dphi_afm^2⟩ + ⟨dphi_qcx^2⟩)/2
      I ≈ var(dphi_afm) + var(dphi_qcx)
      C ≈ (⟨omega_afm⟩ + ⟨omega_qcx⟩)/2
      λ_eff ~ (1 - (C - H7)^2) as a simple cusp-adjacent proxy
      entanglement_index: curvature cross-correlation (AFM vs QCX)
    """
    H7 = 0.70

    flat_afm = dphi_afm.ravel()
    flat_qcx = dphi_qcx.ravel()

    E = float(np.mean(flat_afm**2) + np.mean(flat_qcx**2)) / 2.0
    I = float(np.var(flat_afm) + np.var(flat_qcx))
    C = float((np.mean(omega_afm) + np.mean(omega_qcx)) / 2.0)

    lambda_eff = float(1.0 - (C - H7) ** 2)

    # Curvature-based entanglement (Ω Laplacian)
    curv_afm = np.abs(ndi.laplace(omega_afm))
    curv_qcx = np.abs(ndi.laplace(omega_qcx))

    fa = curv_afm.ravel()
    fq = curv_qcx.ravel()

    fa = fa - fa.mean()
    fq = fq - fq.mean()

    denom = float(np.linalg.norm(fa) * np.linalg.norm(fq) + EPS)
    entanglement_index = float(np.dot(fa, fq) / denom)

    return {
        "E": E,
        "I": I,
        "C": C,
        "lambda_eff": lambda_eff,
        "entanglement_index": entanglement_index,
    }


def save_sharp_2d(data: np.ndarray, path: Path, title: str) -> None:
    """
    High-contrast 2D render:
      • 1%–99% percentile clipping for better structure
      • unsharp mask
      • 300 DPI for print-ready stills
    """
    if not MATPLOTLIB_OK:
        return

    vmin, vmax = np.percentile(data, [1.0, 99.0])
    if (not np.isfinite(vmin)) or (not np.isfinite(vmax)) or (vmax <= vmin):
        vmin = float(np.min(data))
        vmax = float(np.max(data))

    sharp = enhance_2d(data)

    fig = plt.figure(figsize=(6, 6), dpi=300)
    plt.imshow(sharp, origin="lower", cmap="viridis",
               vmin=vmin, vmax=vmax, interpolation="lanczos")
    plt.title(title)
    plt.colorbar()
    plt.tight_layout()
    fig.savefig(path.as_posix(), bbox_inches="tight")
    plt.close(fig)


def make_visuals(dphi_afm: np.ndarray,
                 dphi_qcx: np.ndarray,
                 omega_afm: np.ndarray,
                 omega_qcx: np.ndarray,
                 out_dir: Path,
                 base: str) -> dict:
    """
    Core QIM v6.4 visuals:
      AFM:
        • Δφ central slice (super-res)
        • Δφ max projection
        • Ω max projection
        • curvature proxy max projection
      QCX:
        • Δφ max projection
        • Ω max projection
        • curvature proxy max projection
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    # Assume (z, y, x)
    z_mid = dphi_afm.shape[0] // 2

    afm_dphi_central = dphi_afm[z_mid]
    afm_dphi_maxproj = dphi_afm.max(axis=0)
    afm_omega_maxproj = omega_afm.max(axis=0)
    afm_curv = np.abs(ndi.laplace(omega_afm))
    afm_curv_maxproj = afm_curv.max(axis=0)

    qcx_dphi_maxproj = dphi_qcx.max(axis=0)
    qcx_omega_maxproj = omega_qcx.max(axis=0)
    qcx_curv = np.abs(ndi.laplace(omega_qcx))
    qcx_curv_maxproj = qcx_curv.max(axis=0)

    afm_dphi_central_path = out_dir / f"{base}_afm_dphi_central.png"
    afm_dphi_maxproj_path = out_dir / f"{base}_afm_dphi_maxproj.png"
    afm_omega_maxproj_path = out_dir / f"{base}_afm_omega_maxproj.png"
    afm_curvature_path = out_dir / f"{base}_afm_curvature.png"

    qcx_dphi_maxproj_path = out_dir / f"{base}_qcx_dphi_maxproj.png"
    qcx_omega_maxproj_path = out_dir / f"{base}_qcx_omega_maxproj.png"
    qcx_curvature_path = out_dir / f"{base}_qcx_curvature.png"

    save_sharp_2d(
        afm_dphi_central,
        afm_dphi_central_path,
        "QIM v6.4 AFM Δφ central slice (super-res)",
    )
    save_sharp_2d(
        afm_dphi_maxproj,
        afm_dphi_maxproj_path,
        "QIM v6.4 AFM Δφ max projection (super-res)",
    )
    save_sharp_2d(
        afm_omega_maxproj,
        afm_omega_maxproj_path,
        "QIM v6.4 AFM Ω max projection (GEO v1.0)",
    )
    save_sharp_2d(
        afm_curv_maxproj,
        afm_curvature_path,
        "QIM v6.4 AFM curvature proxy (Ω Laplace)",
    )

    save_sharp_2d(
        qcx_dphi_maxproj,
        qcx_dphi_maxproj_path,
        "QIM v6.4 QCX Δφ max projection (super-res)",
    )
    save_sharp_2d(
        qcx_omega_maxproj,
        qcx_omega_maxproj_path,
        "QIM v6.4 QCX Ω max projection (GEO v1.0)",
    )
    save_sharp_2d(
        qcx_curv_maxproj,
        qcx_curvature_path,
        "QIM v6.4 QCX curvature proxy (Ω Laplace)",
    )

    paths["afm_dphi_central"] = str(afm_dphi_central_path)
    paths["afm_dphi_maxproj"] = str(afm_dphi_maxproj_path)
    paths["afm_omega_maxproj"] = str(afm_omega_maxproj_path)
    paths["afm_curvature"] = str(afm_curvature_path)
    paths["qcx_dphi_maxproj"] = str(qcx_dphi_maxproj_path)
    paths["qcx_omega_maxproj"] = str(qcx_omega_maxproj_path)
    paths["qcx_curvature"] = str(qcx_curvature_path)

    return paths


def write_state(root_dir: Path,
                state_dir: Path,
                metrics: dict,
                visuals: dict,
                afm_path: Path,
                qcx_path: Path,
                superres_factor: int,
                timestamp: str) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"qim_v6_4_state_{timestamp}.json"

    payload = {
        "meta": {
            "node": "QIM",
            "version": VERSION,
            "mode": "afm-qcx-entangle-superres",
            "timestamp_utc": timestamp,
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
            "qcx_path": str(qcx_path),
            "superres_factor": int(superres_factor),
        },
        "metrics": metrics,
        "visuals": visuals,
    }

    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return state_path


def append_ledger(ledger_dir: Path,
                  metrics: dict,
                  timestamp: str,
                  state_path: Path,
                  visuals: dict) -> Path:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / "qim_v6_4_ledger.jsonl"

    record = {
        "timestamp_utc": timestamp,
        "version": VERSION,
        "mode": "afm-qcx-entangle-superres",
        "metrics": metrics,
        "paths": {
            "state": str(state_path),
            "visuals": visuals,
        },
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return ledger_path


def append_log(logs_dir: Path, lines: list, timestamp: str) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"qim_v6_4_run_{timestamp}.log"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="QIM v6.4 AFM↔QCX Entanglement Super-Resolution Engine"
    )
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--afm_path", required=True)
    parser.add_argument("--qcx_path", required=True)
    parser.add_argument("--superres_factor", type=int, default=12)

    args = parser.parse_args(argv)

    root_dir = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir)

    afm_path = Path(args.afm_path)
    qcx_path = Path(args.qcx_path)
    factor = int(args.superres_factor)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    log_lines = []

    def log(msg: str) -> None:
        print(msg)
        log_lines.append(msg)

    log("QIM v6.4 · AFM↔QCX Entanglement Engine starting…")
    log(f"root_dir   : {root_dir}")
    log(f"state_dir  : {state_dir}")
    log(f"visuals_dir: {visuals_dir}")
    log(f"ledger_dir : {ledger_dir}")
    log(f"logs_dir   : {logs_dir}")
    log(f"afm_path   : {afm_path}")
    log(f"qcx_path   : {qcx_path}")
    log(f"superres_factor: {factor}")

    try:
        if not afm_path.exists():
            raise FileNotFoundError(f"AFM cube not found: {afm_path}")
        if not qcx_path.exists():
            raise FileNotFoundError(f"QCX field not found: {qcx_path}")

        afm = np.load(afm_path)
        qcx = np.load(qcx_path)

        log(f"[AFM] Shape = {afm.shape}, dtype = {afm.dtype}")
        log(f"[QCX] Shape = {qcx.shape}, dtype = {qcx.dtype}")

        # Super-resolution volumes
        afm_sr = superres(afm, factor)
        qcx_sr = superres(qcx, factor)

        # Δφ fields
        dphi_afm = compute_delta_phi(afm_sr)
        dphi_qcx = compute_delta_phi(qcx_sr)

        # Ω error geometry fields
        omega_afm = geo_omega(dphi_afm)
        omega_qcx = geo_omega(dphi_qcx)

        metrics = compute_metrics(dphi_afm, dphi_qcx, omega_afm, omega_qcx)
        log(
            "[Metrics] "
            f"E={metrics['E']:.6g}, "
            f"I={metrics['I']:.6g}, "
            f"C={metrics['C']:.6g}, "
            f"λ_eff={metrics['lambda_eff']:.6g}, "
            f"entanglement_index={metrics['entanglement_index']:.6g}"
        )

        visuals = make_visuals(
            dphi_afm,
            dphi_qcx,
            omega_afm,
            omega_qcx,
            visuals_dir,
            "qim_v6_4_afm_qcx",
        )
        for k, v in visuals.items():
            log(f"[Visual] {k} → {v}")

        state_path = write_state(
            root_dir,
            state_dir,
            metrics,
            visuals,
            afm_path,
            qcx_path,
            factor,
            timestamp,
        )
        log(f"[State] Written → {state_path}")

        ledger_path = append_ledger(
            ledger_dir,
            metrics,
            timestamp,
            state_path,
            visuals,
        )
        log(f"[Ledger] Appended → {ledger_path}")

        append_log(logs_dir, log_lines, timestamp)
        log("QIM v6.4 AFM↔QCX Entanglement Engine complete.")
        return 0

    except Exception as e:
        tb = traceback.format_exc()
        log(f"QIM v6.4 encountered an error: {e!r}")
        log(tb)
        append_log(logs_dir, log_lines + [tb], timestamp)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
