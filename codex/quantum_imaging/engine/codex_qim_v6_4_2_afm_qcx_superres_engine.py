#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v6.4.2 — AFM↔QCX ENTANGLEMENT SUPER-RES ENGINE          ║
# ║  REAL AFM + QCX v10.3 Δφ · 12× SUPERRES · GEO v1.0           ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

VERSION = "6.4.2"
EPS = 1e-8


def geo_omega(dphi: np.ndarray) -> np.ndarray:
    """GEO v1.0: Ω = 1 / (1 + |Δφ|)."""
    return 1.0 / (1.0 + np.abs(dphi))


def enhance_field(field: np.ndarray) -> np.ndarray:
    """
    QIM v6.4.2 sharpener:
      • 4× cubic upsample
      • Gaussian blur
      • Unsharp mask (0.9 gain)
    """
    try:
        up = ndi.zoom(field, 4, order=3)
    except Exception:
        return field
    blurred = ndi.gaussian_filter(up, sigma=1.0)
    sharpened = up + 0.9 * (up - blurred)
    return sharpened


def percentile_window(data: np.ndarray, lo: float = 2.0, hi: float = 98.0) -> tuple[float, float]:
    vmin, vmax = np.percentile(data, [lo, hi])
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        vmin = float(np.min(data))
        vmax = float(np.max(data))
    return float(vmin), float(vmax)


def load_npy(path: Path) -> np.ndarray:
    arr = np.load(path.as_posix())
    if arr.dtype not in (np.float32, np.float64):
        arr = arr.astype(np.float32)
    return arr


def compute_metrics(dphi_afm: np.ndarray,
                    dphi_qcx: np.ndarray,
                    omega_afm: np.ndarray,
                    omega_qcx: np.ndarray) -> dict:
    """
    Triadic + entanglement:
      E = ½ (⟨|Δφ_afm|⟩ + ⟨|Δφ_qcx|⟩)
      I = var_afm + var_qcx
      C = ½ (⟨Ω_afm⟩ + ⟨Ω_qcx⟩)
      λ_eff ~ coherence proximity to H7
      entanglement_index = corr(curv_afm, curv_qcx)
    """
    E = float(0.5 * (np.mean(np.abs(dphi_afm)) + np.mean(np.abs(dphi_qcx))))
    I = float(np.var(dphi_afm) + np.var(dphi_qcx))
    C = float(0.5 * (np.mean(omega_afm) + np.mean(omega_qcx)))

    H7 = 0.70
    lambda_eff = float(1.0 - (C - H7) ** 2)

    curv_afm = np.abs(ndi.laplace(omega_afm))
    curv_qcx = np.abs(ndi.laplace(omega_qcx))

    af = curv_afm.ravel().astype(np.float64)
    qf = curv_qcx.ravel().astype(np.float64)

    af -= af.mean()
    qf -= qf.mean()

    denom = float(np.linalg.norm(af) * np.linalg.norm(qf) + EPS)
    entanglement_index = float(np.dot(af, qf) / denom)

    return {
        "E": E,
        "I": I,
        "C": C,
        "lambda_eff": lambda_eff,
        "entanglement_index": entanglement_index,
    }


def save_imshow(data: np.ndarray,
                out_path: Path,
                title: str) -> None:
    if not MATPLOTLIB_OK:
        return

    vmin, vmax = percentile_window(data, 1.0, 99.0)
    fig = plt.figure(figsize=(6, 6), dpi=240)
    sharp = enhance_field(data)
    plt.imshow(sharp, origin="lower", vmin=vmin, vmax=vmax,
               cmap="viridis", interpolation="lanczos")
    plt.title(title)
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(out_path.as_posix(), dpi=320, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    import sys
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="QIM v6.4.2 — AFM↔QCX Entanglement Super-Res Engine"
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

    root_dir   = Path(args.root_dir)
    state_dir  = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir   = Path(args.logs_dir)
    afm_path   = Path(args.afm_path)
    qcx_path   = Path(args.qcx_path)
    factor     = int(args.superres_factor)

    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path  = logs_dir / f"qim_v6_4_2_run_{timestamp}.log"

    log_lines: list[str] = []

    def log(msg: str) -> None:
        print(msg)
        log_lines.append(msg)

    log("QIM v6.4.2 · AFM↔QCX Entanglement Engine starting…")
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

        afm = load_npy(afm_path)
        qcx = load_npy(qcx_path)

        log(f"[AFM] shape={afm.shape}, dtype={afm.dtype}")
        log(f"[QCX] shape={qcx.shape}, dtype={qcx.dtype}")

        # Super-resolution 3D zoom
        zoom_factors = (factor, factor, factor) if afm.ndim == 3 else factor
        afm_sr = ndi.zoom(afm, zoom_factors, order=1)
        qcx_sr = ndi.zoom(qcx, zoom_factors, order=1)

        dphi_afm = afm_sr - np.mean(afm_sr)
        dphi_qcx = qcx_sr - np.mean(qcx_sr)

        omega_afm = geo_omega(dphi_afm)
        omega_qcx = geo_omega(dphi_qcx)

        metrics = compute_metrics(dphi_afm, dphi_qcx, omega_afm, omega_qcx)
        log(f"[Metrics] {metrics}")

        # Slicing for visuals
        if dphi_afm.ndim == 3:
            z_mid = dphi_afm.shape[0] // 2
            afm_central = dphi_afm[z_mid]
            afm_maxproj = dphi_afm.max(axis=0)
            qcx_maxproj = dphi_qcx.max(axis=0)
            omega_afm_max = omega_afm.max(axis=0)
            omega_qcx_max = omega_qcx.max(axis=0)
        else:
            afm_central = dphi_afm
            afm_maxproj = dphi_afm
            qcx_maxproj = dphi_qcx
            omega_afm_max = omega_afm
            omega_qcx_max = omega_qcx

        base = "qim_v6_4_2_afm_qcx"

        afm_central_path = visuals_dir / f"{base}_afm_dphi_central.png"
        afm_maxproj_path = visuals_dir / f"{base}_afm_dphi_maxproj.png"
        afm_omega_path   = visuals_dir / f"{base}_afm_omega_maxproj.png"
        qcx_maxproj_path = visuals_dir / f"{base}_qcx_dphi_maxproj.png"
        qcx_omega_path   = visuals_dir / f"{base}_qcx_omega_maxproj.png"

        save_imshow(afm_central, afm_central_path,
                    "QIM v6.4.2 AFM Δφ central slice (12× super-res)")
        save_imshow(afm_maxproj, afm_maxproj_path,
                    "QIM v6.4.2 AFM Δφ max projection (12×)")
        save_imshow(omega_afm_max, afm_omega_path,
                    "QIM v6.4.2 AFM Ω max projection (GEO v1.0)")
        save_imshow(qcx_maxproj, qcx_maxproj_path,
                    "QIM v6.4.2 QCX Δφ max projection (12×)")
        save_imshow(omega_qcx_max, qcx_omega_path,
                    "QIM v6.4.2 QCX Ω max projection (GEO v1.0)")

        visuals = {
            "afm_dphi_central": afm_central_path.name,
            "afm_dphi_maxproj": afm_maxproj_path.name,
            "afm_omega_maxproj": afm_omega_path.name,
            "qcx_dphi_maxproj": qcx_maxproj_path.name,
            "qcx_omega_maxproj": qcx_omega_path.name,
        }

        now_utc = timestamp

        state_payload = {
            "meta": {
                "node": "QIM",
                "version": VERSION,
                "mode": "afm-qcx-entangle-superres",
                "timestamp_utc": now_utc,
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
                "superres_factor": factor,
            },
            "metrics": metrics,
            "visuals": visuals,
        }

        state_path = state_dir / f"qim_v6_4_2_state_{now_utc}.json"
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state_payload, f, indent=2)
        log(f"[State] Written → {state_path}")

        ledger_path = ledger_dir / "qim_v6_4_2_ledger.jsonl"
        with ledger_path.open("a", encoding="utf-8") as f:
            entry = {
                "timestamp_utc": now_utc,
                "version": VERSION,
                "mode": "afm-qcx-entangle-superres",
                "metrics": metrics,
                "paths": {
                    "state": str(state_path),
                    "afm_dphi_central": str(afm_central_path),
                    "afm_dphi_maxproj": str(afm_maxproj_path),
                    "afm_omega_maxproj": str(afm_omega_path),
                    "qcx_dphi_maxproj": str(qcx_maxproj_path),
                    "qcx_omega_maxproj": str(qcx_omega_path),
                },
            }
            f.write(json.dumps(entry) + "\n")
        log(f"[Ledger] Appended → {ledger_path}")

        with log_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")

        log("QIM v6.4.2 run complete.")
        return 0

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log(f"QIM v6.4.2 encountered an error: {e!r}")
        log(tb)
        with log_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n" + tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

