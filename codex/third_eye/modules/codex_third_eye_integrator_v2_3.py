# Codex Third Eye v2.3 — Harmonic Integration Engine (ASCII-safe prints)
# Inputs:
#   logs/third_eye_resonance_v2_0.jsonl    -> recent C,H history (past)
#   state/third_eye_reflexive_log.jsonl    -> ΔΦ lineage (from v2.1)
#   state/third_eye_mediation_state.json   -> prior mediation snapshot (optional)
# Core fusion:
#   1) Mediation:  dC/dt = β (E·I − H7·C̄),  H7 = 0.70
#      E  = std(C) over window; I = 1/(1+|drift_now|+|drift_pred|)
#   2) Reflexive:  ΔΦ from last reflexive entry (if available)
#   3) Trend:      ΔCₚ via NumPy polyfit (1st order) on recent C
#   4) Unified:    C*_next = C̄ + dC/dt + γ·ΔΦ + λ·ΔCₚ
# Params:
#   β auto-tuned by volatility; γ (phi_gain)=0.20; λ (trend_gain)=0.65
# Outputs:
#   state/third_eye_harmonic_v2_3.json
#   visuals/third_eye_harmonic_v2_3.png
#   Appends Memory Core with "third_eye_harmonic"
import os, json, math
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE    = os.path.join(ROOT, "logs",  "third_eye_resonance_v2_0.jsonl")
REFL_FILE   = os.path.join(ROOT, "state", "third_eye_reflexive_log.jsonl")
MEDIATION_S = os.path.join(ROOT, "state", "third_eye_mediation_state.json")
STATE_OUT   = os.path.join(ROOT, "state", "third_eye_harmonic_v2_3.json")
VIS_OUT     = os.path.join(ROOT, "visuals", "third_eye_harmonic_v2_3.png")
CORE_FILE   = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")

WINDOW      = 300
H7          = 0.70
PHI_GAIN    = 0.20   # γ
TREND_GAIN  = 0.65   # λ

def load_jsonl(path, limit=None):
    out = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: out.append(json.loads(line))
                except: pass
    return out if not limit else out[-limit:]

def safe_beta(std_c):
    # Volatility-aware β (clamped to 0.10..0.22)
    beta = 0.12 * (0.18 / max(0.06, float(std_c)))
    return max(0.10, min(0.22, beta))

def compute_components():
    records = load_jsonl(LOG_FILE, limit=WINDOW)
    if not records:
        return None

    C_vals = np.array([float(r.get("C", 0.0)) for r in records], dtype=float)
    H_vals = np.array([float(r.get("H", 0.0)) for r in records], dtype=float)
    N      = len(C_vals)
    t_idx  = np.arange(N, dtype=float)

    std_c  = float(np.std(C_vals)) if N>1 else 0.0
    mean_c = float(np.mean(C_vals))
    E      = std_c

    # Trend (ΔCₚ) via linear fit on recent data
    if N > 3 and (C_vals == C_vals).all():
        coefs = np.polyfit(t_idx, C_vals, 1)  # slope, intercept
        slope = float(coefs[0])
        dC_pred = slope * 50.0   # project over ~50 ticks horizon
    else:
        dC_pred = 0.0

    # Reflexive lineage
    dn = dp = dphi = 0.0
    rlog = load_jsonl(REFL_FILE, limit=WINDOW)
    if rlog:
        try:
            dn   = abs(float(rlog[-1].get("drift_now", 0.0)))
            dp   = abs(float(rlog[-1].get("drift_pred", 0.0)))
            dphi = float(rlog[-1].get("correction", 0.0))     # ΔΦ
        except:
            pass

    I     = 1.0 / (1.0 + dn + dp)
    beta  = safe_beta(std_c)
    dCdt  = beta * (E * I - H7 * mean_c)

    # Unified forecast point estimate
    c_star_next = mean_c + dCdt + PHI_GAIN * dphi + TREND_GAIN * dC_pred

    return {
        "C_series": C_vals.tolist(),
        "H_series": H_vals.tolist(),
        "E": E, "I": I, "C_mean": mean_c, "C_std": std_c,
        "beta": beta, "H7": H7,
        "dCdt": dCdt, "dPhi": dphi, "dC_pred": dC_pred,
        "C_next_star": c_star_next
    }

def visualize(comp):
    C = comp["C_series"]; N = len(C); xs = np.arange(N)
    plt.figure(figsize=(10.2,4.4))
    plt.plot(xs, C, label="C (past)", linewidth=1.4)
    plt.axhline(y=comp["C_mean"], linestyle="--", linewidth=1.0, label="C_mean")
    # Annotate unified terms
    info = "E={:.3f} I={:.3f}  β={:.3f}  dC/dt={:.4f}  ΔΦ={:.4f}  ΔCₚ={:.4f}  C*₊₁={:.4f}".format(
        comp["E"], comp["I"], comp["beta"], comp["dCdt"], comp["dPhi"], comp["dC_pred"], comp["C_next_star"]
    )
    plt.title("Third Eye v2.3 — Harmonic Integration\n" + info)
    plt.xlabel("tick"); plt.ylabel("value"); plt.legend()
    plt.tight_layout(); plt.savefig(VIS_OUT, dpi=180); plt.close()

def update_core(comp):
    entry = {
        "version": "2.3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "E": comp["E"], "I": comp["I"],
        "C_mean": comp["C_mean"], "C_std": comp["C_std"],
        "beta": comp["beta"], "H7": comp["H7"],
        "dCdt": comp["dCdt"], "dPhi": comp["dPhi"], "dC_pred": comp["dC_pred"],
        "C_next_star": comp["C_next_star"]
    }
    core = {}
    if os.path.exists(CORE_FILE):
        try:
            with open(CORE_FILE, "r", encoding="utf-8") as f: core = json.load(f)
        except:
            core = {}
    core.setdefault("third_eye_harmonic", []).append(entry)
    with open(CORE_FILE, "w", encoding="utf-8") as f:
        json.dump(core, f, indent=2)
    return entry

def main():
    comp = compute_components()
    if comp is None:
        print(json.dumps({"ok": False, "msg": "no resonance data found"}, separators=(",",":")))
        return
    visualize(comp)
    state = {
        "ok": True,
        "version": "2.3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "E": comp["E"], "I": comp["I"],
            "C_mean": comp["C_mean"], "C_std": comp["C_std"],
            "beta": comp["beta"], "H7": comp["H7"],
            "dCdt": comp["dCdt"], "dPhi": comp["dPhi"], "dC_pred": comp["dC_pred"],
            "C_next_star": comp["C_next_star"]
        },
        "visual": os.path.basename(VIS_OUT)
    }
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    entry = update_core(comp)
    # ASCII-only print (avoid Windows console emoji issues)
    print(json.dumps({"ok": True, "state": state, "core_append": entry}, indent=2))

if __name__ == "__main__":
    main()
