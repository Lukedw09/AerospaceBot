#!/usr/bin/env python3
"""Laplace sphere of influence between a central body and a third body.

The isotropic radius is sphere_of_influence_radius. Masses use
gravitational_parameter then that same radius, or
sphere_of_influence_radius_from_mass. Central-body radii use
sphere_of_influence_in_central_radii. An optional satellite radius is
compared with the third-body sphere.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

G0 = 9.80665
G_CODATA = 6.67430e-11
R0_EARTH = 6.3742e6
PLOT_TITLE = "Sphere of influence"
CHECK_TOL = 1e-9
N_CIRCLE = 361
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "classical Laplace sphere of influence for patched-conic handoff; "
    "inverse-square point masses; isotropic radius is "
    "sphere_of_influence_radius r_SOI = D*(mu2/mu1)**(2/5), equal to "
    "sphere_of_influence_radius_from_mass when mu = G*M from "
    "gravitational_parameter with NIST CODATA 2022 G; "
    "angle-dependent Tisserand corrections from Burrows TM X-53485 are "
    "omitted; r_SOI is measured from the third-body center; "
    "sphere_of_influence_in_central_radii is r_SOI/R0; the reciprocal "
    "central-body sphere relative to the third body is the same record "
    "with swapped mus; Earth default uses mu = g0*R0^2 with "
    "g0 = 9.80665 m/s^2 and R0 = 6374200 m; an optional satellite radius "
    "is the distance from the third-body center"
)
PALETTE = {
    "central": "#1a5276",
    "third": "#922b21",
    "soi_third": "#b03a2e",
    "soi_central": "#2874a6",
    "line": "#7f8c8d",
    "sat": "#117a65",
    "grid": "#d5d8dc",
    "text": "#1b2631",
    "fill_central": "#d4e6f1",
    "fill_third": "#f5b7b1",
}


@dataclass(frozen=True)
class BodyState:
    radius: float
    mu: float
    mass: float | None
    mu_source: str
    radius_source: str
    mass_source: str | None


@dataclass(frozen=True)
class Solution:
    central: BodyState
    third: BodyState
    distance: float
    r_soi_third: float
    r_soi_central: float
    r_soi_over_r0: float
    mass_ratio: float
    mu_ratio: float
    satellite_radius: float | None
    satellite_location: str | None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(value: float, flag: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def require_positive(name: str, value: float) -> None:
    require_finite(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0")


def gravitational_parameter(mass: float, g_const: float = G_CODATA) -> float:
    """gravitational_parameter."""
    return g_const * mass


def sphere_of_influence_radius(distance: float, mu_secondary: float, mu_primary: float) -> float:
    """sphere_of_influence_radius."""
    return distance * (mu_secondary / mu_primary) ** (2.0 / 5.0)


def sphere_of_influence_radius_from_mass(
    distance: float, mass_secondary: float, mass_primary: float
) -> float:
    """sphere_of_influence_radius_from_mass."""
    return distance * (mass_secondary / mass_primary) ** (2.0 / 5.0)


def sphere_of_influence_in_central_radii(r_soi: float, radius: float) -> float:
    """sphere_of_influence_in_central_radii."""
    return r_soi / radius


def resolve_body(
    radius_arg: float | None,
    mu_arg: float | None,
    mass_arg: float | None,
    *,
    radius_flag: str,
    mu_flag: str,
    mass_flag: str,
    default_radius: float | None = None,
    allow_default_mu_from_radius: bool = False,
) -> BodyState:
    if mu_arg is not None and mass_arg is not None:
        raise ValueError(f"pass {mu_flag} or {mass_flag}, not both")
    if radius_arg is None:
        if default_radius is None:
            raise ValueError(f"{radius_flag} is required")
        radius = default_radius
        radius_source = "default"
    else:
        require_positive(radius_flag, radius_arg)
        radius = radius_arg
        radius_source = "input"
    mass: float | None = None
    mass_source: str | None = None
    if mass_arg is not None:
        require_positive(mass_flag, mass_arg)
        mass = mass_arg
        mass_source = "input"
        mu = gravitational_parameter(mass)
        mu_source = "mass"
    elif mu_arg is not None:
        require_positive(mu_flag, mu_arg)
        mu = mu_arg
        mu_source = "input"
    elif allow_default_mu_from_radius:
        mu = G0 * radius * radius
        mu_source = "g0_R0_sq"
    else:
        raise ValueError(f"requires {mu_flag} or {mass_flag}")
    return BodyState(
        radius=radius,
        mu=mu,
        mass=mass,
        mu_source=mu_source,
        radius_source=radius_source,
        mass_source=mass_source,
    )


def evaluate(
    central: BodyState,
    third: BodyState,
    distance: float,
    satellite_radius: float | None,
) -> Solution:
    require_positive("center-to-center distance", distance)
    if distance <= central.radius + third.radius:
        raise ValueError("center-to-center distance must exceed the sum of the body radii")
    if third.mu >= central.mu:
        raise ValueError("third-body mu must be smaller than the central-body mu")
    r_soi_third = sphere_of_influence_radius(distance, third.mu, central.mu)
    r_soi_central = sphere_of_influence_radius(distance, central.mu, third.mu)
    if central.mass is not None and third.mass is not None:
        from_mass = sphere_of_influence_radius_from_mass(distance, third.mass, central.mass)
        if abs(from_mass - r_soi_third) > CHECK_TOL * max(1.0, r_soi_third):
            raise ValueError("mass and mu sphere-of-influence radii disagree")
    r_over = sphere_of_influence_in_central_radii(r_soi_third, central.radius)
    location: str | None = None
    if satellite_radius is not None:
        require_positive("satellite radius", satellite_radius)
        if satellite_radius < third.radius:
            raise ValueError("satellite radius must be at or above the third-body surface")
        location = "inside" if satellite_radius <= r_soi_third else "outside"
    return Solution(
        central=central,
        third=third,
        distance=distance,
        r_soi_third=r_soi_third,
        r_soi_central=r_soi_central,
        r_soi_over_r0=r_over,
        mass_ratio=third.mu / central.mu,
        mu_ratio=third.mu / central.mu,
        satellite_radius=satellite_radius,
        satellite_location=location,
    )


def circle_xy(center_x: float, radius: float, count: int = N_CIRCLE) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for i in range(count):
        angle = 2.0 * math.pi * i / (count - 1)
        xs.append(center_x + radius * math.cos(angle))
        ys.append(radius * math.sin(angle))
    return xs, ys


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the sphere of influence") from exc
    return plt, Circle


def plot_png(path: Path, result: Solution) -> None:
    plt, Circle = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    c = result.central
    t = result.third
    d_km = result.distance / 1000.0
    r0_km = c.radius / 1000.0
    r3_km = t.radius / 1000.0
    soi3_km = result.r_soi_third / 1000.0
    soi1_km = result.r_soi_central / 1000.0

    ax.add_patch(
        Circle(
            (0.0, 0.0),
            r0_km,
            facecolor=PALETTE["fill_central"],
            edgecolor=PALETTE["central"],
            linewidth=1.6,
            zorder=3,
        )
    )
    ax.add_patch(
        Circle(
            (d_km, 0.0),
            r3_km,
            facecolor=PALETTE["fill_third"],
            edgecolor=PALETTE["third"],
            linewidth=1.6,
            zorder=3,
        )
    )

    xs, ys = circle_xy(d_km, soi3_km)
    ax.plot(xs, ys, color=PALETTE["soi_third"], linewidth=1.8, linestyle="--", label="third-body SOI", zorder=4)
    frame = max(d_km + max(r3_km, soi3_km), r0_km, soi3_km) * 1.18
    if soi1_km <= 1.35 * frame:
        xs1, ys1 = circle_xy(0.0, soi1_km)
        ax.plot(
            xs1,
            ys1,
            color=PALETTE["soi_central"],
            linewidth=1.3,
            linestyle=":",
            label="central-body SOI",
            zorder=2,
        )
    else:
        ax.plot([], [], color=PALETTE["soi_central"], linestyle=":", label="central-body SOI (beyond frame)")

    ax.plot([0.0, d_km], [0.0, 0.0], color=PALETTE["line"], linewidth=1.0, zorder=1)
    ax.plot(0.0, 0.0, "o", color=PALETTE["central"], markersize=5, zorder=5)
    ax.plot(d_km, 0.0, "o", color=PALETTE["third"], markersize=5, zorder=5)

    if result.satellite_radius is not None:
        sat_km = result.satellite_radius / 1000.0
        ax.plot(
            d_km + sat_km,
            0.0,
            marker="s",
            color=PALETTE["sat"],
            markersize=7,
            zorder=6,
            label=f"satellite ({result.satellite_location})",
        )
        frame = max(frame, d_km + sat_km)

    ax.set_xlim(-0.12 * frame, frame)
    ax.set_ylim(-0.55 * frame, 0.55 * frame)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(PLOT_TITLE, color=PALETTE["text"])
    ax.grid(True, color=PALETTE["grid"], alpha=0.7)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.text(
        0.0,
        -r0_km - 0.04 * frame,
        "central",
        ha="center",
        va="top",
        color=PALETTE["central"],
        fontsize=9,
    )
    ax.text(
        d_km,
        -max(r3_km, soi3_km) - 0.04 * frame,
        "third body",
        ha="center",
        va="top",
        color=PALETTE["third"],
        fontsize=9,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: Solution, path: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("R0_m", result.central.radius)
    print_kv("R0_source", result.central.radius_source)
    print_kv("g0_m_s2", G0)
    print_kv("G_m3_kg_s2", G_CODATA)
    print_kv("mu_m3_s2", result.central.mu)
    print_kv("mu_source", result.central.mu_source)
    if result.central.mass is not None:
        print_kv("M_kg", result.central.mass)
        print_kv("M_source", result.central.mass_source)
    print_kv("R3_m", result.third.radius)
    print_kv("R3_source", result.third.radius_source)
    print_kv("mu3_m3_s2", result.third.mu)
    print_kv("mu3_source", result.third.mu_source)
    if result.third.mass is not None:
        print_kv("M3_kg", result.third.mass)
        print_kv("M3_source", result.third.mass_source)
    print_kv("D_m", result.distance)
    print_kv("mu_ratio", result.mu_ratio)
    print_kv("r_SOI_m", result.r_soi_third)
    print_kv("r_SOI_central_radii", result.r_soi_over_r0)
    print_kv("r_SOI_central_m", result.r_soi_central)
    print_kv("r_SOI_central_third_radii", result.r_soi_central / result.third.radius)
    if result.satellite_radius is not None:
        print_kv("rsat_m", result.satellite_radius)
        print_kv("satellite_location", result.satellite_location)
    if result.r_soi_third + result.third.radius > result.distance - result.central.radius:
        print_kv(
            "warning",
            "third-body SOI reaches beyond the gap to the central surface; "
            "the isotropic Laplace model is only a patched-conic estimate",
        )
    if path is not None:
        print_kv("graph", str(path))


def run(ns: argparse.Namespace) -> int:
    central = resolve_body(
        ns.R0,
        ns.mu,
        ns.mass,
        radius_flag="--R0",
        mu_flag="--mu",
        mass_flag="--mass",
        default_radius=R0_EARTH,
        allow_default_mu_from_radius=True,
    )
    if ns.R3 is None:
        raise ValueError("--R3 is required")
    if ns.D is None:
        raise ValueError("--D is required")
    third = resolve_body(
        ns.R3,
        ns.mu3,
        ns.mass3,
        radius_flag="--R3",
        mu_flag="--mu3",
        mass_flag="--mass3",
    )
    result = evaluate(central, third, ns.D, ns.rsat)
    path: Path | None = None
    if not ns.no_plot:
        path = Path(ns.out) if ns.out else SKILL_DIR / "sphere_of_influence.png"
        path = path.resolve()
        plot_png(path, result)
    elif ns.out is not None:
        raise ValueError("pass --out only when a PNG is written")
    emit(result, path)
    return 0


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
    # Unit geometry: D = 32, mu1 = 32, mu2 = 1 => r_SOI = 8.
    r = sphere_of_influence_radius(32.0, 1.0, 32.0)
    if abs(r - 8.0) > CHECK_TOL:
        return fail("sphere_of_influence_radius unit case")
    if abs(sphere_of_influence_radius_from_mass(32.0, 1.0, 32.0) - 8.0) > CHECK_TOL:
        return fail("sphere_of_influence_radius_from_mass unit case")
    if abs(sphere_of_influence_in_central_radii(20.0, 2.0) - 10.0) > CHECK_TOL:
        return fail("sphere_of_influence_in_central_radii unit case")
    mu = gravitational_parameter(2.0, 3.0)
    if abs(mu - 6.0) > CHECK_TOL:
        return fail("gravitational_parameter unit case")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "soi.png"
        code, text, err = capture(
            [
                "--R0",
                "1",
                "--mu",
                "32",
                "--R3",
                "0.1",
                "--mu3",
                "1",
                "--D",
                "32",
                "--rsat",
                "4",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli unit case failed: {err}")
        if "r_SOI_m: 8" not in text:
            return fail("cli r_SOI was not 8")
        if "r_SOI_central_radii: 8" not in text:
            return fail("cli r_SOI/R0 was not 8")
        if "satellite_location: inside" not in text:
            return fail("cli satellite was not inside")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")

        code, text, err = capture(
            [
                "--R0",
                "1",
                "--mass",
                "32",
                "--R3",
                "0.1",
                "--mass3",
                "1",
                "--D",
                "32",
                "--no-plot",
            ]
        )
        if code != 0:
            return fail(f"mass path failed: {err}")
        if "mu_source: mass" not in text or "mu3_source: mass" not in text:
            return fail("mass path did not report mu from mass")
        # G*32 and G*1 keep the same ratio, so r_SOI stays 8.
        if "r_SOI_m: 8" not in text:
            return fail("mass path r_SOI was not 8")

        code, text, err = capture(
            [
                "--R0",
                "1",
                "--mu",
                "32",
                "--R3",
                "0.1",
                "--mu3",
                "1",
                "--D",
                "32",
                "--rsat",
                "20",
                "--no-plot",
            ]
        )
        if code != 0:
            return fail(f"outside satellite failed: {err}")
        if "satellite_location: outside" not in text:
            return fail("cli satellite was not outside")

        code, _text, err = capture(
            ["--R0", "1", "--mu", "1", "--mass", "1", "--R3", "0.1", "--mu3", "0.1", "--D", "10"]
        )
        if code == 0:
            return fail("accepted both --mu and --mass")

        code, text, err = capture(
            [
                "--R3",
                "1.737e6",
                "--mu3",
                "4.9048695e12",
                "--D",
                "3.844e8",
                "--no-plot",
            ]
        )
        # Earth defaults are allowed for the central body.
        if code != 0:
            return fail(f"Earth-default central body failed: {err}")
        if "R0_source: default" not in text or "mu_source: g0_R0_sq" not in text:
            return fail("Earth-default sources were not reported")
        if "r_SOI_m:" not in text:
            return fail("Earth-Moon style case omitted r_SOI")

        code, _text, err = capture(
            ["--R0", "1", "--mu", "32", "--mu3", "1", "--D", "32", "--no-plot"]
        )
        if code == 0:
            return fail("missing --R3 was accepted")

    print("check: pass")
    print_kv("unit_r_SOI_m", r)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Laplace sphere of influence of a third body relative to a "
            "central body, with optional satellite location and PNG."
        )
    )
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"central-body radius [m]; default Earth {R0_EARTH:.8g}",
    )
    parser.add_argument("--mu", type=float, default=None, help="central-body gravitational parameter [m^3/s^2]")
    parser.add_argument("--mass", type=float, default=None, help="central-body mass [kg]; mu = G*M")
    parser.add_argument("--R3", type=float, default=None, help="third-body radius [m]")
    parser.add_argument("--mu3", type=float, default=None, help="third-body gravitational parameter [m^3/s^2]")
    parser.add_argument("--mass3", type=float, default=None, help="third-body mass [kg]; mu3 = G*M3")
    parser.add_argument("--D", type=float, default=None, help="distance between the two centers [m]")
    parser.add_argument(
        "--rsat",
        type=float,
        default=None,
        help="optional satellite radius from the third-body center [m]",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="skip the PNG (optional figure)",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
