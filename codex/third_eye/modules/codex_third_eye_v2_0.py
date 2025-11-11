# Codex Third Eye v2.0 — Feedback Loop Engine (self-tuning from analysis)
# Runs from modules/; writes relative to .. (third_eye root)
import json, os, time, signal
from datetime import datetime, UTC
import numpy as np
import matplotlib.pyplot as plt

ITERATIONS  = int(os.environ.get("THIRDEYE_ITER","300"))
INTERVAL_S  = float(os.environ.get("THIRDEYE_INTERVAL","2"))
WINDOW      = int(os.environ.get("THIRDEYE_WINDOW","240"))
RUNSTAMP    = os.environ.get("THIRDEYE_RUNSTAMP","unknown")
CORE_EVERY  = int(os.environ.get("THIRDEYE_CORE_EVERY","10"))
TARGET_C    = float(os.environ.get("THIRDEYE_TARGET_C","0.70"))
DPHI_MIN    = float(os.environ.get("THIRDEYE_DPHI_MIN","-0.30"))
DPHI_MAX    = float(os.environ.get("THIRDEYE_DPHI_MAX","0.30"))
ADAPT_RATE  = float(os.environ.get("THIRDEYE_ADAPT_RATE","0.06"))

ROOT      = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
LOG_FILE  = os.path.join(ROOT,"logs","third_eye_resonance_v2_0.jsonl")
STATE_DIR = os.path.join(ROOT,"state")
VIS_DIR   = os.path.join(ROOT,"visuals")
CORE_FILE = os.path.join(ROOT,"..","codex_memory_core_v1_2.json")
DUAL_PNG  = os.path.join(VIS_DIR, f"third_eye_dual_{RUNSTAMP}.png")
CTRL_PNG  = os.path.join(VIS_DIR, f"third_eye_control_{RUNSTAMP}.png")

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def coherence(E,I,dp):
    return (E*I)/(1+abs(dp))

def snapshot(dphi_min, dphi_max):
    now = datetime.now(UTC).isoformat()
    E   = float(np.round(np.random.uniform(0.85,1.15), 3))
    I   = float(np.round(np.random.uniform(0.85,1.15), 3))
    dφ  = float(np.round(np.random.uniform(dphi_min, dphi_max), 3))
    C   = float(np.round(coherence(E,I,dφ), 3))
    H   = float(np.round(C/(1+abs(dφ)), 3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dφ,"C":C,"H":H}

def append_log(s): 
    with open(LOG_FILE,"a",encoding="utf-8") as f: f.write(json.dumps(s)+"\n")

def write_state(s,i):
    p=os.path.join(STATE_DIR, f"third_eye_state_{RUNSTAMP}_{i:05d}.json")
    with open(p,"w",encoding="utf-8") as f: json.dump(s,f,indent=2)

def update_core(obj):
    core={"memory_core_version":"v1.2","third_eye_history":[]}
    if os.path.exists(CORE_FILE):
        try:
            with open(CORE_FILE,"r",encoding="utf-8") as f:
                core=json.load(f)
        except: pass
    hist=core.get("third_eye_history",[])
    hist.append(obj)
    core["third_eye_history"]=hist[-1024:]
    with open(CORE_FILE,"w",encoding="utf-8") as f:
        json.dump(core,f,indent=2)

def recent_vals(key, window=WINDOW):
    vals=[]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE,"r",encoding="utf-8") as f:
            for ln in f: 
                try:
                    o=json.loads(ln); vals.append(float(o.get(key,0.0)))
                except: pass
    return vals[-window:]

def render_panels(current, dphi_min, dphi_max):
    Cs = recent_vals("C")
    Hs = recent_vals("H")
    import matplotlib.pyplot as plt
    # Current + rolling
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(7,6))
    ax1.bar(["E","I","C"], [current["E"], current["I"], current["C"]],
            color=["#6baed6","#fc9272","#9ecae1"])
    ax1.axhline(y=TARGET_C, linestyle="--", linewidth=1)
    ax1.set_title("Third Eye v2.0 — Current Resonance")
    if Cs:
        ax2.plot(Cs, marker="o", linewidth=1, label="C")
        ax2.plot(Hs, linewidth=1, label="H")
        ax2.legend(); ax2.set_ylim(0, max(1.2, max(Cs+Hs)+0.05 if Hs else max(Cs)+0.05))
        ax2.set_title("Rolling Coherence / H-index")
    plt.tight_layout(); plt.savefig(DUAL_PNG, dpi=180); plt.close()

    # Control panel: ΔΦ bounds + error
    err = TARGET_C - current["C"]
    fig,ax=plt.subplots(figsize=(7,2.8))
    ax.bar(["err","ΔΦmin","ΔΦmax"], [err, dphi_min, dphi_max])
    ax.set_title("v2.0 Control State — error & ΔΦ bounds")
    plt.tight_layout(); plt.savefig(CTRL_PNG, dpi=180); plt.close()

_stop=False
def _sigint(sig,frame):
    global _stop; _stop=True
signal.signal(signal.SIGINT,_sigint)

dphi_min, dphi_max = DPHI_MIN, DPHI_MAX

for i in range(1, 10**9):
    s = snapshot(dphi_min, dphi_max)
    append_log(s); write_state(s,i)
    # controller
    err = TARGET_C - s["C"]
    # proportional-like tweak of ΔΦ bounds: reduce width if C < target
    scale = (1 - ADAPT_RATE) if err>0 else (1 + ADAPT_RATE)
    # maintain symmetry around 0 and clamp to safe limits
    width_min = max(0.03, min(0.90, abs(dphi_min)*scale))
    width_max = max(0.03, min(0.90, abs(dphi_max)*scale))
    dphi_min, dphi_max = -width_min, width_max

    if i % CORE_EVERY == 0:
        recentC = recent_vals("C", window=60)
        summary = {
            "timestamp": s["timestamp"],
            "mode": "v2.0_feedback_loop",
            "iteration": i, "run": RUNSTAMP,
            "C": s["C"], "H": s["H"],
            "err": round(err,3),
            "ΔΦ_bounds": [round(dphi_min,3), round(dphi_max,3)],
            "target_C": TARGET_C,
            "avgC_60": float(np.mean(recentC)) if recentC else s["C"]
        }
        update_core(summary)
    if i % 5 == 0:
        render_panels(s, dphi_min, dphi_max)

    if _stop: break
    if ITERATIONS>0 and i>=ITERATIONS: break
    time.sleep(INTERVAL_S)
