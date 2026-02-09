#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex Quantum Imaging v2.0 — AFM Volumetric Resonance Engine
Domain : AFM Molecule Imaging • 3D ΔΦ Lattice • Resonant Horizons
Field  : Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
Law    : AFM Stack → Volume → ΔΦ → Horizon → Triad(E,I,C) → State
"""

import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib.pyplot as plt


@dataclass
class TriadicState:
    energy: float
    information: float
    coherence: float
    h7_target: float = 0.70


@dataclass
class QIMVolumeSummary:
    shape: List[int]
    delta_phi_mean: float
    delta_phi_std: float
    gradient_mean: float
    gradient_std: float
    horizon_threshold: float
    triad: TriadicState


@dataclass
class QIMStateEnvelope:
    protocol: str
    version: str
    timestamp: str
    input_dir: str
    state_path: str
    visuals: Dict[str, str]
    volume_summary: QIMVolumeSummary


def load_afm_stack(input_dir: str) -> np.ndarray:
    """
    Load a stack of AFM images from a directory and build a 3D volume (z, y, x),
    normalizing each slice independently to [0, 1].
    """
    files = sorted(
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"))
    )
    if not files:
        raise RuntimeError(f"No AFM image files found in {input_dir}")

    slices = []
    for fname in files:
        path = os.path.join(input_dir, fname)
        img = Image.open(path).convert("L")
        arr = np.array(img, dtype=np.float32)
        # Normalize each slice to [0,1]
        min_val = float(arr.min())
        max_val = float(arr.max())
        arr = (arr - min_val) / (max_val - min_val + 1e-8)
        slices.append(arr)

    volume = np.stack(slices, axis=0)  # (z, y, x)
    return volume


def compute_delta_phi(volume: np.ndarray) -> Dict[str, Any]:
    """
    Compute a 3D gradient-based ΔΦ field from the volume.
    ΔΦ is defined as normalized gradient magnitude minus its mean.
    """
    gz, gy, gx = np.gradient(volume)
    grad_mag = np.sqrt(gx**2 + gy**2 + gz**2)

    g_min = float(grad_mag.min())
    g_max = float(grad_mag.max())
    denom = g_max - g_min + 1e-8
    g_norm = (grad_mag - g_min) / denom

    # ΔΦ as deviation from mean normalized gradient
    delta_phi = g_norm - g_norm.mean()
    delta_phi_mean = float(delta_phi.mean())
    delta_phi_std = float(delta_phi.std())

    gradient_mean = float(grad_mag.mean())
    gradient_std = float(grad_mag.std())

    return {
        "delta_phi": delta_phi,
        "delta_phi_mean": delta_phi_mean,
        "delta_phi_std": delta_phi_std,
        "gradient_mean": gradient_mean,
        "gradient_std": gradient_std,
    }


def compute_entropy(delta_phi: np.ndarray, bins: int = 128) -> float:
    """
    Approximate Shannon entropy of the ΔΦ field using a histogram.
    Normalized by log(bins) to yield a rough [0,1]-like value.
    """
    flat = delta_phi.flatten()
    hist, _ = np.histogram(flat, bins=bins, density=True)
    p = hist + 1e-12
    p = p / p.sum()
    entropy = -np.sum(p * np.log(p))
    entropy_norm = float(entropy / np.log(len(p)))
    return entropy_norm


def compute_triad(delta_phi: np.ndarray,
                  gradient_mean: float,
                  horizon_threshold: float) -> TriadicState:
    """
    Compute Codex triadic state from ΔΦ and gradient statistics.
    Energy    ~ gradient_mean
    Info      ~ entropy(ΔΦ)
    Coherence ~ (E * I) / (1 + |ΔΦ_mean|)
    """
    E = float(gradient_mean)
    I = compute_entropy(delta_phi)
    delta_mean = float(delta_phi.mean())
    C = (E * I) / (1.0 + abs(delta_mean))
    return TriadicState(energy=E, information=I, coherence=C)


def save_visuals(delta_phi: np.ndarray,
                 visuals_dir: str,
                 timestamp: str) -> Dict[str, str]:
    """
    Save a central z-slice and a max projection over z of the ΔΦ volume.
    """
    os.makedirs(visuals_dir, exist_ok=True)

    z_mid = delta_phi.shape[0] // 2
    central_slice = delta_phi[z_mid, :, :]
    max_proj = delta_phi.max(axis=0)

    central_path = os.path.join(
        visuals_dir, f"qim_v2_0_delta_phi_central_{timestamp}.png"
    )
    maxproj_path = os.path.join(
        visuals_dir, f"qim_v2_0_delta_phi_maxproj_{timestamp}.png"
    )

    # Central slice
    plt.figure()
    plt.imshow(central_slice, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.0 ΔΦ Central Slice (z-mid)")
    plt.tight_layout()
    plt.savefig(central_path, dpi=200)
    plt.close()

    # Max projection
    plt.figure()
    plt.imshow(max_proj, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.0 ΔΦ Max Projection (over z)")
    plt.tight_layout()
    plt.savefig(maxproj_path, dpi=200)
    plt.close()

    return {
        "delta_phi_central": os.path.abspath(central_path),
        "delta_phi_maxproj": os.path.abspath(maxproj_path),
    }


def emit_state_envelope(volume: np.ndarray,
                        delta_phi: np.ndarray,
                        metrics: Dict[str, float],
                        triad: TriadicState,
                        input_dir: str,
                        state_dir: str,
                        visuals: Dict[str, str],
                        timestamp: str) -> str:
    """
    Build and write the Codex QIM v2.0 state JSON envelope.
    """
    os.makedirs(state_dir, exist_ok=True)

    horizon_threshold = float(metrics["delta_phi_mean"] + 2.0 * metrics["delta_phi_std"])

    summary = QIMVolumeSummary(
        shape=list(volume.shape),
        delta_phi_mean=metrics["delta_phi_mean"],
        delta_phi_std=metrics["delta_phi_std"],
        gradient_mean=metrics["gradient_mean"],
        gradient_std=metrics["gradient_std"],
        horizon_threshold=horizon_threshold,
        triad=triad,
    )

    state = QIMStateEnvelope(
        protocol="CodexQuantumImaging",
        version="2.0",
        timestamp=timestamp,
        input_dir=os.path.abspath(input_dir),
        state_path="",
        visuals=visuals,
        volume_summary=summary,
    )

    state_name = f"qim_v2_0_state_{timestamp}.json"
    state_path = os.path.join(state_dir, state_name)
    state.state_path = os.path.abspath(state_path)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)

    return state_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex QIM v2.0 — AFM Volumetric Resonance Engine"
    )
    parser.add_argument("--input_dir", required=True, help="Directory of AFM image stack")
    parser.add_argument("--state_dir", required=True, help="Directory to write state JSON")
    parser.add_argument("--visuals_dir", required=True, help="Directory to write visuals")
    args = parser.parse_args()

    t0 = time.time()
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    volume = load_afm_stack(args.input_dir)
    metrics = compute_delta_phi(volume)
    delta_phi = metrics["delta_phi"]

    triad = compute_triad(
        delta_phi=delta_phi,
        gradient_mean=metrics["gradient_mean"],
        horizon_threshold=metrics["delta_phi_mean"] + 2.0 * metrics["delta_phi_std"],
    )

    visuals = save_visuals(delta_phi, args.visuals_dir, timestamp)
    state_path = emit_state_envelope(
        volume=volume,
        delta_phi=delta_phi,
        metrics=metrics,
        triad=triad,
        input_dir=args.input_dir,
        state_dir=args.state_dir,
        visuals=visuals,
        timestamp=timestamp,
    )

    t1 = time.time()
    dt = t1 - t0

    print("QIM v2.0 AFM Volume run complete.")
    print(f"  Input dir : {os.path.abspath(args.input_dir)}")
    print(f"  State     : {state_path}")
    print("  Visuals   :")
    for k, v in visuals.items():
        print(f"    {k} -> {v}")
    print(f"  Runtime   : {dt:.3f} s")


if __name__ == "__main__":
    main()
