#!/usr/bin/env python3
"""Inviscid thin-section lift from angle of attack or a NACA four-digit mean line.

thin_airfoil_section_lift is cl = 2*pi*(alpha - alpha_L0).
A mean line uses naca4_glauert_station, naca4_zero_lift_angle,
naca4_glauert_A1, naca4_glauert_A2, and naca4_quarter_chord_moment.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-12
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Thin airfoil section lift"

ASSUMPTIONS = (
    "two-dimensional inviscid incompressible thin-section theory; "
    "cl_alpha = 2*pi per radian; "
    "thin_airfoil_section_lift is 2*pi*(alpha - alpha_L0); "
    "path B uses naca4_glauert_station, naca4_zero_lift_angle, "
    "naca4_glauert_A1, naca4_glauert_A2, and naca4_quarter_chord_moment; "
    "thickness does not enter lift or quarter-chord moment; "
    "inviscid pressure drag is zero; "
    "a sealed flap is not recorded; "
    "tunnel polars are not this program"
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


def naca4_glauert_station(p_camber: float) -> float:
    return 2.0 * math.atan(math.sqrt(p_camber / (1.0 - p_camber)))


def naca4_zero_lift_angle(m_camber: float, p_camber: float, theta_p: float) -> float:
    return (1.0 / math.pi) * (
        (m_camber / p_camber**2)
        * (
            (2.0 * p_camber - 1.0 - 0.5) * theta_p
            + 2.0 * math.sqrt(p_camber * (1.0 - p_camber)) * (1.0 - (2.0 * p_camber - 1.0))
            + (2.0 * p_camber - 1.0) * math.sqrt(p_camber * (1.0 - p_camber))
        )
        + (m_camber / (1.0 - p_camber) ** 2)
        * (
            (2.0 * p_camber - 1.0 - 0.5) * math.pi
            - (
                (2.0 * p_camber - 1.0 - 0.5) * theta_p
                + 2.0 * math.sqrt(p_camber * (1.0 - p_camber)) * (1.0 - (2.0 * p_camber - 1.0))
                + (2.0 * p_camber - 1.0) * math.sqrt(p_camber * (1.0 - p_camber))
            )
        )
    )


def naca4_glauert_a1(m_camber: float, p_camber: float, theta_p: float) -> float:
    return (2.0 / math.pi) * (
        (m_camber / p_camber**2)
        * ((2.0 * p_camber - 1.0) * math.sqrt(p_camber * (1.0 - p_camber)) + theta_p / 2.0)
        + (m_camber / (1.0 - p_camber) ** 2)
        * (
            math.pi / 2.0
            - ((2.0 * p_camber - 1.0) * math.sqrt(p_camber * (1.0 - p_camber)) + theta_p / 2.0)
        )
    )


def naca4_glauert_a2(m_camber: float, p_camber: float) -> float:
    root = math.sqrt(p_camber * (1.0 - p_camber))
    return (2.0 / math.pi) * (
        -2.0 * (2.0 * p_camber - 1.0) ** 2 * root
        + 2.0 * root
        - (16.0 / 3.0) * root**3
    ) * (m_camber / p_camber**2 - m_camber / (1.0 - p_camber) ** 2)


def naca4_quarter_chord_moment(a2: float, a1: float) -> float:
    return (math.pi / 4.0) * (a2 - a1)


def thin_airfoil_section_lift(alpha: float, alpha_l0: float) -> float:
    return 2.0 * math.pi * (alpha - alpha_l0)


def section_state(
    alpha: float | None,
    alpha_l0: float | None,
    m_camber: float | None,
    p_camber: float | None,
) -> dict[str, object]:
    mean_line = m_camber is not None or p_camber is not None
    if mean_line:
        if m_camber is None or p_camber is None:
            raise ValueError("path B requires both --m and --p")
        if not math.isfinite(m_camber) or m_camber < 0.0 or m_camber >= 1.0:
            raise ValueError("--m must satisfy 0 <= m < 1")
        if not math.isfinite(p_camber) or p_camber <= 0.0 or p_camber >= 1.0:
            raise ValueError("--p must satisfy 0 < p < 1")
        if alpha_l0 is not None:
            raise ValueError("path B computes alpha_L0; do not also pass --alpha-l0")
        theta_p = naca4_glauert_station(p_camber)
        alpha_zero = naca4_zero_lift_angle(m_camber, p_camber, theta_p)
        a1 = naca4_glauert_a1(m_camber, p_camber, theta_p)
        a2 = naca4_glauert_a2(m_camber, p_camber)
        moment = naca4_quarter_chord_moment(a2, a1)
        state: dict[str, object] = {
            "path": "mean_line",
            "m": m_camber,
            "p": p_camber,
            "alpha_L0": alpha_zero,
            "A1": a1,
            "A2": a2,
            "cm_c4": moment,
            "cl_alpha": 2.0 * math.pi,
        }
        if alpha is not None:
            if not math.isfinite(alpha):
                raise ValueError("--alpha must be finite")
            state["alpha"] = alpha
            state["cl"] = thin_airfoil_section_lift(alpha, alpha_zero)
        return state
    if alpha is None:
        raise ValueError("requires --alpha, or --m with --p")
    if not math.isfinite(alpha):
        raise ValueError("--alpha must be finite")
    zero = 0.0 if alpha_l0 is None else alpha_l0
    if not math.isfinite(zero):
        raise ValueError("--alpha-l0 must be finite")
    return {
        "path": "angle",
        "alpha": alpha,
        "alpha_L0": zero,
        "alpha_L0_source": "default" if alpha_l0 is None else "flag",
        "cl_alpha": 2.0 * math.pi,
        "cl": thin_airfoil_section_lift(alpha, zero),
    }


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "path",
        "alpha",
        "alpha_L0",
        "alpha_L0_source",
        "m",
        "p",
        "A1",
        "A2",
        "cm_c4",
        "cl_alpha",
        "cl",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    alpha_l0 = float(result["alpha_L0"])
    if "alpha" in result:
        center = float(result["alpha"])
    else:
        center = alpha_l0
    grid = [center - 0.25 + 0.5 * i / 80.0 for i in range(81)]
    lift = [thin_airfoil_section_lift(value, alpha_l0) for value in grid]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(grid, lift, color="C0", label=r"$c_l$")
    ax.axhline(0.0, color="0.5", linewidth=0.8)
    ax.axvline(alpha_l0, color="0.6", linestyle=":", label=r"$\alpha_{L0}$")
    if "alpha" in result and "cl" in result:
        ax.plot(float(result["alpha"]), float(result["cl"]), "s", color="C0")
    if "cm_c4" in result:
        ax.annotate(
            rf"$c_{{m,c/4}}={float(result['cm_c4']):.4g}$",
            xy=(0.03, 0.95),
            xycoords="axes fraction",
            va="top",
        )
    ax.set_xlabel(r"Geometric angle of attack $\alpha$ [rad]")
    ax.set_ylabel(r"Section lift coefficient $c_l$")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    symmetric = section_state(1.0, None, None, None)
    if symmetric["alpha_L0_source"] != "default" or not close(float(symmetric["cl"]), 2.0 * math.pi):
        return fail("symmetric unit angle is not 2*pi")
    zero = section_state(-1.0 / 25.0, -1.0 / 25.0, None, None)
    if not close(float(zero["cl"]), 0.0):
        return fail("lift at alpha_L0 is not 0")
    arc = section_state(None, None, 1.0 / 50.0, 0.5)
    if not close(float(arc["alpha_L0"]), -1.0 / 25.0):
        return fail("two-percent circular-arc alpha_L0 is not -1/25")
    if not close(float(arc["A1"]), 4.0 / 50.0):
        return fail("two-percent circular-arc A1 is not 4/50")
    if not close(float(arc["A2"]), 0.0, 1e-10):
        return fail("two-percent circular-arc A2 is not 0")
    if not close(float(arc["cm_c4"]), -math.pi / 50.0):
        return fail("two-percent circular-arc cm_c4 is not -pi/50")
    lifted = section_state(0.0, None, 1.0 / 50.0, 0.5)
    if not close(float(lifted["cl"]), 2.0 * math.pi / 25.0):
        return fail("circular-arc lift at zero alpha is not 2*pi/25")
    try:
        section_state(None, None, None, None)
        return fail("an empty path was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(arc, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("alpha_L0_circular_arc", arc["alpha_L0"])
    print_kv("cm_c4_circular_arc", arc["cm_c4"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inviscid thin-airfoil section lift and moment.")
    parser.add_argument("--alpha", type=float, default=None, help="geometric angle of attack [rad]")
    parser.add_argument("--alpha-l0", type=float, default=None, dest="alpha_l0", help="zero-lift angle [rad]")
    parser.add_argument("--m", type=float, default=None, help="maximum camber as a fraction of chord")
    parser.add_argument("--p", type=float, default=None, help="chordwise station of maximum camber")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        result = section_state(args.alpha, args.alpha_l0, args.m, args.p)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "thin_airfoil_theory.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
