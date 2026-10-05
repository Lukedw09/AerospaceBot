#!/usr/bin/env python3
"""Load frozen CEA performance tables. No rocketcea, subprocess, or network."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

# src/../table and src/../scripts/pairs.json
SKILL_DIR = Path(__file__).resolve().parent.parent
TABLE_DIR = SKILL_DIR / "table"
PAIRS_PATH = SKILL_DIR / "scripts" / "pairs.json"

BUILD_HINT = "Run scripts/build_table.py"

# Bar exists only inside frozen tables. Pascals convert here, not with the
# builder's psia factor.
PA_PER_BAR = 1e5
OFFSET_WARN_BAR = 10.0

COLUMNS = [
    "r",
    "Tc_K",
    "cstar_m_s",
    "Mw",
    "gamma_chamber",
    "gamma_throat",
    "cstar_perfect_m_s",
    "cstar_rel_diff",
]

REQUIRED_KEYS = (
    "source",
    "rocketcea_version",
    "pair",
    "oxName",
    "fuelName",
    "case",
    "pc_bar",
    "of_min",
    "of_max",
    "of_step",
    "units",
    "columns",
    "built_utc",
    "rows",
)

_STRING_KEYS = (
    "source",
    "rocketcea_version",
    "pair",
    "oxName",
    "fuelName",
    "case",
    "built_utc",
)


class TableError(Exception):
    """A frozen table or pair record cannot be used."""


@dataclass(frozen=True)
class PairSpec:
    oxName: str
    fuelName: str
    pair: str
    of_min: float
    of_max: float
    of_step: float
    rho_ox_kg_m3: float
    rho_ox_T_K: float
    rho_fuel_kg_m3: float
    rho_fuel_T_K: float
    cea: bool = True


@dataclass(frozen=True)
class PairCatalog:
    pc_bar: tuple[float, ...]
    pairs: dict[str, PairSpec]


@dataclass(frozen=True)
class TablePick:
    table: dict
    offset_bar: float
    warning: str | None


_CACHE_SIG: tuple | None = None
_CACHE: dict[str, list[dict]] | None = None


def pc_bar_from_pa(pc_Pa: float) -> float:
    """Loader boundary: pc_bar = pc_Pa / 1e5."""
    return pc_Pa / PA_PER_BAR


def pc_pa_from_bar(pc_bar: float) -> float:
    """Loader boundary: pc_Pa = pc_bar * 1e5."""
    return pc_bar * PA_PER_BAR


# Common spellings of the card names stored in pairs.json and the frozen tables.
_CARDS = {
    "lox": "LOX",
    "n2o4": "N2O4",
    "nto": "N2O4",
    "rp1": "RP1",
    "ch4": "CH4",
    "lch4": "CH4",
    "lng": "CH4",
    "methane": "CH4",
    "lh2": "LH2",
    "ethanol": "Ethanol",
    "mmh": "MMH",
    "udmh": "UDMH",
    "n2h4": "N2H4",
    "hydrazine": "N2H4",
    "a50": "A50",
    "aerozine50": "A50",
    "az50": "A50",
    "methanol": "Methanol",
    "meoh": "Methanol",
    "propane": "Propane",
}


def _card_name(token: str) -> str:
    folded = token.strip().casefold()
    folded = folded.replace("–", "-").replace("—", "-").replace("_", "").replace(" ", "")
    if folded in _CARDS:
        return _CARDS[folded]
    hyphenless = folded.replace("-", "")
    if hyphenless in _CARDS:
        return _CARDS[hyphenless]
    return token.strip()


def canonical_pair(text: str) -> str:
    """oxName/fuelName. Spaces around the slash are removed. Known names fold to the card."""
    if "/" not in text:
        raise TableError(f"pair must be oxName/fuelName, got {text!r}")
    ox, fuel = text.split("/", 1)
    ox = _card_name(ox)
    fuel = _card_name(fuel)
    if not ox or not fuel or "/" in fuel:
        raise TableError(f"pair must be oxName/fuelName, got {text!r}")
    return f"{ox}/{fuel}"


def clear_table_cache() -> None:
    global _CACHE_SIG, _CACHE
    _CACHE_SIG = None
    _CACHE = None


def _hint(message: str) -> str:
    return f"{message} {BUILD_HINT}"


def _as_float(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TableError(_hint(f"{where} is not a number."))
    number = float(value)
    if not math.isfinite(number):
        raise TableError(_hint(f"{where} is not finite."))
    return number


def _as_text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TableError(_hint(f"{where} is missing."))
    return value


def load_pairs(path: Path | None = None) -> PairCatalog:
    """Read density constants and OF grids from scripts/pairs.json."""
    src = path or PAIRS_PATH
    if not src.is_file():
        raise TableError(f"missing {src.name} pair list at {src}")
    try:
        doc = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TableError(f"{src.name} is not valid JSON ({exc})") from exc
    if not isinstance(doc, dict):
        raise TableError(f"{src.name} must be an object")
    if "pc_bar" not in doc or "pairs" not in doc:
        raise TableError(f"{src.name} must contain pc_bar and pairs")
    raw_pc = doc["pc_bar"]
    raw_pairs = doc["pairs"]
    if not isinstance(raw_pc, list) or not raw_pc:
        raise TableError(f"{src.name} pc_bar must be a non-empty list")
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise TableError(f"{src.name} pairs must be a non-empty list")

    pressures: list[float] = []
    for i, item in enumerate(raw_pc):
        pc = _as_float(item, f"{src.name} pc_bar[{i}]")
        if pc <= 0:
            raise TableError(f"{src.name} pc_bar[{i}] must be > 0")
        if any(abs(pc - prev) <= 1e-9 for prev in pressures):
            raise TableError(f"{src.name} pc_bar contains a duplicate {pc:g}")
        pressures.append(pc)

    required = (
        "oxName",
        "fuelName",
        "of_min",
        "of_max",
        "of_step",
        "rho_ox_kg_m3",
        "rho_ox_T_K",
        "rho_fuel_kg_m3",
        "rho_fuel_T_K",
    )
    pairs: dict[str, PairSpec] = {}
    for i, row in enumerate(raw_pairs):
        if not isinstance(row, dict):
            raise TableError(f"{src.name} pairs[{i}] must be an object")
        missing = [key for key in required if key not in row]
        if missing:
            raise TableError(
                f"{src.name} pairs[{i}] is missing {', '.join(missing)}"
            )
        ox = row["oxName"]
        fuel = row["fuelName"]
        if not isinstance(ox, str) or not ox.strip():
            raise TableError(f"{src.name} pairs[{i}] oxName must be a card name")
        if not isinstance(fuel, str) or not fuel.strip():
            raise TableError(f"{src.name} pairs[{i}] fuelName must be a card name")
        ox = ox.strip()
        fuel = fuel.strip()
        pair = f"{ox}/{fuel}"
        if pair in pairs:
            raise TableError(f"{src.name} lists {pair} more than once")
        of_min = _as_float(row["of_min"], f"{pair} of_min")
        of_max = _as_float(row["of_max"], f"{pair} of_max")
        of_step = _as_float(row["of_step"], f"{pair} of_step")
        rho_ox = _as_float(row["rho_ox_kg_m3"], f"{pair} rho_ox_kg_m3")
        t_ox = _as_float(row["rho_ox_T_K"], f"{pair} rho_ox_T_K")
        rho_fuel = _as_float(row["rho_fuel_kg_m3"], f"{pair} rho_fuel_kg_m3")
        t_fuel = _as_float(row["rho_fuel_T_K"], f"{pair} rho_fuel_T_K")
        if of_step <= 0:
            raise TableError(f"{pair} of_step must be > 0")
        if of_max < of_min:
            raise TableError(f"{pair} of_max must be >= of_min")
        if rho_ox <= 0 or rho_fuel <= 0:
            raise TableError(f"{pair} densities must be > 0")
        cea = row.get("cea", True)
        if not isinstance(cea, bool):
            raise TableError(f"{pair} cea must be true or false")
        pairs[pair] = PairSpec(
            oxName=ox,
            fuelName=fuel,
            pair=pair,
            of_min=of_min,
            of_max=of_max,
            of_step=of_step,
            rho_ox_kg_m3=rho_ox,
            rho_ox_T_K=t_ox,
            rho_fuel_kg_m3=rho_fuel,
            rho_fuel_T_K=t_fuel,
            cea=cea,
        )
    return PairCatalog(pc_bar=tuple(pressures), pairs=pairs)


def pair_spec(pair: str, catalog: PairCatalog | None = None) -> PairSpec:
    """Density record for a pair. Missing pairs cannot supply bulk density."""
    key = canonical_pair(pair)
    book = catalog or load_pairs()
    spec = book.pairs.get(key)
    if spec is None:
        raise TableError(
            f"pair {key} is not listed in scripts/pairs.json; bulk density is unavailable"
        )
    return spec


def validate_table(doc: object, name: str) -> dict:
    """Fail closed when a frozen-table file does not match the builder contract."""
    if not isinstance(doc, dict):
        raise TableError(_hint(f"{name} is not a JSON object."))
    missing = [key for key in REQUIRED_KEYS if key not in doc]
    if missing:
        raise TableError(
            _hint(f"{name} is missing header keys: {', '.join(missing)}.")
        )
    for key in _STRING_KEYS:
        _as_text(doc[key], f"{name} {key}")
    if doc["units"] is None:
        raise TableError(_hint(f"{name} units is missing."))

    ox = doc["oxName"].strip()
    fuel = doc["fuelName"].strip()
    pair = doc["pair"].strip()
    if pair != f"{ox}/{fuel}":
        raise TableError(
            _hint(f"{name} pair {pair!r} does not match {ox}/{fuel}.")
        )

    columns = doc["columns"]
    if not isinstance(columns, list) or columns != COLUMNS:
        raise TableError(
            _hint(f"{name} columns do not match the frozen table.")
        )

    pc_bar = _as_float(doc["pc_bar"], f"{name} pc_bar")
    of_min = _as_float(doc["of_min"], f"{name} of_min")
    of_max = _as_float(doc["of_max"], f"{name} of_max")
    of_step = _as_float(doc["of_step"], f"{name} of_step")
    if pc_bar <= 0:
        raise TableError(_hint(f"{name} pc_bar must be > 0."))
    if of_step <= 0:
        raise TableError(_hint(f"{name} of_step must be > 0."))
    if of_max < of_min:
        raise TableError(_hint(f"{name} of_max must be >= of_min."))

    rows = doc["rows"]
    if not isinstance(rows, list) or not rows:
        raise TableError(_hint(f"{name} rows is missing."))

    r_index = columns.index("r")
    parsed: list[list[float]] = []
    previous: float | None = None
    for i, row in enumerate(rows):
        if not isinstance(row, list):
            raise TableError(_hint(f"{name} row {i} is not a list."))
        if len(row) != len(columns):
            raise TableError(
                _hint(
                    f"{name} row {i} has {len(row)} values; columns has {len(columns)}."
                )
            )
        numbers = [_as_float(cell, f"{name} row {i} column {columns[j]}") for j, cell in enumerate(row)]
        r_value = numbers[r_index]
        if previous is not None and not r_value > previous:
            raise TableError(
                _hint(f"{name} mixture-ratio column is not strictly increasing.")
            )
        previous = r_value
        parsed.append(numbers)

    if abs(parsed[0][r_index] - of_min) > 1e-6 or abs(parsed[-1][r_index] - of_max) > 1e-6:
        raise TableError(
            _hint(f"{name} of_min/of_max do not match the stored mixture-ratio rows.")
        )

    return {
        "source": doc["source"],
        "rocketcea_version": doc["rocketcea_version"],
        "pair": pair,
        "oxName": ox,
        "fuelName": fuel,
        "case": doc["case"],
        "pc_bar": pc_bar,
        "of_min": of_min,
        "of_max": of_max,
        "of_step": of_step,
        "units": doc["units"],
        "columns": list(columns),
        "built_utc": doc["built_utc"],
        "rows": parsed,
        "path": name,
    }


def load_table_file(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TableError(_hint(f"{path.name} is not valid JSON ({exc}).")) from exc
    return validate_table(doc, path.name)


def _directory_signature() -> tuple:
    if not TABLE_DIR.is_dir():
        return ("missing", str(TABLE_DIR))
    files = []
    for path in sorted(TABLE_DIR.glob("*.json")):
        stat = path.stat()
        stamp = getattr(stat, "st_mtime_ns", stat.st_mtime)
        files.append((path.name, stat.st_size, stamp))
    return (str(TABLE_DIR), tuple(files))


def _reject_duplicate_pressures(pair: str, tables: list[dict]) -> None:
    seen: list[tuple[float, str]] = []
    for table in tables:
        pc = table["pc_bar"]
        for prev, prev_name in seen:
            if abs(pc - prev) <= 1e-6:
                raise TableError(
                    _hint(
                        f"multiple frozen tables for {pair} at {pc:g} bar "
                        f"({prev_name} and {table['path']})."
                    )
                )
        seen.append((pc, table["path"]))


def all_tables() -> dict[str, list[dict]]:
    """Valid frozen tables grouped by pair id. Invalid JSON fails closed."""
    global _CACHE_SIG, _CACHE
    signature = _directory_signature()
    if _CACHE is not None and _CACHE_SIG == signature:
        return _CACHE
    grouped: dict[str, list[dict]] = {}
    if TABLE_DIR.is_dir():
        for path in sorted(TABLE_DIR.glob("*.json")):
            table = load_table_file(path)
            grouped.setdefault(table["pair"], []).append(table)
    for pair, tables in grouped.items():
        _reject_duplicate_pressures(pair, tables)
    _CACHE = grouped
    _CACHE_SIG = signature
    return grouped


def tables_for_pair(pair: str) -> list[dict]:
    return list(all_tables().get(canonical_pair(pair), []))


def select_pc_bar(requested: float, available: list[float]) -> float:
    """Nearest table pressure. An exact distance tie uses the higher pressure.

    15 bar among 10/20/40 selects 20. 30 bar among 10/20/40 selects 40.
    """
    if not available:
        raise TableError(_hint("no frozen pressures are available."))
    best = available[0]
    for pc in available[1:]:
        dist = abs(pc - requested)
        best_dist = abs(best - requested)
        nearer = dist < best_dist - 1e-9
        tie_higher = abs(dist - best_dist) <= 1e-9 and pc > best
        if nearer or tie_higher:
            best = pc
    return best


def pressure_warning(requested_bar: float, table_bar: float, pair: str) -> str | None:
    offset = requested_bar - table_bar
    if abs(offset) > OFFSET_WARN_BAR:
        return (
            f"requested chamber pressure is {offset:+.6g} bar from the nearest "
            f"frozen table ({table_bar:g} bar) for {pair}. The offset is larger "
            f"than {OFFSET_WARN_BAR:g} bar. {BUILD_HINT} to add a closer pressure."
        )
    return None


def pick_table(pair: str, pc_bar: float) -> TablePick:
    """Choose the nearest valid file for this pair. Offset is requested minus table."""
    key = canonical_pair(pair)
    tables = tables_for_pair(key)
    if not tables:
        raise TableError(_hint(f"no frozen table for {key}."))
    chosen = select_pc_bar(pc_bar, [table["pc_bar"] for table in tables])
    table = next(item for item in tables if abs(item["pc_bar"] - chosen) <= 1e-6)
    offset = pc_bar - table["pc_bar"]
    return TablePick(
        table=table,
        offset_bar=offset,
        warning=pressure_warning(pc_bar, table["pc_bar"], key),
    )


def interpolate_row(table: dict, r: float) -> dict[str, float]:
    """Linear interpolation on mixture ratio. Values outside the stored rows error."""
    columns: list[str] = table["columns"]
    rows: list[list[float]] = table["rows"]
    r_index = columns.index("r")
    xs = [row[r_index] for row in rows]
    pair = table.get("pair", "table")
    tol = 1e-9 * max(1.0, abs(r))
    if r < xs[0] - tol or r > xs[-1] + tol:
        raise TableError(
            f"mixture ratio {r:g} is outside {pair} frozen rows "
            f"{xs[0]:g} to {xs[-1]:g}; not extrapolating"
        )
    if r < xs[0]:
        r = xs[0]
    if r > xs[-1]:
        r = xs[-1]

    for i, x_value in enumerate(xs):
        if abs(x_value - r) <= tol:
            return {column: rows[i][j] for j, column in enumerate(columns)}

    hi = 0
    while hi < len(xs) and xs[hi] < r:
        hi += 1
    lo = hi - 1
    span = xs[hi] - xs[lo]
    t = (r - xs[lo]) / span
    out: dict[str, float] = {}
    for j, column in enumerate(columns):
        if column == "r":
            out[column] = r
        else:
            out[column] = rows[lo][j] + t * (rows[hi][j] - rows[lo][j])
    return out
