#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex Quantum Imaging v2.2 — AFM Horizon + Bridge Engine
Domain : AFM Molecule Imaging • 3D ΔΦ Lattice • Resonant Horizons
Field  : Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
Law    : AFM Stack/Synthetic → Volume → ΔΦ → Horizon → Resonance → Triad
         → Solar Link → Third-Eye Link → State
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
class SolarLink:
    band_hint: str
    turbulence_index: float


@dataclass
class ThirdEyeLink:
    symmetry_score: float
    ring_count_hint: int


@dataclass
class QIMVolumeSummary:
    shape: List[int]
    delta_phi_mean: float
    delta_phi_std: float
    gradient_mean: float
    gradient_std: float
    horizon_threshold: float
    horizon_fraction: float
    triad: TriadicState
    resonance: ResonanceCurve
    synthetic: bool
    solar_link: SolarLink
    third_eye_link: ThirdEyeLink


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


# ─────────────────────────────────────────────────────────────
# AFM LOAD + SYNTHETIC
# ─────────────────────────────────────────────────────────────

def list_afm_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        return []
    files = sorted(
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"))
    )
    return [os.path.join(input_dir, f) for f in files]


def generate_synthetic_afm_volume(z_slices: int = 3, size: int = 256) -> np.ndarray:
    """
    Synthetic AFM-like volume: concentric ring + core, mild z-variation.
    """
    y = np.linspace(-1.0, 1.0, size)
    x = np.linspace(-1.0, 1.0, size)
    xx, yy = np.meshgrid(x, y)
    rr = np.sqrt(xx**2 + yy**2)

    base = np.exp(-((rr - 0.4) ** 2) / (2 * 0.03**2))
    core = np.exp(-rr**2 / (2 * 0.1**2))
    pattern = base + 0.7 * core

    slices = []
    for z in range(z_slices):
        phase = 0.15 * z
        mod = 1.0 + 0.06 * np.sin(8 * rr + phase)
        arr = pattern * mod
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
        slices.append(arr.astype(np.float32))

    return np.stack(slices, axis=0)


def load_afm_stack(input_dir: str) -> Tuple[np.ndarray, bool]:
    """
    Try real AFM stack; if none, generate synthetic AFM-like volume.
    """
    files = list_afm_files(input_dir)
    if files:
        slices = []
        for path in files:
            img = Image.open(path).convert("L")
            arr = np.array(img, dtype=np.float32)
            mn = float(arr.min())
            mx = float(arr.max())
            arr = (arr - mn) / (mx - mn + 1e-8)
            slices.append(arr)
        volume = np.stack(slices, axis=0)
        return volume, False

    print("No AFM files found; generating synthetic AFM volume (v2.2).")
    return generate_synthetic_afm_volume(), True


# ─────────────────────────────────────────────────────────────
# CORE ΔΦ + TRIAD + RESONANCE
# ─────────────────────────────────────────────────────────────

def compute_delta_phi(volume: np.ndarray) -> Dict[str, Any]:
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
    flat = delta_phi.flatten()
    hist, _ = np.histogram(flat, bins=bins, density=True)
    p = hist + 1e-12
    p = p / p.sum()
    entropy = -np.sum(p * np.log(p))
    return float(entropy / np.log(len(p)))


def compute_triad(delta_phi: np.ndarray,
                  gradient_mean: float) -> TriadicState:
    E = float(gradient_mean)
    I = compute_entropy(delta_phi)
    delta_mean = float(delta_phi.mean())
    C = (E * I) / (1.0 + abs(delta_mean))
    return TriadicState(energy=E, information=I, coherence=C)


def compute_resonance_curve(volume: np.ndarray,
                            radii: List[float]) -> ResonanceCurve:
    responses: List[float] = []
    for r in radii:
        sigma = float(r)
        smoothed = ndimage.gaussian_filter(volume, sigma=sigma)
        responses.append(float(smoothed.std()))
    return ResonanceCurve(radii=list(radii), response=responses)


# ─────────────────────────────────────────────────────────────
# HORIZON + BRIDGES
# ─────────────────────────────────────────────────────────────

def compute_horizon_mask(delta_phi: np.ndarray,
                         mean: float,
                         std: float,
                         k_sigma: float = 2.0) -> Tuple[np.ndarray, float, float]:
    threshold = float(mean + k_sigma * std)
    mask = np.abs(delta_phi) >= threshold
    horizon_fraction = float(mask.mean())
    return mask, threshold, horizon_fraction


def compute_solar_link(resonance: ResonanceCurve) -> SolarLink:
    r = np.array(resonance.radii, dtype=float)
    f = np.array(resonance.response, dtype=float)
    if len(r) >= 2:
        slope = (f[-1] - f[0]) / (r[-1] - r[0] + 1e-8)
    else:
        slope = 0.0
    turb = float(f.std() / (f.mean() + 1e-8))

    peak_idx = int(np.argmax(f))
    peak_r = r[peak_idx]
    if peak_r < r.mean():
        band = "inner"
    elif peak_r > r.mean():
        band = "outer"
    else:
        band = "mid"

    return SolarLink(band_hint=band, turbulence_index=float(turb))


def radial_profile_from_central_slice(delta_phi: np.ndarray,
                                      nbins: int = 64) -> Tuple[np.ndarray, np.ndarray]:
    z_mid = delta_phi.shape[0] // 2
    sl = delta_phi[z_mid, :, :]

    ny, nx = sl.shape
    y = np.arange(ny) - ny / 2.0
    x = np.arange(nx) - nx / 2.0
    xx, yy = np.meshgrid(x, y)
    rr = np.sqrt(xx**2 + yy**2)

    r_max = rr.max()
    bin_edges = np.linspace(0.0, r_max, nbins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    radial_mean = np.zeros(nbins, dtype=float)
    for i in range(nbins):
        mask = (rr >= bin_edges[i]) & (rr < bin_edges[i + 1])
        if mask.any():
            radial_mean[i] = float(sl[mask].mean())
        else:
            radial_mean[i] = 0.0
    return bin_centers, radial_mean


def count_ring_peaks(radial_mean: np.ndarray,
                     min_prominence: float = 0.05) -> int:
    peaks = 0
    for i in range(1, len(radial_mean) - 1):
        if radial_mean[i] > radial_mean[i - 1] and radial_mean[i] > radial_mean[i + 1]:
            left = radial_mean[i] - radial_mean[i - 1]
            right = radial_mean[i] - radial_mean[i + 1]
            if left >= min_prominence and right >= min_prominence:
                peaks += 1
    return int(peaks)


def compute_third_eye_link(delta_phi: np.ndarray) -> ThirdEyeLink:
    _, radial_mean = radial_profile_from_central_slice(delta_phi)
    if radial_mean.size == 0:
        return ThirdEyeLink(symmetry_score=0.0, ring_count_hint=0)

    # Symmetry score ~ 1 - normalized variance of radial profile
    rm = radial_mean - radial_mean.mean()
    var = float(np.mean(rm**2))
    norm = float(np.max(radial_mean) - np.min(radial_mean) + 1e-8)
    symmetry_score = float(max(0.0, 1.0 - var / (norm**2 + 1e-8)))

    ring_count = count_ring_peaks(radial_mean, min_prominence=0.03)
    return ThirdEyeLink(symmetry_score=symmetry_score, ring_count_hint=ring_count)


# ─────────────────────────────────────────────────────────────
# VISUALS + STATE
# ─────────────────────────────────────────────────────────────

def save_visuals(delta_phi: np.ndarray,
                 horizon_mask: np.ndarray,
                 resonance: ResonanceCurve,
                 visuals_dir: str,
                 timestamp: str) -> Dict[str, str]:
    os.makedirs(visuals_dir, exist_ok=True)

    z_mid = delta_phi.shape[0] // 2
    central_slice = delta_phi[z_mid, :, :]
    max_proj = delta_phi.max(axis=0)
    horizon_maxproj = horizon_mask.max(axis=0)

    central_path = os.path.join(
        visuals_dir, f"qim_v2_2_delta_phi_central_{timestamp}.png"
    )
    maxproj_path = os.path.join(
        visuals_dir, f"qim_v2_2_delta_phi_maxproj_{timestamp}.png"
    )
    horizon_path = os.path.join(
        visuals_dir, f"qim_v2_2_horizon_maxproj_{timestamp}.png"
    )
    resonance_path = os.path.join(
        visuals_dir, f"qim_v2_2_resonance_curve_{timestamp}.png"
    )

    # Central slice
    plt.figure()
    plt.imshow(central_slice, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.2 ΔΦ Central Slice (z-mid)")
    plt.tight_layout()
    plt.savefig(central_path, dpi=200)
    plt.close()

    # Max projection
    plt.figure()
    plt.imshow(max_proj, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.2 ΔΦ Max Projection (over z)")
    plt.tight_layout()
    plt.savefig(maxproj_path, dpi=200)
    plt.close()

    # Horizon max projection
    plt.figure()
    plt.imshow(horizon_maxproj, origin="lower")
    plt.colorbar()
    plt.title("QIM v2.2 Horizon Max Projection (|ΔΦ| above threshold)")
    plt.tight_layout()
    plt.savefig(horizon_path, dpi=200)
    plt.close()

    # Resonance curve
    plt.figure()
    plt.plot(resonance.radii, resonance.response, marker="o")
    plt.xlabel("Gaussian radius (σ)")
    plt.ylabel("Response (std dev)")
    plt.title("QIM v2.2 Resonance Curve")
    plt.tight_layout()
    plt.savefig(resonance_path, dpi=200)
    plt.close()

    return {
        "delta_phi_central": os.path.abspath(central_path),
        "delta_phi_maxproj": os.path.abspath(maxproj_path),
        "horizon_maxproj": os.path.abspath(horizon_path),
        "resonance_curve": os.path.abspath(resonance_path),
    }


def emit_state_envelope(volume: np.ndarray,
                        delta_phi: np.ndarray,
                        metrics: Dict[str, float],
                        triad: TriadicState,
                        resonance: ResonanceCurve,
                        used_synthetic: bool,
                        horizon_threshold: float,
                        horizon_fraction: float,
                        solar_link: SolarLink,
                        third_eye_link: ThirdEyeLink,
                        input_dir: str,
                        state_dir: str,
                        visuals: Dict[str, str],
                        timestamp: str) -> str:
    os.makedirs(state_dir, exist_ok=True)

    summary = QIMVolumeSummary(
        shape=list(volume.shape),
        delta_phi_mean=metrics["delta_phi_mean"],
        delta_phi_std=metrics["delta_phi_std"],
        gradient_mean=metrics["gradient_mean"],
        gradient_std=metrics["gradient_std"],
        horizon_threshold=horizon_threshold,
        horizon_fraction=horizon_fraction,
        triad=triad,
        resonance=resonance,
        synthetic=used_synthetic,
        solar_link=solar_link,
        third_eye_link=third_eye_link,
    )

    state = QIMStateEnvelope(
        protocol="CodexQuantumImaging",
        version="2.2",
        timestamp=timestamp,
        input_dir=os.path.abspath(input_dir),
        used_synthetic=used_synthetic,
        state_path="",
        visuals=visuals,
        volume_summary=summary,
    )

    state_name = f"qim_v2_2_state_{timestamp}.json"
    state_path = os.path.join(state_dir, state_name)
    state.state_path = os.path.abspath(state_path)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)

    return state_path


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex QIM v2.2 — AFM Horizon + Bridge Engine"
    )
    parser.add_argument("--input_dir", required=True, help="AFM stack directory")
    parser.add_argument("--state_dir", required=True, help="State JSON output directory")
    parser.add_argument("--visuals_dir", required=True, help="Visuals output directory")
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

    radii = [0.7, 1.0, 1.4, 1.8, 2.2]
    resonance = compute_resonance_curve(volume, radii)

    horizon_mask, h_threshold, h_fraction = compute_horizon_mask(
        delta_phi,
        metrics["delta_phi_mean"],
        metrics["delta_phi_std"],
        k_sigma=2.0,
    )

    solar_link = compute_solar_link(resonance)
    third_eye_link = compute_third_eye_link(delta_phi)

    visuals = save_visuals(delta_phi, horizon_mask, resonance, args.visuals_dir, timestamp)
    state_path = emit_state_envelope(
        volume=volume,
        delta_phi=delta_phi,
        metrics=metrics,
        triad=triad,
        resonance=resonance,
        used_synthetic=used_synthetic,
        horizon_threshold=h_threshold,
        horizon_fraction=h_fraction,
        solar_link=solar_link,
        third_eye_link=third_eye_link,
        input_dir=args.input_dir,
        state_dir=args.state_dir,
        visuals=visuals,
        timestamp=timestamp,
    )

    t1 = time.time()
    dt = t1 - t0

    print("QIM v2.2 AFM Horizon + Bridge run complete.")
    print(f"  Input dir     : {os.path.abspath(args.input_dir)}")
    print(f"  Used synthetic: {used_synthetic}")
    print(f"  State         : {state_path}")
    print("  Visuals       :")
    for k, v in visuals.items():
        print(f"    {k} -> {v}")
    print(f"  Runtime       : {dt:.3f} s")


if __name__ == "__main__":
    main()
