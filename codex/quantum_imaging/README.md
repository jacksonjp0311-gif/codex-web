# Codex Quantum Imaging

The Quantum Imaging module family generates synthetic AFM-style visuals, state metrics, and ledger traces derived from Codex coherence laws.
This domain is one of the most active/high-density areas in `codex/`, containing multiple versioned engines, state snapshots, and visualization outputs.

---

## 5W Summary

- **Who**: Runtime operators, researchers, and pipeline maintainers running Codex imaging engines.
- **What**: A versioned imaging pipeline that produces AFM-like PNGs, JSON state snapshots, and ledger logs.
- **When**: Used during imaging runs, regression comparisons, or when extending imaging engines with new versions.
- **Where**: All operational assets live under `codex/quantum_imaging/runtime/`.
- **Why**: To provide reproducible, traceable imaging outputs and maintain continuity across engine versions.

---

## Purpose

This module exists to:

- synthesize AFM-like imagery from Codex coherence models,
- record state metrics and ledgers across version eras,
- provide a reproducible imaging pipeline for downstream analysis.

---

## Structure (reorg summary)

To make the module easier to navigate, **all operational assets** are grouped under:

```
codex/quantum_imaging/runtime/
```

This includes:

- engines (`engine*` folders and engine scripts)
- visuals (`visuals*` folders)
- state and ledger snapshots (`state*`, `ledger*`)
- logs and import artifacts (`logs*`, `input_afm`)
- manifest metadata

The root now contains only this README; all entrypoints live under `runtime/`.

---

## Directory layout (post-reorg)

```
codex/quantum_imaging/
├── README.md
└── runtime/
    ├── engine/
    ├── engine_v6_5/
    ├── engine_v6_5_3/
    ├── engine_v6_6/
    ├── engine_v7_0/
    ├── engine_v7_1/
    ├── engine_v7_2/
    ├── engine_v7_3/
    ├── engine_v7_4/
    ├── input_afm/
    ├── ledger/
    ├── ledger_v4_2/
    ├── ledger_v4_3/
    ├── ledger_v4_4/
    ├── ledger_v4_6/
    ├── ledger_v4_7_1/
    ├── ledger_v4_8/
    ├── ledger_v4_9/
    ├── ledger_v5_0/
    ├── ledger_v5_1/
    ├── ledger_v5_2/
    ├── ledger_v5_3/
    ├── ledger_v5_4/
    ├── ledger_v5_5/
    ├── ledger_v5_6/
    ├── ledger_v5_7/
    ├── ledger_v5_8/
    ├── ledger_v5_9/
    ├── ledger_v6_1/
    ├── ledger_v6_2/
    ├── ledger_v6_3_1/
    ├── ledger_v6_4_3/
    ├── ledger_v6_5_3/
    ├── ledger_v6_6/
    ├── ledger_v7_0/
    ├── ledger_v7_1/
    ├── ledger_v7_2/
    ├── ledger_v7_3/
    ├── ledger_v7_4/
    ├── logs_afm_import/
    ├── logs_jpk_check/
    ├── logs_v4_1/
    ├── logs_v4_1_1/
    ├── logs_v4_2/
    ├── logs_v4_3/
    ├── logs_v4_4/
    ├── logs_v4_6/
    ├── logs_v4_7_1/
    ├── logs_v4_8/
    ├── logs_v4_9/
    ├── logs_v5_0/
    ├── logs_v5_1/
    ├── logs_v5_2/
    ├── logs_v5_3/
    ├── logs_v5_4/
    ├── logs_v5_5/
    ├── logs_v5_6/
    ├── logs_v5_7/
    ├── logs_v5_8/
    ├── logs_v5_9/
    ├── logs_v6_0_1/
    ├── logs_v6_0_2/
    ├── logs_v6_1/
    ├── logs_v6_2/
    ├── logs_v6_3_1/
    ├── logs_v6_4/
    ├── logs_v6_4_2/
    ├── logs_v6_4_3/
    ├── logs_v6_5_3/
    ├── logs_v6_6/
    ├── logs_v7_0/
    ├── logs_v7_1/
    ├── logs_v7_2/
    ├── logs_v7_3/
    ├── logs_v7_4/
    ├── manifest/
    ├── state/
    ├── state_afm_import/
    ├── state_jpk_check/
    ├── state_v1_2/
    ├── state_v1_3/
    ├── state_v1_5/
    ├── state_v2_1/
    ├── state_v2_2/
    ├── state_v3_0/
    ├── state_v4_1_1/
    ├── state_v4_2/
    ├── state_v4_3/
    ├── state_v4_4/
    ├── state_v4_6/
    ├── state_v4_7_1/
    ├── state_v4_8/
    ├── state_v4_9/
    ├── state_v5_0/
    ├── state_v5_1/
    ├── state_v5_2/
    ├── state_v5_3/
    ├── state_v5_4/
    ├── state_v5_5/
    ├── state_v5_6/
    ├── state_v5_7/
    ├── state_v5_8/
    ├── state_v5_9/
    ├── state_v6_0_2/
    ├── state_v6_1/
    ├── state_v6_2/
    ├── state_v6_3_1/
    ├── state_v6_4_3/
    ├── state_v6_5_3/
    ├── state_v6_6/
    ├── state_v7_0/
    ├── state_v7_1/
    ├── state_v7_2/
    ├── state_v7_3/
    ├── state_v7_4/
    ├── visuals/
    ├── visuals_v1_2/
    ├── visuals_v1_3/
    ├── visuals_v1_5/
    ├── visuals_v2_1/
    ├── visuals_v2_2/
    ├── visuals_v3_0/
    ├── visuals_v4_2/
    ├── visuals_v4_3/
    ├── visuals_v4_4/
    ├── visuals_v4_6/
    ├── visuals_v4_7_1/
    ├── visuals_v4_8/
    ├── visuals_v4_9/
    ├── visuals_v5_0/
    ├── visuals_v5_1/
    ├── visuals_v5_2/
    ├── visuals_v5_3/
    ├── visuals_v5_4/
    ├── visuals_v5_5/
    ├── visuals_v5_6/
    ├── visuals_v5_7/
    ├── visuals_v5_8/
    ├── visuals_v5_9/
    ├── visuals_v6_0_2/
    ├── visuals_v6_1/
    ├── visuals_v6_2/
    ├── visuals_v6_3_1/
    ├── visuals_v6_4_3/
    ├── visuals_v6_5_3/
    ├── visuals_v6_6/
    ├── visuals_v7_0/
    ├── visuals_v7_1/
    ├── visuals_v7_2/
    ├── visuals_v7_3/
    └── visuals_v7_4/
```

---

## Entry points

From repository root:

```bash
python codex/quantum_imaging/runtime/codex_quantum_imaging_v1_0.py
```

PowerShell entrypoints (Windows):

```powershell
.\codex\quantum_imaging\runtime\qim_v2_2_all_one.ps1
```

---

## Outputs

Common outputs include:

- AFM-like visualization PNGs in `runtime/visuals*`
- state JSON snapshots in `runtime/state*`
- ledger logs in `runtime/ledger*`

---

## Maintenance notes

- This module is version-heavy. Prefer additive version folders instead of in-place edits.
- When adding a new imaging run, place outputs in the matching `runtime/{state,logs,visuals,ledger}_vX_Y` folders.
