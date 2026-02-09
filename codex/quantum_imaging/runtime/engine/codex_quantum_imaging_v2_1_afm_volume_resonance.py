#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex Quantum Imaging v2.1 — AFM Volumetric Resonance + Synthetic Fallback
Domain : AFM Molecule Imaging • 3D ΔΦ Lattice • Resonant Horizons
Field  : Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
Law    : AFM Stack → Volume → ΔΦ → Resonance(r) → Triad(E,I,C) → State
Notes  : If no AFM images found, generate synthetic AFM-like volume and proceed.
"""

import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple

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
class ResonanceCurve:
    radii: List[float]
    response: List[float]


@dataclass
class QIMVolumeSummary:
    shape: List[int]
    delta_phi_mean: float
    delta_phi_std: float
    gradient_mean: float
    gradient_std: float
    horizon_threshold: float
    triad: TriadicState
    resonance: ResonanceCurve
    synthetic: bool


@dataclass
class QIMStateEnvelope:
    protocol: str
    version: str
    timestamp: str
    input_dir: str
    used_synthetic: bool
    state_path: str
    visuals: Dict[str, str]
    volume_summary: QIMVolumeSummary


def list_afm_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        return []
    files = sorted(
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"))
    )
    return [os.path.join(input_dir, f) for f in files]


def load_afm_stack(input_dir: str) -> Tuple[np.ndarray, bool]:
    """
    Try to load an AFM stack. If none found, fall back to a synthetic AFM-like volume.
    Returns (volume, used_synthetic_flag).
    """
    files = list_afm_files(input_dir)
    if files:
        slices = []
        for path in files:
            img = Image.open(path).convert("L")
            arr = np.array(img, dtype=np.float32)
            min_val = float(arr.min())
            max_val = float(arr.max())
            arr = (arr - min_val) / (max_val - min_val + 1e-8)
            slices.append(arr)
        volume = np.stack(slices, axis=0)  # (z, y, x)
        return volume, False

    # Synthetic fallback: AFM-like concentric ring volume
    print("No AFM files found; generating synthetic AFM volume (v2.1).")
    volume = generate_synthetic_afm_volume(z_slices=3, size=256)
    return volume, True


def generate_synthetic_afm_volume(z_slices: int = 3, size: int = 256) -> np.ndarray:
    """
    Generate a synthetic AFM-like volume: concentric rings / 'molecular' pattern
    with slight variation across z.
    """
    y = np.linspace(-1.0, 1.0, size)
    x = np.linspace(-1.0, 1.0, size)
    xx, yy = np.meshgrid(x, y)
    rr = np.sqrt(xx**2 + yy**2)

    base = np.exp(-((rr - 0.4) ** 2) / (2 * 0.03**2))  # ring
    core = np.exp(-rr**2 / (2 * 0.1**2))               # central bump
    pattern = base + 0.7 * core

    volume_slices = []
    for z in range(z_slices):
        phase = 0.1 * z
        mod = 1.0 + 0.05 * np.sin(8 * rr + phase)
        slice_arr = pattern * mod
        slice_arr = (slice_arr - slice_arr.min()) / (slice_arr.max() - slice_arr.min() + 1e-8)
        volume_slices.append(slice_arr.astype(np.float32))

    volume = np.stack(volume_slices, axis=0)
    return volume


def compute_delta_phi(volume: np.ndarray) -> Dict[str, Any]:
    """
    Compute a 3D gradient-based ΔΦ field from the volume.
    """
    gz, gy, gx = np.gradient(volume)
    grad_mag = np.sqrt(gx**2 + gy**2 + gz**2)

    g_min = float(grad_mag.min())
    g_max = float(grad_mag.max())
    denom = g_max - g_min + 1e-8
    g_norm = (grad_mag - g_min) / denom

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
    """
    flat = delta_phi.flatten()
    hist, _ = np.histogram(flat, bins=bins, density=True)
    p = hist + 1e-12
    p = p / p.sum()
    entropy = -np.sum(p * np.log(p))
    entropy_norm = float(entropy / np.log(len(p)))
    return entropy_norm


def compute_triad(delta_phi: np.ndarray,
                  gradient_mean: float) -> TriadicState:
    """
    Compute Codex triadic state from ΔΦ and gradient statistics.
    """
    E = float(gradient_mean)
    I = compute_entropy(delta_phi)
    delta_mean = float(delta_phi.mean())
    C = (E * I) / (1.0 + abs(delta_mean))
    return TriadicState(energy=E, information=I, coherence=C)


def compute_resonance_curve(volume: np.ndarray,
                            radii: List[float]) -> ResonanceCurve:
    """
    Simple 'resonance' over Gaussian scales:
    For each r, smooth the volume and compute std dev as response.
    """
    responses: List[float] = []
    for r in radii:
        sigma = float(r)
        smoothed = ndimage.gaussian_filter(volume, sigma=sigma)
        responses.append(float(smoothed.std()))
    return ResonanceCurve(radii=list(radii), response=responses)


def save_visuals(delta_phi: np.ndarray,
                 resonance: ResonanceCurve,
                 visuals_dir: str,
                 timestamp: str) -> Dict[str, str]:
    """
    Save central slice, max projection, and resonance curve plot.
    """
    os.makedirs(visuals_dir, exist_ok=True)

    z_mid = delta_phi.shape[0] // 2
    central_slice = delta_phi[z_mid, :, :]
    max_proj = delta_phi.max(axis=0)

    central_path = os.path.join(
        visuals_dir, f"qim_v2_1_delta_phi_central_{timestamp}.png"
    )
    maxproj_path = os.path.join(
        visuals_dir, f"qim_v2_1_delta_phi_maxproj_{timestamp}.png"
    )
    resonance_path = os.path.join(
        visuals_dir, f"qim_v2_1_resonance_curve_{timestamp}.png"
    )

    # Central slice
    plt.figure()
    plt.imshow(central_slice, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.1 ΔΦ Central Slice (z-mid)")
    plt.tight_layout()
    plt.savefig(central_path, dpi=200)
    plt.close()

    # Max projection
    plt.figure()
    plt.imshow(max_proj, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.1 ΔΦ Max Projection (over z)")
    plt.tight_layout()
    plt.savefig(maxproj_path, dpi=200)
    plt.close()

    # Resonance curve
    plt.figure()
    plt.plot(resonance.radii, resonance.response, marker="o")
    plt.xlabel("Gaussian radius (σ)")
    plt.ylabel("Response (std dev)")
    plt.title("QIM v2.1 Resonance Curve")
    plt.tight_layout()
    plt.savefig(resonance_path, dpi=200)
    plt.close()

    return {
        "delta_phi_central": os.path.abspath(central_path),
        "delta_phi_maxproj": os.path.abspath(maxproj_path),
        "resonance_curve": os.path.abspath(resonance_path),
    }


def emit_state_envelope(volume: np.ndarray,
                        delta_phi: np.ndarray,
                        metrics: Dict[str, float],
                        triad: TriadicState,
                        resonance: ResonanceCurve,
                        used_synthetic: bool,
                        input_dir: str,
                        state_dir: str,
                        visuals: Dict[str, str],
                        timestamp: str) -> str:
    """
    Build and write the Codex QIM v2.1 state JSON envelope.
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
        resonance=resonance,
        synthetic=used_synthetic,
    )

    state = QIMStateEnvelope(
        protocol="CodexQuantumImaging",
        version="2.1",
        timestamp=timestamp,
        input_dir=os.path.abspath(input_dir),
        used_synthetic=used_synthetic,
        state_path="",
        visuals=visuals,
        volume_summary=summary,
    )

    state_name = f"qim_v2_1_state_{timestamp}.json"
    state_path = os.path.join(state_dir, state_name)
    state.state_path = os.path.abspath(state_path)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)

    return state_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex QIM v2.1 — AFM Volumetric Resonance Engine"
    )
    parser.add_argument("--input_dir", required=True, help="Directory of AFM image stack")
    parser.add_argument("--state_dir", required=True, help="Directory to write state JSON")
    parser.add_argument("--visuals_dir", required=True, help="Directory to write visuals")
    args = parser.parse_args()

    t0 = time.time()
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    volume, used_synthetic = load_afm_stack(args.input_dir)
    metrics = compute_delta_phi(volume)
    delta_phi = metrics["delta_phi"]

    triad = compute_triad(
        delta_phi=delta_phi,
        gradient_mean=metrics["gradient_mean"],
    )

    # Simple resonance over Gaussian σ; this is our first 4D axis (scale).
    radii = [0.7, 1.0, 1.4, 1.8, 2.2]
    resonance = compute_resonance_curve(volume, radii)

    visuals = save_visuals(delta_phi, resonance, args.visuals_dir, timestamp)
    state_path = emit_state_envelope(
        volume=volume,
        delta_phi=delta_phi,
        metrics=metrics,
        triad=triad,
        resonance=resonance,
        used_synthetic=used_synthetic,
        input_dir=args.input_dir,
        state_dir=args.state_dir,
        visuals=visuals,
        timestamp=timestamp,
    )

    t1 = time.time()
    dt = t1 - t0

    print("QIM v2.1 AFM Volume run complete.")
    print(f"  Input dir     : {os.path.abspath(args.input_dir)}")
    print(f"  Used synthetic: {used_synthetic}")
    print(f"  State         : {state_path}")
    print("  Visuals       :")
    for k, v in visuals.items():
        print(f"    {k} -> {v}")
    print(f"  Runtime       : {dt:.3f} s")


if __name__ == "__main__":
    main()
