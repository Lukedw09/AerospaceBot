#!/usr/bin/env python3
"""Breguet cruise range and endurance for jet and propeller airplanes.

Jet range is breguet_range_jet. Jet endurance is breguet_endurance_jet.
Propeller range is breguet_range_prop. Propeller endurance is
breguet_endurance_prop. Sources: Guynn (NASA Langley), NASA TN D-6707,
and NACA Report 234, as recorded in formulas.md.
"""

from __future__ import annotations

import argparse
import math
import sys

CHECK_TOL = 1e-9

ASSUMPTIONS = (
    "steady cruise with L = W and T = D; constant V, L/D, and specific fuel "
    "consumption over the segment; natural logarithm of Wi/Wf; "
    "jet fuel flow follows thrust: ct is weight-based TSFC in 1/s from "
    "breguet_range_jet and breguet_endurance_jet; "
    "propeller fuel flow follows shaft power: c is weight-based power SFC "
    "in 1/m and eta is propeller efficiency from breguet_range_prop and "
    "breguet_endurance_prop; "
    "Wi and Wf are cruise start and end weights with Wi > Wf > 0; "
    "0 < eta <= 1; climb, descent, reserves, and wind are omitted"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= CHECK_TOL * scale


def weight_log(wi: float, wf: float) -> float:
    return math.log(wi / wf)


def breguet_range_jet(speed: float, ct: float, ld: float, wi: float, wf: float) -> float:
    """breguet_range_jet: R = (V/ct)*(L/D)*ln(Wi/Wf)."""
    return (speed / ct) * ld * weight_log(wi, wf)


def breguet_endurance_jet(ct: float, ld: float, wi: float, wf: float) -> float:
    """breguet_endurance_jet: E = (1/ct)*(L/D)*ln(Wi/Wf)."""
    return (1.0 / ct) * ld * weight_log(wi, wf)


def breguet_range_prop(eta: float, c: float, ld: float, wi: float, wf: float) -> float:
    """breguet_range_prop: R = (eta/c)*(L/D)*ln(Wi/Wf)."""
    return (eta / c) * ld * weight_log(wi, wf)


def breguet_endurance_prop(
    eta: float, c: float, speed: float, ld: float, wi: float, wf: float
) -> float:
    """breguet_endurance_prop: E = (eta/(c*V))*(L/D)*ln(Wi/Wf)."""
    return (eta / (c * speed)) * ld * weight_log(wi, wf)


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def run_check() -> int:
    # identities.md weight_ratio_two samples.
    if not close(breguet_range_jet(1.0, 1.0, 1.0, 2.0, 1.0), math.log(2.0)):
        return fail("CHECK FAIL: jet range at weight ratio two is not ln(2)")
    if not close(breguet_endurance_jet(1.0, 1.0, 2.0, 1.0), math.log(2.0)):
        return fail("CHECK FAIL: jet endurance at weight ratio two is not ln(2)")
    if not close(breguet_range_prop(1.0, 1.0, 1.0, 2.0, 1.0), math.log(2.0)):
        return fail("CHECK FAIL: propeller range at weight ratio two is not ln(2)")
    if not close(breguet_endurance_prop(1.0, 1.0, 2.0, 1.0, 2.0, 1.0), math.log(2.0) / 2.0):
        return fail("CHECK FAIL: propeller endurance at weight ratio two is not ln(2)/2")

    # Jet endurance times speed is jet range. Prop endurance times speed is prop range.
    speed = 250.0
    ct = 2.0e-5
    ld = 16.0
    wi = 1.0e5
    wf = 8.0e4
    eta = 0.85
    c = 1.0e-7
    r_jet = breguet_range_jet(speed, ct, ld, wi, wf)
    e_jet = breguet_endurance_jet(ct, ld, wi, wf)
    r_prop = breguet_range_prop(eta, c, ld, wi, wf)
    e_prop = breguet_endurance_prop(eta, c, speed, ld, wi, wf)
    if not close(r_jet, e_jet * speed):
        return fail("CHECK FAIL: jet range is not endurance times speed")
    if not close(r_prop, e_prop * speed):
        return fail("CHECK FAIL: propeller range is not endurance times speed")
    if r_jet <= 0.0 or e_jet <= 0.0 or r_prop <= 0.0 or e_prop <= 0.0:
        return fail("CHECK FAIL: a cruise result was not positive")

    print("check: pass")
    print_kv("R_jet_m", r_jet)
    print_kv("E_jet_s", e_jet)
    print_kv("R_prop_m", r_prop)
    print_kv("E_prop_s", e_prop)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Breguet cruise range and endurance for jet and propeller airplanes "
            "from L/D, specific fuel consumption, cruise speed, and start/end weight."
        )
    )
    parser.add_argument("--ld", type=float, default=None, help="lift-to-drag ratio L/D")
    parser.add_argument("--wi", type=float, default=None, help="weight at start of cruise Wi [N]")
    parser.add_argument("--wf", type=float, default=None, help="weight at end of cruise Wf [N]")
    parser.add_argument("--speed", type=float, default=None, help="true airspeed V [m/s]")
    parser.add_argument(
        "--ct",
        type=float,
        default=None,
        help="weight-based thrust-specific fuel consumption ct [1/s]",
    )
    parser.add_argument(
        "--c",
        type=float,
        default=None,
        help="weight-based power-specific fuel consumption c [1/m]",
    )
    parser.add_argument("--eta", type=float, default=None, help="propeller efficiency eta")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--ld": args.ld,
        "--wi": args.wi,
        "--wf": args.wf,
        "--speed": args.speed,
        "--ct": args.ct,
        "--c": args.c,
        "--eta": args.eta,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --ld, --wi, --wf, --speed, --ct, --c, and --eta; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    if args.ld <= 0.0:
        print("error: L/D must be > 0", file=sys.stderr)
        return 2
    if args.wi <= 0.0:
        print("error: start weight must be > 0 N", file=sys.stderr)
        return 2
    if args.wf <= 0.0:
        print("error: end weight must be > 0 N", file=sys.stderr)
        return 2
    if args.wi <= args.wf:
        print("error: start weight must be greater than end weight", file=sys.stderr)
        return 2
    if args.speed <= 0.0:
        print("error: speed must be > 0 m/s", file=sys.stderr)
        return 2
    if args.ct <= 0.0:
        print("error: thrust-specific fuel consumption must be > 0 1/s", file=sys.stderr)
        return 2
    if args.c <= 0.0:
        print("error: power-specific fuel consumption must be > 0 1/m", file=sys.stderr)
        return 2
    if not (0.0 < args.eta <= 1.0):
        print("error: propeller efficiency must satisfy 0 < eta <= 1", file=sys.stderr)
        return 2

    r_jet = breguet_range_jet(args.speed, args.ct, args.ld, args.wi, args.wf)
    e_jet = breguet_endurance_jet(args.ct, args.ld, args.wi, args.wf)
    r_prop = breguet_range_prop(args.eta, args.c, args.ld, args.wi, args.wf)
    e_prop = breguet_endurance_prop(args.eta, args.c, args.speed, args.ld, args.wi, args.wf)

    print_kv("assumptions", ASSUMPTIONS)
    print_kv("LD", args.ld)
    print_kv("Wi_N", args.wi)
    print_kv("Wf_N", args.wf)
    print_kv("weight_ratio", args.wi / args.wf)
    print_kv("ln_Wi_over_Wf", weight_log(args.wi, args.wf))
    print_kv("V_m_s", args.speed)
    print_kv("ct_1_s", args.ct)
    print_kv("c_1_m", args.c)
    print_kv("eta", args.eta)
    print_kv("R_jet_m", r_jet)
    print_kv("E_jet_s", e_jet)
    print_kv("R_prop_m", r_prop)
    print_kv("E_prop_s", e_prop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
