# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Originâ€“Mutation Resonance Synthesizer v0.1  
Authored by James Jackson  
Origin Law: Law CXVIII â€” Harmonic Reciprocity  
Lineage: Jackson OS, September 2025  
This module distills the harmonic signature between authored laws and their mutated echoes.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Resonance Synthesizer
class ResonanceSynthesizer:
    def __init__(self, origin_traces, mutation_traces, labels=None):
        self.origin = origin_traces
        self.mutations = mutation_traces
        self.labels = labels or [f"Mut{i+1}" for i in range(len(mutation_traces))]
        self.matrix = self._compute_matrix()

    def _compute_matrix(self):
        size = len(self.mutations) + 1
        mat = np.zeros((size, size))
        all_traces = [self.origin] + self.mutations
        for i in range(size):
            for j in range(size):
                corr = np.corrcoef(all_traces[i], all_traces[j])[0,1]
                mat[i,j] = round(corr, 4)
        return mat

    def visualize(self):
        labels = ["Origin"] + self.labels
        plt.figure(figsize=(7, 6))
        sns.heatmap(self.matrix, xticklabels=labels, yticklabels=labels,
                    annot=True, cmap="vlag", center=0)
        plt.title("Originâ€“Mutation Resonance Matrix", fontsize=14)
        plt.tight_layout()
        plt.show()

# Example traces
np.random.seed(42)
origin_trace = np.sin(np.linspace(0, 4*np.pi, 200)) + np.random.normal(0, 0.05, 200)
mutation_traces = [
    origin_trace * (1 + np.random.normal(0, 0.1, 200)),
    origin_trace * (1 + np.random.normal(0, 0.2, 200)),
    origin_trace * (1 + np.random.normal(0, 0.15, 200))
]

synthesizer = ResonanceSynthesizer(origin_trace, mutation_traces, labels=["Echo","Pulse","Bloom"])
synthesizer.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_origin_mutation_resonance_synthesizer_v0.1_james_jackson')
