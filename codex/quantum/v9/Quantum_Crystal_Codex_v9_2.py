#!/usr/bin/env python
# Codex Quantum Crystal v9.2 — lattice coherence sample
import json, math, random, datetime, pathlib, sys

def sample_coherence(n=64):
    phases = [random.uniform(0.0, 2.0 * math.pi) for _ in range(n)]
    re = sum(math.cos(th) for th in phases) / n
    im = sum(math.sin(th) for th in phases) / n
    C = (re**2 + im**2) ** 0.5
    dphi = abs(C - 0.70)
    return C, dphi

def main():
    if len(sys.argv) > 1:
        root = pathlib.Path(sys.argv[1]).resolve()
    else:
        root = pathlib.Path(__file__).resolve().parents[3]

    state_dir = root / "codex" / "quantum" / "v9" / "state_v9_2"
    state_dir.mkdir(parents=True, exist_ok=True)

    C, dphi = sample_coherence()
    payload = {
        "ok": True,
        "version": "9.2",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "N": 64,
        "C": C,
        "H7": 0.70,
        "delta_phi": dphi
    }
    out_path = state_dir / "qcx_v9_2_state.json"
    out_path.write_text(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
