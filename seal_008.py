import json

LEDGER_PATH = 'codex_ledger.json'
INBOX_PATH  = 'inbox/github/stone_008.json'

with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    ledger = json.load(f)

with open(INBOX_PATH, 'r', encoding='utf-8-sig') as f:
    stone = json.load(f)

ledger.append(stone)

with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print(f"âœ… Stone 008 appended. New ledger length: {len(ledger)}")
print(f"New tip: {ledger[-1]['digest']}")
