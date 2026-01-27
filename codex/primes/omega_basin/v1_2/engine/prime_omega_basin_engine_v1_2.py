#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  PRIME Ω-BASIN v1.2 — NOISE-IMMUNITY ENGINE                  ║
# ║  v1.2: ASCII-safe logging + stable artifacts + extra metrics  ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def ascii_safe(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")

# ───────── PRIME GENERATION ─────────

def primes_up_to(N: int) -> np.ndarray:
    sieve = np.ones(N+1, dtype=bool)
    sieve[:2] = False
    r = int(N**0.5)
    for i in range(2, r+1):
        if sieve[i]:
            sieve[i*i:N+1:i] = False
    return np.nonzero(sieve)[0]

# ───────── FIELD BUILD ─────────

def build_gap_field(gaps: np.ndarray, T: int) -> np.ndarray:
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

# ───────── MAIN ─────────

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
        s = ascii_safe(msg)
        print(s)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(s + "\n")

    try:
        log("PRIME OMEGA-BASIN v1.2 starting...")
        log(f"prime_limit : {limit}")
        log(f"noise_level : {noise_level}")
        log(f"T           : {T}")

        # 1) primes + gaps
        P = primes_up_to(int(limit))
        gaps = np.diff(P).astype(np.float32)
        n = int(gaps.shape[0])

        gap_mean = float(gaps.mean()) if n > 0 else 0.0
        gap_std  = float(gaps.std())  if n > 0 else 0.0
        gap_max  = float(gaps.max())  if n > 0 else 0.0

        log(f"primes_count : {int(P.shape[0])}")
        log(f"gaps_count   : {n}")
        log(f"gap_mean     : {gap_mean:.6g}")
        log(f"gap_std      : {gap_std:.6g}")
        log(f"gap_max      : {gap_max:.6g}")

        # 2) ΔΦ field
        V  = build_gap_field(gaps, T=int(T))
        dP = dphi(V)
        Om = omega(dP)

        # 3) noise injection on ΔΦ
        dP_std = float(np.std(dP)) if dP.size else 0.0
        sigma = float(noise_level) * max(dP_std, 1e-12)
        noise = np.random.normal(0.0, sigma, size=dP.shape).astype(np.float32)
        dP2 = dP + noise
        Om2 = omega(dP2)

        # 4) Ω-basin metrics
        omega_diff = float(np.mean(np.abs(Om2 - Om)))
        noise_immunity = 1.0/(1.0 + max(0.0, omega_diff))

        drop = float(np.mean(Om) - np.mean(Om2))
        basin_drop = 1.0/(1.0 + max(0.0, drop))

        # extra stability metrics (v1.2)
        om_mean_before = float(np.mean(Om))
        om_mean_after  = float(np.mean(Om2))
        om_std_before  = float(np.std(Om))
        om_std_after   = float(np.std(Om2))

        # timewise invariance: mean |Ω_noisy(t) - Ω_base(t)|
        omega_t = np.mean(Om, axis=1)
        omega_t2 = np.mean(Om2, axis=1)
        omega_time_L1 = float(np.mean(np.abs(omega_t2 - omega_t)))

        log(f"dphi_std            : {dP_std:.6g}")
        log(f"noise_sigma         : {sigma:.6g}")
        log(f"omega_mean_before   : {om_mean_before:.6g}")
        log(f"omega_mean_after    : {om_mean_after:.6g}")
        log(f"omega_std_before    : {om_std_before:.6g}")
        log(f"omega_std_after     : {om_std_after:.6g}")
        log(f"omega_diff_L1       : {omega_diff:.6g}")
        log(f"omega_time_L1       : {omega_time_L1:.6g}")
        log(f"noise_immunity_index: {noise_immunity:.6g}")
        log(f"basin_drop_index    : {basin_drop:.6g}")

        # 5) visuals (timestamped)
        p1 = vis_d / f"prime_dphi_baseline_{ts}.png"
        p2 = vis_d / f"prime_dphi_noisy_{ts}.png"
        p3 = vis_d / f"prime_omega_noise_immunity_{ts}.png"

        safe_write_img(p1, dP,  "Prime dPhi field (baseline)")
        safe_write_img(p2, dP2, "Prime dPhi field (noisy)")

        plt.figure()
        plt.plot(omega_t,  label="Omega baseline")
        plt.plot(omega_t2, label="Omega noisy", linestyle="--")
        plt.legend()
        plt.title("Omega-basin invariance curve")
        plt.xlabel("t")
        plt.ylabel("Omega(t)")
        plt.savefig(p3, bbox_inches="tight")
        plt.close()

        # 6) state JSON
        state_path = state_d / f"prime_omega_state_{ts}.json"
        state = {
            "protocol":"CodexPrimeOmegaBasin",
            "version":"1.2",
            "timestamp":now_iso(),
            "prime_limit":int(limit),
            "T":int(T),
            "noise_level":float(noise_level),
            "shape":{"T":int(V.shape[0]), "gaps":int(V.shape[1])},
            "metrics":{
                "gap_mean": gap_mean,
                "gap_std":  gap_std,
                "gap_max":  gap_max,
                "dphi_std": dP_std,
                "noise_sigma": sigma,
                "omega_mean_before": om_mean_before,
                "omega_mean_after":  om_mean_after,
                "omega_std_before":  om_std_before,
                "omega_std_after":   om_std_after,
                "omega_diff_L1": omega_diff,
                "omega_time_L1": omega_time_L1,
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
                "H19":"Global dPhi integration",
                "H20":"Omega-basin invariance / noise-immunity",
                "law":"Omega = 1/(1+|dPhi|)"
            }
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log(f"State -> {state_path}")

        # 7) ledger append
        ledger_path = ledger_d / "prime_omega_ledger.jsonl"
        row = {
            "timestamp":now_iso(),
            "version":"1.2",
            "prime_limit":int(limit),
            "T":int(T),
            "noise_level":float(noise_level),
            "omega_diff_L1":omega_diff,
            "omega_time_L1":omega_time_L1,
            "noise_immunity_index":noise_immunity,
            "basin_drop_index":basin_drop
        }
        with ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

        log("PRIME OMEGA-BASIN v1.2 complete.")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(ascii_safe(err) + "\n")
            f.write(ascii_safe(traceback.format_exc()) + "\n")
        return 1

if __name__=="__main__":
    if len(sys.argv) != 9:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS LIMIT NOISE T", file=sys.stderr)
        sys.exit(1)

    _, root, state, vis, led, logs, lim, noise, T = sys.argv
    code = main(root, state, vis, led, logs, int(lim), float(noise), int(T))
    sys.exit(code)
