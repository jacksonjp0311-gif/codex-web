#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  CODEX–OBSERVABILITY OBR v1.1 — H₇ FIXED-POINT RESIDUE ENGINE  ║
# ║  Adds Ω-basin noise-immunity sweeps + H₇ ridge detection.      ║
# ║  Geometry-first artifacts. Narrative downstream.              ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt

# H₇: projection-shadow band of a geometric fixed point (not a universal constant)
H7 = 0.70

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def parse_csv_floats(s: str, default=None):
    out = []
    for x in (s or "").split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float(x))
    out = sorted(list(dict.fromkeys(out)))
    if out:
        return out
    return default if default is not None else [0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

def l2(x):
    x = np.asarray(x)
    return float(np.sqrt(np.mean(np.square(np.abs(x))) + 1e-12))

def omega_from_dphi(dphi):
    # Ω regulator per Codex (H20 noise immunity theory): Ω = 1/(1+|ΔΦ|)
    return 1.0 / (1.0 + np.abs(dphi))

def detect_monotone_decreasing(y, tol=1e-9):
    for i in range(1, len(y)):
        if y[i] > y[i-1] + tol:
            return False
    return True

def sharp_drop_index(y, frac=0.20):
    for i in range(1, len(y)):
        prev = max(y[i-1], 1e-12)
        if (prev - y[i]) / prev >= frac:
            return i
    return None

def first_cross_below(y, thresh):
    for i, v in enumerate(y):
        if v < thresh:
            return i
    return -1

def ridge_index_near(y, target=H7):
    # pick index minimizing |y-target|
    y = list(y)
    j = int(min(range(len(y)), key=lambda i: abs(y[i]-target)))
    return j

# ─────────────────────────────────────────────────────────────
# Instrument A: Cutoff Renorm
def instr_cutoff_renorm(K0: int, lambdas):
    k = np.arange(1, K0+1, dtype=np.float64)
    X = 1.0 / k
    full = l2(X)
    O = []
    for lam in lambdas:
        K = int(max(1, round(K0 * (1.0 - 0.95*lam))))
        Y = X.copy()
        Y[K:] = 0.0
        O.append(l2(Y)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument B: EFT Decimation
def instr_eft_decimation(N: int, lambdas, seed=1337):
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, N, endpoint=False)
    X = (np.sin(2*np.pi*7*t) + 0.7*np.sin(2*np.pi*53*t) + 0.5*np.sin(2*np.pi*211*t))
    X = X + 0.35*rng.normal(0.0, 1.0, size=N)
    full = l2(X)
    F = np.fft.rfft(X)
    freqs = np.fft.rfftfreq(N, d=1.0/N)
    fmax = freqs.max()
    O = []
    for lam in lambdas:
        cutoff = fmax * max(0.02, (1.0 - 0.98*lam))
        G = F.copy()
        G[freqs > cutoff] = 0.0
        Y = np.fft.irfft(G, n=N)
        O.append(l2(Y)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument C: Horizon Mask
def instr_horizon_mask(N: int, lambdas, seed=2025):
    rng = np.random.default_rng(seed)
    x = np.linspace(-1.0, 1.0, N)
    X, Y = np.meshgrid(x, x, indexing="xy")
    field = np.exp(-(X*X + Y*Y)*2.0) + 0.25*np.sin(6*X)*np.cos(5*Y)
    field += 0.20*rng.normal(0.0, 1.0, size=(N, N))
    full = l2(field)
    r = np.sqrt(X*X + Y*Y)
    O = []
    for lam in lambdas:
        r0 = 0.10 + 0.85*lam
        mask = (r >= r0).astype(np.float64)
        residue = field * mask
        O.append(l2(residue)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument D: Trace Reduction Analogue
def instr_trace_reduction(dA: int, dB: int, lambdas, seed=7):
    rng = np.random.default_rng(seed)
    dim = dA*dB
    psi = rng.normal(0.0, 1.0, size=dim) + 1j*rng.normal(0.0, 1.0, size=dim)
    psi = psi / np.linalg.norm(psi)
    rho = np.outer(psi, np.conjugate(psi))
    rhoA = np.zeros((dA, dA), dtype=np.complex128)
    for i in range(dA):
        for j in range(dA):
            s = 0.0+0.0j
            for b in range(dB):
                s += rho[i*dB+b, j*dB+b]
            rhoA[i, j] = s
    I = np.eye(dA, dtype=np.complex128)/float(dA)
    full = l2(rhoA - I)
    O = []
    for lam in lambdas:
        rhoA_lam = (1.0 - lam)*rhoA + lam*I
        O.append(l2(rhoA_lam - I)/max(full, 1e-12))
    return np.array(O, dtype=np.float64)

def save_curve_png(path, x, y, title, ylabel, hline=None):
    plt.figure()
    plt.plot(x, y, marker="o")
    if hline is not None:
        plt.axhline(hline, linestyle="--")
    plt.title(title)
    plt.xlabel("lambda (boundary strength)")
    plt.ylabel(ylabel)
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def save_noise_heatmap(path, lambdas, sigmas, Z, title):
    # Z shape: (len(sigmas), len(lambdas))
    plt.figure()
    plt.imshow(Z, aspect="auto", origin="lower",
               extent=[min(lambdas), max(lambdas), min(sigmas), max(sigmas)])
    plt.colorbar(label="E[Ω·𝒪(λ,σ)]")
    plt.title(title)
    plt.xlabel("lambda (boundary strength)")
    plt.ylabel("sigma (noise amplitude)")
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def compute_omega_weighted_observability(base_O, sigmas, trials, seed=1337):
    """
    Ω-basin noise immunity sweep:
      Treat λ as boundary strength.
      Inject bounded noise into a synthetic ΔΦ(λ) = 1/O(λ) - 1 (inverse map),
      then compute Ω = 1/(1+|ΔΦ|) after noise, and weight observability:
         O_Ω(λ,σ) = E[ Ω(ΔΦ+ε) * O(λ) ].
    This enforces the v2.1 framing: H7 is a fixed-point geometry shadow
    under residual error + nonlinear weighting + survival (bounded noise).
    """
    base_O = np.asarray(base_O, dtype=np.float64)
    dphi = (1.0/np.maximum(base_O, 1e-12)) - 1.0  # invert C=1/(1+|ΔΦ|) style mapping
    rng = np.random.default_rng(seed)
    sigmas = list(sigmas)
    Z = np.zeros((len(sigmas), len(base_O)), dtype=np.float64)
    for si, sigma in enumerate(sigmas):
        vals = []
        for _ in range(int(trials)):
            eps = rng.normal(0.0, 1.0, size=dphi.shape) * float(sigma)
            dphi_n = dphi + eps
            om = omega_from_dphi(dphi_n)
            vals.append(om * base_O)
        Z[si, :] = np.mean(np.vstack(vals), axis=0)
    return Z

def audits_for_curve(lambdas, y):
    mono = detect_monotone_decreasing(list(y))
    drop = sharp_drop_index(list(y), frac=0.20)
    a = {
        "monotone_decreasing": bool(mono),
        "sharp_drop_index": int(drop) if drop is not None else None,
        "sharp_drop_lambda": float(lambdas[drop]) if drop is not None else None,
        "H7_cross_index": int(first_cross_below(list(y), H7)),
        "H7_ridge_index": int(ridge_index_near(list(y), H7)),
        "H7_ridge_lambda": float(lambdas[ridge_index_near(list(y), H7)]),
        "H7_ridge_value": float(y[ridge_index_near(list(y), H7)]),
    }
    return a

def main(root, state_d, vis_d, ledger_d, logs_d, N, K, lambda_csv, noise_csv, noise_trials, seed):
    root = Path(root)
    state_d = Path(state_d); vis_d = Path(vis_d)
    ledger_d = Path(ledger_d); logs_d = Path(logs_d)
    for d in (state_d, vis_d, ledger_d, logs_d):
        d.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = logs_d / f"obr_run_{ts}.log"

    def log(msg):
        print(msg)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")

    try:
        lambdas = parse_csv_floats(lambda_csv, default=[0.0,0.1,0.2,0.4,0.6,0.8,1.0])
        lambdas = [max(0.0, min(1.0, float(x))) for x in lambdas]
        lambdas = sorted(list(dict.fromkeys(lambdas)))

        sigmas = parse_csv_floats(noise_csv, default=[0.0,0.05,0.10,0.20,0.30])
        sigmas = [max(0.0, float(x)) for x in sigmas]
        sigmas = sorted(list(dict.fromkeys(sigmas)))

        log("CODEX–OBSERVABILITY OBR v1.1 starting...")
        log(f"N             : {int(N)}")
        log(f"K             : {int(K)}")
        log(f"lambda_sweep   : {lambdas}")
        log(f"noise_sweep σ  : {sigmas}")
        log(f"noise_trials   : {int(noise_trials)}")
        log(f"seed           : {int(seed)}")
        log(f"H7 (shadow)    : {H7}")

        # base instruments
        A = instr_cutoff_renorm(int(K), lambdas)
        B = instr_eft_decimation(int(N), lambdas, seed=int(seed))
        C = instr_horizon_mask(max(64, int(N//32)), lambdas, seed=2025)
        D = instr_trace_reduction(dA=16, dB=16, lambdas=lambdas, seed=7)

        instruments = {
            "cutoff_renorm": A,
            "eft_decimation": B,
            "horizon_mask": C,
            "trace_reduction": D
        }

        audits = {}
        for name, y in instruments.items():
            audits[name] = audits_for_curve(lambdas, y)
            log(f"{name}: monotone={audits[name]['monotone_decreasing']} "
                f"drop_idx={audits[name]['sharp_drop_index']} "
                f"H7_cross_idx={audits[name]['H7_cross_index']} "
                f"H7_ridge@{audits[name]['H7_ridge_lambda']}={audits[name]['H7_ridge_value']:.6f}"
            )

        # ensemble
        Y = np.vstack([A, B, C, D]).astype(np.float64)
        mean_curve = np.mean(Y, axis=0)
        min_curve  = np.min(Y, axis=0)
        max_curve  = np.max(Y, axis=0)
        audits["ensemble"] = audits_for_curve(lambdas, mean_curve)

        # Ω-weighted observability (H20 noise immunity sweep) for ensemble mean
        Z = compute_omega_weighted_observability(mean_curve, sigmas, int(noise_trials), seed=int(seed))

        # Derived ridge under noise: pick per-sigma ridge idx near H7
        ridge_by_sigma = []
        for si, sigma in enumerate(sigmas):
            ysig = Z[si, :]
            j = ridge_index_near(ysig, H7)
            ridge_by_sigma.append({
                "sigma": float(sigma),
                "H7_ridge_index": int(j),
                "H7_ridge_lambda": float(lambdas[j]),
                "H7_ridge_value": float(ysig[j]),
                "H7_cross_index": int(first_cross_below(list(ysig), H7)),
            })

        # visuals
        pA = vis_d / f"obr_O_lambda_cutoff_renorm_{ts}.png"
        pB = vis_d / f"obr_O_lambda_eft_decimation_{ts}.png"
        pC = vis_d / f"obr_O_lambda_horizon_mask_{ts}.png"
        pD = vis_d / f"obr_O_lambda_trace_reduction_{ts}.png"
        pE = vis_d / f"obr_O_lambda_ensemble_{ts}.png"
        pF = vis_d / f"obr_OmegaWeighted_heatmap_{ts}.png"
        pG = vis_d / f"obr_OmegaWeighted_ridge_by_sigma_{ts}.png"

        save_curve_png(pA, lambdas, A, "OBR v1.1 — Cutoff Renorm: O(lambda)", "O(lambda)", hline=H7)
        save_curve_png(pB, lambdas, B, "OBR v1.1 — EFT Decimation: O(lambda)", "O(lambda)", hline=H7)
        save_curve_png(pC, lambdas, C, "OBR v1.1 — Horizon Mask: O(lambda)", "O(lambda)", hline=H7)
        save_curve_png(pD, lambdas, D, "OBR v1.1 — Trace Reduction: O(lambda)", "O(lambda)", hline=H7)

        plt.figure()
        plt.plot(lambdas, mean_curve, marker="o", label="mean")
        plt.plot(lambdas, min_curve,  linestyle="--", label="min")
        plt.plot(lambdas, max_curve,  linestyle="--", label="max")
        plt.axhline(H7, linestyle=":")
        plt.legend()
        plt.title("OBR v1.1 — Ensemble O(lambda) (mean/min/max)")
        plt.xlabel("lambda (boundary strength)")
        plt.ylabel("O(lambda)")
        plt.savefig(pE, bbox_inches="tight")
        plt.close()

        save_noise_heatmap(pF, lambdas, sigmas, Z, "OBR v1.1 — Ω·O(lambda,σ) (H20 noise immunity sweep)")

        # Ridge-vs-sigma plot
        plt.figure()
        plt.plot([r["sigma"] for r in ridge_by_sigma], [r["H7_ridge_value"] for r in ridge_by_sigma], marker="o", label="H7 ridge value")
        plt.axhline(H7, linestyle="--", label="H7 shadow")
        plt.title("OBR v1.1 — H7 Ridge Under Noise (Ω-weighted)")
        plt.xlabel("sigma (noise amplitude)")
        plt.ylabel("ridge value near H7")
        plt.legend()
        plt.savefig(pG, bbox_inches="tight")
        plt.close()

        # state artifact
        state_path = state_d / f"obr_state_{ts}.json"
        state = {
            "protocol": "CodexObservabilityOBR",
            "version": "1.1",
            "timestamp": now_iso(),
            "params": {
                "N": int(N),
                "K": int(K),
                "lambda_sweep": lambdas,
                "noise_sweep_sigma": sigmas,
                "noise_trials": int(noise_trials),
                "seed": int(seed)
            },
            "H7_shadow": H7,
            "instruments": {k: [float(x) for x in v] for k, v in instruments.items()},
            "ensemble": {
                "mean": [float(x) for x in mean_curve],
                "min":  [float(x) for x in min_curve],
                "max":  [float(x) for x in max_curve],
            },
            "omega_weighted": {
                "definition": "E[ Ω(ΔΦ+ε) * O(λ) ] with Ω=1/(1+|ΔΦ|), ΔΦ≈1/O-1",
                "sigma_sweep": sigmas,
                "O_omega_matrix": [[float(x) for x in row] for row in Z],
                "ridge_by_sigma": ridge_by_sigma
            },
            "audits": audits,
            "visuals": {
                "cutoff_renorm": str(pA),
                "eft_decimation": str(pB),
                "horizon_mask": str(pC),
                "trace_reduction": str(pD),
                "ensemble": str(pE),
                "omega_weighted_heatmap": str(pF),
                "omega_weighted_ridge_by_sigma": str(pG)
            },
            "codex": {
                "law": "X_obs = Pi_{∂,λ}(X_sub)",
                "observability_functional": "O(λ)=||Pi_{∂,λ}(X)||/||X||",
                "canon_upgrades": [
                    "H7 reframe: fixed-point geometry shadow (projection-dependent number).",
                    "H20: Ω-basin noise immunity enforced via Ω weighting under bounded perturbation.",
                    "777: boundary-excess selection is minimal defect beyond closure (conceptual alignment)."
                ],
                "notes": [
                    "Observational instrument. No new physics claim.",
                    "Compute-first: artifacts emitted; narrative downstream.",
                    "Falsify by removing alignment/weighting/survival and observing ridge collapse."
                ]
            }
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log(f"State -> {state_path}")

        # ledger append
        ledger_path = ledger_d / "obr_ledger.jsonl"
        with ledger_path.open("a", encoding="utf-8") as f:
            for name, y in instruments.items():
                f.write(json.dumps({
                    "timestamp": now_iso(),
                    "version": "1.1",
                    "instrument": name,
                    "lambda_sweep": lambdas,
                    "O_lambda": [float(x) for x in y],
                    "audits": audits[name]
                }) + "\n")
            f.write(json.dumps({
                "timestamp": now_iso(),
                "version": "1.1",
                "instrument": "ensemble",
                "lambda_sweep": lambdas,
                "mean": [float(x) for x in mean_curve],
                "min":  [float(x) for x in min_curve],
                "max":  [float(x) for x in max_curve],
                "audits": audits["ensemble"],
                "H7_shadow": H7
            }) + "\n")
            f.write(json.dumps({
                "timestamp": now_iso(),
                "version": "1.1",
                "instrument": "omega_weighted",
                "lambda_sweep": lambdas,
                "sigma_sweep": sigmas,
                "noise_trials": int(noise_trials),
                "seed": int(seed),
                "O_omega_matrix": [[float(x) for x in row] for row in Z],
                "ridge_by_sigma": ridge_by_sigma,
                "H7_shadow": H7
            }) + "\n")

        log("CODEX–OBSERVABILITY OBR v1.1 complete.")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(err + "\n")
            f.write(traceback.format_exc() + "\n")
        return 1

if __name__ == "__main__":
    # Usage: engine ROOT STATE VIS LEDGER LOGS N K LAMBDA_CSV NOISE_CSV NOISE_TRIALS SEED
    if len(sys.argv) < 12:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS N K LAMBDA_CSV NOISE_CSV NOISE_TRIALS SEED", file=sys.stderr)
        sys.exit(1)
    _, root, state, vis, led, logs, N, K, lambda_csv, noise_csv, noise_trials, seed = sys.argv[:12]
    sys.exit(main(root, state, vis, led, logs, int(N), int(K), lambda_csv, noise_csv, int(noise_trials), int(seed)))
