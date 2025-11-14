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
state_dir   = module_root / "state" / "v1_9"
visuals_dir = module_root / "visuals" / "v1_9"
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
# Simple 2D smoothing (AFM-style height field)
# ─────────────────────────────────────────
def smooth2d(arr, passes=2):
    import numpy as np
    kernel = np.array([[1, 2, 1],
                       [2, 4, 2],
                       [1, 2, 1]], dtype=float)
    kernel = kernel / kernel.sum()

    out = np.array(arr, dtype=float)
    for _ in range(passes):
        padded = np.pad(out, 1, mode="edge")
        tmp = np.zeros_like(out)
        for i in range(out.shape[0]):
            for j in range(out.shape[1]):
                block = padded[i:i+3, j:j+3]
                tmp[i, j] = float((block * kernel).sum())
        out = tmp
    return out

# ─────────────────────────────────────────
# Codex Solar Resonance Model v1.9
#   Solar AFM Imaging Node:
#   C, Ω, spectral ΔΦ, trend, QIM lattice + AFM height-map
# ─────────────────────────────────────────
def compute_state_and_field():
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

    # Local ΔΦ field (QIM-style strip)
    dphi_local = []
    Lg = min(len(g_flux), len(g_bz))
    for i in range(Lg):
        dphi_local.append(abs(g_flux[i]) + abs(g_bz[i]))
    if not dphi_local:
        dphi_local = [0.0]

    delta_phi_local_mean = sum(dphi_local) / float(len(dphi_local))

    import numpy as np
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

    # Combined coherence score
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

    # ─────────────────────────────────────
    # Solar AFM QIM lattice construction
    # ─────────────────────────────────────
    dphi_abs = [abs(x) for x in dphi_local]
    if not dphi_abs:
        dphi_abs = [0.0]
    m0 = max(dphi_abs)
    if m0 == 0.0:
        m0 = 1.0
    base = [x / m0 for x in dphi_abs]
    base_arr = np.array(base, dtype=float)

    # Multi-scale rows (deterministic warps)
    scales = [1.0, 0.8, 0.6, 0.4, 0.3, 0.2]
    rows = []
    L = base_arr.size
    for k, s in enumerate(scales):
        shift = int((k * L) / (len(scales) * 3) )
        rolled = np.roll(base_arr, shift)
        gamma = 0.7 + 0.5 * (1.0 - s)
        warped = np.power(rolled + 1e-9, gamma)
        rows.append(warped)

    field = np.vstack(rows)  # shape: (len(scales), L)

    # Fold into near-square lattice
    total = field.size
    side = int(math.sqrt(total))
    if side < field.shape[0]:
        side = field.shape[0]
    side2 = side * side

    flat = field.flatten()
    if flat.size < side2:
        pad = np.zeros(side2 - flat.size, dtype=float)
        flat = np.concatenate([flat, pad])
    if flat.size > side2:
        flat = flat[:side2]

    lattice = flat.reshape(side, side)
    lattice_smooth = smooth2d(lattice, passes=2)

    # Normalize height + simple texture metric
    h_min = float(lattice_smooth.min())
    h_max = float(lattice_smooth.max())
    denom = h_max - h_min if h_max != h_min else 1.0
    lattice_norm = (lattice_smooth - h_min) / denom

    texture_contrast = float(lattice_norm.std())

    # Sun Resonance Signature (SRS) — extended with AFM stats
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
        "AFM_height_min": h_min,
        "AFM_height_max": h_max,
        "AFM_texture_contrast": texture_contrast,
        "AFM_side": side,
    }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "1.9",
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

    return state, t_idx, flux, bz, dphi_local, lattice_norm

# ─────────────────────────────────────────
# Visuals (Solar AFM QIM + Harmonic Seal v2)
# ─────────────────────────────────────────
def make_visuals(state, dphi_local, lattice_norm, ts_tag):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        return []

    saved = []

    # 1) ΔΦ Harmonic Spectrum (for continuity)
    dphi_abs = [abs(x) for x in dphi_local]
    if not dphi_abs:
        dphi_abs = [0.0]
    arr_spec = np.array(dphi_abs, dtype=float)
    spec = abs(np.fft.rfft(arr_spec))
    freqs = np.arange(spec.size)

    fig0, ax0 = plt.subplots(figsize=(6, 3))
    if spec.size > 0:
        ax0.plot(freqs, spec)
    ax0.set_xlabel("Frequency bin")
    ax0.set_ylabel("|FFT(ΔΦ)|")
    ax0.set_title("Solar ΔΦ Harmonic Spectrum v1.9")
    ax0.grid(True, alpha=0.3)
    fig0.tight_layout()
    out0 = visuals_dir / f"solar_resonance_dphi_spectrum_v1_9_{ts_tag}.png"
    fig0.savefig(out0)
    plt.close(fig0)
    saved.append(str(out0))

    # 2) Harmonic Seal v2 (oracle triad)
    C = state.get("C", 0.0)
    coh = state.get("coherence_score", 0.0)
    trend = state.get("trend_score", 0.5)
    Omega = state.get("Omega", 0.0)
    band = state.get("band", "unknown")
    alert = state.get("alert_level", "quiet")

    fig1 = plt.figure(figsize=(4, 4))
    ax1 = fig1.add_subplot(111, projection="polar")

    angles = [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0]
    for ang in angles:
        ax1.plot([ang, ang], [0.0, 1.0])

    ax1.set_ylim(0.0, 1.0)

    r_C = max(0.0, min(1.0, C))
    ax1.plot([0.0], [r_C], marker="o")

    r_coh = max(0.0, min(1.0, coh))
    ax1.plot([angles[1]], [r_coh], marker="s")

    r_trend = max(0.0, min(1.0, trend))
    ax1.plot([angles[2]], [r_trend], marker="^")

    r_O = max(0.0, min(1.0, Omega))
    th = [i * 2.0 * math.pi / 360.0 for i in range(361)]
    rO_list = [r_O for _ in th]
    ax1.plot(th, rO_list, linestyle=":")

    ax1.set_xticks(angles)
    ax1.set_xticklabels(["E", "I", "C"])
    ax1.set_yticks([])
    ax1.set_title(f"Harmonic Seal v1.9\nband={band} • alert={alert}", va="bottom")
    fig1.tight_layout()
    out1 = visuals_dir / f"solar_resonance_harmonic_seal_v1_9_{ts_tag}.png"
    fig1.savefig(out1)
    plt.close(fig1)
    saved.append(str(out1))

    # 3) Solar QIM Lattice (height map)
    fig2, ax2 = plt.subplots(figsize=(4, 4))
    im2 = ax2.imshow(lattice_norm, aspect="equal", interpolation="nearest")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("Solar QIM Lattice v1.9")
    fig2.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    fig2.tight_layout()
    out2 = visuals_dir / f"solar_resonance_qim_lattice_v1_9_{ts_tag}.png"
    fig2.savefig(out2)
    plt.close(fig2)
    saved.append(str(out2))

    # 4) Solar AFM Map (same lattice, emphasized as AFM surface)
    #    (height map reused; conceptually AFM imaging)
    fig3, ax3 = plt.subplots(figsize=(4, 4))
    im3 = ax3.imshow(lattice_norm, aspect="equal", interpolation="bilinear")
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.set_title("Solar AFM Map v1.9")
    fig3.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    fig3.tight_layout()
    out3 = visuals_dir / f"solar_resonance_afm_map_v1_9_{ts_tag}.png"
    fig3.savefig(out3)
    plt.close(fig3)
    saved.append(str(out3))

    return saved

# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    state, t_idx, flux, bz, dphi_local, lattice_norm = compute_state_and_field()

    ts_safe = (
        state["timestamp"]
        .replace(":", "")
        .replace("-", "")
        .replace(".", "")
    )

    out_path = state_dir / f"solar_resonance_state_v1_9_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    visuals = make_visuals(state, dphi_local, lattice_norm, ts_safe)

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
        "node": "solar_resonance_v1_9"
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\\n")

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
