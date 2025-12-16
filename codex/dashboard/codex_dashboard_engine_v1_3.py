#!/usr/bin/env python3
# 𓂀 Codex All-One Dashboard Engine v1.3 (Dark Mode — Codex Eclipse Black)
# Reads dashboard_state.json and renders a multi-panel geometry PNG.

import os
import sys
import json
import math
import argparse
import datetime as _dt

import numpy as np

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False


def render_dashboard(state_path, output_png):
    """
    Render a dark-mode multi-panel dashboard using module visuals.

    Style B — Codex Eclipse Black:
      * Background: near-black
      * Colormap: whatever is in the PNGs (we just display them)
      * Titles / text slightly larger for readability
    """
    if not HAVE_MPL:
        print("Matplotlib not available; cannot render dashboard PNG.", file=sys.stderr)
        return 1

    if not os.path.isfile(state_path):
        print(f"State JSON not found: {state_path}", file=sys.stderr)
        return 1

    # Use a dark background style.
    try:
        plt.style.use("dark_background")
    except Exception:
        pass

    # Tolerant to a UTF-8 BOM from PowerShell writers.
    with open(state_path, "r", encoding="utf-8-sig") as f:
        state = json.load(f)

    modules = state.get("modules", [])
    n = len(modules)
    if n == 0:
        print("No modules in dashboard_state.json; nothing to render.", file=sys.stderr)
        return 1

    cols = min(3, max(1, n))
    rows = int(math.ceil(float(n) / float(cols)))

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4.5 * rows), dpi=150)
    axes = np.array(axes).reshape(rows, cols)

    # Darken figure background
    try:
        fig.patch.set_facecolor("#050608")
    except Exception:
        pass

    for idx, mod in enumerate(modules):
        ax = axes[idx // cols, idx % cols]
        name = mod.get("name", "Module")
        C_avg = mod.get("C_avg", None)
        H7_frac = mod.get("H7_fraction", None)
        r_h = mod.get("r_h", None)
        primary_visual = mod.get("primary_visual", None)

        img = None
        if primary_visual and os.path.isfile(primary_visual):
            try:
                img = plt.imread(primary_visual)
            except Exception:
                img = None

        if img is not None:
            ax.imshow(img, origin="lower")
            ax.axis("off")
        else:
            ax.axis("off")

        subtitle_parts = []
        if C_avg is not None:
            try:
                subtitle_parts.append(f"C≈{float(C_avg):.3f}")
            except Exception:
                pass
        if H7_frac is not None:
            try:
                subtitle_parts.append(f"H7%≈{100.0 * float(H7_frac):.1f}")
            except Exception:
                pass
        if r_h is not None:
            try:
                subtitle_parts.append(f"r_h≈{float(r_h):.3f}")
            except Exception:
                pass

        subtitle = " • ".join(subtitle_parts)
        if subtitle:
            ax.set_title(f"{name}\n{subtitle}", fontsize=9)
        else:
            ax.set_title(name, fontsize=9)

    # Hide unused subplots
    for j in range(n, rows * cols):
        axes[j // cols, j % cols].axis("off")

    codex_law = state.get("codex_law", "C = (E·I)/(1+|ΔΦ|), H₇ ≈ 0.70–0.75")

    # Bigger, readable super-title
    title_str = "Codex All-One Geometry Dashboard\n" + codex_law
    fig.suptitle(title_str, fontsize=14, y=1.02)

    plt.tight_layout()
    plt.savefig(output_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-json", required=True)
    ap.add_argument("--output-png", required=True)
    args = ap.parse_args()

    rc = render_dashboard(args.state_json, args.output_png)
    return rc


if __name__ == "__main__":
    sys.exit(main())
