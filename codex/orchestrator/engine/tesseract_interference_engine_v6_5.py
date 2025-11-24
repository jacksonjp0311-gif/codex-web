# CODEX TESSERACT INTERFERENCE ENGINE v6.5 (mini)
#   • Synthetic interference field (1D)
#   • Emits triad + ΔΦ state for All-One v6.5

import os
import json
import math
from datetime import datetime

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    orch_root  = os.path.dirname(engine_dir)
    state_dir  = os.path.join(orch_root, "state")
    os.makedirs(state_dir, exist_ok=True)

    t = datetime.utcnow().isoformat() + "Z"

    # simple synthetic interference band
    n = 64
    field = []
    for i in range(n):
        x = i / float(n - 1)
        val = math.sin(2.0 * math.pi * x) * math.cos(4.0 * math.pi * x)
        field.append(val)

    phi_min = min(field)
    phi_max = max(field)
    phi_mean = sum(field) / len(field)
    delta_phi = phi_max - phi_min

    # interference triad (local field sample)
    E = 1.0
    I = 1.0
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
        "module": "Codex Tesseract Interference Engine v6.5 (mini)",
        "version": "6.5-mini",
        "timestamp": t,
        "triad": triad,
        "phi_min": phi_min,
        "phi_max": phi_max,
        "phi_mean": phi_mean,
        "samples": n
    }

    out_path = os.path.join(state_dir, "tesseract_interference_state_v6_5.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # ascii-safe print (no unicode arrows)
    print("[Tesseract v6.5 mini] State written:", out_path)

if __name__ == "__main__":
    main()
