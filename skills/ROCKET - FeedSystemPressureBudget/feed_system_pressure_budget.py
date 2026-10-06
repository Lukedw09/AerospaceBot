#!/usr/bin/env python3
"""Feed-system pressure budget for one or two propellant branches.

injector_manifold_pressure is pm = pc + dp_inj.
feed_supply_pressure is p_supply = pc + dp_inj + dp_extra + rho*g*h.
g0 = 9.80665 m/s^2 unless --g is set.
A positive height is a lift, so it raises the required supply pressure.
"""

from __future__ import annotations

import argparse
import math
import sys

CHECK_TOL = 1e-6
G0 = 9.80665


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def parse_drop(text: str) -> tuple[str, float]:
    if "=" not in text:
        raise argparse.ArgumentTypeError(f"{text!r} is not name=Pa")
    name, raw = text.split("=", 1)
    name = name.strip()
    if not name.isidentifier():
        raise argparse.ArgumentTypeError(f"drop name {name!r} is not an identifier")
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{text!r} pressure is not a number") from exc
    return name, value


def supply_pressure(
    pc: float,
    dp_inj: float,
    dp_extra: float,
    rho: float,
    height: float,
    g: float,
) -> tuple[float, float, float]:
    """Return manifold pressure, hydrostatic rise, and supply pressure."""
    manifold = pc + dp_inj
    head = rho * g * height
    return manifold, head, manifold + dp_extra + head


def run_check() -> int:
    manifold, head, supply = supply_pressure(2.0e6, 2.0e5, 5.0e4, 1000.0, 2.0, G0)
    expected = 2_250_000.0 + 1000.0 * G0 * 2.0
    if abs(manifold - 2.2e6) > CHECK_TOL:
        print(f"CHECK FAIL: manifold = {manifold}", file=sys.stderr)
        return 1
    if abs(head - 1000.0 * G0 * 2.0) > CHECK_TOL:
        print(f"CHECK FAIL: head = {head}", file=sys.stderr)
        return 1
    if abs(supply - expected) > CHECK_TOL:
        print(f"CHECK FAIL: supply = {supply}", file=sys.stderr)
        return 1
    ox = supply_pressure(2.0e6, 1.6e5, 1.0e4, 1140.0, 1.0, G0)[2]
    fuel = supply_pressure(2.0e6, 6.0e4, 1.0e4, 800.0, 1.0, G0)[2]
    if abs(max(ox, fuel) - ox) > CHECK_TOL:
        print("CHECK FAIL: MEOP should be the higher branch", file=sys.stderr)
        return 1
    print("check: pass")
    print_kv("p_manifold_Pa", manifold)
    print_kv("dp_head_Pa", head)
    print_kv("p_supply_Pa", supply)
    print_kv("meop_Pa", supply)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sum chamber pressure, injector drop, line drops, and head."
    )
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure [Pa]")
    parser.add_argument(
        "--dp-injector",
        type=float,
        default=None,
        help="injector pressure drop for one branch [Pa]",
    )
    parser.add_argument(
        "--dp-injector-ox",
        type=float,
        default=None,
        help="oxidizer injector pressure drop [Pa]",
    )
    parser.add_argument(
        "--dp-injector-fuel",
        type=float,
        default=None,
        help="fuel injector pressure drop [Pa]",
    )
    parser.add_argument(
        "--dp",
        action="append",
        type=parse_drop,
        default=None,
        help="named extra drop, name=Pa (repeatable)",
    )
    parser.add_argument("--rho", type=float, default=None, help="density for one branch [kg/m^3]")
    parser.add_argument("--rho-ox", type=float, default=None, help="oxidizer density [kg/m^3]")
    parser.add_argument("--rho-fuel", type=float, default=None, help="fuel density [kg/m^3]")
    parser.add_argument(
        "--height",
        type=float,
        default=None,
        help="lift from tank free surface to injector [m]",
    )
    parser.add_argument("--g", type=float, default=None, help="gravity [m/s^2]")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.pc is None:
        print("error: requires --pc", file=sys.stderr)
        return 2
    if not math.isfinite(args.pc):
        print("error: pc must be finite", file=sys.stderr)
        return 2
    if args.pc <= 0:
        print("error: pc must be > 0 Pa", file=sys.stderr)
        return 2

    pair = args.dp_injector_ox is not None or args.dp_injector_fuel is not None
    single = args.dp_injector is not None
    if pair and single:
        print(
            "error: pass --dp-injector or the ox/fuel pair, not both",
            file=sys.stderr,
        )
        return 2
    if pair and (args.dp_injector_ox is None or args.dp_injector_fuel is None):
        print(
            "error: --dp-injector-ox and --dp-injector-fuel are both required",
            file=sys.stderr,
        )
        return 2
    if not pair and not single:
        print(
            "error: pass --dp-injector or both --dp-injector-ox and --dp-injector-fuel",
            file=sys.stderr,
        )
        return 2

    drops = args.dp or []
    names = [name for name, _value in drops]
    if len(names) != len(set(names)):
        print("error: repeated --dp name", file=sys.stderr)
        return 2
    for name, value in drops:
        if not math.isfinite(value) or value < 0:
            print(f"error: drop {name} must be a finite number >= 0 Pa", file=sys.stderr)
            return 2
    dp_extra = sum(value for _name, value in drops)

    g = G0 if args.g is None else args.g
    if not math.isfinite(g) or g <= 0:
        print("error: g must be a finite number > 0 m/s^2", file=sys.stderr)
        return 2
    if args.height is not None and not math.isfinite(args.height):
        print("error: height must be finite", file=sys.stderr)
        return 2
    height = 0.0 if args.height is None else args.height

    def head_inputs(rho: float | None, label: str) -> tuple[float, float] | None:
        if args.height is None:
            if rho is not None:
                print(f"error: --{label} requires --height", file=sys.stderr)
                return None
            return 0.0, 0.0
        if rho is None:
            print(f"error: --height requires --{label}", file=sys.stderr)
            return None
        if not math.isfinite(rho) or rho <= 0:
            print(f"error: {label} must be > 0 kg/m^3", file=sys.stderr)
            return None
        return rho, height

    print_kv(
        "assumptions",
        (
            "steady branch budget; p_manifold = pc + dp_injector; "
            "p_supply = p_manifold + sum of named drops + rho*g*height; "
            "positive height is a lift; meop_Pa is p_supply for a pressure-fed tank; "
            "a pump-fed tank is not at this pressure"
        ),
    )
    print_kv("pc_Pa", args.pc)
    print_kv("g_m_s2", g)
    print_kv("dp_extra_Pa", dp_extra)
    for name, value in drops:
        print_kv(f"dp_{name}_Pa", value)

    supplies: list[float] = []
    if single:
        if not math.isfinite(args.dp_injector) or args.dp_injector < 0:
            print("error: dp-injector must be >= 0 Pa", file=sys.stderr)
            return 2
        if args.rho_ox is not None or args.rho_fuel is not None:
            print("error: --rho-ox and --rho-fuel are for the ox/fuel pair", file=sys.stderr)
            return 2
        headed = head_inputs(args.rho, "rho")
        if headed is None:
            return 2
        rho, h = headed
        manifold, head, supply = supply_pressure(
            args.pc, args.dp_injector, dp_extra, rho, h, g
        )
        if not all(math.isfinite(item) for item in (manifold, head, supply)):
            print("error: result is not finite", file=sys.stderr)
            return 2
        print_kv("dp_injector_Pa", args.dp_injector)
        if args.height is not None:
            print_kv("rho_kg_m3", rho)
            print_kv("height_m", h)
        print_kv("p_manifold_Pa", manifold)
        print_kv("dp_head_Pa", head)
        print_kv("p_supply_Pa", supply)
        supplies.append(supply)
    else:
        if args.rho is not None:
            print("error: use --rho-ox and --rho-fuel with the ox/fuel pair", file=sys.stderr)
            return 2
        assert args.dp_injector_ox is not None and args.dp_injector_fuel is not None
        for label, drop, rho in (
            ("ox", args.dp_injector_ox, args.rho_ox),
            ("fuel", args.dp_injector_fuel, args.rho_fuel),
        ):
            if not math.isfinite(drop) or drop < 0:
                print(f"error: dp-injector-{label} must be >= 0 Pa", file=sys.stderr)
                return 2
            headed = head_inputs(rho, f"rho-{label}")
            if headed is None:
                return 2
            rho_used, h = headed
            manifold, head, supply = supply_pressure(
                args.pc, drop, dp_extra, rho_used, h, g
            )
            if not all(math.isfinite(item) for item in (manifold, head, supply)):
                print("error: result is not finite", file=sys.stderr)
                return 2
            print_kv(f"dp_injector_{label}_Pa", drop)
            if args.height is not None:
                print_kv(f"rho_{label}_kg_m3", rho_used)
                print_kv(f"height_{label}_m", h)
            print_kv(f"p_manifold_{label}_Pa", manifold)
            print_kv(f"dp_head_{label}_Pa", head)
            print_kv(f"p_supply_{label}_Pa", supply)
            supplies.append(supply)

    print_kv("meop_Pa", max(supplies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
