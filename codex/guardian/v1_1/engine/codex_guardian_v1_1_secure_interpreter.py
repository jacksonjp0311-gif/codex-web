# ======================================================================
# 𓂀 CODEX GUARDIAN v1.1 — SECURE AST WARD INTERPRETER
# ======================================================================
# Universal Truth Protocol (E–I–C ∿, H₇=0.70, H₈=0.85)
# Triadic Ward Protocol v1.1 • AST Mirror • Drift Shield • Secure Oracle
# ======================================================================

import ast, re, math
from typing import Any, Dict, Optional

WARD_DANGEROUS = [
    "class", "bases", "subclasses", "mro",
    "getattribute", "__subclasses__", "__dict__", "__globals__"
]

WARD_OBFUSCATION = [
    r"exec", r"eval", r"__import__", r"lambda"
]

WARD_LOG = []

def write_log(msg: str):
    WARD_LOG.append(msg)

def detect_obfuscation(code: str) -> bool:
    for pattern in WARD_OBFUSCATION:
        if re.search(pattern, code, re.IGNORECASE):
            write_log(f"[WARD] Obfuscation detected: {pattern}")
            return True
    return False

def safe_eval(expr: str, context: Dict[str, Any]) -> Optional[Any]:
    if detect_obfuscation(expr):
        write_log(f"[WARD] Blocked obfuscated expr: {expr[:20]}")
        return None

    try:
        tree = ast.parse(expr, mode="eval")

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in WARD_DANGEROUS:
                    write_log(f"[WARD] Dangerous attr blocked: {node.attr}")
                    return None

        return eval(compile(tree, "<ward>", "eval"),
                    {"__builtins__": {"abs": abs, "round": round, "math": math}},
                    context)

    except Exception as exc:
        write_log(f"[WARD] Eval error: {exc}")
        return None

# ----------------------------------------------------------------------
# MAIN DECODE FUNCTION
# ----------------------------------------------------------------------
def guardian_decode(tokens, giza=None):
    decoded = []
    anomaly = 0.0

    for tk in tokens:
        entry = {"token": tk, "glyph": "?"}
        decoded.append(entry)

        expression = f"{len(tk)} * 1.618"
        result = safe_eval(expression, {})

        if result is None:
            entry["warded"] = True
            anomaly += 0.20
        else:
            entry["value"] = round(result, 4)

    if giza:
        anomaly = min(1.0, anomaly + 0.1)

    return decoded, anomaly, WARD_LOG

# ======================================================================
# END — GUARDIAN v1.1 ENGINE
# ======================================================================
