#!/usr/bin/env python3
"""One year of geostationary north-south and east-west station-keeping impulse.

North-south reuses plane_change_impulse, split across equal burns.
East-west is eccentricity_removal_impulse, 2*v*e.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Geostationary station-keeping"
G0 = 9.80665
R0_EARTH = 6.3742e6
OMEGA_EARTH = 7.292115e-5
ASSUMPTIONS = (
    "circular geostationary radius from mu = g0*R0^2 and the sidereal Earth rate; "
    "north-south reuses plane_change_impulse, 2*v*sin(di/2), summed over equal pieces of the yearly angle; "
    "east-west is eccentricity_removal_impulse, 2*v*e, two tangential burns of v*e; "
    "years scales both pieces; the figure is one year; "
    "not a station-keeping box, a longitude deadband, or a thruster duty cycle"
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


def geostationary_radius() -> float:
    mu = G0 * R0_EARTH**2
    return (mu / OMEGA_EARTH**2) ** (1.0 / 3.0)


def circular_speed(radius: float) -> float:
    return math.sqrt(G0 * R0_EARTH**2 / radius)


def plane_change(speed: float, angle: float) -> float:
    """plane_change_impulse."""
    return 2.0 * speed * math.sin(angle / 2.0)


def eccentricity_removal(speed: float, eccentricity: float) -> float:
    """eccentricity_removal_impulse."""
    return 2.0 * speed * eccentricity


def north_south(speed: float, di_year: float, burns: int) -> float:
    piece = di_year / burns
    return burns * plane_change(speed, piece)


def evaluate(di_year: float, e_year: float, burns: int, years: float) -> dict[str, float]:
    if not math.isfinite(di_year) or di_year < 0.0:
        raise ValueError("yearly inclination must be finite and >= 0")
    if not math.isfinite(e_year) or e_year < 0.0:
        raise ValueError("yearly eccentricity must be finite and >= 0")
    if burns < 1:
        raise ValueError("north-south burn count must be an integer >= 1")
    require_positive("years", years)
    radius = geostationary_radius()
    speed = circular_speed(radius)
    dv_ns_year = north_south(speed, di_year, burns)
    dv_ew_year = eccentricity_removal(speed, e_year)
    return {
        "a_m": radius,
        "v_m_s": speed,
        "di_year_rad": di_year,
        "e_year": e_year,
        "ns_burns": float(burns),
        "years": years,
        "dv_ns_year_m_s": dv_ns_year,
        "dv_ew_year_m_s": dv_ew_year,
        "dv_ns_m_s": dv_ns_year * years,
        "dv_ew_m_s": dv_ew_year * years,
        "dv_total_m_s": (dv_ns_year + dv_ew_year) * years,
    }


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the station-keeping budget") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    ns = float(result["dv_ns_year_m_s"])
    ew = float(result["dv_ew_year_m_s"])
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.bar(0, ns, color="#1a5276", width=0.6, label="north-south")
    ax.bar(1, ew, bottom=ns, color="#b9770e", width=0.6, label="east-west")
    ax.bar(2, ns + ew, color="#1e8449", width=0.6, label="one-year total")
    ax.set_xticks([0, 1, 2], ["north-south", "east-west", "total"])
    ax.set_ylabel("delta-v (m/s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, axis="y", alpha=0.35)
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


def emit(result: dict[str, float], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "a_m",
        "v_m_s",
        "di_year_rad",
        "e_year",
        "ns_burns",
        "years",
        "dv_ns_m_s",
        "dv_ew_m_s",
        "dv_total_m_s",
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
    speed = circular_speed(geostationary_radius())
    one = north_south(speed, 0.02, 1)
    if not close(one, plane_change(speed, 0.02)):
        return fail("single burn")
    split = north_south(speed, 0.02, 4)
    if not close(split, 4.0 * plane_change(speed, 0.005)):
        return fail("split burns")
    if split <= one:
        return fail("split burns did not follow the sine law")
    if not close(eccentricity_removal(speed, 1.0e-4), 2.0 * speed * 1.0e-4):
        return fail("eccentricity")
    result = evaluate(0.02, 1.0e-4, 2, 3.0)
    if not close(float(result["dv_total_m_s"]), 3.0 * (float(result["dv_ns_year_m_s"]) + float(result["dv_ew_year_m_s"]))):
        return fail("years")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "geo.png"
        code, text, err = capture(
            ["--di-year", "0.02", "--e-year", "0.0001", "--ns-burns", "2", "--years", "3", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "dv_ns_m_s:" not in text or "dv_ew_m_s:" not in text or "dv_total_m_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(["--di-year", "0.01"])
        if code == 0:
            return fail("missing eccentricity was accepted")

    print("check: pass")
    print_kv("v_m_s", speed)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Geostationary north-south and east-west impulses.")
    parser.add_argument("--di-year", type=float, default=None, help="inclination to remove each year [rad]")
    parser.add_argument("--e-year", type=float, default=None, help="eccentricity to remove each year")
    parser.add_argument("--ns-burns", type=int, default=1, help="equal north-south burns per year")
    parser.add_argument("--years", type=float, default=1.0, help="years to scale both budgets")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.di_year is None or args.e_year is None:
        print("error: requires --di-year and --e-year", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.di_year, args.e_year, args.ns_burns, args.years)
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
