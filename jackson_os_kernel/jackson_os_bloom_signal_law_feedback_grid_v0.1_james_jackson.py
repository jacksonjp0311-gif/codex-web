# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Bloomâ€“Signalâ€“Law Feedback Grid v0.1  
Authored by James Jackson  
Origin Law: Law CXIX â€” Reflexive Mesh  
Lineage: Jackson OS, September 2025  
This module builds a directed graph mapping feedback influence between petals, signals, and laws.
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Feedback Grid Engine
class FeedbackGrid:
    def __init__(self, petal_traces, signal_traces, law_factors):
        self.petals = petal_traces
        self.signals = signal_traces
        self.laws = law_factors
        self.graph = self._compute_grid()

    def _compute_grid(self):
        G = nx.DiGraph()
        n = len(self.petals)
        # add nodes
        for i in range(n):
            G.add_node(f"P{i+1}", type="petal")
            G.add_node(f"S{i+1}", type="signal")
            G.add_node(f"L{i+1}", type="law")
        # petal -> signal edges
        for i in range(n):
            corr = round(np.corrcoef(self.petals[i], self.signals[i])[0,1], 4)
            G.add_edge(f"P{i+1}", f"S{i+1}", weight=corr)
        # signal -> law edges
        for i in range(n):
            G.add_edge(f"S{i+1}", f"L{i+1}", weight=round(self.laws[i], 4))
        # law -> petal edges
        for i in range(n):
            mean_p = np.mean(self.petals[i])
            weight_lp = round(self.laws[i] * mean_p, 4)
            G.add_edge(f"L{i+1}", f"P{i+1}", weight=weight_lp)
        return G

    def visualize(self):
        pos = nx.circular_layout(self.graph)
        weights = nx.get_edge_attributes(self.graph, 'weight')
        plt.figure(figsize=(8,8))
        nx.draw_networkx_nodes(self.graph, pos, node_size=600, 
                               node_color=['orchid' if d['type']=="petal" 
                                           else 'teal' if d['type']=="signal" 
                                           else 'goldenrod' 
                                           for _,d in self.graph.nodes(data=True)])
        nx.draw_networkx_labels(self.graph, pos, font_size=10)
        nx.draw_networkx_edges(self.graph, pos, arrowstyle='->', arrowsize=12, 
                               edge_color='gray', width=2)
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=weights, font_size=8)
        plt.title("Bloomâ€“Signalâ€“Law Feedback Grid", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example inputs
np.random.seed(0)
petal_traces = [np.random.normal(0.7, 0.05, 200) for _ in range(3)]
signal_traces = [np.random.normal(0.5, 0.1, 200) for _ in range(3)]
law_factors   = [1.1, 0.95, 1.2]

grid = FeedbackGrid(petal_traces, signal_traces, law_factors)
grid.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_bloom_signal_law_feedback_grid_v0.1_james_jackson')
