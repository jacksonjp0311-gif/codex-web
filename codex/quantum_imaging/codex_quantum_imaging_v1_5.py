#!/usr/bin/env python
# 🌀 QIM v1.5 — Resonance Sweep
import json,math,datetime,pathlib
p = pathlib.Path(__file__).parent
t = datetime.datetime.utcnow().isoformat()
sweep=[{"r":r,"phi":0.7*math.exp(-abs(r-1))} for r in [1.0,1.2,1.4,1.6]]
(p/"qim_v1_5_state.json").write_text(json.dumps({"ok":True,"timestamp":t,"sweep":sweep}, indent=2))
