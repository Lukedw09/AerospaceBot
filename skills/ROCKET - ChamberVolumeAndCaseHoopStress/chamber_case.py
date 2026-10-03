#!/usr/bin/env python3
"""Chamber volume from L*, and thin-wall case hoop stress and margin of safety.

Vc comes from characteristic_length (formulas.md): L* = Vc / At.
Hoop stress comes from cylinder_hoop_stress: sigma_h = p * R / t.
Margin of safety comes from margin_of_safety: MS = allowable / design - 1,
with the hoop stress used as the design stress.
"""

from __future__ import annotations

import argparse
import sys

CHECK_TOL = 1e-9
THIN_WALL_LIMIT = 0.1


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= CHECK_TOL * scale


def chamber_volume(throat: float, lstar: float) -> float:
    """Vc = L* * At."""
    return lstar * throat


def hoop_stress(pc: float, radius: float, thickness: float) -> float:
    """sigma_h = p * R / t."""
    return pc * radius / thickness


def margin_of_safety(allowable: float, design: float) -> float:
    """MS = allowable / design - 1."""
    return allowable / design - 1.0


def thin_wall(radius: float, thickness: float) -> str:
    """SP-8025 thin membrane: thickness small compared with radius."""
    if thickness / radius < THIN_WALL_LIMIT:
        return "yes"
    return "no"


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def run_check() -> int:
    # characteristic_length identity: Vc = 3/1000, At = 1/500, L* = 3/2.
    throat_id = 1.0 / 500.0
    lstar_id = 3.0 / 2.0
    volume_id = chamber_volume(throat_id, lstar_id)
    if not close(volume_id, 3.0 / 1000.0):
        return fail(f"CHECK FAIL: Vc = {volume_id}, expected {3.0 / 1000.0}")
    if not close(lstar_id, volume_id / throat_id):
        return fail("CHECK FAIL: L* does not match Vc / At")

    # cylinder_hoop_stress identity: forty-inch cylinder sample, p*R/t.
    hoop_id = hoop_stress(1000.0, 20.0, 1.0 / 10.0)
    if not close(hoop_id, 200000.0):
        return fail(f"CHECK FAIL: hoop = {hoop_id}, expected 200000")

    # margin_of_safety identities: zero_margin and quarter_margin.
    if not close(margin_of_safety(200000.0, 200000.0), 0.0):
        return fail("CHECK FAIL: equal allowable and design stress are not MS = 0")
    if not close(margin_of_safety(200000.0, 160000.0), 0.25):
        return fail("CHECK FAIL: quarter margin is not 0.25")
    if not close(margin_of_safety(hoop_id, hoop_id), 0.0):
        return fail("CHECK FAIL: hoop used as both allowable and design is not MS = 0")

    # Combined SI point: At = 1/2000 m^2, L* = 6/5 m, Vc = 6/10000 m^3.
    throat = 1.0 / 2000.0
    lstar = 6.0 / 5.0
    pc = 2.0e6
    radius = 1.0 / 20.0
    thickness = 1.0 / 500.0
    allowable = 6.25e7
    volume = chamber_volume(throat, lstar)
    hoop = hoop_stress(pc, radius, thickness)
    margin = margin_of_safety(allowable, hoop)
    if not close(volume, 6.0 / 10000.0):
        return fail(f"CHECK FAIL: SI Vc = {volume}, expected {6.0 / 10000.0}")
    if not close(hoop, 5.0e7):
        return fail(f"CHECK FAIL: SI hoop = {hoop}, expected 50000000")
    if not close(hoop * thickness, pc * radius):
        return fail("CHECK FAIL: hoop * t does not match pc * R")
    if not close(margin, 0.25):
        return fail(f"CHECK FAIL: SI MS = {margin}, expected 0.25")
    if thin_wall(radius, thickness) != "yes":
        return fail("CHECK FAIL: t/R = 0.04 was not treated as a thin wall")
    if thin_wall(1.0, 0.1) != "no":
        return fail("CHECK FAIL: t/R = 0.1 was treated as a thin wall")

    print("check: pass")
    print_kv("At_m2", throat)
    print_kv("Lstar_m", lstar)
    print_kv("Vc_m3", volume)
    print_kv("hoop_Pa", hoop)
    print_kv("margin_of_safety", margin)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Chamber volume from characteristic length, and thin-wall "
            "case hoop stress with margin of safety."
        )
    )
    parser.add_argument("--throat", type=float, default=None, help="throat area At [m^2]")
    parser.add_argument("--lstar", type=float, default=None, help="characteristic length L* [m]")
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure p [Pa]")
    parser.add_argument("--radius", type=float, default=None, help="case radius R [m]")
    parser.add_argument("--thickness", type=float, default=None, help="wall thickness t [m]")
    parser.add_argument(
        "--allowable",
        type=float,
        default=None,
        help="allowable stress [Pa]",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--throat": args.throat,
        "--lstar": args.lstar,
        "--pc": args.pc,
        "--radius": args.radius,
        "--thickness": args.thickness,
        "--allowable": args.allowable,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --throat, --lstar, --pc, --radius, --thickness, "
            f"and --allowable; missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    limits = {
        "--throat": "throat area must be > 0 m^2",
        "--lstar": "L* must be > 0 m",
        "--pc": "pc must be > 0 Pa",
        "--radius": "case radius must be > 0 m",
        "--thickness": "wall thickness must be > 0 m",
        "--allowable": "allowable stress must be > 0 Pa",
    }
    for flag, message in limits.items():
        if supplied[flag] <= 0:
            print(f"error: {message}", file=sys.stderr)
            return 2

    volume = chamber_volume(args.throat, args.lstar)
    hoop = hoop_stress(args.pc, args.radius, args.thickness)
    margin = margin_of_safety(args.allowable, hoop)

    print_kv(
        "assumptions",
        (
            "Vc = L* * At, volume through the throat plane; "
            "thin cylindrical membrane sigma_h = pc * R / t; "
            "MS = allowable / hoop - 1; "
            "pc is used as the design pressure and is not multiplied by a factor here; "
            "thin_wall is yes when t/R < 0.1"
        ),
    )
    print_kv("At_m2", args.throat)
    print_kv("Lstar_m", args.lstar)
    print_kv("pc_Pa", args.pc)
    print_kv("R_m", args.radius)
    print_kv("t_m", args.thickness)
    print_kv("allowable_Pa", args.allowable)
    print_kv("t_over_R", args.thickness / args.radius)
    print_kv("thin_wall", thin_wall(args.radius, args.thickness))
    print_kv("Vc_m3", volume)
    print_kv("hoop_Pa", hoop)
    print_kv("margin_of_safety", margin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
