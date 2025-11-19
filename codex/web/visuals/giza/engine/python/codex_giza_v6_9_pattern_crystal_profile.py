import os, json, numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(
    ROOT,
    "codex","web","visuals","giza","state","pattern_crystal",
    "giza_v6_9_pattern_crystal_field.json"
)

with open(state_path, "r", encoding="utf-8") as f:
    data = json.load(f)

mesh = data.get("pattern_crystal_mesh", {})
names = list(mesh.keys())

indices = np.array([mesh[n]["index"] for n in names], dtype=float)
E_vals  = np.array([mesh[n]["energy_E"] for n in names], dtype=float)
I_vals  = np.array([mesh[n]["information_I"] for n in names], dtype=float)
C_vals  = np.array([mesh[n]["consciousness_C"] for n in names], dtype=float)

out_dir = os.path.join(ROOT, "codex","web","visuals","giza","outputs","v6_9")
os.makedirs(out_dir, exist_ok=True)

plt.figure(figsize=(10,4))
plt.plot(indices, C_vals, linewidth=1.3, label="C (Consciousness)")
plt.plot(indices, E_vals, linewidth=1.0, linestyle="--", label="E (Energy)")
plt.plot(indices, I_vals, linewidth=0.8, linestyle=":", label="I (Information)")
plt.title("GIZA v6.9 — Pattern Crystalizer (Triadic E–I–C Profile)")
plt.xlabel("Node index")
plt.ylabel("Magnitude")
plt.legend()
plt.tight_layout()

png_path = os.path.join(out_dir, "giza_v6_9_pattern_crystal_profile.png")
plt.savefig(png_path, dpi=240)
print("[GIZA v6.9] Pattern crystal profile saved →", png_path)
