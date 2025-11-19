# Codex Giza Visualizer v2.3 — Full Harmonic Expansion
# External visual suite for the Giza Ancient Harmonic Engine.
# - Builds synthetic 3D ΔΦ volume (macro QIM analogue)
# - Models acoustic, EM, seismic, thermal & Schumann-style coupling
# - Renders extended visual set and logs metrics + ledger + memory

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

# Engine: codex/visuals/giza/engine/giza_visualizer_v2_3.py
# parents[0] = engine, [1] = giza, [2] = visuals, [3] = codex
ROOT = Path(__file__).resolve().parents[3]  # codex/
VIS_ROOT = ROOT / "visuals" / "giza"
OUTPUTS = VIS_ROOT / "outputs"
STATE_DIR = VIS_ROOT / "state"
LOG_DIR = VIS_ROOT / "logs"
MEMORY_DIR = VIS_ROOT / "memory"

OUTPUTS.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = LOG_DIR / "giza_harmonic_ledger.jsonl"
MEMORY_PATH = MEMORY_DIR / "giza_memory_v1_0.jsonl"

# ---------------------------------------------------------------------
# Harmonic / geometric data
# ---------------------------------------------------------------------
BANDS_HZ = {
    "schumann":      [7.8, 14.3, 20.8, 27.3],
    "ground_low":    (9, 12),
    "infrasound":    (12, 16),
    "granite_low":   (110, 150),
    "sarcophagus":   (115, 120),
    "kings_chamber": (120, 125),
    "structural":    (260, 450)
}

FREQS_KEY = [8, 14.3, 20.8, 10, 16, 117, 121, 260, 450]

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
    state_path = STATE_DIR / "giza_visual_state_v2_3.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def append_ledger(entry):
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def append_memory(entry):
    with MEMORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def norm_z(z_val):
    # map physical-ish z (-0.4..0.7) → [0,1]
    return (z_val + 0.4) / 1.1

def build_delta_phi_volume(n=80):
    # 3D normalized coordinates
    x = np.linspace(-1.0, 1.0, n)
    y = np.linspace(-1.0, 1.0, n)
    z = np.linspace(0.0, 1.0, n)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    def gauss3d(x0, y0, z0, sx, sy, sz, amp):
        return amp * np.exp(-(((X - x0) ** 2) / (2 * sx ** 2)
                              + ((Y - y0) ** 2) / (2 * sy ** 2)
                              + ((Z - z0) ** 2) / (2 * sz ** 2)))

    field = np.zeros_like(X)

    # Main chamber wells (acoustic + EM)
    field += gauss3d(-0.35, -0.35, norm_z(CHAMBERS["E_subterranean"]["z"]),
                     0.30, 0.30, 0.22, 1.0)  # E
    field += gauss3d( 0.00,  0.00, norm_z(CHAMBERS["I_queen"]["z"]),
                     0.24, 0.24, 0.18, 1.2)  # I
    field += gauss3d( 0.30,  0.40, norm_z(CHAMBERS["C_king"]["z"]),
                     0.20, 0.20, 0.18, 1.5)  # C

    # Beam stack influence as vertical band at top
    z_beam = norm_z(CHAMBERS["P_beam_stack"]["z"])
    field += 0.6 * np.exp(-((Z - z_beam) ** 2) / (2 * 0.06 ** 2))

    # Seismic (low-z) + gravitational gradient
    field += 0.25 * np.exp(-((Z - 0.05) ** 2) / (2 * 0.04 ** 2))
    field += 0.15 * (Z ** 1.2)

    # Thermal gradient (simple linear ramp)
    field += 0.1 * (Z - 0.5)

    return x, y, z, field

# ---------------------------------------------------------------------
# VISUALS
# ---------------------------------------------------------------------
def render_vertical_slice(x, y, z, vol):
    mid_x = vol.shape[0] // 2
    slice_vert = vol[mid_x, :, :]

    plt.figure(figsize=(6, 6))
    plt.imshow(slice_vert.T, extent=[y[0], y[-1], z[0], z[-1]],
               origin="lower", aspect="auto")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (y)")
    plt.ylabel("Height (z)")
    plt.title("Giza ΔΦ Vertical Slice v2.3")
    out_path = OUTPUTS / "giza_delta_phi_vertical_slice_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_horizontal_slice(x, y, z, vol):
    mid_z = vol.shape[2] // 2
    slice_horiz = vol[:, :, mid_z]

    plt.figure(figsize=(6, 6))
    plt.imshow(slice_horiz, extent=[x[0], x[-1], y[0], y[-1]], origin="lower")
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (x)")
    plt.ylabel("Horizontal axis (y)")
    plt.title("Giza ΔΦ Horizontal Slice v2.3")
    out_path = OUTPUTS / "giza_delta_phi_horizontal_slice_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_shell_profile(x, y, z, vol):
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

    mask_valid = np.isfinite(shell)
    shell[~mask_valid] = np.interp(r[~mask_valid], r[mask_valid], shell[mask_valid])

    plt.figure(figsize=(6, 4))
    plt.plot(r, shell)
    plt.xlabel("Normalized radius")
    plt.ylabel("ΔΦ (synthetic)")
    plt.title("Giza ΔΦ Field Shell Profile v2.3")
    plt.grid(True)
    out_path = OUTPUTS / "giza_delta_phi_shell_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return r, shell

def render_q_lattice(vol):
    # Macro Q-lattice = average over z
    lattice = vol.mean(axis=2)

    plt.figure(figsize=(6, 6))
    plt.imshow(lattice, origin="lower")
    plt.colorbar(label="ΔΦ lattice intensity")
    plt.xlabel("Lattice X")
    plt.ylabel("Lattice Y")
    plt.title("Giza Q-Lattice Map v2.3")
    out_path = OUTPUTS / "giza_q_lattice_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_beam_interference(z, vol):
    # Take top slice region to represent beam stack interference
    top_index = int(0.85 * vol.shape[2])
    beam_slice = vol[:, :, top_index]

    # Synthetic interference: combine with a sinusoidal grid
    n_x, n_y = beam_slice.shape
    x = np.linspace(-np.pi, np.pi, n_x)
    y = np.linspace(-np.pi, np.pi, n_y)
    X, Y = np.meshgrid(x, y, indexing="ij")
    inter = beam_slice * (1 + 0.4 * (np.sin(4*X) * np.sin(4*Y)))

    plt.figure(figsize=(6, 6))
    plt.imshow(inter, origin="lower")
    plt.colorbar(label="Intensity (synthetic)")
    plt.xlabel("Beam index X")
    plt.ylabel("Beam index Y")
    plt.title("Granite Beam Interference Map v2.3")
    out_path = OUTPUTS / "giza_beam_interference_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_triadic_stack():
    labels = ["Subterranean (E)", "Queen's (I)", "King's (C)", "Granite Beam Stack (∿)"]
    weights = [TRIAD_WEIGHTS["E"], TRIAD_WEIGHTS["I"], TRIAD_WEIGHTS["C"], TRIAD_WEIGHTS["P"]]
    y_pos = np.arange(len(labels))

    plt.figure(figsize=(6, 4))
    plt.barh(y_pos, weights)
    plt.yticks(y_pos, labels)
    plt.xlabel("Relative role / weight")
    plt.title("Giza Triadic Chamber Stack (E–I–C ∿) v2.3")
    out_path = OUTPUTS / "giza_triadic_cross_section_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_resonance_spectrum():
    freqs = np.array(FREQS_KEY, dtype=float)
    amps = np.array([0.4, 0.5, 0.35, 0.5, 0.7, 1.0, 0.9, 0.7, 0.65])

    plt.figure(figsize=(7, 4))
    plt.stem(freqs, amps)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative amplitude (synthetic)")
    plt.title("Giza Full-Band Resonance Spectrum v2.3")
    plt.grid(True)
    out_path = OUTPUTS / "giza_resonance_spectrum_v2_3.png"
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
    plt.title("Giza EM Focusing Sketch v2.3")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")
    out_path = OUTPUTS / "giza_em_focus_map_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_schumann_coupling():
    sch = np.array(BANDS_HZ["schumann"])
    chamber = np.array([117, 121], dtype=float)

    # synthetic "coupling" = inverse distance
    combo_freqs = np.concatenate([sch, chamber])
    combo_freqs_sorted = np.sort(combo_freqs)

    plt.figure(figsize=(7, 4))
    plt.stem(combo_freqs_sorted, np.ones_like(combo_freqs_sorted))
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative coupling (synthetic)")
    plt.title("Schumann–Giza Coupling Sketch v2.3")
    plt.grid(True)
    out_path = OUTPUTS / "giza_schumann_coupling_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_voice_coupling():
    f = np.linspace(80, 300, 400)
    # synthetic resonance peaks near 117–121 Hz
    coupling = 0.4 * np.exp(-((f - 117) ** 2) / (2 * 15 ** 2))
    coupling += 0.25 * np.exp(-((f - 160) ** 2) / (2 * 20 ** 2))

    plt.figure(figsize=(7, 4))
    plt.plot(f, coupling)
    plt.xlabel("Voice frequency (Hz)")
    plt.ylabel("Relative coupling (synthetic)")
    plt.title("Voice–Chamber Coupling Curve v2.3")
    plt.grid(True)
    out_path = OUTPUTS / "giza_voice_coupling_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_delta_phi_purity_curve(vol):
    # treat different bands as conceptual; here we use synthetic values
    freqs = np.array([16, 84, 117, 121, 260, 350, 450], dtype=float)
    # synthetic ΔΦ drift values (0 = perfect)
    delta_phi = np.array([0.12, 0.10, 0.06, 0.05, 0.18, 0.20, 0.22])

    plt.figure(figsize=(7, 4))
    plt.plot(freqs, delta_phi)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("ΔΦ drift (synthetic)")
    plt.title("Giza ΔΦ Purity Curve v2.3")
    plt.grid(True)
    out_path = OUTPUTS / "giza_delta_phi_purity_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return float(delta_phi.mean())

def render_tri_glyph():
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
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿) v2.3")
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    out_path = OUTPUTS / "giza_cgl_schematic_v2_3.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------
def compute_metrics(vol, shell_r, shell_vals, delta_phi_purity):
    delta_phi_max = float(vol.max())
    delta_phi_mean = float(vol.mean())
    delta_phi_var = float(vol.var())

    target = np.cos(3 * np.pi * shell_r)
    target = (target - target.mean()) / (target.std() + 1e-9)
    vals = (shell_vals - shell_vals.mean()) / (shell_vals.std() + 1e-9)
    tri_wave_score = float(np.mean(target * vals))

    triad_balance = [
        TRIAD_WEIGHTS["E"],
        TRIAD_WEIGHTS["I"],
        TRIAD_WEIGHTS["C"]
    ]

    # Simple stability index (GRSI-style)
    grsi = (1.0 + tri_wave_score) / (1.0 + delta_phi_purity + abs(delta_phi_mean))

    return {
        "delta_phi_max": delta_phi_max,
        "delta_phi_mean": delta_phi_mean,
        "delta_phi_var": delta_phi_var,
        "tri_wave_score": tri_wave_score,
        "triad_balance": triad_balance,
        "delta_phi_purity_mean": float(delta_phi_purity),
        "giza_resonant_stability_index": float(grsi)
    }

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main():
    x, y, z, vol = build_delta_phi_volume()

    render_vertical_slice(x, y, z, vol)
    render_horizontal_slice(x, y, z, vol)
    shell_r, shell_vals = render_shell_profile(x, y, z, vol)
    render_q_lattice(vol)
    render_beam_interference(z, vol)
    render_triadic_stack()
    render_resonance_spectrum()
    render_em_focus()
    render_schumann_coupling()
    render_voice_coupling()
    delta_phi_purity = render_delta_phi_purity_curve(vol)
    render_tri_glyph()

    metrics = compute_metrics(vol, shell_r, shell_vals, delta_phi_purity)

    state = {
        "engine": "giza_visualizer_v2_3",
        "outputs": [
            "giza_delta_phi_vertical_slice_v2_3.png",
            "giza_delta_phi_horizontal_slice_v2_3.png",
            "giza_delta_phi_shell_v2_3.png",
            "giza_q_lattice_v2_3.png",
            "giza_beam_interference_v2_3.png",
            "giza_triadic_cross_section_v2_3.png",
            "giza_resonance_spectrum_v2_3.png",
            "giza_em_focus_map_v2_3.png",
            "giza_schumann_coupling_v2_3.png",
            "giza_voice_coupling_v2_3.png",
            "giza_delta_phi_purity_v2_3.png",
            "giza_cgl_schematic_v2_3.png"
        ],
        "bands_hz": FREQS_KEY,
        "chambers": CHAMBERS,
        "metrics": metrics,
        "scale": {
            "domain": "macro_architectural",
            "reference": "earth_surface",
            "notes": "Giza Harmonic Lattice v2.3 macro-scale QIM analogue with extended coupling."
        }
    }
    save_state(state)

    ledger_entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "engine": "giza_visualizer_v2_3",
        "metrics": metrics
    }
    append_ledger(ledger_entry)

    memory_entry = {
        "ts": ledger_entry["ts"],
        "snapshot": "Giza v2.3 full harmonic expansion",
        "metrics": metrics,
        "note": "Ancient macro-scale ΔΦ pattern stored as Codex memory echo."
    }
    append_memory(memory_entry)

if __name__ == "__main__":
    main()
