# codex/cgl

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/cgl` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **cgl** subsystem.
- **Why:** This folder exists to isolate `cgl` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/cgl` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `compiler/`
- `engine/`
- `glyph_table/`
- `input/`
- `logs/`
- `manifest/`
- `state/`

### Files

- `README_cgl_v1_0.md`
- `README_cgl_v1_0_1.md`
- `README_cgl_v1_1.md`
- `README_cgl_v1_2.md`
- `cgl_interpreter_v0_2.py`

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
