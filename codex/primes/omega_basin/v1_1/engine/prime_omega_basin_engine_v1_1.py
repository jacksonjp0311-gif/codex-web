#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  PRIME Ω-BASIN v1.1 — NOISE-IMMUNITY ENGINE                  ║
# ║  Prime gaps → ΔΦ field → Ω invariance (H20)                  ║
# ║  v1.1: better logging + T configurable + stable artifacts     ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def primes_up_to(N: int) -> np.ndarray:
    sieve = np.ones(N+1, dtype=bool)
    sieve[:2] = False
    r = int(N**0.5)
    for i in range(2, r+1):
        if sieve[i]:
            sieve[i*i:N+1:i] = False
    return np.nonzero(sieve)[0]

def build_gap_field(gaps: np.ndarray, T: int = 64) -> np.ndarray:
    n = len(gaps)
    V = np.zeros((T, n), dtype=np.float32)
    x = np.linspace(0.0, 1.0, n, dtype=np.float32)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = 1.0 + 0.35*np.sin(theta) + 0.20*np.cos(2.0*theta + 6.0*x)
        V[t] = gaps * mod
    return V

def dphi(V: np.ndarray) -> np.ndarray:
    gx = np.gradient(V, axis=1)
    gt = np.gradient(V, axis=0)
    return np.sqrt(gx*gx + gt*gt)

def omega(dP: np.ndarray) -> np.ndarray:
    return 1.0/(1.0 + np.abs(dP))

def safe_write_img(path: Path, img: np.ndarray, title: str):
    plt.figure()
    plt.imshow(img, aspect="auto", origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def main(root, state_d, vis_d, ledger_d, logs_d, limit, noise_level, T):
    root = Path(root)
    state_d  = Path(state_d)
    vis_d    = Path(vis_d)
    ledger_d = Path(ledger_d)
    logs_d   = Path(logs_d)

    for d in (state_d, vis_d, ledger_d, logs_d):
        d.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = logs_d / f"prime_omega_run_{ts}.log"

    def log(msg: str):
        s = msg.encode("ascii","replace").decode("ascii")
        print(s)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(s + "\n")

    try:
        log("PRIME Ω-BASIN v1.1 starting...")
        log(f"prime_limit : {limit}")
        log(f"noise_level : {noise_level}")
        log(f"T           : {T}")

        # 1) primes + gaps
        P = primes_up_to(int(limit))
        gaps = np.diff(P).astype(np.float32)
        n = int(gaps.shape[0])
        log(f"primes_count : {int(P.shape[0])}")
        log(f"gaps_count   : {n}")
        log(f"gap_mean     : {float(gaps.mean()):.6g}")
        log(f"gap_std      : {float(gaps.std()):.6g}")
        log(f"gap_max      : {float(gaps.max()):.6g}")

        # 2) ΔΦ field
        V  = build_gap_field(gaps, T=int(T))
        dP = dphi(V)
        Om = omega(dP)

        # 3) noise injection on ΔΦ
        dP_std = float(np.std(dP))
        sigma = float(noise_level) * max(dP_std, 1e-12)
        noise = np.random.normal(0.0, sigma, size=dP.shape).astype(np.float32)

        dP2 = dP + noise
        Om2 = omega(dP2)

        # 4) Ω-basin metrics
        omega_diff = float(np.mean(np.abs(Om2 - Om)))
        noise_immunity = 1.0/(1.0 + max(0.0, omega_diff))

        drop = float(np.mean(Om) - np.mean(Om2))
        basin_drop = 1.0/(1.0 + max(0.0, drop))

        om_mean = float(np.mean(Om))
        om_mean2 = float(np.mean(Om2))

        log(f"dphi_std         : {dP_std:.6g}")
        log(f"noise_sigma      : {sigma:.6g}")
        log(f"omega_mean_base  : {om_mean:.6g}")
        log(f"omega_mean_noisy : {om_mean2:.6g}")
        log(f"omega_diff_L1    : {omega_diff:.6g}")
        log(f"noise_immunity   : {noise_immunity:.6g}")
        log(f"basin_drop_index : {basin_drop:.6g}")

        # 5) visuals
        p1 = vis_d / f"prime_dphi_baseline_{ts}.png"
        p2 = vis_d / f"prime_dphi_noisy_{ts}.png"
        p3 = vis_d / f"prime_omega_noise_immunity_{ts}.png"

        safe_write_img(p1, dP,  "Prime ΔΦ field (baseline)")
        safe_write_img(p2, dP2, "Prime ΔΦ field (noisy)")

        plt.figure()
        plt.plot(np.mean(Om, axis=1),  label="Ω baseline")
        plt.plot(np.mean(Om2, axis=1), label="Ω noisy", linestyle="--")
        plt.legend()
        plt.title("Ω-basin invariance curve")
        plt.xlabel("t")
        plt.ylabel("Ω(t)")
        plt.savefig(p3, bbox_inches="tight")
        plt.close()

        # 6) state JSON
        state_path = state_d / f"prime_omega_state_{ts}.json"
        state = {
            "protocol":"CodexPrimeOmegaBasin",
            "version":"1.1",
            "timestamp":now_iso(),
            "prime_limit":int(limit),
            "T":int(T),
            "noise_level":float(noise_level),
            "shape":{"T":int(V.shape[0]), "gaps":int(V.shape[1])},
            "metrics":{
                "gap_mean": float(gaps.mean()),
                "gap_std":  float(gaps.std()),
                "gap_max":  float(gaps.max()),
                "dphi_std": dP_std,
                "noise_sigma": sigma,
                "omega_mean_before": om_mean,
                "omega_mean_after":  om_mean2,
                "omega_diff_L1": omega_diff,
                "noise_immunity_index": noise_immunity,
                "basin_drop_index": basin_drop
            },
            "visuals":{
                "dphi_baseline":str(p1),
                "dphi_noisy":str(p2),
                "omega_curve":str(p3)
            },
            "codex":{
                "H7":0.70,
                "H19":"Global ΔΦ integration",
                "H20":"Ω-basin invariance / noise-immunity",
                "law":"Ω = 1/(1+|ΔΦ|)"
            }
        }

        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        # 7) ledger append
        ledger_path = ledger_d / "prime_omega_ledger.jsonl"
        row = {
            "timestamp":now_iso(),
            "version":"1.1",
            "prime_limit":int(limit),
            "T":int(T),
            "noise_level":float(noise_level),
            "omega_diff_L1":omega_diff,
            "noise_immunity_index":noise_immunity,
            "basin_drop_index":basin_drop
        }
        with ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

        log("Prime Ω-Basin v1.1 complete.")
        log(f"State → {state_path}")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(err + "\n")
            f.write(traceback.format_exc() + "\n")
        return 1

if __name__=="__main__":
    if len(sys.argv) != 9:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS LIMIT NOISE T", file=sys.stderr)
        sys.exit(1)

    _, root, state, vis, led, logs, lim, noise, T = sys.argv
    code = main(root, state, vis, led, logs, int(lim), float(noise), int(T))
    sys.exit(code)
