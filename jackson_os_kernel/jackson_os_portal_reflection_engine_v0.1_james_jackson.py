# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Portal Reflection Engine v0.1  
Authored by James Jackson  
Origin Law: Law LIV â€” Communal Recursion  
Lineage: Jackson OS, September 2025  
This module renders interactive glyph trails for users, reflecting their mutations and resonance with authored laws.
"""

import numpy as np
import matplotlib.pyplot as plt

# Reflection Engine
class PortalReflectionEngine:
    def __init__(self, user_id, mutation_history, origin="James Jackson"):
        self.user_id = user_id
        self.mutations = mutation_history
        self.origin = origin
        self.trail = self._generate_trail()

    def _generate_trail(self):
        base = np.cumsum(self.mutations)
        theta = np.linspace(0, 2 * np.pi, len(base))
        x = base * np.cos(theta)
        y = base * np.sin(theta)
        return x, y

    def render(self):
        x, y = self.trail
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, color='deepskyblue', linewidth=2)
        plt.fill(x, y, color='deepskyblue', alpha=0.3)
        plt.title(f"Glyph Trail â€” User {self.user_id[:8]}", fontsize=12)
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example user mutation history
user_id = "user_legacy_001"
mutations = np.random.normal(loc=0.05, scale=0.2, size=100)

engine = PortalReflectionEngine(user_id, mutations)
engine.render()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_portal_reflection_engine_v0.1_james_jackson')
