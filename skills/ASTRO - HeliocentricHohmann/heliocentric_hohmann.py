#!/usr/bin/env python3
"""Heliocentric Hohmann coast between two circular orbits.

The half-ellipse, phase angle, and synodic period are hohmann_phase_angle,
synodic_period, vis_viva, and elliptic_half_period. Excess speeds are the
coplanar speed difference and inclined_excess_speed. They are not the
planet-centered rocket burns.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
BODY_DIR = SKILL_DIR.parent / "ASTRO - SolarSystemBody"
if str(BODY_DIR) not in sys.path:
    sys.path.insert(0, str(BODY_DIR))

import solar_system_body as bodies  # noqa: E402

CHECK_TOL = 1e-9
PLOT_TITLE = "Heliocentric Hohmann"
SCALE_M = 1.0e9
ASSUMPTIONS = (
    "impulsive heliocentric Hohmann coast between two circular orbits about "
    "the Sun; inverse-square gravity and no drag, thrust, or third body on "
    "the coast; the coast is half of the transfer ellipse; circular speeds "
    "and coast speeds are vis_viva; time of flight is elliptic_half_period; "
    "the target lead angle is hohmann_phase_angle wrapped into (-pi, pi]; "
    "the synodic period is synodic_period; coplanar excess is the absolute "
    "speed difference; inclined excess is inclined_excess_speed with the "
    "whole inclination difference at that apsis; those excess speeds are not "
    "the planet-centered rocket burns; the line of nodes is assumed to lie "
    "on the apsidal line; eccentricity selects only the circular radius"
)


@dataclass(frozen=True)
class Hohmann:
    mode: str
    radius_mode: str
    depart_name: str
    arrive_name: str
    mu: float
    r_depart: float
    r_arrive: float
    i_depart: float
    i_arrive: float
    di: float
    direction: str
    a: float
    e: float
    v_planet_depart: float
    v_planet_arrive: float
    v_transfer_depart: float
    v_transfer_arrive: float
    sense_depart: str
    sense_arrive: str
    vinf_depart_coplanar: float
    vinf_arrive_coplanar: float
    vinf_depart_inclined: float
    vinf_arrive_inclined: float
    tof: float
    period: float
    n_depart: float
    n_arrive: float
    phase: float
    synodic: float


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        if math.isinf(value):
            text = "inf"
        else:
            text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = max(abs(expected), abs(got), 1.0 if scale is None else abs(scale))
    return abs(got - expected) <= CHECK_TOL * span


def require_positive(value: float, flag: str) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be finite and > 0")


def vis_viva(mu: float, radius: float, semi_major: float) -> float:
    argument = mu * (2.0 / radius - 1.0 / semi_major)
    if argument < 0.0:
        if argument > -1e-9 * (mu / radius):
            argument = 0.0
        else:
            raise ValueError("transfer speed is not real at that radius")
    return math.sqrt(argument)


def inclined_excess(v1: float, v2: float, di: float) -> float:
    """inclined_excess_speed."""
    argument = v1 * v1 + v2 * v2 - 2.0 * v1 * v2 * math.cos(di)
    if argument < 0.0:
        argument = 0.0
    return math.sqrt(argument)


def wrap_phase(angle: float) -> float:
    """Wrap into (-pi, pi]."""
    turned = math.remainder(angle, 2.0 * math.pi)
    if turned <= -math.pi:
        turned += 2.0 * math.pi
    return turned


def solve_hohmann(
    mu: float,
    r_depart: float,
    r_arrive: float,
    i_depart: float,
    i_arrive: float,
    mode: str,
    radius_mode: str,
    depart_name: str,
    arrive_name: str,
) -> Hohmann:
    require_positive(mu, "mu")
    require_positive(r_depart, "departure radius")
    require_positive(r_arrive, "arrival radius")
    semi_major = 0.5 * (r_depart + r_arrive)
    if r_arrive > r_depart:
        direction = "outward"
        eccentricity = (r_arrive - r_depart) / (r_arrive + r_depart)
        sense_depart = "prograde"
        sense_arrive = "retrograde"
    elif r_depart > r_arrive:
        direction = "inward"
        eccentricity = (r_depart - r_arrive) / (r_depart + r_arrive)
        sense_depart = "retrograde"
        sense_arrive = "prograde"
    else:
        direction = "coast"
        eccentricity = 0.0
        sense_depart = "none"
        sense_arrive = "none"
    v_depart = math.sqrt(mu / r_depart)
    v_arrive = math.sqrt(mu / r_arrive)
    vt_depart = vis_viva(mu, r_depart, semi_major)
    vt_arrive = vis_viva(mu, r_arrive, semi_major)
    period = 2.0 * math.pi * math.sqrt(semi_major**3 / mu)
    tof = 0.5 * period
    n_depart = math.sqrt(mu / r_depart**3)
    n_arrive = math.sqrt(mu / r_arrive**3)
    phase = wrap_phase(math.pi - n_arrive * tof)
    if math.isclose(n_depart, n_arrive, rel_tol=0.0, abs_tol=0.0):
        synodic = math.inf
    else:
        synodic = 2.0 * math.pi / abs(n_depart - n_arrive)
    di = abs(i_arrive - i_depart)
    return Hohmann(
        mode=mode,
        radius_mode=radius_mode,
        depart_name=depart_name,
        arrive_name=arrive_name,
        mu=mu,
        r_depart=r_depart,
        r_arrive=r_arrive,
        i_depart=i_depart,
        i_arrive=i_arrive,
        di=di,
        direction=direction,
        a=semi_major,
        e=eccentricity,
        v_planet_depart=v_depart,
        v_planet_arrive=v_arrive,
        v_transfer_depart=vt_depart,
        v_transfer_arrive=vt_arrive,
        sense_depart=sense_depart,
        sense_arrive=sense_arrive,
        vinf_depart_coplanar=abs(vt_depart - v_depart),
        vinf_arrive_coplanar=abs(vt_arrive - v_arrive),
        vinf_depart_inclined=inclined_excess(vt_depart, v_depart, di),
        vinf_arrive_inclined=inclined_excess(vt_arrive, v_arrive, di),
        tof=tof,
        period=period,
        n_depart=n_depart,
        n_arrive=n_arrive,
        phase=phase,
        synodic=synodic,
    )


def linspace(lo: float, hi: float, count: int) -> list[float]:
    step = (hi - lo) / (count - 1)
    return [lo + step * i for i in range(count - 1)] + [hi]


def conic_xy(semi_major: float, eccentricity: float, nu0: float, nu1: float, count: int = 241) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for nu in linspace(nu0, nu1, count):
        radius = semi_major * (1.0 - eccentricity * eccentricity) / (1.0 + eccentricity * math.cos(nu))
        xs.append(radius * math.cos(nu) / SCALE_M)
        ys.append(radius * math.sin(nu) / SCALE_M)
    return xs, ys


def circle_xy(radius: float, count: int = 361) -> tuple[list[float], list[float]]:
    return conic_xy(radius, 0.0, 0.0, 2.0 * math.pi, count)


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the heliocentric Hohmann") from exc
    return plt


def plot_hohmann(path: Path, transfer: Hohmann, title: str, arrows: bool) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    dx, dy = circle_xy(transfer.r_depart)
    ax.plot(dx, dy, color="#1f4e79", linewidth=1.2, label="departure orbit")
    ax.plot(*circle_xy(transfer.r_arrive), color="#b85c38", linewidth=1.2, label="arrival orbit")
    if transfer.direction == "inward":
        nu0, nu1 = math.pi, 2.0 * math.pi
        depart_nu = math.pi
        arrive_nu = 2.0 * math.pi
    else:
        nu0, nu1 = 0.0, math.pi
        depart_nu = 0.0
        arrive_nu = math.pi
    ax.plot(*conic_xy(transfer.a, transfer.e, nu0, nu1), color="#222222", linewidth=2.0, label="transfer")
    ax.scatter([0.0], [0.0], s=28, color="#e6b800", zorder=4)
    if arrows:
        _draw_arrow(ax, transfer, depart_nu, transfer.sense_depart, "Δv")
        _draw_arrow(ax, transfer, arrive_nu, transfer.sense_arrive, "Δv")
    span = 1.15 * max(transfer.r_depart, transfer.r_arrive) / SCALE_M
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.set_aspect("equal")
    ax.set_xlabel("X (10^6 km)")
    ax.set_ylabel("Y (10^6 km)")
    ax.set_title(title)
    ax.annotate(
        f"di = {math.degrees(transfer.di):.3g} deg",
        xy=(0.03, 0.97),
        xycoords="axes fraction",
        va="top",
        fontsize=10,
    )
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _draw_arrow(ax, transfer: Hohmann, nu: float, sense: str, label: str) -> None:
    if sense == "none":
        return
    radius = transfer.a * (1.0 - transfer.e * transfer.e) / (1.0 + transfer.e * math.cos(nu))
    x = radius * math.cos(nu) / SCALE_M
    y = radius * math.sin(nu) / SCALE_M
    sign = 1.0 if sense == "prograde" else -1.0
    length = 0.12 * min(transfer.r_depart, transfer.r_arrive) / SCALE_M
    tx = -sign * math.sin(nu) * length
    ty = sign * math.cos(nu) * length
    ax.annotate(
        "",
        xy=(x + tx, y + ty),
        xytext=(x, y),
        arrowprops={"arrowstyle": "->", "color": "#c0392b", "lw": 1.6},
    )
    ax.annotate(label, xy=(x + tx, y + ty), fontsize=8, color="#c0392b")


def report(transfer: Hohmann, graph: Path) -> None:
    print_kv("mode", transfer.mode)
    print_kv("radius_mode", transfer.radius_mode)
    print_kv("from", transfer.depart_name)
    print_kv("to", transfer.arrive_name)
    print_kv("mu_m3_s2", transfer.mu)
    print_kv("r_depart_m", transfer.r_depart)
    print_kv("r_arrive_m", transfer.r_arrive)
    print_kv("i_depart_rad", transfer.i_depart)
    print_kv("i_arrive_rad", transfer.i_arrive)
    print_kv("di_rad", transfer.di)
    print_kv("direction", transfer.direction)
    print_kv("a_m", transfer.a)
    print_kv("e", transfer.e)
    print_kv("v_planet_depart_m_s", transfer.v_planet_depart)
    print_kv("v_planet_arrive_m_s", transfer.v_planet_arrive)
    print_kv("v_transfer_depart_m_s", transfer.v_transfer_depart)
    print_kv("v_transfer_arrive_m_s", transfer.v_transfer_arrive)
    print_kv("sense_depart", transfer.sense_depart)
    print_kv("sense_arrive", transfer.sense_arrive)
    print_kv("vinf_depart_coplanar_m_s", transfer.vinf_depart_coplanar)
    print_kv("vinf_arrive_coplanar_m_s", transfer.vinf_arrive_coplanar)
    print_kv("vinf_depart_inclined_m_s", transfer.vinf_depart_inclined)
    print_kv("vinf_arrive_inclined_m_s", transfer.vinf_arrive_inclined)
    print_kv("tof_s", transfer.tof)
    print_kv("period_s", transfer.period)
    print_kv("n_depart_rad_s", transfer.n_depart)
    print_kv("n_arrive_rad_s", transfer.n_arrive)
    print_kv("phase_rad", transfer.phase)
    print_kv("synodic_s", transfer.synodic)
    print_kv("graph", str(graph))
    print_kv("assumptions", ASSUMPTIONS)
    if math.isinf(transfer.synodic):
        print_kv("warning", "equal mean motions have no finite synodic period")
    print_kv(
        "warning",
        "excess speeds are heliocentric; the rocket burns are planet-centered",
    )


def from_names(depart: str, arrive: str, radius_mode: str) -> Hohmann:
    table = bodies.load_bodies()
    left = bodies.require_body(table, depart)
    right = bodies.require_body(table, arrive)
    if left.name == "sun" or right.name == "sun":
        raise ValueError("the Sun is the central body, not a transfer endpoint")
    if left.name == right.name:
        raise ValueError("from and to must be different bodies")
    return solve_hohmann(
        table["sun"].mu,
        left.heliocentric_radius(radius_mode),
        right.heliocentric_radius(radius_mode),
        0.0 if left.i_rad is None else left.i_rad,
        0.0 if right.i_rad is None else right.i_rad,
        "bodies",
        radius_mode,
        left.name,
        right.name,
    )


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    unit = solve_hohmann(1.0, 1.0, 4.0, 0.0, 0.0, "radii", "mean", "r1", "r2")
    if not close_enough(unit.tof, 0.5 * unit.period, unit.period):
        return fail("time of flight is not half the period")
    if not close_enough(unit.a, 2.5, 2.5):
        return fail("semi-major axis")
    if not close_enough(unit.vinf_depart_coplanar, abs(unit.v_transfer_depart - unit.v_planet_depart), 1.0):
        return fail("coplanar departure excess")
    flat = solve_hohmann(1.0, 1.0, 4.0, 0.3, 0.3, "radii", "mean", "r1", "r2")
    if not close_enough(flat.vinf_depart_inclined, flat.vinf_depart_coplanar, 1.0):
        return fail("zero inclination did not match the coplanar excess")
    turned = math.remainder(unit.phase + unit.n_arrive * unit.tof - math.pi, 2.0 * math.pi)
    if not close_enough(turned, 0.0, 1.0):
        return fail("phase angle identity")
    if unit.phase <= -math.pi or unit.phase > math.pi:
        return fail("phase angle is outside (-pi, pi]")
    mars = from_names("earth", "mars", "mean")
    if mars.direction != "outward":
        return fail("Earth to Mars should be outward")
    if mars.di <= 0.0:
        return fail("Earth to Mars inclination difference")
    inward = from_names("earth", "venus", "mean")
    if inward.direction != "inward" or inward.sense_depart != "retrograde":
        return fail("Earth to Venus sense")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "heliocentric_hohmann.png"
        plot_hohmann(out, mars, PLOT_TITLE, arrows=False)
        data = out.read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("plot did not write a PNG")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Heliocentric Hohmann coast between two circular orbits.")
    parser.add_argument("--from", dest="depart", type=str, default=None, help="departure body")
    parser.add_argument("--to", dest="arrive", type=str, default=None, help="arrival body")
    parser.add_argument("--r1", type=float, default=None, help="departure heliocentric radius, m")
    parser.add_argument("--r2", type=float, default=None, help="arrival heliocentric radius, m")
    parser.add_argument("--mu", type=float, default=None, help="solar gravitational parameter, m^3/s^2")
    parser.add_argument("--i1", type=float, default=None, help="departure inclination, rad")
    parser.add_argument("--i2", type=float, default=None, help="arrival inclination, rad")
    parser.add_argument(
        "--radius-mode",
        choices=bodies.RADIUS_MODES,
        default="mean",
        help="which circular radius a named body uses",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    args = parser.parse_args(argv)
    if args.check:
        return run_check()
    try:
        named = args.depart is not None or args.arrive is not None
        radial = args.r1 is not None or args.r2 is not None or args.mu is not None
        if named and radial:
            raise ValueError("pass body names or --r1, --r2, and --mu, not both")
        if named:
            if args.depart is None or args.arrive is None:
                raise ValueError("pass both --from and --to")
            if args.i1 is not None or args.i2 is not None:
                raise ValueError("inclinations come from the body table when names are used")
            transfer = from_names(args.depart, args.arrive, args.radius_mode)
        else:
            if args.r1 is None or args.r2 is None or args.mu is None:
                raise ValueError("pass --from and --to, or --r1, --r2, and --mu")
            i1 = 0.0 if args.i1 is None else args.i1
            i2 = 0.0 if args.i2 is None else args.i2
            transfer = solve_hohmann(args.mu, args.r1, args.r2, i1, i2, "radii", "radii", "r1", "r2")
        out = Path(args.out) if args.out else SKILL_DIR / "heliocentric_hohmann.png"
        plot_hohmann(out.resolve(), transfer, PLOT_TITLE, arrows=False)
        report(transfer, out.resolve())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
