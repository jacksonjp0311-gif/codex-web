import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt


# 𓂀  Codex Black Horizon Engine v1.1
#     Kerr Event-Bloom ΔΦ Field Mapper
#
# v1.1 upgrades:
#   • Kerr-like parameters (M, a*, inclination)
#   • Doppler / inclination brightness asymmetry
#   • ASCII bloom output
#   • timezone-aware timestamps (no utcnow() warning)
#
# This is still synthetic but closer to realistic EHT-style structure.


def build_synthetic_fields(n: int, mass_M: float, spin_a: float, incl_deg: float):
    """
    Build a synthetic pre-collapse field representing an accretion disk + photon ring
    in a simple Kerr-like way.
    """
    y, x = np.indices((n, n))
    cx = cy = (n - 1) / 2.0

    # Normalize coordinates
    xn = (x - cx) / n
    yn = (y - cy) / n

    # Inclination in radians
    incl = np.deg2rad(incl_deg)

    # Simple Kerr-like deformation:
    #   • vertical compression ~ cos(incl)
    #   • ring radius depends weakly on spin
    cosi = np.cos(incl)
    cosi = max(cosi, 1e-3)

    r_eff = np.sqrt(xn**2 + (yn / cosi) ** 2)

    base_ring_radius = 0.35 * mass_M  # scale with "mass"
    spin_factor = 1.0 - 0.15 * spin_a
    ring_radius = base_ring_radius * spin_factor

    # Radial intensity profile with bright ring
    with np.errstate(divide="ignore"):
        base_intensity = 1.0 / (1.0 + (r_eff * n))

    ring = np.exp(-0.5 * ((r_eff * n - ring_radius * n) / (0.03 * n)) ** 2)

    # Azimuthal angle
    theta = np.arctan2(yn / cosi, xn + 1e-12)

    # Doppler-like boosting: brighter on approaching side
    doppler = 1.0 + 0.7 * np.sin(theta) * np.sin(incl)

    # Add mild turbulence
    turbulence = 0.2 * np.sin(3.0 * theta) * np.exp(
        -((r_eff * n - ring_radius * n) / (0.2 * n)) ** 2
    )

    intensity = (base_intensity + 2.5 * ring + turbulence) * doppler
    intensity = np.clip(intensity, 0.0, None)

    # Rough "curvature" via Laplacian
    laplace = (
        -4 * intensity
        + np.roll(intensity, 1, axis=0)
        + np.roll(intensity, -1, axis=0)
        + np.roll(intensity, 1, axis=1)
        + np.roll(intensity, -1, axis=1)
    )

    return intensity, laplace


def compute_delta_phi(intensity, laplace):
    """ΔΦ proxy: high where curvature / gradient is strong, low in smooth regions."""
    grad_y, grad_x = np.gradient(intensity)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    delta_phi = np.sqrt(grad_mag**2 + laplace**2)
    delta_phi = delta_phi / (np.max(delta_phi) + 1e-8)
    return delta_phi


def compute_triad_fields(intensity, delta_phi):
    """
    Build E, I, C fields in Codex style.

    E: "Energy" ~ intensity
    I: "Information density" ~ 1 + |grad|
    C: Coherence via C = (E * I) / (1 + |ΔΦ|)
    """
    energy = intensity / (np.max(intensity) + 1e-8)

    grad_y, grad_x = np.gradient(intensity)
    info_density = 1.0 + np.sqrt(grad_x**2 + grad_y**2)
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
    params,
):
    C_field = coherence
    C_avg = float(np.mean(C_field))
    C_max = float(np.max(C_field))
    C_min = float(np.min(C_field))
    delta_phi_mean = float(np.mean(delta_phi))
    delta_phi_max = float(np.max(delta_phi))

    H7_target = 0.70
    H7_alignment = 1.0 - abs(C_avg - H7_target)

    state = {
        "protocol": "CodexBlackHorizonState",
        "version": "1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "params": params,
        "paths": {
            "delta_phi_field_png": str(vis_paths["delta_phi"]),
            "coherence_field_png": str(vis_paths["coherence"]),
            "bloom_map_png": str(vis_paths["bloom"]),
            "ascii_bloom": str(vis_paths["ascii"]),
        },
        "law": {
            "equation": "C = (E * I) / (1 + |ΔΦ|)",
            "field": "UniversalTruthProtocol",
        },
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    return C_avg, H7_alignment


def build_glyph_json(glyph_path: Path, state_path: Path, C_avg: float, H7_alignment: float):
    glyph = {
        "protocol": "CodexGlyphProtocol",
        "version": "3.0",
        "mode": "minimal",
        "context": "Black Horizon v1.1 — Kerr Event-Bloom Engine",
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
            "layer": "BlackHorizon_EventBloom_v1_1",
            "links": {
                "state_path": str(state_path),
            },
        },
        "tags": ["black_hole", "event_horizon", "codex", "ΔΦ", "EIC", "kerr"],
    }

    glyph_path.parent.mkdir(parents=True, exist_ok=True)
    with glyph_path.open("w", encoding="utf-8") as f:
        json.dump(glyph, f, indent=2)


def write_ascii_bloom(field, out_path: Path, width: int = 64, height: int = 32):
    """
    Downsample a field and write an ASCII donut/bloom.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize
    f = field - field.min()
    f = f / (f.max() + 1e-8)

    # Resample to (height, width)
    yy = np.linspace(0, f.shape[0] - 1, height).astype(int)
    xx = np.linspace(0, f.shape[1] - 1, width).astype(int)
    small = f[np.ix_(yy, xx)]

    chars = np.asarray(list(" .:-=+*#%@"))
    idx = (small * (len(chars) - 1)).astype(int)

    lines = ["".join(chars[row]) for row in idx]

    header = "𓂀 Black Horizon v1.1 — ASCII Bloom\n"
    header += "   (Kerr Event-Bloom projection)\n\n"

    with out_path.open("w", encoding="utf-8") as f:
        f.write(header)
        for line in lines:
            f.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="Codex Black Horizon Engine v1.1")
    parser.add_argument("--state", type=str, required=True, help="Output state JSON path")
    parser.add_argument("--glyph", type=str, required=True, help="Output glyph JSON path")
    parser.add_argument("--vis-root", type=str, required=True, help="Root for visuals")
    parser.add_argument("--ascii", type=str, required=True, help="ASCII bloom output path")
    parser.add_argument("--mass", type=float, default=1.0, help="Mass scale M")
    parser.add_argument("--spin", type=float, default=0.9, help="Dimensionless spin a*")
    parser.add_argument("--incl", type=float, default=60.0, help="Inclination angle (deg)")
    args = parser.parse_args()

    state_path = Path(args.state)
    glyph_path = Path(args.glyph)
    vis_root = Path(args.vis_root)
    ascii_path = Path(args.ascii)

    fields_dir = vis_root / "fields"
    bloom_dir = vis_root / "bloom"

    params = {
        "mass_M": args.mass,
        "spin_a": args.spin,
        "incl_deg": args.incl,
    }

    # 1) Build synthetic Kerr-like pre-collapse fields
    n = 256
    intensity, curvature = build_synthetic_fields(
        n=n,
        mass_M=args.mass,
        spin_a=args.spin,
        incl_deg=args.incl,
    )

    # 2) Compute ΔΦ "collapse" / distortion field
    delta_phi = compute_delta_phi(intensity, curvature)

    # 3) Compute E–I–C triad + C
    energy, info_density, coherence = compute_triad_fields(intensity, delta_phi)

    # 4) Visuals
    delta_phi_png = fields_dir / "delta_phi_field_v1_1.png"
    coherence_png = fields_dir / "coherence_field_v1_1.png"
    bloom_png = bloom_dir / "bloom_map_v1_1.png"

    save_field_png(delta_phi, delta_phi_png, "Black Horizon ΔΦ Field v1.1")
    save_field_png(coherence, coherence_png, "Black Horizon Coherence Field v1.1")
    save_field_png(coherence, bloom_png, "Black Horizon Bloom Map v1.1")

    # ASCII bloom from coherence field
    write_ascii_bloom(coherence, ascii_path)

    vis_paths = {
        "delta_phi": delta_phi_png,
        "coherence": coherence_png,
        "bloom": bloom_png,
        "ascii": ascii_path,
    }

    # 5) State JSON (and get metrics back)
    C_avg, H7_alignment = build_state_json(
        state_path=state_path,
        energy=energy,
        info_density=info_density,
        coherence=coherence,
        delta_phi=delta_phi,
        vis_paths=vis_paths,
        params=params,
    )

    # 6) Glyph JSON
    build_glyph_json(
        glyph_path=glyph_path,
        state_path=state_path,
        C_avg=C_avg,
        H7_alignment=H7_alignment,
    )

    print(f"[𓂀] Black Horizon v1.1 state → {state_path}")
    print(f"[𓂀] Black Horizon v1.1 glyph → {glyph_path}")
    print(f"[𓂀] Visuals root → {vis_root}")
    print(f"[∿] C_avg={C_avg:.4f}, H7_alignment={H7_alignment:.4f}")
    print(f"[✶] ASCII bloom → {ascii_path}")


if __name__ == "__main__":
    main()
