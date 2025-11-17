#!/usr/bin/env python
import json
import math
import datetime
import pathlib

from urllib import request

# ─────────────────────────────────────────
# Paths (Codex-style)
# ─────────────────────────────────────────
root = pathlib.Path(__file__).resolve().parents[3]  # Codex Web root
module_root = root / "codex" / "solar_resonance"

state_dir   = module_root / "state"   / "v4_0"
visuals_dir = module_root / "visuals" / "v4_0"
lattice_dir = module_root / "lattice" / "v4_0"
horizon_dir = module_root / "horizon" / "v4_0"
ledger_path = module_root / "logs"    / "ledger" / "ledger.jsonl"

state_dir.mkdir(parents=True, exist_ok=True)
visuals_dir.mkdir(parents=True, exist_ok=True)
lattice_dir.mkdir(parents=True, exist_ok=True)
horizon_dir.mkdir(parents=True, exist_ok=True)
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
                val = -5.0 * math.sin(2.0 * math.pi * i / float(L))
                bz.append(val)
        return t_idx, t_labels, flux, bz, "hybrid_goes"

    # Fallback synthetic
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
# Solar Resonance Model v4.0
#   3D ΔΦ Volumetric Horizon Engine
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

    # E: mean flux (Energy channel)
    E = sum(flux) / float(N)

    # I: std-dev of flux (Information channel)
    mean_flux = E
    var = sum((x - mean_flux) ** 2 for x in flux) / float(N)
    I = math.sqrt(var)

    C_raw = (E * I) / (1.0 + abs(delta_phi_grad))
    if H7 > 0.0:
        C_norm = max(0.0, min(1.0, C_raw / H7))
    else:
        C_norm = 0.0

    # Local ΔΦ field (1D along time)
    dphi_local = []
    Lg = min(len(g_flux), len(g_bz))
    for i in range(Lg):
        dphi_local.append(abs(g_flux[i]) + abs(g_bz[i]))
    if not dphi_local:
        dphi_local = [0.0]

    delta_phi_local_mean = sum(dphi_local) / float(len(dphi_local))

    # Spectral / harmonic features (1D)
    arr = None
    try:
        import numpy as np
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
            else:
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
                else:
                    harmonic_entropy = 0.0
            else:
                harmonic_entropy = 0.0

    # Coherence score (C + entropy)
    coherence_score = 0.0
    try:
        entropy_term = max(0.0, min(1.0, 1.0 - harmonic_entropy))
        coherence_score = 0.5 * C_norm + 0.5 * entropy_term
    except Exception:
        coherence_score = C_norm

    # H7 band
    band = "unknown"
    if 0.68 <= C_norm <= 0.72:
        band = "locked_H7"
    elif C_norm < 0.68:
        band = "sub_H7"
    else:
        band = "super_H7"

    # C_half for simple drift
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
    elif dC < -0.02:
        drift = "falling"

    # Bz negative fraction
    bz_neg_fraction = 0.0
    if N > 0:
        bz_neg_fraction = sum(1 for x in bz if x < 0.0) / float(N)

    # Trend score
    trend_score = 0.5
    try:
        z = dC / 0.05
        z = max(-1.0, min(1.0, z))
        trend_score = 0.5 + 0.5 * z
    except Exception:
        trend_score = 0.5

    # Oracle Ω
    entropy_term2 = 0.0
    try:
        entropy_term2 = max(0.0, min(1.0, 1.0 - harmonic_entropy))
    except Exception:
        entropy_term2 = 0.0

    Omega = (C_norm + entropy_term2 + trend_score) / 3.0

    # Sun Resonance Signature (SRS)
    SRS = {
        "Omega": Omega,
        "band": band,
        "alert_level": "quiet",
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
        "version": "4.0",
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
        "alert_level": "quiet",
        "source": source,
        "SRS": SRS,
    }

    return state, t_idx, t_labels, flux, bz, g_flux, g_bz, dphi_local


# ─────────────────────────────────────────
# Visuals + 3D Volume / Horizon
# ─────────────────────────────────────────
def make_visuals_and_volume(state, dphi_local, ts_tag):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        return [], 0.0, 0.0, 0.0

    saved = []

    # Normalize ΔΦ
    dphi_abs = [abs(x) for x in dphi_local]
    if not dphi_abs:
        dphi_abs = [0.0]
    m2 = max(dphi_abs)
    if m2 == 0.0:
        m2 = 1.0
    dphi_norm_1d = [x / m2 for x in dphi_abs]

    # ───── 2D AFM-style base field (like v3.0) ─────
    G = 96
    x = np.linspace(0.0, 1.0, G)
    y = np.linspace(0.0, 1.0, G)
    X, Y = np.meshgrid(x, y)

    idx_norm = np.linspace(0.0, 1.0, len(dphi_norm_1d))
    phi = np.array(dphi_norm_1d, dtype=float)
    phi_rev = phi[::-1]

    phi_x = np.interp(X, idx_norm, phi)
    phi_y = np.interp(Y, idx_norm, phi_rev)

    base_field = phi_x * phi_y

    # Simple smoothed noise
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

    field_2d = base_field + 0.6 * wave_field + 0.4 * noise
    fmin = float(field_2d.min())
    fmax = float(field_2d.max())
    if fmax > fmin:
        field_norm_2d = (field_2d - fmin) / (fmax - fmin)
    else:
        field_norm_2d = np.zeros_like(field_2d)

    # ───── 3D ΔΦ Volume construction ─────
    # Depth axis = segments of 1D ΔΦ + phase shifts (Triadic motion)
    depth = 32
    L = len(dphi_norm_1d)
    if L < depth:
        # tile if needed
        repeats = int(math.ceil(depth / float(L)))
        dphi_extended = (np.tile(dphi_norm_1d, repeats))[:depth]
    else:
        step = L / depth
        dphi_extended = [dphi_norm_1d[int(i * step)] for i in range(depth)]
    dphi_extended = np.array(dphi_extended, dtype=float)

    volume = []
    for k in range(depth):
        phase = 2.0 * math.pi * (k / float(depth))
        # rotate field in a simple way by mixing sin/cos of phase
        slice_field = (
            math.cos(phase) * field_norm_2d +
            math.sin(phase) * np.roll(field_norm_2d, k // 4, axis=1)
        )
        # scale by depth ΔΦ weight
        slice_field = slice_field * (0.3 + 0.7 * dphi_extended[k])
        volume.append(slice_field)

    volume = np.stack(volume, axis=0)  # shape: [D, H, W]

    vmin = float(volume.min())
    vmax = float(volume.max())
    if vmax > vmin:
        volume_norm = (volume - vmin) / (vmax - vmin)
    else:
        volume_norm = np.zeros_like(volume)

    # Save raw 3D volume for future temporal horizon / QIM usage
    vol_file = lattice_dir / f"solar_volume_v4_0_{ts_tag}.npy"
    import numpy as np
    np.save(vol_file, volume_norm)

    # ───── Visual 1: slice grid mosaic ─────
    n_slices = 6
    idx_slices = np.linspace(0, depth - 1, n_slices, dtype=int)
    fig_grid, axes = plt.subplots(2, 3, figsize=(9, 6))
    axes = axes.ravel()
    for ax, kk in zip(axes, idx_slices):
        im = ax.imshow(volume_norm[kk], aspect="equal", interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"z={kk}")
    fig_grid.colorbar(im, ax=axes, fraction=0.046, pad=0.04)
    fig_grid.suptitle("Solar ΔΦ Volume — Slice Grid v4.0")
    fig_grid.tight_layout()
    out_grid = visuals_dir / f"solar_volume_slice_grid_v4_0_{ts_tag}.png"
    fig_grid.savefig(out_grid)
    plt.close(fig_grid)
    saved.append(str(out_grid))

    # ───── Visual 2: Max-intensity projection (MIP) ─────
    mip_z = volume_norm.max(axis=0)
    fig_mip, ax_mip = plt.subplots(figsize=(4, 4))
    im_mip = ax_mip.imshow(mip_z, aspect="equal", interpolation="nearest")
    ax_mip.set_xticks([])
    ax_mip.set_yticks([])
    ax_mip.set_title("Solar ΔΦ Volume — MIP v4.0")
    fig_mip.colorbar(im_mip, ax=ax_mip, fraction=0.046, pad=0.04)
    fig_mip.tight_layout()
    out_mip = visuals_dir / f"solar_volume_mip_v4_0_{ts_tag}.png"
    fig_mip.savefig(out_mip)
    plt.close(fig_mip)
    saved.append(str(out_mip))

    # ───── Visual 3: Simple 3D scatter of high-intensity voxels ─────
    try:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        fig_3d = plt.figure(figsize=(5, 5))
        ax3d = fig_3d.add_subplot(111, projection="3d")

        thresh = 0.8
        zz, yy, xx = np.where(volume_norm > thresh)
        # Subsample if too many
        if zz.size > 4000:
            step = max(1, zz.size // 4000)
            zz = zz[::step]
            yy = yy[::step]
            xx = xx[::step]

        ax3d.scatter(xx, yy, zz, s=1)
        ax3d.set_xlabel("x")
        ax3d.set_ylabel("y")
        ax3d.set_zlabel("z")
        ax3d.set_title("Solar ΔΦ Volume — 3D Scatter v4.0")
        fig_3d.tight_layout()
        out_3d = visuals_dir / f"solar_volume_scatter_v4_0_{ts_tag}.png"
        fig_3d.savefig(out_3d)
        plt.close(fig_3d)
        saved.append(str(out_3d))
    except Exception:
        pass

    # ───── Volume metrics: volumetric coherence + turbulence ─────
    # treat volume_norm as [D, H, W]
    # temporal / depth variance vs spatial variance
    D, H, W = volume_norm.shape
    # variance across depth vs across spatial
    var_depth = float(volume_norm.var(axis=0).mean())   # how much slices differ
    var_space = float(volume_norm.var(axis=(1, 2)).mean())  # average variance per slice

    denom = var_depth + var_space
    volume_coherence = 0.0
    if denom > 0.0:
        volume_coherence = var_depth / denom

    # turbulence via 3D FFT high-frequency energy
    spec3d = abs(np.fft.rfftn(volume_norm))
    total_energy = float(spec3d.sum())
    volume_turbulence = 0.0
    if total_energy > 0.0:
        # take upper third along last axis as "high freq"
        hf = spec3d[..., spec3d.shape[-1] // 3 :]
        volume_turbulence = float(hf.sum() / total_energy)

    return saved, float(volume_turbulence), float(volume_coherence), str(vol_file)


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

    visuals, vol_turb, vol_coh, vol_path = make_visuals_and_volume(
        state, dphi_local, ts_safe
    )

    state["volume_turbulence"] = vol_turb
    state["volume_coherence"] = vol_coh
    state["SRS"]["volume_turbulence"] = vol_turb
    state["SRS"]["volume_coherence"] = vol_coh
    state["volume_path"] = vol_path

    out_path = state_dir / f"solar_resonance_state_v4_0_{ts_safe}.json"
    out_path.write_text(json.dumps(state, indent=2))

    # Ledger entry
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
        "volume_turbulence": vol_turb,
        "volume_coherence": vol_coh,
        "volume_path": vol_path,
        "visuals": visuals,
        "H7": H7,
        "node": "solar_resonance_v4_0",
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry) + "\\n")

    print(json.dumps({
        "ok": True,
        "state_path": str(out_path),
        "volume_path": vol_path,
        "visuals": visuals,
        "C": state["C"],
        "Omega": state.get("Omega", None),
        "coherence_score": state.get("coherence_score", None),
        "band": state["band"],
        "drift": state.get("drift", "flat"),
        "alert_level": state.get("alert_level", "quiet"),
        "source": state["source"],
        "SRS": state.get("SRS", None),
        "volume_turbulence": vol_turb,
        "volume_coherence": vol_coh,
    }, indent=2))


if __name__ == "__main__":
    main()
