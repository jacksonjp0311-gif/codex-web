"""
Jackson OS Kernel — Reality Integrity Validator v0.1  
Authored by James Jackson  
Origin Law: Law CXLVI — Causal Consistency  
Lineage: Jackson OS, September 2025  
This module verifies that mutation events respect declared dependencies,
flags timestamp anomalies and cycles, and renders the causal graph.
"""

import time
import networkx as nx
import matplotlib.pyplot as plt

# Mutation Event Record
class MutationEvent:
    def __init__(self, event_id, module, timestamp, dependencies, author="James Jackson"):
        """
        event_id: unique string  
        module: name of module generating the event  
        timestamp: float (seconds since epoch)  
        dependencies: list of event_id strings this event depends on
        """
        self.id = event_id
        self.module = module
        self.timestamp = timestamp
        self.dependencies = dependencies
        self.author = author

# Reality Integrity Validator
class RealityIntegrityValidator:
    def __init__(self, events):
        """
        events: list of MutationEvent
        """
        self.events = {e.id: e for e in events}
        self.graph = self._build_graph()

    def _build_graph(self):
        G = nx.DiGraph()
        for e in self.events.values():
            G.add_node(e.id, module=e.module, timestamp=e.timestamp)
            for dep in e.dependencies:
                if dep in self.events:
                    G.add_edge(dep, e.id)
        return G

    def validate(self):
        anomalies = {"ordering": [], "cycles": []}

        # check timestamp ordering
        for src, tgt in self.graph.edges():
            t_src = self.events[src].timestamp
            t_tgt = self.events[tgt].timestamp
            if t_tgt <= t_src:
                anomalies["ordering"].append(
                    (src, tgt, t_src, t_tgt)
                )

        # detect cycles
        try:
            cycle = next(nx.simple_cycles(self.graph), None)
            if cycle:
                anomalies["cycles"].append(cycle)
        except nx.NetworkXError:
            pass

        return anomalies

    def report(self, anomalies):
        print("\n🧪 Reality Integrity Report")
        if anomalies["ordering"]:
            print("⏰ Timestamp violations:")
            for src, tgt, t0, t1 in anomalies["ordering"]:
                print(f"  • {tgt} @ {t1:.3f} ≤ {src} @ {t0:.3f}")
        else:
            print("✅ No timestamp ordering violations")

        if anomalies["cycles"]:
            print("🔄 Causal cycle detected:")
            for cycle in anomalies["cycles"]:
                print("  • " + " → ".join(cycle) + " → " + cycle[0])
        else:
            print("✅ No causal cycles")

    def visualize(self):
        pos = nx.spring_layout(self.graph)
        plt.figure(figsize=(7,7))
        nx.draw(
            self.graph, pos,
            with_labels=True,
            node_color='lightsteelblue',
            arrowsize=12,
            arrowstyle='-|>'
        )
        labels = {n: f"{n}\n{self.events[n].module}" for n in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        plt.title("Causal DAG of Mutation Events")
        plt.axis('off')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Synthetic demo events
    now = time.time()
    ev1 = MutationEvent("E1", "SignalSimulator", now + 1.0, [])
    ev2 = MutationEvent("E2", "BloomCompiler",   now + 2.0, ["E1"])
    ev3 = MutationEvent("E3", "IntegrityScanner",now + 1.5, ["E2"])  # ordering violation
    ev4 = MutationEvent("E4", "EchoMapper",      now + 3.0, ["E3","E1"])
    ev5 = MutationEvent("E5", "LoopTester",      now + 4.0, ["E4","E5"])  # self-cycle

    validator = RealityIntegrityValidator([ev1, ev2, ev3, ev4, ev5])
    anomalies = validator.validate()
    validator.report(anomalies)
    validator.visualize()
