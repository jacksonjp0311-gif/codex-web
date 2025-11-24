"""
𓂀  Quantum Crystal Codex v9.1 — Lattice Glyph Engine
    Law: C = (E·I) / (1 + |ΔΦ|)
    Mode: 3D crystal field → ΔΦ → triadic state (E–I–C ∿, H₇)
"""

import os, json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt


# 𓊹  LATTICE CONSTRUCTION
def build_crystal(shape=(48, 48, 48), seed=911):
    np.random.seed(seed)
    z, y, x = np.indices(shape)

    # scaled coordinates (0 → 2π)
    sx = 2.0 * np.pi * x / shape[2]
    sy = 2.0 * np.pi * y / shape[1]
    sz = 2.0 * np.pi * z / shape[0]

    # base crystal harmonics
    base = (
        0.6 * np.sin(sx)
        + 0.6 * np.sin(sy)
        + 0.6 * np.sin(sz)
        + 0.3 * np.sin(sx + sy + sz)
    )

    # small structured noise
    noise = 0.15 * np.random.randn(*shape)
    field = base + noise

    # normalize to [0, 1]
    field -= field.min()
    field /= max(field.max(), 1e-9)
    return field


# 𓊹  ΔΦ FIELD
def delta_phi_field(field):
    gx, gy, gz = np.gradient(field)
    dphi = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)
    return dphi


# 𓊹  TRIAD + METRICS
def triad_metrics(field, dphi):
    flat_phi = dphi.reshape(-1)

    # energy ~ mean crystal amplitude
    E_val = float(field.mean())
    # information ~ variance of ΔΦ
    I_val = float(np.var(flat_phi))

    # ΔΦ histogram gradient → coarse coherence roughness
    bins = np.linspace(0.0, float(flat_phi.max()), 64)
    hist, edges = np.histogram(flat_phi, bins=bins, density=True)
    grad = np.gradient(hist)
    delta_phi = float(np.mean(np.abs(grad)))

    C_val = (E_val * I_val) / (1.0 + abs(delta_phi))
    H7 = 0.70

    stats = {
        "phi_min": float(flat_phi.min()),
        "phi_max": float(flat_phi.max()),
        "phi_mean": float(flat_phi.mean()),
    }

    triad = {
        "E": E_val,
        "I": I_val,
        "C": C_val,
        "H7": H7,
        "placidity": "∿",
        "delta_phi": delta_phi,
    }

    return triad, stats, (hist, 0.5 * (edges[:-1] + edges[1:]))


# 𓊹  VISUAL HELPERS
def save_img(arr, path, title):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.figure()
    plt.imshow(arr, origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_curve(x, y, path, title, xlabel, ylabel):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.figure()
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


# 𓊹  MAIN RUNNER
def run_qcx_v9_1(output_root="."):
    field = build_crystal()
    dphi = delta_phi_field(field)
    triad, stats, (hist, centers) = triad_metrics(field, dphi)

    z_mid = field.shape[0] // 2
    y_mid = field.shape[1] // 2
    x_mid = field.shape[2] // 2

    # crystal slices (XY, XZ, YZ) for intuition
    slice_xy = field[z_mid, :, :]
    slice_xz = field[:, y_mid, :]
    slice_yz = field[:, :, x_mid]

    # ΔΦ central slice
    dphi_xy = dphi[z_mid, :, :]

    state_path = os.path.join(output_root, "state", "v9_1", "qc_v9_1_state.json")

    img_xy_field = os.path.join(output_root, "visuals", "v9_1", "qc_field_xy_v9_1.png")
    img_xz_field = os.path.join(output_root, "visuals", "v9_1", "qc_field_xz_v9_1.png")
    img_yz_field = os.path.join(output_root, "visuals", "v9_1", "qc_field_yz_v9_1.png")
    img_xy_dphi  = os.path.join(output_root, "visuals", "v9_1", "qc_dphi_xy_v9_1.png")
    curve_path   = os.path.join(output_root, "visuals", "v9_1", "qc_resonance_curve_v9_1.png")

    save_img(slice_xy, img_xy_field, "QCX v9.1 — Crystal Field XY")
    save_img(slice_xz, img_xz_field, "QCX v9.1 — Crystal Field XZ")
    save_img(slice_yz, img_yz_field, "QCX v9.1 — Crystal Field YZ")
    save_img(dphi_xy,  img_xy_dphi,  "QCX v9.1 — ΔΦ Central Slice")

    save_curve(
        centers,
        hist,
        curve_path,
        "QCX v9.1 — ΔΦ Resonance Curve",
        "ΔΦ",
        "Density",
    )

    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    state = {
        "module": "Codex Quantum Crystal v9.1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "triad": triad,
        "stats": stats,
        "links": {
            "qim": "codex_quantum_imaging_v2_2",
            "tunneling": "codex_quantum_tunneling_v1_0",
            "giza": "giza_drift_mesh",
        },
        "outputs": {
            "field_xy": img_xy_field,
            "field_xz": img_xz_field,
            "field_yz": img_yz_field,
            "dphi_xy": img_xy_dphi,
            "resonance_curve": curve_path,
        },
        "law": "C=(E·I)/(1+|ΔΦ|)"
    }

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

    # print short summary for the orchestrator
    summary = {
        "state_path": state_path,
        "triad": triad,
        "stats": stats,
    }
    print(json.dumps(summary, indent=2))
    return state_path


if __name__ == "__main__":
    run_qcx_v9_1(".")
