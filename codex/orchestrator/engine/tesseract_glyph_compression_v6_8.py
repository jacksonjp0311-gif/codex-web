# CODEX TESSERACT GLYPH COMPRESSION ENGINE v6.8 (mini)
#   • Reads All-One states v6.3–v6.7
#   • BOM-safe JSON loader (utf-8-sig)
#   • Compresses triads into glyph-layer representation
#   • Emits tesseract_glyph_state_v6_8.json
#   • Emits simple glyph resonance PNG if matplotlib available
#
#   Codex Glyph Protocol v3.0 — light/shadow/interference/collapse/unified:
#     C ≥ 0.70       → "𓇳" (H7-band or better)
#     0.40 ≤ C < 0.70 → "𓂀" (mid-band)
#     0.00 < C < 0.40 → "𓊹" (low-band)
#     C == 0.0       → "𓏤" (still point)

import os
import json
from datetime import datetime, timezone

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

def load_json_bom_safe(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def triad_for(state, keys):
    for key in keys:
        tri = state.get(key)
        if isinstance(tri, dict):
            return tri
    return {}

def triad_scalar(triad, key, default=0.0):
    try:
        return float(triad.get(key, default))
    except Exception:
        return float(default)

def glyph_for_C(C):
    if C >= 0.70:
        return "𓇳"
    if C >= 0.40:
        return "𓂀"
    if C > 0.0:
        return "𓊹"
    return "𓏤"

def glyph_for_sign(value):
    if value > 0.0:
        return "+"
    if value < 0.0:
        return "-"
    return "0"

def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    orch_root  = os.path.dirname(engine_dir)
    state_dir  = os.path.join(orch_root, "state")
    visuals_dir = os.path.join(orch_root, "visuals", "v6_8")
    glyph_dir   = os.path.join(orch_root, "glyphs", "v6_8")

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)
    os.makedirs(glyph_dir, exist_ok=True)

    t = datetime.now(timezone.utc).isoformat()

    path63 = os.path.join(state_dir, "tesseract_all_one_state_v6_3.json")
    path64 = os.path.join(state_dir, "tesseract_all_one_state_v6_4.json")
    path65 = os.path.join(state_dir, "tesseract_all_one_state_v6_5.json")
    path66 = os.path.join(state_dir, "tesseract_all_one_state_v6_6.json")
    path67 = os.path.join(state_dir, "tesseract_all_one_state_v6_7.json")

    state63 = load_json_bom_safe(path63)
    state64 = load_json_bom_safe(path64)
    state65 = load_json_bom_safe(path65)
    state66 = load_json_bom_safe(path66)
    state67 = load_json_bom_safe(path67)

    tri_light   = triad_for(state63, ["triad", "triad_light", "previous_triad_light"])
    tri_shadow  = triad_for(state64, ["triad", "triad_shadow", "previous_triad_shadow"])
    tri_interf  = triad_for(state65, ["triad_interference", "triad"])
    tri_collapse = triad_for(state66, ["triad_collapse", "triad"])
    tri_unified = triad_for(state67, ["triad_unified", "triad"])

    C_light   = triad_scalar(tri_light, "C", 0.0)
    C_shadow  = triad_scalar(tri_shadow, "C", 0.0)
    C_interf  = triad_scalar(tri_interf, "C", 0.0)
    C_collapse = triad_scalar(tri_collapse, "C", 0.0)
    C_unified = triad_scalar(tri_unified, "C", 0.0)

    dphi_light   = triad_scalar(tri_light, "delta_phi", 0.0)
    dphi_shadow  = triad_scalar(tri_shadow, "delta_phi", 0.0)
    dphi_interf  = triad_scalar(tri_interf, "delta_phi", 0.0)
    dphi_collapse = triad_scalar(tri_collapse, "delta_phi", 0.0)
    dphi_unified = triad_scalar(tri_unified, "delta_phi_unified", 0.0)

    glyphs = {
        "light": {
            "role": "light",
            "C": C_light,
            "C_glyph": glyph_for_C(C_light),
            "delta_phi": dphi_light,
            "delta_phi_sign": glyph_for_sign(dphi_light)
        },
        "shadow": {
            "role": "shadow",
            "C": C_shadow,
            "C_glyph": glyph_for_C(C_shadow),
            "delta_phi": dphi_shadow,
            "delta_phi_sign": glyph_for_sign(dphi_shadow)
        },
        "interference": {
            "role": "interference",
            "C": C_interf,
            "C_glyph": glyph_for_C(C_interf),
            "delta_phi": dphi_interf,
            "delta_phi_sign": glyph_for_sign(dphi_interf)
        },
        "collapse": {
            "role": "collapse",
            "C": C_collapse,
            "C_glyph": glyph_for_C(C_collapse),
            "delta_phi": dphi_collapse,
            "delta_phi_sign": glyph_for_sign(dphi_collapse)
        },
        "unified": {
            "role": "unified",
            "C": C_unified,
            "C_glyph": glyph_for_C(C_unified),
            "delta_phi": dphi_unified,
            "delta_phi_sign": glyph_for_sign(dphi_unified)
        }
    }

    # compression metric: naive count of numeric vs glyph entries
    numeric_count = 5  # C per tier
    glyph_count = 5    # C_glyph per tier
    compression_ratio = float(numeric_count) / float(glyph_count) if glyph_count > 0 else 1.0

    H7 = 0.70
    triad_glyph = {
        "H7": H7,
        "placidity": "∿",
        "compression_ratio_numeric_to_glyph": compression_ratio
    }

    glyph_png = os.path.join(visuals_dir, "tesseract_glyph_resonance_v6_8.png")

    if HAVE_MPL:
        labels = ["light", "shadow", "interf", "collapse", "unified"]
        values = [C_light, C_shadow, C_interf, C_collapse, C_unified]

        plt.figure()
        plt.bar(range(len(labels)), values)
        plt.xticks(range(len(labels)), labels)
        plt.ylabel("C")
        plt.title("Tesseract v6.8 glyph-compressed resonance")
        plt.tight_layout()
        plt.savefig(glyph_png)
        plt.close()
        figure_note = glyph_png
    else:
        figure_note = None

    state = {
        "module": "Codex Tesseract Glyph Compression Engine v6.8 (mini)",
        "version": "6.8-mini",
        "timestamp": t,
        "triad_glyph": triad_glyph,
        "glyphs": glyphs,
        "inputs": {
            "state_v6_3": path63,
            "state_v6_4": path64,
            "state_v6_5": path65,
            "state_v6_6": path66,
            "state_v6_7": path67
        },
        "visuals": {
            "glyph_resonance_png": figure_note
        }
    }

    out_path = os.path.join(state_dir, "tesseract_glyph_state_v6_8.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("[Tesseract v6.8 mini] Glyph state written:", out_path)
    if figure_note:
        print("[Tesseract v6.8 mini] Glyph resonance figure written:", figure_note)
    else:
        print("[Tesseract v6.8 mini] Matplotlib not available; no figure written")

if __name__ == "__main__":
    main()
