# Codex Third Eye v2.4C — Harmonic Predictive Fusion Engine (ASCII-safe)
# Uses reflexive drift for I and dPhi; std(C) for E; robust field synth.
import os, json, math
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE    = os.path.join(ROOT, "logs",  "third_eye_resonance_v2_0.jsonl")
REFL_FILE   = os.path.join(ROOT, "state", "third_eye_reflexive_log.jsonl")
STATE_OUT   = os.path.join(ROOT, "state", "third_eye_fusion_v2_4.json")
VIS_OUT     = os.path.join(ROOT, "visuals", "third_eye_fusion_surface_v2_4.png")
CORE_FILE   = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")

WINDOW, H7, PHI_GAIN, FIELD_SIZE = 300, 0.70, 0.22, 48

def load_jsonl(path, limit=None):
    out=[]
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: out.append(json.loads(line))
                except: pass
    return out if not limit else out[-limit:]

def safe_beta(std_c):
    std_c=float(std_c)
    raw=0.12*(0.18/max(0.06,std_c if std_c>0 else 0.06))
    return max(0.10,min(0.22,raw))

def get_reflexive():
    dn=dp=dphi=0.0
    r=load_jsonl(REFL_FILE,limit=WINDOW)
    if r:
        try:
            last=r[-1]
            dn=abs(float(last.get("drift_now",0.0)))
            dp=abs(float(last.get("drift_pred",0.0)))
            dphi=float(last.get("correction",0.0))
        except: pass
    return dn,dp,dphi

def compute_base_components():
    rec=load_jsonl(LOG_FILE,limit=WINDOW)
    if not rec: return None
    C=np.array([float(x.get("C",0.0)) for x in rec],dtype=float)
    H=np.array([float(x.get("H",0.0)) for x in rec],dtype=float)
    N=len(C)
    std_c=float(np.std(C)) if N>1 else 0.0
    mean_c=float(np.mean(C))
    E=std_c
    dn,dp,dphi=get_reflexive()
    I=1.0/(1.0+dn+dp)
    beta=safe_beta(std_c)
    dCdt=beta*(E*I-H7*mean_c)
    M=(dCdt+dphi)/(1.0+abs(beta-H7))
    return {"E":E,"I":I,"C_mean":mean_c,"C_std":std_c,
            "beta":beta,"H7":H7,"dCdt":dCdt,"dPhi":dphi,"M":M}

def synthesize_field(c):
    E0,I0=c["E"],c["I"]
    dE=max(1e-6,0.25*max(0.02,E0))
    dI=0.20*max(0.1,I0 if I0>0 else 0.1)
    E_ax=np.linspace(max(0.0,E0-dE),E0+dE,FIELD_SIZE)
    I_ax=np.linspace(max(0.0,I0-dI),min(1.0,I0+dI),FIELD_SIZE)
    Z=np.zeros((FIELD_SIZE,FIELD_SIZE))
    for i,e in enumerate(E_ax):
        b=safe_beta(max(1e-6,e))
        for j,ii in enumerate(I_ax):
            d=b*(e*ii-H7*c["C_mean"])
            Z[i,j]=c["C_mean"]+d+PHI_GAIN*c["dPhi"]
    return E_ax,I_ax,Z,float(np.min(Z)),float(np.max(Z))

def visualize(E_ax,I_ax,Z,zmin,zmax):
    plt.figure(figsize=(9.6,4.8))
    plt.imshow(Z.T,origin="lower",
               extent=[E_ax[0],E_ax[-1],I_ax[0],I_ax[-1]],
               aspect="auto",interpolation="nearest",vmin=zmin,vmax=zmax)
    plt.colorbar(label="C_fusion")
    plt.xlabel("E (volatility proxy)")
    plt.ylabel("I (information integrity)")
    plt.title("Third Eye v2.4C — Harmonic Predictive Fusion")
    plt.tight_layout(); plt.savefig(VIS_OUT,dpi=180); plt.close()

def update_core(c,zmin,zmax):
    e={"version":"2.4C","timestamp":datetime.now(timezone.utc).isoformat(),**c,
       "zmin":zmin,"zmax":zmax,"visual":os.path.basename(VIS_OUT)}
    core={}
    if os.path.exists(CORE_FILE):
        try: core=json.load(open(CORE_FILE,"r",encoding="utf-8"))
        except: core={}
    core.setdefault("third_eye_fusion",[]).append(e)
    json.dump(core,open(CORE_FILE,"w",encoding="utf-8"),indent=2)
    return e

def main():
    base=compute_base_components()
    if not base:
        print(json.dumps({"ok":False,"msg":"no resonance data"})); return
    E_ax,I_ax,Z,zmin,zmax=synthesize_field(base)
    visualize(E_ax,I_ax,Z,zmin,zmax)
    state={"ok":True,"version":"2.4C","timestamp":datetime.now(timezone.utc).isoformat(),
           "components":base,"zmin":zmin,"zmax":zmax,"visual":os.path.basename(VIS_OUT)}
    json.dump(state,open(STATE_OUT,"w",encoding="utf-8"),indent=2)
    core_entry=update_core(base,zmin,zmax)
    print(json.dumps({"ok":True,"state":state,"core_append":core_entry},indent=2))

if __name__=="__main__": main()
