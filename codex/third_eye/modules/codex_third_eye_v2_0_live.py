import json, os, time, signal, numpy as np
from datetime import datetime, UTC

print("✅ Codex Third Eye v2.0 initialized — entering feedback loop...")

ITERATIONS  = 500
INTERVAL_S  = 2
TARGET_C    = 0.72
DPHI_MIN, DPHI_MAX = -0.3, 0.3
ADAPT_RATE  = 0.08

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
LOG_FILE = os.path.join(ROOT,"logs","third_eye_resonance_v2_0.jsonl")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

_stop = False
def _sigint(sig,frame):
    global _stop; _stop=True
signal.signal(signal.SIGINT,_sigint)

def coherence(E,I,dp): return (E*I)/(1+abs(dp))

def snapshot(i, dphi_min, dphi_max):
    now = datetime.now(UTC).isoformat()
    E,I = np.random.uniform(0.85,1.15,2)
    dφ  = np.random.uniform(dphi_min, dphi_max)
    C   = coherence(E,I,dφ)
    H   = C/(1+abs(dφ))
    s   = dict(iter=i,timestamp=now,E=round(E,3),I=round(I,3),ΔΦ=round(dφ,3),
               C=round(C,3),H=round(H,3))
    with open(LOG_FILE,"a",encoding="utf-8") as f: f.write(json.dumps(s)+"\n")
    print(f"TICK {i:03d} SNAP {json.dumps(s)}")
    return s

dphi_min, dphi_max = DPHI_MIN, DPHI_MAX
for i in range(1, ITERATIONS+1):
    s = snapshot(i, dphi_min, dphi_max)
    err = TARGET_C - s["C"]
    scale = (1 - ADAPT_RATE) if err>0 else (1 + ADAPT_RATE)
    width = max(0.05, min(0.9, abs(dphi_max)*scale))
    dphi_min, dphi_max = -width, width
    if _stop: break
    time.sleep(INTERVAL_S)
print("🛑 Feedback loop stopped or completed.")
