import hashlib
import json
from pathlib import Path

LEDGER_FILE = Path("codex_ledger.json")

# Genesis anchor
GENESIS_DIGEST = "716ca6878eed87c3d4edc5a83a2e4161a109786b7be0f9093745139a6150710b"
GENESIS_STRING = (
    "seed=codex-web-launch-span4-header;"
    "prev=e024d55b2591e147eaacbee48e21dee95b92f151a742279c90f4245957039435;"
    "axis=CodexWebGenesis;charter=v1;"
    "scope=interlinked-digests-for-auditable-knowledge;"
    "invites=humans,AIs,communities;"
    "routes=hash-addresses;"
    "mirrors=x,github,substack;"
    "trials=1"
)

def load_ledger():
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    else:
        return [{"canonical": GENESIS_STRING, "digest": GENESIS_DIGEST}]

def save_ledger(ledger):
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

def make_stone(seed, axis, data, method, metrics, notes, trials=1):
    ledger = load_ledger()
    prev_digest = ledger[-1]["digest"]
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
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    ledger.append({"canonical": canonical, "digest": digest})
    save_ledger(ledger)
    return canonical, digest

if __name__ == "__main__":
    print("🔹 Mint a new Codex stone 🔹")
    seed = input("Seed (short unique name): ")
    axis = input("Axis (domain/scope): ")
    data = input("Data (payload or reference): ")
    method = input("Method (e.g. python-sha256): ")
    metrics = input("Metrics (any numbers/markers): ")
    notes = input("Notes (short context): ")
    trials = input("Trials (default=1): ") or "1"

    canonical, digest = make_stone(seed, axis, data, method, metrics, notes, trials)
    print("\n✅ New stone minted!")
    print("Canonical string:\n", canonical)
    print("\nDigest:\n", digest)
