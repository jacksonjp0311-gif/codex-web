# THOTH Python Adapter (Non-authoritative)

Implements a **THOTH-compliant** freeze:
- reads config/map.json (scope ℳ)
- compares structural fingerprints vs untime/index.json
- freezes only changed routes into untime/memory/YYYY-MM-DD/###/
- updates dashboard dashboard/data/

No semantics. No refactors. No execution of target code.
