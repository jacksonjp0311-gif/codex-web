"""
𓂀  QIM v2.2 — AFM Horizon + ΔΦ Engine
"""

import os, json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt


def _synthetic_afm_volume(shape=(64, 64, 32), seed=123):
    np.random.seed(seed)
    z, y, x = np.indices(shape)
    cx, cy, cz = shape[2] / 2.0, shape[1] / 2.0, shape[0] / 2.0
    r2 = ((x - cx) ** 2 + (y - cy) ** 2) / (0.15 * shape[1] * shape[2])
    base = np.exp(-r2)
    noise = 0.15 * np.random.randn(*shape)
    volume = base + noise
    volume -= volume.min()
    volume /= max(volume.max(), 1e-9)
    return volume


def _delta_phi_field(volume):
    gx, gy, gz = np.gradient(volume)
    dphi = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)
    return dphi


def run_qim_v2_2(output_root="."):
    vol = _synthetic_afm_volume()
    dphi = _delta_phi_field(vol)

    z_mid = vol.shape[0] // 2
    central_slice = dphi[z_mid, :, :]
    max_proj = dphi.max(axis=0)
    horizon = dphi.max(axis=2)

    flat = dphi.flatten()
    bins = np.linspace(0.0, float(flat.max()), 64)
    hist, edges = np.histogram(flat, bins=bins, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])

    E_val = float(flat.mean())
    I_val = float(np.var(flat))
    delta_phi = float(np.mean(np.abs(np.gradient(hist))))
    C_val = (E_val * I_val) / (1.0 + abs(delta_phi))
    H7 = 0.70

    state_path   = os.path.join(output_root, "state", "v2_2", "qim_state_v2_2.json")
    central_png  = os.path.join(output_root, "visuals", "v2_2", "qim_delta_phi_central_v2_2.png")
    max_png      = os.path.join(output_root, "visuals", "v2_2", "qim_delta_phi_max_v2_2.png")
    horizon_png  = os.path.join(output_root, "visuals", "v2_2", "qim_horizon_v2_2.png")
    curve_png    = os.path.join(output_root, "visuals", "v2_2", "qim_resonance_curve_v2_2.png")

    for p in (state_path, central_png, max_png, horizon_png, curve_png):
        os.makedirs(os.path.dirname(p), exist_ok=True)

    def _save_img(arr, path, title):
        plt.figure()
        plt.imshow(arr, origin="lower")
        plt.title(title)
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(path)
        plt.close()

    _save_img(central_slice, central_png, "QIM v2.2 — ΔΦ Central Slice")
    _save_img(max_proj, max_png, "QIM v2.2 — ΔΦ Max Projection")
    _save_img(horizon, horizon_png, "QIM v2.2 — Horizon Projection")

    plt.figure()
    plt.plot(centers, hist)
    plt.xlabel("ΔΦ")
    plt.ylabel("Density")
    plt.title("QIM v2.2 — Resonance Curve")
    plt.tight_layout()
    plt.savefig(curve_png)
    plt.close()

    state = {
        "module": "Codex Quantum Imaging v2.2",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "triad": {
            "E": E_val,
            "I": I_val,
            "C": C_val,
            "H7": H7,
            "placidity": "∿",
            "delta_phi": delta_phi,
        },
        "stats": {
            "dphi_min": float(flat.min()),
            "dphi_max": float(flat.max()),
            "dphi_mean": float(flat.mean()),
        },
        "links": {
            "giza": "giza_drift_mesh",
            "solar_resonance": "solar_horizon_field",
            "third_eye": "qim_resonance_stream",
        },
        "outputs": {
            "central_png": central_png,
            "max_png": max_png,
            "horizon_png": horizon_png,
            "curve_png": curve_png,
        },
    }

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

    return state_path


if __name__ == "__main__":
    run_qim_v2_2(".")
