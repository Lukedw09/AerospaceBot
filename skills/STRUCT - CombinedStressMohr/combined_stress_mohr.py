#!/usr/bin/env python3
"""Plane-stress principals for bending plus torsion.

principal_stress_max and principal_stress_min are
(sx+sy)/2 ± (((sx-sy)/2)**2 + tau**2)**0.5 with sy = 0.
mohr_center is (sx+sy)/2. mohr_radius and max_shear_from_mohr are the
same square root. Bending stress is M/Z or M*c/I. Shaft shear is T*R/J.
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
    "plane stress; linear elastic; sy = 0 on the bending-plus-torsion path; "
    "principal_stress_max and principal_stress_min; mohr_center; "
    "mohr_radius = max_shear_from_mohr; "
    "bending stress M/Z or M*c/I; circular_shaft_shear tau = T*R/J; "
    "optional margin_of_safety uses max(|sigma1|, |sigma2|) as the design stress; "
    "plastic Mohr and a second normal stress are omitted"
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


def principal_stress_max(sx: float, sy: float, tau: float) -> float:
    return 0.5 * (sx + sy) + math.hypot(0.5 * (sx - sy), tau)


def principal_stress_min(sx: float, sy: float, tau: float) -> float:
    return 0.5 * (sx + sy) - math.hypot(0.5 * (sx - sy), tau)


def mohr_center(sx: float, sy: float) -> float:
    return 0.5 * (sx + sy)


def mohr_radius(sx: float, sy: float, tau: float) -> float:
    return math.hypot(0.5 * (sx - sy), tau)


def polar_moment(outer_radius: float, inner_radius: float) -> float:
    return 0.5 * math.pi * (outer_radius**4 - inner_radius**4)


def solve(sx: float, sy: float, tau: float, allowable: float | None) -> dict[str, object]:
    s1 = principal_stress_max(sx, sy, tau)
    s2 = principal_stress_min(sx, sy, tau)
    radius = mohr_radius(sx, sy, tau)
    result: dict[str, object] = {
        "sigma_x_Pa": sx,
        "sigma_y_Pa": sy,
        "tau_xy_Pa": tau,
        "sigma1_Pa": s1,
        "sigma2_Pa": s2,
        "tau_max_Pa": radius,
        "mohr_center_Pa": mohr_center(sx, sy),
        "mohr_radius_Pa": radius,
    }
    if allowable is not None:
        design = max(abs(s1), abs(s2))
        if design == 0.0:
            raise ValueError("design stress is zero; margin is undefined")
        result["allowable_Pa"] = allowable
        result["margin_of_safety"] = allowable / design - 1.0
    return result


def outer_radius(args: argparse.Namespace) -> float:
    if args.radius is not None and args.diameter is not None:
        raise ValueError("pass --radius or --diameter, not both")
    if args.radius is not None:
        require_positive("radius", args.radius)
        return args.radius
    if args.diameter is not None:
        require_positive("diameter", args.diameter)
        return 0.5 * args.diameter
    raise ValueError("torque path needs --radius or --diameter for the outer fiber")


def inner_radius(args: argparse.Namespace, outer: float) -> float:
    if args.inner_radius is not None and args.inner_diameter is not None:
        raise ValueError("pass --inner-radius or --inner-diameter, not both")
    if args.radius is not None and args.inner_diameter is not None:
        raise ValueError("use --inner-radius with --radius")
    if args.diameter is not None and args.inner_radius is not None:
        raise ValueError("use --inner-diameter with --diameter")
    if args.inner_radius is not None:
        require_finite("inner-radius", args.inner_radius)
        inner = args.inner_radius
    elif args.inner_diameter is not None:
        require_finite("inner-diameter", args.inner_diameter)
        inner = 0.5 * args.inner_diameter
    else:
        return 0.0
    if inner < 0.0 or inner >= outer:
        raise ValueError("inner radius must satisfy 0 <= Ri < Ro")
    return inner


def from_loads(args: argparse.Namespace) -> tuple[float, float, str]:
    if args.moment is None or args.torque is None:
        raise ValueError("load path needs --moment and --torque")
    require_finite("moment", args.moment)
    require_finite("torque", args.torque)
    if args.section_modulus is not None and (args.inertia is not None or args.fiber is not None):
        raise ValueError("pass --section-modulus or --inertia with --fiber, not both")
    if args.section_modulus is not None:
        require_positive("section-modulus", args.section_modulus)
        sigma = args.moment / args.section_modulus
        bend = "section_modulus"
    elif args.inertia is not None or args.fiber is not None:
        if args.inertia is None or args.fiber is None:
            raise ValueError("--inertia and --fiber are a pair")
        require_positive("inertia", args.inertia)
        require_positive("fiber", args.fiber)
        sigma = args.moment * args.fiber / args.inertia
        bend = "inertia_fiber"
    else:
        raise ValueError("bending needs --section-modulus or --inertia and --fiber")
    radius = outer_radius(args)
    if args.polar is not None:
        require_positive("polar", args.polar)
        polar = args.polar
        shear_path = "supplied_polar"
    else:
        polar = polar_moment(radius, inner_radius(args, radius))
        shear_path = "circular_shaft"
    tau = args.torque * radius / polar
    return sigma, tau, f"{bend}+{shear_path}"


def from_args(args: argparse.Namespace) -> dict[str, object]:
    direct = args.sigma is not None or args.tau is not None
    loads = any(
        value is not None
        for value in (
            args.moment,
            args.torque,
            args.section_modulus,
            args.inertia,
            args.fiber,
            args.polar,
            args.radius,
            args.diameter,
            args.inner_radius,
            args.inner_diameter,
        )
    )
    if direct and loads:
        raise ValueError("do not mix --sigma/--tau with the load path")
    if direct:
        if args.sigma is None or args.tau is None:
            raise ValueError("--sigma and --tau are a pair")
        require_finite("sigma", args.sigma)
        require_finite("tau", args.tau)
        sigma, tau, path = args.sigma, args.tau, "sigma_tau"
    elif loads:
        sigma, tau, path = from_loads(args)
    else:
        raise ValueError("pass --sigma and --tau, or bending plus torsion loads")
    if args.allowable is not None:
        require_positive("allowable", args.allowable)
    result = solve(sigma, 0.0, tau, args.allowable)
    result["path"] = path
    return result


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "path",
        "sigma_x_Pa",
        "sigma_y_Pa",
        "tau_xy_Pa",
        "sigma1_Pa",
        "sigma2_Pa",
        "tau_max_Pa",
        "mohr_center_Pa",
        "mohr_radius_Pa",
        "allowable_Pa",
        "margin_of_safety",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    center = float(result["mohr_center_Pa"])
    radius = float(result["mohr_radius_Pa"])
    s1 = float(result["sigma1_Pa"])
    s2 = float(result["sigma2_Pa"])
    sx = float(result["sigma_x_Pa"])
    tau = float(result["tau_xy_Pa"])
    steps = 181
    xs = [center + radius * math.cos(2.0 * math.pi * i / (steps - 1)) for i in range(steps)]
    ys = [radius * math.sin(2.0 * math.pi * i / (steps - 1)) for i in range(steps)]
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    ax.plot(xs, ys, color="C0")
    ax.plot([s2, s1], [0.0, 0.0], "o", color="C3", label="principals")
    ax.plot([sx], [tau], "s", color="C2", label="element")
    ax.axhline(0.0, color="0.6", lw=0.6)
    ax.axvline(0.0, color="0.6", lw=0.6)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel(r"Normal stress $\sigma$ [Pa]")
    ax.set_ylabel(r"Shear stress $\tau$ [Pa]")
    ax.set_title("Mohr circle")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    radius = math.hypot(50.0, 50.0)
    state = solve(100.0, 0.0, 50.0, None)
    if not close(float(state["sigma1_Pa"]), 50.0 + radius):
        return fail(f"sigma1 {state['sigma1_Pa']}")
    if not close(float(state["sigma2_Pa"]), 50.0 - radius):
        return fail(f"sigma2 {state['sigma2_Pa']}")
    if not close(float(state["mohr_center_Pa"]), 50.0):
        return fail("center")
    if not close(float(state["tau_max_Pa"]), radius):
        return fail("radius")
    # M/Z = 1000/0.01 = 1e5. Solid J = pi/2*R^4, tau = T*R/J.
    outer = 0.05
    polar = polar_moment(outer, 0.0)
    tau = 500.0 * outer / polar
    loaded = from_loads(
        argparse.Namespace(
            moment=1000.0,
            torque=500.0,
            section_modulus=0.01,
            inertia=None,
            fiber=None,
            polar=None,
            radius=outer,
            diameter=None,
            inner_radius=None,
            inner_diameter=None,
        )
    )
    if not close(loaded[0], 1.0e5) or not close(loaded[1], tau):
        return fail(f"load path {loaded}")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(state, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("sigma1_Pa", float(state["sigma1_Pa"]))
    print_kv("tau_load_Pa", loaded[1])
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Principals and Mohr circle for bending plus torsion."
    )
    parser.add_argument("--sigma", type=float, default=None, help="normal stress σx [Pa]")
    parser.add_argument("--tau", type=float, default=None, help="shear stress τxy [Pa]")
    parser.add_argument("--moment", type=float, default=None, help="bending moment M [N*m]")
    parser.add_argument("--section-modulus", type=float, default=None, help="section modulus Z [m^3]")
    parser.add_argument("--inertia", type=float, default=None, help="second moment I [m^4]")
    parser.add_argument("--fiber", type=float, default=None, help="extreme-fiber distance c [m]")
    parser.add_argument("--torque", type=float, default=None, help="torque T [N*m]")
    parser.add_argument("--polar", type=float, default=None, help="polar second moment J [m^4]")
    parser.add_argument("--radius", type=float, default=None, help="outer radius Ro [m]")
    parser.add_argument("--diameter", type=float, default=None, help="outer diameter Do [m]")
    parser.add_argument("--inner-radius", type=float, default=None, help="inner radius Ri [m]")
    parser.add_argument("--inner-diameter", type=float, default=None, help="inner diameter Di [m]")
    parser.add_argument("--allowable", type=float, default=None, help="allowable normal stress [Pa]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        result = from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "combined_stress_mohr.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
