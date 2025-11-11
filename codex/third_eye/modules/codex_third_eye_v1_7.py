# Codex Third Eye Amplify v1.7 — Continuous Resonance Engine
# Runs from modules/; writes relative to .. (third_eye root)
import json, os, time, signal, sys
from datetime import datetime, UTC
import numpy as np
import matplotlib.pyplot as plt

# Runtime parameters injected via env (with defaults)
ITERATIONS  = int(os.environ.get("THIRDEYE_ITER", "12"))
INTERVAL_S  = float(os.environ.get("THIRDEYE_INTERVAL", "5"))
WINDOW      = int(os.environ.get("THIRDEYE_WINDOW", "64"))
RUNSTAMP    = os.environ.get("THIRDEYE_RUNSTAMP", "unknown")

# Paths
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
LOG_FILE    = os.path.join(ROOT,"logs","third_eye_resonance_log.jsonl")
CORE_PATH   = os.path.join(ROOT,"..","codex_memory_core_v1_2.json")
STATE_DIR   = os.path.join(ROOT,"state")
VIS_DIR     = os.path.join(ROOT,"visuals")

# Per-run filenames (with stable run timestamp)
DUAL_PNG    = os.path.join(VIS_DIR, f"third_eye_dual_{RUNSTAMP}.png")
GRID_PNG    = os.path.join(VIS_DIR, f"third_eye_grid_{RUNSTAMP}.png")

# Ensure dirs
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)

def coherence(E,I,dp): 
    return (E*I)/(1+abs(dp))

def snapshot():
    now = datetime.now(UTC).isoformat()
    E   = float(np.round(np.random.uniform(0.85,1.15), 3))
    I   = float(np.round(np.random.uniform(0.85,1.15), 3))
    dφ  = float(np.round(np.random.uniform(-0.35,0.35), 3))
    C   = float(np.round(coherence(E,I,dφ), 3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dφ,"C":C}

def append_log(s):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(s) + "\n")

def write_state(s, idx):
    path = os.path.join(STATE_DIR, f"third_eye_state_{RUNSTAMP}_{idx:03d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    return path

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

def load_last_Cs(window):
    Cs, times = [], []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for ln in lines[-window:]:
            try:
                o = json.loads(ln)
                Cs.append(float(o.get("C")))
                times.append(o.get("timestamp")[11:19])
            except:
                pass
    return Cs, times

def render_dual(current):
    # bar for current E/I/C, line for recent C
    Cs, times = load_last_Cs(WINDOW)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6,6))
    ax1.bar(["E","I","C"], [current["E"], current["I"], current["C"]],
            color=["#6baed6", "#fc9272", "#9ecae1"])
    ax1.set_title("Codex Third Eye — Current Resonance (v1.7)")
    if Cs:
        ax2.plot(Cs, marker="o", linewidth=1)
        ax2.set_title("C (Coherence) — Recent")
        ax2.set_ylim(0, max(1.1, max(Cs)+0.05))
        ax2.set_xticks(range(len(Cs)))
        ax2.set_xticklabels(times, rotation=45, fontsize=7)
    else:
        ax2.text(0.5,0.5,"no history",ha="center",va="center")
    plt.tight_layout()
    plt.savefig(DUAL_PNG, dpi=180)
    plt.close()

def render_grid():
    # persistence grid: a (1 x T) image of normalized C (0..1) over last WINDOW steps
    Cs,_ = load_last_Cs(WINDOW)
    if not Cs:
        # initialize with a neutral strip to avoid empty file
        Cs = [0.5]
    # normalize to [0,1] using min/max of slice
    vmin, vmax = min(Cs), max(Cs)
    if vmax - vmin < 1e-12:
        data = np.array(Cs)[None,:] * 0 + 0.5
    else:
        data = (np.array(Cs) - vmin) / (vmax - vmin)
        data = data[None,:]
    plt.figure(figsize=(8,1.4))
    plt.imshow(data, aspect="auto", interpolation="nearest")
    plt.yticks([])
    plt.xticks([])
    plt.title("Third Eye — Coherence Persistence Grid (latest → right)")
    plt.tight_layout()
    plt.savefig(GRID_PNG, dpi=180, bbox_inches="tight")
    plt.close()

# graceful stop on Ctrl+C
_stop = False
def _sigint(sig, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _sigint)

# live loop
for i in range(ITERATIONS):
    s = snapshot()
    append_log(s)
    write_state(s, i)
    update_core(s)
    render_dual(s)
    render_grid()
    print("TICK", i+1, "SNAP", json.dumps(s))
    if _stop: break
    if i < ITERATIONS-1:
        time.sleep(INTERVAL_S)
