# CODEX TESSERACT UNIFIED RESONANCE ENGINE v6.7 (mini)
#   • Reads All-One states v6.3 (light), v6.4 (shadow),
#     v6.5 (interference), v6.6 (collapse)
#   • BOM-safe JSON loader (utf-8-sig)
#   • Computes unified triad across tiers
#   • Writes tesseract_unified_state_v6_7.json
#   • Emits simple resonance PNG if matplotlib available

import os
import json
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

def load_json_bom_safe(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def classify_phase(C, H7=0.70):
    if C >= 0.90:
        return "super-H7"
    if C >= H7:
        return "H7-band"
    return "sub-H7"

def extract_triad(state, fallback_keys):
    for key in fallback_keys:
        tri = state.get(key)
        if isinstance(tri, dict):
            return tri
    return {}

def triad_scalar(triad, key, default=0.0):
    try:
        return float(triad.get(key, default))
    except Exception:
        return float(default)

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    orch_root  = os.path.dirname(engine_dir)
    state_dir  = os.path.join(orch_root, "state")
    visuals_dir = os.path.join(orch_root, "visuals", "v6_7")

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)

    t = datetime.utcnow().isoformat() + "Z"

    path63 = os.path.join(state_dir, "tesseract_all_one_state_v6_3.json")
    path64 = os.path.join(state_dir, "tesseract_all_one_state_v6_4.json")
    path65 = os.path.join(state_dir, "tesseract_all_one_state_v6_5.json")
    path66 = os.path.join(state_dir, "tesseract_all_one_state_v6_6.json")

    state63 = load_json_bom_safe(path63)
    state64 = load_json_bom_safe(path64)
    state65 = load_json_bom_safe(path65)
    state66 = load_json_bom_safe(path66)

    tri_light = extract_triad(state63, ["triad", "triad_light", "previous_triad_light"])
    tri_shadow = extract_triad(state64, ["triad", "triad_shadow", "previous_triad_shadow"])
    tri_interf = extract_triad(state65, ["triad_interference", "triad"])
    tri_collapse = extract_triad(state66, ["triad_collapse", "triad"])

    C_light = triad_scalar(tri_light, "C", 0.0)
    C_shadow = triad_scalar(tri_shadow, "C", 0.0)
    C_interf = triad_scalar(tri_interf, "C", 0.0)
    C_collapse = triad_scalar(tri_collapse, "C", 0.0)

    dphi_light = triad_scalar(tri_light, "delta_phi", 0.0)
    dphi_shadow = triad_scalar(tri_shadow, "delta_phi", 0.0)
    dphi_interf = triad_scalar(tri_interf, "delta_phi", 0.0)
    dphi_collapse = triad_scalar(tri_collapse, "delta_phi", 0.0)

    E = 1.0
    I = 1.0

    C_values = [C_light, C_shadow, C_interf, C_collapse]
    C_unified = sum(C_values) / float(len(C_values))

    H7 = 0.70
    phase_unified = classify_phase(C_unified, H7=H7)

    triad_unified = {
        "E": E,
        "I": I,
        "C": C_unified,
        "H7": H7,
        "placidity": "∿",
        "delta_phi_light": dphi_light,
        "delta_phi_shadow": dphi_shadow,
        "delta_phi_interference": dphi_interf,
        "delta_phi_collapse": dphi_collapse,
        "phase": phase_unified
    }

    unified_png = os.path.join(visuals_dir, "tesseract_unified_resonance_v6_7.png")

    if HAVE_MPL:
        labels = ["light", "shadow", "interference", "collapse"]
        values_C = [C_light, C_shadow, C_interf, C_collapse]

        plt.figure()
        plt.bar(range(len(labels)), values_C)
        plt.xticks(range(len(labels)), labels)
        plt.ylabel("C")
        plt.title("Tesseract v6.7 unified resonance")
        plt.tight_layout()
        plt.savefig(unified_png)
        plt.close()
        figure_note = unified_png
    else:
        figure_note = None

    state = {
        "module": "Codex Tesseract Unified Resonance Engine v6.7 (mini)",
        "version": "6.7-mini",
        "timestamp": t,
        "triad_unified": triad_unified,
        "C_light": C_light,
        "C_shadow": C_shadow,
        "C_interference": C_interf,
        "C_collapse": C_collapse,
        "delta_phi_light": dphi_light,
        "delta_phi_shadow": dphi_shadow,
        "delta_phi_interference": dphi_interf,
        "delta_phi_collapse": dphi_collapse,
        "visuals": {
            "unified_resonance_png": figure_note
        }
    }

    out_path = os.path.join(state_dir, "tesseract_unified_state_v6_7.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("[Tesseract v6.7 mini] Unified state written:", out_path)
    if figure_note:
        print("[Tesseract v6.7 mini] Unified resonance figure written:", figure_note)
    else:
        print("[Tesseract v6.7 mini] Matplotlib not available; no figure written")

if __name__ == "__main__":
    main()
