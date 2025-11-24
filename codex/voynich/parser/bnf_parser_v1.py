def parse_token(token):
    import re

    # BNF structure segments
    prefix = None
    core = None
    bench = None
    suffix = None

    if token.startswith("qo"):
        prefix = "qo"
        token = token[2:]
    elif token.startswith("q"):
        prefix = "q"
        token = token[1:]

    # suffixes
    for suf in ["aiiin","aiiin","aiiin","aiin","ain","edy","dy","y"]:
        if token.endswith(suf):
            suffix = suf
            token = token[:-len(suf)]
            break

    # bench forms
    benches = ["ckh","cth","cfh","cph","ch","sh"]
    for b in benches:
        if token.startswith(b):
            bench = b
            token = token[len(b):]
            break

    core = token if token else None

    return {
        "prefix": prefix,
        "core": core,
        "bench": bench,
        "suffix": suffix
    }
