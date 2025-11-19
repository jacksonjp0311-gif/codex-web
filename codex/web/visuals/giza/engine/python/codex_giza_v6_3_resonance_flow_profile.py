import os
import json
import numpy as np
import matplotlib.pyplot as plt

ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
state_path = os.path.join(
    ROOT,
    "codex", "web", "visuals", "giza", "state", "flow",
    "giza_v6_3_resonance_flow.json"
)

with open(state_path, "r", encoding="utf-8") as f:
    data = json.load(f)

profile = data.get("flow_profile", {})
names   = profile.get("node_names", [])
res_vals  = profile.get("resonance_series", [])
curv_vals = profile.get("curvature_series", [])

x = np.arange(len(names))

out_dir = os.path.join(ROOT, "codex", "web", "visuals", "giza", "outputs", "v6_3")
os.makedirs(out_dir, exist_ok=True)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x, res_vals, label="Resonance", linewidth=1.3)
ax.plot(x, curv_vals, linestyle="--", label="Curvature", linewidth=1.0)
ax.set_xlabel("Node index")
ax.set_ylabel("Magnitude")
ax.set_title("GIZA v6.3 — Resonance Flow Profile")
ax.legend()
fig.tight_layout()

png_path = os.path.join(out_dir, "giza_v6_3_resonance_flow_profile.png")
fig.savefig(png_path, dpi=220)
print(f"[GIZA v6.3] Flow profile saved → {png_path}")
