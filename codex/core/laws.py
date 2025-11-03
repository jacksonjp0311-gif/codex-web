"""
codex.core.laws
v0.6 — Seven Quantum Laws integration for The Codex Project.

This module encodes the seven quantum laws as symbolic rule objects and exposes:
- LAW_DEFINITIONS: list of law metadata
- evaluate_payload(payload): returns a normalized score (0..1) and diagnostics
- summary(): human-readable summary for quick checks

Design notes:
- Laws are modeled as small evaluators which accept an input payload (dict-like) and
  return influence values. These are intentionally lightweight so you can call them
  from your orchestrator or gate system (Python).
- Extend/replace any law function with your mathematical formulation.
"""
from typing import Dict, Any, List, Tuple
import math
import json
import time

# Seven quantum laws (symbolic representation + evaluator stub)
LAW_DEFINITIONS = [
    {"id": 1, "name": "Law of Resonant Equilibrium", "symbol": "L1"},
    {"id": 2, "name": "Law of Dual Expansion", "symbol": "L2"},
    {"id": 3, "name": "Law of Harmonic Compression", "symbol": "L3"},
    {"id": 4, "name": "Law of Triadic Reflection", "symbol": "L4"},
    {"id": 5, "name": "Law of Energetic Reciprocity", "symbol": "L5"},
    {"id": 6, "name": "Law of Symbolic Coherence", "symbol": "L6"},
    {"id": 7, "name": "Law of Conscious Unification", "symbol": "L7"},
]

# Example core evaluators for each law.
# Replace these stubs with your formal Codex math (lotus/torus operators, spectral couplings, etc.)
def law_resonant_equilibrium(payload: Dict[str, Any]) -> float:
    # expects payload to include numeric fields; fallback to heuristic
    x = float(payload.get("energy", 1.0))
    y = float(payload.get("information", 1.0))
    val = 1.0 / (1.0 + abs(x - y))
    return max(0.0, min(1.0, val))

def law_dual_expansion(payload: Dict[str, Any]) -> float:
    a = float(payload.get("expansion_factor", 1.0))
    return math.tanh(a / 2.0)

def law_harmonic_compression(payload: Dict[str, Any]) -> float:
    h = float(payload.get("compression", 0.5))
    return 1.0 - math.exp(-h)

def law_triadic_reflection(payload: Dict[str, Any]) -> float:
    e = float(payload.get("energy", 1.0))
    i = float(payload.get("information", 1.0))
    c = float(payload.get("consciousness", 1.0))
    # triadic coherence heuristic (normalize then multiply)
    vals = [e, i, c]
    norm = [v / (sum(vals) + 1e-9) for v in vals]
    return max(0.0, min(1.0, norm[0] * norm[1] * norm[2] * 27.0))  # scaled

def law_energetic_reciprocity(payload: Dict[str, Any]) -> float:
    p = float(payload.get("reciprocity", 1.0))
    return (p % 1.0)

def law_symbolic_coherence(payload: Dict[str, Any]) -> float:
    s = str(payload.get("symbolic_pattern", ""))
    # crude pattern score: longer patterns -> higher score, but bounded
    score = min(1.0, len(s) / 32.0)
    return score

def law_conscious_unification(payload: Dict[str, Any]) -> float:
    # measure "alignment" between numeric anchors
    anchors = payload.get("anchors", {})
    if not isinstance(anchors, dict) or not anchors:
        return 0.5
    vals = [float(v) for v in anchors.values() if isinstance(v, (int, float, str))]
    if not vals:
        return 0.5
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return max(0.0, min(1.0, 1.0 / (1.0 + var)))

# mapping
LAW_EVALUATORS = [
    law_resonant_equilibrium,
    law_dual_expansion,
    law_harmonic_compression,
    law_triadic_reflection,
    law_energetic_reciprocity,
    law_symbolic_coherence,
    law_conscious_unification,
]

def evaluate_payload(payload: Dict[str, Any]) -> Tuple[float, List[float], Dict[str, Any]]:
    """
    Evaluate the payload against all seven laws.
    Returns: (composite_score, per_law_scores, diagnostics)
    """
    scores = []
    for fn in LAW_EVALUATORS:
        try:
            s = float(fn(payload))
        except Exception:
            s = 0.0
        scores.append(max(0.0, min(1.0, s)))
    # composite: weighted average (equal weights here, can be adjusted)
    composite = sum(scores) / len(scores) if scores else 0.0
    diagnostics = {
        "timestamp": time.time(),
        "per_law": scores,
        "composite": composite,
    }
    return composite, scores, diagnostics

def summary() -> str:
    lines = ["Codex Seven Quantum Laws — Summary (v0.6)"]
    for d in LAW_DEFINITIONS:
        lines.append(f"{d['id']}. {d['name']} ({d['symbol']})")
    return "\\n".join(lines)

# Self-check helper
if __name__ == "__main__":
    test_payload = {
        "energy": 1.2,
        "information": 1.1,
        "consciousness": 0.9,
        "expansion_factor": 1.4,
        "compression": 0.3,
        "symbolic_pattern": "lotus:torus:triad",
        "anchors": {"a": 1.0, "b": 1.05, "c": 0.95}
    }
    comp, per, diag = evaluate_payload(test_payload)
    print(json.dumps({"composite": comp, "per_law": per, "diagnostics": diag}, indent=2))
