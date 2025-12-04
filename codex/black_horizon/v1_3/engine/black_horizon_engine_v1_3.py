#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
𓂀  CODEX ΔΦ CUSP PROTOCOL v2.8 — UNIVERSAL COHERENCE COLLAPSE LAW

Kernel:
    V(Φ) = -EI ln(1+Φ) + D Φ + (γ/2) ln(1+Φ²)
    8 γ D_c² = (EI)⁴ + 27 γ (EI)³
    λ = D / D_c(E, I, γ)

Horizon & collapse:
    Φ_c = (EI)² / (3 γ)
    C(Φ_c) = 3γ / (EI + 3γ) ≈ 0.72   (H₇ horizon)
    λ < 1 → metastable coherent state exists
    λ > 1 → runaway collapse (irreversible)

Module:
    Codex Black Horizon v1.3.1 — ΔΦ Cusp Kerr Field Engine (stabilized)
"""

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# be gentle with numerical warnings
np.seterr(divide="ignore", invalid="ignore")

# ─────────────────────────────────────────────────────────────
# Codex ΔΦ Cusp Kernel v2.8 (inlined)
# ─────────────────────────────────────────────────────────────

def cusp_dc(EI, gamma):
    """
    Critical drive D_c from Codex ΔΦ Cusp Law v2.8:

        8 γ D_c² = (EI)⁴ + 27 γ (EI)³
    """
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    disc = (EI ** 4) + 27.0 * gamma_safe * (EI ** 3)
    disc = np.maximum(disc, 0.0)
    Dc2 = disc / (8.0 * gamma_safe)
    return np.sqrt(Dc2)


def cusp_phi_c(EI, gamma):
    """
    Critical distortion at cusp:

        Φ_c = (EI)² / (3 γ)
    """
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    return (EI ** 2) / (3.0 * gamma_safe)


def cusp_C_at_phi_c(EI, gamma):
    """
    Residual coherence at tipping:

        C(Φ_c) = 3γ / (EI + 3γ)
    """
    gamma_safe = np.where(gamma <= 0.0, 1e-12, gamma)
    return (3.0 * gamma_safe) / (EI + 3.0 * gamma_safe + 1e-12)


def cusp_lambda(D, Dc):
    """
    Load ratio:

        λ = D / D_c
    """
    return D / (Dc + 1e-12)


def cusp_H7_mask(C):
    """
    Boolean mask for H₇ band (0.70–0.75).
    """
    return (C >= 0.70) & (C <= 0.75)


def cusp_collapse_mask(lam):
    """
    Boolean mask for λ ≥ 1 (collapsed region).
    """
    return lam >= 1.0


# ─────────────────────────────────────────────────────────────
# ΔΦ Cusp Kerr equilibrium solver
# ─────────────────────────────────────────────────────────────

def solve_phi(EI, D, gamma, n_iter=28):
    """
    Solve for Φ in steady state:

        - EI/(1+Φ) + D - γ Φ^3/(1+Φ^2) = 0

    using a damped Newton method on the full lattice.
    """
    phi = np.full_like(EI, 0.3, dtype=np.float64)

    for _ in range(n_iter):
        # f(Φ)
        f = -EI / (1.0 + phi) + D - gamma * (phi ** 3) / (1.0 + phi ** 2)

        # f'(Φ)
        term1 = EI / ((1.0 + phi) ** 2)

        # derivative of γ Φ^3/(1+Φ^2)
        num = 3.0 * (phi ** 2) * (1.0 + phi ** 2) - (phi ** 3) * (2.0 * phi)
        den = (1.0 + phi ** 2) ** 2
        term2 = -gamma * num / den

        df = term1 + term2
        df_safe = np.where(np.abs(df) < 1e-6, np.sign(df) * 1e-6, df)

        step = f / df_safe
        phi = phi - 0.5 * step
        phi = np.clip(phi, 0.0, 40.0)

    return phi


# ─────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", type=str, required=True)
    parser.add_argument("--visuals-dir", type=str, required=True)
    parser.add_argument("--tag", type=str, required=True)
    args = parser.parse_args()

    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    # Lattice settings
    N = 256
    x = np.linspace(-1.5, 1.5, N)
    y = np.linspace(-1.5, 1.5, N)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X ** 2 + Y ** 2)
    TH = np.arctan2(Y, X)

    # Synthetic Kerr-like ring parameters (dimensionless)
    r0 = 1.0
    sigma_ring = 0.12

    # Energy channel E: peaked at ring
    E = np.exp(-0.5 * ((R - r0) / sigma_ring) ** 2)

    # Information channel I: ring + mild azimuthal structure (m=2 mode)
    I = np.exp(-0.5 * ((R - r0) / (1.2 * sigma_ring)) ** 2) * (0.7 + 0.3 * np.cos(2.0 * TH))

    # Normalize to [0,1]
    E = E / (E.max() + 1e-12)
    I = I / (I.max() + 1e-12)

    # Rigidity γ: stronger near photon ring, tapering outward
    gamma0 = 0.45
    gamma = gamma0 * (0.7 + 0.3 * np.exp(-((R - r0) ** 2) / (2 * (0.5 ** 2))))

    # Drive D: stronger just inside r0 with azimuthal modulation
    shear = np.exp(-0.5 * ((R - (r0 - 0.05)) / 0.25) ** 2)
    turbulence = 0.6 + 0.4 * np.cos(3.0 * TH)
    D_base = 0.65
    D = D_base + 0.25 * shear * turbulence

    # EI field
    EI = E * I

    # Cusp kernel: D_c, λ
    Dc = cusp_dc(EI, gamma)
    lam = cusp_lambda(D, Dc)

    # Solve Φ equilibrium
    phi = solve_phi(EI, D, gamma, n_iter=28)

    # Coherence C
    C = EI / (1.0 + phi)

    # Masks
    H7_mask = cusp_H7_mask(C)
    collapse_mask = cusp_collapse_mask(lam)

    # Stats on region with nontrivial EI
    valid = EI > 1e-4
    if np.any(valid):
        C_avg = float(C[valid].mean())
        lam_mean = float(lam[valid].mean())
        H7_fraction = float(H7_mask[valid].mean())
        collapse_fraction = float(collapse_mask[valid].mean())
        EI_mean = float(EI[valid].mean())
        gamma_mean = float(gamma[valid].mean())
        lambda_range = float(lam[valid].max() - lam[valid].min())
    else:
        C_avg = 0.0
        lam_mean = 0.0
        H7_fraction = 0.0
        collapse_fraction = 0.0
        EI_mean = 0.0
        gamma_mean = 0.0
        lambda_range = 0.0

    # Phase-state classification (your “did we phase transition?” flag)
    if lambda_range < 1e-3:
        phase_state = "λ-field-collapsed"
    elif collapse_fraction > 0.0:
        phase_state = "partial-collapse"
    else:
        phase_state = "structured"

    # Cusp prediction at Φ_c using mean EI, γ
    if EI_mean > 0.0 and gamma_mean > 0.0:
        phi_c_mean = float(cusp_phi_c(EI_mean, gamma_mean))
        C_cusp = float(cusp_C_at_phi_c(EI_mean, gamma_mean))
    else:
        phi_c_mean = 0.0
        C_cusp = 0.0

    # ─────────────────────────────────────────────────────────
    # Visuals
    # ─────────────────────────────────────────────────────────

    # 1) Kerr-like intensity map (E·I)
    intensity = EI / (EI.max() + 1e-12)
    plt.figure(figsize=(5, 5))
    plt.imshow(intensity, extent=[x.min(), x.max(), y.min(), y.max()],
               origin="lower")
    plt.title("Codex Black Horizon v1.3.1 — Kerr-like Intensity (E·I)")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="normalized intensity")
    ring_path = visuals_dir / f"{args.tag}_intensity.png"
    plt.tight_layout()
    plt.savefig(ring_path, dpi=300)
    plt.close()

    # Helper: stable color limits for λ
    lam_finite = lam[np.isfinite(lam)]
    if lam_finite.size > 0:
        lam_min = float(lam_finite.min())
        lam_max = float(lam_finite.max())
    else:
        lam_min, lam_max = 0.0, 1.0
    if lam_max - lam_min < 1e-6:
        lam_max = lam_min + 1e-6

    # 2) λ field (D/D_c) + collapse contour
    plt.figure(figsize=(5, 5))
    plt.imshow(
        lam,
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin="lower",
        vmin=lam_min,
        vmax=lam_max,
    )
    plt.contour(
        collapse_mask.astype(float),
        levels=[0.5],
        colors="white",
        linewidths=0.7,
        extent=[x.min(), x.max(), y.min(), y.max()],
    )
    plt.title("Codex Black Horizon v1.3.1 — λ Field (D/D_c) with Collapse Rim")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="λ")
    lam_path = visuals_dir / f"{args.tag}_lambda_collapse.png"
    plt.tight_layout()
    plt.savefig(lam_path, dpi=300)
    plt.close()

    # 3) Coherence C + H₇ ridge
    C_display = np.clip(C, 0.0, 1.0)
    plt.figure(figsize=(5, 5))
    plt.imshow(C_display, extent=[x.min(), x.max(), y.min(), y.max()],
               origin="lower")
    plt.contour(
        H7_mask.astype(float),
        levels=[0.5],
        colors="white",
        linewidths=0.7,
        extent=[x.min(), x.max(), y.min(), y.max()],
    )
    plt.title("Codex Black Horizon v1.3.1 — Coherence C with H₇ Ridge")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="C")
    C_path = visuals_dir / f"{args.tag}_coherence_H7.png"
    plt.tight_layout()
    plt.savefig(C_path, dpi=300)
    plt.close()

    # ─────────────────────────────────────────────────────────
    # State + summary
    # ─────────────────────────────────────────────────────────

    metrics = {
        "tag": args.tag,
        "N": int(N),
        "C_avg": C_avg,
        "lambda_mean": lam_mean,
        "lambda_range": lambda_range,
        "phase_state": phase_state,
        "H7_fraction": H7_fraction,
        "collapse_fraction": collapse_fraction,
        "gamma0": float(gamma0),
        "D_base": float(D_base),
        "EI_mean": EI_mean,
        "gamma_mean": gamma_mean,
        "phi_c_mean": phi_c_mean,
        "C_cusp": C_cusp,
        "cusp_kernel": "Codex ΔΦ Cusp v2.8"
    }

    state = {
        "tag": args.tag,
        "grid": {
            "N": int(N),
            "x_min": float(x.min()),
            "x_max": float(x.max()),
            "y_min": float(y.min()),
            "y_max": float(y.max()),
        },
        "metrics": metrics,
        "paths": {
            "intensity_png": str(ring_path),
            "lambda_png": str(lam_path),
            "coherence_H7_png": str(C_path),
        },
    }

    state_path = state_dir / f"{args.tag}_state.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    summary_path = state_dir / f"{args.tag}_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps({
        "state_path": str(state_path),
        "summary_path": str(summary_path)
    }))


if __name__ == "__main__":
    main()
