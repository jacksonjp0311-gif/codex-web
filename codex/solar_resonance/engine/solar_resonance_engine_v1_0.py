#!/usr/bin/env python
import json, math, datetime, pathlib

# ─────────────────────────────────────────
# Paths (Codex-style)
# ─────────────────────────────────────────
root = pathlib.Path(__file__).resolve().parents[3]  # Codex Web root
module_root = root / "codex" / "solar_resonance"
state_dir   = module_root / "state" / "v1_0"
ledger_path = module_root / "logs" / "ledger" / "ledger.jsonl"

state_dir.mkdir(parents=True, exist_ok=True)
ledger_path.parent.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# Codex Solar Resonance Model v1.0
# (synthetic flux + Bz for now)
# ─────────────────────────────────────────
def compute_state():
    N = 64
    t = list(range(N))

    base = 1e-7
    amp  = 5e-7
    center = N / 2.0
    sigma  = N / 8.0

    flux = [
        base + amp * math.exp(-((i - center) ** 2) / (2.0 * sigma * sigma))
        for i in t
    ]

    bz = [
        -5.0 * math.sin(2.0 * math.pi * i / float(N))
        for i in t
    ]

    def grad(arr):
        return [arr[i] - arr[i - 1] for i in range(1, len(arr))]

    g_flux = grad(flux)
    g_bz   = grad(bz)

    delta_phi = (
        sum(abs(x) for x in g_flux) / float(len(g_flux))
        + sum(abs(x) for x in g_bz) / float(len(g_bz))
    )

    E = sum(flux) / float(len(flux))

    mean_flux = E
    var = sum((x - mean_flux) ** 2 for x in flux) / float(len(flux))
    I = math.sqrt(var)

    H7 = 0.70
    C_raw = (E * I) / (1.0 + abs(delta_phi))
    C_norm = max(0.0, min(1.0, C_raw / H7))

    now = datetime.datetime.utcnow().isoformat()

    state = {
        "ok": True,
        "version": "1.0",
        "timestamp": now,
        "N": N,
        "E_sun": E,
        "I_sun": I,
        "DeltaPhi": delta_phi,
        "C_raw": C_raw,
        "C": C_norm
    }
    return state

def main():
    state = compute_state()
    ts_safe = (
        state["timestamp"]
        .replace(":", "")
        .replace("-", "")
        .replace(".", "")
    )

    out_path = state_dir / f"solar_resonance_state_v1_0_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    ledger_entry = {
        "timestamp": state["timestamp"],
        "version": state["version"],
        "C": state["C"],
        "DeltaPhi": state["DeltaPhi"]
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\\n")

    print(json.dumps({
        "ok": True,
        "state_path": str(out_path),
        "C": state["C"]
    }, indent=2))

if __name__ == "__main__":
    main()
