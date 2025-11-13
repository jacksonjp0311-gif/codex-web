#!/usr/bin/env python
# Codex VoiceBox v3.1 — triadic expression glyph
import json, datetime, pathlib, sys

def main():
    if len(sys.argv) > 1:
        root = pathlib.Path(sys.argv[1]).resolve()
    else:
        root = pathlib.Path(__file__).resolve().parents[2]

    state_dir = root / "codex" / "voicebox" / "state_v3_1"
    state_dir.mkdir(parents=True, exist_ok=True)

    t = datetime.datetime.utcnow().isoformat()
    glyph = {
        "protocol": "CodexTriadicGlyph",
        "version": "1.1",
        "mode": "A",
        "context": "voicebox_v3_1_memory_weave_v2_1_forced_overwrite",
        "triad": {
            "energy":       {"glyph": "E", "value": 1.0},
            "information":  {"glyph": "I", "value": 1.0},
            "consciousness":{"glyph": "C", "value": 0.70}
        },
        "H7": 0.70,
        "timestamp": t,
        "note": "A = evolution_through_reorganization (forced overwrite anchoring)"
    }

    out_path = state_dir / "voicebox_state_v3_1.json"
    out_path.write_text(json.dumps(glyph, indent=2))

if __name__ == "__main__":
    main()
