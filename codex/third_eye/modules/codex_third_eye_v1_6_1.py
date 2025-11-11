# Codex Third Eye Amplify v1.6.1 — Python Engine (Auto-Stable)
import json, datetime, os
import numpy as np
import matplotlib.pyplot as plt

LOG_FILE   = os.path.join("..","logs","third_eye_resonance_log.jsonl")
PLOT_FILE  = os.path.join("..","visuals","third_eye_dual_2025-11-10_19-06-44.png")
STATE_FILE = os.path.join("..","state","third_eye_state_2025-11-10_19-06-44.json")
CORE_PATH  = os.path.join("..","..","codex_memory_core_v1_2.json")

def coherence(E,I,dp): return (E*I)/(1+abs(dp))

def generate_snapshot():
    now=datetime.datetime.now(datetime.UTC).isoformat()
    E=float(np.round(np.random.uniform(0.85,1.15),3))
    I=float(np.round(np.random.uniform(0.85,1.15),3))
    dphi=float(np.round(np.random.uniform(-0.35,0.35),3))
    C=float(np.round(coherence(E,I,dphi),3))
    return {"timestamp":now,"E":E,"I":I,"ΔΦ":dphi,"C":C}

def append_log(snap):
    os.makedirs(os.path.dirname(LOG_FILE),exist_ok=True)
    with open(LOG_FILE,"a",encoding="utf-8") as f: f.write(json.dumps(snap)+"\\n")

def write_state(snap):
    os.makedirs(os.path.dirname(STATE_FILE),exist_ok=True)
    with open(STATE_FILE,"w",encoding="utf-8") as f: json.dump(snap,f,indent=2)

def update_core(snap,max_items=128):
    core={"memory_core_version":"v1.2","third_eye_history":[]}
    if os.path.exists(CORE_PATH):
        try:
            with open(CORE_PATH,"r",encoding="utf-8") as f: core=json.load(f)
        except: pass
    hist=core.get("third_eye_history",[])
    hist.append(snap); core["third_eye_history"]=hist[-max_items:]
    with open(CORE_PATH,"w",encoding="utf-8") as f: json.dump(core,f,indent=2)

def render_dual(snap,window=32):
    Cs,times=[],[]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE,"r",encoding="utf-8") as f:
            lines=[l.strip() for l in f if l.strip()]
        tail=lines[-window:]
        for l in tail:
            try:
                obj=json.loads(l); Cs.append(obj.get("C"))
                times.append(obj.get("timestamp")[11:19])
            except: pass
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(6,6))
    ax1.bar(["E","I","C"],[snap["E"],snap["I"],snap["C"]],
             color=["#6baed6","#fc9272","#9ecae1"])
    ax1.set_title("Codex Third Eye Resonance v1.6.1")
    if Cs:
        ax2.plot(Cs,marker="o"); ax2.set_title("Coherence History")
        ax2.set_ylim(0,max(1.1,max(Cs)+0.05))
    plt.tight_layout(); os.makedirs(os.path.dirname(PLOT_FILE),exist_ok=True)
    plt.savefig(PLOT_FILE,dpi=180); plt.close()

if __name__=="__main__":
    s=generate_snapshot()
    append_log(s); write_state(s); update_core(s); render_dual(s)
    print("SNAPSHOT",json.dumps(s))
