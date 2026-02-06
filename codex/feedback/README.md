# codex/feedback

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/feedback` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **feedback** subsystem.
- **Why:** This folder exists to isolate `feedback` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/feedback` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `applied/`
- `ledger/`
- `state/`

### Files

- `.gitkeep`
- `codex_autobalance_v1_2.ps1`
- `codex_continuity_ledger_v1_0.ps1`
- `codex_continuity_synth_v2_1.ps1`
- `codex_continuity_synth_v2_1_README.md`
- `codex_feedback_20251111_103756.json`
- `codex_feedback_20251111_103934.json`
- `codex_feedback_20251111_104729.json`
- `codex_feedback_20251111_105457.json`
- `codex_feedback_echo_v4_0.ps1`
- `codex_feedback_gateway_v2_1.ps1`
- `codex_feedback_harmonic_v4_0.ps1`
- `codex_feedback_integrator_v1_0.ps1`
- `codex_feedback_stim_20251111_185305.json`
- `codex_feedback_summary.json`
- _... plus 30 more files_

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
