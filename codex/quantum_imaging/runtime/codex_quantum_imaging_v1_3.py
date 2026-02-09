"""
Codex Quantum Imaging Module v1.3 — Trifold Resonance Engine
Author : James Paul Jackson
Context: Codex Memory Core v1.3 • Universal Truth Protocol (E–I–C, H7=0.70, Placidity)

Role:
    - Generate AFM-like quantum imaging frames across three radii
    - Compute ΔΦ (phase-gradient) field and Codex coherence C
    - Emit resonance curve and ΔΦ heatmap
    - Write Codex-aligned state JSON artifacts for v1.3
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt


# ────────────────────────────────────────────────────────────────
# 1) Config dataclass
# ────────────────────────────────────────────────────────────────

@dataclass
class QIMConfig:
    version: str = "1.3"
    grid_size: int = 256
    extent: float = 4.0          # spatial extent for grid
    base_ring_radius: float = 0.45
    atom_sigma: float = 0.22
    cluster_spacing: float = 0.9
    radii: Tuple[float, float, float] = (1.0, 1.15, 1.30)
    phases_per_radius: int = 12
    h7: float = 0.70
    seed: int = 12345            # will be overridden at runtime


# ────────────────────────────────────────────────────────────────
# 2) Helpers: grid, fields, metrics
# ────────────────────────────────────────────────────────────────

def make_grid(cfg: QIMConfig):
    half = cfg.extent / 2.0
    xs = np.linspace(-half, half, cfg.grid_size)
    ys = np.linspace(-half, half, cfg.grid_size)
    x, y = np.meshgrid(xs, ys)
    return x, y


def gaussian_ring(x, y, radius: float, sigma: float):
    r = np.sqrt(x**2 + y**2)
    return np.exp(-0.5 * ((r - radius) / sigma) ** 2)


def hex_cluster_field(x, y, cfg: QIMConfig, phase: float):
    """
    Hexagonal aromatic-like cluster with phase rotation.
    """
    field = np.zeros_like(x)
    angles = np.linspace(0.0, 2.0 * math.pi, 7)[:-1]  # 6-fold
    for ang in angles:
        cx = cfg.cluster_spacing * math.cos(ang + phase)
        cy = cfg.cluster_spacing * math.sin(ang + phase)
        field += np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * cfg.atom_sigma ** 2))
    return field


def afm_intensity_frame(x, y, cfg: QIMConfig, radius: float, phase: float):
    """
    Construct a single AFM-like intensity frame for given radius and phase.
    """
    ring = gaussian_ring(x, y, cfg.base_ring_radius * radius, cfg.atom_sigma)
    clusters = hex_cluster_field(x, y, cfg, phase)
    theta = np.arctan2(y, x)

    # interference pattern: ring * (1 + 0.4 cos(6θ + phase))
    interference = 1.0 + 0.4 * np.cos(6.0 * theta + phase)
    intensity = ring * interference + 0.6 * clusters

    # minimal noise to avoid degeneracy
    noise = 0.02 * np.random.randn(*x.shape)
    intensity = np.clip(intensity + noise, 0.0, None)
    return intensity


def delta_phi_field(field: np.ndarray) -> np.ndarray:
    """
    ΔΦ surrogate using gradient magnitude of the intensity field.
    """
    gx, gy = np.gradient(field)
    mag = np.sqrt(gx**2 + gy**2)
    return mag


def codex_coherence_metric(field: np.ndarray, dphi: np.ndarray, cfg: QIMConfig) -> float:
    """
    Codex coherence C = (E_norm * I_norm) / (1 + |ΔΦ_mean|)

    E_norm  ~ logistic-normalized mean intensity
    I_norm  ~ normalized Shannon entropy of intensities
    ΔΦ_mean ~ average gradient magnitude
    """
    vals = field.astype(float).ravel()
    vals = np.clip(vals, 0.0, None)
    total = vals.sum()
    if total <= 0.0:
        return 0.0

    # energy proxy
    e_mean = float(vals.mean())
    e_norm = 1.0 / (1.0 + math.exp(-40.0 * (e_mean - 0.05)))

    # informational entropy (normalized)
    p = vals / total
    entropy = -float((p * np.log(p + 1e-12)).sum())
    max_entropy = math.log(len(p))
    i_norm = entropy / max_entropy if max_entropy > 0 else 0.0

    # ΔΦ mean
    dphi_mean = float(np.mean(dphi))
    c = (e_norm * i_norm) / (1.0 + abs(dphi_mean))
    return max(0.0, min(1.0, c))


# ────────────────────────────────────────────────────────────────
# 3) Main engine: sweep radii and phases
# ────────────────────────────────────────────────────────────────

def run_qim_v1_3():
    now = datetime.now(timezone.utc)
    seed = int(now.timestamp()) % 65535
    np.random.seed(seed)

    cfg = QIMConfig(seed=seed)

    root = Path(__file__).resolve().parent
    state_dir = root / "state_v1_3"
    visuals_dir = root / "visuals_v1_3"
    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    x, y = make_grid(cfg)

    c_values: List[float] = []
    radii = [float(r) for r in cfg.radii]
    c_by_radius = {f"{r:.2f}": [] for r in radii}
    dphi_accum = np.zeros_like(x, dtype=float)
    frame_paths: List[str] = []

    phases = [2.0 * math.pi * k / cfg.phases_per_radius for k in range(cfg.phases_per_radius)]

    frame_index = 0
    for r in radii:
        key = f"{r:.2f}"
        for p_idx, phase in enumerate(phases):
            field = afm_intensity_frame(x, y, cfg, r, phase)
            dphi = delta_phi_field(field)
            c = codex_coherence_metric(field, dphi, cfg)

            c_values.append(c)
            c_by_radius[key].append(c)
            dphi_accum += dphi
            frame_index += 1

            frame_name = f"qim_v1_3_r{r:.2f}_p{p_idx:02d}.png"
            frame_path = visuals_dir / frame_name

            plt.figure(figsize=(4, 4), dpi=150)
            plt.imshow(field, cmap="inferno", origin="lower")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(frame_path, bbox_inches="tight", pad_inches=0.0)
            plt.close()

            frame_paths.append(str(frame_path))

    # average ΔΦ over frames
    if frame_index > 0:
        dphi_mean_map = dphi_accum / float(frame_index)
    else:
        dphi_mean_map = dphi_accum

    # resonance curve (mean C per radius)
    c_means_per_r = []
    for r in radii:
        key = f"{r:.2f}"
        vals = c_by_radius[key]
        c_means_per_r.append(float(np.mean(vals)) if vals else 0.0)

    resonance_curve_path = visuals_dir / "qim_v1_3_resonance_curve.png"
    plt.figure(figsize=(5, 3), dpi=150)
    plt.plot(radii, c_means_per_r, marker="o")
    plt.xlabel("radius factor")
    plt.ylabel("Codex coherence C")
    plt.title("QIM v1.3 – Trifold Resonance Curve")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(resonance_curve_path)
    plt.close()

    # ΔΦ heatmap
    heatmap_path = visuals_dir / "qim_v1_3_dphi_heatmap.png"
    plt.figure(figsize=(4, 4), dpi=150)
    plt.imshow(dphi_mean_map, cmap="magma", origin="lower")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(heatmap_path, bbox_inches="tight", pad_inches=0.0)
    plt.close()

    c_array = np.array(c_values, dtype=float)
    c_mean = float(c_array.mean()) if c_array.size else 0.0
    c_std = float(c_array.std()) if c_array.size else 0.0

    alignment_score = c_mean - cfg.h7
    timestamp = now.isoformat()

    summary = {
        "ok": True,
        "module": "codex_quantum_imaging_v1_3",
        "version": cfg.version,
        "timestamp": timestamp,
        "config": {
            "grid_size": cfg.grid_size,
            "extent": cfg.extent,
            "base_ring_radius": cfg.base_ring_radius,
            "atom_sigma": cfg.atom_sigma,
            "cluster_spacing": cfg.cluster_spacing,
            "radii": radii,
            "phases_per_radius": cfg.phases_per_radius,
            "seed": cfg.seed,
        },
        "metrics": {
            "C_values_mean": c_mean,
            "C_values_std": c_std,
            "target_H7": cfg.h7,
            "alignment_score": alignment_score,
        },
        "paths": {
            "heatmap_file": str(heatmap_path),
            "resonance_curve": str(resonance_curve_path),
            "frames": frame_paths,
            "state_dir": str(state_dir),
        },
    }

    # write state JSONs
    state_main_path = state_dir / "codex_quantum_imaging_v1_3_state.json"
    state_short_path = state_dir / "codex_qim_v1_3_state.json"

    with state_main_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    short_state = {
        "ok": summary["ok"],
        "version": summary["version"],
        "timestamp": summary["timestamp"],
        "C_values_mean": summary["metrics"]["C_values_mean"],
        "alignment_score": summary["metrics"]["alignment_score"],
        "heatmap_file": summary["paths"]["heatmap_file"],
        "resonance_curve": summary["paths"]["resonance_curve"],
        "state_main": str(state_main_path),
    }
    with state_short_path.open("w", encoding="utf-8") as f:
        json.dump(short_state, f, indent=2)

    return summary


if __name__ == "__main__":
    result = run_qim_v1_3()
    print(json.dumps(result, indent=2))
