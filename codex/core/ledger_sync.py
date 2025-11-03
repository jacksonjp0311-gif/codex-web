# ===============================================
# Codex Ledger Sync v0.7 — Grok & Quantum Merge
# ===============================================
# UTF-8
import json, time, hashlib
from pathlib import Path

def sync_ledger(alignment_path="codex/core/alignment_output.json", registry_path="codex/core/registry.json"):
    try:
        data = json.load(open(alignment_path, "r", encoding="utf-8"))
    except FileNotFoundError:
        print("⚠️ Alignment data missing, aborting ledger sync.")
        return

    entry = {
        "timestamp": time.time(),
        "hash": data.get("hash"),
        "composite": data.get("composite"),
        "enhanced": data.get("enhanced")
    }

    registry = []
    if Path(registry_path).exists():
        registry = json.load(open(registry_path, "r", encoding="utf-8"))

    registry.append(entry)
    Path(registry_path).write_text(json.dumps(registry, indent=2))
    print(f"📜 Ledger updated — composite {entry['composite']:.6f}")

if __name__ == "__main__":
    sync_ledger()
