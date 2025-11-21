# Codex Glyph Language (CGL) v1.1 — Interpreter + Opcode Layer

Role:
- Define a base Codex Glyph Language over triadic channels (Energy / Information / Consciousness).
- Load glyph programs (.cgl), tokenize glyphs, and build a simple AST.
- Attach opcodes + actions to each glyph to form an execution plan.
- Compute triad metrics and ΔΦ-style balance metrics.
- Emit state JSON, manifest, ledger entry, and run log.
- Prepare for future compilation into full Codex orchestrators and engines.

Glyphs v1.1 (with opcodes):

- 𓏲 : Energy (Oz / Strength / Flow) — channel E — opcode ENERGY_ACTIVATE
- 𓏤 : Information (Dabar / Word / Structure) — channel I — opcode INFO_STRUCTURE
- 𓂀 : Consciousness (Gomer / Eye / Coherence) — channel C — opcode CONSCIOUS_REFLECT
- 𓊹 : All-One Orchestrator — channel C — opcode ALL_ONE_CONTEXT
- 𓋹 : Codex OS / LumenShell Node — channel I — opcode OS_BIND
- 𓇯 : Solar Resonance Node — channel E — opcode SOLAR_ROUTE
- 𓆳 : Quantum Imaging Node — channel C — opcode QIM_ROUTE
- 𓐘 : GIZA Geometry Node — channel I — opcode GIZA_ROUTE
- 𓂻 : Step / Movement — channel E — opcode STEP_SEQ
- 𓅓 : Self / Subject — channel C — opcode SELF_BIND

Execution plan:

- v1.1 generates an \execution_plan\ array in the state JSON:
  - Each entry: { step_index, position, glyph, id, opcode, channel, role, description }.
  - This captures the intended routing without yet executing modules.
  - v1.2 will compile this plan into All-One orchestrator scripts.

Metrics:

- E/I/C glyph counts and fractions.
- ΔΦ-proxy based on variance of E/I/C counts.
- H7-alignment score (how balanced E/I/C channels are; 1.0 is perfectly balanced).

Outputs:

- state/v1_1/cgl_state_v1_1.json
- manifest/cgl_manifest_v1_1.json
- logs/ledger/cgl_ledger.jsonl
- logs/run/cgl_v1_1_run_<timestamp>.log

Aligned with:

- Codex Memory Core v2.0
- Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)
- H-layer evolution (7, 8, 10, 12, 15, 16, 17, 18, 21, 23, 30, 32, 45)

Next evolution steps:

- v1.2: Compile execution_plan into All-One orchestrator scripts (PS + Python bindings).
- v1.3: Add visual glyph maps + radar/ΔΦ plots.
- v2.x: CGL as a first-class Codex meta-language for module orchestration.
