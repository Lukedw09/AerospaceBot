#!/usr/bin/env python3
"""Freestream Mach and dynamic pressure from a pitot measurement.

Below Mach 1 the measured pitot pressure is the isentropic stagnation
pressure from stagnation_temperature and stagnation_pressure. Above Mach 1
a normal shock stands ahead of the probe and the measured value is the
stagnation pressure behind that shock from rayleigh_pitot. Dynamic pressure
uses q = (gamma/2)*p*M**2 from dynamic_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys

CHECK_TOL = 1e-9
DEFAULT_GAMMA = 1.4
MACH_MAX = 1.0e6
SONIC_TOL = 1e-12

ASSUMPTIONS = (
    "calorically perfect gas; steady freestream; "
    "measured pitot pressure is the stagnation pressure recovered by the "
    "probe; below Mach 1 that pressure is isentropic stagnation from "
    "stagnation_temperature and stagnation_pressure, "
    "pt/p = (1 + ((gamma-1)/2)*M**2)**(gamma/(gamma-1)); "
    "above Mach 1 a normal shock stands ahead of the probe and the measured "
    "pressure is pt2 from rayleigh_pitot; "
    "the sonic pressure ratio "
    "((gamma+1)/2)**(gamma/(gamma-1)) selects the branch; "
    "dynamic pressure is dynamic_pressure as q = (gamma/2)*p*M**2; "
    "probe geometry, viscous loss, and thermal imperfect-gas effects are omitted"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def sonic_pressure_ratio(gamma: float) -> float:
    """Isentropic pt/p at M = 1. Also rayleigh_pitot at M1 = 1."""
    return ((gamma + 1.0) / 2.0) ** (gamma / (gamma - 1.0))


def isentropic_stagnation_ratio(mach: float, gamma: float) -> float:
    """pt/p from stagnation_temperature and stagnation_pressure."""
    temperature_ratio = 1.0 + 0.5 * (gamma - 1.0) * mach * mach
    return temperature_ratio ** (gamma / (gamma - 1.0))


def rayleigh_pitot_ratio(mach: float, gamma: float) -> float:
    """pt2/p1 from rayleigh_pitot. Upstream Mach must be at least 1."""
    return (
        (((gamma + 1.0) / 2.0) * mach * mach) ** (gamma / (gamma - 1.0))
        * ((gamma + 1.0) / (2.0 * gamma * mach * mach - (gamma - 1.0)))
        ** (1.0 / (gamma - 1.0))
    )


def mach_from_isentropic(ratio: float, gamma: float) -> float:
    """Inverse of isentropic_stagnation_ratio for 1 <= pt/p <= sonic ratio."""
    if ratio < 1.0:
        raise ValueError("pitot pressure must be at least freestream static pressure")
    exponent = (gamma - 1.0) / gamma
    mach_sq = (2.0 / (gamma - 1.0)) * (ratio**exponent - 1.0)
    if mach_sq < 0.0 and abs(mach_sq) <= 1e-15:
        mach_sq = 0.0
    if mach_sq < 0.0 or not math.isfinite(mach_sq):
        raise ValueError("pressure ratio does not give a real subsonic Mach number")
    return math.sqrt(mach_sq)


def mach_from_rayleigh_pitot(ratio: float, gamma: float) -> float:
    """Inverse of rayleigh_pitot_ratio for pt2/p1 above the sonic ratio."""
    sonic = sonic_pressure_ratio(gamma)
    if ratio < sonic - 1e-14:
        raise ValueError("pressure ratio is below the sonic Rayleigh-Pitot value")
    if abs(ratio - sonic) <= 1e-14:
        return 1.0

    lo = 1.0
    hi = 2.0
    while rayleigh_pitot_ratio(hi, gamma) < ratio:
        hi *= 2.0
        if hi > MACH_MAX:
            raise ValueError("could not bracket a Mach number for the pitot ratio")

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if rayleigh_pitot_ratio(mid, gamma) < ratio:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def dynamic_pressure(pressure: float, mach: float, gamma: float) -> float:
    """dynamic_pressure as q = (gamma/2)*p*M**2."""
    return 0.5 * gamma * pressure * mach * mach


def pitot_state(pitot: float, static: float, gamma: float) -> dict[str, float | str]:
    if not math.isfinite(pitot) or not math.isfinite(static) or not math.isfinite(gamma):
        raise ValueError("pitot, static, and gamma must be finite")
    if pitot <= 0.0:
        raise ValueError("pitot pressure must be > 0 Pa")
    if static <= 0.0:
        raise ValueError("freestream static pressure must be > 0 Pa")
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if pitot < static:
        raise ValueError("pitot pressure must be at least freestream static pressure")

    ratio = pitot / static
    sonic = sonic_pressure_ratio(gamma)
    if ratio <= sonic + SONIC_TOL:
        mach = mach_from_isentropic(ratio, gamma)
        if mach > 1.0 and abs(mach - 1.0) <= 1e-12:
            mach = 1.0
        if mach > 1.0:
            raise ValueError("isentropic branch returned a Mach number above 1")
        branch = "sonic" if abs(mach - 1.0) <= 1e-12 else "subsonic"
        relation = "isentropic_stagnation"
    else:
        mach = mach_from_rayleigh_pitot(ratio, gamma)
        branch = "supersonic"
        relation = "rayleigh_pitot"

    return {
        "pitot": pitot,
        "static": static,
        "gamma": gamma,
        "ratio": ratio,
        "sonic_ratio": sonic,
        "branch": branch,
        "relation": relation,
        "M": mach,
        "q": dynamic_pressure(static, mach, gamma),
    }


def emit(result: dict[str, float | str], gamma_source: str) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("pitot_Pa", result["pitot"])
    print_kv("static_Pa", result["static"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("pitot_over_static", result["ratio"])
    print_kv("sonic_pitot_over_static", result["sonic_ratio"])
    print_kv("branch", result["branch"])
    print_kv("relation", result["relation"])
    print_kv("M", result["M"])
    print_kv("q_Pa", result["q"])


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    gamma = 7.0 / 5.0

    # Isentropic air at M = 0: pt/p = 1.
    if not close(isentropic_stagnation_ratio(0.0, gamma), 1.0):
        return fail("reservoir stagnation ratio is not 1")

    # Isentropic air at M = 1 equals the sonic Rayleigh-Pitot value.
    sonic = sonic_pressure_ratio(gamma)
    if not close(isentropic_stagnation_ratio(1.0, gamma), sonic):
        return fail("isentropic M=1 does not match the sonic pressure ratio")
    if not close(rayleigh_pitot_ratio(1.0, gamma), sonic):
        return fail("rayleigh_pitot at M=1 does not match the sonic pressure ratio")

    # stagnation_pressure_air identity path: M = 1/2.
    half = isentropic_stagnation_ratio(0.5, gamma)
    expected_half = (1.0 + (0.5**2) / 5.0) ** (7.0 / 2.0)
    if not close(half, expected_half):
        return fail(f"subsonic air ratio = {half}, expected {expected_half}")
    mach_half = mach_from_isentropic(half, gamma)
    if not close(mach_half, 0.5):
        return fail(f"subsonic inverse returned {mach_half}, expected 0.5")

    # rayleigh_pitot identity air_mach_two.
    ratio_two = rayleigh_pitot_ratio(2.0, gamma)
    expected_two = (24.0 / 5.0) ** (7.0 / 2.0) * (2.0 / 9.0) ** (5.0 / 2.0)
    if not close(ratio_two, expected_two):
        return fail(f"air Mach 2 Rayleigh-Pitot = {ratio_two}, expected {expected_two}")
    mach_two = mach_from_rayleigh_pitot(ratio_two, gamma)
    if not close(mach_two, 2.0):
        return fail(f"supersonic inverse returned {mach_two}, expected 2")

    # Full state: subsonic branch.
    static = 101325.0
    sub = pitot_state(half * static, static, gamma)
    if sub["branch"] != "subsonic" or sub["relation"] != "isentropic_stagnation":
        return fail(f"half-Mach branch was {sub['branch']} / {sub['relation']}")
    if not close(float(sub["M"]), 0.5):
        return fail(f"half-Mach state M = {sub['M']}")
    q_half = float(sub["q"])
    if not close(q_half, 0.5 * gamma * static * 0.25):
        return fail(f"half-Mach dynamic pressure = {q_half}")
    # dynamic_pressure_air: q/p = (7/10)*M**2.
    if not close(q_half / static, (7.0 / 10.0) * 0.25):
        return fail("half-Mach q/p is not dynamic_pressure_air")

    # Full state: sonic branch.
    sonic_state = pitot_state(sonic * static, static, gamma)
    if sonic_state["branch"] != "sonic":
        return fail(f"sonic branch was {sonic_state['branch']}")
    if not close(float(sonic_state["M"]), 1.0):
        return fail(f"sonic Mach = {sonic_state['M']}")

    # Full state: supersonic branch.
    super_state = pitot_state(ratio_two * static, static, gamma)
    if super_state["branch"] != "supersonic" or super_state["relation"] != "rayleigh_pitot":
        return fail(
            f"Mach-2 branch was {super_state['branch']} / {super_state['relation']}"
        )
    if not close(float(super_state["M"]), 2.0):
        return fail(f"Mach-2 state M = {super_state['M']}")
    q_two = float(super_state["q"])
    if not close(q_two, 0.5 * gamma * static * 4.0):
        return fail(f"Mach-2 dynamic pressure = {q_two}")
    if not close(q_two / static, (7.0 / 10.0) * 4.0):
        return fail("Mach-2 q/p is not dynamic_pressure_air")

    # Reject a pitot below static.
    try:
        pitot_state(0.9 * static, static, gamma)
        return fail("pitot below static did not raise")
    except ValueError:
        pass

    print("check: pass")
    print_kv("sonic_pitot_over_static", sonic)
    print_kv("subsonic_M", 0.5)
    print_kv("subsonic_pitot_over_static", half)
    print_kv("supersonic_M", 2.0)
    print_kv("supersonic_pitot_over_static", ratio_two)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freestream Mach number and dynamic pressure from measured pitot "
            "pressure, freestream static pressure, and gamma."
        )
    )
    parser.add_argument("--pitot", type=float, default=None, help="measured pitot pressure [Pa]")
    parser.add_argument(
        "--static",
        type=float,
        default=None,
        help="freestream static pressure [Pa]",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    missing = [
        flag
        for flag, value in (("--pitot", args.pitot), ("--static", args.static))
        if value is None
    ]
    if missing:
        print(
            "error: requires --pitot and --static; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    if args.gamma is None:
        gamma = DEFAULT_GAMMA
        gamma_source = "default"
    else:
        gamma = args.gamma
        gamma_source = "flag"

    try:
        result = pitot_state(args.pitot, args.static, gamma)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, gamma_source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
