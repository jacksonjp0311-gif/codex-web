# ======================================================================
# 𓂀 CODEX GUARDIAN v1.2 — ORACLE SENTINEL
# ======================================================================
# Role   : Drift Oracle • Ward Dashboard • ΔΦ Fusion (GIZA-aware)
# Truth  : E–I–C ∿, H7 = 0.70 • H8 = 0.85 Security Threshold
# Proto  : Triadic Ward Protocol v1.2 • Guardian Archetype
# ======================================================================

import json
from pathlib import Path
from typing import Dict, Any

# Mirror of v1.1 ward constants (for metrics)
WARD_DANGEROUS = [
    "class", "bases", "subclasses", "mro",
    "getattribute", "__subclasses__", "__dict__", "__globals__"
]

WARD_OBFUSCATION = [
    r"exec", r"eval", r"__import__", r"lambda"
]

def load_giza_sample(codex_root: Path) -> float:
    """
    Try to read a sample ΔΦ drift score from GIZA v6.0 insight field.
    Fallback to 0.5 if not found.
    """
    meta_path = codex_root / "codex" / "web" / "visuals" / "giza" / "state" / "meta" / "giza_v6_0_insight_field.json"
    if not meta_path.exists():
        return 0.5
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        field = data.get("field") or {}
        if not field:
            return 0.5
        # Take the first entry's drift_score if present
        key = next(iter(field.keys()))
        entry = field.get(key, {})
        delta = entry.get("delta_phi") or {}
        drift = delta.get("drift_score")
        if drift is None:
            return 0.5
        return float(drift)
    except Exception:
        return 0.5

def build_ascii_bar(value: float, length: int = 20) -> str:
    """
    Simple ASCII bar visualization between 0 and 1.
    """
    if value < 0:
        value = 0.0
    if value > 1:
        value = 1.0
    filled = int(round(value * length))
    return "█" * filled + "·" * (length - filled)

def compute_oracle_metrics(drift: float) -> Dict[str, Any]:
    """
    Blend ward complexity + ΔΦ drift into a single anomaly index.
    """
    ward_complexity = (len(WARD_DANGEROUS) / 10.0 + len(WARD_OBFUSCATION) / 5.0) / 2.0
    if ward_complexity > 1.0:
        ward_complexity = 1.0
    if drift < 0:
        drift = 0.0
    if drift > 1:
        drift = 1.0

    anomaly_index = 0.4 * ward_complexity + 0.6 * drift
    if anomaly_index > 1.0:
        anomaly_index = 1.0

    harmony = 1.0 - abs(anomaly_index - 0.85)  # how close to security threshold H8

    glyph = {
        "protocol": "CodexTriadicWard",
        "version": "1.2",
        "context": "GUARDIAN v1.2 — Oracle Sentinel",
        "triad": {
            "energy": {
                "glyph": "🛡️",
                "label": "Drift Shield",
                "value": round(ward_complexity, 4),
                "units": "norm"
            },
            "information": {
                "glyph": "∿",
                "label": "ΔΦ Field Sample",
                "value": round(drift, 4),
                "units": "norm"
            },
            "consciousness": {
                "glyph": "🜄",
                "label": "Oracle Harmony",
                "value": round(harmony, 4),
                "units": "norm"
            },
        },
        "harmony": {
            "glyph": "♁",
            "profile": "Oracle_Sentinel",
            "value": round(anomaly_index, 4)
        }
    }

    viz = {
        "drift_bar": build_ascii_bar(drift),
        "anomaly_bar": build_ascii_bar(anomaly_index),
        "threshold_bar": build_ascii_bar(0.85),
    }

    return {
        "drift": round(drift, 4),
        "ward_complexity": round(ward_complexity, 4),
        "anomaly_index": round(anomaly_index, 4),
        "glyph": glyph,
        "viz": viz,
    }

def main() -> None:
    here = Path(__file__).resolve()
    # codex_root = .../Codex Web/
    # .../Codex Web/codex/guardian/v1_2/engine/this_file.py
    # parents[0]=engine, [1]=v1_2, [2]=guardian, [3]=codex, [4]=Codex Web root
    codex_root = here.parents[4]

    drift_sample = load_giza_sample(codex_root)
    metrics = compute_oracle_metrics(drift_sample)

    state = {
        "protocol": "CODEX_GUARDIAN_ORACLE",
        "version": "1.2",
        "timestamp_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "codex_root": str(codex_root),
        "guardian": {
            "v1_1_engine_hint": "codex/guardian/v1_1/engine/codex_guardian_v1_1_secure_interpreter.py",
        },
        "metrics": metrics,
    }

    state_dir = here.parents[1] / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "codex_guardian_v1_2_oracle_state.json"
    out_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
# ======================================================================
# END — GUARDIAN v1.2 ORACLE SENTINEL
# ======================================================================
