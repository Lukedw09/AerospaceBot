#!/usr/bin/env python3
"""Propellant mass and tank volume from mass flow, burn time, and mixture ratio.

Densities come from the user, or from ROCKET - PerformanceParameters pairs.json.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CHECK_TOL = 1e-9

PERF_SRC = Path(__file__).resolve().parent.parent / "ROCKET - PerformanceParameters" / "src"
if str(PERF_SRC) not in sys.path:
    sys.path.insert(0, str(PERF_SRC))

from load_table import TableError, pair_spec  # noqa: E402


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def bulk_density(r: float, rho_ox: float, rho_fuel: float) -> float:
    """rho_av = rho_o * rho_f * (r + 1) / (r * rho_f + rho_o)."""
    return rho_ox * rho_fuel * (r + 1.0) / (r * rho_fuel + rho_ox)


def fuel_flow(mdot: float, r: float) -> float:
    """mdot_f = mdot / (r + 1)."""
    return mdot / (r + 1.0)


def oxidizer_flow(mdot: float, r: float) -> float:
    """mdot_o = r * mdot / (r + 1)."""
    return r * mdot / (r + 1.0)


def load_pair_densities(pair: str) -> tuple[float, float, float, float, str]:
    spec = pair_spec(pair)
    return (
        spec.rho_ox_kg_m3,
        spec.rho_ox_T_K,
        spec.rho_fuel_kg_m3,
        spec.rho_fuel_T_K,
        spec.pair,
    )


def run_check() -> int:
    mdot = 4.0
    tb = 10.0
    r = 3.0
    rho_ox = 1000.0
    rho_fuel = 200.0
    mdot_f = fuel_flow(mdot, r)
    mdot_o = oxidizer_flow(mdot, r)
    m_p = mdot * tb
    m_ox = mdot_o * tb
    m_fuel = mdot_f * tb
    rho_b = bulk_density(r, rho_ox, rho_fuel)
    v_ox = m_ox / rho_ox
    v_fuel = m_fuel / rho_fuel
    v_p = v_ox + v_fuel
    expected = {
        "mdot_f": 1.0,
        "mdot_o": 3.0,
        "m_p": 40.0,
        "m_ox": 30.0,
        "m_fuel": 10.0,
        "rho_b": 500.0,
        "v_ox": 0.03,
        "v_fuel": 0.05,
        "v_p": 0.08,
    }
    got = {
        "mdot_f": mdot_f,
        "mdot_o": mdot_o,
        "m_p": m_p,
        "m_ox": m_ox,
        "m_fuel": m_fuel,
        "rho_b": rho_b,
        "v_ox": v_ox,
        "v_fuel": v_fuel,
        "v_p": v_p,
    }
    for name, want in expected.items():
        if abs(got[name] - want) > CHECK_TOL:
            print(f"CHECK FAIL: {name} = {got[name]}, expected {want}", file=sys.stderr)
            return 1
    if abs(v_p - m_p / rho_b) > CHECK_TOL:
        print("CHECK FAIL: V_p is not m_p / rho_av", file=sys.stderr)
        return 1
    if abs(mdot_o + mdot_f - mdot) > CHECK_TOL:
        print("CHECK FAIL: mdot_o + mdot_f is not mdot", file=sys.stderr)
        return 1

    try:
        rho_ox_p, t_ox, rho_fuel_p, t_fuel, pair = load_pair_densities("LOX/RP1")
    except TableError as exc:
        print(f"CHECK FAIL: pair lookup: {exc}", file=sys.stderr)
        return 1
    if abs(rho_ox_p - 1141.0) > CHECK_TOL or abs(rho_fuel_p - 810.0) > CHECK_TOL:
        print(
            f"CHECK FAIL: LOX/RP1 densities = {rho_ox_p}, {rho_fuel_p}",
            file=sys.stderr,
        )
        return 1
    if abs(t_ox - 90.0) > CHECK_TOL or abs(t_fuel - 288.0) > CHECK_TOL:
        print(f"CHECK FAIL: LOX/RP1 temperatures = {t_ox}, {t_fuel}", file=sys.stderr)
        return 1
    if pair != "LOX/RP1":
        print(f"CHECK FAIL: pair = {pair!r}, expected 'LOX/RP1'", file=sys.stderr)
        return 1
    try:
        alias = load_pair_densities("LOX/RP-1")
        hydrazine = load_pair_densities("N2O4/hydrazine")
        aerozine = load_pair_densities("NTO/Aerozine-50")
    except TableError as exc:
        print(f"CHECK FAIL: alias lookup: {exc}", file=sys.stderr)
        return 1
    if alias[4] != "LOX/RP1" or abs(alias[0] - 1141.0) > CHECK_TOL:
        print(f"CHECK FAIL: LOX/RP-1 resolved to {alias}", file=sys.stderr)
        return 1
    if hydrazine[4] != "N2O4/N2H4" or abs(hydrazine[2] - 1008.0) > CHECK_TOL:
        print(f"CHECK FAIL: hydrazine resolved to {hydrazine}", file=sys.stderr)
        return 1
    if aerozine[4] != "N2O4/A50" or abs(aerozine[2] - 899.0) > CHECK_TOL:
        print(f"CHECK FAIL: Aerozine-50 resolved to {aerozine}", file=sys.stderr)
        return 1

    print("check: pass")
    print_kv("m_p_kg", m_p)
    print_kv("m_ox_kg", m_ox)
    print_kv("m_fuel_kg", m_fuel)
    print_kv("V_p_m3", v_p)
    print_kv("V_ox_m3", v_ox)
    print_kv("V_fuel_m3", v_fuel)
    print_kv("rho_b_kg_m3", rho_b)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Propellant mass and volume from mass flow, burn time, and mixture ratio."
    )
    parser.add_argument("--mdot", type=float, default=None, help="total propellant mass flow [kg/s]")
    parser.add_argument("--tb", type=float, default=None, help="burn time [s]")
    parser.add_argument("--r", type=float, default=None, help="mixture ratio ox/fuel")
    parser.add_argument("--pair", type=str, default=None, help="oxName/fuelName; densities from pairs.json")
    parser.add_argument("--rho-ox", type=float, default=None, help="oxidizer density [kg/m^3]")
    parser.add_argument("--rho-fuel", type=float, default=None, help="fuel density [kg/m^3]")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--mdot": args.mdot,
        "--tb": args.tb,
        "--r": args.r,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --mdot, --tb, and --r; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    if args.mdot <= 0:
        print("error: mass flow must be > 0 kg/s", file=sys.stderr)
        return 2
    if args.tb <= 0:
        print("error: burn time must be > 0 s", file=sys.stderr)
        return 2
    if args.r <= 0:
        print("error: mixture ratio must be > 0", file=sys.stderr)
        return 2

    user_ox = args.rho_ox is not None
    user_fuel = args.rho_fuel is not None
    if user_ox != user_fuel:
        print("error: --rho-ox and --rho-fuel must be given together", file=sys.stderr)
        return 2
    if user_ox and (args.rho_ox <= 0 or args.rho_fuel <= 0):
        print("error: densities must be > 0 kg/m^3", file=sys.stderr)
        return 2
    if not user_ox and not args.pair:
        print(
            "error: densities require --rho-ox and --rho-fuel, or --pair "
            "from ROCKET - PerformanceParameters",
            file=sys.stderr,
        )
        return 2

    t_ox = None
    t_fuel = None
    pair_name = None
    if user_ox:
        rho_ox = args.rho_ox
        rho_fuel = args.rho_fuel
        density_source = "user"
        if args.pair:
            try:
                pair_name = pair_spec(args.pair).pair
            except TableError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
    else:
        try:
            rho_ox, t_ox, rho_fuel, t_fuel, pair_name = load_pair_densities(args.pair)
        except TableError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        density_source = "pairs.json"

    mdot_f = fuel_flow(args.mdot, args.r)
    mdot_o = oxidizer_flow(args.mdot, args.r)
    m_p = args.mdot * args.tb
    m_ox = mdot_o * args.tb
    m_fuel = mdot_f * args.tb
    rho_b = bulk_density(args.r, rho_ox, rho_fuel)
    v_ox = m_ox / rho_ox
    v_fuel = m_fuel / rho_fuel
    v_p = v_ox + v_fuel

    print_kv(
        "assumptions",
        (
            "steady liquid-propellant flow; constant mdot during tb; "
            "r = mdot_o/mdot_f; m = mdot*tb; V = m/rho; "
            "rho_av = rho_o*rho_f*(r+1)/(r*rho_f+rho_o); "
            "listed pair densities are liquid storage values"
        ),
    )
    print_kv("mdot_kg_s", args.mdot)
    print_kv("tb_s", args.tb)
    print_kv("r", args.r)
    if pair_name:
        print_kv("pair", pair_name)
    print_kv("density_source", density_source)
    print_kv("rho_ox_kg_m3", rho_ox)
    if t_ox is not None:
        print_kv("rho_ox_T_K", t_ox)
    print_kv("rho_fuel_kg_m3", rho_fuel)
    if t_fuel is not None:
        print_kv("rho_fuel_T_K", t_fuel)
    print_kv("rho_b_kg_m3", rho_b)
    print_kv("mdot_o_kg_s", mdot_o)
    print_kv("mdot_f_kg_s", mdot_f)
    print_kv("m_p_kg", m_p)
    print_kv("m_ox_kg", m_ox)
    print_kv("m_fuel_kg", m_fuel)
    print_kv("V_p_m3", v_p)
    print_kv("V_ox_m3", v_ox)
    print_kv("V_fuel_m3", v_fuel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
