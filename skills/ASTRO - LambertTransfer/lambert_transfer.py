#!/usr/bin/env python3
"""Single-revolution Lambert transfer between two position vectors.

lambert_geometric_parameter, stumpff_c_elliptic, stumpff_s_elliptic,
stumpff_c_hyperbolic, stumpff_s_hyperbolic, lambert_y_parameter,
lambert_time_of_flight, lagrange_f, lagrange_g, and lagrange_gdot
build the universal-variable residual. The root is found numerically.
semimajor_axis_from_state, eccentricity_from_energy, and
parameter_from_angular_momentum describe the conic.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-6
G0 = 9.80665
R0_EARTH = 6.3742e6
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Lambert transfer"
Z_MIN = -40.0
Z_MAX = (2.0 * math.pi) ** 2 * (1.0 - 1e-8)
N_PROP = 160

Vec = tuple[float, float, float]

ASSUMPTIONS = (
    "two-body inverse-square gravity; one revolution; "
    "lambert_geometric_parameter A = sin(dth)*sqrt(r1*r2/(1-cos(dth))); "
    "stumpff_c_elliptic, stumpff_s_elliptic, stumpff_c_hyperbolic, stumpff_s_hyperbolic; "
    "lambert_y_parameter and lambert_time_of_flight; "
    "lagrange_f, lagrange_g, lagrange_gdot, and lambert_velocity_from_lagrange; "
    "semimajor_axis_from_state, eccentricity_from_energy, parameter_from_angular_momentum; "
    "short way is the transfer angle at most pi; long way is the supplement through 2*pi; "
    "a 180 degree chord uses the fixed parameter p = 2*r1*r2/(r1+r2) and an elliptic root; "
    "equal radii at half the circular period are the circular coast, eccentricity 0; "
    "the 180 degree plane normal is r1 cross z, or r1 cross y if those are parallel; "
    "long way flips that normal; "
    "parking delta-v uses a circular velocity in the transfer plane; "
    "multi-revolution branches are not solved; "
    "default mu = g0*R0^2 with g0 = 9.80665 m/s^2 and Earth R0 = 6.3742e6 m"
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


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec, factor: float) -> Vec:
    return (a[0] * factor, a[1] * factor, a[2] * factor)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Vec) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec) -> Vec:
    length = norm(a)
    if length == 0.0:
        raise ValueError("a zero vector has no direction")
    return scale(a, 1.0 / length)


def stumpff(z: float) -> tuple[float, float]:
    if abs(z) < 1.0e-4:
        c_val = 0.5 - z / 24.0 + z * z / 720.0
        s_val = 1.0 / 6.0 - z / 120.0 + z * z / 5040.0
        return c_val, s_val
    if z > 0.0:
        root = math.sqrt(z)
        return (1.0 - math.cos(root)) / z, (root - math.sin(root)) / (root**3)
    root = math.sqrt(-z)
    cosh = math.cosh(root)
    sinh = math.sinh(root)
    return (cosh - 1.0) / (-z), (sinh - root) / (root**3)


def y_parameter(z: float, r1: float, r2: float, geometric: float) -> tuple[float, float, float] | None:
    c_val, s_val = stumpff(z)
    if c_val <= 0.0:
        return None
    y_val = r1 + r2 + geometric * (z * s_val - 1.0) / math.sqrt(c_val)
    if y_val <= 0.0:
        return None
    return y_val, c_val, s_val


def time_of_flight(z: float, r1: float, r2: float, geometric: float, mu: float) -> float | None:
    packed = y_parameter(z, r1, r2, geometric)
    if packed is None:
        return None
    y_val, c_val, s_val = packed
    return ((y_val / c_val) ** 1.5 * s_val + geometric * math.sqrt(y_val)) / math.sqrt(mu)


def bisect(func, lo: float, hi: float, y_lo: float) -> float:
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        value = func(mid)
        if value is None:
            hi = mid
            continue
        if y_lo * value <= 0.0:
            hi = mid
        else:
            lo = mid
            y_lo = value
    return 0.5 * (lo + hi)


def find_universal_z(r1: float, r2: float, geometric: float, mu: float, tof: float) -> float:
    samples: list[tuple[float, float]] = []
    for index in range(160):
        z_val = Z_MIN + (Z_MAX - Z_MIN) * index / 159.0
        flight = time_of_flight(z_val, r1, r2, geometric, mu)
        if flight is not None and math.isfinite(flight):
            samples.append((z_val, flight - tof))
    for (z0, y0), (z1, y1) in zip(samples, samples[1:]):
        if y0 == 0.0:
            return z0
        if y0 * y1 < 0.0:
            return bisect(lambda z_val: _residual(z_val, r1, r2, geometric, mu, tof), z0, z1, y0)
    raise ValueError("time of flight is outside the single-revolution range")


def _residual(z_val: float, r1: float, r2: float, geometric: float, mu: float, tof: float) -> float | None:
    flight = time_of_flight(z_val, r1, r2, geometric, mu)
    if flight is None:
        return None
    return flight - tof


def collinear_normal(r1: Vec, way: str) -> Vec:
    normal = cross(r1, (0.0, 0.0, 1.0))
    if norm(normal) < 1.0e-8 * norm(r1):
        normal = cross(r1, (0.0, 1.0, 0.0))
    if way == "long":
        normal = scale(normal, -1.0)
    return unit(normal)


def elliptic_half_tof(eccentricity: float, r1: float, r2: float, mu: float) -> float:
    parameter = 2.0 * r1 * r2 / (r1 + r2)
    kappa = (parameter / 2.0) * (1.0 / r1 - 1.0 / r2)
    semimajor = parameter / (1.0 - eccentricity * eccentricity)
    cos1 = max(-1.0, min(1.0, kappa / eccentricity))
    sin1 = math.sqrt(max(0.0, 1.0 - cos1 * cos1))

    def anomaly(cos_nu: float, sin_nu: float) -> float:
        denom = 1.0 + eccentricity * cos_nu
        sin_e = sin_nu * math.sqrt(1.0 - eccentricity * eccentricity) / denom
        cos_e = (eccentricity + cos_nu) / denom
        return math.atan2(sin_e, cos_e)

    first = anomaly(cos1, sin1)
    second = anomaly(-cos1, -sin1)
    if second <= first:
        second += 2.0 * math.pi
    mean = (second - eccentricity * math.sin(second)) - (first - eccentricity * math.sin(first))
    return math.sqrt(semimajor**3 / mu) * mean


def solve_collinear(r1: Vec, r2: Vec, tof: float, mu: float, way: str) -> tuple[Vec, Vec, float]:
    r1n, r2n = norm(r1), norm(r2)
    # Equal radii: the circular half-period is the elliptic 180° coast.
    # The eccentricity search starts above zero, so that exact time is not a root.
    if abs(r1n - r2n) <= 1.0e-9 * max(r1n, r2n):
        half = math.pi * math.sqrt(r1n**3 / mu)
        if abs(tof - half) <= 1.0e-6 * half:
            specific_h = math.sqrt(mu * r1n)
            normal = collinear_normal(r1, way)
            r1_hat = unit(r1)
            r2_hat = unit(r2)
            v1 = scale(cross(normal, r1_hat), specific_h / r1n)
            v2 = scale(cross(normal, r2_hat), specific_h / r2n)
            return v1, v2, 0.0
    parameter = 2.0 * r1n * r2n / (r1n + r2n)
    kappa = (parameter / 2.0) * (1.0 / r1n - 1.0 / r2n)
    e_min = max(abs(kappa), 1.0e-8)
    if e_min >= 1.0:
        raise ValueError("the 180 degree chord has no elliptic solution")
    target_min = elliptic_half_tof(e_min, r1n, r2n, mu)
    if close(tof, target_min, 1e-8):
        eccentricity = e_min
    else:
        samples = []
        for index in range(1, 80):
            eccentricity = e_min + (0.999 - e_min) * index / 79.0
            samples.append((eccentricity, elliptic_half_tof(eccentricity, r1n, r2n, mu) - tof))
        eccentricity = None
        chain = [(e_min, target_min - tof)] + samples
        for (e0, y0), (e1, y1) in zip(chain, chain[1:]):
            if y0 == 0.0:
                eccentricity = e0
                break
            if y0 * y1 < 0.0:
                eccentricity = bisect(
                    lambda ecc: elliptic_half_tof(ecc, r1n, r2n, mu) - tof,
                    e0,
                    e1,
                    y0,
                )
                break
        if eccentricity is None:
            raise ValueError("time of flight is outside the single-revolution elliptic range for a 180 degree chord")
    specific_h = math.sqrt(mu * parameter)
    cos1 = max(-1.0, min(1.0, kappa / eccentricity))
    sin1 = math.sqrt(max(0.0, 1.0 - cos1 * cos1))
    normal = collinear_normal(r1, way)
    r1_hat = unit(r1)
    r2_hat = unit(r2)
    t1 = cross(normal, r1_hat)
    t2 = cross(normal, r2_hat)
    v1 = add(scale(r1_hat, mu / specific_h * eccentricity * sin1), scale(t1, specific_h / r1n))
    v2 = add(scale(r2_hat, mu / specific_h * eccentricity * (-sin1)), scale(t2, specific_h / r2n))
    return v1, v2, eccentricity


def transfer_angle(r1: Vec, r2: Vec, way: str) -> float:
    cosine = dot(r1, r2) / (norm(r1) * norm(r2))
    cosine = max(-1.0, min(1.0, cosine))
    short = math.acos(cosine)
    return short if way == "short" else 2.0 * math.pi - short


def velocities(r1: Vec, r2: Vec, tof: float, mu: float, way: str) -> tuple[Vec, Vec]:
    if tof <= 0.0 or not math.isfinite(tof):
        raise ValueError("time of flight must be finite and > 0")
    if mu <= 0.0 or not math.isfinite(mu):
        raise ValueError("mu must be finite and > 0")
    r1n, r2n = norm(r1), norm(r2)
    if r1n == 0.0 or r2n == 0.0:
        raise ValueError("position vectors must be nonzero")
    angle = transfer_angle(r1, r2, way)
    if angle < 1.0e-4 or 2.0 * math.pi - angle < 1.0e-4:
        raise ValueError("transfer angle is too small")
    if abs(math.sin(angle)) < 1.0e-8:
        v1, v2, _ = solve_collinear(r1, r2, tof, mu, way)
        return v1, v2
    geometric = math.sin(angle) * math.sqrt(r1n * r2n / (1.0 - math.cos(angle)))
    z_root = find_universal_z(r1n, r2n, geometric, mu, tof)
    packed = y_parameter(z_root, r1n, r2n, geometric)
    if packed is None:
        raise ValueError("the universal-variable root has no positive y")
    y_val, _, _ = packed
    lagrange_f = 1.0 - y_val / r1n
    lagrange_g = geometric * math.sqrt(y_val / mu)
    lagrange_gdot = 1.0 - y_val / r2n
    if abs(lagrange_g) < 1.0e-9:
        raise ValueError("Lagrange g vanished")
    v1 = scale(sub(r2, scale(r1, lagrange_f)), 1.0 / lagrange_g)
    v2 = scale(sub(scale(r2, lagrange_gdot), r1), 1.0 / lagrange_g)
    return v1, v2


def conic(r_vec: Vec, v_vec: Vec, mu: float) -> dict[str, float | str]:
    radius = norm(r_vec)
    speed = norm(v_vec)
    energy = speed * speed / 2.0 - mu / radius
    semimajor = mu * radius / (2.0 * mu - radius * speed * speed)
    specific_h = norm(cross(r_vec, v_vec))
    parameter = specific_h**2 / mu
    eccentricity = math.sqrt(max(0.0, 1.0 + 2.0 * energy * specific_h**2 / mu**2))
    scale_energy = mu / radius
    if energy < -1.0e-8 * scale_energy:
        kind = "ellipse"
    elif energy > 1.0e-8 * scale_energy:
        kind = "hyperbola"
    else:
        kind = "parabola"
    return {
        "a_m": semimajor,
        "e": eccentricity,
        "p_m": parameter,
        "energy_m2_s2": energy,
        "energy_class": kind,
    }


def parking_delta(v_vec: Vec, r_vec: Vec, speed: float) -> Vec:
    if speed <= 0.0 or not math.isfinite(speed):
        raise ValueError("a parking speed must be finite and > 0")
    normal = unit(cross(r_vec, v_vec))
    tangential = cross(normal, unit(r_vec))
    return sub(v_vec, scale(tangential, speed))


def propagate(r_vec: Vec, v_vec: Vec, tof: float, mu: float) -> list[Vec]:
    state_r, state_v = r_vec, v_vec
    dt = tof / N_PROP
    points = [state_r]
    for _ in range(N_PROP):
        def deriv(rr: Vec, vv: Vec) -> tuple[Vec, Vec]:
            return vv, scale(rr, -mu / norm(rr) ** 3)

        k1r, k1v = deriv(state_r, state_v)
        k2r, k2v = deriv(add(state_r, scale(k1r, dt / 2.0)), add(state_v, scale(k1v, dt / 2.0)))
        k3r, k3v = deriv(add(state_r, scale(k2r, dt / 2.0)), add(state_v, scale(k2v, dt / 2.0)))
        k4r, k4v = deriv(add(state_r, scale(k3r, dt)), add(state_v, scale(k3v, dt)))
        state_r = add(state_r, scale(add(add(k1r, scale(k2r, 2.0)), add(scale(k3r, 2.0), k4r)), dt / 6.0))
        state_v = add(state_v, scale(add(add(k1v, scale(k2v, 2.0)), add(scale(k3v, 2.0), k4v)), dt / 6.0))
        points.append(state_r)
    return points


def solve(r1: Vec, r2: Vec, tof: float, mu: float, way: str, v1circ: float | None, v2circ: float | None) -> dict[str, object]:
    v1, v2 = velocities(r1, r2, tof, mu, way)
    elements = conic(r1, v1, mu)
    result: dict[str, object] = {
        "way": way,
        "tof_s": tof,
        "mu_m3_s2": mu,
        "r1x_m": r1[0],
        "r1y_m": r1[1],
        "r1z_m": r1[2],
        "r2x_m": r2[0],
        "r2y_m": r2[1],
        "r2z_m": r2[2],
        "v1x_m_s": v1[0],
        "v1y_m_s": v1[1],
        "v1z_m_s": v1[2],
        "v2x_m_s": v2[0],
        "v2y_m_s": v2[1],
        "v2z_m_s": v2[2],
        "path_m": propagate(r1, v1, tof, mu),
    }
    result.update(elements)
    if v1circ is not None:
        delta = parking_delta(v1, r1, v1circ)
        result["dv1_m_s"] = norm(delta)
        result["dv1_vec"] = delta
    if v2circ is not None:
        delta = parking_delta(v2, r2, v2circ)
        result["dv2_m_s"] = norm(delta)
        result["dv2_vec"] = delta
    return result


def emit(result: dict[str, object], graph: Path, html: Path | None, mu_source: str) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mu_source", mu_source)
    for key in (
        "way",
        "tof_s",
        "mu_m3_s2",
        "v1x_m_s",
        "v1y_m_s",
        "v1z_m_s",
        "v2x_m_s",
        "v2y_m_s",
        "v2z_m_s",
        "a_m",
        "e",
        "p_m",
        "energy_m2_s2",
        "energy_class",
        "dv1_m_s",
        "dv2_m_s",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))
    if html is not None:
        print_kv("viewer", str(html))


_OP = None


def op_mod():
    """OrbitalParameters drawing helpers. This skill does not call that program's run()."""
    global _OP
    if _OP is None:
        folder = str(SKILL_DIR.parent / "ASTRO - OrbitalParameters")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import orbital_parameters as imported

        _OP = imported
    return _OP


def coast_state(leg: dict[str, object]) -> tuple[Vec, Vec]:
    """Position in metres and velocity in m/s at the start of a coast leg."""
    nu = float(leg["nu0"])
    radius = float(leg["p"]) / (1.0 + float(leg["e"]) * math.cos(nu))
    argument = float(leg["omega"]) + nu
    position = perifocal_point(radius, nu, float(leg["i"]), float(leg["Omega"]), float(leg["omega"]))
    vr = (float(leg["h"]) * float(leg["e"]) / float(leg["p"])) * math.sin(nu)
    vp = float(leg["h"]) / radius
    omega_node = float(leg["Omega"])
    inclination = float(leg["i"])
    velocity = (
        (vr / radius) * position[0]
        - vp * (math.cos(omega_node) * math.sin(argument) + math.sin(omega_node) * math.cos(inclination) * math.cos(argument)),
        (vr / radius) * position[1]
        + vp * (-math.sin(omega_node) * math.sin(argument) + math.cos(omega_node) * math.cos(inclination) * math.cos(argument)),
        (vr / radius) * position[2] + vp * math.sin(inclination) * math.cos(argument),
    )
    return position, velocity


def epoch_state(payload: dict[str, object]) -> tuple[list[float], Vec, str]:
    """Spacecraft kilometres, velocity, and readout label at the viewer's first frame."""
    sequence = payload["sequence"]
    leg = sequence[0]
    label = str(leg.get("label") or leg.get("kind") or "")
    if leg["kind"] == "path":
        samples = leg["samples_km"]
        craft = [float(samples[0][0]), float(samples[0][1]), float(samples[0][2])]
        if len(samples) > 1:
            velocity = (
                float(samples[1][0]) - craft[0],
                float(samples[1][1]) - craft[1],
                float(samples[1][2]) - craft[2],
            )
        else:
            velocity = (0.0, 1.0, 0.0)
        return craft, velocity, label
    if leg["kind"] == "burn":
        burn = payload["burns"][int(leg["burn"])]
        craft = [float(burn["km"][0]), float(burn["km"][1]), float(burn["km"][2])]
        velocity = tuple(float(component) for component in leg.get("v_from") or burn["dv_m_s"])
        return craft, velocity, label
    position, velocity = coast_state(leg)
    return [position[0] / 1000.0, position[1] / 1000.0, position[2] / 1000.0], velocity, label


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
            op.behind_planet(x, y, z, outward[0], outward[1], outward[2], radius_km) for x, y, z in polyline
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


def write_plot(path: Path, payload: dict[str, object]) -> None:
    """Still PNG of the viewer scene at the first playback frame."""
    from types import SimpleNamespace

    from matplotlib.ticker import MaxNLocator

    op = op_mod()
    plt = op.ensure_matplotlib()
    palette = payload["palette"]
    planet = SimpleNamespace(
        elev_deg=payload["elev_deg"],
        azim_deg=payload["azim_deg"],
        roll_deg=payload["roll_deg"],
        planet_segments_u=payload["planet_segments_u"],
        planet_segments_v=payload["planet_segments_v"],
        equatorial_radius_km=payload["equatorial_radius_km"],
        polar_radius_km=payload["polar_radius_km"],
        planet_opacity=payload["planet_opacity"],
    )
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

    xs, ys, zs, rgba = op._planet_arrays(planet)
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
    radius_km = float(payload["equatorial_radius_km"])
    active = str(payload["sequence"][0].get("layer") or "")
    layers = list(payload["layers"])
    layers.sort(key=lambda layer: layer["id"] == active)
    for layer in layers:
        hot = layer["id"] == active
        _draw_polylines(
            ax,
            layer["polylines"],
            layer["color"],
            outward,
            radius_km,
            2.8 if hot else 2.2,
            1.65 if hot else 1.3,
            1.0 if hot else 0.38,
        )

    craft, velocity, phase = epoch_state(payload)
    ax.plot(
        [0.0, craft[0]],
        [0.0, craft[1]],
        [0.0, craft[2]],
        color=palette["radius"],
        linewidth=1.15,
        zorder=5,
        solid_capstyle="round",
    )
    if norm(velocity) > 0.0:
        ax.quiver(
            craft[0],
            craft[1],
            craft[2],
            velocity[0],
            velocity[1],
            velocity[2],
            length=float(payload["velocity_length_km"]),
            normalize=True,
            color=palette["velocity"],
            arrow_length_ratio=0.18,
            linewidth=1.35,
        )
    arrow_length = float(payload["velocity_length_km"]) * 1.65
    for burn in payload["burns"]:
        dv = burn["dv_m_s"]
        if norm((float(dv[0]), float(dv[1]), float(dv[2]))) <= 0.0:
            continue
        ax.quiver(
            burn["km"][0],
            burn["km"][1],
            burn["km"][2],
            dv[0],
            dv[1],
            dv[2],
            length=arrow_length,
            normalize=True,
            color=burn["color"],
            arrow_length_ratio=0.22,
            linewidth=2.2,
        )

    for marker in payload["markers"]:
        if marker["id"] == "spacecraft":
            continue
        ax.scatter(
            [marker["km"][0]],
            [marker["km"][1]],
            [marker["km"][2]],
            color=marker["color"],
            s=78,
            marker="s" if marker["shape"] == "square" else "o",
            depthshade=False,
            edgecolors="white",
            linewidths=1.15,
            zorder=9,
        )
    craft_marker = next(marker for marker in payload["markers"] if marker["id"] == "spacecraft")
    ax.scatter(
        [craft[0]],
        [craft[1]],
        [craft[2]],
        color=craft_marker["color"],
        s=88,
        marker="o",
        depthshade=False,
        edgecolors="white",
        linewidths=1.2,
        zorder=10,
    )

    limit = float(payload["limit_km"])
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
    ax.set_title(str(payload["title"]), pad=8, fontsize=15, color=palette["text"])
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
        f"elev {float(payload['elev_deg']):.4g}°    azim {float(payload['azim_deg']):.4g}°    {phase}",
        transform=ax.transAxes,
        fontsize=9,
        color=palette["caption"],
    )
    handles = [
        op._legend_handle(op.LegendEntry(entry["label"], entry["swatch"], entry["color"], entry["edge"]))
        for entry in payload["legend"]
    ]
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


PALETTE = {
    "planet": "#c5ddef",
    "planet_edge": "#1a5276",
    "equator": "#7eb6e0",
    "equator_spoke": "#a9d2ef",
    "equator_limb": "#1a5276",
    "orbit": "#1a5276",
    "radius": "#922b21",
    "velocity": "#2471a3",
    "craft": "#c0392b",
    "axis": "#1a5276",
    "text": "#1b2631",
    "caption": "#34495e",
    "pane": "#f7f9fb",
    "dv": "#e67e22",
    "transfer": "#c0392b",
    "arrive": "#1a5276",
    "depart": "#1a5276",
}
VIEW_ELEV_DEG = 20.0
VIEW_AZIM_DEG = 35.0
F_EARTH = 1.0 / 298.257
COAST_WALL_S = 8.0
BURN_WALL_S = 2.4
PARK_WALL_S = 3.6
ARRIVE_WALL_S = 11.0


def _km(point: Vec) -> list[float]:
    return [point[0] / 1000.0, point[1] / 1000.0, point[2] / 1000.0]


def _true_anomaly(reference: Vec, position: Vec, h_hat: Vec) -> float:
    return math.atan2(dot(cross(reference, position), h_hat), dot(reference, position))


def orbit_frame(r_vec: Vec, v_vec: Vec, mu: float) -> dict[str, float]:
    h_vec = cross(r_vec, v_vec)
    h_mag = norm(h_vec)
    h_hat = scale(h_vec, 1.0 / h_mag)
    radius = norm(r_vec)
    e_vec = sub(scale(r_vec, dot(v_vec, v_vec) / mu - 1.0 / radius), scale(v_vec, dot(r_vec, v_vec) / mu))
    eccentricity = norm(e_vec)
    inclination = math.acos(max(-1.0, min(1.0, h_hat[2])))
    node = cross((0.0, 0.0, 1.0), h_vec)
    if norm(node) < 1.0e-10 * h_mag:
        omega_node = 0.0
        reference = e_vec if eccentricity > 1.0e-8 else (1.0, 0.0, 0.0)
        argument = _true_anomaly((1.0, 0.0, 0.0), reference, h_hat) if eccentricity > 1.0e-8 else 0.0
    else:
        omega_node = math.atan2(node[1], node[0])
        argument = 0.0 if eccentricity <= 1.0e-8 else _true_anomaly(node, e_vec, h_hat)
        reference = e_vec if eccentricity > 1.0e-8 else node
    if eccentricity <= 1.0e-8:
        reference = node if norm(node) >= 1.0e-10 * h_mag else (1.0, 0.0, 0.0)
        argument = 0.0
    true_anomaly = _true_anomaly(reference, r_vec, h_hat)
    return {
        "i": inclination,
        "Omega": omega_node,
        "omega": argument,
        "nu": true_anomaly,
        "h": h_mag,
        "e": eccentricity,
    }


def perifocal_point(radius: float, angle: float, inclination: float, omega_node: float, argument: float) -> Vec:
    argument_of_latitude = argument + angle
    return (
        radius
        * (
            math.cos(omega_node) * math.cos(argument_of_latitude)
            - math.sin(omega_node) * math.cos(inclination) * math.sin(argument_of_latitude)
        ),
        radius
        * (
            math.sin(omega_node) * math.cos(argument_of_latitude)
            + math.cos(omega_node) * math.cos(inclination) * math.sin(argument_of_latitude)
        ),
        radius * math.sin(inclination) * math.sin(argument_of_latitude),
    )


def conic_polyline(frame: dict[str, float], count: int = 361) -> list[list[float]]:
    eccentricity = frame["e"]
    parameter = frame["p"]
    points: list[list[float]] = []
    for index in range(count):
        anomaly = 2.0 * math.pi * index / (count - 1)
        if eccentricity >= 1.0:
            break
        denominator = 1.0 + eccentricity * math.cos(anomaly)
        if denominator <= 1.0e-8:
            continue
        radius = parameter / denominator
        point = perifocal_point(radius, anomaly, frame["i"], frame["Omega"], frame["omega"])
        points.append(_km(point))
    return points


def circle_polyline(radius: float, radial: Vec, tangential: Vec, count: int = 361) -> list[list[float]]:
    points: list[list[float]] = []
    for index in range(count):
        angle = 2.0 * math.pi * index / (count - 1)
        point = add(scale(radial, radius * math.cos(angle)), scale(tangential, radius * math.sin(angle)))
        points.append(_km(point))
    return points


def central_body(mu: float, inner_radius: float) -> tuple[float, bool]:
    earth_mu = G0 * R0_EARTH**2
    if math.isclose(mu, earth_mu, rel_tol=1.0e-6):
        return R0_EARTH, True
    guessed = math.sqrt(max(mu, 0.0) / G0)
    if 0.0 < guessed < 0.98 * inner_radius:
        return guessed, math.isclose(guessed, R0_EARTH, rel_tol=1.0e-4)
    return 0.42 * inner_radius, False


def scene_payload(result: dict[str, object]) -> dict[str, object]:
    r1 = (float(result["r1x_m"]), float(result["r1y_m"]), float(result["r1z_m"]))
    r2 = (float(result["r2x_m"]), float(result["r2y_m"]), float(result["r2z_m"]))
    v1 = (float(result["v1x_m_s"]), float(result["v1y_m_s"]), float(result["v1z_m_s"]))
    v2 = (float(result["v2x_m_s"]), float(result["v2y_m_s"]), float(result["v2z_m_s"]))
    mu = float(result["mu_m3_s2"])
    frame = orbit_frame(r1, v1, mu)
    frame["p"] = float(result["p_m"])
    frame["e"] = float(result["e"])
    h_hat = unit(cross(r1, v1))
    chord_sine = dot(cross(r1, r2), h_hat) / (norm(r1) * norm(r2))
    chord_cosine = dot(r1, r2) / (norm(r1) * norm(r2))
    span = math.atan2(max(-1.0, min(1.0, chord_sine)), max(-1.0, min(1.0, chord_cosine)))
    if result["way"] == "long" and abs(abs(span) - math.pi) > 1.0e-4:
        span += -2.0 * math.pi if span > 0.0 else 2.0 * math.pi
    nu0 = frame["nu"]
    body_radius, earth = central_body(mu, min(norm(r1), norm(r2)))
    outer = max(norm(r1), norm(r2), body_radius, abs(float(result["a_m"])))
    if float(result["e"]) < 1.0:
        periapsis = frame["p"] / (1.0 + float(result["e"]))
        apoapsis = frame["p"] / max(1.0e-8, 1.0 - float(result["e"]))
        outer = max(outer, apoapsis)
    span_m = max(body_radius, outer)
    limit_m = 1.16 * span_m
    axis_len = min(max(1.35 * body_radius, 0.42 * span_m), 0.72 * span_m)
    ring_r = min(1.22 * body_radius, 0.98 * span_m)
    flattening = F_EARTH if earth else 0.0
    angles = [2.0 * math.pi * index / 180.0 for index in range(181)]
    ring = [[ring_r * math.cos(angle) / 1000.0, ring_r * math.sin(angle) / 1000.0, 0.0] for angle in angles]
    equator = [
        [body_radius * math.cos(angle) / 1000.0, body_radius * math.sin(angle) / 1000.0, 0.0] for angle in angles
    ]
    spokes: list[list[list[float]]] = []
    inner = min(body_radius, ring_r)
    if ring_r > inner * (1.0 + 1.0e-6):
        for spoke in range(8):
            angle = spoke * math.pi / 8.0
            spokes.append(
                [
                    [inner * math.cos(angle) / 1000.0, inner * math.sin(angle) / 1000.0, 0.0],
                    [ring_r * math.cos(angle) / 1000.0, ring_r * math.sin(angle) / 1000.0, 0.0],
                ]
            )
    axes = [
        {"label": "X", "tip_km": [axis_len / 1000.0, 0.0, 0.0], "label_km": [axis_len * 1.08 / 1000.0, 0.0, 0.0]},
        {"label": "Y", "tip_km": [0.0, axis_len / 1000.0, 0.0], "label_km": [0.0, axis_len * 1.08 / 1000.0, 0.0]},
        {"label": "Z", "tip_km": [0.0, 0.0, axis_len / 1000.0], "label_km": [0.0, 0.0, axis_len * 1.08 / 1000.0]},
    ]
    if result["energy_class"] == "ellipse":
        transfer_line = conic_polyline(frame)
    else:
        transfer_line = [_km(point) for point in result["path_m"]]
    layers = [
        {"id": "transfer", "color": PALETTE["transfer"], "faded": False, "polylines": [transfer_line]},
    ]
    normal = unit(cross(r1, v1))
    if "dv1_vec" in result:
        layers.insert(
            0,
            {
                "id": "depart",
                "color": PALETTE["depart"],
                "faded": True,
                "polylines": [circle_polyline(norm(r1), unit(r1), cross(normal, unit(r1)))],
            },
        )
    if "dv2_vec" in result:
        layers.append(
            {
                "id": "arrive",
                "color": PALETTE["arrive"],
                "faded": True,
                "polylines": [circle_polyline(norm(r2), unit(r2), cross(normal, unit(r2)))],
            }
        )
    depart_km = _km(r1)
    arrive_km = _km(r2)
    markers = [
        {"id": "departure", "label": "departure", "shape": "square", "color": "#27ae60", "km": depart_km},
        {"id": "arrival", "label": "arrival", "shape": "circle", "color": PALETTE["arrive"], "km": arrive_km},
        {"id": "spacecraft", "label": "spacecraft", "shape": "circle", "color": PALETTE["craft"], "km": depart_km},
    ]
    def circle_coast(radius: float, omega: float, nu_start: float, nu_end: float, wall: float, layer: str, label: str) -> dict[str, object]:
        return {
            "kind": "coast",
            "label": label,
            "layer": layer,
            "wall_s": wall,
            "direct": True,
            "a": radius,
            "e": 0.0,
            "i": frame["i"],
            "Omega": frame["Omega"],
            "omega": omega,
            "p": radius,
            "h": math.sqrt(mu * radius),
            "mu": mu,
            "nu0": nu_start,
            "nu1": nu_end,
        }

    def burn_leg(
        index: int,
        label: str,
        layer: str,
        place: Vec,
        v_from: Vec,
        v_to: Vec,
        from_layer: str,
        to_layer: str,
    ) -> dict[str, object]:
        return {
            "kind": "burn",
            "label": label,
            "layer": layer,
            "wall_s": BURN_WALL_S,
            "burn": index,
            "r_m": [place[0], place[1], place[2]],
            "v_from": [v_from[0], v_from[1], v_from[2]],
            "v_to": [v_to[0], v_to[1], v_to[2]],
            "mu": mu,
            "from_layer": from_layer,
            "to_layer": to_layer,
        }

    burns = []
    sequence: list[dict[str, object]] = []
    if "dv1_vec" in result:
        v_depart = sub(v1, result["dv1_vec"])
        burns.append(
            {
                "km": depart_km,
                "dv_m_s": [v1[0] - v_depart[0], v1[1] - v_depart[1], v1[2] - v_depart[2]],
                "color": PALETTE["dv"],
                "label": "departure burn",
            }
        )
        sequence.append(circle_coast(norm(r1), frame["omega"] + nu0, -0.95, 0.0, PARK_WALL_S, "depart", "departure orbit"))
        sequence.append(burn_leg(0, "departure burn", "transfer", r1, v_depart, v1, "depart", "transfer"))
    if result["energy_class"] == "ellipse":
        sequence.append(
            {
                "kind": "coast",
                "label": "transfer",
                "layer": "transfer",
                "wall_s": COAST_WALL_S,
                "direct": True,
                "a": float(result["a_m"]),
                "e": frame["e"],
                "i": frame["i"],
                "Omega": frame["Omega"],
                "omega": frame["omega"],
                "p": frame["p"],
                "h": frame["h"],
                "mu": mu,
                "nu0": nu0,
                "nu1": nu0 + span,
            }
        )
    else:
        sequence.append(
            {
                "kind": "path",
                "label": "transfer",
                "layer": "transfer",
                "wall_s": COAST_WALL_S,
                "samples_km": [_km(point) for point in result["path_m"]],
            }
        )
    if "dv2_vec" in result:
        v_arrive = sub(v2, result["dv2_vec"])
        burns.append(
            {
                "km": arrive_km,
                "dv_m_s": [v_arrive[0] - v2[0], v_arrive[1] - v2[1], v_arrive[2] - v2[2]],
                "color": PALETTE["dv"],
                "label": "arrival burn",
            }
        )
        sequence.append(burn_leg(len(burns) - 1, "arrival burn", "arrive", r2, v2, v_arrive, "transfer", "arrive"))
        sequence.append(
            circle_coast(norm(r2), frame["omega"] + nu0 + span, 0.0, 2.0 * math.pi, ARRIVE_WALL_S, "arrive", "arrival orbit")
        )
    legend = [
        {"label": "planet", "swatch": "planet", "color": PALETTE["planet"], "edge": PALETTE["planet_edge"]},
    ]
    if "dv1_vec" in result:
        legend.append({"label": "departure orbit", "swatch": "line", "color": PALETTE["depart"], "edge": None})
    legend.append({"label": "transfer", "swatch": "line", "color": PALETTE["transfer"], "edge": None})
    if "dv2_vec" in result:
        legend.append({"label": "arrival orbit", "swatch": "line", "color": PALETTE["arrive"], "edge": None})
    legend.extend(
        [
            {"label": "departure", "swatch": "square", "color": "#27ae60", "edge": None},
            {"label": "arrival", "swatch": "circle", "color": PALETTE["arrive"], "edge": None},
            {"label": "spacecraft", "swatch": "circle", "color": PALETTE["craft"], "edge": None},
        ]
    )
    if burns:
        legend.append({"label": "delta-v", "swatch": "line", "color": PALETTE["dv"], "edge": None})
    return {
        "title": PLOT_TITLE,
        "elev_deg": VIEW_ELEV_DEG,
        "azim_deg": VIEW_AZIM_DEG,
        "roll_deg": 0.0,
        "limit_km": limit_m / 1000.0,
        "axis_length_km": axis_len / 1000.0,
        "equatorial_radius_km": body_radius / 1000.0,
        "polar_radius_km": body_radius * (1.0 - flattening) / 1000.0,
        "flattening": flattening,
        "planet_segments_u": 96,
        "planet_segments_v": 48,
        "planet_opacity": 0.52,
        "ring_km": ring,
        "spokes_km": spokes,
        "equator_km": equator,
        "axes": axes,
        "velocity_length_km": 0.10 * span_m / 1000.0,
        "layers": layers,
        "markers": markers,
        "craft_km": depart_km,
        "burns": burns,
        "legend": legend,
        "palette": PALETTE,
        "sequence": sequence,
    }


def write_viewer_html(path: Path, payload: dict[str, object]) -> None:
    viewer_dir = SKILL_DIR / "viewer"
    try:
        template = (viewer_dir / "template.html").read_text(encoding="utf-8")
        three_source = (viewer_dir / "three.min.js").read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read the viewer template: {exc}") from exc
    if "</script>" in three_source.lower():
        three_source = three_source.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    before, placeholder, after = template.partition("__THREE_SOURCE__")
    if not placeholder or "__SCENE_JSON__" not in after:
        raise ValueError("viewer template is missing a placeholder")
    before = before.replace("__TITLE__", PLOT_TITLE).replace("__AXIS_CAPTION__", "X, Y, Z (km)")
    after = (
        after.replace("__TITLE__", PLOT_TITLE)
        .replace("__AXIS_CAPTION__", "X, Y, Z (km)")
        .replace("__SCENE_JSON__", encoded)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(before + three_source + after, encoding="utf-8")


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    mu = 1.0
    radius = 1.0
    quarter_tof = (math.pi / 2.0) * math.sqrt(radius**3 / mu)
    quarter = solve((radius, 0.0, 0.0), (0.0, radius, 0.0), quarter_tof, mu, "short", None, None)
    speed = math.sqrt(mu / radius)
    if not close(float(quarter["v1y_m_s"]), speed) or not close(float(quarter["v1x_m_s"]), 0.0):
        return fail("quarter-circle departure velocity is not tangential")
    if not close(float(quarter["v2x_m_s"]), -speed) or not close(float(quarter["v2y_m_s"]), 0.0):
        return fail("quarter-circle arrival velocity is not tangential")
    if quarter["energy_class"] != "ellipse" or not close(float(quarter["e"]), 0.0, 1e-6):
        return fail("quarter-circle transfer is not circular")
    if not close(float(quarter["a_m"]), radius):
        return fail("quarter-circle semimajor axis is not the radius")
    half_tof = math.pi * math.sqrt(radius**3 / mu)
    half = solve((radius, 0.0, 0.0), (-radius, 0.0, 0.0), half_tof, mu, "short", None, None)
    if not close(float(half["v1z_m_s"]), speed) or not close(float(half["v1x_m_s"]), 0.0):
        return fail("half-period 180 degree departure is not the circular speed")
    if not close(float(half["v2z_m_s"]), -speed) or not close(float(half["e"]), 0.0, 1e-6):
        return fail("half-period 180 degree arrival is not circular")
    c_val, s_val = stumpff(math.pi**2)
    if not close(c_val, 2.0 / math.pi**2, 1e-12) or not close(s_val, 1.0 / math.pi**2, 1e-12):
        return fail("Stumpff values at pi^2 are wrong")
    mu_e = G0 * R0_EARTH**2
    r_peri = 7000.0e3
    r_apo = 14000.0e3
    semimajor = 0.5 * (r_peri + r_apo)
    hohmann_tof = math.pi * math.sqrt(semimajor**3 / mu_e)
    hohmann = solve((r_peri, 0.0, 0.0), (-r_apo, 0.0, 0.0), hohmann_tof, mu_e, "short", None, None)
    v_peri = math.sqrt(mu_e * (2.0 / r_peri - 1.0 / semimajor))
    v_apo = math.sqrt(mu_e * (2.0 / r_apo - 1.0 / semimajor))
    if not close(float(hohmann["v1z_m_s"]), v_peri, 1e-6) or not close(float(hohmann["v1x_m_s"]), 0.0, 1e-8):
        return fail("180 degree departure speed is not the Hohmann periapsis speed")
    if not close(float(hohmann["v2z_m_s"]), -v_apo, 1e-6):
        return fail("180 degree arrival speed is not the Hohmann apoapsis speed")
    if not close(float(hohmann["e"]), (r_apo - r_peri) / (r_apo + r_peri), 1e-5):
        return fail("180 degree eccentricity is not the Hohmann eccentricity")
    raised = solve(
        (r_peri, 0.0, 0.0),
        (-r_apo, 0.0, 0.0),
        hohmann_tof,
        mu_e,
        "short",
        math.sqrt(mu_e / r_peri),
        math.sqrt(mu_e / r_apo),
    )
    raised_scene = scene_payload(raised)
    labels = [str(leg["label"]) for leg in raised_scene["sequence"]]
    if labels != ["departure orbit", "departure burn", "transfer", "arrival burn", "arrival orbit"]:
        return fail("a parking transfer did not show both burns and both orbits")
    depart = raised_scene["sequence"][0]
    depart_end = perifocal_point(float(depart["p"]), float(depart["nu1"]), float(depart["i"]), float(depart["Omega"]), float(depart["omega"]))
    if not close(depart_end[0], r_peri, 1e-6) or not close(depart_end[1], 0.0, 1e-6):
        return fail("the departure coast does not end on the first position")
    depart_burn = raised_scene["sequence"][1]
    arrive_burn = raised_scene["sequence"][3]
    r_depart = (r_peri, 0.0, 0.0)
    r_arrive = (-r_apo, 0.0, 0.0)
    if float(conic(r_depart, tuple(depart_burn["v_from"]), mu_e)["e"]) > 1.0e-5:
        return fail("departure burn does not start on the circular orbit")
    if not close(float(conic(r_depart, tuple(depart_burn["v_to"]), mu_e)["e"]), 1.0 / 3.0, 1.0e-4):
        return fail("departure burn does not end on the transfer")
    if not close(float(conic(r_arrive, tuple(arrive_burn["v_from"]), mu_e)["e"]), 1.0 / 3.0, 1.0e-4):
        return fail("arrival burn does not start on the transfer")
    if float(conic(r_arrive, tuple(arrive_burn["v_to"]), mu_e)["e"]) > 1.0e-5:
        return fail("arrival burn does not end on the circular orbit")
    mid_v = tuple(0.5 * (left + right) for left, right in zip(depart_burn["v_from"], depart_burn["v_to"]))
    mid = conic(r_depart, mid_v, mu_e)
    if not (0.05 < float(mid["e"]) < 0.28):
        return fail("the departure burn does not pass through a midway ellipse")
    if depart_burn.get("from_layer") != "depart" or arrive_burn.get("to_layer") != "arrive":
        return fail("burn morph is missing its orbit layers")
    epoch_km, _epoch_velocity, epoch_label = epoch_state(raised_scene)
    epoch_m = (epoch_km[0] * 1000.0, epoch_km[1] * 1000.0, epoch_km[2] * 1000.0)
    if epoch_label != "departure orbit" or not close(norm(epoch_m), r_peri, 1.0e-4) or epoch_m[2] >= 0.0:
        return fail("PNG epoch is not the spacecraft before the departure burn")
    try:
        velocities((1.0, 0.0, 0.0), (1.0000001, 0.0, 0.0), 0.1, 1.0, "short")
        return fail("a vanishing transfer angle was accepted")
    except ValueError:
        pass
    try:
        velocities((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.01, 1.0, "short")
        return fail("a time of flight below the single-revolution branch was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        html = Path(folder) / "check.html"
        scene = scene_payload(quarter)
        write_plot(path, scene)
        write_viewer_html(html, scene)
        text = html.read_text(encoding="utf-8")
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
        if (
            PLOT_TITLE not in text
            or "__THREE_SOURCE__" in text
            or "__SCENE_JSON__" in text
            or "__AXIS_CAPTION__" in text
            or "Reset camera" not in text
        ):
            return fail("viewer placeholders were not filled")
        if scene["title"] != PLOT_TITLE or not scene["layers"] or scene["sequence"][0]["kind"] != "coast":
            return fail("viewer scene is missing the orbit coast")
        if len(scene["layers"][0]["polylines"][0]) < 100:
            return fail("transfer ellipse was not sampled")
    print("check: pass")
    print_kv("v1y_quarter", quarter["v1y_m_s"])
    print_kv("v_peri_hohmann", hohmann["v1z_m_s"])
    return 0


def parse_vector(args: argparse.Namespace, prefix: str) -> Vec:
    values = [getattr(args, f"{prefix}{axis}") for axis in ("x", "y", "z")]
    if any(value is None for value in values):
        raise ValueError(f"requires --{prefix}x, --{prefix}y, and --{prefix}z")
    if any(not math.isfinite(value) for value in values):
        raise ValueError(f"{prefix} components must be finite")
    return (float(values[0]), float(values[1]), float(values[2]))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-revolution Lambert transfer.")
    parser.add_argument("--r1x", type=float, default=None, help="r1 x component [m]")
    parser.add_argument("--r1y", type=float, default=None, help="r1 y component [m]")
    parser.add_argument("--r1z", type=float, default=None, help="r1 z component [m]")
    parser.add_argument("--r2x", type=float, default=None, help="r2 x component [m]")
    parser.add_argument("--r2y", type=float, default=None, help="r2 y component [m]")
    parser.add_argument("--r2z", type=float, default=None, help="r2 z component [m]")
    parser.add_argument("--tof", type=float, default=None, help="time of flight [s]")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter [m^3/s^2]")
    parser.add_argument("--R0", type=float, default=None, help="planetary radius used only for the default mu [m]")
    parser.add_argument("--way", choices=("short", "long"), default="short", help="short or long way")
    parser.add_argument("--v1circ", type=float, default=None, help="parking circular speed at r1 [m/s]")
    parser.add_argument("--v2circ", type=float, default=None, help="parking circular speed at r2 [m/s]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--html", action="store_true", help="write the optional HTML 3D viewer beside the PNG")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def gravitational_parameter(args: argparse.Namespace) -> tuple[float, str]:
    if args.mu is not None:
        if args.R0 is not None:
            raise ValueError("pass --mu or --R0, not both")
        return args.mu, "flag"
    radius = R0_EARTH if args.R0 is None else args.R0
    if radius <= 0.0 or not math.isfinite(radius):
        raise ValueError("--R0 must be finite and > 0")
    source = "earth_default" if args.R0 is None else "R0"
    return G0 * radius * radius, source


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        r1 = parse_vector(args, "r1")
        r2 = parse_vector(args, "r2")
        if args.tof is None:
            raise ValueError("requires --tof")
        mu, mu_source = gravitational_parameter(args)
        result = solve(r1, r2, args.tof, mu, args.way, args.v1circ, args.v2circ)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "lambert_transfer.png"
    html_path = out_path.with_suffix(".html") if args.html or args.open else None
    try:
        scene = scene_payload(result)
        write_plot(out_path, scene)
        if html_path is not None:
            write_viewer_html(html_path, scene)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path, html_path, mu_source)
    if args.open and html_path is not None:
        import webbrowser

        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
