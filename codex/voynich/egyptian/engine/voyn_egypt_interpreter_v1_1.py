import os
import sys
import json
from pathlib import Path

"""
Voyn–Egypt Hybrid Interpreter v1.1 (ASCII-safe)

- Input: hybrid script (.vegl) with commands like:

    ROOT "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web"
    DIR  "codex/voynich/egyptian/state"
    LOG  path="codex/voynich/egyptian/logs/f1_hybrid.log"
    ENGINE name=F1 path="codex/voynich/egyptian/engine/f1_core.py" voyn="qokedy chedy dain"
    STATE  id=f1_state path="codex/voynich/egyptian/state/f1_state.json" voyn="qokedy ain"
    RUN engine=F1
    STATE_UPDATE id=f1_state status=OK note="Hybrid F1 mapping complete."
    LOG_APPEND msg="Done."
    EIC E=0.69 I=0.73 C=0.70
    PHASE name=F1_Mapping from=H19 to=H20 note="Voynich->Egypt mapping online."
    MIRROR note="F1 mirror check"
    STABILIZE

- It maps EVA Voynich tokens to symbolic "Egyptian-style" roles and tags.
- No real hieroglyph codepoints here; all ASCII-safe tags (EG_EYE, EG_BENCH, etc.).
"""

VOYNICH_MAP = {
    "o":     {"role": "seed",        "tag": "EG_EYE"},
    "a":     {"role": "ingress",     "tag": "EG_LOOP"},
    "y":     {"role": "flow_tail",   "tag": "EG_TAIL"},
    "e":     {"role": "split",       "tag": "EG_SPLIT"},
    "i":     {"role": "unit",        "tag": "EG_REED"},
    "u":     {"role": "join",        "tag": "EG_FOLD"},
    "k":     {"role": "pillar",      "tag": "EG_PILLAR"},
    "t":     {"role": "operator",    "tag": "EG_ARM"},
    "f":     {"role": "anchor",      "tag": "EG_ANCHOR"},
    "p":     {"role": "bind",        "tag": "EG_HOOK"},
    "ch":    {"role": "bench",       "tag": "EG_BENCH"},
    "sh":    {"role": "bench_str",   "tag": "EG_BENCH_STR"},
    "ol":    {"role": "ingest_proc", "tag": "EG_EYE_WATER"},
    "or":    {"role": "emit",        "tag": "EG_EYE_MOUTH"},
    "ar":    {"role": "converge",    "tag": "EG_LOOP_MOUTH"},
    "ain":   {"role": "growth",      "tag": "EG_LOOP_REED_WATER"},
    "dain":  {"role": "transform",   "tag": "EG_HAND_LOOP_REED_WATER"},
    "chedy": {"role": "bench_proc",  "tag": "EG_BENCH_HAND_REED"},
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
            f.write(msg + "\\n")

def decode_voynich_seq(seq: str):
    tokens = seq.split()
    decoded = []
    for tk in tokens:
        info = VOYNICH_MAP.get(tk, {"role": "unknown", "tag": "EG_UNKNOWN"})
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
    cmd = parts[0]
    rest = parts[1:]

    # ROOT "C:\..."
    if cmd == "ROOT":
        raw = line.split("ROOT", 1)[1].strip().strip('"')
        raw = os.path.expanduser(os.path.expandvars(raw))
        context["root"] = str(Path(raw).resolve())
        write_log(f"[ROOT] {context['root']}")
        return

    # DIR "relative/path"
    if cmd == "DIR":
        raw = line.split("DIR", 1)[1].strip().strip('"')
        full = resolve(raw)
        ensure_dir(full)
        write_log(f"[DIR] ready: {full}")
        return

    # LOG path="..."
    if cmd == "LOG":
        frag = line.split("LOG", 1)[1].strip()
        if frag.startswith("path="):
            val = frag.split("=", 1)[1].strip().strip('"')
            set_log(val)
            write_log(f"[LOG] bound: {context['log']}")
        return

    # ENGINE name=... path="..." voyn="..."
    if cmd == "ENGINE":
        kv = parse_kv(rest)
        name = kv.get("name")
        path = kv.get("path", "")
        voyn_seq = kv.get("voyn", "")
        context["engines"][name] = path
        write_log(f"[ENGINE] {name} -> {path}")
        if voyn_seq:
            decoded = decode_voynich_seq(voyn_seq)
            write_log("  [ENGINE VOYN] sequence:")
            for d in decoded:
                write_log(f"    {d['token']:>8} -> {d['tag']} ({d['role']})")
        return

    # STATE id=... path="..." voyn="..."
    if cmd == "STATE":
        kv = parse_kv(rest)
        sid = kv.get("id")
        path = kv.get("path", "")
        voyn_seq = kv.get("voyn", "")
        context["states"][sid] = path
        write_log(f"[STATE] {sid} -> {path}")
        if voyn_seq:
            decoded = decode_voynich_seq(voyn_seq)
            write_log("  [STATE VOYN] glyphs:")
            for d in decoded:
                write_log(f"    {d['token']:>8} -> {d['tag']} ({d['role']})")
        return

    # RUN engine=...
    if cmd == "RUN":
        kv = parse_kv(rest)
        name = kv.get("engine")
        path = context["engines"].get(name, "?")
        write_log(f"[RUN] (sim) engine={name}, path={path}")
        return

    # STATE_UPDATE / LOG_APPEND
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
            write_log(f"[STATE_UPDATE] {sid} -> {spath}")
        else:
            write_log(f"[STATE_UPDATE] WARNING: unknown id {sid}")
        return

    if cmd == "LOG_APPEND":
        msg = line.split("LOG_APPEND", 1)[1].strip().strip('"')
        write_log(f"[LOG+] {msg}")
        return

    # EIC E=... I=... C=...
    if cmd == "EIC":
        kv = parse_kv(rest)
        E = kv.get("E", "0")
        I = kv.get("I", "0")
        C = kv.get("C", "0")
        write_log(f"[EIC] E={E} I={I} C={C}")
        return

    # PHASE name=... from=H.. to=H.. note="..."
    if cmd == "PHASE":
        kv = parse_kv(rest)
        name  = kv.get("name")
        fromH = kv.get("from")
        toH   = kv.get("to")
        note  = kv.get("note", "")
        write_log(f"[PHASE] {name}: {fromH}->{toH} ({note})")
        return

    # MIRROR note="..."
    if cmd == "MIRROR":
        note = line.split("MIRROR", 1)[1].strip()
        write_log(f"[MIRROR] {note}")
        return

    # STABILIZE
    if cmd == "STABILIZE":
        write_log("[STABILIZE] run complete.")
        return

def run_hybrid(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            handle(line)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: voyn_egypt_interpreter_v1_1.py <script.vegl>")
        sys.exit(1)
    run_hybrid(sys.argv[1])
