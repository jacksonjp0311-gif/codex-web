# -*- coding: utf-8 -*-
"""
QIM v5.5 — Pentacene-style nc-AFM generator
• Builds a 3D volume (64³) with elongated aromatic chain
• Approximates pentacene: 5 fused rings along x-axis
• Tip-convolution blur + mild noise
• Normalized to [0,1] as AFM-like force field
"""
import sys
from pathlib import Path
import numpy as np


def make_pentacene_afm(shape=(64, 64, 64), rings=5, noise_level=0.02):
    nx, ny, nz = shape
    x = np.linspace(-2.0, 2.0, nx)
    y = np.linspace(-2.0, 2.0, ny)
    z = np.linspace(-1.0, 1.0, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    base = np.zeros(shape, dtype=np.float32)

    xs = np.linspace(-1.4, 1.4, rings)
    ys = np.zeros_like(xs)
    zs = np.zeros_like(xs)

    for cx, cy, cz in zip(xs, ys, zs):
        R_xy = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        R_z  = np.abs(Z - cz)
        ring = np.exp(-((R_xy - 0.55) ** 2) * 28.0) * np.exp(-R_z * 10.0)
        base += ring.astype(np.float32)

    backbone = np.exp(-(X ** 2) * 6.0) * np.exp(-(Y ** 2) * 10.0)
    base += 0.5 * backbone.astype(np.float32)

    def gaussian_kernel_1d(sigma, radius=2):
        xs = np.arange(-radius, radius + 1, dtype=np.float32)
        k = np.exp(-0.5 * (xs / sigma) ** 2)
        k /= k.sum()
        return k

    k = gaussian_kernel_1d(1.0, radius=2)

    def blur1d(vol, axis):
        vol = np.swapaxes(vol, 0, axis)
        out = np.zeros_like(vol)
        rad = len(k) // 2
        for i in range(vol.shape[0]):
            i0 = max(0, i - rad)
            i1 = min(vol.shape[0], i + rad + 1)
            sl = slice(i0, i1)
            ks = k[(rad - (i - i0)):(rad + (i1 - i))]
            out[i] = np.tensordot(ks, vol[sl], axes=(0, 0))
        out = np.swapaxes(out, 0, axis)
        return out

    blurred = blur1d(base, 0)
    blurred = blur1d(blurred, 1)
    blurred = blur1d(blurred, 2)

    vol = blurred
    vol = vol.max() - vol

    vmin, vmax = float(vol.min()), float(vol.max())
    if vmax > vmin:
        vol = (vol - vmin) / (vmax - vmin)

    rng = np.random.default_rng(153)
    vol = vol + noise_level * rng.standard_normal(vol.shape, dtype=np.float32)
    vol = np.clip(vol, 0.0, 1.0).astype(np.float32)
    return vol


def main():
    if len(sys.argv) < 2:
        print("Usage: afm_pentacene_generate_v5_5.py OUT_PATH.npy", file=sys.stderr)
        sys.exit(1)

    out_path = Path(sys.argv[1]).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    vol = make_pentacene_afm()
    np.save(out_path, vol)
    print(f"[AFM] Pentacene-style AFM cube written → {out_path}")


if __name__ == "__main__":
    main()
