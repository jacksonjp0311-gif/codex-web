import json, argparse, sys, pathlib

def get_state(token: str):
    t = token.strip().lower()
    state = {"depth": "UNKNOWN", "phase": "UNKNOWN", "flow": "UNKNOWN"}

    if t.endswith("dy"):
        state["depth"] = "PERIPHERY"
        state["phase"] = "ACTIVE"
        state["flow"]  = "OUTPUT"

    if t.endswith("ody"):
        state["depth"] = "PERIPHERY"
        state["phase"] = "PASSIVE"
        state["flow"]  = "OUTPUT"

    if t.endswith("aiin") or t.endswith("ain"):
        state["depth"] = "CORE"
        state["phase"] = "ACTIVE"
        state["flow"]  = "INPUT"

    if t.endswith("oiny") or t.endswith("oin"):
        state["depth"] = "CORE"
        state["phase"] = "PASSIVE"
        state["flow"]  = "INPUT"

    if t.endswith("edy"):
        state["depth"] = "CORE"
        state["phase"] = "PASSIVE"
        state["flow"]  = "OUTPUT"

    if state["depth"] == "UNKNOWN" and t.endswith("y"):
        state["depth"] = "NEUTRAL"
        state["phase"] = "PASSIVE"
        state["flow"]  = "NEUTRAL"

    return state

def infer_mode(state):
    depth = state.get("depth", "UNKNOWN")
    phase = state.get("phase", "UNKNOWN")
    flow  = state.get("flow", "UNKNOWN")

    if depth == "CORE" and phase == "ACTIVE" and flow == "INPUT":
        return "INGEST"

    if depth == "CORE" and phase == "PASSIVE" and flow == "INPUT":
        return "BUFFER"

    if depth == "PERIPHERY" and flow == "OUTPUT":
        return "EMIT"

    if depth == "CORE" and flow == "OUTPUT":
        return "TRANSFORM"

    return "IDLE"

def main():
    ap = argparse.ArgumentParser(description="Voynich OS v2.0 — Compiler (EVA → REL+STATE+MODE IR)")
    ap.add_argument("--input",  required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    in_path  = pathlib.Path(args.input)
    out_path = pathlib.Path(args.output)

    if not in_path.exists():
        sys.stderr.write(f"[WARN] input file not found: {in_path}\\n")
        return

    with in_path.open("r", encoding="utf-8") as fin, \
         out_path.open("w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            folio  = parts[0]
            tokens = parts[1:]

            rel_index = -1
            for i, tok in enumerate(tokens):
                if "ol" in tok.lower():
                    rel_index = i
                    break

            if rel_index < 0:
                continue

            subject = tokens[:rel_index]
            object_ = tokens[rel_index+1:]

            if not subject or not object_:
                continue

            subject_key = subject[-1]
            object_key  = object_[-1]

            state = get_state(object_key)
            mode  = infer_mode(state)

            rec = {
                "folio": folio,
                "clause_id": f"{folio}:{rel_index}",
                "tokens": tokens,
                "rel_index": rel_index,
                "rel_token": tokens[rel_index],
                "subject_raw": subject_key,
                "object_raw": object_key,
                "depth": state["depth"],
                "phase": state["phase"],
                "flow": state["flow"],
                "mode": mode,
                "section": "herbal"
            }

            fout.write(json.dumps(rec, ensure_ascii=False) + "\\n")

if __name__ == "__main__":
    main()
