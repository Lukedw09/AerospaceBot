"""Safe arithmetic and unit conversion for the calculate tool.

No eval or exec. Expressions walk a restricted AST. Unit conversion uses a
fixed table. Symbols and SI prefixes are case-sensitive: m means milli and M
means mega. Whole-word names such as "meters" match in any case. An ambiguous
or unknown symbol is an error. Temperature conversions are absolute readings
and reject values below absolute zero.
"""

from __future__ import annotations

import ast
import math
import re
import time
from dataclasses import dataclass

TIME_LIMIT_SEC = 1.0
MAX_EXPONENT = 1000
MAX_DIGITS = 10_000
MAX_EXPRESSION_CHARS = 4_000
MAX_NODES = 10_000
MAX_DEPTH = 100
# 10_000 decimal digits is about 33_219 bits.
MAX_BITS = int(MAX_DIGITS * math.log2(10)) + 1

_FUNCTIONS = {
    "sqrt": (math.sqrt, 1),
    "sin": (math.sin, 1),
    "cos": (math.cos, 1),
    "tan": (math.tan, 1),
    "asin": (math.asin, 1),
    "acos": (math.acos, 1),
    "atan": (math.atan, 1),
    "arcsin": (math.asin, 1),
    "arccos": (math.acos, 1),
    "arctan": (math.atan, 1),
    "atan2": (math.atan2, 2),
    "arctan2": (math.atan2, 2),
    "log": (math.log, (1, 2)),
    "log10": (math.log10, 1),
    "exp": (math.exp, 1),
    "radians": (math.radians, 1),
    "degrees": (math.degrees, 1),
}

_CONSTANTS = {"pi": math.pi, "e": math.e}

_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)

# factor: multiply by this to reach the SI unit of the dimension.
# Keys are exact symbols. Do not lowercase them: mPa and MPa are different.
_FOOT_M = 0.3048
_STD_GRAVITY = 9.80665  # standard gravity, m/s^2, exact by convention
_KNOT_MPS = 1852.0 / 3600.0
_LBF_N = 0.45359237 * _STD_GRAVITY
_PSI_PA = _LBF_N / (0.0254 ** 2)
_AU_M = 149_597_870_700.0

_SYMBOLS: dict[str, tuple[str, float]] = {
    "m": ("length", 1.0),
    "km": ("length", 1000.0),
    "cm": ("length", 0.01),
    "mm": ("length", 0.001),
    "Mm": ("length", 1_000_000.0),
    "ft": ("length", _FOOT_M),
    "in": ("length", 0.0254),
    "yd": ("length", 0.9144),
    "mi": ("length", 1609.344),
    "nmi": ("length", 1852.0),
    "AU": ("length", _AU_M),
    "s": ("time", 1.0),
    "ms": ("time", 0.001),
    "Ms": ("time", 1_000_000.0),
    "us": ("time", 1e-6),
    "ns": ("time", 1e-9),
    "min": ("time", 60.0),
    "h": ("time", 3600.0),
    "day": ("time", 86400.0),
    "sec": ("time", 1.0),
    "secs": ("time", 1.0),
    "msec": ("time", 0.001),
    "mins": ("time", 60.0),
    "hr": ("time", 3600.0),
    "hrs": ("time", 3600.0),
    "m/s": ("speed", 1.0),
    "km/s": ("speed", 1000.0),
    "ft/s": ("speed", _FOOT_M),
    "km/h": ("speed", 1000.0 / 3600.0),
    "mph": ("speed", 1609.344 / 3600.0),
    "kn": ("speed", _KNOT_MPS),
    "kt": ("speed", _KNOT_MPS),
    "kts": ("speed", _KNOT_MPS),
    "knot": ("speed", _KNOT_MPS),
    "knots": ("speed", _KNOT_MPS),
    "m/sec": ("speed", 1.0),
    "m/second": ("speed", 1.0),
    "mps": ("speed", 1.0),
    "km/sec": ("speed", 1000.0),
    "km/second": ("speed", 1000.0),
    "kps": ("speed", 1000.0),
    "ft/sec": ("speed", _FOOT_M),
    "ft/second": ("speed", _FOOT_M),
    "feet/s": ("speed", _FOOT_M),
    "feet/sec": ("speed", _FOOT_M),
    "feet/second": ("speed", _FOOT_M),
    "fps": ("speed", _FOOT_M),
    "km/hr": ("speed", 1000.0 / 3600.0),
    "km/hour": ("speed", 1000.0 / 3600.0),
    "kph": ("speed", 1000.0 / 3600.0),
    "mi/h": ("speed", 1609.344 / 3600.0),
    "mi/hr": ("speed", 1609.344 / 3600.0),
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
    "mg": ("mass", 1e-6),
    "Mg": ("mass", 1000.0),
    "lb": ("mass", 0.45359237),
    "lbs": ("mass", 0.45359237),
    "lbm": ("mass", 0.45359237),
    "slug": ("mass", 14.59390294),
    "N": ("force", 1.0),
    "kN": ("force", 1000.0),
    "mN": ("force", 0.001),
    "MN": ("force", 1_000_000.0),
    "lbf": ("force", _LBF_N),
    "kgf": ("force", _STD_GRAVITY),
    "Pa": ("pressure", 1.0),
    "kPa": ("pressure", 1_000.0),
    "MPa": ("pressure", 1_000_000.0),
    "GPa": ("pressure", 1_000_000_000.0),
    "mPa": ("pressure", 0.001),
    "bar": ("pressure", 100_000.0),
    "atm": ("pressure", 101_325.0),
    "psi": ("pressure", _PSI_PA),
    "deg": ("angle", math.pi / 180.0),
    "rad": ("angle", 1.0),
    "arcmin": ("angle", math.pi / (180.0 * 60.0)),
    "arcsec": ("angle", math.pi / (180.0 * 3600.0)),
    "m/s^2": ("acceleration", 1.0),
    "ft/s^2": ("acceleration", _FOOT_M),
    "g0": ("acceleration", _STD_GRAVITY),
    "rad/s": ("angular_speed", 1.0),
    "deg/s": ("angular_speed", math.pi / 180.0),
    "rpm": ("angular_speed", 2.0 * math.pi / 60.0),
    "J": ("energy", 1.0),
    "kJ": ("energy", 1_000.0),
    "MJ": ("energy", 1_000_000.0),
    "W": ("power", 1.0),
    "kW": ("power", 1_000.0),
    "MW": ("power", 1_000_000.0),
}

_TEMPERATURE = {"C", "F", "K", "R"}

# Whole words only. Lookup is case-insensitive. Values are symbol keys above.
_NAMES = {
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",
    "centimeter": "cm",
    "centimeters": "cm",
    "centimetre": "cm",
    "centimetres": "cm",
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "megameter": "Mm",
    "megameters": "Mm",
    "megametre": "Mm",
    "megametres": "Mm",
    "foot": "ft",
    "feet": "ft",
    "inch": "in",
    "inches": "in",
    "yard": "yd",
    "yards": "yd",
    "mile": "mi",
    "miles": "mi",
    "nauticalmile": "nmi",
    "nauticalmiles": "nmi",
    "astronomicalunit": "AU",
    "astronomicalunits": "AU",
    "second": "s",
    "seconds": "s",
    "millisecond": "ms",
    "milliseconds": "ms",
    "megasecond": "Ms",
    "megaseconds": "Ms",
    "microsecond": "us",
    "microseconds": "us",
    "nanosecond": "ns",
    "nanoseconds": "ns",
    "minute": "min",
    "minutes": "min",
    "hour": "h",
    "hours": "h",
    "day": "day",
    "days": "day",
    "knot": "kn",
    "knots": "kn",
    "kilogram": "kg",
    "kilograms": "kg",
    "gram": "g",
    "grams": "g",
    "milligram": "mg",
    "milligrams": "mg",
    "megagram": "Mg",
    "megagrams": "Mg",
    "pound": "lb",
    "pounds": "lb",
    "slug": "slug",
    "slugs": "slug",
    "newton": "N",
    "newtons": "N",
    "kilonewton": "kN",
    "kilonewtons": "kN",
    "millinewton": "mN",
    "millinewtons": "mN",
    "meganewton": "MN",
    "meganewtons": "MN",
    "pascal": "Pa",
    "pascals": "Pa",
    "kilopascal": "kPa",
    "kilopascals": "kPa",
    "megapascal": "MPa",
    "megapascals": "MPa",
    "gigapascal": "GPa",
    "gigapascals": "GPa",
    "millipascal": "mPa",
    "millipascals": "mPa",
    "atmosphere": "atm",
    "atmospheres": "atm",
    "degree": "deg",
    "degrees": "deg",
    "radian": "rad",
    "radians": "rad",
    "arcminute": "arcmin",
    "arcminutes": "arcmin",
    "arcsecond": "arcsec",
    "arcseconds": "arcsec",
    "celsius": "C",
    "fahrenheit": "F",
    "kelvin": "K",
    "rankine": "R",
    "degc": "C",
    "degf": "F",
    "degk": "K",
    "degr": "R",
    "joule": "J",
    "joules": "J",
    "kilojoule": "kJ",
    "kilojoules": "kJ",
    "megajoule": "MJ",
    "megajoules": "MJ",
    "watt": "W",
    "watts": "W",
    "kilowatt": "kW",
    "kilowatts": "kW",
    "megawatt": "MW",
    "megawatts": "MW",
}


class CalcError(Exception):
    """The expression or conversion was rejected."""


@dataclass(frozen=True)
class _Unit:
    token: str
    dimension: str
    factor: float


def calculate_request(
    expression: object = None,
    value: object = None,
    from_unit: object = None,
    to_unit: object = None,
) -> str:
    """Return input/result/units lines, or an error: line."""
    deadline = time.monotonic() + TIME_LIMIT_SEC
    try:
        return _request(expression, value, from_unit, to_unit, deadline)
    except CalcError as exc:
        return f"error: {exc}"
    except ZeroDivisionError:
        return "error: division by zero"
    except RecursionError:
        return "error: expression is too deep"


def _request(
    expression: object,
    value: object,
    from_unit: object,
    to_unit: object,
    deadline: float,
) -> str:
    _check_time(deadline)
    expr = _optional_text(expression, "expression")
    src_name = _optional_text(from_unit, "from_unit")
    dst_name = _optional_text(to_unit, "to_unit")
    has_value = value is not None and value != ""
    if (src_name is None) ^ (dst_name is None):
        raise CalcError("unit conversion needs from_unit and to_unit")
    if expr and has_value:
        raise CalcError("pass an expression or a value to convert, not both")
    if not expr and not has_value:
        raise CalcError("pass an expression or a value to convert")
    if has_value and src_name is None:
        raise CalcError("unit conversion needs from_unit and to_unit")

    if expr:
        number = evaluate(expr, deadline)
        shown = expr
    else:
        number = _parse_value(value)
        _real(number)
        shown = _format_number(number)

    units = "dimensionless"
    if src_name is not None and dst_name is not None:
        number = _convert(number, src_name, dst_name)
        shown = f"{shown} {src_name}"
        units = dst_name
    result = _format_number(number)
    if len(result) > MAX_DIGITS + 8:
        raise CalcError("result is too large")
    return f"input: {shown}\nresult: {result}\nunits: {units}"


def evaluate(expression: str, deadline: float) -> int | float:
    """Evaluate one expression. Raises CalcError. deadline is time.monotonic()."""
    _check_time(deadline)
    if not isinstance(expression, str):
        raise CalcError("expression must be text")
    text = expression.strip()
    if not text:
        raise CalcError("expression is empty")
    if "\n" in text or "\r" in text:
        raise CalcError("expression must be one line")
    if len(text) > MAX_EXPRESSION_CHARS:
        raise CalcError("expression is too long")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise CalcError("expression syntax is not allowed") from exc
    state = {"nodes": 0}
    return _eval(tree.body, deadline, state, 0)


def _eval(node: ast.AST, deadline: float, state: dict[str, int], depth: int) -> int | float:
    _check_time(deadline)
    state["nodes"] += 1
    if state["nodes"] > MAX_NODES:
        raise CalcError("expression is too long")
    if depth > MAX_DEPTH:
        raise CalcError("expression is too deep")
    if isinstance(node, ast.Constant):
        return _constant(node.value)
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise CalcError(f"name {node.id!r} is not allowed")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval(node.operand, deadline, state, depth + 1)
        if isinstance(node.op, ast.USub):
            value = -value
        return _real(value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, _BINOPS):
        left = _eval(node.left, deadline, state, depth + 1)
        right = _eval(node.right, deadline, state, depth + 1)
        return _apply_bin(node.op, left, right)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalcError("only named math functions are allowed")
        if node.func.id not in _FUNCTIONS:
            raise CalcError(f"name {node.func.id!r} is not allowed")
        if node.keywords:
            raise CalcError("keyword arguments are not allowed")
        args = [_eval(item, deadline, state, depth + 1) for item in node.args]
        return _call(node.func.id, args)
    raise CalcError("expression is not allowed")


def _constant(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalcError("only real numbers are allowed")
    return _real(value)


def _real(value: int | float) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalcError("result is not a real number")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CalcError("result is not finite")
        return value
    if value.bit_length() > MAX_BITS:
        raise CalcError("result is too large")
    return value


def _apply_bin(op: ast.operator, left: int | float, right: int | float) -> int | float:
    left = _real(left)
    right = _real(right)
    if isinstance(op, ast.Add):
        return _real(left + right)
    if isinstance(op, ast.Sub):
        return _real(left - right)
    if isinstance(op, ast.Mult):
        return _real(left * right)
    if isinstance(op, ast.Div):
        if right == 0:
            raise CalcError("division by zero")
        return _real(left / right)
    if isinstance(op, ast.Mod):
        if right == 0:
            raise CalcError("division by zero")
        return _real(left % right)
    if isinstance(op, ast.Pow):
        return _pow(left, right)
    raise CalcError("operator is not allowed")


def _pow(base: int | float, exp: int | float) -> int | float:
    base = _real(base)
    exp = _real(exp)
    if isinstance(exp, float):
        if abs(exp) > MAX_EXPONENT:
            raise CalcError("exponent is too large")
    elif abs(exp) > MAX_EXPONENT:
        raise CalcError("exponent is too large")
    if isinstance(base, int) and isinstance(exp, int) and exp > 0 and abs(base) > 1:
        digits = int(exp * math.log10(abs(base))) + 1
        if digits > MAX_DIGITS:
            raise CalcError("result is too large")
    try:
        result = base ** exp
    except OverflowError as exc:
        raise CalcError("result is too large") from exc
    except ZeroDivisionError as exc:
        raise CalcError("division by zero") from exc
    if isinstance(result, complex):
        raise CalcError("result is not a real number")
    return _real(result)


def _call(name: str, args: list[int | float]) -> int | float:
    spec = _FUNCTIONS.get(name)
    if spec is None:
        raise CalcError(f"name {name!r} is not allowed")
    fn, arity = spec
    allowed = arity if isinstance(arity, tuple) else (arity,)
    if len(args) not in allowed:
        count = " or ".join(str(item) for item in allowed)
        raise CalcError(f"{name} expects {count} arguments")
    try:
        result = fn(*args)
    except ValueError as exc:
        message = str(exc).strip() or "math domain error"
        raise CalcError(message) from exc
    except OverflowError as exc:
        raise CalcError("result is too large") from exc
    if isinstance(result, complex):
        raise CalcError("result is not a real number")
    return _real(result)


def _convert(value: int | float, from_unit: str, to_unit: str) -> int | float:
    src = _lookup(from_unit)
    dst = _lookup(to_unit)
    if src.dimension != dst.dimension:
        raise CalcError(f"cannot convert {from_unit} to {to_unit}")
    number = float(value)
    if not math.isfinite(number):
        raise CalcError("value is too large to convert")
    if src.dimension == "temperature":
        kelvin = _to_kelvin(number, src.token)
        # Snap float noise around absolute zero. A reading below that is refused.
        if kelvin < -1e-9:
            raise CalcError("temperature is below absolute zero")
        if kelvin < 0:
            kelvin = 0.0
        result = _from_kelvin(kelvin, dst.token)
    else:
        result = number * src.factor / dst.factor
    return _real(result)


def _lookup(unit: str) -> _Unit:
    token = _canonical(unit)
    if token in _TEMPERATURE:
        return _Unit(token, "temperature", 1.0)
    found = _SYMBOLS.get(token)
    if found is None:
        raise CalcError(f"unknown unit {unit!r}")
    dimension, factor = found
    return _Unit(token, dimension, factor)


def _canonical(unit: str) -> str:
    """Return the symbol key for unit. Raises CalcError if unknown or ambiguous."""
    return _resolve_symbol(_normalize(unit), unit)


def _normalize(unit: str) -> str:
    text = unit.strip().replace("°", "deg").replace("º", "deg").replace("μ", "u").replace("µ", "u")
    text = text.replace("_", "")
    text = re.sub(r"\s+per\s+", "/", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*/\s*", "/", text)
    return re.sub(r"\s+", "", text)


def _resolve_symbol(text: str, original: str) -> str:
    if text in _SYMBOLS or text in _TEMPERATURE:
        return text
    if text.isalpha():
        named = _NAMES.get(text.casefold())
        if named is not None:
            return named
    folded = text.casefold()
    matches = [symbol for symbol in (*_SYMBOLS, *_TEMPERATURE) if symbol.casefold() == folded]
    if len(matches) > 1:
        raise CalcError(f"ambiguous unit {original!r}")
    raise CalcError(f"unknown unit {original!r}")


def _to_kelvin(value: float, token: str) -> float:
    if token == "K":
        return value
    if token == "C":
        return value + 273.15
    if token == "F":
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    if token == "R":
        return value * 5.0 / 9.0
    raise CalcError(f"unknown unit {token!r}")


def _from_kelvin(value: float, token: str) -> float:
    if token == "K":
        return value
    if token == "C":
        return value - 273.15
    if token == "F":
        return (value - 273.15) * 9.0 / 5.0 + 32.0
    if token == "R":
        return value * 9.0 / 5.0
    raise CalcError(f"unknown unit {token!r}")


def _parse_value(value: object) -> int | float:
    if isinstance(value, bool) or value is None:
        raise CalcError("value must be a number")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CalcError("value must be finite")
        return value
    if isinstance(value, str):
        text = value.strip()
        try:
            if text and _is_int_text(text):
                return int(text)
            number = float(text)
        except ValueError as exc:
            raise CalcError("value must be a number") from exc
        if not math.isfinite(number):
            raise CalcError("value must be finite")
        return number
    raise CalcError("value must be a number")


def _is_int_text(text: str) -> bool:
    body = text[1:] if text[0] in "+-" else text
    return bool(body) and body.isdigit()


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CalcError(f"{label} must be text")
    stripped = value.strip()
    return stripped or None


def _format_number(value: int | float) -> str:
    number = _real(value)
    if isinstance(number, float) and number.is_integer() and abs(number) < 1e15:
        return str(int(number))
    if isinstance(number, int):
        return str(number)
    return format(number, ".12g")


def _check_time(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise CalcError("evaluation timed out")
