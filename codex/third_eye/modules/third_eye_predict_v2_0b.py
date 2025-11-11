#!/usr/bin/env python3
# third_eye_predict_v2_0b.py — Adaptive Predictive Mode
import os, json, math, hashlib, datetime, statistics
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CODEX_ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
HANDOFF    = os.path.join(CODEX_ROOT, "codex","handoff","handoff_state.json")
OUT_DIR    = os.path.join(CODEX_ROOT, "codex","third_eye")
STATE_DIR  = os.path.join(OUT_DIR,"state")
VIS_DIR    = os.path.join(OUT_DIR,"visuals")
LOGS_DIR   = os.path.join(OUT_DIR,"logs")
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CFG = {
    "version": "v2.0B",
    "H7": 0.70,             # Codex critical coherence constant
    "forecast_horizon": 32, # steps to forecast ahead
    "ewma_alpha": 0.22,     # EWMA smoothing
    "poly_deg": 2,          # quadratic
    "blend": 0.55,          # EWMA/Poly blend weight (EWMA dominates slightly)
    "plot": True
}

def _nanmean(x):
    arr = np.array(x, dtype=float)
    if arr.size == 0: return float("nan")
    return float(np.nanmean(arr))

def _ewma(x, alpha):
    if len(x)==0: return []
    y=[x[0]]
    for i in range(1,len(x)):
        y.append(alpha*x[i] + (1-alpha)*y[-1])
    return y

def _poly_forecast(x, steps=16, deg=2):
    if len(x) < deg+1:  # fallback: replicate last value
        return [x[-1]]*steps if x else [0.0]*steps
    xx = np.arange(len(x), dtype=float)
    coeffs = np.polyfit(xx, np.array(x, dtype=float), deg=deg)
    p = np.poly1d(coeffs)
    futx = np.arange(len(x), len(x)+steps, dtype=float)
    return list(map(float, p(futx)))

def _bound01(seq):
    return [max(0.0, min(1.0, float(v))) for v in seq]

def _median_last(seq, k=8):
    if len(seq)==0: return float("nan")
    window = seq[-k:] if len(seq)>=k else seq[:]
    return float(np.median(window))

def _last_increase(seq, k=8):
    if len(seq) < 2: return 0.0
    window = seq[-k:] if len(seq)>=k else seq[:]
    diffs = np.diff(window)
    return float(np.nanmean(diffs)) if len(diffs)>0 else 0.0

def load_handoff(path):
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)

def extract_traces(handoff):
    # Expect quantum[].summary.{Phi_mean,C_mean} and optional per-run series in quantum[*]
    C_means=[]; Phi_means=[]
    runs=[]
    for q in handoff.get("quantum", []):
        sm = (q.get("summary") or {})
        C_means.append(sm.get("C_mean"))
        Phi_means.append(sm.get("Phi_mean"))
        # graceful handling if timeseries present
        C_t  = q.get("C_t")
        Phi_t= q.get("Phi_t")
        runs.append({"C_t":C_t,"Phi_t":Phi_t})
    # Ensemble series (align by min length for crude stacking)
    def stack_mean(key):
        series = [r.get(key) for r in runs if isinstance(r.get(key), list) and len(r.get(key))>0]
        if not series: return []
        L = min(len(s) for s in series)
        arr = np.array([s[:L] for s in series], dtype=float)
        return list(np.nanmean(arr, axis=0))
    C_t_mean  = stack_mean("C_t")
    Phi_t_mean= stack_mean("Phi_t")
    return {
        "C_means": [v for v in C_means if v is not None],
        "Phi_means": [v for v in Phi_means if v is not None],
        "C_t_mean": C_t_mean,
        "Phi_t_mean": Phi_t_mean
    }

def forecast_series(series, horizon, cfg=CFG):
    if not series: 
        return {"baseline": [], "ewma": [], "poly": [], "blend": []}
    # Normalize to [0,1] soft for coherence-like behavior
    base = list(series)
    ewma_all = _ewma(base, cfg["ewma_alpha"])
    ewma_last = ewma_all[-1] if ewma_all else (base[-1] if base else 0.0)
    ewma_future = [ewma_last]*horizon
    poly_future = _poly_forecast(base, steps=horizon, deg=cfg["poly_deg"])
    # blend
    blend = [cfg["blend"]*e + (1.0-cfg["blend"])*p for e,p in zip(ewma_future, poly_future)]
    return {
        "baseline": base,
        "ewma": ewma_future,
        "poly": poly_future,
        "blend": blend
    }

def plot_forecast(name, hist, fut, h7, out_png):
    if not hist and not fut: return
    plt.figure(figsize=(9,4.6))
    xs = np.arange(len(hist))
    plt.plot(xs, hist, label=f"{name}(t)")
    if fut:
        fx = np.arange(len(hist), len(hist)+len(fut))
        plt.plot(fx, fut, label=f"{name} forecast")
    plt.axhline(h7, linestyle="--", label="H7 threshold")
    plt.xlabel("t"); plt.ylabel(name)
    plt.title(f"Third Eye v2.0B — {name} forecast")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()

def main():
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not os.path.exists(HANDOFF):
        raise FileNotFoundError(f"handoff_state.json not found at {HANDOFF}")
    h = load_handoff(HANDOFF)
    traces = extract_traces(h)

    # recent stats
    C_hist = _bound01(traces["C_t_mean"])
    Phi_hist = traces["Phi_t_mean"]
    C_med = _median_last(C_hist, 12)
    C_drift = _last_increase(C_hist, 8)
    C_mean_ensemble = _nanmean(traces["C_means"])
    Phi_mean_ensemble = _nanmean(traces["Phi_means"])

    # forecasts
    C_fc = forecast_series(C_hist, CFG["forecast_horizon"], CFG)
    Phi_fc = forecast_series(Phi_hist, CFG["forecast_horizon"], CFG)

    # recommendation logic
    rec = "stabilize"
    if not math.isnan(C_med) and C_med >= CFG["H7"]:
        rec = "amplify"
    if C_drift > 0.002 and (C_med >= 0.6):
        rec = "resonant"
    if C_med < 0.2 and C_drift <= 0:
        rec = "dormant"

    # write summary JSON
    out = {
        "meta": {
            "version": CFG["version"],
            "timestamp": stamp,
            "source": "codex_third_eye_v2_0b",
            "handoff_hash": hashlib.md5(json.dumps(h.get("meta", {}), sort_keys=True).encode()).hexdigest()[:8] if h.get("meta") else None
        },
        "inputs": {
            "C_mean_ensemble": C_mean_ensemble,
            "Phi_mean_ensemble": Phi_mean_ensemble,
            "C_hist_len": len(C_hist),
            "Phi_hist_len": len(Phi_hist),
        },
        "recent": {
            "C_median_last12": C_med,
            "C_drift_last8": C_drift
        },
        "forecast": {
            "C_blend": C_fc["blend"],
            "Phi_blend": Phi_fc["blend"],
            "horizon": CFG["forecast_horizon"]
        },
        "thresholds": {
            "H7": CFG["H7"]
        },
        "recommendation": rec
    }
    out_name = os.path.join(STATE_DIR, "predictive_summary_v2_0b.json")
    with open(out_name,"w",encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    # plots
    if CFG["plot"]:
        c_png = os.path.join(VIS_DIR, "C_forecast_v2_0b.png")
        p_png = os.path.join(VIS_DIR, "Phi_forecast_v2_0b.png")
        plot_forecast("C", C_hist, out["forecast"]["C_blend"], CFG["H7"], c_png)
        plot_forecast("Phi", Phi_hist, out["forecast"]["Phi_blend"], CFG["H7"], p_png)

    print(f"[ThirdEye v2.0B] wrote {out_name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
