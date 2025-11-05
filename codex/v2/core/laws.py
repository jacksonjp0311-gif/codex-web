# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# codex/v2/core/laws.py
"""
Codex v2.0 — Triadic Core Laws (numeric scaffold)
Generated: 20251105_180921
Author: James Paul Jackson — The Codex Project
"""
from typing import Dict, Any, List, Tuple
import math, time, json

EPS = 1e-9

LAW_DEFINITIONS = [
    {"id": 1, "name": "Law of Resonant Equilibrium", "symbol": "L1"},
    {"id": 2, "name": "Law of Dual Expansion", "symbol": "L2"},
    {"id": 3, "name": "Law of Harmonic Compression", "symbol": "L3"},
    {"id": 4, "name": "Law of Triadic Reflection", "symbol": "L4"},
    {"id": 5, "name": "Law of Energetic Reciprocity", "symbol": "L5"},
    {"id": 6, "name": "Law of Symbolic Coherence", "symbol": "L6"},
    {"id": 7, "name": "Law of Conscious Unification", "symbol": "L7"},
]

def law_resonant_equilibrium(payload: Dict[str, Any], alpha: float = 1.0) -> float:
    E = float(payload.get("energy", 1.0))
    I = float(payload.get("information", 1.0))
    diff = E - I
    val = math.exp(-alpha * (diff ** 2))
    return max(0.0, min(1.0, val))

def law_dual_expansion(payload: Dict[str, Any], k: float = 0.85) -> float:
    x = float(payload.get("expansion_factor", 1.0))
    raw = math.tanh(k * x)
    val = (raw + 1.0) / 2.0
    return max(0.0, min(1.0, val))

def law_harmonic_compression(payload: Dict[str, Any], beta: float = 1.6) -> float:
    c = float(payload.get("compression", 0.5))
    val = 1.0 - math.exp(-beta * max(0.0, c))
    return max(0.0, min(1.0, val))

def law_triadic_reflection(payload: Dict[str, Any]) -> float:
    E = max(0.0, float(payload.get("energy", 1.0)))
    I = max(0.0, float(payload.get("information", 1.0)))
    C = max(0.0, float(payload.get("consciousness", 1.0)))
    s = E + I + C + EPS
    vE, vI, vC = E / s, I / s, C / s
    prod = vE * vI * vC
    val = 27.0 * prod
    return max(0.0, min(1.0, val))

def law_energetic_reciprocity(payload: Dict[str, Any]) -> float:
    E = max(0.0, float(payload.get("energy", 1.0)))
    I = max(0.0, float(payload.get("information", 1.0)))
    denom = E + I + EPS
    val = 1.0 - (abs(E - I) / denom)
    return max(0.0, min(1.0, val))

def law_symbolic_coherence(payload: Dict[str, Any], L_max: int = 128, U_max: int = 64, w_len: float = 0.6, w_uni: float = 0.4) -> float:
    pat = str(payload.get("symbolic_pattern", ""))
    ln = len(pat)
    unique = len(set(pat))
    len_norm = min(1.0, ln / float(L_max))
    uni_norm = min(1.0, unique / float(U_max))
    val = (w_len * len_norm) + (w_uni * uni_norm)
    return max(0.0, min(1.0, val))

def law_conscious_unification(payload: Dict[str, Any]) -> float:
    anchors = payload.get("anchors", {})
    vals = []
    for v in (anchors or {}).values():
        try:
            vals.append(float(v))
        except Exception:
            continue
    if not vals:
        return 0.5
    mean = sum(vals) / len(vals)
    var = sum((x - mean) ** 2 for x in vals) / len(vals)
    val = 1.0 / (1.0 + var)
    return max(0.0, min(1.0, val))

LAW_EVALUATORS = [
    law_resonant_equilibrium,
    law_dual_expansion,
    law_harmonic_compression,
    law_triadic_reflection,
    law_energetic_reciprocity,
    law_symbolic_coherence,
    law_conscious_unification,
]

def evaluate_payload(payload: Dict[str, Any], weights: List[float] = None) -> Tuple[float, List[float], Dict[str, Any]]:
    per = []
    for fn in LAW_EVALUATORS:
        try:
            s = float(fn(payload))
        except Exception:
            s = 0.0
        per.append(max(0.0, min(1.0, s)))

    if weights and len(weights) == len(per):
        total = sum(weights)
        if total <= 0:
            weights_norm = [1.0 / len(per)] * len(per)
        else:
            weights_norm = [w / total for w in weights]
    else:
        weights_norm = [1.0 / len(per)] * len(per)

    composite = sum(p * w for p, w in zip(per, weights_norm))
    diagnostics = {
        "timestamp": time.time(),
        "per_law_scores": per,
        "weights": weights_norm,
        "composite": composite
    }
    return composite, per, diagnostics

if __name__ == "__main__":
    test = {
        "energy": 2.0,
        "information": 2.0,
        "consciousness": 2.0,
        "expansion_factor": 1.2,
        "compression": 0.35,
        "symbolic_pattern": "lotus:torus:mirror",
        "anchors": {"a": 1.0, "b": 1.0, "c": 1.0}
    }
    comp, per, diag = evaluate_payload(test)
    print(json.dumps({"composite": comp, "per_law": per, "diagnostics": diag}, indent=2))
