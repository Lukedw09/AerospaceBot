#!/usr/bin/env python3
"""Delivered rocket performance from ideal CF, ideal c*, and named efficiencies.

Ideal CF and ideal c* are inputs. Each named efficiency is a multiplier.
Combustion and c* efficiencies scale c*. Nozzle and divergence efficiencies
scale CF. An omitted canonical efficiency is 1. c, Isp, thrust, and mass
flow then follow effective_exhaust_velocity, specific_impulse,
thrust_coefficient_form, and characteristic_velocity in formulas.md.
"""

from __future__ import annotations

import argparse
import math
import sys

# g0 converts specific impulse in seconds to effective exhaust velocity.
G0 = 9.80665
CHECK_TOL = 1e-8

# name, side. Side "cstar" multiplies ideal c*. Side "cf" multiplies ideal CF.
CANONICAL = (
    ("combustion", "cstar"),
    ("cstar", "cstar"),
    ("nozzle", "cf"),
    ("divergence", "cf"),
)

ALIASES = {
    "combustion": "combustion",
    "comb": "combustion",
    "cstar": "cstar",
    "c-star": "cstar",
    "c*": "cstar",
    "cee-star": "cstar",
    "nozzle": "nozzle",
    "cf-efficiency": "nozzle",
    "thrust-coefficient": "nozzle",
    "divergence": "divergence",
    "lambda": "divergence",
    "thrust-efficiency": "divergence",
    "conical": "divergence",
}

SIDE_ALIASES = {
    "cstar": "cstar",
    "c-star": "cstar",
    "c*": "cstar",
    "cf": "cf",
}

ASSUMPTIONS = (
    "steady flow; ideal CF and ideal c* are inputs and are not computed here; "
    "each named efficiency is a multiplier and each omitted canonical "
    "efficiency is 1; combustion and cstar, plus any extra marked @cstar, "
    "multiply ideal c*; nozzle and divergence, plus any extra marked @cf, "
    "multiply ideal CF; the same physical loss is not entered under two "
    "names; c = c* * CF from effective_exhaust_velocity; "
    "Isp = c/g0 from specific_impulse; g0 = 9.80665 m/s^2; "
    "when pc and At are both given, F = CF * pc * At from "
    "thrust_coefficient_form and mdot = pc * At / c* from "
    "characteristic_velocity; thrust_ideal and mdot_ideal use ideal CF and "
    "ideal c* with every efficiency equal to 1; thrust and mdot use the "
    "actual CF and actual c*; at fixed pc and At, thrust follows CF and "
    "mass flow follows c*; an efficiency may be greater than 1"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def normalize_token(raw: str) -> str:
    name = raw.strip().lower().replace("_", "-")
    return "-".join(part for part in name.split() if part)


def name_candidates(raw: str) -> list[str]:
    """Token after an eta- prefix is removed, then again with a trailing -efficiency removed."""
    name = normalize_token(raw)
    if name.startswith("eta-") and name != "eta-":
        name = name[4:]
    candidates = [name]
    if name.endswith("-efficiency") and name != "-efficiency":
        candidates.append(name[: -len("-efficiency")])
    return candidates


def canonical_side(name: str) -> str | None:
    for canonical, side in CANONICAL:
        if canonical == name:
            return side
    return None


def parse_side(raw: str) -> str:
    side = normalize_token(raw)
    if side not in SIDE_ALIASES:
        known = ", ".join(sorted(SIDE_ALIASES))
        raise ValueError(f"unknown efficiency side {raw!r}; use one of {known}")
    return SIDE_ALIASES[side]


def resolve_name(raw: str, explicit_side: str | None) -> tuple[str, str]:
    candidates = name_candidates(raw)
    if not candidates[0] or any(ch in candidates[0] for ch in "=@"):
        raise ValueError(f"efficiency name {raw!r} is not usable")
    name = None
    for candidate in candidates:
        if candidate in ALIASES:
            name = ALIASES[candidate]
            break
    if name is None:
        name = candidates[-1]
    side = canonical_side(name)
    if side is None:
        if explicit_side is None:
            known = ", ".join(item[0] for item in CANONICAL)
            raise ValueError(
                f"efficiency {raw!r} needs @cstar or @cf; "
                f"known names are {known}"
            )
        if name in {"cstar-product", "cf-product", "product"}:
            raise ValueError(f"efficiency name {raw!r} is reserved")
        return name, explicit_side
    if explicit_side is not None and explicit_side != side:
        target = "c*" if side == "cstar" else "CF"
        given = "c*" if explicit_side == "cstar" else "CF"
        raise ValueError(f"{name} applies to {target}, not {given}")
    return name, side


def parse_eta(text: str) -> tuple[str, str, float]:
    """Parse name=value or name=value@side. Returns name, side, value."""
    item = text.strip()
    if "=" not in item:
        raise ValueError(
            f"--eta {text!r} must be name=value or name=value@cstar or name=value@cf"
        )
    raw_name, rest = item.split("=", 1)
    raw_side = None
    raw_value = rest.strip()
    if "@" in rest:
        raw_value, raw_side = rest.rsplit("@", 1)
        raw_value = raw_value.strip()
        raw_side = raw_side.strip()
    explicit = parse_side(raw_side) if raw_side else None
    name, side = resolve_name(raw_name, explicit)
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"efficiency {name} is not a number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"efficiency {name} must be > 0")
    return name, side, value


def collect_efficiencies(
    items: list[str],
) -> list[tuple[str, str, float]]:
    """Canonical efficiencies in catalog order, then extras in input order."""
    supplied: dict[str, tuple[str, float]] = {}
    extras: list[tuple[str, str, float]] = []
    for text in items:
        name, side, value = parse_eta(text)
        if name in supplied or any(existing == name for existing, _, _ in extras):
            raise ValueError(f"repeated efficiency {name}")
        if canonical_side(name) is None:
            extras.append((name, side, value))
        else:
            supplied[name] = (side, value)
    ordered: list[tuple[str, str, float]] = []
    for name, side in CANONICAL:
        if name in supplied:
            ordered.append((name, supplied[name][0], supplied[name][1]))
        else:
            ordered.append((name, side, 1.0))
    ordered.extend(extras)
    return ordered


def product_for(efficiencies: list[tuple[str, str, float]], side: str) -> float:
    value = 1.0
    for _, item_side, factor in efficiencies:
        if item_side == side:
            value *= factor
    return value


def delivered(
    cf_ideal: float,
    cstar_ideal: float,
    efficiencies: list[tuple[str, str, float]],
    pc: float | None,
    throat: float | None,
) -> dict[str, float]:
    eta_cstar = product_for(efficiencies, "cstar")
    eta_cf = product_for(efficiencies, "cf")
    cstar = cstar_ideal * eta_cstar
    cf = cf_ideal * eta_cf
    c = cstar * cf
    isp = c / G0
    out = {
        "eta_product_cstar": eta_cstar,
        "eta_product_CF": eta_cf,
        "cstar_m_s": cstar,
        "CF": cf,
        "c_m_s": c,
        "Isp_s": isp,
    }
    if pc is not None and throat is not None:
        out["thrust_ideal_N"] = cf_ideal * pc * throat
        out["mdot_ideal_kg_s"] = pc * throat / cstar_ideal
        out["thrust_N"] = cf * pc * throat
        out["mdot_kg_s"] = pc * throat / cstar
    return out


def run_check() -> int:
    cf_ideal = 1.5
    cstar_ideal = 1600.0
    pc = 2.0e6
    throat = 5.0e-4
    items = ["combustion=0.98", "nozzle=0.97", "boundary=0.99@cf"]
    efficiencies = collect_efficiencies(items)
    by_name = {name: value for name, _, value in efficiencies}
    if by_name["cstar"] != 1.0 or by_name["divergence"] != 1.0:
        print("CHECK FAIL: omitted canonical efficiencies are not 1", file=sys.stderr)
        return 1
    if abs(by_name["combustion"] - 0.98) > CHECK_TOL:
        print("CHECK FAIL: combustion efficiency was not kept", file=sys.stderr)
        return 1
    result = delivered(cf_ideal, cstar_ideal, efficiencies, pc, throat)
    eta_cstar = 0.98
    eta_cf = 0.97 * 0.99
    cstar = cstar_ideal * eta_cstar
    cf = cf_ideal * eta_cf
    c = cstar * cf
    expected = {
        "eta_product_cstar": eta_cstar,
        "eta_product_CF": eta_cf,
        "cstar_m_s": cstar,
        "CF": cf,
        "c_m_s": c,
        "Isp_s": c / G0,
        "thrust_ideal_N": cf_ideal * pc * throat,
        "mdot_ideal_kg_s": pc * throat / cstar_ideal,
        "thrust_N": cf * pc * throat,
        "mdot_kg_s": pc * throat / cstar,
    }
    for name, want in expected.items():
        if abs(result[name] - want) > CHECK_TOL:
            print(
                f"CHECK FAIL: {name} = {result[name]}, expected {want}",
                file=sys.stderr,
            )
            return 1
    thrust = result["thrust_N"]
    mdot = result["mdot_kg_s"]
    if abs(thrust - mdot * result["c_m_s"]) > CHECK_TOL:
        print("CHECK FAIL: thrust is not mdot * c", file=sys.stderr)
        return 1
    if abs(result["Isp_s"] - thrust / (mdot * G0)) > CHECK_TOL:
        print("CHECK FAIL: Isp is not F/(mdot*g0)", file=sys.stderr)
        return 1
    ideal_c = cstar_ideal * cf_ideal
    if abs(result["thrust_ideal_N"] - result["mdot_ideal_kg_s"] * ideal_c) > CHECK_TOL:
        print("CHECK FAIL: ideal thrust is not ideal mdot * ideal c", file=sys.stderr)
        return 1

    bare = delivered(cf_ideal, cstar_ideal, collect_efficiencies([]), None, None)
    if abs(bare["CF"] - cf_ideal) > CHECK_TOL or abs(bare["cstar_m_s"] - cstar_ideal) > CHECK_TOL:
        print("CHECK FAIL: all-unity efficiencies changed CF or c*", file=sys.stderr)
        return 1
    if any(key in bare for key in ("thrust_N", "mdot_kg_s", "thrust_ideal_N", "mdot_ideal_kg_s")):
        print("CHECK FAIL: thrust or mdot without pc and At", file=sys.stderr)
        return 1

    aliased = collect_efficiencies(
        ["c*=0.99", "cf-efficiency=0.97", "thrust-efficiency=0.983"]
    )
    alias_values = {name: value for name, _, value in aliased}
    if abs(alias_values["cstar"] - 0.99) > CHECK_TOL:
        print("CHECK FAIL: c* was not read as cstar", file=sys.stderr)
        return 1
    if abs(alias_values["nozzle"] - 0.97) > CHECK_TOL:
        print("CHECK FAIL: cf-efficiency was not read as nozzle", file=sys.stderr)
        return 1
    if abs(alias_values["divergence"] - 0.983) > CHECK_TOL:
        print("CHECK FAIL: thrust-efficiency was not read as divergence", file=sys.stderr)
        return 1

    stacked = collect_efficiencies(["combustion=0.5", "cstar=0.5"])
    both = delivered(cf_ideal, cstar_ideal, stacked, None, None)
    if abs(both["cstar_m_s"] - 0.25 * cstar_ideal) > CHECK_TOL:
        print("CHECK FAIL: combustion and cstar did not both scale c*", file=sys.stderr)
        return 1
    if abs(both["CF"] - cf_ideal) > CHECK_TOL:
        print("CHECK FAIL: c* efficiencies changed CF", file=sys.stderr)
        return 1

    print("check: pass")
    print_kv("cstar_m_s", result["cstar_m_s"])
    print_kv("CF", result["CF"])
    print_kv("Isp_s", result["Isp_s"])
    print_kv("thrust_ideal_N", result["thrust_ideal_N"])
    print_kv("mdot_ideal_kg_s", result["mdot_ideal_kg_s"])
    print_kv("thrust_N", result["thrust_N"])
    print_kv("mdot_kg_s", result["mdot_kg_s"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply named efficiencies to ideal thrust coefficient and ideal c*."
        )
    )
    parser.add_argument(
        "--cf",
        type=float,
        default=None,
        help="ideal thrust coefficient CF",
    )
    parser.add_argument(
        "--cstar",
        type=float,
        default=None,
        help="ideal characteristic velocity c* [m/s]",
    )
    parser.add_argument(
        "--throat",
        type=float,
        default=None,
        help="throat area At [m^2]",
    )
    parser.add_argument(
        "--pc",
        type=float,
        default=None,
        help="chamber pressure p1 [Pa]",
    )
    parser.add_argument(
        "--eta",
        action="append",
        default=[],
        help=(
            "named efficiency, name=value or name=value@cstar or name=value@cf; "
            "repeat for each one the user supplied"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run built-in consistency checks",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--cf": args.cf,
        "--cstar": args.cstar,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --cf and --cstar; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if args.cf <= 0:
        print("error: CF must be > 0", file=sys.stderr)
        return 2
    if args.cstar <= 0:
        print("error: c* must be > 0 m/s", file=sys.stderr)
        return 2

    has_throat = args.throat is not None
    has_pc = args.pc is not None
    if has_throat != has_pc:
        print("error: --throat and --pc must be given together", file=sys.stderr)
        return 2
    if has_throat and args.throat <= 0:
        print("error: throat area must be > 0 m^2", file=sys.stderr)
        return 2
    if has_pc and args.pc <= 0:
        print("error: pc must be > 0 Pa", file=sys.stderr)
        return 2

    try:
        efficiencies = collect_efficiencies(args.eta)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = delivered(args.cf, args.cstar, efficiencies, args.pc, args.throat)

    print_kv("assumptions", ASSUMPTIONS)
    print_kv("CF_ideal", args.cf)
    print_kv("cstar_ideal_m_s", args.cstar)
    print_kv("g0_m_s2", G0)
    for name, side, value in efficiencies:
        print_kv(f"eta_{name.replace('-', '_').replace('*', 'star')}", value)
        print_kv(
            f"eta_{name.replace('-', '_').replace('*', 'star')}_applies",
            "cstar" if side == "cstar" else "CF",
        )
    print_kv("eta_product_cstar", result["eta_product_cstar"])
    print_kv("eta_product_CF", result["eta_product_CF"])
    print_kv("cstar_m_s", result["cstar_m_s"])
    print_kv("CF", result["CF"])
    print_kv("c_m_s", result["c_m_s"])
    print_kv("Isp_s", result["Isp_s"])
    if has_throat:
        print_kv("pc_Pa", args.pc)
        print_kv("At_m2", args.throat)
        print_kv("thrust_ideal_N", result["thrust_ideal_N"])
        print_kv("mdot_ideal_kg_s", result["mdot_ideal_kg_s"])
        print_kv("thrust_N", result["thrust_N"])
        print_kv("mdot_kg_s", result["mdot_kg_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
