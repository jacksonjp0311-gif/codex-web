#!/usr/bin/env python3
import argparse, json, numpy as np, os, time
from pathlib import Path
from scipy.ndimage import gaussian_filter

def load_afm_cubes(path):
    files = list(Path(path).glob("*.npy")) + list(Path(path).glob("*.npz"))
    if len(files) == 0:
        raise ValueError("No AFM cubes found — required for QCX v10.4 physical mode.")
    vols = []
    for f in files:
        arr = np.load(f)
        if isinstance(arr, np.lib.npyio.NpzFile):
            for k in arr.files:
                vols.append(arr[k])
        else:
            vols.append(arr)
    return vols

def box_counting_dim(slice2d):
    binary = slice2d > slice2d.mean()
    dims = []
    sizes = [2,4,8,16,32]
    for s in sizes:
        h = int(np.ceil(binary.shape[0] / s))
        w = int(np.ceil(binary.shape[1] / s))
        blocks = binary.reshape(h, s, w, s).sum(axis=(1,3))
        dims.append((s, np.count_nonzero(blocks)))
    xs = np.log([x[0] for x in dims])
    ys = np.log([x[1] for x in dims])
    p = np.polyfit(xs, ys, 1)
    return float(-p[0])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--visuals", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--afm_dir", required=True)
    args = parser.parse_args()

    afm_vols = load_afm_cubes(args.afm_dir)

    # Use average AFM cube as binding potential
    base = np.mean(np.stack(afm_vols, axis=0), axis=0)
    base = gaussian_filter(base, sigma=1.0)
    base = (base - base.min()) / (base.max() - base.min() + 1e-9)

    T = 40
    field = []
    for t in range(T):
        phase = 0.02 * np.sin(t/6.0)
        slice3d = base + phase
        field.append(slice3d)
    field = np.array(field)

    dphi = np.abs(field - field.mean())
    omega = 1.0 / (1.0 + dphi)

    maxproj = dphi.max(axis=0)
    central = dphi[T//2]

    fractal = box_counting_dim(central)

    core  = np.count_nonzero(dphi <  0.33*dphi.max())
    shell = np.count_nonzero((dphi >= 0.33*dphi.max()) & (dphi < 0.66*dphi.max()))
    void  = np.count_nonzero(dphi >= 0.66*dphi.max())

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    state_file = Path(args.state)/f"qcx_v10_4_state_{timestamp}.json"

    state = {
        "protocol": "CodexQCXPhysicalAFMFusion",
        "version": "10.4",
        "timestamp": timestamp,
        "afm_cubes_loaded": len(afm_vols),
        "metrics": {
            "dphi_global": float(dphi.mean()),
            "omega_mean":  float(omega.mean()),
            "omega_std":   float(omega.std()),
            "fractal_dim_H16B": fractal,
            "harmonics": {
                "core": int(core),
                "shell": int(shell),
                "void": int(void)
            }
        }
    }
    with open(state_file, "w") as f: json.dump(state, f, indent=2)

    ledger_file = Path(args.ledger)/"qcx_v10_4_ledger.jsonl"
    with open(ledger_file, "a") as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "state_file": str(state_file),
            "afm_cubes": len(afm_vols),
            "dphi_global": float(dphi.mean()),
            "omega_mean": float(omega.mean()),
            "fractal_dim_H16B": fractal,
            "core": int(core), "shell": int(shell), "void": int(void)
        })+"\n")

    # Write visuals
    import matplotlib.pyplot as plt
    plt.imshow(central, cmap="viridis"); 
    plt.colorbar(); 
    plt.savefig(Path(args.visuals)/f"central_{timestamp}.png"); plt.close()

    plt.imshow(maxproj, cmap="viridis");
    plt.colorbar();
    plt.savefig(Path(args.visuals)/f"maxproj_{timestamp}.png"); plt.close()

if __name__ == "__main__":
    main()
