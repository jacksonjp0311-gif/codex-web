# codex-web

`codex-web` is a multi-runtime monorepo for the Codex project.
It combines:

- a large **Codex knowledge/runtime tree** (`codex/`),
- **automation and ingestion tooling** (Python + PowerShell),
- and **UI/feedback surfaces** (React/Node-based apps).

This repository is intentionally broad: it stores active runtime code, operational scripts, state artifacts, and historical archives.

---

## What this repo is

At a practical level, this repo is used to:

1. Run Codex orchestration and symbolic workflows.
2. Process ledger/inbox data with watcher tooling.
3. Develop web interfaces (`approval-ui`, `copilot-feedback`).
4. Keep historical project artifacts in version control.

---

## Clone the repo

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

---

## Quick start

### 1) Python watcher tooling

The watcher CLI lives in `codex_watcher/cli.py` and processes inbox files into a ledger.

```bash
python -m py_compile codex_watcher/cli.py
python -m compileall -q codex_watcher
python codex_watcher/cli.py
```

Optional watch mode:

```bash
python codex_watcher/cli.py --watch --active 15 --rest 15 --interval 3
```

### 2) Approval UI (React)

```bash
cd approval-ui
npm install
npm start
```

### 3) PowerShell tests (if `pwsh` available)

```bash
pwsh -File tests/Codex.Ledger.Tests.ps1
pwsh -File tests/Unit/Parse-CodexDsl.Tests.ps1
```

---

## Repository layout (top level)

- `codex/` — core Codex module tree (largest and primary project domain).
- `codex_watcher/` — Python watcher CLI for inbox → ledger processing.
- `approval-ui/` — React approval UI.
- `copilot-feedback/` — feedback orchestration/UI.
- `interface/` — connector and protocol integration layer.
- `src/`, `tests/`, `tools/` — source modules, tests, and analyzers.
- `scripts/root-utilities/` — operational scripts previously stored in root.
- `data/root-state/` — root-level state artifacts moved out of `/`.
- `docs/archive/` and `archive/root-legacy/` — archived legacy artifacts and folders.

---

## `codex/` directory map

The core project content is inside `codex/`. First-level directories currently include:

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

If you are new to this repo, start with these areas first:

- `codex/core`
- `codex/orchestrator`
- `codex/spiral`
- `codex/handoff`
- `codex/observability`

---

## Root cleanup policy

To keep the root clean and navigable:

- New scripts should go in `scripts/` (or a scoped subfolder).
- State/data artifacts should go in `data/`.
- Archival material should go in `docs/archive/` or `archive/`.
- Avoid introducing new loose files/folders directly under repository root unless required.

- Keep changes scoped and incremental.
- Avoid modifying `codex/` unless explicitly requested.
- Prefer moving root artifacts into purpose-specific folders (`scripts/`, `data/`, `docs/`) instead of adding new loose files.
