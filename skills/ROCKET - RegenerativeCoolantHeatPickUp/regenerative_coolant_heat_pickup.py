#!/usr/bin/env python3
"""Regenerative coolant outlet temperature and minimum flow.

coolant_outlet_temperature is Tout = Tin + Q / (mdot * cp).
coolant_capacity is Qc = mdot * cp * (Tmax - Tin).
coolant_min_flow is mdot_min = Q / (cp * (Tmax - Tin)).
Heat rate is --q-dot, or --flux times --area.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Coolant outlet temperature"


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def outlet_temperature(tin: float, heat: float, mdot: float, cp: float) -> float:
    return tin + heat / (mdot * cp)


def min_flow(heat: float, cp: float, tmax: float, tin: float) -> float:
    return heat / (cp * (tmax - tin))


def write_plot(
    tin: float,
    heat: float,
    mdot: float,
    cp: float,
    tmax: float | None,
    out_path: Path,
) -> None:
    import matplotlib.pyplot as plt

    flows = [mdot * (0.25 + 2.75 * i / 40.0) for i in range(41)]
    outlets = [outlet_temperature(tin, heat, item, cp) for item in flows]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(flows, outlets, color="C0")
    ax.plot(mdot, outlet_temperature(tin, heat, mdot, cp), "s", color="C3")
    if tmax is not None:
        ax.axhline(tmax, color="0.45", linestyle="--", linewidth=0.9)
    ax.set_xlabel("Coolant mass flow [kg/s]")
    ax.set_ylabel("Outlet temperature [K]")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def run_check() -> int:
    heat = 1.0e6 * 0.4
    tout = outlet_temperature(300.0, heat, 2.0, 2000.0)
    if abs(heat - 400000.0) > CHECK_TOL or abs(tout - 400.0) > CHECK_TOL:
        print(f"CHECK FAIL: Q = {heat}, Tout = {tout}", file=sys.stderr)
        return 1
    needed = min_flow(heat, 2000.0, 450.0, 300.0)
    if abs(needed - 4.0 / 3.0) > CHECK_TOL:
        print(f"CHECK FAIL: mdot_min = {needed}", file=sys.stderr)
        return 1
    if tout > 450.0:
        print("CHECK FAIL: limit should pass", file=sys.stderr)
        return 1
    if not (tout > 350.0):
        print("CHECK FAIL: limit should fail at 350 K", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "coolant.png"
        write_plot(300.0, heat, 2.0, 2000.0, 450.0, path)
        if not path.is_file() or path.stat().st_size <= 0:
            print("CHECK FAIL: plot was not written", file=sys.stderr)
            return 1
    print("check: pass")
    print_kv("Q_W", heat)
    print_kv("T_out_K", tout)
    print_kv("dT_K", tout - 300.0)
    print_kv("limit", "pass")
    print_kv("mdot_min_kg_s", needed)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coolant outlet temperature from an absorbed heat rate."
    )
    parser.add_argument("--mdot", type=float, default=None, help="coolant mass flow [kg/s]")
    parser.add_argument("--cp", type=float, default=None, help="coolant specific heat [J/(kg·K)]")
    parser.add_argument("--t-in", type=float, default=None, help="coolant inlet temperature [K]")
    parser.add_argument("--q-dot", type=float, default=None, help="absorbed heat rate [W]")
    parser.add_argument("--flux", type=float, default=None, help="heat flux [W/m^2]")
    parser.add_argument("--area", type=float, default=None, help="cooled area [m^2]")
    parser.add_argument("--t-max", type=float, default=None, help="limiting bulk temperature [K]")
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
            ("--cp", args.cp),
            ("--t-in", args.t_in),
        )
        if value is None
    ]
    if missing:
        print(
            "error: requires --mdot, --cp, and --t-in; " f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if args.mdot <= 0 or args.cp <= 0 or args.t_in <= 0:
        print("error: mdot, cp, and t-in must be > 0", file=sys.stderr)
        return 2
    if not all(math.isfinite(value) for value in (args.mdot, args.cp, args.t_in)):
        print("error: inputs must be finite", file=sys.stderr)
        return 2
    extras = [
        value
        for value in (args.q_dot, args.flux, args.area, args.t_max)
        if value is not None
    ]
    if any(not math.isfinite(value) for value in extras):
        print("error: inputs must be finite", file=sys.stderr)
        return 2
    has_q = args.q_dot is not None
    has_flux = args.flux is not None or args.area is not None
    if has_q and has_flux:
        print("error: pass --q-dot or --flux with --area, not both", file=sys.stderr)
        return 2
    if not has_q and not has_flux:
        print("error: pass --q-dot or both --flux and --area", file=sys.stderr)
        return 2
    if has_flux and (args.flux is None or args.area is None):
        print("error: --flux and --area are both required", file=sys.stderr)
        return 2
    if has_q:
        heat = args.q_dot
    else:
        assert args.flux is not None and args.area is not None
        heat = args.flux * args.area
    scale = args.mdot * args.cp
    if (
        not math.isfinite(heat)
        or heat <= 0
        or not math.isfinite(scale)
        or scale <= 0
    ):
        print("error: heat rate must be finite and > 0 W", file=sys.stderr)
        return 2
    if args.t_max is not None and args.t_max <= args.t_in:
        print("error: t-max must exceed t-in", file=sys.stderr)
        return 2

    tout = outlet_temperature(args.t_in, heat, args.mdot, args.cp)
    needed = None if args.t_max is None else min_flow(heat, args.cp, args.t_max, args.t_in)
    results = [heat, tout]
    if needed is not None:
        results.append(needed)
    if any(not math.isfinite(value) for value in results):
        print("error: result is not finite", file=sys.stderr)
        return 2
    print_kv(
        "assumptions",
        (
            "steady coolant energy balance Q = mdot*cp*(Tout - Tin); "
            "constant cp; channel Nusselt number and boiling limit are not evaluated; "
            "Tmax is an input (SP-125 uses the coolant critical temperature)"
        ),
    )
    print_kv("mdot_kg_s", args.mdot)
    print_kv("cp_J_kg_K", args.cp)
    print_kv("T_in_K", args.t_in)
    print_kv("Q_W", heat)
    print_kv("T_out_K", tout)
    print_kv("dT_K", tout - args.t_in)
    if args.t_max is not None:
        needed = min_flow(heat, args.cp, args.t_max, args.t_in)
        print_kv("T_max_K", args.t_max)
        print_kv("Q_capacity_W", args.mdot * args.cp * (args.t_max - args.t_in))
        print_kv("limit", "pass" if tout <= args.t_max else "fail")
        print_kv("mdot_min_kg_s", needed)
    if args.out:
        write_plot(args.t_in, heat, args.mdot, args.cp, args.t_max, Path(args.out))
        print_kv("graph", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
