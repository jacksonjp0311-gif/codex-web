import os
import json
import sys
import re
from pathlib import Path

# Egyptian Codex Glyph Interpreter v0.2 — fixed ROOT + LOG handling

context = {
    "root": None,
    "engines": {},
    "states": {},
    "log": None,
}

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def resolve(path: str) -> str:
    """Resolve a path relative to ROOT if set, otherwise return as-is."""
    if os.path.isabs(path):
        return path
    root = context.get("root")
    if root:
        return str(Path(root) / path)
    return path

def log(msg: str):
    """Write to log file (if set) and echo to stdout."""
    lp = context.get("log")
    if lp:
        ensure_dir(os.path.dirname(lp))
        with open(lp, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    print(msg)

def parse_kv(arg: str):
    if "=" in arg:
        return arg.split("=", 1)
    return None, arg

def handle(line: str):
    line = line.strip()
    if not line or line.startswith("#"):
        return

    parts = line.split()
    glyph = parts[0]
    if len(parts) < 2:
        return
    cmd = parts[1]
    args = parts[2:]

    # 𓊖 ROOT / DIR
    if glyph == "𓊖":
        if cmd == "ROOT":
            raw = line.split("ROOT", 1)[1].strip()
            raw = raw.strip('"').strip("'")
            raw = os.path.expanduser(os.path.expandvars(raw))
            root_path = Path(raw).resolve()
            context["root"] = str(root_path)
            print(f"𓊖 ROOT set: {context['root']}")
        elif cmd == "DIR":
            raw = line.split("DIR", 1)[1].strip()
            raw = raw.strip('"').strip("'")
            full = resolve(raw)
            ensure_dir(full)
            print(f"𓊖 DIR ready: {full}")

    # 𓂜 ENGINE
    elif glyph == "𓂜" and cmd == "ENGINE":
        kv = dict(parse_kv(a) for a in args)
        name = kv.get("name")
        path = kv.get("path", "").strip('"').strip("'")
        context["engines"][name] = path
        print(f"𓂜 ENGINE registered: {name} -> {path}")

    # 𓊹 STATE
    elif glyph == "𓊹" and cmd == "STATE":
        kv = dict(parse_kv(a) for a in args)
        sid  = kv.get("id")
        path = kv.get("path", "").strip('"').strip("'")
        context["states"][sid] = path
        print(f"𓊹 STATE registered: {sid} -> {path}")

    # 𓏭 LOG  (robust path="..." parser)
    elif glyph == "𓏭" and cmd == "LOG":
        # Expect pattern: LOG    path="relative/or/absolute/path"
        m = re.search(r'LOG\s+path\s*=\s*"([^"]+)"', line)
        if m:
            logpath = m.group(1)
            context["log"] = resolve(logpath)
            print(f"𓏭 LOG path: {context['log']}")
        else:
            print("𓏭 LOG parse error: no valid path found")

    # 𓇳 RUN (simulated)
    elif glyph == "𓇳" and cmd == "RUN":
        kv = dict(parse_kv(a) for a in args)
        engine_name = kv.get("engine")
        engine_path = context["engines"].get(engine_name, "")
        msg = f"𓇳 RUN (simulated): engine={engine_name}, path={engine_path}"
        log(msg)

    # 𓈗 STATE_UPDATE / LOG_APPEND
    elif glyph == "𓈗":
        if cmd == "STATE_UPDATE":
            kv = dict(parse_kv(a) for a in args)
            sid    = kv.get("id")
            status = kv.get("status")
            note   = kv.get("note", "").strip('"').strip("'")
            state_rel = context["states"].get(sid)
            if state_rel is None:
                log(f"𓈗 STATE_UPDATE warning: unknown id {sid}")
                return
            state_path = resolve(state_rel)
            ensure_dir(os.path.dirname(state_path))
            data = {
                "glyph": "𓊹",
                "id": sid,
                "status": status,
                "note": note,
            }
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"𓊹 STATE_UPDATE wrote: {state_path}")
        elif cmd == "LOG_APPEND":
            msg = line.split("LOG_APPEND", 1)[1].strip()
            msg = msg.strip('"').strip("'")
            log(f"𓏭 {msg}")

    # 𓂋 EIC snapshot
    elif glyph == "𓂋" and cmd == "EIC":
        kv = dict(parse_kv(a) for a in args)
        E = kv.get("E", "0")
        I = kv.get("I", "0")
        C = kv.get("C", "0")
        log(f"𓂋 EIC: E={E}, I={I}, C={C}")

    # 𓁹 MIRROR events
    elif glyph == "𓁹":
        if cmd.upper() == "CHECK":
            log("𓁹 MIRROR CHECK")

    # 𓏣 PHASE
    elif glyph == "𓏣" and cmd == "PHASE":
        kv = dict(parse_kv(a) for a in args)
        name  = kv.get("name")
        fromH = kv.get("from")
        toH   = kv.get("to")
        note  = kv.get("note", "").strip('"').strip("'")
        log(f"𓏣 PHASE {name}: {fromH}→{toH} — {note}")

    # 𓎛 STABILIZE
    elif glyph == "𓎛" and cmd == "STABILIZE":
        log("𓎛 STABILIZE — run complete.")

def run_cgl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            handle(line)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: cgl_interpreter_v0_2.py <file.cgl>")
        sys.exit(1)
    run_cgl(sys.argv[1])
