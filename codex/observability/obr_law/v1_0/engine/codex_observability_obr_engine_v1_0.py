#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  CODEX–OBSERVABILITY OBR v1.0 — BOUNDARY RESIDUE OBSERVATORY   ║
# ║  Instruments: cutoff renorm, EFT decimation, horizon mask,     ║
# ║  trace reduction analogue. Emits O(lambda) curves + audits.    ║
# ╚══════════════════════════════════════════════════════════════╝

import sys, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def parse_csv_floats(s: str):
    out = []
    for x in (s or "").split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float(x))
    out = sorted(list(dict.fromkeys(out)))
    return out or [0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

def l2(x):
    x = np.asarray(x)
    return float(np.sqrt(np.mean(np.square(np.abs(x))) + 1e-12))

def detect_monotone_decreasing(y, tol=1e-9):
    # allow tiny numerical wiggles
    for i in range(1, len(y)):
        if y[i] > y[i-1] + tol:
            return False
    return True

def sharp_drop_index(y, frac=0.20):
    # first index where relative drop vs previous exceeds frac
    for i in range(1, len(y)):
        prev = max(y[i-1], 1e-12)
        if (prev - y[i]) / prev >= frac:
            return i
    return None

# ─────────────────────────────────────────────────────────────
# Instrument A: Cutoff Renorm (divergent substrate -> cutoff residue)
# Substrate X_sub(k) ~ 1/k (harmonic divergence). Boundary λ controls cutoff.
# Π_{λ}: keep k <= K(λ), discard higher (screened UV).
# O(λ) = ||keep|| / ||full|| computed with finite max K0 (instrument window).
def instr_cutoff_renorm(K0: int, lambdas):
    k = np.arange(1, K0+1, dtype=np.float64)
    X = 1.0 / k
    full = l2(X)
    O = []
    for lam in lambdas:
        # lam in [0,1]: stronger boundary means smaller cutoff
        # K(λ) decreases with λ
        K = int(max(1, round(K0 * (1.0 - 0.95*lam))))
        Y = X.copy()
        Y[K:] = 0.0
        O.append(l2(Y)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument B: EFT Decimation (UV Fourier modes -> IR residue)
# Substrate is a signal with broad spectrum. Boundary λ controls low-pass cutoff.
def instr_eft_decimation(N: int, lambdas, seed=1337):
    rng = np.random.default_rng(seed)
    # broad-band substrate: mixture of sinusoids + noise
    t = np.linspace(0.0, 1.0, N, endpoint=False)
    X = (np.sin(2*np.pi*7*t) + 0.7*np.sin(2*np.pi*53*t) + 0.5*np.sin(2*np.pi*211*t))
    X = X + 0.35*rng.normal(0.0, 1.0, size=N)
    full = l2(X)

    F = np.fft.rfft(X)
    freqs = np.fft.rfftfreq(N, d=1.0/N)
    fmax = freqs.max()

    O = []
    for lam in lambdas:
        # stronger boundary -> lower cutoff
        cutoff = fmax * max(0.02, (1.0 - 0.98*lam))
        G = F.copy()
        G[freqs > cutoff] = 0.0
        Y = np.fft.irfft(G, n=N)
        O.append(l2(Y)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument C: Horizon Mask (inside/outside residue)
# Substrate is a 2D field. Boundary λ controls mask radius: what escapes.
def instr_horizon_mask(N: int, lambdas, seed=2025):
    rng = np.random.default_rng(seed)
    # synthetic "bulk" field: smooth + noise
    x = np.linspace(-1.0, 1.0, N)
    X, Y = np.meshgrid(x, x, indexing="xy")
    field = np.exp(-(X*X + Y*Y)*2.0) + 0.25*np.sin(6*X)*np.cos(5*Y)
    field += 0.20*rng.normal(0.0, 1.0, size=(N, N))
    full = l2(field)

    r = np.sqrt(X*X + Y*Y)
    O = []
    for lam in lambdas:
        # stronger boundary -> smaller escape region (outside horizon shrinks)
        # define escape as r >= r0(λ)
        r0 = 0.10 + 0.85*lam
        mask = (r >= r0).astype(np.float64)
        residue = field * mask
        O.append(l2(residue)/full)
    return np.array(O, dtype=np.float64)

# ─────────────────────────────────────────────────────────────
# Instrument D: Trace Reduction Analogue (reduced subsystem observables)
# Build a random bipartite state vector |ψ> over A⊗B of dims (dA,dB).
# Boundary λ controls "environment size" effectively traced (stronger -> more traced).
# We model it by mixing reduced rho_A with maximally mixed component.
def instr_trace_reduction(dA: int, dB: int, lambdas, seed=7):
    rng = np.random.default_rng(seed)
    dim = dA*dB
    psi = rng.normal(0.0, 1.0, size=dim) + 1j*rng.normal(0.0, 1.0, size=dim)
    psi = psi / np.linalg.norm(psi)
    # rho = |psi><psi|
    rho = np.outer(psi, np.conjugate(psi))
    # partial trace over B -> rho_A
    rhoA = np.zeros((dA, dA), dtype=np.complex128)
    for i in range(dA):
        for j in range(dA):
            # sum over B index
            s = 0.0+0.0j
            for b in range(dB):
                s += rho[i*dB+b, j*dB+b]
            rhoA[i, j] = s

    # baseline "observable content" as purity deviation from maximally mixed
    I = np.eye(dA, dtype=np.complex128)/float(dA)
    full = l2(rhoA - I)

    O = []
    for lam in lambdas:
        # stronger boundary -> more effective tracing / decoherence in A
        # mix rhoA towards maximally mixed
        rhoA_lam = (1.0 - lam)*rhoA + lam*I
        O.append(l2(rhoA_lam - I)/max(full, 1e-12))
    return np.array(O, dtype=np.float64)

def save_curve_png(path, lambdas, y, title, ylabel):
    plt.figure()
    plt.plot(lambdas, y, marker="o")
    plt.axhline(H7, linestyle="--")
    plt.title(title)
    plt.xlabel("lambda (boundary strength)")
    plt.ylabel(ylabel)
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def main(root, state_d, vis_d, ledger_d, logs_d, N, K, lambda_csv):
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
        lambdas = parse_csv_floats(lambda_csv)
        lambdas = [max(0.0, min(1.0, float(x))) for x in lambdas]
        lambdas = sorted(list(dict.fromkeys(lambdas)))

        log("CODEX–OBSERVABILITY OBR v1.0 starting...")
        log(f"N            : {N}")
        log(f"K            : {K}")
        log(f"lambda_sweep  : {lambdas}")
        log(f"H7           : {H7}")

        # Compute instruments
        A = instr_cutoff_renorm(int(K), lambdas)
        B = instr_eft_decimation(int(N), lambdas)
        C = instr_horizon_mask(max(64, int(N//32)), lambdas)   # 2D field uses smaller grid
        D = instr_trace_reduction(dA=16, dB=16, lambdas=lambdas)

        instruments = {
            "cutoff_renorm": A,
            "eft_decimation": B,
            "horizon_mask": C,
            "trace_reduction": D
        }

        # audits
        audits = {}
        for name, y in instruments.items():
            mono = detect_monotone_decreasing(list(y))
            drop = sharp_drop_index(list(y), frac=0.20)
            audits[name] = {
                "monotone_decreasing": bool(mono),
                "sharp_drop_index": int(drop) if drop is not None else None,
                "sharp_drop_lambda": float(lambdas[drop]) if drop is not None else None,
                "H7_cross_index": int(next((i for i,v in enumerate(y) if v < H7), -1)),
            }
            log(f"{name}: monotone={mono} drop_idx={drop} H7_cross_idx={audits[name]['H7_cross_index']}")

        # Aggregate: mean curve (instrument ensemble)
        Y = np.vstack([A, B, C, D]).astype(np.float64)
        mean_curve = np.mean(Y, axis=0)
        min_curve  = np.min(Y, axis=0)
        max_curve  = np.max(Y, axis=0)

        # visuals
        pA = vis_d / f"obr_O_lambda_cutoff_renorm_{ts}.png"
        pB = vis_d / f"obr_O_lambda_eft_decimation_{ts}.png"
        pC = vis_d / f"obr_O_lambda_horizon_mask_{ts}.png"
        pD = vis_d / f"obr_O_lambda_trace_reduction_{ts}.png"
        pE = vis_d / f"obr_O_lambda_ensemble_{ts}.png"

        save_curve_png(pA, lambdas, A, "OBR v1.0 — Cutoff Renorm: O(lambda)", "O(lambda)")
        save_curve_png(pB, lambdas, B, "OBR v1.0 — EFT Decimation: O(lambda)", "O(lambda)")
        save_curve_png(pC, lambdas, C, "OBR v1.0 — Horizon Mask: O(lambda)", "O(lambda)")
        save_curve_png(pD, lambdas, D, "OBR v1.0 — Trace Reduction: O(lambda)", "O(lambda)")

        plt.figure()
        plt.plot(lambdas, mean_curve, marker="o", label="mean")
        plt.plot(lambdas, min_curve,  marker=None, linestyle="--", label="min")
        plt.plot(lambdas, max_curve,  marker=None, linestyle="--", label="max")
        plt.axhline(H7, linestyle=":")
        plt.legend()
        plt.title("OBR v1.0 — Ensemble O(lambda) (mean/min/max)")
        plt.xlabel("lambda (boundary strength)")
        plt.ylabel("O(lambda)")
        plt.savefig(pE, bbox_inches="tight")
        plt.close()

        # state artifact
        state_path = state_d / f"obr_state_{ts}.json"
        state = {
            "protocol": "CodexObservabilityOBR",
            "version": "1.0",
            "timestamp": now_iso(),
            "params": {
                "N": int(N),
                "K": int(K),
                "lambda_sweep": lambdas
            },
            "H7": H7,
            "instruments": {k: [float(x) for x in v] for k, v in instruments.items()},
            "ensemble": {
                "mean": [float(x) for x in mean_curve],
                "min":  [float(x) for x in min_curve],
                "max":  [float(x) for x in max_curve],
            },
            "audits": audits,
            "visuals": {
                "cutoff_renorm": str(pA),
                "eft_decimation": str(pB),
                "horizon_mask": str(pC),
                "trace_reduction": str(pD),
                "ensemble": str(pE),
            },
            "codex": {
                "law": "X_obs = Pi_{∂,λ}(X_sub)",
                "observability_functional": "O(λ)=||Pi_{∂,λ}(X)||/||X||",
                "notes": [
                    "Toy instruments: observational only; do not claim new physics.",
                    "Twin-primes discipline: sweep boundaries; audit monotonic survival; detect sharp admissibility drops.",
                    "Geometry-first: outputs are artifacts; narrative downstream."
                ]
            }
        }
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        log(f"State -> {state_path}")

        # ledger append (one row per instrument + ensemble summary)
        ledger_path = ledger_d / "obr_ledger.jsonl"
        with ledger_path.open("a", encoding="utf-8") as f:
            for name, y in instruments.items():
                f.write(json.dumps({
                    "timestamp": now_iso(),
                    "version": "1.0",
                    "instrument": name,
                    "lambda_sweep": lambdas,
                    "O_lambda": [float(x) for x in y],
                    "audits": audits[name]
                }) + "\n")
            f.write(json.dumps({
                "timestamp": now_iso(),
                "version": "1.0",
                "instrument": "ensemble",
                "lambda_sweep": lambdas,
                "mean": [float(x) for x in mean_curve],
                "min":  [float(x) for x in min_curve],
                "max":  [float(x) for x in max_curve],
                "H7": H7
            }) + "\n")

        log("CODEX–OBSERVABILITY OBR v1.0 complete.")
        return 0

    except Exception as e:
        err = "ERROR: " + repr(e)
        print(err, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(err + "\n")
            f.write(traceback.format_exc() + "\n")
        return 1

if __name__ == "__main__":
    # Usage: engine ROOT STATE VIS LEDGER LOGS N K LAMBDA_CSV
    if len(sys.argv) < 9:
        print("Usage: engine ROOT STATE VIS LEDGER LOGS N K LAMBDA_CSV", file=sys.stderr)
        sys.exit(1)

    _, root, state, vis, led, logs, N, K, lambda_csv = sys.argv[:9]
    sys.exit(main(root, state, vis, led, logs, int(N), int(K), lambda_csv))
