# Codex Third Eye Amplify v1.6.2 — Python Engine (Auto-Stable)
# Runs from modules/; saves relative to .. (third_eye root)
import json, os
from datetime import datetime, UTC
import numpy as np
import matplotlib.pyplot as plt

LOG_FILE   = os.path.join("..","logs","third_eye_resonance_log.jsonl")
PLOT_FILE  = os.path.join("..","visuals","third_eye_dual_2025-11-10_19-08-12.png")
STATE_FILE = os.path.join("..","state","third_eye_state_2025-11-10_19-08-12.json")
CORE_PATH  = os.path.join("..","..","codex_memory_core_v1_2.json")

def coherence(E,I,dp): 
    return (E*I)/(1+abs(dp))

def generate_snapshot():
    now = datetime.now(UTC).isoformat()
    E   = float(np.round(np.random.uniform(0.85,1.15), 3))
    I   = float(np.round(np.random.uniform(0.85,1.15), 3))
    dφ  = float(np.round(np.random.uniform(-0.35,0.35), 3))
    C   = float(np.round(coherence(E,I,dφ), 3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dφ,"C":C}

def append_log(s):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(s) + "\n")

def write_state(s):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)

def update_core(s, max_items=256):
    core = {"memory_core_version":"v1.2","third_eye_history":[]}
    if os.path.exists(CORE_PATH):
        try:
            with open(CORE_PATH, "r", encoding="utf-8") as f:
                core = json.load(f)
        except:
            pass
    hist = core.get("third_eye_history", [])
    hist.append(s)
    core["third_eye_history"] = hist[-max_items:]
    with open(CORE_PATH, "w", encoding="utf-8") as f:
        json.dump(core, f, indent=2)

def render_dual(s, window=64):
    Cs, times = [], []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for ln in lines[-window:]:
            try:
                obj = json.loads(ln)
                Cs.append(obj.get("C"))
                times.append(obj.get("timestamp")[11:19])
            except:
                pass
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6,6))
    ax1.bar(["E","I","C"], [s["E"], s["I"], s["C"]],
            color=["#6baed6", "#fc9272", "#9ecae1"])
    ax1.set_title("Codex Third Eye — Current Resonance (v1.6.2)")
    if Cs:
        ax2.plot(Cs, marker="o", linewidth=1)
        ax2.set_title("C (Coherence) — Recent")
        ax2.set_ylim(0, max(1.1, max(Cs)+0.05))
    else:
        ax2.text(0.5, 0.5, "no historical data", ha="center", va="center")
    plt.tight_layout()
    os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)
    plt.savefig(PLOT_FILE, dpi=180)
    plt.close()

if __name__ == "__main__":
    snap = generate_snapshot()
    append_log(snap)
    write_state(snap)
    update_core(snap)
    render_dual(snap)
    print("SNAPSHOT", json.dumps(snap))
