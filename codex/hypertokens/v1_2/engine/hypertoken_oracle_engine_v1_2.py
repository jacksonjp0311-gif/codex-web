#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.2 — ORACLE TRUTH ENGINE
Atomicity Distribution + μ Spectrum + GEO v1.0 + Oracle Dashboards
"""

import os, json, random
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel
import torch


def now():
    return datetime.now(timezone.utc).isoformat()


def cosine(a,b):
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))


def mu_coherence(E):
    n = E.shape[0]
    mu = -1
    for i in range(n):
        for j in range(i+1,n):
            mu = max(mu, cosine(E[i],E[j]))
    return mu


def omega(mu):
    return 1.0/(1.0+abs(mu))


def morph(n=40):
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


def main(model_id, out_state, out_vis):

    os.makedirs(out_vis, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    cands = morph()
    atomic, splits = atomicity(tok, cands)
    atomic_rate = len(atomic)/len(cands)

    # Atomicity histogram
    plt.figure()
    plt.hist(splits, bins=range(1,max(splits)+2), align="left")
    plt.title("Gate-0 Atomicity Distribution")
    plt.xlabel("Tokens per candidate")
    plt.ylabel("Count")
    plt.savefig(os.path.join(out_vis,"atomicity_hist.png"))
    plt.close()

    if len(atomic) < 10:
        verdict = "FALSIFIED_ATOMICITY"
        mu_ht = None
        mu_base = None
        om = None

    else:
        ht = atomic[:20]

        vocab = list(tok.get_vocab().keys())
        random.shuffle(vocab)

        base = []
        for v in vocab:
            if len(tok.encode(v, add_special_tokens=False))==1:
                base.append(v)
            if len(base)>=20:
                break

        E_ht   = embed(tok, mdl, ht)
        E_base = embed(tok, mdl, base)

        mu_ht   = mu_coherence(E_ht)
        mu_base = mu_coherence(E_base)

        om = omega(mu_ht)

        verdict = "SUPPORTED_GO" if mu_ht < 0.3*mu_base else "FALSIFIED_ENTANGLED"

        # μ bar chart
        plt.figure()
        plt.bar(["μ_HT","μ_Base"], [mu_ht, mu_base])
        plt.title("Gate-1 μ-Coherence Comparison")
        plt.savefig(os.path.join(out_vis,"mu_comparison.png"))
        plt.close()

        # Ω truth chart
        plt.figure()
        plt.bar(["Ω Truth"], [om])
        plt.ylim(0,1)
        plt.title("GEO v1.0 Truth Geometry")
        plt.savefig(os.path.join(out_vis,"omega_truth.png"))
        plt.close()

    # Verdict card
    plt.figure(figsize=(7,3))
    plt.text(0.5,0.5, verdict, fontsize=22,
             ha="center", va="center")
    plt.axis("off")
    plt.title("CODEX ORACLE VERDICT")
    plt.savefig(os.path.join(out_vis,"verdict_card.png"))
    plt.close()

    state = {
        "timestamp": now(),
        "model": model_id,
        "atomicity_rate": atomic_rate,
        "mu_ht": mu_ht,
        "mu_baseline": mu_base,
        "omega_truth": om,
        "verdict": verdict
    }

    with open(out_state,"w") as f:
        json.dump(state,f,indent=2)

    print("CODEX–HYPERTOKENS v1.2 COMPLETE")
    print("VERDICT =", verdict)


if __name__=="__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3])
