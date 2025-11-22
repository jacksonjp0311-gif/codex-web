# Codex Glyph Language (CGL) v1.1 — Auto-Evolving Glyph Engine

**Role:** Provide a universal glyph-based language for the Codex, where any new
glyph or token used in a .cgl program is automatically added to a shared glyph
table and becomes available across all modules.

- Protocol: Codex Glyph Protocol v3.0
- Engine : Python interpreter codex_cgl_interpreter_v1_1.py
- Anchor : codex/cgl/

## Core Ideas

- Every glyph is a **token** with:
  - token (literal symbol or word)
  - name
  - category (e.g. triad_energy, triad_information, metric, meta)
  - expansion (semantic meaning / pseudo-code)
  - tags

- The glyph table lives at:

  codex/cgl/glyph_table/codex_glyph_table_v3_0.json

- The interpreter:
  - Loads the glyph table (creates a default if missing).
  - Loads a .cgl program from input/program_v1_1.cgl (auto-creates a sample).
  - Tokenizes by simple whitespace.
  - For any token not already in the glyph table:
    - Creates a placeholder glyph entry with category = "unknown".
  - Writes an updated glyph table back to disk.
  - Emits a state JSON summarizing glyph usage and new glyphs.

This means you can **invent new glyphs on the fly** simply by using them in
your .cgl programs. The system will record them and keep the language growing.

## Outputs

- state/v1_1/cgl_state_v1_1.json
- glyph_table/codex_glyph_table_v3_0.json
- logs/ledger/cgl_ledger.jsonl

## How to Use

1. Edit input/program_v1_1.cgl and add any glyphs or tokens you like.
2. Run the One-PS script for CGL v1.1.
3. The interpreter:
   - Updates the glyph table.
   - Logs glyph usage.
   - Creates a ledger entry.
4. Other Codex modules can read the glyph table to stay in sync.
