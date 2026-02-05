# Codex Runtime (`codex/`)

This directory is the core runtime domain of `codex-web`.
It contains symbolic engines, orchestration modules, state/ledger systems, observability surfaces, and domain-specific submodules.

## Purpose

`codex/` is designed to host:

- runtime engines and orchestration flows,
- versioned module families,
- persistent state/log/ledger artifacts,
- handoff and continuity mechanisms,
- visualization and dashboard layers.

## Directory Guide (first-level)

| Directory | Purpose |
|---|---|
| `core/` | Foundational laws, gates, registry, ledger sync, and orchestrator primitives. |
| `orchestrator/` | Cross-module orchestration engine state, visuals, glyphs, and control flow. |
| `spiral/` | Recursive spiral engine and related cycle modules. |
| `handoff/` | Session continuity, handoff manifests/state, and handoff scripts. |
| `observability/` | Runtime observability assets and law/trace instrumentation. |
| `dashboard/` | Dashboard engines and state/visual outputs. |
| `quantum_imaging/` | Imaging engine family with versioned state/log/ledger/visual outputs. |
| `quantum/`, `quantum.crystal/` | Quantum module families and versioned evolution tracks. |
| `guardian/`, `third_eye/`, `voice/`, `voicebox/` | Supervisory, mediation, and interaction-oriented module families. |
| `cgl/`, `glyphs/` | Glyph language, compilation, and symbolic expression assets. |
| `dna/`, `memory/`, `state/`, `data/` | Stateful memory/data and model-layer runtime persistence. |
| `feedback/`, `evolution/`, `logs/` | Feedback loops, evolution history, and runtime logging domains. |
| `visuals/`, `web/` | Visualization/rendering assets and web-facing runtime pieces. |
| `tools/`, `utils/`, `config/` | Operational helpers, utilities, and configuration. |
| `archive/`, `ancient/`, `mirror_temp/` | Historical/legacy and temporary mirror work areas. |
| `v0.5/`, `v2/`, `v3/` | Versioned runtime eras retained for continuity/reference. |

## Suggested Entry Points

Start here if you are onboarding into `codex/`:

1. `core/laws.py` and `core/gates.py` for conceptual runtime foundations.
2. `core/orchestrator/codex_orchestrator.ps1` for orchestration baseline.
3. `handoff/codex_handoff.ps1` for continuity and resume behavior.
4. `dashboard/codex_dashboard_engine_v1_3.py` for visualization path.
5. `quantum_imaging/README.md` for a representative deep module family.

## Working Conventions

- Prefer additive, versioned changes for major module revisions.
- Keep generated outputs (state/log/visual artifacts) in the appropriate module subtrees.
- Avoid introducing new top-level categories unless they represent a durable domain.
- When creating a new module family, include a local README explaining purpose, inputs, outputs, and run flow.

## Known Improvement Opportunities

- Normalize and de-duplicate historical state/log snapshots where safe.
- Standardize module-level README format across major domains.
- Add lightweight integrity checks for key PowerShell orchestration scripts.
