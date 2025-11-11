import json, os, numpy as np, matplotlib.pyplot as plt
from datetime import datetime, UTC

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(ROOT, "logs", "third_eye_resonance_v1_9.jsonl")
CORE_FILE = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")
VISUAL_FILE = os.path.join(ROOT, "visuals", f"third_eye_harmonic_trend_v1_9.png")
OUT_FILE = os.path.join(ROOT, "state", f"third_eye_analysis_v1_9.json")

records = []
with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        try:
            records.append(json.loads(line))
        except:
            pass

if not records:
    print("❌ No data found.")
    exit()

C_vals = np.array([r["C"] for r in records])
H_vals = np.array([r["H"] for r in records])
Δ_vals = np.array([r["ΔΦ"] for r in records])

summary = {
    "version": "1.9A",
    "count": len(records),
    "mean_C": float(np.mean(C_vals)),
    "mean_H": float(np.mean(H_vals)),
    "std_C": float(np.std(C_vals)),
    "std_H": float(np.std(H_vals)),
    "min_C": float(np.min(C_vals)),
    "max_C": float(np.max(C_vals)),
    "drift_rate": float(np.mean(np.diff(C_vals))) if len(C_vals)>1 else 0.0,
    "classification": "stable" if np.std(C_vals)<0.15 else "chaotic",
    "timestamp": datetime.now(UTC).isoformat()
}

# --- Plot harmonic evolution ---
plt.figure(figsize=(8,4))
plt.plot(C_vals, label="C (Coherence)", linewidth=1.5)
plt.plot(H_vals, label="H (H-Index)", linewidth=1.0)
plt.axhline(y=0.70, color="gray", linestyle="--", linewidth=1)
plt.legend()
plt.title("Codex Third Eye v1.9A — Harmonic Evolution Trend")
plt.xlabel("Tick"); plt.ylabel("Value")
plt.tight_layout(); plt.savefig(VISUAL_FILE, dpi=180); plt.close()

# --- Write outputs ---
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

core = {}
if os.path.exists(CORE_FILE):
    try:
        with open(CORE_FILE,"r",encoding="utf-8") as f:
            core = json.load(f)
    except:
        pass

core.setdefault("third_eye_long_term", []).append(summary)

with open(CORE_FILE,"w",encoding="utf-8") as f:
    json.dump(core, f, indent=2)

print(json.dumps(summary, indent=2))
