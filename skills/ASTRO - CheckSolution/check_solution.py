#!/usr/bin/env python3
"""PROTOTYPE homework checker for the rocket equation and two-impulse Hohmann transfers.

Correctness is deterministic: dimensional analysis, symbolic equivalence with
numeric spot checks, and numeric tolerances. An undecidable line is
"can't verify". The final number is compared with vacuum_propellant_mass or
hohmann_transfer. Hint mode names the line and the error type only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pint
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
)

G0_FALLBACK = 9.80665
REL_CORRECT = 1e-4
REL_APPROX = 1e-2
ABS_TOL = 1e-6
SAMPLE_SEED = 0
SAMPLE_COUNT = 8
UNLOCATED = (
    "Final answer doesn't match. Likely a setup or formula error. "
    "Couldn't locate the line."
)

FAMILIES = ("rocket_equation", "hohmann")
MODES = ("hint",)
# One literal tuple so the catalog can list every allowed target on the tool schema.
TARGETS = (
    "delta_v",
    "mass_ratio",
    "mass_ratio_final_over_initial",
    "propellant_mass",
    "exhaust_speed",
    "specific_impulse",
    "circular_speed_depart",
    "circular_speed_arrive",
    "transfer_speed_depart",
    "transfer_speed_arrive",
    "dv1",
    "dv2",
    "dv_total",
    "time_of_flight",
)
ROCKET_TARGETS = TARGETS[:6]
HOHMANN_TARGETS = TARGETS[6:]

CLAIM_SYMBOLS = {
    "delta_v": ("dv", "answer"),
    "mass_ratio": ("mr", "answer"),
    "mass_ratio_final_over_initial": ("mr", "answer"),
    "propellant_mass": ("mp", "answer"),
    "exhaust_speed": ("ve", "answer"),
    "specific_impulse": ("isp", "answer"),
    "circular_speed_depart": ("vc1", "answer"),
    "circular_speed_arrive": ("vc2", "answer"),
    "transfer_speed_depart": ("vt1", "answer"),
    "transfer_speed_arrive": ("vt2", "answer"),
    "dv1": ("dv1", "answer"),
    "dv2": ("dv2", "answer"),
    "dv_total": ("dv", "answer"),
    "time_of_flight": ("tof", "answer"),
}

TARGET_UNIT = {
    "delta_v": "m/s",
    "mass_ratio": "1",
    "mass_ratio_final_over_initial": "1",
    "propellant_mass": "kg",
    "exhaust_speed": "m/s",
    "specific_impulse": "s",
    "circular_speed_depart": "m/s",
    "circular_speed_arrive": "m/s",
    "transfer_speed_depart": "m/s",
    "transfer_speed_arrive": "m/s",
    "dv1": "m/s",
    "dv2": "m/s",
    "dv_total": "m/s",
    "time_of_flight": "s",
}

UNIT_SPECS = (
    "m/s**2",
    "m/s2",
    "km/s",
    "m/s",
    "kg",
    "km",
    "m",
    "s",
    "N",
    "dimensionless",
)
UNIT_TO_PINT = {
    "m/s**2": "meter / second ** 2",
    "m/s2": "meter / second ** 2",
    "km/s": "kilometer / second",
    "m/s": "meter / second",
    "kg": "kilogram",
    "km": "kilometer",
    "m": "meter",
    "s": "second",
    "N": "newton",
    "dimensionless": "dimensionless",
    "1": "dimensionless",
}

ROCKET_ALIASES = {
    "m0": "m0",
    "mwet": "m0",
    "minitial": "m0",
    "mi": "m0",
    "mf": "mf",
    "mfinal": "mf",
    "mp": "mp",
    "mprop": "mp",
    "mpropellant": "mp",
    "dry": "dry",
    "mdry": "dry",
    "ve": "ve",
    "vex": "ve",
    "c": "ve",
    "isp": "isp",
    "dv": "dv",
    "deltav": "dv",
    "g0": "g0",
    "g": "g0",
    "growth": "growth",
    "mr": "mr",
    "massratio": "mr",
    "answer": "answer",
    "ans": "answer",
    "result": "answer",
}
HOHMANN_ALIASES = {
    "r1": "r1",
    "rdepart": "r1",
    "r2": "r2",
    "rarrive": "r2",
    "h1": "h1",
    "hdepart": "h1",
    "h2": "h2",
    "harrive": "h2",
    "alt": "alt",
    "r0": "R0",
    "rearth": "R0",
    "re": "R0",
    "mu": "mu",
    "g0": "g0",
    "g": "g0",
    "a": "a",
    "ecc": "ecc",
    "eccentricity": "ecc",
    "e": "ecc",
    "vc1": "vc1",
    "vcirc1": "vc1",
    "vcircular1": "vc1",
    "vc2": "vc2",
    "vcirc2": "vc2",
    "vcircular2": "vc2",
    "vt1": "vt1",
    "vtrans1": "vt1",
    "vtransfer1": "vt1",
    "vt2": "vt2",
    "vtrans2": "vt2",
    "vtransfer2": "vt2",
    "dv1": "dv1",
    "deltav1": "dv1",
    "dv2": "dv2",
    "deltav2": "dv2",
    "dv": "dv",
    "deltav": "dv",
    "dvtot": "dv",
    "dvtotal": "dv",
    "tof": "tof",
    "timeofflight": "tof",
    "period": "period",
    "answer": "answer",
    "ans": "answer",
    "result": "answer",
}
PROTECTED_TOKENS = {"log", "exp", "sqrt", "sin", "cos", "abs", "pi"}

SKILL_DIR = Path(__file__).resolve().parent
SKILLS = SKILL_DIR.parent
# Multiplication is inserted explicitly. SymPy's implicit-multiplication
# transform would split a name such as "gap" into single-letter symbols.
TRANSFORMS = standard_transformations
UREG = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)

_MODULES: dict[str, object] = {}
_SYMS: dict[str, sp.Symbol] = {}
_ROCKET_CANON: dict[str, list[sp.Expr]] = {}
_HOHMANN_CANON: dict[str, list[sp.Expr]] = {}
_SAMPLES: list[dict[str, float]] | None = None


def S(name: str) -> sp.Symbol:
    return _SYMS[name]


def _pint(spec: str) -> pint.Unit:
    return UREG.Unit(UNIT_TO_PINT[spec])


def _build_symbols() -> None:
    if _SYMS:
        return
    positive = {
        "m0", "mf", "mp", "dry", "ve", "isp", "dv", "g0", "r1", "r2", "R0",
        "mu", "a", "vc1", "vc2", "vt1", "vt2", "dv1", "dv2", "tof", "period",
    }
    for name in (
        *positive,
        "growth", "mr", "h1", "h2", "alt", "ecc", "answer",
    ):
        if name in positive:
            _SYMS[name] = sp.Symbol(name, positive=True)
        else:
            _SYMS[name] = sp.Symbol(name, real=True, nonnegative=True)
    _build_canon()


def _build_canon() -> None:
    m0, mf, mp = S("m0"), S("mf"), S("mp")
    ve, dv, isp, g0 = S("ve"), S("dv"), S("isp"), S("g0")
    dry, growth = S("dry"), S("growth")
    _ROCKET_CANON.update(
        {
            "dv": [
                ve * sp.log(m0 / mf),
                ve * sp.log(m0) - ve * sp.log(mf),
                -ve * sp.log(mf / m0),
                ve * sp.log((mf + mp) / mf),
                ve * sp.log(m0 / (m0 - mp)),
            ],
            "mp": [
                m0 - mf,
                mf * (sp.exp(dv / ve) - 1),
                m0 * (1 - sp.exp(-dv / ve)),
            ],
            "m0": [mf + mp, mf * sp.exp(dv / ve)],
            "mf": [m0 - mp, m0 * sp.exp(-dv / ve), dry * (1 + growth)],
            "ve": [isp * g0, dv / sp.log(m0 / mf)],
            "isp": [ve / g0],
        }
    )
    r1, r2, mu, R0 = S("r1"), S("r2"), S("mu"), S("R0")
    a = S("a")
    vc1, vc2, vt1, vt2 = S("vc1"), S("vc2"), S("vt1"), S("vt2")
    dv1, dv2 = S("dv1"), S("dv2")
    h1, h2, alt, ecc = S("h1"), S("h2"), S("alt"), S("ecc")
    period = S("period")
    _HOHMANN_CANON.update(
        {
            "mu": [g0 * R0**2],
            "r1": [R0 + h1, R0 + alt],
            "r2": [R0 + h2, r1 * (1 + ecc) / (1 - ecc)],
            "vc1": [sp.sqrt(mu / r1), R0 * sp.sqrt(g0 / r1)],
            "vc2": [sp.sqrt(mu / r2), R0 * sp.sqrt(g0 / r2)],
            "a": [(r1 + r2) / 2],
            "vt1": [sp.sqrt(mu * (2 / r1 - 1 / a))],
            "vt2": [sp.sqrt(mu * (2 / r2 - 1 / a))],
            "dv1": [sp.Abs(vt1 - vc1)],
            "dv2": [sp.Abs(vt2 - vc2)],
            "dv": [dv1 + dv2],
            "period": [2 * sp.pi * sp.sqrt(a**3 / mu)],
            "tof": [sp.pi * sp.sqrt(a**3 / mu), period / 2],
            "ecc": [sp.Abs(r2 - r1) / (r1 + r2)],
        }
    )


def canon_for(family: str) -> dict[str, list[sp.Expr]]:
    _build_symbols()
    if family == "rocket_equation":
        return _ROCKET_CANON
    return _HOHMANN_CANON


def load_module(folder: str, filename: str, mod_name: str):
    if mod_name in _MODULES:
        return _MODULES[mod_name]
    path = SKILLS / folder / filename
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    _MODULES[mod_name] = module
    return module


def vacuum_module():
    return load_module(
        "ASTRO - VacuumPropellantMass",
        "vacuum_propellant_mass.py",
        "astraeus_vacuum_propellant_mass",
    )


def hohmann_module():
    return load_module(
        "ASTRO - HohmannTransfer",
        "hohmann_transfer.py",
        "astraeus_hohmann_transfer",
    )


def numeric_class(got: float, ref: float) -> str:
    if not math.isfinite(got) or not math.isfinite(ref):
        return "far"
    scale = max(abs(ref), ABS_TOL)
    if abs(got - ref) <= ABS_TOL or abs(got - ref) / scale <= REL_CORRECT:
        return "correct"
    if abs(got + ref) <= ABS_TOL or abs(got + ref) / scale <= REL_CORRECT:
        return "sign"
    if abs(got - ref) / scale <= REL_APPROX:
        return "approximation"
    return "far"


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)


def print_kv(rows: list[tuple[str, object]]) -> None:
    for key, value in rows:
        print(f"{key}: {fmt(value)}")


class InputError(Exception):
    def __init__(self, message: str, missing: bool = False) -> None:
        super().__init__(message)
        self.missing = missing


@dataclass
class Reference:
    status: str
    note: str
    value: float | None
    unit: str
    tool: str
    prebind: dict[str, float]
    locked: set[str]
    echo: list[tuple[str, object]] = field(default_factory=list)


def _finite(name: str, value: float | None, *, positive: bool = False, nonnegative: bool = False) -> None:
    if value is None:
        return
    if not math.isfinite(value):
        raise InputError(f"{name} must be finite")
    if positive and value <= 0.0:
        raise InputError(f"{name} must be positive")
    if nonnegative and value < 0.0:
        raise InputError(f"{name} must be >= 0")


def solve_rocket(raw: dict[str, float | None]) -> Reference:
    vac = vacuum_module()
    g0 = float(vac.G0)
    for name in ("m0", "mf", "mp", "dry", "ve", "isp"):
        _finite(name, raw.get(name), positive=True)
    _finite("dv", raw.get("dv"), nonnegative=True)
    _finite("growth", raw.get("growth"), nonnegative=True)

    isp = raw.get("isp")
    ve = raw.get("ve")
    note_bits: list[str] = []
    if isp is not None and ve is not None:
        from_isp = vac.exhaust_speed(isp, None)
        if numeric_class(ve, from_isp) != "correct":
            return Reference(
                "inconsistent",
                "isp and ve disagree beyond the correct tolerance; reference not computed",
                None,
                TARGET_UNIT["exhaust_speed"],
                "vacuum_propellant_mass",
                _rocket_prebind(raw, g0, ve, isp),
                _rocket_locked(raw),
            )
        ve = vac.exhaust_speed(None, ve)
    elif isp is not None:
        ve = vac.exhaust_speed(isp, None)
    elif ve is not None:
        ve = vac.exhaust_speed(None, ve)

    dry = raw.get("dry")
    growth = raw.get("growth")
    mf = raw.get("mf")
    m0 = raw.get("m0")
    mp = raw.get("mp")
    dv = raw.get("dv")
    growth_used = growth
    if dry is not None and growth_used is None:
        growth_used = 0.0
        note_bits.append(
            "growth omitted with dry mass; vacuum_propellant_mass default growth 0 is used"
        )
    if dry is None and growth not in (None, 0.0):
        raise InputError("growth requires dry mass")
    if dry is not None:
        mf_from_dry = dry * (1.0 + float(growth_used))
        if mf is not None and numeric_class(mf, mf_from_dry) != "correct":
            return Reference(
                "inconsistent",
                "mf does not equal dry*(1+growth); reference not computed",
                None,
                "kg",
                "vacuum_propellant_mass",
                _rocket_prebind(raw, g0, ve, isp, mf=mf),
                _rocket_locked(raw),
                [("growth_used", growth_used)],
            )
        mf = mf_from_dry

    def masses_conflict() -> bool:
        if m0 is None or mf is None or mp is None:
            return False
        return numeric_class(m0, mf + mp) != "correct"

    if masses_conflict():
        return Reference(
            "inconsistent",
            "m0, mf, and mp are inconsistent; reference not computed",
            None,
            "kg",
            "vacuum_propellant_mass",
            _rocket_prebind(raw, g0, ve, isp, mf=mf),
            _rocket_locked(raw),
        )
    if m0 is None and mf is not None and mp is not None:
        m0 = mf + mp
    if mf is None and m0 is not None and mp is not None:
        mf = m0 - mp
    if mp is None and m0 is not None and mf is not None:
        mp = m0 - mf

    guard = 0
    while guard < 6:
        guard += 1
        changed = False
        if dv is None and ve is not None and m0 is not None and mf is not None:
            if mf <= 0.0 or m0 <= 0.0 or m0 + ABS_TOL < mf:
                raise InputError("masses must be positive and m0 >= mf")
            dv = 0.0 if abs(m0 - mf) <= ABS_TOL else ve * math.log(m0 / mf)
            changed = True
        if ve is None and dv is not None and m0 is not None and mf is not None and m0 > mf:
            ve = dv / math.log(m0 / mf)
            changed = True
        if mf is None and m0 is not None and dv is not None and ve is not None:
            mf = m0 * math.exp(-dv / ve)
            changed = True
        if m0 is None and mf is not None and dv is not None and ve is not None:
            _final, prop, wet = vac.propellant_mass(mf, 0.0, dv, ve)
            m0, mp = wet, prop
            changed = True
        if mp is None and m0 is not None and mf is not None:
            mp = m0 - mf
            changed = True
        if not changed:
            break

    tool_called = False
    if mf is not None and dv is not None and ve is not None:
        if dry is not None:
            final, prop, wet = vac.propellant_mass(dry, float(growth_used), dv, ve)
        else:
            final, prop, wet = vac.propellant_mass(mf, 0.0, dv, ve)
        tool_called = True
        if m0 is not None and numeric_class(wet, m0) != "correct":
            return Reference(
                "inconsistent",
                "masses do not satisfy vacuum_propellant_mass at this exhaust speed",
                None,
                "kg",
                "vacuum_propellant_mass",
                _rocket_prebind(raw, g0, ve, isp, mf=raw.get("mf")),
                _rocket_locked(raw),
            )
        if mp is not None and numeric_class(prop, mp) != "correct" and raw.get("mp") is not None:
            return Reference(
                "inconsistent",
                "propellant does not satisfy vacuum_propellant_mass",
                None,
                "kg",
                "vacuum_propellant_mass",
                _rocket_prebind(raw, g0, ve, isp, mf=raw.get("mf")),
                _rocket_locked(raw),
            )
        m0, mf, mp = wet, final, prop
        dv = 0.0 if abs(wet - final) <= ABS_TOL else ve * math.log(wet / final)

    values = {
        "m0": m0,
        "mf": mf,
        "mp": mp,
        "ve": ve,
        "dv": dv,
        "isp": (ve / g0) if ve is not None else isp,
        "g0": g0,
        "dry": dry,
        "growth": growth_used if dry is not None else growth,
    }
    prebind = {key: val for key, val in values.items() if val is not None and key in _rocket_locked(raw) | {"g0"}}
    # Derived mf from dry is a problem fact, so lock it when dry was given.
    if dry is not None and mf is not None:
        prebind["mf"] = mf
        prebind["growth"] = float(growth_used)
    if ve is not None and (raw.get("ve") is not None or raw.get("isp") is not None):
        prebind["ve"] = ve
    if isp is not None or (ve is not None and raw.get("isp") is not None):
        if raw.get("isp") is not None:
            prebind["isp"] = float(raw["isp"])
    locked = set(prebind)
    echo = [("g0_m_s2", g0), ("tool_called", "yes" if tool_called else "no")]
    if growth_used is not None and dry is not None:
        echo.append(("growth_used", float(growth_used)))
    note = " ".join(note_bits)
    return Reference("ok", note, None, "", "vacuum_propellant_mass", prebind, locked, echo)


def _rocket_locked(raw: dict[str, float | None]) -> set[str]:
    locked = {"g0"}
    for key in ("m0", "mf", "mp", "dry", "ve", "isp", "dv", "growth"):
        if raw.get(key) is not None:
            locked.add(key)
    return locked


def _rocket_prebind(
    raw: dict[str, float | None],
    g0: float,
    ve: float | None,
    isp: float | None,
    mf: float | None = None,
) -> dict[str, float]:
    pre: dict[str, float] = {"g0": g0}
    for key in ("m0", "mp", "dry", "dv", "growth"):
        if raw.get(key) is not None:
            pre[key] = float(raw[key])
    if raw.get("mf") is not None:
        pre["mf"] = float(raw["mf"])
    elif mf is not None:
        pre["mf"] = mf
    if raw.get("ve") is not None:
        pre["ve"] = float(raw["ve"])
    elif ve is not None and raw.get("isp") is not None:
        pre["ve"] = ve
    if raw.get("isp") is not None:
        pre["isp"] = float(raw["isp"])
    elif isp is not None:
        pre["isp"] = isp
    return pre


def rocket_target_value(ref_values: dict[str, float], target: str) -> float | None:
    m0 = ref_values.get("m0")
    mf = ref_values.get("mf")
    mp = ref_values.get("mp")
    ve = ref_values.get("ve")
    dv = ref_values.get("dv")
    isp = ref_values.get("isp")
    table = {
        "delta_v": dv,
        "mass_ratio": (m0 / mf) if m0 is not None and mf not in (None, 0.0) else None,
        "mass_ratio_final_over_initial": (mf / m0) if m0 not in (None, 0.0) and mf is not None else None,
        "propellant_mass": mp,
        "exhaust_speed": ve,
        "specific_impulse": isp if isp is not None else (ve / ref_values["g0"] if ve is not None else None),
    }
    return table[target]


def solve_hohmann(raw: dict[str, float | None]) -> tuple[Reference, dict[str, float]]:
    hoh = hohmann_module()
    for name in ("r1", "r2", "R0"):
        _finite(name, raw.get(name), positive=True)
    for name in ("h1", "h2", "alt"):
        _finite(name, raw.get(name), nonnegative=True)
    ecc = raw.get("ecc")
    if ecc is not None:
        _finite("ecc", ecc, nonnegative=True)
        if ecc >= 1.0:
            raise InputError("ecc must satisfy 0 <= ecc < 1")
    has_r = raw.get("r1") is not None or raw.get("r2") is not None
    has_h = raw.get("h1") is not None or raw.get("h2") is not None
    has_alt = raw.get("alt") is not None or raw.get("ecc") is not None
    selected = sum(1 for flag in (has_r, has_h, has_alt) if flag)
    body = hoh.resolve_body(raw.get("R0"))
    pre: dict[str, float] = {
        "g0": float(hoh.G0),
        "R0": float(body.radius),
        "mu": float(body.mu),
    }
    for key in ("r1", "r2", "h1", "h2", "alt", "ecc"):
        if raw.get(key) is not None:
            pre[key] = float(raw[key])
    locked = set(pre)
    details: dict[str, float] = {
        "g0": float(body.g0),
        "R0": float(body.radius),
        "mu": float(body.mu),
    }
    if selected == 0:
        return (
            Reference(
                "underdetermined",
                "need r1 and r2, or h1 and h2, or alt and ecc; reference not computed",
                None,
                "m/s",
                "hohmann_transfer",
                pre,
                locked,
                [("R0_m", body.radius), ("mu_m3_s2", body.mu)],
            ),
            details,
        )
    if selected > 1:
        raise InputError("pass one of: r1 and r2, or h1 and h2, or alt and ecc")
    try:
        if has_alt:
            if raw.get("alt") is None or raw.get("ecc") is None:
                raise InputError("alt and ecc are both required")
            r1, r2 = hoh.radii_from_altitude(body.radius, float(raw["alt"]), float(raw["ecc"]))
            mode = "altitude"
        elif has_h:
            if raw.get("h1") is None or raw.get("h2") is None:
                raise InputError("h1 and h2 are both required")
            r1 = body.radius + float(raw["h1"])
            r2 = body.radius + float(raw["h2"])
            mode = "altitudes"
        else:
            if raw.get("r1") is None or raw.get("r2") is None:
                raise InputError("r1 and r2 are both required")
            r1 = float(raw["r1"])
            r2 = float(raw["r2"])
            mode = "radii"
        transfer = hoh.solve_transfer(body.mu, r1, r2, mode)
        hoh.require_outside_body(transfer, body.radius)
    except ValueError as exc:
        raise InputError(str(exc)) from exc
    pre["r1"] = float(transfer.r_depart)
    pre["r2"] = float(transfer.r_arrive)
    locked.update({"r1", "r2", "g0", "R0"})
    details.update(
        {
            "r1": float(transfer.r_depart),
            "r2": float(transfer.r_arrive),
            "vc1": float(transfer.v_circular_depart),
            "vc2": float(transfer.v_circular_arrive),
            "vt1": float(transfer.v_depart_transfer),
            "vt2": float(transfer.v_arrive_transfer),
            "dv1": float(transfer.dv_depart),
            "dv2": float(transfer.dv_arrive),
            "dv": float(transfer.dv),
            "tof": float(transfer.tof),
            "a": float(transfer.a),
            "ecc": float(transfer.e),
            "period": float(transfer.period),
        }
    )
    ref = Reference(
        "ok",
        "",
        None,
        "",
        "hohmann_transfer",
        pre,
        locked,
        [
            ("R0_m", body.radius),
            ("R0_source", body.radius_source),
            ("mu_m3_s2", body.mu),
            ("r1_m", transfer.r_depart),
            ("r2_m", transfer.r_arrive),
            ("hohmann_mode", mode),
        ],
    )
    return ref, details


def hohmann_target_value(details: dict[str, float], target: str) -> float | None:
    table = {
        "circular_speed_depart": details.get("vc1"),
        "circular_speed_arrive": details.get("vc2"),
        "transfer_speed_depart": details.get("vt1"),
        "transfer_speed_arrive": details.get("vt2"),
        "dv1": details.get("dv1"),
        "dv2": details.get("dv2"),
        "dv_total": details.get("dv"),
        "time_of_flight": details.get("tof"),
    }
    return table.get(target)


# --- parsing -----------------------------------------------------------------


def _find_brace(text: str, open_at: int) -> int | None:
    depth = 0
    for index in range(open_at, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _replace_command(text: str, command: str, arity: int) -> str:
    while True:
        start = text.rfind(command)
        if start < 0:
            return text
        index = start + len(command)
        while index < len(text) and text[index].isspace():
            index += 1
        groups: list[str] = []
        cursor = index
        ok = True
        for _ in range(arity):
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if cursor >= len(text) or text[cursor] != "{":
                ok = False
                break
            end = _find_brace(text, cursor)
            if end is None:
                ok = False
                break
            groups.append(text[cursor + 1 : end])
            cursor = end + 1
        if not ok:
            text = text[:start] + text[start + len(command) :]
            continue
        if arity == 2:
            piece = f"(({groups[0]})/({groups[1]}))"
        else:
            inner = groups[0]
            if command in {r"\sqrt"}:
                piece = f"sqrt({inner})"
            else:
                piece = f" {inner} "
        text = text[:start] + piece + text[cursor:]
    return text


def latex_to_plain(text: str) -> str:
    s = text.strip()
    s = s.replace("$$", "").replace("$", "")
    s = s.replace(r"\(", " ").replace(r"\)", " ")
    s = s.replace(r"\[", " ").replace(r"\]", " ")
    for src, dst in (
        ("−", "-"),
        ("–", "-"),
        ("—", "-"),
        ("×", "*"),
        ("·", "*"),
        ("∙", "*"),
        ("≈", "="),
        ("≃", "="),
    ):
        s = s.replace(src, dst)
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = s.replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", "")
    s = s.replace(r"\quad", " ").replace(r"\qquad", " ")
    s = s.replace(r"\times", "*").replace(r"\cdot", "*")
    s = s.replace(r"\approx", "=").replace(r"\simeq", "=")
    s = s.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    s = _replace_command(s, r"\frac", 2)
    s = _replace_command(s, r"\sqrt", 1)
    s = _replace_command(s, r"\mathrm", 1)
    s = _replace_command(s, r"\text", 1)
    s = _replace_command(s, r"\operatorname", 1)
    s = s.replace(r"\Delta v", " dv ")
    s = s.replace(r"\Delta V", " dv ")
    s = s.replace(r"\Delta", " Delta ")
    s = s.replace(r"\ln", " ln ")
    s = s.replace(r"\log", " log ")
    s = s.replace(r"\exp", " exp ")
    s = s.replace(r"\sin", " sin ")
    s = s.replace(r"\cos", " cos ")
    s = s.replace(r"\mu", " mu ")
    s = s.replace(r"\pi", " pi ")
    s = s.replace("Δ", " Delta ")
    s = s.replace("μ", " mu ")
    s = s.replace("π", " pi ")
    s = re.sub(r"\bDelta\s*v\b", "dv", s)
    s = s.replace("²", "**2").replace("³", "**3")
    s = re.sub(
        r"([A-Za-z]+)_\{([^{}]+)\}",
        lambda match: match.group(1) + re.sub(r"[^A-Za-z0-9]", "", match.group(2)),
        s,
    )
    s = re.sub(r"([A-Za-z])_([A-Za-z0-9])", r"\1\2", s)
    s = re.sub(r"\^\{([^{}]+)\}", r"**(\1)", s)
    s = s.replace("^", "**")
    s = re.sub(r"\bDeltav\b", "dv", s)
    s = re.sub(r"\bln\b", "log", s)
    return s


def _match_paren(text: str, open_at: int) -> int | None:
    depth = 0
    for index in range(open_at, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _replace_e_pow(text: str) -> str:
    out: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("e**", index) or text.startswith("E**", index):
            cursor = index + 3
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if cursor < len(text) and text[cursor] == "(":
                end = _match_paren(text, cursor)
                if end is not None:
                    out.append(f"exp({text[cursor + 1 : end]})")
                    index = end + 1
                    continue
            match = re.match(r"[+-]?\d+(?:\.\d+)?", text[cursor:])
            if match:
                out.append(f"exp({match.group(0)})")
                index = cursor + match.end()
                continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _alias_tokens(text: str, family: str) -> str:
    aliases = ROCKET_ALIASES if family == "rocket_equation" else HOHMANN_ALIASES

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        lower = word.lower()
        if lower in PROTECTED_TOKENS:
            return "log" if lower == "log" else ("pi" if lower == "pi" else word if lower != "abs" else "Abs")
        if family == "rocket_equation" and lower == "e":
            return "exp(1)"
        mapped = aliases.get(lower)
        if mapped:
            return mapped
        return word

    return re.sub(r"[A-Za-z][A-Za-z0-9]*", repl, text)


def _insert_mul(text: str) -> str:
    s = re.sub(r"(\d(?:\.\d+)?)[eE]([+-]?\d+)", r"(\1*10**(\2))", text)
    s = re.sub(r"\b(log|exp|sqrt|sin|cos|Abs|abs)\s*\(", r"\1(", s)
    s = re.sub(r"(\d)\s*([A-Za-z(])", r"\1*\2", s)
    s = re.sub(r"(\))\s*(\()", r"\1*\2", s)
    s = re.sub(r"(\))\s*([A-Za-z])", r"\1*\2", s)
    s = re.sub(r"([A-Za-z])\s+\(", r"\1*(", s)
    s = re.sub(r"([A-Za-z0-9])\s+([A-Za-z])", r"\1*\2", s)
    return s


def _collapse_units(text: str) -> str:
    s = text
    s = re.sub(r"m\s*/\s*s\s*\*\*\s*\(?\s*2\s*\)?", "m/s**2", s)
    s = re.sub(r"m\s*/\s*s\s*\^\s*2", "m/s**2", s)
    s = re.sub(r"m\s*/\s*s2\b", "m/s2", s)
    s = re.sub(r"m\s*/\s*s\b", "m/s", s)
    s = re.sub(r"km\s*/\s*s\b", "km/s", s)
    s = s.replace("m/s2", "m/s**2")
    return s


_NUMBER_UNIT = re.compile(
    r"(?P<num>(?:\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\*10\*\*\([+-]?\d+\)\)))\s*"
    r"(?P<unit>m/s\*\*2|km/s|m/s|kg|km|m|s|N|dimensionless)\b"
)


@dataclass
class Parsed:
    expr: sp.Expr
    claimed: pint.Unit | None
    atoms: dict[str, float]
    atom_dims: dict[str, pint.Unit]
    source: str


def _peel_trailing_unit(text: str) -> tuple[str, str | None]:
    stripped = text.strip()
    for unit in UNIT_SPECS:
        token = "m/s**2" if unit == "m/s2" else unit
        if stripped == token:
            return "", token
        suffix = token
        if stripped.endswith(suffix):
            cut = len(stripped) - len(suffix)
            if cut > 0 and (stripped[cut - 1].isalnum() or stripped[cut - 1] == "_"):
                continue
            return stripped[:cut].strip(), token
    return stripped, None


def parse_math(text: str, family: str, local: dict[str, sp.Expr]) -> tuple[Parsed | None, str | None]:
    raw = latex_to_plain(text)
    if "\\" in raw:
        return None, "could not parse"
    raw = _collapse_units(raw)
    raw = _replace_e_pow(raw)
    atoms: dict[str, float] = {}
    atom_dims: dict[str, pint.Unit] = {}
    counter = 0

    def put_unit(match: re.Match[str]) -> str:
        nonlocal counter
        number = match.group("num")
        unit = match.group("unit")
        if number.startswith("("):
            magnitude = float(sp.N(parse_expr(number[1:-1], local_dict={"__builtins__": {}})))
        else:
            magnitude = float(number)
        name = f"U{counter}"
        counter += 1
        atoms[name] = magnitude
        atom_dims[name] = _pint(unit)
        local[name] = sp.Symbol(name, real=True)
        return name

    replaced = _NUMBER_UNIT.sub(put_unit, raw)
    body, trailing = _peel_trailing_unit(replaced)
    body = _alias_tokens(body, family)
    body = _insert_mul(body)
    body = body.strip()
    if not body:
        return None, "could not parse"
    if not re.fullmatch(r"[0-9A-Za-z+\-*/().,\s]+", body):
        return None, "could not parse"
    try:
        expr = parse_expr(body, local_dict=local, transformations=TRANSFORMS, evaluate=True)
    except Exception:
        return None, "could not parse"
    allowed = {sp.log, sp.exp, sp.sqrt, sp.sin, sp.cos, sp.Abs}
    for fn in expr.atoms(sp.Function):
        if fn.func not in allowed:
            return None, "could not parse"
    claimed = _pint(trailing) if trailing else None
    return Parsed(expr, claimed, atoms, atom_dims, body), None


def split_equals(text: str) -> list[str] | None:
    parts: list[str] = []
    depth_paren = 0
    depth_brace = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth_paren += 1
        elif char == ")":
            depth_paren -= 1
        elif char == "{":
            depth_brace += 1
        elif char == "}":
            depth_brace -= 1
        elif char == "=" and depth_paren == 0 and depth_brace == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    if any(not part for part in parts):
        return None
    return parts


def prepare_line(text: str) -> str | None:
    s = text.strip()
    if not s or s.startswith("#") or s.startswith("%") or s.startswith("//"):
        return None
    s = re.sub(r"\s+(#|%|//).*$", "", s).strip()
    s = re.sub(r"^(?:therefore|so|hence|thus|then|and)\b[\s,:-]*", "", s, flags=re.I)
    s = re.sub(r"^(?:step\s+)?\d+\s*[:.)-]\s*", "", s, flags=re.I)
    s = s.strip()
    return s or None


# --- dimensions and equivalence ----------------------------------------------


@dataclass
class Dim:
    kind: str  # ok, unknown, mismatch, tainted
    unit: pint.Unit | None = None


def _dimless() -> pint.Unit:
    return _pint("1")


def _same(left: pint.Unit | None, right: pint.Unit | None) -> bool:
    if left is None or right is None:
        return False
    return UREG.Quantity(1, left).dimensionality == UREG.Quantity(1, right).dimensionality


def _mul(left: pint.Unit, right: pint.Unit) -> pint.Unit:
    return (UREG.Quantity(1, left) * UREG.Quantity(1, right)).units


def _pow(unit: pint.Unit, exponent: float) -> pint.Unit:
    return (UREG.Quantity(1, unit) ** exponent).units


KNOWN_DIM = {
    "m0": "kg",
    "mf": "kg",
    "mp": "kg",
    "dry": "kg",
    "ve": "m/s",
    "dv": "m/s",
    "isp": "s",
    "g0": "m/s**2",
    "growth": "1",
    "mr": "1",
    "r1": "m",
    "r2": "m",
    "h1": "m",
    "h2": "m",
    "alt": "m",
    "R0": "m",
    "mu": "m**3/s**2",
    "a": "m",
    "ecc": "1",
    "vc1": "m/s",
    "vc2": "m/s",
    "vt1": "m/s",
    "vt2": "m/s",
    "dv1": "m/s",
    "dv2": "m/s",
    "tof": "s",
    "period": "s",
}


def symbol_dim(name: str, state_dims: dict[str, pint.Unit | None], atom_dims: dict[str, pint.Unit]) -> Dim:
    if name in atom_dims:
        return Dim("ok", atom_dims[name])
    if name in state_dims and state_dims[name] is not None:
        return Dim("ok", state_dims[name])
    if name in KNOWN_DIM:
        spec = KNOWN_DIM[name]
        if spec == "m**3/s**2":
            return Dim("ok", UREG.meter**3 / UREG.second**2)
        return Dim("ok", _pint(spec))
    return Dim("unknown")


def infer_dim(expr: sp.Expr, state_dims: dict[str, pint.Unit | None], atom_dims: dict[str, pint.Unit]) -> Dim:
    if expr.is_number:
        return Dim("ok", _dimless())
    if isinstance(expr, sp.Symbol):
        return symbol_dim(str(expr), state_dims, atom_dims)
    if expr.func is sp.Add:
        parts = [infer_dim(arg, state_dims, atom_dims) for arg in expr.args]
        if any(part.kind == "mismatch" for part in parts):
            return Dim("mismatch")
        tainted = any(part.kind == "tainted" for part in parts)
        known = [part for part in parts if part.kind == "ok"]
        if len(known) >= 2 and any(not _same(known[0].unit, part.unit) for part in known[1:]):
            return Dim("mismatch")
        if tainted:
            return Dim("tainted", known[0].unit if len(known) == len(parts) and known else None)
        if len(known) != len(parts) or not known:
            return Dim("unknown")
        return Dim("ok", known[0].unit)
    if expr.func is sp.Mul:
        unit = _dimless()
        tainted = False
        unknown = False
        for arg in expr.args:
            part = infer_dim(arg, state_dims, atom_dims)
            if part.kind == "mismatch":
                return Dim("mismatch")
            if part.kind == "tainted":
                tainted = True
            if part.kind != "ok" or part.unit is None:
                unknown = True
                continue
            unit = _mul(unit, part.unit)
        if tainted:
            return Dim("tainted")
        if unknown:
            return Dim("unknown")
        return Dim("ok", unit)
    if expr.func is sp.Pow:
        base = infer_dim(expr.args[0], state_dims, atom_dims)
        exponent = expr.args[1]
        if base.kind == "mismatch":
            return Dim("mismatch")
        if not exponent.is_number:
            exp_dim = infer_dim(exponent, state_dims, atom_dims)
            if exp_dim.kind == "mismatch":
                return Dim("mismatch")
            if exp_dim.kind != "ok" or not _same(exp_dim.unit, _dimless()):
                return Dim("tainted")
        if base.kind != "ok" or base.unit is None:
            return Dim("tainted" if base.kind == "tainted" else "unknown")
        try:
            power = float(exponent)
        except Exception:
            return Dim("unknown")
        try:
            return Dim("ok", _pow(base.unit, power))
        except Exception:
            return Dim("unknown")
    if expr.func in {sp.log, sp.exp}:
        arg = infer_dim(expr.args[0], state_dims, atom_dims)
        if arg.kind == "mismatch":
            return Dim("mismatch")
        if arg.kind == "tainted":
            return Dim("tainted")
        if arg.kind != "ok" or arg.unit is None:
            return Dim("unknown")
        if not _same(arg.unit, _dimless()):
            return Dim("tainted")
        return Dim("ok", _dimless())
    if expr.func is sp.Abs:
        return infer_dim(expr.args[0], state_dims, atom_dims)
    if expr.func in {sp.sin, sp.cos, sp.sqrt}:
        arg = infer_dim(expr.args[0], state_dims, atom_dims)
        if expr.func is sp.sqrt and arg.kind == "ok" and arg.unit is not None:
            try:
                return Dim("ok", _pow(arg.unit, 0.5))
            except Exception:
                return Dim("unknown")
        if arg.kind == "ok" and _same(arg.unit, _dimless()):
            return Dim("ok", _dimless())
        if arg.kind == "mismatch":
            return Dim("mismatch")
        if arg.kind == "tainted":
            return Dim("tainted")
        return Dim("unknown")
    return Dim("unknown")


def _sample_env(rng: random.Random) -> dict[str, float]:
    g0 = 9.80665
    R0 = 10 ** rng.uniform(6.2, 7.5)
    r_small = R0 * rng.uniform(1.01, 1.8)
    r_large = r_small * rng.uniform(1.2, 6.0)
    if rng.random() < 0.5:
        r1, r2 = r_small, r_large
    else:
        r1, r2 = r_large, r_small
    mu = g0 * R0**2
    a = 0.5 * (r1 + r2)
    vc1 = math.sqrt(mu / r1)
    vc2 = math.sqrt(mu / r2)
    vt1 = math.sqrt(mu * (2.0 / r1 - 1.0 / a))
    vt2 = math.sqrt(mu * (2.0 / r2 - 1.0 / a))
    dv1 = abs(vt1 - vc1)
    dv2 = abs(vt2 - vc2)
    mf = 10 ** rng.uniform(0.3, 3.0)
    ratio = rng.uniform(1.2, 8.0)
    m0 = mf * ratio
    mp = m0 - mf
    ve = rng.uniform(800.0, 4500.0)
    dv = ve * math.log(m0 / mf)
    isp = ve / g0
    growth = rng.uniform(0.0, 0.25)
    dry = mf / (1.0 + growth)
    return {
        "g0": g0,
        "R0": R0,
        "r1": r1,
        "r2": r2,
        "mu": mu,
        "a": a,
        "vc1": vc1,
        "vc2": vc2,
        "vt1": vt1,
        "vt2": vt2,
        "dv1": dv1,
        "dv2": dv2,
        "dv": dv,
        "tof": math.pi * math.sqrt(a**3 / mu),
        "period": 2.0 * math.pi * math.sqrt(a**3 / mu),
        "ecc": abs(r2 - r1) / (r1 + r2),
        "h1": r1 - R0,
        "h2": r2 - R0,
        "alt": r1 - R0,
        "m0": m0,
        "mf": mf,
        "mp": mp,
        "ve": ve,
        "isp": isp,
        "dry": dry,
        "growth": growth,
        "mr": m0 / mf,
        "answer": dv,
    }


def sample_envs() -> list[dict[str, float]]:
    global _SAMPLES
    if _SAMPLES is None:
        rng = random.Random(SAMPLE_SEED)
        _SAMPLES = [_sample_env(rng) for _ in range(SAMPLE_COUNT)]
    return _SAMPLES


def _subs_map(expr: sp.Expr, env: dict[str, float]) -> dict[sp.Symbol, float] | None:
    _build_symbols()
    needed = {sym.name for sym in expr.free_symbols}
    if not needed <= set(env):
        return None
    return {_SYMS[name]: env[name] for name in needed if name in _SYMS}


def symbolic_equal(left: sp.Expr, right: sp.Expr) -> bool:
    try:
        diff = sp.simplify(left - right)
    except Exception:
        return False
    return diff == 0


def spot_relation(left: sp.Expr, right: sp.Expr) -> str | None:
    agree = 0
    disagree = 0
    for env in sample_envs():
        subs = _subs_map(left - right, env)
        if subs is None:
            return None
        try:
            value = (left - right).evalf(subs=subs)
            number = float(value)
        except Exception:
            continue
        if not math.isfinite(number):
            continue
        scale = max(abs(float(left.evalf(subs=subs))), abs(float(right.evalf(subs=subs))), 1e-12)
        if abs(number) / scale <= 1e-6:
            agree += 1
        else:
            disagree += 1
    if agree >= 4 and disagree == 0:
        return "equal"
    if disagree >= 1 and agree == 0:
        return "different"
    return None


def try_num(expr: sp.Expr, values: dict[str, float], extra: dict[str, float] | None = None) -> float | None:
    env = dict(values)
    if extra:
        env.update(extra)
    subs: dict[sp.Expr, float] = {}
    for sym in expr.free_symbols:
        name = sym.name
        if name not in env:
            return None
        subs[sym] = env[name]
    try:
        value = expr.evalf(subs=subs) if subs else expr.evalf()
        number = float(value)
    except Exception:
        return None
    if not math.isfinite(number):
        return None
    return number


def is_pure_number(expr: sp.Expr, atoms: set[str]) -> bool:
    return {sym.name for sym in expr.free_symbols} <= atoms


def canon_numeric(symbol: str, forms: list[sp.Expr], values: dict[str, float]) -> tuple[float | None, str]:
    found: list[float] = []
    for form in forms:
        value = try_num(form, values)
        if value is not None:
            found.append(value)
    if not found:
        return None, "missing"
    first = found[0]
    if any(numeric_class(value, first) not in {"correct", "approximation"} for value in found[1:]):
        # Approximation between algebraically equivalent forms is still one value.
        if any(numeric_class(value, first) == "far" or numeric_class(value, first) == "sign" for value in found[1:]):
            return None, "inconsistent"
    return first, "ok"


# --- line judgements ---------------------------------------------------------


@dataclass
class Verdict:
    kind: str
    error_type: str | None = None
    note: str = ""


def V_correct(note: str = "follows from the previous lines") -> Verdict:
    return Verdict("correct", None, note)


def V_approx() -> Verdict:
    return Verdict(
        "approximation",
        None,
        f"within the stated approximation tolerance (relative {REL_APPROX})",
    )


def V_error(error_type: str, note: str) -> Verdict:
    return Verdict("error", error_type, note)


def V_cant(note: str) -> Verdict:
    return Verdict("can't verify", None, note)


def from_numeric(kind: str, *, formula: bool) -> Verdict:
    if kind == "correct":
        return V_correct()
    if kind == "approximation":
        return V_approx()
    if kind == "sign":
        return V_error("sign", "sign disagrees with the value implied by the previous lines")
    if formula:
        return V_error("wrong formula", "the relation does not match a checked formula for this quantity")
    return V_error("arithmetic", "the number does not match evaluation of this line")


def combine(verdicts: list[Verdict]) -> Verdict:
    order = ("units", "sign", "wrong formula", "algebra", "arithmetic")
    errors = [item for item in verdicts if item.kind == "error"]
    for error_type in order:
        for item in errors:
            if item.error_type == error_type:
                return item
    if errors:
        return errors[0]
    if any(item.kind == "can't verify" for item in verdicts):
        return next(item for item in verdicts if item.kind == "can't verify")
    if any(item.kind == "approximation" for item in verdicts):
        return next(item for item in verdicts if item.kind == "approximation")
    return V_correct()


@dataclass
class State:
    family: str
    values: dict[str, float]
    exprs: dict[str, sp.Expr]
    dims: dict[str, pint.Unit | None]
    locked: set[str]
    local: dict[str, sp.Expr]
    claims: list[tuple[int, str, float]] = field(default_factory=list)
    student_dims: dict[str, pint.Unit | None] = field(default_factory=dict)


def _base_local() -> dict[str, sp.Expr]:
    _build_symbols()
    local: dict[str, sp.Expr] = dict(_SYMS)
    local["log"] = sp.log
    local["exp"] = sp.exp
    local["sqrt"] = sp.sqrt
    local["sin"] = sp.sin
    local["cos"] = sp.cos
    local["Abs"] = sp.Abs
    local["pi"] = sp.pi
    return local


def unknown_names(expr: sp.Expr, state: State, atoms: set[str]) -> list[str]:
    known = set(_SYMS) | set(state.values) | set(state.exprs) | atoms | {"pi"}
    found = []
    for sym in expr.free_symbols:
        if sym.name not in known:
            found.append(sym.name)
    return found


def _parsed_dim(parsed: Parsed, state: State) -> Dim:
    dims = dict(state.dims)
    dims.update(state.student_dims)
    return infer_dim(parsed.expr, dims, parsed.atom_dims)


def _unit_problem(parsed: Parsed, state: State, symbol: str | None = None) -> str | None:
    inferred = _parsed_dim(parsed, state)
    if inferred.kind == "mismatch":
        return "mismatch"
    if parsed.claimed is not None and inferred.kind == "ok" and not _same(parsed.claimed, inferred.unit):
        return "mismatch"
    if symbol is not None:
        expected = state.dims.get(symbol)
        if expected is None and symbol in KNOWN_DIM:
            spec = KNOWN_DIM[symbol]
            expected = UREG.meter**3 / UREG.second**2 if spec == "m**3/s**2" else _pint(spec)
        if (
            expected is not None
            and inferred.kind == "ok"
            and inferred.unit is not None
            and not _same(expected, inferred.unit)
        ):
            return "mismatch"
        if parsed.claimed is not None and expected is not None and not _same(parsed.claimed, expected):
            return "mismatch"
    if inferred.kind == "tainted":
        return "tainted"
    return None


def judge_canon(symbol: str, parsed: Parsed, state: State, tainted: bool) -> Verdict:
    forms = canon_for(state.family).get(symbol, [])
    if not forms:
        return V_cant("could not decide")
    env = dict(state.values)
    env.update(parsed.atoms)
    got = try_num(parsed.expr, env)
    ref, status = canon_numeric(symbol, forms, state.values)
    if status == "inconsistent":
        return V_cant("could not decide")
    if got is not None and ref is not None:
        kind = numeric_class(got, ref)
        if tainted and kind not in {"correct", "approximation"}:
            return V_error("units", "dimensions are inconsistent")
        if kind == "far" and any(symbolic_equal(parsed.expr, form) for form in forms):
            return V_error("arithmetic", "the number does not match evaluation of this line")
        return from_numeric(kind, formula=True)
    for form in forms:
        if symbolic_equal(parsed.expr, form) or spot_relation(parsed.expr, form) == "equal":
            return V_correct()
    for form in forms:
        if symbolic_equal(parsed.expr, -form) or spot_relation(parsed.expr, -form) == "equal":
            if tainted:
                return V_error("units", "dimensions are inconsistent")
            return V_error("sign", "sign disagrees with the value implied by the previous lines")
    if tainted:
        return V_error("units", "dimensions are inconsistent")
    relations = [spot_relation(parsed.expr, form) for form in forms]
    if relations and all(item == "different" for item in relations):
        return V_error("wrong formula", "the relation does not match a checked formula for this quantity")
    return V_cant("could not decide")


def judge_definition(symbol: str, parsed: Parsed, state: State) -> Verdict:
    problem = _unit_problem(parsed, state, symbol if symbol != "answer" else None)
    if symbol == "answer":
        # Dimensional check against the target is applied by the caller via state.dims["answer"].
        problem = _unit_problem(parsed, state, "answer")
    if problem == "mismatch":
        return V_error("units", "dimensions are inconsistent")
    tainted = problem == "tainted"
    unknown = unknown_names(parsed.expr, state, set(parsed.atoms))
    if unknown:
        return V_cant("unknown symbol " + ", ".join(sorted(unknown)))
    env = dict(state.values)
    env.update(parsed.atoms)
    if symbol in state.values:
        got = try_num(parsed.expr, env)
        if got is None:
            stored = state.exprs.get(symbol)
            if stored is not None and symbolic_equal(parsed.expr, stored):
                return V_correct()
            return V_cant("could not decide")
        kind = numeric_class(got, state.values[symbol])
        if tainted and kind not in {"correct", "approximation"}:
            return V_error("units", "dimensions are inconsistent")
        if kind == "far":
            if is_pure_number(parsed.expr, set(parsed.atoms)):
                return V_error("arithmetic", "the number does not match evaluation of this line")
            if symbol in canon_for(state.family):
                return V_error("wrong formula", "the relation does not match a checked formula for this quantity")
            return V_error("algebra", "the two sides are not algebraically equivalent")
        return from_numeric(kind, formula=False)
    if symbol in canon_for(state.family):
        return judge_canon(symbol, parsed, state, tainted)
    if tainted:
        return V_error("units", "dimensions are inconsistent")
    return V_correct()


def judge_equal(left: Parsed, right: Parsed, state: State) -> Verdict:
    for parsed in (left, right):
        problem = _unit_problem(parsed, state)
        if problem == "mismatch":
            return V_error("units", "dimensions are inconsistent")
    left_dim = _parsed_dim(left, state)
    right_dim = _parsed_dim(right, state)
    if (
        left_dim.kind == "ok"
        and right_dim.kind == "ok"
        and not _same(left_dim.unit, right_dim.unit)
    ):
        return V_error("units", "dimensions are inconsistent")
    if left.claimed is not None and right.claimed is not None and not _same(left.claimed, right.claimed):
        return V_error("units", "dimensions are inconsistent")
    env = dict(state.values)
    env.update(left.atoms)
    env.update(right.atoms)
    unknown = unknown_names(left.expr, state, set(left.atoms)) + unknown_names(right.expr, state, set(right.atoms))
    if unknown:
        return V_cant("unknown symbol " + ", ".join(sorted(set(unknown))))
    lv = try_num(left.expr, env)
    rv = try_num(right.expr, env)
    tainted = _unit_problem(left, state) == "tainted" or _unit_problem(right, state) == "tainted"
    if lv is not None and rv is not None:
        kind = numeric_class(lv, rv)
        pure = is_pure_number(left.expr, set(left.atoms)) or is_pure_number(right.expr, set(right.atoms))
        if tainted and kind not in {"correct", "approximation"}:
            return V_error("units", "dimensions are inconsistent")
        if kind == "far":
            if pure:
                return V_error("arithmetic", "the number does not match evaluation of this line")
            return V_error("algebra", "the two sides are not algebraically equivalent")
        return from_numeric(kind, formula=False)
    if symbolic_equal(left.expr, right.expr) or spot_relation(left.expr, right.expr) == "equal":
        return V_correct()
    if symbolic_equal(left.expr, -right.expr) or spot_relation(left.expr, -right.expr) == "equal":
        return V_error("sign", "sign disagrees with the value implied by the previous lines")
    if spot_relation(left.expr, right.expr) == "different":
        if tainted:
            return V_error("units", "dimensions are inconsistent")
        return V_error("algebra", "the two sides are not algebraically equivalent")
    return V_cant("could not decide")


def bare_symbol(parsed: Parsed) -> str | None:
    expr = parsed.expr
    if isinstance(expr, sp.Symbol) and not expr.name.startswith("U"):
        return expr.name
    return None


def _store(state: State, symbol: str, parsed: Parsed, verdict: Verdict, line_no: int, claim_names: tuple[str, ...]) -> None:
    if verdict.kind == "can't verify" or verdict.error_type == "units":
        return
    env = dict(state.values)
    env.update(parsed.atoms)
    value = try_num(parsed.expr, env)
    if value is None and symbol in canon_for(state.family) and verdict.kind == "correct":
        ref, status = canon_numeric(symbol, canon_for(state.family)[symbol], state.values)
        if status == "ok":
            value = ref
    inferred = _parsed_dim(parsed, state)
    if inferred.kind == "ok":
        state.student_dims[symbol] = inferred.unit
    state.exprs[symbol] = parsed.expr
    if value is None:
        return
    if verdict.kind == "correct" and symbol in state.locked and symbol in state.values:
        # A restatement within the correct tolerance keeps the problem value.
        if numeric_class(value, state.values[symbol]) == "correct":
            value = state.values[symbol]
    state.values[symbol] = value
    if symbol in claim_names:
        state.claims.append((line_no, symbol, value))


def grade_line(
    text: str,
    state: State,
    line_no: int,
    claim_names: tuple[str, ...],
) -> Verdict:
    parts = split_equals(text)
    if not parts or len(parts) < 2:
        return V_cant("could not parse")
    parsed_parts: list[Parsed] = []
    # Use one local dict so unit-atom symbols stay visible inside the line.
    local = state.local
    for part in parts:
        parsed, reason = parse_math(part, state.family, local)
        if parsed is None:
            return V_cant(reason or "could not parse")
        parsed_parts.append(parsed)
    symbol = bare_symbol(parsed_parts[0])
    verdicts: list[Verdict] = []
    if symbol is not None and len(parsed_parts) >= 2:
        verdicts.append(judge_definition(symbol, parsed_parts[1], state))
        for left, right in zip(parsed_parts[1:], parsed_parts[2:]):
            verdicts.append(judge_equal(left, right, state))
        verdict = combine(verdicts)
        # Bind from the rightmost numeric claim when the chain states one,
        # otherwise from the defining expression.
        carrier = parsed_parts[-1]
        if try_num(carrier.expr, {**state.values, **carrier.atoms}) is None:
            carrier = parsed_parts[1]
        _store(state, symbol, carrier, verdict, line_no, claim_names)
        return verdict
    for left, right in zip(parsed_parts, parsed_parts[1:]):
        verdicts.append(judge_equal(left, right, state))
        name = bare_symbol(left) or bare_symbol(right)
        other = right if bare_symbol(left) else left
        if name is not None:
            _store(state, name, other, combine(verdicts), line_no, claim_names)
    if not verdicts:
        return V_cant("could not parse")
    return combine(verdicts)


# --- driver ------------------------------------------------------------------


def _family_givens(raw: dict[str, float | None], family: str) -> None:
    rocket_keys = {"m0", "mf", "mp", "dry", "ve", "isp", "dv", "growth"}
    hohmann_keys = {"r1", "r2", "h1", "h2", "alt", "ecc", "R0"}
    if family == "rocket_equation":
        foreign = [key for key in hohmann_keys if raw.get(key) is not None]
        allowed = ", ".join(sorted(rocket_keys))
    else:
        foreign = [key for key in rocket_keys if raw.get(key) is not None]
        allowed = ", ".join(sorted(hohmann_keys))
    if foreign:
        names = ", ".join(foreign)
        raise InputError(
            f"unknown parameter for family {family}: {names}; valid given parameters: {allowed}"
        )


def _raw_from_flags(flags: dict[str, float | None]) -> dict[str, float | None]:
    mapping = {
        "m0_kg": "m0",
        "mf_kg": "mf",
        "mp_kg": "mp",
        "dry_kg": "dry",
        "ve_m_s": "ve",
        "isp_s": "isp",
        "dv_m_s": "dv",
        "growth": "growth",
        "r1_m": "r1",
        "r2_m": "r2",
        "h1_m": "h1",
        "h2_m": "h2",
        "alt_m": "alt",
        "ecc": "ecc",
        "R0_m": "R0",
    }
    return {mapping[key]: flags.get(key) for key in mapping}


def grade(family: str, target: str, solution: str, givens: dict[str, float | None], mode: str = "hint") -> tuple[int, list[tuple[str, object]]]:
    if family not in FAMILIES:
        allowed = ", ".join(FAMILIES)
        raise InputError(f"unknown family {family!r}; allowed values: {allowed}")
    if target not in TARGETS:
        allowed = ", ".join(TARGETS)
        raise InputError(f"unknown target {target!r}; allowed values: {allowed}")
    if mode not in MODES:
        raise InputError("unknown mode; allowed values: hint")
    allowed_targets = ROCKET_TARGETS if family == "rocket_equation" else HOHMANN_TARGETS
    if target not in allowed_targets:
        raise InputError(
            f"target {target} is not valid for family {family}; allowed targets: {', '.join(allowed_targets)}"
        )
    if solution is None or not str(solution).strip():
        raise InputError("missing solution text", missing=True)
    _family_givens(givens, family)
    _build_symbols()
    details: dict[str, float] = {}
    if family == "rocket_equation":
        vac = vacuum_module()
        ref = solve_rocket(givens)
        # Recompute the full value table for the target from a second pass that
        # keeps derived numbers when the reference status is ok.
        values = _rocket_value_table(givens)
        ref.value = None if ref.status != "ok" else rocket_target_value(values, target)
        ref.unit = TARGET_UNIT[target]
        assumptions = vac.ASSUMPTIONS
        if ref.status == "ok" and ref.value is None:
            ref.status = "underdetermined"
            ref.note = (ref.note + " " if ref.note else "") + "the target is not determined by these givens"
    else:
        hoh = hohmann_module()
        ref, details = solve_hohmann(givens)
        ref.value = None if ref.status != "ok" else hohmann_target_value(details, target)
        ref.unit = TARGET_UNIT[target]
        assumptions = hoh.ASSUMPTIONS
        if ref.status == "ok" and ref.value is None:
            ref.status = "underdetermined"
            ref.note = "the target is not determined by these givens"

    state = State(
        family=family,
        values=dict(ref.prebind),
        exprs={},
        dims={name: None for name in ref.prebind},
        locked=set(ref.locked),
        local=_base_local(),
    )
    for name in list(state.values):
        if name in KNOWN_DIM:
            spec = KNOWN_DIM[name]
            state.dims[name] = UREG.meter**3 / UREG.second**2 if spec == "m**3/s**2" else _pint(spec)
    answer_unit = _pint(TARGET_UNIT[target]) if TARGET_UNIT[target] != "1" else _dimless()
    if TARGET_UNIT[target] == "m/s**2":
        answer_unit = _pint("m/s**2")
    state.dims["answer"] = answer_unit
    claim_names = CLAIM_SYMBOLS[target]

    rows: list[tuple[str, object]] = [
        ("prototype", "yes"),
        ("banner", "PROTOTYPE homework checker"),
        ("mode", "hint"),
        ("hint", "line verdicts name the line and the error type and do not include a corrected line"),
        ("family", family),
        ("target", target),
        ("target_unit", TARGET_UNIT[target] if TARGET_UNIT[target] != "1" else "dimensionless"),
        ("assumptions", assumptions),
        ("checker_assumptions", _checker_assumptions(family)),
        ("tolerance_correct_relative", REL_CORRECT),
        ("tolerance_approximation_relative", REL_APPROX),
        ("tolerance_absolute", ABS_TOL),
        ("symbolic_sample_seed", SAMPLE_SEED),
        ("symbolic_sample_count", SAMPLE_COUNT),
        ("log_base", "natural"),
        ("reference_tool", ref.tool),
        ("reference_status", ref.status),
    ]
    rows.extend(ref.echo)
    if ref.note:
        rows.append(("reference_note", ref.note))

    verdicts: list[tuple[int, Verdict]] = []
    for line_no, raw_line in enumerate(solution.replace("\r\n", "\n").replace("\r", "\n").split("\n"), start=1):
        prepared = prepare_line(raw_line)
        if prepared is None:
            continue
        verdict = grade_line(prepared, state, line_no, claim_names)
        verdicts.append((line_no, verdict))
        echo = " ".join(raw_line.strip().split())
        if len(echo) > 180:
            echo = echo[:177] + "..."
        rows.append((f"line_{line_no}_verdict", verdict.kind))
        if verdict.error_type:
            rows.append((f"line_{line_no}_error_type", verdict.error_type))
        rows.append((f"line_{line_no}_note", verdict.note))
        rows.append((f"line_{line_no}_text", echo))

    rows.append(("checked_line_count", len(verdicts)))
    counts = {"correct": 0, "approximation": 0, "error": 0, "can't verify": 0}
    for _, verdict in verdicts:
        counts[verdict.kind] = counts.get(verdict.kind, 0) + 1
    rows.append(("verdict_correct", counts.get("correct", 0)))
    rows.append(("verdict_approximation", counts.get("approximation", 0)))
    rows.append(("verdict_error", counts.get("error", 0)))
    rows.append(("verdict_cant_verify", counts.get("can't verify", 0)))

    student = _student_final(state, claim_names)
    final_status, final_note = _final_status(ref, student, verdicts, answer_unit, state)
    rows.append(("final_check", final_status))
    if student is not None:
        rows.append(("final_student", student))
        rows.append(("final_student_unit", TARGET_UNIT[target] if TARGET_UNIT[target] != "1" else "dimensionless"))
    if ref.value is not None and final_status != "can't verify":
        rows.append(("final_reference", ref.value))
        rows.append(("final_reference_unit", TARGET_UNIT[target] if TARGET_UNIT[target] != "1" else "dimensionless"))
    rows.append(("final_reference_tool", ref.tool))
    rows.append(("final_note", final_note))
    return 0, rows


def _checker_assumptions(family: str) -> str:
    common = (
        "prototype; hint mode names the line and the error type and does not give a corrected line; "
        "undecidable lines are can't verify; log is natural; "
        f"correct when relative error <= {REL_CORRECT} or absolute error <= {ABS_TOL}; "
        f"approximation when relative error <= {REL_APPROX}; "
        f"symbolic spot checks use seed {SAMPLE_SEED} and {SAMPLE_COUNT} samples; "
        "g0 = 9.80665 m/s^2 from the Astraeus tools"
    )
    if family == "rocket_equation":
        return (
            common
            + "; rocket equation is delta_v_vacuum, dv = ve*ln(m0/mf), with ve = Isp*g0; "
            "propellant and wet mass come from vacuum_propellant_mass; "
            "mass_ratio means m0/mf (wet/final); mass_ratio_final_over_initial means catalogue MR = mf/m0; "
            "optional growth applies only to dry mass, matching vacuum_propellant_mass"
        )
    return (
        common
        + "; two-impulse Hohmann transfer only; burns are positive magnitudes from hohmann_transfer; "
        "mu = g0*R0^2; Earth default R0 is hohmann_transfer's Earth radius; "
        "two altitudes are converted with r = R0 + h and then solved by hohmann_transfer.solve_transfer; "
        "alt and ecc use hohmann_transfer.radii_from_altitude"
    )


def _rocket_value_table(raw: dict[str, float | None]) -> dict[str, float]:
    """Values implied by solve_rocket when the givens are consistent.

    solve_rocket already rejected inconsistent input. This repeats the fill so
    the target number comes from vacuum_propellant_mass when that call is possible.
    """
    vac = vacuum_module()
    g0 = float(vac.G0)
    isp = raw.get("isp")
    ve = raw.get("ve")
    if isp is not None and ve is None:
        ve = vac.exhaust_speed(isp, None)
    elif ve is not None:
        ve = vac.exhaust_speed(None, ve)
    dry = raw.get("dry")
    growth = raw.get("growth")
    mf = raw.get("mf")
    m0 = raw.get("m0")
    mp = raw.get("mp")
    dv = raw.get("dv")
    if dry is not None:
        if growth is None:
            growth = 0.0
        mf = dry * (1.0 + growth)
    if m0 is None and mf is not None and mp is not None:
        m0 = mf + mp
    if mf is None and m0 is not None and mp is not None:
        mf = m0 - mp
    if mp is None and m0 is not None and mf is not None:
        mp = m0 - mf
    for _ in range(6):
        changed = False
        if dv is None and ve and m0 and mf and m0 >= mf:
            dv = 0.0 if abs(m0 - mf) <= ABS_TOL else ve * math.log(m0 / mf)
            changed = True
        if ve is None and dv is not None and m0 and mf and m0 > mf:
            ve = dv / math.log(m0 / mf)
            changed = True
        if mf is None and m0 and dv is not None and ve:
            mf = m0 * math.exp(-dv / ve)
            changed = True
        if m0 is None and mf is not None and dv is not None and ve:
            _final, prop, wet = vac.propellant_mass(mf, 0.0, dv, ve)
            m0, mp = wet, prop
            changed = True
        if mp is None and m0 is not None and mf is not None:
            mp = m0 - mf
            changed = True
        if not changed:
            break
    if mf is not None and dv is not None and ve is not None:
        if dry is not None:
            final, prop, wet = vac.propellant_mass(dry, float(growth or 0.0), dv, ve)
        else:
            final, prop, wet = vac.propellant_mass(mf, 0.0, dv, ve)
        m0, mf, mp = wet, final, prop
        dv = 0.0 if abs(wet - final) <= ABS_TOL else ve * math.log(wet / final)
    values: dict[str, float] = {"g0": g0}
    for key, val in (("m0", m0), ("mf", mf), ("mp", mp), ("ve", ve), ("dv", dv)):
        if val is not None:
            values[key] = val
    if ve is not None:
        values["isp"] = ve / g0
    return values


def _student_final(state: State, claim_names: tuple[str, ...]) -> float | None:
    for _line, name, value in reversed(state.claims):
        if name in claim_names:
            return value
    return None


def _final_status(
    ref: Reference,
    student: float | None,
    verdicts: list[tuple[int, Verdict]],
    answer_unit: pint.Unit,
    state: State,
) -> tuple[str, str]:
    if ref.status == "inconsistent":
        return "can't verify", ref.note or "givens are inconsistent; reference not computed"
    if ref.status != "ok" or ref.value is None:
        return "can't verify", ref.note or "the target is not determined by these givens"
    if student is None:
        return "can't verify", "no numeric claim for the target symbol or answer"
    claim_dim = None
    for _line, name, value in reversed(state.claims):
        if value == student:
            if name in state.student_dims and state.student_dims[name] is not None:
                claim_dim = state.student_dims[name]
            elif name in KNOWN_DIM:
                spec = KNOWN_DIM[name]
                claim_dim = UREG.meter**3 / UREG.second**2 if spec == "m**3/s**2" else _pint(spec)
            break
    if claim_dim is not None and not _same(claim_dim, answer_unit):
        return "can't verify", "the claimed answer dimension does not match the target"
    kind = numeric_class(student, ref.value)
    every_pass = bool(verdicts) and all(item.kind in {"correct", "approximation"} for _, item in verdicts)
    if kind == "correct":
        return "match", "Final answer matches the reference within the correct tolerance."
    if kind == "approximation":
        return "approximate", "Final answer is within the approximation tolerance but not the correct tolerance."
    if every_pass:
        return "mismatch", UNLOCATED
    return "mismatch", "Final answer doesn't match the reference."


def rows_to_text(rows: list[tuple[str, object]]) -> str:
    return "\n".join(f"{key}: {fmt(value)}" for key, value in rows)


def run_dict(payload: dict[str, object]) -> tuple[int, str, str]:
    try:
        family = str(payload["family"])
        target = str(payload["target"])
        solution = str(payload["solution"])
        mode = str(payload.get("mode") or "hint")
        givens = _raw_from_flags({key: payload.get(key) for key in _FLAG_KEYS})  # type: ignore[arg-type]
        # payload may already use flag dest names
        code, rows = grade(family, target, solution, givens, mode)
    except InputError as exc:
        prefix = "error: "
        return (2, "", prefix + str(exc))
    except KeyError as exc:
        return (2, "", f"error: missing {exc}")
    return code, rows_to_text(rows), ""


_FLAG_KEYS = (
    "m0_kg",
    "mf_kg",
    "mp_kg",
    "dry_kg",
    "ve_m_s",
    "isp_s",
    "dv_m_s",
    "growth",
    "r1_m",
    "r2_m",
    "h1_m",
    "h2_m",
    "alt_m",
    "ecc",
    "R0_m",
)


def parse_kv(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        found[key] = value
    return found


def run_dev_case(case: dict[str, object]) -> dict[str, str]:
    givens = case.get("givens") or {}
    payload: dict[str, object] = {
        "family": case["family"],
        "target": case["target"],
        "solution": case["solution"],
        "mode": "hint",
    }
    if isinstance(givens, dict):
        payload.update(givens)
    code, stdout, stderr = run_dict(payload)
    parsed = parse_kv(stdout)
    parsed["__exit__"] = str(code)
    parsed["__stderr__"] = stderr
    return parsed


def run_check() -> int:
    path = SKILL_DIR / "dev_set.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in document["cases"]:
        result = run_dev_case(case)
        if result.get("__exit__") != "0":
            failures.append(f"{case['id']}: exit {result.get('__exit__')} {result.get('__stderr__')}")
            continue
        expected = case.get("expect") or {}
        for key, value in expected.items():
            if key == "note_contains":
                if str(value) not in result.get("final_note", ""):
                    failures.append(f"{case['id']}: final_note missing {value!r}")
                continue
            if key == "error_types":
                got = [
                    result[name]
                    for name in sorted(result, key=_line_sort)
                    if name.startswith("line_") and name.endswith("_error_type")
                ]
                if got != list(value):
                    failures.append(f"{case['id']}: error types {got} != {list(value)}")
                continue
            if key == "verdicts":
                got = [
                    result[name]
                    for name in sorted(
                        (name for name in result if name.startswith("line_") and name.endswith("_verdict")),
                        key=_line_sort,
                    )
                ]
                if got != list(value):
                    failures.append(f"{case['id']}: verdicts {got} != {list(value)}")
                continue
            if result.get(key) != str(value):
                failures.append(f"{case['id']}: {key}={result.get(key)!r} != {value!r}")
    if failures:
        print("check: fail: " + "; ".join(failures), file=sys.stderr)
        return 1
    print("check: pass")
    print_kv([("dev_cases", len(document["cases"]))])
    return 0


def _line_sort(name: str) -> tuple[int, str]:
    match = re.match(r"line_(\d+)_", name)
    if not match:
        return (10**9, name)
    return (int(match.group(1)), name)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PROTOTYPE homework checker for the rocket equation and Hohmann transfers."
    )
    parser.add_argument(
        "--family",
        choices=FAMILIES,
        help="Problem family. rocket_equation or hohmann.",
    )
    parser.add_argument(
        "--target",
        choices=TARGETS,
        help=(
            "Quantity the final answer claims. "
            "Rocket: delta_v, mass_ratio (m0/mf), mass_ratio_final_over_initial (mf/m0), "
            "propellant_mass, exhaust_speed, specific_impulse. "
            "Hohmann: circular_speed_depart, circular_speed_arrive, transfer_speed_depart, "
            "transfer_speed_arrive, dv1, dv2, dv_total, time_of_flight."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="hint",
        help="Hint mode names the line and the error type and does not give a corrected line.",
    )
    parser.add_argument(
        "--solution",
        help="Student solution, one step per line, LaTeX or plain math with units. Typed text only.",
    )
    parser.add_argument("--m0-kg", type=float, dest="m0_kg", default=None, help="Initial mass m0 [kg]")
    parser.add_argument("--mf-kg", type=float, dest="mf_kg", default=None, help="Final mass mf [kg]")
    parser.add_argument("--mp-kg", type=float, dest="mp_kg", default=None, help="Propellant mass mp [kg]")
    parser.add_argument("--dry-kg", type=float, dest="dry_kg", default=None, help="Dry mass before growth [kg]")
    parser.add_argument("--ve-m-s", type=float, dest="ve_m_s", default=None, help="Exhaust speed [m/s]")
    parser.add_argument("--isp-s", type=float, dest="isp_s", default=None, help="Specific impulse [s]")
    parser.add_argument("--dv-m-s", type=float, dest="dv_m_s", default=None, help="Delta-v [m/s]")
    parser.add_argument(
        "--growth",
        type=float,
        default=None,
        help="Growth fraction on dry mass [dimensionless]. vacuum_propellant_mass default is 0 when dry is set.",
    )
    parser.add_argument("--r1-m", type=float, dest="r1_m", default=None, help="Departure circular radius [m]")
    parser.add_argument("--r2-m", type=float, dest="r2_m", default=None, help="Arrival circular radius [m]")
    parser.add_argument("--h1-m", type=float, dest="h1_m", default=None, help="Departure geometric altitude [m]")
    parser.add_argument("--h2-m", type=float, dest="h2_m", default=None, help="Arrival geometric altitude [m]")
    parser.add_argument("--alt-m", type=float, dest="alt_m", default=None, help="Departure altitude for alt/ecc [m]")
    parser.add_argument("--ecc", type=float, default=None, help="Transfer eccentricity, 0 <= ecc < 1 [dimensionless]")
    parser.add_argument(
        "--R0-m",
        type=float,
        dest="R0_m",
        default=None,
        help="Planetary radius [m]. Default is the Earth radius in hohmann_transfer.",
    )
    parser.add_argument("--check", action="store_true", help="Run the development-set self check")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if not args.family or not args.target or args.solution is None:
        print("error: missing --family, --target, or --solution", file=sys.stderr)
        return 2
    payload = {
        "family": args.family,
        "target": args.target,
        "solution": args.solution,
        "mode": args.mode,
    }
    for key in _FLAG_KEYS:
        payload[key] = getattr(args, key)
    try:
        givens = _raw_from_flags({key: payload.get(key) for key in _FLAG_KEYS})  # type: ignore[arg-type]
        code, rows = grade(str(args.family), str(args.target), str(args.solution), givens, str(args.mode))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print_kv(rows)
    return code


if __name__ == "__main__":
    sys.exit(main())
