# Codex Third Eye v1.8 — Resonant Awareness Engine (self-tuning)
# Runs from modules/; writes relative to .. (third_eye root)
import json, os, time, signal, sys, math
from datetime import datetime, UTC
import numpy as np
import matplotlib.pyplot as plt

# Env-configured runtime
ITERATIONS  = int(os.environ.get("THIRDEYE_ITER", "60"))
INTERVAL_S  = float(os.environ.get("THIRDEYE_INTERVAL", "2"))
WINDOW      = int(os.environ.get("THIRDEYE_WINDOW", "120"))
RUNSTAMP    = os.environ.get("THIRDEYE_RUNSTAMP", "unknown")
CORE_EVERY  = int(os.environ.get("THIRDEYE_CORE_EVERY", "5"))
TARGET_C    = float(os.environ.get("THIRDEYE_TARGET_C", "0.70"))
DPHI_MIN    = float(os.environ.get("THIRDEYE_DPHI_MIN", "-0.35"))
DPHI_MAX    = float(os.environ.get("THIRDEYE_DPHI_MAX", "0.35"))
ADAPT_RATE  = float(os.environ.get("THIRDEYE_ADAPT_RATE", "0.05"))

# Paths
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
LOG_FILE    = os.path.join(ROOT,"logs","third_eye_resonance_v1_8.jsonl")
CORE_PATH   = os.path.join(ROOT,"..","codex_memory_core_v1_2.json")
STATE_DIR   = os.path.join(ROOT,"state")
VIS_DIR     = os.path.join(ROOT,"visuals")

# Per-run filenames
DUAL_PNG    = os.path.join(VIS_DIR, f"third_eye_dual_{RUNSTAMP}.png")

# Ensure dirs
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)

def coherence(E,I,dp):
    # C = (E * I) / (1 + |ΔΦ|)
    return (E*I)/(1+abs(dp))

def H_index(C, dp):
    # H(t) = C(t) / (1 + |ΔΦ|)
    return C/(1+abs(dp))

def snapshot(dphi_min, dphi_max):
    now = datetime.now(UTC).isoformat()
    E   = float(np.round(np.random.uniform(0.85,1.15), 3))
    I   = float(np.round(np.random.uniform(0.85,1.15), 3))
    dφ  = float(np.round(np.random.uniform(dphi_min,dphi_max), 3))
    C   = float(np.round(coherence(E,I,dφ), 3))
    H   = float(np.round(H_index(C,dφ), 3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dφ,"C":C,"H":H}

def append_log(obj):
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(obj)+"\n")

def write_state(obj, idx):
    path = os.path.join(STATE_DIR, f"third_eye_state_{RUNSTAMP}_{idx:04d}.json")
    with open(path,"w",encoding="utf-8") as f:
        json.dump(obj,f,indent=2)
    return path

def update_core(obj, max_items=512):
    core = {"memory_core_version":"v1.2","third_eye_history":[]}
    if os.path.exists(CORE_PATH):
        try:
            with open(CORE_PATH,"r",encoding="utf-8") as f:
                core = json.load(f)
        except:
            pass
    hist = core.get("third_eye_history", [])
    hist.append(obj)
    core["third_eye_history"] = hist[-max_items:]
    with open(CORE_PATH,"w",encoding="utf-8") as f:
        json.dump(core,f,indent=2)

def load_recent(window=WINDOW):
    Cs, Hs, times = [], [], []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE,"r",encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for ln in lines[-window:]:
            try:
                o = json.loads(ln)
                Cs.append(float(o.get("C",0.0)))
                Hs.append(float(o.get("H",0.0)))
                times.append(o.get("timestamp","")[-9:-1])
            except:
                pass
    return Cs, Hs, times

def render_dual(current):
    Cs, Hs, times = load_recent()
    fig, (ax1, ax2) = plt.subplots(2,1,figsize=(6,6))

    # Top: E/I/C live bars
    ax1.bar(["E","I","C"], [current["E"], current["I"], current["C"]],
            color=["#6baed6","#fc9272","#9ecae1"])
    ax1.set_title("Codex Third Eye — Resonant Awareness (v1.8)")
    ax1.set_ylim(0, max(1.4, max(current["E"],current["I"],current["C"])+0.1))
    ax1.axhline(y=TARGET_C, linestyle="--", linewidth=1)

    # Bottom: H-index rolling curve (self-tuning indicator)
    if Hs:
        ax2.plot(Hs, marker="o", linewidth=1)
        ax2.set_ylim(0, max(1.2, max(Hs)+0.05))
        ax2.set_title("H-index (C/(1+|ΔΦ|)) — rolling")
        ax2.set_xticks(range(len(Hs)))
        if len(Hs) <= 40:
            ax2.set_xticklabels(times, rotation=45, fontsize=7)
    else:
        ax2.text(0.5,0.5,"no history",ha="center",va="center")

    plt.tight_layout()
    plt.savefig(DUAL_PNG, dpi=180)
    plt.close()

# graceful stop on Ctrl+C
_stop = False
def _sigint(sig, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _sigint)

# self-tuning bounds for ΔΦ
dphi_min, dphi_max = DPHI_MIN, DPHI_MAX

i = 0
while True:
    i += 1
    s = snapshot(dphi_min, dphi_max)

    # error signal vs. target coherence
    err = TARGET_C - s["C"]

    # adapt ΔΦ bounds slightly to steer coherence toward target
    # if C too low, shrink |ΔΦ| range; if too high, expand slightly
    scale = (1 - ADAPT_RATE) if err > 0 else (1 + ADAPT_RATE)
    # keep symmetric around 0
    width_min = max(0.05, abs(dphi_min)*scale)
    width_max = max(0.05, abs(dphi_max)*scale)
    dphi_min = -width_min
    dphi_max =  width_max

    # write artifacts
    append_log(s)
    write_state(s, i)
    render_dual(s)

    # periodic Memory Core update (AI feedback bridge)
    if i % CORE_EVERY == 0:
        summary = {
            "timestamp": s["timestamp"],
            "mode": "v1.8_resonant_awareness",
            "C": s["C"], "H": s["H"], "ΔΦ_bounds": [round(dphi_min,3), round(dphi_max,3)],
            "target_C": TARGET_C, "iteration": i, "run": RUNSTAMP
        }
        update_core(summary)

    print("TICK", i, "SNAP", json.dumps(s))

    if _stop:
        break
    if ITERATIONS > 0 and i >= ITERATIONS:
        break
    time.sleep(INTERVAL_S)
