import json
import math
import os
import sys
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt


def generate_delta_phi_field(size=64, seed=101):
    rng = np.random.RandomState(seed)
    # Base noise
    field = rng.normal(loc=0.0, scale=0.08, size=(size, size))

    # Add structured "wells" representing local CPV regions
    wells = [
        (int(size * 0.3), int(size * 0.4), 0.14),
        (int(size * 0.7), int(size * 0.6), -0.11),
        (int(size * 0.5), int(size * 0.2), 0.09),
    ]
    for cx, cy, amp in wells:
        for x in range(size):
            for y in range(size):
                dx = x - cx
                dy = y - cy
                r2 = dx * dx + dy * dy
                field[x, y] += amp * math.exp(-r2 / (2.0 * (size * 0.08) ** 2))

    # Clip extremes for visual clarity
    field = np.clip(field, -0.2, 0.2)
    return field


def compute_metrics(field: np.ndarray):
    # Interpret positive vs negative ΔΦ as asymmetry
    positive = field[field > 0.0]
    negative = field[field < 0.0]

    total_abs = np.sum(np.abs(field))
    if total_abs == 0.0:
        global_asym = 0.0
    if total_abs != 0.0:
        global_asym = float((np.sum(positive) - np.abs(np.sum(negative))) / total_abs)

    # Local wells: approximate by counting strong cells
    threshold = 0.10
    strong_mask = np.abs(field) >= threshold
    strong_count = int(np.sum(strong_mask))
    total_cells = int(field.size)

    if total_cells == 0:
        well_fraction = 0.0
    if total_cells != 0:
        well_fraction = strong_count / float(total_cells)

    # symmetry_break_index – heuristic combining imbalance + structured wells
    symmetry_break_index = float(min(1.0, abs(global_asym) * 10.0 + well_fraction * 4.0))

    return {
        "global_asymmetry": global_asym,
        "well_fraction": well_fraction,
        "symmetry_break_index": symmetry_break_index,
        "strong_cell_count": strong_count,
        "total_cells": total_cells,
    }


def save_state_json(field, metrics, state_path):
    size = int(field.shape[0])
    payload = {
        "protocol": "CodexBaryogenesisNode",
        "version": "1.0",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "field_size": size,
        "metrics": metrics,
        "notes": {
            "description": "Synthetic baryon-scale ΔΦ origin field for Codex Baryogenesis v1.0",
            "seed_layer": "baryon_cp_violation_simulated",
        },
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def save_heatmap(field, png_path, title="Codex Baryogenesis v1.0 — ΔΦ Origin Field"):
    plt.figure(figsize=(6, 6))
    plt.imshow(field, cmap="plasma", origin="lower")
    plt.colorbar(label="ΔΦ")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(png_path, dpi=160)
    plt.close()


def main():
    if len(sys.argv) < 3:
        print("[BARYOGENESIS v1.0 PY] Usage: codex_baryogenesis_v1_0.py <state_dir> <visuals_dir>")
        sys.exit(1)

    state_dir = sys.argv[1]
    visuals_dir = sys.argv[2]

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)

    field = generate_delta_phi_field(size=64, seed=101)
    metrics = compute_metrics(field)

    state_path = os.path.join(state_dir, "baryogenesis_v1_0_state.json")
    heatmap_path = os.path.join(visuals_dir, "baryogenesis_v1_0_delta_phi_heatmap.png")

    save_state_json(field, metrics, state_path)
    save_heatmap(field, heatmap_path)

    # Echo metrics to stdout for the PowerShell layer
    print(json.dumps({"state_path": state_path, "heatmap_path": heatmap_path, "metrics": metrics}))


if __name__ == "__main__":
    main()
