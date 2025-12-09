#!/usr/bin/env python3
# 𓂀  Codex Telemetry All-One Engine v2.1 — Multi-Source ΔΦ Fusion
#
#  ROLE
#    • Accept one telemetry profile (JSON) at a time
#    • Pull real data (GOES X-ray, Open-Meteo weather) with synthetic fallback
#    • Convert series → ΔΦ(t), C(t) using Codex law C = 1 / (1+|ΔΦ|)
#    • Map telemetry to 2D Kerr-like field + ΔΦ field + coherence C field
#    • Compute H₇, λ_eff, collapse_state under ΔΦ Cusp Law v2.8
#    • Emit:
#         – state JSON (telemetry + metrics_ref + visuals paths)
#         – summary JSON (compact metrics)
#    • Print {state_path, summary_path} to stdout as JSON

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
# 2 ▸ Telemetry acquisition
# ─────────────────────────────────────────────────────────────
def fetch_goes_xray(max_points=512):
    """NOAA SWPC GOES X-ray flux (0.1–0.8 nm) — 1-day fallback 6h."""
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
                f = item.get("flux", None)
                if f is None:
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
                    times    = times[-max_points:]
                return {
                    "name":  "NOAA SWPC GOES X-ray",
                    "times": times,
                    "series": flux_arr,
                }
        except Exception as exc:
            last_err = exc
            continue

    raise RuntimeError(f"GOES telemetry fetch failed: {last_err}")

def fetch_openmeteo(lat, lon, variable="temperature_2m", max_points=512):
    """
    Open-Meteo hourly forecast for last 1 day.
    variable ∈ {"temperature_2m", "windspeed_10m", "precipitation"}
    """
    from urllib.request import urlopen
    import urllib.parse as _up

    base = "https://api.open-meteo.com/v1/forecast"
    query = {
        "latitude":  f"{lat}",
        "longitude": f"{lon}",
        "hourly":    variable,
        "past_days": "1",
        "forecast_days": "1",
        "timezone": "UTC",
    }
    url = base + "?" + _up.urlencode(query)
    with urlopen(url, timeout=10) as resp:
        data = resp.read()
    obj = json.loads(data.decode("utf-8", errors="ignore"))
    hourly = obj.get("hourly", {})
    times  = hourly.get("time", [])
    vals   = hourly.get(variable, [])

    if not times or not vals:
        raise RuntimeError("Open-Meteo hourly data missing")

    arr = np.array(vals, dtype=np.float64)
    if arr.size > max_points:
        arr   = arr[-max_points:]
        times = times[-max_points:]

    label = f"Open-Meteo {variable}"
    return {
        "name":  label,
        "times": times,
        "series": arr,
    }

def synthetic_weather_series(kind="baseline", max_points=512):
    """
    Synthetic atmospheric-like series: baseline + daily cycle + transient.
    """
    n = max_points
    t = np.linspace(0.0, 1.0, n, dtype=np.float64)

    if kind == "baseline":
        base  = 20.0 + 5.0 * np.sin(2.0 * math.pi * t)
        pulse = 3.0 * np.exp(-0.5 * ((t - 0.6) / 0.07) ** 2)
        noise = 0.3 * np.random.randn(n)
        series = base + pulse + noise
        name = "Synthetic Temperature (baseline)"
    else:
        base  = 5.0 + 2.0 * np.sin(4.0 * math.pi * t)
        pulse = 1.5 * np.exp(-0.5 * ((t - 0.3) / 0.05) ** 2)
        noise = 0.2 * np.random.randn(n)
        series = base + pulse + noise
        name = "Synthetic Atmosphere (alt)"

    return {
        "name":  name,
        "times": ["" for _ in range(n)],
        "series": series.astype(np.float64),
    }

def acquire_telemetry(profile, max_points=512):
    """
    Profile: dict with keys {id, label, provider, lat, lon}
    Returns dict {name, series, times, provider, used_real_data}
    """
    provider = profile.get("provider", "")
    lat = profile.get("lat", None)
    lon = profile.get("lon", None)

    used_real = True
    tele_raw = None

    try:
        if provider == "goes_xray":
            tele_raw = fetch_goes_xray(max_points=max_points)
        elif provider == "openmeteo_temp":
            if lat is None or lon is None:
                raise RuntimeError("lat/lon missing for openmeteo_temp")
            tele_raw = fetch_openmeteo(lat, lon, variable="temperature_2m", max_points=max_points)
        elif provider == "openmeteo_wind":
            if lat is None or lon is None:
                raise RuntimeError("lat/lon missing for openmeteo_wind")
            tele_raw = fetch_openmeteo(lat, lon, variable="windspeed_10m", max_points=max_points)
        elif provider == "openmeteo_precip":
            if lat is None or lon is None:
                raise RuntimeError("lat/lon missing for openmeteo_precip")
            tele_raw = fetch_openmeteo(lat, lon, variable="precipitation", max_points=max_points)
        else:
            used_real = False
            tele_raw  = synthetic_weather_series(kind="baseline", max_points=max_points)
    except Exception:
        used_real = False
        if provider.startswith("openmeteo"):
            tele_raw = synthetic_weather_series(kind="baseline", max_points=max_points)
        elif provider == "goes_xray":
            tele_raw = synthetic_weather_series(kind="alt", max_points=max_points)
        else:
            tele_raw = synthetic_weather_series(kind="baseline", max_points=max_points)

    series = np.array(tele_raw["series"], dtype=np.float64)
    times  = tele_raw.get("times", [""] * series.size)
    name   = tele_raw.get("name", provider)
    if series.size > max_points:
        series = series[-max_points:]
        times  = times[-max_points:]

    return {
        "name":     name,
        "series":   series,
        "times":    times,
        "provider": provider,
        "used_real_data": bool(used_real),
    }

# ─────────────────────────────────────────────────────────────
# 3 ▸ Telemetry → ΔΦ(t), C(t)
# ─────────────────────────────────────────────────────────────
def fuse_telemetry(tele):
    """
    From raw series → ΔΦ(t) + C(t) using:
      flux_norm = (series - median) / MAD
      ΔΦ(t)     = ∂/∂t flux_norm
      C(t)      = 1 / (1 + |ΔΦ|)
    """
    series = np.array(tele["series"], dtype=np.float64)
    mask   = np.isfinite(series)
    series = series[mask]
    if series.size < 16:
        raise RuntimeError("Not enough valid telemetry points")

    med = np.median(series)
    dev = np.median(np.abs(series - med)) + 1e-12
    flux_norm = (series - med) / dev

    dphi_series = np.gradient(flux_norm)
    C_series    = 1.0 / (1.0 + np.abs(dphi_series))

    C_avg_1d   = float(C_series.mean())
    H7_frac_1d = float(np.mean(C_series >= 0.70))
    D_eff      = float(np.mean(np.abs(dphi_series)))
    N_points   = int(series.size)

    return {
        "flux_norm":   flux_norm,
        "dphi_series": dphi_series,
        "C_series":    C_series,
        "C_avg_1d":    C_avg_1d,
        "H7_frac_1d":  H7_frac_1d,
        "D_eff":       D_eff,
        "N_points":    N_points,
    }

# ─────────────────────────────────────────────────────────────
# 4 ▸ Geometry: Kerr-like intensity + ΔΦ field
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
# 5 ▸ I/O helpers
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

def save_series_png(path, flux_norm, C_series, label):
    if not HAVE_MPL:
        return
    import matplotlib.pyplot as plt
    t = np.linspace(0.0, 1.0, flux_norm.size, dtype=np.float64)
    plt.figure(figsize=(6,3), dpi=150)
    plt.plot(t, flux_norm, label=f"{label} (norm)")
    plt.plot(t, C_series,    label="C(t)")
    plt.xlabel("normalized time")
    plt.ylabel("value")
    plt.legend(loc="best", fontsize=7)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", pad_inches=0.05)
    plt.close()

# ─────────────────────────────────────────────────────────────
# 6 ▸ Main
# ─────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 7:
        print("Usage: ROOT STATE VISUAL LEDGER LOGS PROFILE_JSON", file=sys.stderr)
        return 1

    ROOT, STATE, VISUAL, LEDGER, LOGS, PROFILE_JSON = sys.argv[1:7]

    os.makedirs(STATE, exist_ok=True)
    os.makedirs(VISUAL, exist_ok=True)
    os.makedirs(LEDGER, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)

    # NOTE: use utf-8-sig to tolerate BOM from PowerShell UTF-8 writes
    with open(PROFILE_JSON, "r", encoding="utf-8-sig") as f:
        profile = json.load(f)

    # 6.1 ▸ Acquire telemetry (real → synthetic fallback)
    tele = acquire_telemetry(profile, max_points=512)
    fuse = fuse_telemetry(tele)

    flux_norm   = fuse["flux_norm"]
    dphi_series = fuse["dphi_series"]
    C_series    = fuse["C_series"]
    C_avg_1d    = fuse["C_avg_1d"]
    H7_1d       = fuse["H7_frac_1d"]
    D_eff       = fuse["D_eff"]
    N_points    = fuse["N_points"]

    # 6.2 ▸ ΔΦ Cusp law metrics (effective)
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

    # 6.3 ▸ Build Kerr-like geometry from coherence
    N = 256
    r0    = 0.8 + 0.15 * (C_avg_1d - 0.5)
    r0    = float(min(max(r0, 0.5), 1.1))
    sigma = 0.05 + 0.15 * (1.0 - min(H7_1d * 1.5, 1.0))
    sigma = float(min(max(sigma, 0.03), 0.25))

    x, y, R, I_field = build_kerr_field(N=N, r0=r0, sigma=sigma, p=2.0)

    smooth     = local_mean_3x3(I_field)
    dphi_field = I_field - smooth
    C_field    = (E_eff * I_field) / (1.0 + np.abs(dphi_field))

    C_avg_2d   = float(C_field.mean())
    H7_2d      = float(np.mean(C_field >= 0.70))
    dphi_global = float(np.mean(np.abs(dphi_field)))

    hsk = hsk_metrics(R, I_field)

    # 6.4 ▸ Visuals
    now_tag = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pid     = profile.get("id", "telemetry")
    label   = profile.get("label", profile.get("provider", "telemetry"))

    intensity_png = os.path.join(VISUAL, f"{pid}_intensity_{now_tag}.png")
    coherence_png = os.path.join(VISUAL, f"{pid}_coherence_{now_tag}.png")
    dphi_png      = os.path.join(VISUAL, f"{pid}_dphi_{now_tag}.png")
    series_png    = os.path.join(VISUAL, f"{pid}_series_{now_tag}.png")

    save_png(intensity_png, I_field, cmap="inferno", title=f"{label} intensity")
    save_png(coherence_png, C_field, cmap="viridis", title=f"{label} coherence C")
    save_png(dphi_png, np.abs(dphi_field), cmap="coolwarm", title=f"{label} |ΔΦ|")
    save_series_png(series_png, flux_norm, C_series, label)

    # 6.5 ▸ State + summary JSON
    now_utc = _dt.datetime.utcnow().isoformat() + "Z"
    tag = f"{pid}_v2_1_{now_tag}"

    metrics_ref = {
        "C_avg_ref":        C_avg_2d,
        "H7_fraction_ref":  H7_2d,
        "r_h":              hsk["r_h"],
        "dr_halfmax":       hsk["dr_halfmax"],
        "delta_phi_global": dphi_global,
        "delta_phi_1d_mean": D_eff,
        "lambda_eff":       lambda_eff,
        "collapse_state":   collapse_state,
        "EI_ref":           E_eff * I_eff,
        "gamma_ref":        gamma,
        "phi_c":            phi_c,
        "C_cusp":           C_cusp,
        "C_avg_1d":         C_avg_1d,
        "H7_fraction_1d":   H7_1d,
    }

    telemetry_info = {
        "profile_id":     profile.get("id"),
        "profile_label":  label,
        "provider":       tele["provider"],
        "used_real_data": bool(tele["used_real_data"]),
        "N_points":       N_points,
        "series_name":    tele["name"],
    }

    state = {
        "module":   "TELEMETRY_ALL_ONE",
        "version":  "2.1",
        "tag":      tag,
        "timestamp_utc": now_utc,
        "source":   "codex_telemetry_all_one_v2_1",
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
                "H16": "Telemetry → geometry (1D→2D)",
                "H19": "Global ΔΦ integration across profiles",
                "H31": "Harmonic stability ridge",
                "H41": "Torsion spiral memory (telemetry strain vault)",
            },
        },
        "visuals": {
            "intensity_png":    intensity_png,
            "coherence_H7_png": coherence_png,
            "dphi_png":         dphi_png,
            "telemetry_series": series_png,
        },
    }

    summary = {
        "tag":            tag,
        "version":        "2.1",
        "profile_id":     profile.get("id"),
        "profile_label":  label,
        "provider":       tele["provider"],
        "used_real_data": bool(tele["used_real_data"]),
        "C_avg_ref":      C_avg_2d,
        "H7_fraction":    H7_2d,
        "lambda_eff":     lambda_eff,
        "collapse_state": collapse_state,
        "delta_phi_global": dphi_global,
        "r_h":            hsk["r_h"],
        "dr_halfmax":     hsk["dr_halfmax"],
        "C_cusp":         C_cusp,
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
