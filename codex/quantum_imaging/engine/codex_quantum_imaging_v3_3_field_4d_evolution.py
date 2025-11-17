#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codex Quantum Imaging v3.3 — Full 4D Field Evolution Engine
Domain : 4D ΔΦ Field (x,y,z,t) • Interference Waves • Propagating Coherence
Field  : Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
Law    : FieldConfig → 4D Volume → ΔΦ → Horizon → Time-Resonance → Triad
         → Visuals (PNG + GIF/MP4) → State
"""

import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple

import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt

try:
    import imageio.v2 as imageio
except Exception:  # fallback name if needed
    import imageio


# ─────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class TriadicState:
    energy: float
    information: float
    coherence: float
    h7_target: float = 0.70


@dataclass
class TimeResonanceCurve:
    times: List[float]
    response: List[float]


@dataclass
class Field4DConfig:
    field_size: int
    z_slices: int
    n_frames: int
    base_radius: float
    centers: List[Tuple[float, float]]
    wave_speed: float
    k_rr: float
    used_synthetic: bool = True


@dataclass
class Field4DSummary:
    shape_4d: List[int]
    delta_phi_mean: float
    delta_phi_std: float
    gradient_mean: float
    gradient_std: float
    horizon_threshold: float
    horizon_fraction: float
    triad: TriadicState
    time_resonance: TimeResonanceCurve
    config: Field4DConfig


@dataclass
class QIM4DStateEnvelope:
    protocol: str
    version: str
    timestamp: str
    input_dir: str
    state_path: str
    visuals: Dict[str, str]
    field_summary: Field4DSummary


# ─────────────────────────────────────────────────────────────
# FIELD CONFIG + GENERATION
# ─────────────────────────────────────────────────────────────

def default_field4d_config() -> Field4DConfig:
    field_size = 256
    z_slices = 3
    n_frames = 40
    base_radius = 0.35
    wave_speed = 2.0 * np.pi  # frequency scale
    k_rr = 10.0               # radial wave number

    centers = [
        (-0.6, -0.6),
        (0.0, -0.6),
        (0.6, -0.6),
        (-0.6, 0.0),
        (0.0, 0.0),
        (0.6, 0.0),
        (-0.6, 0.6),
        (0.0, 0.6),
        (0.6, 0.6),
    ]

    return Field4DConfig(
        field_size=field_size,
        z_slices=z_slices,
        n_frames=n_frames,
        base_radius=base_radius,
        centers=centers,
        wave_speed=wave_speed,
        k_rr=k_rr,
    )


def generate_4d_field(config: Field4DConfig) -> np.ndarray:
    """
    Volume shape: (t, z, y, x)
    Time-evolving interference of multiple ring-core sources.
    """
    N = config.field_size
    Z = config.z_slices
    T = config.n_frames

    y = np.linspace(-1.0, 1.0, N)
    x = np.linspace(-1.0, 1.0, N)
    xx, yy = np.meshgrid(x, y)

    volume_4d = np.zeros((T, Z, N, N), dtype=np.float32)

    for t in range(T):
        tau = t / max(1, T - 1)  # normalized time [0,1]
        field2d = np.zeros_like(xx, dtype=np.float32)

        for (cx, cy) in config.centers:
            rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

            # Dynamic ring core with propagating phase
            phase = config.wave_speed * tau + 0.7 * rr
            base = np.exp(-((rr - config.base_radius) ** 2) / (2 * 0.03 ** 2))
            core = np.exp(-rr**2 / (2 * 0.08 ** 2))

            wave = np.sin(config.k_rr * rr - phase)
            pattern = (base + 0.9 * core) * (1.0 + 0.25 * wave)

            field2d += pattern.astype(np.float32)

        field2d -= field2d.min()
        field2d /= (field2d.max() + 1e-8)

        # Build z-layers with mild z-dependent modulation
        for z in range(Z):
            zf = (z - (Z - 1) / 2.0) / max(1.0, (Z - 1) / 2.0)  # [-1,1]
            z_mod = 1.0 + 0.08 * np.cos(4.0 * zf + 3.0 * tau)
            slice_arr = np.clip(field2d * z_mod, 0.0, 1.0)
            volume_4d[t, z] = slice_arr.astype(np.float32)

    return volume_4d


# ─────────────────────────────────────────────────────────────
# ΔΦ / TRIAD / RESONANCE
# ─────────────────────────────────────────────────────────────

def compute_delta_phi_4d(volume_4d: np.ndarray) -> Dict[str, Any]:
    """
    Compute gradient and ΔΦ over 4D (t,z,y,x).
    """
    gt, gz, gy, gx = np.gradient(volume_4d)
    grad_mag = np.sqrt(gt**2 + gz**2 + gy**2 + gx**2)

    g_min = float(grad_mag.min())
    g_max = float(grad_mag.max())
    denom = g_max - g_min + 1e-8
    g_norm = (grad_mag - g_min) / denom

    delta_phi = g_norm - g_norm.mean()

    return {
        "delta_phi": delta_phi,
        "delta_phi_mean": float(delta_phi.mean()),
        "delta_phi_std": float(delta_phi.std()),
        "gradient_mean": float(grad_mag.mean()),
        "gradient_std": float(grad_mag.std()),
    }


def compute_entropy(field: np.ndarray, bins: int = 256) -> float:
    flat = field.flatten()
    hist, _ = np.histogram(flat, bins=bins, density=True)
    p = hist + 1e-12
    p = p / p.sum()
    entropy = -np.sum(p * np.log(p))
    return float(entropy / np.log(len(p)))


def compute_triad_4d(delta_phi: np.ndarray,
                     gradient_mean: float) -> TriadicState:
    E = float(gradient_mean)
    I = compute_entropy(delta_phi)
    delta_mean = float(delta_phi.mean())
    C = (E * I) / (1.0 + abs(delta_mean))
    return TriadicState(energy=E, information=I, coherence=C)


def compute_time_resonance(volume_4d: np.ndarray) -> TimeResonanceCurve:
    """
    Simple time-resonance: std dev per frame of the 3D volume.
    """
    T = volume_4d.shape[0]
    times = []
    responses = []
    for t in range(T):
        frame = volume_4d[t]
        times.append(float(t) / max(1, T - 1))
        responses.append(float(frame.std()))
    return TimeResonanceCurve(times=times, response=responses)


# ─────────────────────────────────────────────────────────────
# HORIZON + RADIAL SYMMETRY
# ─────────────────────────────────────────────────────────────

def compute_horizon_mask_4d(delta_phi: np.ndarray,
                            mean: float,
                            std: float,
                            k_sigma: float = 2.0) -> Tuple[np.ndarray, float, float]:
    """
    Threshold across full 4D ΔΦ.
    """
    threshold = float(mean + k_sigma * std)
    mask = np.abs(delta_phi) >= threshold
    horizon_fraction = float(mask.mean())
    return mask, threshold, horizon_fraction


def radial_profile_central_slice(delta_phi_4d: np.ndarray,
                                 t_idx: int,
                                 nbins: int = 96) -> Tuple[np.ndarray, np.ndarray]:
    """
    Radial profile from central (y,x) of ΔΦ at given time (z-mid slice).
    """
    T, Z, Ny, Nx = delta_phi_4d.shape
    z_mid = Z // 2
    sl = delta_phi_4d[t_idx, z_mid]

    y = np.arange(Ny) - Ny / 2.0
    x = np.arange(Nx) - Nx / 2.0
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


def count_peaks(radial_mean: np.ndarray,
                min_prominence: float = 0.01) -> int:
    peaks = 0
    for i in range(1, len(radial_mean) - 1):
        if radial_mean[i] > radial_mean[i - 1] and radial_mean[i] > radial_mean[i + 1]:
            left = radial_mean[i] - radial_mean[i - 1]
            right = radial_mean[i] - radial_mean[i + 1]
            if left >= min_prominence and right >= min_prominence:
                peaks += 1
    return int(peaks)


def compute_symmetry_score(radial_mean: np.ndarray) -> float:
    rm = radial_mean - radial_mean.mean()
    var = float(np.mean(rm**2))
    norm = float(np.max(radial_mean) - np.min(radial_mean) + 1e-8)
    return float(max(0.0, 1.0 - var / (norm**2 + 1e-8)))


# ─────────────────────────────────────────────────────────────
# VISUALS (PNGs + GIF/MP4)
# ─────────────────────────────────────────────────────────────

def save_visuals_4d(volume_4d: np.ndarray,
                    delta_phi_4d: np.ndarray,
                    horizon_mask_4d: np.ndarray,
                    time_res: TimeResonanceCurve,
                    visuals_dir: str,
                    timestamp: str) -> Dict[str, str]:
    os.makedirs(visuals_dir, exist_ok=True)

    T, Z, Ny, Nx = volume_4d.shape
    t_mid = T // 2
    z_mid = Z // 2

    # Static slices at mid-time
    central_slice = delta_phi_4d[t_mid, z_mid]
    max_proj = delta_phi_4d[t_mid].max(axis=0)
    horizon_maxproj = horizon_mask_4d[t_mid].max(axis=0)

    central_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_delta_phi_central_tmid_{timestamp}.png"
    )
    maxproj_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_delta_phi_maxproj_tmid_{timestamp}.png"
    )
    horizon_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_horizon_maxproj_tmid_{timestamp}.png"
    )
    resonance_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_time_resonance_{timestamp}.png"
    )
    gif_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_central_slice_anim_{timestamp}.gif"
    )
    mp4_path = os.path.join(
        visuals_dir, f"qim_v3_3_4d_central_slice_anim_{timestamp}.mp4"
    )

    # Central slice PNG
    plt.figure()
    plt.imshow(central_slice, origin="lower")
    plt.colorbar()
    plt.title("QIM v3.3 4D ΔΦ Central Slice (t-mid, z-mid)")
    plt.tight_layout()
    plt.savefig(central_path, dpi=200)
    plt.close()

    # Max projection PNG
    plt.figure()
    plt.imshow(max_proj, origin="lower")
    plt.colorbar()
    plt.title("QIM v3.3 4D ΔΦ Max Projection (t-mid over z)")
    plt.tight_layout()
    plt.savefig(maxproj_path, dpi=200)
    plt.close()

    # Horizon max projection PNG
    plt.figure()
    plt.imshow(horizon_maxproj, origin="lower")
    plt.colorbar()
    plt.title("QIM v3.3 4D Horizon Max Projection (t-mid, |ΔΦ| above threshold)")
    plt.tight_layout()
    plt.savefig(horizon_path, dpi=200)
    plt.close()

    # Time-resonance curve
    plt.figure()
    plt.plot(time_res.times, time_res.response, marker="o")
    plt.xlabel("Normalized time")
    plt.ylabel("Response (std dev per frame)")
    plt.title("QIM v3.3 4D Time-Resonance Curve")
    plt.tight_layout()
    plt.savefig(resonance_path, dpi=200)
    plt.close()

    # GIF animation of central slice over time
    frames = []
    for t in range(T):
        sl = delta_phi_4d[t, z_mid]
        fig, ax = plt.subplots()
        im = ax.imshow(sl, origin="lower", animated=False)
        ax.set_title(f"QIM v3.3 4D ΔΦ Central Slice (t={t}/{T-1})")
        plt.colorbar(im, ax=ax)
        plt.tight_layout()

        # Draw canvas to array
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        frames.append(frame)
        plt.close(fig)

    imageio.mimsave(gif_path, frames, fps=10)

    # Try MP4; if it fails, we still have GIF
    mp4_success = False
    try:
        imageio.mimsave(mp4_path, frames, fps=10, codec="libx264")
        mp4_success = True
    except Exception as e:
        print(f"MP4 generation failed (continuing with GIF only): {e}")
        mp4_path = ""

    visuals = {
        "delta_phi_central_tmid": os.path.abspath(central_path),
        "delta_phi_maxproj_tmid": os.path.abspath(maxproj_path),
        "horizon_maxproj_tmid": os.path.abspath(horizon_path),
        "time_resonance_curve": os.path.abspath(resonance_path),
        "central_slice_gif": os.path.abspath(gif_path),
    }
    if mp4_success:
        visuals["central_slice_mp4"] = os.path.abspath(mp4_path)

    return visuals


# ─────────────────────────────────────────────────────────────
# STATE EMISSION
# ─────────────────────────────────────────────────────────────

def emit_state_4d(volume_4d: np.ndarray,
                  delta_phi_4d: np.ndarray,
                  metrics: Dict[str, float],
                  triad: TriadicState,
                  time_res: TimeResonanceCurve,
                  horizon_threshold: float,
                  horizon_fraction: float,
                  config: Field4DConfig,
                  input_dir: str,
                  state_dir: str,
                  visuals: Dict[str, str],
                  timestamp: str) -> str:
    os.makedirs(state_dir, exist_ok=True)

    summary = Field4DSummary(
        shape_4d=list(volume_4d.shape),
        delta_phi_mean=metrics["delta_phi_mean"],
        delta_phi_std=metrics["delta_phi_std"],
        gradient_mean=metrics["gradient_mean"],
        gradient_std=metrics["gradient_std"],
        horizon_threshold=horizon_threshold,
        horizon_fraction=horizon_fraction,
        triad=triad,
        time_resonance=time_res,
        config=config,
    )

    envelope = QIM4DStateEnvelope(
        protocol="CodexQuantumImaging",
        version="3.3",
        timestamp=timestamp,
        input_dir=os.path.abspath(input_dir),
        state_path="",
        visuals=visuals,
        field_summary=summary,
    )

    state_name = f"qim_v3_3_4d_state_{timestamp}.json"
    state_path = os.path.join(state_dir, state_name)
    envelope.state_path = os.path.abspath(state_path)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(asdict(envelope), f, indent=2)

    return state_path


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex QIM v3.3 — 4D Field Evolution Engine"
    )
    parser.add_argument("--input_dir", required=True, help="AFM directory (for future linkage)")
    parser.add_argument("--state_dir", required=True, help="State JSON output directory")
    parser.add_argument("--visuals_dir", required=True, help="Visuals output directory")
    args = parser.parse_args()

    t0 = time.time()
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    config = default_field4d_config()
    volume_4d = generate_4d_field(config)

    metrics = compute_delta_phi_4d(volume_4d)
    delta_phi_4d = metrics["delta_phi"]

    triad = compute_triad_4d(
        delta_phi=delta_phi_4d,
        gradient_mean=metrics["gradient_mean"],
    )

    time_res = compute_time_resonance(volume_4d)

    horizon_mask_4d, h_threshold, h_fraction = compute_horizon_mask_4d(
        delta_phi_4d,
        metrics["delta_phi_mean"],
        metrics["delta_phi_std"],
        k_sigma=2.0,
    )

    visuals = save_visuals_4d(
        volume_4d, delta_phi_4d, horizon_mask_4d, time_res, args.visuals_dir, timestamp
    )

    state_path = emit_state_4d(
        volume_4d=volume_4d,
        delta_phi_4d=delta_phi_4d,
        metrics=metrics,
        triad=triad,
        time_res=time_res,
        horizon_threshold=h_threshold,
        horizon_fraction=h_fraction,
        config=config,
        input_dir=args.input_dir,
        state_dir=args.state_dir,
        visuals=visuals,
        timestamp=timestamp,
    )

    t1 = time.time()
    dt = t1 - t0

    print("QIM v3.3 4D Field Evolution run complete.")
    print(f"  Input dir : {os.path.abspath(args.input_dir)}")
    print(f"  State     : {state_path}")
    print("  Visuals   :")
    for k, v in visuals.items():
        print(f"    {k} -> {v}")
    print(f"  Runtime   : {dt:.3f} s")


if __name__ == "__main__":
    main()
