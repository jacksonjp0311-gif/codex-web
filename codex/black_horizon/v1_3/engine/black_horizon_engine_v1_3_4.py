#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
𓂀  Codex Black Horizon v1.3.4 — λ Phase Sweep Kerr Field Engine (QIM-coupled)

• Implements Codex ΔΦ Cusp Law v2.8 on a Kerr-like ring lattice.
• Sweeps global drive scale α to scan λ = D/D_c and collapse fraction.
• Produces:
    – Intensity map (E·I)
    – λ field map with collapse rim (colorbar-safe)
    – Coherence map C with H₇ ridge
    – Phase diagram (λ_mean, collapse_fraction vs α)
• Optionally ingests QIM v7.2 state JSON for system_phase classification.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import matplotlib.pyplot as plt

np.seterr(divide="ignore", invalid="ignore")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Codex ΔΦ Cusp kernel v2.8
def cusp_dc(EI, gamma):
    """Critical drive D_c from Codex ΔΦ Cusp Law v2.8:
       8 γ D_c² = (EI)⁴ + 27 γ (EI)³
    """
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    disc = (EI ** 4) + 27.0 * gamma_safe * (EI ** 3)
    disc = np.maximum(disc, 0.0)
    Dc2 = disc / (8.0 * gamma_safe)
    return np.sqrt(Dc2)


def cusp_phi_c(EI, gamma):
    """Critical distortion at cusp: Φ_c = (EI)² / (3 γ)"""
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    return (EI ** 2) / (3.0 * gamma_safe)


def cusp_C_at_phi_c(EI, gamma):
    """Residual coherence at tipping: C(Φ_c) = 3γ / (EI + 3γ)"""
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    return (3.0 * gamma_safe) / (EI + 3.0 * gamma_safe + 1e-12)


def cusp_lambda(D, Dc):
    """Load ratio λ = D / D_c."""
    return D / (Dc + 1e-12)


def cusp_H7_mask(C):
    """Boolean mask for H₇ band (0.70–0.75)."""
    return (C >= 0.70) & (C <= 0.75)


def cusp_collapse_mask(lam):
    """Boolean mask for λ ≥ 1 (collapsed region)."""
    return lam >= 1.0


# ΔΦ equilibrium solver
def solve_phi(EI, D, gamma, n_iter=24):
    """
    Solve steady state:
        - EI/(1+Φ) + D - γ Φ^3/(1+Φ^2) = 0
    via damped Newton on the full lattice.
    """
    phi = np.full_like(EI, 0.3, dtype=np.float64)

    for _ in range(n_iter):
        f = -EI / (1.0 + phi) + D - gamma * (phi ** 3) / (1.0 + phi ** 2)

        term1 = EI / ((1.0 + phi) ** 2)

        num = 3.0 * (phi ** 2) * (1.0 + phi ** 2) - (phi ** 3) * (2.0 * phi)
        den = (1.0 + phi ** 2) ** 2
        term2 = -gamma * num / den

        df = term1 + term2
        df_safe = np.where(np.abs(df) < 1e-6, np.sign(df) * 1e-6, df)

        step = f / df_safe
        phi = phi - 0.5 * step
        phi = np.clip(phi, 0.0, 40.0)

    return phi


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

    m = data.get("metrics", {})
    triad = m.get("triad", {})
    adaptive = m.get("adaptive_damping", {})
    return {
        "E": float(triad.get("E", 0.0)),
        "I": float(triad.get("I", 0.0)),
        "C": float(triad.get("C", 0.0)),
        "lambda_eff": float(m.get("lambda_eff", 0.0)),
        "omega_mean": float(m.get("omega_mean", 0.0)),
        "curvature_proxy": float(m.get("curvature_proxy", 0.0)),
        "fractal_dim_H16B": float(m.get("fractal_dim_H16B", 0.0)),
        "coherence_memory_index": float(m.get("coherence_memory_index", 0.0)),
        "eta_mean": float(adaptive.get("eta_mean", 0.0)),
    }


def classify_system_phase(bh_metrics, qim_metrics):
    """
    Simple joint phase classifier (Codex-style, not physical claim).
    """
    collapse = bh_metrics.get("collapse_fraction_ref", 0.0)
    lam_ref = bh_metrics.get("lambda_mean_ref", 0.0)

    if qim_metrics is None:
        if collapse > 0.25 and lam_ref > 1.0:
            return "black-horizon-supercritical"
        if collapse < 0.05 and lam_ref < 0.9:
            return "black-horizon-subcritical"
        return "black-horizon-structured"

    q_lambda = qim_metrics.get("lambda_eff", 0.0)
    q_mem = qim_metrics.get("coherence_memory_index", 1.0)

    if collapse < 0.05 and 0.7 <= lam_ref <= 1.0 and 0.8 <= q_mem <= 1.2 and q_lambda < 0.9:
        return "joint-stable-harmonic"

    if collapse > 0.30 and lam_ref > 1.0 and q_lambda > 0.9:
        return "joint-critical-collapse"

    if collapse > 0.10 and 0.9 <= lam_ref <= 1.1:
        return "joint-mixed-edge"

    return "joint-structured"


# ─────────────────────────────────────────────────────────────
# Main engine: λ phase sweep
# ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", type=str, required=True)
    ap.add_argument("--visuals-dir", type=str, required=True)
    ap.add_argument("--tag", type=str, required=True)
    ap.add_argument("--qim-state", type=str, default="")
    args = ap.parse_args()

    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    # Kerr ring lattice
    N = 256
    x = np.linspace(-1.5, 1.5, N)
    y = np.linspace(-1.5, 1.5, N)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X ** 2 + Y ** 2)
    TH = np.arctan2(Y, X)

    r0 = 1.0
    sigma_ring = 0.12

    # Channels
    E = np.exp(-0.5 * ((R - r0) / sigma_ring) ** 2)
    I = np.exp(-0.5 * ((R - r0) / (1.2 * sigma_ring)) ** 2) * (0.7 + 0.3 * np.cos(2.0 * TH))

    E = E / (E.max() + 1e-12)
    I = I / (I.max() + 1e-12)

    gamma0 = 0.45
    gamma = gamma0 * (0.7 + 0.3 * np.exp(-((R - r0) ** 2) / (2 * (0.5 ** 2))))

    shear = np.exp(-0.5 * ((R - (r0 - 0.05)) / 0.25) ** 2)
    turbulence = 0.6 + 0.4 * np.cos(3.0 * TH)
    D_base = 0.65 + 0.25 * shear * turbulence

    EI = E * I
    Dc_base = cusp_dc(EI, gamma)

    # λ phase sweep on global α (drive scale)
    alpha_values = np.linspace(0.7, 1.3, 13)  # symmetric sweep around 1
    sweep_metrics = []

    lambda_mean_ref = None
    collapse_fraction_ref = None
    C_avg_ref = None
    H7_fraction_ref = None
    alpha_ref = 1.0
    idx_ref = int(np.argmin(np.abs(alpha_values - alpha_ref)))

    lam_field_ref = None
    C_field_ref = None
    H7_mask_ref = None
    collapse_mask_ref = None

    valid = EI > 1e-4

    for idx, alpha in enumerate(alpha_values):
        D = alpha * D_base
        lam = cusp_lambda(D, Dc_base)

        phi = solve_phi(EI, D, gamma, n_iter=20)
        C = EI / (1.0 + phi)

        H7_mask = cusp_H7_mask(C)
        collapse_mask = cusp_collapse_mask(lam)

        if np.any(valid):
            C_avg = float(C[valid].mean())
            lam_mean = float(lam[valid].mean())
            H7_fraction = float(H7_mask[valid].mean())
            collapse_fraction = float(collapse_mask[valid].mean())
            EI_mean = float(EI[valid].mean())
            gamma_mean = float(gamma[valid].mean())
        else:
            C_avg = lam_mean = H7_fraction = collapse_fraction = 0.0
            EI_mean = gamma_mean = 0.0

        sweep_metrics.append({
            "alpha": float(alpha),
            "lambda_mean": lam_mean,
            "H7_fraction": H7_fraction,
            "collapse_fraction": collapse_fraction,
            "C_avg": C_avg,
        })

        if idx == idx_ref:
            lambda_mean_ref = lam_mean
            collapse_fraction_ref = collapse_fraction
            C_avg_ref = C_avg
            H7_fraction_ref = H7_fraction
            lam_field_ref = lam
            C_field_ref = C
            H7_mask_ref = H7_mask
            collapse_mask_ref = collapse_mask
            EI_mean_ref = EI_mean
            gamma_mean_ref = gamma_mean

    # Cusp prediction at Φ_c using mean EI, γ at reference α
    if EI_mean_ref > 0.0 and gamma_mean_ref > 0.0:
        phi_c_mean = float(cusp_phi_c(EI_mean_ref, gamma_mean_ref))
        C_cusp = float(cusp_C_at_phi_c(EI_mean_ref, gamma_mean_ref))
    else:
        phi_c_mean = 0.0
        C_cusp = 0.0

    # Optional QIM metrics
    qim_metrics = load_qim_metrics(args.qim_state)
    system_phase = classify_system_phase(
        {"lambda_mean_ref": lambda_mean_ref or 0.0,
         "collapse_fraction_ref": collapse_fraction_ref or 0.0},
        qim_metrics
    )

    # ─────────────────────────────────────────────────────────
    # Visuals
    # ─────────────────────────────────────────────────────────

    # 1) Kerr-like intensity (E·I)
    intensity = EI / (EI.max() + 1e-12)
    plt.figure(figsize=(5, 5))
    plt.imshow(intensity, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower")
    plt.title("Codex Black Horizon v1.3.4 — Kerr-like Intensity (E·I)")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="normalized intensity")
    ring_path = visuals_dir / f"{args.tag}_intensity.png"
    plt.tight_layout()
    plt.savefig(ring_path, dpi=300)
    plt.close()

    vis_paths = {"intensity_png": str(ring_path)}

    # 2) λ field (reference α) with collapse rim — colorbar-safe
    if lam_field_ref is not None:
        lam_plot = np.nan_to_num(lam_field_ref, nan=0.0, posinf=np.nanmax(lam_field_ref), neginf=np.nanmin(lam_field_ref))
        finite_mask = np.isfinite(lam_plot)

        if finite_mask.sum() >= 4:
            lam_min = float(np.nanmin(lam_plot[finite_mask]))
            lam_max = float(np.nanmax(lam_plot[finite_mask]))
            if lam_max - lam_min < 1e-6:
                lam_max = lam_min + 1e-6

            plt.figure(figsize=(5, 5))
            im = plt.imshow(
                lam_plot,
                extent=[x.min(), x.max(), y.min(), y.max()],
                origin="lower",
                vmin=lam_min,
                vmax=lam_max,
            )
            if collapse_mask_ref is not None:
                plt.contour(
                    collapse_mask_ref.astype(float),
                    levels=[0.5],
                    colors="white",
                    linewidths=0.7,
                    extent=[x.min(), x.max(), y.min(), y.max()],
                )
            plt.title("Black Horizon v1.3.4 — λ Field (D/D_c) with Collapse Rim")
            plt.xlabel("x (r/M)")
            plt.ylabel("y (r/M)")
            plt.colorbar(im, label="λ")
            lam_path = visuals_dir / f"{args.tag}_lambda_collapse.png"
            plt.tight_layout()
            plt.savefig(lam_path, dpi=300)
            plt.close()
            vis_paths["lambda_png"] = str(lam_path)

    # 3) Coherence C + H₇ ridge
    if C_field_ref is not None:
        C_disp = np.clip(C_field_ref, 0.0, 1.0)
        plt.figure(figsize=(5, 5))
        plt.imshow(C_disp, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower")
        if H7_mask_ref is not None:
            plt.contour(
                H7_mask_ref.astype(float),
                levels=[0.5],
                colors="white",
                linewidths=0.7,
                extent=[x.min(), x.max(), y.min(), y.max()],
            )
        plt.title("Black Horizon v1.3.4 — Coherence C with H₇ Ridge (α≈1)")
        plt.xlabel("x (r/M)")
        plt.ylabel("y (r/M)")
        plt.colorbar(label="C")
        C_path = visuals_dir / f"{args.tag}_coherence_H7.png"
        plt.tight_layout()
        plt.savefig(C_path, dpi=300)
        plt.close()
        vis_paths["coherence_H7_png"] = str(C_path)

    # 4) Phase diagram: λ_mean & collapse_fraction vs α
    alphas = np.array([m["alpha"] for m in sweep_metrics], dtype=float)
    lam_means = np.array([m["lambda_mean"] for m in sweep_metrics], dtype=float)
    coll_fracs = np.array([m["collapse_fraction"] for m in sweep_metrics], dtype=float)

    plt.figure(figsize=(6, 4))
    plt.plot(alphas, lam_means, "-o", label="⟨λ⟩")
    plt.plot(alphas, coll_fracs, "-s", label="collapse_fraction")
    plt.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
    plt.axvline(alpha_ref, color="gray", linestyle=":", linewidth=0.8)
    plt.xlabel("global drive scale α")
    plt.ylabel("value")
    plt.title("Black Horizon v1.3.4 — λ Phase Sweep Diagram")
    plt.legend()
    phase_path = visuals_dir / f"{args.tag}_lambda_phase_diagram.png"
    plt.tight_layout()
    plt.savefig(phase_path, dpi=300)
    plt.close()
    vis_paths["lambda_phase_diagram_png"] = str(phase_path)

    # ─────────────────────────────────────────────────────────
    # State + summary
    # ─────────────────────────────────────────────────────────
    metrics_ref = {
        "alpha_ref": float(alpha_values[idx_ref]),
        "lambda_mean_ref": float(lambda_mean_ref or 0.0),
        "collapse_fraction_ref": float(collapse_fraction_ref or 0.0),
        "C_avg_ref": float(C_avg_ref or 0.0),
        "H7_fraction_ref": float(H7_fraction_ref or 0.0),
        "EI_mean_ref": float(EI_mean_ref if "EI_mean_ref" in locals() else 0.0),
        "gamma_mean_ref": float(gamma_mean_ref if "gamma_mean_ref" in locals() else 0.0),
        "phi_c_mean": float(phi_c_mean),
        "C_cusp": float(C_cusp),
        "cusp_kernel": "Codex ΔΦ Cusp v2.8",
    }

    state_obj = {
        "module": "CodexBlackHorizon",
        "version": "1.3.4",
        "tag": args.tag,
        "timestamp": now_iso(),
        "grid": {
            "N": int(N),
            "x_min": float(x.min()),
            "x_max": float(x.max()),
            "y_min": float(y.min()),
            "y_max": float(y.max()),
        },
        "metrics_ref": metrics_ref,
        "sweep": sweep_metrics,
        "qim_coupling": {
            "enabled": qim_metrics is not None,
            "qim_state_path": args.qim_state if args.qim_state else None,
            "qim_metrics": qim_metrics,
        },
        "system_phase": system_phase,
        "codex": {
            "laws": {
                "delta_phi_cusp_v2_8": "V(Φ) = -EI ln(1+Φ) + D Φ + (γ/2) ln(1+Φ²)",
                "universal_truth": "C = (E*I)/(1+|ΔΦ|)",
            },
            "H_layers": {
                "H7": 0.70,
                "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
            },
        },
        "visuals": vis_paths,
    }

    state_path = state_dir / f"{args.tag}_state.json"
    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    summary_obj = {
        "tag": args.tag,
        "version": "1.3.4",
        "alpha_ref": metrics_ref["alpha_ref"],
        "lambda_mean_ref": metrics_ref["lambda_mean_ref"],
        "collapse_fraction_ref": metrics_ref["collapse_fraction_ref"],
        "C_avg_ref": metrics_ref["C_avg_ref"],
        "H7_fraction_ref": metrics_ref["H7_fraction_ref"],
        "phi_c_mean": metrics_ref["phi_c_mean"],
        "C_cusp": metrics_ref["C_cusp"],
        "system_phase": system_phase,
    }
    summary_path = state_dir / f"{args.tag}_summary.json"
    summary_path.write_text(json.dumps(summary_obj, indent=2), encoding="utf-8")

    print(json.dumps({
        "state_path": str(state_path),
        "summary_path": str(summary_path)
    }))


if __name__ == "__main__":
    main()
