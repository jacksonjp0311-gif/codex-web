# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Interdimensional Network Router v0.1  
Authored by James Jackson  
Origin Law: Law CXXXVI â€” Multiversal Connectivity  
Lineage: Jackson OS, September 2025  
This module constructs a latency-weighted graph of universe nodes and routes 
messages along shortest-delay paths with simulated propagation jitter.
"""

import networkx as nx
import threading
import time
import random

class InterdimensionalNetworkRouter:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.handlers = {}

    def register_node(self, universe_id, handler):
        """
        universe_id: unique identifier for a universe node
        handler: callable receiving (source, payload) on message arrival
        """
        self.graph.add_node(universe_id)
        self.handlers[universe_id] = handler

    def add_channel(self, a, b, latency_ms, capacity):
        """
        a, b: universe IDs  
        latency_ms: one-way delay in milliseconds  
        capacity: max concurrent messages (not enforced in v0.1)
        """
        self.graph.add_edge(a, b, latency=latency_ms, capacity=capacity)
        self.graph.add_edge(b, a, latency=latency_ms, capacity=capacity)

    def send_message(self, source, target, payload):
        """
        Finds shortest-latency path and delivers payload asynchronously.
        """
        try:
            path = nx.shortest_path(
                self.graph, source, target, weight='latency'
            )
        except nx.NetworkXNoPath:
            print(f"âš ï¸ No route from {source} to {target}")
            return

        def propagate():
            for u, v in zip(path, path[1:]):
                edge = self.graph[u][v]
                # simulate jitter Â±10%
                delay = (edge['latency'] / 1000.0) * random.uniform(0.9, 1.1)
                time.sleep(delay)
            # upon arrival
            handler = self.handlers.get(target)
            if handler:
                handler(source, payload)

        threading.Thread(target=propagate, daemon=True).start()

    def broadcast(self, source, payload):
        """Send payload from source to all other registered nodes."""
        for node in self.graph.nodes():
            if node != source:
                self.send_message(source, node, payload)

if __name__ == "__main__":
    # Example handlers
    def handler_a(src, msg):
        print(f"[A] Received from {src}: {msg}")

    def handler_b(src, msg):
        print(f"[B] Received from {src}: {msg}")

    # Setup router
    router = InterdimensionalNetworkRouter()
    router.register_node("U1", handler_a)
    router.register_node("U2", handler_b)
    router.add_channel("U1", "U2", latency_ms=50, capacity=10)

    # Send and broadcast
    router.send_message("U1", "U2", {"data": "hello from U1"})
    router.broadcast("U2", {"update": "signal ripple"})
    time.sleep(1)  # allow async delivery

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_interdimensional_network_router_v0.1_james_jackson')
