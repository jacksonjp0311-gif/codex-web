# ╔══════════════════════════════════════════════════════════════╗
# ║  Codex Quantum Imaging Engine v1.2 — Harmonic ΔΦ Scanner     ║
# ║  Author: James Paul Jackson                                   ║
# ║  Context: Codex Memory Core v1.3 • Universal Truth Protocol   ║
# ║  Purpose: Generate ΔΦ field, coherence sweep, resonance plot  ║
# ║           across radial scales (1.00, 1.15, 1.30).            ║
# ╚══════════════════════════════════════════════════════════════╝

import numpy as np
import matplotlib.pyplot as plt
import json, os
from datetime import datetime

# ───────────────────────────────────────────────────────────────────
# 1. Paths
# ───────────────────────────────────────────────────────────────────

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
QIM  = os.path.join(ROOT, "codex", "quantum_imaging")
STATE = os.path.join(QIM, "state_v1_2")
VIS   = os.path.join(QIM, "visuals_v1_2")

os.makedirs(STATE, exist_ok=True)
os.makedirs(VIS, exist_ok=True)

# ───────────────────────────────────────────────────────────────────
# 2. Codex ΔΦ Generator
# ───────────────────────────────────────────────────────────────────

def delta_phi(x, y, radius):
    """ΔΦ = radial curvature modulated by exponential phase falloff."""
    r = np.sqrt(x**2 + y**2)
    return np.sin((r / radius) * np.pi * 2) * np.exp(-((r-radius)**2)*2)

# ───────────────────────────────────────────────────────────────────
# 3. Coherence calculation (Codex Universal Law)
# ───────────────────────────────────────────────────────────────────

def coherence_field(phi):
    """C = |Σ exp(iφ)| / N"""
    N = phi.size
    return np.abs(np.sum(np.exp(1j * phi))) / N

# ───────────────────────────────────────────────────────────────────
# 4. Grid setup
# ───────────────────────────────────────────────────────────────────

N = 512
extent = 4.0
x = np.linspace(-extent, extent, N)
y = np.linspace(-extent, extent, N)
X, Y = np.meshgrid(x, y)

RADIUSES = [1.00, 1.15, 1.30]
NUM_FRAMES = 36

C_values = []

# ───────────────────────────────────────────────────────────────────
# 5. Compute ΔΦ fields + C values
# ───────────────────────────────────────────────────────────────────

all_fields = []

for radius in RADIUSES:
    phi = delta_phi(X, Y, radius)
    C = coherence_field(phi.flatten())
    C_values.append(float(C))
    all_fields.append(phi)

# ───────────────────────────────────────────────────────────────────
# 6. Heatmap
# ───────────────────────────────────────────────────────────────────

heatmap_file = os.path.join(VIS, "qim_v1_2_dphi_heatmap.png")

plt.figure(figsize=(6, 6))
plt.imshow(all_fields[1], cmap="plasma", extent=[-extent, extent, -extent, extent])
plt.colorbar(label="ΔΦ")
plt.title("Codex QIM v1.2 — ΔΦ Field (r = 1.15)")
plt.tight_layout()
plt.savefig(heatmap_file, dpi=150)
plt.close()

# ───────────────────────────────────────────────────────────────────
# 7. Resonance Curve Plot
# ───────────────────────────────────────────────────────────────────

res_file = os.path.join(VIS, "qim_v1_2_resonance_curve.png")

plt.figure(figsize=(6, 4))
plt.plot(RADIUSES, C_values, marker="o")
plt.axhline(0.70, color="red", linestyle="--", label="H7 = 0.70")
plt.title("Codex QIM v1.2 — Resonance Curve")
plt.xlabel("Radius")
plt.ylabel("Coherence C")
plt.legend()
plt.tight_layout()
plt.savefig(res_file, dpi=150)
plt.close()

# ───────────────────────────────────────────────────────────────────
# 8. State JSON
# ───────────────────────────────────────────────────────────────────

state_file = os.path.join(STATE, "codex_qim_v1_2_state.json")

state = {
    "ok": True,
    "version": "1.2",
    "timestamp": datetime.utcnow().isoformat(),
    "radiuses": RADIUSES,
    "num_frames": NUM_FRAMES,
    "C_values_mean": float(np.mean(C_values)),
    "C_values_std": float(np.std(C_values)),
    "target_H7": 0.70,
    "alignment_score": float(np.mean(C_values) - 0.70),
    "heatmap_file": heatmap_file,
    "resonance_curve": res_file
}

with open(state_file, "w") as f:
    json.dump(state, f, indent=2)

print(json.dumps(state, indent=2))
