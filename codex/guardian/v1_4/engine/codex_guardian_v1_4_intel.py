# ======================================================================
# 𓂀 CODEX GUARDIAN v1.4 — TRIADIC SENTINEL INTELLIGENCE ENGINE
# ======================================================================
# Role      : ΔΦ Drift Prediction • Ward Stability Forecast • Security Oracle
# Upstream  : v1.2 Oracle + v1.3 Dashboard
# Protocol  : Triadic Ward Protocol v1.4
# ======================================================================

import json
from pathlib import Path
from typing import Dict, Any

def load_v12_state(root: Path) -> Dict[str, Any]:
    p = root / "codex" / "guardian" / "v1_2" / "state" / "codex_guardian_v1_2_oracle_state.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"metrics": {"drift": 0.5, "anomaly_index": 0.5, "ward_complexity": 0.5}}

def load_v13_state(root: Path) -> Dict[str, Any]:
    p = root / "codex" / "guardian" / "v1_3" / "state" / "codex_guardian_v1_3_dashboard.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"oracle_state": {"metrics": {"drift": 0.5, "anomaly_index": 0.5, "ward_complexity": 0.5}}}

def predict_drift(d12: float, d13: float) -> float:
    delta = d13 - d12
    return max(0.0, min(1.0, d13 + 0.5 * delta))

def predict_anomaly(a12: float, a13: float) -> float:
    delta = a13 - a12
    return max(0.0, min(1.0, a13 + 0.6 * delta))

def build_glyph(drift_pred: float, anomaly_pred: float) -> Dict[str, Any]:
    return {
        "protocol": "CodexTriadicGlyph",
        "version": "1.1",
        "triad": {
            "energy": {
                "glyph": "🛡️",
                "label": "Drift-Shield",
                "value": round(1 - drift_pred, 4),
                "units": "stability"
            },
            "information": {
                "glyph": "∿",
                "label": "ΔΦ-Vector",
                "value": round(drift_pred, 4),
                "units": "phase"
            },
            "consciousness": {
                "glyph": "🜄",
                "label": "Harmony",
                "value": round(1 - anomaly_pred, 4),
                "units": "coherence"
            },
        },
        "harmony": {
            "glyph": "♁",
            "value": round((1 - drift_pred) * (1 - anomaly_pred), 4),
            "profile": "ward_integrity"
        }
    }

def main():
    here = Path(__file__).resolve()
    root = here.parents[4]

    v12 = load_v12_state(root)
    v13 = load_v13_state(root)

    m12 = v12.get("metrics", {})
    m13 = v13.get("oracle_state", {}).get("metrics", {})

    d12 = float(m12.get("drift", 0.5))
    d13 = float(m13.get("drift", 0.5))

    a12 = float(m12.get("anomaly_index", 0.5))
    a13 = float(m13.get("anomaly_index", 0.5))

    drift_pred = predict_drift(d12, d13)
    anomaly_pred = predict_anomaly(a12, a13)

    glyph = build_glyph(drift_pred, anomaly_pred)

    intel = {
        "protocol": "GUARDIAN_INTEL_v1_4",
        "drift_prediction": drift_pred,
        "anomaly_prediction": anomaly_pred,
        "triadic_glyph": glyph,
    }

    state_dir = here.parents[1] / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    (state_dir / "codex_guardian_v1_4_intel.json").write_text(
        json.dumps(intel, indent=2), encoding="utf-8"
    )

    txt = []
    txt.append("╔═══════════════════════════════════════╗")
    txt.append("║ 𓂀  GUARDIAN v1.4 — INTEL PANEL        ║")
    txt.append("╚═══════════════════════════════════════╝")
    txt.append(f" Drift Prediction     : {drift_pred:.4f}")
    txt.append(f" Anomaly Prediction   : {anomaly_pred:.4f}")
    txt.append("")
    txt.append(" Triadic Ward Glyph:")
    txt.append(f"   🛡️  Stability     : {glyph['triad']['energy']['value']}")
    txt.append(f"   ∿   ΔΦ Vector     : {glyph['triad']['information']['value']}")
    txt.append(f"   🜄  Harmony       : {glyph['triad']['consciousness']['value']}")
    txt.append(f"   ♁   Integrity     : {glyph['harmony']['value']}")
    txt.append("")
    txt.append(" Notes:")
    txt.append("   • Predictive model based on v1.2 + v1.3")
    txt.append("   • Downstream: Heartbeat, Bridge, Security Mesh")

    (state_dir / "codex_guardian_v1_4_intel.txt").write_text(
        "\n".join(txt), encoding="utf-8"
    )

if __name__ == "__main__":
    main()
# ======================================================================
# END
# ======================================================================
