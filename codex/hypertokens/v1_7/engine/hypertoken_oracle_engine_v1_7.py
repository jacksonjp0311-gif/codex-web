#!/usr/bin/env python3
\"\"\"
CODEX–HYPERTOKENS v1.7 — ATOM-MINT + μ/DRIFT ORACLE

Key upgrade vs v1.6:
- If tokenizer contains *no* naturally-atomic hypertokens, we *mint* them:
  tokenizer.add_tokens([...]); model.resize_token_embeddings(...)
  Then re-run atomicity proof POST-mint.
- Emits richer oracle set + env/proof artifacts.
- Always emits state.json (READY or FAILSTATE).
\"\"\"

import json, os, sys, random, platform, subprocess
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import torch
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def write_json(path, obj, pretty=True):
    Path(path).write_text(json.dumps(obj, indent=2 if pretty else None), encoding="utf-8")

def write_jsonl_line(path, obj):
    # single-line JSON for ledger immunity
    line = json.dumps(obj, separators=(",",":"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def cosine(a, b):
    return float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def env_fingerprint():
    fp = {
        "python": sys.version.replace("\n"," "),
        "platform": platform.platform(),
        "torch": getattr(torch, "__version__", None),
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
    }
    # best-effort pip freeze (bounded)
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], stderr=subprocess.STDOUT, timeout=25)
        lines = out.decode("utf-8", errors="replace").splitlines()
        # keep small; this is proof, not a dump
        keep = [l for l in lines if any(l.lower().startswith(x) for x in ("torch","transformers","numpy","matplotlib","huggingface-hub","tokenizers","safetensors"))]
        fp["pip_freeze_subset"] = keep[:80]
    except Exception as e:
        fp["pip_freeze_subset_error"] = repr(e)
    return fp

def model_arch_truth(mdl):
    cfg = getattr(mdl, "config", None)
    out = {"model_class": type(mdl).__name__}
    if cfg is not None:
        out.update({
            "model_type": getattr(cfg, "model_type", None),
            "is_encoder_decoder": bool(getattr(cfg, "is_encoder_decoder", False)),
            "architectures": getattr(cfg, "architectures", None),
            "hidden_size": getattr(cfg, "hidden_size", None),
            "num_hidden_layers": getattr(cfg, "num_hidden_layers", None),
        })
    # classify simply for gate(A)
    out["arch_gate"] = "ENCODER_DECODER" if out.get("is_encoder_decoder") else "ENCODER_ONLY"
    return out

def atomicity_stats(tok, cands):
    splits = [len(tok.encode(c, add_special_tokens=False)) for c in cands]
    atomic = [c for c, s in zip(cands, splits) if s == 1]
    rate = float(len(atomic) / max(1, len(cands)))
    return splits, atomic, rate

def plot_atomicity_hist(splits, out_png, title):
    plt.figure()
    plt.hist(splits, bins=8)
    plt.title(title)
    plt.xlabel("Token Splits")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(out_png, dpi=140)

def embed_tokens(tok, mdl, tokens):
    emb = mdl.get_input_embeddings()
    ids = [tok.encode(t, add_special_tokens=False)[0] for t in tokens]
    with torch.no_grad():
        return emb(torch.tensor(ids)).cpu().numpy()

def mu_maxcos(E):
    m = -1.0
    for i in range(len(E)):
        for j in range(i+1, len(E)):
            m = max(m, cosine(E[i], E[j]))
    return float(m)

def mu_heatmap(E, tokens, out_png, title):
    n = len(E)
    M = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            M[i, j] = cosine(E[i], E[j])
    plt.figure(figsize=(7.2, 6.0))
    plt.imshow(M, interpolation="nearest")
    plt.title(title)
    plt.colorbar()
    plt.xticks(range(n), tokens, rotation=90, fontsize=6)
    plt.yticks(range(n), tokens, fontsize=6)
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)

def drift_sweep(tok, mdl, token, noise_levels):
    drift = []
    for n in noise_levels:
        p1 = "Key: " + token
        p2 = ("random " * n) + p1
        ids1 = tok.encode(p1, add_special_tokens=False)
        ids2 = tok.encode(p2, add_special_tokens=False)
        with torch.no_grad():
            h1 = mdl(torch.tensor([ids1]))[0].mean(dim=1).cpu().numpy()[0]
            h2 = mdl(torch.tensor([ids2]))[0].mean(dim=1).cpu().numpy()[0]
        drift.append(float(1.0 - cosine(h1, h2)))
    return drift

def plot_drift(noise_levels, drift, out_png):
    plt.figure()
    plt.plot(noise_levels, drift)
    plt.title("Gate-2 Retrieval Drift Sweep")
    plt.xlabel("Noise Tokens")
    plt.ylabel("Drift (1 - cos)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=140)

def main(model_id, ht_prefix, ht_count, out_state, out_latest, out_vis_dir, out_dash, out_proof_dir, out_manifest_dir, out_schema_dir):
    vis = Path(out_vis_dir); vis.mkdir(parents=True, exist_ok=True)
    proof = Path(out_proof_dir); proof.mkdir(parents=True, exist_ok=True)

    state = {
        "version": "1.7",
        "timestamp": now(),
        "model": model_id,
        "verdict": "INIT"
    }

    # Load
    try:
        tok = AutoTokenizer.from_pretrained(model_id)
        mdl = AutoModel.from_pretrained(model_id)
        mdl.eval()
    except Exception as e:
        state.update({"verdict":"MODEL_LOAD_FAIL","error":repr(e)})
        write_json(out_state, state, pretty=True)
        write_json(out_latest, state, pretty=True)
        return 3

    # Gate(A): architecture truth
    arch = model_arch_truth(mdl)
    state["architecture"] = arch
    write_json(proof / "arch_truth.json", arch, pretty=True)

    # Env fingerprint
    fp = env_fingerprint()
    write_json(proof / "env_fingerprint.json", fp, pretty=True)
    state["env_fingerprint"] = fp

    # Candidates
    cands = [f"{ht_prefix}{k:04d}" for k in range(1, ht_count+1)]

    # Gate-0 PRE atomicity
    splits_pre, atomic_pre, rate_pre = atomicity_stats(tok, cands)
    state["atomicity_pre"] = {"rate": rate_pre, "atomic_count": len(atomic_pre), "total": len(cands)}
    plot_atomicity_hist(splits_pre, vis / "atomicity_pre_hist.png", "Gate-0 Atomicity (PRE-MINT)")
    write_json(proof / "atomicity_pre.json", {"splits": splits_pre, "atomic": atomic_pre, "rate": rate_pre}, pretty=True)

    # Gate-0b: Mint if needed
    minted = False
    minted_tokens = []
    if len(atomic_pre) < min(20, ht_count):
        try:
            add = cands[:]  # mint the whole set
            n_added = tok.add_tokens(add, special_tokens=False)
            if n_added > 0:
                mdl.resize_token_embeddings(len(tok))
                minted = True
                minted_tokens = add
        except Exception as e:
            state.update({"verdict":"MINT_FAIL","error":repr(e)})
            write_json(out_state, state, pretty=True)
            write_json(out_latest, state, pretty=True)
            return 4

    state["mint"] = {"performed": bool(minted), "requested": len(cands), "minted_tokens": len(minted_tokens)}

    # Gate-0 POST atomicity
    splits_post, atomic_post, rate_post = atomicity_stats(tok, cands)
    state["atomicity_post"] = {"rate": rate_post, "atomic_count": len(atomic_post), "total": len(cands)}
    plot_atomicity_hist(splits_post, vis / "atomicity_post_hist.png", "Gate-0 Atomicity (POST-MINT)")
    write_json(proof / "atomicity_post.json", {"splits": splits_post, "atomic": atomic_post, "rate": rate_post}, pretty=True)

    # Gate decisions
    verdict = "ATOMICITY_FAIL"
    mu_sep = None
    mu_ht = None
    mu_base = None
    drift = None

    if len(atomic_post) >= min(20, ht_count):
        # choose 20
        ht = atomic_post[:20]

        vocab = list(tok.get_vocab().keys())
        random.shuffle(vocab)
        base = [v for v in vocab if len(tok.encode(v, add_special_tokens=False)) == 1][:20]

        # μ separation
        Eht = embed_tokens(tok, mdl, ht)
        Ebase = embed_tokens(tok, mdl, base)
        mu_ht = mu_maxcos(Eht)
        mu_base = mu_maxcos(Ebase)
        mu_sep = float(mu_ht / (mu_base + 1e-9))

        state["mu"] = {"mu_ht": mu_ht, "mu_base": mu_base, "mu_separation": mu_sep}
        mu_heatmap(Eht, ht, vis / "mu_heatmap_ht.png", "Gate-1 μ Heatmap (Hypertokens)")
        mu_heatmap(Ebase, base, vis / "mu_heatmap_base.png", "Gate-1 μ Heatmap (Baseline)")

        # Drift sweep (token = first hypertoken)
        noise_levels = [0, 5, 10, 20, 40, 80, 120]
        token = ht[0]
        drift = drift_sweep(tok, mdl, token, noise_levels)
        plot_drift(noise_levels, drift, vis / "drift_sweep.png")

        state["drift"] = {"token": token, "noise_levels": noise_levels, "drift_curve": drift}

        # Verdict threshold: conservative defaults
        drift_max = float(max(drift))
        verdict = "READY_FOR_SWEEPS" if drift_max < 0.15 else "DRIFT_FAIL"
        state["thresholds"] = {"drift_max": drift_max, "pass_if_drift_max_lt": 0.15}

    else:
        state["note"] = "Not enough atomic hypertokens even after mint attempt."

    state["verdict"] = verdict

    # Dashboard
    dash = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>CODEX–HYPERTOKENS v1.7 ORACLE</title>
</head>
<body style="font-family:monospace;background:#000;color:#00ffcc;padding:16px;">
  <h1>𓂀 CODEX–HYPERTOKENS v1.7 ORACLE</h1>
  <pre>{json.dumps(state, indent=2)}</pre>

  <h2>Gate-0 Atomicity</h2>
  <div>
    <p>PRE-MINT</p>
    <img src="../visuals/atomicity_pre_hist.png" width="760"/>
    <p>POST-MINT</p>
    <img src="../visuals/atomicity_post_hist.png" width="760"/>
  </div>

  <h2>Gate-1 μ Heatmaps</h2>
  <div>
    <p>Hypertokens</p>
    <img src="../visuals/mu_heatmap_ht.png" width="760"/>
    <p>Baseline</p>
    <img src="../visuals/mu_heatmap_base.png" width="760"/>
  </div>

  <h2>Gate-2 Drift Sweep</h2>
  <img src="../visuals/drift_sweep.png" width="760"/>

  <h2>Proof Artifacts</h2>
  <ul>
    <li><a style="color:#00ffcc" href="../confirmations/arch_truth.json">arch_truth.json</a></li>
    <li><a style="color:#00ffcc" href="../confirmations/env_fingerprint.json">env_fingerprint.json</a></li>
    <li><a style="color:#00ffcc" href="../confirmations/atomicity_pre.json">atomicity_pre.json</a></li>
    <li><a style="color:#00ffcc" href="../confirmations/atomicity_post.json">atomicity_post.json</a></li>
  </ul>
</body>
</html>
"""
    Path(out_dash).write_text(dash, encoding="utf-8")

    # Minimal schema (light contract)
    schema = {
        "state_required_keys": ["version","timestamp","model","architecture","verdict"],
        "verdict_enum": ["INIT","DEPENDENCY_FAIL","MODEL_LOAD_FAIL","MINT_FAIL","ATOMICITY_FAIL","DRIFT_FAIL","READY_FOR_SWEEPS"],
        "notes": "This is a lightweight Codex contract: proof-first, falsifiable, non-ontological."
    }
    write_json(Path(out_schema_dir) / "state_schema_min.json", schema, pretty=True)

    # Manifest
    manifest = {
        "module": "CodexHypertokens",
        "version": "1.7",
        "law": "Anchor→Verify→ArchGate→Atomicity→Mint→μ→Drift→Oracle→Ledger→Git→Return",
        "model_default": model_id,
        "ht_prefix": ht_prefix,
        "ht_count": int(ht_count),
    }
    write_json(Path(out_manifest_dir) / "manifest.json", manifest, pretty=True)

    # Write state (run + latest)
    write_json(out_state, state, pretty=True)
    write_json(out_latest, state, pretty=True)

    return 0

if __name__ == "__main__":
    # argv:
    # 1 model_id
    # 2 ht_prefix
    # 3 ht_count
    # 4 out_state (run)
    # 5 out_latest
    # 6 out_vis_dir
    # 7 out_dash
    # 8 out_proof_dir
    # 9 out_manifest_dir
    # 10 out_schema_dir
    sys.exit(main(
        sys.argv[1], sys.argv[2], int(sys.argv[3]),
        sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7],
        sys.argv[8], sys.argv[9], sys.argv[10]
    ))
