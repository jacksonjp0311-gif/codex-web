#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.7 — ATOM-MINT + μ/DRIFT ORACLE (CANON)

Adds confirmation artifacts:
- env_proof.json
- mint_proof.json
- arch_proof.json
"""

import json, sys, random, platform
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import torch
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")


def cosine(a, b):
    return float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def emit(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")


def main(model_id, out_state, out_vis, out_dash, confirm_dir):

    confirm_dir = Path(confirm_dir)
    confirm_dir.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    arch = str(type(mdl)).split(".")[-1]

    # ───────── Confirmation: ENV PROOF ─────────
    emit(confirm_dir/"env_proof.json",{
        "timestamp": now(),
        "python": sys.version,
        "torch": torch.__version__,
        "platform": platform.platform(),
        "model_id": model_id
    })

    emit(confirm_dir/"arch_proof.json",{
        "architecture": arch,
        "encoder_like": "Bert" in arch or "Encoder" in arch
    })

    # ───────── Gate-0 PRE Atomicity ─────────
    cands = [f"HTAG{k:04d}" for k in range(1,120)]
    splits_pre = [len(tok.encode(c, add_special_tokens=False)) for c in cands]
    atomic_pre = [c for c,s in zip(cands,splits_pre) if s==1]

    plt.figure()
    plt.hist(splits_pre,bins=8)
    plt.title("Gate-0 Atomicity PRE-MINT")
    plt.savefig(Path(out_vis)/"atomicity_pre.png")

    # ───────── Gate-0b ATOM-MINT ─────────
    minted=False
    if len(atomic_pre) < 20:
        tok.add_tokens(cands)
        mdl.resize_token_embeddings(len(tok))
        minted=True

    emit(confirm_dir/"mint_proof.json",{
        "timestamp": now(),
        "minted": minted,
        "added_tokens": len(cands),
        "atomicity_pre": len(atomic_pre)
    })

    # ───────── Gate-0 POST Atomicity ─────────
    splits_post=[len(tok.encode(c,add_special_tokens=False)) for c in cands]
    atomic_post=[c for c,s in zip(cands,splits_post) if s==1]

    plt.figure()
    plt.hist(splits_post,bins=8)
    plt.title("Gate-0 Atomicity POST-MINT")
    plt.savefig(Path(out_vis)/"atomicity_post.png")

    verdict="ATOMICITY_FAIL"
    mu_sep=None
    drift=None

    if len(atomic_post) >= 20:

        ht=atomic_post[:20]
        vocab=list(tok.get_vocab().keys())
        random.shuffle(vocab)
        base=[v for v in vocab if len(tok.encode(v,add_special_tokens=False))==1][:20]

        emb=mdl.get_input_embeddings()

        def E(tokens):
            ids=[tok.encode(t,add_special_tokens=False)[0] for t in tokens]
            with torch.no_grad():
                return emb(torch.tensor(ids)).cpu().numpy()

        def mu(E):
            m=-1
            for i in range(len(E)):
                for j in range(i+1,len(E)):
                    m=max(m,cosine(E[i],E[j]))
            return float(m)

        mu_ht=mu(E(ht))
        mu_base=mu(E(base))
        mu_sep=mu_ht/(mu_base+1e-9)

        # Drift sweep
        noise=[0,5,10,20,40,80]
        drift=[]
        token=ht[0]

        for n in noise:
            p1="Key:"+token
            p2=("random "*n)+p1
            ids1=tok.encode(p1,add_special_tokens=False)
            ids2=tok.encode(p2,add_special_tokens=False)

            with torch.no_grad():
                h1=mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
                h2=mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]

            drift.append(1.0-cosine(h1,h2))

        plt.figure()
        plt.plot(noise,drift)
        plt.title("Gate-2 Retrieval Drift Sweep")
        plt.savefig(Path(out_vis)/"drift_sweep.png")

        verdict="READY_FOR_SWEEPS" if max(drift)<0.15 else "DRIFT_FAIL"

    state={
        "version":"1.7",
        "timestamp":now(),
        "model":model_id,
        "architecture":arch,
        "minted":minted,
        "atomicity_pre":len(atomic_pre),
        "atomicity_post":len(atomic_post),
        "mu_separation":mu_sep,
        "drift_curve":drift,
        "verdict":verdict
    }

    emit(out_state,state)

    html=f"""
    <html><body style='background:black;color:#00ffcc;font-family:monospace'>
    <h1>CODEX–HYPERTOKENS v1.7 ORACLE</h1>
    <pre>{json.dumps(state,indent=2)}</pre>
    <img src='../visuals/atomicity_pre.png' width='600'>
    <img src='../visuals/atomicity_post.png' width='600'>
    <img src='../visuals/drift_sweep.png' width='600'>
    </body></html>
    """

    Path(out_dash).write_text(html,encoding="utf-8")
    return 0


if __name__=="__main__":
    sys.exit(main(
        sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]
    ))
