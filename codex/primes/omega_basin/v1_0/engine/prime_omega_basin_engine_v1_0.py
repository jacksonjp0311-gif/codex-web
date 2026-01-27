#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  PRIME Ω-BASIN v1.0 — NOISE-IMMUNITY ENGINE                  ║
# ║  Prime gaps → ΔΦ field → Ω invariance (H20)                  ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

# ───────── PRIME GENERATION ─────────

def primes_up_to(N):
    sieve = np.ones(N+1, dtype=bool)
    sieve[:2] = False
    for i in range(2,int(N**0.5)+1):
        if sieve[i]:
            sieve[i*i:N+1:i] = False
    return np.nonzero(sieve)[0]

# ───────── FIELD BUILD ─────────

def build_gap_field(gaps, T=64):
    n = len(gaps)
    V = np.zeros((T,n), dtype=np.float32)

    x = np.linspace(0,1,n)
    for t in range(T):
        theta = 2*math.pi*t/T
        mod = 1.0 + 0.35*np.sin(theta) + 0.20*np.cos(2*theta + 6*x)
        V[t] = gaps * mod
    return V

def dphi(V):
    gx = np.gradient(V, axis=1)
    gt = np.gradient(V, axis=0)
    return np.sqrt(gx*gx + gt*gt)

def omega(dphi):
    return 1.0/(1.0+np.abs(dphi))

# ───────── MAIN ─────────

def main(root,state_d,vis_d,ledger_d,logs_d,limit,noise_level):

    root = Path(root)
    state_d  = Path(state_d)
    vis_d    = Path(vis_d)
    ledger_d = Path(ledger_d)
    logs_d   = Path(logs_d)

    for d in [state_d,vis_d,ledger_d,logs_d]:
        d.mkdir(parents=True, exist_ok=True)

    # 1) primes + gaps
    P = primes_up_to(limit)
    gaps = np.diff(P).astype(np.float32)

    # 2) build ΔΦ field
    V = build_gap_field(gaps,T=64)
    dP = dphi(V)
    Om = omega(dP)

    # 3) noise injection
    sigma = noise_level*np.std(dP)
    noise = np.random.normal(0,sigma,size=dP.shape).astype(np.float32)
    dP2 = dP + noise
    Om2 = omega(dP2)

    # 4) Ω-basin metrics
    omega_diff = float(np.mean(np.abs(Om2-Om)))
    noise_immunity = 1.0/(1.0+omega_diff)

    drop = float(np.mean(Om)-np.mean(Om2))
    basin_drop = 1.0/(1.0+max(0.0,drop))

    # 5) visuals
    plt.figure()
    plt.imshow(dP,aspect="auto",origin="lower")
    plt.title("Prime ΔΦ field (baseline)")
    p1 = vis_d/"prime_dphi_baseline.png"
    plt.savefig(p1,bbox_inches="tight"); plt.close()

    plt.figure()
    plt.imshow(dP2,aspect="auto",origin="lower")
    plt.title("Prime ΔΦ field (noisy)")
    p2 = vis_d/"prime_dphi_noisy.png"
    plt.savefig(p2,bbox_inches="tight"); plt.close()

    plt.figure()
    plt.plot(np.mean(Om,axis=1),label="Ω baseline")
    plt.plot(np.mean(Om2,axis=1),label="Ω noisy",linestyle="--")
    plt.legend()
    plt.title("Ω-basin invariance curve")
    p3 = vis_d/"prime_omega_noise_immunity.png"
    plt.savefig(p3,bbox_inches="tight"); plt.close()

    # 6) state JSON
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    state_path = state_d/f"prime_omega_state_{ts}.json"

    state = {
        "protocol":"CodexPrimeOmegaBasin",
        "version":"1.0",
        "timestamp":now_iso(),
        "prime_limit":int(limit),
        "noise_level":float(noise_level),
        "metrics":{
            "omega_diff_L1":omega_diff,
            "noise_immunity_index":noise_immunity,
            "basin_drop_index":basin_drop
        },
        "visuals":{
            "dphi_baseline":str(p1),
            "dphi_noisy":str(p2),
            "omega_curve":str(p3)
        },
        "codex":{
            "H7":0.70,
            "H20":"Ω-basin invariance",
            "law":"Ω = 1/(1+|ΔΦ|)"
        }
    }

    state_path.write_text(json.dumps(state,indent=2),encoding="utf-8")

    # 7) ledger append
    ledger_path = ledger_d/"prime_omega_ledger.jsonl"
    row = {
        "timestamp":now_iso(),
        "prime_limit":int(limit),
        "noise_level":float(noise_level),
        "omega_diff_L1":omega_diff,
        "noise_immunity_index":noise_immunity,
        "basin_drop_index":basin_drop
    }
    with ledger_path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row)+"\n")

    print("Prime Ω-Basin v1.0 complete.")
    print("State →",state_path)

if __name__=="__main__":
    if len(sys.argv)!=8:
        print("Usage: engine ROOT STATE VIS VISLED LOGS LIMIT NOISE")
        sys.exit(1)

    _,root,state,vis,led,logs,lim,noise = sys.argv
    main(root,state,vis,led,logs,int(lim),float(noise))
