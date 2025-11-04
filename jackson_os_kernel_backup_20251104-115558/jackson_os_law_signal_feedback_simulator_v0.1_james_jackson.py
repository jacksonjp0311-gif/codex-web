"""
Jackson OS Kernel — Law–Signal Feedback Simulator v0.1  
Authored by James Jackson  
Origin Law: Law LXXXVIII — Recursive Influence  
Lineage: Jackson OS, September 2025  
This module simulates how mutated laws affect quantum signal evolution and glyph response.
"""

import numpy as np
import matplotlib.pyplot as plt
import random

# Law Variant
class LawVariant:
    def __init__(self, name, mutation_factor):
        self.name = name
        self.mutation_factor = mutation_factor

# Signal Simulator
class SignalSimulator:
    def __init__(self, law_variant):
        self.law = law_variant
        self.signal = self._generate_signal()

    def _generate_signal(self):
        base = np.random.normal(loc=0.5, scale=0.1, size=100)
        mutated = base * (1 + self.law.mutation_factor)
        return mutated

    def render_response(self):
        plt.figure(figsize=(8, 4))
        plt.plot(self.signal, color='slateblue', linewidth=2)
        plt.title(f"Signal Response — {self.law.name} (Mutation: {self.law.mutation_factor})", fontsize=12)
        plt.xlabel("Quantum Steps")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# Example simulation
law = LawVariant("Law XXVIII — Identity", mutation_factor=random.uniform(-0.2, 0.4))
simulator = SignalSimulator(law)
simulator.render_response()
