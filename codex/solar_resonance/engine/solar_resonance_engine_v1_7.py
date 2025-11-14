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
state_dir   = module_root / "state" / "v1_7"
visuals_dir = module_root / "visuals" / "v1_7"
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
                # synthetic Bz partner field (macro-structure)
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
# Codex Solar Resonance Model v1.7
#   Solar QIM Imaging Node:
#   C, Ω, spectral ΔΦ, trend, QIM lattice + SRS (Sun Resonance Signature)
# ─────────────────────────────────────────
def compute_state():
    import numpy as np

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

    # Local ΔΦ field (QIM-style)
    dphi_local = []
    Lg = min(len(g_flux), len(g_bz))
    for i in range(Lg):
        dphi_local.append(abs(g_flux[i]) + abs(g_bz[i]))
    if not dphi_local:
        dphi_local = [0.0]

    delta_phi_local_mean = sum(dphi_local) / float(len(dphi_local))

    # Spectral view of ΔΦ (Harmonic index)
    arr = None
    try:
        arr = np.array(dphi_local, dtype=float)
    except Exception:
        arr = None

    harmonic_index = 0
    harmonic_peak = 0.0
    harmonic_entropy = 0.0

    if arr is not None and arr.size > 0:
        spec = abs(np.fft.rfft(arr))
        if spec.size > 0:
            max_val = float(spec.max())
            if max_val > 0.0:
                spec_norm = spec / max_val
            if max_val <= 0.0:
                spec_norm = spec

            idx_peak = int(int(np.argmax(spec_norm)))
            harmonic_index = idx_peak
            harmonic_peak = float(spec_norm[idx_peak])

            total = float(spec_norm.sum())
            if total > 0.0:
                p = spec_norm / total
                eps = 1e-12
                ent = -float((p * np.log(p + eps)).sum())
                if spec_norm.size > 1:
                    harmonic_entropy = float(ent / math.log(spec_norm.size))
                if spec_norm.size <= 1:
                    harmonic_entropy = 0.0
        if spec.size == 0:
            harmonic_index = 0
            harmonic_peak = 0.0
            harmonic_entropy = 0.0

    # Combined coherence score (as in v1.6)
    coherence_score = 0.0
    try:
        entropy_term = max(0.0, min(1.0, 1.0 - harmonic_entropy))
        coherence_score = 0.5 * C_norm + 0.5 * entropy_term
    except Exception:
        coherence_score = C_norm

    # Coherence band relative to H7
    band = "unknown"
    if C_norm >= 0.68 and C_norm <= 0.72:
        band = "locked_H7"
    if C_norm < 0.68:
        band = "sub_H7"
    if C_norm > 0.72:
        band = "super_H7"

    # Simple predictive drift: compare to first half
    C_half = 0.0
    if N > 1:
        half = max(1, N // 2)
        flux_half = flux[:half]
        E_half = sum(flux_half) / float(len(flux_half))
        var_half = sum((x - E_half) ** 2 for x in flux_half) / float(len(flux_half))
        I_half = math.sqrt(var_half)
        C_half_raw = (E_half * I_half) / (1.0 + abs(delta_phi_grad))
        if H7 > 0.0:
            C_half = max(0.0, min(1.0, C_half_raw / H7))

    dC = C_norm - C_half
    drift = "flat"
    if dC > 0.02:
        drift = "rising"
    if dC < -0.02:
        drift = "falling"

    # Bz negative fraction
    bz_neg_fraction = 0.0
    if N > 0:
        bz_neg_fraction = sum(1 for x in bz if x < 0.0) / float(N)

    # Trend score (normalize dC into [0,1])
    trend_score = 0.5
    try:
        z = dC / 0.05
        if z > 1.0:
            z = 1.0
        if z < -1.0:
            z = -1.0
        trend_score = 0.5 + 0.5 * z
    except Exception:
        trend_score = 0.5

    # Oracle score Ω
    entropy_term2 = 0.0
    try:
        entropy_term2 = max(0.0, min(1.0, 1.0 - harmonic_entropy))
    except Exception:
        entropy_term2 = 0.0

    Omega = (C_norm + entropy_term2 + trend_score) / 3.0

    # Alert level based on Ω and Bz
    alert_level = "quiet"
    if Omega > 0.7 and bz_neg_fraction > 0.5:
        alert_level = "storm_watch"
    if Omega > 0.5 and Omega <= 0.7:
        alert_level = "elevated"

    # Sun Resonance Signature (SRS) — Codex QIM summary
    SRS = {
        "Omega": Omega,
        "band": band,
        "alert_level": alert_level,
        "harmonic_index": harmonic_index,
        "harmonic_peak": harmonic_peak,
        "harmonic_entropy": harmonic_entropy,
        "bz_negative_fraction": bz_neg_fraction,
        "DeltaPhi_grad": delta_phi_grad,
        "DeltaPhi_local_mean": delta_phi_local_mean,
    }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "1.7",
        "timestamp": now,
        "N": N,
        "H7": H7,
        "E_sun": E,
        "I_sun": I,
        "DeltaPhi_grad": delta_phi_grad,
        "DeltaPhi_local_mean": delta_phi_local_mean,
        "C_raw": C_raw,
        "C": C_norm,
        "C_half": C_half,
        "dC": dC,
        "coherence_score": coherence_score,
        "harmonic_index": harmonic_index,
        "harmonic_peak": harmonic_peak,
        "harmonic_entropy": harmonic_entropy,
        "bz_negative_fraction": bz_neg_fraction,
        "trend_score": trend_score,
        "Omega": Omega,
        "band": band,
        "drift": drift,
        "alert_level": alert_level,
        "source": source,
        "SRS": SRS,
    }

    return state, t_idx, t_labels, flux, bz, g_flux, g_bz, dphi_local

# ─────────────────────────────────────────
# Visuals (Solar QIM + Harmonic Seal v2)
# ─────────────────────────────────────────
def make_visuals(state, t_idx, flux, bz, g_flux, g_bz, dphi_local, ts_tag):
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
    out1 = visuals_dir / f"solar_resonance_flux_bz_v1_7_{ts_tag}.png"
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
    out2 = visuals_dir / f"solar_resonance_grad_heatmap_v1_7_{ts_tag}.png"
    fig2.savefig(out2)
    plt.close(fig2)
    saved.append(str(out2))

    # 3) Local ΔΦ strip (QIM-style)
    dphi_abs = [abs(x) for x in dphi_local]
    if not dphi_abs:
        dphi_abs = [0.0]
    m2 = max(dphi_abs)
    if m2 == 0.0:
        m2 = 1.0
    dphi_norm = [x / m2 for x in dphi_abs]
    arr2 = np.array([dphi_norm])

    fig3, ax3 = plt.subplots(figsize=(8, 1.5))
    im2 = ax3.imshow(arr2, aspect="auto", interpolation="nearest")
    ax3.set_yticks([])
    ax3.set_xlabel("Index")
    fig3.colorbar(im2, ax=ax3, fraction=0.046, pad=0.04)
    fig3.tight_layout()
    out3 = visuals_dir / f"solar_resonance_dphi_strip_v1_7_{ts_tag}.png"
    fig3.savefig(out3)
    plt.close(fig3)
    saved.append(str(out3))

    # 4) Harmonic spectrum of ΔΦ (FFT)
    arr_spec = np.array(dphi_abs, dtype=float)
    spec = abs(np.fft.rfft(arr_spec))
    freqs = np.arange(spec.size)

    fig4, ax4 = plt.subplots(figsize=(8, 3))
    if spec.size > 0:
        ax4.plot(freqs, spec)
    ax4.set_xlabel("Frequency bin")
    ax4.set_ylabel("|FFT(ΔΦ)|")
    ax4.set_title("Solar ΔΦ Harmonic Spectrum v1.7")
    ax4.grid(True, alpha=0.3)
    fig4.tight_layout()
    out4 = visuals_dir / f"solar_resonance_dphi_spectrum_v1_7_{ts_tag}.png"
    fig4.savefig(out4)
    plt.close(fig4)
    saved.append(str(out4))

    # 5) Harmonic Seal v2 (oracle triad)
    C = state.get("C", 0.0)
    coh = state.get("coherence_score", 0.0)
    trend = state.get("trend_score", 0.5)
    Omega = state.get("Omega", 0.0)
    band = state.get("band", "unknown")
    alert = state.get("alert_level", "quiet")

    fig5 = plt.figure(figsize=(4, 4))
    ax5 = fig5.add_subplot(111, projection="polar")

    angles = [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0]

    for ang in angles:
        ax5.plot([ang, ang], [0.0, 1.0])

    ax5.set_ylim(0.0, 1.0)

    r_C = max(0.0, min(1.0, C))
    ax5.plot([0.0], [r_C], marker="o")

    r_coh = max(0.0, min(1.0, coh))
    ax5.plot([angles[1]], [r_coh], marker="s")

    r_trend = max(0.0, min(1.0, trend))
    ax5.plot([angles[2]], [r_trend], marker="^")

    r_O = max(0.0, min(1.0, Omega))
    th = [i * 2.0 * math.pi / 360.0 for i in range(361)]
    rO_list = [r_O for _ in th]
    ax5.plot(th, rO_list, linestyle=":")

    ax5.set_xticks(angles)
    ax5.set_xticklabels(["E", "I", "C"])
    ax5.set_yticks([])
    ax5.set_title(f"Harmonic Seal v1.7\nband={band} • alert={alert}", va="bottom")
    fig5.tight_layout()
    out5 = visuals_dir / f"solar_resonance_harmonic_seal_v1_7_{ts_tag}.png"
    fig5.savefig(out5)
    plt.close(fig5)
    saved.append(str(out5))

    # 6) Solar QIM lattice (ΔΦ → 2D resonance map)
    L = len(dphi_norm)
    side = int(math.sqrt(L))
    if side < 1:
        side = 1
    L2 = side * side

    vals = dphi_norm[:L2]
    if len(vals) < L2:
        vals = vals + [0.0] * (L2 - len(vals))

    lattice = np.array(vals, dtype=float).reshape(side, side)

    fig6, ax6 = plt.subplots(figsize=(4, 4))
    im3 = ax6.imshow(lattice, aspect="equal", interpolation="nearest")
    ax6.set_xticks([])
    ax6.set_yticks([])
    ax6.set_title("Solar QIM Lattice v1.7")
    fig6.colorbar(im3, ax=ax6, fraction=0.046, pad=0.04)
    fig6.tight_layout()
    out6 = visuals_dir / f"solar_resonance_qim_lattice_v1_7_{ts_tag}.png"
    fig6.savefig(out6)
    plt.close(fig6)
    saved.append(str(out6))

    return saved

# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    state, t_idx, t_labels, flux, bz, g_flux, g_bz, dphi_local = compute_state()

    ts_safe = (
        state["timestamp"]
        .replace(":", "")
        .replace("-", "")
        .replace(".", "")
    )

    out_path = state_dir / f"solar_resonance_state_v1_7_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    visuals = make_visuals(state, t_idx, flux, bz, g_flux, g_bz, dphi_local, ts_safe)

    ledger_entry = {
        "timestamp": state["timestamp"],
        "version": state["version"],
        "C": state["C"],
        "C_half": state.get("C_half", None),
        "dC": state.get("dC", None),
        "coherence_score": state.get("coherence_score", None),
        "DeltaPhi_grad": state["DeltaPhi_grad"],
        "DeltaPhi_local_mean": state.get("DeltaPhi_local_mean", None),
        "harmonic_index": state.get("harmonic_index", None),
        "harmonic_peak": state.get("harmonic_peak", None),
        "harmonic_entropy": state.get("harmonic_entropy", None),
        "bz_negative_fraction": state.get("bz_negative_fraction", None),
        "trend_score": state.get("trend_score", None),
        "Omega": state.get("Omega", None),
        "band": state.get("band", "unknown"),
        "drift": state.get("drift", "flat"),
        "alert_level": state.get("alert_level", "quiet"),
        "source": state.get("source", "unknown"),
        "SRS": state.get("SRS", None),
        "visuals": visuals,
        "H7": H7,
        "node": "solar_resonance_v1_7"
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\n")

    print(json.dumps({
        "ok": True,
        "state_path": str(out_path),
        "visuals": visuals,
        "C": state["C"],
        "Omega": state.get("Omega", None),
        "coherence_score": state.get("coherence_score", None),
        "band": state["band"],
        "drift": state.get("drift", "flat"),
        "alert_level": state.get("alert_level", "quiet"),
        "source": state["source"],
        "SRS": state.get("SRS", None)
    }, indent=2))

if __name__ == "__main__":
    main()
