# 𓂀 CODEX TRUTHFIELD VISUALIZER v1.0 — ΔΦ FIELD MAP
# Reads truthfield_state_v1_0.json and renders a simple scatter field:
#   x = authority_weight
#   y = provenance_entropy
#   color/size = trust_score

import json
import sys
from typing import Dict

import matplotlib.pyplot as plt


def load_state(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_truthfield(state_path: str, png_path: str) -> None:
    state = load_state(state_path)
    runs = state.get("runs", [])

    if not runs:
        print("[TRUTHFIELD-VIZ] No runs found in state.")
        return

    xs = [r["authority_weight"] for r in runs]
    ys = [r["provenance_entropy"] for r in runs]
    ts = [r.get("trust_score", 0.0) for r in runs]
    labels = [r["name"] for r in runs]

    # Normalize trust for size scaling
    max_t = max(ts) if ts else 1.0
    sizes = [100 + 400 * (t / (max_t + 1e-8)) for t in ts]

    fig, ax = plt.subplots()
    scatter = ax.scatter(xs, ys, s=sizes)

    for x, y, label in zip(xs, ys, labels):
        ax.text(x, y, label, fontsize=9, ha="center", va="bottom")

    ax.set_xlabel("authority_weight (coordination)")
    ax.set_ylabel("provenance_entropy (bits)")
    ax.set_title("Codex Truthfield v1.0 — ΔΦ Trust Map")

    ax.grid(True)

    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    plt.close(fig)
    print(f"[TRUTHFIELD-VIZ] PNG written → {png_path}")


def main(state_path: str, png_path: str) -> None:
    render_truthfield(state_path, png_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: truthfield_visualizer_v1_0.py STATE_PATH PNG_PATH")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
