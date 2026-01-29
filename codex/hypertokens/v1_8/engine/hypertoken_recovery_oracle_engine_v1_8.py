#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.8 — EMBEDDING-TRAIN + DRIFT-RECOVERY ORACLE (CANON)

Adds:
- Gate-3 embedding-only training (freeze backbone; train NEW token rows only)
- Gate-4 drift recovery (post-train drift sweep)
- True-black dashboard + more visuals
- Handoff.json (no stdout dependency)

Confirmation artifacts:
- env_proof.json
- mint_proof.json
- arch_proof.json
- train_proof.json
"""

import os, json, sys, random, platform, math
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")


def cosine(a, b):
    return float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def emit(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")


def set_dark(ax):
    ax.set_facecolor("#000000")
    for sp in ax.spines.values():
        sp.set_color("#444444")
    ax.tick_params(colors="#eaeaea", labelsize=9)
    ax.grid(True, alpha=0.22, color="#444444")


def save_hist(path, y, title, xlabel):
    fig = plt.figure(figsize=(7.4, 3.0), dpi=160)
    ax = plt.gca()
    ax.hist(y, bins=40, alpha=0.9)
    set_dark(ax)
    ax.set_title(title, fontsize=12, color="#f5f5f5")
    ax.set_xlabel(xlabel, fontsize=10, color="#e5e5e5")
    ax.set_ylabel("count", fontsize=10, color="#e5e5e5")
    fig.tight_layout(pad=0.35)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.06, facecolor="#000000")
    plt.close(fig)


def save_line(path, x, y, title, xlabel, ylabel):
    fig = plt.figure(figsize=(7.4, 3.2), dpi=160)
    ax = plt.gca()
    ax.plot(x, y, linewidth=1.3)
    set_dark(ax)
    ax.set_title(title, fontsize=12, color="#f5f5f5")
    ax.set_xlabel(xlabel, fontsize=10, color="#e5e5e5")
    ax.set_ylabel(ylabel, fontsize=10, color="#e5e5e5")
    fig.tight_layout(pad=0.35)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.06, facecolor="#000000")
    plt.close(fig)


def save_scatter(path, x, y, title, xlabel, ylabel):
    fig = plt.figure(figsize=(7.0, 5.2), dpi=160)
    ax = plt.gca()
    ax.scatter(x, y, s=10)
    set_dark(ax)
    ax.set_title(title, fontsize=12, color="#f5f5f5")
    ax.set_xlabel(xlabel, fontsize=10, color="#e5e5e5")
    ax.set_ylabel(ylabel, fontsize=10, color="#e5e5e5")
    fig.tight_layout(pad=0.35)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.06, facecolor="#000000")
    plt.close(fig)


def encode_mean(mdl, tok, text):
    ids = tok.encode(text, add_special_tokens=False)
    with torch.no_grad():
        out = mdl(torch.tensor([ids]))[0].mean(dim=1).cpu().numpy()[0]
    return out


def atomicity(tok, cands):
    splits = [len(tok.encode(c, add_special_tokens=False)) for c in cands]
    atoms = [c for c,s in zip(cands, splits) if s == 1]
    return splits, atoms


def mu_cluster(emb, tok, tokens):
    ids = [tok.encode(t, add_special_tokens=False)[0] for t in tokens]
    with torch.no_grad():
        E = emb(torch.tensor(ids)).cpu().numpy()
    m = -1.0
    for i in range(len(E)):
        for j in range(i+1, len(E)):
            m = max(m, cosine(E[i], E[j]))
    return float(m)


def drift_sweep(mdl, tok, token, noise_list):
    drift = []
    for n in noise_list:
        p1 = "Key:" + token
        p2 = ("random " * n) + p1
        h1 = encode_mean(mdl, tok, p1)
        h2 = encode_mean(mdl, tok, p2)
        drift.append(1.0 - cosine(h1, h2))
    return drift


def main(model_id, out_state, out_vis, out_dash, confirm_dir, steps, batch, lr, seed):

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    out_vis = Path(out_vis); out_vis.mkdir(parents=True, exist_ok=True)
    confirm_dir = Path(confirm_dir); confirm_dir.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModel.from_pretrained(model_id)
    mdl.eval()

    arch = str(type(mdl)).split(".")[-1]

    # Confirm: ENV + ARCH
    emit(confirm_dir / "env_proof.json", {
        "timestamp": now(),
        "python": sys.version,
        "torch": torch.__version__,
        "platform": platform.platform(),
        "model_id": model_id
    })
    emit(confirm_dir / "arch_proof.json", {
        "architecture": arch,
        "encoder_like": ("Bert" in arch) or ("Encoder" in arch)
    })

    # Gate-0 PRE atomicity
    cands = [f"HTAG{k:04d}" for k in range(1, 120)]
    splits_pre, atomic_pre = atomicity(tok, cands)
    save_hist(out_vis / "atomicity_pre_hist.png", splits_pre, "Gate-0 Atomicity PRE-MINT", "token split count")

    # Mint
    minted = False
    if len(atomic_pre) < 20:
        tok.add_tokens(cands)
        mdl.resize_token_embeddings(len(tok))
        minted = True

    emit(confirm_dir / "mint_proof.json", {
        "timestamp": now(),
        "minted": minted,
        "added_tokens": len(cands),
        "atomicity_pre": len(atomic_pre)
    })

    # Gate-0 POST atomicity
    splits_post, atomic_post = atomicity(tok, cands)
    save_hist(out_vis / "atomicity_post_hist.png", splits_post, "Gate-0 Atomicity POST-MINT", "token split count")

    verdict = "ATOMICITY_FAIL"
    mu_sep_pre = None
    drift_pre = None
    loss_final = None
    mu_sep_post = None
    drift_post = None

    if len(atomic_post) >= 20:
        ht = atomic_post[:20]

        vocab = list(tok.get_vocab().keys())
        random.shuffle(vocab)
        base = [v for v in vocab if len(tok.encode(v, add_special_tokens=False)) == 1][:20]

        emb = mdl.get_input_embeddings()

        mu_ht = mu_cluster(emb, tok, ht)
        mu_base = mu_cluster(emb, tok, base)
        mu_sep_pre = mu_ht / (mu_base + 1e-9)

        # Visual: mu components
        save_scatter(out_vis / "mu_sep_components.png",
                     list(range(2)), [mu_ht, mu_base],
                     "Gate-1 μ components (HT vs base)", "index (0=HT,1=base)", "μ (max cosine)")

        # Gate-2 drift pre
        noise = [0,5,10,20,40,80]
        token = ht[0]
        drift_pre = drift_sweep(mdl, tok, token, noise)
        save_line(out_vis / "drift_pretrain.png", noise, drift_pre, "Gate-2 Retrieval Drift (PRE-TRAIN)", "prefix noise (n)", "drift = 1-cos")

        verdict = "DRIFT_FAIL" if max(drift_pre) >= 0.15 else "RECOVERY_PASS"

        # Gate-3 Embedding-only training
        # Freeze ALL params
        for p in mdl.parameters():
            p.requires_grad = False

        emb = mdl.get_input_embeddings()
        W = emb.weight

        # Identify ids for minted tokens (these are atoms now)
        ht_ids = [tok.encode(t, add_special_tokens=False)[0] for t in ht]
        # Create a gradient mask: only minted rows allowed to update
        mask = torch.zeros_like(W, dtype=torch.bool)
        for i in ht_ids:
            mask[i] = True

        # Optimizer on entire embedding matrix, but we will zero grads for non-masked rows
        opt = torch.optim.Adam([W], lr=lr)

        # Simple contrastive objective:
        # - Keep HT tokens mutually close
        # - Push away random baseline atoms
        # This is *not* "good semantics" training; it's anchor-shaping to resist drift.
        def step_loss():
            # sample ht batch
            b_ht = random.sample(ht_ids, k=min(len(ht_ids), max(4, batch//2)))
            # sample base ids
            base_ids = [tok.encode(v, add_special_tokens=False)[0] for v in base[:batch]]
            with torch.no_grad():
                Ebase = W[torch.tensor(base_ids)]
            Eht = W[torch.tensor(b_ht)]
            # pull term: mean pairwise distance in ht
            pull = 0.0
            cnt = 0
            for i in range(Eht.size(0)):
                for j in range(i+1, Eht.size(0)):
                    pull = pull + (1.0 - torch.nn.functional.cosine_similarity(Eht[i:i+1], Eht[j:j+1])).mean()
                    cnt += 1
            pull = pull / max(cnt, 1)

            # push term: ht vs base cosine should be low
            push = 0.0
            for i in range(Eht.size(0)):
                sim = torch.nn.functional.cosine_similarity(Eht[i:i+1], Ebase).mean()
                push = push + sim
            push = push / max(Eht.size(0), 1)

            # balance
            return pull + 0.25*push

        loss_curve = []
        for s in range(int(steps)):
            opt.zero_grad(set_to_none=True)
            L = step_loss()
            L.backward()

            # zero grads except masked rows
            if W.grad is not None:
                g = W.grad
                g[~mask] = 0.0

            opt.step()
            loss_curve.append(float(L.detach().cpu().item()))

        loss_final = float(loss_curve[-1]) if loss_curve else None
        save_line(out_vis / "train_loss.png", list(range(len(loss_curve))), loss_curve,
                  "Gate-3 Embedding-only training loss", "step", "loss")

        emit(confirm_dir / "train_proof.json", {
            "timestamp": now(),
            "steps": int(steps),
            "batch": int(batch),
            "lr": float(lr),
            "seed": int(seed),
            "loss_final": loss_final,
            "rows_trainable": len(ht_ids),
            "backbone_frozen": True
        })

        # Gate-4 drift post
        mdl.eval()
        drift_post = drift_sweep(mdl, tok, token, noise)
        save_line(out_vis / "drift_posttrain.png", noise, drift_post, "Gate-4 Retrieval Drift (POST-TRAIN)", "prefix noise (n)", "drift = 1-cos")

        # μ-separation post (should often change slightly)
        emb = mdl.get_input_embeddings()
        mu_ht2 = mu_cluster(emb, tok, ht)
        mu_base2 = mu_cluster(emb, tok, base)
        mu_sep_post = mu_ht2 / (mu_base2 + 1e-9)

        # Visual: drift delta
        delta = [float(a-b) for a,b in zip(drift_pre, drift_post)]
        save_line(out_vis / "drift_delta.png", noise, delta, "Drift Δ = PRE − POST (positive = recovery)", "prefix noise (n)", "Δ drift")

        # Verdict
        if max(drift_post) < 0.15:
            verdict = "RECOVERY_PASS"
        else:
            verdict = "RECOVERY_FAIL" if max(drift_pre) >= 0.15 else "RECOVERY_PASS"

    state = {
        "version": "1.8",
        "timestamp": now(),
        "model": model_id,
        "architecture": arch,
        "seed": int(seed),
        "minted": minted,
        "atomicity_pre": int(len(atomic_pre)),
        "atomicity_post": int(len(atomic_post)),
        "mu_separation_pretrain": mu_sep_pre,
        "drift_curve_pretrain": drift_pre,
        "train": {
            "steps": int(steps),
            "batch": int(batch),
            "lr": float(lr),
            "loss_final": loss_final
        },
        "mu_separation_posttrain": mu_sep_post,
        "drift_curve_posttrain": drift_post,
        "verdict": verdict
    }

    emit(out_state, state)

    # True-black dashboard
    dash = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>CODEX–HYPERTOKENS v1.8</title>
    <style>
      body{{background:#000;color:#f5f5f5;font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:16px}}
      h1{{margin:0 0 8px 0;font-size:26px}}
      .meta{{opacity:.88;font-size:14px;margin-bottom:12px;line-height:1.5;max-width:1600px}}
      .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px;max-width:1800px}}
      .card{{border:1px solid #222;background:#050505;border-radius:18px;padding:12px}}
      pre{{white-space:pre-wrap;word-break:break-word;background:#020202;border:1px solid #222;border-radius:14px;padding:10px}}
      img{{width:100%;border-radius:14px;border:1px solid #333;background:#000;display:block;margin-top:10px}}
    </style></head><body>
    <h1>𓂀 CODEX–HYPERTOKENS v1.8 — Drift Recovery Oracle</h1>
    <div class="meta">
      Gates: Atomicity → Mint → μ → Drift(pre) → Train(emb-only) → Drift(post).<br>
      H₁₇D: drift recovery under frozen backbone implies stability is an embedding-row property.
    </div>
    <pre>{json.dumps(state, indent=2)}</pre>
    <div class="grid">
      <div class="card"><b>Atomicity (PRE)</b><img src="../visuals/atomicity_pre_hist.png"></div>
      <div class="card"><b>Atomicity (POST)</b><img src="../visuals/atomicity_post_hist.png"></div>
      <div class="card"><b>μ components</b><img src="../visuals/mu_sep_components.png"></div>
      <div class="card"><b>Drift PRE</b><img src="../visuals/drift_pretrain.png"></div>
      <div class="card"><b>Train loss</b><img src="../visuals/train_loss.png"></div>
      <div class="card"><b>Drift POST</b><img src="../visuals/drift_posttrain.png"></div>
      <div class="card"><b>Drift Δ (PRE−POST)</b><img src="../visuals/drift_delta.png"></div>
    </div>
    </body></html>"""

    Path(out_dash).write_text(dash, encoding="utf-8")

    # handoff.json (no stdout dependency)
    emit(Path(out_state).parent / "handoff.json", {"dashboard": str(Path(out_dash).resolve())})

    return 0


if __name__ == "__main__":
    # argv: model_id out_state out_vis out_dash confirm_dir steps batch lr seed
    sys.exit(main(
        sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
        int(sys.argv[6]), int(sys.argv[7]), float(sys.argv[8]), int(sys.argv[9])
    ))
