"""
Jackson OS Kernel — Multiverse Mutation Visualizer v0.1  
Authored by James Jackson  
Origin Law: Law XCIV — Divergence Rendering  
Lineage: Jackson OS, September 2025  
This module animates law mutation and divergence across symbolic universes.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Universe Mutation Profile
class MutationProfile:
    def __init__(self, name, base_value, mutation_rate):
        self.name = name
        self.base = base_value
        self.rate = mutation_rate
        self.trace = self._generate_trace()

    def _generate_trace(self):
        steps = 100
        trace = [self.base]
        for _ in range(steps - 1):
            trace.append(trace[-1] + np.random.normal(self.rate, 0.02))
        return trace

# Visualizer
class MutationVisualizer:
    def __init__(self, profiles):
        self.profiles = profiles

    def animate(self):
        fig, ax = plt.subplots()
        lines = [ax.plot([], [], label=p.name)[0] for p in self.profiles]
        ax.set_xlim(0, 100)
        ax.set_ylim(0.5, 2.0)
        ax.set_title("Multiverse Mutation Divergence — Jackson OS")
        ax.legend()

        def update(frame):
            for line, profile in zip(lines, self.profiles):
                line.set_data(range(frame), profile.trace[:frame])
            return lines

        ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=True)
        plt.tight_layout()
        plt.show()

# Example profiles
profiles = [
    MutationProfile("Echo", 1.0, 0.005),
    MutationProfile("Pulse", 1.0, 0.01),
    MutationProfile("Bloom", 1.0, 0.015),
    MutationProfile("Drift", 1.0, 0.02),
    MutationProfile("Aether", 1.0, 0.003)
]

visualizer = MutationVisualizer(profiles)
visualizer.animate()
