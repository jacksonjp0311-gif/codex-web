#!/usr/bin/env python3
"""
Codex Black Horizon Engine v1.3.6
ΔΦ Cusp Kerr λ-phase sweep (QIM-coupled)

ROLE
 • Build a 2D Kerr-like λ-field over (x,y)
 • Apply Codex ΔΦ Cusp Law v2.8:
     V(Φ) = -EI ln(1+Φ) + D Φ + (γ/2) ln(1+Φ²)
     8 γ D_c² = (EI)^4 + 27 γ (EI)^3
     λ = D / D_c(E,I,γ)
     Φ_c = (EI)² / (3γ)
     C(Φ_c) = 3γ / (EI + 3γ)
 • Sweep global drive scale α ∈ [0.7, 1.3]
 • Compute collapse_fraction, H7 ridge fraction, C_avg
 • Optionally couple QIM v7.2 state JSON
 • Emit state JSON + summary JSON
 • Print {"state_path": ..., "summary_path": ...} to STDOUT
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def compute_cusp_params(E, I, gamma, D):
    EI = E * I
    # Avoid divide-by-zero at γ→0
    Dc_num = EI**4 + 27.0 * gamma * (EI**3)
    Dc_den = 8.0 * gamma if gamma != 0.0 else 1e-9
    Dc = math.sqrt(max(Dc_num / Dc_den, 1e-12))
    lam = D / (Dc + 1e-12)
    phi_c = (EI**2) / (3.0 * gamma + 1e-9)
    C_cusp = (3.0 * gamma) / (EI + 3.0 * gamma + 1e-9)
    return {
        "E": E,
        "I": I,
        "EI": EI,
        "gamma": gamma,
        "D": D,
        "Dc": Dc,
        "lambda_mean": lam,
        "phi_c": phi_c,
        "C_cusp": C_cusp,
    }


def build_grid(N=256, x_min=-1.5, x_max=1.5, y_min=-1.5, y_max=1.5):
    x = np.linspace(x_min, x_max, N)
    y = np.linspace(y_min, y_max, N)
    X, Y = np.meshgrid(x, y, indexing="xy")
    R2 = X**2 + Y**2
    return x, y, X, Y, R2


def compute_fields(E, I, gamma, D_base, alpha, R2):
    """
    Build λ-field and C-field for a given global drive scale α.

    We treat the local drive as D(r) = α D_base (1 + R2),
    and ΔΦ ≈ λ(r) - 1 so that:
        C(r) = EI / (1 + |ΔΦ|)  (Codex ΔΦ law form)
    """
    params = compute_cusp_params(E, I, gamma, D_base * alpha)
    Dc = params["Dc"]
    EI = params["EI"]

    D_field = params["D"] * (1.0 + R2)
    lam_field = D_field / (Dc + 1e-12)

    # ΔΦ ≈ λ - 1, C = EI / (1 + |ΔΦ|)
    dphi = lam_field - 1.0
    C_field = EI / (1.0 + np.abs(dphi))

    collapse_mask = lam_field > 1.0
    collapse_fraction = float(np.mean(collapse_mask))

    # H7 ridge: where C is close to 0.70 (±0.02)
    H7_low = 0.68
    H7_high = 0.72
    H7_mask = (C_field >= H7_low) & (C_field <= H7_high)
    H7_fraction = float(np.mean(H7_mask))

    C_avg = float(np.mean(C_field))

    params.update(
        {
            "collapse_fraction": collapse_fraction,
            "H7_fraction": H7_fraction,
            "C_avg": C_avg,
        }
    )
    return lam_field, C_field, params


def classify_phase(collapse_fraction, C_cusp, qim_metrics=None):
    """
    Very simple phase classifier.
    """
    phase = "bh-structured"
    if collapse_fraction > 0.8 and C_cusp > 0.8:
        phase = "λ-field-collapsed"
    if 0.6 < collapse_fraction <= 0.8 and C_cusp > 0.7:
        phase = "partial-collapse"
    if qim_metrics is not None:
        # If QIM coherence_memory_index is high, upgrade to joint-structured
        cmi = float(qim_metrics.get("coherence_memory_index", 0.0))
        if cmi > 0.5:
            phase = "joint-structured"
    return phase


def load_qim_metrics(qim_state_path):
    if not qim_state_path:
        return None
    p = Path(qim_state_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

    # Flexible: accept either "metrics" or "triad" field, etc.
    metrics = data.get("metrics", {})
    if not metrics and "triad" in data:
        metrics = data["triad"]
    return metrics or None


def make_visuals(x, y, lam_field, C_field, sweep_data, out_dir, tag):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Intensity-like map (simple Kerr-ish profile)
    intensity = np.exp(-0.8 * (x[None, :] ** 2 + y[:, None] ** 2)) * lam_field
    fig1, ax1 = plt.subplots()
    im1 = ax1.imshow(
        intensity,
        extent=(x[0], x[-1], y[0], y[-1]),
        origin="lower",
        aspect="equal",
    )
    ax1.set_title("Black Horizon — Intensity (λ-weighted)")
    plt.colorbar(im1, ax=ax1, label="Intensity")
    intensity_png = out_dir / f"{tag}_intensity.png"
    fig1.tight_layout()
    fig1.savefig(intensity_png, dpi=150)
    plt.close(fig1)

    # 2) λ-collapse map
    fig2, ax2 = plt.subplots()
    im2 = ax2.imshow(
        lam_field,
        extent=(x[0], x[-1], y[0], y[-1]),
        origin="lower",
        aspect="equal",
    )
    ax2.set_title("Black Horizon — λ Field")
    plt.colorbar(im2, ax=ax2, label="λ")
    lambda_png = out_dir / f"{tag}_lambda_collapse.png"
    fig2.tight_layout()
    fig2.savefig(lambda_png, dpi=150)
    plt.close(fig2)

    # 3) C + H7 ridge
    fig3, ax3 = plt.subplots()
    im3 = ax3.imshow(
        C_field,
        extent=(x[0], x[-1], y[0], y[-1]),
        origin="lower",
        aspect="equal",
    )
    ax3.set_title("Black Horizon — Coherence Field C (H7 ridge)")
    plt.colorbar(im3, ax=ax3, label="C")
    coherence_png = out_dir / f"{tag}_coherence_H7.png"
    fig3.tight_layout()
    fig3.savefig(coherence_png, dpi=150)
    plt.close(fig3)

    # 4) λ-phase diagram (alpha vs λ_mean + collapse_fraction)
    alphas = [d["alpha"] for d in sweep_data]
    lambda_means = [d["lambda_mean"] for d in sweep_data]
    collapse_fracs = [d["collapse_fraction"] for d in sweep_data]

    fig4, ax4 = plt.subplots()
    ax4.plot(alphas, lambda_means, marker="o", label="λ_mean")
    ax4.set_xlabel("α (global drive scale)")
    ax4.set_ylabel("λ_mean", loc="center")
    ax4_t = ax4.twinx()
    ax4_t.plot(alphas, collapse_fracs, marker="s", linestyle="--", label="collapse_fraction")
    ax4_t.set_ylabel("collapse_fraction", loc="center")
    ax4.set_title("Black Horizon — λ-Phase Diagram (α sweep)")

    # Join the legends from both axes
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_t.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc="best")

    lambda_phase_png = out_dir / f"{tag}_lambda_phase_diagram.png"
    fig4.tight_layout()
    fig4.savefig(lambda_phase_png, dpi=150)
    plt.close(fig4)

    return {
        "intensity_png": str(intensity_png),
        "lambda_png": str(lambda_png),
        "coherence_H7_png": str(coherence_png),
        "lambda_phase_diagram_png": str(lambda_phase_png),
    }


def main():
    ap = argparse.ArgumentParser(description="Codex Black Horizon Engine v1.3.6")
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--visuals-dir", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--qim-state", default=None)
    args = ap.parse_args()

    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    tag = args.tag
    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    # Core parameters (can be tuned; these are safe, non-explosive)
    N = 256
    x_min, x_max = -1.5, 1.5
    y_min, y_max = -1.5, 1.5

    E = 1.0
    I = 1.0
    gamma = 0.35
    D_base = 12000.0  # tuned so λ_mean ~ 1e4–1.5e4 for α ≈ 1

    x, y, X, Y, R2 = build_grid(N=N, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)

    # α sweep
    alphas = np.linspace(0.7, 1.3, 13)
    sweep_data = []
    lam_ref = None
    C_field_ref = None
    params_ref = None

    for alpha in alphas:
        lam_field, C_field, params = compute_fields(E, I, gamma, D_base, float(alpha), R2)
        row = {
            "alpha": float(alpha),
            "lambda_mean": float(params["lambda_mean"]),
            "H7_fraction": float(params["H7_fraction"]),
            "collapse_fraction": float(params["collapse_fraction"]),
            "C_avg": float(params["C_avg"]),
        }
        sweep_data.append(row)

        # Use α ≈ 1 as reference
        if abs(alpha - 1.0) < 1e-9:
            lam_ref = lam_field
            C_field_ref = C_field
            params_ref = params

    if lam_ref is None or C_field_ref is None or params_ref is None:
        raise RuntimeError("No α=1 reference slice computed.")

    # Load QIM coupling if available
    qim_metrics = load_qim_metrics(args.qim_state)
    system_phase = classify_phase(
        collapse_fraction=params_ref["collapse_fraction"],
        C_cusp=params_ref["C_cusp"],
        qim_metrics=qim_metrics,
    )

    # Visuals based on reference α=1 field
    visuals = make_visuals(x, y, lam_ref, C_field_ref, sweep_data, visuals_dir, tag)

    # Build metrics_ref block
    metrics_ref = {
        "alpha_ref": 1.0,
        "lambda_mean_ref": float(params_ref["lambda_mean"]),
        "collapse_fraction_ref": float(params_ref["collapse_fraction"]),
        "C_avg_ref": float(params_ref["C_avg"]),
        "H7_fraction_ref": float(params_ref["H7_fraction"]),
        "EI_mean_ref": float(params_ref["EI"]),
        "gamma_mean_ref": float(params_ref["gamma"]),
        "phi_c_mean": float(params_ref["phi_c"]),
        "C_cusp": float(params_ref["C_cusp"]),
        "cusp_kernel": "Codex ΔΦ Cusp v2.8",
    }

    # QIM coupling block
    qim_block = {
        "enabled": qim_metrics is not None,
        "qim_state_path": str(args.qim_state) if args.qim_state else None,
        "qim_metrics": qim_metrics or {},
    }

    # Full state JSON
    state = {
        "module": "CodexBlackHorizon",
        "version": "1.3.6",
        "tag": tag,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "grid": {
            "N": N,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
        },
        "metrics_ref": metrics_ref,
        "sweep": sweep_data,
        "qim_coupling": qim_block,
        "system_phase": system_phase,
        "codex": {
            "laws": {
                "delta_phi_cusp_v2_8": "V(Φ) = -EI ln(1+Φ) + D Φ + (γ/2) ln(1+Φ²)",
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
            },
            "H_layers": {
                "H7": 0.7,
                "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
            },
        },
        "visuals": visuals,
    }

    state_path = state_dir / f"{tag}_state.json"
    summary_path = state_dir / f"{tag}_summary.json"

    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    summary = {
        "tag": tag,
        "version": "1.3.6",
        "alpha_ref": metrics_ref["alpha_ref"],
        "lambda_mean_ref": metrics_ref["lambda_mean_ref"],
        "collapse_fraction_ref": metrics_ref["collapse_fraction_ref"],
        "C_avg_ref": metrics_ref["C_avg_ref"],
        "H7_fraction_ref": metrics_ref["H7_fraction_ref"],
        "phi_c_mean": metrics_ref["phi_c_mean"],
        "C_cusp": metrics_ref["C_cusp"],
        "system_phase": system_phase,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # STDOUT contract for the PS orchestrator
    out = {
        "state_path": str(state_path),
        "summary_path": str(summary_path),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
