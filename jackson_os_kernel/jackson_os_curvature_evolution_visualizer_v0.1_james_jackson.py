# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Curvature Evolution Visualizer v0.1  
Authored by James Jackson  
Origin Law: Law I â€” Curvature Initialization  
Lineage: Jackson OS, September 2025  
This module animates curvature field evolution across recursive kernel cycles.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Curvature Field Generator
class CurvatureField:
    def __init__(self, shape=(64, 64), seed=0.1):
        self.shape = shape
        self.seed = seed
        self.field = np.random.normal(loc=seed, scale=0.05, size=shape)

    def evolve(self):
        noise = np.random.normal(loc=0, scale=0.01, size=self.shape)
        self.field += noise
        self.field = np.clip(self.field, 0, 1)

# Visualizer
class CurvatureVisualizer:
    def __init__(self, field, steps=100):
        self.field = field
        self.steps = steps
        self.frames = []

    def simulate(self):
        for _ in range(self.steps):
            self.field.evolve()
            self.frames.append(np.copy(self.field.field))

    def animate(self):
        fig, ax = plt.subplots()
        im = ax.imshow(self.frames[0], cmap='magma', animated=True)

        def update(frame):
            im.set_array(frame)
            return [im]

        ani = animation.FuncAnimation(fig, update, frames=self.frames, interval=50, blit=True)
        plt.title("Curvature Evolution â€” Jackson OS", fontsize=14)
        plt.tight_layout()
        plt.show()

# Execute
field = CurvatureField()
viz = CurvatureVisualizer(field)
viz.simulate()
viz.animate()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_curvature_evolution_visualizer_v0.1_james_jackson')
