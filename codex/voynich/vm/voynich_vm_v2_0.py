import json, argparse, sys, pathlib

def main():
    ap = argparse.ArgumentParser(description="Voynich OS v2.0 — VM (IR → Codex State)")
    ap.add_argument("--input",  required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    in_path  = pathlib.Path(args.input)
    out_path = pathlib.Path(args.output)

    data = []

    if in_path.exists():
        with in_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                data.append(rec)
    else:
        sys.stderr.write(f"[WARN] IR file not found: {in_path}\\n")

    total = len(data)
    rel_modes = {}
    depths = {}
    tokens_set = set()

    for rec in data:
        mode = rec.get("mode", "UNKNOWN")
        rel_modes[mode] = rel_modes.get(mode, 0) + 1

        depth = rec.get("depth", "UNKNOWN")
        depths[depth] = depths.get(depth, 0) + 1

        for t in rec.get("tokens", []):
            tokens_set.add(t)

    core   = depths.get("CORE", 0)
    peri   = depths.get("PERIPHERY", 0)
    neutral = depths.get("NEUTRAL", 0)
    denom  = core + peri + neutral

    E = float(total)
    I = float(len(tokens_set))

    delta_phi = 0.0
    if denom > 0:
        delta_phi = (core - peri) / float(denom)

    C = 0.0
    if E > 0.0 and I > 0.0:
        C = (E * I) / (1.0 + abs(delta_phi))

    result = {
        "summary": {
            "total_clauses": total,
            "modes": rel_modes,
            "depths": depths,
            "distinct_tokens": len(tokens_set)
        },
        "codex_state": {
            "E": E,
            "I": I,
            "delta_phi": delta_phi,
            "C": C,
            "H7": 0.70
        }
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
