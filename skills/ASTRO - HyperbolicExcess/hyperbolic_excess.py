#!/usr/bin/env python3
"""Escape from a circular park onto a planet-centered hyperbola.

Hyperbolic excess, C3, axis, eccentricity, periapsis speed, the circular-park
burn, and the asymptote follow hyperbolic_excess_from_axis,
characteristic_energy, semimajor_from_characteristic_energy,
energy_radius_from_excess, hyperbolic_eccentricity_from_periapsis, vis_viva,
circular_orbit_velocity, hyperbola_asymptote_true_anomaly, and
hyperbola_turning_angle in formulas.md.
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

G0 = 9.80665
R0_EARTH = 6.3742e6
PLOT_TITLE = "Hyperbolic excess"
CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent
PNG_ELEV_DEG = 90.0
PNG_AZIM_DEG = -90.0
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
DV_COLOR = "#e67e22"
HYPER_COLOR = "#c0392b"
ASYMPTOTE_COLOR = "#85929e"
BURN_WALL_S = 2.4
PARK_WALL_S = 3.2
COAST_WALL_S = 10.0
_OP = None
ASSUMPTIONS = (
    "impulsive periapsis burn from a circular park onto a planet-centered "
    "hyperbola; spherical inverse-square gravity with no drag, thrust, or "
    "third body on the coast; hyperbolic excess is hyperbolic_excess_from_axis, "
    "C3 is characteristic_energy, the axis is semimajor_from_characteristic_energy, "
    "the energy radius is energy_radius_from_excess, eccentricity is "
    "hyperbolic_eccentricity_from_periapsis, periapsis speed is vis_viva, "
    "circular speed is circular_orbit_velocity, the asymptote true anomaly is "
    "hyperbola_asymptote_true_anomaly, and the turning angle is "
    "hyperbola_turning_angle; mu = g0*R0^2 with g0 = 9.80665 m/s^2; "
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
class Escape:
    mode: str
    rp: float
    vinf: float
    c3: float
    rinf: float
    a: float
    e: float
    p: float
    nu_inf: float
    turn: float
    v_periapsis: float
    v_circular: float
    v_escape: float
    energy: float
    dv: float
    sense: str


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


def vis_viva(mu: float, radius: float, semi_major: float) -> float:
    """vis_viva."""
    argument = mu * (2.0 / radius - 1.0 / semi_major)
    scale = mu / radius
    if argument < 0.0:
        if argument > -1e-9 * scale:
            argument = 0.0
        else:
            raise ValueError("speed is not real at that radius")
    return math.sqrt(argument)


def hyperbolic_excess_from_axis(mu: float, semi_major: float) -> float:
    """hyperbolic_excess_from_axis."""
    if semi_major >= 0.0:
        raise ValueError("hyperbola semi-major axis must be < 0 m")
    return math.sqrt(mu * (-1.0 / semi_major))


def characteristic_energy(vinf: float) -> float:
    """characteristic_energy."""
    return vinf * vinf


def semimajor_from_c3(mu: float, c3: float) -> float:
    """semimajor_from_characteristic_energy."""
    if c3 <= 0.0:
        raise ValueError("characteristic energy must be > 0 m^2/s^2")
    return -mu / c3


def energy_radius_from_excess(mu: float, vinf: float) -> float:
    """energy_radius_from_excess."""
    if vinf <= 0.0:
        raise ValueError("hyperbolic excess speed must be > 0 m/s")
    return mu / (vinf * vinf)


def hyperbolic_eccentricity(rp: float, vinf: float, mu: float) -> float:
    """hyperbolic_eccentricity_from_periapsis."""
    return 1.0 + rp * vinf * vinf / mu


def asymptote_true_anomaly(eccentricity: float) -> float:
    """hyperbola_asymptote_true_anomaly."""
    if eccentricity <= 1.0:
        raise ValueError("hyperbola eccentricity must be > 1")
    return math.acos(-1.0 / eccentricity)


def turning_angle(eccentricity: float) -> float:
    """hyperbola_turning_angle."""
    if eccentricity <= 1.0:
        raise ValueError("hyperbola eccentricity must be > 1")
    return 2.0 * math.asin(1.0 / eccentricity)


def same_radius(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=0.0)


def solve_escape(mu: float, rp: float, vinf: float, mode: str) -> Escape:
    if rp <= 0.0:
        raise ValueError("periapsis radius must be > 0 m")
    if vinf <= 0.0:
        raise ValueError("hyperbolic excess speed must be > 0 m/s")
    c3 = characteristic_energy(vinf)
    semi_major = semimajor_from_c3(mu, c3)
    rinf = energy_radius_from_excess(mu, vinf)
    eccentricity = hyperbolic_eccentricity(rp, vinf, mu)
    parameter = semi_major * (1.0 - eccentricity**2)
    v_periapsis = vis_viva(mu, rp, semi_major)
    v_circular = circular_speed(mu, rp)
    dv = v_periapsis - v_circular
    return Escape(
        mode=mode,
        rp=rp,
        vinf=vinf,
        c3=c3,
        rinf=rinf,
        a=semi_major,
        e=eccentricity,
        p=parameter,
        nu_inf=asymptote_true_anomaly(eccentricity),
        turn=turning_angle(eccentricity),
        v_periapsis=v_periapsis,
        v_circular=v_circular,
        v_escape=escape_speed(mu, rp),
        energy=vinf * vinf / 2.0,
        dv=dv,
        sense="prograde",
    )


def require_outside_body(escape: Escape, body_radius: float) -> None:
    if escape.rp < body_radius and not same_radius(escape.rp, body_radius):
        raise ValueError(
            f"periapsis radius {escape.rp:.8g} m is inside the planetary "
            f"radius {body_radius:.8g} m"
        )


def surface_warning(escape: Escape, body_radius: float) -> str | None:
    if same_radius(escape.rp, body_radius):
        return "the circular park lies on the planetary surface"
    return None


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the hyperbola") from exc
    return plt


def polar_xy(radius_of_angle, angles: list[float]) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for angle in angles:
        radius_km = radius_of_angle(angle) / 1000.0
        xs.append(radius_km * math.cos(angle))
        ys.append(radius_km * math.sin(angle))
    return xs, ys


def km(meters: float) -> float:
    return meters / 1000.0


def apsis_xy_km(radius: float, nu: float) -> tuple[float, float]:
    return km(radius * math.cos(nu)), km(radius * math.sin(nu))


def burn_vector_m_s(delta_v: float) -> tuple[float, float, float]:
    return (0.0, delta_v, 0.0)


def equatorial_circle_km(radius: float, count: int = 361) -> list[list[float]]:
    points: list[list[float]] = []
    for angle in linspace(0.0, 2.0 * math.pi, count):
        points.append([km(radius * math.cos(angle)), km(radius * math.sin(angle)), 0.0])
    return points


def equatorial_arc_km(
    parameter: float, eccentricity: float, nu0: float, nu1: float, count: int = 241
) -> list[list[float]]:
    points: list[list[float]] = []
    for nu in linspace(nu0, nu1, count):
        radius = parameter / (1.0 + eccentricity * math.cos(nu))
        points.append([km(radius * math.cos(nu)), km(radius * math.sin(nu)), 0.0])
    return points


def asymptote_line_km(escape: Escape, sign: float, span_m: float) -> list[list[float]]:
    """Geometric asymptote through the hyperbola centre (focus at the origin)."""
    slope = sign * math.sqrt(escape.e**2 - 1.0)
    x_center = escape.a * escape.e
    x0 = x_center - span_m
    x1 = x_center + span_m
    y0 = slope * (x0 - x_center)
    y1 = slope * (x1 - x_center)
    return [[km(x0), km(y0), 0.0], [km(x1), km(y1), 0.0]]


def coast_leg(
    mu: float,
    semi_major: float,
    eccentricity: float,
    parameter: float,
    nu0: float,
    nu1: float,
    wall_s: float,
    layer: str,
    label: str,
    rp: float,
) -> dict[str, object]:
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
        "rp": rp,
    }


def circular_conic(mu: float, radius: float) -> dict[str, float]:
    return {
        "a": radius,
        "e": 0.0,
        "p": radius,
        "h": math.sqrt(mu * radius),
        "mu": mu,
        "rp": radius,
        "i": 0.0,
        "Omega": 0.0,
        "omega": 0.0,
    }


def hyperbola_conic(mu: float, escape: Escape) -> dict[str, float]:
    return {
        "a": escape.a,
        "e": escape.e,
        "p": escape.p,
        "h": math.sqrt(mu * escape.p),
        "mu": mu,
        "rp": escape.rp,
        "i": 0.0,
        "Omega": 0.0,
        "omega": 0.0,
    }


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


def draw_radius(escape: Escape, nu: float) -> float:
    return escape.p / (1.0 + escape.e * math.cos(nu))


def display_span(body: Body, escape: Escape) -> float:
    sample = 0.72 * escape.nu_inf
    far = draw_radius(escape, sample)
    return max(body.radius, escape.rp, far, 2.4 * escape.rp)


def build_payload(body: Body, escape: Escape) -> dict[str, object]:
    op = op_mod()
    outer = display_span(body, escape)
    scene = planet_backdrop(body, outer)
    palette = dict(op.PALETTE)
    palette["dv"] = DV_COLOR
    palette["hyperbola"] = HYPER_COLOR
    peri_km = [km(escape.rp), 0.0, 0.0]
    nu_draw = 0.92 * escape.nu_inf
    layers = [
        {
            "id": "park",
            "color": palette["orbit"],
            "faded": True,
            "polylines": [equatorial_circle_km(escape.rp)],
        },
        {
            "id": "hyperbola",
            "color": HYPER_COLOR,
            "faded": False,
            "polylines": [equatorial_arc_km(escape.p, escape.e, -nu_draw, nu_draw, 241)],
        },
        {
            "id": "asymptotes",
            "color": ASYMPTOTE_COLOR,
            "faded": True,
            "polylines": [
                asymptote_line_km(escape, 1.0, outer * 1.4),
                asymptote_line_km(escape, -1.0, outer * 1.4),
            ],
        },
    ]
    burns = [{"km": peri_km, "dv_m_s": list(burn_vector_m_s(escape.dv)), "color": DV_COLOR, "label": "periapsis burn"}]
    markers = [
        {"id": "periapsis", "label": "periapsis", "shape": "square", "color": "#27ae60", "km": peri_km},
        {"id": "spacecraft", "label": "spacecraft", "shape": "circle", "color": palette["craft"], "km": peri_km},
    ]
    legend = [
        {"label": "planet", "swatch": "planet", "color": palette["planet"], "edge": palette["planet_edge"]},
        {"label": "circular park", "swatch": "line", "color": palette["orbit"], "edge": None},
        {"label": "hyperbola", "swatch": "line", "color": HYPER_COLOR, "edge": None},
        {"label": "asymptotes", "swatch": "line", "color": ASYMPTOTE_COLOR, "edge": None},
        {"label": "periapsis", "swatch": "square", "color": "#27ae60", "edge": None},
        {"label": "spacecraft", "swatch": "circle", "color": palette["craft"], "edge": None},
        {"label": "delta-v", "swatch": "line", "color": DV_COLOR, "edge": None},
    ]
    park_conic = circular_conic(body.mu, escape.rp)
    hyper_conic = hyperbola_conic(body.mu, escape)
    sequence: list[dict[str, object]] = [
        coast_leg(body.mu, escape.rp, 0.0, escape.rp, -0.55, 0.0, PARK_WALL_S, "park", "circular park", escape.rp),
        {
            "kind": "burn",
            "label": "periapsis burn",
            "layer": "hyperbola",
            "wall_s": BURN_WALL_S,
            "burn": 0,
            "from": park_conic,
            "to": hyper_conic,
            "from_layer": "park",
            "to_layer": "hyperbola",
        },
        coast_leg(
            body.mu,
            escape.a,
            escape.e,
            escape.p,
            0.0,
            0.82 * escape.nu_inf,
            COAST_WALL_S,
            "hyperbola",
            "hyperbola",
            escape.rp,
        ),
    ]
    return {
        "title": PLOT_TITLE,
        "elev_deg": PNG_ELEV_DEG,
        "azim_deg": PNG_AZIM_DEG,
        "roll_deg": op.CAMERA_ROLL_DEG,
        **scene,
        "layers": layers,
        "markers": markers,
        "craft_km": peri_km,
        "burns": burns,
        "legend": legend,
        "palette": palette,
        "sequence": sequence,
    }


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


def plot_escape(path: Path, body: Body, escape: Escape) -> None:
    """Planet, circular park, hyperbola, asymptotes, and the periapsis burn."""
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8.4, 7.2))

    full = linspace(0.0, 2.0 * math.pi, 361)
    earth_x, earth_y = polar_xy(lambda _angle: body.radius, full)
    ax.fill(earth_x, earth_y, color="#d4e6f1", zorder=1)
    ax.plot(earth_x, earth_y, color="#1a5276", linewidth=1.0, zorder=2, label="planet")

    park_x, park_y = polar_xy(lambda _angle: escape.rp, full)
    ax.plot(
        park_x,
        park_y,
        color="#1a5276",
        linestyle="--",
        linewidth=1.3,
        zorder=3,
        label="circular park",
    )

    outer = display_span(body, escape)
    for sign, label in ((1.0, "asymptotes"), (-1.0, None)):
        line = asymptote_line_km(escape, sign, outer * 1.4)
        ax.plot(
            [line[0][0], line[1][0]],
            [line[0][1], line[1][1]],
            color=ASYMPTOTE_COLOR,
            linestyle=":",
            linewidth=1.0,
            zorder=3,
            label=label,
        )

    nu_draw = 0.92 * escape.nu_inf
    branch = linspace(-nu_draw, nu_draw, 241)
    hyper_x, hyper_y = polar_xy(lambda angle: draw_radius(escape, angle), branch)
    ax.plot(hyper_x, hyper_y, color=HYPER_COLOR, linewidth=2.2, zorder=4, label="hyperbola")
    mid = len(hyper_x) // 2
    ahead = min(len(hyper_x) - 1, mid + max(1, len(hyper_x) // 24))
    ax.annotate(
        "",
        xy=(hyper_x[ahead], hyper_y[ahead]),
        xytext=(hyper_x[mid], hyper_y[mid]),
        arrowprops={
            "arrowstyle": "-|>",
            "color": HYPER_COLOR,
            "lw": 1.6,
            "mutation_scale": 14,
        },
        zorder=5,
    )
    ax.plot(
        km(escape.rp),
        0.0,
        "s",
        color="#27ae60",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=6,
        label="periapsis",
    )
    arrow_km = 0.10 * outer / 1000.0
    draw_delta_v(ax, apsis_xy_km(escape.rp, 0.0), burn_vector_m_s(escape.dv), arrow_km, DV_COLOR)

    limit = 1.12 * outer / 1000.0
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_title(PLOT_TITLE)
    altitude_km = (escape.rp - body.radius) / 1000.0
    ax.text(
        0.5,
        1.02,
        f"park altitude {altitude_km:.6g} km,  v_inf {escape.vinf:.6g} m/s",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#34495e",
    )
    ax.text(
        0.02,
        0.98,
        f"delta-v  {escape.dv:.6g} m/s\nC3  {escape.c3:.6g} m^2/s^2",
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
        raise ValueError(f"could not write the PNG: {exc}") from exc
    finally:
        plt.close(fig)


def print_report(body: Body, escape: Escape, path: Path, viewer: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", escape.mode)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("rp_m", escape.rp)
    print_kv("h_park_m", escape.rp - body.radius)
    print_kv("vinf_m_s", escape.vinf)
    print_kv("C3_m2_s2", escape.c3)
    print_kv("rinf_m", escape.rinf)
    print_kv("a_m", escape.a)
    print_kv("e", escape.e)
    print_kv("p_m", escape.p)
    print_kv("v_periapsis_m_s", escape.v_periapsis)
    print_kv("v_circular_m_s", escape.v_circular)
    print_kv("v_escape_m_s", escape.v_escape)
    print_kv("energy_J_kg", escape.energy)
    print_kv("dv_m_s", escape.dv)
    print_kv("dv_sense", escape.sense)
    print_kv("turn_rad", escape.turn)
    print_kv("nu_inf_rad", escape.nu_inf)
    warning = surface_warning(escape, body.radius)
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


def resolve_energy(ns: argparse.Namespace, mu: float) -> tuple[str, float]:
    chosen = [(name, getattr(ns, name)) for name in ("vinf", "C3", "rinf") if getattr(ns, name) is not None]
    if len(chosen) != 1:
        raise ValueError("pass exactly one of --vinf, --C3, or --rinf")
    name, value = chosen[0]
    require_finite(value, f"--{name}")
    if name == "vinf":
        if value <= 0.0:
            raise ValueError("--vinf must be > 0 m/s")
        return "vinf", value
    if name == "C3":
        if value <= 0.0:
            raise ValueError("--C3 must be > 0 m^2/s^2")
        return "C3", math.sqrt(value)
    if value <= 0.0:
        raise ValueError("--rinf must be > 0 m")
    return "rinf", math.sqrt(mu / value)


def resolve_periapsis(ns: argparse.Namespace) -> float:
    if ns.rp is None:
        raise ValueError("--rp is required")
    require_finite(ns.rp, "--rp")
    if ns.rp <= 0.0:
        raise ValueError("--rp must be > 0 m")
    return ns.rp


def run(ns: argparse.Namespace) -> int:
    body = resolve_body(ns.R0)
    rp = resolve_periapsis(ns)
    mode, vinf = resolve_energy(ns, body.mu)
    escape = solve_escape(body.mu, rp, vinf, mode)
    require_outside_body(escape, body.radius)
    out_path = Path(ns.out) if ns.out else SKILL_DIR / "hyperbolic_excess.png"
    out_path = out_path.resolve()
    plot_escape(out_path, body, escape)
    viewer_path = out_path.with_suffix(".html")
    wrote_html = bool(ns.html or ns.open)
    if wrote_html:
        write_viewer_html(SKILL_DIR, viewer_path, build_payload(body, escape), PLOT_TITLE)
    print_report(body, escape, out_path, viewer_path if wrote_html else None)
    if ns.open:
        webbrowser.open(viewer_path.as_uri())
    return 0


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    body = resolve_body(None)
    if body.radius_source != "default" or body.radius != R0_EARTH:
        return fail("Earth radius default")
    if not close_enough(body.mu, G0 * R0_EARTH**2, body.mu):
        return fail("mu is not g0*R0^2")

    mu = 1.0
    rp = 1.0
    vinf = 1.0
    unit = solve_escape(mu, rp, vinf, "vinf")
    if not close_enough(unit.a, -1.0, 1.0):
        return fail("semi-major axis")
    if not close_enough(unit.e, 2.0, 1.0):
        return fail("eccentricity")
    if not close_enough(unit.c3, 1.0, 1.0):
        return fail("C3")
    if not close_enough(unit.rinf, 1.0, 1.0):
        return fail("energy radius")
    if not close_enough(unit.v_circular, 1.0, 1.0):
        return fail("circular speed")
    if not close_enough(unit.v_periapsis, math.sqrt(3.0), 1.0):
        return fail("periapsis speed")
    if not close_enough(unit.dv, math.sqrt(3.0) - 1.0, 1.0):
        return fail("periapsis burn")
    if not close_enough(unit.nu_inf, 2.0 * math.pi / 3.0, 1.0):
        return fail("asymptote true anomaly")
    if not close_enough(unit.turn, math.pi / 3.0, 1.0):
        return fail("turning angle")
    if not close_enough(unit.energy, 0.5, 1.0):
        return fail("specific energy")
    if not close_enough(unit.v_periapsis**2, unit.vinf**2 + 2.0 * mu / rp, 1.0):
        return fail("vis-viva split of excess and escape")
    if not close_enough(2.0 * unit.nu_inf - math.pi, unit.turn, 1.0):
        return fail("turning angle is not 2*nu_inf - pi")
    if abs(unit.p - unit.a * (1.0 - unit.e**2)) > CHECK_TOL:
        return fail("semi-latus rectum")
    if not close_enough(unit.rp, unit.a * (1.0 - unit.e), 1.0):
        return fail("periapsis radius identity")

    by_c3 = solve_escape(mu, rp, math.sqrt(unit.c3), "C3")
    by_rinf = solve_escape(mu, rp, math.sqrt(mu / unit.rinf), "rinf")
    if not close_enough(by_c3.dv, unit.dv, 1.0) or not close_enough(by_rinf.a, unit.a, 1.0):
        return fail("C3 and rinf modes")

    try:
        solve_escape(mu, rp, 0.0, "vinf")
    except ValueError:
        pass
    else:
        return fail("zero excess speed was accepted")
    try:
        require_outside_body(solve_escape(mu, 0.5, vinf, "vinf"), 1.0)
    except ValueError:
        pass
    else:
        return fail("a periapsis inside the planet was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "escape.png")
        captured: list[str] = []

        class _Capture:
            def write(self, text: str) -> None:
                captured.append(text)

            def flush(self) -> None:
                return None

        old_out = sys.stdout
        sys.stdout = _Capture()
        try:
            code = main(["--rp", "6774200", "--vinf", "3200", "--out", out])
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"main returned {code}")
        if not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        text = "".join(captured)
        for key in (
            "mode: vinf",
            "vinf_m_s:",
            "C3_m2_s2:",
            "a_m:",
            "e:",
            "v_periapsis_m_s:",
            "v_circular_m_s:",
            "dv_m_s:",
            "turn_rad:",
            "nu_inf_rad:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "viewer:" in text:
            return fail("HTML viewer was written without --html")

        html_out = str(Path(tmp) / "escape_html.png")
        captured.clear()
        sys.stdout = _Capture()
        try:
            html_code = main(["--rp", "1", "--C3", "1", "--R0", "0.5", "--out", html_out, "--html"])
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
        if "periapsis burn" not in html or "sequence" not in html:
            return fail("HTML missing the burn")
        if "function lerpEscape" not in html:
            return fail("viewer missing the circular-to-hyperbola morph")
        scene = scene_from_html(html)
        first_burn = next((leg for leg in scene.get("sequence") or [] if leg.get("kind") == "burn"), None)
        if first_burn is None or "from" not in first_burn or "to" not in first_burn:
            return fail("burn legs missing from/to conics")
        html_mu = G0 * 0.5**2
        expected_e = 1.0 + 1.0 / html_mu
        if abs(float(first_burn["to"]["e"]) - expected_e) > 1e-9:
            return fail("viewer hyperbola eccentricity")
        hyper_layer = next((layer for layer in scene.get("layers") or [] if layer.get("id") == "hyperbola"), None)
        if hyper_layer is None:
            return fail("viewer missing the hyperbola")
        if abs(float(scene["elev_deg"]) - PNG_ELEV_DEG) > 1e-9:
            return fail("viewer elevation is not orbit-normal")
        if len(scene.get("burns") or []) != 1:
            return fail("viewer needs one periapsis burn")
        if "viewer:" not in "".join(captured):
            return fail("stdout missing viewer")

        captured.clear()
        sys.stdout = _Capture()
        try:
            rinf_code = main(["--rp", "1", "--rinf", "1", "--R0", "0.5", "--out", str(Path(tmp) / "rinf.png")])
        finally:
            sys.stdout = old_out
        if rinf_code != 0:
            return fail(f"rinf main returned {rinf_code}")
        if "mode: rinf" not in "".join(captured):
            return fail("rinf mode was not printed")

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
    print_kv("unit_dv_m_s", unit.dv)
    print_kv("unit_e", unit.e)
    print_kv("unit_turn_rad", unit.turn)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Escape from a circular park onto a planet-centered hyperbola."
    )
    parser.add_argument("--rp", type=float, default=None, help="periapsis / circular-park radius from the center [m]")
    parser.add_argument("--vinf", type=float, default=None, help="hyperbolic excess speed [m/s]")
    parser.add_argument("--C3", type=float, default=None, help="characteristic energy v_inf^2 [m^2/s^2]")
    parser.add_argument(
        "--rinf",
        type=float,
        default=None,
        help="energy radius |a| = mu/v_inf^2 implied by the excess speed [m]",
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
