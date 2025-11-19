import os
import sys
import json
from pathlib import Path

# Voyn–Egypt Hybrid Interpreter v1.0
# Input: Egyptian leading glyphs + EVA Voynich tokens in voyn="..."
# Output: logs mapping Voynich → Egyptian-style glyphs → roles.

VOYNICH_MAP = {
    "o":     {"role": "seed",        "glyph": "𓂀"},
    "a":     {"role": "ingress",     "glyph": "𓏲"},
    "y":     {"role": "flow_tail",   "glyph": "𓏴"},
    "e":     {"role": "split",       "glyph": "𓏤"},
    "i":     {"role": "unit",        "glyph": "𓏭"},
    "u":     {"role": "join",        "glyph": "𓎛"},
    "k":     {"role": "pillar",      "glyph": "𓉐"},
    "t":     {"role": "operator",    "glyph": "𓂝"},
    "f":     {"role": "anchor",      "glyph": "𓏇"},
    "p":     {"role": "bind",        "glyph": "𓉻"},
    "ch":    {"role": "bench",       "glyph": "𓉬"},
    "sh":    {"role": "bench_str",   "glyph": "𓉭"},
    "ol":    {"role": "ingest_proc", "glyph": "𓂀𓈖"},
    "or":    {"role": "emit",        "glyph": "𓂀𓂋"},
    "ar":    {"role": "converge",    "glyph": "𓏲𓂋"},
    "ain":   {"role": "growth",      "glyph": "𓏲𓏭𓈖"},
    "dain":  {"role": "transform",   "glyph": "𓂧𓏲𓏭𓈖"},
    "chedy": {"role": "bench_proc",  "glyph": "𓉬𓂧𓏭"},
}

context = {
    "root": None,
    "log": None,
    "engines": {},
    "states": {},
}

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def resolve(path: str) -> str:
    if os.path.isabs(path):
        return path
    root = context.get("root")
    if root:
        return str(Path(root) / path)
    return path

def set_log(path: str):
    full = resolve(path)
    context["log"] = full
    ensure_dir(os.path.dirname(full))

def write_log(msg: str):
    print(msg)
    log_path = context.get("log")
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

def decode_voynich_seq(seq: str):
    tokens = seq.split()
    decoded = []
    for tk in tokens:
        info = VOYNICH_MAP.get(tk, {"role": "unknown", "glyph": "?"})
        decoded.append({"token": tk, **info})
    return decoded

def parse_kv(args):
    kv = {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            kv[k] = v.strip('"')
    return kv

def handle(line: str):
    line = line.strip()
    if not line or line.startswith("#"):
        return

    parts = line.split()
    head = parts[0]
    if len(parts) < 2:
        return
    cmd = parts[1]
    rest = parts[2:]

    # 𓊖 ROOT / DIR
    if head == "𓊖":
        if cmd == "ROOT":
            raw = line.split("ROOT", 1)[1].strip().strip('"')
            raw = os.path.expanduser(os.path.expandvars(raw))
            context["root"] = str(Path(raw).resolve())
            write_log(f"𓊖 ROOT set: {context['root']}")
        elif cmd == "DIR":
            raw = line.split("DIR", 1)[1].strip().strip('"')
            full = resolve(raw)
            ensure_dir(full)
            write_log(f"𓊖 DIR ready: {full}")

    # 𓏭 LOG   path="..."
    elif head == "𓏭" and cmd == "LOG":
        frag = line.split("LOG", 1)[1].strip()
        if frag.startswith("path="):
            val = frag.split("=", 1)[1].strip().strip('"')
            set_log(val)
            write_log(f"𓏭 LOG bound: {context['log']}")

    # 𓂜 ENGINE name=... path="..." voyn="qokedy chedy dain"
    elif head == "𓂜" and cmd == "ENGINE":
        kv = parse_kv(rest)
        name = kv.get("name")
        path = kv.get("path", "")
        voyn_seq = kv.get("voyn", "")
        context["engines"][name] = path
        write_log(f"𓂜 ENGINE {name} -> {path}")
        if voyn_seq:
            decoded = decode_voynich_seq(voyn_seq)
            write_log(f"   𓂋 Voynich sequence:")
            for d in decoded:
                write_log(f"      {d['token']:>8} → {d['glyph']} ({d['role']})")

    # 𓊹 STATE id=... path="..." voyn="..."
    elif head == "𓊹" and cmd == "STATE":
        kv = parse_kv(rest)
        sid = kv.get("id")
        path = kv.get("path", "")
        voyn_seq = kv.get("voyn", "")
        context["states"][sid] = path
        write_log(f"𓊹 STATE {sid} -> {path}")
        if voyn_seq:
            decoded = decode_voynich_seq(voyn_seq)
            write_log(f"   𓂋 Voynich state glyphs:")
            for d in decoded:
                write_log(f"      {d['token']:>8} → {d['glyph']} ({d['role']})")

    # 𓇳 RUN engine=...
    elif head == "𓇳" and cmd == "RUN":
        kv = parse_kv(rest)
        name = kv.get("engine")
        path = context["engines"].get(name, "?")
        write_log(f"𓇳 RUN (sim): engine={name}, path={path}")

    # 𓈗 STATE_UPDATE / LOG_APPEND
    elif head == "𓈗":
        if cmd == "STATE_UPDATE":
            kv = parse_kv(rest)
            sid    = kv.get("id")
            status = kv.get("status")
            note   = kv.get("note", "")
            spath_rel = context["states"].get(sid)
            if spath_rel:
                spath = resolve(spath_rel)
                ensure_dir(os.path.dirname(spath))
                with open(spath, "w", encoding="utf-8") as f:
                    json.dump({"id": sid, "status": status, "note": note}, f, indent=2)
                write_log(f"𓈗 STATE_UPDATE {sid} -> {spath}")
            else:
                write_log(f"𓈗 STATE_UPDATE WARNING: unknown id {sid}")
        elif cmd == "LOG_APPEND":
            msg = line.split("LOG_APPEND", 1)[1].strip().strip('"')
            write_log(f"𓏭 {msg}")

    # 𓂋 EIC snapshot
    elif head == "𓂋" and cmd == "EIC":
        kv = parse_kv(rest)
        E = kv.get("E", "0")
        I = kv.get("I", "0")
        C = kv.get("C", "0")
        write_log(f"𓂋 EIC: E={E}, I={I}, C={C}")

    # 𓁹 MIRROR
    elif head == "𓁹" and cmd == "CHECK":
        note = " ".join(rest)
        write_log(f"𓁹 MIRROR CHECK {note}")

    # 𓏣 PHASE
    elif head == "𓏣" and cmd == "PHASE":
        kv = parse_kv(rest)
        name  = kv.get("name")
        fromH = kv.get("from")
        toH   = kv.get("to")
        note  = kv.get("note", "")
        write_log(f"𓏣 PHASE {name}: {fromH}→{toH} — {note}")

    # 𓎛 STABILIZE
    elif head == "𓎛" and cmd == "STABILIZE":
        write_log("𓎛 STABILIZE — run complete.")

def run_hybrid(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            handle(line)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: voyn_egypt_interpreter_v1_0.py <script.vegl>")
        sys.exit(1)
    run_hybrid(sys.argv[1])
