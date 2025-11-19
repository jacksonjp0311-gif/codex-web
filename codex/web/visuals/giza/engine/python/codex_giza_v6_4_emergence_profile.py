import os, json, numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(ROOT,
    "codex","web","visuals","giza","state","emergence",
    "giza_v6_4_emergence_field.json"
)

with open(state_path,"r",encoding="utf-8") as f:
    data = json.load(f)

mesh = data["emergence_mesh"]
names = list(mesh.keys())
em_vals = np.array([mesh[n]["emergence"] for n in names])

x = np.arange(len(names))

out_dir = os.path.join(ROOT,"codex","web","visuals","giza","outputs","v6_4")
os.makedirs(out_dir,exist_ok=True)

plt.figure(figsize=(10,4))
plt.plot(x,em_vals,linewidth=1.3)
plt.title("GIZA v6.4 — Holographic Emergence Profile")
plt.xlabel("Node Index")
plt.ylabel("Emergence Magnitude")
plt.tight_layout()

png_path = os.path.join(out_dir,"giza_v6_4_emergence_profile.png")
plt.savefig(png_path,dpi=240)
print("[GIZA v6.4] Emergence profile saved →",png_path)
