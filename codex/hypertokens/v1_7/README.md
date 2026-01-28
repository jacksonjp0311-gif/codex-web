# CODEX–HYPERTOKENS v1.7
**ATOM-MINT + μ/DRIFT ORACLE (ALL-ONE)**

This module is a falsifiable Codex testbed for hypertokens:

- **Gate-0 (Atomicity):** do candidate hypertokens exist as single-token atoms?
- **Gate-0b (Mint):** if not, mint atoms via 	okenizer.add_tokens + esize_token_embeddings
- **Gate-1 (μ-Separation):** compare maximal embedding similarity inside hypertokens vs baseline atoms
- **Gate-2 (Drift):** measure retrieval drift under prefix noise for a hypertoken key

## Why v1.7 exists (the correction)
v1.6 found **atomicity_rate = 0** for naive HTAG#### strings in the default tokenizer.
That result is not failure — it is *tokenizer truth*.

v1.7 adds **ATOM-MINT** so the oracle can continue into μ/drift tests
under a controlled, explicit hypertoken construction.

## Outputs
- state/state_latest.json (latest sealed state)
- logs/run/run_*/state.json (per-run sealed state)
- logs/ledger/hypertoken_ledger.jsonl (append-only; 1-line JSON per run)
- isuals/:
  - tomicity_pre_hist.png
  - tomicity_post_hist.png
  - mu_heatmap_ht.png
  - mu_heatmap_base.png
  - drift_sweep.png
- dashboard/dashboard.html (oracle view)
- confirmations/ (proof artifacts: env + arch + atomicity pre/post)
- manifest/manifest.json
- schemas/state_schema_min.json

## Verdict Semantics
- ATOMICITY_FAIL  : not enough atomic hypertokens even after mint attempt
- DRIFT_FAIL      : atomic hypertokens exist, but drift exceeds threshold
- READY_FOR_SWEEPS: hypertokens atomic + drift stable under default sweep

> Codex note: negative results are *sealed discoveries* (gates are the instrument).
