#!/usr/bin/env python3
"""Magnetic dipole that produces a stated torque in a stated field.

magnetic_moment inverts magnetic_disturbance_torque: m = T/(B*sin(psi)).
magnetic_coil_current is m/(N*A) when both coil inputs are given.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Magnetic torquer sizing"
N_CURVE = 161
ASSUMPTIONS = (
    "magnetic_moment m = T/(B*sin(psi)), the inverse of magnetic_disturbance_torque; "
    "default angle is pi/2, the perpendicular dipole; "
    "magnetic_coil_current I = m/(N*A) only when turns and area are both given; "
    "the field is a user input; no Earth-field model, dipole tilt, or multi-coil pyramid"
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


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def magnetic_moment(torque: float, field: float, angle: float) -> float:
    """magnetic_moment."""
    sine = math.sin(angle)
    if sine <= 0.0:
        raise ValueError("the angle between the dipole and the field must give sin(psi) > 0")
    return torque / (field * sine)


def coil_current(moment: float, turns: float, area: float) -> float:
    """magnetic_coil_current."""
    return moment / (turns * area)


def margin(limit: float, value: float) -> float:
    return limit / value - 1.0


def evaluate(
    torque: float,
    field: float,
    angle: float,
    turns: float | None,
    area: float | None,
    m_max: float | None,
    i_max: float | None,
) -> dict[str, float | str]:
    require_positive("torque", torque)
    require_positive("field", field)
    if not math.isfinite(angle) or angle <= 0.0 or angle > math.pi:
        raise ValueError("magnetic angle must be in (0, pi]")
    moment = magnetic_moment(torque, field, angle)
    result: dict[str, float | str] = {
        "torque_N_m": torque,
        "B_T": field,
        "psi_rad": angle,
        "m_A_m2": moment,
    }
    if (turns is None) != (area is None):
        raise ValueError("pass both --turns and --area to print coil current")
    if turns is not None and area is not None:
        require_positive("turns", turns)
        require_positive("coil area", area)
        result["turns"] = turns
        result["area_m2"] = area
        result["I_A"] = coil_current(moment, turns, area)
    if m_max is not None:
        require_positive("dipole limit", m_max)
        result["m_max_A_m2"] = m_max
        result["margin_m"] = margin(m_max, moment)
    if i_max is not None:
        if "I_A" not in result:
            raise ValueError("coil current margin needs --turns and --area")
        require_positive("current limit", i_max)
        result["i_max_A"] = i_max
        result["margin_I"] = margin(i_max, float(result["I_A"]))
    return result


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the dipole") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    torque = float(result["torque_N_m"])
    angle = float(result["psi_rad"])
    field = float(result["B_T"])
    span = linspace(field / 5.0, field * 3.0, N_CURVE)
    moments = [magnetic_moment(torque, item, angle) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, moments, color="#1a5276", linewidth=1.8, label="required dipole")
    ax.plot(field, float(result["m_A_m2"]), "s", color="#1a5276", markersize=7, label="operating field")
    ax.set_xlabel("field (T)")
    ax.set_ylabel("magnetic moment (A m$^2$)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: dict[str, float | str], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "torque_N_m",
        "B_T",
        "psi_rad",
        "m_A_m2",
        "m_max_A_m2",
        "margin_m",
        "turns",
        "area_m2",
        "I_A",
        "i_max_A",
        "margin_I",
    ):
        if key in result:
            print_kv(key, result[key])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def capture(argv: list[str]) -> tuple[int, str, str]:
    from io import StringIO

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    moment = magnetic_moment(0.01, 5.0e-5, math.pi / 2.0)
    if not close(moment, 200.0):
        return fail("perpendicular moment")
    angled = magnetic_moment(0.01, 5.0e-5, math.pi / 6.0)
    if not close(angled, 0.01 / (5.0e-5 * 0.5)):
        return fail("angled moment")
    if not close(coil_current(200.0, 100.0, 0.02), 100.0):
        return fail("current")
    if not close(margin(400.0, 200.0), 1.0):
        return fail("margin")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "torquer.png"
        code, text, err = capture(
            [
                "--torque",
                "0.01",
                "--b-field",
                "5e-5",
                "--turns",
                "100",
                "--area",
                "0.02",
                "--m-max",
                "400",
                "--i-max",
                "200",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "m_A_m2: 200" not in text or "I_A: 100" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, text, err = capture(["--torque", "0.01", "--b-field", "5e-5"])
        if code != 0:
            return fail(f"dipole-only path failed: {err}")
        if "I_A:" in text:
            return fail("current was invented")
        code, _text, _err = capture(["--torque", "0.01", "--b-field", "5e-5", "--turns", "100"])
        if code == 0:
            return fail("turns without area were accepted")

    print("check: pass")
    print_kv("m_A_m2", moment)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Magnetic moment and optional coil current.")
    parser.add_argument("--torque", type=float, default=None, help="required torque [N m]")
    parser.add_argument("--b-field", type=float, default=None, help="local magnetic field [T]")
    parser.add_argument("--mag-angle", type=float, default=math.pi / 2.0, help="angle between dipole and field [rad]")
    parser.add_argument("--turns", type=float, default=None, help="coil turns")
    parser.add_argument("--area", type=float, default=None, help="area enclosed by one turn [m^2]")
    parser.add_argument("--m-max", type=float, default=None, help="dipole limit [A m^2]")
    parser.add_argument("--i-max", type=float, default=None, help="coil current limit [A]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.torque is None or args.b_field is None:
        print("error: requires --torque and --b-field", file=sys.stderr)
        return 2
    try:
        result = evaluate(
            args.torque,
            args.b_field,
            args.mag_angle,
            args.turns,
            args.area,
            args.m_max,
            args.i_max,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(result, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
