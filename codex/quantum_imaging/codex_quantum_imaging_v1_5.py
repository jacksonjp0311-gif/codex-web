"""
Codex Quantum Imaging Module v1.5 — Triadic Vision Engine
Author : James Paul Jackson
Context: Codex Memory Core v1.4 • Universal Truth Protocol (E–I–C, H7=0.70, Placidity)

Role:
    - Generate AFM-like synthetic ΔΦ field across three radii
    - Compute Codex coherence C = (E * I) / (1 + |ΔΦ|)
    - Emit Triadic Vision frames (E, ΔΦ, C overlays)
    - Save ΔΦ heatmap grid + triadic vision map
    - Write Codex-aligned v1.5 state JSON
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
    version: str = "1.5"
    grid_size: int = 256
    extent: float = 3.0
    base_radius: float = 0.55
    atom_sigma: float = 0.22
    cluster_spacing: float = 0.9
    radii: Tuple[float, float, float] = (1.0, 1.15, 1.30)
    phases_per_radius: int = 4      # 3 radii × 4 phases = 12 frames
    h7: float = 0.70
    seed: int = 0                   # set at runtime


# ────────────────────────────────────────────────────────────────
# 2) Helpers: grid, fields, ΔΦ, coherence
# ────────────────────────────────────────────────────────────────

def make_polar_grid(cfg: QIMConfig):
    half = cfg.extent
    xs = np.linspace(-half, half, cfg.grid_size)
    ys = np.linspace(-half, half, cfg.grid_size)
    x, y = np.meshgrid(xs, ys)
    r = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)
    return x, y, r, theta


def gaussian_ring(r: np.ndarray, radius: float, sigma: float):
    return np.exp(-0.5 * ((r - radius) / sigma) ** 2)


def hex_cluster_field(x, y, cfg: QIMConfig, phase: float):
    """
    Aromatic-like hexagonal cluster structure.
    """
    field = np.zeros_like(x)
    angles = np.linspace(0.0, 2.0 * math.pi, 7)[:-1]  # 6-fold
    for ang in angles:
        cx = cfg.cluster_spacing * math.cos(ang + phase)
        cy = cfg.cluster_spacing * math.sin(ang + phase)
        field += np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * cfg.atom_sigma ** 2))
    return field


def make_frame(x, y, r, theta, cfg: QIMConfig, radius_factor: float, phase: float):
    """
    Construct single AFM-like intensity frame.
    """
    ring = gaussian_ring(r, cfg.base_radius * radius_factor, cfg.atom_sigma)
    clusters = hex_cluster_field(x, y, cfg, phase)

    # Six-fold angular modulation
    interference = 1.0 + 0.5 * np.cos(6.0 * theta + phase)
    field = ring * interference + 0.7 * clusters

    noise = 0.02 * np.random.randn(*x.shape)
    field = np.clip(field + noise, 0.0, None)
    return field


def delta_phi_field(field: np.ndarray) -> np.ndarray:
    gx, gy = np.gradient(field)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    return mag


def codex_coherence(field: np.ndarray, dphi: np.ndarray, cfg: QIMConfig) -> float:
    vals = field.astype(float).ravel()
    vals = np.clip(vals, 0.0, None)
    total = vals.sum()
    if total <= 0.0:
        return 0.0

    # Energy proxy
    e_mean = float(vals.mean())
    e_norm = 1.0 / (1.0 + math.exp(-40.0 * (e_mean - 0.05)))

    # Information (entropy) normalized
    p = vals / total
    entropy = -float((p * np.log(p + 1e-12)).sum())
    max_entropy = math.log(len(p))
    i_norm = entropy / max_entropy if max_entropy > 0 else 0.0

    dphi_mean = float(np.mean(dphi))
    c = (e_norm * i_norm) / (1.0 + abs(dphi_mean))

    c_clamped = max(0.0, min(1.0, c))
    return c_clamped


# ────────────────────────────────────────────────────────────────
# 3) Triadic Vision Engine
# ────────────────────────────────────────────────────────────────

def run_qim_v1_5():
    now = datetime.now(timezone.utc)
    seed = int(now.timestamp()) % 65535
    np.random.seed(seed)

    cfg = QIMConfig(seed=seed)

    root = Path(__file__).resolve().parent
    state_dir = root / "state_v1_5"
    visuals_dir = root / "visuals_v1_5"
    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    x, y, r, theta = make_polar_grid(cfg)

    radii = [float(rr) for rr in cfg.radii]
    phases = [2.0 * math.pi * k / cfg.phases_per_radius for k in range(cfg.phases_per_radius)]

    c_values: List[float] = []
    c_per_radius = {f"{rr:.2f}": [] for rr in radii}
    frames: List[str] = []

    dphi_accum = np.zeros_like(r, dtype=float)
    e_accum = []
    i_accum = []

    frame_index = 0
    for rr in radii:
        key = f"{rr:.2f}"
        for p_idx, phase in enumerate(phases):
            field = make_frame(x, y, r, theta, cfg, rr, phase)
            dphi = delta_phi_field(field)
            c = codex_coherence(field, dphi, cfg)

            c_values.append(c)
            c_per_radius[key].append(c)
            dphi_accum += dphi
            frame_index += 1

            # E/I tracking for triadic summary (coarse)
            vals = field.ravel()
            vals = np.clip(vals, 0.0, None)
            total = vals.sum()
            if total > 0.0:
                e_accum.append(float(vals.mean()))
                p = vals / total
                entropy = -float((p * np.log(p + 1e-12)).sum())
                max_entropy = math.log(len(p))
                i_norm = entropy / max_entropy if max_entropy > 0 else 0.0
                i_accum.append(i_norm)

            frame_name = f"qim_v1_5_frame_{frame_index:02d}.png"
            frame_path = visuals_dir / frame_name

            plt.figure(figsize=(4, 4), dpi=150)
            plt.imshow(field, origin="lower", cmap="magma")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(frame_path, bbox_inches="tight", pad_inches=0.0)
            plt.close()

            frames.append(str(frame_path))

    if frame_index > 0:
        dphi_mean_map = dphi_accum / float(frame_index)
    else:
        dphi_mean_map = dphi_accum

    # ΔΦ grid heatmap
    dphi_grid_path = visuals_dir / "qim_v1_5_delta_phi_grid.png"
    plt.figure(figsize=(4, 4), dpi=150)
    plt.imshow(dphi_mean_map, origin="lower", cmap="viridis")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(dphi_grid_path, bbox_inches="tight", pad_inches=0.0)
    plt.close()

    # Resonance curve (mean C vs radius)
    c_means_per_r = []
    for rr in radii:
        key = f"{rr:.2f}"
        vals_r = c_per_radius[key]
        c_means_per_r.append(float(np.mean(vals_r)) if vals_r else 0.0)

    triadic_vision_path = visuals_dir / "qim_v1_5_triadic_vision.png"
    plt.figure(figsize=(9, 3), dpi=150)

    # Panel 1: ΔΦ map
    plt.subplot(1, 3, 1)
    plt.imshow(dphi_mean_map, origin="lower", cmap="plasma")
    plt.title("ΔΦ field")
    plt.axis("off")

    # Panel 2: C vs radius
    plt.subplot(1, 3, 2)
    plt.plot(radii, c_means_per_r, marker="o")
    plt.axhline(cfg.h7, linestyle="--")
    plt.xlabel("radius factor")
    plt.ylabel("C")
    plt.title("Resonance vs radius")
    plt.grid(True, alpha=0.3)

    # Panel 3: Triadic summary (E,I,C)
    c_array = np.array(c_values, dtype=float)
    c_mean = float(c_array.mean()) if c_array.size else 0.0
    e_mean = float(np.mean(e_accum)) if e_accum else 0.0
    i_mean = float(np.mean(i_accum)) if i_accum else 0.0

    alignment_score = c_mean - cfg.h7

    plt.subplot(1, 3, 3)
    bars = ["E_mean", "I_mean", "C_mean", "H7"]
    vals = [e_mean, i_mean, c_mean, cfg.h7]
    plt.bar(bars, vals)
    plt.ylim(0.0, 1.2)
    plt.title("Triadic metrics")
    plt.tight_layout()

    plt.savefig(triadic_vision_path, bbox_inches="tight")
    plt.close()

    timestamp = now.isoformat()
    summary = {
        "ok": True,
        "module": "codex_quantum_imaging_v1_5",
        "version": cfg.version,
        "timestamp": timestamp,
        "config": {
            "grid_size": cfg.grid_size,
            "extent": cfg.extent,
            "base_radius": cfg.base_radius,
            "atom_sigma": cfg.atom_sigma,
            "cluster_spacing": cfg.cluster_spacing,
            "radii": radii,
            "phases_per_radius": cfg.phases_per_radius,
            "seed": cfg.seed,
        },
        "metrics": {
            "E_mean": e_mean,
            "I_mean": i_mean,
            "C_values_mean": c_mean,
            "target_H7": cfg.h7,
            "alignment_score": alignment_score,
        },
        "paths": {
            "delta_phi_grid": str(dphi_grid_path),
            "triadic_vision_map": str(triadic_vision_path),
            "frames": frames,
            "state_dir": str(state_dir),
        },
    }

    state_main_path = state_dir / "codex_quantum_imaging_v1_5_state.json"
    state_short_path = state_dir / "codex_qim_v1_5_state.json"

    with state_main_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    short_state = {
        "ok": summary["ok"],
        "version": summary["version"],
        "timestamp": summary["timestamp"],
        "C_values_mean": summary["metrics"]["C_values_mean"],
        "alignment_score": summary["metrics"]["alignment_score"],
        "delta_phi_grid": summary["paths"]["delta_phi_grid"],
        "triadic_vision_map": summary["paths"]["triadic_vision_map"],
        "state_main": str(state_main_path),
    }
    with state_short_path.open("w", encoding="utf-8") as f:
        json.dump(short_state, f, indent=2)

    return summary


if __name__ == "__main__":
    result = run_qim_v1_5()
    print(json.dumps(result, indent=2))
