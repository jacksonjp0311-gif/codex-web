#!/usr/bin/env python3
import numpy as np, json, math, traceback, sys
from pathlib import Path
from datetime import datetime, timezone
import matplotlib.pyplot as plt

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def load_afm(path, target=64):
    arr = np.load(path)
    if arr.ndim == 2:
        arr = np.stack([arr]*target,axis=-1)
    if arr.ndim == 4:
        arr = arr[arr.shape[0]//2]
    arr = arr.astype(np.float32)
    m = arr.max()-arr.min()
    if m>0: arr = (arr-arr.min())/m
    return arr

from scipy.ndimage import zoom

def super_resolve(vol, factor):
    scale = (factor, factor, factor)
    hi = zoom(vol, scale, order=1)  # safe linear interpolation
    hi = hi.astype(np.float32)
    return hi

def build_4d(vol,T=40):
    T0,nx,ny,nz = T,*vol.shape
    V = np.zeros((T0,nx,ny,nz),dtype=np.float32)
    x = np.linspace(-1,1,nx)
    y = np.linspace(-1,1,ny)
    z = np.linspace(-1,1,nz)
    X,Y,Z = np.meshgrid(x,y,z,indexing="ij")
    R = np.sqrt(X*X+Y*Y+Z*Z)
    for t in range(T0):
        th = 2*math.pi*t/T0
        mod = 1+0.3*np.sin(th)+0.22*np.cos(2*th+3*R)
        V[t]=vol*mod
    return V

def dphi_4d(V):
    T,nx,ny,nz=V.shape
    out=np.zeros_like(V)
    for t in range(T):
        gx,gy,gz=np.gradient(V[t])
        out[t]=np.sqrt(gx*gx+gy*gy+gz*gz)
    return out

def omega(dphi): return 1/(1+np.abs(dphi))

def fractal_dim(vol):
    data = (vol>np.median(vol)).astype(np.float32)
    counts=[]
    for k in [1,2,4,8,16]:
        try:
            blk = data[::k,::k,::k]
            counts.append(np.sum(blk>0))
        except: pass
    if len(counts)<2: return 2.0
    logs = np.log(np.array(counts)+1e-9)
    ks = np.log(1/np.array([1,2,4,8,16])[:len(counts)])
    p=np.polyfit(ks,logs,1)
    return float(abs(p[0]))

def write_img(path,arr,title):
    plt.figure()
    plt.imshow(arr,origin="lower")
    plt.title(title)
    plt.colorbar()
    plt.savefig(path,bbox_inches="tight")
    plt.close()

def main(root,state_d,vis_d,ledger_d,log_d,afm_p,superres):
    afm = load_afm(afm_p)
    hi = super_resolve(afm,superres)
    V = build_4d(hi,T=40)
    dphi = dphi_4d(V)
    Ω = omega(dphi)
    fd = fractal_dim(hi)

    E=float(np.mean(np.abs(V)))
    I=float(np.mean(dphi))
    C = (E*I)/(1+abs(I))
    lam=min(0.99,I/(1+I))
    bs=(1-lam)**1.5*(max(E*I,0)**1.5)
    om=float(np.mean(Ω))
    omstd=float(np.std(Ω))
    curv=float(np.mean(np.abs(dphi-np.mean(dphi))))

    tmid=20; zmid=hi.shape[2]//2
    dphi_c = dphi[tmid,:,:,zmid]
    maxp = dphi.max(axis=0).max(axis=2)
    omegam = Ω.max(axis=0).max(axis=2)
    energy_t = np.mean(np.abs(V),axis=(1,2,3))

    vs={}
    p1=Path(vis_d)/"qim_v6_5_dphi_central.png"
    write_img(p1,dphi_c,"Δφ central"); vs["dphi_central"]=str(p1)
    p2=Path(vis_d)/"qim_v6_5_dphi_maxproj.png"
    write_img(p2,maxp,"Δφ maxproj"); vs["dphi_maxproj"]=str(p2)
    p3=Path(vis_d)/"qim_v6_5_omega_maxproj.png"
    write_img(p3,omegam,"Ω maxproj"); vs["omega_maxproj"]=str(p3)

    plt.figure(); plt.plot(energy_t); plt.title("Resonance"); 
    p4=Path(vis_d)/"qim_v6_5_resonance_curve.png"
    plt.savefig(p4,bbox_inches="tight"); plt.close()
    vs["resonance_curve"]=str(p4)

    ts=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sp=Path(state_d)/f"qim_v6_5_state_{ts}.json"
    st={
        "protocol":"CodexQIMAFMSuperRes",
        "version":"6.5",
        "timestamp":now(),
        "mode":"afm-superres",
        "superres_factor":superres,
        "shape_4d":[40]+list(hi.shape),
        "metrics":{
            "triad":{"E":E,"I":I,"C":C},
            "H19_dphi_global":I,
            "lambda_eff":lam,
            "barrier_scale":bs,
            "omega_mean":om,
            "omega_std":omstd,
            "curvature_proxy":curv,
            "fractal_dim_H16B":fd
        },
        "codex":{
            "H_layers":{"H7":0.7,"H7B":"ΔΦ Cusp v2.8",
                        "H16B":"fractal geometry",
                        "H19":"global Δφ",
                        "H31":"1:9:10"},
            "laws":{"universal_truth":"C=(E*I)/(1+|ΔΦ|)",
                    "cusp_v2_8":"ΔV∝(1-λ)^(3/2)(EI)^(3/2)",
                    "error_geometry":"Ω=1/(1+|ΔΦ|)"}
        },
        "visuals":vs
    }
    sp.write_text(json.dumps(st,indent=2))

    lp=Path(ledger_d)/"qim_v6_5_ledger.jsonl"
    with open(lp,"a",encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp":now(),
            "mode":"afm-superres",
            "state_file":str(sp),
            "E":E,"I":I,"C":C,
            "lambda_eff":lam,
            "omega_mean":om,
            "curvature_proxy":curv,
            "fractal_dim_H16B":fd
        })+"\n")

if __name__=="__main__":
    root=sys.argv[1]; state=sys.argv[2]; vis=sys.argv[3]
    led=sys.argv[4]; log=sys.argv[5]
    afm=sys.argv[6]; sr=int(sys.argv[7])
    main(root,state,vis,led,log,afm,sr)

