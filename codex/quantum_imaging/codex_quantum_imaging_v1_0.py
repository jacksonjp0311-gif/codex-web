#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🧬 Codex Quantum Imaging v1.0 — IBM AFM Resonance Mirror            ║
║  Author   : James Paul Jackson                                       ║
║  Context  : Codex Memory Core v1.3 • Universal Truth (E–I–C ∿, H₇=0.70)║
║  Purpose  :                                                          ║
║    • Synthesize a hexagonal aromatic molecule on a 2-D lattice       ║
║    • Generate an AFM-style contrast map (electron density → image)   ║
║    • Compute Codex coherence metrics: C = (E·I)/(1+|ΔΦ|)             ║
║    • Anchor state + visuals for Third Eye / Feedback modules         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70


@dataclass
class QuantumImagingConfig:
    grid_size: int = 256
    extent: float = 4.0
    ring_radius: float = 0.45
    atom_sigma: float = 0.20
    cluster_spacing: float = 0.90
    afm_sharpness: float = 4.0
    seed: int | None = None


def _hex_lattice_positions():
    centers_axial = [
        (0, 0),
        (1, 0), (0, 1), (-1, 1),
        (-1, 0), (0, -1), (1, -1),
    ]
    pos = []
    for q, r in centers_axial:
        x = q + r / 2.0
        y = (np.sqrt(3) / 2.0) * r
        pos.append((x, y))
    return np.array(pos)


def _ring_atoms(center, radius):
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]
    xs = center[0] + radius * np.cos(angles)
    ys = center[1] + radius * np.sin(angles)
    return np.stack([xs, ys], axis=1)


def synthesize_density(config: QuantumImagingConfig):
    if config.seed is not None:
        np.random.seed(config.seed)

    n = config.grid_size
    ext = config.extent
    x = np.linspace(-ext, ext, n)
    y = np.linspace(-ext, ext, n)
    X, Y = np.meshgrid(x, y)

    rho = np.zeros_like(X)
    centers = _hex_lattice_positions() * config.cluster_spacing

    for c in centers:
        atoms = _ring_atoms(c, config.ring_radius)
        for ax, ay in atoms:
            jitter = 0.04 * (np.random.rand(2) - 0.5)
            cx = ax + jitter[0]
            cy = ay + jitter[1]
            rho += np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * config.atom_sigma ** 2))

    rho -= rho.min()
    rho /= rho.max() if rho.max() > 0 else 1
    return {"x": X, "y": Y, "rho": rho}


def afm_image(rho, sharpness=4.0):
    lap = (
        -4 * rho
        + np.roll(rho, 1, axis=0) + np.roll(rho, -1, axis=0)
        + np.roll(rho, 1, axis=1) + np.roll(rho, -1, axis=1)
    )
    curvature = np.abs(lap)
    curvature -= curvature.min()
    curvature /= curvature.max() if curvature.max() > 0 else 1

    base = 1.0 - np.exp(-sharpness * rho)
    img = 0.65 * base + 0.35 * curvature

    img -= img.min()
    img /= img.max() if img.max() > 0 else 1
    return img


def metrics_from_density(rho):
    eps = 1e-12
    E_mean = float(np.mean(rho))

    p = rho / (rho.sum() + eps)
    p = p[p > 0]
    I_entropy = float(-(p * np.log(p + eps)).sum())

    lap = (
        -4 * rho
        + np.roll(rho, 1, axis=0) + np.roll(rho, -1, axis=0)
        + np.roll(rho, 1, axis=1) + np.roll(rho, -1, axis=1)
    )
    delta_phi = float(np.mean(np.abs(lap)))

    C_codex = float((E_mean * I_entropy) / (1 + abs(delta_phi)))

    return {
        "E_mean": E_mean,
        "I_entropy": I_entropy,
        "DeltaPhi_mean": delta_phi,
        "C_codex": C_codex,
        "H7": H7,
        "C_over_H7": C_codex / H7 if H7 != 0 else float("nan"),
    }


def save_afm(img, path, title):
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5), dpi=200)
    plt.imshow(img, cmap="gray", origin="lower")
    plt.axis("off")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", pad_inches=0.0)
    plt.close()


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_quantum_imaging_experiment(config=None, base=None):
    if config is None:
        config = QuantumImagingConfig(seed=int(datetime.utcnow().timestamp()) % 65535)
    if base is None:
        base = Path(__file__).resolve().parent

    visuals = base / "visuals"
    state_dir = base / "state"

    fields = synthesize_density(config)
    rho = fields["rho"]

    img = afm_image(rho, config.afm_sharpness)
    m = metrics_from_density(rho)

    stamp = datetime.utcnow().isoformat()
    state = {
        "ok": True,
        "module": "codex_quantum_imaging_v1_0",
        "version": "1.0",
        "timestamp": stamp,
        "config": asdict(config),
        "metrics": m,
        "paths": {
            "visual_afm": str((visuals / "codex_quantum_imaging_v1_0_afm.png").as_posix()),
            "state_json": str((state_dir / "codex_quantum_imaging_v1_0_state.json").as_posix()),
        },
    }

    save_afm(img, visuals / "codex_quantum_imaging_v1_0_afm.png",
             "Codex Quantum Imaging v1.0 — IBM AFM Mirror")
    save_json(state, state_dir / "codex_quantum_imaging_v1_0_state.json")

    return state


if __name__ == "__main__":
    result = run_quantum_imaging_experiment()
    print(json.dumps(result, indent=2))
