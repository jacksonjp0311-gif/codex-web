#!/usr/bin/env python
import json,math,datetime,pathlib
root = pathlib.Path(__file__).resolve().parents[2]
t = datetime.datetime.utcnow().isoformat()
sweep=[{"r":r,"phi":0.7*math.exp(-abs(r-1))} for r in [1.0,1.15,1.3,1.45]]
(root/"codex"/"quantum_imaging"/"qim_v1_7_state.json").write_text(
  json.dumps({"ok":True,"timestamp":t,"sweep":sweep}, indent=2)
)
