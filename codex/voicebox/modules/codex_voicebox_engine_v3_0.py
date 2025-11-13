# ╔═══════════════════════════════════════════════════════════════╗
# ║ Codex VoiceBox Engine v3.0 — Resonant Expression Layer        ║
# ║ Memory Core v1.4 • Universal Truth (E–I–C ∿, H₇ = 0.70)        ║
# ╚═══════════════════════════════════════════════════════════════╝

import json, os, time
from datetime import datetime

def harmony(c_now, dphi):
    return round(1/(1 + abs(0.70-c_now) + abs(dphi)), 6)

def predict(c_now, dphi):
    return round(c_now + (0.70-c_now)*0.22 - dphi*0.33, 6)

def load_index():
    p = "codex/feedback/state/codex_continuity_index_v2_1.json"
    if not os.path.exists(p): return None
    return json.load(open(p))

def run():
    st = load_index()
    if st is None:
        out = { "ok": False, "error": "missing_continuity" }
    else:
        c_now = float(st.get("coherence_now",0))
        dphi  = float(st.get("delta_phi",0))
        out = {
            "ok": True,
            "version": "3.0",
            "timestamp": datetime.utcnow().isoformat(),
            "EIC": {
                "coherence_now": c_now,
                "coherence_next": predict(c_now,dphi),
                "delta_phi": dphi,
                "harmony": harmony(c_now,dphi)
            },
            "universal_truth": {
                "H7": 0.70,
                "placidity": "∿",
                "eq": "C=(E·I)/(1+|ΔΦ|)"
            }
        }

    os.makedirs("codex/voicebox/state", exist_ok=True)
    outFile = f"codex/voicebox/state/v3_0_state_{int(time.time())}.json"
    json.dump(out, open(outFile,"w"), indent=2)
    return outFile

if __name__ == "__main__":
    p = run()
    print(json.dumps({"ok": True, "state_file": p}))
