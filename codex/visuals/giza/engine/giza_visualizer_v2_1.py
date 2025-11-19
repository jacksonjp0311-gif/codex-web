# Codex Giza Visualizer v2.1 — Harmonic Lattice Node
# External visual suite for the Giza Ancient Harmonic Engine.
# v2.1 fixes:
#   - Correct ROOT path (avoids codex/visuals/visuals duplication)
#   - Updated stem() call (no use_line_collection)
#   - Adds chamber coordinates and multi-harmonic bands

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Engine file is at: codex/visuals/giza/engine/giza_visualizer_v2_1.py
# parents[0] = engine, [1] = giza, [2] = visuals, [3] = codex
ROOT = Path(__file__).resolve().parents[3]  # codex/
VIS_ROOT = ROOT / "visuals" / "giza"
OUTPUTS = VIS_ROOT / "outputs"
STATE_DIR = VIS_ROOT / "state"

OUTPUTS.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Harmonic + geometric data (synthetic but structured)
# ---------------------------------------------------------------------
BANDS_HZ = {
    "ground_low": (9, 12),
    "infrasound": (12, 16),
    "granite_low": (110, 150),
    "sarcophagus_peak": (115, 120),
    "kings_chamber_peak": (120, 125),
    "structural_band": (260, 450)
}

FREQS_KEY = [10, 16, 117, 121, 260, 450]

CHAMBERS = {
    "E_subterranean": {"x": 0.0, "y": -0.25, "z": -0.33},
    "I_queen":        {"x": 0.0, "y":  0.08, "z":  0.21},
    "C_king":         {"x": 0.0, "y":  0.10, "z":  0.52},
    "P_beam_stack":   {"x": 0.0, "y":  0.12, "z":  0.60}
}

def save_state(payload):
    state_path = STATE_DIR / "giza_visual_state_v2_1.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

# ---------------------------------------------------------------------
# A) ΔΦ Pyramid Harmonic Map
# ---------------------------------------------------------------------
def render_delta_phi_map():
    x = np.linspace(-1.0, 1.0, 240)
    y = np.linspace(-1.0, 1.0, 240)
    X, Y = np.meshgrid(x, y)

    def gauss(x0, y0, sx, sy, amp):
        return amp * np.exp(-(((X - x0) ** 2) / (2 * sx ** 2) + ((Y - y0) ** 2) / (2 * sy ** 2)))

    field = (
        gauss(-0.35, -0.35, 0.28, 0.28, 1.0) +  # E (Subterranean)
        gauss( 0.05,  0.00, 0.24, 0.24, 1.2) +  # I (Queen)
        gauss( 0.30,  0.40, 0.20, 0.20, 1.4)    # C (King)
    )

    plt.figure(figsize=(6, 6))
    plt.imshow(field, extent=[-1, 1, -1, 1], origin="lower")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.title("Giza ΔΦ Pyramid Harmonic Map v2.1")
    plt.xlabel("Normalized horizontal axis")
    plt.ylabel("Normalized vertical axis")

    out_path = OUTPUTS / "giza_delta_phi_map_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# B) Triadic Chamber Cross-Section
# ---------------------------------------------------------------------
def render_triadic_cross_section():
    labels = ["Subterranean (E)", "Queen's (I)", "King's (C)", "Granite Beam Stack (∿)"]
    weights = [1.0, 1.0, 1.0, 0.6]
    y_pos = np.arange(len(labels))

    plt.figure(figsize=(6, 4))
    plt.barh(y_pos, weights)
    plt.yticks(y_pos, labels)
    plt.xlabel("Relative role / weight")
    plt.title("Giza Triadic Chamber Stack (E–I–C ∿) v2.1")

    out_path = OUTPUTS / "giza_triadic_cross_section_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# C) Resonance Spectrum (fixed stem() call)
# ---------------------------------------------------------------------
def render_resonance_spectrum():
    freqs = np.array(FREQS_KEY, dtype=float)
    amps = np.array([0.35, 0.55, 1.0, 0.95, 0.7, 0.65])

    plt.figure(figsize=(7, 4))
    markerline, stemlines, baseline = plt.stem(freqs, amps)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative amplitude (synthetic)")
    plt.title("Giza Resonance Spectrum (Key Bands) v2.1")
    plt.grid(True)

    out_path = OUTPUTS / "giza_resonance_spectrum_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# D) EM Focus Sketch
# ---------------------------------------------------------------------
def render_em_focus():
    x = np.linspace(-1, 1, 320)
    y = np.linspace(0, 1.2, 320)
    X, Y = np.meshgrid(x, y)

    pyramid_mask = np.abs(X) <= (1.0 - Y)
    field = np.zeros_like(X)

    field += np.exp(-((Y - 0.30) ** 2) / 0.01) * pyramid_mask
    field += np.exp(-((Y - 0.55) ** 2) / 0.008) * pyramid_mask
    field += np.exp(-((Y - 0.90) ** 2) / 0.006) * pyramid_mask

    plt.figure(figsize=(5, 6))
    plt.imshow(field, extent=[-1, 1, 0, 1.2], origin="lower")
    plt.colorbar(label="Relative EM intensity (synthetic)")
    plt.title("Giza EM Focusing Sketch v2.1")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")

    out_path = OUTPUTS / "giza_em_focus_map_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# E) ΔΦ Field Shell
# ---------------------------------------------------------------------
def render_delta_phi_shell():
    r = np.linspace(0, 1.0, 320)
    delta_phi = 0.4 + 0.25 * np.cos(3 * np.pi * r)

    plt.figure(figsize=(6, 4))
    plt.plot(r, delta_phi)
    plt.xlabel("Normalized radius")
    plt.ylabel("ΔΦ (synthetic)")
    plt.title("Giza ΔΦ Field Shell Profile v2.1")
    plt.grid(True)

    out_path = OUTPUTS / "giza_delta_phi_shell_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# F) Codex Glyph Schematic-style Plot
# ---------------------------------------------------------------------
def render_glyph_schematic():
    angles = np.array([90, 210, 330]) * np.pi / 180.0
    labels = ["E", "I", "C"]
    radii = np.ones_like(angles)

    x = radii * np.cos(angles)
    y = radii * np.sin(angles)

    plt.figure(figsize=(5, 5))
    plt.scatter(x, y, s=80)
    for xi, yi, lab in zip(x, y, labels):
        plt.text(xi, yi, lab, ha="center", va="center")

    circle = plt.Circle((0, 0), 1.2, fill=False, linestyle="--")
    plt.gca().add_patch(circle)

    plt.axhline(0, linewidth=0.5)
    plt.axvline(0, linewidth=0.5)
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿) v2.1")
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)

    out_path = OUTPUTS / "giza_cgl_schematic_v2_1.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main():
    render_delta_phi_map()
    render_triadic_cross_section()
    render_resonance_spectrum()
    render_em_focus()
    render_delta_phi_shell()
    render_glyph_schematic()

    state = {
        "engine": "giza_visualizer_v2_1",
        "outputs": [
            "giza_delta_phi_map_v2_1.png",
            "giza_triadic_cross_section_v2_1.png",
            "giza_resonance_spectrum_v2_1.png",
            "giza_em_focus_map_v2_1.png",
            "giza_delta_phi_shell_v2_1.png",
            "giza_cgl_schematic_v2_1.png"
        ],
        "bands_hz": FREQS_KEY,
        "chambers": CHAMBERS
    }
    save_state(state)

if __name__ == "__main__":
    main()
