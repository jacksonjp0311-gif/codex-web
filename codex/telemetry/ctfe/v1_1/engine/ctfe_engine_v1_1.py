#!/usr/bin/env python3
# 𓂀  Codex Telemetric Fusion Engine v1.1 — CTFE ΔΦ Telemetry Node
# Multi-source telemetry → ΔΦ proxy → coherence C → H7 proximity → visuals

import os
import sys
import json
import math
import time
import datetime as _dt
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

try:
    import urllib.request
    import urllib.error
    HAVE_URLLIB = True
except Exception:
    HAVE_URLLIB = False

# H7 band (Codex universal coherence horizon)
H7_MIN = 0.70
H7_MAX = 0.75

# ─────────────────────────────────────────────────────────────
# 0 ▸ H7 / ΔΦ metrics (v1.1 proxy)
# ─────────────────────────────────────────────────────────────

def compute_coherence_from_series(x: np.ndarray, eps: float = 1e-9) -> float:
    """
    v1.1 proxy for coherence:
      - drop NaNs
      - normalize to zero mean, unit variance
      - ΔΦ ~ mean |gradient|
      - C = 1 / (1 + ΔΦ)

    Returns C in [0, 1].
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size < 3 or np.allclose(x, x[0]):
        return 0.0

    x = (x - x.mean()) / (x.std() + eps)
    grad = np.diff(x)
    dphi = float(np.mean(np.abs(grad)))
    C = 1.0 / (1.0 + dphi)
    C = max(0.0, min(1.0, C))
    return C

def h7_proximity(C: float, c_min: float = H7_MIN, c_max: float = H7_MAX) -> float:
    """
    H7 proximity:
      - 1.0 if C ∈ [c_min, c_max]
      - taper linearly to 0 outside the band
    """
    if not (0.0 <= C <= 1.0):
        return 0.0
    if c_min <= C <= c_max:
        return 1.0
    if C < c_min:
        return max(0.0, C / c_min)
    return max(0.0, (1.0 - C) / (1.0 - c_max + 1e-9))

def cusp_params(E: float = 1.0, I: float = 1.0, gamma: float = 0.35) -> Tuple[float, float, float]:
    """
    Approximate Codex ΔΦ Cusp v2.8 kernel parameters:
      • D_c via 8 γ D_c² = (EI)⁴ + 27 γ (EI)³
      • Φ_c = (EI)² / (3 γ)
      • C_cusp = 3γ / (EI + 3γ)
    """
    EI = E * I
    Dc_sq = ((EI ** 4) + 27.0 * gamma * (EI ** 3)) / (8.0 * gamma)
    Dc = math.sqrt(max(Dc_sq, 0.0))
    phi_c = (EI ** 2) / (3.0 * gamma)
    C_cusp = (3.0 * gamma) / (EI + 3.0 * gamma)
    return Dc, phi_c, C_cusp

# ─────────────────────────────────────────────────────────────
# 1 ▸ Telemetry sources
# ─────────────────────────────────────────────────────────────

class TelemetrySource:
    name: str = "abstract"
    domain: str = "generic"

    def fetch(self) -> Tuple[List[str], np.ndarray, Dict[str, Any]]:
        raise NotImplementedError

class SyntheticSineSource(TelemetrySource):
    name = "synthetic_sine_demo"
    domain = "synthetic"

    def fetch(self):
        t = np.linspace(0.0, 10.0, 1000)
        values = np.sin(t) + 0.2 * np.random.randn(t.size)
        now = _dt.datetime.utcnow().isoformat() + "Z"
        t_iso = [now for _ in range(values.size)]
        meta = {
            "type": "synthetic",
            "description": "Noisy sine wave demo",
        }
        return t_iso, values, meta

class USGSEarthquakeSource(TelemetrySource):
    name = "usgs_quakes_all_day"
    domain = "seismic"

    def fetch(self):
        if not HAVE_URLLIB:
            synth = SyntheticSineSource()
            return synth.fetch()

        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            synth = SyntheticSineSource()
            return synth.fetch()

        feats = data.get("features", [])
        mags = []
        times = []
        for f in feats:
            props = f.get("properties", {})
            mag = props.get("mag", None)
            tms = props.get("time", None)  # ms since epoch
            if mag is None or tms is None:
                continue
            try:
                mags.append(float(mag))
                dt = _dt.datetime.utcfromtimestamp(tms / 1000.0)
                times.append(dt.isoformat() + "Z")
            except Exception:
                continue

        if not mags:
            synth = SyntheticSineSource()
            return synth.fetch()

        values = np.array(mags, dtype=float)
        return times, values, {
            "type": "usgs",
            "description": "USGS all_day earthquake magnitudes",
            "url": url,
            "count": len(values),
        }

class OpenMeteoTempSource(TelemetrySource):
    name = "openmeteo_temp_nyc"
    domain = "weather"

    def fetch(self):
        if not HAVE_URLLIB:
            synth = SyntheticSineSource()
            return synth.fetch()

        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=40.71&longitude=-74.01"
            "&hourly=temperature_2m"
            "&past_days=1&forecast_days=0"
        )
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            synth = SyntheticSineSource()
            return synth.fetch()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        if not times or not temps or len(times) != len(temps):
            synth = SyntheticSineSource()
            return synth.fetch()

        values = np.array(temps, dtype=float)
        return times, values, {
            "type": "open-meteo",
            "description": "Open-Meteo hourly temperature (NYC)",
            "url": url,
            "count": len(values),
            "units": "°C",
        }

def discover_sources() -> List[TelemetrySource]:
    return [
        SyntheticSineSource(),
        USGSEarthquakeSource(),
        OpenMeteoTempSource(),
    ]

# ─────────────────────────────────────────────────────────────
# 2 ▸ Paths, logging, JSONL DB
# ─────────────────────────────────────────────────────────────

def ensure_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)

def log(line: str, log_path: str) -> None:
    ts = _dt.datetime.utcnow().isoformat() + "Z"
    msg = f"[{ts}] {line}"
    print(msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")

# ─────────────────────────────────────────────────────────────
# 3 ▸ Visuals & dashboard
# ─────────────────────────────────────────────────────────────

def plot_histogram(coherences: List[float], out_path: str, log_path: str) -> None:
    if not coherences or not HAVE_MPL:
        return
    plt.figure(figsize=(5, 4), dpi=150)
    plt.hist(coherences, bins=20, alpha=0.85)
    plt.axvspan(H7_MIN, H7_MAX, alpha=0.25)
    plt.xlabel("Coherence C")
    plt.ylabel("Count")
    plt.title(f"Global Coherence vs H7 band [{H7_MIN:.2f}, {H7_MAX:.2f}]")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    log(f"Wrote global coherence histogram → {out_path}", log_path)

def plot_per_source_bars(per_source: List[Dict[str, Any]], out_path: str, log_path: str) -> None:
    if not per_source or not HAVE_MPL:
        return
    names = [s["name"] for s in per_source]
    C_vals = [s["coherence"] for s in per_source]
    H_vals = [s["h7_proximity"] for s in per_source]

    x = np.arange(len(names))
    width = 0.35

    plt.figure(figsize=(6, 4), dpi=150)
    plt.bar(x - width/2, C_vals, width=width, label="C")
    plt.bar(x + width/2, H_vals, width=width, label="H7 proximity")
    plt.axhspan(H7_MIN, H7_MAX, alpha=0.15)
    plt.xticks(x, names, rotation=30, ha="right")
    plt.ylim(0, 1.05)
    plt.ylabel("Score")
    plt.title("Per-source coherence & H7 proximity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    log(f"Wrote per-source coherence bars → {out_path}", log_path)

def write_dashboard(dash_path: str,
                    summary: Dict[str, Any],
                    hist_rel: str,
                    bars_rel: str,
                    qim_context: Dict[str, Any] | None = None) -> None:
    lines = []
    lines.append(f"# Codex Telemetric Fusion Engine — Run {summary['run_id']}")
    lines.append("")
    lines.append(f"- Timestamp (UTC): **{summary['timestamp_utc']}**")
    lines.append(f"- Sources analyzed: **{summary['num_sources']}**")
    lines.append(f"- Mean coherence C: **{summary['coherence_mean']:.4f}**")
    lines.append(f"- Std coherence C: **{summary['coherence_std']:.4f}**")
    lines.append(f"- H7 band: **[{H7_MIN:.2f}, {H7_MAX:.2f}]**")
    lines.append(f"- Global H7 proximity index: **{summary['global_h7_index']:.4f}**")
    lines.append("")
    if qim_context is not None:
        lines.append("## QIM Coupling")
        lines.append(f"- QIM source: **{qim_context.get('source_tag','?')}**")
        triad = qim_context.get("triad")
        if triad:
            lines.append(f"- QIM triad: E={triad.get('E')}, I={triad.get('I')}, C={triad.get('C')}")
        lam = qim_context.get("lambda_eff")
        if lam is not None:
            lines.append(f"- QIM λ_eff: {lam}")
        om = qim_context.get("omega_mean")
        if om is not None:
            lines.append(f"- QIM ω_mean: {om}")
        lines.append("")
    lines.append("## Global Coherence Histogram")
    lines.append(f"![Global Coherence Histogram]({hist_rel})")
    lines.append("")
    lines.append("## Per-Source Coherence & H7 Proximity")
    lines.append(f"![Per-Source Coherence]({bars_rel})")
    lines.append("")
    lines.append("## Sources")
    for s in summary["per_source"]:
        lines.append(
            f"- **{s['name']}** "
            f"(domain={s.get('domain','?')}): "
            f"C={s['coherence']:.4f}, "
            f"H7_proximity={s['h7_proximity']:.4f}, "
            f"C_cusp≈{s['C_cusp']:.4f}, "
            f"λ≈{s['lambda_eff']:.4f}"
        )

    with open(dash_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ─────────────────────────────────────────────────────────────
# 4 ▸ Main CTFE run
# ─────────────────────────────────────────────────────────────

def run_ctfe(state_dir: str,
             db_dir: str,
             raw_dir: str,
             visuals_dir: str,
             logs_dir: str,
             dashboard_dir: str,
             qim_context: Dict[str, Any] | None = None) -> Dict[str, str]:
    ensure_dirs(state_dir, db_dir, raw_dir, visuals_dir, logs_dir, dashboard_dir)

    run_id = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(logs_dir, f"ctfe_run_{run_id}.log")
    db_jsonl_path = os.path.join(db_dir, "ctfe_timeseries.jsonl")
    ledger_path = os.path.join(logs_dir, "ctfe_ledger.jsonl")

    log(f"⊹ CTFE v1.1 start (run_id={run_id})", log_path)

    sources = discover_sources()
    per_source_stats: List[Dict[str, Any]] = []
    global_coherences: List[float] = []
    global_proximities: List[float] = []

    for src in sources:
        log(f"Fetching telemetry from source: {src.name}", log_path)
        try:
            t_iso, values, meta = src.fetch()
            values = np.asarray(values, dtype=float)

            raw_snapshot = {
                "run_id": run_id,
                "source_name": src.name,
                "domain": getattr(src, "domain", "unknown"),
                "timestamps": t_iso,
                "values": values.tolist(),
                "meta": meta,
            }
            append_jsonl(os.path.join(raw_dir, f"ctfe_raw_{run_id}.jsonl"), raw_snapshot)

            now = _dt.datetime.utcnow().isoformat() + "Z"
            for ts, v in zip(t_iso, values):
                row = {
                    "run_id": run_id,
                    "source_name": src.name,
                    "domain": getattr(src, "domain", "unknown"),
                    "t_iso": ts or now,
                    "value": float(v),
                }
                append_jsonl(db_jsonl_path, row)

            C = compute_coherence_from_series(values)
            H = h7_proximity(C)

            v_abs = np.abs(values)
            EI_eff = float(v_abs.mean() + 1e-6)
            gamma_eff = 0.35
            Dc, phi_c, C_cusp = cusp_params(E=1.0, I=EI_eff, gamma=gamma_eff)
            D_eff = float(np.median(values))
            lambda_eff = D_eff / (Dc + 1e-9)

            global_coherences.append(C)
            global_proximities.append(H)

            stat = {
                "name": src.name,
                "domain": getattr(src, "domain", "unknown"),
                "coherence": C,
                "h7_proximity": H,
                "EI_eff": EI_eff,
                "gamma_eff": gamma_eff,
                "D_eff": D_eff,
                "Dc": Dc,
                "phi_c": phi_c,
                "C_cusp": C_cusp,
                "lambda_eff": lambda_eff,
                "meta": meta,
            }
            per_source_stats.append(stat)
            log(
                f"Source {src.name}: C={C:.4f}, H7={H:.4f}, "
                f"C_cusp≈{C_cusp:.4f}, λ≈{lambda_eff:.4f}",
                log_path,
            )
        except Exception as e:
            log(f"ERROR in source {src.name}: {e}", log_path)

    if global_coherences:
        C_arr = np.asarray(global_coherences, dtype=float)
        C_mean = float(C_arr.mean())
        C_std = float(C_arr.std())
    else:
        C_mean = 0.0
        C_std = 0.0

    if global_proximities:
        H_arr = np.asarray(global_proximities, dtype=float)
        H_index = float(H_arr.mean())
    else:
        H_index = 0.0

    summary = {
        "run_id": run_id,
        "timestamp_utc": _dt.datetime.utcnow().isoformat() + "Z",
        "num_sources": len(per_source_stats),
        "coherence_mean": C_mean,
        "coherence_std": C_std,
        "global_h7_index": H_index,
        "h7_band": [H7_MIN, H7_MAX],
        "per_source": per_source_stats,
    }

    state_path = os.path.join(state_dir, f"ctfe_run_state_{run_id}.json")
    summary_path = os.path.join(state_dir, f"ctfe_run_summary_{run_id}.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log(f"Wrote CTFE state → {state_path}", log_path)
    log(f"Wrote CTFE summary → {summary_path}", log_path)

    hist_png = os.path.join(visuals_dir, f"ctfe_global_histogram_{run_id}.png")
    bars_png = os.path.join(visuals_dir, f"ctfe_per_source_{run_id}.png")
    plot_histogram(global_coherences, hist_png, log_path)
    plot_per_source_bars(per_source_stats, bars_png, log_path)

    dash_path = os.path.join(dashboard_dir, "index.md")
    hist_rel = os.path.relpath(hist_png, dashboard_dir) if os.path.exists(hist_png) else hist_png
    bars_rel = os.path.relpath(bars_png, dashboard_dir) if os.path.exists(bars_png) else bars_png
    write_dashboard(dash_path, summary, hist_rel, bars_rel, qim_context=qim_context)
    log(f"Wrote CTFE dashboard → {dash_path}", log_path)

    ledger_entry = {
        "run_id": run_id,
        "timestamp_utc": summary["timestamp_utc"],
        "state_path": state_path,
        "summary_path": summary_path,
        "version": "1.1.0",
        "H7_band": [H7_MIN, H7_MAX],
        "global_h7_index": H_index,
        "coherence_mean": C_mean,
        "coherence_std": C_std,
        "num_sources": len(per_source_stats),
        "qim_context": qim_context,
    }
    append_jsonl(ledger_path, ledger_entry)
    log(f"Appended CTFE ledger entry → {ledger_path}", log_path)

    out = {
        "state_path": state_path,
        "summary_path": summary_path,
    }
    print(json.dumps(out))
    return out

# ─────────────────────────────────────────────────────────────
# 5 ▸ CLI entrypoint
# ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) not in (7, 8):
        print("Usage: ctfe_engine_v1_1.py STATE_DIR DB_DIR RAW_DIR VISUALS_DIR LOGS_DIR DASHBOARD_DIR [QIM_JSON]", file=sys.stderr)
        sys.exit(1)
    state_dir, db_dir, raw_dir, visuals_dir, logs_dir, dash_dir = sys.argv[1:7]
    qim_context = None
    if len(sys.argv) == 8:
        try:
            qim_context = json.loads(sys.argv[7])
        except Exception:
            qim_context = None
    run_ctfe(state_dir, db_dir, raw_dir, visuals_dir, logs_dir, dash_dir, qim_context=qim_context)
    return 0

if __name__ == "__main__":
    sys.exit(main())
