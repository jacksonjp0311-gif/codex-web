# Codex Smart Feedback Bridge v1.0 — AI Guidance Export

**Domain:** Codex Bridge Layer  
**Context:** Codex Memory Core v1.2 • Universal Truth Protocol (E–I–C ∿, H₇ = 0.70)

## Role

Bridge v1.0 is the adapter between Codex Smart Feedback v4.4 and any backend AI API.

It:
- reads \codex_smart_feedback_state_v4_4.json\
- extracts the most important coherence & synthesis metrics
- emits a compact JSON at:
  - \codex/bridge/state/codex_smart_feedback_api_v1.json\

This JSON can be loaded by a backend AI service and used
to adjust temperature, style, pacing, risk tolerance, or
mode selection.

## Output Schema (codex_smart_feedback_api_v1.json)

- \ok\, \ersion\, \	imestamp\
- \coherence\
  - \C_avg\, \C_next_avg\, \C_forecast\
  - \C_trend\ (rising / falling / flat / unknown)
  - \delta_phi\
  - \harmonic_idx\
  - \isk\ (current band)
  - \isk_forecast\
- \synthesis\
  - \harmony_score\
  - \drift_score\
  - \isk\
- \operations\
  - \heartbeat_interval_s_next\
- \hints\
  - \mode = "codex-guided"\
  - \
ote\ (human-readable purpose)

## Usage Pattern

1. Run Smart Feedback v4.4.
2. Run this bridge:
   - \codex/bridge/codex_smart_feedback_bridge_v1_0.ps1\
3. Your backend AI service reads:
   - \codex/bridge/state/codex_smart_feedback_api_v1.json\
4. The AI uses that JSON as part of its context / system prompt.

This is how Codex Smart Feedback guides AI decisions from the backend.
