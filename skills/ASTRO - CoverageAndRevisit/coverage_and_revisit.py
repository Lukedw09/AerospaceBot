#!/usr/bin/env python3
"""Swath and equatorial revisit of one satellite above an elevation mask.

elevation_mask_earth_angle is lambda = pi/2 - eps - asin((R/(R+h))*cos(eps)).
The revisit count is for a single satellite at the equator.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Coverage and revisit"
G0 = 9.80665
R0_EARTH = 6.3742e6
OMEGA_EARTH = 7.292115e-5
N_CURVE = 161
EQUATOR_NOTE = "single satellite at the equator; higher latitudes are covered more often"
ASSUMPTIONS = (
    "spherical Earth; "
    "elevation_mask_earth_angle lambda = pi/2 - eps - asin((R0/(R0+h))*cos(eps)); "
    "swath arc 2*R0*lambda; footprint radius R0*lambda; "
    "nodal gap is Earth rotation over one Kepler period; "
    "equatorial revisit is the ceiling of that gap over the swath angle; "
    "not a Walker constellation and not a sensor narrower than the elevation mask"
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


def earth_angle(radius_planet: float, orbit_radius: float, elevation: float) -> float:
    """elevation_mask_earth_angle."""
    argument = (radius_planet / orbit_radius) * math.cos(elevation)
    if argument > 1.0 or argument < 0.0:
        raise ValueError("elevation is outside the geometric mask")
    rho = math.asin(argument)
    return math.pi / 2.0 - elevation - rho


def swath_arc(radius_planet: float, earth_central: float) -> float:
    """swath_arc."""
    return 2.0 * radius_planet * earth_central


def footprint_radius(radius_planet: float, earth_central: float) -> float:
    """footprint_radius."""
    return radius_planet * earth_central


def period(mu: float, semi_major: float) -> float:
    return 2.0 * math.pi * math.sqrt(semi_major**3 / mu)


def radius_from_inputs(alt: float | None, semi_major: float | None) -> float:
    if (alt is None) == (semi_major is None):
        raise ValueError("pass exactly one of --alt or --a")
    if alt is not None:
        require_positive("altitude", alt)
        return R0_EARTH + alt
    require_positive("semi-major axis", float(semi_major))
    if float(semi_major) <= R0_EARTH:
        raise ValueError("semi-major axis must be above the Earth radius")
    return float(semi_major)


def evaluate(orbit_radius: float, elevation: float) -> dict[str, float | str | int]:
    if not math.isfinite(elevation) or elevation < 0.0 or elevation >= math.pi / 2.0:
        raise ValueError("minimum elevation must be in [0, pi/2)")
    lam = earth_angle(R0_EARTH, orbit_radius, elevation)
    if lam <= 0.0:
        raise ValueError("the elevation mask leaves no swath")
    mu = G0 * R0_EARTH**2
    p = period(mu, orbit_radius)
    gap = OMEGA_EARTH * p
    passes = math.ceil(gap / (2.0 * lam) - 1e-12)
    if passes < 1:
        passes = 1
    return {
        "a_m": orbit_radius,
        "elev_min_rad": elevation,
        "lambda_rad": lam,
        "swath_m": swath_arc(R0_EARTH, lam),
        "footprint_m": footprint_radius(R0_EARTH, lam),
        "period_s": p,
        "nodal_gap_rad": gap,
        "revisit_periods": passes,
        "revisit_s": passes * p,
        "revisit_note": EQUATOR_NOTE,
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
        raise ValueError("matplotlib is required to plot swath") from exc
    return plt


def write_plot(result: dict[str, float | str | int], out_path: Path) -> None:
    plt = ensure_matplotlib()
    orbit_radius = float(result["a_m"])
    elevation = float(result["elev_min_rad"])
    span = linspace(0.0, math.pi / 2.0 * 0.98, N_CURVE)
    widths: list[float] = []
    angles: list[float] = []
    for item in span:
        try:
            lam = earth_angle(R0_EARTH, orbit_radius, item)
        except ValueError:
            continue
        if lam <= 0.0:
            continue
        angles.append(item)
        widths.append(swath_arc(R0_EARTH, lam) / 1000.0)
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(angles, widths, color="#1a5276", linewidth=1.8, label="swath")
    ax.plot(elevation, float(result["swath_m"]) / 1000.0, "s", color="#1a5276", markersize=7, label="mask")
    ax.set_xlabel("minimum elevation (rad)")
    ax.set_ylabel("swath (km)")
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


def emit(result: dict[str, float | str | int], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "a_m",
        "elev_min_rad",
        "lambda_rad",
        "swath_m",
        "footprint_m",
        "period_s",
        "nodal_gap_rad",
        "revisit_periods",
        "revisit_s",
        "revisit_note",
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
    radius = R0_EARTH + 600000.0
    lam = earth_angle(R0_EARTH, radius, 0.0)
    rho = math.asin(R0_EARTH / radius)
    if not close(lam, math.pi / 2.0 - rho):
        return fail("horizon angle")
    if not close(swath_arc(R0_EARTH, lam), 2.0 * footprint_radius(R0_EARTH, lam)):
        return fail("swath")
    zenith = earth_angle(R0_EARTH, radius, math.pi / 2.0 - 1e-6)
    if zenith >= lam:
        return fail("swath did not shrink toward zenith")
    result = evaluate(radius, 0.2)
    gap = float(result["nodal_gap_rad"])
    expected = math.ceil(gap / (2.0 * float(result["lambda_rad"])) - 1e-12)
    if int(result["revisit_periods"]) != expected:
        return fail("revisit count")
    if not close(float(result["revisit_s"]), expected * float(result["period_s"])):
        return fail("revisit time")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "coverage.png"
        code, text, err = capture(["--alt", "600000", "--elev-min", "0.2", "--out", str(png)])
        if code != 0:
            return fail(f"run failed: {err}")
        if "swath_m:" not in text or "revisit_periods:" not in text or EQUATOR_NOTE not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(["--alt", "600000", "--a", str(radius), "--elev-min", "0.2"])
        if code == 0:
            return fail("both radius paths were accepted")

    print("check: pass")
    print_kv("swath_m", result["swath_m"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Swath and equatorial revisit for one satellite.")
    parser.add_argument("--alt", type=float, default=None, help="circular altitude [m]")
    parser.add_argument("--a", type=float, default=None, help="circular radius [m]")
    parser.add_argument("--elev-min", type=float, default=None, help="minimum elevation [rad]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.elev_min is None or (args.alt is None) == (args.a is not None and args.alt is not None) or (
        args.alt is None and args.a is None
    ):
        if args.elev_min is None or (args.alt is None and args.a is None):
            print("error: requires --elev-min and exactly one of --alt or --a", file=sys.stderr)
            return 2
    if args.alt is not None and args.a is not None:
        print("error: pass exactly one of --alt or --a", file=sys.stderr)
        return 2
    try:
        result = evaluate(radius_from_inputs(args.alt, args.a), args.elev_min)
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
