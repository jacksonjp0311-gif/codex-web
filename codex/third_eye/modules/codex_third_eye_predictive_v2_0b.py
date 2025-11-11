import json, os, time, numpy as np, matplotlib.pyplot as plt
from datetime import datetime, UTC
from sklearn.linear_model import LinearRegression

ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE   = os.path.join(ROOT, "logs", "third_eye_resonance_v2_0.jsonl")
STATE_FILE = os.path.join(ROOT, "state", f"third_eye_predictive_state_{datetime.now(UTC).isoformat().replace(':','-')}.json")
VIS_PRED   = os.path.join(ROOT, "visuals", f"third_eye_predictive_v2_0b.png")
CORE_FILE  = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")

TARGET_C   = 0.769
ADAPT_RATE = 0.12
HORIZON    = 50

print("🔮 Codex Third Eye v2.0B — Adaptive Predictive Mode Initialized")

# --- Load recent resonance data ---
records = []
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for ln in f:
            try: records.append(json.loads(ln))
            except: pass

if len(records) < 50:
    print("⚠️ Not enough data to predict; exiting.")
    raise SystemExit(0)

C_vals = np.array([r.get("C", 0.0) for r in records[-300:]])
H_vals = np.array([r.get("H", 0.0) for r in records[-300:]])
t_idx  = np.arange(len(C_vals)).reshape(-1,1)

# --- Predictive modeling (linear + adaptive smoothing) ---
model_C = LinearRegression().fit(t_idx, C_vals)
model_H = LinearRegression().fit(t_idx, H_vals)

future_idx = np.arange(len(C_vals), len(C_vals)+HORIZON).reshape(-1,1)
pred_C = model_C.predict(future_idx)
pred_H = model_H.predict(future_idx)

# Adaptive smooth (Placidity Layer ∿)
smoothed_C = TARGET_C + (pred_C - TARGET_C) * (1 - ADAPT_RATE)
smoothed_H = np.clip(pred_H, 0, 1.2)

# --- Visualization ---
plt.figure(figsize=(9,4))
plt.plot(C_vals, label="C (past)", color="#6baed6")
plt.plot(H_vals, label="H (past)", color="#fc9272")
plt.plot(np.arange(len(C_vals), len(C_vals)+HORIZON), smoothed_C, "--", label="C forecast", color="#08519c")
plt.plot(np.arange(len(H_vals), len(H_vals)+HORIZON), smoothed_H, "--", label="H forecast", color="#a50f15")
plt.axhline(y=TARGET_C, linestyle="--", color="gray", linewidth=1)
plt.title("Codex Third Eye v2.0B — Adaptive Predictive Horizon")
plt.xlabel("Tick"); plt.ylabel("Resonant Value")
plt.legend(); plt.tight_layout(); plt.savefig(VIS_PRED, dpi=180); plt.close()

# --- Compute predictive metrics ---
ΔC = float(np.mean(np.diff(C_vals)))
ΔC_future = float(pred_C[-1] - C_vals[-1])
coherence_tendency = "rising" if ΔC_future > 0 else "falling"

summary = {
    "version": "2.0B",
    "timestamp": datetime.now(UTC).isoformat(),
    "mean_C": float(np.mean(C_vals)),
    "mean_H": float(np.mean(H_vals)),
    "drift_now": ΔC,
    "drift_predicted": ΔC_future,
    "forecast_trend": coherence_tendency,
    "target_C": TARGET_C,
    "adapt_rate": ADAPT_RATE,
    "horizon": HORIZON
}

# Save state + update Core
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

core = {}
if os.path.exists(CORE_FILE):
    try:
        with open(CORE_FILE,"r",encoding="utf-8") as f: core=json.load(f)
    except: core = {}
core.setdefault("third_eye_predictive", []).append(summary)
with open(CORE_FILE,"w",encoding="utf-8") as f: json.dump(core,f,indent=2)

print(json.dumps(summary, indent=2))
print("✅ Predictive analysis complete. Visual saved to", VIS_PRED)
