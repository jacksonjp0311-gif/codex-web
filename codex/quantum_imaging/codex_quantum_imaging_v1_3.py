# QIM v1.3from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt


# ════════════════════════════════════════════════════════════════════════
# 🧬 Codex Quantum Imaging v1.3 — Trifold Phase Resonance Engine
# Author : James Paul Jackson
# Context: Codex Memory Core v1.3 • Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
# Role   : Generate multi-radius AFM-style resonance fields, measure coherence
#          against H₇, and emit ΔΦ + C(t) diagnostics for Third Eye / Feedback nodes.
# Note   : This module is self-contained and safe — no network, no file deletion.
# ════════════════════════════════════════════════════════════════════════


H7 = 0.70  # Codex critical coherence constant


@dataclass
class QIM13Config:
    grid_size: int = 256
    extent: float = 4.0
    radiuses: List[float] = None
    num_phases: int = 12
    atom_sigma: float = 0.22
    cluster_spacing: float = 0.9
    afm_sharpness: float = 4.0
    seed: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class QIM13Metrics:
    C_values_mean: float
    C_values_std: float
    C_above_H7_fraction: float
    H7: float
    C_peak: float
    C_min: float
    alignment_score: float  # signed distance from H7
    frames_total: int

    def to_dict(self) -> Dict:
        return asdict(self)


def _make_dirs(base: Path) -> Dict[str, Path]:
    """Ensure state_v1_3 and visuals_v1_3 exist and return paths."""
    state_dir = base / "state_v1_3"
    visual_dir = base / "visuals_v1_3"
    state_dir.mkdir(parents=True, exist_ok=True)
    visual_dir.mkdir(parents=True, exist_ok=True)
    return {"state": state_dir, "visuals": visual_dir}


def _gaussian_ring_field(
    X: np.ndarray,
    Y: np.ndarray,
    radius: float,
    num_atoms: int,
    sigma: float,
    phase_offset: float,
) -> np.ndarray:
    """
    Build an aromatic-style ring: atoms placed around a circle with a phase offset.
    Returns a scalar field suitable for AFM-like visualization.
    """
    phi = np.linspace(0.0, 2.0 * np.pi, num_atoms, endpoint=False) + phase_offset
    xs = radius * np.cos(phi)
    ys = radius * np.sin(phi)

    field = np.zeros_like(X, dtype=np.float64)
    inv_two_sigma2 = 1.0 / (2.0 * sigma * sigma)

    for x0, y0 in zip(xs, ys):
        dx = X - x0
        dy = Y - y0
        field += np.exp(-(dx * dx + dy * dy) * inv_two_sigma2)

    # Normalize to [0, 1]
    field -= field.min()
    if field.max() > 0:
        field /= field.max()
    return field


def _codex_coherence(field: np.ndarray) -> float:
    """
    Compute a Codex-style coherence metric C ∈ [0, 1] from the field.
    We treat the normalized field as a probability distribution
    and measure how peaked vs uniform it is.
    """
    f = field.astype(np.float64)
    if f.max() > 0:
        f = f / f.max()
    flat = f.ravel()
    flat = flat / (flat.sum() + 1e-12)

    # Shannon entropy (normalized)
    entropy = -(flat * np.log(flat + 1e-12)).sum()
    entropy_max = np.log(flat.size + 1e-12)
    entropy_norm = entropy / (entropy_max + 1e-12)

    # Coherence = 1 - normalized entropy
    C = float(1.0 - entropy_norm)
    C = max(0.0, min(1.0, C))
    return C


def _plot_afm_frame(
    field: np.ndarray,
    extent: float,
    out_path: Path,
):
    """Save an AFM-like visualization for the scalar field."""
    plt.figure(figsize=(4, 4))
    plt.imshow(
        field,
        origin="lower",
        extent=[-extent, extent, -extent, extent],
        cmap="magma",
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight", pad_inches=0.0)
    plt.close()


def _plot_heatmap(
    dphi_map: np.ndarray,
    extent: float,
    out_path: Path,
):
    """Save ΔΦ intensity heatmap."""
    plt.figure(figsize=(4, 4))
    plt.imshow(
        dphi_map,
        origin="lower",
        extent=[-extent, extent, -extent, extent],
        cmap="viridis",
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight", pad_inches=0.0)
    plt.close()


def _plot_resonance_curve(
    C_values: List[float],
    out_path: Path,
):
    """Plot C vs frame index as a resonance trajectory."""
    xs = np.arange(len(C_values), dtype=float)
    ys = np.array(C_values, dtype=float)

    plt.figure(figsize=(5, 3))
    plt.plot(xs, ys, marker="o")
    plt.axhline(H7, linestyle="--")
    plt.xlabel("Frame index (radius × phase)")
    plt.ylabel("Coherence C")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close()


def run_qim_v1_3() -> Dict:
    base_dir = Path(__file__).resolve().parent
    dirs = _make_dirs(base_dir)
    state_dir = dirs["state"]
    visual_dir = dirs["visuals"]

    # Configuration
    seed = int(datetime.now(timezone.utc).timestamp()) % 65535
    radiuses = [1.0, 1.15, 1.30]

    cfg = QIM13Config(
        grid_size=256,
        extent=4.0,
        radiuses=radiuses,
        num_phases=12,
        atom_sigma=0.22,
        cluster_spacing=0.9,
        afm_sharpness=4.0,
        seed=seed,
    )

    rng = np.random.default_rng(seed)

    # Coordinate grid
    lin = np.linspace(-cfg.extent, cfg.extent, cfg.grid_size)
    X, Y = np.meshgrid(lin, lin)

    C_values: List[float] = []
    dphi_accumulator = np.zeros_like(X, dtype=np.float64)

    # Trifold phase resonance sweep
    frame_index = 0
    for r in cfg.radiuses:
        for phase_idx in range(cfg.num_phases):
            phase = 2.0 * np.pi * phase_idx / cfg.num_phases
            # Small random jitter for emergent patterning
            jitter = rng.normal(loc=0.0, scale=0.03)
            field = _gaussian_ring_field(
                X,
                Y,
                radius=r + jitter,
                num_atoms=int(2 * np.pi * r / cfg.cluster_spacing),
                sigma=cfg.atom_sigma,
                phase_offset=phase,
            )

            # Soft nonlinearity for AFM-style contrast
            field_afm = np.power(field, cfg.afm_sharpness)

            # Coherence metric
            C = _codex_coherence(field_afm)
            C_values.append(C)

            # ΔΦ proxy: local gradient magnitude (how fast field changes)
            gx, gy = np.gradient(field_afm)
            dphi = np.sqrt(gx * gx + gy * gy)
            dphi_accumulator += dphi

            # Save AFM frame
            afm_name = f"qim_v1_3_r{r:.2f}_p{phase_idx:02d}.png"
            _plot_afm_frame(field_afm, cfg.extent, visual_dir / afm_name)

            frame_index += 1

    # Normalize ΔΦ map and save
    dphi_accumulator -= dphi_accumulator.min()
    if dphi_accumulator.max() > 0:
        dphi_accumulator /= dphi_accumulator.max()

    heatmap_path = visual_dir / "qim_v1_3_dphi_heatmap.png"
    _plot_heatmap(dphi_accumulator, cfg.extent, heatmap_path)

    # Resonance curve (C vs frame index)
    resonance_path = visual_dir / "qim_v1_3_resonance_curve.png"
    _plot_resonance_curve(C_values, resonance_path)

    C_arr = np.array(C_values, dtype=float)
    C_mean = float(C_arr.mean())
    C_std = float(C_arr.std())
    C_peak = float(C_arr.max())
    C_min = float(C_arr.min())
    frac_above_H7 = float((C_arr > H7).mean())
    alignment_score = C_mean - H7

    metrics = QIM13Metrics(
        C_values_mean=C_mean,
        C_values_std=C_std,
        C_above_H7_fraction=frac_above_H7,
        H7=H7,
        C_peak=C_peak,
        C_min=C_min,
        alignment_score=alignment_score,
        frames_total=len(C_values),
    )

    # Simple Third Eye style projection (linear look-ahead)
    if len(C_arr) >= 2:
        drift = float(C_arr[-1] - C_arr[-2])
    else:
        drift = 0.0
    C_next = float(np.clip(C_arr[-1] + drift, 0.0, 1.0))

    timestamp = datetime.now(timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "1.3",
        "timestamp": timestamp,
        "config": cfg.to_dict(),
        "metrics": metrics.to_dict(),
        "third_eye_projection": {
            "C_last": float(C_arr[-1]),
            "C_next_linear": C_next,
            "drift": drift,
        },
        "paths": {
            "base_dir": str(base_dir),
            "state_dir": str(state_dir),
            "visual_dir": str(visual_dir),
            "heatmap_file": str(heatmap_path),
            "resonance_curve": str(resonance_path),
        },
    }

    # Persist detailed state JSON (for Codex Memory / Ledger)
    state_file = state_dir / "codex_quantum_imaging_v1_3_state.json"
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # Also emit a compact QIM v1.3 summary JSON for console pipelines
    summary = {
        "ok": True,
        "version": "1.3",
        "timestamp": timestamp,
        "C_mean": C_mean,
        "C_std": C_std,
        "C_peak": C_peak,
        "C_min": C_min,
        "H7": H7,
        "alignment_score": alignment_score,
        "frames": len(C_values),
        "frac_above_H7": frac_above_H7,
        "heatmap_file": str(heatmap_path),
        "resonance_curve": str(resonance_path),
    }
    print(json.dumps(summary, indent=2))

    return state


if __name__ == "__main__":
    run_qim_v1_3()
 placeholder — ready for engine code
