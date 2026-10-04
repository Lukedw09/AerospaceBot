#!/usr/bin/env python3
"""Solid-motor burning-area ratio, equilibrium pressure, burn rate, and mass flow.

K comes from burning_area_ratio (formulas.md): K = Ab / At.
p1 comes from equilibrium_chamber_pressure:
    p1 = (K * a * rho_b * c*)**(1/(1 - n)).
r comes from burning_rate: r = a * p1**n.
mdot comes from solid_mass_flow: mdot = Ab * r * rho_b.
That mass flow also equals p1 * At / c* from characteristic_velocity.
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


def burning_area_ratio(ab: float, throat: float) -> float:
    """K = Ab / At."""
    return ab / throat


def equilibrium_chamber_pressure(
    k: float, a: float, rho_b: float, cstar: float, n: float
) -> float:
    """p1 = (K * a * rho_b * c*)**(1/(1 - n))."""
    return (k * a * rho_b * cstar) ** (1.0 / (1.0 - n))


def burn_rate(a: float, pc: float, n: float) -> float:
    """r = a * p1**n."""
    return a * pc**n


def solid_mass_flow(ab: float, r: float, rho_b: float) -> float:
    """mdot = Ab * r * rho_b."""
    return ab * r * rho_b


def nozzle_mass_flow(pc: float, throat: float, cstar: float) -> float:
    """mdot = p1 * At / c*."""
    return pc * throat / cstar


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def run_check() -> int:
    # burning_area_ratio identity: Ab = 2/5, At = 1/500, K = 200.
    ab_id = 2.0 / 5.0
    throat_id = 1.0 / 500.0
    k_id = burning_area_ratio(ab_id, throat_id)
    if not close(k_id, 200.0):
        return fail(f"CHECK FAIL: K = {k_id}, expected 200")

    # equilibrium_chamber_pressure identity: square_root_pressure.
    a_id = 1.0 / 100000.0
    rho_id = 1800.0
    cstar_id = 5000.0 / 9.0
    n_id = 0.5
    pc_id = equilibrium_chamber_pressure(k_id, a_id, rho_id, cstar_id, n_id)
    if not close(pc_id, 4000000.0):
        return fail(f"CHECK FAIL: pc = {pc_id}, expected 4000000")

    # burning_rate identity: square_root_pressure, r = 1/50.
    r_id = burn_rate(a_id, pc_id, n_id)
    if not close(r_id, 1.0 / 50.0):
        return fail(f"CHECK FAIL: r = {r_id}, expected {1.0 / 50.0}")

    # solid_mass_flow identity uses Ab = 1/5; keep Ab = 2/5 here and
    # check mass balance against the nozzle expression instead.
    mdot_grain = solid_mass_flow(ab_id, r_id, rho_id)
    mdot_nozzle = nozzle_mass_flow(pc_id, throat_id, cstar_id)
    if not close(mdot_grain, mdot_nozzle):
        return fail("CHECK FAIL: Ab*r*rho_b does not match pc*At/c*")
    if not close(mdot_grain, 14.4):
        return fail(f"CHECK FAIL: mdot = {mdot_grain}, expected 14.4")

    # solid_mass_flow identity: steady_regression.
    mdot_smf = solid_mass_flow(1.0 / 5.0, 1.0 / 200.0, 1800.0)
    if not close(mdot_smf, 9.0 / 5.0):
        return fail(f"CHECK FAIL: solid_mass_flow = {mdot_smf}, expected 1.8")

    print("check: pass")
    print_kv("K", k_id)
    print_kv("pc_Pa", pc_id)
    print_kv("r_m_s", r_id)
    print_kv("mdot_kg_s", mdot_grain)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Solid-motor burning-area ratio, equilibrium chamber pressure, "
            "burn rate, and mass flow."
        )
    )
    parser.add_argument(
        "--a",
        type=float,
        default=None,
        help="burn-rate coefficient a [m/(s·Pa^n)]",
    )
    parser.add_argument(
        "--n",
        type=float,
        default=None,
        help="burn-rate pressure exponent n",
    )
    parser.add_argument(
        "--ab",
        type=float,
        default=None,
        help="burning surface area Ab [m^2]",
    )
    parser.add_argument(
        "--throat",
        type=float,
        default=None,
        help="throat area At [m^2]",
    )
    parser.add_argument(
        "--rho",
        type=float,
        default=None,
        help="solid propellant density rho_b [kg/m^3]",
    )
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
        "--a": args.a,
        "--n": args.n,
        "--ab": args.ab,
        "--throat": args.throat,
        "--rho": args.rho,
        "--cstar": args.cstar,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --a, --n, --ab, --throat, --rho, and --cstar; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    limits = {
        "--a": "burn-rate coefficient must be > 0",
        "--ab": "burning area must be > 0 m^2",
        "--throat": "throat area must be > 0 m^2",
        "--rho": "propellant density must be > 0 kg/m^3",
        "--cstar": "c* must be > 0 m/s",
    }
    for flag, message in limits.items():
        if supplied[flag] <= 0:
            print(f"error: {message}", file=sys.stderr)
            return 2

    if args.n >= 1.0:
        print(
            "error: burn-rate exponent n must be < 1 for a stable equilibrium",
            file=sys.stderr,
        )
        return 2

    k = burning_area_ratio(args.ab, args.throat)
    pc = equilibrium_chamber_pressure(k, args.a, args.rho, args.cstar, args.n)
    r = burn_rate(args.a, pc, args.n)
    mdot = solid_mass_flow(args.ab, r, args.rho)
    mdot_noz = nozzle_mass_flow(pc, args.throat, args.cstar)
    if not close(mdot, mdot_noz):
        print(
            "error: mass balance failed: Ab*r*rho_b does not match pc*At/c*",
            file=sys.stderr,
        )
        return 1

    print_kv(
        "assumptions",
        (
            "quasi-steady solid-motor mass balance; "
            "K = Ab/At; r = a*pc**n; "
            "pc = (K*a*rho_b*c*)**(1/(1-n)); "
            "mdot = Ab*r*rho_b = pc*At/c*; "
            "constant a, n, rho_b, and c*; no erosive burning; n < 1"
        ),
    )
    print_kv("a", args.a)
    print_kv("n", args.n)
    print_kv("Ab_m2", args.ab)
    print_kv("At_m2", args.throat)
    print_kv("rho_b_kg_m3", args.rho)
    print_kv("cstar_m_s", args.cstar)
    print_kv("K", k)
    print_kv("pc_Pa", pc)
    print_kv("r_m_s", r)
    print_kv("mdot_kg_s", mdot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
