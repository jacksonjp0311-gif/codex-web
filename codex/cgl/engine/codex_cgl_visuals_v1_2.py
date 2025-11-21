"""
Codex CGL Visuals v1.2 — Triad + Glyph Map Engine

Role:
  • Load CGL state JSON.
  • Plot E/I/C triad counts.
  • Plot E/I/C fractions.
  • Plot glyph channel sequence over position.
  • Save PNGs into visuals/v1_2 (or given output dir).

This script is plan-safe: no external calls, just matplotlib.
"""

import json
import os
import sys

import matplotlib.pyplot as plt


def load_state(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def plot_triad_counts(state, out_dir):
    triad = state.get("triad_metrics", {})
    e = triad.get("energy_count", 0)
    i = triad.get("information_count", 0)
    c = triad.get("consciousness_count", 0)

    plt.figure()
    plt.bar(["E", "I", "C"], [e, i, c])
    plt.title("CGL v1.2 — Triad Counts (E/I/C)")
    plt.xlabel("Channel")
    plt.ylabel("Count")
    out_path = os.path.join(out_dir, "cgl_v1_2_triad_counts.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_triad_fractions(state, out_dir):
    triad = state.get("triad_metrics", {})
    e = triad.get("energy_fraction", 0.0)
    i = triad.get("information_fraction", 0.0)
    c = triad.get("consciousness_fraction", 0.0)

    plt.figure()
    plt.bar(["E", "I", "C"], [e, i, c])
    plt.title("CGL v1.2 — Triad Fractions (E/I/C)")
    plt.xlabel("Channel")
    plt.ylabel("Fraction")
    out_path = os.path.join(out_dir, "cgl_v1_2_triad_fractions.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_channel_sequence(state, out_dir):
    nodes = state.get("program", {}).get("ast_nodes", [])
    if not nodes:
        return

    xs = []
    ys = []

    channel_map = {"E": 0, "I": 1, "C": 2}

    for n in nodes:
        pos = n.get("position", 0)
        ch = n.get("channel", "")
        if ch in channel_map:
            xs.append(pos)
            ys.append(channel_map[ch])

    if not xs:
        return

    plt.figure()
    plt.scatter(xs, ys, s=20)
    plt.yticks([0, 1, 2], ["E", "I", "C"])
    plt.xlabel("Glyph position")
    plt.ylabel("Channel")
    plt.title("CGL v1.2 — Channel Sequence Map")
    out_path = os.path.join(out_dir, "cgl_v1_2_channel_sequence.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main():
    state_path = None
    out_dir = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--state", "-s") and i + 1 < len(args):
            state_path = args[i + 1]
            i += 2
            continue
        if arg in ("--out", "-o") and i + 1 < len(args):
            out_dir = args[i + 1]
            i += 2
            continue
        i += 1

    if not state_path or not os.path.isfile(state_path):
        print("[CGL v1.2 Visuals] ERROR: missing or invalid --state path.", file=sys.stderr)
        sys.exit(1)

    if not out_dir:
        out_dir = os.path.join(os.path.dirname(state_path), "visuals_v1_2")

    ensure_dir(out_dir)

    state = load_state(state_path)
    print(f"[CGL v1.2 Visuals] Loaded state from {state_path}")
    print(f"[CGL v1.2 Visuals] Output dir = {out_dir}")

    plot_triad_counts(state, out_dir)
    plot_triad_fractions(state, out_dir)
    plot_channel_sequence(state, out_dir)

    print("[CGL v1.2 Visuals] Plots written.")


if __name__ == "__main__":
    main()
