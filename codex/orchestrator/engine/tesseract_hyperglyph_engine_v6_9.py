# CODEX TESSERACT HYPERGLYPH ENGINE v6.9 (mini)
#   • Reads All-One states v6.3–v6.8 plus glyph tier v6.8
#   • BOM-safe JSON loader (utf-8-sig)
#   • Folds light/shadow + interference/collapse + unified/light
#   • Computes HyperGlyph triad with effective C over pairs
#   • Emits tesseract_hyperglyph_state_v6_9.json
#   • Emits simple HyperGlyph resonance PNG if matplotlib available
#
#   Pair schema:
#     pair_ls  = (light, shadow)
#     pair_ic  = (interference, collapse)
#     pair_ul  = (unified, light)
#
#   Each pair tracks:
#     • C_avg
#     • delta_phi_diff
#     • sign_pattern (e.g. "+-" or "0+")
#     • hyperglyph tag = sign_pattern

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


def main():
    engine_dir  = os.path.dirname(os.path.abspath(__file__))
    orch_root   = os.path.dirname(engine_dir)
    state_dir   = os.path.join(orch_root, "state")
    visuals_dir = os.path.join(orch_root, "visuals", "v6_9")
    glyph_dir   = os.path.join(orch_root, "glyphs", "v6_9")

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)
    os.makedirs(glyph_dir, exist_ok=True)

    t = datetime.now(timezone.utc).isoformat()

    path63 = os.path.join(state_dir, "tesseract_all_one_state_v6_3.json")
    path64 = os.path.join(state_dir, "tesseract_all_one_state_v6_4.json")
    path65 = os.path.join(state_dir, "tesseract_all_one_state_v6_5.json")
    path66 = os.path.join(state_dir, "tesseract_all_one_state_v6_6.json")
    path67 = os.path.join(state_dir, "tesseract_all_one_state_v6_7.json")
    path68 = os.path.join(state_dir, "tesseract_all_one_state_v6_8.json")
    glyph68 = os.path.join(state_dir, "tesseract_glyph_state_v6_8.json")

    state63 = load_json_bom_safe(path63)
    state64 = load_json_bom_safe(path64)
    state65 = load_json_bom_safe(path65)
    state66 = load_json_bom_safe(path66)
    state67 = load_json_bom_safe(path67)
    state68 = load_json_bom_safe(path68)
    g68     = load_json_bom_safe(glyph68)

    tri_light    = triad_for(state63, ["triad", "triad_light", "previous_triad_light"])
    tri_shadow   = triad_for(state64, ["triad", "triad_shadow", "previous_triad_shadow"])
    tri_interf   = triad_for(state65, ["triad_interference", "triad"])
    tri_collapse = triad_for(state66, ["triad_collapse", "triad"])
    tri_unified  = triad_for(state67, ["triad_unified", "triad"])

    C_light    = triad_scalar(tri_light, "C", 0.0)
    C_shadow   = triad_scalar(tri_shadow, "C", 0.0)
    C_interf   = triad_scalar(tri_interf, "C", 0.0)
    C_collapse = triad_scalar(tri_collapse, "C", 0.0)
    C_unified  = triad_scalar(tri_unified, "C", 0.0)

    dphi_light    = triad_scalar(tri_light, "delta_phi", 0.0)
    dphi_shadow   = triad_scalar(tri_shadow, "delta_phi", 0.0)
    dphi_interf   = triad_scalar(tri_interf, "delta_phi", 0.0)
    dphi_collapse = triad_scalar(tri_collapse, "delta_phi", 0.0)
    dphi_unified  = triad_scalar(tri_unified, "delta_phi_unified", 0.0)

    glyphs = g68.get("glyphs", {})

    def get_role(role):
        return glyphs.get(role, {})

    g_light  = get_role("light")
    g_shadow = get_role("shadow")
    g_interf = get_role("interference")
    g_coll   = get_role("collapse")
    g_unif   = get_role("unified")

    def pair_metrics(name, a_role, b_role, C_a, C_b, dphi_a, dphi_b):
        C_avg = 0.5 * (C_a + C_b)
        dphi_diff = dphi_b - dphi_a
        ga = glyphs.get(a_role, {})
        gb = glyphs.get(b_role, {})
        sa = ga.get("delta_phi_sign", "0")
        sb = gb.get("delta_phi_sign", "0")
        sign_pattern = sa + sb
        hyperglyph = sign_pattern
        return {
            "name": name,
            "roles": [a_role, b_role],
            "C_avg": C_avg,
            "delta_phi_diff": dphi_diff,
            "sign_pattern": sign_pattern,
            "hyperglyph": hyperglyph
        }

    pair_ls = pair_metrics("ls", "light", "shadow",
                           C_light, C_shadow,
                           dphi_light, dphi_shadow)

    pair_ic = pair_metrics("ic", "interference", "collapse",
                           C_interf, C_collapse,
                           dphi_interf, dphi_collapse)

    pair_ul = pair_metrics("ul", "unified", "light",
                           C_unified, C_light,
                           dphi_unified, dphi_light)

    pairs = [pair_ls, pair_ic, pair_ul]

    if pairs:
        C_effective = sum(p["C_avg"] for p in pairs) / float(len(pairs))
    else:
        C_effective = 0.0

    H7 = 0.70
    triad_hyper = {
        "H7": H7,
        "placidity": "∿",
        "C_effective": C_effective,
        "pair_count": len(pairs)
    }

    hyper_png = os.path.join(visuals_dir, "tesseract_hyperglyph_resonance_v6_9.png")

    if HAVE_MPL:
        labels = [p["name"] for p in pairs]
        values = [p["C_avg"] for p in pairs]

        plt.figure()
        plt.bar(range(len(labels)), values)
        plt.xticks(range(len(labels)), labels)
        plt.ylabel("C_avg")
        plt.title("Tesseract v6.9 hyperglyph pair resonance")
        plt.tight_layout()
        plt.savefig(hyper_png)
        plt.close()
        figure_note = hyper_png
    else:
        figure_note = None

    state = {
        "module": "Codex Tesseract HyperGlyph Engine v6.9 (mini)",
        "version": "6.9-mini",
        "timestamp": t,
        "triad_hyperglyph": triad_hyper,
        "pairs": pairs,
        "inputs": {
            "state_v6_3": path63,
            "state_v6_4": path64,
            "state_v6_5": path65,
            "state_v6_6": path66,
            "state_v6_7": path67,
            "state_v6_8": path68,
            "glyph_state_v6_8": glyph68
        },
        "visuals": {
            "hyperglyph_resonance_png": figure_note
        }
    }

    out_path = os.path.join(state_dir, "tesseract_hyperglyph_state_v6_9.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("[Tesseract v6.9 mini] HyperGlyph state written:", out_path)
    if figure_note:
        print("[Tesseract v6.9 mini] HyperGlyph resonance figure written:", figure_note)
    else:
        print("[Tesseract v6.9 mini] Matplotlib not available; no figure written")


if __name__ == "__main__":
    main()
