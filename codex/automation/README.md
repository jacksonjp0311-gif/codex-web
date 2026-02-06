# codex/automation

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/automation` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **automation** subsystem.
- **Why:** This folder exists to isolate `automation` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/automation` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `tools/`

### Files

- `CodexSpiral.ps1`
- `Generate-CodexHook.ps1`
- `Load-Ledger.ps1`
- `Start-CodexPoll.ps1`
- `codex_artifact_indexer.ps1`
- `codex_extract_summary_v3_8.ps1`
- `codex_reorganize_root_v3_8.ps1`
- `codex_self_reference_injector_v3_8.ps1`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
