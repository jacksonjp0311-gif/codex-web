"""
Jackson OS Kernel — Multiverse Congestion Manager v0.2  
Authored by James Jackson  
Origin Law: Law CXLV — Dynamic Capacity Scaling  
Lineage: Jackson OS, September 2025  
This module enforces channel capacity limits, queues excess traffic by priority,
auto-scales capacities based on utilization, and dispatches backpressured messages
in priority order.
"""

import networkx as nx
import threading
import time
from queue import PriorityQueue
from collections import defaultdict

class CongestionManagerV2:
    def __init__(
        self,
        router,
        scale_interval=5.0,
        scale_up_factor=1.5,
        scale_down_factor=0.75,
        up_threshold=0.8,
        down_threshold=0.3,
    ):
        """
        router: InterdimensionalNetworkRouter instance
        scale_interval: seconds between auto-scaling checks
        scale_up_factor: multiply capacity when over-utilized
        scale_down_factor: multiply capacity when under-utilized
        up_threshold: fraction of capacity to trigger scale-up
        down_threshold: fraction to trigger scale-down
        """
        self.router = router
        self.scale_interval = scale_interval
        self.scale_up = scale_up_factor
        self.scale_down = scale_down_factor
        self.up_th = up_threshold
        self.down_th = down_threshold

        # initial capacities and live loads
        self.capacities = {
            (u, v): data["capacity"]
            for u, v, data in router.graph.edges(data=True)
        }
        self.loads = defaultdict(int)

        # priority queue: (priority, timestamp, source, target, payload)
        self.queue = PriorityQueue()

        # wrap router.send_message
        self._orig_send = router.send_message
        router.send_message = self._send_message

        self._stop_event = threading.Event()
        self._scale_thread = threading.Thread(
            target=self._auto_scale_loop, daemon=True
        )
        self._scale_thread.start()

    def _send_message(self, source, target, payload, priority=5):
        """
        Attempt immediate send; if any edge saturated, queue by priority.
        Lower priority value dispatches first.
        """
        try:
            path = nx.shortest_path(
                self.router.graph, source, target, weight="latency"
            )
        except nx.NetworkXNoPath:
            print(f"⚠️ No route {source}→{target}")
            return

        # check all edges
        edges = list(zip(path, path[1:]))
        utilization = [
            self.loads[(u, v)] / self.capacities[(u, v)]
            for u, v in edges
        ]
        if all(u < 1.0 for u in utilization):
            # reserve load and send
            for u, v in edges:
                self.loads[(u, v)] += 1
            self._orig_send(source, target, payload)
        else:
            ts = time.time()
            self.queue.put((priority, ts, source, target, payload))
            print(f"⏳ Queued {source}→{target} (prio={priority})")

    def release_capacity(self, path):
        """Called by router when delivery completes to free loads."""
        for u, v in zip(path, path[1:]):
            key = (u, v)
            self.loads[key] = max(0, self.loads[key] - 1)

    def _auto_scale_loop(self):
        while not self._stop_event.is_set():
            time.sleep(self.scale_interval)
            # scale capacities
            for edge, cap in list(self.capacities.items()):
                load = self.loads[edge]
                util = load / cap if cap > 0 else 0
                if util > self.up_th:
                    new_cap = int(cap * self.scale_up)
                    self.capacities[edge] = new_cap
                    self.router.graph[edge[0]][edge[1]]["capacity"] = new_cap
                    print(f"⬆️ Scaled up {edge} to {new_cap}")
                elif util < self.down_th and cap > 1:
                    new_cap = max(1, int(cap * self.scale_down))
                    self.capacities[edge] = new_cap
                    self.router.graph[edge[0]][edge[1]]["capacity"] = new_cap
                    print(f"⬇️ Scaled down {edge} to {new_cap}")
            # retry queued messages by priority
            self._dispatch_queued()

    def _dispatch_queued(self):
        temp = []
        while not self.queue.empty():
            prio, ts, src, tgt, pay = self.queue.get()
            try:
                path = nx.shortest_path(
                    self.router.graph, src, tgt, weight="latency"
                )
            except nx.NetworkXNoPath:
                continue
            edges = list(zip(path, path[1:]))
            if all(self.loads[e] < self.capacities[e] for e in edges):
                for e in edges:
                    self.loads[e] += 1
                self._orig_send(src, tgt, pay)
                print(f"▶️ Dispatched queued {src}→{tgt} (prio={prio})")
            else:
                temp.append((prio, ts, src, tgt, pay))
        # re-queue leftovers
        for item in temp:
            self.queue.put(item)

    def stop(self):
        """Stop auto-scaling and dispatch loop."""
        self._stop_event.set()
        self._scale_thread.join()

if __name__ == "__main__":
    from jackson_os_interdimensional_network_router_v0_1_james_jackson import (
        InterdimensionalNetworkRouter
    )

    # Setup router and congestion manager
    router = InterdimensionalNetworkRouter()
    router.register_node("U1", lambda s,p: print(f"[U1] recv {p}"))
    router.register_node("U2", lambda s,p: print(f"[U2] recv {p}"))
    router.add_channel("U1", "U2", latency_ms=20, capacity=2)

    mgr = CongestionManagerV2(router, scale_interval=2.0)

    # send bursts with mixed priority
    for i in range(6):
        prio = 1 if i % 3 == 0 else 5
        router.send_message("U1", "U2", {"seq": i}, priority=prio)
        time.sleep(0.3)

    time.sleep(5)
    mgr.stop()
