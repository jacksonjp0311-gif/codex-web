#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 𓂀 Codex All-One Dashboard Engine v1.1
# Reads dashboard_state.json and:
#   • renders a multi-panel geometry PNG
#   • emits dashboard_feedback.json for GPT-Bridge style analysis

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


def build_feedback(state, modules, output_path):
    """
    Build a lightweight feedback JSON that GPT Bridge can ingest later.
    No external calls; this is just structured state.
    """
    now_utc = _dt.datetime.utcnow().isoformat() + "Z"
    tag = state.get("tag", "geometry_dashboard")
    codex_law = state.get("codex_law", "")
    summary_lines = []

    total = len(modules)
    with_visual = 0
    with_metrics = 0

    module_feedback = []
    for m in modules:
        name = m.get("name", "Module")
        C_avg = m.get("C_avg", None)
        H7_fraction = m.get("H7_fraction", None)
        primary_visual = m.get("primary_visual", None)

        status = []
        if primary_visual and os.path.isfile(primary_visual):
            status.append("visual_ok")
            with_visual += 1
        else:
            status.append("visual_missing")

        if C_avg is not None or H7_fraction is not None:
            status.append("metrics_ok")
            with_metrics += 1
        else:
            status.append("metrics_missing")

        module_feedback.append({
            "name": name,
            "C_avg": C_avg,
            "H7_fraction": H7_fraction,
            "primary_visual": primary_visual,
            "status": status,
        })

    summary_lines.append(f"Modules wired: {total}")
    summary_lines.append(f"Modules with visuals: {with_visual}/{total}")
    summary_lines.append(f"Modules with metrics: {with_metrics}/{total}")

    feedback = {
        "module": "CodexAllOneDashboardFeedback",
        "version": "v1.1",
        "tag": tag,
        "timestamp_utc": now_utc,
        "codex_law": codex_law,
        "summary": " | ".join(summary_lines),
        "modules": module_feedback,
        "recommendations": [
            "Feed this JSON to GPT Bridge v3.x for narrative synthesis.",
            "Investigate modules flagged with 'visual_missing' or 'metrics_missing'.",
            "Use repeated runs to track which modules stabilize around H7."
        ],
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(feedback, f, indent=2)
    except Exception as exc:
        # Non-fatal: just log to stderr
        print(f"Failed to write dashboard_feedback.json: {exc}", file=sys.stderr)


def render_dashboard(state_path, output_png, feedback_json=None):
    if not HAVE_MPL:
        print("Matplotlib not available; cannot render dashboard PNG.", file=sys.stderr)
        return 1

    if not os.path.isfile(state_path):
        print(f"State JSON not found: {state_path}", file=sys.stderr)
        return 1

    # utf-8-sig = tolerant to potential BOM from PowerShell writers
    with open(state_path, "r", encoding="utf-8-sig") as f:
        state = json.load(f)

    modules = state.get("modules", [])
    n = len(modules)
    if n == 0:
        print("No modules in dashboard_state.json; nothing to render.", file=sys.stderr)
        return 1

    cols = min(3, max(1, n))
    rows = int(math.ceil(float(n) / float(cols)))

    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows), dpi=150)
    axes = np.array(axes).reshape(rows, cols)

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
            # Default origin (upper) avoids weird flips; no mirroring.
            ax.imshow(img)
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
            ax.set_title(f"{name}\n{subtitle}", fontsize=8)
        else:
            ax.set_title(name, fontsize=8)

    # Hide any unused subplots
    for j in range(n, rows * cols):
        axes[j // cols, j % cols].axis("off")

    codex_law = state.get("codex_law", "C = (E·I)/(1+|ΔΦ|), H₇ ≈ 0.70–0.75")

    fig.suptitle("Codex All-One Geometry Dashboard\n" + codex_law, fontsize=10)
    # Leave a bit more room for title to avoid overlapping text
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(output_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    if feedback_json is not None:
        try:
            build_feedback(state, modules, feedback_json)
        except Exception as exc:
            print(f"Feedback generation failed: {exc}", file=sys.stderr)

    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-json", required=True)
    ap.add_argument("--output-png", required=True)
    ap.add_argument("--feedback-json", required=False)
    args = ap.parse_args()

    rc = render_dashboard(args.state_json, args.output_png, feedback_json=args.feedback_json)
    return rc


if __name__ == "__main__":
    sys.exit(main())
