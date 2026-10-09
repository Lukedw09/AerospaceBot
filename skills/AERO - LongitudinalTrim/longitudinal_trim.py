#!/usr/bin/env python3
"""Stick-fixed 1-g trim angle and elevator.

level_flight_lift_coefficient is W/(q*S).
cm_alpha_from_static_margin is -a*kn with kn = x/c, not percent.
trim_angle_of_attack is CL/a. trim_elevator is -(cm0 + cma*alpha)/cmde.
Neutral point reuses stick_fixed_neutral_point when geometry is passed.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "steady 1-g level flight; stick fixed; linear coefficients; "
    "lift curve through the origin; "
    "level_flight_lift_coefficient; trim_angle_of_attack alpha = CL/a; "
    "cm_alpha_from_static_margin Cm_alpha = -a*kn with kn = x/c; "
    "trim_elevator; Cm_de is supplied; "
    "stick_fixed_neutral_point when tail geometry is passed"
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


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def stick_fixed_neutral_point(
    downwash: float, tail_slope: float, wing_slope: float, q_ratio: float, volume: float
) -> float:
    return (1.0 - downwash) * (tail_slope / wing_slope) * q_ratio * volume


def solve(
    lift_slope: float,
    cm0: float,
    cm_de: float,
    cl: float,
    cm_alpha: float,
    de_max: float | None,
    extra: dict[str, object],
) -> dict[str, object]:
    require_positive("a", lift_slope)
    require_finite("cm0", cm0)
    if cm_de == 0.0 or not math.isfinite(cm_de):
        raise ValueError("cm-de must be finite and nonzero")
    require_finite("CL", cl)
    require_finite("cm-alpha", cm_alpha)
    alpha = cl / lift_slope
    de = -(cm0 + cm_alpha * alpha) / cm_de
    residual = cm0 + cm_alpha * alpha + cm_de * de
    result: dict[str, object] = {
        "CL": cl,
        "a_per_rad": lift_slope,
        "cm0": cm0,
        "cm_alpha_per_rad": cm_alpha,
        "cm_de_per_rad": cm_de,
        "alpha_trim_rad": alpha,
        "de_trim_rad": de,
        "residual_cm": residual,
    }
    result.update(extra)
    if de_max is not None:
        require_positive("de-max", de_max)
        result["de_max_rad"] = de_max
        if abs(de) <= 1e-15:
            result["elevator_status"] = "within_limit"
        elif abs(de) <= de_max:
            result["elevator_margin"] = de_max / abs(de) - 1.0
            result["elevator_status"] = "within_limit"
        else:
            result["elevator_margin"] = de_max / abs(de) - 1.0
            result["elevator_status"] = "exceeds_limit"
    return result


def geometry_kn(args: argparse.Namespace, lift_slope: float) -> dict[str, object]:
    names = ("at", "downwash", "q_ratio", "tail_area", "tail_length", "wing_area", "mac", "cg")
    if any(getattr(args, name) is None for name in names):
        raise ValueError("static-margin geometry needs the tail, wing, and --cg flags together")
    require_positive("at", args.at)
    require_positive("q-ratio", args.q_ratio)
    require_positive("tail-area", args.tail_area)
    require_positive("tail-length", args.tail_length)
    require_positive("wing-area", args.wing_area)
    require_positive("mac", args.mac)
    require_finite("downwash", args.downwash)
    require_finite("cg", args.cg)
    volume = (args.tail_area * args.tail_length) / (args.wing_area * args.mac)
    x0 = stick_fixed_neutral_point(args.downwash, args.at, lift_slope, args.q_ratio, volume)
    kn = x0 - args.cg
    return {
        "neutral_point_x0_over_c": x0,
        "kn": kn,
        "cm_alpha_source": "static_margin",
        "cm_alpha": -lift_slope * kn,
    }


def pitching_slope(args: argparse.Namespace, lift_slope: float) -> tuple[float, dict[str, object]]:
    supplied = args.cm_alpha is not None
    kn_flag = args.kn is not None
    geom_names = ("at", "downwash", "q_ratio", "tail_area", "tail_length", "wing_area", "mac", "cg")
    geom = any(getattr(args, name) is not None for name in geom_names)
    chosen = sum(1 for flag in (supplied, kn_flag, geom) if flag)
    if chosen != 1:
        raise ValueError("pass --cm-alpha, or --kn, or the static-margin geometry, not more than one")
    if supplied:
        require_finite("cm-alpha", args.cm_alpha)
        return args.cm_alpha, {"cm_alpha_source": "supplied"}
    if kn_flag:
        require_finite("kn", args.kn)
        return -lift_slope * args.kn, {"kn": args.kn, "cm_alpha_source": "kn"}
    built = geometry_kn(args, lift_slope)
    return float(built.pop("cm_alpha")), built


def lift_coefficient(args: argparse.Namespace) -> float:
    if args.CL is not None and any(v is not None for v in (args.q, args.S, args.W)):
        raise ValueError("pass --CL or --q --S --W, not both")
    if args.CL is not None:
        require_finite("CL", args.CL)
        return args.CL
    if args.q is None or args.S is None or args.W is None:
        raise ValueError("pass --CL, or --q, --S, and --W")
    require_positive("q", args.q)
    require_positive("S", args.S)
    require_finite("W", args.W)
    return args.W / (args.q * args.S)


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "CL",
        "a_per_rad",
        "cm0",
        "cm_alpha_source",
        "neutral_point_x0_over_c",
        "kn",
        "cm_alpha_per_rad",
        "cm_de_per_rad",
        "alpha_trim_rad",
        "de_trim_rad",
        "residual_cm",
        "de_max_rad",
        "elevator_margin",
        "elevator_status",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    cm0 = float(result["cm0"])
    cma = float(result["cm_alpha_per_rad"])
    cmde = float(result["cm_de_per_rad"])
    alpha = float(result["alpha_trim_rad"])
    de = float(result["de_trim_rad"])
    span = max(abs(alpha) * 1.5, 0.05)
    grid = [-span + 2.0 * span * i / 80.0 for i in range(81)]
    bare = [cm0 + cma * value for value in grid]
    trimmed = [cm0 + cma * value + cmde * de for value in grid]
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    ax.plot(grid, bare, color="C0", label=r"$\delta_e=0$")
    ax.plot(grid, trimmed, color="C1", label="trim elevator")
    ax.plot([alpha], [0.0], "o", color="C3")
    ax.axhline(0.0, color="0.6", lw=0.6)
    ax.set_xlabel(r"Angle of attack $\alpha$ [rad]")
    ax.set_ylabel(r"Pitching moment $C_m$")
    ax.set_title("Stick-fixed trim")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    cl = 1000.0 / (500.0 * 10.0)
    if not close(cl, 0.2):
        return fail("CL")
    cma = -5.0 * 0.1
    if not close(cma, -0.5):
        return fail("cm alpha")
    state = solve(5.0, 0.05, -0.8, cl, cma, None, {"kn": 0.1, "cm_alpha_source": "kn"})
    if not close(float(state["alpha_trim_rad"]), 0.04):
        return fail("alpha")
    if not close(float(state["de_trim_rad"]), 0.0375):
        return fail("elevator")
    if not close(float(state["residual_cm"]), 0.0):
        return fail("residual")
    # stick_fixed_neutral_point sample: x0/c = 54/125, cg = 0.1, kn = 83/250.
    built = geometry_kn(
        argparse.Namespace(
            at=4.0,
            downwash=0.4,
            q_ratio=0.9,
            tail_area=2.0,
            tail_length=5.0,
            wing_area=10.0,
            mac=1.0,
            cg=0.1,
        ),
        5.0,
    )
    if not close(float(built["kn"]), 83.0 / 250.0):
        return fail("kn from geometry")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(state, path)
        if path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("de_trim_rad", float(state["de_trim_rad"]))
    print_kv("kn", float(built["kn"]))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stick-fixed 1-g angle of attack and elevator.")
    parser.add_argument("--a", type=float, default=None, help="lift-curve slope [1/rad]")
    parser.add_argument("--cm0", type=float, default=None, help="pitching moment at zero alpha and elevator")
    parser.add_argument("--cm-de", type=float, default=None, help="elevator effectiveness [1/rad]")
    parser.add_argument("--CL", type=float, default=None, help="lift coefficient")
    parser.add_argument("--q", type=float, default=None, help="dynamic pressure [Pa]")
    parser.add_argument("--S", type=float, default=None, help="wing area [m^2]")
    parser.add_argument("--W", type=float, default=None, help="weight [N]")
    parser.add_argument("--cm-alpha", type=float, default=None, help="pitch stiffness [1/rad]")
    parser.add_argument("--kn", type=float, default=None, help="static margin x/c, fraction of chord")
    parser.add_argument("--at", type=float, default=None, help="tail lift-curve slope [1/rad]")
    parser.add_argument("--downwash", type=float, default=None, help="downwash slope")
    parser.add_argument("--q-ratio", type=float, default=None, help="tail dynamic-pressure ratio")
    parser.add_argument("--tail-area", type=float, default=None, help="horizontal-tail area [m^2]")
    parser.add_argument("--tail-length", type=float, default=None, help="tail length [m]")
    parser.add_argument("--wing-area", type=float, default=None, help="wing area [m^2]")
    parser.add_argument("--mac", type=float, default=None, help="mean aerodynamic chord [m]")
    parser.add_argument("--cg", type=float, default=None, help="x'/c of the center of gravity")
    parser.add_argument("--de-max", type=float, default=None, help="elevator limit [rad]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        if args.a is None or args.cm0 is None or args.cm_de is None:
            raise ValueError("requires --a, --cm0, and --cm-de")
        cl = lift_coefficient(args)
        cm_alpha, extra = pitching_slope(args, args.a)
        result = solve(args.a, args.cm0, args.cm_de, cl, cm_alpha, args.de_max, extra)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "longitudinal_trim.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
