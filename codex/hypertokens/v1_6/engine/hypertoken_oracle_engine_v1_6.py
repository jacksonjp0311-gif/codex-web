#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.6 — FULL ORACLE ENGINE

Outputs:
- state.json
- atomicity_hist.png
- drift_sweep.png
- dashboard.html
"""

import json, random, sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import torch
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def cosine(a,b):
    return float((a@b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))

def emit(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2),encoding="utf-8")

def main(model_id, out_state, out_vis, out_dash):

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    arch = str(type(mdl)).split(".")[-1]

    # ───────── Gate-0 Atomicity ─────────
    cands = [f"HTAG{k:04d}" for k in range(1,120)]
    splits = [len(tok.encode(c,add_special_tokens=False)) for c in cands]
    atomic = [c for c,s in zip(cands,splits) if s==1]

    atomic_rate = len(atomic)/len(cands)

    # Plot atomicity histogram
    plt.figure()
    plt.hist(splits, bins=6)
    plt.title("Gate-0 Atomicity Distribution")
    plt.xlabel("Token Splits")
    plt.ylabel("Count")
    atomic_png = Path(out_vis)/"atomicity_histogram.png"
    plt.savefig(atomic_png)

    verdict="ATOMICITY_FAIL"
    mu_sep=None
    drift_curve=None

    if len(atomic) >= 20:

        ht = atomic[:20]

        vocab = list(tok.get_vocab().keys())
        random.shuffle(vocab)
        base=[v for v in vocab if len(tok.encode(v,add_special_tokens=False))==1][:20]

        emb = mdl.get_input_embeddings()

        def E(tokens):
            ids=[tok.encode(t,add_special_tokens=False)[0] for t in tokens]
            with torch.no_grad():
                return emb(torch.tensor(ids)).cpu().numpy()

        def mu(E):
            m=-1
            for i in range(len(E)):
                for j in range(i+1,len(E)):
                    m=max(m, cosine(E[i],E[j]))
            return float(m)

        mu_ht   = mu(E(ht))
        mu_base = mu(E(base))
        mu_sep  = mu_ht/(mu_base+1e-9)

        # ───────── Gate-2 Drift Sweep ─────────
        noise=[0,5,10,20,40,80]
        drift=[]
        token=ht[0]

        for n in noise:
            p1="Key: "+token
            p2=("random "*n)+p1

            ids1=tok.encode(p1,add_special_tokens=False)
            ids2=tok.encode(p2,add_special_tokens=False)

            with torch.no_grad():
                h1=mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
                h2=mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]

            drift.append(1.0-cosine(h1,h2))

        drift_curve=drift

        verdict="STRONG_SUPPORT" if max(drift)<0.15 else "DRIFT_FAIL"

        plt.figure()
        plt.plot(noise,drift)
        plt.title("Gate-2 Retrieval Drift Sweep")
        plt.xlabel("Noise Tokens")
        plt.ylabel("Drift (1-cos)")
        drift_png = Path(out_vis)/"drift_sweep.png"
        plt.savefig(drift_png)

    # ───────── State Seal ─────────
    state={
        "version":"1.6",
        "timestamp":now(),
        "model":model_id,
        "architecture":arch,
        "atomicity_rate":atomic_rate,
        "mu_separation":mu_sep,
        "drift_curve":drift_curve,
        "verdict":verdict
    }

    emit(out_state,state)

    # ───────── Dashboard ─────────
    html=f"""
    <html><body style='font-family:monospace;background:black;color:#00ffcc'>
    <h1>CODEX–HYPERTOKENS v1.6 ORACLE</h1>
    <pre>{json.dumps(state,indent=2)}</pre>
    <h2>Atomicity Histogram</h2>
    <img src='../visuals/atomicity_histogram.png' width='600'>
    <h2>Drift Sweep</h2>
    <img src='../visuals/drift_sweep.png' width='600'>
    </body></html>
    """
    Path(out_dash).write_text(html,encoding="utf-8")

    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]))
