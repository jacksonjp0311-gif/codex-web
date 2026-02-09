#!/usr/bin/env python3
import numpy as np, json, time, os
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

def main(root, afm_path, qcx_npy, qcx_json, state_dir, visual_dir, ledger_dir):
    # Load AFM cube
    afm = np.load(afm_path)

    # Try QCX .npy first
    field_qcx = None
    if qcx_npy and os.path.exists(qcx_npy):
        field_qcx = np.load(qcx_npy)

    # If no .npy, try JSON
    if field_qcx is None and qcx_json and os.path.exists(qcx_json):
        with open(qcx_json) as f:
            data = json.load(f)
        for k in ["field","dphi","qcx_field","crystal"]:
            if k in data:
                field_qcx = np.array(data[k],dtype="float32")
                break

    # If still none → fail
    if field_qcx is None:
        raise ValueError("No QCX Δφ field found in .npy or JSON.")

    # Resize AFM to match QCX spatial dims
    # assume field_qcx shape = (T,X,Y,Z) or (X,Y,Z)
    if field_qcx.ndim == 4:
        T,X,Y,Z = field_qcx.shape
        afm_resized = gaussian_filter(afm, sigma=1.0)
        afm_resized = (afm_resized - afm_resized.min())/(afm_resized.max()-afm_resized.min()+1e-9)
        afm_resized = afm_resized[:X,:Y,:Z]
    else:
        X,Y,Z = field_qcx.shape
        afm_resized = afm[:X,:Y,:Z]

    # Build QIM Δφ entanglement
    dphi = np.abs(field_qcx - field_qcx.mean())
    omega = 1/(1+np.abs(dphi))
    ent = 0.5*dphi + 0.5*afm_resized

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Visuals
    central = ent[ent.shape[0]//2] if ent.ndim==4 else ent
    maxproj = ent.max(axis=0)

    plt.imshow(central, cmap="inferno")
    plt.colorbar()
    plt.savefig(Path(visual_dir)/f"qim6_4_central_{timestamp}.png")
    plt.close()

    plt.imshow(maxproj, cmap="inferno")
    plt.colorbar()
    plt.savefig(Path(visual_dir)/f"qim6_4_maxproj_{timestamp}.png")
    plt.close()

    # Metrics
    state = {
        "version":"6.4",
        "timestamp":timestamp,
        "metrics":{
            "dphi_global":float(dphi.mean()),
            "omega_mean":float(omega.mean()),
            "omega_std":float(omega.std()),
            "entanglement_energy":float(ent.mean())
        }
    }

    # Save state
    out_state = Path(state_dir)/f"qim_v6_4_state_{timestamp}.json"
    with open(out_state,"w") as f:
        json.dump(state,f,indent=2)

    # Ledger
    with open(Path(ledger_dir)/"qim_v6_4_ledger.jsonl","a") as f:
        f.write(json.dumps(state)+"\n")

if __name__ == "__main__":
    import argparse
    P = argparse.ArgumentParser()
    P.add_argument("--root")
    P.add_argument("--afm")
    P.add_argument("--qcx_npy")
    P.add_argument("--qcx_json")
    P.add_argument("--state")
    P.add_argument("--visuals")
    P.add_argument("--ledger")
    args = P.parse_args()
    main(args.root,args.afm,args.qcx_npy,args.qcx_json,args.state,args.visuals,args.ledger)
