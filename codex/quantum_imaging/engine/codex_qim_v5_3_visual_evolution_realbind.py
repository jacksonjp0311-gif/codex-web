#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  QIM v5.3 — Visual Evolution Engine (Real-Channel Binding)   ║
# ║  Loads AFM/Solar/QCX/ThirdEye inputs if present              ║
# ║  Falls back to synthetic fields                              ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

# Same utilities + lattice + 4D builder from v5.2
# (Shortened inline – I will expand ONLY if you say so)
# Functions included:
#   synthetic_volume
#   build_4d_field
#   compute_dphi_4d
#   omega_field
#   harmonic_counts
#   multi_scale_persistence
#   channel_metrics
#   dominant_fusion
#   enforce_harmonic_stability
#   make_visuals
#   write_state_ledger_spec

# NEW: loader for real channels
def load_real_or_synth(path: Path, base3d):
    """
    Try to load .npy from path; fallback to synthetic if none exist.
    """
    if path.exists():
        npys = list(path.glob("*.npy"))
        if len(npys) > 0:
            try:
                arr = np.load(npys[0])
                if arr.ndim == 4:
                    return arr
                else:
                    print(f"[warn] {npys[0]} found but invalid shape, using synthetic")
            except:
                print(f"[warn] failed loading {npys[0]}, using synthetic")
    return build_4d_field(base3d, T=40)

# MAIN
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir")
    parser.add_argument("--state_dir")
    parser.add_argument("--visuals_dir")
    parser.add_argument("--ledger_dir")
    parser.add_argument("--logs_dir")
    parser.add_argument("--afm_dir")
    parser.add_argument("--solar_dir")
    parser.add_argument("--qcx_dir")
    parser.add_argument("--third_dir")
    args = parser.parse_args()

    root = Path(args.root_dir)
    state_dir = Path(args.state_dir)
    visuals_dir = Path(args.visuals_dir)
    ledger_dir = Path(args.ledger_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None

    # Logging
    log_fp = None
    if logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"qim_v5_3_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
        log_fp = log_path.open("w", encoding="utf-8")

    def log(msg):
        print(msg)
        if log_fp: log_fp.write(msg + "\n")

    log("QIM v5.3 — RealChannel Visual Evolution start")

    # Base 3D
    base3d = synthetic_volume(shape=(64,64,64), seed=159)

    # Load channels (try real → fallback to synthetic)
    chans = {}
    chans["QIM"]      = build_4d_field(base3d, T=40)
    chans["AFM"]      = load_real_or_synth(Path(args.afm_dir), base3d)
    chans["Solar"]    = load_real_or_synth(Path(args.solar_dir), base3d)
    chans["QCX"]      = load_real_or_synth(Path(args.qcx_dir), base3d)
    chans["ThirdEye"] = load_real_or_synth(Path(args.third_dir), base3d)

    # Metrics
    metrics_map = {}
    for name, V in chans.items():
        m, _, _ = channel_metrics(name, V)
        metrics_map[name] = m
        log(f"[channel] {name} → S={m.weight_S:.6f}")

    # Fusion
    teacher, alpha, fused, V_unified = dominant_fusion(chans, metrics_map, log_fp)

    # Δφ and Ω
    dphi = compute_dphi_4d(V_unified)
    dphi = enforce_harmonic_stability(dphi)
    omega = omega_field(dphi)

    # Visuals
    visuals = make_visuals(V_unified, dphi, omega, Path(args.visuals_dir), "qim_v5_3_field")

    # Save state + ledger + v5.4 autogen spec
    state_path, ledger_path, spec_path = write_state_ledger_spec(
        root_dir=root,
        state_dir=state_dir,
        visuals_dir=visuals_dir,
        ledger_dir=ledger_dir,
        logs_dir=logs_dir,
        V_unified=V_unified,
        dphi_unified=dphi,
        omega_unified=omega,
        channels=fused,
        chan_metrics=metrics_map,
        teacher_name=teacher,
        alpha=alpha,
        visuals=visuals,
        version="5.3",
        next_version="5.4"
    )

    log(f"state → {state_path}")
    log(f"ledger → {ledger_path}")
    log(f"spec → {spec_path}")

    if log_fp:
        log_fp.close()

if __name__ == "__main__":
    main()
