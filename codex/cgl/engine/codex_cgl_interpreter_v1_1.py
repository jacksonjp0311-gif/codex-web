import argparse
import json
import os
from datetime import datetime
from collections import Counter


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def default_glyph_table():
    """
    Seed table with a few core Codex glyphs.
    Each glyph entry:
      id         : unique id (string)
      token      : literal token in .cgl program
      name       : human label
      category   : e.g. elemental, triad, meta, op
      expansion  : semantic meaning / pseudo-code
      tags       : list of extra hints
      created_at : ISO timestamp
    """
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "protocol": "CodexGlyphProtocol",
        "version": "3.0",
        "updated_at": now,
        "glyphs": [
            {
                "id": "core_eye_consciousness",
                "token": "𓂀",
                "name": "Eye of Coherence",
                "category": "triad_consciousness",
                "expansion": "Gomer • Beauty • Coherence • C-channel focus",
                "tags": ["C", "triad", "consciousness", "coherence"],
                "created_at": now,
            },
            {
                "id": "core_energy_oz",
                "token": "𓏲",
                "name": "Oz / Strength / Energy",
                "category": "triad_energy",
                "expansion": "Oz • Strength • Energy • E-channel",
                "tags": ["E", "triad", "energy"],
                "created_at": now,
            },
            {
                "id": "core_information_dabar",
                "token": "𓏤",
                "name": "Dabar / Wisdom / Information",
                "category": "triad_information",
                "expansion": "Dabar • Wisdom • Information • I-channel",
                "tags": ["I", "triad", "information"],
                "created_at": now,
            },
            {
                "id": "core_delta_phi",
                "token": "ΔΦ",
                "name": "Delta Phi",
                "category": "metric",
                "expansion": "|E - I| phase offset; coherence stress",
                "tags": ["metric", "delta_phi"],
                "created_at": now,
            },
            {
                "id": "core_h7",
                "token": "H7",
                "name": "H7 Threshold",
                "category": "metric",
                "expansion": "H7 ≈ 0.70 harmonic coherence threshold",
                "tags": ["metric", "threshold", "coherence"],
                "created_at": now,
            },
            {
                "id": "core_placidity",
                "token": "∿",
                "name": "Placidity Layer",
                "category": "meta",
                "expansion": "∿ Placidity: safe damping / stabilization layer",
                "tags": ["meta", "safety", "stability"],
                "created_at": now,
            },
        ],
    }


def index_glyphs(table):
    by_token = {}
    glyphs = table.get("glyphs", [])
    for g in glyphs:
        token = g.get("token")
        if token is None:
            continue
        by_token[token] = g
    return by_token


def detect_tokens(program_text):
    """
    Simple tokenizer:
    - split on whitespace
    - keep tokens as-is (glyphs or ASCII words)
    """
    raw = program_text.split()
    tokens = [t for t in raw if t.strip() != ""]
    return tokens


def auto_extend_glyph_table(table, tokens):
    """
    For any token not in glyph table → create a placeholder glyph entry.
    """
    now = datetime.utcnow().isoformat() + "Z"
    glyphs = table.get("glyphs", [])
    by_token = index_glyphs(table)

    new_entries = []
    for tok in sorted(set(tokens)):
        if tok in by_token:
            continue
        entry = {
            "id": f"auto_{tok}_{len(glyphs) + len(new_entries)}",
            "token": tok,
            "name": f"Auto-discovered glyph `{tok}`",
            "category": "unknown",
            "expansion": "TODO: define semantic expansion for this glyph.",
            "tags": ["auto", "unknown"],
            "created_at": now,
        }
        new_entries.append(entry)

    if new_entries:
        glyphs.extend(new_entries)
        table["glyphs"] = glyphs
        table["updated_at"] = now

    return table, new_entries


def build_state(program_path, tokens, table, new_glyphs, version, state_path):
    counter = Counter(tokens)
    by_token = index_glyphs(table)
    now = datetime.utcnow().isoformat() + "Z"

    glyph_usage = []
    for tok, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        g = by_token.get(tok)
        glyph_usage.append(
            {
                "token": tok,
                "count": int(count),
                "glyph_id": None if g is None else g.get("id"),
                "name": None if g is None else g.get("name"),
                "category": None if g is None else g.get("category"),
            }
        )

    state = {
        "module": "codex_cgl",
        "version": version,
        "timestamp": now,
        "program_path": program_path,
        "metrics": {
            "total_tokens": int(len(tokens)),
            "unique_tokens": int(len(counter)),
            "new_glyphs": int(len(new_glyphs)),
        },
        "glyph_usage": glyph_usage,
        "new_glyphs": new_glyphs,
        "glyph_table_snapshot": {
            "protocol": table.get("protocol"),
            "version": table.get("version"),
            "updated_at": table.get("updated_at"),
            "total_glyphs": int(len(table.get("glyphs", []))),
        },
    }

    save_json(state_path, state)
    return state


def ensure_sample_program(program_path):
    """
    If no .cgl program exists yet, create a small sample to demonstrate.
    """
    if os.path.exists(program_path):
        return
    sample = (
        "𓂀 𓏲 𓏤 ΔΦ H7 ∿\n"
        "# sample CGL program: eye → energy → information → delta_phi → threshold → placidity\n"
        "𓂀 ASCEND 𓏲 FLOW ΔΦ STABILIZE ∿\n"
    )
    os.makedirs(os.path.dirname(program_path), exist_ok=True)
    with open(program_path, "w", encoding="utf-8") as f:
        f.write(sample)


def main():
    parser = argparse.ArgumentParser(
        description="Codex CGL v1.1 — Auto-Evolving Glyph Interpreter"
    )
    parser.add_argument("--glyph-table", required=True)
    parser.add_argument("--program", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    os.makedirs(args.state_dir, exist_ok=True)

    # 1) Ensure program exists
    ensure_sample_program(args.program)

    # 2) Load glyph table (or create default)
    glyph_table = load_json(args.glyph_table, None)
    if glyph_table is None:
        glyph_table = default_glyph_table()

    # 3) Load program and detect tokens
    with open(args.program, "r", encoding="utf-8") as f:
        program_text = f.read()
    tokens = detect_tokens(program_text)

    # 4) Auto-extend glyph table with new tokens
    glyph_table, new_glyphs = auto_extend_glyph_table(glyph_table, tokens)

    # 5) Save updated glyph table
    save_json(args.glyph_table, glyph_table)

    # 6) Build and save state JSON
    state_path = os.path.join(args.state_dir, f"cgl_state_{args.version}.json")
    state = build_state(
        program_path=args.program,
        tokens=tokens,
        table=glyph_table,
        new_glyphs=new_glyphs,
        version=args.version,
        state_path=state_path,
    )

    # 7) Emit console summary
    print(f"[CGL v1.1] Program: {args.program}")
    print(f"[CGL v1.1] Tokens: {state['metrics']['total_tokens']} total, "
          f"{state['metrics']['unique_tokens']} unique")
    print(f"[CGL v1.1] New glyphs this run: {state['metrics']['new_glyphs']}")
    print(f"[CGL v1.1] Glyph table now has "
          f"{state['glyph_table_snapshot']['total_glyphs']} entries")
    print(f"[CGL v1.1] State written to {state_path}")
    if new_glyphs:
        print("[CGL v1.1] New glyphs:")
        for g in new_glyphs:
            print(f"  - {g['token']} → {g['id']} ({g['category']})")


if __name__ == "__main__":
    main()
