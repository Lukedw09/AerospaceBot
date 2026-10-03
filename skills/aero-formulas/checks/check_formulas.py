"""Check script formulas against named numeric identities.

Reads the ```formula records in ../formulas.md, evaluates each `expr` with the
inputs named in identities.md, and writes check.md. A formula is listed there
only when every identity under it passes.

Run from anywhere:

    python check_formulas.py
    python check_formulas.py --init-identities
    python check_formulas.py --list
"""

from __future__ import annotations

import argparse
import ast
import math
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_FORMULAS = ROOT.parent / "formulas.md"
DEFAULT_IDENTITIES = ROOT / "identities.md"
DEFAULT_OUTPUT = ROOT / "check.md"

FUNCTIONS = {
    "log": math.log,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "cot": lambda value: 1.0 / math.tan(value),
    "atan": math.atan,
    "asin": math.asin,
}
CONSTANTS = {"pi": math.pi, "e": math.e}
IDENTITY_NAME = re.compile(r"- name:\s*([A-Za-z_][A-Za-z0-9_-]*)\s*")
DEFAULT_TOL = 1e-9
DEFAULT_REL = 1e-9


class FormulaFileError(Exception):
    """formulas.md could not be read as script records."""


class IdentityFileError(Exception):
    """identities.md is structurally invalid."""


class EvalError(Exception):
    """A script expression could not be reduced to a finite number."""


@dataclass(frozen=True)
class Formula:
    name: str
    category: str
    family: str
    expr: str
    symbols: tuple[str, ...]
    line: int

    @property
    def numeric(self) -> bool:
        if re.search(r"\bpartial\s*\(", self.expr):
            return False
        # integral(F, t) is indefinite. integral(lower, upper, integrand) is definite.
        return (
            re.search(r"\bintegral\s*\(\s*[^,()]+\s*,\s*[^,()]+\s*\)", self.expr)
            is None
        )

    @property
    def is_definition(self) -> bool:
        """Definitions are exempt from the identity check.

        A definition is a script whose id ends with ``_definition``, or a
        script that only states a derivative or an indefinite integral.
        """

        if self.name.endswith("_definition"):
            return True
        return not self.numeric


@dataclass(frozen=True)
class Identity:
    name: str
    category: str
    formula: str
    inputs: tuple[tuple[str, float], ...]
    expected: float
    tol: float | None
    rel: float | None
    line: int

    def limits(self) -> tuple[float, float]:
        """Absolute and relative tolerances.

        When both are omitted, each default is 1e-9. When one is set, the
        other is zero so the named bound is the only bound.
        """

        if self.tol is None and self.rel is None:
            return DEFAULT_TOL, DEFAULT_REL
        return (0.0 if self.tol is None else self.tol), (
            0.0 if self.rel is None else self.rel
        )


@dataclass(frozen=True)
class Outcome:
    formula: Formula
    identity: Identity
    ok: bool
    actual: float | None
    detail: str


def parse_formulas(text: str) -> list[Formula]:
    lines = text.splitlines()
    formulas: list[Formula] = []
    seen: set[str] = set()
    category: str | None = None
    seen_title = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("# ") and not line.startswith("##"):
            if not seen_title:
                seen_title = True
            else:
                category = line[2:].strip()
            index += 1
            continue
        if line.strip() != "```formula":
            index += 1
            continue
        start = index + 1
        index += 1
        block: list[str] = []
        while index < len(lines) and lines[index].strip() != "```":
            block.append(lines[index])
            index += 1
        if index >= len(lines):
            raise FormulaFileError(f"formulas.md:{start}: unclosed formula block")
        formula = _parse_formula_block(block, start, category)
        if formula.name in seen:
            raise FormulaFileError(
                f"formulas.md:{formula.line}: duplicate formula id {formula.name}"
            )
        seen.add(formula.name)
        formulas.append(formula)
        index += 1
    if not formulas:
        raise FormulaFileError("formulas.md: no script formula records found")
    return formulas


def _parse_formula_block(
    block: list[str], start_line: int, category: str | None
) -> Formula:
    if category is None:
        raise FormulaFileError(
            f"formulas.md:{start_line}: formula appears before a category heading"
        )
    fields: dict[str, str] = {}
    name: str | None = None
    name_line = start_line
    for offset, raw in enumerate(block):
        line_no = start_line + offset
        text = raw.strip()
        if text == "":
            continue
        if text.startswith("## "):
            if name is not None:
                raise FormulaFileError(
                    f"formulas.md:{line_no}: extra heading in formula block"
                )
            name = text[3:].strip()
            name_line = line_no
            continue
        if ":" not in text:
            raise FormulaFileError(
                f"formulas.md:{line_no}: expected name, family, expr, or symbols"
            )
        key, value = text.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key not in {"family", "expr", "symbols"}:
            raise FormulaFileError(
                f"formulas.md:{line_no}: unknown formula field {key}"
            )
        if key in fields:
            raise FormulaFileError(
                f"formulas.md:{line_no}: repeated formula field {key}"
            )
        fields[key] = value
    if name is None:
        raise FormulaFileError(f"formulas.md:{start_line}: formula block has no id")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise FormulaFileError(
            f"formulas.md:{name_line}: formula id {name!r} is not an identifier"
        )
    missing = [key for key in ("family", "expr", "symbols") if key not in fields]
    if missing:
        raise FormulaFileError(
            f"formulas.md:{name_line}: {name} is missing {', '.join(missing)}"
        )
    symbols = tuple(part.strip() for part in fields["symbols"].split(",") if part.strip())
    if not symbols:
        raise FormulaFileError(f"formulas.md:{name_line}: {name} has no symbols")
    for symbol in symbols:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
            raise FormulaFileError(
                f"formulas.md:{name_line}: {name} has invalid symbol {symbol!r}"
            )
    if len(set(symbols)) != len(symbols):
        raise FormulaFileError(
            f"formulas.md:{name_line}: {name} repeats a symbol"
        )
    return Formula(
        name=name,
        category=category,
        family=fields["family"],
        expr=fields["expr"],
        symbols=symbols,
        line=name_line,
    )


def free_names(expr: str) -> set[str]:
    """Names the expression reads. Function names such as sin are excluded."""

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise EvalError(f"could not parse expr: {exc.msg}") from exc
    found: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name):
                for arg in node.args:
                    self.visit(arg)
                return
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name) -> None:
            found.add(node.id)

    Visitor().visit(tree)
    return found


def symbol_notes(formula: Formula) -> list[str]:
    try:
        used = free_names(formula.expr)
    except EvalError as exc:
        return [f"{formula.name}: {exc}"]
    declared = set(formula.symbols)
    notes: list[str] = []
    missing = sorted(used - declared)
    extra = sorted(declared - used)
    if missing:
        notes.append(
            f"{formula.name}: expr uses {', '.join(missing)}, which is not in symbols"
        )
    if extra:
        notes.append(
            f"{formula.name}: symbols lists {', '.join(extra)}, which expr does not use"
        )
    return notes


def evaluate(expr: str, inputs: dict[str, float]) -> float:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise EvalError(f"could not parse expr: {exc.msg}") from exc
    try:
        value = _eval_node(tree.body, inputs, allow_names=True)
    except EvalError:
        raise
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise EvalError(str(exc)) from exc
    if not math.isfinite(value):
        raise EvalError("result is not a finite number")
    return value


def eval_constant(expr: str, line: int) -> float:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise IdentityFileError(
            f"identities.md:{line}: {expr!r} is not a number ({exc.msg})"
        ) from exc
    try:
        value = _eval_node(tree.body, {}, allow_names=False)
    except EvalError as exc:
        raise IdentityFileError(f"identities.md:{line}: {expr!r} {exc}") from exc
    if not math.isfinite(value):
        raise IdentityFileError(f"identities.md:{line}: {expr!r} is not finite")
    return value


def _eval_node(node: ast.AST, env: dict[str, float], allow_names: bool) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise EvalError("only real numbers are allowed")
        return float(node.value)
    if isinstance(node, ast.Name):
        if allow_names:
            if node.id not in env:
                raise EvalError(f"missing symbol {node.id}")
            return float(env[node.id])
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise EvalError(f"cannot use symbol {node.id} in a numeric answer")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_node(node.operand, env, allow_names)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
    ):
        left = _eval_node(node.left, env, allow_names)
        right = _eval_node(node.right, env, allow_names)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        return left**right
    if isinstance(node, ast.Call):
        if node.keywords or not isinstance(node.func, ast.Name):
            raise EvalError("only direct function calls are allowed")
        fname = node.func.id
        if fname == "integral":
            return _eval_integral(node, env, allow_names)
        if fname == "partial":
            raise EvalError(
                "partial() is not evaluated numerically, so this formula cannot pass an identity"
            )
        if fname not in FUNCTIONS:
            raise EvalError(f"unknown function {fname}")
        args = [_eval_node(arg, env, allow_names) for arg in node.args]
        try:
            return float(FUNCTIONS[fname](*args))
        except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
            raise EvalError(f"{fname}() {exc}") from exc
    raise EvalError(f"unsupported syntax {type(node).__name__}")


def _eval_integral(node: ast.Call, env: dict[str, float], allow_names: bool) -> float:
    """Exact definite integral of a polynomial integrand.

    ``integral(lower, upper, integrand)`` integrates with respect to the one
    name in the integrand that has no numeric input. A constant integrand uses
    the factor ``upper - lower``. ``integral(F, t)`` is indefinite and has no
    numeric value.
    """

    if len(node.args) != 3:
        raise EvalError(
            "indefinite integral() is not a number, so this formula cannot pass an identity"
        )
    lower = _eval_node(node.args[0], env, allow_names)
    upper = _eval_node(node.args[1], env, allow_names)
    unbound = _unbound_names(node.args[2], env)
    if len(unbound) > 1:
        names = ", ".join(sorted(unbound))
        raise EvalError(f"integrand depends on more than one free symbol: {names}")
    dummy = next(iter(unbound)) if unbound else None
    polynomial = _polynomial(node.args[2], dummy, env)
    total = 0.0
    for power, coeff in polynomial.items():
        total += coeff * (upper ** (power + 1) - lower ** (power + 1)) / (power + 1)
    return total


def _unbound_names(node: ast.AST, env: dict[str, float]) -> set[str]:
    found: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, call: ast.Call) -> None:
            for arg in call.args:
                self.visit(arg)

        def visit_Name(self, name: ast.Name) -> None:
            if name.id not in env:
                found.add(name.id)

    Visitor().visit(node)
    return found


def _polynomial(node: ast.AST, dummy: str | None, env: dict[str, float]) -> dict[int, float]:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise EvalError("only real numbers are allowed")
        return {0: float(node.value)}
    if isinstance(node, ast.Name):
        if dummy is not None and node.id == dummy:
            return {1: 1.0}
        if node.id not in env:
            raise EvalError(f"missing symbol {node.id}")
        return {0: float(env[node.id])}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _polynomial(node.operand, dummy, env)
        if isinstance(node.op, ast.UAdd):
            return value
        return _scale_poly(value, -1.0)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        left = _polynomial(node.left, dummy, env)
        right = _polynomial(node.right, dummy, env)
        if isinstance(node.op, ast.Sub):
            right = _scale_poly(right, -1.0)
        return _add_poly(left, right)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _mul_poly(
            _polynomial(node.left, dummy, env),
            _polynomial(node.right, dummy, env),
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _polynomial(node.left, dummy, env)
        right = _polynomial(node.right, dummy, env)
        if set(right) - {0}:
            raise EvalError("only division by a constant is integrated")
        denom = right.get(0, 0.0)
        return _scale_poly(left, 1.0 / denom)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        base = _polynomial(node.left, dummy, env)
        exponent = _polynomial(node.right, dummy, env)
        if set(exponent) - {0}:
            raise EvalError("only a constant power is integrated")
        power = exponent.get(0, 0.0)
        if power < 0 or power != int(power):
            raise EvalError("only a non-negative integer power is integrated")
        degree = int(power)
        if set(base) <= {0}:
            return {0: base.get(0, 0.0) ** degree}
        if base == {1: 1.0}:
            return {degree: 1.0}
        raise EvalError("only a constant or the integration variable is raised to a power")
    raise EvalError(f"unsupported integrand syntax {type(node).__name__}")


def _add_poly(left: dict[int, float], right: dict[int, float]) -> dict[int, float]:
    keys = set(left) | set(right)
    total = {key: left.get(key, 0.0) + right.get(key, 0.0) for key in keys}
    return {key: value for key, value in total.items() if value != 0.0} or {0: 0.0}


def _scale_poly(poly: dict[int, float], factor: float) -> dict[int, float]:
    total = {key: value * factor for key, value in poly.items() if value * factor != 0.0}
    return total or {0: 0.0}


def _mul_poly(left: dict[int, float], right: dict[int, float]) -> dict[int, float]:
    total: dict[int, float] = {}
    for left_power, left_coeff in left.items():
        for right_power, right_coeff in right.items():
            power = left_power + right_power
            total[power] = total.get(power, 0.0) + left_coeff * right_coeff
    return {key: value for key, value in total.items() if value != 0.0} or {0: 0.0}


def mask_code_fences(lines: list[str]) -> list[str]:
    masked: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            masked.append("")
            continue
        masked.append("" if in_fence else line)
    if in_fence:
        raise IdentityFileError("identities.md: unclosed code fence")
    return masked


def parse_identities(text: str, formulas: list[Formula]) -> list[Identity]:
    by_name = {formula.name: formula for formula in formulas}
    categories = list(dict.fromkeys(formula.category for formula in formulas))
    lines = mask_code_fences(text.splitlines())
    identities: list[Identity] = []
    seen_sections: set[str] = set()
    seen_names: set[tuple[str, str]] = set()
    category: str | None = None
    formula_name: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        line_no = index + 1
        if _is_category(line):
            category = line[3:].strip()
            if category not in categories:
                known = ", ".join(categories)
                raise IdentityFileError(
                    f"identities.md:{line_no}: unknown category {category!r}. "
                    f"Use one of: {known}"
                )
            formula_name = None
            index += 1
            continue
        if category is None:
            if line.startswith("- name:"):
                raise IdentityFileError(
                    f"identities.md:{line_no}: identity appears before a category"
                )
            index += 1
            continue
        if line.startswith("### "):
            formula_name = line[4:].strip()
            if formula_name not in by_name:
                raise IdentityFileError(
                    f"identities.md:{line_no}: unknown formula {formula_name}"
                )
            owner = by_name[formula_name]
            if owner.category != category:
                raise IdentityFileError(
                    f"identities.md:{line_no}: {formula_name} is in "
                    f"{owner.category}, not {category}"
                )
            if formula_name in seen_sections:
                raise IdentityFileError(
                    f"identities.md:{line_no}: repeated formula section {formula_name}"
                )
            seen_sections.add(formula_name)
            index += 1
            continue
        if _is_ignored(line):
            index += 1
            continue
        if line.startswith("- name:"):
            if formula_name is None:
                raise IdentityFileError(
                    f"identities.md:{line_no}: identity is not under a ### formula id"
                )
            block = [line]
            index += 1
            while index < len(lines) and not _is_boundary(lines[index]):
                block.append(lines[index])
                index += 1
            identity = _parse_identity_block(
                block, line_no, category, by_name[formula_name]
            )
            key = (identity.formula, identity.name)
            if key in seen_names:
                raise IdentityFileError(
                    f"identities.md:{identity.line}: duplicate identity "
                    f"{identity.name} under {identity.formula}"
                )
            seen_names.add(key)
            identities.append(identity)
            continue
        raise IdentityFileError(
            f"identities.md:{line_no}: unexpected line {line.strip()!r}"
        )
    return identities


def _is_category(line: str) -> bool:
    return line.startswith("## ") and not line.startswith("### ")


def _is_boundary(line: str) -> bool:
    return line.startswith("#") or line.startswith("- name:")


def _is_ignored(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped == ""
        or stripped.startswith("<!--")
        or line.startswith("####")
        or (line.startswith("#") and not line.startswith("##"))
    )


def _parse_identity_block(
    block: list[str], start_line: int, category: str, formula: Formula
) -> Identity:
    match = IDENTITY_NAME.fullmatch(block[0])
    if match is None:
        raise IdentityFileError(
            f"identities.md:{start_line}: identity name must be an identifier"
        )
    name = match.group(1)
    inputs: dict[str, float] = {}
    expected: float | None = None
    tol: float | None = None
    rel: float | None = None
    vary: set[str] = set()
    seen_inputs = False
    in_inputs = False
    seen_fields: set[str] = set()
    for offset, raw in enumerate(block[1:], start=1):
        line_no = start_line + offset
        if raw.strip() == "" or raw.strip().startswith("<!--"):
            continue
        if in_inputs and raw.startswith("    "):
            key, value = _split_field(raw.strip(), line_no)
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                raise IdentityFileError(
                    f"identities.md:{line_no}: invalid symbol {key!r}"
                )
            if value == "":
                raise IdentityFileError(
                    f"identities.md:{line_no}: {key} needs a numeric value"
                )
            if key in inputs:
                raise IdentityFileError(
                    f"identities.md:{line_no}: repeated input {key}"
                )
            inputs[key] = eval_constant(value, line_no)
            continue
        if raw.startswith("  ") and not raw.startswith("    "):
            key, value = _split_field(raw.strip(), line_no)
            if key in seen_fields:
                raise IdentityFileError(
                    f"identities.md:{line_no}: repeated field {key}"
                )
            seen_fields.add(key)
            if key == "inputs":
                if value != "":
                    raise IdentityFileError(
                        f"identities.md:{line_no}: put each input on its own indented line"
                    )
                seen_inputs = True
                in_inputs = True
                continue
            in_inputs = False
            if key == "vary":
                if value == "":
                    raise IdentityFileError(
                        f"identities.md:{line_no}: vary needs the integration variable"
                    )
                names = [part.strip() for part in value.split(",")]
                if not names or any(
                    re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part) is None for part in names
                ):
                    raise IdentityFileError(
                        f"identities.md:{line_no}: vary must list symbols"
                    )
                vary = set(names)
                continue
            if value == "":
                raise IdentityFileError(
                    f"identities.md:{line_no}: {key} needs a numeric value"
                )
            number = eval_constant(value, line_no)
            if key == "expected":
                expected = number
            elif key == "tol":
                if number < 0:
                    raise IdentityFileError(
                        f"identities.md:{line_no}: tol must be >= 0"
                    )
                tol = number
            elif key == "rel":
                if number < 0:
                    raise IdentityFileError(
                        f"identities.md:{line_no}: rel must be >= 0"
                    )
                rel = number
            else:
                raise IdentityFileError(
                    f"identities.md:{line_no}: unknown field {key}"
                )
            continue
        raise IdentityFileError(
            f"identities.md:{line_no}: indent fields two spaces, and inputs four spaces"
        )
    if not seen_inputs:
        raise IdentityFileError(
            f"identities.md:{start_line}: {name} is missing inputs"
        )
    if expected is None:
        raise IdentityFileError(
            f"identities.md:{start_line}: {name} is missing expected"
        )
    declared = set(formula.symbols)
    unknown_vary = sorted(vary - declared)
    if unknown_vary:
        raise IdentityFileError(
            f"identities.md:{start_line}: {formula.name} has no symbol "
            + ", ".join(unknown_vary)
        )
    varied_inputs = sorted(vary & set(inputs))
    if varied_inputs:
        raise IdentityFileError(
            f"identities.md:{start_line}: do not assign "
            + ", ".join(varied_inputs)
            + "; it is named by vary"
        )
    missing = [symbol for symbol in formula.symbols if symbol not in inputs and symbol not in vary]
    extra = sorted(set(inputs) - declared)
    if missing or extra:
        raise IdentityFileError(
            f"identities.md:{start_line}: {formula.name} inputs must be "
            f"{', '.join(symbol for symbol in formula.symbols if symbol not in vary)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; extra {', '.join(extra)}" if extra else "")
        )
    ordered = tuple(
        (symbol, inputs[symbol]) for symbol in formula.symbols if symbol in inputs
    )
    return Identity(
        name=name,
        category=category,
        formula=formula.name,
        inputs=ordered,
        expected=expected,
        tol=tol,
        rel=rel,
        line=start_line,
    )


def _split_field(text: str, line: int) -> tuple[str, str]:
    if ":" not in text:
        raise IdentityFileError(f"identities.md:{line}: expected key: value")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def check_identity(formula: Formula, identity: Identity) -> Outcome:
    tol, rel = identity.limits()
    try:
        actual = evaluate(formula.expr, dict(identity.inputs))
    except EvalError as exc:
        return Outcome(formula, identity, False, None, str(exc))
    limit = tol + rel * abs(identity.expected)
    if abs(actual - identity.expected) <= limit:
        return Outcome(formula, identity, True, actual, "")
    return Outcome(
        formula,
        identity,
        False,
        actual,
        (
            f"expected {_fmt(identity.expected)}, got {_fmt(actual)}, "
            f"limit {_fmt(limit)}"
        ),
    )


def run_checks(
    formulas: list[Formula], identities: list[Identity]
) -> tuple[dict[str, list[str]], list[Outcome], list[Formula]]:
    grouped: dict[str, list[Identity]] = {}
    for identity in identities:
        grouped.setdefault(identity.formula, []).append(identity)
    passed: dict[str, list[str]] = {}
    failed: list[Outcome] = []
    unchecked: list[Formula] = []
    for formula in formulas:
        named = grouped.get(formula.name, [])
        if not named:
            if not formula.is_definition:
                unchecked.append(formula)
            continue
        outcomes = [check_identity(formula, identity) for identity in named]
        if all(outcome.ok for outcome in outcomes):
            passed[formula.name] = [outcome.identity.name for outcome in outcomes]
        else:
            failed.extend(outcome for outcome in outcomes if not outcome.ok)
    return passed, failed, unchecked


def render_check(
    formulas: list[Formula],
    passed: dict[str, list[str]],
    failed_count: int,
    unchecked_count: int,
) -> str:
    categories = list(dict.fromkeys(formula.category for formula in formulas))
    lines = [
        "# Checked formulas",
        "",
        "Generated by `check_formulas.py` from `identities.md`.",
        "A formula is listed when every identity named for it passed, or when it is a definition.",
        "A definition is exempt from the identity check.",
        "Use only these formula ids. Do not use a formula that is absent from this file.",
        "",
        f"Passed: {len(passed)}",
        f"Failed: {failed_count}",
        f"Unchecked: {unchecked_count}",
        "",
        "## Definitions",
        "",
        "Exempt from the identity check.",
        "",
    ]
    definitions = [formula for formula in formulas if formula.is_definition]
    if definitions:
        for formula in definitions:
            lines.append(f"- `{formula.name}` ({formula.family})")
    else:
        lines.append("None.")
    lines.append("")
    if not passed:
        lines.extend(
            [
                "No formula has passed an identity check.",
                "",
                "Add identities under the formula ids in `identities.md`, then run `python check_formulas.py`.",
                "",
            ]
        )
    for category in categories:
        lines.append(f"## {category}")
        lines.append("")
        found = False
        for formula in formulas:
            if formula.category != category:
                continue
            if formula.name in passed:
                found = True
                names = ", ".join(passed[formula.name])
                lines.append(f"- `{formula.name}` ({formula.family}): {names}")
            elif formula.is_definition:
                found = True
                lines.append(
                    f"- `{formula.name}` ({formula.family}): definition, exempt from the identity check"
                )
        if not found:
            lines.append("None.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_identities(formulas: list[Formula]) -> str:
    categories = list(dict.fromkeys(formula.category for formula in formulas))
    lines = [
        "# Identities",
        "",
        "Named numeric checks for the script records in `../formulas.md`.",
        "`check_formulas.py` evaluates each formula `expr` with the inputs below.",
        "A formula is written to `check.md` when every identity under it passes.",
        "A definition is exempt from that requirement and is still written to `check.md`.",
        "Any other formula with no identity stays unchecked and is omitted from `check.md`.",
        "",
        "The expected number is the physical value of the recorded quantity.",
        "`inputs` must set every symbol listed for the formula.",
        "Name an integration variable with `vary` and do not assign it an input.",
        "Values may be numbers or numeric expressions such as `7/5` or `2/2.4`.",
        "Inside those values, `pi` and `e` are the math constants. They are not implied symbols of a formula.",
        "`log` in a formula is the natural logarithm.",
        "",
        "A check passes when `abs(actual - expected) <= tol + rel * abs(expected)`.",
        "If both `tol` and `rel` are omitted, each is `1e-9`.",
        "If only one is set, the other is `0`.",
        "",
        "`partial(...)` and an indefinite `integral(F, t)` are not numbers.",
        "A definite `integral(lower, upper, integrand)` is integrated exactly.",
        "",
        "Add one or more identities under a formula id:",
        "",
        "```",
        "- name: gamma_7_over_5",
        "  inputs:",
        "    g: 7/5",
        "  expected: 5/6",
        "  tol: 1e-12",
        "  rel: 0",
        "```",
        "",
        "Then run `python check_formulas.py`.",
        "",
    ]
    for category in categories:
        lines.append(f"## {category}")
        lines.append("")
        family: str | None = None
        for formula in formulas:
            if formula.category != category:
                continue
            if formula.family != family:
                family = formula.family
                lines.append(f"#### {family}")
                lines.append("")
            lines.append(f"### {formula.name}")
            lines.append("")
            status = (
                "yes"
                if formula.numeric
                else "no (uses partial or an indefinite integral)"
            )
            lines.append(
                "<!-- "
                + f"family: {formula.family}; symbols: {', '.join(formula.symbols)}; "
                + f"expr: {formula.expr.replace('-->', '- ->')}; numeric: {status}"
                + " -->"
            )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_list(formulas: list[Formula]) -> str:
    categories = list(dict.fromkeys(formula.category for formula in formulas))
    lines: list[str] = []
    for category in categories:
        chosen = [formula for formula in formulas if formula.category == category]
        lines.append(f"{category} ({len(chosen)})")
        family: str | None = None
        for formula in chosen:
            if formula.family != family:
                family = formula.family
                lines.append(f"  {family}")
            mark = "" if formula.numeric else "  [not numeric]"
            lines.append(
                f"    {formula.name}  symbols: {', '.join(formula.symbols)}{mark}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _fmt(value: float) -> str:
    return f"{value:.16g}"


def execute(formulas_path: Path, identities_path: Path, output_path: Path) -> int:
    if not formulas_path.is_file():
        print(f"Missing formulas file: {formulas_path}", file=sys.stderr)
        return 2
    try:
        formulas = parse_formulas(formulas_path.read_text(encoding="utf-8"))
    except FormulaFileError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not identities_path.is_file():
        print(
            f"Missing {identities_path}. Run: python check_formulas.py --init-identities",
            file=sys.stderr,
        )
        return 2
    try:
        identities = parse_identities(
            identities_path.read_text(encoding="utf-8"), formulas
        )
    except IdentityFileError as exc:
        print(str(exc), file=sys.stderr)
        print("check.md was not changed.", file=sys.stderr)
        return 2
    for formula in formulas:
        for note in symbol_notes(formula):
            print(f"warning: {note}")
    passed, failed, unchecked = run_checks(formulas, identities)
    failed_formulas = {outcome.formula.name for outcome in failed}
    output_path.write_bytes(
        render_check(formulas, passed, len(failed_formulas), len(unchecked)).encode(
            "utf-8"
        )
    )
    for outcome in failed:
        print(
            f"FAIL {outcome.formula.category} / {outcome.formula.name} / "
            f"{outcome.identity.name}: {outcome.detail}"
        )
    print(f"Identities: {len(identities)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed_formulas)}")
    print(f"Unchecked: {len(unchecked)}")
    print(f"Wrote {output_path}")
    return 1 if failed else 0


def init_identities(formulas_path: Path, identities_path: Path) -> int:
    if identities_path.exists():
        print(f"Refusing to overwrite {identities_path}", file=sys.stderr)
        return 2
    try:
        formulas = parse_formulas(formulas_path.read_text(encoding="utf-8"))
    except FormulaFileError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    identities_path.write_bytes(render_identities(formulas).encode("utf-8"))
    print(f"Wrote {identities_path}")
    return 0


def self_test() -> int:
    text = DEFAULT_FORMULAS.read_text(encoding="utf-8")
    formulas = parse_formulas(text)
    if text.count("```formula") != len(formulas):
        print("self-test: formula count does not match formula fences", file=sys.stderr)
        return 1
    categories = list(dict.fromkeys(formula.category for formula in formulas))
    if categories != [
        "Compressible flow",
        "Atmosphere",
        "Rocket propulsion",
        "Aerodynamics",
        "Structures",
    ]:
        print(f"self-test: unexpected categories {categories}", file=sys.stderr)
        return 1
    by_name = {formula.name: formula for formula in formulas}
    problems: list[str] = []
    for formula in formulas:
        problems.extend(symbol_notes(formula))
    if problems:
        print("self-test: symbol mismatch", file=sys.stderr)
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    def expect(name: str, inputs: dict[str, float], value: float) -> None:
        got = evaluate(by_name[name].expr, inputs)
        if abs(got - value) > 1e-12:
            raise AssertionError(f"{name}: got {got}, expected {value}")

    expect("sonic_temperature", {"g": 1.4}, 2.0 / 2.4)
    expect("area_mach", {"M": 1.0, "g": 1.4}, 1.0)
    expect("normal_shock_pressure", {"g": 1.4, "M1": 1.0}, 1.0)
    expect("normal_shock_pressure_air", {"M1": 2.0}, 4.5)
    expect("mach_angle", {"M": 2.0}, math.asin(0.5))
    expect("prandtl_meyer", {"g": 1.4, "M": 1.0}, 0.0)
    expect("mass_ratio", {"mf": 2.0, "m0": 8.0}, 0.25)
    expect("delta_v_vacuum", {"c": 3000.0, "m0": math.e, "mf": 1.0}, 3000.0)
    gamma = evaluate(
        by_name["gamma_imperfect"].expr,
        {"g_perf": 1.4, "theta": 3055.6, "T": 3000.0},
    )
    if not 1.0 < gamma < 1.4:
        print(f"self-test: gamma_imperfect out of range {gamma}", file=sys.stderr)
        return 1
    try:
        evaluate(by_name["cp_definition"].expr, {"h": 1.0, "T": 300.0})
    except EvalError:
        pass
    else:
        print("self-test: partial() was evaluated", file=sys.stderr)
        return 1
    if abs(evaluate("integral(0, 2, x)", {}) - 2.0) > 1e-12:
        print("self-test: integral of x", file=sys.stderr)
        return 1
    if abs(evaluate("integral(1, 3, 2*x + 5)", {}) - 18.0) > 1e-12:
        print("self-test: integral of 2x+5", file=sys.stderr)
        return 1
    try:
        evaluate("integral(F, t)", {"F": 1.0, "t": 2.0})
    except EvalError:
        pass
    else:
        print("self-test: indefinite integral was evaluated", file=sys.stderr)
        return 1

    sample = "\n".join(
        [
            "# Identities",
            "",
            "```",
            "- name: not_live",
            "  inputs:",
            "    g: 1",
            "  expected: 1",
            "```",
            "",
            "## Compressible flow",
            "",
            "### sonic_temperature",
            "",
            "- name: air",
            "  inputs:",
            "    g: 7/5",
            "  expected: 5/6",
            "",
            "### perfect_gas",
            "",
            "- name: wrong",
            "  inputs:",
            "    rho: 2",
            "    R: 3",
            "    T: 4",
            "  expected: 0",
            "  tol: 0",
            "  rel: 0",
            "",
        ]
    )
    parsed = parse_identities(sample, formulas)
    if [item.name for item in parsed] != ["air", "wrong"]:
        print("self-test: identity parse mismatch", file=sys.stderr)
        return 1
    template = render_identities(formulas)
    if parse_identities(template, formulas):
        print("self-test: empty template parsed as identities", file=sys.stderr)
        return 1
    passed, failed, unchecked = run_checks(formulas, parsed)
    if set(passed) != {"sonic_temperature"}:
        print(f"self-test: pass set {set(passed)}", file=sys.stderr)
        return 1
    if len(failed) != 1 or failed[0].formula.name != "perfect_gas":
        print("self-test: expected perfect_gas to fail", file=sys.stderr)
        return 1
    definitions = {formula.name for formula in formulas if formula.is_definition}
    if not {
        "cp_definition",
        "cv_definition",
        "gamma_definition",
        "enthalpy_definition",
        "thrust_coefficient_definition",
        "total_impulse",
        "burn_rate_temperature_sensitivity",
        "pressure_temperature_sensitivity",
    } <= definitions:
        print("self-test: definition set", file=sys.stderr)
        return 1
    if by_name["sonic_temperature"].is_definition or by_name["area_mach"].is_definition:
        print("self-test: non-definition marked as a definition", file=sys.stderr)
        return 1
    if len(unchecked) != len(formulas) - 2 - len(definitions):
        print("self-test: unchecked count", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "check.md"
        output.write_bytes(
            render_check(formulas, passed, 1, len(unchecked)).encode("utf-8")
        )
        written = output.read_text(encoding="utf-8")
    if "`sonic_temperature`" not in written or "`perfect_gas`" in written:
        print("self-test: check.md contents", file=sys.stderr)
        return 1
    if "`cp_definition`" not in written or "`total_impulse`" not in written:
        print("self-test: definitions missing from check.md", file=sys.stderr)
        return 1
    print(f"self-test: ok ({len(formulas)} formulas)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formulas", type=Path, default=DEFAULT_FORMULAS)
    parser.add_argument("--identities", type=Path, default=DEFAULT_IDENTITIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--init-identities",
        action="store_true",
        help="write identities.md if it does not already exist",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print categories, families, and formula ids",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="check the parser and a few known formula values",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.list:
        try:
            formulas = parse_formulas(args.formulas.read_text(encoding="utf-8"))
        except (OSError, FormulaFileError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        sys.stdout.write(render_list(formulas))
        return 0
    if args.init_identities:
        return init_identities(args.formulas, args.identities)
    return execute(args.formulas, args.identities, args.output)


if __name__ == "__main__":
    sys.exit(main())
