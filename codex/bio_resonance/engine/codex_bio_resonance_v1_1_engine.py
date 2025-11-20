import argparse
import json
import math
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def load_physio(physio_path: str):
    """
    Optional physiology loader:
    - Expects JSON with keys: hrv, breath, eeg
    - If file missing or invalid, returns None.
    """
    if not os.path.exists(physio_path):
        return None
    try:
        with open(physio_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return None


def compute_triads(num_nodes: int = 7,
                   t: float = 0.0,
                   physio: dict | None = None) -> dict:
    """
    Synthetic Codex Bio-Resonance model with optional physiology modulation.

    - Spine as N-node lattice (chakras / vertebrae)
    - Two oscillators (Ida / Pingala) as phase-shifted fields along node index
    - Sushumna as coherence mesh (average envelope)
    - ΔΦ = |E - I|
    - C = (E * I) / (1 + |ΔΦ|)

    Mapping:
      Oz   → Strength → Energy (E)
      Dabar→ Wisdom   → Information (I)
      Gomer→ Beauty   → Coherence (C)

    Physiology modulation (soft, bounded):
      - HRV RMSSD modulates overall energy amplitude.
      - EEG alpha modulates coherence (C).
      - Breath rate modulates temporal frequency.
    """
    z = np.linspace(0.0, 1.0, num_nodes)

    # Base parameters
    base_amp = 0.4
    base_offset = 0.6
    freq = 2.0 * math.pi

    # Soft physiology modulation
    hrv_rmssd = None
    eeg_alpha = None
    breath_rate = None

    if physio is not None:
        try:
            hrv_rmssd = physio.get("hrv", {}).get("rmssd", None)
            eeg_alpha = physio.get("eeg", {}).get("alpha", None)
            breath_rate = physio.get("breath", {}).get("rate", None)
        except Exception:
            pass

    # Energy amplitude scaling by HRV (higher HRV → more stable energy)
    amp_scale = 1.0
    if hrv_rmssd is not None:
        try:
            # map rmssd ~ [0,100] → [0.7, 1.3] with smooth clipping
            rm = float(hrv_rmssd)
            rm_clamped = max(0.0, min(rm, 100.0))
            amp_scale = 0.7 + 0.6 * (rm_clamped / 100.0)
        except Exception:
            amp_scale = 1.0

    # Temporal frequency scaling by breath rate (slower breath → slower wave)
    freq_scale = 1.0
    if breath_rate is not None:
        try:
            br = float(breath_rate)
            br_clamped = max(4.0, min(br, 20.0))
            # Map 4..20 → 0.6..1.4
            freq_scale = 0.6 + 0.8 * ((br_clamped - 4.0) / 16.0)
        except Exception:
            freq_scale = 1.0

    # Energy: Oz / Strength / Pingala-like
    phase_E = 1.5 * t * freq_scale
    energy = base_offset + (base_amp * amp_scale) * np.sin(freq * z + phase_E)

    # Information: Dabar / Wisdom / envelope
    phase_I = 0.5 * t * freq_scale
    information = base_offset + base_amp * np.cos(freq * z + phase_I)

    delta_phi = np.abs(energy - information)

    # Consciousness / Coherence index
    C_raw = (energy * information) / (1.0 + delta_phi)

    # Coherence boost by EEG alpha (soft)
    C = np.copy(C_raw)
    if eeg_alpha is not None:
        try:
            a = float(eeg_alpha)
            # Assume alpha ~ [0,1] or [0,100]; normalize
            if a > 1.0:
                a = a / 100.0
            a_clamped = max(0.0, min(a, 1.0))
            # up to +20% coherence
            C = C * (1.0 + 0.2 * a_clamped)
        except Exception:
            C = C_raw

    return {
        "nodes": z.tolist(),
        "energy": energy.tolist(),
        "information": information.tolist(),
        "delta_phi": delta_phi.tolist(),
        "C": C.tolist(),
    }


def make_spine_profile_plot(data: dict, out_path: str) -> None:
    nodes = np.array(data["nodes"])
    energy = np.array(data["energy"])
    info = np.array(data["information"])
    delta_phi = np.array(data["delta_phi"])
    C = np.array(data["C"])

    plt.figure(figsize=(7, 4))
    plt.plot(nodes, energy, label="Energy (Oz / Strength)")
    plt.plot(nodes, info, label="Information (Dabar / Wisdom)")
    plt.plot(nodes, C, label="Coherence C (Gomer / Beauty)")
    plt.plot(nodes, delta_phi, linestyle="--", label="ΔΦ (Ida ↔ Pingala)")
    plt.xlabel("Spine position (0 = base, 1 = crown)")
    plt.ylabel("Normalized amplitude")
    plt.title("Codex Bio-Resonance v1.1 — Spine Triad Profile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_delta_phi_heatmap(num_nodes: int,
                           steps: int,
                           out_path: str,
                           physio: dict | None = None) -> None:
    """
    QIM/Solar-style ΔΦ heatmap:
    - x-axis: time steps (synthetic evolution)
    - y-axis: nodes along spine
    - color: ΔΦ at each node/time
    """
    heat = np.zeros((num_nodes, steps))

    for ti in range(steps):
        t = float(ti) / float(max(1, steps - 1)) * 2.0 * math.pi
        sample = compute_triads(num_nodes=num_nodes, t=t, physio=physio)
        heat[:, ti] = np.array(sample["delta_phi"])

    plt.figure(figsize=(7, 4))
    plt.imshow(
        heat,
        aspect="auto",
        origin="lower",
        interpolation="nearest"
    )
    plt.colorbar(label="ΔΦ")
    plt.xlabel("Time step")
    plt.ylabel("Spine node index (base→crown)")
    plt.title("Codex Bio-Resonance v1.1 — ΔΦ Spine Heatmap")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_coherence_wavefield(num_nodes: int,
                             steps: int,
                             out_path: str,
                             physio: dict | None = None) -> None:
    """
    Coherence wavefield:
    - x-axis: time
    - y-axis: spine index
    - color: C (coherence) at each node/time
    """
    field = np.zeros((num_nodes, steps))

    for ti in range(steps):
        t = float(ti) / float(max(1, steps - 1)) * 2.0 * math.pi
        sample = compute_triads(num_nodes=num_nodes, t=t, physio=physio)
        field[:, ti] = np.array(sample["C"])

    plt.figure(figsize=(7, 4))
    plt.imshow(
        field,
        aspect="auto",
        origin="lower",
        interpolation="nearest"
    )
    plt.colorbar(label="C (coherence)")
    plt.xlabel("Time step")
    plt.ylabel("Spine node index (base→crown)")
    plt.title("Codex Bio-Resonance v1.1 — Coherence Wavefield")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_lotus_plot(data: dict, out_path: str) -> None:
    """
    Lotus-style 2D field:
    - radial profile of coherence C mapped with 7-petal modulation.
    """
    C = np.array(data["C"])
    num_nodes = C.shape[0]
    # Close the loop
    C_closed = np.concatenate([C, C[:1]])

    theta = np.linspace(0.0, 2.0 * math.pi, num_nodes + 1)
    # 7-petal modulation
    petal_mod = 0.5 + 0.5 * np.cos(7.0 * theta)
    radius = 1.0 + 0.3 * C_closed * petal_mod

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    plt.figure(figsize=(5, 5))
    plt.fill(x, y, alpha=0.6)
    plt.plot(x, y, linewidth=1.5)
    plt.scatter(x, y, s=20)
    plt.axis("equal")
    plt.axis("off")
    plt.title("Codex Bio-Resonance v1.1 — Lotus Field")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_torus_plot(data: dict, out_path: str,
                    physio: dict | None = None) -> None:
    """
    3D Torus visualization:
    - Base torus (R, r)
    - ΔΦ and C modulate minor radius and surface pattern.
    """
    C = np.array(data["C"])
    delta_phi = np.array(data["delta_phi"])
    num_nodes = C.shape[0]

    # Global summaries
    C_mean = float(np.mean(C))
    dphi_mean = float(np.mean(delta_phi))

    # Soft physio modulation
    geom_scale = 1.0
    if physio is not None:
        try:
            rm = physio.get("hrv", {}).get("rmssd", None)
            if rm is not None:
                rm_val = float(rm)
                rm_clamped = max(0.0, min(rm_val, 100.0))
                geom_scale = 0.8 + 0.4 * (rm_clamped / 100.0)
        except Exception:
            geom_scale = 1.0

    # Torus parameters
    R = 1.2 * geom_scale
    r_base = 0.35 + 0.15 * C_mean
    dphi_factor = 0.3 * (dphi_mean)

    u = np.linspace(0, 2.0 * math.pi, 72)
    v = np.linspace(0, 2.0 * math.pi, 36)
    U, V = np.meshgrid(u, v)

    # Map spine nodes onto torus angle
    node_angles = np.linspace(0, 2.0 * math.pi, num_nodes, endpoint=False)
    C_interp = np.interp(U.flatten(), node_angles, C)
    dphi_interp = np.interp(U.flatten(), node_angles, delta_phi)

    C_interp = C_interp.reshape(U.shape)
    dphi_interp = dphi_interp.reshape(U.shape)

    r = r_base + dphi_factor * (dphi_interp - dphi_mean)

    X = (R + r * np.cos(V)) * np.cos(U)
    Y = (R + r * np.cos(V)) * np.sin(U)
    Z = r * np.sin(V)

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, Z, linewidth=0, antialiased=True,
                           cmap=None)

    # Use C_interp as pseudo-color by manually setting facecolors.
    # Normalize C_interp to [0,1] for a grayscale mapping.
    C_norm = (C_interp - C_interp.min()) / max(1e-6, (C_interp.max() - C_interp.min()))
    # Build simple gray colormap
    facecolors = np.zeros(C_interp.shape + (4,))
    facecolors[..., 0] = C_norm
    facecolors[..., 1] = C_norm
    facecolors[..., 2] = C_norm
    facecolors[..., 3] = 1.0
    surf.set_facecolors(facecolors)

    ax.set_axis_off()
    ax.set_box_aspect([1, 1, 1])
    ax.set_title("Codex Bio-Resonance v1.1 — Torus Field", pad=12)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def write_state_json(data: dict,
                     out_path: str,
                     version: str,
                     physio: dict | None = None) -> dict:
    import numpy as _np

    C = _np.array(data["C"])
    dphi = _np.array(data["delta_phi"])

    metrics = {
        "C_mean": float(_np.mean(C)),
        "C_max": float(_np.max(C)),
        "delta_phi_mean": float(_np.mean(dphi)),
        "delta_phi_max": float(_np.max(dphi)),
        "H7_target": 0.70,
    }

    # Node role assignment (root → mirror → flow-style)
    # Simple mapping across 7 nodes:
    # 0: root (Oz), 1: flow, 2: mirror, 3: coherence, 4: mirror, 5: flow, 6: crown (Gomer)
    roles = [
        {"index": 0, "label": "root", "channel": "E"},
        {"index": 1, "label": "flow", "channel": "E"},
        {"index": 2, "label": "mirror", "channel": "I"},
        {"index": 3, "label": "heart", "channel": "C"},
        {"index": 4, "label": "voice", "channel": "I"},
        {"index": 5, "label": "vision", "channel": "C"},
        {"index": 6, "label": "crown", "channel": "C"},
    ]

    summary = {
        "module": "codex_bio_resonance",
        "version": version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "triad": data,
        "metrics": metrics,
        "law": "C = (E·I)/(1+|ΔΦ|)",
        "mapping": {
            "Gomer": "Beauty / Coherence / C",
            "Dabar": "Wisdom / Information / I",
            "Oz": "Strength / Energy / E",
        },
        "node_roles": roles,
        "physiology": physio,
        "notes": {
            "ida_pingala_model": "dual-channel oscillators with physio modulation",
            "sushumna": "coherence channel / central mesh",
            "lotus_torus": "lotus + torus resonance fields",
        },
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex Bio-Resonance v1.1 — Living Resonance Engine"
    )
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--visual-dir", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--input-dir", required=False, default=None)
    args = parser.parse_args()

    os.makedirs(args.state_dir, exist_ok=True)
    os.makedirs(args.visual_dir, exist_ok=True)

    physio = None
    physio_path = None
    if args.input_dir is not None:
        physio_path = os.path.join(args.input_dir, "physiology.json")
        physio = load_physio(physio_path)

    num_nodes = 7
    data = compute_triads(num_nodes=num_nodes, t=0.0, physio=physio)

    state_path = os.path.join(args.state_dir, "bio_resonance_state_v1_1.json")
    profile_png = os.path.join(args.visual_dir, "bio_resonance_spine_profile_v1_1.png")
    heatmap_png = os.path.join(args.visual_dir, "bio_resonance_delta_phi_heatmap_v1_1.png")
    wavefield_png = os.path.join(args.visual_dir, "bio_resonance_coherence_wavefield_v1_1.png")
    lotus_png = os.path.join(args.visual_dir, "bio_resonance_lotus_field_v1_1.png")
    torus_png = os.path.join(args.visual_dir, "bio_resonance_torus_field_v1_1.png")

    state_obj = write_state_json(data, state_path, args.version, physio)
    make_spine_profile_plot(data, profile_png)
    make_delta_phi_heatmap(
        num_nodes=num_nodes, steps=72, out_path=heatmap_png, physio=physio
    )
    make_coherence_wavefield(
        num_nodes=num_nodes, steps=72, out_path=wavefield_png, physio=physio
    )
    make_lotus_plot(data, lotus_png)
    make_torus_plot(data, torus_png, physio=physio)

    print(f"[Bio-Resonance v1.1] Wrote state to {state_path}")
    print(f"[Bio-Resonance v1.1] Wrote spine profile to {profile_png}")
    print(f"[Bio-Resonance v1.1] Wrote ΔΦ heatmap to {heatmap_png}")
    print(f"[Bio-Resonance v1.1] Wrote coherence wavefield to {wavefield_png}")
    print(f"[Bio-Resonance v1.1] Wrote lotus field to {lotus_png}")
    print(f"[Bio-Resonance v1.1] Wrote torus field to {torus_png}")


if __name__ == "__main__":
    main()
