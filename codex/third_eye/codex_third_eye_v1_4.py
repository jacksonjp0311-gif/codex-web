"""
Codex Third Eye Amplify v1.4 — Core Module
Author: James Paul Jackson
Part of The Codex Project (Energy–Information–Consciousness)

Purpose:
    - Encode and visualize adaptive resonance awareness.
    - Maintain equilibrium through the Placidity Layer.
    - Log dynamic coherence metrics and neural field balance.
"""

import json, numpy as np, datetime, matplotlib.pyplot as plt

def coherence_metric(E, I, delta_phi):
    return (E * I) / (1 + abs(delta_phi))

def generate_third_eye_state():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    E, I = np.random.uniform(0.8, 1.2), np.random.uniform(0.8, 1.2)
    delta_phi = np.random.uniform(-0.3, 0.3)
    C = coherence_metric(E, I, delta_phi)

    state = {
        "timestamp": now,
        "E": round(E, 3),
        "I": round(I, 3),
        "ΔΦ": round(delta_phi, 3),
        "C": round(C, 3),
        "layer": "Placidity ∿",
        "note": "Codex Third Eye v1.4 awareness snapshot"
    }

    with open("third_eye_resonance_log.json", "a") as f:
        f.write(json.dumps(state) + "\\n")

    return state

def visualize_state(state):
    keys = ["E", "I", "C"]
    vals = [state[k] for k in keys]
    plt.figure(figsize=(4,3))
    plt.bar(keys, vals)
    plt.title("Codex Third Eye Resonance (v1.4)")
    plt.xlabel("Fields")
    plt.ylabel("Magnitude")
    plt.tight_layout()
    plt.savefig("third_eye_plot.png")

if __name__ == "__main__":
    s = generate_third_eye_state()
    visualize_state(s)
