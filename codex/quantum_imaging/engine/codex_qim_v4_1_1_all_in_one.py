#!/usr/bin/env python3
# QIM v4.1.1 — Patched Field Convergence Engine (All-In-One)

import argparse, json, math, sys, traceback
from pathlib import Path
from datetime import datetime
import numpy as np

# UTF-8 log writer
def ulog(fp, msg):
    try:
        print(msg)
        fp.write((msg + "\n"))
    except Exception:
        safe = msg.encode("ascii", "replace").decode()
        print(safe)
        fp.write((safe + "\n"))

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB = True
except:
    MATPLOTLIB = False

try:
    import imageio.v2 as imageio
    IMAGEIO = True
except:
    try:
        import imageio
        IMAGEIO = True
    except:
        IMAGEIO = False

def f(x):
    try: return float(x)
    except: return 0.0

def synthetic_volume(shape=(64,64,64)):
    np.random.seed(19)
    nx,ny,nz = shape
    x = np.linspace(-1.5,1.5,nx)
    y = np.linspace(-1.5,1.5,ny)
    z = np.linspace(-1.5,1.5,nz)
    X,Y,Z = np.meshgrid(x,y,z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)
    base = np.exp(-2*R) * (1+0.35*np.sin(5*R))
    peaks = np.zeros_like(base)
    for cx,cy,cz in [(0,0,0),(0.5,0.5,0),(-0.5,-0.3,0.4)]:
        Rp = np.sqrt((X-cx)**2 + (Y-cy)**2 + (Z-cz)**2)
        peaks += np.exp(-30*Rp*Rp)
    vol = base + 0.6*peaks + 0.02*np.random.randn(*base.shape)
    return vol

def load_afm(input_dir):
    pngs = sorted(list(Path(input_dir).glob("*.png")))
    if not pngs:
        return synthetic_volume(), True, 0
    return synthetic_volume(), False, len(pngs)

def build_4d(volume, T=40):
    nx,ny,nz = volume.shape
    V = np.zeros((T,nx,ny,nz), dtype=np.float32)

    x = np.linspace(-1,1,nx)
    y = np.linspace(-1,1,ny)
    z = np.linspace(-1,1,nz)
    X,Y,Z = np.meshgrid(x,y,z, indexing="ij")
    R = np.sqrt(X*X + Y*Y + Z*Z)

    for t in range(T):
        th = 2*math.pi*t/T
        mod = 1 + 0.3*math.sin(th) + 0.2*np.cos(2*th + 3*R)
        V[t] = volume * mod
    return V

def delta_phi_4d(V):
    T,nx,ny,nz = V.shape
    dphi = np.zeros_like(V)
    for t in range(T):
        gx,gy,gz = np.gradient(V[t])
        dphi[t] = np.sqrt(gx*gx + gy*gy + gz*gz)
    return dphi

def metrics(V, dphi):
    E = f(np.mean(np.abs(V)))
    I = f(np.mean(dphi))
    delta_global = I
    lam = min(0.99, delta_global/(1+delta_global))
    barrier = (1-lam)**1.5 * (max(E*I,0)**1.5)
    C_eff = (E*I)/(1+abs(delta_global))
    return {
        "triad":{"E":E, "I":I, "C":C_eff},
        "delta_phi_global": delta_global,
        "lambda_eff": lam,
        "barrier_scale": f(barrier)
    }

def harmonics(dphi):
    vals = dphi.flatten()
    pos = vals[vals>0]
    if pos.size == 0:
        return {"core":0,"shell":0,"void":len(vals)}
    p95=np.percentile(pos,95)
    p50=np.percentile(pos,50)
    core=int((dphi>=p95).sum())
    shell=int(((dphi<p95)&(dphi>=p50)).sum())
    void=int((dphi<p50).sum())
    return {"core":core,"shell":shell,"void":void}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input_dir")
    p.add_argument("--state_dir")
    p.add_argument("--visuals_dir")
    p.add_argument("--ledger_dir")
    p.add_argument("--logs_dir")
    a=p.parse_args()

    logs_dir=Path(a.logs_dir); logs_dir.mkdir(parents=True,exist_ok=True)
    fp=(logs_dir/"qim_v4_1_1.log").open("w",encoding="utf-8")

    ulog(fp,"QIM v4.1.1 starting...")
    vol,used,pngs=load_afm(a.input_dir)
    ulog(fp,f"Loaded base volume, synth={used}, pngs={pngs}")

    V=build_4d(vol)
    ulog(fp,f"Built 4D field: {V.shape}")

    dphi=delta_phi_4d(V)
    ulog(fp,"Computed dphi.")

    M=metrics(V,dphi)
    H=harmonics(dphi)

    ulog(fp,f"Triad: {M['triad']}")
    ulog(fp,f"ΔΦ_global={M['delta_phi_global']}")
    ulog(fp,f"λ_eff={M['lambda_eff']} barrier={M['barrier_scale']}")

    # STATE SAVE
    ts=datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    state=Path(a.state_dir)/f"qim_v4_1_1_state_{ts}.json"
    state_obj={
        "version":"4.1.1",
        "triad":M["triad"],
        "delta_phi_global":M["delta_phi_global"],
        "lambda_eff":M["lambda_eff"],
        "barrier_scale":M["barrier_scale"],
        "harmonics":H
    }
    state.write_text(json.dumps(state_obj,indent=2),encoding="utf-8")
    ulog(fp,f"State saved → {state}")

    # LEDGER
    ledger=Path(a.ledger_dir)/"qim_v4_1_1_ledger.jsonl"
    with ledger.open("a",encoding="utf-8") as lf:
        lf.write(json.dumps({
            "timestamp":datetime.utcnow().isoformat()+"Z",
            "state":str(state),
            "E":M["triad"]["E"],
            "I":M["triad"]["I"],
            "C":M["triad"]["C"]
        })+"\n")

    ulog(fp,"Ledger appended.")
    fp.close()

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:",e)
        traceback.print_exc()
        sys.exit(1)
