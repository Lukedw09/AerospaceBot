#!/usr/bin/env python3
"""First lateral slosh frequency of a flat free surface in a rigid upright cylinder.

propellant_slosh_frequency uses xi = 1.841, the first root of J1'(xi) = 0.
slosh_pendulum_length is g/omega^2.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Propellant slosh frequency"
G0 = 9.80665
XI = 1.841
SHALLOW_RATIO = 0.2
N_CURVE = 201
ASSUMPTIONS = (
    "flat free surface in a rigid upright circular cylinder; "
    "propellant_slosh_frequency omega^2 = (g/R)*xi*tanh(xi*h/R) with xi = 1.841; "
    "slosh_pendulum_length = g/omega^2; "
    "shallow: yes when h/R < 0.2; "
    "no baffles, curved meniscus, axial slosh, or control law"
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


def omega_squared(gravity: float, radius: float, height: float, xi: float = XI) -> float:
    return (gravity / radius) * xi * math.tanh(xi * height / radius)


def slosh_frequency(gravity: float, radius: float, height: float, xi: float = XI) -> float:
    """propellant_slosh_frequency, rad/s."""
    return math.sqrt(omega_squared(gravity, radius, height, xi))


def pendulum_length(gravity: float, omega: float) -> float:
    """slosh_pendulum_length."""
    return gravity / omega**2


def evaluate(radius: float, height: float, gravity: float) -> dict[str, float | str]:
    require_positive("tank radius", radius)
    require_positive("liquid depth", height)
    require_positive("acceleration", gravity)
    omega = slosh_frequency(gravity, radius, height)
    return {
        "radius_m": radius,
        "height_m": height,
        "g_m_s2": gravity,
        "xi": XI,
        "h_over_R": height / radius,
        "omega_rad_s": omega,
        "f_Hz": omega / (2.0 * math.pi),
        "pendulum_length_m": pendulum_length(gravity, omega),
        "shallow": "yes" if height / radius < SHALLOW_RATIO else "no",
    }


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
        raise ValueError("matplotlib is required to plot slosh frequency") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    radius = float(result["radius_m"])
    height = float(result["height_m"])
    gravity = float(result["g_m_s2"])
    span = linspace(0.05 * radius, 5.0 * radius, N_CURVE)
    freqs = [slosh_frequency(gravity, radius, item) / (2.0 * math.pi) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, freqs, color="#1a5276", linewidth=1.8, label="first lateral mode")
    ax.plot(height, float(result["f_Hz"]), "s", color="#1a5276", markersize=7, label="operating depth")
    ax.set_xlabel("liquid depth (m)")
    ax.set_ylabel("frequency (Hz)")
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
        "radius_m",
        "height_m",
        "g_m_s2",
        "xi",
        "h_over_R",
        "shallow",
        "omega_rad_s",
        "f_Hz",
        "pendulum_length_m",
    ):
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
    deep = slosh_frequency(G0, 1.0, 5.0)
    limit = math.sqrt((G0 / 1.0) * XI)
    if not close(deep, limit, tol=1e-4):
        return fail("deep-fill limit")
    omega = slosh_frequency(1.0, 1.0, 1.0, xi=1.0)
    if not close(omega, math.sqrt(math.tanh(1.0))):
        return fail("frequency")
    if not close(pendulum_length(G0, deep), G0 / deep**2):
        return fail("pendulum")
    shallow = evaluate(1.0, 0.1, G0)
    if shallow["shallow"] != "yes":
        return fail("shallow flag")
    deep_case = evaluate(1.0, 1.0, G0)
    if deep_case["shallow"] != "no":
        return fail("deep flag")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "slosh.png"
        code, text, err = capture(["--radius", "1", "--height", "0.1", "--g", "9.80665", "--out", str(png)])
        if code != 0:
            return fail(f"run failed: {err}")
        if "shallow: yes" not in text or "f_Hz:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("omega_rad_s", deep)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="First lateral slosh frequency in an upright cylinder.")
    parser.add_argument("--radius", type=float, default=None, help="tank inner radius [m]")
    parser.add_argument("--height", type=float, default=None, help="liquid depth [m]")
    parser.add_argument("--g", type=float, default=G0, help="axial acceleration [m/s^2]; default g0")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.radius is None or args.height is None:
        print("error: requires --radius and --height", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.radius, args.height, args.g)
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
