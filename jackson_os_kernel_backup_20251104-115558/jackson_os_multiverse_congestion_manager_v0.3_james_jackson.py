"""
Jackson OS Kernel — Multiverse Congestion Manager v0.3  
Authored by James Jackson  
Origin Law: Law CLI — Adaptive Throughput  
Lineage: Jackson OS, September 2025  
This module routes messages across multiple kernel endpoints,  
honors per-endpoint SLAs, and dynamically rebalances priorities  
to prevent congestion and maintain performance guarantees.
"""

import time
import threading
import random
import logging
from collections import defaultdict, deque

# configure logger
logger = logging.getLogger("MultiverseCongestionManagerV3")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("multiverse_congestion_manager_v0.3.log")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Endpoint:
    def __init__(self, name, sla_rate, weight=1.0):
        """
        name: unique identifier  
        sla_rate: max messages per second  
        weight: dynamic priority factor  
        """
        self.name = name
        self.sla_rate = sla_rate
        self.weight = weight
        self.queue = deque()
        self.processed = 0
        self.lock = threading.Lock()

    def enqueue(self, msg):
        with self.lock:
            self.queue.append(msg)
            logger.debug(f"Enqueued to {self.name}: {msg}")

    def dequeue(self):
        with self.lock:
            if self.queue:
                self.processed += 1
                return self.queue.popleft()
        return None

    @property
    def backlog(self):
        return len(self.queue)

    def adjust_weight(self, factor):
        with self.lock:
            # safeguard floor at 0.1 to avoid starvation
            self.weight = max(0.1, self.weight * factor)
            logger.info(f"Adjusted weight for {self.name} -> {self.weight:.2f}")


class MultiverseCongestionManagerV3:
    def __init__(self, rebalance_interval=5):
        """
        rebalance_interval: seconds between dynamic priority adjustments
        """
        self.endpoints = {}
        self.lock = threading.Lock()
        self.rebalance_interval = rebalance_interval
        self.running = False
        self._rebalance_thread = None

    def register_endpoint(self, endpoint):
        with self.lock:
            self.endpoints[endpoint.name] = endpoint
            logger.info(f"Registered endpoint {endpoint.name} (SLA={endpoint.sla_rate}/s)")

    def unregister_endpoint(self, name):
        with self.lock:
            self.endpoints.pop(name, None)
            logger.info(f"Unregistered endpoint {name}")

    def route_message(self, msg):
        """
        Routes a message to the endpoint with the highest (weight / (backlog+1)) ratio.
        """
        with self.lock:
            if not self.endpoints:
                logger.warning("No endpoints available for routing")
                return
            # choose endpoint maximizing weight/(backlog+1)
            chosen = max(
                self.endpoints.values(),
                key=lambda ep: ep.weight / (ep.backlog + 1)
            )
        chosen.enqueue(msg)
        logger.info(f"Routed message to {chosen.name}: {msg}")

    def _rebalance_loop(self):
        while self.running:
            time.sleep(self.rebalance_interval)
            with self.lock:
                for ep in self.endpoints.values():
                    if ep.backlog > ep.sla_rate * self.rebalance_interval:
                        ep.adjust_weight(0.9)
                    else:
                        ep.adjust_weight(1.01)

    def start(self):
        if self.running:
            return
        self.running = True
        self._rebalance_thread = threading.Thread(
            target=self._rebalance_loop, daemon=True
        )
        self._rebalance_thread.start()
        logger.info("Multiverse Congestion Manager started")

    def stop(self):
        self.running = False
        if self._rebalance_thread:
            self._rebalance_thread.join(timeout=1)
        logger.info("Multiverse Congestion Manager stopped")


if __name__ == "__main__":
    # demo simulation
    mgr = MultiverseCongestionManagerV3(rebalance_interval=3)

    # create endpoints with different SLAs
    eps = [
        Endpoint("SignalSim", sla_rate=5),
        Endpoint("BloomCompile", sla_rate=3),
        Endpoint("IntegrityScan", sla_rate=4),
    ]
    for ep in eps:
        mgr.register_endpoint(ep)

    mgr.start()

    try:
        # inject messages at random
        for i in range(30):
            msg = f"MSG-{i}"
            mgr.route_message(msg)

            # simulate processing
            for ep in eps:
                item = ep.dequeue()
                if item:
                    print(f"Processed by {ep.name}: {item}")

            time.sleep(random.uniform(0.2, 0.7))
    finally:
        mgr.stop()
