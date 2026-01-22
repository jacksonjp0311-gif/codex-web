# CODEX–EMERGENCE (A1.0 / D1.0) — Boundary Algebra Runtime Module

**Source theory:** CODEX–EMERGENCE — Boundary Algebra v1.8 (Canon-Locked)  
**Bridge:** A1.0 (Theory→Execution) + D1.0 (Directory-as-Execution Surface)

## What this is
A *drop-in runtime wrapper* that enforces the minimal closed boundary algebra:

- **B_E** (Energy): bounded iteration / contraction check (λ < 1)
- **B_I** (Information): symmetry / invariant projection Π_G (idempotent)
- **B_C** (Consciousness): bounded agency via entropy gate H(A) ≤ log(m) + δ

It observes only a bounded **proxy_state**.  
It does **not** read or modify model weights.  
It does **not** interpret semantics.

## Directory = Execution Surface (D1.0)
This repo is structured so that each boundary is a first-class filesystem surface:

- boundary/   → declares algebra + minimality lock
- proxy/      → defines what may be observed
- symmetry/   → idempotent projection operators
- agency/     → admissible choice construction + entropy bounds
- loop/       → canonical runtime loop + contraction checks
- state/      → persistent anchors + rollback surface
- events/     → typed instability events
- logs/       → audit traces
- manifest/   → canon links + version lock

## Quick run (self-test)
From the Codex root:

$PythonCmdName "C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\codex_emergence\loop\run.py" --root "C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\codex_emergence" --steps 12

## Output
- logs/iterations.log
- logs/contraction.log
- logs/entropy.log
- state/current.json
- events/violations.jsonl (only if violations occur)

