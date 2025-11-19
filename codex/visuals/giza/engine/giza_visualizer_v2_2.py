# Codex Giza Visualizer v2.2 — Macro QIM Harmonic Lattice
# External visual suite for the Giza Ancient Harmonic Engine.
# - Builds a synthetic 3D ΔΦ volume (macro-scale QIM analogue)
# - Derives 2D maps, shell profile, EM map, spectrum, triad glyph & stack
# - Computes metrics and appends to a harmonic ledger JSONL

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

# Engine file: codex/visuals/giza/engine/giza_visualizer_v2_2.py
# parents[0] = engine, [1] = giza, [2] = visuals, [3] = codex
ROOT = Path(__file__).resolve().parents[3]  # codex/
VIS_ROOT = ROOT / "visuals" / "giza"
OUTPUTS = VIS_ROOT / "outputs"
STATE_DIR = VIS_ROOT / "state"
LOG_DIR = VIS_ROOT / "logs"

OUTPUTS.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = LOG_DIR / "giza_harmonic_ledger.jsonl"

# ---------------------------------------------------------------------
# Harmonic + geometric data
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

TRIAD_WEIGHTS = {
    "E": 1.0,
    "I": 1.0,
    "C": 1.0,
    "P": 0.6
}

def save_state(payload):
    state_path = STATE_DIR / "giza_visual_state_v2_2.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def append_ledger(entry):
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\\n")

# ---------------------------------------------------------------------
# 3D ΔΦ VOLUME (MACRO QIM ANALOGUE)
# ---------------------------------------------------------------------
def build_delta_phi_volume(n=80):
    # Normalized coordinates: x,y in [-1,1], z in [0,1]
    x = np.linspace(-1.0, 1.0, n)
    y = np.linspace(-1.0, 1.0, n)
    z = np.linspace(0.0, 1.0, n)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    def gauss3d(x0, y0, z0, sx, sy, sz, amp):
        return amp * np.exp(-(((X - x0) ** 2) / (2 * sx ** 2)
                              + ((Y - y0) ** 2) / (2 * sy ** 2)
                              + ((Z - z0) ** 2) / (2 * sz ** 2)))

    # Map chamber z from physical-ish coordinates (-0.33..0.6) into 0..1
    def norm_z(z_val):
        # simple linear map from [-0.4, 0.7] to [0,1]
        return (z_val + 0.4) / 1.1

    field = np.zeros_like(X)

    field += gauss3d(-0.35, -0.35, norm_z(CHAMBERS["E_subterranean"]["z"]),
                     0.30, 0.30, 0.20, 1.0)  # E
    field += gauss3d( 0.00,  0.00, norm_z(CHAMBERS["I_queen"]["z"]),
                     0.24, 0.24, 0.18, 1.2)  # I
    field += gauss3d( 0.30,  0.40, norm_z(CHAMBERS["C_king"]["z"]),
                     0.20, 0.20, 0.18, 1.4)  # C

    # Slight vertical gradient to mimic load/stress & beam stack influence
    field += 0.15 * (Z ** 1.2)

    return x, y, z, field

# ---------------------------------------------------------------------
# VISUALS
# ---------------------------------------------------------------------
def render_central_slices(x, y, z, vol):
    # central vertical slice at middle x
    mid_x = vol.shape[0] // 2
    slice_vert = vol[mid_x, :, :]

    plt.figure(figsize=(6, 6))
    plt.imshow(slice_vert.T, extent=[y[0], y[-1], z[0], z[-1]], origin="lower", aspect="auto")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (y)")
    plt.ylabel("Height (z)")
    plt.title("Giza ΔΦ Vertical Slice v2.2")
    out_path = OUTPUTS / "giza_delta_phi_vertical_slice_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    # horizontal slice at mid z
    mid_z = vol.shape[2] // 2
    slice_horiz = vol[:, :, mid_z]

    plt.figure(figsize=(6, 6))
    plt.imshow(slice_horiz, extent=[x[0], x[-1], y[0], y[-1]], origin="lower")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (x)")
    plt.ylabel("Horizontal axis (y)")
    plt.title("Giza ΔΦ Horizontal Slice v2.2")
    out_path = OUTPUTS / "giza_delta_phi_horizontal_slice_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_shell_profile(x, y, z, vol):
    # radial shell profile from center in x-y plane, averaged over z
    X, Y = np.meshgrid(x, y, indexing="ij")
    R = np.sqrt(X**2 + Y**2)
    vol_xy_mean = vol.mean(axis=2)

    r = np.linspace(0.0, 1.0, 200)
    shell = np.zeros_like(r)
    for i, rv in enumerate(r):
        mask = (R >= rv - 0.01) & (R < rv + 0.01)
        if np.any(mask):
            shell[i] = vol_xy_mean[mask].mean()
        else:
            shell[i] = np.nan
    # simple nan-fill
    mask_valid = np.isfinite(shell)
    shell[~mask_valid] = np.interp(r[~mask_valid], r[mask_valid], shell[mask_valid])

    plt.figure(figsize=(6, 4))
    plt.plot(r, shell)
    plt.xlabel("Normalized radius")
    plt.ylabel("ΔΦ (synthetic)")
    plt.title("Giza ΔΦ Field Shell Profile v2.2")
    plt.grid(True)
    out_path = OUTPUTS / "giza_delta_phi_shell_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return r, shell

def render_triadic_stack():
    labels = ["Subterranean (E)", "Queen's (I)", "King's (C)", "Granite Beam Stack (∿)"]
    weights = [TRIAD_WEIGHTS["E"], TRIAD_WEIGHTS["I"], TRIAD_WEIGHTS["C"], TRIAD_WEIGHTS["P"]]
    y_pos = np.arange(len(labels))

    plt.figure(figsize=(6, 4))
    plt.barh(y_pos, weights)
    plt.yticks(y_pos, labels)
    plt.xlabel("Relative role / weight")
    plt.title("Giza Triadic Chamber Stack (E–I–C ∿) v2.2")
    out_path = OUTPUTS / "giza_triadic_cross_section_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_resonance_spectrum():
    freqs = np.array(FREQS_KEY, dtype=float)
    amps = np.array([0.35, 0.55, 1.0, 0.95, 0.7, 0.65])

    plt.figure(figsize=(7, 4))
    plt.stem(freqs, amps)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative amplitude (synthetic)")
    plt.title("Giza Resonance Spectrum (Key Bands) v2.2")
    plt.grid(True)
    out_path = OUTPUTS / "giza_resonance_spectrum_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

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
    plt.title("Giza EM Focusing Sketch v2.2")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")
    out_path = OUTPUTS / "giza_em_focus_map_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

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
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿) v2.2")
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    out_path = OUTPUTS / "giza_cgl_schematic_v2_2.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------
def compute_metrics(vol, shell_r, shell_vals):
    delta_phi_max = float(vol.max())
    delta_phi_mean = float(vol.mean())
    delta_phi_var = float(vol.var())

    # simple tri-wave score: correlation with cos(3πr)
    target = np.cos(3 * np.pi * shell_r)
    target = (target - target.mean()) / (target.std() + 1e-9)
    vals = (shell_vals - shell_vals.mean()) / (shell_vals.std() + 1e-9)
    tri_wave_score = float(np.mean(target * vals))

    triad_balance = [
        TRIAD_WEIGHTS["E"],
        TRIAD_WEIGHTS["I"],
        TRIAD_WEIGHTS["C"]
    ]

    return {
        "delta_phi_max": delta_phi_max,
        "delta_phi_mean": delta_phi_mean,
        "delta_phi_var": delta_phi_var,
        "tri_wave_score": tri_wave_score,
        "triad_balance": triad_balance
    }

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main():
    x, y, z, vol = build_delta_phi_volume()
    render_central_slices(x, y, z, vol)
    shell_r, shell_vals = render_shell_profile(x, y, z, vol)
    render_triadic_stack()
    render_resonance_spectrum()
    render_em_focus()
    render_glyph_schematic()

    metrics = compute_metrics(vol, shell_r, shell_vals)

    state = {
        "engine": "giza_visualizer_v2_2",
        "outputs": [
            "giza_delta_phi_vertical_slice_v2_2.png",
            "giza_delta_phi_horizontal_slice_v2_2.png",
            "giza_delta_phi_shell_v2_2.png",
            "giza_triadic_cross_section_v2_2.png",
            "giza_resonance_spectrum_v2_2.png",
            "giza_em_focus_map_v2_2.png",
            "giza_cgl_schematic_v2_2.png"
        ],
        "bands_hz": FREQS_KEY,
        "chambers": CHAMBERS,
        "metrics": metrics,
        "scale": {
            "domain": "macro_architectural",
            "reference": "earth_surface",
            "notes": "Giza macro-scale ΔΦ lattice (analogue to QIM molecular and Solar stellar nodes)."
        }
    }
    save_state(state)

    ledger_entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "engine": "giza_visualizer_v2_2",
        "metrics": metrics
    }
    append_ledger(ledger_entry)

if __name__ == "__main__":
    main()
