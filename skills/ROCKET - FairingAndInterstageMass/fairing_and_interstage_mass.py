#!/usr/bin/env python3
"""Fairing and interstage shell masses from developed area, thickness, and density.

cylinder_shell_mass, cone_shell_mass, and tangent_ogive_shell_mass.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

PI = math.pi
CHECK_TOL = 1e-8

ASSUMPTIONS = (
    "constant-thickness open shells; cylinder_shell_mass is the lateral "
    "cylinder only; cone_shell_mass is the cone lateral area; "
    "tangent_ogive_shell_mass is the tangent-ogive surface of revolution; "
    "bulkheads are omitted; design_factor multiplies both masses and defaults "
    "to 1 only when omitted; areal density replaces rho*t when given; "
    "jettison mass is the fairing"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def cylinder_shell_mass(rho: float, thickness: float, diameter: float, length: float) -> float:
    return rho * thickness * PI * diameter * length


def cone_shell_mass(rho: float, thickness: float, radius: float, length: float) -> float:
    return rho * thickness * PI * radius * math.sqrt(radius * radius + length * length)


def ogive_shell_mass(rho: float, thickness: float, radius: float, length: float) -> float:
    rho_c = (radius * radius + length * length) / (2.0 * radius)
    arc = length + (radius - rho_c) * math.asin(length / rho_c)
    return rho * thickness * 2.0 * PI * rho_c * arc


def run(args: argparse.Namespace) -> int:
    for name, value in (
        ("fairing diameter", args.fairing_diameter),
        ("cylinder length", args.cylinder_length),
        ("nose length", args.nose_length),
        ("interstage diameter", args.interstage_diameter),
        ("interstage length", args.interstage_length),
    ):
        if value is None or value <= 0.0:
            raise ValueError(f"{name} must be > 0")
    factor = 1.0 if args.design_factor is None else args.design_factor
    if factor <= 0.0:
        raise ValueError("design factor must be > 0")
    if args.areal is not None:
        if args.areal <= 0.0:
            raise ValueError("areal density must be > 0")
        rho, thickness = args.areal, 1.0
        areal_mode = True
    else:
        if args.thickness is None or args.rho is None:
            raise ValueError("pass --thickness and --rho, or --areal")
        if args.thickness <= 0.0 or args.rho <= 0.0:
            raise ValueError("thickness and density must be > 0")
        rho, thickness = args.rho, args.thickness
        areal_mode = False
    nose = args.nose
    radius = 0.5 * args.fairing_diameter
    barrel = cylinder_shell_mass(rho, thickness, args.fairing_diameter, args.cylinder_length)
    if nose == "cone":
        nose_mass = cone_shell_mass(rho, thickness, radius, args.nose_length)
    elif nose == "ogive":
        nose_mass = ogive_shell_mass(rho, thickness, radius, args.nose_length)
    else:
        raise ValueError("nose must be cone or ogive")
    if areal_mode:
        # cylinder_shell_mass used rho*t = areal when thickness is 1.
        pass
    fairing = factor * (barrel + nose_mass)
    interstage = factor * cylinder_shell_mass(rho, thickness, args.interstage_diameter, args.interstage_length)
    print_kv("title", "Fairing and interstage")
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("nose", nose)
    print_kv("design_factor", factor)
    print_kv("mass_source", "areal" if areal_mode else "rho_t")
    print_kv("fairing_cylinder_kg", factor * barrel)
    print_kv("fairing_nose_kg", factor * nose_mass)
    print_kv("fairing_kg", fairing)
    print_kv("interstage_kg", interstage)
    print_kv("jettison_kg", fairing)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    cyl = cylinder_shell_mass(2.0, 0.1, 2.0, 3.0)
    if abs(cyl - 1.2 * PI) > 1e-9:
        return fail("cylinder")
    cone = cone_shell_mass(2.0, 0.1, 3.0, 4.0)
    if abs(cone - 3.0 * PI) > 1e-9:
        return fail("cone")
    ogive = ogive_shell_mass(2.0, 0.5, 1.0, 1.0)
    if abs(ogive - 2.0 * PI) > 1e-8:
        return fail("ogive hemisphere")
    try:
        # build a namespace via main
        with tempfile.TemporaryDirectory() as tmp:
            png = str(Path(tmp) / "out.png")
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                code = main(
                    [
                        "--fairing-diameter", "2",
                        "--cylinder-length", "4",
                        "--nose-length", "1",
                        "--nose", "cone",
                        "--interstage-diameter", "2",
                        "--interstage-length", "1",
                        "--thickness", "0.002",
                        "--rho", "2700",
                        "--out", png,
                    ]
                )
            finally:
                sys.stdout = old
            text = buf.getvalue()
            if code != 0 or "fairing_kg:" not in text:
                return fail("cli")
            if "graph:" in text:
                return fail("png")
    except ValueError as exc:
        return fail(str(exc))
    bad = main(["--fairing-diameter", "0", "--cylinder-length", "1", "--nose-length", "1", "--nose", "cone", "--interstage-diameter", "1", "--interstage-length", "1", "--thickness", "1", "--rho", "1"])
    if bad == 0:
        return fail("accepted zero diameter")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fairing and interstage shell mass.")
    parser.add_argument("--fairing-diameter", type=float)
    parser.add_argument("--cylinder-length", type=float)
    parser.add_argument("--nose-length", type=float)
    parser.add_argument("--nose", choices=("cone", "ogive"), default="cone")
    parser.add_argument("--interstage-diameter", type=float)
    parser.add_argument("--interstage-length", type=float)
    parser.add_argument("--thickness", type=float, default=None)
    parser.add_argument("--rho", type=float, default=None)
    parser.add_argument("--areal", type=float, default=None, help="Areal density kg/m^2, instead of thickness and rho")
    parser.add_argument("--design-factor", type=float, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
