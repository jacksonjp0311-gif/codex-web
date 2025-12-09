#!/usr/bin/env python3
# 𓂀  CTFE Engine v1.3 — Telemetry Fusion Kernel (Real GOES + ΔΦ Cusp v2.8)

import os
import sys
import json
import math
import datetime as _dt

import numpy as np

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False


# ─────────────────────────────────────────────────────────────
# 1 ▸ ΔΦ Cusp helpers (v2.8 kernel)
# ─────────────────────────────────────────────────────────────
def cusp_params(E=1.0, I=1.0, gamma=0.35):
    EI = E * I
    Dc_sq = ((EI**4) + 27.0 * gamma * (EI**3)) / (8.0 * gamma)
    Dc    = math.sqrt(max(Dc_sq, 1e-16))
    phi_c = (EI**2) / (3.0 * gamma)
    C_c   = (3.0 * gamma) / (EI + 3.0 * gamma)
    return Dc, phi_c, C_c


# ─────────────────────────────────────────────────────────────
# 2 ▸ Telemetry acquisition (NOAA GOES X-ray + fallback)
# ─────────────────────────────────────────────────────────────
def fetch_goes_xray(max_points=512):
    """
    Try NOAA SWPC GOES primary X-ray flux endpoints.
    Returns dict: {name, times, flux} or raises on failure.
    """
    import ssl
    from urllib.request import urlopen

    urls = [
        "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json",
        "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json",
    ]

    ctx = ssl.create_default_context()
    last_err = None

    for url in urls:
        try:
            with urlopen(url, context=ctx, timeout=10) as resp:
                data = resp.read()
            obj = json.loads(data.decode("utf-8", errors="ignore"))
            if not isinstance(obj, list) or not obj:
                continue

            times = []
            flux_vals = []
            for item in obj:
                if not isinstance(item, dict):
                    continue
                # Try generic "flux" key first (common in SWPC JSON)
                f = item.get("flux", None)
                if f is None:
                    # Try some alternative keys we have seen in practice
                    for key in ("flux_0.1-0.8nm", "flux_0_1_0_8", "flux_short"):
                        if key in item and item[key] is not None:
                            f = item[key]
                            break
                if f is None:
                    continue
                try:
                    fv = float(f)
                except Exception:
                    continue
                flux_vals.append(fv)
                times.append(item.get("time_tag", item.get("time", "")))

            if len(flux_vals) >= 16:
                flux_arr = np.array(flux_vals, dtype=np.float64)
                if flux_arr.size > max_points:
                    flux_arr = flux_arr[-max_points:]
                    times = times[-max_points:]
                return {
                    "name":  "NOAA SWPC GOES X-ray",
                    "times": times,
                    "flux":  flux_arr,
                }
        except Exception as exc:
            last_err = exc
            continue

    raise RuntimeError(f"GOES telemetry fetch failed: {last_err}")


def synthetic_xray_series(max_points=512):
    """
    Offline / failure fallback: synthetic flare-like X-ray series.
    """
    n = max_points
    t = np.linspace(0.0, 1.0, n, dtype=np.float64)

    # Base + slow modulation + one sharp flare bump.
    base   = 1e-6 + 5e-7 * np.sin(2.0 * math.pi * 1.5 * t)
    flare  = 6e-6 * np.exp(-0.5 * ((t - 0.7) / 0.05) ** 2)
    noise  = 1e-7 * np.random.randn(n)

    flux = base + flare + noise
    return {
        "name":  "Synthetic X-ray (offline)",
        "times": ["" for _ in range(n)],
        "flux":  flux.astype(np.float64),
    }


def fuse_telemetry(tele):
    """
    From raw flux → ΔΦ(t) and C(t) using simple Codex law:
      C = 1 / (1 + |ΔΦ|)
    Returns metrics + normalized arrays for plotting.
    """
    flux = np.array(tele["flux"], dtype=np.float64)
    mask = np.isfinite(flux)
    flux = flux[mask]
    if flux.size < 16:
        raise RuntimeError("Not enough valid telemetry points")

    # Normalize around median with robust scale
    med = np.median(flux)
    dev = np.median(np.abs(flux - med)) + 1e-12
    flux_norm = (flux - med) / dev

    dphi_series = np.gradient(flux_norm)
    C_series    = 1.0 / (1.0 + np.abs(dphi_series))

    C_avg_1d      = float(C_series.mean())
    H7_frac_1d    = float(np.mean(C_series >= 0.70))
    D_eff         = float(np.mean(np.abs(dphi_series)))
    N_points      = int(flux.size)

    return {
        "flux_norm":     flux_norm,
        "dphi_series":   dphi_series,
        "C_series":      C_series,
        "C_avg_1d":      C_avg_1d,
        "H7_frac_1d":    H7_frac_1d,
        "D_eff":         D_eff,
        "N_points":      N_points,
    }


# ─────────────────────────────────────────────────────────────
# 3 ▸ Geometry: Kerr-like ring + local ΔΦ field
# ─────────────────────────────────────────────────────────────
def build_kerr_field(N=256, r0=0.8, sigma=0.08, p=2.0):
    x = np.linspace(-1.5, 1.5, N, dtype=np.float64)
    y = np.linspace(-1.5, 1.5, N, dtype=np.float64)
    X, Y = np.meshgrid(x, y, indexing="xy")
    R = np.sqrt(X**2 + Y**2)

    ring = np.exp(-0.5 * ((R - r0) / sigma) ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        radial = 1.0 / (1.0 + (R / max(r0, 1e-3)) ** p)

    I = ring * radial
    I /= (I.max() + 1e-12)
    return x, y, R, I


def radial_profile(R, I, nbins=512):
    r = R.ravel()
    v = I.ravel()
    rmin, rmax = r.min(), r.max()
    bins = np.linspace(rmin, rmax, nbins + 1)
    idx = np.digitize(r, bins) - 1
    prof = np.zeros(nbins, dtype=np.float64)
    cnt  = np.zeros(nbins, dtype=np.float64)
    for k in range(len(r)):
        j = idx[k]
        if 0 <= j < nbins:
            prof[j] += v[k]
            cnt[j]  += 1.0
    cnt[cnt == 0.0] = 1.0
    prof /= cnt
    centers = 0.5 * (bins[:-1] + bins[1:])
    return centers, prof


def hsk_metrics(R, I):
    r_centers, prof = radial_profile(R, I, nbins=512)
    imax = prof.max()
    iidx = int(np.argmax(prof))
    r_h  = float(r_centers[iidx])

    half = 0.5 * imax
    above = prof >= half

    left = iidx
    while left > 0 and above[left]:
        left -= 1
    right = iidx
    while right < len(prof) - 1 and above[right]:
        right += 1

    r_low  = float(r_centers[max(left, 0)])
    r_high = float(r_centers[min(right, len(r_centers)-1)])
    dr_halfmax = float(max(r_high - r_low, 0.0))

    if 1 <= iidx < len(prof) - 1:
        dr = float(r_centers[iidx+1] - r_centers[iidx-1])
        if dr != 0.0:
            S_h = float((prof[iidx+1] - prof[iidx-1]) / dr)
        else:
            S_h = 0.0
    else:
        S_h = 0.0

    return {
        "r_h":        r_h,
        "r_low":      r_low,
        "r_high":     r_high,
        "dr_halfmax": dr_halfmax,
        "I_max":      float(imax),
        "S_h":        S_h,
        "radial_r":   r_centers.tolist(),
        "radial_I":   prof.tolist(),
    }


def local_mean_3x3(arr):
    """
    Simple 3×3 local mean (no SciPy dependency).
    """
    h, w = arr.shape
    out = np.zeros_like(arr)
    for i in range(h):
        i0 = max(0, i-1)
        i1 = min(h, i+2)
        for j in range(w):
            j0 = max(0, j-1)
            j1 = min(w, j+2)
            patch = arr[i0:i1, j0:j1]
            out[i, j] = patch.mean()
    return out


# ─────────────────────────────────────────────────────────────
# 4 ▸ I/O helpers
# ─────────────────────────────────────────────────────────────
def save_png(path, img, cmap="inferno", vmin=None, vmax=None, title=None):
    if not HAVE_MPL:
        return
    import matplotlib.pyplot as plt
    plt.figure(figsize=(4,4), dpi=150)
    if img.ndim == 2:
        plt.imshow(img, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax)
    else:
        plt.imshow(img, origin="lower")
    plt.axis("off")
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close()


def save_series_png(path, flux_norm, C_series):
    if not HAVE_MPL:
        return
    import matplotlib.pyplot as plt
    t = np.linspace(0.0, 1.0, flux_norm.size, dtype=np.float64)
    plt.figure(figsize=(6,3), dpi=150)
    plt.plot(t, flux_norm, label="flux_norm")
    plt.plot(t, C_series,    label="C(t)")
    plt.xlabel("normalized time")
    plt.ylabel("value")
    plt.legend(loc="best", fontsize=7)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", pad_inches=0.05)
    plt.close()


# ─────────────────────────────────────────────────────────────
# 5 ▸ Main
# ─────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 9:
        print("Usage: ROOT STATE VISUAL LEDGER LOGS SOURCE SUPERRES NOISE [QIM_JSON]")
        return 1

    ROOT, STATE, VISUAL, LEDGER, LOGS, SOURCE, SUPERRES, NOISE = sys.argv[1:9]
    QIM_JSON = sys.argv[9] if len(sys.argv) > 9 else None

    os.makedirs(STATE, exist_ok=True)
    os.makedirs(VISUAL, exist_ok=True)
    os.makedirs(LEDGER, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)

    # 5.1 ▸ Telemetry: real → synthetic fallback
    used_real = True
    try:
        tele = fetch_goes_xray(max_points=512)
    except Exception:
        tele = synthetic_xray_series(max_points=512)
        used_real = False

    fuse = fuse_telemetry(tele)

    flux_norm   = fuse["flux_norm"]
    dphi_series = fuse["dphi_series"]
    C_series    = fuse["C_series"]
    C_avg_1d    = fuse["C_avg_1d"]
    H7_1d       = fuse["H7_frac_1d"]
    D_eff       = fuse["D_eff"]
    N_points    = fuse["N_points"]

    # 5.2 ▸ ΔΦ Cusp law metrics
    E_eff = 1.0
    I_eff = 1.0
    gamma = 0.35
    Dc, phi_c, C_cusp = cusp_params(E=E_eff, I=I_eff, gamma=gamma)
    lambda_eff = float(D_eff / Dc)

    if lambda_eff < 0.9:
        collapse_state = "metastable"
    elif lambda_eff <= 1.1:
        collapse_state = "near-cusp"
    else:
        collapse_state = "collapsed"

    # 5.3 ▸ Build Kerr-like geometry driven by telemetry coherence
    N = 256
    # r0 shifts slightly with coherence; sigma widens when coherence is low
    r0    = 0.8 + 0.15 * (C_avg_1d - 0.5)
    r0    = float(min(max(r0, 0.5), 1.1))
    sigma = 0.05 + 0.15 * (1.0 - min(H7_1d * 1.5, 1.0))
    sigma = float(min(max(sigma, 0.03), 0.25))

    x, y, R, I_field = build_kerr_field(N=N, r0=r0, sigma=sigma, p=2.0)

    smooth = local_mean_3x3(I_field)
    dphi_field = I_field - smooth
    C_field    = (E_eff * I_field) / (1.0 + np.abs(dphi_field))

    C_avg_2d = float(C_field.mean())
    H7_2d    = float(np.mean(C_field >= 0.70))
    dphi_global = float(np.mean(np.abs(dphi_field)))

    hsk = hsk_metrics(R, I_field)

    # 5.4 ▸ QIM coupling (optional)
    qim_metrics = None
    if QIM_JSON and os.path.isfile(QIM_JSON):
        try:
            with open(QIM_JSON, "r", encoding="utf-8") as f:
                qobj = json.load(f)
            qmet = qobj.get("metrics_ref", {})
            triad = qmet.get("triad", {
                "E": qmet.get("E", 1.0),
                "I": qmet.get("I", 0.1),
                "C": qmet.get("C", 0.05),
            })
            qim_metrics = {
                "triad": triad,
                "lambda_eff": qmet.get("lambda_eff", 0.0),
                "omega_mean": qmet.get("omega_mean", 0.0),
                "curvature_proxy": qmet.get("curvature_proxy", 0.0),
                "coherence_memory_index": qmet.get("coherence_memory_index", 0.0),
            }
        except Exception:
            qim_metrics = None

    # ─────────────────────────────────────────────────────────
    # 6 ▸ Visuals
    # ─────────────────────────────────────────────────────────
    now_tag = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    intensity_png = os.path.join(VISUAL, f"ctfe_field_intensity_{now_tag}.png")
    coherence_png = os.path.join(VISUAL, f"ctfe_coherence_map_{now_tag}.png")
    dphi_png      = os.path.join(VISUAL, f"ctfe_delta_phi_map_{now_tag}.png")
    series_png    = os.path.join(VISUAL, f"ctfe_telemetry_series_{now_tag}.png")

    save_png(intensity_png, I_field, cmap="inferno", title="CTFE Kerr-like intensity")
    save_png(coherence_png, C_field, cmap="viridis", title="CTFE ΔΦ-weighted coherence (C)")
    save_png(dphi_png, np.abs(dphi_field), cmap="coolwarm", title="CTFE |ΔΦ| field")
    save_series_png(series_png, flux_norm, C_series)

    # ─────────────────────────────────────────────────────────
    # 7 ▸ State + summary JSON
    # ─────────────────────────────────────────────────────────
    now_utc = _dt.datetime.utcnow().isoformat() + "Z"
    tag = f"ctfe_v1_3_{now_tag}"

    metrics_ref = {
        "C_avg_ref":          C_avg_2d,
        "H7_fraction_ref":    H7_2d,
        "r_h":                hsk["r_h"],
        "dr_halfmax":         hsk["dr_halfmax"],
        "delta_phi_global":   dphi_global,
        "delta_phi_1d_mean":  D_eff,
        "lambda_eff":         lambda_eff,
        "collapse_state":     collapse_state,
        "EI_ref":             E_eff * I_eff,
        "gamma_ref":          gamma,
        "phi_c":              phi_c,
        "C_cusp":             C_cusp,
        "C_avg_1d":           C_avg_1d,
        "H7_fraction_1d":     H7_1d,
    }

    telemetry_info = {
        "provider":       tele["name"],
        "used_real_data": bool(used_real),
        "N_points":       N_points,
    }

    state = {
        "module":    "CTFE",
        "version":   "1.3",
        "tag":       tag,
        "timestamp_utc": now_utc,
        "source":    SOURCE,
        "telemetry": telemetry_info,
        "metrics_ref": metrics_ref,
        "codex": {
            "laws": {
                "delta_phi_cusp_v2_8": "V(Φ) = -EI ln(1+Φ) + D Φ + (γ/2) ln(1+Φ²)",
                "universal_truth":     "C = (E*I)/(1+|ΔΦ|)",
            },
            "H_layers": {
                "H7":  "Coherence horizon (0.70–0.75)",
                "H7B": "ΔΦ Cusp Law v2.8 irreversible kernel",
                "H16": "Multi-scale insight (1D→2D geometry)",
                "H19": "Global ΔΦ integration",
                "H31": "Harmonic stability ridge",
                "H41": "Torsion spiral memory (telemetry strain vault)",
            },
        },
        "visuals": {
            "intensity_png":     intensity_png,
            "coherence_H7_png":  coherence_png,
            "dphi_png":          dphi_png,
            "telemetry_series":  series_png,
        },
        "qim_coupling": {
            "enabled":        bool(qim_metrics is not None),
            "qim_state_path": QIM_JSON,
            "qim_metrics":    qim_metrics,
        },
    }

    summary = {
        "tag":          tag,
        "version":      "1.3",
        "C_avg_ref":    C_avg_2d,
        "H7_fraction":  H7_2d,
        "lambda_eff":   lambda_eff,
        "collapse_state": collapse_state,
        "delta_phi_global": dphi_global,
        "r_h":          hsk["r_h"],
        "dr_halfmax":   hsk["dr_halfmax"],
        "C_cusp":       C_cusp,
    }

    state_path   = os.path.join(STATE,  f"{tag}_state.json")
    summary_path = os.path.join(STATE,  f"{tag}_summary.json")

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    out = {
        "state_path":   state_path,
        "summary_path": summary_path,
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
