#!/usr/bin/env python3
"""Throat area, throat diameter, and propellant mass flow.

At comes from thrust_coefficient_form (formulas.md): F = CF * p1 * At.
Dt is the diameter of a circular throat: At = pi * Dt**2 / 4.
mdot comes from characteristic_velocity (formulas.md): c* = p1 * At / mdot.
"""

from __future__ import annotations

import argparse
import math
import sys

CHECK_TOL = 1e-9


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def throat_area(thrust: float, cf: float, pc: float) -> float:
    """At = F / (CF * p1)."""
    return thrust / (cf * pc)


def throat_diameter(area: float) -> float:
    """Circular throat: Dt = sqrt(4 * At / pi)."""
    return math.sqrt(4.0 * area / math.pi)


def mass_flow(pc: float, area: float, cstar: float) -> float:
    """mdot = p1 * At / c*."""
    return pc * area / cstar


def run_check() -> int:
    thrust = 1500.0
    cf = 1.5
    pc = 2.0e6
    cstar = 1600.0
    area = throat_area(thrust, cf, pc)
    diameter = throat_diameter(area)
    mdot = mass_flow(pc, area, cstar)
    expected_area = 5.0e-4
    expected_mdot = 0.625
    if abs(area - expected_area) > CHECK_TOL:
        print(
            f"CHECK FAIL: At = {area}, expected {expected_area}",
            file=sys.stderr,
        )
        return 1
    if abs(diameter**2 * math.pi / 4.0 - area) > CHECK_TOL:
        print(
            f"CHECK FAIL: circular area from Dt = {diameter} is not At",
            file=sys.stderr,
        )
        return 1
    if abs(mdot - expected_mdot) > CHECK_TOL:
        print(
            f"CHECK FAIL: mdot = {mdot}, expected {expected_mdot}",
            file=sys.stderr,
        )
        return 1
    if abs(mdot - thrust / (cf * cstar)) > CHECK_TOL:
        print(
            "CHECK FAIL: p1*At/c* does not match F/(c* * CF)",
            file=sys.stderr,
        )
        return 1
    print("check: pass")
    print_kv("At_m2", area)
    print_kv("Dt_m", diameter)
    print_kv("mdot_kg_s", mdot)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Size a circular nozzle throat and the propellant mass flow."
    )
    parser.add_argument("--thrust", type=float, default=None, help="thrust F [N]")
    parser.add_argument("--cf", type=float, default=None, help="thrust coefficient CF")
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure p1 [Pa]")
    parser.add_argument(
        "--cstar",
        type=float,
        default=None,
        help="characteristic velocity c* [m/s]",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--thrust": args.thrust,
        "--cf": args.cf,
        "--pc": args.pc,
        "--cstar": args.cstar,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --thrust, --cf, --pc, and --cstar; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    limits = {
        "--thrust": "thrust must be > 0 N",
        "--cf": "CF must be > 0",
        "--pc": "pc must be > 0 Pa",
        "--cstar": "c* must be > 0 m/s",
    }
    for flag, message in limits.items():
        if supplied[flag] <= 0:
            print(f"error: {message}", file=sys.stderr)
            return 2

    area = throat_area(args.thrust, args.cf, args.pc)
    diameter = throat_diameter(area)
    mdot = mass_flow(args.pc, area, args.cstar)

    print_kv(
        "assumptions",
        (
            "steady flow; F = CF * pc * At; circular throat; "
            "mdot = pc * At / c*; CF and c* are inputs and are not computed here"
        ),
    )
    print_kv("thrust_N", args.thrust)
    print_kv("CF", args.cf)
    print_kv("pc_Pa", args.pc)
    print_kv("cstar_m_s", args.cstar)
    print_kv("At_m2", area)
    print_kv("Dt_m", diameter)
    print_kv("mdot_kg_s", mdot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
