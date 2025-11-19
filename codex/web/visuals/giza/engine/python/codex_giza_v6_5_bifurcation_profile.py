import os, json, numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(
    ROOT,
    "codex","web","visuals","giza","state","bifurcation",
    "giza_v6_5_bifurcation_field.json"
)

with open(state_path,"r",encoding="utf-8") as f:
    data = json.load(f)

mesh = data.get("bifurcation_mesh", {})
names = list(mesh.keys())
plus_vals  = np.array([mesh[n]["plus_channel"] for n in names], dtype=float)
minus_vals = np.array([mesh[n]["minus_channel"] for n in names], dtype=float)

x = np.arange(len(names))

out_dir = os.path.join(ROOT,"codex","web","visuals","giza","outputs","v6_5")
os.makedirs(out_dir,exist_ok=True)

plt.figure(figsize=(10,4))
plt.plot(x, plus_vals,  linewidth=1.2, label="Plus channel")
plt.plot(x, minus_vals, linewidth=1.0, linestyle="--", label="Minus channel")
plt.title("GIZA v6.5 — Bifurcation Profile")
plt.xlabel("Node Index")
plt.ylabel("Channel Magnitude")
plt.legend()
plt.tight_layout()

png_path = os.path.join(out_dir,"giza_v6_5_bifurcation_profile.png")
plt.savefig(png_path,dpi=240)
print("[GIZA v6.5] Bifurcation profile saved →",png_path)
