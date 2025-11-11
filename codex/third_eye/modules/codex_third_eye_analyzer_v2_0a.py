import json, os, numpy as np, matplotlib.pyplot as plt
from datetime import datetime, UTC

ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE   = os.path.join(ROOT, "logs", "third_eye_resonance_v2_0.jsonl")
CORE_FILE  = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")
VIS_FIELD  = os.path.join(ROOT, "visuals", "third_eye_harmonic_field_v2_0a.png")
VIS_HEAT   = os.path.join(ROOT, "visuals", "third_eye_stability_map_v2_0a.png")
OUT_FILE   = os.path.join(ROOT, "state", "third_eye_analysis_v2_0a.json")

# Load records
records = []
with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        try:
            records.append(json.loads(line))
        except:
            pass

if not records:
    print("❌ No data found.")
    raise SystemExit(0)

# Extract vectors
C_vals  = np.array([r.get("C", 0.0) for r in records], dtype=float)
H_vals  = np.array([r.get("H", 0.0) for r in records], dtype=float)
dphi    = np.array([r.get("ΔΦ", 0.0) for r in records], dtype=float)

# Derived metrics
drift    = float(np.mean(np.diff(C_vals))) if len(C_vals) > 1 else 0.0
var_C    = float(np.var(C_vals))
var_H    = float(np.var(H_vals))
width    = np.abs(dphi)                     # ΔΦ magnitude
mean_w   = float(np.mean(width))
trend_w  = float(np.mean(np.diff(width))) if len(width) > 1 else 0.0

classification = "stable"
if np.std(C_vals) >= 0.15: classification = "volatile"
if np.std(C_vals) >= 0.25: classification = "chaotic"

summary = {
    "version": "2.0A",
    "count": int(len(records)),
    "mean_C": float(np.mean(C_vals)),
    "mean_H": float(np.mean(H_vals)),
    "std_C": float(np.std(C_vals)),
    "std_H": float(np.std(H_vals)),
    "min_C": float(np.min(C_vals)),
    "max_C": float(np.max(C_vals)),
    "drift_rate_C": drift,
    "mean_abs_dphi": mean_w,
    "dphi_width_trend": trend_w,
    "classification": classification,
    "timestamp": datetime.now(UTC).isoformat(),
}

# --- Visual 1: Harmonic Field Curve (C & H vs ticks)
plt.figure(figsize=(9,4))
plt.plot(C_vals, label="C (Coherence)", linewidth=1.6)
plt.plot(H_vals, label="H (H-index)", linewidth=1.2)
plt.axhline(y=0.70, linestyle="--", linewidth=1)
plt.title("Codex Third Eye v2.0A — Harmonic Field")
plt.xlabel("Tick"); plt.ylabel("Value"); plt.legend()
plt.tight_layout(); plt.savefig(VIS_FIELD, dpi=180); plt.close()

# --- Visual 2: Resonant Stability Map (C vs H density)
# 2D histogram / heatmap
plt.figure(figsize=(5.5,4.5))
hist = plt.hist2d(C_vals, H_vals, bins=40)
plt.xlabel("C (Coherence)")
plt.ylabel("H (H-index)")
plt.title("Resonant Stability Map (C vs H)")
plt.tight_layout(); plt.savefig(VIS_HEAT, dpi=180); plt.close()

# Persist analysis outputs
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

# Update Memory Core
core = {}
if os.path.exists(CORE_FILE):
    try:
        with open(CORE_FILE, "r", encoding="utf-8") as f:
            core = json.load(f)
    except:
        core = {}

core.setdefault("third_eye_long_term", []).append(summary)
with open(CORE_FILE, "w", encoding="utf-8") as f:
    json.dump(core, f, indent=2)

print(json.dumps(summary, indent=2))
