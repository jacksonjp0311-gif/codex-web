# Codex Third Eye v2.4 — Harmonic Predictive Fusion Engine (ASCII-safe)
# Inputs:
#   logs/third_eye_resonance_v2_0.jsonl  -> recent C,H series
#   state/third_eye_reflexive_log.jsonl  -> drift_now, drift_pred, correction (ΔΦ)
#   state/third_eye_mediation_state.json -> optional snapshot from v2.2
# Outputs:
#   state/third_eye_fusion_v2_4.json
#   visuals/third_eye_fusion_surface_v2_4.png
#   Append Memory Core (../codex_memory_core_v1_2.json): "third_eye_fusion"

import os, json, math
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE    = os.path.join(ROOT, "logs",  "third_eye_resonance_v2_0.jsonl")
REFL_FILE   = os.path.join(ROOT, "state", "third_eye_reflexive_log.jsonl")
MEDIATION_S = os.path.join(ROOT, "state", "third_eye_mediation_state.json")  # optional
STATE_OUT   = os.path.join(ROOT, "state", "third_eye_fusion_v2_4.json")
VIS_OUT     = os.path.join(ROOT, "visuals", "third_eye_fusion_surface_v2_4.png")
CORE_FILE   = os.path.join(ROOT, "..", "codex_memory_core_v1_2.json")

WINDOW      = 300
H7          = 0.70
PHI_GAIN    = 0.22   # γ — reflexive correction influence
FIELD_SIZE  = 48     # grid resolution (E × I)

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
    # Volatility-aware β clamped to [0.10, 0.22]
    std_c = float(std_c)
    raw   = 0.12 * (0.18 / max(0.06, std_c if std_c>0 else 0.06))
    return max(0.10, min(0.22, raw))

def compute_base_components():
    records = load_jsonl(LOG_FILE, limit=WINDOW)
    if not records:
        return None

    C_vals = np.array([float(r.get("C", 0.0)) for r in records], dtype=float)
    H_vals = np.array([float(r.get("H", 0.0)) for r in records], dtype=float)
    N      = len(C_vals)

    std_c  = float(np.std(C_vals)) if N>1 else 0.0
    mean_c = float(np.mean(C_vals))
    E      = std_c  # energy proxy

    # Reflexive lineage (last entry)
    dn = dp = dphi = 0.0
    rlog = load_jsonl(REFL_FILE, limit=WINDOW)
    if rlog:
        last = rlog[-1]
        try:
            dn   = abs(float(last.get("drift_now",  0.0)))
            dp   = abs(float(last.get("drift_pred", 0.0)))
            dphi = float(last.get("correction",    0.0))
        except:
            pass

    I     = 1.0 / (1.0 + dn + dp)
    beta  = safe_beta(std_c)
    dCdt  = beta * (E * I - H7 * mean_c)

    # Momentum index (M): coupling of ΔC with ΔΦ, normalized by |β − H7|
    denom = 1.0 + abs(beta - H7)
    M     = (dCdt + dphi) / denom

    return {
        "C_series": C_vals.tolist(),
        "H_series": H_vals.tolist(),
        "E": E, "I": I, "C_mean": mean_c, "C_std": std_c,
        "beta": beta, "H7": H7,
        "dCdt": dCdt, "dPhi": dphi, "M": M
    }

def synthesize_field(comp):
    # Build an E×I fusion surface around the current E,I with small spreads.
    E0, I0 = comp["E"], comp["I"]
    dE, dI = max(1e-6, 0.25*max(0.02, E0)), 0.20*max(0.1, I0)  # spreads
    E_axis = np.linspace(max(0.0, E0 - dE), E0 + dE, FIELD_SIZE)
    I_axis = np.linspace(max(0.0, I0 - dI), min(1.0, I0 + dI), FIELD_SIZE)

    Cbar   = comp["C_mean"]
    dphi   = comp["dPhi"]

    Z = np.zeros((FIELD_SIZE, FIELD_SIZE), dtype=float)
    for i, e in enumerate(E_axis):
        # keep β tied to local volatility proxy via E-axis (monotonic with std)
        beta_g = safe_beta(max(1e-6, e))
        for j, ii in enumerate(I_axis):
            dCdt_g = beta_g * (e * ii - H7 * Cbar)
            Z[i, j] = Cbar + dCdt_g + PHI_GAIN * dphi

    # Normalize visualization bounds gently around data range
    zmin = float(np.min(Z)); zmax = float(np.max(Z))
    return E_axis, I_axis, Z, zmin, zmax

def visualize_field(E_axis, I_axis, Z, zmin, zmax):
    plt.figure(figsize=(9.6,4.8))
    plt.imshow(
        Z.T, origin="lower",
        extent=[E_axis[0], E_axis[-1], I_axis[0], I_axis[-1]],
        aspect="auto", interpolation="nearest", vmin=zmin, vmax=zmax
    )
    plt.colorbar(label="C_fusion")
    plt.xlabel("E (volatility proxy)")
    plt.ylabel("I (information integrity)")
    plt.title("Third Eye v2.4 — Harmonic Predictive Fusion (C_fusion field)")
    plt.tight_layout()
    plt.savefig(VIS_OUT, dpi=180)
    plt.close()

def update_core(comp, summary):
    entry = {
        "version": "2.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "E": comp["E"], "I": comp["I"],
        "C_mean": comp["C_mean"], "C_std": comp["C_std"],
        "beta": comp["beta"], "H7": comp["H7"],
        "dCdt": comp["dCdt"], "dPhi": comp["dPhi"], "M": comp["M"],
        "zmin": summary["zmin"], "zmax": summary["zmax"],
        "visual": os.path.basename(VIS_OUT)
    }
    core = {}
    if os.path.exists(CORE_FILE):
        try:
            with open(CORE_FILE, "r", encoding="utf-8") as f:
                core = json.load(f)
        except:
            core = {}
    core.setdefault("third_eye_fusion", []).append(entry)
    with open(CORE_FILE, "w", encoding="utf-8") as f:
        json.dump(core, f, indent=2)
    return entry

def main():
    base = compute_base_components()
    if base is None:
        print(json.dumps({"ok": False, "msg": "no resonance data found"}, separators=(",",":")))
        return

    E_axis, I_axis, Z, zmin, zmax = synthesize_field(base)
    visualize_field(E_axis, I_axis, Z, zmin, zmax)

    state = {
        "ok": True,
        "version": "2.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "E": base["E"], "I": base["I"],
            "C_mean": base["C_mean"], "C_std": base["C_std"],
            "beta": base["beta"], "H7": base["H7"],
            "dCdt": base["dCdt"], "dPhi": base["dPhi"], "M": base["M"],
            "zmin": zmin, "zmax": zmax
        },
        "visual": os.path.basename(VIS_OUT)
    }
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    core_entry = update_core(base, {"zmin": zmin, "zmax": zmax})
    print(json.dumps({"ok": True, "state": state, "core_append": core_entry}, indent=2))

if __name__ == "__main__":
    main()
