#!/usr/bin/env python3
"""Impulsive pure inclination change at a node of one Keplerian conic.

Orbit geometry, vis-viva speed, and the inertial frame come from
ASTRO - OrbitalParameters. The impulse is plane_change_impulse.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "ASTRO - PlaneChangeImpulse"
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
HINGE_WALL_S = 3.5
INITIAL_REVS = 1
FINAL_REVS = 4
SLOW_REVS = 0.4
INITIAL_ORBIT_COLOR = "#1f6feb"
FINAL_ORBIT_COLOR = "#9b59b6"
DV_COLOR = "#e67e22"
NODE_LINE_COLOR = "#b7950b"
DN_COLOR = "#6c3483"
_OP = None

ASSUMPTIONS = (
    "spherical inverse-square two-body gravity; planetary flattening is visual "
    "only and does not enter mu; mu = g0*R0^2 with g0 = 9.80665 m/s^2; "
    "Earth default R0 = 6374200 m and visual flattening 1/298.257; "
    "pure inclination change at a node with the same a, e, Omega, and omega; "
    "ascending-node true anomaly is -omega and descending-node true anomaly is "
    "pi - omega; radius is conic_radius; speed is vis_viva; impulse is "
    "plane_change_impulse, an impulsive equal-speed turn; no combined plane "
    "and radius change; no drag, coast thrust, or third body; a NORAD two-line "
    "element set may be passed with --tle and is used as a Keplerian conic: "
    "line-2 angles are degrees, semi-major axis is the inverse of mean_motion "
    "from the published mean motion in revolutions per 86400 s and this mu, and "
    "BSTAR, mean-motion derivatives, SGP4, and the epoch do not change the state"
)


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


def km(meters: float) -> float:
    return meters / 1000.0


def plane_change_impulse(speed: float, di: float) -> float:
    """plane_change_impulse. di is the inclination change in radians."""
    return 2.0 * speed * math.sin(di / 2.0)


def conic_radius(semi_major: float, eccentricity: float, nu: float) -> float:
    """conic_radius."""
    return semi_major * (1.0 - eccentricity**2) / (1.0 + eccentricity * math.cos(nu))


def orbital_speed(mu: float, radius: float, semi_major: float | None) -> float:
    """vis_viva. A parabola uses the 1/a = 0 limit."""
    if semi_major is None:
        return math.sqrt(mu * 2.0 / radius)
    return op_mod().vis_viva(mu, radius, semi_major)


def line_of_nodes(orbit: object) -> tuple[float, float, float]:
    """Unit vector from the centre toward the ascending node."""
    axis = (math.cos(orbit.Omega), math.sin(orbit.Omega), 0.0)
    scale = math.hypot(axis[0], axis[1])
    if scale == 0.0:
        return (1.0, 0.0, 0.0)
    return (axis[0] / scale, axis[1] / scale, 0.0)


def rotate_velocity(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
    di: float,
) -> tuple[float, float, float]:
    """Rotate v about the outward radius. At the ascending node this raises inclination."""
    mag = math.sqrt(position[0] ** 2 + position[1] ** 2 + position[2] ** 2)
    axis = (position[0] / mag, position[1] / mag, position[2] / mag)
    return op_mod()._rotate_about(velocity, axis, di)


def rotate_about_nodes(
    orbit: object, velocity: tuple[float, float, float], di: float
) -> tuple[float, float, float]:
    """Hinge v about the ascending-node direction. Positive di increases inclination.

    At the descending node the outward radius points the other way, so the
    shared hinge is the line of nodes rather than that outward radius.
    """
    return op_mod()._rotate_about(velocity, line_of_nodes(orbit), di)


@dataclass(frozen=True)
class NodeBurn:
    kind: str
    nu: float
    on_branch: bool
    radius: float | None
    speed: float | None
    dv: float | None
    position_m: tuple[float, float, float] | None
    velocity_m_s: tuple[float, float, float] | None
    dv_m_s: tuple[float, float, float] | None


def nu_on_branch(orbit: object, nu: float, span_m: float) -> bool:
    """True when this true anomaly lies on the drawn conic branch."""
    op = op_mod()
    nu = op.wrap_pi(nu)
    if orbit.conic == "ellipse":
        return True
    samples = op.sample_true_anomalies(orbit, span_m)
    if nu < samples[0] - 1e-8 or nu > samples[-1] + 1e-8:
        return False
    return 1.0 + orbit.e * math.cos(nu) > 1e-8


def radius_at(orbit: object, nu: float) -> float:
    if orbit.a is None:
        return op_mod().conic_radius_from_parameter(orbit.p, orbit.e, nu)
    return conic_radius(orbit.a, orbit.e, nu)


def evaluate_node(body: object, orbit: object, kind: str, di: float, span_m: float) -> NodeBurn:
    op = op_mod()
    nu = op.wrap_pi(-orbit.omega if kind == "an" else math.pi - orbit.omega)
    if not nu_on_branch(orbit, nu, span_m):
        return NodeBurn(kind, nu, False, None, None, None, None, None, None)
    radius = radius_at(orbit, nu)
    if radius <= 0.0 or not math.isfinite(radius):
        return NodeBurn(kind, nu, False, None, None, None, None, None, None)
    speed = orbital_speed(body.mu, radius, orbit.a)
    impulse = plane_change_impulse(speed, di)
    x, y, z, _radius = op.position_at_true(orbit, nu)
    vx, vy, vz = op.velocity_at_true(orbit, nu)
    rotated = rotate_about_nodes(orbit, (vx, vy, vz), di)
    delta = (rotated[0] - vx, rotated[1] - vy, rotated[2] - vz)
    return NodeBurn(
        kind,
        nu,
        True,
        radius,
        speed,
        impulse,
        (x, y, z),
        (vx, vy, vz),
        delta,
    )


def choose_burn(ascending: NodeBurn, descending: NodeBurn, requested: str | None) -> NodeBurn:
    available = [node for node in (ascending, descending) if node.on_branch]
    if not available:
        raise ValueError("neither node lies on the drawn branch")
    if requested is None:
        return min(available, key=lambda node: (node.speed, 0 if node.kind == "an" else 1))
    chosen = ascending if requested == "an" else descending
    if not chosen.on_branch:
        raise ValueError(f"the {requested} node is not on the drawn branch")
    return chosen


def final_orbit(body: object, initial: object, burn: NodeBurn, i_final: float):
    """Same conic, new inclination, state taken at the burn node."""
    op = op_mod()
    if initial.a is None:
        rotated = rotate_about_nodes(initial, burn.velocity_m_s, i_final - initial.i)
        return op.orbit_from_state(
            body.mu,
            burn.position_m[0],
            burn.position_m[1],
            burn.position_m[2],
            rotated[0],
            rotated[1],
            rotated[2],
            initial.mode,
        )
    return op.orbit_from_elements(
        body.mu,
        initial.a,
        initial.e,
        i_final,
        initial.Omega,
        initial.omega,
        burn.nu,
        None,
        initial.mode,
    )


def orbit_polylines(orbit: object, span_m: float) -> list[list[list[float]]]:
    op = op_mod()
    polylines: list[list[list[float]]] = []
    current: list[list[float]] = []
    for nu in op.sample_true_anomalies(orbit, span_m):
        px, py, pz, radius = op.position_at_true(orbit, nu)
        if radius > span_m * 1.02 or not math.isfinite(radius):
            if len(current) > 1:
                polylines.append(current)
            current = []
            continue
        current.append([km(px), km(py), km(pz)])
    if len(current) > 1:
        polylines.append(current)
    return polylines


def nu_limits(orbit: object, span_m: float) -> tuple[float, float]:
    samples = op_mod().sample_true_anomalies(orbit, span_m)
    return samples[0], samples[-1]


def inclined(angle: float) -> bool:
    op = op_mod()
    return op.WEDGE_INCLINATION < angle < math.pi - op.WEDGE_INCLINATION


def wedge_point_m(orbit: object, fallback_radius: float) -> tuple[float, float, float]:
    """Radius at argument of latitude pi/2, so the inclination sector has area at a node."""
    op = op_mod()
    nu = op.wrap_pi(math.pi / 2.0 - orbit.omega)
    radius = fallback_radius
    denom = 1.0 + orbit.e * math.cos(nu)
    if denom > 1e-8:
        if orbit.a is not None:
            trial = conic_radius(orbit.a, orbit.e, nu)
        else:
            trial = orbit.p / denom
        if trial > 0.0 and math.isfinite(trial):
            radius = trial
    argument = math.pi / 2.0
    return (
        op.inertial_position_x(radius, orbit.Omega, argument, orbit.i),
        op.inertial_position_y(radius, orbit.Omega, argument, orbit.i),
        op.inertial_position_z(radius, orbit.i, argument),
    )


def backdrop(body: object, span_m: float) -> dict[str, object]:
    op = op_mod()
    limit_m = op.LIMIT_SPAN_FRAC * span_m
    axis_len = min(max(1.35 * body.radius, 0.42 * span_m), 0.72 * span_m)
    ring_r = min(1.22 * body.radius, 0.98 * span_m)
    polar_m = body.radius * (1.0 - body.flattening)
    ring_angles = op.linspace(0.0, 2.0 * math.pi, 181)
    ring = [[km(ring_r * math.cos(angle)), km(ring_r * math.sin(angle)), 0.0] for angle in ring_angles]
    equator = [
        [km(body.radius * math.cos(angle)), km(body.radius * math.sin(angle)), 0.0]
        for angle in ring_angles
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
    axes = []
    for label, tip_m in (
        ("+X", (axis_len, 0.0, 0.0)),
        ("+Y", (0.0, axis_len, 0.0)),
        ("+Z", (0.0, 0.0, axis_len)),
    ):
        tip = [km(tip_m[0]), km(tip_m[1]), km(tip_m[2])]
        axes.append(
            {
                "label": label,
                "tip_km": tip,
                "label_km": [tip[0] * 1.06, tip[1] * 1.06, tip[2] * 1.06],
            }
        )
    return {
        "limit_km": km(limit_m),
        "axis_length_km": km(axis_len),
        "equatorial_radius_km": km(body.radius),
        "polar_radius_km": km(polar_m),
        "ring_km": ring,
        "spokes_km": spokes,
        "equator_km": equator,
        "axes": axes,
    }


def kepler_dict(orbit: object, mu: float, nu_min: float, nu_max: float) -> dict[str, object]:
    op = op_mod()
    return {
        "conic": orbit.conic,
        "mu": mu,
        "a": orbit.a,
        "e": orbit.e,
        "i": orbit.i,
        "Omega": orbit.Omega,
        "omega": orbit.omega,
        "nu": orbit.nu,
        "M": orbit.M,
        "p": orbit.p,
        "h": orbit.h,
        "period": orbit.period,
        "nu_min": nu_min,
        "nu_max": nu_max,
        "ellipse_wall_s": op.ELLIPSE_WALL_S,
        "open_arc_wall_s": op.OPEN_ARC_WALL_S,
    }


def build_payload(
    body: object,
    initial: object,
    final: object,
    ascending: NodeBurn,
    descending: NodeBurn,
    burn: NodeBurn,
    di: float,
    i_final: float,
    elev: float,
    azim: float,
    span_m: float,
) -> dict[str, object]:
    op = op_mod()
    scene = backdrop(body, span_m)
    initial_nu = nu_limits(initial, span_m)
    final_nu = nu_limits(final, span_m)
    craft = [km(burn.position_m[0]), km(burn.position_m[1]), km(burn.position_m[2])]
    wedge_m = wedge_point_m(initial, burn.radius)
    wedge = op.inclination_sector((km(wedge_m[0]), km(wedge_m[1]), km(wedge_m[2])), initial.Omega)
    show_wedge = inclined(initial.i) or inclined(i_final)
    palette = dict(op.PALETTE)
    palette["orbit"] = INITIAL_ORBIT_COLOR
    palette["final_orbit"] = FINAL_ORBIT_COLOR
    palette["dv"] = DV_COLOR
    palette["nodes"] = NODE_LINE_COLOR
    palette["descending_node"] = DN_COLOR

    markers: list[dict[str, object]] = []
    legend: list[dict[str, object]] = [
        {"label": "planet", "swatch": "planet", "color": palette["planet"], "edge": palette["planet_edge"]},
        {"label": "equatorial plane", "swatch": "line", "color": palette["equator"], "edge": None},
        {"label": "initial orbit", "swatch": "line", "color": palette["orbit"], "edge": None},
        {"label": "final orbit", "swatch": "line", "color": palette["final_orbit"], "edge": None},
    ]
    nodes_km: list[list[float]] = []
    if ascending.on_branch and descending.on_branch:
        nodes_km = [
            [km(ascending.position_m[0]), km(ascending.position_m[1]), km(ascending.position_m[2])],
            [km(descending.position_m[0]), km(descending.position_m[1]), km(descending.position_m[2])],
        ]
        legend.append({"label": "line of nodes", "swatch": "line", "color": palette["nodes"], "edge": None})
    elif burn.on_branch:
        place = burn.position_m
        nodes_km = [
            [km(place[0]), km(place[1]), km(place[2])],
            [km(-place[0]), km(-place[1]), km(-place[2])],
        ]
        legend.append({"label": "line of nodes", "swatch": "line", "color": palette["nodes"], "edge": None})
    if ascending.on_branch:
        markers.append(
            {
                "id": "ascending_node",
                "label": "ascending node",
                "shape": "circle",
                "color": palette["node"],
                "km": [km(ascending.position_m[0]), km(ascending.position_m[1]), km(ascending.position_m[2])],
            }
        )
        legend.append({"label": "ascending node", "swatch": "circle", "color": palette["node"], "edge": None})
    if descending.on_branch:
        markers.append(
            {
                "id": "descending_node",
                "label": "descending node",
                "shape": "square",
                "color": palette["descending_node"],
                "km": [
                    km(descending.position_m[0]),
                    km(descending.position_m[1]),
                    km(descending.position_m[2]),
                ],
            }
        )
        legend.append(
            {"label": "descending node", "swatch": "square", "color": palette["descending_node"], "edge": None}
        )
    if show_wedge and len(wedge) >= 3:
        legend.append(
            {"label": "inclination", "swatch": "wedge", "color": palette["wedge"], "edge": palette["wedge_edge"]}
        )
    peri = op.position_at_true(initial, 0.0)
    if nu_on_branch(initial, 0.0, span_m) and math.isfinite(peri[3]) and peri[3] <= span_m * 1.02:
        markers.append(
            {
                "id": "periapsis",
                "label": "periapsis",
                "shape": "circle",
                "color": palette["periapsis"],
                "km": [km(peri[0]), km(peri[1]), km(peri[2])],
            }
        )
        legend.append({"label": "periapsis", "swatch": "circle", "color": palette["periapsis"], "edge": None})
    if initial.ra is not None:
        apo = op.position_at_true(initial, math.pi)
        markers.append(
            {
                "id": "apoapsis",
                "label": "apoapsis",
                "shape": "square",
                "color": palette["apoapsis"],
                "km": [km(apo[0]), km(apo[1]), km(apo[2])],
            }
        )
        legend.append({"label": "apoapsis", "swatch": "square", "color": palette["apoapsis"], "edge": None})
    markers.append(
        {
            "id": "spacecraft",
            "label": "spacecraft",
            "shape": "circle",
            "color": palette["craft"],
            "km": craft,
        }
    )
    legend.append({"label": "spacecraft", "swatch": "circle", "color": palette["craft"], "edge": None})
    legend.append({"label": "plane change", "swatch": "line", "color": palette["dv"], "edge": None})

    coast = kepler_dict(final, body.mu, final_nu[0], final_nu[1])
    payload = {
        "title": PLOT_TITLE,
        "elev_deg": elev,
        "azim_deg": azim,
        "roll_deg": op.CAMERA_ROLL_DEG,
        "limit_km": scene["limit_km"],
        "axis_length_km": scene["axis_length_km"],
        "equatorial_radius_km": scene["equatorial_radius_km"],
        "polar_radius_km": scene["polar_radius_km"],
        "flattening": body.flattening,
        "planet_segments_u": op.PLANET_SEGMENTS_U,
        "planet_segments_v": op.PLANET_SEGMENTS_V,
        "planet_opacity": 0.52,
        "show_wedge": show_wedge and len(wedge) >= 3,
        "wedge_km": [[point[0], point[1], point[2]] for point in wedge],
        "wedge_length_km": math.sqrt(craft[0] ** 2 + craft[1] ** 2 + craft[2] ** 2),
        "wedge_steps": op.WEDGE_STEPS,
        "ring_km": scene["ring_km"],
        "spokes_km": scene["spokes_km"],
        "equator_km": scene["equator_km"],
        "axes": scene["axes"],
        "initial_orbit_km": orbit_polylines(initial, span_m),
        "final_orbit_km": orbit_polylines(final, span_m),
        "nodes_km": nodes_km,
        "markers": markers,
        "craft_km": craft,
        "dv_m_s": [burn.dv_m_s[0], burn.dv_m_s[1], burn.dv_m_s[2]],
        "dv_length_km": km(op.ARROW_SPAN_FRAC * span_m),
        "velocity_length_km": km(op.ARROW_SPAN_FRAC * span_m),
        "legend": legend,
        "palette": palette,
        "kepler": coast,
        "kepler_initial": kepler_dict(initial, body.mu, initial_nu[0], initial_nu[1]),
        "kepler_final": coast,
        "hinge": {
            "wall_s": HINGE_WALL_S if abs(di) > 1e-8 else 0.0,
            "i0": initial.i,
            "i1": i_final,
            "Omega": initial.Omega,
            "omega": initial.omega,
            "p": initial.p,
            "e": initial.e,
            "h": initial.h,
            "mu": body.mu,
            "a": initial.a,
            "conic": initial.conic,
            "period": initial.period,
            "nu_min": initial_nu[0],
            "nu_max": initial_nu[1],
            "burn_radius_m": burn.radius,
            "burn_nu": burn.nu,
            "burn_M": coast["M"],
            "ellipse_wall_s": op.ELLIPSE_WALL_S,
            "open_arc_wall_s": op.OPEN_ARC_WALL_S,
            "initial_revs": INITIAL_REVS,
            "final_revs": FINAL_REVS,
            "slow_revs": min(SLOW_REVS, INITIAL_REVS, FINAL_REVS),
        },
    }
    return payload


def _draw_polylines(
    ax: object,
    polylines: list,
    color: str,
    outward: tuple[float, float, float],
    radius_km: float,
    near_width: float,
    far_width: float,
    alpha: float = 1.0,
) -> None:
    op = op_mod()
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        hidden = [
            op.behind_planet(x, y, z, outward[0], outward[1], outward[2], radius_km)
            for x, y, z in polyline
        ]
        near_strokes, far_strokes = op.split_orbit_strokes(polyline, hidden)
        for stroke in far_strokes:
            xs, ys, zs = zip(*stroke)
            ax.plot(
                xs,
                ys,
                zs,
                color=color,
                linewidth=far_width,
                linestyle=(0, (1.8, 1.9)),
                alpha=alpha * 0.65,
                zorder=6,
                solid_capstyle="round",
            )
        for stroke in near_strokes:
            xs, ys, zs = zip(*stroke)
            ax.plot(
                xs,
                ys,
                zs,
                color=color,
                linewidth=near_width,
                alpha=alpha,
                zorder=8,
                solid_capstyle="round",
            )


def plot_png(path: Path, payload: dict[str, object], body: object, initial: object) -> None:
    """Still of both planes, the line of nodes, and the burn arrow."""
    op = op_mod()
    plt = op.ensure_matplotlib()
    from matplotlib.ticker import MaxNLocator
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    palette = payload["palette"]
    planet_scene = op.build_scene(body, initial, payload["elev_deg"], payload["azim_deg"])
    fig = plt.figure(figsize=(10.2, 7.9), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    try:
        ax.set_proj_type("ortho")
    except AttributeError:
        pass
    ax.computed_zorder = False

    ring = payload["ring_km"]
    if len(ring) > 1:
        xs, ys, zs = zip(*ring)
        ax.plot(xs, ys, zs, color=palette["equator"], linewidth=1.25, zorder=1, solid_capstyle="round")
    for spoke in payload["spokes_km"]:
        xs, ys, zs = zip(*spoke)
        ax.plot(xs, ys, zs, color=palette["equator_spoke"], linewidth=0.9, zorder=1)

    xs, ys, zs, rgba = op._planet_arrays(planet_scene)
    surface = ax.plot_surface(
        xs,
        ys,
        zs,
        facecolors=rgba,
        shade=False,
        linewidth=0,
        antialiased=False,
        rstride=1,
        cstride=1,
        zorder=3,
    )
    surface.set_zorder(3)
    surface.set_linewidth(0.0)
    surface.set_edgecolor((0.0, 0.0, 0.0, 0.0))
    equator = payload["equator_km"]
    if len(equator) > 1:
        ex, ey, ez = zip(*equator)
        ax.plot(ex, ey, ez, color=palette["equator_limb"], linewidth=0.95, zorder=4)

    for axis in payload["axes"]:
        tip = axis["tip_km"]
        label_at = axis["label_km"]
        ax.plot(
            [0.0, tip[0]],
            [0.0, tip[1]],
            [0.0, tip[2]],
            color=palette["axis"],
            linewidth=1.2,
            zorder=4,
            solid_capstyle="round",
        )
        ax.text(label_at[0], label_at[1], label_at[2], axis["label"], color=palette["axis"], fontsize=9)

    _right, _up, outward = op.view_basis(payload["elev_deg"], payload["azim_deg"], payload["roll_deg"])
    radius_km = payload["equatorial_radius_km"]
    _draw_polylines(
        ax, payload["final_orbit_km"], palette["final_orbit"], outward, radius_km, 2.2, 1.3, alpha=0.38
    )
    _draw_polylines(ax, payload["initial_orbit_km"], palette["orbit"], outward, radius_km, 2.8, 1.65)
    if len(payload["nodes_km"]) > 1:
        _draw_polylines(ax, [payload["nodes_km"]], palette["nodes"], outward, radius_km, 1.5, 1.1)

    wedge = payload["wedge_km"]
    if payload["show_wedge"] and len(wedge) >= 3 and any(abs(point[2]) > 1e-3 for point in wedge):
        patch = Poly3DCollection(
            [list(map(tuple, wedge))],
            alpha=0.72,
            facecolor=palette["wedge"],
            edgecolor=palette["wedge_edge"],
            linewidths=1.1,
        )
        patch.set_zorder(9)
        ax.add_collection3d(patch)

    craft = payload["craft_km"]
    ax.plot(
        [0.0, craft[0]],
        [0.0, craft[1]],
        [0.0, craft[2]],
        color=palette["radius"],
        linewidth=1.15,
        zorder=5,
        solid_capstyle="round",
    )
    dv = payload["dv_m_s"]
    dv_norm = math.sqrt(dv[0] ** 2 + dv[1] ** 2 + dv[2] ** 2)
    if dv_norm > 0.0:
        length = payload["dv_length_km"] * 1.6
        tip = (
            craft[0] + dv[0] / dv_norm * length,
            craft[1] + dv[1] / dv_norm * length,
            craft[2] + dv[2] / dv_norm * length,
        )
        ax.plot(
            [craft[0], tip[0]],
            [craft[1], tip[1]],
            [craft[2], tip[2]],
            color=palette["dv"],
            linewidth=2.6,
            zorder=12,
            solid_capstyle="round",
        )
        ax.quiver(
            craft[0],
            craft[1],
            craft[2],
            dv[0],
            dv[1],
            dv[2],
            length=length,
            normalize=True,
            color=palette["dv"],
            arrow_length_ratio=0.22,
            linewidth=2.2,
            zorder=13,
        )

    sizes = {
        "ascending_node": 96,
        "descending_node": 84,
        "periapsis": 74,
        "apoapsis": 80,
        "spacecraft": 88,
    }
    for marker in payload["markers"]:
        if marker["id"] == "spacecraft":
            continue
        ax.scatter(
            [marker["km"][0]],
            [marker["km"][1]],
            [marker["km"][2]],
            color=marker["color"],
            s=sizes.get(marker["id"], 72),
            marker="s" if marker["shape"] == "square" else "o",
            depthshade=False,
            edgecolors="white",
            linewidths=1.15,
            zorder=9,
        )
    craft_marker = next(marker for marker in payload["markers"] if marker["id"] == "spacecraft")
    ax.scatter(
        [craft_marker["km"][0]],
        [craft_marker["km"][1]],
        [craft_marker["km"][2]],
        color=craft_marker["color"],
        s=sizes["spacecraft"],
        marker="o",
        depthshade=False,
        edgecolors="white",
        linewidths=1.2,
        zorder=10,
    )

    limit = payload["limit_km"]
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    try:
        ax.set_box_aspect((1.0, 1.0, 1.0), zoom=1.38)
    except TypeError:
        try:
            ax.set_box_aspect((1.0, 1.0, 1.0))
        except AttributeError:
            pass
    except AttributeError:
        pass
    ax.set_xlabel("X (km)", labelpad=7, fontsize=10, color=palette["text"])
    ax.set_ylabel("Y (km)", labelpad=7, fontsize=10, color=palette["text"])
    ax.set_zlabel("Z (km)", labelpad=6, fontsize=10, color=palette["text"])
    ax.set_title(PLOT_TITLE, pad=8, fontsize=15, color=palette["text"])
    ax.tick_params(labelsize=8, pad=1, colors="#5d6d7e")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.zaxis.set_major_locator(MaxNLocator(nbins=4))
    op.apply_matplotlib_view(ax, payload["elev_deg"], payload["azim_deg"], payload["roll_deg"])
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor(palette["pane"])
        axis.pane.set_edgecolor("#d5d8dc")
        axis.pane.set_alpha(0.55)
    ax.grid(False)
    ax.text2D(
        0.0,
        -0.02,
        f"elev {payload['elev_deg']:.4g}°    azim {payload['azim_deg']:.4g}°",
        transform=ax.transAxes,
        fontsize=9,
        color=palette["caption"],
    )
    handles = []
    for entry in payload["legend"]:
        handles.append(
            op._legend_handle(
                op.LegendEntry(entry["label"], entry["swatch"], entry["color"], entry["edge"])
            )
        )
    legend = ax.legend(
        handles=handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8.5,
        framealpha=0.96,
        borderaxespad=0.2,
        handlelength=1.6,
        labelspacing=0.45,
    )
    frame = legend.get_frame()
    frame.set_facecolor("white")
    frame.set_edgecolor("#d5d8dc")
    frame.set_linewidth(0.6)
    fig.subplots_adjust(left=0.0, right=0.78, bottom=0.04, top=0.94)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=170, bbox_inches="tight", pad_inches=0.22, facecolor="white")
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def write_viewer_html(path: Path, payload: dict[str, object]) -> None:
    viewer_dir = SKILL_DIR / "viewer"
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
    before = before.replace("__TITLE__", PLOT_TITLE).replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
    after = (
        after.replace("__TITLE__", PLOT_TITLE)
        .replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
        .replace("__SCENE_JSON__", encoded)
    )
    html = before + three_source + after
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not write the viewer: {exc}") from exc


def _none_or_float(value: float | None) -> object:
    return "none" if value is None else value


def print_report(
    body: object,
    initial: object,
    ascending: NodeBurn,
    descending: NodeBurn,
    burn: NodeBurn,
    di: float,
    i_final: float,
    elev: float,
    azim: float,
    path: Path,
    viewer: Path,
) -> None:
    op = op_mod()
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", initial.mode)
    if getattr(initial, "tle", None) is not None:
        op.print_tle(initial.tle)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("flattening", body.flattening)
    print_kv("conic", initial.conic)
    if initial.a is None:
        print_kv("a", "none")
    else:
        print_kv("a_m", initial.a)
    print_kv("e", initial.e)
    print_kv("i_rad", initial.i)
    print_kv("Omega_rad", initial.Omega)
    print_kv("omega_rad", initial.omega)
    print_kv("nu_rad", initial.nu)
    if initial.M is None:
        print_kv("M", "none")
    else:
        print_kv("M_rad", initial.M)
    print_kv("p_m", initial.p)
    print_kv("energy_J_kg", initial.energy)
    print_kv("h_m2_s", initial.h)
    print_kv("hx_m2_s", initial.hx)
    print_kv("hy_m2_s", initial.hy)
    print_kv("hz_m2_s", initial.hz)
    print_kv("rp_m", initial.rp)
    if initial.ra is None:
        print_kv("apoapsis", "none")
    else:
        print_kv("ra_m", initial.ra)
    if initial.period is None:
        print_kv("period", "none")
    else:
        print_kv("period_s", initial.period)
    print_kv("rx_m", initial.rx)
    print_kv("ry_m", initial.ry)
    print_kv("rz_m", initial.rz)
    print_kv("vx_m_s", initial.vx)
    print_kv("vy_m_s", initial.vy)
    print_kv("vz_m_s", initial.vz)
    print_kv("di_rad", di)
    print_kv("i_initial_rad", initial.i)
    print_kv("i_final_rad", i_final)
    print_kv("nu_an_rad", ascending.nu)
    print_kv("nu_dn_rad", descending.nu)
    print_kv("r_an_m", _none_or_float(ascending.radius))
    print_kv("r_dn_m", _none_or_float(descending.radius))
    print_kv("v_an_m_s", _none_or_float(ascending.speed))
    print_kv("v_dn_m_s", _none_or_float(descending.speed))
    print_kv("dv_an_m_s", _none_or_float(ascending.dv))
    print_kv("dv_dn_m_s", _none_or_float(descending.dv))
    print_kv("burn", burn.kind)
    print_kv("elev_deg", elev)
    print_kv("azim_deg", azim)
    warning = op.surface_warning(body, initial)
    if warning:
        print_kv("warning", warning)
    print_kv("graph", str(path))
    print_kv("viewer", str(viewer))


def resolve_orbit(ns: argparse.Namespace, body: object):
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
        return op.orbit_from_tle(body.mu, op.parse_tle_args(tle_parts))
    if state_used:
        missing = [name for name in state_names if getattr(ns, name) is None]
        if missing:
            flags = ", ".join(f"--{name}" for name in missing)
            raise ValueError(f"missing vector components: {flags}")
        return op.orbit_from_state(body.mu, ns.rx, ns.ry, ns.rz, ns.vx, ns.vy, ns.vz, "state")
    if not element_used:
        raise ValueError(
            "pass --tle, or --a --e --i --raan --aop and one of --nu or --M, "
            "or pass --rx --ry --rz --vx --vy --vz"
        )
    missing = [name for name in ("a", "e", "i", "raan", "aop") if getattr(ns, name) is None]
    if missing:
        flags = ", ".join(f"--{name}" for name in missing)
        raise ValueError(f"missing elements: {flags}")
    if ns.nu is not None and ns.M is not None:
        raise ValueError("pass exactly one of --nu or --M")
    if ns.nu is None and ns.M is None:
        raise ValueError("pass exactly one of --nu or --M")
    return op.orbit_from_elements(
        body.mu, ns.a, ns.e, ns.i, ns.raan, ns.aop, ns.nu, ns.M, "elements"
    )


def solve(ns: argparse.Namespace):
    op = op_mod()
    if ns.di is None:
        raise ValueError("missing --di")
    op.require_finite(ns.di, "--di")
    body = op.resolve_body(ns.R0, ns.flattening)
    elev, azim = op.resolve_camera(ns.elev, ns.azim)
    initial = resolve_orbit(ns, body)
    i_final = initial.i + ns.di
    if i_final < 0.0 or i_final > math.pi:
        raise ValueError("final inclination must satisfy 0 <= i <= pi radians")
    span_m = op.display_span_m(body, initial)
    ascending = evaluate_node(body, initial, "an", ns.di, span_m)
    descending = evaluate_node(body, initial, "dn", ns.di, span_m)
    burn = choose_burn(ascending, descending, ns.burn)
    final = final_orbit(body, initial, burn, i_final)
    span_m = max(span_m, op.display_span_m(body, final))
    payload = build_payload(
        body, initial, final, ascending, descending, burn, ns.di, i_final, elev, azim, span_m
    )
    return body, initial, final, ascending, descending, burn, i_final, elev, azim, payload


def run(ns: argparse.Namespace) -> int:
    body, initial, _final, ascending, descending, burn, i_final, elev, azim, payload = solve(ns)
    out_path = Path(ns.out) if ns.out else SKILL_DIR / "plane_change_impulse.png"
    out_path = out_path.resolve()
    viewer_path = out_path.with_suffix(".html")
    plot_png(out_path, payload, body, initial)
    write_viewer_html(viewer_path, payload)
    print_report(
        body, initial, ascending, descending, burn, ns.di, i_final, elev, azim, out_path, viewer_path
    )
    if ns.open:
        webbrowser.open(viewer_path.as_uri())
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
    op = op_mod()
    parser = argparse.ArgumentParser(
        description="Impulsive pure inclination change at a node of a Keplerian conic."
    )
    parser.add_argument("--a", type=float, default=None, help="semi-major axis [m]; negative on a hyperbola")
    parser.add_argument("--e", type=float, default=None, help="eccentricity, dimensionless")
    parser.add_argument("--i", type=float, default=None, help="initial inclination [rad], 0 <= i <= pi")
    parser.add_argument("--raan", type=float, default=None, help="longitude of the ascending node [rad]")
    parser.add_argument("--aop", type=float, default=None, help="argument of periapsis [rad]")
    parser.add_argument("--nu", type=float, default=None, help="epoch true anomaly [rad]; not the burn")
    parser.add_argument("--M", type=float, default=None, help="epoch mean anomaly [rad], ellipse only; not the burn")
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
    parser.add_argument("--di", type=float, default=None, help="inclination change [rad]")
    parser.add_argument("--burn", choices=("an", "dn"), default=None, help="node to draw; default is the slower node")
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"planetary radius [m]; default Earth {op.R0_EARTH:.8g}",
    )
    parser.add_argument(
        "--flattening",
        type=float,
        default=None,
        help="visual polar flattening; Earth default 1/298.257, otherwise 0",
    )
    parser.add_argument("--elev", type=float, default=None, help=f"camera elevation [deg]; default {op.ELEV_DEG:g}")
    parser.add_argument("--azim", type=float, default=None, help=f"camera azimuth [deg]; default {op.AZIM_DEG:g}")
    parser.add_argument("--out", type=str, default=None, help="PNG path; the HTML viewer uses the same stem")
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
    return abs(got - expected) <= 1e-8 * span


def _angle_close(got: float, expected: float) -> bool:
    return abs(op_mod().wrap_pi(got - expected)) <= 1e-7


def _vector_close(got: tuple[float, ...], expected: tuple[float, ...]) -> bool:
    scale = max(math.sqrt(sum(component * component for component in expected)), 1.0)
    return all(abs(left - right) <= 1e-8 * scale for left, right in zip(got, expected))


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
    "--di",
    "0.2",
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
    "--di",
    "0.3",
]


def _scene_from_html(html: str) -> dict[str, object]:
    token = '<script type="application/json" id="orbital-scene">'
    start = html.find(token)
    if start < 0:
        raise ValueError("viewer is missing the scene payload")
    start += len(token)
    end = html.find("</script>", start)
    if end < 0:
        raise ValueError("viewer scene payload is not closed")
    return json.loads(html[start:end])


def run_check() -> int:
    op = op_mod()
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(_close(plane_change_impulse(1.0, math.pi), 2.0, 1.0), "half turn impulse")
    check(_close(plane_change_impulse(1.0, math.pi / 3.0), 1.0, 1.0), "sixty degree impulse")

    body = op.resolve_body(None, None)
    orbit = op.orbit_from_elements(body.mu, 1.0e7, 0.3, 0.9, 0.6, 1.2, 0.8, None, "elements")
    span = op.display_span_m(body, orbit)
    for kind in ("an", "dn"):
        node = evaluate_node(body, orbit, kind, 0.2, span)
        expected = conic_radius(orbit.a, orbit.e, node.nu)
        check(node.on_branch, f"{kind} should lie on an ellipse")
        check(node.radius is not None and _close(node.radius, expected), f"{kind} radius vs conic_radius")
        speed = op.vis_viva(body.mu, expected, orbit.a)
        check(node.speed is not None and _close(node.speed, speed), f"{kind} speed vs vis_viva")
        check(
            node.dv is not None and _close(node.dv, plane_change_impulse(speed, 0.2)),
            f"{kind} impulse",
        )

    shared_a = 9.0e6
    shared_e = 0.2
    shared_omega = 0.7
    shared_omega_node = 0.4
    low = op.orbit_from_elements(
        body.mu, shared_a, shared_e, 0.35, shared_omega_node, shared_omega, 0.2, None, "elements"
    )
    high = op.orbit_from_elements(
        body.mu, shared_a, shared_e, 1.15, shared_omega_node, shared_omega, 0.2, None, "elements"
    )
    for kind, label in ((-1.0, "an"), (1.0, "dn")):
        nu = op.wrap_pi(-low.omega if label == "an" else math.pi - low.omega)
        left = op.position_at_true(low, nu)
        right = op.position_at_true(high, nu)
        check(
            _vector_close(left[:3], right[:3]),
            f"shared {label} position for two inclinations",
        )
        check(abs(left[2]) <= 1e-6 * left[3] and abs(right[2]) <= 1e-6 * right[3], f"{label} is equatorial")

    di = 0.25
    i0 = 0.7
    base = op.orbit_from_elements(body.mu, 1.2e7, 0.25, i0, 0.8, 0.5, 1.0, None, "elements")
    nu_an = op.wrap_pi(-base.omega)
    pos = op.position_at_true(base, nu_an)
    vel = op.velocity_at_true(base, nu_an)
    rotated = rotate_velocity(pos[:3], vel, di)
    recovered = op.orbit_from_state(
        body.mu, pos[0], pos[1], pos[2], rotated[0], rotated[1], rotated[2], "state"
    )
    check(_angle_close(recovered.i, i0 + di), "rotated AN state recovers i_f")
    equatorial = recovered.i <= op.EQUATORIAL_FRAC or recovered.i >= math.pi - op.EQUATORIAL_FRAC
    if equatorial:
        check(abs(recovered.Omega) <= 1e-8, "ELCONO sets Omega to 0 on an equator")
    else:
        check(_angle_close(recovered.Omega, base.Omega), "Omega unchanged within ELCONO")
    final_elements = op.orbit_from_elements(
        body.mu, base.a, base.e, i0 + di, base.Omega, base.omega, nu_an, None, "elements"
    )
    final_velocity = op.velocity_at_true(final_elements, op.wrap_pi(-final_elements.omega))
    check(_vector_close(rotated, final_velocity), "AN rotation matches the final-orbit velocity")

    nu_dn = op.wrap_pi(math.pi - base.omega)
    pos_dn = op.position_at_true(base, nu_dn)
    vel_dn = op.velocity_at_true(base, nu_dn)
    rotated_dn = rotate_about_nodes(base, vel_dn, di)
    final_dn = op.velocity_at_true(final_elements, op.wrap_pi(math.pi - final_elements.omega))
    check(_vector_close(rotated_dn, final_dn), "DN rotation matches the final-orbit velocity")

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        png = root / "earth.png"
        code, out, err = invoke(EARTH_ELLIPSE + ["--out", str(png)])
        check(code == 0 and err == "", f"earth ellipse example failed: {err or out}")
        if code == 0:
            report = parse_stdout(out)
            html_path = png.with_suffix(".html")
            check(png.is_file() and html_path.is_file(), "earth example writes PNG and HTML")
            data = png.read_bytes()
            check(data.startswith(b"\x89PNG\r\n\x1a\n"), "PNG magic bytes")
            html = html_path.read_text(encoding="utf-8")
            check(PLOT_TITLE in html, "HTML title")
            check("__THREE_SOURCE__" not in html and "__SCENE_JSON__" not in html, "placeholders replaced")
            check("<script src=" not in html.lower(), "Three.js is inlined")
            check("new THREE.OrthographicCamera" in html and len(html) > 100000, "inlined Three.js")
            check("inclination hinge" in html and "sampleInclined" in html, "hinge animation")
            scene = _scene_from_html(html)
            check("initial_orbit_km" in scene and "final_orbit_km" in scene, "dual orbit payload")
            check("kepler_initial" in scene and "kepler_final" in scene, "both Kepler element sets")
            check(scene["title"] == PLOT_TITLE, "payload title")
            check(report.get("burn") == "dn", "default burn is the slower node")
            check(_close(float(report["di_rad"]), 0.2, 1.0), "printed di")
            check(
                _close(float(report["i_final_rad"]), float(report["i_initial_rad"]) + 0.2, 1.0),
                "printed i_f",
            )
            check(report.get("graph") == str(png.resolve()), "graph path")
            check(report.get("viewer") == str(html_path.resolve()), "viewer path")

        state_png = root / "state.png"
        code, out, err = invoke(STATE_EXAMPLE + ["--out", str(state_png)])
        check(code == 0 and err == "", f"state mode failed: {err or out}")
        if code == 0:
            report = parse_stdout(out)
            check(report.get("mode") == "state", "state mode tag")
            check(state_png.is_file() and state_png.with_suffix(".html").is_file(), "state artifacts")

        op = op_mod()
        tle_png = root / "tle.png"
        code, out, err = invoke(
            ["--tle", op.ISS_TLE_LINE1, op.ISS_TLE_LINE2, "--di", "0.05", "--out", str(tle_png)]
        )
        check(code == 0 and err == "", f"TLE mode failed: {err or out}")
        if code == 0:
            report = parse_stdout(out)
            check(report.get("mode") == "tle", "tle mode tag")
            check(report.get("tle_catalog") == "25544", "tle catalog")
            check(tle_png.is_file() and tle_png.with_suffix(".html").is_file(), "tle artifacts")

        code, _out, err = invoke(
            [
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
        )
        check(code == 2 and "missing --di" in err, "missing --di exits 2")

        code, _out, err = invoke(EARTH_ELLIPSE[:-1] + ["2.5", "--out", str(root / "high.png")])
        check(code == 2 and "final inclination" in err, "i_f above pi exits 2")
        code, _out, err = invoke(
            [
                "--a",
                "10000000",
                "--e",
                "0.1",
                "--i",
                "0.2",
                "--raan",
                "0.4",
                "--aop",
                "0.5",
                "--nu",
                "0.3",
                "--di",
                "-0.3",
            ]
        )
        check(code == 2 and "final inclination" in err, "i_f below 0 exits 2")

        hyper_png = root / "hyper.png"
        code, out, err = invoke(
            [
                "--a=-25000000",
                "--e",
                "1.4",
                "--i",
                "1.1",
                "--raan",
                "0.8",
                "--aop",
                "0.5",
                "--nu",
                "0.6",
                "--di",
                "0.15",
                "--out",
                str(hyper_png),
            ]
        )
        check(code == 0 and err == "", f"hyperbola failed: {err or out}")
        if code == 0:
            report = parse_stdout(out)
            check(report.get("conic") == "hyperbola", "hyperbola conic")
            check(report.get("dv_dn_m_s") == "none", "descending node off the drawn branch")
            check(report.get("dv_an_m_s") != "none", "ascending node on the branch")
            check(report.get("burn") == "an", "only the available node is selected")

        eq_png = root / "eq.png"
        code, out, err = invoke(
            [
                "--a",
                "8000000",
                "--e",
                "0.05",
                "--i",
                "0",
                "--raan",
                "0",
                "--aop",
                "0.3",
                "--nu",
                "1",
                "--di",
                "0.4",
                "--out",
                str(eq_png),
            ]
        )
        check(code == 0 and err == "", f"equatorial start failed: {err or out}")
        if code == 0:
            report = parse_stdout(out)
            check(report.get("dv_an_m_s") != "none" and report.get("dv_dn_m_s") != "none", "equator has both nodes")

    if errors:
        for message in errors:
            print(f"check failed: {message}", file=sys.stderr)
        return 1
    print("check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
