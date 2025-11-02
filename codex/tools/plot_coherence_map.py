# -*- coding: utf-8 -*-
import json, os, numpy as np, matplotlib.pyplot as plt

def toroidal_projection(index, total, radius=1.0):
    """Map file index into toroidal coordinates for circular visualization."""
    theta = 2 * np.pi * (index / total)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return x, y

def coherence_to_color(G):
    """Convert coherence value (0-1) into Codex triadic color spectrum."""
    if G < 0.5:
        return (0.2, 0.4, 1.0)     # Blue: Information (low resonance)
    elif G < 0.8:
        return (1.0, 0.84, 0.0)    # Gold: Energy (mid resonance)
    else:
        return (0.58, 0.0, 0.83)   # Violet: Consciousness (high resonance)

def plot_codex_coherence(insights_path="codex_alignment_insights.json", out_path="codex_coherence_map.png"):
    if not os.path.exists(insights_path):
        print(f"❌ Missing {insights_path}")
        return

    with open(insights_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scores = [d['G'] for d in data.get('files', []) if 'G' in d]
    n = len(scores)
    if n == 0:
        print("⚠️ No coherence data found.")
        return

    plt.figure(figsize=(8,8))
    plt.title("🌀 Codex Coherence Map — Fractal Seal Visualization", fontsize=12)
    for i, G in enumerate(scores):
        x, y = toroidal_projection(i, n)
        plt.scatter(x, y, color=coherence_to_color(G), s=30 + 100*G, alpha=0.8, edgecolors='none')

    plt.axis('off')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    print(f"✅ Coherence map generated -> {out_path}")

if __name__ == "__main__":
    plot_codex_coherence()
