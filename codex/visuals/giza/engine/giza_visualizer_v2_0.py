# Codex Giza Visualizer v2.0
# External visual suite for the Giza Ancient Harmonic Engine
# Uses QIM/Solar-style ideas to render:
#  - ΔΦ Pyramid Harmonic Map
#  - Triadic Chamber Cross-Section
#  - Resonance Spectrum (16 / 117 / 121 / 260–450 Hz)
#  - EM Focus Sketch
#  - ΔΦ Field Shell
#  - Codex Glyph Schematic-style plot

import json
import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]  # .../codex/visuals/giza/engine -> codex/
VIS_ROOT = ROOT / "visuals" / "giza"
OUTPUTS = VIS_ROOT / "outputs"
STATE_DIR = VIS_ROOT / "state"

OUTPUTS.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Basic harmonic data (aligned with Giza Node v1.0)
# ---------------------------------------------------------------------
BANDS_HZ = {
    "infrasound": 16,
    "sarcophagus_peak": 117,
    "kings_chamber_peak": 121,
    "structural_low": 260,
    "structural_high": 450,
}

FREQS_KEY = [16, 117, 121, 260, 450]

# ---------------------------------------------------------------------
# Helper: save state
# ---------------------------------------------------------------------
def save_state(payload):
    state_path = STATE_DIR / "giza_visual_state_v2_0.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ---------------------------------------------------------------------
# A) ΔΦ Pyramid Harmonic Map (simplified QIM-style 2D field)
# ---------------------------------------------------------------------
def render_delta_phi_map():
    x = np.linspace(-1.0, 1.0, 200)
    y = np.linspace(-1.0, 1.0, 200)
    X, Y = np.meshgrid(x, y)

    # Simple synthetic ΔΦ field: three Gaussian wells for E, I, C layers
    def gauss(x0, y0, sx, sy, amp):
        return amp * np.exp(-(((X - x0) ** 2) / (2 * sx ** 2) + ((Y - y0) ** 2) / (2 * sy ** 2)))

    field = (
        gauss(-0.4, -0.3, 0.25, 0.25, 1.0) +  # Subterranean (E)
        gauss(0.0, 0.0, 0.23, 0.23, 1.2) +   # Queen's (I)
        gauss(0.3, 0.4, 0.20, 0.20, 1.4)     # King's (C)
    )

    plt.figure(figsize=(6, 6))
    plt.imshow(field, extent=[-1, 1, -1, 1], origin="lower")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.title("Giza ΔΦ Pyramid Harmonic Map (Synthetic Codex View)")
    plt.xlabel("Normalized horizontal axis")
    plt.ylabel("Normalized vertical axis")

    out_path = OUTPUTS / "giza_delta_phi_map_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# B) Triadic Chamber Cross-Section
# ---------------------------------------------------------------------
def render_triadic_cross_section():
    layers = ["Subterranean (E)", "Queen's (I)", "King's (C)", "Granite Beam Stack (∿)"]
    y_pos = np.arange(len(layers))

    plt.figure(figsize=(6, 4))
    plt.barh(y_pos, [1, 1, 1, 0.5])
    plt.yticks(y_pos, layers)
    plt.xlabel("Relative role / weight")
    plt.title("Giza Triadic Chamber Stack (E–I–C ∿)")

    out_path = OUTPUTS / "giza_triadic_cross_section_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# C) Resonance Spectrum
# ---------------------------------------------------------------------
def render_resonance_spectrum():
    freqs = np.array(FREQS_KEY, dtype=float)
    amps = np.array([0.4, 1.0, 0.95, 0.7, 0.65])

    plt.figure(figsize=(7, 4))
    plt.stem(freqs, amps, use_line_collection=True)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative amplitude (synthetic)")
    plt.title("Giza Resonance Spectrum (Key Bands)")
    plt.grid(True)

    out_path = OUTPUTS / "giza_resonance_spectrum_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# D) EM Focus Sketch
# ---------------------------------------------------------------------
def render_em_focus():
    # Simple 2D sketch: pyramid outline + EM intensity lobes
    x = np.linspace(-1, 1, 300)
    y = np.linspace(0, 1.2, 300)
    X, Y = np.meshgrid(x, y)

    # Pyramid mask: |x| <= (1 - y)
    pyramid_mask = np.abs(X) <= (1.0 - Y)
    field = np.zeros_like(X)

    # EM lobes near chamber heights (synthetic)
    field += np.exp(-((Y - 0.3) ** 2) / 0.01) * pyramid_mask
    field += np.exp(-((Y - 0.6) ** 2) / 0.008) * pyramid_mask
    field += np.exp(-((Y - 0.9) ** 2) / 0.006) * pyramid_mask

    plt.figure(figsize=(5, 6))
    plt.imshow(field, extent=[-1, 1, 0, 1.2], origin="lower")
    plt.colorbar(label="Relative EM intensity (synthetic)")
    plt.title("Giza EM Focusing Sketch (Chamber Zones)")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")

    out_path = OUTPUTS / "giza_em_focus_map_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# E) ΔΦ Field Shell (radial view)
# ---------------------------------------------------------------------
def render_delta_phi_shell():
    r = np.linspace(0, 1.0, 300)
    # Synthetic shells: lower ΔΦ near mid-radius
    delta_phi = 0.4 + 0.3 * np.cos(3 * np.pi * r)

    plt.figure(figsize=(6, 4))
    plt.plot(r, delta_phi)
    plt.xlabel("Normalized radius")
    plt.ylabel("ΔΦ (synthetic)")
    plt.title("Giza ΔΦ Field Shell Profile")
    plt.grid(True)

    out_path = OUTPUTS / "giza_delta_phi_shell_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# F) Codex Glyph Schematic-style Plot
# ---------------------------------------------------------------------
def render_glyph_schematic():
    # Radial triad diagram (E, I, C) + ∿ ring
    angles = np.array([90, 210, 330]) * np.pi / 180.0
    labels = ["E", "I", "C"]
    radii = np.ones_like(angles)

    x = radii * np.cos(angles)
    y = radii * np.sin(angles)

    plt.figure(figsize=(5, 5))
    plt.scatter(x, y, s=80)
    for xi, yi, lab in zip(x, y, labels):
        plt.text(xi, yi, lab, ha="center", va="center")

    # ∿ ring
    circle = plt.Circle((0, 0), 1.2, fill=False, linestyle="--")
    plt.gca().add_patch(circle)

    plt.axhline(0, linewidth=0.5)
    plt.axvline(0, linewidth=0.5)
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿)")
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)

    out_path = OUTPUTS / "giza_cgl_schematic_v2_0.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# MAIN RUN
# ---------------------------------------------------------------------
def main():
    render_delta_phi_map()
    render_triadic_cross_section()
    render_resonance_spectrum()
    render_em_focus()
    render_delta_phi_shell()
    render_glyph_schematic()

    state = {
        "engine": "giza_visualizer_v2_0",
        "outputs": [
            "giza_delta_phi_map_v2_0.png",
            "giza_triadic_cross_section_v2_0.png",
            "giza_resonance_spectrum_v2_0.png",
            "giza_em_focus_map_v2_0.png",
            "giza_delta_phi_shell_v2_0.png",
            "giza_cgl_schematic_v2_0.png"
        ],
        "bands_hz": FREQS_KEY
    }
    save_state(state)


if __name__ == "__main__":
    main()
