# codex/v0.5

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/v0.5` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **v0.5** subsystem.
- **Why:** This folder exists to isolate `v0.5` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/v0.5` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `orchestrator/`

### Files

- `_codex_alignment_seal.json`
- `_synthesis_manifest.json`
- `alignment_helper.py`
- `gates.py`
- `registry.json`
- `seal_2025-11-03-09-11-33.txt`
- `seal_protocol.py`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
