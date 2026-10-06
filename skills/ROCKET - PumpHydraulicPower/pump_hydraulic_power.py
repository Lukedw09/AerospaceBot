#!/usr/bin/env python3
"""Pump volume flow, hydraulic power, and shaft power.

pump_volume_flow is Vdot = mdot / rho.
pump_hydraulic_power is P_hyd = mdot * dp / rho.
pump_shaft_power is P_shaft = P_hyd / eta.
pump_drive_power is P_drive = P_shaft / eta_drive when a drive efficiency is given.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Pump shaft power"


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def volume_flow(mdot: float, rho: float) -> float:
    return mdot / rho


def hydraulic_power(mdot: float, rho: float, dp: float) -> float:
    return volume_flow(mdot, rho) * dp


def shaft_power(mdot: float, rho: float, dp: float, eta: float) -> float:
    return hydraulic_power(mdot, rho, dp) / eta


def write_plot(mdot: float, rho: float, eta: float, dp: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    drops = [dp * i / 40.0 for i in range(41)]
    powers = [shaft_power(mdot, rho, item, eta) for item in drops]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot([item / 1.0e6 for item in drops], [item / 1.0e3 for item in powers], color="C0")
    ax.plot(dp / 1.0e6, shaft_power(mdot, rho, dp, eta) / 1.0e3, "s", color="C3")
    ax.set_xlabel("Pump pressure rise [MPa]")
    ax.set_ylabel("Shaft power [kW]")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def run_check() -> int:
    vdot = volume_flow(2.0, 1000.0)
    hyd = hydraulic_power(2.0, 1000.0, 2.0e5)
    shaft = shaft_power(2.0, 1000.0, 2.0e5, 0.7)
    drive = shaft / 0.8
    if abs(vdot - 0.002) > CHECK_TOL:
        print(f"CHECK FAIL: Vdot = {vdot}", file=sys.stderr)
        return 1
    if abs(hyd - 400.0) > CHECK_TOL:
        print(f"CHECK FAIL: P_hyd = {hyd}", file=sys.stderr)
        return 1
    if abs(shaft - 4000.0 / 7.0) > CHECK_TOL:
        print(f"CHECK FAIL: P_shaft = {shaft}", file=sys.stderr)
        return 1
    if abs(drive - 5000.0 / 7.0) > CHECK_TOL:
        print(f"CHECK FAIL: P_drive = {drive}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "pump.png"
        write_plot(2.0, 1000.0, 0.7, 2.0e5, path)
        if not path.is_file() or path.stat().st_size <= 0:
            print("CHECK FAIL: plot was not written", file=sys.stderr)
            return 1
    print("check: pass")
    print_kv("Vdot_m3_s", vdot)
    print_kv("P_hyd_W", hyd)
    print_kv("P_shaft_W", shaft)
    print_kv("P_drive_W", drive)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hydraulic, shaft, and optional drive power of a propellant pump."
    )
    parser.add_argument("--mdot", type=float, default=None, help="mass flow [kg/s]")
    parser.add_argument("--rho", type=float, default=None, help="density [kg/m^3]")
    parser.add_argument("--dp", type=float, default=None, help="pump pressure rise [Pa]")
    parser.add_argument("--eta", type=float, default=None, help="overall pump efficiency")
    parser.add_argument(
        "--eta-drive",
        type=float,
        default=None,
        help="prime-mover efficiency",
    )
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
            ("--dp", args.dp),
            ("--eta", args.eta),
        )
        if value is None
    ]
    if missing:
        print(
            "error: requires --mdot, --rho, --dp, and --eta; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    supplied = [args.mdot, args.rho, args.dp, args.eta]
    if args.eta_drive is not None:
        supplied.append(args.eta_drive)
    if any(not math.isfinite(value) for value in supplied):
        print("error: inputs must be finite", file=sys.stderr)
        return 2
    if args.mdot <= 0 or args.rho <= 0 or args.dp <= 0:
        print("error: mdot, rho, and dp must be > 0", file=sys.stderr)
        return 2
    if args.eta <= 0 or args.eta > 1:
        print("error: eta must be in (0, 1]", file=sys.stderr)
        return 2
    if args.eta_drive is not None and (args.eta_drive <= 0 or args.eta_drive > 1):
        print("error: eta-drive must be in (0, 1]", file=sys.stderr)
        return 2

    vdot = volume_flow(args.mdot, args.rho)
    hyd = hydraulic_power(args.mdot, args.rho, args.dp)
    shaft = shaft_power(args.mdot, args.rho, args.dp, args.eta)
    drive = None if args.eta_drive is None else shaft / args.eta_drive
    results = [vdot, hyd, shaft]
    if drive is not None:
        results.append(drive)
    if any(not math.isfinite(value) for value in results):
        print("error: result is not finite", file=sys.stderr)
        return 2
    print_kv(
        "assumptions",
        (
            "incompressible delivered flow; Vdot = mdot/rho; "
            "P_hyd = Vdot*dp; P_shaft = P_hyd/eta; eta is an input"
        ),
    )
    print_kv("mdot_kg_s", args.mdot)
    print_kv("rho_kg_m3", args.rho)
    print_kv("dp_Pa", args.dp)
    print_kv("eta", args.eta)
    print_kv("Vdot_m3_s", vdot)
    print_kv("P_hyd_W", hyd)
    print_kv("P_shaft_W", shaft)
    if args.eta_drive is not None:
        print_kv("eta_drive", args.eta_drive)
        print_kv("P_drive_W", drive)
    if args.out:
        write_plot(args.mdot, args.rho, args.eta, args.dp, Path(args.out))
        print_kv("graph", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
