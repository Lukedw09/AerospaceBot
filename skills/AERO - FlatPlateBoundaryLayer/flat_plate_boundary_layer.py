#!/usr/bin/env python3
"""Flat-plate skin friction for a laminar or one-seventh-power turbulent layer.

blasius_local_skin_friction, blasius_plate_friction, and
blasius_thickness_ratio are the laminar records.
turbulent_local_skin_friction_seventh and turbulent_plate_friction_seventh
are the turbulent records. Reynolds number reuses reynolds_number or
reynolds_number_kinematic.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-12
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Flat-plate skin friction"
N_CURVE = 200

ASSUMPTIONS = (
    "smooth flat plate at zero incidence; one wetted side; "
    "no transition model; --law is laminar or turbulent; "
    "blasius_local_skin_friction cf = 0.664/sqrt(Re); "
    "blasius_plate_friction Cf = 1.328/sqrt(Re); "
    "blasius_thickness_ratio delta/x = 5/sqrt(Re); "
    "turbulent_local_skin_friction_seventh cf = 0.0592/Re**(1/5); "
    "turbulent_plate_friction_seventh Cf = 0.074/Re**(1/5); "
    "laminar statement is for Re below about 5e5 to 1e6; "
    "turbulent statement is for 5e5 < Re < 1e7; "
    "friction drag uses Cf times dynamic pressure times L*span"
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


def require_positive(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def blasius_local_skin_friction(reynolds: float) -> float:
    return 0.664 / math.sqrt(reynolds)


def blasius_plate_friction(reynolds: float) -> float:
    return 1.328 / math.sqrt(reynolds)


def blasius_thickness_ratio(reynolds: float) -> float:
    return 5.0 / math.sqrt(reynolds)


def turbulent_plate_friction_seventh(reynolds: float) -> float:
    return 0.074 / reynolds**0.2


def turbulent_local_skin_friction_seventh(reynolds: float) -> float:
    return 0.0592 / reynolds**0.2


def range_note(law: str, reynolds: float) -> str:
    if law == "laminar" and reynolds > 1.0e6:
        return "above the laminar range stated in NASA TM 84363"
    if law == "turbulent" and not (5.0e5 < reynolds < 1.0e7):
        return "outside 5e5 < Re < 1e7 stated for the one-seventh-power law"
    return "inside the stated range"


def plate_state(
    law: str,
    reynolds: float,
    length: float | None,
    span: float | None,
    rho: float | None,
    speed: float | None,
) -> dict[str, object]:
    require_positive(reynolds, "Reynolds number")
    if law == "laminar":
        local = blasius_local_skin_friction(reynolds)
        plate = blasius_plate_friction(reynolds)
        thickness = blasius_thickness_ratio(reynolds)
    elif law == "turbulent":
        local = turbulent_local_skin_friction_seventh(reynolds)
        plate = turbulent_plate_friction_seventh(reynolds)
        thickness = None
    else:
        raise ValueError("--law must be laminar or turbulent")
    state: dict[str, object] = {
        "law": law,
        "Re_L": reynolds,
        "cf": local,
        "Cf": plate,
        "range_note": range_note(law, reynolds),
    }
    if thickness is not None:
        state["delta_over_L"] = thickness
    if span is not None:
        if length is None or rho is None or speed is None:
            raise ValueError("--span needs --L and the freestream density and speed")
        require_positive(length, "L")
        require_positive(span, "span")
        require_positive(rho, "rho")
        require_positive(speed, "V")
        area = length * span
        dynamic = 0.5 * rho * speed * speed
        state["S_m2"] = area
        state["q_Pa"] = dynamic
        state["Df_N"] = plate * dynamic * area
    return state


def reynolds_from_flags(args: argparse.Namespace) -> tuple[float, float | None, float | None, float | None]:
    if args.re is not None:
        if any(value is not None for value in (args.rho, args.V, args.L, args.mu, args.nu)):
            raise ValueError("pass --re or the flow quantities, not both")
        return args.re, args.L, None, None
    if args.nu is not None:
        if args.mu is not None or args.rho is not None:
            raise ValueError("pass --nu or --rho with --mu, not both")
        if args.V is None or args.L is None:
            raise ValueError("--nu requires --V and --L")
        require_positive(args.nu, "nu")
        require_positive(args.V, "V")
        require_positive(args.L, "L")
        return args.V * args.L / args.nu, args.L, None, args.V
    if args.rho is None or args.V is None or args.L is None or args.mu is None:
        raise ValueError("requires --re, or --rho, --V, --L, and --mu, or --nu with --V and --L")
    require_positive(args.rho, "rho")
    require_positive(args.V, "V")
    require_positive(args.L, "L")
    require_positive(args.mu, "mu")
    return args.rho * args.V * args.L / args.mu, args.L, args.rho, args.V


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "law",
        "Re_L",
        "cf",
        "Cf",
        "delta_over_L",
        "S_m2",
        "q_Pa",
        "Df_N",
        "range_note",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    law = str(result["law"])
    reynolds = float(result["Re_L"])
    lo = reynolds / 20.0
    hi = reynolds * 20.0
    if law == "laminar":
        lo = max(lo, 1.0e3)
        func = blasius_plate_friction
    else:
        lo = max(lo, 1.0e5)
        func = turbulent_plate_friction_seventh
    grid = [lo * (hi / lo) ** (i / (N_CURVE - 1)) for i in range(N_CURVE)]
    curve = [func(value) for value in grid]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(grid, curve, color="C0", label=r"$C_f$")
    ax.plot(reynolds, float(result["Cf"]), "s", color="C0")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Reynolds number $Re_L$")
    ax.set_ylabel(r"Plate friction coefficient $C_f$")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    reynolds = 10000.0
    laminar = plate_state("laminar", reynolds, None, None, None, None)
    if not close(float(laminar["cf"]), 0.664 / 100.0):
        return fail("laminar local cf is not 0.664/sqrt(Re)")
    if not close(float(laminar["Cf"]), 1.328 / 100.0):
        return fail("laminar plate Cf is not 1.328/sqrt(Re)")
    if not close(float(laminar["Cf"]), 2.0 * float(laminar["cf"])):
        return fail("laminar plate Cf is not twice the local cf")
    if not close(float(laminar["delta_over_L"]), 5.0 / 100.0):
        return fail("laminar thickness ratio is not 5/sqrt(Re)")
    turbulent = plate_state("turbulent", 1.0e5, None, None, None, None)
    if not close(float(turbulent["Cf"]), 0.074 / 10.0):
        return fail("turbulent plate Cf is not 0.074/Re**(1/5)")
    if not close(float(turbulent["cf"]), 0.0592 / 10.0):
        return fail("turbulent local cf is not 0.0592/Re**(1/5)")
    if not close(float(turbulent["cf"]) * 5.0 / 4.0, float(turbulent["Cf"])):
        return fail("seventh-power local cf is not 4/5 of the plate Cf")
    forced = plate_state("laminar", 1.0e4, 2.0, 3.0, 1.25, 40.0)
    dynamic = 0.5 * 1.25 * 40.0 * 40.0
    if not close(float(forced["Df_N"]), float(forced["Cf"]) * dynamic * 6.0):
        return fail("friction drag is not Cf*q*S")
    if "delta_over_L" in turbulent:
        return fail("turbulent thickness was printed")
    try:
        plate_state("transitional", 1.0e5, None, None, None, None)
        return fail("an unknown law was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(laminar, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("Cf_laminar_1e4", laminar["Cf"])
    print_kv("Cf_turbulent_1e5", turbulent["Cf"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flat-plate laminar or turbulent skin friction.")
    parser.add_argument("--law", choices=("laminar", "turbulent"), default=None, help="laminar or turbulent")
    parser.add_argument("--re", type=float, default=None, help="Reynolds number based on plate length")
    parser.add_argument("--rho", type=float, default=None, help="freestream density [kg/m^3]")
    parser.add_argument("--V", type=float, default=None, help="freestream speed [m/s]")
    parser.add_argument("--L", type=float, default=None, help="plate length [m]")
    parser.add_argument("--mu", type=float, default=None, help="dynamic viscosity [Pa s]")
    parser.add_argument("--nu", type=float, default=None, help="kinematic viscosity [m^2/s]")
    parser.add_argument("--span", type=float, default=None, help="span of one wetted side [m]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.law is None:
        print("error: requires --law laminar or turbulent", file=sys.stderr)
        return 2
    try:
        reynolds, length, rho, speed = reynolds_from_flags(args)
        if args.span is not None and (rho is None or speed is None or length is None):
            raise ValueError("--span needs --rho, --V, and --L")
        result = plate_state(args.law, reynolds, length, args.span, rho, speed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "flat_plate_boundary_layer.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
