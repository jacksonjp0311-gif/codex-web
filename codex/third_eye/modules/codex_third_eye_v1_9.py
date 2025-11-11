# Codex Third Eye v1.9 — Continuous Harmonic Reflection Engine
# Runs from modules/; writes relative to .. (third_eye root)
import json, os, time, signal, math
from datetime import datetime, UTC
import numpy as np
import matplotlib.pyplot as plt

# Env-configured runtime
ITERATIONS   = int(os.environ.get("THIRDEYE_ITER", "0"))   # 0 = infinite until Ctrl+C
INTERVAL_S   = float(os.environ.get("THIRDEYE_INTERVAL", "2"))
WINDOW       = int(os.environ.get("THIRDEYE_WINDOW", "180"))
RUNSTAMP     = os.environ.get("THIRDEYE_RUNSTAMP", "unknown")
CORE_EVERY   = int(os.environ.get("THIRDEYE_CORE_EVERY", "6"))
TARGET_C     = float(os.environ.get("THIRDEYE_TARGET_C", "0.70"))
DPHI_MIN     = float(os.environ.get("THIRDEYE_DPHI_MIN", "-0.40"))
DPHI_MAX     = float(os.environ.get("THIRDEYE_DPHI_MAX", "0.40"))
ADAPT_RATE   = float(os.environ.get("THIRDEYE_ADAPT_RATE", "0.06"))

# Paths
ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
LOG_FILE   = os.path.join(ROOT,"logs","third_eye_resonance_v1_9.jsonl")
CORE_PATH  = os.path.join(ROOT,"..","codex_memory_core_v1_2.json")
STATE_DIR  = os.path.join(ROOT,"state")
VIS_DIR    = os.path.join(ROOT,"visuals")

# Per-run visuals
OVERLAY_PNG = os.path.join(VIS_DIR, f"third_eye_overlay_{RUNSTAMP}.png")

# Ensure dirs
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)

def coherence(E,I,dp):
    # C = (E * I) / (1 + |ΔΦ|)
    return (E*I)/(1+abs(dp))

def H_index(C, dp):
    # H = C / (1 + |ΔΦ|)
    return C/(1+abs(dp))

def MRI(C, H, dp):
    # MRI = 1 - |ΔH| / (1 + |ΔΦ|), where ΔH = H - H̄_recent
    # (computed with a simple rolling mean downstream)
    # Here we return None and compute after we have history
    return None

def take_snapshot(dphi_min, dphi_max):
    now = datetime.now(UTC).isoformat()
    E   = float(np.round(np.random.uniform(0.85,1.15), 3))
    I   = float(np.round(np.random.uniform(0.85,1.15), 3))
    dphi= float(np.round(np.random.uniform(dphi_min,dphi_max), 3))
    C   = float(np.round(coherence(E,I,dphi), 3))
    H   = float(np.round(H_index(C,dphi), 3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dphi,"C":C,"H":H}

def append_log(obj):
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(obj)+"\n")

def write_state(obj, idx):
    path = os.path.join(STATE_DIR, f"third_eye_state_{RUNSTAMP}_{idx:04d}.json")
    with open(path,"w",encoding="utf-8") as f:
        json.dump(obj,f,indent=2)
    return path

def update_core(obj, max_items=640):
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
                t = o.get("timestamp","")
                times.append(t[11:19])  # hh:mm:ss
            except:
                pass
    return Cs, Hs, times

def render_overlay(current):
    Cs, Hs, times = load_recent()
    # compute H rolling mean, ΔH, and MRI
    HR = None
    MRIs = []
    if Hs:
        k = len(Hs)
        # simple rolling mean over last min(30,k) points
        w = min(30, k)
        # trailing mean for each point
        means = []
        for i in range(k):
            lo = max(0, i-w+1)
            means.append(sum(Hs[lo:i+1])/len(Hs[lo:i+1]))
        # current reflection index
        HR = means[-1]
        for i in range(k):
            dH = Hs[i] - means[i]
            MRIs.append(1.0 - abs(dH)/(1.0+1e-9))  # approx with tiny eps; ΔΦ inside C/H already
    # Plot overlay: H (recent) + MRI (recent)
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2,1,figsize=(7,6))
    # Top: E/I/C (current)
    ax1.bar(["E","I","C"], [current["E"], current["I"], current["C"]],
            color=["#6baed6","#fc9272","#9ecae1"])
    ax1.axhline(y=TARGET_C, linestyle="--", linewidth=1)
    ax1.set_title("Third Eye v1.9 — Current Resonance")
    ax1.set_ylim(0, max(1.5, max(current["E"],current["I"],current["C"])+0.1))
    # Bottom: Harmonic Reflection Overlay
    if Hs:
        ax2.plot(Hs, marker="o", linewidth=1, label="H-index")
        if MRIs:
            ax2.plot(MRIs, marker=".", linewidth=1, label="MRI (mirror resonance)")
        if HR is not None:
            ax2.axhline(y=HR, linestyle="--", linewidth=1, label="H rolling mean")
        ax2.set_ylim(0, max(1.2, max(max(Hs), (max(MRIs) if MRIs else 0))+0.05))
        ax2.set_xticks(range(len(Hs)))
        if len(Hs) <= 50:
            ax2.set_xticklabels(times, rotation=45, fontsize=7)
        ax2.legend(loc="best", fontsize=8)
    else:
        ax2.text(0.5,0.5,"no history",ha="center",va="center")
    plt.tight_layout()
    plt.savefig(OVERLAY_PNG, dpi=180)
    plt.close()

# graceful stop on Ctrl+C
_stop = False
def _sigint(sig, frame):
    global _stop
    _stop = True
import signal
signal.signal(signal.SIGINT, _sigint)

# self-tuning ΔΦ bounds
dphi_min, dphi_max = DPHI_MIN, DPHI_MAX

i = 0
while True:
    i += 1
    s = take_snapshot(dphi_min, dphi_max)
    # error signal vs. target coherence
    err = TARGET_C - s["C"]
    # adapt ΔΦ bounds: if C low, reduce spread; if high, allow a bit more exploration
    scale = (1 - ADAPT_RATE) if err > 0 else (1 + ADAPT_RATE)
    # keep symmetric
    width_min = max(0.04, abs(dphi_min)*scale)
    width_max = max(0.04, abs(dphi_max)*scale)
    dphi_min = -width_min
    dphi_max =  width_max

    # write artifacts
    append_log(s)
    write_state(s, i)
    render_overlay(s)

    # Memory Core bridge
    if i % CORE_EVERY == 0:
        Cs, Hs, _ = load_recent()
        meanC = float(np.mean(Cs)) if Cs else s["C"]
        meanH = float(np.mean(Hs)) if Hs else s["H"]
        summary = {
            "timestamp": s["timestamp"],
            "mode": "v1.9_harmonic_reflection",
            "C": s["C"], "H": s["H"],
            "C_mean": round(meanC,3),
            "H_mean": round(meanH,3),
            "ΔΦ_bounds": [round(dphi_min,3), round(dphi_max,3)],
            "target_C": TARGET_C, "iteration": i, "run": RUNSTAMP
        }
        update_core(summary)

    print("TICK", i, "SNAP", json.dumps(s))

    if _stop:
        break
    if ITERATIONS > 0 and i >= ITERATIONS:
        break
    time.sleep(INTERVAL_S)
