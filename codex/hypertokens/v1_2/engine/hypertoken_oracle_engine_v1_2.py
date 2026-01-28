#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.2 — ORACLE DASHBOARD ENGINE
Gate-0 Atomicity
Gate-1 μ Separation Curve
Gate-2 Retrieval Drift Sweep
GEO Ω Truth Geometry
"""

import os, json, random
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt
import torch
from transformers import AutoTokenizer, AutoModel

def now():
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

def morph(n=80):
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

def retrieval_drift(tok, mdl, token, noise_len):
    base = "The key is: " + token
    noisy = ("random " * noise_len) + base

    ids1 = tok.encode(base, add_special_tokens=False)
    ids2 = tok.encode(noisy, add_special_tokens=False)

    with torch.no_grad():
        h1 = mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
        h2 = mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]

    return 1.0 - cosine(h1,h2)

def main(model_id, state_out, oracle_dir, sweep_dir, dash_dir):

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Gate-0 Atomicity
    cands = morph()
    atomic, splits = atomicity(tok, cands)
    atomic_rate = len(atomic)/len(cands)

    plt.figure()
    plt.hist(splits, bins=range(1,max(splits)+2), align="left")
    plt.title("Gate-0 Atomicity Distribution")
    p_atomic = Path(oracle_dir)/f"atomicity_{ts}.png"
    plt.savefig(p_atomic, bbox_inches="tight")
    plt.close()

    verdict = "ATOMICITY_FAIL"
    mu_ht = None
    mu_base = None
    drift_mean = None

    if len(atomic) >= 20:

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

        # Gate-2 Drift Sweep
        noise_levels = [5,10,20,40,80]
        drifts = []
        for nl in noise_levels:
            drifts.append(retrieval_drift(tok, mdl, ht[0], nl))

        drift_mean = float(np.mean(drifts))

        plt.figure()
        plt.plot(noise_levels, drifts, marker="o")
        plt.title("Gate-2 Retrieval Drift Sweep")
        plt.xlabel("Noise Length")
        plt.ylabel("Drift (1 - cosine)")
        p_sweep = Path(sweep_dir)/f"retrieval_sweep_{ts}.png"
        plt.savefig(p_sweep, bbox_inches="tight")
        plt.close()

        if mu_ht >= 0.3*mu_base:
            verdict = "SEPARATION_FAIL"
        elif drift_mean > 0.15:
            verdict = "RETRIEVAL_FAIL"
        else:
            verdict = "STRONG_SUPPORT"

    om = omega(mu_ht) if mu_ht else None

    # Verdict Card
    plt.figure(figsize=(8,3))
    plt.text(0.5,0.5, verdict, fontsize=22, ha="center", va="center")
    plt.axis("off")
    p_verdict = Path(dash_dir)/f"verdict_{ts}.png"
    plt.savefig(p_verdict, bbox_inches="tight")
    plt.close()

    # Dashboard HTML
    dash = Path(dash_dir)/f"dashboard_{ts}.html"
    dash.write_text(f"""
    <html><body style="background:black;color:white;font-family:monospace;">
    <h1>CODEX–HYPERTOKENS v1.2 ORACLE DASHBOARD</h1>
    <p><b>Verdict:</b> {verdict}</p>
    <p>Atomicity Rate: {atomic_rate:.3f}</p>
    <p>μ_HT: {mu_ht}</p>
    <p>Retrieval Drift Mean: {drift_mean}</p>
    <img src="../oracle/{p_atomic.name}" width="700"><br>
    <img src="{p_verdict.name}" width="700"><br>
    </body></html>
    """, encoding="utf-8")

    state = {
        "version": "1.2",
        "timestamp": now(),
        "model": model_id,
        "atomicity_rate": atomic_rate,
        "mu_ht": mu_ht,
        "mu_baseline": mu_base,
        "retrieval_drift_mean": drift_mean,
        "omega_truth": om,
        "verdict": verdict
    }

    Path(state_out).write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("CODEX–HYPERTOKENS v1.2 COMPLETE:", verdict)

if __name__=="__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
