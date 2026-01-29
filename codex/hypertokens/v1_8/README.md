# CODEX–HYPERTOKENS v1.8 — CANON

## Codex Discovery (H₁₇ → H₁₇D)

v1.8 extends v1.7 by adding embedding-only training (frozen backbone) to test recovery.

**H₁₇:** Atomicity can be forced, but stability cannot.  
**H₁₇B:** μ_sep ↑ does not imply retrieval invariance.  
**H₁₇C:** Prefix-noise causes drift explosion.  
**H₁₇D (NEW):** Drift recovery under frozen backbone implies stability is an embedding-row property.

## Outputs

- visuals/atomicity_pre_hist.png
- visuals/atomicity_post_hist.png
- visuals/mu_sep_components.png
- visuals/drift_pretrain.png
- visuals/train_loss.png
- visuals/drift_posttrain.png
- visuals/drift_delta.png
- dashboard/dashboard.html
- confirmations/env_proof.json
- confirmations/arch_proof.json
- confirmations/mint_proof.json
- confirmations/train_proof.json
- schemas/state_schema_min.json
- logs/ledger/hypertoken_ledger.jsonl
- logs/run/run_*/state.json + handoff.json

Verdicts are falsifiable boundary events.
