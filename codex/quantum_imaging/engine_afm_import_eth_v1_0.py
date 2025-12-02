#!/usr/bin/env python3
# QIM AFM Import v1.0 — ETH roughness → AFM cubes (.npy)

import sys, json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
from PIL import Image

IMAGE_EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_height(path: Path) -> np.ndarray:
    img = Image.open(path)
    img = img.convert("F")        # 32-bit grayscale
    arr = np.array(img, dtype=np.float32)
    mn = float(arr.min())
    mx = float(arr.max())
    if mx > mn:
        arr = (arr - mn) / (mx - mn)
    else:
        arr = np.zeros_like(arr, dtype=np.float32)
    return arr

def make_cube(height: np.ndarray, depth: int) -> np.ndarray:
    # Stack the 2D AFM surface into a simple 3D cube [Z,X,Y]
    cube = np.repeat(height[None, :, :], depth, axis=0)
    return cube.astype(np.float32)

def main(src_dir, out_dir, logs_dir, state_dir, depth):
    src = Path(src_dir)
    out = Path(out_dir)
    logs = Path(logs_dir)
    state = Path(state_dir)

    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)

    log_file = logs / f"afm_import_eth_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    log_f = log_file.open("w", encoding="utf-8")

    converted = []
    skipped = []

    def log(msg: str):
        line = msg.encode("ascii", "replace").decode("ascii")
        print(line)
        log_f.write(line + "\n")
        log_f.flush()

    log("QIM AFM Import v1.0 — ETH roughness")
    log(f"src_dir  : {src}")
    log(f"out_dir  : {out}")
    log(f"cube_depth: {depth}")

    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in IMAGE_EXTS:
            continue

        rel = path.relative_to(src)
        stem = rel.stem.replace(" ", "_")
        cube_name = f"afm_eth_{stem}.npy"
        cube_path = out / cube_name

        try:
            hmap = load_height(path)
            cube = make_cube(hmap, depth)
            np.save(cube_path, cube)
            log(f"OK  → {rel}  →  {cube_name}  shape={cube.shape}")
            converted.append({
                "source": str(rel),
                "target": str(cube_path),
                "shape": list(cube.shape),
            })
        except Exception as e:
            log(f"SKIP → {rel}  ({repr(e)})")
            skipped.append({
                "source": str(rel),
                "error": repr(e),
            })

    log_f.close()

    state_obj = {
        "protocol": "CodexQIMAFMImportETH",
        "version": "1.0",
        "timestamp": now_iso(),
        "source_dir": str(src),
        "target_dir": str(out),
        "cube_depth": depth,
        "counts": {
            "converted": len(converted),
            "skipped": len(skipped),
        },
        "converted": converted,
        "skipped": skipped,
    }

    state_path = state / f"afm_import_eth_state_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    state_path.write_text(json.dumps(state_obj, indent=2), encoding="utf-8")
    print(f"State JSON written → {state_path}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: engine_afm_import_eth_v1_0.py SRC_DIR OUT_DIR LOGS_DIR STATE_DIR DEPTH", file=sys.stderr)
        sys.exit(1)
    src_dir, out_dir, logs_dir, state_dir, depth_s = sys.argv[1:]
    main(src_dir, out_dir, logs_dir, state_dir, int(depth_s))
