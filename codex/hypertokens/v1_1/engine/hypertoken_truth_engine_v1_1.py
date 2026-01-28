#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.1 — RETRIEVAL DRIFT + AUTOHEAL TRUTH ENGINE
Gate-0 Atomicity
Gate-1 μ Separation
Gate-2 Retrieval Drift Stability
"""

import sys, json, random, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
import torch

H7 = 0.70

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def cosine(a,b):
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))

def omega(x):
    return 1.0/(1.0+abs(x))

def mu_coherence(E):
    mu = -1.0
    for i in range(len(E)):
        for j in range(i+1,len(E)):
            mu = max(mu, cosine(E[i],E[j]))
    return float(mu)

def morph(n=60):
    return [f"HTAG{k:04d}" for k in range(1,n+1)]

def atomicity(tok, cands):
    splits, atomic = [], []
    for c in cands:
        ids = tok.encode(c, add_special_tokens=False)
        splits.append(len(ids))
        if len(ids)==1:
            atomic.append(c)
    return atomic, splits

def embed(tok, mdl, toks):
    layer = mdl.get_input_embeddings()
    ids = [tok.encode(x, add_special_tokens=False)[0] for x in toks]
    with torch.no_grad():
        return layer(torch.tensor(ids)).cpu().numpy()

def retrieval_probe(tok, mdl, anchor_tokens):
    """
    Gate-2: Retrieval Drift under noise context.
    Measures how stable anchor token meaning is under perturbation.
    """
    base_prompt = "The key is: "
    noisy = " ".join(["random"]*50)

    drift_scores = []
    for a in anchor_tokens[:5]:

        p1 = base_prompt + a
        p2 = noisy + " " + base_prompt + a

        ids1 = tok.encode(p1, add_special_tokens=False)
        ids2 = tok.encode(p2, add_special_tokens=False)

        with torch.no_grad():
            h1 = mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
            h2 = mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]

        drift = 1.0 - cosine(h1,h2)
        drift_scores.append(drift)

    return float(np.mean(drift_scores))

def main(root, state_d, vis_d, ledger_d, logs_d, model_id):

    from transformers import AutoTokenizer, AutoModel

    root = Path(root)
    state_d  = Path(state_d)
    vis_d    = Path(vis_d)
    ledger_d = Path(ledger_d)
    logs_d   = Path(logs_d)

    for d in (state_d, vis_d, ledger_d, logs_d):
        d.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    # Gate-0 Atomicity
    cands = morph()
    atomic, splits = atomicity(tok, cands)
    atomic_rate = len(atomic)/len(cands)

    if len(atomic) < 10:
        verdict = "ATOMICITY_FAIL"
        mu_ht = None
        mu_base = None
        retrieval_drift = None

    else:
        ht = atomic[:25]

        vocab = list(tok.get_vocab().keys())
        random.shuffle(vocab)

        base = []
        for v in vocab:
            if len(tok.encode(v, add_special_tokens=False))==1:
                base.append(v)
            if len(base)>=25:
                break

        E_ht   = embed(tok, mdl, ht)
        E_base = embed(tok, mdl, base)

        mu_ht   = mu_coherence(E_ht)
        mu_base = mu_coherence(E_base)

        retrieval_drift = retrieval_probe(tok, mdl, ht)

        if mu_ht >= 0.3*mu_base:
            verdict = "SEPARATION_FAIL"
        elif retrieval_drift > 0.15:
            verdict = "RETRIEVAL_FAIL"
        else:
            verdict = "STRONG_SUPPORT"

    om = omega(mu_ht) if mu_ht is not None else None

    # State JSON
    state_path = state_d / f"hypertoken_state_{ts}.json"
    state = {
        "protocol": "CodexHypertokensTruthGate",
        "version": "1.1",
        "timestamp": now_iso(),
        "model": model_id,
        "atomicity_rate": atomic_rate,
        "mu_ht": mu_ht,
        "mu_baseline": mu_base,
        "retrieval_drift": retrieval_drift,
        "omega_truth": om,
        "verdict": verdict
    }

    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # Ledger append
    ledger_path = ledger_d / "hypertoken_ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(state) + "\n")

    print("CODEX–HYPERTOKENS v1.1 COMPLETE")
    print("VERDICT =", verdict)

    return 0

if __name__=="__main__":
    _, root, state, vis, led, logs, model_id = sys.argv[:7]
    sys.exit(main(root, state, vis, led, logs, model_id))
