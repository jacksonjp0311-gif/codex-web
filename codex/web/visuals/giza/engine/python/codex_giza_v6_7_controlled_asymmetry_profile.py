import os, json, numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(
    ROOT,
    "codex","web","visuals","giza","state","asymmetry",
    "giza_v6_7_controlled_asymmetry_field.json"
)

with open(state_path, "r", encoding="utf-8") as f:
    data = json.load(f)

mesh = data.get("controlled_asymmetry_mesh", {})
names = list(mesh.keys())

asym_vals   = np.array([mesh[n]["asym_value"] for n in names], dtype=float)
asym_delta  = np.array([mesh[n]["asym_delta"] for n in names], dtype=float)
sym_vals    = np.array([mesh[n]["branch_symmetry"] for n in names], dtype=float)

x = np.arange(len(names))

out_dir = os.path.join(ROOT, "codex","web","visuals","giza","outputs","v6_7")
os.makedirs(out_dir, exist_ok=True)

plt.figure(figsize=(10,4))
plt.plot(x, asym_vals,  linewidth=1.3, label="Asym value")
plt.plot(x, asym_delta, linewidth=1.0, linestyle="--", label="Asym Δ (tiny)")
plt.plot(x, sym_vals,   linewidth=0.8, linestyle=":", label="Branch symmetry")
plt.title("GIZA v6.7 — Controlled Asymmetry Profile (ε = 1e-7)")
plt.xlabel("Node Index")
plt.ylabel("Magnitude")
plt.legend()
plt.tight_layout()

png_path = os.path.join(out_dir, "giza_v6_7_controlled_asymmetry_profile.png")
plt.savefig(png_path, dpi=240)
print("[GIZA v6.7] Controlled asymmetry profile saved →", png_path)
