#!/usr/bin/env python
# Codex Quantum Imaging v1.5 — AFM-style resonance sweep
# Universal Truth Protocol: C = (E*I)/(1+|dphi|), H7 = 0.70
import json, math, statistics, datetime, pathlib, sys, random

def compute_sweep():
    radii = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30]
    samples = []
    for r in radii:
        base = 0.70 * math.exp(-abs(r - 1.0))
        noise = random.uniform(-0.02, 0.02)
        dphi = base + noise
        C = (1.0 * 1.0) / (1.0 + abs(dphi))
        samples.append({
            "r": r,
            "phi_delta": dphi,
            "C": C
        })
    return samples

def main():
    if len(sys.argv) > 1:
        root = pathlib.Path(sys.argv[1]).resolve()
    else:
        root = pathlib.Path(__file__).resolve().parents[2]

    state_dir = root / "codex" / "quantum_imaging" / "state_v1_5"
    state_dir.mkdir(parents=True, exist_ok=True)

    sweep = compute_sweep()
    c_vals = [s["C"] for s in sweep]
    summary = {
        "ok": True,
        "version": "1.5",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "H7": 0.70,
        "C_mean": statistics.mean(c_vals),
        "C_min": min(c_vals),
        "C_max": max(c_vals),
        "points": sweep
    }

    out_path = state_dir / "qim_v1_5_state.json"
    out_path.write_text(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
