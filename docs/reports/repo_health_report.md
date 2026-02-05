# codex-web Repository Health Report

Generated: 2026-02-05T16:58:06.670791+00:00

## Executive summary

- Structural risk score: **50/100**
- Tracked files: **104233**
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
| `codex_watcher.egg-info` | 5 |
| `inbox` | 5 |
| `scripts` | 5 |
| `codex_watcher` | 4 |

## Risk flags

- High file volume in `backups_reorg`: 50410 files (threshold: 1000).
- High file volume in `approval-ui`: 38431 files (threshold: 1000).
- High file volume in `copilot-feedback`: 6566 files (threshold: 1000).
- High file volume in `.venv`: 4047 files (threshold: 1000).
- High file volume in `codex`: 2955 files (threshold: 1000).
- Tracked `node_modules` content detected. This creates noisy diffs and large commits.
- Tracked `.venv` content detected. Virtual environments should usually be untracked.
- Tracked `backups_reorg` content detected. Prefer external long-term backup storage.

## Recommended next actions

1. Untrack dependency/vendor trees gradually (start with node_modules and .venv) in controlled PRs.
2. Move long-term backups to external object storage and keep curated snapshots only.
3. Add CI checks for Python tests and selected app checks on each PR.
4. Continue modular docs under docs/ and keep README focused on onboarding.

