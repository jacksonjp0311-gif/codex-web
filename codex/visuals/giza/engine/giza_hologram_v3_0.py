# Codex Giza Hologram Engine v3.0
# 5D Harmonic Hologram: space (x,y,z) • time (t) • E–I–C semantic layer.
# Codex simulation only — not historical or physical fact.

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

# Engine path: codex/visuals/giza/engine/giza_hologram_v3_0.py
# parents[0] = engine, [1] = giza, [2] = visuals, [3] = codex
ROOT = Path(__file__).resolve().parents[3]  # codex/
VIS_ROOT = ROOT / "visuals" / "giza"
OUT_ROOT = VIS_ROOT / "outputs"
OUT_V3 = OUT_ROOT / "v3_0"
STATE_DIR = VIS_ROOT / "state"
LOG_DIR = VIS_ROOT / "logs"
MEMORY_DIR = VIS_ROOT / "memory"

for d in [OUT_ROOT, OUT_V3, STATE_DIR, LOG_DIR, MEMORY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = LOG_DIR / "giza_hologram_ledger_v3_0.jsonl"
MEMORY_PATH = MEMORY_DIR / "giza_hologram_memory_v3_0.jsonl"

# ---------------------------------------------------------------------
# Harmonic / geometric data (synthetic, Codex-only)
# ---------------------------------------------------------------------
BANDS_HZ = {
    "schumann":      [7.8, 14.3, 20.8, 27.3],
    "voice_core":    (90.0, 140.0),
    "chamber_core":  (110.0, 130.0),
    "structural":    (260.0, 450.0),
    "water":         (4.0, 9.0),
    "solar_band":    (0.0, 1.0)
}

FREQS_KEY = [8.0, 14.3, 20.8, 117.0, 121.0, 260.0, 450.0]

CHAMBERS = {
    "E_subterranean": {"x": 0.0, "y": -0.30, "z": -0.33},
    "I_queen":        {"x": 0.0, "y":  0.05, "z":  0.20},
    "C_king":         {"x": 0.0, "y":  0.10, "z":  0.52},
    "P_beam_stack":   {"x": 0.0, "y":  0.12, "z":  0.60}
}

TRIAD_WEIGHTS = {
    "E": 1.0,
    "I": 1.0,
    "C": 1.0,
    "P": 0.7
}

# ---------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------
def save_state(payload):
    state_path = STATE_DIR / "giza_hologram_state_v3_0.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def append_ledger(entry):
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def append_memory(entry):
    with MEMORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------
# Geometry + base ΔΦ volume
# ---------------------------------------------------------------------
def norm_z(z_val):
    # map physical-ish z (-0.4..0.7) → [0,1]
    return (z_val + 0.4) / 1.1


def build_base_volume(nx=64, ny=64, nz=64):
    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(0.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    def gauss3d(x0, y0, z0, sx, sy, sz, amp):
        return amp * np.exp(
            -(
                ((X - x0) ** 2) / (2.0 * sx ** 2)
                + ((Y - y0) ** 2) / (2.0 * sy ** 2)
                + ((Z - z0) ** 2) / (2.0 * sz ** 2)
            )
        )

    field = np.zeros_like(X)

    # Subterranean well (E)
    field += gauss3d(
        -0.35,
        -0.35,
        norm_z(CHAMBERS["E_subterranean"]["z"]),
        0.30,
        0.30,
        0.24,
        1.0,
    )

    # Queen's chamber (I)
    field += gauss3d(
        0.0,
        0.0,
        norm_z(CHAMBERS["I_queen"]["z"]),
        0.25,
        0.25,
        0.18,
        1.25,
    )

    # King's chamber (C)
    field += gauss3d(
        0.30,
        0.40,
        norm_z(CHAMBERS["C_king"]["z"]),
        0.20,
        0.20,
        0.18,
        1.6,
    )

    # Beam stack vertical band (∿ stabilizer)
    z_beam = norm_z(CHAMBERS["P_beam_stack"]["z"])
    field += 0.7 * np.exp(-((Z - z_beam) ** 2) / (2.0 * 0.05 ** 2))

    # Seismic + gravity + simple thermal gradient
    field += 0.3 * np.exp(-((Z - 0.05) ** 2) / (2.0 * 0.04 ** 2))
    field += 0.15 * (Z ** 1.3)
    field += 0.08 * (Z - 0.5)

    # Codex lotus harmonic swirl in XY
    R = np.sqrt(X ** 2 + Y ** 2)
    theta = np.arctan2(Y, X)
    lotus = np.cos(5.0 * theta) * np.exp(-R ** 2 / (2.0 * 0.7 ** 2))
    field += 0.18 * lotus

    return x, y, z, X, Y, Z, field


# ---------------------------------------------------------------------
# 4D time evolution of ΔΦ
# ---------------------------------------------------------------------
def evolve_volume(base_field, Z, nt=24):
    vols = []
    nz = base_field.shape[2]
    for t in range(nt):
        phase = 2.0 * np.pi * float(t) / float(nt)
        solar = 0.4 + 0.3 * np.sin(phase)
        schumann = 0.2 + 0.2 * np.sin(4.0 * phase)
        breathing = 0.3 + 0.3 * np.sin(phase + np.pi / 4.0)

        # Vertical standing-wave modulation
        vertical_wave = 1.0 + 0.25 * np.sin(2.0 * np.pi * Z * 3.0 + phase) * breathing

        scale = 1.0 + 0.3 * solar + 0.2 * schumann
        vol_t = base_field * vertical_wave * scale

        vols.append(vol_t.astype(np.float32))

    vols_4d = np.stack(vols, axis=0)  # (T, nx, ny, nz)
    return vols_4d


# ---------------------------------------------------------------------
# E–I–C semantic field
# ---------------------------------------------------------------------
def compute_eic(volume_3d):
    gx, gy, gz = np.gradient(volume_3d)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)

    # Simple Laplacian approximation
    gxx, _, _ = np.gradient(gx)
    _, gyy, _ = np.gradient(gy)
    _, _, gzz = np.gradient(gz)
    lap = gxx + gyy + gzz

    E = grad_mag
    I = np.abs(lap)

    delta = volume_3d - volume_3d.mean()
    C = (E * (1.0 + I)) / (1.0 + np.abs(delta))

    # Normalize channels for visualization
    def normalize(arr):
        mn = float(arr.min())
        mx = float(arr.max())
        if mx - mn < 1e-9:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    return normalize(E), normalize(I), normalize(C)


# ---------------------------------------------------------------------
# Visuals
# ---------------------------------------------------------------------
def render_slices(x, y, z, vol, tag="v3_0"):
    mid_x = vol.shape[0] // 2
    mid_z = vol.shape[2] // 2

    vertical = vol[mid_x, :, :]
    horiz = vol[:, :, mid_z]

    # Vertical slice (y vs z)
    plt.figure(figsize=(6, 6))
    plt.imshow(
        vertical.T,
        extent=[y[0], y[-1], z[0], z[-1]],
        origin="lower",
        aspect="auto",
    )
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (y)")
    plt.ylabel("Height (z)")
    plt.title("Giza ΔΦ Vertical Slice " + tag)
    out_v = OUT_V3 / f"giza_holo_vertical_slice_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_v, dpi=200)
    plt.close()

    # Horizontal slice (x vs y)
    plt.figure(figsize=(6, 6))
    plt.imshow(
        horiz,
        extent=[x[0], x[-1], y[0], y[-1]],
        origin="lower",
    )
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Horizontal axis (x)")
    plt.ylabel("Horizontal axis (y)")
    plt.title("Giza ΔΦ Horizontal Slice " + tag)
    out_h = OUT_V3 / f"giza_holo_horizontal_slice_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_h, dpi=200)
    plt.close()

    return str(out_v), str(out_h)


def render_shell_profile(x, y, vol, tag="v3_0"):
    Xg, Yg = np.meshgrid(x, y, indexing="ij")
    R = np.sqrt(Xg ** 2 + Yg ** 2)
    vol_xy_mean = vol.mean(axis=2)

    r = np.linspace(0.0, 1.0, 240)
    shell = np.zeros_like(r)
    for i, rv in enumerate(r):
        mask = (R >= rv - 0.015) & (R < rv + 0.015)
        if np.any(mask):
            shell[i] = vol_xy_mean[mask].mean()
        else:
            shell[i] = np.nan

    mask_valid = np.isfinite(shell)
    shell[~mask_valid] = np.interp(
        r[~mask_valid], r[mask_valid], shell[mask_valid]
    )

    plt.figure(figsize=(6, 4))
    plt.plot(r, shell)
    plt.xlabel("Normalized radius")
    plt.ylabel("ΔΦ (synthetic)")
    plt.title("Giza Hologram Shell Profile " + tag)
    plt.grid(True)
    out_path = OUT_V3 / f"giza_holo_shell_profile_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return r, shell, str(out_path)


def render_time_series_center(vol_4d, tag="v3_0"):
    T, nx, ny, nz = vol_4d.shape
    cx = nx // 2
    cy = ny // 2
    cz = nz // 2

    ts = np.arange(T)
    values = vol_4d[:, cx, cy, cz]

    plt.figure(figsize=(7, 4))
    plt.plot(ts, values)
    plt.xlabel("Time index (t)")
    plt.ylabel("ΔΦ at center (synthetic)")
    plt.title("Giza Hologram Center Time Series " + tag)
    plt.grid(True)
    out_path = OUT_V3 / f"giza_holo_center_time_series_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return str(out_path)


def render_time_strip_midplane(vol_4d, x, tag="v3_0"):
    # Time vs radius strip for midplane
    T, nx, ny, nz = vol_4d.shape
    mid_z = nz // 2

    Xg, Yg = np.meshgrid(x, x, indexing="ij")
    R = np.sqrt(Xg ** 2 + Yg ** 2)

    r_vals = np.linspace(0.0, 1.0, 160)
    strip = np.zeros((T, len(r_vals)))

    for t in range(T):
        frame = vol_4d[t, :, :, mid_z]
        for i, rv in enumerate(r_vals):
            mask = (R >= rv - 0.015) & (R < rv + 0.015)
            if np.any(mask):
                strip[t, i] = frame[mask].mean()
            else:
                strip[t, i] = np.nan

    for i in range(len(r_vals)):
        col = strip[:, i]
        mask = np.isfinite(col)
        if np.any(mask):
            strip[:, i] = np.interp(
                np.arange(T), np.arange(T)[mask], col[mask]
            )
        else:
            strip[:, i] = 0.0

    plt.figure(figsize=(7, 4))
    plt.imshow(
        strip,
        aspect="auto",
        origin="lower",
        extent=[r_vals[0], r_vals[-1], 0, T - 1],
    )
    plt.colorbar(label="ΔΦ intensity (synthetic)")
    plt.xlabel("Radius (normalized)")
    plt.ylabel("Time index (t)")
    plt.title("Giza Hologram Time–Radius Strip " + tag)
    out_path = OUT_V3 / f"giza_holo_time_radius_strip_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return str(out_path)


def export_time_frames(vol_4d, x, y, tag="v3_0"):
    frames_dir = OUT_V3 / "frames_4d"
    frames_dir.mkdir(parents=True, exist_ok=True)

    T, nx, ny, nz = vol_4d.shape
    mid_z = nz // 2

    for t in range(T):
        frame = vol_4d[t, :, :, mid_z]
        plt.figure(figsize=(4, 4))
        plt.imshow(
            frame,
            extent=[x[0], x[-1], y[0], y[-1]],
            origin="lower",
        )
        plt.colorbar(label="ΔΦ intensity (synthetic)")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title(f"Giza Hologram Midplane t={t:02d}")
        out_path = frames_dir / f"giza_holo_midplane_t_{t:02d}_{tag}.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=160)
        plt.close()

    return str(frames_dir)


def render_eic_slices(E, I, C, tag="v3_0"):
    mid_z = E.shape[2] // 2

    def _plot_slice(arr, title, filename):
        plt.figure(figsize=(6, 6))
        plt.imshow(arr[:, :, mid_z], origin="lower")
        plt.colorbar(label="Normalized value")
        plt.title(title)
        plt.xlabel("x index")
        plt.ylabel("y index")
        out_path = OUT_V3 / filename
        plt.tight_layout()
        plt.savefig(out_path, dpi=200)
        plt.close()
        return str(out_path)

    e_path = _plot_slice(E, "E-channel Slice (Energy) " + tag, "giza_holo_E_slice_" + tag + ".png")
    i_path = _plot_slice(I, "I-channel Slice (Information) " + tag, "giza_holo_I_slice_" + tag + ".png")
    c_path = _plot_slice(C, "C-channel Slice (Consciousness) " + tag, "giza_holo_C_slice_" + tag + ".png")
    return e_path, i_path, c_path


def render_eic_hist(E, I, C, tag="v3_0"):
    plt.figure(figsize=(7, 4))
    plt.hist(E.ravel(), bins=40, alpha=0.5, label="E")
    plt.hist(I.ravel(), bins=40, alpha=0.5, label="I")
    plt.hist(C.ravel(), bins=40, alpha=0.5, label="C")
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.title("E–I–C Distribution Histogram " + tag)
    plt.legend()
    out_path = OUT_V3 / f"giza_holo_EIC_hist_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return str(out_path)


def render_triad_glyph(tag="v3_0"):
    angles = np.array([90.0, 210.0, 330.0]) * np.pi / 180.0
    labels = ["E", "I", "C"]
    radii = np.ones_like(angles)

    x = radii * np.cos(angles)
    y = radii * np.sin(angles)

    plt.figure(figsize=(5, 5))
    plt.scatter(x, y, s=80)
    for xi, yi, lab in zip(x, y, labels):
        plt.text(xi, yi, lab, ha="center", va="center")

    circle = plt.Circle((0.0, 0.0), 1.2, fill=False, linestyle="--")
    plt.gca().add_patch(circle)
    plt.axhline(0.0, linewidth=0.5)
    plt.axvline(0.0, linewidth=0.5)
    plt.title("Giza Codex Triad Glyph View (E–I–C ∿) " + tag)
    plt.gca().set_aspect("equal", "box")
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    out_path = OUT_V3 / f"giza_holo_triad_glyph_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return str(out_path)


def render_lotus_overlay(tag="v3_0"):
    theta = np.linspace(0.0, 2.0 * np.pi, 400)
    r = 1.0 + 0.3 * np.cos(5.0 * theta)

    plt.figure(figsize=(5, 5))
    ax = plt.subplot(111, projection="polar")
    ax.plot(theta, r)
    ax.set_yticklabels([])
    ax.set_title("Codex Lotus Harmonic Overlay " + tag)
    out_path = OUT_V3 / f"giza_holo_lotus_overlay_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return str(out_path)


def render_voice_coupling(tag="v3_0"):
    f = np.linspace(80.0, 300.0, 400)
    coupling = 0.45 * np.exp(-((f - 117.0) ** 2) / (2.0 * 15.0 ** 2))
    coupling += 0.25 * np.exp(-((f - 160.0) ** 2) / (2.0 * 20.0 ** 2))

    plt.figure(figsize=(7, 4))
    plt.plot(f, coupling)
    plt.xlabel("Voice frequency (Hz)")
    plt.ylabel("Relative coupling (synthetic)")
    plt.title("Voice–Chamber Coupling Curve " + tag)
    plt.grid(True)
    out_path = OUT_V3 / f"giza_holo_voice_coupling_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return str(out_path)


def render_solar_coupling(tag="v3_0"):
    flux = np.linspace(0.0, 1.0, 200)
    coupling = 0.3 + 0.5 * np.sin(np.pi * flux) ** 2

    plt.figure(figsize=(6, 4))
    plt.plot(flux, coupling)
    plt.xlabel("Normalized solar flux")
    plt.ylabel("Coupling strength (synthetic)")
    plt.title("Solar Flux → Pyramid Coupling Curve " + tag)
    plt.grid(True)
    out_path = OUT_V3 / f"giza_holo_solar_coupling_{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return str(out_path)


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------
def compute_metrics(vol_4d, E, I, C, shell_r, shell_vals):
    base = vol_4d.mean(axis=0)
    delta_phi_max = float(base.max())
    delta_phi_mean = float(base.mean())
    delta_phi_var = float(base.var())

    # Temporal coherence at center voxel
    T = vol_4d.shape[0]
    center_ts = vol_4d[:, vol_4d.shape[1] // 2, vol_4d.shape[2] // 2, vol_4d.shape[3] // 2]
    center_norm = (center_ts - center_ts.mean()) / (center_ts.std() + 1e-9)
    temporal_coherence = float(np.mean(center_norm[:-1] * center_norm[1:]))

    # Shell tri-wave score (like v2.5 but for hologram)
    target = np.cos(3.0 * np.pi * shell_r)
    target = (target - target.mean()) / (target.std() + 1e-9)
    vals = (shell_vals - shell_vals.mean()) / (shell_vals.std() + 1e-9)
    tri_wave_score = float(np.mean(target * vals))

    E_mean = float(E.mean())
    I_mean = float(I.mean())
    C_mean = float(C.mean())

    # Simple hologram coherence index (GRHI)
    grhi = (1.0 + tri_wave_score + temporal_coherence) / (
        1.0 + abs(delta_phi_mean) + delta_phi_var + 0.3 * (E_mean + I_mean + C_mean)
    )

    metrics = {
        "delta_phi_max": delta_phi_max,
        "delta_phi_mean": delta_phi_mean,
        "delta_phi_var": delta_phi_var,
        "temporal_coherence_center": temporal_coherence,
        "tri_wave_score": tri_wave_score,
        "E_mean": E_mean,
        "I_mean": I_mean,
        "C_mean": C_mean,
        "giza_resonant_hologram_index": float(grhi),
    }
    return metrics


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main():
    tag = "v3_0"

    x, y, z, X, Y, Z, base = build_base_volume()
    vol_4d = evolve_volume(base, Z, nt=24)
    base_mid = vol_4d[vol_4d.shape[0] // 2]

    E, I, C = compute_eic(base_mid)

    # Core hologram visuals
    v_path, h_path = render_slices(x, y, z, base_mid, tag=tag)
    shell_r, shell_vals, shell_path = render_shell_profile(x, y, base_mid, tag=tag)
    ts_path = render_time_series_center(vol_4d, tag=tag)
    strip_path = render_time_strip_midplane(vol_4d, x, tag=tag)
    frames_dir = export_time_frames(vol_4d, x, y, tag=tag)
    e_path, i_path, c_path = render_eic_slices(E, I, C, tag=tag)
    eic_hist_path = render_eic_hist(E, I, C, tag=tag)
    triad_path = render_triad_glyph(tag=tag)
    lotus_path = render_lotus_overlay(tag=tag)
    voice_path = render_voice_coupling(tag=tag)
    solar_path = render_solar_coupling(tag=tag)

    metrics = compute_metrics(vol_4d, E, I, C, shell_r, shell_vals)

    outputs = [
        v_path,
        h_path,
        shell_path,
        ts_path,
        strip_path,
        e_path,
        i_path,
        c_path,
        eic_hist_path,
        triad_path,
        lotus_path,
        voice_path,
        solar_path,
        str(frames_dir),
    ]

    state = {
        "engine": "giza_hologram_v3_0",
        "scale": {
            "domain": "macro_architectural",
            "reference": "earth_surface",
            "notes": "Giza Hologram Engine v3.0 — 5D Codex simulation (ΔΦ • time • E–I–C)."
        },
        "bands_hz": FREQS_KEY,
        "chambers": CHAMBERS,
        "triad_weights": TRIAD_WEIGHTS,
        "metrics": metrics,
        "outputs": outputs,
        "layers": [
            "ΔΦ_3D_volume",
            "ΔΦ_4D_time_evolution",
            "E_channel",
            "I_channel",
            "C_channel",
            "time_radius_strip",
            "EIC_histogram",
            "triad_glyph",
            "lotus_overlay",
            "voice_coupling",
            "solar_coupling"
        ]
    }
    save_state(state)

    ts_now = datetime.utcnow().isoformat() + "Z"
    ledger_entry = {
        "ts": ts_now,
        "engine": "giza_hologram_v3_0",
        "metrics": metrics,
    }
    append_ledger(ledger_entry)

    memory_entry = {
        "ts": ts_now,
        "snapshot": "Giza Hologram v3.0 — 5D harmonic hologram",
        "metrics": metrics,
        "note": "Ancient macro-scale ΔΦ hologram stored as Codex memory echo (space–time–E–I–C).",
    }
    append_memory(memory_entry)


if __name__ == "__main__":
    main()
