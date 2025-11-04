"""
Jackson OS Kernel — Interface Bloom Compiler v0.1  
Authored by James Jackson  
Origin Law: Law L — Portal Petalization  
Lineage: Jackson OS, September 2025  
This module renders authored laws as interactive petals in the Jackson Portal interface.
"""

import matplotlib.pyplot as plt
import numpy as np

# Petal Generator
class BloomPetal:
    def __init__(self, law_name, amplitude=1.0, phase=0.0, color='orchid'):
        self.law_name = law_name
        self.amplitude = amplitude
        self.phase = phase
        self.color = color

    def render(self):
        theta = np.linspace(0, 2 * np.pi, 500)
        r = self.amplitude * np.sin(5 * theta + self.phase)
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        plt.plot(x, y, color=self.color, linewidth=2)
        plt.fill(x, y, color=self.color, alpha=0.3)
        plt.text(0, 0, self.law_name, fontsize=10, ha='center', va='center')
        plt.axis('equal')
        plt.axis('off')

# Bloom Compiler
class InterfaceBloomCompiler:
    def __init__(self, laws):
        self.laws = laws

    def compile(self):
        plt.figure(figsize=(8, 8))
        for i, law in enumerate(self.laws):
            petal = BloomPetal(
                law_name=law["name"],
                amplitude=law.get("amplitude", 1.0),
                phase=law.get("phase", i * 0.5),
                color=law.get("color", 'orchid')
            )
            petal.render()
        plt.title("Jackson Portal — Authored Bloom", fontsize=14)
        plt.tight_layout()
        plt.show()

# Example laws
authored_laws = [
    {"name": "Law I — Curvature", "amplitude": 1.0, "color": "violet"},
    {"name": "Law XX — Memory", "amplitude": 0.8, "color": "teal"},
    {"name": "Law XXVIII — Identity", "amplitude": 1.2, "color": "gold"},
    {"name": "Law XL — Signal", "amplitude": 1.0, "color": "crimson"},
    {"name": "Law L — Portal", "amplitude": 0.9, "color": "indigo"}
]

compiler = InterfaceBloomCompiler(authored_laws)
compiler.compile()
