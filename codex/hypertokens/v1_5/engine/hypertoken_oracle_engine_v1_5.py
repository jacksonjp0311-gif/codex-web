#!/usr/bin/env python3
"""
CODEX–HYPERTOKENS v1.5 — STATE SEALED ENGINE
Always emits state.json (READY or FAIL).
"""

import json, sys
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def emit(path, state):
    Path(path).write_text(json.dumps(state, indent=2), encoding="utf-8")

def main(model_id, out_state):

    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
    except Exception as e:
        emit(out_state,{
            "version":"1.5",
            "timestamp":now(),
            "verdict":"IMPORT_FAIL",
            "error":repr(e)
        })
        return 2

    try:
        tok = AutoTokenizer.from_pretrained(model_id)
        mdl = AutoModel.from_pretrained(model_id)
        mdl.eval()

        emit(out_state,{
            "version":"1.5",
            "timestamp":now(),
            "model":model_id,
            "verdict":"READY_FOR_SWEEPS"
        })
        return 0

    except Exception as e:
        emit(out_state,{
            "version":"1.5",
            "timestamp":now(),
            "model":model_id,
            "verdict":"MODEL_LOAD_FAIL",
            "error":repr(e)
        })
        return 3

if __name__=="__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
