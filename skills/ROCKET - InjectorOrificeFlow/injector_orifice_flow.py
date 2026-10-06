#!/usr/bin/env python3
"""Injector orifice area, jet speed, and pressure drop.

injector_orifice_area is A = mdot / (Cd * (2*rho*dp)**0.5).
injector_jet_velocity is v = mdot / (rho * A).
injector_pressure_drop is dp = (mdot / (Cd*A))**2 / (2*rho).
dynamic_pressure is q = 0.5 * rho * v**2.
circular_orifice_diameter is d = (4*A / (N*pi))**0.5 when a count is given.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Injector orifice diameter"


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def orifice_area(mdot: float, rho: float, cd: float, dp: float) -> float:
    """A = mdot / (Cd * sqrt(2 * rho * dp))."""
    return mdot / (cd * math.sqrt(2.0 * rho * dp))


def jet_velocity(mdot: float, rho: float, area: float) -> float:
    """v = mdot / (rho * A)."""
    return mdot / (rho * area)


def pressure_drop(mdot: float, rho: float, cd: float, area: float) -> float:
    """dp = (mdot / (Cd * A))**2 / (2 * rho)."""
    return (mdot / (cd * area)) ** 2 / (2.0 * rho)


def dynamic_pressure(rho: float, velocity: float) -> float:
    """q = 0.5 * rho * v**2."""
    return 0.5 * rho * velocity**2


def orifice_diameter(area: float, count: float) -> float:
    """d = sqrt(4 * A / (N * pi))."""
    return math.sqrt(4.0 * area / (count * math.pi))


def solve(
    mdot: float,
    rho: float,
    cd: float,
    dp: float | None,
    velocity: float | None,
) -> dict[str, float]:
    if dp is not None:
        area = orifice_area(mdot, rho, cd, dp)
        speed = jet_velocity(mdot, rho, area)
        drop = dp
    else:
        assert velocity is not None
        area = mdot / (rho * velocity)
        speed = velocity
        drop = pressure_drop(mdot, rho, cd, area)
    return {
        "A_m2": area,
        "v_m_s": speed,
        "dp_Pa": drop,
        "q_jet_Pa": dynamic_pressure(rho, speed),
    }


def write_plot(area: float, out_path: Path, count: float | None) -> None:
    import matplotlib.pyplot as plt

    n_hi = 40
    if count is not None:
        n_hi = max(n_hi, int(math.ceil(count)))
    counts = list(range(1, n_hi + 1))
    diameters = [orifice_diameter(area, float(n)) for n in counts]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(counts, diameters, color="C0")
    if count is not None:
        ax.plot(count, orifice_diameter(area, count), "s", color="C3")
    ax.set_xlabel("Orifice count N")
    ax.set_ylabel("Orifice diameter d [m]")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def run_check() -> int:
    mdot = 2.0
    rho = 1000.0
    cd = 0.75
    dp = 3200000.0 / 9.0
    state = solve(mdot, rho, cd, dp, None)
    if abs(state["A_m2"] - 1.0e-4) > CHECK_TOL:
        print(f"CHECK FAIL: A = {state['A_m2']}", file=sys.stderr)
        return 1
    if abs(state["v_m_s"] - 20.0) > CHECK_TOL:
        print(f"CHECK FAIL: v = {state['v_m_s']}", file=sys.stderr)
        return 1
    if abs(state["q_jet_Pa"] - 200000.0) > CHECK_TOL:
        print(f"CHECK FAIL: q = {state['q_jet_Pa']}", file=sys.stderr)
        return 1
    back = solve(mdot, rho, cd, None, 20.0)
    if abs(back["dp_Pa"] - dp) > 1e-6:
        print(f"CHECK FAIL: dp from velocity = {back['dp_Pa']}", file=sys.stderr)
        return 1
    diameter = orifice_diameter(state["A_m2"], 4.0)
    expected_d = math.sqrt(1.0e-4 / math.pi)
    if abs(diameter - expected_d) > CHECK_TOL:
        print(f"CHECK FAIL: d = {diameter}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "orifice.png"
        write_plot(state["A_m2"], path, 4.0)
        if not path.is_file() or path.stat().st_size <= 0:
            print("CHECK FAIL: plot was not written", file=sys.stderr)
            return 1
    print("check: pass")
    print_kv("A_m2", state["A_m2"])
    print_kv("v_m_s", state["v_m_s"])
    print_kv("dp_Pa", state["dp_Pa"])
    print_kv("q_jet_Pa", state["q_jet_Pa"])
    print_kv("N", 4.0)
    print_kv("d_m", diameter)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Size injector orifices from mass flow, density, and Cd."
    )
    parser.add_argument("--mdot", type=float, default=None, help="mass flow [kg/s]")
    parser.add_argument("--rho", type=float, default=None, help="density [kg/m^3]")
    parser.add_argument("--cd", type=float, default=None, help="discharge coefficient")
    parser.add_argument("--dp", type=float, default=None, help="injector pressure drop [Pa]")
    parser.add_argument(
        "--velocity",
        type=float,
        default=None,
        help="mean geometric-area jet speed [m/s]",
    )
    parser.add_argument("--count", type=float, default=None, help="number of orifices")
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    missing = [
        flag
        for flag, value in (
            ("--mdot", args.mdot),
            ("--rho", args.rho),
            ("--cd", args.cd),
        )
        if value is None
    ]
    if missing:
        print(
            "error: requires --mdot, --rho, and --cd; " f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if (args.dp is None) == (args.velocity is None):
        print("error: pass exactly one of --dp or --velocity", file=sys.stderr)
        return 2
    supplied = [args.mdot, args.rho, args.cd]
    if args.dp is not None:
        supplied.append(args.dp)
    if args.velocity is not None:
        supplied.append(args.velocity)
    if args.count is not None:
        supplied.append(args.count)
    if any(not math.isfinite(value) for value in supplied):
        print("error: inputs must be finite", file=sys.stderr)
        return 2
    if args.mdot <= 0 or args.rho <= 0 or args.cd <= 0 or args.cd > 1:
        print("error: mdot, rho, and Cd must be > 0, and Cd must be <= 1", file=sys.stderr)
        return 2
    if args.dp is not None and args.dp <= 0:
        print("error: dp must be > 0 Pa", file=sys.stderr)
        return 2
    if args.velocity is not None and args.velocity <= 0:
        print("error: velocity must be > 0 m/s", file=sys.stderr)
        return 2
    if args.count is not None and args.count <= 0:
        print("error: count must be > 0", file=sys.stderr)
        return 2

    state = solve(args.mdot, args.rho, args.cd, args.dp, args.velocity)
    diameter = None if args.count is None else orifice_diameter(state["A_m2"], args.count)
    results = list(state.values())
    if diameter is not None:
        results.append(diameter)
    if any(not math.isfinite(value) for value in results):
        print("error: result is not finite", file=sys.stderr)
        return 2
    print_kv(
        "assumptions",
        (
            "steady incompressible orifice; "
            "mdot = Cd*A*sqrt(2*rho*dp); v = mdot/(rho*A); "
            "q = 0.5*rho*v**2; Cd is an input"
        ),
    )
    print_kv("mdot_kg_s", args.mdot)
    print_kv("rho_kg_m3", args.rho)
    print_kv("Cd", args.cd)
    for key in ("A_m2", "v_m_s", "dp_Pa", "q_jet_Pa"):
        print_kv(key, state[key])
    if args.count is not None:
        print_kv("N", args.count)
        print_kv("d_m", diameter)
    if args.cd < 0.5 or args.cd > 0.92:
        print_kv(
            "warning",
            "Cd is outside the 0.5 to 0.92 water-flow range quoted in SP-125",
        )
    if args.out:
        write_plot(state["A_m2"], Path(args.out), args.count)
        print_kv("graph", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
