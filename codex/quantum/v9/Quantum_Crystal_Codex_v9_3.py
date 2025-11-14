#!/usr/bin/env python
import json,math,random,datetime,pathlib
root = pathlib.Path(__file__).resolve().parents[3]
t = datetime.datetime.utcnow().isoformat()
N=64
ph=[random.uniform(0,2*math.pi) for _ in range(N)]
re=sum(math.cos(x) for x in ph)/N
im=sum(math.sin(x) for x in ph)/N
C=(re*re+im*im)**0.5
(root/"codex"/"quantum"/"v9"/"qcx_v9_3_state.json").write_text(
    json.dumps({"ok":True,"C":C,"timestamp":t}, indent=2)
)
