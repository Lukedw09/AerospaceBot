#!/usr/bin/env python3
"""Impulsive coplanar bi-elliptic transfer between two circular orbits.

Apsidal speeds are apsis_speed (vis_viva with semimajor_from_apsides).
Circular speed is circular_orbit_velocity. Each coast is elliptic_half_period.
The three-impulse geometry is NASA TM X-64662.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Bielliptic transfer"
CHECK_TOL = 1e-9
CIRCULAR_E = 1e-7
ASSUMPTIONS = (
    "impulsive coplanar three-burn bi-elliptic transfer between circular orbits "
    "about a spherical planet; inverse-square gravity with no drag, thrust, or "
    "third body on the coasts; the first ellipse has periapsis at the departure "
    "circular radius and apoapsis at rb, the second has apoapsis at rb and "
    "periapsis at the arrival circular radius; apsidal speeds are apsis_speed "
    "(vis_viva with semimajor_from_apsides), circular speed is "
    "circular_orbit_velocity, and each coast is elliptic_half_period; "
    "mu = g0*R0^2 with g0 = 9.80665 m/s^2; Earth default R0 = 6374200 m; "
    "a radius is distance from the center and an altitude is geometric height "
    "above R0; a plane change is omitted; a NORAD two-line element set may be "
    "passed for each orbit with --tle1 and --tle2 and is used as a Keplerian "
    "conic: line-2 angles are degrees, semi-major axis is the inverse of "
    "mean_motion from the published mean motion in revolutions per 86400 s and "
    "this mu, and BSTAR, mean-motion derivatives, SGP4, and the epoch do not "
    "change the state; each TLE still contributes only its epoch radius"
)

_HT = None
_OP = None


def ht_mod():
    global _HT
    if _HT is None:
        folder = str(SKILL_DIR.parent / "ASTRO - HohmannTransfer")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import hohmann_transfer as imported

        _HT = imported
    return _HT


def op_mod():
    global _OP
    if _OP is None:
        folder = str(SKILL_DIR.parent / "ASTRO - OrbitalParameters")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import orbital_parameters as imported

        _OP = imported
    return _OP


@dataclass(frozen=True)
class Transfer:
    mode: str
    r_depart: float
    r_arrive: float
    r_b: float
    a1: float
    e1: float
    a2: float
    e2: float
    v_circular_depart: float
    v_circular_arrive: float
    v1: float
    v1b: float
    v2b: float
    v2: float
    dv1: float
    dv2: float
    dv3: float
    sense1: str
    sense2: str
    sense3: str
    dv: float
    tof1: float
    tof2: float
    tof: float
    dv_hohmann: float
    dv_biparabolic: float
    r2_over_r1: float
    recommendation: str


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def apsis_speed(mu: float, occupied: float, opposite: float) -> float:
    """apsis_speed."""
    if occupied <= 0.0 or opposite <= 0.0:
        raise ValueError("apsis radii must be > 0 m")
    return math.sqrt(2.0 * mu * opposite / (occupied * (occupied + opposite)))


def elliptic_half_period(mu: float, semi_major: float) -> float:
    """elliptic_half_period."""
    return math.pi * math.sqrt(semi_major**3 / mu)


def ellipse_from_apsides(periapsis: float, apoapsis: float) -> tuple[float, float]:
    """semimajor_from_apsides and orbit_eccentricity."""
    ht = ht_mod()
    if ht.same_radius(periapsis, apoapsis):
        return periapsis, 0.0
    if apoapsis < periapsis:
        raise ValueError("apoapsis must be at least periapsis")
    semi_major = 0.5 * (apoapsis + periapsis)
    eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)
    return semi_major, eccentricity


def coast_time(mu: float, periapsis: float, apoapsis: float) -> float:
    ht = ht_mod()
    if ht.same_radius(periapsis, apoapsis):
        return 0.0
    semi_major, _ecc = ellipse_from_apsides(periapsis, apoapsis)
    return elliptic_half_period(mu, semi_major)


def recommend_bielliptic(dv: float, dv_hohmann: float) -> str:
    span = max(abs(dv), abs(dv_hohmann), 1.0)
    if dv < dv_hohmann and not math.isclose(dv, dv_hohmann, rel_tol=1e-12, abs_tol=1e-9 * span):
        return "bielliptic"
    return "Hohmann"


def solve_transfer(mu: float, r_depart: float, r_arrive: float, r_b: float, mode: str) -> Transfer:
    ht = ht_mod()
    if r_depart <= 0.0 or r_arrive <= 0.0 or r_b <= 0.0:
        raise ValueError("orbit radii must be > 0 m")
    outer = max(r_depart, r_arrive)
    if r_b < outer and not ht.same_radius(r_b, outer):
        raise ValueError(
            f"--rb {r_b:.8g} m must be at least the larger circular radius {outer:.8g} m"
        )
    r_b = max(r_b, outer) if ht.same_radius(r_b, outer) else r_b

    a1, e1 = ellipse_from_apsides(min(r_depart, r_b), max(r_depart, r_b))
    a2, e2 = ellipse_from_apsides(min(r_arrive, r_b), max(r_arrive, r_b))
    v_circular_depart = ht.circular_speed(mu, r_depart)
    v_circular_arrive = ht.circular_speed(mu, r_arrive)
    v1 = apsis_speed(mu, r_depart, r_b)
    v1b = apsis_speed(mu, r_b, r_depart)
    v2b = apsis_speed(mu, r_b, r_arrive)
    v2 = apsis_speed(mu, r_arrive, r_b)
    dv1 = abs(v1 - v_circular_depart)
    dv2 = abs(v2b - v1b)
    dv3 = abs(v_circular_arrive - v2)
    hohmann = ht.solve_transfer(mu, r_depart, r_arrive, "radii")
    dv_infinity = ht.biparabolic_delta_v(mu, r_depart, r_arrive)
    dv = dv1 + dv2 + dv3
    return Transfer(
        mode=mode,
        r_depart=r_depart,
        r_arrive=r_arrive,
        r_b=r_b,
        a1=a1,
        e1=e1,
        a2=a2,
        e2=e2,
        v_circular_depart=v_circular_depart,
        v_circular_arrive=v_circular_arrive,
        v1=v1,
        v1b=v1b,
        v2b=v2b,
        v2=v2,
        dv1=dv1,
        dv2=dv2,
        dv3=dv3,
        sense1=ht.burn_sense(v1, v_circular_depart),
        sense2=ht.burn_sense(v2b, v1b),
        sense3=ht.burn_sense(v_circular_arrive, v2),
        dv=dv,
        tof1=coast_time(mu, r_depart, r_b),
        tof2=coast_time(mu, r_arrive, r_b),
        tof=coast_time(mu, r_depart, r_b) + coast_time(mu, r_arrive, r_b),
        dv_hohmann=hohmann.dv,
        dv_biparabolic=dv_infinity,
        r2_over_r1=ht.radius_ratio(r_depart, r_arrive),
        recommendation=recommend_bielliptic(dv, hohmann.dv),
    )


def require_outside_body(transfer: Transfer, body_radius: float) -> None:
    ht = ht_mod()
    for flag, radius in (
        ("departure", transfer.r_depart),
        ("arrival", transfer.r_arrive),
        ("intermediate apoapsis", transfer.r_b),
    ):
        if radius < body_radius and not ht.same_radius(radius, body_radius):
            raise ValueError(
                f"{flag} radius {radius:.8g} m is inside the planetary "
                f"radius {body_radius:.8g} m"
            )


def surface_warning(
    transfer: Transfer,
    body_radius: float,
    notes: list[str],
) -> str | None:
    ht = ht_mod()
    extra = list(notes)
    if ht.same_radius(transfer.r_depart, body_radius):
        extra.append("the departure orbit lies on the planetary surface")
    if ht.same_radius(transfer.r_arrive, body_radius):
        extra.append("the arrival orbit lies on the planetary surface")
    if ht.same_radius(transfer.r_b, max(transfer.r_depart, transfer.r_arrive)):
        extra.append(
            "rb equals the larger circular radius, so one transfer ellipse "
            "degenerates and the burns recover a Hohmann transfer"
        )
    if transfer.recommendation == "Hohmann":
        extra.append(
            "this rb is not cheaper than a Hohmann transfer; use ASTRO - HohmannTransfer"
        )
    if not extra:
        return None
    return "; ".join(extra)


def orbit_radius(orbit: object) -> float:
    return math.sqrt(orbit.rx**2 + orbit.ry**2 + orbit.rz**2)


def resolve_one_orbit(ns: argparse.Namespace, body, suffix: str):
    op = op_mod()
    element_names = ("a", "e", "i", "raan", "aop", "nu", "M")
    state_names = ("rx", "ry", "rz", "vx", "vy", "vz")
    tle_parts = getattr(ns, f"tle{suffix}", None)
    tle_used = bool(tle_parts)
    element_used = [name for name in element_names if getattr(ns, f"{name}{suffix}") is not None]
    state_used = [name for name in state_names if getattr(ns, f"{name}{suffix}") is not None]
    if int(tle_used) + int(bool(element_used)) + int(bool(state_used)) > 1:
        raise ValueError(f"orbit {suffix}: pass a TLE, classical elements, or an inertial state, not more than one")
    if tle_used:
        return op.orbit_from_tle(body.mu, op.parse_tle_args(tle_parts))
    if state_used:
        missing = [name for name in state_names if getattr(ns, f"{name}{suffix}") is None]
        if missing:
            flags = ", ".join(f"--{name}{suffix}" for name in missing)
            raise ValueError(f"missing vector components: {flags}")
        orbit = op.orbit_from_state(
            body.mu,
            getattr(ns, f"rx{suffix}"),
            getattr(ns, f"ry{suffix}"),
            getattr(ns, f"rz{suffix}"),
            getattr(ns, f"vx{suffix}"),
            getattr(ns, f"vy{suffix}"),
            getattr(ns, f"vz{suffix}"),
            "state",
        )
        return orbit
    if not element_used:
        return None
    missing = [name for name in ("a", "e", "i", "raan", "aop") if getattr(ns, f"{name}{suffix}") is None]
    if missing:
        flags = ", ".join(f"--{name}{suffix}" for name in missing)
        raise ValueError(f"missing elements: {flags}")
    nu = getattr(ns, f"nu{suffix}")
    mean_anomaly = getattr(ns, f"M{suffix}")
    if nu is not None and mean_anomaly is not None:
        raise ValueError(f"orbit {suffix}: pass exactly one of --nu{suffix} or --M{suffix}")
    if nu is None and mean_anomaly is None:
        raise ValueError(f"orbit {suffix}: pass exactly one of --nu{suffix} or --M{suffix}")
    return op.orbit_from_elements(
        body.mu,
        getattr(ns, f"a{suffix}"),
        getattr(ns, f"e{suffix}"),
        getattr(ns, f"i{suffix}"),
        getattr(ns, f"raan{suffix}"),
        getattr(ns, f"aop{suffix}"),
        nu,
        mean_anomaly,
        "elements",
    )


def require_ellipse(orbit: object, label: str) -> None:
    if orbit.conic != "ellipse":
        raise ValueError(f"{label} must be an ellipse, including a circle")


def orbit_notes(initial: object, final: object) -> list[str]:
    notes: list[str] = []
    if initial.e > CIRCULAR_E or final.e > CIRCULAR_E:
        notes.append(
            "a non-circular ellipse contributed only its epoch radius as a circular orbit"
        )
    if not math.isclose(initial.i, final.i, rel_tol=0.0, abs_tol=1e-8):
        notes.append("the burns are coplanar; a plane change is omitted")
    return notes


def resolve_radii(ns: argparse.Namespace, body) -> tuple[str, float, float, list[str]]:
    ht = ht_mod()
    if ns.rb is None:
        raise ValueError("missing --rb")
    ht.require_finite(ns.rb, "--rb")
    have_radii = ns.r1 is not None or ns.r2 is not None
    initial = resolve_one_orbit(ns, body, "1")
    final = resolve_one_orbit(ns, body, "2")
    ns.parsed_tles = []
    if initial is not None and getattr(initial, "tle", None) is not None:
        ns.parsed_tles.append(("1", initial.tle))
    if final is not None and getattr(final, "tle", None) is not None:
        ns.parsed_tles.append(("2", final.tle))
    if have_radii and (initial is not None or final is not None):
        raise ValueError("pass either --r1 and --r2, or two orbits, not both")
    if have_radii:
        if ns.r1 is None or ns.r2 is None:
            raise ValueError("--r1 and --r2 are both required")
        ht.require_finite(ns.r1, "--r1")
        ht.require_finite(ns.r2, "--r2")
        return "radii", ns.r1, ns.r2, []
    if initial is None or final is None:
        raise ValueError(
            "pass --r1 --r2 --rb, or two classical-element sets, or two inertial states, or two TLEs, plus --rb"
        )
    require_ellipse(initial, "the departure orbit")
    require_ellipse(final, "the arrival orbit")
    if initial.mode != final.mode:
        if "tle" in (initial.mode, final.mode):
            raise ValueError("pass two TLEs, or two element sets, or two states, not a mix with a TLE")
        mode = "mixed"
    else:
        mode = initial.mode
    return mode, orbit_radius(initial), orbit_radius(final), orbit_notes(initial, final)


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the bi-elliptic transfer") from exc
    return plt


def polar_xy(radius_of_angle, angles: list[float]) -> tuple[list[float], list[float]]:
    ht = ht_mod()
    return ht.polar_xy(radius_of_angle, angles)


def plot_transfer(path: Path, body, transfer: Transfer) -> None:
    ht = ht_mod()
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8.4, 7.2))

    def circle(radius: float, _angle: float) -> float:
        return radius

    full = ht.linspace(0.0, 2.0 * math.pi, 361)
    earth_x, earth_y = polar_xy(lambda angle: circle(body.radius, angle), full)
    ax.fill(earth_x, earth_y, color="#d4e6f1", zorder=1)
    ax.plot(earth_x, earth_y, color="#1a5276", linewidth=1.0, zorder=2, label="planet")

    depart_x, depart_y = polar_xy(lambda angle: circle(transfer.r_depart, angle), full)
    ax.plot(
        depart_x,
        depart_y,
        color="#1a5276",
        linestyle="--",
        linewidth=1.3,
        zorder=3,
        label="departure orbit",
    )
    if not ht.same_radius(transfer.r_depart, transfer.r_arrive):
        arrive_x, arrive_y = polar_xy(lambda angle: circle(transfer.r_arrive, angle), full)
        ax.plot(
            arrive_x,
            arrive_y,
            color="#1a5276",
            linestyle=":",
            linewidth=1.5,
            zorder=3,
            label="arrival orbit",
        )
    if not ht.same_radius(transfer.r_b, transfer.r_depart) and not ht.same_radius(
        transfer.r_b, transfer.r_arrive
    ):
        apo_x, apo_y = polar_xy(lambda angle: circle(transfer.r_b, angle), full)
        ax.plot(
            apo_x,
            apo_y,
            color="#85929e",
            linestyle=":",
            linewidth=0.9,
            zorder=3,
            label="intermediate apoapsis",
        )

    def ellipse_radius(periapsis: float, apoapsis: float, angle: float) -> float:
        semi_major, eccentricity = ellipse_from_apsides(periapsis, apoapsis)
        if eccentricity <= 1e-12:
            return periapsis
        return semi_major * (1.0 - eccentricity**2) / (1.0 + eccentricity * math.cos(angle))

    first = ht.linspace(0.0, math.pi, 181)
    first_x, first_y = polar_xy(
        lambda angle: ellipse_radius(transfer.r_depart, transfer.r_b, angle), first
    )
    ax.plot(first_x, first_y, color="#c0392b", linewidth=2.2, zorder=4, label="first coast")
    second = ht.linspace(math.pi, 2.0 * math.pi, 181)
    second_x, second_y = polar_xy(
        lambda angle: ellipse_radius(transfer.r_arrive, transfer.r_b, angle), second
    )
    ax.plot(second_x, second_y, color="#8e44ad", linewidth=2.2, zorder=4, label="second coast")

    ax.plot(
        first_x[0],
        first_y[0],
        "s",
        color="#27ae60",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="departure",
    )
    ax.plot(
        first_x[-1],
        first_y[-1],
        "D",
        color="#d68910",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="apoapsis burn",
    )
    ax.plot(
        second_x[-1],
        second_y[-1],
        "o",
        color="#1a5276",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="arrival",
    )
    arrow_km = 0.10 * max(transfer.r_depart, transfer.r_arrive, transfer.r_b, body.radius) / 1000.0
    ht.draw_delta_v(
        ax,
        ht.apsis_xy_km(transfer.r_depart, 0.0),
        ht.burn_vector_m_s(transfer.dv1, transfer.sense1, 0.0),
        arrow_km,
        ht.DV_COLOR,
    )
    ht.draw_delta_v(
        ax,
        ht.apsis_xy_km(transfer.r_b, math.pi),
        ht.burn_vector_m_s(transfer.dv2, transfer.sense2, math.pi),
        arrow_km,
        ht.DV_COLOR,
    )
    ht.draw_delta_v(
        ax,
        ht.apsis_xy_km(transfer.r_arrive, 0.0),
        ht.burn_vector_m_s(transfer.dv3, transfer.sense3, 0.0),
        arrow_km,
        ht.DV_COLOR,
    )

    outer = max(transfer.r_depart, transfer.r_arrive, transfer.r_b, body.radius)
    limit = 1.18 * outer / 1000.0
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(PLOT_TITLE)
    ax.text(
        0.5,
        1.02,
        f"{(transfer.r_depart - body.radius) / 1000.0:.6g} km to "
        f"{(transfer.r_arrive - body.radius) / 1000.0:.6g} km via "
        f"{(transfer.r_b - body.radius) / 1000.0:.6g} km apoapsis",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#34495e",
    )
    ax.text(
        0.02,
        0.98,
        f"delta-v  {transfer.dv:.6g} m/s\nTOF  {ht.format_tof(transfer.tof)}\n"
        f"|r2|/|r1|  {transfer.r2_over_r1:.6g}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.9,
            "edgecolor": "#d5d8dc",
        },
        zorder=7,
    )
    ax.grid(True, alpha=0.25)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8, framealpha=0.95)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def print_report(
    body,
    transfer: Transfer,
    path: Path,
    notes: list[str],
    viewer: Path | None,
    tles: list | None = None,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", transfer.mode)
    if tles:
        op = op_mod()
        for label, tle in tles:
            op.print_tle(tle, label)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("r_depart_m", transfer.r_depart)
    print_kv("r_arrive_m", transfer.r_arrive)
    print_kv("r_b_m", transfer.r_b)
    print_kv("h_depart_m", transfer.r_depart - body.radius)
    print_kv("h_arrive_m", transfer.r_arrive - body.radius)
    print_kv("h_b_m", transfer.r_b - body.radius)
    print_kv("a1_m", transfer.a1)
    print_kv("e1", transfer.e1)
    print_kv("a2_m", transfer.a2)
    print_kv("e2", transfer.e2)
    print_kv("v_circular_depart_m_s", transfer.v_circular_depart)
    print_kv("v_circular_arrive_m_s", transfer.v_circular_arrive)
    print_kv("v1_m_s", transfer.v1)
    print_kv("v1b_m_s", transfer.v1b)
    print_kv("v2b_m_s", transfer.v2b)
    print_kv("v2_m_s", transfer.v2)
    print_kv("dv1_m_s", transfer.dv1)
    print_kv("dv1_sense", transfer.sense1)
    print_kv("dv2_m_s", transfer.dv2)
    print_kv("dv2_sense", transfer.sense2)
    print_kv("dv3_m_s", transfer.dv3)
    print_kv("dv3_sense", transfer.sense3)
    print_kv("dv_m_s", transfer.dv)
    print_kv("tof1_s", transfer.tof1)
    print_kv("tof2_s", transfer.tof2)
    print_kv("tof_s", transfer.tof)
    print_kv("r2_over_r1", transfer.r2_over_r1)
    print_kv("dv_hohmann_m_s", transfer.dv_hohmann)
    print_kv("dv_biparabolic_m_s", transfer.dv_biparabolic)
    print_kv("recommendation", transfer.recommendation)
    warning = surface_warning(transfer, body.radius, notes)
    if warning:
        print_kv("warning", warning)
    print_kv("elev_deg", ht_mod().PNG_ELEV_DEG)
    print_kv("azim_deg", ht_mod().PNG_AZIM_DEG)
    print_kv("graph", str(path))
    if viewer is not None:
        print_kv("viewer", str(viewer))


def build_bielliptic_payload(body, transfer: Transfer) -> dict[str, object]:
    ht = ht_mod()
    op = op_mod()
    outer = max(transfer.r_depart, transfer.r_arrive, transfer.r_b, body.radius)
    scene = ht.planet_backdrop(body, outer)
    palette = dict(op.PALETTE)
    palette["dv"] = ht.DV_COLOR
    palette["first"] = "#c0392b"
    palette["second"] = "#8e44ad"
    palette["arrive"] = "#1a5276"
    depart_km = [ht.apsis_xy_km(transfer.r_depart, 0.0)[0], ht.apsis_xy_km(transfer.r_depart, 0.0)[1], 0.0]
    apo_km = [ht.apsis_xy_km(transfer.r_b, math.pi)[0], ht.apsis_xy_km(transfer.r_b, math.pi)[1], 0.0]
    arrive_km = [ht.apsis_xy_km(transfer.r_arrive, 0.0)[0], ht.apsis_xy_km(transfer.r_arrive, 0.0)[1], 0.0]
    layers = [
        {
            "id": "depart",
            "color": palette["orbit"],
            "faded": True,
            "polylines": [ht.equatorial_circle_km(transfer.r_depart)],
        },
        {
            "id": "arrive",
            "color": palette["arrive"],
            "faded": True,
            "polylines": [ht.equatorial_circle_km(transfer.r_arrive)],
        },
        {
            "id": "first",
            "color": palette["first"],
            "faded": False,
            "polylines": [ht.equatorial_arc_km(transfer.a1, transfer.e1, 0.0, 2.0 * math.pi, 361)],
        },
        {
            "id": "second",
            "color": palette["second"],
            "faded": False,
            "polylines": [ht.equatorial_arc_km(transfer.a2, transfer.e2, 0.0, 2.0 * math.pi, 361)],
        },
    ]
    burns = [
        {
            "km": depart_km,
            "dv_m_s": list(ht.burn_vector_m_s(transfer.dv1, transfer.sense1, 0.0)),
            "color": ht.DV_COLOR,
            "label": "departure burn",
        },
        {
            "km": apo_km,
            "dv_m_s": list(ht.burn_vector_m_s(transfer.dv2, transfer.sense2, math.pi)),
            "color": ht.DV_COLOR,
            "label": "apoapsis burn",
        },
        {
            "km": arrive_km,
            "dv_m_s": list(ht.burn_vector_m_s(transfer.dv3, transfer.sense3, 0.0)),
            "color": ht.DV_COLOR,
            "label": "arrival burn",
        },
    ]
    markers = [
        {"id": "departure", "label": "departure", "shape": "square", "color": "#27ae60", "km": depart_km},
        {"id": "apoapsis", "label": "apoapsis burn", "shape": "diamond", "color": "#d68910", "km": apo_km},
        {"id": "arrival", "label": "arrival", "shape": "circle", "color": palette["arrive"], "km": arrive_km},
        {"id": "spacecraft", "label": "spacecraft", "shape": "circle", "color": palette["craft"], "km": depart_km},
    ]
    legend = [
        {"label": "planet", "swatch": "planet", "color": palette["planet"], "edge": palette["planet_edge"]},
        {"label": "departure orbit", "swatch": "line", "color": palette["orbit"], "edge": None},
        {"label": "arrival orbit", "swatch": "line", "color": palette["arrive"], "edge": None},
        {"label": "first ellipse", "swatch": "line", "color": palette["first"], "edge": None},
        {"label": "second ellipse", "swatch": "line", "color": palette["second"], "edge": None},
        {"label": "departure", "swatch": "square", "color": "#27ae60", "edge": None},
        {"label": "apoapsis burn", "swatch": "diamond", "color": "#d68910", "edge": None},
        {"label": "arrival", "swatch": "circle", "color": palette["arrive"], "edge": None},
        {"label": "spacecraft", "swatch": "circle", "color": palette["craft"], "edge": None},
        {"label": "delta-v", "swatch": "line", "color": ht.DV_COLOR, "edge": None},
    ]
    sequence: list[dict[str, object]] = [
        ht.coast_leg(body.mu, transfer.r_depart, 0.0, -0.55, 0.0, ht.PARK_WALL_S, "depart", "departure orbit"),
        ht.burn_leg(
            0,
            "departure burn",
            "first",
            ht.conic_apsides(body.mu, transfer.r_depart, transfer.r_depart),
            ht.conic_apsides(body.mu, transfer.r_depart, transfer.r_b),
            "depart",
            "first",
        ),
        ht.coast_leg(body.mu, transfer.a1, transfer.e1, 0.0, math.pi, ht.COAST_WALL_S, "first", "first ellipse"),
        ht.burn_leg(
            1,
            "apoapsis burn",
            "second",
            ht.conic_apsides(body.mu, transfer.r_depart, transfer.r_b),
            ht.conic_apsides(body.mu, transfer.r_arrive, transfer.r_b),
            "first",
            "second",
        ),
        ht.coast_leg(
            body.mu, transfer.a2, transfer.e2, math.pi, 2.0 * math.pi, ht.COAST_WALL_S, "second", "second ellipse"
        ),
        ht.burn_leg(
            2,
            "arrival burn",
            "arrive",
            ht.conic_apsides(body.mu, transfer.r_arrive, transfer.r_b),
            ht.conic_apsides(body.mu, transfer.r_arrive, transfer.r_arrive),
            "second",
            "arrive",
        ),
        ht.coast_leg(
            body.mu,
            transfer.r_arrive,
            0.0,
            0.0,
            4.0 * math.pi,
            ht.ARRIVE_WALL_S,
            "arrive",
            "arrival orbit",
        ),
    ]
    return {
        "title": PLOT_TITLE,
        "elev_deg": ht.PNG_ELEV_DEG,
        "azim_deg": ht.PNG_AZIM_DEG,
        "roll_deg": op.CAMERA_ROLL_DEG,
        **scene,
        "layers": layers,
        "markers": markers,
        "craft_km": depart_km,
        "burns": burns,
        "legend": legend,
        "palette": palette,
        "sequence": sequence,
    }


def run(ns: argparse.Namespace) -> int:
    ht = ht_mod()
    body = ht.resolve_body(ns.R0)
    mode, r_depart, r_arrive, notes = resolve_radii(ns, body)
    transfer = solve_transfer(body.mu, r_depart, r_arrive, ns.rb, mode)
    require_outside_body(transfer, body.radius)
    out_path = Path(ns.out) if ns.out else SKILL_DIR / "bielliptic_transfer.png"
    out_path = out_path.resolve()
    plot_transfer(out_path, body, transfer)
    viewer_path = out_path.with_suffix(".html")
    wrote_html = bool(ns.html or ns.open)
    if wrote_html:
        ht.write_viewer_html(SKILL_DIR, viewer_path, build_bielliptic_payload(body, transfer), PLOT_TITLE)
    print_report(
        body,
        transfer,
        out_path,
        notes,
        viewer_path if wrote_html else None,
        getattr(ns, "parsed_tles", None),
    )
    if ns.open:
        webbrowser.open(viewer_path.as_uri())
    return 0


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def run_check() -> int:
    ht = ht_mod()

    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    body = ht.resolve_body(None)
    mu = 1.0
    r1 = 1.0
    r2 = 4.0
    rb = 12.0
    transfer = solve_transfer(mu, r1, r2, rb, "radii")
    a1 = 0.5 * (r1 + rb)
    a2 = 0.5 * (r2 + rb)
    if not close_enough(transfer.a1, a1, a1):
        return fail("first semi-major axis")
    if not close_enough(transfer.a2, a2, a2):
        return fail("second semi-major axis")
    expected_v1 = apsis_speed(mu, r1, rb)
    expected_v1b = apsis_speed(mu, rb, r1)
    expected_v2b = apsis_speed(mu, rb, r2)
    expected_v2 = apsis_speed(mu, r2, rb)
    if not close_enough(transfer.v1, expected_v1, 1.0):
        return fail("first periapsis speed")
    if not close_enough(transfer.v1b, expected_v1b, 1.0):
        return fail("first apoapsis speed")
    if not close_enough(transfer.v2b, expected_v2b, 1.0):
        return fail("second apoapsis speed")
    if not close_enough(transfer.v2, expected_v2, 1.0):
        return fail("second periapsis speed")
    if not close_enough(transfer.v1, ht.vis_viva(mu, r1, a1), 1.0):
        return fail("apsis_speed is not vis_viva")
    dv1 = abs(expected_v1 - 1.0)
    dv2 = abs(expected_v2b - expected_v1b)
    dv3 = abs(0.5 - expected_v2)
    if not close_enough(transfer.dv1, dv1, 1.0):
        return fail("first burn")
    if not close_enough(transfer.dv2, dv2, 1.0):
        return fail("apoapsis burn")
    if not close_enough(transfer.dv3, dv3, 1.0):
        return fail("third burn")
    if not close_enough(transfer.dv, dv1 + dv2 + dv3, 1.0):
        return fail("total delta-v")
    expected_tof = elliptic_half_period(mu, a1) + elliptic_half_period(mu, a2)
    if not close_enough(transfer.tof, expected_tof, expected_tof):
        return fail("time of flight")
    if transfer.recommendation != "Hohmann":
        return fail("small radius ratio should recommend Hohmann")
    if not close_enough(transfer.r2_over_r1, 4.0, 4.0):
        return fail("radius ratio")

    hohmann = ht.solve_transfer(mu, r1, r2, "radii")
    degenerate = solve_transfer(mu, r1, r2, r2, "radii")
    if not close_enough(degenerate.dv, hohmann.dv, max(hohmann.dv, 1.0)):
        return fail("rb equal to r2 did not recover Hohmann delta-v")
    if not close_enough(degenerate.tof, hohmann.tof, hohmann.tof):
        return fail("rb equal to r2 did not recover Hohmann time of flight")
    if degenerate.recommendation != "Hohmann":
        return fail("degenerate bielliptic should recommend Hohmann")

    inward = solve_transfer(mu, r2, r1, rb, "radii")
    if not close_enough(inward.dv, transfer.dv, 1.0):
        return fail("inward total delta-v")
    if not close_enough(inward.tof, transfer.tof, transfer.tof):
        return fail("inward time of flight")
    if not close_enough(inward.r2_over_r1, 0.25, 1.0):
        return fail("inward radius ratio")

    wide = solve_transfer(mu, 1.0, 20.0, 60.0, "radii")
    if wide.recommendation != "bielliptic":
        return fail("large radius ratio with distant rb should recommend bielliptic")
    if wide.dv >= wide.dv_hohmann:
        return fail("wide bielliptic was not cheaper than Hohmann")

    try:
        solve_transfer(mu, r1, r2, 3.0, "radii")
    except ValueError:
        pass
    else:
        return fail("an interior apoapsis was accepted")

    earth = solve_transfer(body.mu, body.radius + 400000.0, body.radius + 35786000.0, 6.0e8, "radii")
    if earth.r2_over_r1 <= 1.0:
        return fail("Earth radius ratio")

    ns_elements = SimpleNamespace(
        r1=None,
        r2=None,
        rb=12.0,
        R0=None,
        a1=1.0,
        e1=0.0,
        i1=0.2,
        raan1=0.1,
        aop1=0.0,
        nu1=0.0,
        M1=None,
        a2=4.0,
        e2=0.0,
        i2=0.2,
        raan2=0.1,
        aop2=0.0,
        nu2=0.0,
        M2=None,
        rx1=None,
        ry1=None,
        rz1=None,
        vx1=None,
        vy1=None,
        vz1=None,
        rx2=None,
        ry2=None,
        rz2=None,
        vx2=None,
        vy2=None,
        vz2=None,
    )
    fake_body = ht.Body(radius=0.1, g0=1.0, mu=1.0, radius_source="check")
    mode, r_depart, r_arrive, notes = resolve_radii(ns_elements, fake_body)
    if mode != "elements":
        return fail("elements mode")
    if not close_enough(r_depart, 1.0, 1.0) or not close_enough(r_arrive, 4.0, 1.0):
        return fail("elements radii")
    if notes:
        return fail("circular coplanar elements produced a warning")

    op = op_mod()
    geo_body = op.ISS_TLE_LINE2[:52] + " 1.00273791" + op.ISS_TLE_LINE2[63:68]
    geo_line2 = geo_body + str(op.tle_checksum(geo_body))
    ns_tle = parse_args(
        [
            "--tle1",
            op.ISS_TLE_LINE1,
            op.ISS_TLE_LINE2,
            "--tle2",
            op.ISS_TLE_LINE1,
            geo_line2,
            "--rb",
            "200000000",
        ]
    )
    mode, r_depart, r_arrive, _tle_notes = resolve_radii(ns_tle, body)
    if mode != "tle":
        return fail("tle mode")
    if not (r_arrive > r_depart > body.radius):
        return fail("TLE radii")
    if [label for label, _tle in ns_tle.parsed_tles] != ["1", "2"]:
        return fail("parsed TLE pair")

    v_circ_1 = 1.0
    ns_state = SimpleNamespace(
        r1=None,
        r2=None,
        rb=12.0,
        R0=None,
        a1=None,
        e1=None,
        i1=None,
        raan1=None,
        aop1=None,
        nu1=None,
        M1=None,
        a2=None,
        e2=None,
        i2=None,
        raan2=None,
        aop2=None,
        nu2=None,
        M2=None,
        rx1=1.0,
        ry1=0.0,
        rz1=0.0,
        vx1=0.0,
        vy1=v_circ_1,
        vz1=0.0,
        rx2=4.0,
        ry2=0.0,
        rz2=0.0,
        vx2=0.0,
        vy2=0.5,
        vz2=0.0,
    )
    mode, r_depart, r_arrive, _notes = resolve_radii(ns_state, fake_body)
    if mode != "state":
        return fail("state mode")
    if not close_enough(r_depart, 1.0, 1.0) or not close_enough(r_arrive, 4.0, 1.0):
        return fail("state radii")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "transfer.png")
        captured: list[str] = []

        class _Capture:
            def write(self, text: str) -> None:
                captured.append(text)

            def flush(self) -> None:
                return None

        old_out = sys.stdout
        sys.stdout = _Capture()
        try:
            code = main(["--r1", "1", "--r2", "4", "--rb", "12", "--R0", "0.5", "--out", out])
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"radii main returned {code}")
        if not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        text = "".join(captured)
        for key in (
            "mode: radii",
            "dv_m_s:",
            "tof_s:",
            "r2_over_r1:",
            "recommendation:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "viewer:" in text:
            return fail("HTML viewer was written without --html")

        html_out = str(Path(tmp) / "transfer_html.png")
        captured.clear()
        sys.stdout = _Capture()
        try:
            html_code = main(
                ["--r1", "1", "--r2", "4", "--rb", "12", "--R0", "0.5", "--out", html_out, "--html"]
            )
        finally:
            sys.stdout = old_out
        if html_code != 0:
            return fail(f"html main returned {html_code}")
        html_path = Path(html_out).with_suffix(".html")
        if not html_path.is_file():
            return fail("HTML viewer was not written")
        html = html_path.read_text(encoding="utf-8")
        if PLOT_TITLE not in html or "__THREE_SOURCE__" in html or "__SCENE_JSON__" in html:
            return fail("HTML placeholders")
        if "new THREE.OrthographicCamera" not in html or len(html) < 100000:
            return fail("Three.js is not inlined")
        if "apoapsis burn" not in html or "sampleInclined" in html:
            return fail("HTML missing three-burn sequence")
        if "flownTrails" in html:
            return fail("viewer still draws a partial coast trail")
        if "function activeLayer" not in html:
            return fail("viewer missing the current-orbit highlight")
        if "lerpApsides" not in html or "morphOrbit" not in html:
            return fail("viewer missing the burn morph")
        scene = ht.scene_from_html(html)
        burns = [leg for leg in scene.get("sequence") or [] if leg.get("kind") == "burn"]
        if len(burns) != 3 or any("from" not in burn or "to" not in burn for burn in burns):
            return fail("three burns need from/to conics")
        first = next((layer for layer in scene.get("layers") or [] if layer.get("id") == "first"), None)
        second = next((layer for layer in scene.get("layers") or [] if layer.get("id") == "second"), None)
        if first is None or second is None:
            return fail("viewer missing the two transfer ellipses")
        for name, layer in (("first", first), ("second", second)):
            loop = (layer.get("polylines") or [[]])[0]
            if len(loop) < 300:
                return fail(f"{name} ellipse is not a full revolution")
            start, end = loop[0], loop[-1]
            if abs(start[0] - end[0]) > 1e-6 or abs(start[1] - end[1]) > 1e-6:
                return fail(f"{name} ellipse is not closed")
        if abs(float(scene["elev_deg"]) - ht.PNG_ELEV_DEG) > 1e-9:
            return fail("viewer elevation is not orbit-normal")
        if len(scene.get("burns") or []) != 3:
            return fail("bielliptic viewer needs three burns")
        if "viewer:" not in "".join(captured):
            return fail("stdout missing viewer")

    sink = sys.stderr
    sys.stderr = tempfile.TemporaryFile(mode="w+")
    try:
        missing = main([])
    finally:
        sys.stderr.close()
        sys.stderr = sink
    if missing != 2:
        return fail("missing inputs were accepted")

    print("check: pass")
    print_kv("unit_dv_m_s", transfer.dv)
    print_kv("unit_tof_s", transfer.tof)
    print_kv("wide_dv_m_s", wide.dv)
    print_kv("wide_hohmann_dv_m_s", wide.dv_hohmann)
    return 0


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _bind_negative_values(argv: list[str]) -> list[str]:
    bound: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if (
            token.startswith("--")
            and "=" not in token
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
    ht = ht_mod()
    parser = argparse.ArgumentParser(
        description="Coplanar bi-elliptic transfer between two circular orbits."
    )
    parser.add_argument("--r1", type=float, default=None, help="departure circular radius from the center [m]")
    parser.add_argument("--r2", type=float, default=None, help="arrival circular radius from the center [m]")
    parser.add_argument(
        "--rb",
        type=float,
        default=None,
        help="common apoapsis of the two transfer ellipses [m]",
    )
    parser.add_argument("--a1", type=float, default=None, help="departure semi-major axis [m]")
    parser.add_argument("--e1", type=float, default=None, help="departure eccentricity")
    parser.add_argument("--i1", type=float, default=None, help="departure inclination [rad]")
    parser.add_argument("--raan1", type=float, default=None, help="departure longitude of the ascending node [rad]")
    parser.add_argument("--aop1", type=float, default=None, help="departure argument of periapsis [rad]")
    parser.add_argument("--nu1", type=float, default=None, help="departure true anomaly [rad]")
    parser.add_argument("--M1", type=float, default=None, help="departure mean anomaly [rad]")
    parser.add_argument("--rx1", type=float, default=None, help="departure inertial position x [m]")
    parser.add_argument("--ry1", type=float, default=None, help="departure inertial position y [m]")
    parser.add_argument("--rz1", type=float, default=None, help="departure inertial position z [m]")
    parser.add_argument("--vx1", type=float, default=None, help="departure inertial velocity x [m/s]")
    parser.add_argument("--vy1", type=float, default=None, help="departure inertial velocity y [m/s]")
    parser.add_argument("--vz1", type=float, default=None, help="departure inertial velocity z [m/s]")
    parser.add_argument("--a2", type=float, default=None, help="arrival semi-major axis [m]")
    parser.add_argument("--e2", type=float, default=None, help="arrival eccentricity")
    parser.add_argument("--i2", type=float, default=None, help="arrival inclination [rad]")
    parser.add_argument("--raan2", type=float, default=None, help="arrival longitude of the ascending node [rad]")
    parser.add_argument("--aop2", type=float, default=None, help="arrival argument of periapsis [rad]")
    parser.add_argument("--nu2", type=float, default=None, help="arrival true anomaly [rad]")
    parser.add_argument("--M2", type=float, default=None, help="arrival mean anomaly [rad]")
    parser.add_argument("--rx2", type=float, default=None, help="arrival inertial position x [m]")
    parser.add_argument("--ry2", type=float, default=None, help="arrival inertial position y [m]")
    parser.add_argument("--rz2", type=float, default=None, help="arrival inertial position z [m]")
    parser.add_argument("--vx2", type=float, default=None, help="arrival inertial velocity x [m/s]")
    parser.add_argument("--vy2", type=float, default=None, help="arrival inertial velocity y [m/s]")
    parser.add_argument("--vz2", type=float, default=None, help="arrival inertial velocity z [m/s]")
    parser.add_argument(
        "--tle1",
        nargs="+",
        default=None,
        help="departure NORAD two-line elements; two 69-character lines, optional name line first",
    )
    parser.add_argument(
        "--tle2",
        nargs="+",
        default=None,
        help="arrival NORAD two-line elements; two 69-character lines, optional name line first",
    )
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"planetary radius [m]; default Earth {ht.R0_EARTH:.8g}",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--html", action="store_true", help="write the optional HTML 3D viewer beside the PNG")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
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


if __name__ == "__main__":
    sys.exit(main())
