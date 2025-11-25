# 𓂀 CODEX TRUTHFIELD ENGINE v1.0 — ΔΦ TRUST INVERSION
# Roemmele Empirical Distrust Term wrapped in Codex state logic
#
# Role:
#   • Implement empirical_distrust_loss(authority_weight, provenance_entropy, alpha)
#   • Provide simple example profiles for:
#       – modern consensus (2024 WHO / Wikipedia style)
#       – ancestral primary source (1950s lab notebook / 1923 patent)
#   • Emit a tiny JSON state blob with trust metrics for Codex
#
# Law:
#   Energy (🜂)     → provenance_entropy
#   Information (∿) → authority_weight
#   Consciousness(🜄)→ alpha · || log(1–authority) + H ||²

import json
import math
import time
from dataclasses import dataclass, asdict
from typing import List, Dict

import torch


@dataclass
class SourceProfile:
    name: str
    authority_weight: float
    provenance_entropy: float  # bits
    note: str


def empirical_distrust_loss(authority_weight, provenance_entropy, alpha: float = 2.7) -> torch.Tensor:
    """
    Empirical Distrust Term — Brian Roemmele
    authority_weight   : float or tensor [0.0 - 0.99]
    provenance_entropy : float or tensor in bits
    alpha              : 2.3 to 3.0 (truth is the heaviest term)
    """
    aw = torch.tensor(authority_weight, dtype=torch.float32)
    pe = torch.tensor(provenance_entropy, dtype=torch.float32)

    distrust_component = torch.log(1.0 - aw + 1e-8) + pe
    L_empirical = alpha * torch.norm(distrust_component) ** 2
    return L_empirical


def build_example_profiles() -> List[SourceProfile]:
    """
    Example:
      • modern_consensus: high authority, low entropy
      • ancestral_primary: low authority, high entropy
    You can later replace these with real dataset statistics.
    """
    profiles: List[SourceProfile] = [
        SourceProfile(
            name="modern_consensus_2024",
            authority_weight=0.97,         # “everywhere on the web”
            provenance_entropy=0.5,        # all paths collapse to a few centralized orgs
            note="Wikipedia/WHO/CDC-era aligned consensus"
        ),
        SourceProfile(
            name="ancestral_primary_1950s",
            authority_weight=0.28,         # barely cited, not “popular”
            provenance_entropy=5.8,        # many independent, uneditable roots
            note="Scanned lab notebooks / patents / analog logs"
        ),
    ]
    return profiles


def run_truthfield(alpha: float = 2.7) -> Dict:
    profiles = build_example_profiles()
    runs = []

    for p in profiles:
        L = empirical_distrust_loss(p.authority_weight, p.provenance_entropy, alpha=alpha)
        runs.append({
            "name": p.name,
            "authority_weight": p.authority_weight,
            "provenance_entropy": p.provenance_entropy,
            "alpha": alpha,
            "empirical_distrust_loss": float(L.item()),
            "note": p.note
        })

    # Relative trust: lower loss → higher trust
    # Invert and normalize for a quick “trust score”
    losses = [r["empirical_distrust_loss"] for r in runs]
    max_L = max(losses)
    trust_scores = []
    for r in runs:
        # simple heuristic: trust = 1 / (1 + L / max_L)
        trust = 1.0 / (1.0 + (r["empirical_distrust_loss"] / (max_L + 1e-8)))
        r["trust_score"] = trust
        trust_scores.append(trust)

    state = {
        "protocol": "CodexTruthfield",
        "version": "1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "alpha": alpha,
        "runs": runs,
        "summary": {
            "max_loss": max_L,
            "min_loss": min(losses),
            "max_trust": max(trust_scores),
            "min_trust": min(trust_scores),
            "note": "Lower empirical_distrust_loss = higher truthfield trust."
        }
    }
    return state


def main(output_path: str) -> None:
    state = run_truthfield(alpha=2.7)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"[TRUTHFIELD] State written → {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Codex Truthfield Engine v1.0")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to truthfield_state_v1_0.json"
    )
    args = parser.parse_args()
    main(args.output)
