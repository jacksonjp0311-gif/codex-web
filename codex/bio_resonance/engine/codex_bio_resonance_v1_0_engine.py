import argparse
import json
import math
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt


def compute_triads(num_nodes: int = 7, t: float = 0.0) -> dict:
    """
    Synthetic Codex Bio-Resonance model:

    - Spine as N-node lattice (chakras / vertebrae)
    - Two oscillators (Ida / Pingala) as phase-shifted fields along node index
    - Sushumna as coherence mesh (average envelope)
    - ΔΦ = |Ida - Pingala|
    - C = (E * I) / (1 + |ΔΦ|)

    Mapping:
      Oz   → Strength → Energy (E)
      Dabar→ Wisdom   → Information (I)
      Gomer→ Beauty   → Coherence (C)
    """
    z = np.linspace(0.0, 1.0, num_nodes)

    # Ida / Pingala modeled as shifted sinusoids along the spine
    # Energy: Oz / Strength / Pingala-like
    energy = 0.6 + 0.4 * np.sin(2.0 * math.pi * z + 1.5 * t)

    # Information: Dabar / Wisdom / Sushumna-like envelope
    information = 0.6 + 0.4 * np.cos(2.0 * math.pi * z + 0.5 * t)

    delta_phi = np.abs(energy - information)

    # Consciousness / Coherence index
    C = (energy * information) / (1.0 + delta_phi)

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
    plt.title("Codex Bio-Resonance v1.0 — Spine Triad Profile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_delta_phi_heatmap(num_nodes: int, steps: int, out_path: str) -> None:
    """
    Create a QIM/Solar-style ΔΦ heatmap:
    - x-axis: time steps (synthetic evolution)
    - y-axis: nodes along spine
    - color: ΔΦ at each node/time
    """
    heat = np.zeros((num_nodes, steps))
    z = np.linspace(0.0, 1.0, num_nodes)

    for ti in range(steps):
        t = float(ti) / float(max(1, steps - 1)) * 2.0 * math.pi
        sample = compute_triads(num_nodes=num_nodes, t=t)
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
    plt.title("Codex Bio-Resonance v1.0 — ΔΦ Spine Heatmap")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def make_lotus_torus_placeholder(data: dict, out_path: str) -> None:
    """
    Simple lotus/torus placeholder:
    - radial profile of coherence C mapped around a circle
    This is a hook for future full lotus/torus field engines.
    """
    C = np.array(data["C"])
    num_nodes = C.shape[0]
    theta = np.linspace(0.0, 2.0 * math.pi, num_nodes + 1)
    C_closed = np.concatenate([C, C[:1]])

    x = (1.0 + 0.3 * C_closed) * np.cos(theta)
    y = (1.0 + 0.3 * C_closed) * np.sin(theta)

    plt.figure(figsize=(5, 5))
    plt.plot(x, y)
    plt.scatter(x, y, s=20)
    plt.axis("equal")
    plt.axis("off")
    plt.title("Codex Bio-Resonance v1.0 — Lotus/Torus Placeholder")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def write_state_json(data: dict, out_path: str, version: str) -> None:
    import numpy as _np

    summary = {
        "module": "codex_bio_resonance",
        "version": version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "triad": data,
        "metrics": {
            "C_mean": float(_np.mean(data["C"])),
            "C_max": float(_np.max(data["C"])),
            "delta_phi_mean": float(_np.mean(data["delta_phi"])),
            "delta_phi_max": float(_np.max(data["delta_phi"])),
            "H7_target": 0.70,
        },
        "law": "C = (E·I)/(1+|ΔΦ|)",
        "mapping": {
            "Gomer": "Beauty / Coherence / C",
            "Dabar": "Wisdom / Information / I",
            "Oz": "Strength / Energy / E",
        },
        "notes": {
            "ida_pingala_model": "dual-channel oscillators",
            "sushumna": "coherence channel / central mesh",
            "lotus_torus": "placeholder radial mapping of C"
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codex Bio-Resonance v1.0 — Spine Coherence Engine"
    )
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--visual-dir", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    os.makedirs(args.state_dir, exist_ok=True)
    os.makedirs(args.visual_dir, exist_ok=True)

    # Base triad snapshot
    num_nodes = 7
    data = compute_triads(num_nodes=num_nodes, t=0.0)

    state_path = os.path.join(args.state_dir, "bio_resonance_state.json")
    profile_png = os.path.join(args.visual_dir, "bio_resonance_spine_profile.png")
    heatmap_png = os.path.join(args.visual_dir, "bio_resonance_delta_phi_heatmap.png")
    lotus_png = os.path.join(args.visual_dir, "bio_resonance_lotus_torus_placeholder.png")

    write_state_json(data, state_path, args.version)
    make_spine_profile_plot(data, profile_png)
    make_delta_phi_heatmap(num_nodes=num_nodes, steps=72, out_path=heatmap_png)
    make_lotus_torus_placeholder(data, lotus_png)

    print(f"[Bio-Resonance] Wrote state to {state_path}")
    print(f"[Bio-Resonance] Wrote spine profile to {profile_png}")
    print(f"[Bio-Resonance] Wrote ΔΦ heatmap to {heatmap_png}")
    print(f"[Bio-Resonance] Wrote lotus/torus placeholder to {lotus_png}")


if __name__ == "__main__":
    main()
