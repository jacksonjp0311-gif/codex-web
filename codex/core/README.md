# codex/core

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/core` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **core** subsystem.
- **Why:** This folder exists to isolate `core` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/core` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `kernel/`
- `orchestrator/`
- `symbolic/`

### Files

- `__init__.py`
- `_codex_alignment_seal.json`
- `active_layer.txt`
- `alignment.py`
- `alignment_helper.py`
- `codex_integrity_sentinel.ps1`
- `gates.py`
- `harmonics.json`
- `laws.py`
- `laws_grok_v07.py`
- `ledger_sync.py`
- `quantum_validator.py`
- `registry.json`
- `seal_2025-11-03-09-11-33.txt`
- `seal_protocol.py`
- _... plus 1 more files_

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
