#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.2 — ORACLE TRUTH ENGINE
Atomicity Distribution + μ Spectrum + GEO v1.0 + Oracle Dashboards
"""

import os, json, random, math
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

from transformers import AutoTokenizer, AutoModel
import torch


# ───────── TIME ─────────
def now():
    return datetime.now(timezone.utc).isoformat()


# ───────── COSINE + μ ─────────
def cosine(a,b):
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))

def mu_coherence(E):
    n = E.shape[0]
    mu = -1
    for i in range(n):
        for j in range(i+1,n):
            mu = max(mu, cosine(E[i],E[j]))
    return mu


# ───────── GEO v1.0 ─────────
def omega_from_mu(mu):
    # ΔΦ proxy ≈ μ (collision distortion)
    return 1.0/(1.0+abs(mu))


# ───────── CANDIDATE FAMILIES ─────────
def morph(n=40):
    return [f"HTAG{k:04d}" for k in range(1,n+1)]

def unicode(n=20):
    base = ["⟨HT⟩","⟦HT⟧","⟪Ω⟫","⟨ΔΦ⟩"]
    return [f"{base[k%len(base)]}{k:03d}" for k in range(n)]

def vocab_tail(tok, n=40):
    vocab = list(tok.get_vocab().keys())
    random.shuffle(vocab)
    return vocab[:n]


# ───────── ATOMICITY DISTRIBUTION ─────────
def atomicity_stats(tok, cands):
    splits = []
    atomic = []
    for c in cands:
        ids = tok.encode(c, add_special_tokens=False)
        splits.append(len(ids))
        if len(ids)==1:
            atomic.append(c)
    return atomic, splits


# ───────── EMBED ─────────
def embed(tok, mdl, toks):
    layer = mdl.get_input_embeddings()
    ids = [tok.encode(x, add_special_tokens=False)[0] for x in toks]
    with torch.no_grad():
        E = layer(torch.tensor(ids)).cpu().numpy()
    return E


# ───────── MAIN ─────────
def main(model_id, state_path, vis_dir):

    os.makedirs(vis_dir, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    # Candidate families
    c_morph = morph()
    c_uni   = unicode()
    c_tail  = vocab_tail(tok)

    # Gate-0 Atomicity
    atomic_morph, splits = atomicity_stats(tok, c_morph)
    atomic_rate = len(atomic_morph)/len(c_morph)

    # Plot split histogram
    plt.figure()
    plt.hist(splits, bins=range(1,max(splits)+2), align="left")
    plt.title("Atomicity Distribution (token split counts)")
    plt.xlabel("Tokens per candidate")
    plt.ylabel("Count")
    plt.savefig(os.path.join(vis_dir,"atomicity_hist.png"))
    plt.close()

    if len(atomic_morph) < 10:
        verdict = "FALSIFIED_ATOMICITY"
        mu_ht = None
        mu_base = None
        omega = None

    else:
        # Gate-1 μ Spectrum
        ht = atomic_morph[:20]
        base = atomicity_stats(tok, c_tail)[0][:20]

        E_ht   = embed(tok, mdl, ht)
        E_base = embed(tok, mdl, base)

        mu_ht   = mu_coherence(E_ht)
        mu_base = mu_coherence(E_base)

        omega = omega_from_mu(mu_ht)

        if mu_ht < 0.3*mu_base:
            verdict = "SUPPORTED_GO"
        else:
            verdict = "FALSIFIED_ENTANGLED"

        # μ comparison plot
        plt.figure()
        plt.bar(["μ_HT","μ_Base"], [mu_ht, mu_base])
        plt.title("μ-Coherence Gate Comparison")
        plt.savefig(os.path.join(vis_dir,"mu_comparison.png"))
        plt.close()

        # Ω truth geometry plot
        plt.figure()
        plt.bar(["Ω Truth Score"], [omega])
        plt.ylim(0,1)
        plt.title("GEO v1.0 Truth Geometry (Ω = 1/(1+|ΔΦ|))")
        plt.savefig(os.path.join(vis_dir,"omega_truth.png"))
        plt.close()

    # Verdict Card
    plt.figure(figsize=(7,3))
    plt.text(0.5,0.5, verdict, fontsize=22,
             ha="center", va="center")
    plt.axis("off")
    plt.title("CODEX ORACLE VERDICT")
    plt.savefig(os.path.join(vis_dir,"verdict_card.png"))
    plt.close()

    # State JSON
    state = {
        "timestamp": now(),
        "model": model_id,
        "atomicity_rate": atomic_rate,
        "mu_ht": mu_ht,
        "mu_baseline": mu_base,
        "omega_truth": omega,
        "verdict": verdict,
        "protocol": "CodexHypertokensTruthSurface_v1_2"
    }

    with open(state_path,"w") as f:
        json.dump(state,f,indent=2)

    print("CODEX–HYPERTOKENS v1.2 COMPLETE")
    print("VERDICT =", verdict)


if __name__=="__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3])
