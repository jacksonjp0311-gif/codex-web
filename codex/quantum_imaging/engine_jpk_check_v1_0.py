import os, sys, json
from pathlib import Path
from datetime import datetime, timezone

try:
    import h5py
except ImportError:
    print("Missing h5py — install with: pip install h5py", file=sys.stderr)
    sys.exit(1)

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def check_jpk(path):
    try:
        with h5py.File(path, "r") as f:
            return True, list(f.keys())
    except Exception as e:
        return False, str(e)

def main(src, logs_dir, state_dir):
    src = Path(src)
    logs_dir = Path(logs_dir)
    state_dir = Path(state_dir)

    logs_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"jpk_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fout = log_file.open("w", encoding="utf8")

    results = []

    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if not (str(f).endswith(".jpk") or str(f).endswith(".jpk-qi-image")):
            continue

        ok, detail = check_jpk(f)
        entry = {
            "file": str(f),
            "is_hdf5": ok,
            "detail": detail
        }
        results.append(entry)

        if ok:
            msg = f"[HDF5 OK] {f}"
        else:
            msg = f"[NOT HDF5] {f} → {detail}"

        print(msg)
        fout.write(msg + "\n")

    fout.close()

    state = {
        "protocol": "QIM_JPK_CHECK",
        "timestamp": now(),
        "source": str(src),
        "total_files": len(results),
        "results": results
    }

    state_path = state_dir / f"jpk_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    state_path.write_text(json.dumps(state, indent=2))
    print(f"State JSON → {state_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: engine_jpk_check_v1_0.py SRC_FOLDER LOGS_DIR STATE_DIR")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
