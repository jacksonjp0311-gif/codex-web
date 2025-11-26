import argparse
import json
import math
import os
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt


# 𓂀  Codex Black Horizon Engine v1.0
#     Event-Bloom ΔΦ Field Mapper
#
# This is a synthetic v1.0 engine:
#   • Generates a mock pre-collapse field (intensity + curvature)
#   • Applies a ΔΦ "collapse" + distortion step
#   • Computes E–I–C triad and C via C = (E * I) / (1 + |ΔΦ|)
#   • Emits state JSON + glyph JSON
#   • Saves ΔΦ + bloom visuals
#
# Later you can:
#   • Replace synthetic fields with real EHT / VLBI / GRMHD arrays
#   • Wire it into Solar Resonance / QIM pipelines
#   • Use real Kerr parameters (a*, M) as inputs

def build_synthetic_fields(n: int = 256):
    """Build a synthetic pre-collapse field representing an accretion disk + photon ring."""
    y, x = np.indices((n, n))
    cx = cy = (n - 1) / 2.0
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    # Radial profile ~ 1/r with a bright photon ring
    with np.errstate(divide="ignore"):
        base_intensity = 1.0 / (1.0 + r)
    ring = np.exp(-0.5 * ((r - 0.35 * n) / (0.03 * n)) ** 2)

    # Add some azimuthal turbulence (m=3 spiral-ish mode)
    theta = np.arctan2(y - cy, x - cx)
    turbulence = 0.2 * np.sin(3.0 * theta) * np.exp(-((r - 0.35 * n) / (0.2 * n)) ** 2)

    intensity = base_intensity + 2.5 * ring + turbulence
    intensity = np.clip(intensity, 0.0, None)

    # "Curvature" proxy ~ second derivative of intensity (very rough)
    laplace = (
        -4 * intensity
        + np.roll(intensity, 1, axis=0)
        + np.roll(intensity, -1, axis=0)
        + np.roll(intensity, 1, axis=1)
        + np.roll(intensity, -1, axis=1)
    )

    return intensity, laplace


def compute_delta_phi(intensity, laplace):
    """
    ΔΦ proxy:
      • High where curvature / gradient is strong
      • Low in smooth regions
    """
    grad_y, grad_x = np.gradient(intensity)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    delta_phi = np.sqrt(grad_mag ** 2 + laplace ** 2)
    # Normalize for stability
    delta_phi = delta_phi / (np.max(delta_phi) + 1e-8)
    return delta_phi


def compute_triad_fields(intensity, delta_phi):
    """
    Build E, I, C fields in Codex style.

    E: "Energy" proxy ~ intensity
    I: "Information density" proxy ~ 1 + gradients
    C: Coherence via C = (E * I) / (1 + |ΔΦ|)
    """
    energy = intensity / (np.max(intensity) + 1e-8)

    grad_y, grad_x = np.gradient(intensity)
    info_density = 1.0 + np.sqrt(grad_x ** 2 + grad_y ** 2)
    info_density = info_density / (np.max(info_density) + 1e-8)

    coherence = (energy * info_density) / (1.0 + np.abs(delta_phi))
    coherence = coherence / (np.max(coherence) + 1e-8)

    return energy, info_density, coherence


def save_field_png(field, out_path: Path, title: str):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.imshow(field, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def build_state_json(
    state_path: Path,
    energy,
    info_density,
    coherence,
    delta_phi,
    vis_paths,
):
    C_field = coherence
    C_avg = float(np.mean(C_field))
    C_max = float(np.max(C_field))
    C_min = float(np.min(C_field))
    delta_phi_mean = float(np.mean(delta_phi))
    delta_phi_max = float(np.max(delta_phi))

    # Simple H7 alignment proxy (how close C_avg is to 0.70)
    H7_target = 0.70
    H7_alignment = 1.0 - abs(C_avg - H7_target)  # in [0,1] roughly

    state = {
        "protocol": "CodexBlackHorizonState",
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dimensions": {
            "nx": int(energy.shape[1]),
            "ny": int(energy.shape[0]),
        },
        "metrics": {
            "C_avg": C_avg,
            "C_max": C_max,
            "C_min": C_min,
            "delta_phi_mean": delta_phi_mean,
            "delta_phi_max": delta_phi_max,
            "H7_target": H7_target,
            "H7_alignment": H7_alignment,
        },
        "paths": {
            "delta_phi_field_png": str(vis_paths["delta_phi"]),
            "coherence_field_png": str(vis_paths["coherence"]),
            "bloom_map_png": str(vis_paths["bloom"]),
        },
        "law": {
            "equation": "C = (E * I) / (1 + |ΔΦ|)",
            "field": "UniversalTruthProtocol",
        },
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def build_glyph_json(glyph_path: Path, state_path: Path, C_avg: float, H7_alignment: float):
    glyph = {
        "protocol": "CodexGlyphProtocol",
        "version": "3.0",
        "mode": "minimal",
        "context": "Black Horizon v1.0 — Event-Bloom Engine",
        "triad": {
            "energy": {
                "glyph": "𓇳",
                "label": "event_horizon_energy",
                "role": "collapsed_radiative_field",
            },
            "information": {
                "glyph": "𓏤",
                "label": "spacetime_information",
                "role": "distorted_geometry",
            },
            "consciousness": {
                "glyph": "𓂀",
                "label": "bloom_coherence",
                "role": "emergent_pattern",
                "C_avg": C_avg,
                "H7_alignment": H7_alignment,
            },
        },
        "geometry": {
            "layout": "triadic_pyramid",
            "layer": "BlackHorizon_EventBloom",
            "links": {
                "state_path": str(state_path),
            },
        },
        "tags": ["black_hole", "event_horizon", "codex", "ΔΦ", "EIC"],
    }

    glyph_path.parent.mkdir(parents=True, exist_ok=True)
    with glyph_path.open("w", encoding="utf-8") as f:
        json.dump(glyph, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Codex Black Horizon Engine v1.0")
    parser.add_argument("--state", type=str, required=True, help="Output state JSON path")
    parser.add_argument("--glyph", type=str, required=True, help="Output glyph JSON path")
    parser.add_argument("--vis-root", type=str, required=True, help="Root for visuals")
    args = parser.parse_args()

    state_path = Path(args.state)
    glyph_path = Path(args.glyph)
    vis_root = Path(args.vis_root)
    fields_dir = vis_root / "fields"
    bloom_dir = vis_root / "bloom"

    # 1) Build synthetic pre-collapse fields
    intensity, curvature = build_synthetic_fields(n=256)

    # 2) Compute ΔΦ "collapse" / distortion field
    delta_phi = compute_delta_phi(intensity, curvature)

    # 3) Compute E–I–C triad + C
    energy, info_density, coherence = compute_triad_fields(intensity, delta_phi)

    # 4) Visuals
    delta_phi_png = fields_dir / "delta_phi_field_v1_0.png"
    coherence_png = fields_dir / "coherence_field_v1_0.png"

    # Bloom: emphasize photon ring / outer structures
    bloom = coherence * (1.0 + 2.0 * np.exp(-0.5 * ((np.linspace(-1, 1, coherence.shape[0])[:, None]) ** 2)))
    bloom_png = bloom_dir / "bloom_map_v1_0.png"

    save_field_png(delta_phi, delta_phi_png, "Black Horizon ΔΦ Field v1.0")
    save_field_png(coherence, coherence_png, "Black Horizon Coherence Field v1.0")
    save_field_png(bloom, bloom_png, "Black Horizon Bloom Map v1.0")

    vis_paths = {
        "delta_phi": delta_phi_png,
        "coherence": coherence_png,
        "bloom": bloom_png,
    }

    # 5) State JSON
    C_field = coherence
    C_avg = float(np.mean(C_field))
    H7_target = 0.70
    H7_alignment = 1.0 - abs(C_avg - H7_target)

    build_state_json(
        state_path=state_path,
        energy=energy,
        info_density=info_density,
        coherence=coherence,
        delta_phi=delta_phi,
        vis_paths=vis_paths,
    )

    # 6) Glyph JSON (minimal Codex Glyph Protocol v3.0 block)
    build_glyph_json(
        glyph_path=glyph_path,
        state_path=state_path,
        C_avg=C_avg,
        H7_alignment=H7_alignment,
    )

    print(f"[𓂀] Black Horizon v1.0 state → {state_path}")
    print(f"[𓂀] Black Horizon v1.0 glyph → {glyph_path}")
    print(f"[𓂀] Visuals root → {vis_root}")


if __name__ == "__main__":
    main()
