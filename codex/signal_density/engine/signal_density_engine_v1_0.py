#!/usr/bin/env python3
import json, math, sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt

def iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def build_field(nx=64, ny=64, nz=64, T=32):
    x = np.linspace(-1,1,nx)
    y = np.linspace(-1,1,ny)
    z = np.linspace(-1,1,nz)
    X,Y,Z = np.meshgrid(x,y,z,indexing="ij")
    R = np.sqrt(X*X+Y*Y+Z*Z)
    V = np.zeros((T,nx,ny,nz),dtype=np.float32)
    for t in range(T):
        θ = 2*math.pi*t/T
        V[t] = np.sin(θ + 3*R) * np.exp(-R*1.5)
    return V

def dphi(V):
    out = np.zeros_like(V)
    for t in range(V.shape[0]):
        gx,gy,gz = np.gradient(V[t])
        out[t] = np.sqrt(gx*gx+gy*gy+gz*gz)
    return out

def omega(dφ):
    return 1.0/(1.0+np.abs(dφ))

def main(root,state,vis,ledger,logs,superres,noise):
    state = Path(state); vis = Path(vis); ledger = Path(ledger)
    state.mkdir(exist_ok=True); vis.mkdir(exist_ok=True); ledger.mkdir(exist_ok=True)

    V = build_field()
    Δφ = dphi(V)
    Ω  = omega(Δφ)

    σ = noise*np.std(Δφ)
    Δφn = Δφ + np.random.normal(0,σ,Δφ.shape)
    Ωn  = omega(Δφn)

    signal_density = float(np.mean(Ω * Δφ))
    omega_diff = float(np.mean(np.abs(Ωn-Ω)))
    noise_immunity = 1.0/(1.0+omega_diff)

    tmid = V.shape[0]//2
    zmid = V.shape[3]//2

    plt.imshow(Δφ[tmid,:,:,zmid]); plt.colorbar()
    p = vis/"signal_density_dphi.png"
    plt.savefig(p); plt.close()

    ts = iso()
    state_obj = {
        "module": "SignalDensity",
        "version": "1.0",
        "timestamp": ts,
        "metrics": {
            "signal_density": signal_density,
            "noise_immunity": noise_immunity,
            "omega_diff": omega_diff
        },
        "codex": {
            "H7": 0.70,
            "H19": "global ΔΦ integration",
            "H20": "Ω-basin invariance",
            "H44": "boundary algebra extremal survival"
        }
    }

    sf = state/f"signal_density_state_{ts.replace(':','')}.json"
    sf.write_text(json.dumps(state_obj,indent=2))

    with (ledger/"signal_density_ledger.jsonl").open("a") as lf:
        lf.write(json.dumps(state_obj)+"\n")

if __name__ == "__main__":
    main(*sys.argv[1:])
