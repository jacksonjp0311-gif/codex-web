#!/usr/bin/env python
import json, math, datetime, pathlib, random
from urllib import request, error

# ─────────────────────────────────────────
# Paths (Codex-style)
# ─────────────────────────────────────────
root = pathlib.Path(__file__).resolve().parents[3]  # Codex Web root
module_root   = root / "codex" / "solar_resonance"
state_dir     = module_root / "state" / "v1_3"
visuals_dir   = module_root / "visuals" / "v1_3"
ledger_path   = module_root / "logs" / "ledger" / "ledger.jsonl"

state_dir.mkdir(parents=True, exist_ok=True)
visuals_dir.mkdir(parents=True, exist_ok=True)
ledger_path.parent.mkdir(parents=True, exist_ok=True)

H7 = 0.70

# ─────────────────────────────────────────
# Helper: safe fetch from SWPC (GOES flux)
# ─────────────────────────────────────────
def fetch_json(url, timeout=5.0):
    try:
        with request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def get_solar_series(N=128):
    """
    Hybrid source:
      • Try real GOES X-ray flux (1-day JSON)
      • Fall back to synthetic Gaussian flare + sinusoidal Bz
    Returns: t_idx, t_labels, flux[], bz[]
    """
    url_flux = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
    data = fetch_json(url_flux)

    if data and isinstance(data, list) and len(data) > 0:
        # Take last N samples if available
        tail = data[-N:] if len(data) >= N else data
        t_idx   = list(range(len(tail)))
        t_labels = [d.get("time_tag", "") for d in tail]
        flux = []
        for d in tail:
            try:
                flux.append(float(d.get("flux", 0.0)))
            except Exception:
                flux.append(0.0)

        # Synthetic Bz to pair with real flux
        L = len(flux)
        if L == 0:
            raise ValueError("Empty flux from SWPC")
        bz = [
            -5.0 * math.sin(2.0 * math.pi * i / float(L))
            for i in range(L)
        ]
        return t_idx, t_labels, flux, bz

    # Fallback: fully synthetic but structured
    N = N
    t_idx = list(range(N))
    t_labels = [f"t{i}" for i in t_idx]
    base   = 1e-7
    amp    = 6e-7
    center = N / 2.0
    sigma  = N / 8.0

    flux = [
        base + amp * math.exp(-((i - center) ** 2) / (2.0 * sigma * sigma))
        for i in t_idx
    ]
    bz = [
        -5.0 * math.sin(2.0 * math.pi * i / float(N))
        for i in t_idx
    ]
    return t_idx, t_labels, flux, bz

def gradient(arr):
    return [arr[i] - arr[i - 1] for i in range(1, len(arr))]

# ─────────────────────────────────────────
# Codex Solar Resonance Model v1.3
# ─────────────────────────────────────────
def compute_state():
    t_idx, t_labels, flux, bz = get_solar_series()
    N = len(flux)

    g_flux = gradient(flux)
    g_bz   = gradient(bz)

    delta_phi = (
        sum(abs(x) for x in g_flux) / float(len(g_flux) or 1)
        + sum(abs(x) for x in g_bz) / float(len(g_bz) or 1)
    )

    # Energy channel: mean flux
    E = sum(flux) / float(len(flux) or 1)

    # Information channel: std-dev of flux
    mean_flux = E
    var = sum((x - mean_flux) ** 2 for x in flux) / float(len(flux) or 1)
    I = math.sqrt(var)

    C_raw  = (E * I) / (1.0 + abs(delta_phi))
    C_norm = max(0.0, min(1.0, C_raw / H7))

    # Basic additional markers
    try:
        peak_idx = max(range(N), key=lambda i: flux[i])
        peak_time = t_labels[peak_idx] if peak_idx < len(t_labels) else ""
    except Exception:
        peak_idx  = 0
        peak_time = ""

    bz_neg_frac = 0.0
    if N > 0:
        bz_neg_frac = sum(1 for x in bz if x < 0.0) / float(N)

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "1.3",
        "timestamp": now,
        "N": N,
        "H7": H7,
        "E_sun": E,
        "I_sun": I,
        "DeltaPhi": delta_phi,
        "C_raw": C_raw,
        "C": C_norm,
        "peak_index": peak_idx,
        "peak_time": peak_time,
        "bz_negative_fraction": bz_neg_frac,
            # Source classification (v1.3.1 — fixed)
    
    }

    return state, t_idx, flux, bz, g_flux, g_bz

# ─────────────────────────────────────────
# Visuals (QIM-style hybrid)
# ─────────────────────────────────────────
def make_visuals(t_idx, flux, bz, g_flux, g_bz, ts_tag):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        # Visuals are optional; state still valid
        return []

    import numpy as np

    saved = []

    # 1) Flux + Bz line plot
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(t_idx, flux, label="GOES X-ray flux (or synthetic)")
    ax1.set_xlabel("Index")
    ax1.set_ylabel("Flux")
    ax1.grid(True, alpha=0.3)
    ax1b = ax1.twinx()
    ax1b.plot(t_idx, bz, linestyle="--", label="Bz (nT)", color="tab:red")
    ax1b.set_ylabel("Bz (nT)")
    fig1.tight_layout()
    out1 = visuals_dir / f"solar_resonance_flux_bz_v1_3_{ts_tag}.png"
    fig1.savefig(out1)
    plt.close(fig1)
    saved.append(str(out1))

    # 2) Simple gradient heatmap (|∇flux|, |∇Bz|)
    g_flux_abs = [abs(x) for x in g_flux]
    g_bz_abs   = [abs(x) for x in g_bz]
    m = max(max(g_flux_abs or [1.0]), max(g_bz_abs or [1.0]))
    if m == 0.0:
        m = 1.0
    g_flux_norm = [x / m for x in g_flux_abs]
    g_bz_norm   = [x / m for x in g_bz_abs]

    arr = np.array([g_flux_norm, g_bz_norm])

    fig2, ax2 = plt.subplots(figsize=(8, 2))
    im = ax2.imshow(arr, aspect="auto", interpolation="nearest")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["|∇flux|", "|∇Bz|"])
    ax2.set_xlabel("Index")
    fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    fig2.tight_layout()
    out2 = visuals_dir / f"solar_resonance_heatmap_v1_3_{ts_tag}.png"
    fig2.savefig(out2)
    plt.close(fig2)
    saved.append(str(out2))

    return saved

# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    state, t_idx, flux, bz, g_flux, g_bz = compute_state()

    ts_safe = (
        state["timestamp"]
        .replace(":", "")
        .replace("-", "")
        .replace(".", "")
    )

    out_path = state_dir / f"solar_resonance_state_v1_3_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    visuals = make_visuals(t_idx, flux, bz, g_flux, g_bz, ts_safe)

    ledger_entry = {
        "timestamp": state["timestamp"],
        "version": state["version"],
        "C": state["C"],
        "DeltaPhi": state["DeltaPhi"],
        "bz_negative_fraction": state.get("bz_negative_fraction", None),
        "visuals": visuals,
        "H7": H7,
        "node": "solar_resonance_v1_3"
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\n")

    print(json.dumps({
        "ok": True,
        "state_path": str(out_path),
        "visuals": visuals,
        "C": state["C"]
    }, indent=2))

if __name__ == "__main__":
    main()


