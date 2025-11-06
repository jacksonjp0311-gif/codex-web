# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Multiverse Congestion Manager v0.1  
Authored by James Jackson  
Origin Law: Law CXL â€” Dynamic Backpressure  
Lineage: Jackson OS, September 2025  
This module enforces capacity limits on interdimensional channels, queues
excess messages under backpressure, and dispatches them when capacity frees.
"""

import networkx as nx
import threading
import time

class MultiverseCongestionManager:
    def __init__(self, router, monitor_interval=0.1):
        """
        router: InterdimensionalNetworkRouter instance
        monitor_interval: seconds between retrying queued messages
        """
        self.router = router
        self.monitor_interval = monitor_interval
        # track load on each directed edge (u,v)
        self.edge_loads = { (u,v): 0 for u, v in self.router.graph.edges() }
        self.pending = []  # list of (source, target, payload)
        self._stop = threading.Event()
        self._wrap_handlers()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitor_thread.start()

    def _wrap_handlers(self):
        # wrap each node handler to decrement load on delivery
        original = dict(self.router.handlers)
        for node, handler in original.items():
            def make_wrapper(n, h):
                def wrapped(src, payload_m):
                    # unwrap our internal payload
                    path = payload_m.get("_path")
                    if path:
                        self._on_message_delivered(path)
                        h(src, payload_m["_orig_payload"])
                    else:
                        h(src, payload_m)
                return wrapped
            self.router.handlers[node] = make_wrapper(node, handler)

    def send_message(self, source, target, payload):
        """
        Attempt to send immediately; if any edge along the path is at capacity,
        queue the message and apply backpressure.
        """
        try:
            path = nx.shortest_path(
                self.router.graph, source, target, weight="latency"
            )
        except nx.NetworkXNoPath:
            print(f"âš ï¸ No route from {source} to {target}")
            return

        # determine bottleneck capacity and current load
        edges = list(zip(path, path[1:]))
        capacities = [self.router.graph[u][v]["capacity"] for u, v in edges]
        loads = [self.edge_loads[(u,v)] for u, v in edges]
        if all(load < cap for load, cap in zip(loads, capacities)):
            # reserve capacity
            for e in edges:
                self.edge_loads[e] += 1
            # wrap payload with path metadata
            payload_m = {"_orig_payload": payload, "_path": path}
            self.router.send_message(source, target, payload_m)
        else:
            # apply backpressure
            self.pending.append((source, target, payload))
            print(f"â³ Backpressure: queuing message {source}â†’{target}")

    def _on_message_delivered(self, path):
        # free capacity on each edge
        for u, v in zip(path, path[1:]):
            key = (u, v)
            self.edge_loads[key] = max(0, self.edge_loads[key] - 1)

    def _monitor_loop(self):
        while not self._stop.is_set():
            to_retry = []
            for msg in list(self.pending):
                src, tgt, pay = msg
                try:
                    path = nx.shortest_path(
                        self.router.graph, src, tgt, weight="latency"
                    )
                except nx.NetworkXNoPath:
                    continue
                edges = list(zip(path, path[1:]))
                capacities = [self.router.graph[u][v]["capacity"] for u, v in edges]
                loads = [self.edge_loads[(u,v)] for u, v in edges]
                if all(load < cap for load, cap in zip(loads, capacities)):
                    to_retry.append(msg)
            for msg in to_retry:
                self.pending.remove(msg)
                self.send_message(*msg)
            time.sleep(self.monitor_interval)

    def stop(self):
        """Stop background monitoring and retries."""
        self._stop.set()
        self._monitor_thread.join()


if __name__ == "__main__":
    # Demo with InterdimensionalNetworkRouter
    from jackson_os_interdimensional_network_router_v0_1_james_jackson import (
        InterdimensionalNetworkRouter
    )

    # setup router
    router = InterdimensionalNetworkRouter()
    router.register_node("U1", lambda s,p: print(f"[U1] recv from {s}: {p}"))
    router.register_node("U2", lambda s,p: print(f"[U2] recv from {s}: {p}"))
    router.register_node("U3", lambda s,p: print(f"[U3] recv from {s}: {p}"))
    router.add_channel("U1", "U2", latency_ms=20, capacity=2)
    router.add_channel("U2", "U3", latency_ms=30, capacity=1)

    # wrap with congestion manager
    mcm = MultiverseCongestionManager(router, monitor_interval=0.2)

    # send bursts to trigger backpressure
    for i in range(5):
        mcm.send_message("U1", "U3", {"seq": i})
        time.sleep(0.05)

    time.sleep(2)   # allow queued retries
    mcm.stop()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_multiverse_congestion_manager_v0.1_james_jackson')
