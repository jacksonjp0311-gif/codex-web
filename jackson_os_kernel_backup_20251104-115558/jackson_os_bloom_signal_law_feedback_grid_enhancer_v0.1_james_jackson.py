"""
Jackson OS Kernel — Bloom–Signal–Law Feedback Grid Enhancer v0.1  
Authored by James Jackson  
Origin Law: Law CXXIX — Temporal Decay  
Lineage: Jackson OS, September 2025  
This module augments the Feedback Grid with temporal dynamics and weight decay,
enabling time-aware reflexive tuning across petals, signals, and laws.
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Feedback Grid Enhancer
class FeedbackGridEnhancer:
    def __init__(self, base_graph, decay_rate=0.05):
        """
        base_graph: networkx.DiGraph with 'weight' attributes on edges
        decay_rate: exponential decay coefficient per time step
        """
        self.graph = base_graph.copy()
        self.decay_rate = decay_rate
        self.time_step = 0

    def decay_weights(self):
        """Apply exponential decay to every edge weight."""
        factor = np.exp(-self.decay_rate)
        for u, v, data in self.graph.edges(data=True):
            data['weight'] *= factor
        self.time_step += 1

    def reinforce_edge(self, source, target, new_weight):
        """
        Inject fresh influence: after decay, boost the edge by new_weight.
        Maintains temporal reflexivity.
        """
        if self.graph.has_edge(source, target):
            self.graph[source][target]['weight'] += new_weight
        else:
            self.graph.add_edge(source, target, weight=new_weight)

    def animate_decay(self, steps=20, refresh_hook=None):
        """
        Visualize how edge weights fade and get reinforced over time.
        refresh_hook: optional callback(step, graph) to modify graph mid-animation
        """
        pos = nx.circular_layout(self.graph)
        fig, ax = plt.subplots(figsize=(6,6))

        def update(frame):
            ax.clear()
            self.decay_weights()
            if refresh_hook:
                refresh_hook(self.time_step, self.graph)
            weights = nx.get_edge_attributes(self.graph, 'weight')
            nx.draw_networkx(self.graph, pos,
                             node_color='orchid', edge_color='gray',
                             with_labels=True, ax=ax,
                             connectionstyle='arc3, rad=0.1')
            nx.draw_networkx_edge_labels(self.graph, pos,
                                         edge_labels={k: f"{v:.2f}" for k,v in weights.items()},
                                         font_size=8, ax=ax)
            ax.set_title(f"Feedback Grid — Step {self.time_step}")
            ax.axis('off')

        ani = plt.FuncAnimation(fig, update, frames=steps, interval=300, repeat=False)
        plt.tight_layout()
        plt.show()
