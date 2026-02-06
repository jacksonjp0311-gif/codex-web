# codex/orchestrator

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/orchestrator` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **orchestrator** subsystem.
- **Why:** This folder exists to isolate `orchestrator` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/orchestrator` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `engine/`
- `glyphs/`
- `ledger/`
- `state/`
- `visuals/`

### Files

- `codex_all_one_v2_4.ps1`
- `codex_all_one_v2_5.ps1`
- `codex_all_one_v2_6.ps1`
- `codex_all_one_v2_6_README.md`
- `codex_all_one_v2_7.ps1`
- `codex_all_one_v2_8.ps1`
- `codex_all_one_v2_8_README.md`
- `codex_all_one_v3_0.ps1`
- `codex_all_one_v3_0_voicebox_patch.ps1`
- `codex_full_loop_v1.ps1`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
