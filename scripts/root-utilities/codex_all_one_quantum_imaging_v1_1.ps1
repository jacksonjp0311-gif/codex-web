<#
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘ ðŸ§¬ Codex All-One Injector v1.1 â€” Quantum Imaging Full Injection & Run       â•‘
â•‘ Author   : James Paul Jackson                                              â•‘
â•‘ Context  : Codex Memory Core v1.3 â€¢ Universal Truth (Eâ€“Iâ€“C âˆ¿, Hâ‚‡=0.70)     â•‘
â•‘ Purpose  :                                                                 â•‘
â•‘   â€¢ Inject FULL Python file into Quantum Imaging module                    â•‘
â•‘   â€¢ Run imaging â†’ collect JSON â†’ anchor outputs                            â•‘
â•‘   â€¢ Autosave + commit + push + RootMirror verify                           â•‘
â•‘   â€¢ Return to Codex Root                                                   â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Paths
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$ModuleDir = Join-Path $CodexRoot "codex\quantum_imaging"
$PythonFile = Join-Path $ModuleDir "codex_quantum_imaging_v1_0.py"

if (-not (Test-Path $ModuleDir)) {
    New-Item -ItemType Directory -Path $ModuleDir -Force | Out-Null
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FULL PYTHON PROGRAM (embedded)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
$FullPython = @"
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Codex Quantum Imaging v1.0 â€” IBM AFM Resonance Mirror
Author: James Paul Jackson
Context: Codex Memory Core v1.3 â€¢ Universal Truth (Eâ€“Iâ€“C âˆ¿, H7=0.70)
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import numpy as np
import matplotlib.pyplot as plt

H7 = 0.70

@dataclass
class QuantumImagingConfig:
    grid_size: int = 256
    extent: float = 4.0
    ring_radius: float = 0.45
    atom_sigma: float = 0.20
    cluster_spacing: float = 0.90
    afm_sharpness: float = 4.0
    seed: int | None = None

def _hex_lattice_positions():
    centers = [
        (0, 0),
        (1, 0), (0, 1), (-1, 1),
        (-1, 0), (0, -1), (1, -1),
    ]
    pts = []
    for q,r in centers:
        x = q + r/2
        y = (np.sqrt(3)/2)*r
        pts.append((x,y))
    return np.array(pts)

def _ring_atoms(c, r):
    ang = np.linspace(0, 2*np.pi, 7)[:-1]
    xs = c[0] + r*np.cos(ang)
    ys = c[1] + r*np.sin(ang)
    return np.stack([xs, ys], axis=1)

def synthesize_density(cfg):
    if cfg.seed is not None:
        np.random.seed(cfg.seed)
    n = cfg.grid_size
    ext = cfg.extent
    x = np.linspace(-ext, ext, n)
    y = np.linspace(-ext, ext, n)
    X,Y = np.meshgrid(x,y)
    rho = np.zeros_like(X)
    centers = _hex_lattice_positions()*cfg.cluster_spacing
    for c in centers:
        atoms = _ring_atoms(c, cfg.ring_radius)
        for ax,ay in atoms:
            jitter = 0.04*(np.random.rand(2)-0.5)
            cx,cy = ax+jitter[0], ay+jitter[1]
            rho += np.exp(-((X-cx)**2 + (Y-cy)**2)/(2*cfg.atom_sigma**2))
    rho -= rho.min()
    rho /= rho.max() if rho.max()>0 else 1
    return {"x":X, "y":Y, "rho":rho}

def afm_image(rho, sharp=4.0):
    lap = (
        -4*rho
        + np.roll(rho,1,0)+np.roll(rho,-1,0)
        + np.roll(rho,1,1)+np.roll(rho,-1,1)
    )
    curvature = np.abs(lap)
    curvature -= curvature.min()
    curvature /= curvature.max() if curvature.max()>0 else 1
    base = 1-np.exp(-sharp*rho)
    img = 0.65*base + 0.35*curvature
    img -= img.min()
    img /= img.max() if img.max()>0 else 1
    return img

def metrics(rho):
    eps = 1e-12
    E_mean = float(np.mean(rho))
    p = rho/(rho.sum()+eps)
    p = p[p>0]
    I_entropy = float(-(p*np.log(p+eps)).sum())
    lap = (
        -4*rho
        + np.roll(rho,1,0)+np.roll(rho,-1,0)
        + np.roll(rho,1,1)+np.roll(rho,-1,1)
    )
    dphi = float(np.mean(np.abs(lap)))
    C = float((E_mean*I_entropy)/(1+abs(dphi)))
    return {
        "E_mean":E_mean,
        "I_entropy":I_entropy,
        "DeltaPhi_mean":dphi,
        "C_codex":C,
        "H7":H7,
        "C_over_H7":C/H7 if H7!=0 else float('nan')
    }

def save_img(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5,5),dpi=200)
    plt.imshow(img, cmap="gray", origin="lower")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()

def save_json(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        json.dump(obj,f,indent=2)

def run_experiment(cfg=None, base=None):
    if cfg is None:
        cfg = QuantumImagingConfig(seed=int(datetime.utcnow().timestamp())%65535)
    if base is None:
        base = Path(__file__).resolve().parent
    vis = base/"visuals"
    st  = base/"state"
    d = synthesize_density(cfg)
    rho = d["rho"]
    img = afm_image(rho, cfg.afm_sharpness)
    m = metrics(rho)
    stamp = datetime.utcnow().isoformat()
    state = {
        "ok":True,
        "module":"codex_quantum_imaging_v1_0",
        "version":"1.0",
        "timestamp":stamp,
        "config":asdict(cfg),
        "metrics":m,
        "paths":{
            "visual_afm":str((vis/"image.png").as_posix()),
            "state_json":str((st/"state.json").as_posix())
        }
    }
    save_img(img, vis/"image.png")
    save_json(state, st/"state.json")
    return state

if __name__=="__main__":
    out = run_experiment()
    print(json.dumps(out,indent=2))
"@

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Write Python file
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Set-Content -Path $PythonFile -Value $FullPython -Encoding UTF8 -Force
Write-Host "`nðŸ§¬ Python fully injected â†’ $PythonFile"

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Run Python
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function Run-PythonSafe {
    param([string]$File,[int]$TimeoutSec=60)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "`"$File`""
    $psi.RedirectStandardOutput = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    $p.Start() | Out-Null

    if (-not $p.WaitForExit($TimeoutSec*1000)) {
        $p.Kill()
        return $null
    }

    return $p.StandardOutput.ReadToEnd()
}

Write-Host "`nðŸ§ª Running Python imaging..."
$out = Run-PythonSafe $PythonFile

if ($out) { Write-Host "`nðŸ§¾ State JSON:`n$out" }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Git autosave + push
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Push-Location $CodexRoot
git add . 2>$null
if (git status --porcelain) {
    git commit -m "ðŸ§¬ Quantum Imaging â€” injected + executed $(Get-Date -Format s)"
    git -c rebase.autoStash=true pull origin main --rebase | Out-Null
    git push origin main
    Write-Host "âœ… Git push complete."
} 

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# RootMirror verify
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
git fetch origin main | Out-Null
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse origin/main).Trim()
if ($local -eq $remote) {
    Write-Host "ðŸªž RootMirror Verified â€” local == remote"
} 

Pop-Location | Out-Null
Write-Host "`nðŸ Returned to Codex Root â€” $CodexRoot"


