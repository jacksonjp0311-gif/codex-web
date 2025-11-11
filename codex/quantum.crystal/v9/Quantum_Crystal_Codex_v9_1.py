#!/usr/bin/env python3
import os
import json
"""
quantum_crystal_codex_v9_1.py
Quantum Crystal Codex v9.1 — Resonant Reawakening Sequence

Improvements over v9:
    - energy scaling tuned (t_hop, t_z)
 - resonance Phi uses direct normalized product (no log)
 - PID-enabled alpha adaptation (default ON)
 - higher alpha_I and alpha_C initial values
 - Kuramoto phase lag and small initial phase offsets
 - extended tmax and smaller dt_min for finer late-time resolution
 - ensemble and diagnostics preserved

Run: python quantum_crystal_codex_v9_1.py
"""
import os, json, math, hashlib, datetime, time
from dataclasses import dataclass
import numpy as np
import scipy.linalg as la
from scipy.sparse import coo_matrix, diags
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# ---------------------------
# Paths
# ---------------------------
CODEX_ROOT = r"C:\Users\jacks\OneDrive\Desktop\Codex Web"
OUT_ROOT = os.path.join(CODEX_ROOT, "codex", "quantum.crystal", "v9")
STATE_DIR = os.path.join(OUT_ROOT, "state")
VIS_DIR = os.path.join(OUT_ROOT, "visuals")
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(VIS_DIR, exist_ok=True)

# ---------------------------
# Config (resonant reawakening defaults)
# ---------------------------
cfg = {
    "version": "v9.1",
    # lattice
    "Lx": 8, "Ly": 8, "Lz": 1,            # N=64
    # energy tweaks
    "t_hop": 0.90, "t_z": 0.40,
    # disorder oscillation
    "W_base": 1.0, "W_amp": 1.0, "W_period": 60.0,
    # triadic alphas (stronger I/C)
    "alpha_E_init": 0.02, "alpha_I_init": 0.04, "alpha_C_init": 0.04,
    "eta_E": 0.004, "eta_I": 0.006, "eta_C": 0.006,
    "wE": 0.35, "wI": 0.33, "wC": 0.32,
    "Phi_target": 6.0, "H7": 0.15,
    # time integration
    "timesteps": 301, "tmax": 12.0,
    "seed_base": 201, "ensemble_size": 5,
    "dt": 0.04, "dt_min": 5e-5, "dt_max": 0.2,
    "rtol": 1e-3, "atol": 1e-8,
    # PID control enabled
    "pid_mode": True,
    "pid_params": {"Kp": 0.02, "Ki": 0.002, "Kd": 0.0005}











,
    # kuramoto tweaks
    "kuramoto_steps": 150, "kuramoto_beta": 3.0,
    "kuramoto_phase_lag": math.pi/6,
    "initial_phase_jitter": 0.1 * math.pi,
    # limits and safety
    "alpha_max": 0.8, "alpha_min": 1e-6,
    "alpha_smooth_lambda": 0.06,
    "alpha_anneal_factor": 0.995,
    # outputs
    "timeseries_png": True,
    "ensemble_parallel": False,
    "max_runtime_seconds": None
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
np.random.seed(cfg["seed_base"])
Lx, Ly, Lz = cfg["Lx"], cfg["Ly"], cfg["Lz"]
N = Lx * Ly * Lz
times = np.linspace(0.0, cfg["tmax"], cfg["timesteps"])
# ---------------------------
# Helpers
# ---------------------------
def idx3(x,y,z):
    return (x % Lx) + (y % Ly) * Lx + (z % Lz) * (Lx * Ly)

def neighbors_3d(i):
    z = i // (Lx*Ly)
    rem = i % (Lx*Ly)
    y = rem // Lx
    x = rem % Lx
    nbrs=[]
    for dx,dy,dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
        nx,ny,nz = x+dx, y+dy, z+dz
        nx%=Lx; ny%=Ly; nz%=Lz
        nbrs.append(idx3(nx,ny,nz))
    return nbrs

def build_H_dense(t_hop, t_z, disorder):
    H = np.zeros((N,N), dtype=np.complex128)
    for i in range(N):
        for j in neighbors_3d(i):
            amp = -t_z if abs(i-j) >= (Lx*Ly) else -t_hop
            H[i,j] = amp
    diag = np.random.uniform(-disorder, disorder, N)
    H[np.diag_indices(N)] += diag
    return H

def shannon_entropy(psi):
    p = np.abs(psi)**2
    s = p.sum()
    if s == 0: return 0.0
    p = p/s
    ppos = p[p>0]
    return float(-np.sum(ppos * np.log2(ppos)))

def coherence_metric(psi):
    return float(np.abs(np.sum(psi)) / math.sqrt(len(psi)))

def resonance_phi_direct(E, I, C, psi, eps=1e-12):
    p = np.abs(psi)**2
    varp = float(np.var(p))
    denom = (varp + eps)
    phase_var = float(np.var(np.angle(psi[p>eps]))) if np.any(p>eps) else 0.0
    damping = math.exp(-phase_var / math.pi)
    return float((E * I * C) / denom * damping)

# ---------------------------
# Integrator (IF-RK4)
# ---------------------------
def compute_eig(H):
    evals, evecs = la.eigh(H)
    return evals, evecs

def expL_action(evals, evecs, tau, vec):
    return evecs @ (np.exp(-1j * evals * tau) * (evecs.conj().T @ vec))

def if_rk4_step(psi, H, dt, alpha_total):
        evals, evecs = compute_eig(H)
        V = evecs; Vh = V.conj().T
            def expL(tau, v):
        return V @ (np.exp(-1j * evals * tau) * (Vh @ v))
            def N(vec):
        E_loc = float(np.real(np.vdot(vec, H.dot(vec))))
        I_loc = shannon_entropy(vec)
        C_loc = coherence_metric(vec)
        Phi_loc = resonance_phi_direct(E_loc, I_loc, C_loc, vec)
        return -1j * alpha_total * Phi_loc * vec, (E_loc, I_loc, C_loc, Phi_loc)
        N1, m1 = N(psi)
        a = expL(dt/2.0, psi + (dt/2.0) * N1)
        N2, m2 = N(a)
        b = expL(dt/2.0, psi + (dt/2.0) * N2)
        N3, m3 = N(b)
        c = expL(dt, psi + dt * N3)
        N4, m4 = N(c)
        psi_next = expL(dt, psi) + (dt/6.0) * (expL(dt, N1) + 2*expL(dt, N2) + 2*expL(dt, N3) + expL(dt, N4))
        psi_next = psi_next / np.linalg.norm(psi_next)
        E_next = float(np.real(np.vdot(psi_next, H.dot(psi_next))))
        I_next = shannon_entropy(psi_next)
        C_next = coherence_metric(psi_next)
        Phi_next = resonance_phi_direct(E_next, I_next, C_next, psi_next)
        return psi_next, (E_next, I_next, C_next, Phi_next)
        # ---------------------------
        # Kuramoto mirror with phase lag + initial jitter
        # ---------------------------
def kuramoto_quantum(psi, K_base=1.0, steps=150, dt_k=0.02, beta=3.0, phase_lag=0.0, jitter=0.0):
    w = np.abs(np.outer(psi, psi.conj()))
    wmax = np.max(w) if np.max(w)>0 else 1.0
    K_mat = K_base * (1.0 + beta * (w / wmax))
    theta = 2*np.pi*np.random.rand(N) + np.random.uniform(-jitter, jitter, size=N)
    omega = np.random.normal(0, 0.1, N)
    r_hist = []
    for _ in range(steps):
    sin_terms = np.sin(theta[None,:] - theta[:,None] - phase_lag)
        coupling = np.sum(K_mat * sin_terms, axis=1)
        theta += dt_k * (omega + coupling)
        r_hist.append(float(np.abs(np.mean(np.exp(1j*theta)))))
    return np.array(r_hist)

# ---------------------------
# Alpha adapters (PID with smoothing)
# ---------------------------
@dataclass
class PIDState:
    integ_E: float = 0.0
    integ_I: float = 0.0
    integ_C: float = 0.0
    prev_err_E: float = 0.0
    prev_err_I: float = 0.0
    prev_err_C: float = 0.0

def adapt_alphas_PID(alpha_E, alpha_I, alpha_C, Phi_recent, C_recent, pid_state):
    pid = cfg["pid_params"]
    err_E = (Phi_recent - cfg["Phi_target"])
    err_I = (C_recent - cfg["H7"])
    err_C = (Phi_recent * C_recent) - (cfg["Phi_target"] * cfg["H7"])
    pid_state.integ_E += err_E
    pid_state.integ_I += err_I
    pid_state.integ_C += err_C
    dE = err_E - pid_state.prev_err_E
    dI = err_I - pid_state.prev_err_I
    dC = err_C - pid_state.prev_err_C
    pid_state.prev_err_E = err_E
    pid_state.prev_err_I = err_I
    pid_state.prev_err_C = err_C
    upd_E = pid["Kp"]*err_E + pid["Ki"]*pid_state.integ_E + pid["Kd"]*dE
    upd_I = pid["Kp"]*err_I + pid["Ki"]*pid_state.integ_I + pid["Kd"]*dI
    upd_C = pid["Kp"]*err_C + pid["Ki"]*pid_state.integ_C + pid["Kd"]*dC
    alpha_E_new = alpha_E + cfg["eta_E"] * upd_E
    alpha_I_new = alpha_I + cfg["eta_I"] * upd_I
    alpha_C_new = alpha_C + cfg["eta_C"] * upd_C
    lam = cfg["alpha_smooth_lambda"]
    alpha_E_sm = (1-lam)*alpha_E + lam*alpha_E_new
    alpha_I_sm = (1-lam)*alpha_I + lam*alpha_I_new
    alpha_C_sm = (1-lam)*alpha_C + lam*alpha_C_new
    alpha_E_sm = float(max(cfg["alpha_min"], min(cfg["alpha_max"], alpha_E_sm)))
    alpha_I_sm = float(max(cfg["alpha_min"], min(cfg["alpha_max"], alpha_I_sm)))
    alpha_C_sm = float(max(cfg["alpha_min"], min(cfg["alpha_max"], alpha_C_sm)))
    return alpha_E_sm, alpha_I_sm, alpha_C_sm

def combine_alpha(alpha_E, alpha_I, alpha_C):
    return cfg["wE"]*alpha_E + cfg["wI"]*alpha_I + cfg["wC"]*alpha_C

# ---------------------------
# Single-run function
# ---------------------------
def run_single(seed:int, run_id:int, save_png=True):
    np.random.seed(seed)
    psi = np.zeros(N, dtype=np.complex128)
    psi[N//2] = 1.0 + 0j
    psi *= np.exp(1j * np.random.uniform(-cfg["initial_phase_jitter"], cfg["initial_phase_jitter"], size=psi.shape))
    psi /= np.linalg.norm(psi)
    alpha_E = cfg["alpha_E_init"]; alpha_I = cfg["alpha_I_init"]; alpha_C = cfg["alpha_C_init"]
    alpha_total = combine_alpha(alpha_E, alpha_I, alpha_C)
    pid_state = PIDState()
    T=[]; Wt=[]; E_t=[]; I_t=[]; C_t=[]; Phi_t=[]
    aE_t=[]; aI_t=[]; aC_t=[]; aTot_t=[]; r_t=[]
    t=0.0; dt_local = cfg["dt"]; start_time = time.time()
    for step_idx in range(cfg["timesteps"]):
        if cfg["max_runtime_seconds"] and (time.time()-start_time) > cfg["max_runtime_seconds"]:
        break
    Wt_val = cfg["W_base"] + cfg["W_amp"]*math.sin(2.0*math.pi*(t/cfg["W_period"]))
        H = build_H_dense(cfg["t_hop"], cfg["t_z"], Wt_val)
        psi, (E_n,I_n,C_n,Phi_n) = if_rk4_step(psi, H, dt_local, alpha_total)
        T.append(t); Wt.append(Wt_val); E_t.append(E_n); I_t.append(I_n); C_t.append(C_n); Phi_t.append(Phi_n)
        aE_t.append(alpha_E); aI_t.append(alpha_I); aC_t.append(alpha_C); aTot_t.append(alpha_total)
        r_hist = kuramoto_quantum(psi, K_base=1.0, steps=min(cfg["kuramoto_steps"],80),
                                  dt_k=0.02,beta=cfg["kuramoto_beta"],
                                  phase_lag=cfg["kuramoto_phase_lag"],
                                  jitter=cfg["initial_phase_jitter"])
        r_t.append(float(np.mean(r_hist[-10:])))
        Phi_recent = float(np.mean(Phi_t[-8:])) if len(Phi_t)>0 else Phi_n
        C_recent = float(np.mean(C_t[-8:])) if len(C_t)>0 else C_n
        alpha_E, alpha_I, alpha_C = adapt_alphas_PID(alpha_E, alpha_I, alpha_C, Phi_recent, C_recent, pid_state)
        alpha_total = combine_alpha(alpha_E, alpha_I, alpha_C)
        cfg["eta_E"] *= cfg["alpha_anneal_factor"]; cfg["eta_I"] *= cfg["alpha_anneal_factor"]; cfg["eta_C"] *= cfg["alpha_anneal_factor"]
        if len(aTot_t)>0 and abs(alpha_total - aTot_t[-1]) > 0.12:
    alpha_total = max(min(alpha_total, cfg["alpha_max"]), cfg["alpha_min"])
            cfg["eta_E"] *= 0.5; cfg["eta_I"] *= 0.5; cfg["eta_C"] *= 0.5
        t += dt_local
    # summary + save
    Phi_mean = float(np.mean(Phi_t)) if len(Phi_t)>0 else 0.0
    C_mean   = float(np.mean(C_t))   if len(C_t)>0 else 0.0
    gap = float(np.mean(np.diff(np.sort(np.real(la.eigvalsh(H)))))) if 'H' in locals() else 0.0
    r_mean = float(np.mean(r_t)) if len(r_t)>0 else 0.0

    if C_mean > cfg["H7"] and Phi_mean > cfg["Phi_target"]:
    rec = "resonant"
    elif gap < 1e-3 and Phi_mean > 3.0:
    rec = "crystallize"
    elif C_mean < 0.05 and Phi_mean < 1.0:
    rec = "dormant"
    elif C_mean < 0.10:
    rec = "diffuse"
    elif Phi_mean > cfg["Phi_target"]:
    rec = "amplify"
    else:
    rec = "stabilize"

    tcl = {
        "Phi_recent": Phi_t[-20:],
        "C_recent":   C_t[-20:],
        "alpha_history": {
            "E": aE_t[-50:], "I": aI_t[-50:], "C": aC_t[-50:], "total": aTot_t[-50:]
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
    meta = {
        "version": cfg["version"], "seed": seed, "run_id": run_id,
        "Lx": Lx, "Ly": Ly, "Lz": Lz, "N": N,
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z"
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
    trace = {
        "meta": meta, "times": T, "W_t": Wt,
        "E_t": E_t, "I_t": I_t, "C_t": C_t, "Phi_t": Phi_t,
        "alpha_E_t": aE_t, "alpha_I_t": aI_t, "alpha_C_t": aC_t, "alpha_total_t": aTot_t,
        "r_t": r_t,
        "summary": {"Phi_mean": Phi_mean, "C_mean": C_mean, "gap": gap, "r_mean": r_mean, "recommendation": rec},
        "tcl_snapshot": tcl
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
    h = hashlib.md5(json.dumps(meta).encode()).hexdigest()[:8]
    fname = os.path.join(STATE_DIR, f"qcx_v9_1_{h}_seed{seed}.json")
    with open(fname, "w") as f:
    json.dump(trace, f, indent=2)

    if cfg["timeseries_png"]:
        try:
        fig, axs = plt.subplots(3,1,figsize=(9,9), sharex=True)
    axs[0].plot(T, Phi_t); axs[0].set_ylabel("Φ(t)")
            axs[1].plot(T, C_t); axs[1].axhline(cfg["H7"], color='r', ls='--'); axs[1].set_ylabel("C(t)")
            axs[2].plot(T, aE_t, label='αE'); axs[2].plot(T, aI_t, label='αI'); axs[2].plot(T, aC_t, label='αC')
            axs[2].legend(); axs[2].set_ylabel("α"); axs[2].set_xlabel("time")
            plt.suptitle(f"Quantum Crystal v9.1 — seed {seed} — rec {rec}")
            pngn = os.path.join(VIS_DIR, f"qcx_v9_1_{h}_seed{seed}.png")
            plt.tight_layout(); plt.savefig(pngn); plt.close()
        except Exception as e:
    print("[v9.1] PNG save failed:", e)

    print(f"[v9.1] Saved -> {fname} ; rec={rec}")
    return trace

# ---------------------------
# Ensemble runner
# ---------------------------
def run_ensemble():
    ensemble=[]
    for i in range(cfg["ensemble_size"]):
    seed = cfg["seed_base"] + i
        print(f"[v9.1] Running seed {seed} ({i+1}/{cfg['ensemble_size']})")
        tr = run_single(seed, i, save_png=True)
        ensemble.append(tr)
    Phi_means = [t["summary"]["Phi_mean"] for t in ensemble]
    C_means   = [t["summary"]["C_mean"] for t in ensemble]
    out = {
        "meta": {"version": cfg["version"], "timestamp": datetime.datetime.utcnow().isoformat()+"Z"},
        "ensemble_summary": {
            "Phi_mean_ensemble": float(np.mean(Phi_means)),
            "Phi_std": float(np.std(Phi_means)),
            "C_mean_ensemble": float(np.mean(C_means)),
            "C_std": float(np.std(C_means)),
            "seeds": [t["meta"]["seed"] for t in ensemble]
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
}
## CODEX_PARAM_OVERRIDE_START
# Optional Codex param override (safe)
try:
    _PFILE = r"C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\config\codex_params.json"
    if os.path.exists(_PFILE):
        with open(_PFILE, "r", encoding="utf-8") as _f:
            _ovr = json.load(_f)
            for _k, _v in _ovr.items():
                cfg[_k] = _v
        print("[v9.1] Codex param override applied.")
except Exception as _e:
    print("[v9.1] Param override failed:", _e)
## CODEX_PARAM_OVERRIDE_END
    sumfile = os.path.join(OUT_ROOT, "qcx_v9_1_ensemble_summary.json")
    with open(sumfile, "w") as f:
    json.dump(out, f, indent=2)
    print("[v9.1] Ensemble complete:", out["ensemble_summary"])
    return out

# ---------------------------
# Execute
# ---------------------------
if __name__ == "__main__":
    t0 = time.time()
    print("Quantum Crystal Codex v9.1 — Resonant Reawakening starting")
    ensemble_out = run_ensemble()
    print("v9.1 done. Elapsed: {:.2f}s".format(time.time()-t0))


























