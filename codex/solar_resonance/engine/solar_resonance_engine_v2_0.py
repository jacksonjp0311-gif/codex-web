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
state_dir   = module_root / "state" / "v2_0"
visuals_dir = module_root / "visuals" / "v2_0"
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
# Codex Solar Resonance Model v2.0
#   Multi-Scale ΔΦ Turbulence + QIM fusion
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

    # Combined coherence score (v1.6/1.7 style)
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

    # Sun Resonance Signature (SRS)
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

    # Multi-scale turbulence index from 2D ΔΦ field (filled in make_visuals)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    state = {
        "ok": True,
        "version": "2.0",
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
# Visuals (AFM-style Solar QIM)
# ─────────────────────────────────────────
def make_visuals(state, t_idx, flux, bz, g_flux, g_bz, dphi_local, ts_tag):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        # Visuals are optional; state still valid
        return [], None

    saved = []

    # Normalize ΔΦ field
    dphi_abs = [abs(x) for x in dphi_local]
    if not dphi_abs:
        dphi_abs = [0.0]
    m2 = max(dphi_abs)
    if m2 == 0.0:
        m2 = 1.0
    dphi_norm = [x / m2 for x in dphi_abs]

    # ───── 1) Solar AFM map v2.0 (macro+micro turbulence) ─────
    G = 128
    import numpy as np

    x = np.linspace(0.0, 1.0, G)
    y = np.linspace(0.0, 1.0, G)
    X, Y = np.meshgrid(x, y)

    idx_norm = np.linspace(0.0, 1.0, len(dphi_norm))
    phi = np.array(dphi_norm, dtype=float)
    phi_rev = phi[::-1]

    phi_x = np.interp(X, idx_norm, phi)
    phi_y = np.interp(Y, idx_norm, phi_rev)

    base_field = phi_x * phi_y

    rng = np.random.default_rng()
    noise = rng.normal(size=(G, G))

    for _ in range(3):
        noise = 0.25 * (
            np.roll(noise, 1, 0)
            + np.roll(noise, -1, 0)
            + np.roll(noise, 1, 1)
            + np.roll(noise, -1, 1)
        )

    mean_phi = float(phi.mean()) if phi.size > 0 else 0.5
    modes = [(1, 2), (3, 5), (5, 8)]
    wave_field = np.zeros_like(base_field)
    for fx, fy in modes:
        phase = 2.0 * math.pi * (fx * X + fy * Y)
        wave_field += math.sqrt(2.0) * mean_phi * np.sin(phase)

    field = base_field + 0.6 * wave_field + 0.4 * noise

    fmin = float(field.min())
    fmax = float(field.max())
    if fmax > fmin:
        field_norm = (field - fmin) / (fmax - fmin)
    if fmax <= fmin:
        field_norm = np.zeros_like(field)

    fig_afm, ax_afm = plt.subplots(figsize=(4, 4))
    im_afm = ax_afm.imshow(field_norm, aspect="equal", interpolation="nearest")
    ax_afm.set_xticks([])
    ax_afm.set_yticks([])
    ax_afm.set_title("Solar AFM Map v2.0")
    fig_afm.colorbar(im_afm, ax=ax_afm, fraction=0.046, pad=0.04)
    fig_afm.tight_layout()
    out_afm = visuals_dir / f"solar_afm_map_v2_0_{ts_tag}.png"
    fig_afm.savefig(out_afm)
    plt.close(fig_afm)
    saved.append(str(out_afm))

    # ───── 2) Solar ΔΦ harmonic spectrum v2.0 ─────
    arr_spec1d = np.array(dphi_abs, dtype=float)
    spec = abs(np.fft.rfft(arr_spec1d))
    freqs = np.arange(spec.size)

    fig_spec, ax_spec = plt.subplots(figsize=(6, 3))
    if spec.size > 0:
        ax_spec.plot(freqs, spec)
    ax_spec.set_xlabel("Frequency bin")
    ax_spec.set_ylabel("|FFT(ΔΦ)|")
    ax_spec.set_title("Solar ΔΦ Harmonic Spectrum v2.0")
    ax_spec.grid(True, alpha=0.3)
    fig_spec.tight_layout()
    out_spec = visuals_dir / f"solar_dphi_spectrum_v2_0_{ts_tag}.png"
    fig_spec.savefig(out_spec)
    plt.close(fig_spec)
    saved.append(str(out_spec))

    # ───── 3) Harmonic Seal v2.0 (E–I–C + Ω ring) ─────
    C = state.get("C", 0.0)
    coh = state.get("coherence_score", 0.0)
    trend = state.get("trend_score", 0.5)
    Omega = state.get("Omega", 0.0)
    band = state.get("band", "unknown")
    alert = state.get("alert_level", "quiet")

    fig_seal = plt.figure(figsize=(4, 4))
    ax_seal = fig_seal.add_subplot(111, projection="polar")

    angles = [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0]
    for ang in angles:
        ax_seal.plot([ang, ang], [0.0, 1.0])

    ax_seal.set_ylim(0.0, 1.0)

    r_C = max(0.0, min(1.0, C))
    ax_seal.plot([0.0], [r_C], marker="o")

    r_coh = max(0.0, min(1.0, coh))
    ax_seal.plot([angles[1]], [r_coh], marker="s")

    r_trend = max(0.0, min(1.0, trend))
    ax_seal.plot([angles[2]], [r_trend], marker="^")

    r_O = max(0.0, min(1.0, Omega))
    th = [i * 2.0 * math.pi / 360.0 for i in range(361)]
    rO_list = [r_O for _ in th]
    ax_seal.plot(th, rO_list, linestyle=":")

    ax_seal.set_xticks(angles)
    ax_seal.set_xticklabels(["E", "I", "C"])
    ax_seal.set_yticks([])
    ax_seal.set_title(f"Harmonic Seal v2.0\nband={band} • alert={alert}", va="bottom")
    fig_seal.tight_layout()
    out_seal = visuals_dir / f"solar_harmonic_seal_v2_0_{ts_tag}.png"
    fig_seal.savefig(out_seal)
    plt.close(fig_seal)
    saved.append(str(out_seal))

    # ───── 4) Solar QIM lattice v2.0 (single-scale) ─────
    fig_lat, ax_lat = plt.subplots(figsize=(4, 4))
    im_lat = ax_lat.imshow(field_norm, aspect="equal", interpolation="nearest")
    ax_lat.set_xticks([])
    ax_lat.set_yticks([])
    ax_lat.set_title("Solar QIM Lattice v2.0")
    fig_lat.colorbar(im_lat, ax=ax_lat, fraction=0.046, pad=0.04)
    fig_lat.tight_layout()
    out_lat = visuals_dir / f"solar_qim_lattice_v2_0_{ts_tag}.png"
    fig_lat.savefig(out_lat)
    plt.close(fig_lat)
    saved.append(str(out_lat))

    # ───── 5) Multi-scale QIM panel (coarse vs fine) ─────
    # coarse: heavy downsample, fine: slight downsample
    coarse = field_norm[::8, ::8]
    fine   = field_norm[::2, ::2]

    fig_ms, (ax_c, ax_f) = plt.subplots(1, 2, figsize=(6, 3))
    im_c = ax_c.imshow(coarse, aspect="equal", interpolation="nearest")
    ax_c.set_xticks([])
    ax_c.set_yticks([])
    ax_c.set_title("Solar QIM — Coarse")

    im_f = ax_f.imshow(fine, aspect="equal", interpolation="nearest")
    ax_f.set_xticks([])
    ax_f.set_yticks([])
    ax_f.set_title("Solar QIM — Fine")

    fig_ms.colorbar(im_f, ax=[ax_c, ax_f], fraction=0.046, pad=0.04)
    fig_ms.tight_layout()
    out_ms = visuals_dir / f"solar_qim_multiscale_v2_0_{ts_tag}.png"
    fig_ms.savefig(out_ms)
    plt.close(fig_ms)
    saved.append(str(out_ms))

    # Turbulence index from high-frequency 2D spectrum
    spec2d = abs(np.fft.rfft2(field_norm))
    total_energy = float(spec2d.sum())
    turbulence_index = 0.0
    if total_energy > 0.0:
        hf = spec2d[:, spec2d.shape[1] // 3 :]
        turbulence_index = float(hf.sum() / total_energy)

    return saved, float(turbulence_index)


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

    visuals, turb_index = make_visuals(
        state, t_idx, flux, bz, g_flux, g_bz, dphi_local, ts_safe
    )

    if turb_index is None:
        turb_index = 0.0

    state["turbulence_index"] = turb_index
    state["SRS"]["turbulence_index"] = turb_index

    out_path = state_dir / f"solar_resonance_state_v2_0_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

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
        "turbulence_index": turb_index,
        "visuals": visuals,
        "H7": H7,
        "node": "solar_resonance_v2_0",
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
        "SRS": state.get("SRS", None),
        "turbulence_index": turb_index,
    }, indent=2))


if __name__ == "__main__":
    main()
