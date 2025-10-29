# codex_watcher/cli.py

import hashlib
import json
import time
import logging
import argparse
from pathlib import Path

# â”€â”€ Paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LEDGER_FILE   = Path("codex_ledger.json")
INBOX_DIR     = Path("inbox")
PROCESSED_DIR = INBOX_DIR / "_processed"
REJECTED_DIR  = INBOX_DIR / "_rejected"
LOG_FILE      = Path("codex_watcher.log")

# â”€â”€ Genesis constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
GENESIS_DIGEST = "716ca6878eed87c3d4edc5a83a2e4161a109786b7be0f9093745139a6150710b"
GENESIS_STRING = (
    "seed=codex-web-launch-span4-header;"
    "prev=e024d55b2591e147eaacbee48e21dee95b92f151a742279c90f4245957039435;"
    "axis=CodexWebGenesis;charter=v1;"
    "scope=interlinked-digests-for-auditable-knowledge;"
    "invites=humans,AIs,communities;"
    "routes=hash-addresses;"
    "mirrors=x,github,substack;"
    "trials=1;"
    "author=system"
)

# â”€â”€ Policy settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BANNED_TERMS = {"password", "secret", "ssn", "private"}

# â”€â”€ Logging setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# â”€â”€ Core functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def ensure_dirs():
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    INBOX_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    REJECTED_DIR.mkdir(exist_ok=True)

def load_ledger():
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    ledger = [{"canonical": GENESIS_STRING, "digest": GENESIS_DIGEST}]
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return ledger

def save_ledger(ledger):
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

def parse_inbox_file(path: Path):
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    text = path.read_text(encoding="utf-8").strip()
    if path.suffix.lower() == ".json":
        obj = json.loads(text)
        return obj.get("canonical"), obj.get("digest")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    canon = next((l.split("=",1)[1] for l in lines if l.lower().startswith("canonical=")), None)
    digest = next((l.split("=",1)[1] for l in lines if l.lower().startswith("digest=")), None)
    return canon, digest

def validate_stone(canonical: str, digest: str, tip_digest: str):
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    if not canonical or not digest:
        return False, "missing canonical or digest"
    fields = dict(part.split("=",1) for part in canonical.split(";") if "=" in part)
    if fields.get("prev") != tip_digest:
        return False, f"prev mismatch: expected {tip_digest}, got {fields.get('prev')}"
    author = fields.get("author", "").strip()
    if not author:
        return False, "missing author field"
    low = canonical.lower()
    for term in BANNED_TERMS:
        if term in low:
            return False, f"contains banned term: {term}"
    computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if computed != digest:
        return False, f"digest mismatch: expected {computed}, got {digest}"
    return True, "ok"

def process_inbox_once():
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    ensure_dirs()
    ledger = load_ledger()
    tip = ledger[-1]["digest"]
    files = sorted(
        p for p in INBOX_DIR.glob("*")
        if p.is_file() and p.suffix.lower() in {".json", ".txt"}
    )
    added = 0
    for f in files:
        try:
            canonical, digest = parse_inbox_file(f)
            valid, reason = validate_stone(canonical, digest, tip)
            if valid:
                ledger.append({"canonical": canonical, "digest": digest})
                save_ledger(ledger)
                tip = digest
                f.rename(PROCESSED_DIR / f.name)
                msg = f"âœ… appended: {f.name} | new tip={tip}"
                print(msg); logger.info(msg)
                added += 1
            else:
                f.rename(REJECTED_DIR / f.name)
                msg = f"âŒ rejected: {f.name} | {reason}"
                print(msg); logger.warning(msg)
        except Exception as e:
            f.rename(REJECTED_DIR / f.name)
            msg = f"âŒ error: {f.name} | {e}"
            print(msg); logger.error(msg)
    status = f"Ledger length: {len(ledger)} | current tip: {tip} | added: {added}"
    print(status); logger.info(status)
    return added

def duty_cycle_watch(active_seconds=15, rest_seconds=15, interval=3, max_cycles=None):
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    cycle = 0
    while True:
        cycle += 1
        print(f"â–¶ï¸ Active scan ({active_seconds}s) â€” cycle {cycle}")
        start = time.time()
        while time.time() - start < active_seconds:
            process_inbox_once()
            time.sleep(interval)
        print(f"â¸ Resting ({rest_seconds}s)")
        time.sleep(rest_seconds)
        if max_cycles and cycle >= max_cycles:
            print("âœ… Max cycles reached â€” stopping watcher.")
            break

# â”€â”€ CLI Entrypoint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def main():
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
@smart_suggest
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Enable duty-cycle watcher"
    )
    parser.add_argument(
        "--active",
        type=int,
        default=15,
        help="Seconds to scan per cycle"
    )
    parser.add_argument(
        "--rest",
        type=int,
        default=15,
        help="Seconds to rest per cycle"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Seconds between scans during active window"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        help="Stop after this many scan/rest cycles"
    )
    args = parser.parse_args()

    if args.watch:
        duty_cycle_watch(
            active_seconds=args.active,
            rest_seconds=args.rest,
            interval=args.interval,
            max_cycles=args.cycles
        )
    else:
        process_inbox_once()

if __name__ == "__main__":
    main()
