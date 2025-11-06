# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Multiverse Congestion Manager v0.4  
Authored by James Jackson  
Origin Law: Law CLV â€” Predictive SLA Routing  
Lineage: Jackson OS, October 2025  
This module extends v0.3 by forecasting per-endpoint backlog with ARIMA  
and proactively rebalancing priorities to avoid SLA violations.
"""

import time
import threading
import random
import logging
from collections import defaultdict, deque

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

# configure logger
logger = logging.getLogger("MultiverseCongestionManagerV4")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("multiverse_congestion_manager_v0.4.log")
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
            logger.debug(f"Enqueued {msg} to {self.name}")

    def dequeue(self):
        with self.lock:
            if self.queue:
                self.processed += 1
                return self.queue.popleft()
        return None

    @property
    def backlog(self):
        with self.lock:
            return len(self.queue)

    def adjust_weight(self, factor):
        with self.lock:
            self.weight = max(0.1, self.weight * factor)
            logger.info(f"Adjusted weight for {self.name} -> {self.weight:.2f}")


class MultiverseCongestionManagerV4:
    def __init__(self, rebalance_interval=5, forecast_horizon=3):
        """
        rebalance_interval: seconds between dynamic adjustments  
        forecast_horizon: steps ahead to forecast backlog
        """
        self.endpoints = {}
        self.lock = threading.Lock()
        self.rebalance_interval = rebalance_interval
        self.forecast_horizon = forecast_horizon
        self.running = False
        self._rebalance_thread = None

        # historic backlog per endpoint (timestamp series)
        self.history = defaultdict(list)

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
        Route to endpoint maximizing weight/(backlog+1).
        """
        with self.lock:
            if not self.endpoints:
                logger.warning("No endpoints to route message")
                return
            chosen = max(
                self.endpoints.values(),
                key=lambda ep: ep.weight / (ep.backlog + 1)
            )
        chosen.enqueue(msg)
        logger.info(f"Routed message {msg} â†’ {chosen.name}")

    def _forecast_backlog(self, name):
        """
        Fit ARIMA(1,0,1) on history and forecast next backlog.
        Returns predicted backlog or None on failure.
        """
        series = self.history[name]
        if len(series) < 5:
            return None
        try:
            idx = pd.RangeIndex(len(series))
            model = ARIMA(series, order=(1, 0, 1)).fit(disp=False)
            forecast = model.get_forecast(steps=self.forecast_horizon)
            pred = forecast.predicted_mean
            return max(0.0, float(pred.iloc[0]))
        except Exception as e:
            logger.debug(f"Forecast error for {name}: {e}")
            return None

    def _rebalance_loop(self):
        while self.running:
            time.sleep(self.rebalance_interval)
            with self.lock:
                for ep in self.endpoints.values():
                    # record current backlog
                    self.history[ep.name].append(ep.backlog)

                for ep in self.endpoints.values():
                    pred = self._forecast_backlog(ep.name)
                    threshold = ep.sla_rate * self.rebalance_interval
                    if pred is not None and pred > threshold:
                        # predicted SLA breach: lower priority
                        ep.adjust_weight(0.8)
                        logger.info(
                            f"Predicted backlog {pred:.1f} > threshold {threshold:.1f} for {ep.name}"
                        )
                    else:
                        # safe: restore weight
                        ep.adjust_weight(1.02)

    def start(self):
        if self.running:
            return
        self.running = True
        self._rebalance_thread = threading.Thread(
            target=self._rebalance_loop, daemon=True
        )
        self._rebalance_thread.start()
        logger.info("Multiverse Congestion Manager v0.4 started")

    def stop(self):
        self.running = False
        if self._rebalance_thread:
            self._rebalance_thread.join(timeout=1)
        logger.info("Multiverse Congestion Manager v0.4 stopped")


if __name__ == "__main__":
    # demo simulation
    mgr = MultiverseCongestionManagerV4(rebalance_interval=4, forecast_horizon=2)

    # create endpoints
    endpoints = [
        Endpoint("SignalSim", sla_rate=5),
        Endpoint("BloomCompile", sla_rate=3),
        Endpoint("IntegrityScan", sla_rate=4),
    ]
    for ep in endpoints:
        mgr.register_endpoint(ep)

    mgr.start()

    try:
        for i in range(40):
            msg = f"MSG-{i}"
            mgr.route_message(msg)
            # process one message per endpoint
            for ep in endpoints:
                item = ep.dequeue()
                if item:
                    print(f"Processed by {ep.name}: {item}")
            time.sleep(random.uniform(0.2, 0.6))
    finally:
        mgr.stop()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_multiverse_congestion_manager_v0.4_james_jackson')
