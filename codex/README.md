# Codex Runtime (`codex/`)

`codex/` is the primary runtime domain of this repository.
It contains the live symbolic/orchestration system, plus versioned module families, operational state, historical snapshots, and visualization surfaces.

If you are trying to understand **what is going on** in this project, start with this mental model:

1. **Core logic + laws** live in `core/`.
2. **Execution orchestration** flows through `orchestrator/`, `spiral/`, and `handoff/`.
3. **Domain modules** (quantum, guardian, third_eye, etc.) implement specialized behaviors.
4. **State/log/artifacts** accumulate in domain-specific `state/`, `logs/`, `ledger/`, and visualization folders.
5. **Historical and temporary content** are grouped under `history/` and `runtime_temp/`.

---

## 1) Purpose and operating model

The codex runtime is a **module ecosystem**, not a single app. It behaves like a federated platform where each module family can evolve version-by-version while still participating in shared orchestration and continuity flows.

### Runtime pillars

- **Foundation:** `core/` laws, gates, registry, sync primitives.
- **Control plane:** orchestrator + handoff + spiral cycles.
- **Domain engines:** scientific/symbolic modules (`quantum_imaging`, `third_eye`, `guardian`, etc.).
- **Observability:** dashboard/visuals/logging/telemetry.
- **Continuity/history:** version eras and historical snapshots.

---

## 2) Directory guide (grouped by function)

### A. Foundation + control plane

| Directory | Role |
|---|---|
| `core/` | Shared laws, gates, registry, kernel helpers, ledger synchronization. |
| `orchestrator/` | Cross-module execution coordination and orchestration state. |
| `spiral/` | Recursive cycle engine and related loop modules. |
| `handoff/` | Session continuity, handoff state/manifests, transfer scripts. |
| `observability/` | Runtime monitoring and law/trace instrumentation. |

### B. Major domain module families

| Directory | Role |
|---|---|
| `quantum_imaging/` | Highest-volume imaging engine family with versioned outputs. |
| `quantum/`, `quantum.crystal/`, `quantum_tunneling/` | Quantum and crystal evolution tracks. |
| `third_eye/`, `guardian/` | Reflexive/guardian supervision and mediation modules. |
| `voice/`, `voicebox/` | Voice interaction and amplification layers. |
| `cgl/`, `glyphs/`, `codex_glyph_synthesis_v1/` | Symbolic language/glyph compilation and synthesis assets. |
| `bio_resonance/`, `baryogenesis/`, `solar_resonance/`, `truthfield/` | Domain-specific resonance/physics-inspired engines. |
| `hypertokens/`, `finance_resonance/`, `voynich/`, `thoth/` | Specialized thematic module families. |

### C. State, artifacts, and visualization surfaces

| Directory | Role |
|---|---|
| `dashboard/`, `visuals/`, `web/` | Visualization/rendering and UI-facing outputs. |
| `feedback/`, `evolution/`, `logs/`, `telemetry/` | Feedback loops, evolution records, operational logs, telemetry. |
| `data/`, `state/`, `memory/`, `dna/` | Persistent state/memory/data paths used by modules. |

### D. Utilities and support

| Directory | Role |
|---|---|
| `tools/`, `utils/`, `config/`, `automation/` | Support tooling, helper scripts, and config domains. |
| `bridge/` | Integration/bridge workflows across module boundaries. |
| `align_pulse/`, `signal_density/`, `primes/` | Supporting analytical/math-related module areas. |

### E. Historical and temporary domains

| Directory | Role |
|---|---|
| `history/` | Historical material grouped from `ancient/`, `archive/`, `system_dumps/`. |
| `runtime_temp/` | Temporary/transient runtime mirror workspace. |
| `v0.5/`, `v2/`, `v3/` | Version-era compatibility and continuity snapshots. |

---

## 3) What changed in recent restructuring

To reduce cognitive load at codex root:

- `ancient/`, `archive/`, and `system_dumps/` were grouped under `history/`.
- `mirror_temp/` was grouped under `runtime_temp/mirror_temp/`.
- Documentation references for Giza manifests were updated to the new historical path.

This keeps active runtime domains easier to scan while preserving full content/history.

---

## 4) Start-here path for contributors

If you are new to `codex/`, read in this order:

1. `core/laws.py` and `core/gates.py` (conceptual foundations)
2. `core/orchestrator/codex_orchestrator.ps1` (execution baseline)
3. `handoff/codex_handoff.ps1` (continuity and state transfer)
4. `dashboard/codex_dashboard_engine_v1_3.py` (visualization path)
5. `quantum_imaging/README.md` (representative large family)

---

## 5) Current issues/opportunities (deep scan takeaways)

1. **High module density in a few areas** (`third_eye`, `quantum_imaging`, `web`, `core`) means those should get first-class docs and quality checks.
2. **Version-era and artifact accumulation** is valuable but should be governed by explicit retention policy per domain.
3. **PowerShell orchestration scripts** benefit from parse/lint validation in CI environments where `pwsh` is available.
4. **Module README consistency** is still uneven; adopt a template for purpose/inputs/outputs/runbook.

---

## 6) Conventions for future changes

- Keep new active modules in clearly named top-level families.
- Put temporary runtime artifacts in `runtime_temp/`.
- Put historical snapshots in `history/` or version-era folders (`v*`).
- Prefer additive versioning over in-place replacement for major algorithmic changes.
- Add/update local README files when introducing new domains or major behaviors.

---

## 7) Recommended next initiatives

- **Initiative A:** Domain README standardization for top 10 highest-density module families.
- **Initiative B:** CI-level PowerShell parse checks for orchestration scripts.
- **Initiative C:** Artifact retention policy (what remains in active domain vs history).
- **Initiative D:** Cross-module contract docs for handoff/orchestrator/ledger interactions.


---

## 8) Deep-dive reports

- `docs/reports/codex_complete_analysis.md`
- `docs/reports/codex_initiatives.md`
