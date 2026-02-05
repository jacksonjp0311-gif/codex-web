# codex-web Deep Review

Generated from a full structural scan and file-density audit.

## 1) What is happening in this repository

`codex-web` currently behaves like a hybrid of:

- a **runtime monorepo** (`codex/`, watcher, apps),
- a **long-term artifact archive** (`backups_reorg/`, `archive/`),
- and a **vendor snapshot store** (tracked `node_modules`, tracked `.venv`).

This mixed role is the core reason day-to-day development feels heavy and noisy.

## 2) Primary structural findings

1. **Very high tracked-file count**
   - Over 100k tracked files, with most noise from vendor/backups.
2. **Dependency trees are tracked**
   - `node_modules` content dominates tracked files and inflates diffs.
3. **Environment artifacts are tracked**
   - `.venv` is tracked, reducing portability and increasing churn.
4. **Backups are first-class in Git history**
   - `backups_reorg/` is valuable but too heavy for frequent code review cycles.

## 3) Risk model

- **Delivery risk:** high PR noise masks real logic changes.
- **Review risk:** large diffs lower reviewer confidence.
- **Ops risk:** local environments vary while tracked env artifacts imply false reproducibility.
- **Maintenance risk:** docs and structure drift unless continuously audited.

## 4) Evolution plan (phased)

### Phase 1 — Stabilize hygiene (current)
- Keep `.gitignore`, `.gitattributes`, `.editorconfig`, and health audit in place.
- Run `python scripts/repo_health_audit.py` on each change wave.

### Phase 2 — Untrack generated/vendor payloads
- Remove tracked `node_modules` and `.venv` from Git in controlled batches.
- Preserve lockfiles and installation instructions only.

### Phase 3 — Archive strategy redesign
- Keep a minimal curated in-repo archive index.
- Move long-term backups to external object storage and reference by manifest.

### Phase 4 — CI enforcement
- Add CI jobs for watcher tests and health-audit threshold checks.
- Fail PRs that exceed defined tracked-artifact policies.

## 5) Operational KPIs to track

- Total tracked files
- Tracked `node_modules` files
- Tracked `.venv` files
- Tracked backup files
- Watcher test pass rate

These metrics are now machine-readable in `docs/reports/repo_health_report.json`.
