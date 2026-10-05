"""Look up an allowed formula and evaluate a plain expression."""

from __future__ import annotations

import ast
import json
import math
import operator
import re
from pathlib import Path

ID_LINE = re.compile(r"`([a-z][a-z0-9_]*)`")
FENCE = re.compile(r"```formula\n(.*?)```", re.DOTALL)
FIELD = re.compile(r"^(family|expr|symbols):\s*(.+)$", re.MULTILINE)

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {
    "log": math.log,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "atan": math.atan,
    "asin": math.asin,
    "acos": math.acos,
    "sqrt": math.sqrt,
}


def allowed_ids(check_md: Path) -> set[str]:
    return set(ID_LINE.findall(check_md.read_text(encoding="utf-8")))


def _blocks(formulas_md: Path) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for match in FENCE.finditer(formulas_md.read_text(encoding="utf-8")):
        body = match.group(1)
        name = re.search(r"^##\s+(\S+)", body, re.MULTILINE)
        if not name:
            continue
        fields = {key: value.strip() for key, value in FIELD.findall(body)}
        fields["body"] = body.strip()
        fields["start"] = str(match.start())
        found[name.group(1)] = fields
    return found


def _surrounding(text: str, start: int) -> str:
    before = text.rfind("\n## ", 0, start)
    heading = 0 if before < 0 else before + 1
    display = text[heading:start].strip()
    fence_close = text.find("\n```", start)
    search_from = fence_close if fence_close > 0 else start
    after = text.find("\n## ", search_from)
    tail_end = after if after > 0 else min(len(text), search_from + 2500)
    return (display + "\n\n" + text[start:tail_end]).strip()


def _eval(expr: str, values: dict[str, float]) -> float:
    tree = ast.parse(expr, mode="eval")

    def walk(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in values:
                raise ValueError(f"missing symbol {node.id}")
            return float(values[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return _BINOPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](walk(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func = _FUNCS.get(node.func.id)
            if func is None or node.keywords:
                raise ValueError("expression is not a plain numeric formula")
            return float(func(*(walk(arg) for arg in node.args)))
        raise ValueError("expression is not a plain numeric formula")

    return walk(tree)


def lookup_formula(
    formulas_md: Path,
    check_md: Path,
    formula_id: str,
    values_json: dict[str, object] | str | None = None,
) -> str:
    if formula_id not in allowed_ids(check_md):
        return "that formula is not allowed"
    blocks = _blocks(formulas_md)
    block = blocks.get(formula_id)
    if block is None:
        return "that formula is not allowed"
    text = formulas_md.read_text(encoding="utf-8")
    shown = _surrounding(text, int(block["start"]))
    expr = block.get("expr", "")
    if "partial(" in expr or "integral(" in expr:
        return shown + "\n\nThis record is a definition. No number was computed."
    if not values_json:
        return shown
    if isinstance(values_json, str):
        try:
            raw = json.loads(values_json)
        except json.JSONDecodeError:
            return shown + "\n\nvalues_json was not valid JSON. No number was computed."
    else:
        raw = values_json
    if not isinstance(raw, dict):
        return shown + "\n\nvalues_json must be an object of symbol names to numbers."
    symbols = [part.strip() for part in block.get("symbols", "").split(",") if part.strip()]
    missing = [name for name in symbols if name not in raw]
    if missing:
        return shown + "\n\nMissing symbols: " + ", ".join(missing) + ". No number was computed."
    values = {name: float(raw[name]) for name in symbols}
    try:
        number = _eval(expr, values)
    except (ValueError, ZeroDivisionError, TypeError) as exc:
        return shown + f"\n\nNo number was computed: {exc}"
    return shown + f"\n\nresult: {number:.8g}"
