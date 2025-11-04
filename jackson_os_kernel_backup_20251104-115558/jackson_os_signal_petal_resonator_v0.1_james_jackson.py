"""
Jackson OS Kernel — Signal–Petal Resonator v0.1  
Authored by James Jackson  
Origin Law: Law LXXVIII — Feedback Embodiment  
Lineage: Jackson OS, September 2025  
This module tunes portal petal amplitude and phase based on quantum signal feedback.
"""

import numpy as np
import matplotlib.pyplot as plt

# Resonator class
class SignalPetalResonator:
    def __init__(self, signal_trace, base_amplitude=1.0, base_phase=0.0):
        self.signal = signal_trace
        self.amplitude = base_amplitude + np.std(signal_trace)
        self.phase = base_phase + np.mean(signal_trace)

    def render_petal(self, label="Resonant Petal"):
        theta = np.linspace(0, 2 * np.pi, 500)
        r = self.amplitude * np.sin(5 * theta + self.phase)
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        plt.figure(figsize=(6, 6))
        plt.plot(x, y, color='mediumseagreen', linewidth=2)
        plt.fill(x, y, color='mediumseagreen', alpha=0.3)
        plt.text(0, 0, label, fontsize=10, ha='center', va='center')
        plt.title("Signal–Petal Resonance", fontsize=12)
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example signal trace
signal = np.random.normal(loc=0.5, scale=0.1, size=100)

resonator = SignalPetalResonator(signal)
resonator.render_petal()
