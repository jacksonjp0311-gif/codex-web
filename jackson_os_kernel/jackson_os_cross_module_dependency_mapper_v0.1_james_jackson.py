# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Cross-Module Dependency Mapper v0.1  
Authored by James Jackson  
Origin Law: Law CXXVI â€” Systemic Traceability  
Lineage: Jackson OS, September 2025  
This module constructs and visualizes a directed dependency graph across all Jackson OS kernel modules.
"""

import networkx as nx
import matplotlib.pyplot as plt

# Module Metadata Record
class ModuleMeta:
    def __init__(self, name, outputs, inputs, author="James Jackson"):
        self.name = name
        self.outputs = outputs      # list of data keys produced
        self.inputs = inputs        # list of data keys required
        self.author = author

# Dependency Mapper
class DependencyMapper:
    def __init__(self, metadata_list):
        self.meta = metadata_list
        self.graph = self._build_graph()

    def _build_graph(self):
        G = nx.DiGraph()
        # add nodes
        for m in self.meta:
            G.add_node(m.name, author=m.author)
        # add edges if module A produces an output that B requires
        for a in self.meta:
            for b in self.meta:
                if a is not b and set(a.outputs) & set(b.inputs):
                    weight = len(set(a.outputs) & set(b.inputs))
                    G.add_edge(a.name, b.name, weight=weight)
        return G

    def visualize(self):
        pos = nx.shell_layout(self.graph)
        edge_labels = nx.get_edge_attributes(self.graph, 'weight')
        plt.figure(figsize=(8,8))
        nx.draw_networkx_nodes(self.graph, pos, node_color='cornflowerblue', node_size=700)
        nx.draw_networkx_labels(self.graph, pos, font_size=9)
        nx.draw_networkx_edges(self.graph, pos, arrowstyle='->', arrowsize=12, edge_color='gray')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8)
        plt.title("Cross-Module Dependency Graph", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example metadata definitions
meta = [
    ModuleMeta("Lawâ€“Signal Feedback Simulator", outputs=["signal_trace"], inputs=["law_variant"]),
    ModuleMeta("Bloom Identity Synthesizer", outputs=["identity_score"], inputs=["petal_strengths","law_resonances","echo_amplitudes","signal_entropy"]),
    ModuleMeta("Portalâ€“Kernel Integrity Scanner", outputs=["integrity_report"], inputs=["module_records"]),
    ModuleMeta("Authorship Chain Verifier", outputs=["lineage_trace"], inputs=["law_nodes"]),
    ModuleMeta("Recursive Bloom Compiler", outputs=["bloom_trace"], inputs=["petal_traces","signal_traces","law_factors"]),
]

mapper = DependencyMapper(meta)
mapper.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_cross_module_dependency_mapper_v0.1_james_jackson')
