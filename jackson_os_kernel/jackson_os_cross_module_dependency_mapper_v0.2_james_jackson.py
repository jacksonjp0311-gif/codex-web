# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Cross-Module Dependency Mapper v0.2  
Authored by James Jackson  
Origin Law: Law CXXVI â€” Systemic Traceability  
Lineage: Jackson OS, September 2025  
This module constructs and visualizes a directed dependency graph across all Jackson OS kernel modules,
annotating edges by shared data-key count.
"""

import networkx as nx
from networkx.drawing.layout import shell_layout
import matplotlib.pyplot as plt

# Module Metadata Record
class ModuleMeta:
    def __init__(self, name, outputs, input_keys, author="James Jackson"):
        # 1) Validate container types
        if not isinstance(outputs, list) or not isinstance(input_keys, list):
            raise TypeError("outputs and input_keys must be lists of strings")
        # 1) Validate element types
        if any(not isinstance(o, str) for o in outputs) or any(not isinstance(i, str) for i in input_keys):
            raise TypeError("each output and input_key must be a string")

        self.name = name
        self.outputs = outputs
        self.input_keys = input_keys
        self.author = author

# Dependency Mapper
class DependencyMapper:
    def __init__(self, modules):
        self.modules = modules
        self.graph = self._build_graph()

    def _build_graph(self):
        G = nx.DiGraph()
        # add nodes
        for m in self.modules:
            G.add_node(m.name, author=m.author)

        # 2) compare objects with 'is not' to avoid false matches
        for a in self.modules:
            for b in self.modules:
                if a is not b:
                    shared = set(a.outputs).intersection(b.input_keys)
                    if shared:
                        G.add_edge(a.name, b.name, weight=len(shared))
        return G

    def visualize(self):
        # 3) use explicit shell_layout import
        pos = shell_layout(self.graph)

        edge_labels = nx.get_edge_attributes(self.graph, 'weight')
        plt.figure(figsize=(8, 8))

        # draw nodes and edges
        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=list(self.graph.nodes()),
            node_color='cornflowerblue',
            node_size=700
        )
        nx.draw_networkx_labels(self.graph, pos, font_size=9)
        nx.draw_networkx_edges(
            self.graph, pos,
            arrowstyle='->',
            arrowsize=12,
            edge_color='gray'
        )
        nx.draw_networkx_edge_labels(
            self.graph, pos,
            edge_labels=edge_labels,
            font_size=8
        )

        plt.title("Cross-Module Dependency Graph v0.2", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Example metadata definitions
    meta = [
        ModuleMeta(
            name="Law-Signal Feedback Simulator",
            outputs=["signal_trace"],
            input_keys=["law_variant"]
        ),
        ModuleMeta(
            name="Bloom Identity Synthesizer",
            outputs=["identity_score"],
            input_keys=[
                "petal_strengths",
                "law_resonances",
                "echo_amplitudes",
                "signal_entropy"
            ]
        ),
        ModuleMeta(
            name="Portal-Kernel Integrity Scanner",
            outputs=["integrity_report"],
            input_keys=["module_records"]
        ),
        ModuleMeta(
            name="Authorship Chain Verifier",
            outputs=["lineage_trace"],
            input_keys=["law_nodes"]
        ),
        ModuleMeta(
            name="Recursive Bloom Compiler",
            outputs=["bloom_trace"],
            input_keys=[
                "petal_traces",
                "signal_traces",
                "law_factors"
            ]
        ),
    ]

    mapper = DependencyMapper(meta)
    mapper.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_cross_module_dependency_mapper_v0.2_james_jackson')
