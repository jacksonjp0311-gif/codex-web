#!/usr/bin/env python
# 🌀 QIM v1.4 — ΔΦ sweep (stub)
import json, math, datetime, pathlib
p = pathlib.Path(__file__).parent
p.mkdir(parents=True, exist_ok=True)
t = datetime.datetime.utcnow().isoformat()
sweep = [{"r": r, "phi_delta": 0.7 * math.exp(-abs(r-1.0))} for r in [1.00,1.15,1.30]]
(p/"qim_v1_4_state.json").write_text(json.dumps({"ok":True,"version":"1.4","timestamp":t,"sweep":sweep}, indent=2))
