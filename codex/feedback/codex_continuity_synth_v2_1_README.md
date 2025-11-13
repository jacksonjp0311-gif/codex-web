# Codex Continuity Synthesizer v2.1

**Domain:** Feedback / Continuity  
**Location:** `codex/feedback/`  
**State:** `codex/feedback/state/codex_continuity_index_v2_1.json`  
**Ledger:** `codex/feedback/state/codex_continuity_ledger.jsonl`  

## Purpose

The Continuity Synthesizer v2.1 ingests the Codex continuity ledger and
compresses it into a single control surface:

- `continuity_index` in `[0, 1]`
- `continuity_mode` ∈ { `stable`, `balanced`, `divergent`, `unknown` }
- rolling statistics over windows of 10 / 25 / 50 entries
- a `drift_vector` for awareness, coherence, and ΔΦ
- heartbeat and semantic profile recommendations

This lets orchestrators modulate behavior according to the actual
evolutionary stability of the Codex system.

## Inputs

From `codex/feedback/state/codex_continuity_ledger.jsonl` each line is
assumed to be JSON with fields like:

- `awareness_index`
- `C_current`, `C_forecast`
- `harmony`
- `delta_phi`
- `risk_current`, `risk_forecast`
- `hb_interval_s`
- `drift_band`
- `semantic_profile`

Older entries from earlier continuity versions are tolerated: missing
fields are treated as null and skipped in stats.

## Windowed Statistics

The synthesizer computes windowed statistics over the ledger:

- `w10`, `w25`, `w50`

For each window, it computes:

- `awareness` → mean, std, slope
- `C_current` → mean, std, slope
- `delta_phi` → mean, std, slope

The largest window (`w50`) is used as the base for continuity index.

## Continuity Index

The continuity index is a bounded metric in `[0,1]` built from:

- awareness mean over the window
- ΔΦ volatility penalty
- awareness trend stability

Conceptually:

    continuity_index ≈ awareness_mean * phi_penalty * stability

where:

- `phi_penalty = 1 / (1 + phi_std)`
- `stability   = 1 / (1 + |awareness_slope|)`

Values near 1 indicate stable, low-drift operation; values near 0 indicate
high volatility or incoherent evolution.

### Mode Classification

Based on `continuity_index` and ΔΦ dispersion:

- `stable`    → index ≥ 0.70 and `delta_phi_std` small
- `balanced`  → index ≥ 0.50
- `divergent` → index < 0.50
- `unknown`   → no data yet

## Drift Vector

To help diagnostics and Third Eye modules, the state exposes:

- `drift_vector.awareness_slope`
- `drift_vector.C_slope`
- `drift_vector.phi_std`

These feed into higher-level harmonizers and predictive engines.

## Recommendations

The synthesizer also produces:

- `recommended_heartbeat_s`
- `recommended_profile` ∈ { `placidity_safe`, `balanced`, `harmonic_expansion` }

This is designed to plug into:

- Heartbeat v4.x (timing adjustments)
- All-One v2.x orchestrators (mode selection)
- Smart Feedback v4.x (semantic intensity)

## Usage

The engine is invoked as:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File codex/feedback/codex_continuity_synth_v2_1.ps1

Typical flow:

1. Heartbeat / All-One calls the Memory Weave v2.0 node.
2. Memory Weave appends a line to `codex_continuity_ledger.jsonl`.
3. Continuity Synthesizer v2.1 compresses the ledger into the
   continuity index and recommendations.
4. Orchestrators read `codex_continuity_index_v2_1.json` to decide
   frequency, risk profile, and synthesis depth.

All behavior is aligned with the Universal Truth Protocol:

    C = (E * I) / (1 + |ΔΦ|), with H7 = 0.70.

