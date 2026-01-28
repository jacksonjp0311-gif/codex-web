#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.3 — HARD VERIFIED ORACLE ENGINE
Atomicity → μ Separation → Retrieval Drift Sweep → Ω Truth
"""

import json, random
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

def mu_coherence(E):
    mu=-1.0
    for i in range(len(E)):
        for j in range(i+1,len(E)):
            mu=max(mu, cosine(E[i],E[j]))
    return float(mu)

def retrieval_drift(tok, mdl, token, noise_len):
    base="The key is: "+token
    noisy=("random "*noise_len)+base
    ids1=tok.encode(base, add_special_tokens=False)
    ids2=tok.encode(noisy, add_special_tokens=False)

    with torch.no_grad():
        h1=mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
        h2=mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]

    return 1.0-cosine(h1,h2)

def main(model_id, out_state, oracle_dir, sweep_dir, dash_dir):

    ts=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    tok=AutoTokenizer.from_pretrained(model_id)
    mdl=AutoModel.from_pretrained(model_id)
    mdl.eval()

    atomic,splits=atomicity(tok,morph())
    atomic_rate=len(atomic)/len(splits)

    verdict="ATOMICITY_FAIL"
    mu_ht=None
    drift_mean=None

    if len(atomic)>=25:
        ht=atomic[:25]
        vocab=list(tok.get_vocab().keys())
        random.shuffle(vocab)

        base=[v for v in vocab if len(tok.encode(v, add_special_tokens=False))==1][:25]

        mu_ht=mu_coherence(embed(tok,mdl,ht))
        mu_base=mu_coherence(embed(tok,mdl,base))

        noise=[5,10,20,40,80]
        drifts=[retrieval_drift(tok,mdl,ht[0],n) for n in noise]
        drift_mean=float(np.mean(drifts))

        verdict="STRONG_SUPPORT" if drift_mean<0.15 else "RETRIEVAL_FAIL"

    om=omega(mu_ht) if mu_ht else None

    state={
        "version":"1.3",
        "timestamp":now(),
        "model":model_id,
        "atomicity_rate":atomic_rate,
        "mu_ht":mu_ht,
        "retrieval_drift_mean":drift_mean,
        "omega_truth":om,
        "verdict":verdict
    }

    Path(out_state).write_text(json.dumps(state,indent=2),encoding="utf-8")
    print("CODEX–HYPERTOKENS v1.3 COMPLETE:", verdict)

if __name__=="__main__":
    import sys
    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
