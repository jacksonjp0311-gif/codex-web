"""
Jackson OS Kernel — Bloom Performance Dashboard v0.1  
Authored by James Jackson  
Origin Law: Law CXXXV — Reflexive Transparency  
Lineage: Jackson OS, September 2025  
This module renders a live dashboard of module throughput, latency, and failure rates.
"""

import time
import random
import matplotlib.pyplot as plt
from collections import deque

class PerformanceDashboard:
    def __init__(self, modules, window=50):
        self.modules = modules
        self.window = window
        self.times = deque(maxlen=window)
        self.throughputs = {m: deque(maxlen=window) for m in modules}
        self.latencies = {m: deque(maxlen=window) for m in modules}
        self.failure_rates = {m: deque(maxlen=window) for m in modules}

        plt.ion()
        self.fig, (self.ax_thr, self.ax_lat, self.ax_err) = plt.subplots(
            3, 1, figsize=(10, 8), sharex=True
        )

    def update_metrics(self):
        timestamp = time.time()
        self.times.append(timestamp)
        for m in self.modules:
            # replace these random values with real metrics
            thr = random.uniform(5, 15)           # units/sec
            lat = random.uniform(0.01, 0.1)       # seconds
            err = random.uniform(0, 0.2)          # failure rate
            self.throughputs[m].append(thr)
            self.latencies[m].append(lat)
            self.failure_rates[m].append(err)

    def render(self):
        self.ax_thr.clear()
        self.ax_lat.clear()
        self.ax_err.clear()

        for m in self.modules:
            self.ax_thr.plot(self.times, self.throughputs[m], label=m)
            self.ax_lat.plot(self.times, self.latencies[m], label=m)
            self.ax_err.plot(self.times, self.failure_rates[m], label=m)

        self.ax_thr.set_ylabel("Throughput\n(units/sec)")
        self.ax_lat.set_ylabel("Latency\n(sec)")
        self.ax_err.set_ylabel("Failure Rate")
        self.ax_err.set_xlabel("Time (s)")

        for ax in (self.ax_thr, self.ax_lat, self.ax_err):
            ax.legend(loc="upper left", fontsize=8)
            ax.grid(True, linestyle="--", alpha=0.3)

        self.fig.tight_layout()
        plt.pause(0.1)

    def run(self, duration=60, interval=1):
        start = time.time()
        while time.time() - start < duration:
            self.update_metrics()
            self.render()
            time.sleep(interval)
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    modules = [
        "Law-Signal Feedback Simulator",
        "Recursive Bloom Compiler",
        "Portal-Kernel Integrity Scanner",
        "Bloom–Signal Entanglement Tracker"
    ]
    dashboard = PerformanceDashboard(modules, window=100)
    dashboard.run(duration=30, interval=0.5)
