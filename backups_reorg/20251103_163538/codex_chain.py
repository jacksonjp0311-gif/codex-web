# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
import json
import hashlib
from pathlib import Path

LEDGER_FILE = Path("codex_ledger.json")

def load_ledger():
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text())
    else:
        return []

def save_ledger(ledger):
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2))

def make_stone(seed, axis, data, method, metrics, notes, trials=1):
    ledger = load_ledger()
    prev_digest = ledger[-1]["digest"] if ledger else "GENESIS"
    canonical = (
        f"seed={seed};"
        f"prev={prev_digest};"
        f"axis={axis};"
        f"data={data};"
        f"method={method};"
        f"metrics={metrics};"
        f"notes={notes};"
        f"trials={trials}"
    )
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    ledger.append({"canonical": canonical, "digest": digest})
    save_ledger(ledger)
    return canonical, digest

def interactive_chain():
    print("🔗 Codex Chain Interactive")
    seed = input("Seed: ")
    axis = input("Axis: ")
    data = input("Data: ")
    method = input("Method: ")
    metrics = input("Metrics: ")
    notes = input("Notes: ")
    canonical, digest = make_stone(seed, axis, data, method, metrics, notes)
    print("\nCanonical:\n", canonical)
    print("\nDigest:\n", digest)

if __name__ == "__main__":
    interactive_chain()

