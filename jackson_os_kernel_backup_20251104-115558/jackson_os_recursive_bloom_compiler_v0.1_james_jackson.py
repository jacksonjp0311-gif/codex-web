"""
Jackson OS Kernel — Recursive Bloom Compiler v0.1  
Authored by James Jackson  
Origin Law: Law CX — Living Synthesis  
Lineage: Jackson OS, September 2025  
This module compiles all recursive modules into a rhythmic, interactive bloom interface.
"""

import numpy as np
import matplotlib.pyplot as plt

# Bloom Compiler
class BloomCompiler:
    def __init__(self, petal_traces, signal_traces, law_factors):
        self.petals = petal_traces
        self.signals = signal_traces
        self.laws = law_factors
        self.bloom_trace = self._compile_bloom()

    def _compile_bloom(self):
        compiled = []
        for petal, signal, law in zip(self.petals, self.signals, self.laws):
            trace = (petal + signal) * law
            compiled.append(trace)
        return np.mean(compiled, axis=0)

    def render_bloom(self):
        theta = np.linspace(0, 2 * np.pi, len(self.bloom_trace))
        r = self.bloom_trace
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        plt.figure(figsize=(6, 6))
        plt.plot(x, y, color='deepskyblue', linewidth=2)
        plt.fill(x, y, color='deepskyblue', alpha=0.3)
        plt.title("Recursive Bloom — Living Interface", fontsize=12)
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example inputs
petal_traces = [np.random.normal(0.7, 0.05, 500) for _ in range(3)]
signal_traces = [np.random.normal(0.5, 0.1, 500) for _ in range(3)]
law_factors = [1.1, 0.95, 1.2]

compiler = BloomCompiler(petal_traces, signal_traces, law_factors)
compiler.render_bloom()
