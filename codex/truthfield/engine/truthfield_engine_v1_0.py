# 𓂀 CODEX TRUTHFIELD ENGINE v1.0 — ΔΦ TRUST INVERSION
# Roemmele Empirical Distrust Term wrapped in Codex state logic

import json
import time
from dataclasses import dataclass
from typing import List, Dict

import torch


@dataclass
class SourceProfile:
    name: str
    authority_weight: float
    provenance_entropy: float  # bits
    note: str


def empirical_distrust_loss(authority_weight, provenance_entropy, alpha: float = 2.7) -> torch.Tensor:
    \"\"\"Empirical Distrust Term — Brian Roemmele\"\"\"
    aw = torch.tensor(authority_weight, dtype=torch.float32)
    pe = torch.tensor(provenance_entropy, dtype=torch.float32)

    distrust_component = torch.log(1.0 - aw + 1e-8) + pe
    L_empirical = alpha * torch.norm(distrust_component) ** 2
    return L_empirical


def build_example_profiles() -> List[SourceProfile]:
    profiles: List[SourceProfile] = [
        SourceProfile(
            name="modern_consensus_2024",
            authority_weight=0.97,
            provenance_entropy=0.5,
            note="Wikipedia/WHO/CDC-era aligned consensus"
        ),
        SourceProfile(
            name="ancestral_primary_1950s",
            authority_weight=0.28,
            provenance_entropy=5.8,
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

    losses = [r["empirical_distrust_loss"] for r in runs]
    max_L = max(losses)
    trust_scores = []
    for r in runs:
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
