# codex-web

A multi-runtime research workspace for the Codex project, combining orchestration scripts, Python automation, and web interfaces in a single repository.

## Repository Goals

- Provide a home for Codex orchestration and automation tooling.
- Track operational state and ledger workflows.
- Host supporting web UIs and integration utilities.
- Preserve historical artifacts while keeping active code maintainable.

## Current Stack

- **PowerShell** for orchestration and operational workflows.
- **Python** for data processing, watcher automation, and ledger logic.
- **JavaScript/TypeScript (React)** for UI surfaces and feedback tools.

## Top-Level Layout

> Note: the `codex/` directory remains untouched in this cleanup pass by request.

- `approval-ui/` — React-based approval interface.
- `codex/` — core Codex module tree (intentionally unchanged in this pass).
- `codex_watcher/` — Python watcher CLI for inbox validation and ledger append flow.
- `copilot-feedback/` — feedback ingestion/orchestration and UI components.
- `core/` — foundational policy/law/handoff assets.
- `data/root-state/` — root-level JSON/state artifacts that were previously loose in `/`.
- `docs/archive/` — archived textual artifacts moved out of root.
- `interface/` — connector and protocol integration layer.
- `scripts/root-utilities/` — root utility scripts moved out of `/` for cleaner structure.
- `src/` — PowerShell module source.
- `tests/` — PowerShell unit/integration tests.
- `tools/` — analysis and coverage utilities.

## Root Cleanup (This Pass)

To reduce clutter in the repository root, the following files were relocated:

- `codex_chain.py` → `scripts/root-utilities/codex_chain.py`
- `codex_sync.ps1` → `scripts/root-utilities/codex_sync.ps1`
- `codex_all_one_quantum_imaging_v1_1.ps1` → `scripts/root-utilities/codex_all_one_quantum_imaging_v1_1.ps1`
- `codex_memory_core_v1_2.json` → `data/root-state/codex_memory_core_v1_2.json`
- `giza_v5_0_block_copy.txt` → `docs/archive/giza_v5_0_block_copy.txt`
- Removed Windows metadata file: `desktop.ini`

## Quick Validation Commands

```bash
python -m py_compile codex_watcher/cli.py
python -m compileall -q codex_watcher
```

## Contribution Notes

- Keep changes scoped and incremental.
- Avoid modifying `codex/` unless explicitly requested.
- Prefer moving root artifacts into purpose-specific folders (`scripts/`, `data/`, `docs/`) instead of adding new loose files.
