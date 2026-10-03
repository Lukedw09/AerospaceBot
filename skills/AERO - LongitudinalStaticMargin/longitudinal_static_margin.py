#!/usr/bin/env python3
"""Stick-fixed neutral point and static margin for the simplified airplane.

x0/c comes from stick_fixed_neutral_point (formulas.md), NACA TN 1670 equation (6).
x/c comes from center_of_gravity_to_neutral_point: x0/c - x'/c.
Static margin comes from static_margin: 100 * x/c, in percent of the mean aerodynamic chord.
"""

from __future__ import annotations

import argparse
import sys

CHECK_TOL = 1e-9


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= CHECK_TOL * scale


def tail_volume(tail_area: float, tail_length: float, wing_area: float, mac: float) -> float:
    """(S_T / S) * (l / c), the geometric group in stick_fixed_neutral_point."""
    return (tail_area * tail_length) / (wing_area * mac)


def stick_fixed_neutral_point(
    downwash: float,
    tail_slope: float,
    wing_slope: float,
    q_ratio: float,
    volume: float,
) -> float:
    """x0/c = (1 - dε/dα) * (a_T / a) * (q_T / q) * (S_T l) / (S c)."""
    return (1.0 - downwash) * (tail_slope / wing_slope) * q_ratio * volume


def center_of_gravity_to_neutral_point(neutral_point: float, cg: float) -> float:
    """x/c = x0/c - x'/c."""
    return neutral_point - cg


def static_margin(distance: float) -> float:
    """Static margin in percent of the mean aerodynamic chord."""
    return 100.0 * distance


def stability(margin: float) -> str:
    """Positive static margin: center of gravity ahead of the neutral point."""
    if margin > 0.0:
        return "stable"
    if margin < 0.0:
        return "unstable"
    return "neutral"


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def run_check() -> int:
    # stick_fixed_neutral_point identity sample_tail: x0/c = 54/125.
    volume_sample = tail_volume(2.0, 5.0, 10.0, 1.0)
    if not close(volume_sample, 1.0):
        return fail(f"CHECK FAIL: sample tail volume = {volume_sample}, expected 1")
    neutral_sample = stick_fixed_neutral_point(2.0 / 5.0, 4.0, 5.0, 9.0 / 10.0, volume_sample)
    if not close(neutral_sample, 54.0 / 125.0):
        return fail(f"CHECK FAIL: sample x0/c = {neutral_sample}, expected {54.0 / 125.0}")

    # stick_fixed_neutral_point identity equal_slopes: x0/c = 1/4.
    volume_equal = tail_volume(1.0, 4.0, 8.0, 2.0)
    neutral_equal = stick_fixed_neutral_point(0.0, 1.0, 1.0, 1.0, volume_equal)
    if not close(neutral_equal, 0.25):
        return fail(f"CHECK FAIL: equal-slope x0/c = {neutral_equal}, expected 0.25")

    # center_of_gravity_to_neutral_point identity ahead: 54/125 - 1/10 = 83/250.
    distance = center_of_gravity_to_neutral_point(neutral_sample, 0.1)
    if not close(distance, 83.0 / 250.0):
        return fail(f"CHECK FAIL: x/c = {distance}, expected {83.0 / 250.0}")

    # static_margin identity five_percent: 100 * (1/20) = 5.
    if not close(static_margin(1.0 / 20.0), 5.0):
        return fail("CHECK FAIL: five percent of the chord is not static margin 5")
    if not close(static_margin(distance), 100.0 * (83.0 / 250.0)):
        return fail("CHECK FAIL: static margin is not 100 * x/c")

    # CG at the neutral point is zero margin. CG aft of it is unstable.
    if stability(static_margin(0.0)) != "neutral":
        return fail("CHECK FAIL: zero distance was not neutral")
    if stability(static_margin(center_of_gravity_to_neutral_point(0.25, 0.25))) != "neutral":
        return fail("CHECK FAIL: CG at the neutral point was not neutral")
    if stability(static_margin(center_of_gravity_to_neutral_point(0.25, 0.4))) != "unstable":
        return fail("CHECK FAIL: CG aft of the neutral point was not unstable")
    if stability(static_margin(distance)) != "stable":
        return fail("CHECK FAIL: positive x/c was not stable")

    print("check: pass")
    print_kv("neutral_point_x0_over_c", neutral_sample)
    print_kv("x_over_c", distance)
    print_kv("static_margin_percent", static_margin(distance))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stick-fixed neutral point and static margin from NACA TN 1670 "
            "equations (6) and (7)."
        )
    )
    parser.add_argument(
        "--a",
        type=float,
        default=None,
        help="wing-fuselage lift-curve slope dCL/dα",
    )
    parser.add_argument(
        "--at",
        type=float,
        default=None,
        help="tail lift-curve slope (dCL/dα)_T, elevator fixed",
    )
    parser.add_argument(
        "--downwash",
        type=float,
        default=None,
        help="downwash slope dε/dα",
    )
    parser.add_argument(
        "--q-ratio",
        type=float,
        default=None,
        help="tail dynamic-pressure ratio qT/q",
    )
    parser.add_argument("--tail-area", type=float, default=None, help="horizontal-tail area ST [m^2]")
    parser.add_argument(
        "--tail-length",
        type=float,
        default=None,
        help="tail length l from the neutral point to the tail quarter-chord [m]",
    )
    parser.add_argument("--wing-area", type=float, default=None, help="wing area S [m^2]")
    parser.add_argument("--mac", type=float, default=None, help="wing mean aerodynamic chord c [m]")
    parser.add_argument(
        "--cg",
        type=float,
        default=None,
        help="x'/c, center of gravity aft of the wing-fuselage aerodynamic center",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--a": args.a,
        "--at": args.at,
        "--downwash": args.downwash,
        "--q-ratio": args.q_ratio,
        "--tail-area": args.tail_area,
        "--tail-length": args.tail_length,
        "--wing-area": args.wing_area,
        "--mac": args.mac,
        "--cg": args.cg,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --a, --at, --downwash, --q-ratio, --tail-area, "
            "--tail-length, --wing-area, --mac, and --cg; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    positive = {
        "--a": "wing-fuselage lift-curve slope must be > 0",
        "--q-ratio": "qT/q must be > 0",
        "--tail-area": "tail area must be > 0 m^2",
        "--tail-length": "tail length must be > 0 m",
        "--wing-area": "wing area must be > 0 m^2",
        "--mac": "mean aerodynamic chord must be > 0 m",
    }
    for flag, message in positive.items():
        if supplied[flag] <= 0.0:
            print(f"error: {message}", file=sys.stderr)
            return 2

    volume = tail_volume(args.tail_area, args.tail_length, args.wing_area, args.mac)
    neutral = stick_fixed_neutral_point(args.downwash, args.at, args.a, args.q_ratio, volume)
    distance = center_of_gravity_to_neutral_point(neutral, args.cg)
    margin = static_margin(distance)

    print_kv(
        "assumptions",
        (
            "stick-fixed; TN 1670 equation (6) for x0/c from the wing-fuselage "
            "aerodynamic center; x/c = x0/c - x'/c; static margin = 100 * x/c; "
            "l is measured from the neutral point to the tail quarter-chord; "
            "qT/q is the tail dynamic-pressure ratio; "
            "both lift-curve slopes use the same angle unit; "
            "drag and propeller forces are omitted"
        ),
    )
    print_kv("a", args.a)
    print_kv("aT", args.at)
    print_kv("downwash", args.downwash)
    print_kv("qT_over_q", args.q_ratio)
    print_kv("tail_area_m2", args.tail_area)
    print_kv("tail_length_m", args.tail_length)
    print_kv("wing_area_m2", args.wing_area)
    print_kv("mac_m", args.mac)
    print_kv("cg_over_c", args.cg)
    print_kv("tail_volume", volume)
    print_kv("neutral_point_x0_over_c", neutral)
    print_kv("x_over_c", distance)
    print_kv("static_margin_percent", margin)
    print_kv("stability", stability(margin))
    return 0


if __name__ == "__main__":
    sys.exit(main())
