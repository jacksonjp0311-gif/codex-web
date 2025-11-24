# 𓏤 CODEX CGL v1.1 — AUTO-GLYPH MINI ENGINE
#   • Ensures glyph table presence
#   • Emits minimal triad + ΔΦ state for Tesseract

import os
import json
import datetime
import math

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    codex_cgl_root = os.path.dirname(engine_dir)
    state_dir = os.path.join(codex_cgl_root, "state", "v1_1")
    os.makedirs(state_dir, exist_ok=True)

    t = datetime.datetime.utcnow().isoformat() + "Z"

    # tiny synthetic ΔΦ based on simple phase sweep
    phases = [i * 0.23 for i in range(8)]
    phi_vals = [math.sin(p) * math.cos(0.5 * p) for p in phases]
    delta_phi = max(phi_vals) - min(phi_vals)

    E = 0.18
    I = 0.004
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
        "module": "Codex CGL v1.1 (mini)",
        "version": "1.1-mini",
        "timestamp": t,
        "triad": triad,
        "phi_min": min(phi_vals),
        "phi_max": max(phi_vals),
        "phi_mean": sum(phi_vals) / len(phi_vals)
    }

    out_path = os.path.join(state_dir, "cgl_state_v1_1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"[CGL v1.1 mini] State written → {out_path}")

if __name__ == "__main__":
    main()
