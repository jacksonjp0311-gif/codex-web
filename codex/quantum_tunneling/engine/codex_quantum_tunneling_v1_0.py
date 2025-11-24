"""
𓂀  Quantum Tunneling v1.0 — 1D ΔΦ Lattice
"""

import os, json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt


def tunneling_probability(V0: float, E: float) -> float:
    if E >= V0:
        return 1.0
    kappa = np.sqrt(max(V0 - E, 0.0))
    return float(np.exp(-2.0 * kappa))


def generate_lattice(N: int = 201, barrier_center: int = 100, barrier_height: float = 1.5):
    lattice = np.zeros(N, dtype=float)
    lattice[barrier_center] = barrier_height
    return lattice


def run_tunneling_engine(output_root: str = ".", seed: int = 123):
    np.random.seed(seed)
    lattice = generate_lattice()
    V0 = float(lattice.max())

    energies = np.linspace(0.01, 2.0, 300)
    probs = np.array([tunneling_probability(V0, float(E)) for E in energies])

    grad = np.gradient(probs, energies)
    delta_phi = float(np.mean(np.abs(grad)))

    E_mean = float(energies.mean())
    I_var = float(np.var(probs))
    C_val = (E_mean * I_var) / (1.0 + abs(delta_phi))
    H7 = 0.70

    state = {
        "module": "Codex Quantum Tunneling v1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "barrier": {
            "height": V0,
            "center_index": 100,
            "lattice_length": int(lattice.size),
        },
        "triad": {
            "E": E_mean,
            "I": I_var,
            "C": C_val,
            "H7": H7,
            "placidity": "∿",
            "delta_phi": delta_phi,
        },
        "notes": {
            "description": "1D tunneling through a single barrier; ΔΦ from T(E) gradient.",
        },
    }

    state_path = os.path.join(output_root, "state", "v1_0", "tunneling_state_v1_0.json")
    curve_path = os.path.join(output_root, "visuals", "v1_0", "tunneling_probability_curve_v1_0.png")

    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    os.makedirs(os.path.dirname(curve_path), exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

    plt.figure()
    plt.plot(energies, probs)
    plt.xlabel("Energy")
    plt.ylabel("T(E)")
    plt.title("Codex Quantum Tunneling v1.0 — T(E)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(curve_path)
    plt.close()

    return state_path, curve_path


if __name__ == "__main__":
    run_tunneling_engine(".")
