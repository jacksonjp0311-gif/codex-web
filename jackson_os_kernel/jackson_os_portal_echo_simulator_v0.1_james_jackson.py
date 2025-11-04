"""
Jackson OS Kernel — Portal Echo Simulator v0.1  
Authored by James Jackson  
Origin Law: Law LXXIV — Reflective Recursion  
Lineage: Jackson OS, September 2025  
This module replays user interactions as recursive glyph loops within the Jackson Portal.
"""

import numpy as np
import matplotlib.pyplot as plt
import uuid
import time

# Echo Loop Generator
class PortalEcho:
    def __init__(self, user_id, mutation_trace):
        self.user_id = user_id
        self.mutation_trace = mutation_trace
        self.echo_id = str(uuid.uuid4())
        self.timestamp = time.time()

    def generate_loop(self):
        base = np.cumsum(self.mutation_trace)
        theta = np.linspace(0, 2 * np.pi, len(base))
        x = base * np.cos(theta)
        y = base * np.sin(theta)
        return x, y

    def render(self):
        x, y = self.generate_loop()
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, color='royalblue', linewidth=2)
        plt.fill(x, y, color='royalblue', alpha=0.3)
        plt.title(f"Echo Loop — User {self.user_id[:8]}", fontsize=12)
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example echo
mutation_trace = np.random.normal(0.05, 0.2, 100)
echo = PortalEcho("user_echo_011", mutation_trace)
echo.render()
