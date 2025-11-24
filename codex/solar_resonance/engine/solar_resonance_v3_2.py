# 𓇯 CODEX SOLAR RESONANCE v3.2 — MINI ENGINE
#   • Synthetic horizon-like ΔΦ field
#   • Emits triad + ΔΦ state for Tesseract

import os
import json
import datetime
import math

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    solar_root = os.path.dirname(engine_dir)
    state_dir = os.path.join(solar_root, "state", "v3_2")
    os.makedirs(state_dir, exist_ok=True)

    t = datetime.datetime.utcnow().isoformat() + "Z"

    # small synthetic solar strip (1D horizon)
    n = 24
    phi_vals = []
    for i in range(n):
        x = i / float(n - 1)
        val = math.sin(2.0 * math.pi * x) * math.cos(3.0 * math.pi * x)
        phi_vals.append(val)

    phi_min = min(phi_vals)
    phi_max = max(phi_vals)
    phi_mean = sum(phi_vals) / len(phi_vals)
    delta_phi = phi_max - phi_min

    E = 0.21
    I = 0.005
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
        "module": "Codex Solar Resonance v3.2 (mini)",
        "version": "3.2-mini",
        "timestamp": t,
        "triad": triad,
        "phi_min": phi_min,
        "phi_max": phi_max,
        "phi_mean": phi_mean,
        "horizon_samples": n
    }

    out_path = os.path.join(state_dir, "solar_resonance_state_v3_2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"[Solar v3.2 mini] State written → {out_path}")

if __name__ == "__main__":
    main()
