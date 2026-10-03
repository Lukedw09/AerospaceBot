#!/usr/bin/env python3
"""Finite-wing lift curve from a section slope, up to stall.

The wing slope is wing_lift_curve_slope. The induced angle at a lift
coefficient is induced_angle, which is elliptic_induced_angle when e = 1.
The straight line is wing_lift_coefficient. It ends at stall_angle, where
the line reaches CLmax. The section check uses section_lift_effective_angle
with alpha_s = alpha - alpha_L0.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Finite-wing lift curve"
N_CURVE = 201

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "straight lifting line; section lift is section_lift_effective_angle "
    "cl = a0*(alpha_s - alpha_i) with alpha_s = alpha - alpha_L0; "
    "wing slope is wing_lift_curve_slope "
    "a = a0/(1 + a0/(pi*AR*e)), per radian; "
    "induced angle is induced_angle alpha_i = CL/(pi*AR*e), in radians, "
    "and equals elliptic_induced_angle when e = 1; "
    "straight lift line is wing_lift_coefficient CL = a*(alpha - alpha_L0) "
    "while CL is below CLmax; the line ends at stall_angle "
    "alpha_stall = alpha_L0 + CLmax/a; "
    "0 < e <= 1; the printed induced angle is the value at CLmax; "
    "the figure is that straight line from the zero-lift angle to stall; "
    "angles in the program are radians"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def wing_slope(a0: float, aspect_ratio: float, efficiency: float) -> float:
    """wing_lift_curve_slope, per radian."""
    return a0 / (1.0 + a0 / (math.pi * aspect_ratio * efficiency))


def induced_angle(cl: float, aspect_ratio: float, efficiency: float) -> float:
    """induced_angle, radians. elliptic_induced_angle when efficiency is 1."""
    return cl / (math.pi * aspect_ratio * efficiency)


def wing_lift(slope: float, alpha: float, alpha_l0: float) -> float:
    """wing_lift_coefficient."""
    return slope * (alpha - alpha_l0)


def stall_angle(alpha_l0: float, clmax: float, slope: float) -> float:
    """stall_angle."""
    return alpha_l0 + clmax / slope


def section_lift(a0: float, alpha_s: float, alpha_i: float) -> float:
    """section_lift_effective_angle."""
    return a0 * (alpha_s - alpha_i)


def lift_curve(
    a0: float,
    alpha_l0: float,
    clmax: float,
    aspect_ratio: float,
    efficiency: float,
) -> dict[str, float]:
    slope = wing_slope(a0, aspect_ratio, efficiency)
    alpha_stall = stall_angle(alpha_l0, clmax, slope)
    alpha_i_stall = induced_angle(clmax, aspect_ratio, efficiency)
    return {
        "a_per_rad": slope,
        "a_per_deg": slope * math.pi / 180.0,
        "alpha_i_stall_rad": alpha_i_stall,
        "alpha_i_stall_deg": math.degrees(alpha_i_stall),
        "alpha_stall_rad": alpha_stall,
        "alpha_stall_deg": math.degrees(alpha_stall),
    }


def curve_points(
    slope: float,
    alpha_l0: float,
    alpha_stall: float,
) -> tuple[list[float], list[float]]:
    """Straight line from zero lift to stall."""
    alphas: list[float] = []
    lifts: list[float] = []
    span = alpha_stall - alpha_l0
    for i in range(N_CURVE):
        alpha = alpha_l0 + span * i / (N_CURVE - 1)
        alphas.append(alpha)
        lifts.append(wing_lift(slope, alpha, alpha_l0))
    return alphas, lifts


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to draw the lift curve") from exc
    return plt


def plot_curve(
    path: Path,
    slope: float,
    alpha_l0: float,
    clmax: float,
    alpha_stall: float,
) -> None:
    plt = ensure_matplotlib()
    alphas, lifts = curve_points(slope, alpha_l0, alpha_stall)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(alphas, lifts, color="#1a5276", linewidth=1.8, label="straight lift line")
    ax.plot(
        alpha_stall,
        clmax,
        "s",
        color="#c0392b",
        markersize=7,
        zorder=5,
        label="stall",
    )
    ax.set_xlabel("geometric angle of attack (rad)")
    ax.set_ylabel("lift coefficient")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    a0: float,
    alpha_l0: float,
    clmax: float,
    aspect_ratio: float,
    efficiency: float,
    result: dict[str, float],
    path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("a0_per_rad", a0)
    print_kv("alpha_L0_rad", alpha_l0)
    print_kv("alpha_L0_deg", math.degrees(alpha_l0))
    print_kv("CLmax", clmax)
    print_kv("AR", aspect_ratio)
    print_kv("e", efficiency)
    print_kv("a_per_rad", result["a_per_rad"])
    print_kv("a_per_deg", result["a_per_deg"])
    print_kv("alpha_i_stall_rad", result["alpha_i_stall_rad"])
    print_kv("alpha_i_stall_deg", result["alpha_i_stall_deg"])
    print_kv("alpha_stall_rad", result["alpha_stall_rad"])
    print_kv("alpha_stall_deg", result["alpha_stall_deg"])
    print_kv("graph", path)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    a0 = 2.0 * math.pi
    aspect = 6.0
    efficiency = 1.0
    clmax = 1.2
    alpha_l0 = -0.04
    result = lift_curve(a0, alpha_l0, clmax, aspect, efficiency)
    if near(result["a_per_rad"], 1.5 * math.pi, "elliptic thin-airfoil slope"):
        return 1
    if near(result["a_per_rad"], a0 * aspect / (aspect + 2.0), "TN 1862 elliptic slope"):
        return 1
    if near(
        result["alpha_i_stall_rad"],
        clmax / (math.pi * aspect),
        "elliptic induced angle at stall",
    ):
        return 1
    alpha_s = result["alpha_stall_rad"] - alpha_l0
    section = section_lift(a0, alpha_s, result["alpha_i_stall_rad"])
    if near(section, clmax, "section lift at stall"):
        return 1
    if near(
        wing_lift(result["a_per_rad"], result["alpha_stall_rad"], alpha_l0),
        clmax,
        "wing lift at stall",
    ):
        return 1

    other = lift_curve(5.0, 0.02, 0.4, 8.0, 0.8)
    want_slope = 160.0 * math.pi / (32.0 * math.pi + 25.0)
    if near(other["a_per_rad"], want_slope, "efficiency slope"):
        return 1
    if near(induced_angle(1.0, 5.0, 0.8), 1.0 / (4.0 * math.pi), "induced angle"):
        return 1
    if near(stall_angle(0.02, 0.4, 5.0), 0.1, "stall angle"):
        return 1
    if near(induced_angle(1.0, 5.0, 1.0), 1.0 / (5.0 * math.pi), "elliptic induced angle"):
        return 1

    alphas, lifts = curve_points(result["a_per_rad"], alpha_l0, result["alpha_stall_rad"])
    if len(alphas) != N_CURVE:
        return fail("lift curve point count")
    if near(alphas[0], alpha_l0, "curve starts at zero lift"):
        return 1
    if near(lifts[0], 0.0, "lift at the zero-lift angle"):
        return 1
    if near(alphas[-1], result["alpha_stall_rad"], "curve ends at stall"):
        return 1
    if near(lifts[-1], clmax, "lift at stall"):
        return 1

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "lift_curve.pdf")
        code, text, err = capture(
            [
                "--a0",
                str(a0),
                "--alpha-l0",
                str(alpha_l0),
                "--clmax",
                str(clmax),
                "--ar",
                str(aspect),
                "--e",
                str(efficiency),
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"%PDF"):
            return fail("run did not write a PDF")
        for key in (
            "title: Finite-wing lift curve",
            "a_per_rad:",
            "alpha_i_stall_rad:",
            "alpha_stall_rad:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

    code, _text, _err = capture(
        ["--a0", "6", "--alpha-l0", "0", "--clmax", "1.2", "--ar", "6"]
    )
    if code != 2:
        return fail("missing efficiency was accepted")
    code, _text, _err = capture([])
    if code != 2:
        return fail("missing inputs were accepted")
    code, _text, _err = capture(
        ["--a0", "6", "--alpha-l0", "0", "--clmax", "1.2", "--ar", "6", "--e", "1.1"]
    )
    if code != 2:
        return fail("efficiency above 1 was accepted")
    code, _text, _err = capture(
        ["--a0", "-1", "--alpha-l0", "0", "--clmax", "1.2", "--ar", "6", "--e", "1"]
    )
    if code != 2:
        return fail("negative section slope was accepted")

    print("check: pass")
    print_kv("a_per_rad", result["a_per_rad"])
    print_kv("alpha_i_stall_rad", result["alpha_i_stall_rad"])
    print_kv("alpha_stall_rad", result["alpha_stall_rad"])
    return 0


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def validate(
    a0: float,
    alpha_l0: float,
    clmax: float,
    aspect_ratio: float,
    efficiency: float,
) -> None:
    require_positive("section lift-curve slope", a0)
    if not math.isfinite(alpha_l0):
        raise ValueError("zero-lift angle must be finite")
    require_positive("CLmax", clmax)
    require_positive("aspect ratio", aspect_ratio)
    if not math.isfinite(efficiency) or efficiency <= 0.0 or efficiency > 1.0:
        raise ValueError("span efficiency must be finite, > 0, and <= 1")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Wing lift-curve slope, induced angle at stall, and a PDF of "
            "lift coefficient versus angle of attack up to stall."
        )
    )
    parser.add_argument("--a0", type=float, default=None, help="section lift-curve slope [1/rad]")
    parser.add_argument("--alpha-l0", type=float, default=None, help="zero-lift angle [rad]")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio")
    parser.add_argument("--e", type=float, default=None, help="span efficiency, 0 < e <= 1")
    parser.add_argument("--out", type=str, default=None, help="PDF path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--a0": args.a0,
        "--alpha-l0": args.alpha_l0,
        "--clmax": args.clmax,
        "--ar": args.ar,
        "--e": args.e,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --a0, --alpha-l0, --clmax, --ar, and --e; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        validate(args.a0, args.alpha_l0, args.clmax, args.ar, args.e)
        result = lift_curve(args.a0, args.alpha_l0, args.clmax, args.ar, args.e)
        out_path = Path(args.out) if args.out else SKILL_DIR / "finite_wing_lift_curve.pdf"
        out_path = out_path.resolve()
        plot_curve(
            out_path,
            result["a_per_rad"],
            args.alpha_l0,
            args.clmax,
            result["alpha_stall_rad"],
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(args.a0, args.alpha_l0, args.clmax, args.ar, args.e, result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
