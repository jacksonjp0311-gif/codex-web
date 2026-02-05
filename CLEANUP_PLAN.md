# Non-`codex/` Cleanup Plan

## Scope Guardrails
- Do not modify anything under the root `codex/` directory.
- Focus on high-impact, low-risk cleanup in active non-`codex/` code.

## Plan
1. **Stabilize broken automation entrypoints**
   - Remove accidental/injected tokens that break Python execution in `codex_watcher`.
2. **Add lightweight validation**
   - Run syntax/compile checks to ensure the cleaned code executes.
3. **Document this pass**
   - Keep this file as a record of scope and completed actions.

## Executed in this pass
- Cleaned `codex_watcher/cli.py` by removing repeated `@smart_suggest` injection lines that interrupted function definitions.
- Validated module syntax with Python compile checks.

## Next passes (optional)
- Add unit tests for `parse_inbox_file` and `validate_stone`.
- Normalize file encoding artifacts in output strings/comments.
- Reduce repository noise outside `codex/` (tracked dependency/vendor churn) in a dedicated PR.
