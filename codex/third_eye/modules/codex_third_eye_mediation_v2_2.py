# Codex Third Eye v2.2 — Coherence Mediation Engine (ASCII-safe output)
# Reads:
#   logs/third_eye_resonance_v2_0.jsonl        (C,H history)
#   state/third_eye_reflexive_log.jsonl        (drift_now, drift_pred, ΔΦ lineage)
# Computes triadic mediation:
#   E  = energy proxy (std(C) over window)
#   I  = information integrity = 1 / (1 + |drift_now| + |drift_pred|)
#   C̄  = mean coherence over window
#   dC/dt = β (E·I − H7·C̄),  H7 = 0.70
# Saves:
#   state/third_eye_mediation_state.json
#   visuals/third_eye_mediation_v2_2.png
# Updates:
#   ../codex_memory_core_v1_2.json with "third_eye_mediation"
import os, json, math, numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone

ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE   = os.path.join(ROOT, "logs",  "third_eye_resonance_v2_0.jsonl")
REFL_FILE  = os.path.join(ROOT, "state", "third_eye_reflexive_log.jsonl")
STATE_OUT  = os.path.join(ROOT, "state", "third_eye_mediation_state.json")
VIS_OUT    = os.path.join(ROOT, "visuals", "third_eye_mediation_v2_2.png")
CORE_FILE  = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")

WINDOW     = 300
H7         = 0.70

def load_jsonl(path, limit=None):
    out = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try:
                    out.append(json.loads(line))
                except:
                    pass
    return out if not limit else out[-limit:]

def safe_beta(std_c):
    # volatility-aware β (clamped 0.10..0.22)
    beta = 0.12 * (0.18 / max(0.06, float(std_c)))
    return max(0.10, min(0.22, beta))

def compute_components():
    records = load_jsonl(LOG_FILE, limit=WINDOW)
    if not records:
        return None

    C_vals = np.array([float(r.get("C", 0.0)) for r in records], dtype=float)
    H_vals = np.array([float(r.get("H", 0.0)) for r in records], dtype=float)

    std_c  = float(np.std(C_vals)) if len(C_vals)>1 else 0.0
    mean_c = float(np.mean(C_vals))
    E      = std_c  # energy proxy
    # reflexive drift components (recent)
    rlog   = load_jsonl(REFL_FILE, limit=WINDOW)
    if rlog:
        dn = abs(float(rlog[-1].get("drift_now", 0.0)))
        dp = abs(float(rlog[-1].get("drift_pred", 0.0)))
    else:
        dn = dp = 0.0
    I = 1.0 / (1.0 + dn + dp)  # information integrity
    beta = safe_beta(std_c)
    dCdt = beta * (E * I - H7 * mean_c)

    return {
        "C_series": C_vals.tolist(),
        "H_series": H_vals.tolist(),
        "E": E, "I": I, "C_mean": mean_c, "C_std": std_c,
        "beta": beta, "H7": H7, "dCdt": dCdt
    }

def visualize(components):
    C_vals = components["C_series"]
    N = len(C_vals)
    xs = np.arange(N)
    plt.figure(figsize=(9,4.2))
    # pane 1: C series
    plt.plot(xs, C_vals, label="C (coherence)", linewidth=1.4)
    plt.axhline(y=components["C_mean"], linestyle="--", linewidth=1, label="C_mean")
    # annotate scalars
    txt = "E={:.3f}  I={:.3f}  beta={:.3f}  dC/dt={:.4f}".format(
        components["E"], components["I"], components["beta"], components["dCdt"]
    )
    plt.title("Third Eye v2.2 — Coherence Mediation\n" + txt)
    plt.xlabel("tick"); plt.ylabel("value"); plt.legend()
    plt.tight_layout(); plt.savefig(VIS_OUT, dpi=180); plt.close()

def update_core(components):
    entry = {
        "version": "2.2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "E": components["E"], "I": components["I"],
        "C_mean": components["C_mean"], "C_std": components["C_std"],
        "beta": components["beta"], "H7": components["H7"],
        "dCdt": components["dCdt"]
    }
    core = {}
    if os.path.exists(CORE_FILE):
        try:
            with open(CORE_FILE, "r", encoding="utf-8") as f:
                core = json.load(f)
        except:
            core = {}
    core.setdefault("third_eye_mediation", []).append(entry)
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
        "version": "2.2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "E": comp["E"], "I": comp["I"], "C_mean": comp["C_mean"],
            "C_std": comp["C_std"], "beta": comp["beta"], "H7": comp["H7"],
            "dCdt": comp["dCdt"]
        },
        "visual": os.path.basename(VIS_OUT)
    }
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    entry = update_core(comp)
    # ASCII-only print to avoid console encoding issues
    print(json.dumps({"ok": True, "state": state, "core_append": entry}, indent=2))

if __name__ == "__main__":
    main()
