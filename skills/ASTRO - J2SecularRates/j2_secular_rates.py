#!/usr/bin/env python3
"""First-order J2 nodal and apsidal rates, and sun-synchronous inclination.

Rates are j2_nodal_rate and j2_apsidal_rate. The sun-synchronous nodal target
is sun_sync_nodal_rate. The matching inclination cosine is
sun_sync_inclination_cosine. Mean motion is mean_motion.
"""

from __future__ import annotations

import argparse
import io
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "ASTRO - J2SecularRates"
CHECK_TOL = 1e-9
G0 = 9.80665
R0_EARTH = 6.3742e6
AE_WGS84 = 6378137.0
J2_GSFC = 1.08228e-3
YEAR_DAYS = 365.2422
DAY_S = 86400.0
N_PLOT = 361
_OP = None
ASSUMPTIONS = (
    "first-order J2 secular rates on an ellipse; a, e, and i have no secular "
    "J2 rate; drag, third body, and higher zonals are omitted; nodal rate is "
    "j2_nodal_rate and apsidal rate is j2_apsidal_rate; mean motion is "
    "mean_motion; mu = g0*R0^2 with g0 = 9.80665 m/s^2; Earth default "
    "R0 = 6374200 m; RE is the equatorial radius in the J2 term, default "
    "WGS 84 ae = 6378137 m; J2 default is 1.08228e-3 (GSFC, March 1986, "
    "NASA RP-1204); sun-synchronous nodal rate is sun_sync_nodal_rate with "
    "Y = 365.2422 days from the GDC Orbit Primer (0.9856 deg/day); "
    "sun-synchronous inclination cosine is sun_sync_inclination_cosine; "
    "element angles are radians; --greenwich and --di are accepted from "
    "GroundTrackEarth or PlaneChangeImpulse and do not enter the rates; "
    "a NORAD two-line element set may be passed with --tle and is used as a "
    "Keplerian ellipse: line-2 angles are degrees, semi-major axis is the "
    "inverse of mean_motion from the published mean motion in revolutions per "
    "86400 s and this mu, and BSTAR, mean-motion derivatives, SGP4, and the "
    "epoch do not change the rates"
)
PALETTE = {
    "nodal": "#1a5276",
    "apsidal": "#6c3483",
    "sun": "#b7950b",
    "current": "#922b21",
    "sync": "#117a65",
    "critical": "#7b241c",
    "grid": "#d5d8dc",
    "text": "#1b2631",
    "zero": "#7f8c8d",
}


@dataclass(frozen=True)
class Body:
    radius: float
    g0: float
    mu: float
    ae: float
    j2: float
    year_days: float
    radius_source: str
    ae_source: str
    j2_source: str
    year_source: str


@dataclass(frozen=True)
class Rates:
    n: float
    p: float
    omega_dot_node: float
    omega_dot_apsis: float
    sun_sync_rate: float
    cosine_ss: float
    i_ss: float | None


def op_mod():
    """OrbitalParameters helpers. This skill does not call that program's run()."""
    global _OP
    if _OP is None:
        folder = str(SKILL_DIR.parent / "ASTRO - OrbitalParameters")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import orbital_parameters as imported

        _OP = imported
    return _OP


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(value: float, flag: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def mean_motion(mu: float, semi_major: float) -> float:
    """mean_motion."""
    return math.sqrt(mu / semi_major**3)


def j2_nodal_rate(n: float, j2: float, re: float, inc: float, a: float, ecc: float) -> float:
    """j2_nodal_rate."""
    return -3.0 * n * j2 * re**2 * math.cos(inc) / (2.0 * a**2 * (1.0 - ecc**2) ** 2)


def j2_apsidal_rate(n: float, j2: float, re: float, inc: float, a: float, ecc: float) -> float:
    """j2_apsidal_rate."""
    return (
        3.0
        * n
        * j2
        * re**2
        * (4.0 - 5.0 * math.sin(inc) ** 2)
        / (4.0 * a**2 * (1.0 - ecc**2) ** 2)
    )


def sun_sync_nodal_rate(year_days: float) -> float:
    """sun_sync_nodal_rate."""
    return 2.0 * math.pi / (year_days * DAY_S)


def sun_sync_inclination_cosine(
    omegadot: float, a: float, ecc: float, n: float, j2: float, re: float
) -> float:
    """sun_sync_inclination_cosine."""
    return -2.0 * omegadot * a**2 * (1.0 - ecc**2) ** 2 / (3.0 * n * j2 * re**2)


def rad_s_to_deg_day(rate: float) -> float:
    return rate * (180.0 / math.pi) * DAY_S


def critical_inclinations() -> tuple[float, float]:
    acute = math.asin(math.sqrt(4.0 / 5.0))
    return acute, math.pi - acute


def evaluate_rates(body: Body, a: float, ecc: float, inc: float) -> Rates:
    n = mean_motion(body.mu, a)
    p = a * (1.0 - ecc**2)
    node = j2_nodal_rate(n, body.j2, body.ae, inc, a, ecc)
    apsis = j2_apsidal_rate(n, body.j2, body.ae, inc, a, ecc)
    sun = sun_sync_nodal_rate(body.year_days)
    cosine = sun_sync_inclination_cosine(sun, a, ecc, n, body.j2, body.ae)
    if abs(cosine) <= 1.0:
        i_ss = math.acos(cosine)
    else:
        i_ss = None
    return Rates(
        n=n,
        p=p,
        omega_dot_node=node,
        omega_dot_apsis=apsis,
        sun_sync_rate=sun,
        cosine_ss=cosine,
        i_ss=i_ss,
    )


def resolve_body(
    radius_arg: float | None,
    ae_arg: float | None,
    j2_arg: float | None,
    year_arg: float | None,
) -> Body:
    if radius_arg is None:
        radius = R0_EARTH
        radius_source = "default"
    else:
        require_finite(radius_arg, "--R0")
        if radius_arg <= 0.0:
            raise ValueError("--R0 must be > 0 m")
        radius = radius_arg
        radius_source = "input"
    if ae_arg is None:
        ae = AE_WGS84
        ae_source = "default"
    else:
        require_finite(ae_arg, "--ae")
        if ae_arg <= 0.0:
            raise ValueError("--ae must be > 0 m")
        ae = ae_arg
        ae_source = "input"
    if j2_arg is None:
        j2 = J2_GSFC
        j2_source = "default"
    else:
        require_finite(j2_arg, "--j2")
        if j2_arg <= 0.0:
            raise ValueError("--j2 must be > 0")
        j2 = j2_arg
        j2_source = "input"
    if year_arg is None:
        year_days = YEAR_DAYS
        year_source = "default"
    else:
        require_finite(year_arg, "--year")
        if year_arg <= 0.0:
            raise ValueError("--year must be > 0 day")
        year_days = year_arg
        year_source = "input"
    return Body(
        radius=radius,
        g0=G0,
        mu=G0 * radius**2,
        ae=ae,
        j2=j2,
        year_days=year_days,
        radius_source=radius_source,
        ae_source=ae_source,
        j2_source=j2_source,
        year_source=year_source,
    )


def resolve_orbit(ns: argparse.Namespace, mu: float):
    op = op_mod()
    element_names = ("a", "e", "i", "raan", "aop", "nu", "M")
    state_names = ("rx", "ry", "rz", "vx", "vy", "vz")
    tle_parts = getattr(ns, "tle", None)
    tle_used = bool(tle_parts)
    element_used = [name for name in element_names if getattr(ns, name) is not None]
    state_used = [name for name in state_names if getattr(ns, name) is not None]
    if int(tle_used) + int(bool(element_used)) + int(bool(state_used)) > 1:
        raise ValueError("pass a TLE, classical elements, or an inertial state, not more than one")
    if tle_used:
        orbit = op.orbit_from_tle(mu, op.parse_tle_args(tle_parts))
    elif state_used:
        missing = [name for name in state_names if getattr(ns, name) is None]
        if missing:
            flags = ", ".join(f"--{name}" for name in missing)
            raise ValueError(f"missing vector components: {flags}")
        orbit = op.orbit_from_state(mu, ns.rx, ns.ry, ns.rz, ns.vx, ns.vy, ns.vz, "state")
    elif element_used:
        needed = ("a", "e", "i", "raan", "aop")
        missing = [name for name in needed if getattr(ns, name) is None]
        if missing:
            flags = ", ".join(f"--{name}" for name in missing)
            raise ValueError(f"elements mode needs {flags}")
        if (ns.nu is None) == (ns.M is None):
            raise ValueError("elements mode needs exactly one of --nu or --M")
        orbit = op.orbit_from_elements(
            mu, ns.a, ns.e, ns.i, ns.raan, ns.aop, ns.nu, ns.M, "elements"
        )
    else:
        raise ValueError("pass a TLE, classical elements, or an inertial state")
    if orbit.conic != "ellipse" or orbit.a is None or orbit.period is None:
        raise ValueError("J2 secular rates are defined on an ellipse only")
    if orbit.e >= 1.0:
        raise ValueError("eccentricity must satisfy 0 <= e < 1")
    return orbit


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the rates") from exc
    return plt


def default_png_path() -> Path:
    return Path.cwd() / "j2_secular_rates.png"


def write_png(path: Path, body: Body, a: float, ecc: float, inc: float, rates: Rates) -> None:
    plt = ensure_matplotlib()
    inclinations = [
        math.pi * index / (N_PLOT - 1) for index in range(N_PLOT)
    ]
    nodal = [rad_s_to_deg_day(j2_nodal_rate(rates.n, body.j2, body.ae, angle, a, ecc)) for angle in inclinations]
    apsidal = [
        rad_s_to_deg_day(j2_apsidal_rate(rates.n, body.j2, body.ae, angle, a, ecc))
        for angle in inclinations
    ]
    degrees = [math.degrees(angle) for angle in inclinations]
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 8.0), sharex=True)
    sun_deg_day = rad_s_to_deg_day(rates.sun_sync_rate)
    i_deg = math.degrees(inc)
    axes[0].plot(degrees, nodal, color=PALETTE["nodal"], lw=2.0, label="nodal rate")
    axes[0].axhline(sun_deg_day, color=PALETTE["sun"], ls="--", lw=1.4, label="sun-sync rate")
    axes[0].axhline(0.0, color=PALETTE["zero"], lw=0.8)
    axes[0].axvline(i_deg, color=PALETTE["current"], ls=":", lw=1.4, label="orbit i")
    if rates.i_ss is not None:
        axes[0].axvline(
            math.degrees(rates.i_ss),
            color=PALETTE["sync"],
            ls="-.",
            lw=1.4,
            label="sun-sync i",
        )
        axes[0].plot(
            [math.degrees(rates.i_ss)],
            [sun_deg_day],
            marker="o",
            color=PALETTE["sync"],
            ms=6,
        )
    axes[0].plot([i_deg], [rad_s_to_deg_day(rates.omega_dot_node)], marker="s", color=PALETTE["current"], ms=6)
    axes[0].set_ylabel("nodal rate (deg/day)")
    axes[0].grid(True, color=PALETTE["grid"])
    axes[0].legend(loc="best", fontsize=8, framealpha=0.95)
    axes[0].set_title(PLOT_TITLE, color=PALETTE["text"])

    axes[1].plot(degrees, apsidal, color=PALETTE["apsidal"], lw=2.0, label="apsidal rate")
    axes[1].axhline(0.0, color=PALETTE["zero"], lw=0.8)
    axes[1].axvline(i_deg, color=PALETTE["current"], ls=":", lw=1.4, label="orbit i")
    for angle, name in zip(critical_inclinations(), ("critical i", "supplement")):
        axes[1].axvline(
            math.degrees(angle),
            color=PALETTE["critical"],
            ls="--",
            lw=1.1,
            label=name,
        )
    axes[1].plot(
        [i_deg],
        [rad_s_to_deg_day(rates.omega_dot_apsis)],
        marker="s",
        color=PALETTE["current"],
        ms=6,
    )
    axes[1].set_xlabel("inclination (deg)")
    axes[1].set_ylabel("apsidal rate (deg/day)")
    axes[1].set_xlim(0.0, 180.0)
    axes[1].grid(True, color=PALETTE["grid"])
    axes[1].legend(loc="best", fontsize=8, framealpha=0.95)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def report(body: Body, orbit, rates: Rates, png: Path, greenwich: float | None, di: float | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", orbit.mode)
    if getattr(orbit, "tle", None) is not None:
        op_mod().print_tle(orbit.tle)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("ae_m", body.ae)
    print_kv("ae_source", body.ae_source)
    print_kv("J2", body.j2)
    print_kv("J2_source", body.j2_source)
    print_kv("year_days", body.year_days)
    print_kv("year_source", body.year_source)
    print_kv("a_m", orbit.a)
    print_kv("e", orbit.e)
    print_kv("i_rad", orbit.i)
    print_kv("Omega_rad", orbit.Omega)
    print_kv("omega_rad", orbit.omega)
    print_kv("nu_rad", orbit.nu)
    if orbit.M is None:
        print_kv("M", "none")
    else:
        print_kv("M_rad", orbit.M)
    print_kv("p_m", rates.p)
    print_kv("n_rad_s", rates.n)
    print_kv("period_s", orbit.period)
    print_kv("Omega_dot_rad_s", rates.omega_dot_node)
    print_kv("Omega_dot_deg_day", rad_s_to_deg_day(rates.omega_dot_node))
    print_kv("omega_dot_rad_s", rates.omega_dot_apsis)
    print_kv("omega_dot_deg_day", rad_s_to_deg_day(rates.omega_dot_apsis))
    print_kv("sun_sync_rate_rad_s", rates.sun_sync_rate)
    print_kv("sun_sync_rate_deg_day", rad_s_to_deg_day(rates.sun_sync_rate))
    print_kv("sun_sync_inclination_cosine", rates.cosine_ss)
    if rates.i_ss is None:
        print_kv("i_ss", "none")
    else:
        print_kv("i_ss_rad", rates.i_ss)
        print_kv("i_ss_deg", math.degrees(rates.i_ss))
    if greenwich is not None:
        print_kv("greenwich_unused_rad", greenwich)
    if di is not None:
        print_kv("di_unused_rad", di)
    warning = op_mod().surface_warning(
        op_mod().Body(
            radius=body.radius,
            g0=body.g0,
            mu=body.mu,
            flattening=0.0,
            ae=body.ae,
            j2=body.j2,
            radius_source=body.radius_source,
            ae_source=body.ae_source,
            j2_source=body.j2_source,
        ),
        orbit,
    )
    if warning:
        print_kv("warning", warning)
    print_kv("graph", str(png))


def run(ns: argparse.Namespace) -> int:
    body = resolve_body(ns.R0, ns.ae, ns.j2, ns.year)
    orbit = resolve_orbit(ns, body.mu)
    if orbit.a is None:
        raise ValueError("J2 secular rates are defined on an ellipse only")
    rates = evaluate_rates(body, orbit.a, orbit.e, orbit.i)
    png = Path(ns.out) if ns.out else default_png_path()
    png = png.resolve()
    write_png(png, body, orbit.a, orbit.e, orbit.i, rates)
    report(body, orbit, rates, png, ns.greenwich, ns.di)
    return 0


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _bind_negative_values(argv: list[str]) -> list[str]:
    flags = {
        "--a",
        "--e",
        "--i",
        "--raan",
        "--aop",
        "--nu",
        "--M",
        "--rx",
        "--ry",
        "--rz",
        "--vx",
        "--vy",
        "--vz",
        "--greenwich",
        "--di",
        "--R0",
        "--ae",
        "--j2",
        "--year",
    }
    bound: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if (
            token in flags
            and index + 1 < len(argv)
            and argv[index + 1].startswith("-")
            and _is_number(argv[index + 1])
        ):
            bound.append(f"{token}={argv[index + 1]}")
            index += 2
            continue
        bound.append(token)
        index += 1
    return bound


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="First-order J2 nodal and apsidal rates and sun-synchronous inclination."
    )
    parser.add_argument("--a", type=float, default=None, help="semi-major axis [m]")
    parser.add_argument("--e", type=float, default=None, help="eccentricity, dimensionless")
    parser.add_argument("--i", type=float, default=None, help="inclination [rad], 0 <= i <= pi")
    parser.add_argument("--raan", type=float, default=None, help="longitude of the ascending node [rad]")
    parser.add_argument("--aop", type=float, default=None, help="argument of periapsis [rad]")
    parser.add_argument("--nu", type=float, default=None, help="true anomaly at epoch [rad]")
    parser.add_argument("--M", type=float, default=None, help="mean anomaly at epoch [rad], ellipse only")
    parser.add_argument("--rx", type=float, default=None, help="inertial position x [m]")
    parser.add_argument("--ry", type=float, default=None, help="inertial position y [m]")
    parser.add_argument("--rz", type=float, default=None, help="inertial position z [m]")
    parser.add_argument("--vx", type=float, default=None, help="inertial velocity x [m/s]")
    parser.add_argument("--vy", type=float, default=None, help="inertial velocity y [m/s]")
    parser.add_argument("--vz", type=float, default=None, help="inertial velocity z [m/s]")
    parser.add_argument(
        "--tle",
        nargs="+",
        default=None,
        help="NORAD two-line elements; two 69-character lines, optional name line first",
    )
    parser.add_argument(
        "--greenwich",
        type=float,
        default=None,
        help="accepted from GroundTrackEarth; unused",
    )
    parser.add_argument(
        "--di",
        type=float,
        default=None,
        help="accepted from PlaneChangeImpulse; unused",
    )
    parser.add_argument("--R0", type=float, default=None, help=f"two-body radius in mu = g0*R0^2 [m]; default Earth {R0_EARTH:.8g}")
    parser.add_argument("--ae", type=float, default=None, help=f"equatorial radius in the J2 term [m]; default WGS 84 {AE_WGS84:.8g}")
    parser.add_argument("--j2", type=float, default=None, help=f"second zonal harmonic; default {J2_GSFC:.8g}")
    parser.add_argument("--year", type=float, default=None, help=f"mean solar year [day]; default {YEAR_DAYS:g}")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    if argv is None:
        argv = sys.argv[1:]
    return parser.parse_args(_bind_negative_values(list(argv)))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def invoke(argv: list[str]) -> tuple[int, str, str]:
    captured: list[str] = []

    class _Capture:
        def write(self, text: str) -> None:
            captured.append(text)

        def flush(self) -> None:
            return None

    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = _Capture()
    sys.stderr = io.StringIO()
    try:
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 2
        err = sys.stderr.getvalue()
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
    return code, "".join(captured), err


def parse_stdout(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition(": ")
        if sep:
            values[key] = value
    return values


def _close(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


EARTH_ELLIPSE = [
    "--a",
    "10000000",
    "--e",
    "0.3",
    "--i",
    "0.9",
    "--raan",
    "0.6",
    "--aop",
    "1.2",
    "--nu",
    "0.8",
]
STATE_EXAMPLE = [
    "--rx",
    "8000000",
    "--ry",
    "0",
    "--rz",
    "0",
    "--vx",
    "0",
    "--vy",
    "7000",
    "--vz",
    "1500",
]
GROUND_TRACK_EXAMPLE = [
    "--a",
    "7000000",
    "--e",
    "0.05",
    "--i",
    "0.9",
    "--raan",
    "0.4",
    "--aop",
    "0.2",
    "--nu",
    "0.1",
    "--greenwich",
    "0.3",
]
PLANE_CHANGE_EXAMPLE = [
    "--a",
    "10000000",
    "--e",
    "0.3",
    "--i",
    "0.9",
    "--raan",
    "0.6",
    "--aop",
    "1.2",
    "--nu",
    "0.8",
    "--di",
    "0.2",
]


def run_check() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    n = 1.0
    j2 = 1.0
    re = 1.0
    a = 1.0
    ecc = 0.0
    check(_close(j2_nodal_rate(n, j2, re, math.pi / 2.0, a, ecc), 0.0, 1.0), "polar nodal rate")
    check(_close(j2_nodal_rate(n, j2, re, 0.0, a, ecc), -1.5, 1.0), "equatorial nodal rate")
    check(_close(j2_apsidal_rate(n, j2, re, 0.0, a, ecc), 3.0, 1.0), "equatorial apsidal rate")
    acute, obtuse = critical_inclinations()
    check(_close(j2_apsidal_rate(n, j2, re, acute, a, ecc), 0.0, 1.0), "critical apsidal rate")
    check(_close(j2_apsidal_rate(n, j2, re, obtuse, a, ecc), 0.0, 1.0), "supplement critical apsidal rate")
    year = YEAR_DAYS
    sun = sun_sync_nodal_rate(year)
    check(_close(sun, 2.0 * math.pi / (year * DAY_S), sun), "sun-sync nodal rate")
    check(
        _close(rad_s_to_deg_day(sun), 360.0 / year, 1.0),
        "sun-sync rate in deg/day",
    )
    check(
        _close(sun_sync_inclination_cosine(1.5, 1.0, 0.0, 1.0, 1.0, 1.0), -1.0, 1.0),
        "sun-sync cosine minus one",
    )
    check(
        _close(sun_sync_inclination_cosine(0.75, 1.0, 0.0, 1.0, 1.0, 1.0), -0.5, 1.0),
        "sun-sync cosine minus half",
    )

    body = resolve_body(None, None, None, None)
    check(body.radius == R0_EARTH and body.radius_source == "default", "Earth R0 default")
    check(body.ae == AE_WGS84 and body.ae_source == "default", "WGS 84 RE default")
    check(body.j2 == J2_GSFC and body.j2_source == "default", "GSFC J2 default")
    check(_close(body.mu, G0 * R0_EARTH**2, body.mu), "mu is g0*R0^2")

    alt_a = AE_WGS84 + 700000.0
    circular = evaluate_rates(body, alt_a, 0.0, math.radians(98.2))
    check(circular.i_ss is not None, "700 km circular has a sun-sync inclination")
    if circular.i_ss is not None:
        check(
            abs(math.degrees(circular.i_ss) - 98.2) <= 0.05,
            f"700 km circular sun-sync i {math.degrees(circular.i_ss)} deg vs primer 98.2 deg",
        )
        recovered = j2_nodal_rate(
            circular.n, body.j2, body.ae, circular.i_ss, alt_a, 0.0
        )
        check(_close(recovered, circular.sun_sync_rate, circular.sun_sync_rate), "sun-sync inversion")

    op = op_mod()
    orbit = op.orbit_from_elements(body.mu, 1.0e7, 0.3, 0.9, 0.6, 1.2, 0.8, None, "elements")
    from_orbit = evaluate_rates(body, orbit.a, orbit.e, orbit.i)
    check(_close(from_orbit.n, mean_motion(body.mu, orbit.a), from_orbit.n), "mean motion")
    check(_close(from_orbit.p, orbit.a * (1.0 - orbit.e**2), from_orbit.p), "semi-latus rectum")

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        png = root / "earth.png"
        code, out, err = invoke(EARTH_ELLIPSE + ["--out", str(png)])
        check(code == 0 and err == "", f"earth ellipse example failed: {err or out}")
        if code == 0:
            report_map = parse_stdout(out)
            check(png.is_file(), "earth example writes PNG")
            check(png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "PNG magic bytes")
            check(report_map.get("title") == PLOT_TITLE, "plot title")
            check(report_map.get("mode") == "elements", "elements mode")
            check("i_ss_rad" in report_map or report_map.get("i_ss") == "none", "sun-sync inclination printed")

        png_state = root / "state.png"
        code, out, err = invoke(STATE_EXAMPLE + ["--out", str(png_state)])
        check(code == 0 and err == "", f"state example failed: {err or out}")
        if code == 0:
            report_map = parse_stdout(out)
            check(report_map.get("mode") == "state", "state mode")
            check(png_state.is_file(), "state example writes PNG")

        png_gt = root / "ground.png"
        code, out, err = invoke(GROUND_TRACK_EXAMPLE + ["--out", str(png_gt)])
        check(code == 0 and err == "", f"ground-track inputs failed: {err or out}")
        if code == 0:
            report_map = parse_stdout(out)
            check(report_map.get("greenwich_unused_rad") == "0.3", "greenwich accepted unused")

        png_pc = root / "plane.png"
        code, out, err = invoke(PLANE_CHANGE_EXAMPLE + ["--out", str(png_pc)])
        check(code == 0 and err == "", f"plane-change inputs failed: {err or out}")
        if code == 0:
            report_map = parse_stdout(out)
            check(report_map.get("di_unused_rad") == "0.2", "di accepted unused")

        op = op_mod()
        png_tle = root / "tle.png"
        code, out, err = invoke(["--tle", op.ISS_TLE_LINE1, op.ISS_TLE_LINE2, "--out", str(png_tle)])
        check(code == 0 and err == "", f"TLE input failed: {err or out}")
        if code == 0:
            report_map = parse_stdout(out)
            check(report_map.get("mode") == "tle", "tle mode")
            check(report_map.get("tle_catalog") == "25544", "tle catalog")
            check(png_tle.is_file(), "TLE example writes PNG")

    rejections = (
        ["--a", "1e7", "--e", "0.1", "--i", "0.9", "--raan", "0.1", "--aop", "0.1"],
        ["--a=-2e7", "--e", "1.4", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0.2"],
        [
            "--a",
            "1e7",
            "--e",
            "0.1",
            "--i",
            "0.9",
            "--raan",
            "0.1",
            "--aop",
            "0.1",
            "--nu",
            "0.2",
            "--rx",
            "1",
        ],
        [],
        ["--tle", op_mod().ISS_TLE_LINE1],
    )
    for argv in rejections:
        code, _text, err = invoke(argv)
        if code != 2 or not err.startswith("error:"):
            errors.append(f"expected exit 2 for {argv}, got {code}: {err}")

    if errors:
        print("CHECK FAIL: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("check: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
