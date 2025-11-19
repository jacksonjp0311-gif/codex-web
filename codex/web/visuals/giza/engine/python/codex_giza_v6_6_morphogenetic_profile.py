import os, json, numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(
    ROOT,
    "codex","web","visuals","giza","state","morphogenesis",
    "giza_v6_6_morphogenetic_field.json"
)

with open(state_path, "r", encoding="utf-8") as f:
    data = json.load(f)

mesh = data.get("morphogenetic_mesh", {})
names = list(mesh.keys())

growth_vals = np.array([mesh[n]["growth_value"] for n in names], dtype=float)
sym_vals    = np.array([mesh[n]["branch_symmetry"] for n in names], dtype=float)

x = np.arange(len(names))

out_dir = os.path.join(ROOT, "codex","web","visuals","giza","outputs","v6_6")
os.makedirs(out_dir, exist_ok=True)

plt.figure(figsize=(10,4))
plt.plot(x, growth_vals, linewidth=1.3, label="Growth value")
plt.plot(x, sym_vals,   linewidth=1.0, linestyle="--", label="Branch symmetry")
plt.title("GIZA v6.6 — Morphogenetic Expansion Profile (Adaptive Growth)")
plt.xlabel("Node Index")
plt.ylabel("Magnitude")
plt.legend()
plt.tight_layout()

png_path = os.path.join(out_dir, "giza_v6_6_morphogenetic_profile.png")
plt.savefig(png_path, dpi=240)
print("[GIZA v6.6] Morphogenetic profile saved →", png_path)
