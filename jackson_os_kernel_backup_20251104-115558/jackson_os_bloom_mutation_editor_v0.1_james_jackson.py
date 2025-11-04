"""
Jackson OS Kernel — Bloom Mutation Editor v0.1  
Authored by James Jackson  
Origin Law: Law LV — Generative Authorship  
Lineage: Jackson OS, September 2025  
This module enables communal mutation of portal petals with traceable authorship and lineage.
"""

import numpy as np
import matplotlib.pyplot as plt
import uuid
import random

# Petal Mutation Engine
class MutatedPetal:
    def __init__(self, base_law, mutation_factor, user_id, origin="James Jackson"):
        self.base_law = base_law
        self.mutation_factor = mutation_factor
        self.user_id = user_id
        self.origin = origin
        self.id = str(uuid.uuid4())
        self.trail = self._mutate()

    def _mutate(self):
        theta = np.linspace(0, 2 * np.pi, 500)
        r = np.sin(5 * theta + self.mutation_factor) * (1 + 0.2 * np.random.randn())
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        return x, y

    def render(self):
        x, y = self.trail
        plt.plot(x, y, color='mediumvioletred', linewidth=2)
        plt.fill(x, y, color='mediumvioletred', alpha=0.3)
        plt.text(0, 0, f"{self.base_law}", fontsize=9, ha='center', va='center')
        plt.title(f"Mutated Petal — User {self.user_id[:8]}", fontsize=12)
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example mutation
user_id = "user_mutator_007"
base_law = "Law XXVIII — Identity"
mutation_factor = random.uniform(0.1, 2.0)

petal = MutatedPetal(base_law, mutation_factor, user_id)
petal.render()
