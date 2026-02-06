# codex/third_eye

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/third_eye` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **third_eye** subsystem.
- **Why:** This folder exists to isolate `third_eye` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/third_eye` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `bridge/`
- `legacy/`
- `logs/`
- `manifest/`
- `modules/`
- `state/`
- `visuals/`

### Files

- `codex_third_eye_harmonic_v2_3.ps1`
- `codex_third_eye_mediation_v2_2.ps1`
- `codex_third_eye_mediation_v2_2B_daemon.ps1`
- `codex_third_eye_predictive_v2_3C.ps1`
- `codex_third_eye_reflexive_v2_1.ps1`
- `codex_third_eye_reflexive_v2_3A.ps1`
- `codex_third_eye_reflexive_v2_3B.ps1`
- `manifest_thirdeye.json`
- `manifest_thirdeye_v1_6_2.json`
- `manifest_thirdeye_v1_7.json`
- `manifest_thirdeye_v1_8.json`
- `manifest_thirdeye_v1_9.json`
- `manifest_thirdeye_v2_0a.json`
- `third_eye_state_2025-11-10_18-50-39.json`
- `third_eye_state_2025-11-10_18-53-28.json`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
