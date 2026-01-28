#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  CODEX–HYPERTOKENS v1.0 — TRUTH GATE FOUNDATION              ║
# ║  Atomicity + μ-Coherence + Ω Truth + Dashboard               ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, random, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def ascii_safe(s: str) -> str:
    return s.encode("ascii","replace").decode("ascii")

def cosine(a,b):
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))

def mu_coherence(E):
    mu = -1.0
    for i in range(len(E)):
        for j in range(i+1,len(E)):
            mu = max(mu, cosine(E[i],E[j]))
    return float(mu)

def omega(mu):
    return 1.0/(1.0+abs(mu))

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
    import torch
    with torch.no_grad():
        return layer(torch.tensor(ids)).cpu().numpy()

def main(root, state_d, vis_d, ledger_d, logs_d, model_id):

    root = Path(root)
    state_d  = Path(state_d)
    vis_d    = Path(vis_d)
    ledger_d = Path(ledger_d)
    logs_d   = Path(logs_d)

    for d in (state_d, vis_d, ledger_d, logs_d):
        d.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = logs_d / f"hypertoken_run_{ts}.log"

    def log(msg):
        s = ascii_safe(msg)
        print(s)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(s+"\n")

    try:
        # Gate(-1): dependency import
        try:
            from transformers import AutoTokenizer, AutoModel
        except Exception:
            log("FATAL: transformers not installed.")
            return 2

        log("CODEX–HYPERTOKENS v1.0 starting...")
        log(f"model_id : {model_id}")

        tok = AutoTokenizer.from_pretrained(model_id)
        mdl = AutoModel.from_pretrained(model_id)
        mdl.eval()

        # Gate-0 Atomicity
        cands = morph()
        atomic, splits = atomicity(tok, cands)
        atomic_rate = len(atomic)/len(cands)

        plt.figure()
        plt.hist(splits, bins=range(1,max(splits)+2), align="left")
        plt.title("Gate-0 Atomicity Distribution")
        plt.xlabel("Tokens per candidate")
        plt.ylabel("Count")
        p_atomic = vis_d / f"atomicity_hist_{ts}.png"
        plt.savefig(p_atomic, bbox_inches="tight")
        plt.close()

        if len(atomic) < 10:
            verdict = "FALSIFIED_ATOMICITY"
            mu_ht = None
            mu_base = None
            om = None
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
            om      = omega(mu_ht)

            verdict = "SUPPORTED_GO" if mu_ht < 0.3*mu_base else "FALSIFIED_ENTANGLED"

            # μ plot
            plt.figure()
            plt.bar(["μ_HT","μ_Base"], [mu_ht, mu_base])
            plt.title("Gate-1 μ-Coherence Comparison")
            p_mu = vis_d / f"mu_comparison_{ts}.png"
            plt.savefig(p_mu, bbox_inches="tight")
            plt.close()

            # Ω plot
            plt.figure()
            plt.bar(["Ω Truth"], [om])
            plt.ylim(0,1)
            plt.title("GEO v1.0 Truth Geometry")
            p_om = vis_d / f"omega_truth_{ts}.png"
            plt.savefig(p_om, bbox_inches="tight")
            plt.close()

        # Verdict card
        plt.figure(figsize=(8,3))
        plt.text(0.5,0.5, verdict, fontsize=22, ha="center", va="center")
        plt.axis("off")
        plt.title("CODEX ORACLE VERDICT")
        p_verdict = vis_d / f"verdict_card_{ts}.png"
        plt.savefig(p_verdict, bbox_inches="tight")
        plt.close()

        # Dashboard HTML
        dash = vis_d / f"dashboard_{ts}.html"
        dash.write_text(f"""
        <html><body>
        <h1>CODEX–HYPERTOKENS v1.0 ORACLE DASHBOARD</h1>
        <p><b>Verdict:</b> {verdict}</p>
        <img src="{p_atomic.name}" width="600"><br>
        <img src="{p_verdict.name}" width="600"><br>
        </body></html>
        """, encoding="utf-8")

        # State JSON
        state_path = state_d / f"hypertoken_state_{ts}.json"
        state = {
            "protocol": "CodexHypertokensTruthGate",
            "version": "1.0",
            "timestamp": now_iso(),
            "model": model_id,
            "atomicity_rate": atomic_rate,
            "mu_ht": mu_ht,
            "mu_baseline": mu_base,
            "omega_truth": om,
            "verdict": verdict,
            "visuals": {
                "atomicity": str(p_atomic),
                "verdict": str(p_verdict),
                "dashboard": str(dash)
            }
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log(f"State -> {state_path}")

        # Ledger append ONLY if state exists
        ledger_path = ledger_d / "hypertoken_ledger.jsonl"
        with ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": now_iso(),
                "version": "1.0",
                "model": model_id,
                "verdict": verdict,
                "atomicity_rate": atomic_rate
            })+"\n")

        log("CODEX–HYPERTOKENS v1.0 complete.")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(ascii_safe(err)+"\n")
            f.write(ascii_safe(traceback.format_exc())+"\n")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS MODEL_ID", file=sys.stderr)
        sys.exit(1)

    _, root, state, vis, led, logs, model_id = sys.argv[:7]
    code = main(root, state, vis, led, logs, model_id)
    sys.exit(code)
