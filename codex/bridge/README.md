# codex/bridge

Auto-generated on 2026-02-06 07:28:54Z.

## 5 W's

- **What:** `codex/bridge` is a Codex runtime domain folder that stores module logic, state, logs, or related artifacts for the **bridge** subsystem.
- **Why:** This folder exists to isolate `bridge` responsibilities, reduce coupling with other domains, and make evolution/versioning safer over time.
- **Who:** Primary maintainers are Codex runtime contributors and automation/orchestration operators working inside this repository.
- **When:** Use this folder whenever work is directly related to this subsystem’s runtime behavior, state transitions, or outputs.
- **Where:** Path: `codex/bridge` (within the core Codex runtime tree).

## Mini directory

### Subdirectories

- `LumenShell_Link/`
- `gpt_v2_0/`
- `gpt_v2_1/`
- `gpt_v3_0/`
- `gpt_v3_1/`
- `inbox/`
- `outbox/`
- `state/`

### Files

- `bridge_log.txt`
- `bridge_message_schema.json`
- `codex_bridge_config.json`
- `codex_bridge_echo_v1_2.ps1`
- `codex_bridge_v1_0.ps1`
- `codex_bridge_v1_1.ps1`
- `codex_bridge_v1_2.ps1`
- `codex_bridge_v1_2_README.md`
- `codex_bridge_v1_3.ps1`
- `codex_bridge_v1_6.ps1`
- `codex_message_harvest.ps1`
- `codex_smart_feedback_bridge_v1_0.ps1`
- `codex_smart_feedback_bridge_v1_0_README.md`
- `conversation.jsonl`
- `echo_log.txt`
- _... plus 4 more files_

## Notes

- Keep subsystem-specific artifacts within this folder where possible.
- Add module-specific run instructions here as this area matures.
