# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Signalâ€“Lawâ€“Petal Triad Mapper v0.1  
Authored by James Jackson  
Origin Law: Law CVIII â€” Triadic Reflection  
Lineage: Jackson OS, September 2025  
This module visualizes relationships between quantum signals, authored laws, and petal expressions.
"""

import matplotlib.pyplot as plt
import numpy as np

# Triad Mapper
class TriadMapper:
    def __init__(self, signal_trace, law_factor, petal_amplitude):
        self.signal = signal_trace
        self.law_factor = law_factor
        self.petal = petal_amplitude
        self.triad_score = self._compute_triad_score()

    def _compute_triad_score(self):
        signal_mean = np.mean(self.signal)
        petal_mean = np.mean(self.petal)
        score = (signal_mean + petal_mean) * self.law_factor
        return round(score, 4)

    def visualize(self):
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')
        x = self.signal
        y = self.petal
        z = self.law_factor * np.ones_like(x)

        ax.scatter(x, y, z, c='mediumvioletred', alpha=0.6)
        ax.set_xlabel("Signal Trace")
        ax.set_ylabel("Petal Amplitude")
        ax.set_zlabel("Law Factor")
        ax.set_title(f"Triad Score: {self.triad_score}")
        plt.tight_layout()
        plt.show()

# Example inputs
signal_trace = np.random.normal(0.5, 0.1, 100)
petal_amplitude = np.random.normal(0.7, 0.08, 100)
law_factor = 1.15

mapper = TriadMapper(signal_trace, law_factor, petal_amplitude)
mapper.visualize()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_signal_law_petal_triad_mapper_v0.1_james_jackson')
