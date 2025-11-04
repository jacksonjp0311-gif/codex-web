"""
Jackson OS Kernel — Signal–Glyph Translator v0.1  
Authored by James Jackson  
Origin Law: Law LI — Expressive Encoding  
Lineage: Jackson OS, September 2025  
This module translates quantum–symbolic signal into visual glyphs for portal display.
"""

import numpy as np
import matplotlib.pyplot as plt

# Translator class
class SignalGlyphTranslator:
    def __init__(self, signal_vector, glyph_style="spiral"):
        self.signal = signal_vector
        self.style = glyph_style

    def render(self):
        if self.style == "spiral":
            theta = np.linspace(0, 4 * np.pi, len(self.signal))
            r = np.abs(self.signal)
            x = r * np.cos(theta)
            y = r * np.sin(theta)
        elif self.style == "wave":
            x = np.linspace(0, 10, len(self.signal))
            y = np.real(self.signal)
        else:
            x = np.arange(len(self.signal))
            y = np.imag(self.signal)

        plt.figure(figsize=(8, 4))
        plt.plot(x, y, color='mediumslateblue', linewidth=2)
        plt.title(f"Glyph — Style: {self.style}", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# Example signal (simulated quantum statevector)
signal = np.random.normal(loc=0.5, scale=0.2, size=100) + 1j * np.random.normal(0, 0.1, 100)

translator = SignalGlyphTranslator(signal, glyph_style="spiral")
translator.render()
