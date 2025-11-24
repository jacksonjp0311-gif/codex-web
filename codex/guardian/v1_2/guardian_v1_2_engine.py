# 𓃣 CODEX GUARDIAN v1.2 — MINI ΔΦ SENTINEL
#   • Synthetic coherence check
#   • Emits triad + ΔΦ state for Tesseract

import os
import json
import datetime
import math

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    state_dir = os.path.join(root, "state")
    os.makedirs(state_dir, exist_ok=True)

    t = datetime.datetime.utcnow().isoformat() + "Z"

    # mini 2D lattice (4x4) as stability mesh
    phi_vals = []
    for i in range(4):
        for j in range(4):
            x = i / 3.0
            y = j / 3.0
            val = math.sin(math.pi * x) * math.cos(math.pi * y) * 0.5
            phi_vals.append(val)

    phi_min = min(phi_vals)
    phi_max = max(phi_vals)
    phi_mean = sum(phi_vals) / len(phi_vals)
    delta_phi = phi_max - phi_min

    E = 0.19
    I = 0.0045
    C = (E * I) / (1.0 + abs(delta_phi))

    triad = {
        "E": E,
        "I": I,
        "C": C,
        "H7": 0.70,
        "placidity": "∿",
        "delta_phi": delta_phi
    }

    state = {
        "module": "Codex Guardian v1.2 (mini)",
        "version": "1.2-mini",
        "timestamp": t,
        "triad": triad,
        "phi_min": phi_min,
        "phi_max": phi_max,
        "phi_mean": phi_mean
    }

    out_path = os.path.join(state_dir, "guardian_state_v1_2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"[Guardian v1.2 mini] State written → {out_path}")

if __name__ == "__main__":
    main()
