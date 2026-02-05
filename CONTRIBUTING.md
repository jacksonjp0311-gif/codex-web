# Contributing to codex-web

## Scope and structure

- Keep changes scoped and incremental.
- Avoid modifying `codex/` unless the task explicitly requires it.
- Place new files by intent:
  - scripts → `scripts/`
  - data/state artifacts → `data/`
  - archive material → `docs/archive/` or `archive/`

## Branch and commit hygiene

- Use focused commits with imperative messages.
- Do not bundle unrelated refactors with feature work.
- Include a short validation list in your PR.

## Quality gates (minimum)

Run these from repository root before opening a PR:

```bash
python -m py_compile codex_watcher/cli.py
python -m compileall -q codex_watcher
python -m unittest discover -s tests/python -p 'test_*.py'
```

If you changed a UI app, also run the app-specific checks where possible.

## Security and data handling

- Never commit secrets, tokens, or credentials.
- Keep environment-specific files (`.env`, local logs, caches) untracked.
- Use synthetic or redacted samples in test fixtures.
