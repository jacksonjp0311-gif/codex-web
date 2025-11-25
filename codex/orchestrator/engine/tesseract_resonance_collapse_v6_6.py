# CODEX TESSERACT RESONANCE COLLAPSE ENGINE v6.6 (mini)
#   • Reads light (v6.3), shadow (v6.4), interference (v6.5) Δφ
#   • Computes collapse Δφ as mean of magnitudes
#   • Applies C = (E*I) / (1 + |Δφ_collapse|) with E=1, I=1
#   • Emits collapse_state_v6_6.json
#   • Emits collapse spectrum PNG (if matplotlib available)

import os
import json
import math
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def classify_phase(C, H7=0.70):
    if C >= 0.90:
        return "super-H7"
    if C >= H7:
        return "H7-band"
    return "sub-H7"

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    orch_root  = os.path.dirname(engine_dir)
    state_dir  = os.path.join(orch_root, "state")
    visuals_dir = os.path.join(orch_root, "visuals", "v6_6")

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)

    t = datetime.utcnow().isoformat() + "Z"

    state63_path = os.path.join(state_dir, "tesseract_all_one_state_v6_3.json")
    state64_path = os.path.join(state_dir, "tesseract_all_one_state_v6_4.json")
    interf_path  = os.path.join(state_dir, "tesseract_interference_state_v6_5.json")

    state63 = load_json(state63_path)
    state64 = load_json(state64_path)
    interf  = load_json(interf_path)

    triad_light  = state63.get("triad", {})
    triad_shadow = state64.get("triad", {})
    triad_interf = interf.get("triad", {})

    dphi_light  = float(triad_light.get("delta_phi", 0.0))
    dphi_shadow = float(triad_shadow.get("delta_phi", 0.0))
    dphi_interf = float(triad_interf.get("delta_phi", 0.0))

    # collapse Δφ: mean of magnitudes (light, shadow, interference)
    phi_vals = [abs(dphi_light), abs(dphi_shadow), abs(dphi_interf)]
    phi_collapse = sum(phi_vals) / float(len(phi_vals))

    E = 1.0
    I = 1.0
    C = (E * I) / (1.0 + abs(phi_collapse))

    H7 = 0.70
    phase = classify_phase(C, H7=H7)

    triad = {
        "E": E,
        "I": I,
        "C": C,
        "H7": H7,
        "placidity": "∿",
        "delta_phi": phi_collapse,
        "phase": phase
    }

    collapse_png = os.path.join(visuals_dir, "tesseract_collapse_spectrum_v6_6.png")

    # simple Δφ spectrum figure if matplotlib is available
    if HAVE_MPL:
        labels = ["light", "shadow", "interference", "collapse"]
        values = [abs(dphi_light), abs(dphi_shadow), abs(dphi_interf), phi_collapse]

        plt.figure()
        plt.bar(range(len(labels)), values)
        plt.xticks(range(len(labels)), labels)
        plt.ylabel("abs(delta_phi)")
        plt.title("Tesseract v6.6 collapse spectrum")
        plt.tight_layout()
        plt.savefig(collapse_png)
        plt.close()
        figure_note = collapse_png
    else:
        figure_note = None

    state = {
        "module": "Codex Tesseract Resonance Collapse Engine v6.6 (mini)",
        "version": "6.6-mini",
        "timestamp": t,
        "triad": triad,
        "delta_phi_light": dphi_light,
        "delta_phi_shadow": dphi_shadow,
        "delta_phi_interference": dphi_interf,
        "delta_phi_collapse": phi_collapse,
        "visuals": {
            "collapse_spectrum_png": figure_note
        }
    }

    out_path = os.path.join(state_dir, "tesseract_collapse_state_v6_6.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("[Tesseract v6.6 mini] Collapse state written:", out_path)
    if figure_note:
        print("[Tesseract v6.6 mini] Collapse figure written:", figure_note)
    else:
        print("[Tesseract v6.6 mini] Matplotlib not available; no figure written")

if __name__ == "__main__":
    main()
