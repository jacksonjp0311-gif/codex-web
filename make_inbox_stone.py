# make_inbox_stone.py
import hashlib, json
from pathlib import Path

LEDGER = Path("codex_ledger.json")
INBOX  = Path("inbox")
INBOX.mkdir(exist_ok=True)

# load current tip
ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
tip = ledger[-1]["digest"]

# build canonical with author
canonical = (
    "seed=inbox-test-002;"
    f"prev={tip};"
    "axis=CodexWeb;"
    "data=validation-check;"
    "method=python-sha256;"
    "metrics=n/a;"
    "notes=valid stone from helper;"
    "trials=1;"
    "author=James"
)

# compute digest
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

# write to inbox
payload = {"canonical": canonical, "digest": digest}
outfile = INBOX / "stone_inbox_test_002.json"
outfile.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print("Wrote:", outfile.name)
print("Canonical:", canonical)
print("Digest:   ", digest)
