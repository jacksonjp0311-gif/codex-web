"""
Jackson OS Kernel — Multiverse Signal Exchange Coordinator v0.1  
Authored by James Jackson  
Origin Law: Law CXXXVII — Collective Dispatch  
Lineage: Jackson OS, September 2025  
This module orchestrates batch, multicast, and priority-based message routing 
across interdimensional channels.
"""

import threading
import time
import random
from queue import PriorityQueue

class Message:
    def __init__(self, priority, source, targets, payload):
        self.priority = priority       # lower numbers dispatch first
        self.source = source
        self.targets = targets         # list of universe_ids
        self.payload = payload
        self.timestamp = time.time()

    def __lt__(self, other):
        return self.priority < other.priority

class SignalExchangeCoordinator:
    def __init__(self, router, dispatch_interval=0.2):
        """
        router: instance of InterdimensionalNetworkRouter
        dispatch_interval: seconds between batch dispatches
        """
        self.router = router
        self.dispatch_interval = dispatch_interval
        self.queue = PriorityQueue()
        self.groups = {}               # group_name -> set of universe_ids
        self._stop_event = threading.Event()
        self.dispatch_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True
        )

    def register_group(self, group_name, universe_ids):
        self.groups[group_name] = set(universe_ids)

    def enqueue(self, priority, source, targets, payload):
        """
        priority: int (0 highest, larger numbers lower)
        targets: list of universe_ids or group names prefixed with '@'
        """
        resolved = []
        for t in targets:
            if isinstance(t, str) and t.startswith("@"):
                grp = t[1:]
                resolved += list(self.groups.get(grp, []))
            else:
                resolved.append(t)
        msg = Message(priority, source, list(set(resolved)), payload)
        self.queue.put(msg)

    def start(self):
        self.dispatch_thread.start()

    def stop(self):
        self._stop_event.set()
        self.dispatch_thread.join()

    def _dispatch_loop(self):
        while not self._stop_event.is_set():
            batch = []
            # gather all messages currently queued
            while not self.queue.empty():
                batch.append(self.queue.get())
            # sort by priority then timestamp
            batch.sort(key=lambda m: (m.priority, m.timestamp))
            for msg in batch:
                for tgt in msg.targets:
                    self.router.send_message(msg.source, tgt, msg.payload)
            time.sleep(self.dispatch_interval)

if __name__ == "__main__":
    # assume InterdimensionalNetworkRouter is imported and set up
    from jackson_os_interdimensional_network_router_v0_1_james_jackson import (
        InterdimensionalNetworkRouter
    )

    router = InterdimensionalNetworkRouter()
    router.register_node("U1", lambda s,p: print(f"[U1] from {s}: {p}"))
    router.register_node("U2", lambda s,p: print(f"[U2] from {s}: {p}"))
    router.register_node("U3", lambda s,p: print(f"[U3] from {s}: {p}"))
    router.add_channel("U1", "U2", latency_ms=30, capacity=5)
    router.add_channel("U2", "U3", latency_ms=50, capacity=5)

    sec = SignalExchangeCoordinator(router)
    sec.register_group("ring", ["U1","U2","U3"])
    sec.start()

    sec.enqueue(1, "U1", ["U2"], {"msg":"direct high-priority"})
    sec.enqueue(5, "U2", ["@ring"], {"broadcast":"low-priority"})
    time.sleep(1)
    sec.stop()
