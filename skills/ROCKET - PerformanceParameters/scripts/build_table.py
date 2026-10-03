#!/usr/bin/env python3
"""Offline frozen-CEA table builder.

rocketcea is imported inside main() only. This script is not part of a user
request: if rocketcea is missing it exits without writing a file.
"""

from __future__ import annotations

import importlib.metadata
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SKILL_DIR / "src"
TABLE_DIR = SKILL_DIR / "table"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from load_table import COLUMNS, load_pairs  # noqa: E402

CASE = (
    "CEA rocket equilibrium chamber; both gammas stored; "
    "default expansion uses gamma_throat"
)
SOURCE = "rocketcea.cea_obj.CEA_Obj"
# rocketcea without cea_obj_w_units takes chamber pressure in psia.
PSIA_PER_BAR = 14.5037738
R_UNIV = 8314.462618  # J/(kmol·K)

UNITS = {
    "r": "ox/fuel",
    "Tc_K": "K",
    "cstar_m_s": "m/s",
    "Mw": "kg/kmol",
    "gamma_chamber": "1",
    "gamma_throat": "1",
    "cstar_perfect_m_s": "m/s",
    "cstar_rel_diff": "1",
}


def mixture_grid(of_min: float, of_max: float, of_step: float) -> list[float]:
    """Inclusive OF grid. The step count is an integer so of_max is included."""
    start = Decimal(str(of_min))
    end = Decimal(str(of_max))
    step = Decimal(str(of_step))
    if step <= 0:
        raise ValueError("of_step must be positive")
    if end < start:
        raise ValueError("of_max must be >= of_min")
    span = (end - start) / step
    n = int(span.to_integral_value(rounding=ROUND_HALF_UP))
    if abs(span - Decimal(n)) > Decimal("0.0000001"):
        raise ValueError(
            f"of_max {of_max} is not an integer number of steps {of_step} from of_min {of_min}"
        )
    values = [float(start + step * i) for i in range(n + 1)]
    values[-1] = float(end)
    return values


def cstar_perfect(gamma_c: float, mw: float, tc_k: float) -> float:
    """Chamber-gamma check. Delivered c* remains the CEA value.

    cstar_perfect_m_s = sqrt(gamma_c*R*Tc_K)/gamma_c
        * ((gamma_c+1)/2)**((gamma_c+1)/(2*(gamma_c-1)))
    """
    if mw <= 0 or tc_k <= 0 or gamma_c <= 1.0:
        raise ValueError("cstar_perfect inputs must have Mw > 0, Tc > 0, and gamma > 1")
    gas_r = R_UNIV / mw
    return (
        math.sqrt(gamma_c * gas_r * tc_k) / gamma_c
        * ((gamma_c + 1.0) / 2.0) ** ((gamma_c + 1.0) / (2.0 * (gamma_c - 1.0)))
    )


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is not finite")
    return number


def table_path(ox_name: str, fuel_name: str, pc_bar: float) -> Path:
    for label, text in (("oxName", ox_name), ("fuelName", fuel_name)):
        if not text or any(ch in text for ch in "\\/"):
            raise ValueError(f"{label} cannot be a path segment: {text!r}")
    return TABLE_DIR / f"{ox_name}_{fuel_name}_{pc_bar:g}bar.json"


def atomic_write(path: Path, payload: dict) -> None:
    """Write via a temp file in table/ then os.replace. Called only after a sweep."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def sweep_rows(cea, pc_bar: float, ratios: list[float]) -> list[list[float]]:
    """One pressure, every mixture ratio. Nothing is written here."""
    Pc = pc_bar * PSIA_PER_BAR
    rows: list[list[float]] = []
    for mr in ratios:
        tc_r = _finite(cea.get_Tcomb(Pc, mr), "Tc_R")
        tc_k = tc_r * 5.0 / 9.0
        cstar_fts = _finite(cea.get_Cstar(Pc, mr), "cstar_fts")
        cstar_m_s = cstar_fts * 0.3048
        mw, gamma_chamber = cea.get_Chamber_MolWt_gamma(Pc, mr, eps=1.0)
        # frozen=0 is this API's equilibrium flag, not a unit kwarg.
        # Mw_t is not a column; stored Mw is the chamber value.
        _mw_throat, gamma_throat = cea.get_Throat_MolWt_gamma(Pc, mr, eps=1.0, frozen=0)
        mw = _finite(mw, "Mw")
        gamma_chamber = _finite(gamma_chamber, "gamma_chamber")
        gamma_throat = _finite(gamma_throat, "gamma_throat")
        tc_k = _finite(tc_k, "Tc_K")
        cstar_m_s = _finite(cstar_m_s, "cstar_m_s")
        if cstar_m_s == 0.0:
            raise ValueError(f"CEA c* is zero at pc={pc_bar:g} bar, r={mr:g}")
        perfect = cstar_perfect(gamma_chamber, mw, tc_k)
        rel = (cstar_m_s - perfect) / cstar_m_s
        rows.append(
            [
                mr,
                tc_k,
                cstar_m_s,
                mw,
                gamma_chamber,
                gamma_throat,
                perfect,
                rel,
            ]
        )
    return rows


def main() -> int:
    try:
        from rocketcea.cea_obj import CEA_Obj
    except ImportError:
        print("pip install rocketcea")
        return 1
    try:
        version = importlib.metadata.version("rocketcea")
    except importlib.metadata.PackageNotFoundError:
        print("pip install rocketcea")
        return 1

    catalog = load_pairs()
    built_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for spec in catalog.pairs.values():
        # Native constructor only. No cea_obj_w_units and no unit kwargs.
        cea = CEA_Obj(oxName=spec.oxName, fuelName=spec.fuelName)
        ratios = mixture_grid(spec.of_min, spec.of_max, spec.of_step)
        for pc_bar in catalog.pc_bar:
            rows = sweep_rows(cea, pc_bar, ratios)
            payload = {
                "source": SOURCE,
                "rocketcea_version": version,
                "pair": spec.pair,
                "oxName": spec.oxName,
                "fuelName": spec.fuelName,
                "case": CASE,
                "pc_bar": pc_bar,
                "of_min": spec.of_min,
                "of_max": spec.of_max,
                "of_step": spec.of_step,
                "units": UNITS,
                "columns": list(COLUMNS),
                "built_utc": built_utc,
                "rows": rows,
            }
            dest = table_path(spec.oxName, spec.fuelName, pc_bar)
            atomic_write(dest, payload)
            print(f"wrote: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
