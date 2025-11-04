"""
codex.utils.safe_eval
Secure, limited expression evaluator for numeric expressions used by the Codex kernel.

Features:
- Uses Python AST to safely evaluate arithmetic expressions and a whitelist of names/functions.
- Supports basic operators: +, -, *, /, **, unary -, parentheses.
- Supports a small set of math functions: sin, cos, tan, exp, log, sqrt, floor, ceil.
- Usage:
    from codex.utils.safe_eval import safe_eval
    value = safe_eval("amplitude * (1 + 0.2 * sin(phase))", {"amplitude": 1.5, "phase": 0.3})
"""

from __future__ import annotations
import ast
import math
from typing import Any, Dict, Optional

# Allowed AST node types
_ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
    ast.Name, ast.Load, ast.Call, ast.Pow, ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.USub, ast.UAdd, ast.Mod, ast.FloorDiv, ast.Tuple, ast.List
}

# Map AST operator classes to Python operations where needed (we use recursion evaluation)
# Allowed functions (whitelist)
_ALLOWED_FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
}

def _ensure_safe_node(node: ast.AST) -> None:
    """Recursively verify only allowed nodes are present."""
    node_type = type(node)
    if node_type not in _ALLOWED_NODES:
        raise ValueError(f"Disallowed expression element: {node_type.__name__}")
    for child in ast.iter_child_nodes(node):
        _ensure_safe_node(child)

def _eval_node(node: ast.AST, symbols: Dict[str, Any]) -> Any:
    """Recursively evaluate an AST node in a controlled manner."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, symbols)
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    if isinstance(node, ast.Num):  # older compatibility
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, symbols)
        right = _eval_node(node.right, symbols)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.Pow):
            return left ** right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.FloorDiv):
            return left // right
        raise ValueError(f"Unsupported binary operator: {type(op).__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, symbols)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
    if isinstance(node, ast.Name):
        if node.id in symbols:
            return symbols[node.id]
        # Support constants like pi, e
        if node.id == "pi":
            return math.pi
        if node.id == "e":
            return math.e
        raise NameError(f"Unknown identifier: {node.id}")
    if isinstance(node, ast.Call):
        # Only allow simple calls with a Name as func
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        func_name = node.func.id
        if func_name not in _ALLOWED_FUNCS:
            raise NameError(f"Function not allowed: {func_name}")
        func = _ALLOWED_FUNCS[func_name]
        args = [_eval_node(a, symbols) for a in node.args]
        # no kwargs allowed
        return func(*args)
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_eval_node(elt, symbols) for elt in node.elts)
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")

def safe_eval(expr: str, symbols: Optional[Dict[str, Any]] = None) -> float:
    """
    Safely evaluate a numeric expression in `expr`, substituting any variables from `symbols`.

    :param expr: Expression string, e.g. "amplitude * (1 + 0.2 * sin(phase))"
    :param symbols: mapping of variable names to numeric values
    :return: numeric result as float
    :raises: ValueError, NameError on disallowed constructs
    """
    if symbols is None:
        symbols = {}
    if not isinstance(expr, str):
        raise TypeError("Expression must be a string")
    # parse
    tree = ast.parse(expr, mode="eval")
    # validate tree nodes
    _ensure_safe_node(tree)
    result = _eval_node(tree, symbols)
    # coerce result to float when possible
    try:
        return float(result)
    except Exception:
        return result
