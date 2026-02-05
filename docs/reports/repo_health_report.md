# codex-web Repository Health Report

Generated: 2026-02-05T16:48:10.857047+00:00

## Summary

- Top-level directories scanned: **26**
- Tracked files: **104231**
- Tracked `node_modules` files: **88089**
- Tracked `.venv` files: **8228**
- Tracked `backups_reorg` files: **50566**

## Top-level file density

| Directory | File count |
|---|---:|
| `backups_reorg` | 50410 |
| `approval-ui` | 38431 |
| `copilot-feedback` | 6566 |
| `.venv` | 4047 |
| `codex` | 2955 |
| `smart_feedback` | 871 |
| `interface` | 665 |
| `tools` | 232 |
| `core` | 63 |
| `archive` | 48 |
| `.` | 7 |
| `scripts` | 5 |
| `codex_watcher.egg-info` | 5 |
| `inbox` | 5 |
| `codex_watcher` | 4 |

## Risk flags

- High file volume in `backups_reorg`: 50410 files (threshold: 1000).
- High file volume in `approval-ui`: 38431 files (threshold: 1000).
- High file volume in `copilot-feedback`: 6566 files (threshold: 1000).
- High file volume in `.venv`: 4047 files (threshold: 1000).
- High file volume in `codex`: 2955 files (threshold: 1000).
- Tracked `node_modules` content detected. This can create very noisy diffs and large commits.
- Tracked `.venv` content detected. Virtual environments should typically be untracked.
- Tracked `backups_reorg` content detected. Consider moving long-term backups to external storage.

## Recommended next actions

1. Untrack dependency/vendor trees gradually (start with `node_modules` and `.venv`) in controlled PRs.
2. Keep archives in `archive/` or external object storage; retain only curated snapshots in Git.
3. Add CI checks that run Python tests and selected app checks on each PR.
4. Continue modular documentation under `docs/` to reduce README bloat.
