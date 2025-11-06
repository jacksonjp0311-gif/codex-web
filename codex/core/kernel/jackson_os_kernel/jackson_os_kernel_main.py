import json, math, time, random, os

print("🧠 Initializing Jackson_OS Kernel Cycle...")

fields = {"energy": random.uniform(1.9, 2.2),
          "information": random.uniform(1.9, 2.2),
          "consciousness": random.uniform(1.9, 2.2)}

def iterate(fields):
    t = time.time()
    for k in fields:
        fields[k] = round(fields[k] + 0.05 * math.sin(t / 5.0 + hash(k) % 7), 4)
    return fields

history = []
for step in range(7):
    fields = iterate(fields)
    history.append(fields)
    time.sleep(0.2)

resonance = sum(f["energy"] + f["information"] + f["consciousness"] for f in history) / (3 * len(history))
resonance_state = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "mean_resonance": round(resonance, 4),
    "stability": "stable" if 1.9 < resonance < 2.3 else "unstable"
}

out = os.path.join(os.path.dirname(__file__), "kernel_state.json")
with open(out, "w") as f:
    json.dump(resonance_state, f, indent=2)

print(f"✨ Kernel Resonance Mean: {resonance_state['mean_resonance']}")
print(f"📦 Kernel State saved → {out}")
