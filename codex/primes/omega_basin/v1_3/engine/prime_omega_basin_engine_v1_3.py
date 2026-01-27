#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  PRIME OMEGA-BASIN v1.3 — NOISE-SWEEP + COLLAPSE DETECTOR     ║
# ║  v1.3: sweep noise levels; detect H7 collapse threshold       ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def ascii_safe(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")

def primes_up_to(N: int) -> np.ndarray:
    sieve = np.ones(N+1, dtype=bool)
    sieve[:2] = False
    r = int(N**0.5)
    for i in range(2, r+1):
        if sieve[i]:
            sieve[i*i:N+1:i] = False
    return np.nonzero(sieve)[0]

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

def main(root, state_d, vis_d, ledger_d, logs_d, limit, T, noise_levels_csv):
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
        # parse noise sweep
        noise_levels = []
        for x in (noise_levels_csv or "").split(","):
            x = x.strip()
            if not x:
                continue
            noise_levels.append(float(x))
        if not noise_levels:
            noise_levels = [0.0, 0.05, 0.10]

        log("PRIME OMEGA-BASIN v1.3 starting...")
        log(f"prime_limit  : {limit}")
        log(f"T            : {T}")
        log(f"noise_sweep  : {noise_levels}")

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

        # 2) baseline ΔΦ/Ω
        V  = build_gap_field(gaps, T=int(T))
        dP = dphi(V)
        Om = omega(dP)

        dP_std = float(np.std(dP)) if dP.size else 0.0
        omega_t = np.mean(Om, axis=1)

        log(f"dphi_std_base : {dP_std:.6g}")
        log(f"omega_mean_base : {float(np.mean(Om)):.6g}")

        # 3) sweep
        rows = []
        immunity = []
        omega_diff = []
        omega_time = []
        sigmas = []

        # lock RNG seed to make sweep comparable across runs (artifact stability)
        rng = np.random.default_rng(1337)

        for nl in noise_levels:
            sigma = float(nl) * max(dP_std, 1e-12)
            noise = rng.normal(0.0, sigma, size=dP.shape).astype(np.float32)
            dP2 = dP + noise
            Om2 = omega(dP2)

            omega_diff_L1 = float(np.mean(np.abs(Om2 - Om)))
            omega_t2 = np.mean(Om2, axis=1)
            omega_time_L1 = float(np.mean(np.abs(omega_t2 - omega_t)))

            noise_immunity_index = 1.0/(1.0 + max(0.0, omega_diff_L1))
            drop = float(np.mean(Om) - np.mean(Om2))
            basin_drop_index = 1.0/(1.0 + max(0.0, drop))

            rows.append({
                "timestamp": now_iso(),
                "version": "1.3",
                "prime_limit": int(limit),
                "T": int(T),
                "noise_level": float(nl),
                "noise_sigma": float(sigma),
                "omega_diff_L1": omega_diff_L1,
                "omega_time_L1": omega_time_L1,
                "noise_immunity_index": noise_immunity_index,
                "basin_drop_index": basin_drop_index
            })

            immunity.append(noise_immunity_index)
            omega_diff.append(omega_diff_L1)
            omega_time.append(omega_time_L1)
            sigmas.append(sigma)

            log(f"noise={nl:.4g} sigma={sigma:.6g} immunity={noise_immunity_index:.6g} omega_diff={omega_diff_L1:.6g} omega_time={omega_time_L1:.6g}")

        # 4) collapse detection vs H7
        collapse_idx = None
        for i, val in enumerate(immunity):
            if val < H7:
                collapse_idx = i
                break

        collapse_noise = float(noise_levels[collapse_idx]) if collapse_idx is not None else None
        collapse_sigma = float(sigmas[collapse_idx]) if collapse_idx is not None else None

        # 5) visuals
        p_curve = vis_d / f"prime_omega_immunity_vs_noise_{ts}.png"
        p_diff  = vis_d / f"prime_omega_diff_vs_noise_{ts}.png"
        p_time  = vis_d / f"prime_omega_time_vs_noise_{ts}.png"

        plt.figure()
        plt.plot(noise_levels, immunity, marker="o")
        plt.axhline(H7, linestyle="--")
        plt.title("Noise immunity vs noise level (H7 threshold)")
        plt.xlabel("noise_level")
        plt.ylabel("noise_immunity_index")
        if collapse_noise is not None:
            plt.axvline(collapse_noise, linestyle=":")
        plt.savefig(p_curve, bbox_inches="tight")
        plt.close()

        plt.figure()
        plt.plot(noise_levels, omega_diff, marker="o")
        plt.title("Omega_diff_L1 vs noise level")
        plt.xlabel("noise_level")
        plt.ylabel("omega_diff_L1")
        plt.savefig(p_diff, bbox_inches="tight")
        plt.close()

        plt.figure()
        plt.plot(noise_levels, omega_time, marker="o")
        plt.title("Omega_time_L1 vs noise level")
        plt.xlabel("noise_level")
        plt.ylabel("omega_time_L1")
        plt.savefig(p_time, bbox_inches="tight")
        plt.close()

        # 6) state JSON
        state_path = state_d / f"prime_omega_state_{ts}.json"
        state = {
            "protocol": "CodexPrimeOmegaBasin",
            "version": "1.3",
            "timestamp": now_iso(),
            "prime_limit": int(limit),
            "T": int(T),
            "noise_sweep": noise_levels,
            "baseline": {
                "gap_mean": gap_mean,
                "gap_std":  gap_std,
                "gap_max":  gap_max,
                "dphi_std": dP_std,
                "omega_mean": float(np.mean(Om))
            },
            "sweep_rows": rows,
            "collapse": {
                "H7": H7,
                "collapse_detected": collapse_idx is not None,
                "collapse_noise_level": collapse_noise,
                "collapse_sigma": collapse_sigma
            },
            "visuals": {
                "immunity_vs_noise": str(p_curve),
                "omega_diff_vs_noise": str(p_diff),
                "omega_time_vs_noise": str(p_time)
            },
            "codex": {
                "H7": H7,
                "H19": "Global dPhi integration",
                "H20": "Omega-basin invariance / noise-immunity",
                "law": "Omega = 1/(1+|dPhi|)"
            }
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log(f"State -> {state_path}")

        # 7) ledger append (one row per noise level + summary row)
        ledger_path = ledger_d / "prime_omega_ledger.jsonl"
        with ledger_path.open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.write(json.dumps({
                "timestamp": now_iso(),
                "version": "1.3",
                "prime_limit": int(limit),
                "T": int(T),
                "event": "collapse_summary",
                "H7": H7,
                "collapse_detected": collapse_idx is not None,
                "collapse_noise_level": collapse_noise,
                "collapse_sigma": collapse_sigma
            }) + "\n")

        log("PRIME OMEGA-BASIN v1.3 complete.")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(ascii_safe(err) + "\n")
            f.write(ascii_safe(traceback.format_exc()) + "\n")
        return 1

if __name__ == "__main__":
    # Usage: engine ROOT STATE VIS LEDGER LOGS LIMIT T NOISE_CSV
    if len(sys.argv) != 9:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS LIMIT T NOISE_SWEEP_CSV", file=sys.stderr)
        sys.exit(1)

    _, root, state, vis, led, logs, lim, T, noise_csv = sys.argv
    code = main(root, state, vis, led, logs, int(lim), int(T), noise_csv)
    sys.exit(code)
