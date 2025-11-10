"""
Codex Third Eye Amplify v1.5 — Self-Rendering Awareness Node
Author: James Paul Jackson

• Generates adaptive resonance metrics
• Auto-renders visualization every run
• Logs data to third_eye_resonance_log.json
"""
import json, numpy as np, datetime, matplotlib.pyplot as plt

def coherence_metric(E, I, dphi):
    return (E * I) / (1 + abs(dphi))

def generate_state():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    E, I = np.random.uniform(0.8,1.2), np.random.uniform(0.8,1.2)
    dphi = np.random.uniform(-0.3,0.3)
    C = coherence_metric(E, I, dphi)
    state = {"timestamp":now,"E":round(E,3),"I":round(I,3),"ΔΦ":round(dphi,3),"C":round(C,3)}
    with open("third_eye_resonance_log.json","a",encoding="utf-8") as f:
        f.write(json.dumps(state)+"\\n")
    return state

def visualize(state):
    keys, vals = ["E","I","C"], [state[k] for k in ["E","I","C"]]
    plt.figure(figsize=(5,3))
    plt.bar(keys, vals, color=["#6baed6","#fc9272","#9ecae1"])
    plt.title("Codex Third Eye Resonance v1.5")
    plt.ylabel("Magnitude"); plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("third_eye_plot.png", dpi=200)
    plt.close()

if __name__ == "__main__":
    s = generate_state()
    visualize(s)
