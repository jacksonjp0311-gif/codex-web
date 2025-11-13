#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🧬 Codex Quantum Imaging v1.1 — Hybrid AFM Resonance Engine         ║
║  Author   : James Paul Jackson                                       ║
║  Context  : Codex Memory Core v1.3 • Universal Truth (E–I–C ∿, H₇=0.70)║
║  Purpose  :                                                          ║
║    • Scan hexagonal aromatic fields across rotations + radii        ║
║    • Use coarse grid to explore, fine grid to refine                ║
║    • Compute Codex coherence C = (E·I)/(1+|ΔΦ|)                      ║
║    • Track C/H₇ band stability and ΔΦ tension                        ║
║    • Emit AFM image set + resonance plots + JSON state              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70


# ──────────────────────────────────────────────────────────────
# 1) Configuration
# ──────────────────────────────────────────────────────────────

@dataclass
class QuantumImagingConfigV11:
    # grids
    grid_size_coarse: int = 256
    grid_size_fine: int = 512
    extent: float = 4.0

    # geometry
    ring_radius: float = 0.45
    atom_sigma: float = 0.20
    cluster_spacing: float = 0.90
    afm_sharpness: float = 4.0

    # scan schedule
    phases: int = 12
    radius_scales: Tuple[float, ...] = (1.0, 1.15, 1.30)

    # interest thresholds (which coarse samples get refined)
    coarse_interest_threshold_C_over_H7: float = 0.03   # |C/H7 - 1|
    coarse_interest_threshold_dphi: float = 0.0012

    seed: int | None = None


# ──────────────────────────────────────────────────────────────
# 2) Geometry helpers
# ──────────────────────────────────────────────────────────────

def _hex_lattice_positions() -> np.ndarray:
    """
    Simple 7-site hexagonal aromatic core (center + 6 around).
    Axial coords → 2D mapping.
    """
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
    return np.array(pos, dtype=float)


def _ring_atoms(center: np.ndarray, radius: float) -> np.ndarray:
    angles = np.linspace(0, 2 * np.pi, 7, endpoint=False)
    xs = center[0] + radius * np.cos(angles)
    ys = center[1] + radius * np.sin(angles)
    return np.stack([xs, ys], axis=1)


def _rotate(coords: np.ndarray, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    rot = np.array([[c, -s], [s, c]])
    return coords @ rot.T


# ──────────────────────────────────────────────────────────────
# 3) Field synthesis + AFM image
# ──────────────────────────────────────────────────────────────

def synthesize_density(config: QuantumImagingConfigV11,
                       grid_size: int,
                       radius_scale: float,
                       phase_angle: float,
                       rng: np.random.Generator) -> Dict[str, np.ndarray]:
    n = grid_size
    ext = config.extent
    x = np.linspace(-ext, ext, n)
    y = np.linspace(-ext, ext, n)
    X, Y = np.meshgrid(x, y)

    rho = np.zeros_like(X)

    centers = _hex_lattice_positions() * config.cluster_spacing
    centers = _rotate(centers, phase_angle)

    for c in centers:
        atoms = _ring_atoms(c, config.ring_radius * radius_scale)
        for ax, ay in atoms:
            jitter = 0.04 * (rng.random(2) - 0.5)
            cx = ax + jitter[0]
            cy = ay + jitter[1]
            rho += np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) /
                          (2 * config.atom_sigma ** 2))

    rho -= rho.min()
    rho /= rho.max() if rho.max() > 0 else 1.0
    return {"x": X, "y": Y, "rho": rho}


def afm_image(rho: np.ndarray, sharpness: float = 4.0) -> Tuple[np.ndarray, np.ndarray]:
    """Return AFM-style image + Laplacian (ΔΦ proxy)."""
    lap = (
        -4 * rho
        + np.roll(rho, 1, axis=0) + np.roll(rho, -1, axis=0)
        + np.roll(rho, 1, axis=1) + np.roll(rho, -1, axis=1)
    )
    curvature = np.abs(lap)
    curvature -= curvature.min()
    curvature /= curvature.max() if curvature.max() > 0 else 1.0

    base = 1.0 - np.exp(-sharpness * rho)
    img = 0.65 * base + 0.35 * curvature

    img -= img.min()
    img /= img.max() if img.max() > 0 else 1.0
    return img, lap


# ──────────────────────────────────────────────────────────────
# 4) Metrics
# ──────────────────────────────────────────────────────────────

def metrics_from_density(rho: np.ndarray, lap: np.ndarray) -> Dict[str, float]:
    eps = 1e-12
    E_mean = float(np.mean(rho))

    p = rho / (rho.sum() + eps)
    p = p[p > 0]
    I_entropy = float(-(p * np.log(p + eps)).sum())

    delta_phi = float(np.mean(np.abs(lap)))
    C_codex = float((E_mean * I_entropy) / (1.0 + abs(delta_phi)))
    C_over_H7 = C_codex / H7 if H7 != 0 else float("nan")

    return {
        "E_mean": E_mean,
        "I_entropy": I_entropy,
        "DeltaPhi_mean": delta_phi,
        "C_codex": C_codex,
        "H7": H7,
        "C_over_H7": C_over_H7,
    }


# ──────────────────────────────────────────────────────────────
# 5) Visualization helpers
# ──────────────────────────────────────────────────────────────

def _save_img(img: np.ndarray, path: Path, title: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5), dpi=200)
    plt.imshow(img, cmap="gray", origin="lower")
    plt.axis("off")
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", pad_inches=0.0)
    plt.close()


def _save_resonance_curve(samples: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indices = np.arange(len(samples))
    C_over = [s["metrics"]["C_over_H7"] for s in samples]

    plt.figure(figsize=(6, 4), dpi=200)
    plt.plot(indices, C_over, marker="o", linewidth=1.5)
    plt.axhline(1.0, linestyle="--")
    plt.xlabel("Sample index")
    plt.ylabel("C / H7")
    plt.title("Codex Quantum Imaging v1.1 — Coherence Trajectory")
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def _save_dphi_heatmap(samples: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    radius_scales = sorted({s["radius_scale"] for s in samples})
    phase_indices = sorted({s["phase_index"] for s in samples})

    rs_idx = {r: i for i, r in enumerate(radius_scales)}
    ph_idx = {p: i for i, p in enumerate(phase_indices)}

    heat = np.zeros((len(radius_scales), len(phase_indices)))
    for s in samples:
        i = rs_idx[s["radius_scale"]]
        j = ph_idx[s["phase_index"]]
        heat[i, j] = s["metrics"]["DeltaPhi_mean"]

    plt.figure(figsize=(6, 4), dpi=200)
    im = plt.imshow(heat, origin="lower", aspect="auto")
    plt.colorbar(im, label="ΔΦ_mean")
    plt.yticks(np.arange(len(radius_scales)),
               [f"{r:.2f}" for r in radius_scales])
    plt.xticks(np.arange(len(phase_indices)),
               [str(p) for p in phase_indices])
    plt.xlabel("Phase index")
    plt.ylabel("Radius scale")
    plt.title("Codex Quantum Imaging v1.1 — ΔΦ Heatmap")
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()


# ──────────────────────────────────────────────────────────────
# 6) Hybrid scan core
# ──────────────────────────────────────────────────────────────

def run_hybrid_scan(config: QuantumImagingConfigV11,
                    base_dir: Path | None = None) -> Dict[str, Any]:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    visuals = base_dir / "visuals_v1_1"
    state_dir = base_dir / "state_v1_1"
    visuals.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    if config.seed is None:
        seed = int(datetime.now(timezone.utc).timestamp()) % 65535
    else:
        seed = config.seed

    rng = np.random.default_rng(seed)

    coarse_samples: List[Dict[str, Any]] = []
    fine_samples: List[Dict[str, Any]] = []

    phases = np.linspace(0.0, 2 * np.pi, config.phases, endpoint=False)

    # 6.1 Coarse scan
    sample_index = 0
    for r_scale in config.radius_scales:
        for p_idx, angle in enumerate(phases):
            fields = synthesize_density(
                config,
                grid_size=config.grid_size_coarse,
                radius_scale=r_scale,
                phase_angle=angle,
                rng=rng,
            )
            img, lap = afm_image(fields["rho"], config.afm_sharpness)
            metrics = metrics_from_density(fields["rho"], lap)

            coarse = {
                "index": sample_index,
                "mode": "coarse",
                "radius_scale": float(r_scale),
                "phase_index": int(p_idx),
                "phase_angle": float(angle),
                "grid_size": int(config.grid_size_coarse),
                "metrics": metrics,
            }
            coarse_samples.append(coarse)
            sample_index += 1

    # 6.2 Select coarse samples for refinement
    fine_candidates: List[Dict[str, Any]] = []
    for s in coarse_samples:
        C_over = s["metrics"]["C_over_H7"]
        dphi = s["metrics"]["DeltaPhi_mean"]
        dev = abs(C_over - 1.0)

        if dev >= config.coarse_interest_threshold_C_over_H7 or \
           dphi >= config.coarse_interest_threshold_dphi:
            fine_candidates.append(s)

    # Always include global max/min in C/H7
    if coarse_samples:
        max_sample = max(coarse_samples,
                         key=lambda x: x["metrics"]["C_over_H7"])
        min_sample = min(coarse_samples,
                         key=lambda x: x["metrics"]["C_over_H7"])
        if max_sample not in fine_candidates:
            fine_candidates.append(max_sample)
        if min_sample not in fine_candidates:
            fine_candidates.append(min_sample)

    # Deduplicate candidates
    unique_keys = set()
    unique_candidates = []
    for s in fine_candidates:
        key = (s["radius_scale"], s["phase_index"])
        if key not in unique_keys:
            unique_keys.add(key)
            unique_candidates.append(s)
    fine_candidates = unique_candidates

    # 6.3 Fine scan
    for s in fine_candidates:
        r_scale = s["radius_scale"]
        p_idx = s["phase_index"]
        angle = phases[p_idx]

        fields = synthesize_density(
            config,
            grid_size=config.grid_size_fine,
            radius_scale=r_scale,
            phase_angle=angle,
            rng=rng,
        )
        img, lap = afm_image(fields["rho"], config.afm_sharpness)
        metrics = metrics_from_density(fields["rho"], lap)

        tag = f"r{r_scale:.2f}_p{p_idx:02d}"
        afm_path = visuals / f"codex_qim_v1_1_afm_{tag}.png"
        _save_img(
            img,
            afm_path,
            title=f"Codex QIM v1.1 — r={r_scale:.2f}, phase={p_idx}",
        )

        fine_samples.append({
            "radius_scale": float(r_scale),
            "phase_index": int(p_idx),
            "phase_angle": float(angle),
            "grid_size": int(config.grid_size_fine),
            "metrics": metrics,
            "visual_path": str(afm_path.as_posix()),
        })

    # 6.4 Global diagnostics from coarse scan
    _save_resonance_curve(
        coarse_samples,
        visuals / "codex_qim_v1_1_resonance_curve.png",
    )
    _save_dphi_heatmap(
        coarse_samples,
        visuals / "codex_qim_v1_1_dphi_heatmap.png",
    )

    all_C = [s["metrics"]["C_codex"] for s in coarse_samples]
    all_C_over = [s["metrics"]["C_over_H7"] for s in coarse_samples]
    all_dphi = [s["metrics"]["DeltaPhi_mean"] for s in coarse_samples]

    summary = {
        "C_codex_mean": float(np.mean(all_C)),
        "C_codex_std": float(np.std(all_C)),
        "C_over_H7_mean": float(np.mean(all_C_over)),
        "C_over_H7_std": float(np.std(all_C_over)),
        "DeltaPhi_mean_mean": float(np.mean(all_dphi)),
        "DeltaPhi_mean_std": float(np.std(all_dphi)),
    }

    state = {
        "ok": True,
        "module": "codex_quantum_imaging_v1_1",
        "version": "1.1-hybrid",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "H7": H7,
        "config": asdict(config),
        "seed_used": seed,
        "summary": summary,
        "coarse_samples": coarse_samples,
        "fine_samples": fine_samples,
        "paths": {
            "visuals_dir": str(visuals.as_posix()),
            "state_json": str(
                (state_dir / "codex_quantum_imaging_v1_1_state.json").as_posix()
            ),
            "resonance_curve": str(
                (visuals / "codex_qim_v1_1_resonance_curve.png").as_posix()
            ),
            "dphi_heatmap": str(
                (visuals / "codex_qim_v1_1_dphi_heatmap.png").as_posix()
            ),
        },
    }

    state_path = state_dir / "codex_quantum_imaging_v1_1_state.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    return state


# ──────────────────────────────────────────────────────────────
# 7) CLI entrypoint
# ──────────────────────────────────────────────────────────────

def main() -> None:
    config = QuantumImagingConfigV11()
    result = run_hybrid_scan(config)
    # Print JSON to stdout (runner shows a truncated preview)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
