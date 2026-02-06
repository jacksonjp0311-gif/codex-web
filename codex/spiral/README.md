# codex/spiral

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/spiral` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **spiral** subsystem.
- **Why:** This folder exists to isolate `spiral` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/spiral` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `core/`
- `logs/`
- `modules/`
- `state/`

### Files

- `Codex_Orchestrator_v4_6.ps1`
- `Codex_Orchestrator_v5_1.ps1`
- `SpiralEngine.ps1`
- `codex_spiral_core_v7_3.ps1`
- `reflection_log.txt`
- `spiral_log.txt`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
