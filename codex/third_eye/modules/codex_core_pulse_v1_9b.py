import json, os, matplotlib.pyplot as plt, numpy as np
from datetime import datetime, UTC

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_PATH = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")
VIS_FILE  = os.path.join(ROOT, "visuals", f"codex_pulse_v1_9b.png")
STATE_OUT = os.path.join(ROOT, "state", f"codex_pulse_state_v1_9b.json")

core = {}
if os.path.exists(CORE_PATH):
    with open(CORE_PATH, "r", encoding="utf-8") as f:
        core = json.load(f)

data = core.get("third_eye_long_term", [])
if not data:
    print("❌ No long-term history found.")
    exit()

C_vals = [d.get("C",0) for d in data]
H_vals = [d.get("H",0) for d in data]
bounds = [d.get("ΔΦ_bounds",[0,0]) for d in data]
low, high = zip(*bounds)

ticks = np.arange(len(C_vals))

plt.figure(figsize=(8,5))
plt.plot(ticks, C_vals, label="C (Coherence)", color="#66b2ff")
plt.plot(ticks, H_vals, label="H (H-Index)", color="#ff6666")
plt.fill_between(ticks, low, high, color="gray", alpha=0.2, label="ΔΦ bounds")
plt.axhline(y=0.70, linestyle="--", color="black", linewidth=1)
plt.title("Codex Third Eye — Core Pulse (v1.9B)")
plt.xlabel("Run Index")
plt.ylabel("Metric Value")
plt.legend()
plt.tight_layout()
plt.savefig(VIS_FILE, dpi=180)
plt.close()

summary = {
    "version": "1.9B",
    "timestamp": datetime.now(UTC).isoformat(),
    "runs_analyzed": len(C_vals),
    "mean_C": float(np.mean(C_vals)),
    "mean_H": float(np.mean(H_vals)),
    "mean_bounds": [float(np.mean(low)), float(np.mean(high))],
    "trend": "stable" if np.std(C_vals)<0.15 else "volatile"
}
with open(STATE_OUT,"w",encoding="utf-8") as f:
    json.dump(summary,f,indent=2)

print(json.dumps(summary,indent=2))
