# codex-web

A multi-runtime monorepo for Codex orchestration, symbolic runtime modules, ingestion/ledger automation, and supporting web interfaces.

## Table of Contents

- [1) What this repository is](#1-what-this-repository-is)
- [2) Architecture at a glance](#2-architecture-at-a-glance)
- [3) Clone and setup](#3-clone-and-setup)
- [4) Quick-start workflows](#4-quick-start-workflows)
- [5) Repository layout](#5-repository-layout)
- [6) `codex/` directory map](#6-codex-directory-map)
- [7) Development standards](#7-development-standards)
- [8) Security and data policy](#8-security-and-data-policy)
- [9) Roadmap (repo quality)](#9-roadmap-repo-quality)

---

## 1) What this repository is

`codex-web` is the operational home for:

1. **Core Codex runtime content** in `codex/` (orchestration, state, symbolic modules).
2. **Automation pipelines** in Python/PowerShell (watchers, ingest, ledger flows).
3. **Application surfaces** (React/Node apps such as `approval-ui` and `copilot-feedback`).
4. **Project history** via structured archive/data directories.

This repository is intentionally broad, but the root is being progressively normalized to keep active development fast and predictable.

---

## 2) Architecture at a glance

| Layer | Primary purpose | Key locations |
|---|---|---|
| Core runtime | Symbolic and orchestration systems | `codex/` |
| Ingestion + ledger | Inbox parsing, validation, digest-chain persistence | `codex_watcher/`, `inbox/` |
| UI surfaces | Human-facing app workflows | `approval-ui/`, `copilot-feedback/` |
| Tooling + tests | Validation, analyzers, test assets | `tools/`, `tests/`, `src/` |
| Data + archive | State artifacts and legacy material | `data/`, `docs/archive/`, `archive/` |

---

## 3) Clone and setup

### Bash (Linux/macOS/Git Bash)

```bash
git clone https://github.com/jacksonjp0311-gif/codex-web.git
cd codex-web
```

### PowerShell (Windows)

```powershell
git clone https://github.com/jacksonjp0311-gif/codex-web.git
Set-Location codex-web
```

### Tooling prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- PowerShell 7+ (`pwsh`) for PowerShell tests/scripts

---

## 4) Quick-start workflows

### A) Watcher pipeline (Python)

```bash
python -m py_compile codex_watcher/cli.py
python -m compileall -q codex_watcher
python codex_watcher/cli.py
```

Watch mode:

```bash
python codex_watcher/cli.py --watch --active 15 --rest 15 --interval 3
```

### B) Run approval UI

```bash
cd approval-ui
npm install
npm start
```

### C) Run feedback orchestrator

```bash
cd copilot-feedback
npm install
npm start
```

### D) Run repository quality checks

```bash
python -m unittest discover -s tests/python -p 'test_*.py'
pwsh -File tests/Codex.Ledger.Tests.ps1
pwsh -File tests/Unit/Parse-CodexDsl.Tests.ps1
```

---

## 5) Repository layout

- `codex/` — core Codex runtime tree (primary domain).
- `codex_watcher/` — Python watcher CLI for inbox→ledger processing.
- `approval-ui/` — React UI for approval workflows.
- `copilot-feedback/` — feedback app + orchestration runtime.
- `interface/` — connector/protocol integration assets.
- `src/`, `tests/`, `tools/` — source modules, tests, analyzers.
- `scripts/root-utilities/` — relocated operational scripts.
- `data/root-state/` — relocated root state artifact(s).
- `docs/archive/`, `archive/root-legacy/` — archive and legacy snapshots.

---

## 6) `codex/` directory map

First-level directories currently present in `codex/`:

```text
align_pulse
analyses
ancient
archive
automation
baryogenesis
bio_resonance
black_horizon
bridge
cgl
codex_emergence
codex_glyph_synthesis_v1
codex_module_generator
config
core
dashboard
data
dna
evolution
feedback
finance_resonance
glyphs
guardian
handoff
hypertokens
logs
memory
mirror_temp
observability
orchestrator
primes
quantum
quantum.crystal
quantum_imaging
quantum_tunneling
rootmirror
signal_density
solar_resonance
spiral
state
system
system_dumps
telemetry
third_eye
thoth
tools
truthfield
utils
v0.5
v2
v3
visuals
voice
voicebox
voynich
web
```

Recommended starting points for new contributors:

- `codex/core`
- `codex/orchestrator`
- `codex/spiral`
- `codex/handoff`
- `codex/observability`

---

## 7) Development standards

- Keep PRs scoped.
- Place new files by purpose (`scripts/`, `data/`, `docs/archive/`, `archive/`).
- Avoid introducing new loose root files.
- Follow checks in `CONTRIBUTING.md` before opening a PR.

---

## 8) Security and data policy

- Never commit credentials or secrets.
- Keep local env/cache artifacts untracked.
- Prefer redacted/synthetic data in samples and tests.

---

## 9) Roadmap (repo quality)

1. Expand Python unit coverage for watcher and ledger edges.
2. Add app-level lint/test/build scripts consistency.
3. Add CI workflow for core quality gates.
4. Continue reducing tracked generated/vendor noise.

---


## 10) Repository health audit

Generate a structural health report at any time:

```bash
python scripts/repo_health_audit.py
```

This writes a markdown report to:

- `docs/reports/repo_health_report.md`

