# codex/logs

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/logs` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **logs** subsystem.
- **Why:** This folder exists to isolate `logs` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/logs` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `closure/`
- `continuity/`
- `feedback_v2/`
- `harmonics_v2/`
- `hre_v3/`
- `hta_v3/`
- `integration/`
- `rcb_v3/`
- `recalibration/`
- `reflection/`
- `resonance/`
- `resonance_v2/`
- `rrb_v3/`
- `synchrony/`
- `tce_v3/`
- _... plus 4 more subdirectories_

### Files

- `codex_cycle_summary_2025-11-11_07-42-11.txt`
- `codex_cycle_summary_2025-11-11_07-47-34.txt`
- `codex_cycle_summary_2025-11-11_07-50-16.txt`
- `codex_cycle_summary_2025-11-11_07-53-51.txt`
- `codex_run_20251103_130545.log`
- `codex_run_20251103_130836.log`
- `dual_verification_20251105_172304.json`
- `harmonic_sync_20251105_173410.json`
- `kernel_validation_20251105_171212.json`
- `reflective_cycle_log.txt`
- `session_20251105_171108.txt`
- `v2_evolution_log_20251105_180618.json`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
