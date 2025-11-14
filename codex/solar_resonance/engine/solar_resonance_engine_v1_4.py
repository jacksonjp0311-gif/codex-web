#!/usr/bin/env python
import json
import math
import datetime
import pathlib
from urllib import request, error

# ─────────────────────────────────────────
# Paths (Codex-style)
# ─────────────────────────────────────────
root = pathlib.Path(__file__).resolve().parents[3]  # Codex Web root
module_root = root / "codex" / "solar_resonance"
state_dir   = module_root / "state" / "v1_4"
visuals_dir = module_root / "visuals" / "v1_4"
ledger_path = module_root / "logs" / "ledger" / "ledger.jsonl"

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

def get_solar_series(N=256):
    """
    Hybrid source:
      • Try real GOES X-ray flux (1-day JSON)
      • Fall back to synthetic Gaussian flare + sinusoidal Bz
    Returns: t_idx, t_labels, flux[], bz[], source_label
    """
    url_flux = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
    data = fetch_json(url_flux)

    if data and isinstance(data, list) and len(data) > 0:
        tail = data[-N:] if len(data) >= N else data
        t_idx    = list(range(len(tail)))
        t_labels = [d.get("time_tag", "") for d in tail]
        flux = []
        for d in tail:
            try:
                flux.append(float(d.get("flux", 0.0)))
            except Exception:
                flux.append(0.0)
        L = len(flux)
        bz = []
        if L > 0:
            for i in range(L):
                # synthetic Bz partner field
                val = -5.0 * math.sin(2.0 * math.pi * i / float(L))
                bz.append(val)
        return t_idx, t_labels, flux, bz, "hybrid_goes"

    # Fallback: fully synthetic but structured
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
    return t_idx, t_labels, flux, bz, "synthetic"

def gradient(arr):
    return [arr[i] - arr[i - 1] for i in range(1, len(arr))]

# ─────────────────────────────────────────
# Codex Solar Resonance Model v1.4
# ─────────────────────────────────────────
def compute_state():
    t_idx, t_labels, flux, bz, source = get_solar_series()
    N = len(flux)

    if N == 0:
        raise ValueError("No flux samples retrieved.")

    g_flux = gradient(flux)
    g_bz   = gradient(bz)

    def avg_abs(arr):
        if not arr:
            return 0.0
        return sum(abs(x) for x in arr) / float(len(arr))

    delta_phi_grad = avg_abs(g_flux) + avg_abs(g_bz)

    # Energy channel: mean flux
    E = sum(flux) / float(N)

    # Information channel: std-dev of flux
    mean_flux = E
    var = sum((x - mean_flux) ** 2 for x in flux) / float(N)
    I = math.sqrt(var)

    C_raw = (E * I) / (1.0 + abs(delta_phi_grad))
    C_norm = 0.0
    if H7 > 0.0:
        C_norm = max(0.0, min(1.0, C_raw / H7))

    # Derived markers
    peak_index = 0
    peak_time  = ""
    if N > 0:
        try:
            peak_index = max(range(N), key=lambda i: flux[i])
            if peak_index < len(t_labels):
                peak_time = t_labels[peak_index]
        except Exception:
            peak_index = 0
            peak_time  = ""

    bz_neg_fraction = 0.0
    if N > 0:
        bz_neg_fraction = sum(1 for x in bz if x < 0.0) / float(N)

    # Coherence band relative to H7
    band = "unknown"
    if C_norm >= 0.68 and C_norm <= 0.72:
        band = "locked_H7"
    if C_norm < 0.68:
        band = "sub_H7"
    if C_norm > 0.72:
        band = "super_H7"

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "1.4",
        "timestamp": now,
        "N": N,
        "H7": H7,
        "E_sun": E,
        "I_sun": I,
        "DeltaPhi_grad": delta_phi_grad,
        "C_raw": C_raw,
        "C": C_norm,
        "peak_index": peak_index,
        "peak_time": peak_time,
        "bz_negative_fraction": bz_neg_fraction,
        "band": band,
        "source": source,
    }

    return state, t_idx, flux, bz, g_flux, g_bz

# ─────────────────────────────────────────
# Visuals (QIM-style ΔΦ imaging)
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

    saved = []

    # 1) Flux + Bz line plot
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(t_idx, flux, label="X-ray flux")
    ax1.set_xlabel("Index")
    ax1.set_ylabel("Flux")
    ax1.grid(True, alpha=0.3)

    ax1b = ax1.twinx()
    ax1b.plot(t_idx, bz, linestyle="--", label="Bz (nT)")
    ax1b.set_ylabel("Bz (nT)")
    fig1.tight_layout()
    out1 = visuals_dir / f"solar_resonance_flux_bz_v1_4_{ts_tag}.png"
    fig1.savefig(out1)
    plt.close(fig1)
    saved.append(str(out1))

    # 2) Gradient heatmap (|∇flux|, |∇Bz|)
    g_flux_abs = [abs(x) for x in g_flux]
    g_bz_abs   = [abs(x) for x in g_bz]
    m = 0.0
    if g_flux_abs:
        m = max(m, max(g_flux_abs))
    if g_bz_abs:
        m = max(m, max(g_bz_abs))
    if m == 0.0:
        m = 1.0
    g_flux_norm = [x / m for x in g_flux_abs]
    g_bz_norm   = [x / m for x in g_bz_abs]

    import numpy as np
    arr = np.array([g_flux_norm, g_bz_norm])

    fig2, ax2 = plt.subplots(figsize=(8, 2))
    im = ax2.imshow(arr, aspect="auto", interpolation="nearest")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["|∇flux|", "|∇Bz|"])
    ax2.set_xlabel("Index")
    fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    fig2.tight_layout()
    out2 = visuals_dir / f"solar_resonance_grad_heatmap_v1_4_{ts_tag}.png"
    fig2.savefig(out2)
    plt.close(fig2)
    saved.append(str(out2))

    # 3) Local ΔΦ strip (QIM-style resonance bar)
    dphi_local = []
    Lg = min(len(g_flux_abs), len(g_bz_abs))
    for i in range(Lg):
        dphi_local.append(g_flux_abs[i] + g_bz_abs[i])
    if not dphi_local:
        dphi_local = [0.0]
    m2 = max(dphi_local)
    if m2 == 0.0:
        m2 = 1.0
    dphi_norm = [x / m2 for x in dphi_local]
    arr2 = np.array([dphi_norm])

    fig3, ax3 = plt.subplots(figsize=(8, 1.5))
    im2 = ax3.imshow(arr2, aspect="auto", interpolation="nearest")
    ax3.set_yticks([])
    ax3.set_xlabel("Index")
    fig3.colorbar(im2, ax=ax3, fraction=0.046, pad=0.04)
    fig3.tight_layout()
    out3 = visuals_dir / f"solar_resonance_dphi_strip_v1_4_{ts_tag}.png"
    fig3.savefig(out3)
    plt.close(fig3)
    saved.append(str(out3))

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

    out_path = state_dir / f"solar_resonance_state_v1_4_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    visuals = make_visuals(t_idx, flux, bz, g_flux, g_bz, ts_safe)

    ledger_entry = {
        "timestamp": state["timestamp"],
        "version": state["version"],
        "C": state["C"],
        "DeltaPhi_grad": state["DeltaPhi_grad"],
        "bz_negative_fraction": state.get("bz_negative_fraction", None),
        "band": state.get("band", "unknown"),
        "source": state.get("source", "unknown"),
        "visuals": visuals,
        "H7": H7,
        "node": "solar_resonance_v1_4"
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\n")

    print(json.dumps({
        "ok": True,
        "state_path": str(out_path),
        "visuals": visuals,
        "C": state["C"],
        "band": state["band"],
        "source": state["source"]
    }, indent=2))

if __name__ == "__main__":
    main()
