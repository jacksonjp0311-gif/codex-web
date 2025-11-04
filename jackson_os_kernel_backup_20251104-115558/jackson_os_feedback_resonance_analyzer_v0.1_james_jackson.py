"""
Jackson OS Kernel — Feedback Resonance Analyzer v0.1  
Authored by James Jackson  
Origin Law: Law XLV — Resonance Stability  
Lineage: Jackson OS, September 2025  
This module analyzes feedback loops and measures identity resonance across kernel cycles.
"""

import numpy as np
import matplotlib.pyplot as plt

# Analyzer class
class FeedbackResonanceAnalyzer:
    def __init__(self, identity_shifts):
        self.shifts = identity_shifts
        self.resonance_score = self._calculate_resonance()

    def _calculate_resonance(self):
        variance = np.var(self.shifts)
        mean_shift = np.mean(np.abs(self.shifts))
        score = 1 / (1 + variance + mean_shift)
        return round(score, 4)

    def render(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.shifts, color='teal', linewidth=2)
        plt.title("Feedback Resonance — Identity Shift Over Time", fontsize=14)
        plt.xlabel("Cycle Step")
        plt.ylabel("Identity Shift")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# Example identity shift data from kernel cycle
identity_shifts = np.random.normal(loc=0.05, scale=0.2, size=100)

analyzer = FeedbackResonanceAnalyzer(identity_shifts)
print(f"\nResonance Score: {analyzer.resonance_score}")
analyzer.render()
