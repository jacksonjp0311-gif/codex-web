#!/usr/bin/env python3
"""
QIM v4.7 — Living Engine v1.0
- Build 4D field
- Compute dphi, triad, H19, cusp metrics
- Read prior QIM v4.x states
- Compute C_gain
- Emit new state + ledger
- Auto-write next engine stub (v4.8)
"""

import argparse
import json
import math
import sys
import traceback
from pathlib import Path
from datetime import datetime

import numpy as np

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

# We keep stdout ASCII-safe (no Greek letters) to avoid Windows console encoding issues.


def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0


# ─────────────────────────────────────────────
# 1) SYNTHETIC 3D VOLUME (AFM-LIKE)
# ─────────────────────────────────────────────
def synthetic_volume(shape=(64, 64, 64), seed=47):
    np.random.seed(seed)
    nx, ny, nz = shape
    x = np.linspace(-1.5, 1.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    z = np.linspace(-1.5, 1.5, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    base = np.exp(-2.2 * R) * (1.0 + 0.40 * np.sin(5.5 * R))
    peaks = np.zeros_like(base)

    centers = [
        (0.0, 0.0, 0.0),
        (0.5, 0.45, -0.1),
        (-0.4, -0.3, 0.5),
        (0.2, -0.6, -0.4),
    ]
    for cx, cy, cz in centers:
        Rp = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
        peaks += np.exp(-32.0 * Rp * Rp)

    vol = base + 0.6 * peaks
    vol += 0.02 * np.random.randn(*vol.shape)
    return vol


def load_volume_from_afm(input_dir: Path, fallback_shape=(64, 64, 64)):
    """
    Future: support real AFM stacks.
    For now: if any PNG exists, we still synthesize but mark used_synthetic=False.
    """
    if not input_dir.exists():
        return synthetic_volume(shape=fallback_shape), True, 0

    pngs = sorted(input_dir.glob("*.png"))
    if len(pngs) == 0:
        return synthetic_volume(shape=fallback_shape), True, 0
    vol = synthetic_volume(shape=fallback_shape)
    return vol, False, len(pngs)


# ─────────────────────────────────────────────
# 2) 4D FIELD + DPHI
# ─────────────────────────────────────────────
def build_4d_field(volume3d, T=40):
    nx, ny, nz = volume3d.shape
    V = np.zeros((T, nx, ny, nz), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, nx)
    y = np.linspace(-1.0, 1.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    R = np.sqrt(X * X + Y * Y + Z * Z)

    for t in range(T):
        theta = 2.0 * math.pi * t / float(T)
        mod = 1.0 + 0.3 * math.sin(theta) + 0.2 * np.cos(2.0 * theta + 3.0 * R)
        V[t] = volume3d * mod
    return V


def compute_dphi_4d(V):
    T, nx, ny, nz = V.shape
    dphi = np.zeros_like(V, dtype=np.float32)
    for t in range(T):
        gx, gy, gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx * gx + gy * gy + gz * gz)
    return dphi


# ─────────────────────────────────────────────
# 3) METRICS (TRIAD, H19, CUSP)
# ─────────────────────────────────────────────
def compute_metrics(V, dphi):
    # E = mean |V|
    E = f(np.mean(np.abs(V)))
    # I = mean |grad V|
    I = f(np.mean(dphi))
    # H19 global dphi
    dphi_global = I

    # cusp-effective lambda in [0, 0.99)
    lam_eff = min(0.99, dphi_global / (1.0 + dphi_global))
    barrier_scale = (1.0 - lam_eff) ** 1.5 * (max(E * I, 0.0) ** 1.5)

    C_eff = (E * I) / (1.0 + abs(dphi_global))

    triad = {"E": E, "I": I, "C": C_eff}
    return {
        "triad": triad,
        "dphi_global": dphi_global,
        "lambda_eff": lam_eff,
        "barrier_scale": f(barrier_scale),
    }


def compute_harmonics(dphi):
    vals = dphi.flatten()
    positive = vals[vals > 0.0]
    if positive.size == 0:
        return {"core": 0, "shell": 0, "void": int(vals.size)}

    p95 = float(np.percentile(positive, 95.0))
    p50 = float(np.percentile(positive, 50.0))

    core = int((dphi >= p95).sum())
    shell = int(((dphi < p95) & (dphi >= p50)).sum())
    void = int((dphi < p50).sum())
    return {"core": core, "shell": shell, "void": void}


# ─────────────────────────────────────────────
# 4) PRIOR STATE SCAN (QIM v4.x)
# ─────────────────────────────────────────────
def scan_prior_states(codex_root: Path):
    """
    Look for codex/quantum_imaging/state_v4_*/qim_v4_*.json
    Use the last JSON (lexicographically) as prior reference.
    """
    pattern = codex_root / "codex" / "quantum_imaging" / "state_v4_*" / "*.json"
    candidates = sorted(pattern.parent.parent.rglob("*.json"))
    # Filter only QIM v4.* state files by name heuristic
    filtered = [p for p in candidates if "qim_v4_" in p.name]
    if not filtered:
        return None, None
    last_state = sorted(filtered)[-1]
    try:
        data = json.loads(last_state.read_text(encoding="utf-8"))
    except Exception:
        return last_state, None

    triad = data.get("triad") or data.get("metrics", {}).get("triad")
    C_prev = None
    if isinstance(triad, dict):
        C_prev = triad.get("C")
    return last_state, C_prev


# ─────────────────────────────────────────────
# 5) VISUALS (OPTIONAL)
# ─────────────────────────────────────────────
def save_visuals(V, dphi, visuals_dir: Path, prefix: str):
    paths = {}
    if not MATPLOTLIB_OK:
        return paths
    visuals_dir.mkdir(parents=True, exist_ok=True)

    T, nx, ny, nz = V.shape
    t_mid = T // 2
    z_mid = nz // 2

    # dphi central slice
    central = dphi[t_mid, :, :, z_mid]
    fig = plt.figure()
    plt.imshow(central, origin="lower")
    plt.title("QIM v4.7 dphi central slice")
    plt.colorbar()
    out_central = visuals_dir / f"{prefix}_dphi_central.png"
    fig.savefig(out_central, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_central"] = str(out_central)

    # max projection over t and z
    maxproj = dphi.max(axis=0).max(axis=2)
    fig = plt.figure()
    plt.imshow(maxproj, origin="lower")
    plt.title("QIM v4.7 dphi max projection (t,z)")
    plt.colorbar()
    out_max = visuals_dir / f"{prefix}_dphi_maxproj.png"
    fig.savefig(out_max, bbox_inches="tight")
    plt.close(fig)
    paths["dphi_maxproj"] = str(out_max)

    # resonance curve: mean |V| vs t
    energy_t = np.mean(np.abs(V), axis=(1, 2, 3))
    fig = plt.figure()
    plt.plot(range(T), energy_t)
    plt.xlabel("t")
    plt.ylabel("mean |V|")
    plt.title("QIM v4.7 resonance curve")
    out_curve = visuals_dir / f"{prefix}_resonance_curve.png"
    fig.savefig(out_curve, bbox_inches="tight")
    plt.close(fig)
    paths["resonance_curve"] = str(out_curve)

    return paths


# ─────────────────────────────────────────────
# 6) STATE + LEDGER + NEXT ENGINE STUB
# ─────────────────────────────────────────────
def write_state_and_ledger(
    codex_root: Path,
    state_dir: Path,
    ledger_dir: Path,
    input_source: str,
    used_synthetic: bool,
    png_count: int,
    V,
    dphi,
    metrics: dict,
    harmonics: dict,
    visuals: dict,
    prior_path: Path,
    prior_C: float,
):
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state_path = state_dir / f"qim_v4_7_living_state_{ts}.json"
    ledger_path = ledger_dir / "qim_v4_7_living_ledger.jsonl"

    T, nx, ny, nz = V.shape
    triad = metrics.get("triad", {})
    C_now = f(triad.get("C", 0.0))
    C_prev = f(prior_C) if prior_C is not None else None
    if C_prev is None or C_prev <= 0.0:
        C_gain = None
    else:
        C_gain = (C_now - C_prev) / C_prev

    state_obj = {
        "protocol": "CodexQIMLivingEngine",
        "version": "4.7",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "shape_4d": [int(T), int(nx), int(ny), int(nz)],
        "input_source": input_source,
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "metrics": {
            "triad": triad,
            "H19_dphi_global": metrics.get("dphi_global", 0.0),
            "cusp_lambda_eff": metrics.get("lambda_eff", 0.0),
            "cusp_barrier_scale": metrics.get("barrier_scale", 0.0),
            "harmonics": harmonics,
        },
        "codex": {
            "H_layer": {
                "H7": 0.70,
                "H19": "Global dphi integration layer (4D field)",
            },
            "laws": {
                "universal_truth": "C = (E*I)/(1 + |dphi_global|)",
                "cusp_v2_8": "lambda = P/P_cr -> 1-, barrier ~ (1-lambda)^(3/2) (E I)^(3/2)",
            },
        },
        "prior_state_path": str(prior_path) if prior_path is not None else None,
        "prior_C": C_prev,
        "C_now": C_now,
        "C_gain": C_gain,
        "visuals": visuals,
    }

    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")

    ledger_obj = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "qim-v4-7-living",
        "state_file": str(state_path),
        "input_source": input_source,
        "used_synthetic": bool(used_synthetic),
        "input_png_count": int(png_count),
        "E": f(triad.get("E", 0.0)),
        "I": f(triad.get("I", 0.0)),
        "C": C_now,
        "dphi_global": f(metrics.get("dphi_global", 0.0)),
        "lambda_eff": f(metrics.get("lambda_eff", 0.0)),
        "barrier_scale": f(metrics.get("barrier_scale", 0.0)),
        "harmonics": harmonics,
        "prior_state_path": str(prior_path) if prior_path is not None else None,
        "prior_C": C_prev,
        "C_gain": C_gain,
    }

    with ledger_path.open("a", encoding="utf-8") as f_ledger:
        f_ledger.write(json.dumps(ledger_obj, ensure_ascii=False) + "\n")

    return state_path, ledger_path


def write_next_engine_stub(codex_root: Path, C_gain):
    """
    Writes a minimal "next engine" stub under:
    codex/quantum_imaging/engine/codex_qim_v4_8_autogen.py

    It does not execute automatically; it is a suggestion artifact.
    """
    engine_dir = codex_root / "codex" / "quantum_imaging" / "engine"
    engine_dir.mkdir(parents=True, exist_ok=True)
    stub_path = engine_dir / "codex_qim_v4_8_autogen.py"

    trend = "neutral"
    if C_gain is not None:
        if C_gain > 0.0:
            trend = "improved"
        if C_gain < 0.0:
            trend = "degraded"

    stub = f'''#!/usr/bin/env python3
"""
QIM v4.8 — Autogenerated stub (from v4.7 Living Engine)
Trend: {trend}, C_gain={C_gain}
This file is a placeholder for the next evolution step.
You can extend it with new kernels, resolutions, or field modes.
"""
def main():
    print("QIM v4.8 autogenerated stub. Trend: {trend}, C_gain={C_gain}")
if __name__ == "__main__":
    main()
'''
    stub_path.write_text(stub, encoding="utf-8")
    return stub_path


# ─────────────────────────────────────────────
# 7) MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", required=True)
    parser.add_argument("--state_dir", required=True)
    parser.add_argument("--visuals_dir", required=True)
    parser.add_argument("--ledger_dir", required=True)
    parser.add_argument("--logs_dir", required=False)
    parser.add_argument("--input_afm_dir", required=False)
    args = parser.parse_args()

    codex_root = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None

    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"qim_v4_7_living_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        log_fp = log_path.open("a", encoding="utf-8")
    else:
        log_fp = None

    def log(msg: str):
        safe = msg
        try:
            print(safe)
        except Exception:
            safe = safe.encode("ascii", "replace").decode()
            print(safe)
        if log_fp is not None:
            log_fp.write(safe + "\n")
            log_fp.flush()

    input_afm_dir = None
    if args.input_afm_dir:
        input_afm_dir = Path(args.input_afm_dir)
    else:
        input_afm_dir = codex_root / "codex" / "quantum_imaging" / "input_afm" / "v4_7"

    try:
        log("QIM v4.7 Living Engine starting...")
        log(f"  codex_root : {codex_root}")
        log(f"  state_dir  : {state_dir}")
        log(f"  visuals_dir: {visuals_dir}")
        log(f"  ledger_dir : {ledger_dir}")
        log(f"  input_afm  : {input_afm_dir}")

        # 1) load or synthesize base volume
        vol3d, used_synth, png_count = load_volume_from_afm(input_afm_dir)
        log(f"Loaded base volume: shape={vol3d.shape}, used_synthetic={used_synth}, png_count={png_count}")

        # 2) build 4D field
        V = build_4d_field(vol3d, T=40)
        log(f"Built 4D field with shape={V.shape}")

        # 3) dphi + metrics
        dphi = compute_dphi_4d(V)
        log("Computed dphi field over 4D volume.")

        metrics = compute_metrics(V, dphi)
        harmonics = compute_harmonics(dphi)
        log(f"Global triad: {metrics.get('triad',{})}")
        log(f"H19 dphi_global: {metrics.get('dphi_global',0.0)}")
        log(f"Cusp lambda_eff: {metrics.get('lambda_eff',0.0)}, barrier_scale: {metrics.get('barrier_scale',0.0)}")
        log(f"Harmonics: {harmonics}")

        # 4) prior states
        prior_path, prior_C = scan_prior_states(codex_root)
        log(f"Prior state path: {prior_path}")
        log(f"Prior triad C: {prior_C}")

        # 5) visuals
        ts_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = f"qim_v4_7_living_{ts_tag}"
        visuals = save_visuals(V, dphi, visuals_dir, prefix)
        log(f"Visuals written: {visuals}")

        # 6) state + ledger
        state_path, ledger_path = write_state_and_ledger(
            codex_root,
            state_dir,
            ledger_dir,
            str(input_afm_dir),
            used_synth,
            png_count,
            V,
            dphi,
            metrics,
            harmonics,
            visuals,
            prior_path,
            prior_C,
        )
        log(f"State JSON written -> {state_path}")
        log(f"Ledger appended    -> {ledger_path}")

        # 7) next engine stub
        triad = metrics.get("triad", {})
        C_now = f(triad.get("C", 0.0))
        C_prev = f(prior_C) if prior_C is not None else None
        if C_prev is None or C_prev <= 0.0:
            C_gain = None
        else:
            C_gain = (C_now - C_prev) / C_prev
        stub_path = write_next_engine_stub(codex_root, C_gain)
        log(f"Next engine stub written -> {stub_path}")

        log("QIM v4.7 Living Engine run complete.")
        if log_fp is not None:
            log_fp.close()
        sys.exit(0)

    except Exception as e:
        err_msg = "QIM v4.7 Living Engine encountered an error: " + repr(e)
        print(err_msg, file=sys.stderr)
        traceback.print_exc()
        if log_fp is not None:
            log_fp.write(err_msg + "\n")
            log_fp.write(traceback.format_exc() + "\n")
            log_fp.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
