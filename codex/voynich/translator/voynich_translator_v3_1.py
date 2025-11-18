#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Voynich Translator v3.1 — REL+STATE → Proto-Semantic Field
Hybrid node for Codex Voynich OS.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_graph(path):
    records = []
    p = Path(path)
    if not p.exists():
        return records
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                # skip malformed
                continue
    return records


def state_to_tags(state):
    depth = (state or {}).get("depth", "UNKNOWN")
    phase = (state or {}).get("phase", "UNKNOWN")
    flow  = (state or {}).get("flow",  "UNKNOWN")

    depth_tag = {
        "CORE": "inner",
        "PERIPHERY": "outer",
        "NEUTRAL": "field",
        "UNKNOWN": "unknown"
    }.get(depth, "unknown")

    phase_tag = {
        "ACTIVE": "rising",
        "PASSIVE": "resting",
        "UNKNOWN": "indeterminate"
    }.get(phase, "indeterminate")

    flow_tag = {
        "INPUT": "intake",
        "OUTPUT": "release",
        "NEUTRAL": "circulation",
        "UNKNOWN": "unresolved"
    }.get(flow, "unresolved")

    return depth_tag, phase_tag, flow_tag


def relation_to_phrase(rel):
    if not rel:
        return "acts upon"

    rel = str(rel).lower()

    if rel == "expression":
        return "expresses toward"
    if rel == "composition":
        return "is composed into"
    if rel == "origin":
        return "arises from"

    # default functional relation
    return "acts on"


def record_to_sentence(rec):
    folio = rec.get("folio", "?")
    subj  = rec.get("subject_raw", "")
    obj   = rec.get("object_raw", "")
    rel   = rec.get("relation", "function")
    state = rec.get("state", {})

    d_tag, p_tag, f_tag = state_to_tags(state)
    rel_phrase = relation_to_phrase(rel)

    # proto-semantic English-ish gloss
    sentence = f"({folio}) {subj} {rel_phrase} {obj} [{d_tag}/{p_tag}/{f_tag}]"
    return sentence, (d_tag, p_tag, f_tag)


def build_translation(records):
    translation = []
    state_counts = Counter()
    rel_counts = Counter()
    folio_map = defaultdict(int)

    for rec in records:
        clause_id = rec.get("clause_id", "")
        relation  = rec.get("relation", "function")
        state     = rec.get("state", {})
        sentence, state_tags = record_to_sentence(rec)

        translation.append({
            "clause_id": clause_id,
            "folio": rec.get("folio", ""),
            "relation": relation,
            "state": state,
            "state_tags": {
                "depth": state_tags[0],
                "phase": state_tags[1],
                "flow":  state_tags[2],
            },
            "proto_sentence": sentence,
            "tokens": rec.get("tokens", [])
        })

        rel_counts[relation] += 1
        state_key = (state.get("depth", "UNKNOWN"),
                     state.get("phase", "UNKNOWN"),
                     state.get("flow", "UNKNOWN"))
        state_counts[state_key] += 1
        folio_map[rec.get("folio", "")] += 1

    summary = {
        "total_clauses": len(translation),
        "relations": rel_counts,
        "states": {f"{d}|{p}|{f}": c for (d, p, f), c in state_counts.items()},
        "folios": folio_map,
    }
    return translation, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True,
                        help="Path to Voynich REL+STATE graph JSONL")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to write translation sample JSON")
    parser.add_argument("-s", "--summary", required=True,
                        help="Path to write translation summary JSON")
    args = parser.parse_args()

    records = load_graph(args.input)
    translation, summary = build_translation(records)

    # Write outputs
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(translation, f, ensure_ascii=False, indent=2)

    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(records)} graph records.")
    print(f"Wrote translation sample → {args.output}")
    print(f"Wrote translation summary → {args.summary}")


if __name__ == "__main__":
    main()
