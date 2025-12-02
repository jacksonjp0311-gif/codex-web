#!/usr/bin/env python3
# 𓂀  Codex Finance Resonance Engine v1.0
# ΔΦ Geometry | Cusp Law v2.8 | GEO v1.0 | H7 / H7B / H16 / H19 / H31

import argparse
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

def load_timeseries_from_csv(path):
    import csv
    values = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        # Try 'value' column first, else first numeric column
        numeric_fields = []
        for row in reader:
            if not numeric_fields:
                for k, v in row.items():
                    try:
                        float(v)
                        numeric_fields.append(k)
                    except Exception:
                        continue
                if not numeric_fields:
                    raise ValueError("No numeric columns found in %s" % path)
            try:
                values.append(float(row[numeric_fields[0]]))
            except Exception:
                continue
    return np.array(values, dtype=float)

def load_timeseries_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    # Cases:
    #  • [1,2,3,...]
    #  • [{"value":x}, ...]
    if isinstance(data, list):
        vals = []
        for item in data:
            if isinstance(item, (int, float)):
                vals.append(float(item))
            elif isinstance(item, dict):
                if "value" in item:
                    vals.append(float(item["value"]))
        return np.array(vals, dtype=float)
    elif isinstance(data, dict) and "values" in data:
        return np.array([float(x) for x in data["values"]], dtype=float)
    else:
        raise ValueError("Unsupported JSON structure in %s" % path)

def load_all_series(input_dir):
    """Load all .csv/.json files as separate channels."""
    input_path = Path(input_dir)
    files = list(input_path.glob("*.csv")) + list(input_path.glob("*.json"))
    if not files:
        raise ValueError("No .csv or .json files in %s" % input_dir)

    channels = []
    names = []
    for f in files:
        try:
            if f.suffix.lower() == ".csv":
                series = load_timeseries_from_csv(str(f))
            else:
                series = load_timeseries_from_json(str(f))
            if series.size < 8:
                # too short to be meaningful
                continue
            channels.append(series)
            names.append(f.name)
        except Exception as e:
            # Skip malformed files but continue
            print("⚠ Skipping", f, ":", repr(e))
            continue

    if not channels:
        raise ValueError("No usable time series in %s" % input_dir)

    # Pad / trim to same length (min length across channels)
    min_len = min(len(c) for c in channels)
    channels = [c[-min_len:] for c in channels]
    data = np.stack(channels, axis=1)  # shape (T, C)
    return data, names

def compute_dphi_and_omega(field):
    """
    field: (T, C) tensor of normalized series.
    We compute ΔΦ as deviation from the global mean across T and C.
    """
    mean_val = field.mean()
    dphi = np.abs(field - mean_val)
    omega = 1.0 / (1.0 + dphi)
    return dphi, omega

def estimate_curvature_proxy(field):
    """
    Very simple curvature proxy:
    Use second finite difference of the aggregate index.
    """
    agg = field.mean(axis=1)  # mean across channels
    if len(agg) < 3:
        return 0.0
    second_diff = agg[:-2] - 2.0 * agg[1:-1] + agg[2:]
    return float(np.mean(np.abs(second_diff)))

def compute_harmonic_counts(dphi):
    """
    Core / shell / void counts in the Codex style.
    """
    max_val = float(dphi.max())
    if max_val <= 0.0:
        return 0, 0, int(dphi.size)
    core  = np.count_nonzero(dphi <  0.33 * max_val)
    shell = np.count_nonzero((dphi >= 0.33 * max_val) & (dphi < 0.66 * max_val))
    void  = np.count_nonzero(dphi >= 0.66 * max_val)
    return int(core), int(shell), int(void)

def compute_cusp_discriminant(field):
    """
    Very simple proxy mapping:
    A = structural stress → volatility / spread amplitude
    B = noise / disorder → short-term jaggedness
    We then compute D = 4A^3 + 27B^2 (cusp discriminant).
    """
    agg = field.mean(axis=1)
    if len(agg) < 4:
        return 0.0, 0.0, 0.0

    # A: structural stress ~ std deviation
    A = float(np.std(agg))

    # B: short-term noise ~ high-frequency component
    # subtract simple moving average
    win = max(3, len(agg) // 16)
    kernel = np.ones(win) / float(win)
    smoothed = np.convolve(agg, kernel, mode="same")
    noise = agg - smoothed
    B = float(np.std(noise))

    D = 4.0 * (A ** 3) + 27.0 * (B ** 2)

    # Map to an effective lambda in [0, 1] as rough cusp proximity
    # Higher stress + noise → closer to 1.
    scale = A + B + 1e-9
    lambda_eff = max(0.0, min(1.0, scale / (scale + 1.0)))
    return A, B, D, lambda_eff

def classify_risk_band(omega_mean, lambda_eff, curvature_proxy):
    """
    Heuristic classification into Codex-style bands.
    """
    # Lower curvature = flatter potential = more fragile
    flat = curvature_proxy < 1e-3

    if omega_mean >= 0.93 and lambda_eff < 0.4:
        return "STABLE_COHERENT"

    if 0.88 <= omega_mean < 0.93 or (lambda_eff >= 0.4 and lambda_eff < 0.7):
        return "ELEVATED_STRESS"

    if 0.82 <= omega_mean < 0.88 or (lambda_eff >= 0.7 and not flat):
        return "SOFT_CUSP_REGION"

    if omega_mean < 0.82 or (lambda_eff >= 0.8 and flat):
        return "HARD_CUSP_FRAGILE"

    return "UNKNOWN"

def write_visuals(output_dir, field, dphi, omega, names, timestamp):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    t = np.arange(field.shape[0])

    # 1) Aggregate index + Ω
    fig, ax1 = plt.subplots()
    agg = field.mean(axis=1)
    ax1.plot(t, agg)
    ax1.set_xlabel("time")
    ax1.set_ylabel("aggregate index")
    ax2 = ax1.twinx()
    ax2.plot(t, omega.mean(axis=1))
    ax2.set_ylabel("Ω_mean(t)")
    fig.suptitle("Codex Finance Resonance — aggregate + Ω(t)")
    fig.tight_layout()
    fig.savefig(out / ("finance_resonance_agg_omega_" + timestamp + ".png"))
    plt.close(fig)

    # 2) ΔΦ max projection across channels
    dphi_max = dphi.max(axis=1)
    plt.figure()
    plt.plot(t, dphi_max)
    plt.xlabel("time")
    plt.ylabel("ΔΦ_max across channels")
    plt.title("Codex Finance Resonance — ΔΦ_max(t)")
    plt.tight_layout()
    plt.savefig(out / ("finance_resonance_dphi_max_" + timestamp + ".png"))
    plt.close()

    # 3) Channel panel
    plt.figure()
    for i in range(field.shape[1]):
        plt.plot(t, field[:, i], alpha=0.6, label=names[i][:12])
    plt.xlabel("time")
    plt.ylabel("normalized series")
    plt.title("Codex Finance Resonance — input channels")
    if field.shape[1] <= 10:
        plt.legend()
    plt.tight_layout()
    plt.savefig(out / ("finance_resonance_channels_" + timestamp + ".png"))
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--visuals", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--input_dir", required=True)
    args = parser.parse_args()

    root_dir   = Path(args.root)
    state_dir  = Path(args.state)
    visuals_dir= Path(args.visuals)
    ledger_dir = Path(args.ledger)
    input_dir  = Path(args.input_dir)

    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load data
    field_raw, names = load_all_series(str(input_dir))

    # 2) Normalize each channel (z-score)
    mean = field_raw.mean(axis=0, keepdims=True)
    std = field_raw.std(axis=0, keepdims=True) + 1e-9
    field = (field_raw - mean) / std

    # 3) ΔΦ + Ω + curvature
    dphi, omega = compute_dphi_and_omega(field)
    curvature_proxy = estimate_curvature_proxy(field)

    # 4) Harmonic structure
    core, shell, void = compute_harmonic_counts(dphi)

    # 5) Cusp law proxies
    A, B, D, lambda_eff = compute_cusp_discriminant(field)

    # 6) Aggregate metrics
    dphi_global = float(dphi.mean())
    omega_mean  = float(omega.mean())
    omega_std   = float(omega.std())

    # 7) Risk band
    risk_band = classify_risk_band(omega_mean, lambda_eff, curvature_proxy)

    # 8) Timestamp + state file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    state_file = state_dir / ("finance_resonance_state_" + timestamp + ".json")

    state = {
        "protocol": "CodexFinanceResonance",
        "version": "1.0",
        "timestamp": timestamp,
        "input": {
            "root_dir": str(root_dir),
            "input_dir": str(input_dir),
            "channels": names,
            "T": int(field.shape[0]),
            "C": int(field.shape[1])
        },
        "metrics": {
            "dphi_global": dphi_global,
            "omega_mean":  omega_mean,
            "omega_std":   omega_std,
            "curvature_proxy": curvature_proxy,
            "harmonics": {
                "core": core,
                "shell": shell,
                "void": void
            },
            "cusp_law": {
                "A_structural_stress": A,
                "B_noise": B,
                "discriminant_D": D,
                "lambda_eff": lambda_eff
            },
            "risk_band": risk_band
        },
        "codex_law": {
            "H7_coherence_threshold": 0.70,
            "H7B_cusp_kernel": True,
            "GEO_v1_0_error_geometry": True,
            "H16_multi_scale_insight": True,
            "H19_global_dphi": True,
            "H31_harmonic_stability": True
        }
    }

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    # 9) Ledger append
    ledger_path = ledger_dir / "finance_resonance_ledger.jsonl"
    ledger_entry = {
        "timestamp": timestamp,
        "state_file": str(state_file),
        "T": int(field.shape[0]),
        "C": int(field.shape[1]),
        "dphi_global": dphi_global,
        "omega_mean": omega_mean,
        "omega_std": omega_std,
        "curvature_proxy": curvature_proxy,
        "lambda_eff": lambda_eff,
        "risk_band": risk_band
    }
    with open(ledger_path, "a") as f:
        f.write(json.dumps(ledger_entry) + "\n")

    # 10) Visuals
    write_visuals(str(visuals_dir), field, dphi, omega, names, timestamp)

    print("𓂀 Codex Finance Resonance v1.0 complete.")
    print("  • state :", state_file)
    print("  • ledger:", ledger_path)
    print("  • risk  :", risk_band)

if __name__ == "__main__":
    main()
