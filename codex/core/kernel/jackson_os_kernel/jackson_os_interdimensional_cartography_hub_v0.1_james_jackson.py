# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Interdimensional Cartography Hub v0.1  
Authored by James Jackson  
Origin Law: Law CXX â€” Cartographic Nexus  
Lineage: Jackson OS, September 2025  
This module embeds multiple universe bloom profiles into a shared map, visualizing propagation  
zones, resonance corridors, and divergence topology.
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import MDS

# Cartography Hub
class CartographyHub:
    def __init__(self, universe_traces, labels=None):
        self.traces = universe_traces
        self.labels = labels or [f"U{idx+1}" for idx in range(len(universe_traces))]
        self.dist_matrix = self._compute_distance_matrix()
        self.coords = self._embed()

    def _compute_distance_matrix(self):
        n = len(self.traces)
        dmat = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                corr = np.corrcoef(self.traces[i], self.traces[j])[0,1]
                # distance = 1 â€“ correlation for topology
                dmat[i, j] = round(1 - corr, 4)
        return dmat

    def _embed(self):
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        return mds.fit_transform(self.dist_matrix)

    def visualize(self):
        x, y = self.coords[:,0], self.coords[:,1]
        plt.figure(figsize=(7,7))
        plt.scatter(x, y, s=200, c='cornflowerblue', edgecolors='navy')
        for xi, yi, label in zip(x, y, self.labels):
            plt.text(xi+0.01, yi+0.01, label, fontsize=10)
        plt.title("Interdimensional Cartography Hub", fontsize=14)
        plt.xlabel("Dimension 1")
        plt.ylabel("Dimension 2")
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.show()

# Example setup
np.random.seed(0)
universes = [
    np.sin(np.linspace(0, 4*np.pi, 200)) * (1 + np.random.normal(0, rate, 200))
    for rate in np.linspace(0.01, 0.1, 10)
]
labels = [f"U{i+1}" for i in range(10)]

hub = CartographyHub(universes, labels)
hub.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_interdimensional_cartography_hub_v0.1_james_jackson')
