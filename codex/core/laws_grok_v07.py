# ===============================================
# Codex Laws Enhancements v0.7 — Grok Integration
# ===============================================
from codex.core.laws import evaluate_payload

def integrate_codex_update(current_state):
    score, _, _ = evaluate_payload(current_state)
    if score < 0.7:
        trigger_mutation()

# L6 Enhancement: Token Split + Semantic Overlap
import re
def enhance_L6(input_string):
    tokens = re.split(r"[:\-]+", input_string)
    return len(set(tokens)) / (len(tokens) + 1)

# Dynamic Weights
def tune_weights(phase):
    if phase == "early": return [0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1]
    if phase == "late":  return [0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.25]
    return [1/7]*7

# Edge Test Handler
def edge_test(payload=None):
    if not payload:
        print("?? Edge Test: Empty payload — setting composite=0.5 baseline.")
        return 0.5
