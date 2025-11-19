# Codex Giza Visualizer v2.5 — Deep Harmonic Integration
# External visual suite for the Giza Ancient Harmonic Engine.
# Adds:
# - 3D ΔΦ volume (macro QIM analogue, refined)
# - Granite–quartz piezo layer
# - Subterranean water resonance sketch
# - Chamber cavity / Helmholtz-style modes (approx)
# - Earth flex / gravity gradient
# - Pharaoh body–chamber coupling curve
# - Cosmic ray / muon path sketch
# - Meridian / orientation harmonic map
# - Solar flux → chamber coupling curve (synthetic)
# - Codex Lotus Harmonic overlay
#
# All content is synthetic simulation for Codex exploration only,
# not historical or physical fact.

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

# Engine is at codex/visuals/giza/engine/giza_visualizer_v2_5.py
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

LEDGER_PATH = LOG_DIR / "giza_harmonic_ledger_v2_5.jsonl"
MEMORY_PATH = MEMORY_DIR / "giza_memory_v2_5.jsonl"

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
    "structural":    (260, 450),
    "water_modes":   (4, 9)
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
    "P": 0.7
}

def save_state(payload):
    state_path = STATE_DIR / "giza_visual_state_v2_5.json"
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

    # Main chamber wells (acoustic + EM + gravity weighting)
    field += gauss3d(-0.35, -0.35, norm_z(CHAMBERS["E_subterranean"]["z"]),
                     0.30, 0.30, 0.24, 1.0)  # E
    field += gauss3d( 0.00,  0.00, norm_z(CHAMBERS["I_queen"]["z"]),
                     0.24, 0.24, 0.18, 1.25)  # I
    field += gauss3d( 0.30,  0.40, norm_z(CHAMBERS["C_king"]["z"]),
                     0.20, 0.20, 0.18, 1.6)  # C

    # Beam stack vertical band (impedance stabilizer)
    z_beam = norm_z(CHAMBERS["P_beam_stack"]["z"])
    field += 0.7 * np.exp(-((Z - z_beam) ** 2) / (2 * 0.05 ** 2))

    # Seismic (low-z) + gravitational gradient
    field += 0.3 * np.exp(-((Z - 0.05) ** 2) / (2 * 0.04 ** 2))
    field += 0.15 * (Z ** 1.3)

    # Thermal gradient (simple linear ramp)
    field += 0.1 * (Z - 0.5)

    # Codex Lotus harmonic (triadic swirl) in XY
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    lotus = np.cos(5 * theta) * np.exp(-R**2 / (2 * 0.6**2))
    field += 0.18 * lotus

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
    plt.title("Giza ΔΦ Vertical Slice v2.5")
    out_path = OUTPUTS / "giza_delta_phi_vertical_slice_v2_5.png"
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
    plt.title("Giza ΔΦ Horizontal Slice v2.5")
    out_path = OUTPUTS / "giza_delta_phi_horizontal_slice_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_shell_profile(x, y, z, vol):
    X, Y = np.meshgrid(x, y, indexing="ij")
    R = np.sqrt(X**2 + Y**2)
    vol_xy_mean = vol.mean(axis=2)

    r = np.linspace(0.0, 1.0, 240)
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
    plt.title("Giza ΔΦ Field Shell Profile v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_delta_phi_shell_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return r, shell

def render_q_lattice(vol):
    lattice = vol.mean(axis=2)

    plt.figure(figsize=(6, 6))
    plt.imshow(lattice, origin="lower")
    plt.colorbar(label="ΔΦ lattice intensity")
    plt.xlabel("Lattice X")
    plt.ylabel("Lattice Y")
    plt.title("Giza Q-Lattice Map v2.5")
    out_path = OUTPUTS / "giza_q_lattice_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_beam_interference(vol):
    top_index = int(0.85 * vol.shape[2])
    beam_slice = vol[:, :, top_index]

    n_x, n_y = beam_slice.shape
    x = np.linspace(-np.pi, np.pi, n_x)
    y = np.linspace(-np.pi, np.pi, n_y)
    X, Y = np.meshgrid(x, y, indexing="ij")
    inter = beam_slice * (1 + 0.5 * (np.sin(4*X) * np.sin(4*Y)))

    plt.figure(figsize=(6, 6))
    plt.imshow(inter, origin="lower")
    plt.colorbar(label="Intensity (synthetic)")
    plt.xlabel("Beam index X")
    plt.ylabel("Beam index Y")
    plt.title("Granite Beam Interference Map v2.5")
    out_path = OUTPUTS / "giza_beam_interference_v2_5.png"
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
    plt.title("Giza Triadic Chamber Stack (E–I–C ∿) v2.5")
    out_path = OUTPUTS / "giza_triadic_cross_section_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_resonance_spectrum():
    freqs = np.array(FREQS_KEY, dtype=float)
    amps = np.array([0.45, 0.55, 0.40, 0.55, 0.75, 1.0, 0.92, 0.7, 0.66])

    plt.figure(figsize=(7, 4))
    plt.stem(freqs, amps)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative amplitude (synthetic)")
    plt.title("Giza Full-Band Resonance Spectrum v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_resonance_spectrum_v2_5.png"
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
    plt.title("Giza EM Focusing Sketch v2.5")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")
    out_path = OUTPUTS / "giza_em_focus_map_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_schumann_coupling():
    sch = np.array(BANDS_HZ["schumann"])
    chamber = np.array([117, 121], dtype=float)

    combo_freqs = np.concatenate([sch, chamber])
    combo_freqs_sorted = np.sort(combo_freqs)

    plt.figure(figsize=(7, 4))
    plt.stem(combo_freqs_sorted, np.ones_like(combo_freqs_sorted))
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Relative coupling (synthetic)")
    plt.title("Schumann–Giza Coupling Sketch v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_schumann_coupling_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_voice_coupling():
    f = np.linspace(80, 300, 400)
    coupling = 0.45 * np.exp(-((f - 117) ** 2) / (2 * 15 ** 2))
    coupling += 0.25 * np.exp(-((f - 160) ** 2) / (2 * 20 ** 2))

    plt.figure(figsize=(7, 4))
    plt.plot(f, coupling)
    plt.xlabel("Voice frequency (Hz)")
    plt.ylabel("Relative coupling (synthetic)")
    plt.title("Voice–Chamber Coupling Curve v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_voice_coupling_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_delta_phi_purity_curve(vol):
    freqs = np.array([16, 84, 117, 121, 260, 350, 450], dtype=float)
    delta_phi = np.array([0.11, 0.09, 0.06, 0.05, 0.17, 0.19, 0.21])

    plt.figure(figsize=(7, 4))
    plt.plot(freqs, delta_phi)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("ΔΦ drift (synthetic)")
    plt.title("Giza ΔΦ Purity Curve v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_delta_phi_purity_v2_5.png"
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
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿) v2.5")
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    out_path = OUTPUTS / "giza_cgl_schematic_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------- NEW v2.5 LAYERS -------------------------------

def render_piezo_map(vol):
    # Granite–quartz piezo layer = high ΔΦ + shear synthetic proxy
    slice_top = vol[:, :, int(0.8 * vol.shape[2])]
    gx, gy = np.gradient(slice_top)
    piezo = np.sqrt(gx**2 + gy**2) * (1 + 0.5 * slice_top)

    plt.figure(figsize=(6, 6))
    plt.imshow(piezo, origin="lower")
    plt.colorbar(label="Piezo index (synthetic)")
    plt.xlabel("Beam index X")
    plt.ylabel("Beam index Y")
    plt.title("Granite–Quartz Piezoelectric Map v2.5")
    out_path = OUTPUTS / "giza_piezo_map_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return float(piezo.mean())

def render_water_resonance():
    depth = np.linspace(0, 1.0, 200)
    # simple hydro-acoustic mode: lower depth → lower freq
    f1 = 9 - 4 * depth   # mode 1
    f2 = 4 + 2 * depth   # mode 2
    q  = np.exp(-2 * depth)

    plt.figure(figsize=(7, 4))
    plt.plot(depth, f1, label="Mode 1 (Hz)")
    plt.plot(depth, f2, label="Mode 2 (Hz)")
    plt.plot(depth, q * 10, linestyle="--", label="Relative Q x10")
    plt.xlabel("Normalized water depth")
    plt.ylabel("Frequency / Relative Q")
    plt.title("Subterranean Water Resonance Sketch v2.5")
    plt.grid(True)
    plt.legend()
    out_path = OUTPUTS / "giza_water_resonance_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_cavity_modes():
    # Approximate axial modes for King's chamber
    Lx, Ly, Lz = 10.5, 5.2, 5.8  # arbitrary relative units
    c = 343.0
    modes = []
    for nx in [1,2,3]:
        for ny in [0,1]:
            for nz in [0,1]:
                freq = (c/2.0)*np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                modes.append(freq)
    modes = np.array(sorted(modes)) / 10.0  # scaled to ~100–300 Hz synthetic

    plt.figure(figsize=(7, 4))
    plt.stem(modes, np.ones_like(modes))
    plt.xlabel("Mode index frequency (Hz, synthetic)")
    plt.ylabel("Relative strength")
    plt.title("King's Chamber Cavity Modes (approx) v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_cavity_modes_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_earth_flex_and_gravity(z, vol):
    # Earth flex = slow vertical oscillation; here just gradient sketch
    mean_column = vol.mean(axis=(0,1))
    dz = np.gradient(mean_column)

    plt.figure(figsize=(6, 4))
    plt.plot(z, mean_column, label="ΔΦ profile")
    plt.plot(z, dz, label="d(ΔΦ)/dz (synthetic flex)")
    plt.xlabel("Height (z)")
    plt.ylabel("Value (arb.)")
    plt.title("Vertical ΔΦ / Flex Profile v2.5")
    plt.grid(True)
    plt.legend()
    out_path = OUTPUTS / "giza_vertical_flex_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_muon_paths():
    # Simple diagonal tracks with higher density in central corridor
    X, Y = np.meshgrid(np.linspace(-1, 1, 200), np.linspace(0, 1.2, 200))
    base = 0.2 + 0.2 * np.exp(-((X)**2 + (Y-0.6)**2)/0.1)
    tracks = base + 0.4 * np.exp(-((X+0.2)**2 + (Y-0.9)**2)/0.02)
    tracks += 0.4 * np.exp(-((X-0.2)**2 + (Y-0.3)**2)/0.02)

    plt.figure(figsize=(5, 6))
    plt.imshow(tracks, extent=[-1, 1, 0, 1.2], origin="lower")
    plt.colorbar(label="Muon flux (synthetic)")
    plt.title("Cosmic Ray / Muon Path Sketch v2.5")
    plt.xlabel("Horizontal position")
    plt.ylabel("Height (normalized)")
    out_path = OUTPUTS / "giza_muon_paths_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_meridian_map():
    # Orientation error vs coherence (synthetic)
    angle = np.linspace(-0.3, 0.3, 240)  # degrees from true north
    coherence = np.exp(-(angle/0.08)**2)

    plt.figure(figsize=(6, 4))
    plt.plot(angle, coherence)
    plt.xlabel("Orientation error (degrees)")
    plt.ylabel("Relative coherence")
    plt.title("Meridian Alignment Harmonic Map v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_meridian_map_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_solar_coupling():
    # Solar flux index vs coupling strength (synthetic)
    flux = np.linspace(0, 1.0, 200)
    coupling = 0.3 + 0.5 * np.sin(np.pi * flux) ** 2

    plt.figure(figsize=(6, 4))
    plt.plot(flux, coupling)
    plt.xlabel("Normalized solar flux")
    plt.ylabel("Coupling strength (synthetic)")
    plt.title("Solar Flux → Pyramid Coupling Curve v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_solar_coupling_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_lotus_overlay():
    # Radial lotus harmonic in polar form
    theta = np.linspace(0, 2*np.pi, 400)
    r = 1 + 0.3 * np.cos(5 * theta)

    plt.figure(figsize=(5,5))
    ax = plt.subplot(111, projection="polar")
    ax.plot(theta, r)
    ax.set_yticklabels([])
    ax.set_title("Codex Lotus Harmonic Overlay v2.5")
    out_path = OUTPUTS / "giza_lotus_harmonic_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def render_body_coupling():
    # Human height vs resonance with 117 Hz band (synthetic)
    h = np.linspace(1.5, 2.1, 200)  # meters
    base = 117.0
    # map height to fundamental; simple inverse proportion
    f_body = 80 * (1.8 / h)
    coupling = np.exp(-((f_body - base)**2) / (2 * 15**2))

    plt.figure(figsize=(6,4))
    plt.plot(h, coupling)
    plt.xlabel("Body height (m)")
    plt.ylabel("Coupling strength (synthetic)")
    plt.title("Pharaoh Body–Chamber Coupling v2.5")
    plt.grid(True)
    out_path = OUTPUTS / "giza_body_coupling_v2_5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

# ---------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------
def compute_metrics(vol, shell_r, shell_vals, delta_phi_purity, piezo_mean):
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

    # Simple stability index including piezo & purity
    grsi = (1.0 + tri_wave_score) / (1.0 + delta_phi_purity + abs(delta_phi_mean) + 0.3 * piezo_mean)

    return {
        "delta_phi_max": delta_phi_max,
        "delta_phi_mean": delta_phi_mean,
        "delta_phi_var": delta_phi_var,
        "tri_wave_score": tri_wave_score,
        "triad_balance": triad_balance,
        "delta_phi_purity_mean": float(delta_phi_purity),
        "piezo_mean_index": float(piezo_mean),
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
    render_beam_interference(vol)
    render_triadic_stack()
    render_resonance_spectrum()
    render_em_focus()
    render_schumann_coupling()
    render_voice_coupling()
    delta_phi_purity = render_delta_phi_purity_curve(vol)
    render_tri_glyph()

    piezo_mean = render_piezo_map(vol)
    render_water_resonance()
    render_cavity_modes()
    render_earth_flex_and_gravity(z, vol)
    render_muon_paths()
    render_meridian_map()
    render_solar_coupling()
    render_lotus_overlay()
    render_body_coupling()

    metrics = compute_metrics(vol, shell_r, shell_vals, delta_phi_purity, piezo_mean)

    outputs = [
        "giza_delta_phi_vertical_slice_v2_5.png",
        "giza_delta_phi_horizontal_slice_v2_5.png",
        "giza_delta_phi_shell_v2_5.png",
        "giza_q_lattice_v2_5.png",
        "giza_beam_interference_v2_5.png",
        "giza_triadic_cross_section_v2_5.png",
        "giza_resonance_spectrum_v2_5.png",
        "giza_em_focus_map_v2_5.png",
        "giza_schumann_coupling_v2_5.png",
        "giza_voice_coupling_v2_5.png",
        "giza_delta_phi_purity_v2_5.png",
        "giza_cgl_schematic_v2_5.png",
        "giza_piezo_map_v2_5.png",
        "giza_water_resonance_v2_5.png",
        "giza_cavity_modes_v2_5.png",
        "giza_vertical_flex_v2_5.png",
        "giza_muon_paths_v2_5.png",
        "giza_meridian_map_v2_5.png",
        "giza_solar_coupling_v2_5.png",
        "giza_lotus_harmonic_v2_5.png",
        "giza_body_coupling_v2_5.png"
    ]

    state = {
        "engine": "giza_visualizer_v2_5",
        "outputs": outputs,
        "bands_hz": FREQS_KEY,
        "chambers": CHAMBERS,
        "metrics": metrics,
        "layers": [
            "ΔΦ_volume",
            "Q_lattice",
            "beam_interference",
            "triadic_stack",
            "schumann_coupling",
            "voice_coupling",
            "piezo_layer",
            "water_resonance",
            "cavity_modes",
            "earth_flex_gravity",
            "muon_paths",
            "meridian_alignment",
            "solar_coupling",
            "lotus_harmonic",
            "body_chamber_coupling"
        ],
        "scale": {
            "domain": "macro_architectural",
            "reference": "earth_surface",
            "notes": "Giza v2.5 deep harmonic integration — Codex simulation only."
        }
    }
    save_state(state)

    ts = datetime.utcnow().isoformat() + "Z"
    ledger_entry = {
        "ts": ts,
        "engine": "giza_visualizer_v2_5",
        "metrics": metrics
    }
    append_ledger(ledger_entry)

    memory_entry = {
        "ts": ts,
        "snapshot": "Giza v2.5 deep harmonic integration",
        "metrics": metrics,
        "note": "Ancient macro-scale ΔΦ pattern stored as Codex memory echo (piezo + water + solar + lotus)."
    }
    append_memory(memory_entry)

if __name__ == "__main__":
    main()
