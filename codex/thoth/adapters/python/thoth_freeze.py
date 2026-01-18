#!/usr/bin/env python3
# =============================================================================
# 𓂀 CODEX–THOTH FREEZE EXECUTOR — v1.9 (COMPLIANT)
# =============================================================================
# AUTHOR: James Paul Jackson (@unifiedenergy11)
#
# NON-CLAIMS:
#   - No target execution, optimization, refactor
#   - No interpretation logic
#   - No agent behavior
#   - No runtime coupling
#
# INVARIANTS:
#   1) Append-only history
#   2) No retroactive enrichment
#   3) Observation before interpretation
#   4) Structure over semantics
#   5) Scope sovereignty
# =============================================================================

import os, sys, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(p: Path, obj):
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8", "replace"))

def safe_rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def is_hidden(path: Path) -> bool:
    parts = path.parts
    for part in parts:
        if part.startswith("."):
            return True
    return False

def list_files(route_path: Path, caps: dict, include=None, exclude=None):
    max_files = int(caps.get("max_files_per_route", 5000))
    max_depth = int(caps.get("max_depth", 32))
    out = []
    route_path = route_path.resolve()

    def allow_by_glob(rel: str, globs):
        if not globs:
            return True
        for g in globs:
            if Path(rel).match(g):
                return True
        return False

    def blocked_by_glob(rel: str, globs):
        if not globs:
            return False
        for g in globs:
            if Path(rel).match(g):
                return True
        return False

    for p in sorted(route_path.rglob("*")):
        if len(out) >= max_files:
            break
        try:
            if not p.is_file():
                continue
        except Exception:
            continue

        rel = safe_rel(route_path, p)
        depth = rel.count("/")
        if depth > max_depth:
            continue
        if is_hidden(Path(rel)):
            continue
        if not allow_by_glob(rel, include):
            continue
        if blocked_by_glob(rel, exclude):
            continue
        out.append(p)
    return out

def file_fingerprint(p: Path, max_bytes: int):
    st = p.stat()
    size = int(st.st_size)
    mtime = int(st.st_mtime)
    read_n = min(size, max_bytes)
    data = b""
    try:
        with p.open("rb") as f:
            data = f.read(read_n)
    except Exception:
        data = b""
    partial_hash = sha256_bytes(data)
    return {
        "size": size,
        "mtime": mtime,
        "partial_sha256": partial_hash,
        "read_bytes": read_n,
    }

def route_index(root: Path, route_id: str, route_rel: str, settings: dict, include=None, exclude=None):
    caps = settings.get("caps", {})
    max_bytes = int(caps.get("max_bytes_per_file", 200000))
    route_path = (root / route_rel).resolve()
    files = []
    byte_count = 0
    file_count = 0

    if not route_path.exists():
        return {
            "path": route_rel,
            "missing": True,
            "file_count": 0,
            "byte_count": 0,
            "route_hash": sha256_text(route_rel + "|MISSING"),
            "files": []
        }

    listed = list_files(route_path, caps, include=include, exclude=exclude)
    for p in listed:
        rel = safe_rel(root, p)
        fp = file_fingerprint(p, max_bytes)
        file_count += 1
        byte_count += int(fp.get("size", 0))
        files.append({
            "rel": rel,
            "size": fp["size"],
            "mtime": fp["mtime"],
            "partial_sha256": fp["partial_sha256"],
            "read_bytes": fp["read_bytes"]
        })

    # route hash: stable aggregate of (rel,size,mtime,partial_hash)
    h = hashlib.sha256()
    h.update(route_rel.encode("utf-8"))
    for f in files:
        line = f'{f["rel"]}|{f["size"]}|{f["mtime"]}|{f["partial_sha256"]}\n'
        h.update(line.encode("utf-8"))
    route_hash = h.hexdigest()

    return {
        "path": route_rel.replace("\\", "/"),
        "missing": False,
        "file_count": file_count,
        "byte_count": byte_count,
        "route_hash": route_hash,
        "files": files
    }

def build_change_tree(root: Path, route_rel: str, route_files: list, prev_set: set, curr_set: set):
    """
    Compressed change tree:
    - only include paths in symmetric-diff (added/removed/changed membership)
    - represent directories as nodes with children
    """
    # simple membership-based delta + path normalization
    changed = sorted(list((prev_set ^ curr_set)))
    # If file still exists in both sets but contents changed, prev_set==curr_set won't catch it;
    # we also mark "changed" files via route_hash delta at snapshot level.
    # tree here is "where" changes are, not "why".

    def insert(tree, parts, leaf):
        node = tree
        for part in parts:
            if "children" not in node:
                node["children"] = {}
            if part not in node["children"]:
                node["children"][part] = {"type": "dir", "name": part, "children": {}}
            node = node["children"][part]
        # leaf
        node["children"][leaf] = {"type": "file", "name": leaf}

    tree = {"type": "dir", "name": Path(route_rel).name, "collapsed": False, "children": {}}
    for rel in changed:
        if not rel.startswith(route_rel.replace("\\", "/")):
            continue
        sub = rel[len(route_rel):].lstrip("/").split("/")
        if len(sub) == 1 and sub[0]:
            insert(tree, [], sub[0])
        if len(sub) > 1:
            insert(tree, sub[:-1], sub[-1])

    def finalize(node):
        if node.get("type") == "file":
            return node
        ch = node.get("children", {})
        # convert dict→list for stable json
        children_list = []
        for k in sorted(ch.keys()):
            children_list.append(finalize(ch[k]))
        node["children"] = children_list
        return node

    return finalize(tree)

def cap_text(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n…[CAPPED]…\n"

def freeze_outputs(root: Path, route_id: str, route_rel: str, idx: dict, settings: dict, out_dir: Path):
    """
    Produce output/route_*.txt with:
    - file list and hashes
    - optional capped text excerpts for text files
    """
    caps = settings.get("caps", {})
    max_bytes = int(caps.get("max_bytes_per_file", 200000))
    max_text = int(caps.get("max_text_chars_per_file", 20000))
    text_exts = set([e.lower() for e in settings.get("text_extensions", [])])
    bin_exts  = set([e.lower() for e in settings.get("binary_extensions", [])])

    lines = []
    lines.append(f"THOTH v1.9 OUTPUT — route_id={route_id} path={route_rel}")
    lines.append(f"timestamp={now_iso()}")
    lines.append("")

    files = idx.get("files", [])
    for f in files:
        rel = f.get("rel")
        size = f.get("size")
        mtime = f.get("mtime")
        ph = f.get("partial_sha256")
        ext = (Path(rel).suffix or "").lower()

        lines.append("────────────────────────────────────────")
        lines.append(f"FILE : {rel}")
        lines.append(f"SIZE : {size} bytes")
        lines.append(f"MTIME: {mtime}")
        lines.append(f"HASH : {ph}")
        lines.append(f"TYPE : {ext if ext else '(none)'}")

        p = (root / rel).resolve()
        # text excerpt (capped) ONLY for text-like, skip binary
        if ext in bin_exts:
            lines.append("[BINARY] excerpt skipped")
            continue

        if (ext in text_exts) or (ext == "" and size < max_bytes):
            try:
                raw = p.read_bytes()
                # decode forgiving
                txt = raw.decode("utf-8", "replace")
                txt = cap_text(txt, max_text)
                lines.append("")
                lines.append("[TEXT EXCERPT — CAPPED]")
                lines.append(txt)
            except Exception:
                lines.append("[TEXT] read failed")
        else:
            lines.append("[NON-TEXT] excerpt skipped")

    out_path = out_dir / f"route_{route_id}.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")

def next_seq(day_dir: Path) -> str:
    day_dir.mkdir(parents=True, exist_ok=True)
    existing = []
    for p in day_dir.iterdir():
        if p.is_dir() and p.name.isdigit():
            existing.append(int(p.name))
    n = (max(existing) + 1) if existing else 1
    return f"{n:03d}"

def main(thoth_root: Path, repo_root: Path):
    cfg_map = read_json(thoth_root / "config" / "map.json", {"version":"1.9","scope":[]})
    settings = read_json(thoth_root / "config" / "settings.json", {"version":"1.9","caps":{}})
    prev_index = read_json(thoth_root / "runtime" / "index.json", {"version":"1.9","timestamp":"1970-01-01T00:00:00Z","routes":{}})

    scope = cfg_map.get("scope", [])
    routes = {}

    for r in scope:
        rid = r.get("id")
        rpath = r.get("path")
        include = r.get("include")
        exclude = r.get("exclude")
        if not rid or not rpath:
            continue
        routes[rid] = route_index(repo_root, rid, rpath, settings, include=include, exclude=exclude)

    curr_index = {"version":"1.9","timestamp":now_iso(),"routes": routes}

    # changed routes: route_hash delta or missing flip
    changed = []
    for rid, cur in routes.items():
        prev = (prev_index.get("routes") or {}).get(rid)
        if prev is None:
            changed.append(rid)
            continue
        if prev.get("route_hash") != cur.get("route_hash"):
            changed.append(rid)
            continue
        if bool(prev.get("missing", False)) != bool(cur.get("missing", False)):
            changed.append(rid)
            continue

    # snapshot folder: runtime/memory/YYYY-MM-DD/###/
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = thoth_root / "runtime" / "memory" / day
    seq = next_seq(day_dir)
    snap_dir = day_dir / seq
    out_dir = snap_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    frame_id = f"default-{day.replace('-','')}-{seq}"
    snapshot = {
        "version":"1.9",
        "timestamp": now_iso(),
        "frame_id": frame_id,
        "seq": seq,
        "declared_scope_map": str(thoth_root / "config" / "map.json"),
        "changed_routes": changed,
        "non_claims": [
            "no execution semantics",
            "no interpretation logic",
            "no agent behavior",
            "no runtime coupling"
        ],
        "invariants": [
            "append_only_history",
            "no_retroactive_enrichment",
            "observation_before_interpretation",
            "structure_over_semantics",
            "scope_sovereignty"
        ]
    }

    # change_map per changed route (compressed location map)
    change_map = {"version":"1.9","timestamp":now_iso(),"routes":{}}

    for rid in changed:
        cur = routes.get(rid, {})
        route_rel = cur.get("path", "")
        prev = (prev_index.get("routes") or {}).get(rid) or {}
        prev_files = set([f.get("rel") for f in (prev.get("files") or []) if f.get("rel")])
        curr_files = set([f.get("rel") for f in (cur.get("files") or []) if f.get("rel")])

        change_map["routes"][rid] = build_change_tree(repo_root, route_rel, cur.get("files") or [], prev_files, curr_files)

        # freeze outputs (structure + capped excerpts)
        try:
            freeze_outputs(repo_root, rid, route_rel, cur, settings, out_dir)
        except Exception:
            # never fail whole run on outputs
            pass

    # write snapshot artifacts (append-only)
    write_json(snap_dir / "snapshot.json", snapshot)
    write_json(snap_dir / "change_map.json", change_map)
    write_json(snap_dir / "index.json", curr_index)

    # update latest baseline (not retroactive; baseline is current reference)
    write_json(thoth_root / "runtime" / "index.json", curr_index)

    # dashboard update (append-only history list)
    hist_path = thoth_root / "dashboard" / "data" / "history.json"
    met_path  = thoth_root / "dashboard" / "data" / "metrics.json"

    hist = read_json(hist_path, {"latest": None, "items": []})
    item = {
        "timestamp": snapshot["timestamp"],
        "frame_id": frame_id,
        "seq": seq,
        "changed_routes": changed,
        "snapshot_dir": str(snap_dir).replace("\\","/")
    }
    hist["items"].append(item)
    hist["latest"] = item
    write_json(hist_path, hist)

    metrics = read_json(met_path, {"last_run": None, "runs": 0})
    metrics["runs"] = int(metrics.get("runs", 0)) + 1
    metrics["last_run"] = {
        "timestamp": snapshot["timestamp"],
        "changed_routes": len(changed),
        "frame_id": frame_id
    }
    write_json(met_path, metrics)

    print("THOTH v1.9 freeze complete.")
    print(f"snapshot_dir: {snap_dir}")

if __name__ == "__main__":
    # Usage: thoth_freeze.py THOTH_ROOT REPO_ROOT
    if len(sys.argv) != 3:
        print("Usage: thoth_freeze.py THOTH_ROOT REPO_ROOT", file=sys.stderr)
        sys.exit(1)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
