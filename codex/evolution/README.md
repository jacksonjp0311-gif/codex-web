# codex/evolution

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/evolution` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **evolution** subsystem.
- **Why:** This folder exists to isolate `evolution` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/evolution` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `backups/`

### Files

- `.codex_trb_debug.log`
- `codex_auto_cycle_v1.8.ps1`
- `codex_evolution_state_v2.0_20251105_180618.json`
- `codex_handoff_v0.7.log`
- `codex_handoff_v3_7.ps1`
- `codex_trb_debug.log`
- `codex_trb_v2_8.log`
- `codex_trb_v2_9.log`
- `codex_v1.7.1.ps1`
- `codex_v2_1_selfsync_manifest_20251105_181132.json`
- `codex_v2_core_manifest_20251105_180921.json`
- `codex_v2_manifest_20251105_180618.json`
- `codex_v3_0_evolution_20251105_183342.json`
- `codex_v3_0_evolution_20251105_183500.json`
- `codex_v3_1_2_tce_evolution_20251105_184115.json`
- _... plus 10 more files_

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
