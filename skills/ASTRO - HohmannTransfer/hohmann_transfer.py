#!/usr/bin/env python3
"""Impulsive Hohmann transfer between two circular orbits.

Circular and escape speeds, specific energy, coast speed, and time of flight
come from circular_orbit_velocity, escape_velocity, specific_orbital_energy,
vis_viva, and orbital_period in formulas.md.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path

# Earth values from formulas.md. R0 is the circular-orbit and escape radius.
# g0 is standard sea-level gravity. mu = g0 * R0^2.
G0 = 9.80665
R0_EARTH = 6.3742e6
PLOT_TITLE = "Hohmann transfer"
CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent
PNG_ELEV_DEG = 90.0
PNG_AZIM_DEG = -90.0
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
DV_COLOR = "#e67e22"
BURN_WALL_S = 2.4
PARK_WALL_S = 3.2
COAST_WALL_S = 8.0
ARRIVE_WALL_S = 12.0
_OP = None
ASSUMPTIONS = (
    "impulsive two-burn Hohmann transfer between circular orbits about a "
    "spherical planet; inverse-square gravity with no drag, thrust, or third "
    "body on the coast; the burns are impulsive at opposite apsides and the "
    "coast is half of the transfer ellipse; circular speed is "
    "circular_orbit_velocity, escape speed is escape_velocity, coast speeds "
    "are vis_viva, specific energy is specific_orbital_energy, and time of "
    "flight is half of orbital_period; mu = g0*R0^2 with g0 = 9.80665 m/s^2; "
    "Earth default R0 = 6374200 m; a radius is distance from the center and "
    "an altitude is geometric height above R0"
)


@dataclass(frozen=True)
class Body:
    radius: float
    g0: float
    mu: float
    radius_source: str


@dataclass(frozen=True)
class Transfer:
    mode: str
    direction: str
    r_depart: float
    r_arrive: float
    a: float
    e: float
    v_circular_depart: float
    v_escape_depart: float
    v_circular_arrive: float
    v_escape_arrive: float
    energy_depart: float
    energy_arrive: float
    energy_transfer: float
    v_depart_transfer: float
    v_arrive_transfer: float
    dv_depart: float
    dv_arrive: float
    sense_depart: str
    sense_arrive: str
    dv: float
    tof: float
    period: float


def op_mod():
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


def linspace(lo: float, hi: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("need at least 2 samples")
    step = (hi - lo) / (count - 1)
    values = [lo + step * i for i in range(count)]
    values[-1] = hi
    return values


def require_finite(value: float, flag: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def circular_speed(mu: float, radius: float) -> float:
    """circular_orbit_velocity, written as sqrt(mu/r) with mu = g0*R0^2."""
    return math.sqrt(mu / radius)


def escape_speed(mu: float, radius: float) -> float:
    """escape_velocity, written as sqrt(2*mu/r)."""
    return math.sqrt(2.0 * mu / radius)


def specific_energy(mu: float, semi_major: float) -> float:
    """specific_orbital_energy."""
    return -(mu) / (2.0 * semi_major)


def vis_viva(mu: float, radius: float, semi_major: float) -> float:
    """vis_viva. A circular orbit uses semi_major = radius."""
    argument = mu * (2.0 / radius - 1.0 / semi_major)
    scale = mu / radius
    if argument < 0.0:
        if argument > -1e-9 * scale:
            argument = 0.0
        else:
            raise ValueError("transfer speed is not real at that radius")
    return math.sqrt(argument)


def orbital_period(mu: float, semi_major: float) -> float:
    """orbital_period."""
    return 2.0 * math.pi * math.sqrt(semi_major**3 / mu)


def burn_sense(speed_after: float, speed_before: float) -> str:
    span = max(abs(speed_before), abs(speed_after), 1.0)
    if math.isclose(speed_after, speed_before, rel_tol=1e-9, abs_tol=1e-6 * span):
        return "none"
    if speed_after > speed_before:
        return "prograde"
    return "retrograde"


def same_radius(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=0.0)


def radius_ratio(r_depart: float, r_arrive: float) -> float:
    """|r_arrive| / |r_depart|."""
    if r_depart == 0.0:
        raise ValueError("departure radius must be > 0 m")
    return abs(r_arrive) / abs(r_depart)


def biparabolic_delta_v(mu: float, r_depart: float, r_arrive: float) -> float:
    """Sum of (escape minus circular) at both radii, from escape_velocity and circular_orbit_velocity."""
    return (escape_speed(mu, r_depart) - circular_speed(mu, r_depart)) + (
        escape_speed(mu, r_arrive) - circular_speed(mu, r_arrive)
    )


def recommend_against_biparabolic(dv: float, dv_infinity: float) -> str:
    """Hohmann if it is cheaper than a transfer through infinity; otherwise bielliptic."""
    span = max(abs(dv_infinity), abs(dv), 1.0)
    if dv > dv_infinity and not math.isclose(dv, dv_infinity, rel_tol=1e-12, abs_tol=1e-9 * span):
        return "bielliptic"
    return "Hohmann"


def solve_transfer(mu: float, r_depart: float, r_arrive: float, mode: str) -> Transfer:
    """Two-burn Hohmann transfer. r_depart is the first circular orbit."""
    if r_depart <= 0.0 or r_arrive <= 0.0:
        raise ValueError("orbit radii must be > 0 m")
    if same_radius(r_depart, r_arrive):
        direction = "coast"
        periapsis = r_depart
        apoapsis = r_depart
    elif r_depart < r_arrive:
        direction = "outward"
        periapsis = r_depart
        apoapsis = r_arrive
    else:
        direction = "inward"
        periapsis = r_arrive
        apoapsis = r_depart

    semi_major = 0.5 * (periapsis + apoapsis)
    if direction == "coast":
        eccentricity = 0.0
    else:
        eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)

    if direction == "inward":
        v_depart_transfer = vis_viva(mu, apoapsis, semi_major)
        v_arrive_transfer = vis_viva(mu, periapsis, semi_major)
    else:
        v_depart_transfer = vis_viva(mu, periapsis, semi_major)
        v_arrive_transfer = vis_viva(mu, apoapsis, semi_major)

    v_circular_depart = circular_speed(mu, r_depart)
    v_circular_arrive = circular_speed(mu, r_arrive)
    dv_depart = abs(v_depart_transfer - v_circular_depart)
    dv_arrive = abs(v_circular_arrive - v_arrive_transfer)
    period = orbital_period(mu, semi_major)
    return Transfer(
        mode=mode,
        direction=direction,
        r_depart=r_depart,
        r_arrive=r_arrive,
        a=semi_major,
        e=eccentricity,
        v_circular_depart=v_circular_depart,
        v_escape_depart=escape_speed(mu, r_depart),
        v_circular_arrive=v_circular_arrive,
        v_escape_arrive=escape_speed(mu, r_arrive),
        energy_depart=specific_energy(mu, r_depart),
        energy_arrive=specific_energy(mu, r_arrive),
        energy_transfer=specific_energy(mu, semi_major),
        v_depart_transfer=v_depart_transfer,
        v_arrive_transfer=v_arrive_transfer,
        dv_depart=dv_depart,
        dv_arrive=dv_arrive,
        sense_depart=burn_sense(v_depart_transfer, v_circular_depart),
        sense_arrive=burn_sense(v_circular_arrive, v_arrive_transfer),
        dv=dv_depart + dv_arrive,
        tof=0.5 * period,
        period=period,
    )


def radii_from_altitude(body_radius: float, altitude: float, eccentricity: float) -> tuple[float, float]:
    """Departure on the circular orbit at this altitude, periapsis of the ellipse."""
    require_finite(altitude, "--alt")
    require_finite(eccentricity, "--ecc")
    if altitude < 0.0:
        raise ValueError("--alt must be >= 0 m")
    if eccentricity < 0.0 or eccentricity >= 1.0:
        raise ValueError("--ecc must satisfy 0 <= e < 1")
    r_depart = body_radius + altitude
    r_arrive = r_depart * (1.0 + eccentricity) / (1.0 - eccentricity)
    return r_depart, r_arrive


def require_outside_body(transfer: Transfer, body_radius: float) -> None:
    for flag, radius in (
        ("departure", transfer.r_depart),
        ("arrival", transfer.r_arrive),
    ):
        if radius < body_radius and not same_radius(radius, body_radius):
            raise ValueError(
                f"{flag} radius {radius:.8g} m is inside the planetary "
                f"radius {body_radius:.8g} m"
            )


def surface_warning(transfer: Transfer, body_radius: float) -> str | None:
    notes = []
    if same_radius(transfer.r_depart, body_radius):
        notes.append("the departure orbit lies on the planetary surface")
    if same_radius(transfer.r_arrive, body_radius):
        notes.append("the arrival orbit lies on the planetary surface")
    if transfer.direction == "coast":
        notes.append(
            "the two circular radii are equal, so both burns are zero and "
            "the coast is a half revolution on that circle"
        )
    if not notes:
        return None
    return "; ".join(notes)


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the Hohmann transfer") from exc
    return plt


def polar_xy(radius_of_angle, angles: list[float]) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for angle in angles:
        radius_km = radius_of_angle(angle) / 1000.0
        xs.append(radius_km * math.cos(angle))
        ys.append(radius_km * math.sin(angle))
    return xs, ys


def format_tof(seconds: float) -> str:
    if seconds >= 3600.0:
        return f"{seconds / 3600.0:.4g} h"
    if seconds >= 60.0:
        return f"{seconds / 60.0:.4g} min"
    return f"{seconds:.4g} s"


def km(meters: float) -> float:
    return meters / 1000.0


def apsis_xy_km(radius: float, nu: float) -> tuple[float, float]:
    return km(radius * math.cos(nu)), km(radius * math.sin(nu))


def apsis_tangent(nu: float) -> tuple[float, float, float]:
    return (-math.sin(nu), math.cos(nu), 0.0)


def burn_vector_m_s(delta_v: float, sense: str, nu: float) -> tuple[float, float, float]:
    if sense == "none" or delta_v == 0.0:
        return (0.0, 0.0, 0.0)
    tx, ty, tz = apsis_tangent(nu)
    sign = 1.0 if sense == "prograde" else -1.0
    return (sign * delta_v * tx, sign * delta_v * ty, sign * delta_v * tz)


def equatorial_circle_km(radius: float, count: int = 361) -> list[list[float]]:
    points: list[list[float]] = []
    for angle in linspace(0.0, 2.0 * math.pi, count):
        points.append([km(radius * math.cos(angle)), km(radius * math.sin(angle)), 0.0])
    return points


def equatorial_arc_km(semi_major: float, eccentricity: float, nu0: float, nu1: float, count: int = 181) -> list[list[float]]:
    points: list[list[float]] = []
    parameter = semi_major * (1.0 - eccentricity**2) if eccentricity < 1.0 else semi_major
    for nu in linspace(nu0, nu1, count):
        radius = parameter / (1.0 + eccentricity * math.cos(nu)) if eccentricity > 1e-12 else semi_major
        points.append([km(radius * math.cos(nu)), km(radius * math.sin(nu)), 0.0])
    return points


def coast_leg(
    mu: float,
    semi_major: float,
    eccentricity: float,
    nu0: float,
    nu1: float,
    wall_s: float,
    layer: str,
    label: str,
) -> dict[str, object]:
    parameter = semi_major if eccentricity <= 1e-12 else semi_major * (1.0 - eccentricity**2)
    return {
        "kind": "coast",
        "label": label,
        "layer": layer,
        "wall_s": wall_s,
        "a": semi_major,
        "e": eccentricity,
        "i": 0.0,
        "Omega": 0.0,
        "omega": 0.0,
        "p": parameter,
        "h": math.sqrt(mu * parameter),
        "mu": mu,
        "nu0": nu0,
        "nu1": nu1,
    }


def conic_apsides(mu: float, periapsis: float, apoapsis: float) -> dict[str, float]:
    """Ellipse or circle from periapsis and apoapsis radii."""
    inner = min(periapsis, apoapsis)
    outer = max(periapsis, apoapsis)
    semi_major = 0.5 * (inner + outer)
    if same_radius(inner, outer):
        eccentricity = 0.0
        parameter = inner
    else:
        eccentricity = (outer - inner) / (outer + inner)
        parameter = semi_major * (1.0 - eccentricity**2)
    return {
        "a": semi_major,
        "e": eccentricity,
        "p": parameter,
        "h": math.sqrt(mu * parameter),
        "mu": mu,
        "rp": inner,
        "ra": outer,
        "i": 0.0,
        "Omega": 0.0,
        "omega": 0.0,
    }


def burn_leg(
    index: int,
    label: str,
    layer: str = "",
    from_conic: dict[str, float] | None = None,
    to_conic: dict[str, float] | None = None,
    from_layer: str = "",
    to_layer: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": "burn",
        "label": label,
        "layer": layer,
        "wall_s": BURN_WALL_S,
        "burn": index,
    }
    if from_conic is not None and to_conic is not None:
        payload["from"] = from_conic
        payload["to"] = to_conic
        payload["from_layer"] = from_layer
        payload["to_layer"] = to_layer
    return payload


def planet_backdrop(body: Body, outer_m: float) -> dict[str, object]:
    op = op_mod()
    span = max(body.radius, outer_m)
    limit_m = op.LIMIT_SPAN_FRAC * span
    axis_len = min(max(1.35 * body.radius, 0.42 * span), 0.72 * span)
    ring_r = min(1.22 * body.radius, 0.98 * span)
    same_earth = math.isclose(body.radius, R0_EARTH, rel_tol=1e-9, abs_tol=0.0)
    flattening = op.F_EARTH if same_earth else 0.0
    polar_m = body.radius * (1.0 - flattening)
    ring_angles = linspace(0.0, 2.0 * math.pi, 181)
    ring = [[km(ring_r * math.cos(angle)), km(ring_r * math.sin(angle)), 0.0] for angle in ring_angles]
    equator = [
        [km(body.radius * math.cos(angle)), km(body.radius * math.sin(angle)), 0.0] for angle in ring_angles
    ]
    spokes: list[list[list[float]]] = []
    inner = min(body.radius, ring_r)
    if ring_r > inner * (1.0 + 1e-6):
        for spoke in range(8):
            angle = spoke * math.pi / 8.0
            spokes.append(
                [
                    [km(inner * math.cos(angle)), km(inner * math.sin(angle)), 0.0],
                    [km(ring_r * math.cos(angle)), km(ring_r * math.sin(angle)), 0.0],
                ]
            )
    axes = [
        {"label": "X", "tip_km": [km(axis_len), 0.0, 0.0], "label_km": [km(axis_len * 1.08), 0.0, 0.0]},
        {"label": "Y", "tip_km": [0.0, km(axis_len), 0.0], "label_km": [0.0, km(axis_len * 1.08), 0.0]},
        {"label": "Z", "tip_km": [0.0, 0.0, km(axis_len)], "label_km": [0.0, 0.0, km(axis_len * 1.08)]},
    ]
    return {
        "limit_km": km(limit_m),
        "axis_length_km": km(axis_len),
        "equatorial_radius_km": km(body.radius),
        "polar_radius_km": km(polar_m),
        "flattening": flattening,
        "planet_segments_u": op.PLANET_SEGMENTS_U,
        "planet_segments_v": op.PLANET_SEGMENTS_V,
        "planet_opacity": 0.52,
        "ring_km": ring,
        "spokes_km": spokes,
        "equator_km": equator,
        "axes": axes,
        "velocity_length_km": km(op.ARROW_SPAN_FRAC * span),
    }


def write_viewer_html(skill_dir: Path, path: Path, payload: dict[str, object], title: str) -> None:
    viewer_dir = skill_dir / "viewer"
    try:
        template = (viewer_dir / "template.html").read_text(encoding="utf-8")
        three_source = (viewer_dir / "three.min.js").read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read the viewer template: {exc}") from exc
    lowered = three_source.lower()
    if "</script>" in lowered:
        three_source = three_source.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"))
    encoded = encoded.replace("<", "\\u003c")
    before, placeholder, after = template.partition("__THREE_SOURCE__")
    if not placeholder:
        raise ValueError("viewer template is missing the Three.js placeholder")
    before = before.replace("__TITLE__", title).replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
    after = (
        after.replace("__TITLE__", title)
        .replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
        .replace("__SCENE_JSON__", encoded)
    )
    html = before + three_source + after
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not write the viewer: {exc}") from exc


def scene_from_html(html: str) -> dict[str, object]:
    token = '<script type="application/json" id="orbital-scene">'
    start = html.find(token)
    if start < 0:
        raise ValueError("viewer is missing the scene payload")
    start += len(token)
    end = html.find("</script>", start)
    if end < 0:
        raise ValueError("viewer scene payload is not closed")
    return json.loads(html[start:end])


def hohmann_anomalies(transfer: Transfer) -> tuple[float, float]:
    if transfer.direction == "inward":
        return math.pi, 2.0 * math.pi
    return 0.0, math.pi


def build_hohmann_payload(body: Body, transfer: Transfer) -> dict[str, object]:
    op = op_mod()
    nu_depart, nu_arrive = hohmann_anomalies(transfer)
    outer = max(transfer.r_depart, transfer.r_arrive, body.radius)
    scene = planet_backdrop(body, outer)
    palette = dict(op.PALETTE)
    palette["dv"] = DV_COLOR
    palette["transfer"] = "#c0392b"
    palette["arrive"] = "#1a5276"
    dv_depart = burn_vector_m_s(transfer.dv_depart, transfer.sense_depart, nu_depart)
    dv_arrive = burn_vector_m_s(transfer.dv_arrive, transfer.sense_arrive, nu_arrive)
    depart_km = [apsis_xy_km(transfer.r_depart, nu_depart)[0], apsis_xy_km(transfer.r_depart, nu_depart)[1], 0.0]
    arrive_km = [apsis_xy_km(transfer.r_arrive, nu_arrive)[0], apsis_xy_km(transfer.r_arrive, nu_arrive)[1], 0.0]
    layers = [
        {
            "id": "depart",
            "color": palette["orbit"],
            "faded": True,
            "polylines": [equatorial_circle_km(transfer.r_depart)],
        },
        {
            "id": "arrive",
            "color": palette["arrive"],
            "faded": True,
            "polylines": [equatorial_circle_km(transfer.r_arrive)],
        },
        {
            "id": "transfer",
            "color": palette["transfer"],
            "faded": False,
            "polylines": [equatorial_arc_km(transfer.a, transfer.e, 0.0, 2.0 * math.pi, 361)],
        },
    ]
    burns = [
        {"km": depart_km, "dv_m_s": list(dv_depart), "color": DV_COLOR, "label": "departure burn"},
        {"km": arrive_km, "dv_m_s": list(dv_arrive), "color": DV_COLOR, "label": "arrival burn"},
    ]
    markers = [
        {"id": "departure", "label": "departure", "shape": "square", "color": "#27ae60", "km": depart_km},
        {"id": "arrival", "label": "arrival", "shape": "circle", "color": palette["arrive"], "km": arrive_km},
        {"id": "spacecraft", "label": "spacecraft", "shape": "circle", "color": palette["craft"], "km": depart_km},
    ]
    legend = [
        {"label": "planet", "swatch": "planet", "color": palette["planet"], "edge": palette["planet_edge"]},
        {"label": "departure orbit", "swatch": "line", "color": palette["orbit"], "edge": None},
        {"label": "arrival orbit", "swatch": "line", "color": palette["arrive"], "edge": None},
        {"label": "transfer ellipse", "swatch": "line", "color": palette["transfer"], "edge": None},
        {"label": "departure", "swatch": "square", "color": "#27ae60", "edge": None},
        {"label": "arrival", "swatch": "circle", "color": palette["arrive"], "edge": None},
        {"label": "spacecraft", "swatch": "circle", "color": palette["craft"], "edge": None},
        {"label": "delta-v", "swatch": "line", "color": DV_COLOR, "edge": None},
    ]
    park_start = nu_depart - 0.55
    circular_depart = conic_apsides(body.mu, transfer.r_depart, transfer.r_depart)
    circular_arrive = conic_apsides(body.mu, transfer.r_arrive, transfer.r_arrive)
    transfer_conic = conic_apsides(
        body.mu,
        transfer.a * (1.0 - transfer.e),
        transfer.a * (1.0 + transfer.e),
    )
    sequence: list[dict[str, object]] = [
        coast_leg(body.mu, transfer.r_depart, 0.0, park_start, nu_depart, PARK_WALL_S, "depart", "departure orbit"),
        burn_leg(
            0,
            "departure burn",
            "transfer",
            circular_depart,
            transfer_conic,
            "depart",
            "transfer",
        ),
        coast_leg(
            body.mu, transfer.a, transfer.e, nu_depart, nu_arrive, COAST_WALL_S, "transfer", "transfer ellipse"
        ),
        burn_leg(
            1,
            "arrival burn",
            "arrive",
            transfer_conic,
            circular_arrive,
            "transfer",
            "arrive",
        ),
        coast_leg(
            body.mu,
            transfer.r_arrive,
            0.0,
            nu_arrive,
            nu_arrive + 4.0 * math.pi,
            ARRIVE_WALL_S,
            "arrive",
            "arrival orbit",
        ),
    ]
    payload = {
        "title": PLOT_TITLE,
        "elev_deg": PNG_ELEV_DEG,
        "azim_deg": PNG_AZIM_DEG,
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
    return payload


def draw_delta_v(
    ax: object,
    origin: tuple[float, float],
    vector: tuple[float, float, float],
    length_km: float,
    color: str,
) -> None:
    mag = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    if mag < 1e-12 or length_km <= 0.0:
        return
    dx = vector[0] / mag * length_km
    dy = vector[1] / mag * length_km
    ax.annotate(
        "",
        xy=(origin[0] + dx, origin[1] + dy),
        xytext=origin,
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "lw": 1.8,
            "mutation_scale": 16,
        },
        zorder=8,
    )


def plot_transfer(path: Path, body: Body, transfer: Transfer) -> None:
    """Planet, both circular orbits, and the coasting half of the transfer ellipse."""
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8.4, 7.2))

    def circle(radius: float, angle: float) -> float:
        return radius

    full = linspace(0.0, 2.0 * math.pi, 361)
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
    if not same_radius(transfer.r_depart, transfer.r_arrive):
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

    def ellipse_radius(angle: float) -> float:
        eccentricity = transfer.e
        return transfer.a * (1.0 - eccentricity**2) / (1.0 + eccentricity * math.cos(angle))

    if transfer.e > 1e-8:
        ellipse_x, ellipse_y = polar_xy(ellipse_radius, full)
        ax.plot(
            ellipse_x,
            ellipse_y,
            color="#85929e",
            linestyle="--",
            linewidth=0.9,
            zorder=3,
            label="transfer ellipse",
        )

    if transfer.direction == "inward":
        coast = linspace(math.pi, 2.0 * math.pi, 181)
    else:
        coast = linspace(0.0, math.pi, 181)
    coast_x, coast_y = polar_xy(ellipse_radius, coast)
    ax.plot(
        coast_x,
        coast_y,
        color="#c0392b",
        linewidth=2.2,
        zorder=4,
        label="transfer coast",
    )
    mid = len(coast_x) // 2
    ahead = min(len(coast_x) - 1, mid + max(1, len(coast_x) // 36))
    ax.annotate(
        "",
        xy=(coast_x[ahead], coast_y[ahead]),
        xytext=(coast_x[mid], coast_y[mid]),
        arrowprops={
            "arrowstyle": "-|>",
            "color": "#c0392b",
            "lw": 1.6,
            "mutation_scale": 14,
        },
        zorder=5,
    )
    ax.plot(
        coast_x[0],
        coast_y[0],
        "s",
        color="#27ae60",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="departure",
    )
    ax.plot(
        coast_x[-1],
        coast_y[-1],
        "o",
        color="#1a5276",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="arrival",
    )
    nu_depart, nu_arrive = hohmann_anomalies(transfer)
    outer = max(transfer.r_depart, transfer.r_arrive, body.radius)
    arrow_km = 0.10 * outer / 1000.0
    draw_delta_v(
        ax,
        apsis_xy_km(transfer.r_depart, nu_depart),
        burn_vector_m_s(transfer.dv_depart, transfer.sense_depart, nu_depart),
        arrow_km,
        DV_COLOR,
    )
    draw_delta_v(
        ax,
        apsis_xy_km(transfer.r_arrive, nu_arrive),
        burn_vector_m_s(transfer.dv_arrive, transfer.sense_arrive, nu_arrive),
        arrow_km,
        DV_COLOR,
    )

    outer = max(transfer.r_depart, transfer.r_arrive, body.radius)
    limit = 1.18 * outer / 1000.0
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(PLOT_TITLE)
    h_depart = (transfer.r_depart - body.radius) / 1000.0
    h_arrive = (transfer.r_arrive - body.radius) / 1000.0
    ax.text(
        0.5,
        1.02,
        f"{h_depart:.6g} km altitude to {h_arrive:.6g} km altitude",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#34495e",
    )
    ax.text(
        0.02,
        0.98,
        f"delta-v  {transfer.dv:.6g} m/s\nTOF  {format_tof(transfer.tof)}",
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


def print_report(body: Body, transfer: Transfer, path: Path, viewer: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", transfer.mode)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("r_depart_m", transfer.r_depart)
    print_kv("r_arrive_m", transfer.r_arrive)
    print_kv("h_depart_m", transfer.r_depart - body.radius)
    print_kv("h_arrive_m", transfer.r_arrive - body.radius)
    print_kv("direction", transfer.direction)
    print_kv("a_m", transfer.a)
    print_kv("e", transfer.e)
    print_kv("v_circular_depart_m_s", transfer.v_circular_depart)
    print_kv("v_escape_depart_m_s", transfer.v_escape_depart)
    print_kv("v_circular_arrive_m_s", transfer.v_circular_arrive)
    print_kv("v_escape_arrive_m_s", transfer.v_escape_arrive)
    print_kv("energy_depart_J_kg", transfer.energy_depart)
    print_kv("energy_arrive_J_kg", transfer.energy_arrive)
    print_kv("energy_transfer_J_kg", transfer.energy_transfer)
    print_kv("v_depart_transfer_m_s", transfer.v_depart_transfer)
    print_kv("v_arrive_transfer_m_s", transfer.v_arrive_transfer)
    print_kv("dv_depart_m_s", transfer.dv_depart)
    print_kv("dv_depart_sense", transfer.sense_depart)
    print_kv("dv_arrive_m_s", transfer.dv_arrive)
    print_kv("dv_arrive_sense", transfer.sense_arrive)
    print_kv("dv_m_s", transfer.dv)
    print_kv("tof_s", transfer.tof)
    print_kv("period_s", transfer.period)
    ratio = radius_ratio(transfer.r_depart, transfer.r_arrive)
    dv_infinity = biparabolic_delta_v(body.mu, transfer.r_depart, transfer.r_arrive)
    print_kv("r2_over_r1", ratio)
    print_kv("dv_biparabolic_m_s", dv_infinity)
    print_kv("recommendation", recommend_against_biparabolic(transfer.dv, dv_infinity))
    warning = surface_warning(transfer, body.radius)
    if warning:
        print_kv("warning", warning)
    print_kv("elev_deg", PNG_ELEV_DEG)
    print_kv("azim_deg", PNG_AZIM_DEG)
    print_kv("graph", str(path))
    if viewer is not None:
        print_kv("viewer", str(viewer))


def resolve_body(radius_arg: float | None) -> Body:
    if radius_arg is None:
        radius = R0_EARTH
        source = "default"
    else:
        require_finite(radius_arg, "--R0")
        if radius_arg <= 0.0:
            raise ValueError("--R0 must be > 0 m")
        radius = radius_arg
        source = "input"
    return Body(radius=radius, g0=G0, mu=G0 * radius**2, radius_source=source)


def resolve_radii(ns: argparse.Namespace, body: Body) -> tuple[str, float, float]:
    have_radii = ns.r1 is not None or ns.r2 is not None
    have_altitude = ns.alt is not None or ns.ecc is not None
    if have_radii and have_altitude:
        raise ValueError("pass either --r1 and --r2, or --alt and --ecc")
    if have_radii:
        if ns.r1 is None or ns.r2 is None:
            raise ValueError("--r1 and --r2 are both required")
        require_finite(ns.r1, "--r1")
        require_finite(ns.r2, "--r2")
        return "radii", ns.r1, ns.r2
    if have_altitude:
        if ns.alt is None or ns.ecc is None:
            raise ValueError("--alt and --ecc are both required")
        r_depart, r_arrive = radii_from_altitude(body.radius, ns.alt, ns.ecc)
        return "altitude", r_depart, r_arrive
    raise ValueError("pass --r1 and --r2, or --alt and --ecc")


def run(ns: argparse.Namespace) -> int:
    body = resolve_body(ns.R0)
    mode, r_depart, r_arrive = resolve_radii(ns, body)
    transfer = solve_transfer(body.mu, r_depart, r_arrive, mode)
    require_outside_body(transfer, body.radius)
    script_dir = Path(__file__).resolve().parent
    out_path = Path(ns.out) if ns.out else script_dir / "hohmann_transfer.png"
    out_path = out_path.resolve()
    plot_transfer(out_path, body, transfer)
    viewer_path = out_path.with_suffix(".html")
    wrote_html = bool(ns.html or ns.open)
    if wrote_html:
        write_viewer_html(SKILL_DIR, viewer_path, build_hohmann_payload(body, transfer), PLOT_TITLE)
    print_report(body, transfer, out_path, viewer_path if wrote_html else None)
    if ns.open:
        webbrowser.open(viewer_path.as_uri())
    return 0


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def algebraic_outward(mu: float, r1: float, r2: float) -> tuple[float, float]:
    """Speed change at periapsis, then at apoapsis, for r2 > r1."""
    dv1 = math.sqrt(mu / r1) * (math.sqrt(2.0 * r2 / (r1 + r2)) - 1.0)
    dv2 = math.sqrt(mu / r2) * (1.0 - math.sqrt(2.0 * r1 / (r1 + r2)))
    return dv1, dv2


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    body = resolve_body(None)
    if body.radius_source != "default" or body.radius != R0_EARTH:
        return fail("Earth radius default")
    if not close_enough(body.mu, G0 * R0_EARTH**2, body.mu):
        return fail("mu is not g0*R0^2")

    # circular_orbit_velocity and escape_velocity at the surface.
    surface_circular = R0_EARTH * math.sqrt(G0 / R0_EARTH)
    surface_escape = R0_EARTH * math.sqrt(2.0 * G0 / R0_EARTH)
    if not close_enough(circular_speed(body.mu, R0_EARTH), surface_circular, surface_circular):
        return fail("surface circular speed")
    if not close_enough(escape_speed(body.mu, R0_EARTH), surface_escape, surface_escape):
        return fail("surface escape speed")
    if not close_enough(surface_escape, math.sqrt(2.0) * surface_circular, surface_escape):
        return fail("escape speed is not sqrt(2) times circular speed")

    # Altitude form of circular_orbit_velocity.
    altitude = 400000.0
    radius = R0_EARTH + altitude
    from_altitude_formula = R0_EARTH * math.sqrt(G0 / radius)
    if not close_enough(circular_speed(body.mu, radius), from_altitude_formula, from_altitude_formula):
        return fail("circular speed at altitude")

    mu = 1.0
    r1 = 1.0
    r2 = 4.0
    outward = solve_transfer(mu, r1, r2, "radii")
    dv1, dv2 = algebraic_outward(mu, r1, r2)
    if outward.direction != "outward":
        return fail("r2 > r1 was not outward")
    if not close_enough(outward.a, 2.5, 2.5):
        return fail("semi-major axis")
    if not close_enough(outward.e, 0.6, 1.0):
        return fail("eccentricity")
    if not close_enough(outward.dv_depart, dv1, 1.0):
        return fail(f"departure delta-v {outward.dv_depart} != {dv1}")
    if not close_enough(outward.dv_arrive, dv2, 1.0):
        return fail(f"arrival delta-v {outward.dv_arrive} != {dv2}")
    if outward.sense_depart != "prograde" or outward.sense_arrive != "prograde":
        return fail("outward burns were not prograde")
    if not close_enough(outward.v_circular_depart, 1.0, 1.0):
        return fail("unit circular speed")
    if not close_enough(outward.v_escape_depart, math.sqrt(2.0), 1.0):
        return fail("unit escape speed")
    if not close_enough(outward.v_circular_arrive, 0.5, 1.0):
        return fail("outer circular speed")
    expected_period = 2.0 * math.pi * math.sqrt(2.5**3 / mu)
    if not close_enough(outward.period, expected_period, expected_period):
        return fail("period")
    if not close_enough(outward.tof, 0.5 * expected_period, expected_period):
        return fail("time of flight is not half the period")

    for radius_i, speed in (
        (r1, outward.v_depart_transfer),
        (r2, outward.v_arrive_transfer),
    ):
        from_speed = speed**2 / 2.0 - mu / radius_i
        if not close_enough(from_speed, outward.energy_transfer, 1.0):
            return fail("specific energy did not match vis-viva")
    if not close_enough(outward.energy_depart, -mu / (2.0 * r1), 1.0):
        return fail("departure circular energy")
    if not close_enough(outward.energy_transfer, -mu / (2.0 * outward.a), 1.0):
        return fail("transfer energy")

    inward = solve_transfer(mu, r2, r1, "radii")
    if inward.direction != "inward":
        return fail("r1 > r2 was not inward")
    if not close_enough(inward.dv, outward.dv, 1.0):
        return fail("inward total delta-v")
    if not close_enough(inward.dv_depart, outward.dv_arrive, 1.0):
        return fail("inward departure burn")
    if not close_enough(inward.dv_arrive, outward.dv_depart, 1.0):
        return fail("inward arrival burn")
    if inward.sense_depart != "retrograde" or inward.sense_arrive != "retrograde":
        return fail("inward burns were not retrograde")
    if not close_enough(inward.tof, outward.tof, outward.tof):
        return fail("inward time of flight")

    coast = solve_transfer(mu, r1, r1, "radii")
    if coast.direction != "coast" or coast.dv != 0.0 or coast.e != 0.0:
        return fail("equal radii did not coast with zero delta-v")
    if coast.sense_depart != "none" or coast.sense_arrive != "none":
        return fail("equal-radius burns were not none")
    half_turn = math.pi * math.sqrt(r1**3 / mu)
    if not close_enough(coast.tof, half_turn, half_turn):
        return fail("equal-radius time of flight")
    if not close_enough(radius_ratio(r1, r2), 4.0, 4.0):
        return fail("radius ratio")
    if recommend_against_biparabolic(outward.dv, biparabolic_delta_v(mu, r1, r2)) != "Hohmann":
        return fail("small radius ratio should recommend Hohmann")
    wide = solve_transfer(mu, 1.0, 20.0, "radii")
    if recommend_against_biparabolic(wide.dv, biparabolic_delta_v(mu, 1.0, 20.0)) != "bielliptic":
        return fail("large radius ratio should recommend a bielliptic transfer")

    # Altitude plus eccentricity is the outward Hohmann with periapsis at that altitude.
    ecc = 0.2
    r_depart, r_arrive = radii_from_altitude(body.radius, altitude, ecc)
    by_altitude = solve_transfer(body.mu, r_depart, r_arrive, "altitude")
    by_radii = solve_transfer(body.mu, r_depart, r_arrive, "radii")
    if not close_enough(by_altitude.e, ecc, 1.0):
        return fail("altitude mode eccentricity")
    if by_altitude.direction != "outward":
        return fail("altitude mode was not outward")
    if not close_enough(by_altitude.dv, by_radii.dv, max(by_radii.dv, 1.0)):
        return fail("altitude mode delta-v")
    if not close_enough(by_altitude.tof, by_radii.tof, by_radii.tof):
        return fail("altitude mode time of flight")
    dv_alt_1, dv_alt_2 = algebraic_outward(body.mu, r_depart, r_arrive)
    if not close_enough(by_altitude.dv_depart, dv_alt_1, max(dv_alt_1, 1.0)):
        return fail("Earth departure delta-v")
    if not close_enough(by_altitude.dv_arrive, dv_alt_2, max(dv_alt_2, 1.0)):
        return fail("Earth arrival delta-v")

    try:
        radii_from_altitude(body.radius, altitude, 1.0)
    except ValueError:
        pass
    else:
        return fail("eccentricity of 1 was accepted")
    try:
        solve_transfer(body.mu, body.radius - 1.0, body.radius * 2.0, "radii")
        require_outside_body(
            solve_transfer(body.mu, body.radius - 1.0, body.radius * 2.0, "radii"),
            body.radius,
        )
    except ValueError:
        pass
    else:
        return fail("a radius inside the planet was accepted")

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
            code = main(
                [
                    "--alt",
                    "400000",
                    "--ecc",
                    "0.2",
                    "--out",
                    out,
                ]
            )
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"altitude main returned {code}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        text = "".join(captured)
        for key in (
            "mode: altitude",
            "direction: outward",
            "v_circular_depart_m_s:",
            "v_escape_depart_m_s:",
            "energy_transfer_J_kg:",
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
                ["--r1", "1", "--r2", "4", "--R0", "0.5", "--out", html_out, "--html"]
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
        if "departure burn" not in html or "sequence" not in html:
            return fail("HTML missing burns")
        if "flownTrails" in html:
            return fail("viewer still draws a partial coast trail")
        if "function activeLayer" not in html:
            return fail("viewer missing the current-orbit highlight")
        if "lerpApsides" not in html or "morphOrbit" not in html:
            return fail("viewer missing the burn morph")
        scene = scene_from_html(html)
        first_burn = next((leg for leg in scene.get("sequence") or [] if leg.get("kind") == "burn"), None)
        if first_burn is None or "from" not in first_burn or "to" not in first_burn:
            return fail("burn legs missing from/to conics")
        transfer_layer = next((layer for layer in scene.get("layers") or [] if layer.get("id") == "transfer"), None)
        if transfer_layer is None:
            return fail("viewer missing the transfer ellipse")
        loop = (transfer_layer.get("polylines") or [[]])[0]
        if len(loop) < 300:
            return fail("transfer ellipse is not a full revolution")
        start, end = loop[0], loop[-1]
        if abs(start[0] - end[0]) > 1e-6 or abs(start[1] - end[1]) > 1e-6:
            return fail("transfer ellipse is not closed")
        if abs(float(scene["elev_deg"]) - PNG_ELEV_DEG) > 1e-9:
            return fail("viewer elevation is not orbit-normal")
        if abs(float(scene["azim_deg"]) - PNG_AZIM_DEG) > 1e-9:
            return fail("viewer azimuth is not orbit-normal")
        if len(scene.get("burns") or []) != 2:
            return fail("Hohmann viewer needs two burns")
        html_text = "".join(captured)
        if "viewer:" not in html_text:
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
    print_kv("unit_dv_m_s", outward.dv)
    print_kv("unit_tof_s", outward.tof)
    print_kv("earth_dv_m_s", by_altitude.dv)
    print_kv("earth_tof_s", by_altitude.tof)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hohmann transfer between two circular orbits."
    )
    parser.add_argument("--r1", type=float, default=None, help="departure circular radius from the center [m]")
    parser.add_argument("--r2", type=float, default=None, help="arrival circular radius from the center [m]")
    parser.add_argument(
        "--alt",
        type=float,
        default=None,
        help="geometric altitude of the departure circular orbit [m]",
    )
    parser.add_argument(
        "--ecc",
        type=float,
        default=None,
        help="eccentricity of the transfer ellipse; departure is periapsis",
    )
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"planetary radius [m]; default Earth {R0_EARTH:.8g}",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--html", action="store_true", help="write the optional HTML 3D viewer beside the PNG")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
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
