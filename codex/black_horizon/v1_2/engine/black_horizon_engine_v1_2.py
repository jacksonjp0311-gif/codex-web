#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Codex Black Horizon v1.2 — ΔΦ Cusp Field Engine

Near-horizon 2D lattice:
  • Define E, I, γ, D fields around a synthetic Kerr ring
  • Solve ΔΦ Cusp equilibrium for Φ on the grid (Newton steps)
  • Compute C, D_c, λ, H7 fraction, collapse fraction
  • Emit:
      - ring intensity map
      - λ (load ratio) map
      - coherence C map
  • Save state JSON + summary JSON
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def compute_dc(EI, gamma):
    """
    Critical drive D_c from Codex ΔΦ Cusp:
      8 γ D_c^2 = 27 γ (EI)^3 + (EI)^4
    """
    # Avoid division issues
    gamma_safe = np.where(gamma <= 0.0, 1e-8, gamma)
    disc = 27.0 * gamma_safe * (EI ** 3) + (EI ** 4)
    disc = np.maximum(disc, 0.0)
    Dc2 = disc / (8.0 * gamma_safe)
    return np.sqrt(Dc2)


def solve_phi(EI, D, gamma, n_iter=25):
    """
    Solve for Φ in steady state:
      dΦ/dτ = -∂V/∂Φ = 0
      → - EI/(1+Φ) + D - γ Φ^3/(1+Φ^2) = 0

    We use a damped Newton method on the entire grid.
    """
    phi = np.full_like(EI, 0.3, dtype=np.float64)

    for _ in range(n_iter):
        # f(Φ)
        f = -EI / (1.0 + phi) + D - gamma * (phi ** 3) / (1.0 + phi ** 2)

        # f'(Φ) — derivative of the RHS
        # d/dΦ[ -EI/(1+Φ) ] = EI/(1+Φ)^2
        term1 = EI / ((1.0 + phi) ** 2)

        # For γ Φ^3/(1+Φ^2): derivative is γ * (3 Φ^2 (1+Φ^2) - Φ^3 * 2Φ)/(1+Φ^2)^2
        num = 3.0 * (phi ** 2) * (1.0 + phi ** 2) - (phi ** 3) * (2.0 * phi)
        den = (1.0 + phi ** 2) ** 2
        term2 = -gamma * num / den

        df = term1 + term2
        df_safe = np.where(np.abs(df) < 1e-6, np.sign(df) * 1e-6, df)

        step = f / df_safe
        phi = phi - 0.5 * step   # damping for robustness
        phi = np.clip(phi, 0.0, 20.0)

    return phi


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

    # Normalize fields to [0,1]
    E = E / (E.max() + 1e-12)
    I = I / (I.max() + 1e-12)

    # Rigidity γ: stronger near the photon ring, tapering outward
    gamma0 = 0.45
    gamma = gamma0 * (0.7 + 0.3 * np.exp(-((R - r0) ** 2) / (2 * (0.5 ** 2))))

    # Drive D: combination of shear / turbulence, stronger just inside r0
    shear = np.exp(-0.5 * ((R - (r0 - 0.05)) / (0.25)) ** 2)
    turbulence = 0.6 + 0.4 * np.cos(3.0 * TH)
    D_base = 0.65
    D = D_base + 0.25 * shear * turbulence

    # EI field
    EI = E * I

    # Compute D_c and λ
    Dc = compute_dc(EI, gamma)
    Dc = Dc + 1e-8
    lam = D / Dc

    # Solve for Φ at steady state
    phi = solve_phi(EI, D, gamma, n_iter=28)

    # Coherence C
    C = EI / (1.0 + phi)

    # H7 band (0.70–0.75)
    H7_mask = (C >= 0.70) & (C <= 0.75)

    # Collapse mask (λ ≥ 1)
    collapse_mask = lam >= 1.0

    # Global metrics
    valid = EI > 1e-4  # restrict stats to region with nontrivial EI
    if np.any(valid):
        C_avg = float(C[valid].mean())
        lam_mean = float(lam[valid].mean())
        H7_fraction = float(H7_mask[valid].mean())
        collapse_fraction = float(collapse_mask[valid].mean())
    else:
        C_avg = 0.0
        lam_mean = 0.0
        H7_fraction = 0.0
        collapse_fraction = 0.0

    metrics = {
        "tag": args.tag,
        "N": int(N),
        "C_avg": C_avg,
        "lambda_mean": lam_mean,
        "H7_fraction": H7_fraction,
        "collapse_fraction": collapse_fraction,
        "gamma0": float(gamma0),
        "D_base": float(D_base),
    }

    # ─────────────────────────────────────────────────────────────
    # Visuals
    # ─────────────────────────────────────────────────────────────

    # 1) Kerr-like intensity map (E*I)
    intensity = EI / (EI.max() + 1e-12)
    plt.figure(figsize=(5, 5))
    plt.imshow(intensity, extent=[x.min(), x.max(), y.min(), y.max()],
               origin="lower")
    plt.title("Codex Black Horizon v1.2 — Kerr-like Intensity (E·I)")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="normalized intensity")
    ring_path = visuals_dir / f"{args.tag}_intensity.png"
    plt.tight_layout()
    plt.savefig(ring_path, dpi=300)
    plt.close()

    # 2) λ map
    plt.figure(figsize=(5, 5))
    plt.imshow(lam, extent=[x.min(), x.max(), y.min(), y.max()],
               origin="lower")
    plt.title("Codex Black Horizon v1.2 — λ Field (D/D_c)")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="λ")
    lam_path = visuals_dir / f"{args.tag}_lambda.png"
    plt.tight_layout()
    plt.savefig(lam_path, dpi=300)
    plt.close()

    # 3) Coherence C map + H7 ridge highlight
    C_display = np.clip(C, 0.0, 1.0)
    plt.figure(figsize=(5, 5))
    plt.imshow(C_display, extent=[x.min(), x.max(), y.min(), y.max()],
               origin="lower")
    plt.contour(H7_mask.astype(float),
                levels=[0.5],
                colors="white",
                linewidths=0.7,
                extent=[x.min(), x.max(), y.min(), y.max()])
    plt.title("Codex Black Horizon v1.2 — Coherence C with H₇ Ridge")
    plt.xlabel("x (r/M)")
    plt.ylabel("y (r/M)")
    plt.colorbar(label="C")
    C_path = visuals_dir / f"{args.tag}_coherence_H7.png"
    plt.tight_layout()
    plt.savefig(C_path, dpi=300)
    plt.close()

    # ─────────────────────────────────────────────────────────────
    # State + summary
    # ─────────────────────────────────────────────────────────────

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
