#!/usr/bin/env python3
"""Classical orbital elements and the inertial state of a Keplerian conic.

Energy, period, radii, anomalies, angular momentum, inclination, node,
argument of latitude, and the inertial position and velocity come from the
flight records in formulas.md. Oblateness is drawn only; it does not enter mu.
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

# Earth values from formulas.md. R0 is the reference radius in mu = g0*R0^2.
# g0 is standard sea-level gravity. Flattening is the visual polar squash only.
G0 = 9.80665
R0_EARTH = 6.3742e6
F_EARTH = 1.0 / 298.257
PLOT_TITLE = "ASTRO - OrbitalParameters"
PNG_AXIS_LABELS = ("X (km)", "Y (km)", "Z (km)")
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
CHECK_TOL = 1e-9
ANGLE_TOL = 1e-8
CIRCULAR_E = 1e-7
EQUATORIAL_FRAC = 1e-10
PARABOLA_REL = 1e-10
ELEV_DEG = 20.0
AZIM_DEG = 35.0
# Matplotlib roll. At elev = 90, screen-up lies along the azimuth and
# screen-right is that axis turned 90 degrees clockwise about the view.
CAMERA_ROLL_DEG = 0.0
ELLIPSE_WALL_S = 8.0
OPEN_ARC_WALL_S = 6.0
PLANET_SEGMENTS_U = 96
PLANET_SEGMENTS_V = 48
LIMIT_SPAN_FRAC = 1.16
ARROW_SPAN_FRAC = 0.10
WEDGE_INCLINATION = 1e-3
WEDGE_STEPS = 36
PALETTE = {
    "planet": "#c5ddef",
    "planet_edge": "#1a5276",
    "equator": "#7eb6e0",
    "equator_spoke": "#a9d2ef",
    "equator_limb": "#1a5276",
    "orbit": "#1a5276",
    "node": "#d68910",
    "wedge": "#d2b4de",
    "wedge_edge": "#6c3483",
    "periapsis": "#117a65",
    "apoapsis": "#6c3483",
    "radius": "#922b21",
    "velocity": "#2471a3",
    "craft": "#c0392b",
    "axis": "#1a5276",
    "text": "#1b2631",
    "caption": "#34495e",
    "pane": "#f7f9fb",
}
ASSUMPTIONS = (
    "spherical inverse-square two-body gravity; planetary flattening is visual "
    "only and does not enter mu or the state; mu = g0*R0^2 with g0 = 9.80665 m/s^2; "
    "Earth default R0 = 6374200 m and visual flattening 1/298.257; any other R0 is a "
    "sphere unless --flattening is set; the frame is planet-centered inertial with "
    "+Z along the polar axis, the XY plane equatorial, and Omega measured from +X "
    "to the ascending node; specific energy is specific_orbital_energy and "
    "specific_orbital_energy_from_speed; semi-major axis is semimajor_axis_from_energy; "
    "eccentricity is eccentricity_from_energy; semi-latus rectum is semi_latus_rectum "
    "on an ellipse or hyperbola and parameter_from_angular_momentum from the state; "
    "radius is conic_radius_from_parameter; periapsis on an ellipse or hyperbola is "
    "periapsis_radius; apoapsis is apoapsis_radius and the period is orbital_period, "
    "both only on an ellipse; h is specific_angular_momentum with components "
    "specific_angular_momentum_x, specific_angular_momentum_y, and "
    "specific_angular_momentum_z; inclination is inclination; the node uses "
    "ascending_node_sine and ascending_node_cosine, and Omega is 0 when the orbit "
    "is equatorial (i = 0 or i = pi); argument of latitude is argument_of_latitude, "
    "and from a state it is argument_of_latitude_cosine and argument_of_latitude_sine, "
    "or equatorial_argument_cosine and equatorial_argument_sine when i = 0; a "
    "retrograde equator uses the inertial position formulas with Omega = 0; "
    "argument of periapsis is argument_of_periapsis, and omega is 0 when e < 1e-7; on a "
    "circle the mean anomaly equals the argument of latitude; true anomaly from a "
    "state uses true_anomaly_cosine_from_state and the sign of position_velocity_dot; "
    "ellipse anomalies use kepler_equation, true_anomaly_sine, true_anomaly_cosine, "
    "eccentric_anomaly_sine, and eccentric_anomaly_cosine; --M is ellipse-only; "
    "inertial position is inertial_position_x, inertial_position_y, and "
    "inertial_position_z; ellipse velocity uses radial_velocity_eccentric and "
    "transverse_velocity_eccentric; hyperbola velocity uses vis_viva with "
    "radial_velocity and transverse_velocity; inertial velocity is inertial_velocity_x, "
    "inertial_velocity_y, and inertial_velocity_z; a parabola has no finite semi-major "
    "axis, no period, and no apoapsis; element angles are radians"
)


@dataclass(frozen=True)
class Body:
    radius: float
    g0: float
    mu: float
    flattening: float
    radius_source: str


@dataclass(frozen=True)
class Orbit:
    mode: str
    conic: str
    a: float | None
    e: float
    i: float
    Omega: float
    omega: float
    nu: float
    M: float | None
    p: float
    energy: float
    h: float
    hx: float
    hy: float
    hz: float
    rp: float
    ra: float | None
    period: float | None
    rx: float
    ry: float
    rz: float
    vx: float
    vy: float
    vz: float


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


def wrap_two_pi(angle: float) -> float:
    """Fold an angle into [0, 2*pi)."""
    twopi = 2.0 * math.pi
    wrapped = math.fmod(angle, twopi)
    if wrapped < 0.0:
        wrapped += twopi
    if wrapped >= twopi or wrapped < 1e-15:
        return 0.0
    return wrapped


def wrap_pi(angle: float) -> float:
    """Fold an angle into (-pi, pi]."""
    wrapped = wrap_two_pi(angle)
    if wrapped > math.pi:
        wrapped -= 2.0 * math.pi
    return wrapped


def specific_orbital_energy(mu: float, semi_major: float) -> float:
    """specific_orbital_energy."""
    return -(mu) / (2.0 * semi_major)


def specific_orbital_energy_from_speed(speed: float, mu: float, radius: float) -> float:
    """specific_orbital_energy_from_speed."""
    return speed**2 / 2.0 - mu / radius


def semimajor_axis_from_energy(mu: float, energy: float) -> float:
    """semimajor_axis_from_energy."""
    return -mu / (2.0 * energy)


def eccentricity_from_energy(energy: float, h: float, mu: float) -> float:
    """eccentricity_from_energy. A tiny negative radicand is roundoff."""
    radicand = 1.0 + 2.0 * energy * h**2 / mu**2
    if radicand < 0.0:
        if radicand > -1e-9:
            return 0.0
        raise ValueError("eccentricity is not real for this state")
    return math.sqrt(radicand)


def semi_latus_rectum(semi_major: float, eccentricity: float) -> float:
    """semi_latus_rectum. The same product is positive on a hyperbola with a < 0."""
    return semi_major * (1.0 - eccentricity**2)


def parameter_from_angular_momentum(h: float, mu: float) -> float:
    """parameter_from_angular_momentum."""
    return h**2 / mu


def specific_angular_momentum(mu: float, parameter: float) -> float:
    """specific_angular_momentum."""
    return math.sqrt(mu * parameter)


def conic_radius_from_parameter(parameter: float, eccentricity: float, nu: float) -> float:
    """conic_radius_from_parameter."""
    return parameter / (1.0 + eccentricity * math.cos(nu))


def periapsis_radius(semi_major: float, eccentricity: float) -> float:
    """periapsis_radius."""
    return semi_major * (1.0 - eccentricity)


def apoapsis_radius(semi_major: float, eccentricity: float) -> float:
    """apoapsis_radius."""
    return semi_major * (1.0 + eccentricity)


def orbital_period(mu: float, semi_major: float) -> float:
    """orbital_period."""
    return 2.0 * math.pi * math.sqrt(semi_major**3 / mu)


def kepler_equation(eccentric_anomaly: float, eccentricity: float) -> float:
    """kepler_equation."""
    return eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)


def true_anomaly_cosine(eccentric_anomaly: float, eccentricity: float) -> float:
    """true_anomaly_cosine."""
    return (math.cos(eccentric_anomaly) - eccentricity) / (
        1.0 - eccentricity * math.cos(eccentric_anomaly)
    )


def true_anomaly_sine(eccentric_anomaly: float, eccentricity: float) -> float:
    """true_anomaly_sine."""
    return (
        math.sqrt(1.0 - eccentricity**2)
        * math.sin(eccentric_anomaly)
        / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    )


def eccentric_anomaly_cosine(eccentricity: float, nu: float) -> float:
    """eccentric_anomaly_cosine."""
    return (eccentricity + math.cos(nu)) / (1.0 + eccentricity * math.cos(nu))


def eccentric_anomaly_sine(eccentricity: float, nu: float) -> float:
    """eccentric_anomaly_sine."""
    return (
        math.sqrt(1.0 - eccentricity**2)
        * math.sin(nu)
        / (1.0 + eccentricity * math.cos(nu))
    )


def argument_of_latitude(omega: float, nu: float) -> float:
    """argument_of_latitude."""
    return omega + nu


def specific_angular_momentum_x(y: float, vz: float, z: float, vy: float) -> float:
    """specific_angular_momentum_x."""
    return y * vz - z * vy


def specific_angular_momentum_y(z: float, vx: float, x: float, vz: float) -> float:
    """specific_angular_momentum_y."""
    return z * vx - x * vz


def specific_angular_momentum_z(x: float, vy: float, y: float, vx: float) -> float:
    """specific_angular_momentum_z."""
    return x * vy - y * vx


def specific_angular_momentum_magnitude(hx: float, hy: float, hz: float) -> float:
    """specific_angular_momentum_magnitude."""
    return math.sqrt(hx**2 + hy**2 + hz**2)


def position_velocity_dot(
    x: float, vx: float, y: float, vy: float, z: float, vz: float
) -> float:
    """position_velocity_dot."""
    return x * vx + y * vy + z * vz


def inclination(hz: float, h: float) -> float:
    """inclination. Clamp only a roundoff step past the ends of asin."""
    ratio = hz / h
    if ratio > 1.0 or ratio < -1.0:
        if abs(ratio) - 1.0 > 1e-10:
            raise ValueError("inclination argument is outside [-1, 1]")
        ratio = math.copysign(1.0, ratio)
    return math.pi / 2.0 - math.asin(ratio)


def ascending_node_sine(hx: float, hy: float) -> float:
    """ascending_node_sine."""
    return hx / math.sqrt(hx**2 + hy**2)


def ascending_node_cosine(hx: float, hy: float) -> float:
    """ascending_node_cosine."""
    return -hy / math.sqrt(hx**2 + hy**2)


def true_anomaly_cosine_from_state(h: float, radius: float, mu: float, eccentricity: float) -> float:
    """true_anomaly_cosine_from_state."""
    return (h**2 / radius - mu) / (mu * eccentricity)


def argument_of_latitude_cosine(x: float, Omega: float, y: float, radius: float) -> float:
    """argument_of_latitude_cosine."""
    return (x * math.cos(Omega) + y * math.sin(Omega)) / radius


def argument_of_latitude_sine(z: float, radius: float, inc: float) -> float:
    """argument_of_latitude_sine."""
    return z / (radius * math.sin(inc))


def equatorial_argument_cosine(x: float, radius: float) -> float:
    """equatorial_argument_cosine."""
    return x / radius


def equatorial_argument_sine(y: float, radius: float) -> float:
    """equatorial_argument_sine."""
    return y / radius


def argument_of_periapsis(argument: float, nu: float) -> float:
    """argument_of_periapsis."""
    return argument - nu


def inertial_position_x(radius: float, Omega: float, argument: float, inc: float) -> float:
    """inertial_position_x."""
    return radius * (
        math.cos(Omega) * math.cos(argument)
        - math.sin(Omega) * math.cos(inc) * math.sin(argument)
    )


def inertial_position_y(radius: float, Omega: float, argument: float, inc: float) -> float:
    """inertial_position_y."""
    return radius * (
        math.sin(Omega) * math.cos(argument)
        + math.cos(Omega) * math.cos(inc) * math.sin(argument)
    )


def inertial_position_z(radius: float, inc: float, argument: float) -> float:
    """inertial_position_z."""
    return radius * math.sin(inc) * math.sin(argument)


def radial_velocity_eccentric(
    mu: float, semi_major: float, eccentricity: float, eccentric_anomaly: float, radius: float
) -> float:
    """radial_velocity_eccentric."""
    return math.sqrt(mu * semi_major) * eccentricity * math.sin(eccentric_anomaly) / radius


def transverse_velocity_eccentric(
    mu: float, semi_major: float, eccentricity: float, radius: float
) -> float:
    """transverse_velocity_eccentric."""
    return math.sqrt(mu * semi_major) * math.sqrt(1.0 - eccentricity**2) / radius


def radial_velocity(speed: float, gamma: float) -> float:
    """radial_velocity."""
    return speed * math.sin(gamma)


def transverse_velocity(speed: float, gamma: float) -> float:
    """transverse_velocity."""
    return speed * math.cos(gamma)


def inertial_velocity_x(
    vr: float,
    radius: float,
    x: float,
    vp: float,
    Omega: float,
    argument: float,
    inc: float,
) -> float:
    """inertial_velocity_x."""
    return (vr / radius) * x - vp * (
        math.cos(Omega) * math.sin(argument)
        + math.sin(Omega) * math.cos(inc) * math.cos(argument)
    )


def inertial_velocity_y(
    vr: float,
    radius: float,
    y: float,
    vp: float,
    Omega: float,
    argument: float,
    inc: float,
) -> float:
    """inertial_velocity_y."""
    return (vr / radius) * y + vp * (
        -math.sin(Omega) * math.sin(argument)
        + math.cos(Omega) * math.cos(inc) * math.cos(argument)
    )


def inertial_velocity_z(
    vr: float, radius: float, z: float, vp: float, inc: float, argument: float
) -> float:
    """inertial_velocity_z."""
    return (vr / radius) * z + vp * math.sin(inc) * math.cos(argument)


def vis_viva(mu: float, radius: float, semi_major: float) -> float:
    """vis_viva."""
    argument = mu * (2.0 / radius - 1.0 / semi_major)
    scale = mu / radius
    if argument < 0.0:
        if argument > -1e-9 * scale:
            argument = 0.0
        else:
            raise ValueError("orbital speed is not real at that radius")
    return math.sqrt(argument)


def nu_from_eccentric(eccentricity: float, eccentric_anomaly: float) -> float:
    """True anomaly from true_anomaly_sine and true_anomaly_cosine."""
    return math.atan2(
        true_anomaly_sine(eccentric_anomaly, eccentricity),
        true_anomaly_cosine(eccentric_anomaly, eccentricity),
    )


def eccentric_from_true(eccentricity: float, nu: float) -> float:
    """Eccentric anomaly from eccentric_anomaly_sine and eccentric_anomaly_cosine."""
    return math.atan2(
        eccentric_anomaly_sine(eccentricity, nu),
        eccentric_anomaly_cosine(eccentricity, nu),
    )


def solve_kepler(mean_anomaly: float, eccentricity: float) -> float:
    """Eccentric anomaly from kepler_equation, by Halley iteration on that residual."""
    mean = wrap_pi(mean_anomaly)
    if eccentricity == 0.0:
        return mean
    eccentric = mean + eccentricity * math.sin(mean)
    for _ in range(50):
        residual = kepler_equation(eccentric, eccentricity) - mean
        slope = 1.0 - eccentricity * math.cos(eccentric)
        if abs(residual) <= 1e-14:
            return eccentric
        if abs(slope) < 1e-14:
            raise ValueError("Kepler equation did not converge")
        curve = eccentricity * math.sin(eccentric)
        denom = slope - residual * curve / (2.0 * slope)
        if denom == 0.0 or not math.isfinite(denom):
            raise ValueError("Kepler equation did not converge")
        step = residual / denom
        eccentric -= step
        if abs(step) <= 1e-14:
            return eccentric
    raise ValueError("Kepler equation did not converge")


def open_flight_path_angle(radius: float, speed: float, h: float, nu: float) -> float:
    """Flight-path angle on a hyperbola.

    cos(gamma) is the rearrangement of specific_angular_momentum_flight_path,
    h = r*v*cos(gamma). sin(gamma) has the sign of sin(nu), because true anomaly
    is zero at periapsis and increases with the motion, so the radius is
    increasing when sin(nu) is positive.
    """
    cosine = h / (radius * speed)
    if cosine > 1.0 or cosine < -1.0:
        if abs(cosine) - 1.0 > 1e-8:
            raise ValueError("flight-path cosine is outside [-1, 1]")
        cosine = math.copysign(1.0, cosine)
    sine = math.copysign(math.sqrt(max(0.0, 1.0 - cosine * cosine)), math.sin(nu))
    return math.atan2(sine, cosine)


def conic_kind(semi_major: float, eccentricity: float) -> str:
    """Ellipse, parabola, or hyperbola, or a ValueError when a and e disagree."""
    if eccentricity < 0.0:
        raise ValueError("--e must be >= 0")
    if eccentricity < 1.0:
        if semi_major <= 0.0:
            raise ValueError("an ellipse needs --a > 0 m")
        return "ellipse"
    if eccentricity == 1.0:
        raise ValueError(
            "a parabola has no finite semi-major axis; "
            "pass --rx --ry --rz --vx --vy --vz"
        )
    if semi_major >= 0.0:
        raise ValueError("a hyperbola needs --a < 0 m")
    return "hyperbola"


def state_from_elements(
    mu: float,
    semi_major: float,
    eccentricity: float,
    inc: float,
    Omega: float,
    omega: float,
    nu: float,
) -> tuple[float, float, float, float, float, float]:
    """Inertial position and velocity from classical elements."""
    nu = wrap_pi(nu)
    Omega = wrap_two_pi(Omega)
    omega = wrap_two_pi(omega)
    kind = conic_kind(semi_major, eccentricity)
    if kind == "hyperbola":
        asymptote = math.acos(-1.0 / eccentricity)
        if abs(nu) >= asymptote:
            raise ValueError("true anomaly is at or beyond the hyperbola asymptote")
    parameter = semi_latus_rectum(semi_major, eccentricity)
    if parameter <= 0.0:
        raise ValueError("semi-latus rectum must be positive")
    radius = conic_radius_from_parameter(parameter, eccentricity, nu)
    if radius <= 0.0 or not math.isfinite(radius):
        raise ValueError("true anomaly is at or beyond the asymptote")
    argument = argument_of_latitude(omega, nu)
    x = inertial_position_x(radius, Omega, argument, inc)
    y = inertial_position_y(radius, Omega, argument, inc)
    z = inertial_position_z(radius, inc, argument)
    if kind == "ellipse":
        eccentric_anomaly = eccentric_from_true(eccentricity, nu)
        vr = radial_velocity_eccentric(mu, semi_major, eccentricity, eccentric_anomaly, radius)
        vp = transverse_velocity_eccentric(mu, semi_major, eccentricity, radius)
    else:
        speed = vis_viva(mu, radius, semi_major)
        h = specific_angular_momentum(mu, parameter)
        gamma = open_flight_path_angle(radius, speed, h, nu)
        vr = radial_velocity(speed, gamma)
        vp = transverse_velocity(speed, gamma)
    vx = inertial_velocity_x(vr, radius, x, vp, Omega, argument, inc)
    vy = inertial_velocity_y(vr, radius, y, vp, Omega, argument, inc)
    vz = inertial_velocity_z(vr, radius, z, vp, inc, argument)
    return x, y, z, vx, vy, vz


def true_anomaly_from_state(
    h: float, radius: float, mu: float, eccentricity: float, radial_momentum: float, speed: float
) -> float:
    """True anomaly from true_anomaly_cosine_from_state and the sign of r·v."""
    cosine = true_anomaly_cosine_from_state(h, radius, mu, eccentricity)
    if cosine > 1.0 or cosine < -1.0:
        if abs(cosine) - 1.0 > 1e-8:
            raise ValueError("true anomaly cosine is outside [-1, 1]")
        cosine = math.copysign(1.0, cosine)
    sine_magnitude = math.sqrt(max(0.0, 1.0 - cosine * cosine))
    if abs(radial_momentum) <= 1e-12 * radius * max(speed, 1.0):
        sine = 0.0
    else:
        sine = math.copysign(sine_magnitude, radial_momentum)
    return math.atan2(sine, cosine)


def argument_from_state(
    x: float, y: float, z: float, radius: float, inc: float, Omega: float, hz: float
) -> float:
    """Argument of latitude, with the equatorial conventions."""
    if abs(math.sin(inc)) <= EQUATORIAL_FRAC:
        if hz >= 0.0:
            cosine = equatorial_argument_cosine(x, radius)
            sine = equatorial_argument_sine(y, radius)
        else:
            # i = pi. inertial_position with Omega = 0 gives x/r = cos(u), y/r = -sin(u).
            cosine = x / radius
            sine = -y / radius
        return math.atan2(sine, cosine)
    cosine = argument_of_latitude_cosine(x, Omega, y, radius)
    sine = argument_of_latitude_sine(z, radius, inc)
    return math.atan2(sine, cosine)


def orbit_from_state(
    mu: float,
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
    mode: str,
) -> Orbit:
    """Classical elements from an inertial state. Singular angles follow ELCONO."""
    for value, flag in (
        (x, "--rx"),
        (y, "--ry"),
        (z, "--rz"),
        (vx, "--vx"),
        (vy, "--vy"),
        (vz, "--vz"),
    ):
        require_finite(value, flag)
    radius = math.sqrt(x**2 + y**2 + z**2)
    if radius == 0.0:
        raise ValueError("position is at the attracting centre")
    hx = specific_angular_momentum_x(y, vz, z, vy)
    hy = specific_angular_momentum_y(z, vx, x, vz)
    hz = specific_angular_momentum_z(x, vy, y, vx)
    h = specific_angular_momentum_magnitude(hx, hy, hz)
    if h == 0.0:
        raise ValueError(
            "specific angular momentum is zero; the path does not define an orbit plane"
        )
    speed = math.sqrt(vx**2 + vy**2 + vz**2)
    energy = specific_orbital_energy_from_speed(speed, mu, radius)
    if abs(energy) <= PARABOLA_REL * (mu / radius):
        kind = "parabola"
        semi_major = None
        eccentricity = 1.0
    else:
        semi_major = semimajor_axis_from_energy(mu, energy)
        if not math.isfinite(semi_major) or semi_major == 0.0:
            raise ValueError("semi-major axis is not finite")
        eccentricity = eccentricity_from_energy(energy, h, mu)
        kind = "ellipse" if energy < 0.0 else "hyperbola"
    parameter = parameter_from_angular_momentum(h, mu)
    inc = inclination(hz, h)
    horizontal = math.hypot(hx, hy)
    if horizontal <= EQUATORIAL_FRAC * h:
        Omega = 0.0
    else:
        Omega = wrap_two_pi(math.atan2(ascending_node_sine(hx, hy), ascending_node_cosine(hx, hy)))
    argument = argument_from_state(x, y, z, radius, inc, Omega, hz)
    if kind == "ellipse" and eccentricity < CIRCULAR_E:
        eccentricity = 0.0
        omega = 0.0
        nu = wrap_pi(argument)
        mean = nu
    elif eccentricity == 0.0:
        omega = 0.0
        nu = wrap_pi(argument)
        mean = nu if kind == "ellipse" else None
    else:
        radial_momentum = position_velocity_dot(x, vx, y, vy, z, vz)
        nu = true_anomaly_from_state(h, radius, mu, eccentricity, radial_momentum, speed)
        omega = wrap_two_pi(argument_of_periapsis(argument, nu))
        if kind == "ellipse":
            mean = wrap_pi(kepler_equation(eccentric_from_true(eccentricity, nu), eccentricity))
        else:
            mean = None
    if kind == "ellipse" and semi_major is not None:
        rp = periapsis_radius(semi_major, eccentricity)
        ra = apoapsis_radius(semi_major, eccentricity)
        period = orbital_period(mu, semi_major)
    elif kind == "hyperbola" and semi_major is not None:
        rp = periapsis_radius(semi_major, eccentricity)
        ra = None
        period = None
    else:
        rp = conic_radius_from_parameter(parameter, eccentricity, 0.0)
        ra = None
        period = None
    if rp <= 0.0 or not math.isfinite(rp):
        raise ValueError("periapsis radius is not positive")
    return Orbit(
        mode=mode,
        conic=kind,
        a=semi_major,
        e=eccentricity,
        i=inc,
        Omega=Omega,
        omega=omega,
        nu=nu,
        M=mean,
        p=parameter,
        energy=energy,
        h=h,
        hx=hx,
        hy=hy,
        hz=hz,
        rp=rp,
        ra=ra,
        period=period,
        rx=x,
        ry=y,
        rz=z,
        vx=vx,
        vy=vy,
        vz=vz,
    )


def orbit_from_elements(
    mu: float,
    semi_major: float,
    eccentricity: float,
    inc: float,
    Omega: float,
    omega: float,
    nu: float | None,
    mean_anomaly: float | None,
    mode: str,
) -> Orbit:
    """Elements to a state, then back to the singular-case conventions."""
    for value, flag in (
        (semi_major, "--a"),
        (eccentricity, "--e"),
        (inc, "--i"),
        (Omega, "--raan"),
        (omega, "--aop"),
    ):
        require_finite(value, flag)
    if inc < 0.0 or inc > math.pi:
        raise ValueError("--i must satisfy 0 <= i <= pi radians")
    kind = conic_kind(semi_major, eccentricity)
    if mean_anomaly is not None:
        require_finite(mean_anomaly, "--M")
        if kind != "ellipse":
            raise ValueError("--M is defined only on an ellipse")
        eccentric_anomaly = solve_kepler(mean_anomaly, eccentricity)
        nu = nu_from_eccentric(eccentricity, eccentric_anomaly)
    if nu is None:
        raise ValueError("pass exactly one of --nu or --M")
    require_finite(nu, "--nu")
    x, y, z, vx, vy, vz = state_from_elements(
        mu, semi_major, eccentricity, inc, Omega, omega, nu
    )
    return orbit_from_state(mu, x, y, z, vx, vy, vz, mode)


def surface_warning(body: Body, orbit: Orbit) -> str | None:
    if orbit.rp < body.radius and not math.isclose(orbit.rp, body.radius, rel_tol=1e-12, abs_tol=0.0):
        return (
            "periapsis is inside the planetary radius; the conic is unchanged "
            "and flattening is visual only"
        )
    return None


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import mpl_toolkits.mplot3d  # noqa: F401
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the orbit") from exc
    return plt


def display_span_m(body: Body, orbit: Orbit) -> float:
    craft = math.sqrt(orbit.rx**2 + orbit.ry**2 + orbit.rz**2)
    span = max(body.radius, orbit.rp, craft)
    if orbit.ra is not None:
        span = max(span, orbit.ra)
    if orbit.conic != "ellipse":
        span = max(span, 3.0 * orbit.rp)
    return span


def sample_true_anomalies(orbit: Orbit, span: float) -> list[float]:
    if orbit.conic == "ellipse" or orbit.e == 0.0:
        return linspace(0.0, 2.0 * math.pi, 361)
    asymptote = math.pi if orbit.e == 1.0 else math.acos(-1.0 / orbit.e)
    cos_limit = (orbit.p / span - 1.0) / orbit.e
    cos_limit = min(1.0, max(-1.0, cos_limit))
    reach = math.acos(cos_limit)
    limit = min(0.985 * asymptote, reach)
    if limit < 0.05:
        limit = min(0.5 * asymptote, 0.5)
    return linspace(-limit, limit, 241)


def _rotate_about(
    vector: tuple[float, float, float], axis: tuple[float, float, float], angle: float
) -> tuple[float, float, float]:
    """Rotate vector about a unit axis. Same matrix as matplotlib's view roll."""
    vx, vy, vz = vector
    ax, ay, az = axis
    cosine = math.cos(angle)
    sine = math.sin(angle)
    tilt = 1.0 - cosine
    return (
        (tilt * ax * ax + cosine) * vx
        + (tilt * ax * ay - az * sine) * vy
        + (tilt * ax * az + ay * sine) * vz,
        (tilt * ay * ax + az * sine) * vx
        + (tilt * ay * ay + cosine) * vy
        + (tilt * ay * az - ax * sine) * vz,
        (tilt * az * ax - ay * sine) * vx
        + (tilt * az * ay + ax * sine) * vy
        + (tilt * az * az + cosine) * vz,
    )


def view_basis(
    elev_deg: float, azim_deg: float, roll_deg: float = CAMERA_ROLL_DEG
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Screen right, screen up, and the direction from the origin toward the camera.

    This is matplotlib's orthographic view at ``roll_deg``. A positive roll spins
    the camera clockwise. At elev = 90 the screen-up vector is the azimuth, and
    screen-right is that vector turned 90 degrees clockwise about the view.
    """
    elev = math.radians(elev_deg)
    azim = math.radians(azim_deg)
    outward = (
        math.cos(elev) * math.cos(azim),
        math.cos(elev) * math.sin(azim),
        math.sin(elev),
    )
    scale = math.sqrt(outward[0] ** 2 + outward[1] ** 2 + outward[2] ** 2)
    outward = (outward[0] / scale, outward[1] / scale, outward[2] / scale)
    vertical = -1.0 if abs(elev) > math.pi / 2.0 else 1.0
    # V × outward, with V = (0, 0, vertical). This is matplotlib's screen-right.
    right = (-vertical * outward[1], vertical * outward[0], 0.0)
    horizontal = math.hypot(right[0], right[1])
    if horizontal < 1e-8:
        # elev = ±90. The cross product is lost in roundoff. The limit approached
        # from the equator turns the azimuth 90° about +Z into screen-right.
        approach = 1.0 if abs(elev_deg) <= 90.0 else -1.0
        signed = approach if vertical > 0.0 else -approach
        right = (-signed * math.sin(azim), signed * math.cos(azim), 0.0)
    else:
        right = (right[0] / horizontal, right[1] / horizontal, 0.0)
    up = (
        outward[1] * right[2] - outward[2] * right[1],
        outward[2] * right[0] - outward[0] * right[2],
        outward[0] * right[1] - outward[1] * right[0],
    )
    if roll_deg != 0.0:
        roll = math.radians(roll_deg)
        right = _rotate_about(right, outward, -roll)
        up = _rotate_about(up, outward, -roll)
    return right, up, outward


def apply_matplotlib_view(ax: object, elev: float, azim: float, roll: float) -> None:
    """Aim a matplotlib axes at this elev, azim, and roll.

    Exactly on the pole, matplotlib's screen axes follow roundoff. A small roll
    correction puts them on the same basis ``view_basis`` gives the HTML viewer.
    """
    try:
        ax.view_init(elev=elev, azim=azim, roll=roll)
    except TypeError:
        ax.view_init(elev=elev, azim=azim)
        return
    ax.get_proj()
    desired_right, desired_up, _outward = view_basis(elev, azim, roll)
    current_right = tuple(float(component) for component in ax._view_u)
    current_up = tuple(float(component) for component in ax._view_v)
    cosine = sum(left * right for left, right in zip(desired_right, current_right))
    sine = sum(left * right for left, right in zip(desired_right, current_up))
    correction = -math.degrees(math.atan2(sine, cosine))
    if abs(correction) >= 1e-3:
        ax.view_init(elev=elev, azim=azim, roll=roll + correction)


def camera_direction(elev: float, azim: float) -> tuple[float, float, float]:
    """Unit vector from the origin toward the matplotlib camera."""
    _right, _up, outward = view_basis(elev, azim, CAMERA_ROLL_DEG)
    return outward


def behind_planet(
    x: float, y: float, z: float, ux: float, uy: float, uz: float, radius: float
) -> bool:
    """True when an opaque sphere of this radius hides the point from the camera."""
    depth = x * ux + y * uy + z * uz
    off_axis = x * x + y * y + z * z - depth * depth
    if off_axis >= radius * radius:
        return False
    return depth < math.sqrt(radius * radius - off_axis)


def position_at_true(orbit: Orbit, nu: float) -> tuple[float, float, float, float]:
    radius = conic_radius_from_parameter(orbit.p, orbit.e, nu)
    argument = argument_of_latitude(orbit.omega, nu)
    return (
        inertial_position_x(radius, orbit.Omega, argument, orbit.i),
        inertial_position_y(radius, orbit.Omega, argument, orbit.i),
        inertial_position_z(radius, orbit.i, argument),
        radius,
    )


def velocity_at_true(orbit: Orbit, nu: float) -> tuple[float, float, float]:
    """Inertial velocity on the conic. The polar rates match the element-to-state map."""
    radius = conic_radius_from_parameter(orbit.p, orbit.e, nu)
    argument = argument_of_latitude(orbit.omega, nu)
    radial = (orbit.h * orbit.e / orbit.p) * math.sin(nu)
    transverse = orbit.h / radius
    x = inertial_position_x(radius, orbit.Omega, argument, orbit.i)
    y = inertial_position_y(radius, orbit.Omega, argument, orbit.i)
    z = inertial_position_z(radius, orbit.i, argument)
    return (
        inertial_velocity_x(radial, radius, x, transverse, orbit.Omega, argument, orbit.i),
        inertial_velocity_y(radial, radius, y, transverse, orbit.Omega, argument, orbit.i),
        inertial_velocity_z(radial, radius, z, transverse, orbit.i, argument),
    )


def split_orbit_strokes(
    polyline: tuple[tuple[float, float, float], ...] | list[tuple[float, float, float]],
    hidden: list[bool],
) -> tuple[list[list[tuple[float, float, float]]], list[list[tuple[float, float, float]]]]:
    """Split a polyline into near and far strokes. The limb point is kept on both."""
    near_strokes: list[list[tuple[float, float, float]]] = []
    far_strokes: list[list[tuple[float, float, float]]] = []
    near: list[tuple[float, float, float]] = []
    far: list[tuple[float, float, float]] = []

    def flush() -> None:
        if len(near) > 1:
            near_strokes.append(list(near))
        if len(far) > 1:
            far_strokes.append(list(far))
        near.clear()
        far.clear()

    previous: bool | None = None
    for point, flag in zip(polyline, hidden):
        if previous is not None and flag != previous:
            if flag:
                near.append(point)
            else:
                far.append(point)
            flush()
        bucket = far if flag else near
        bucket.append(point)
        previous = flag
    flush()
    return near_strokes, far_strokes


@dataclass(frozen=True)
class LegendEntry:
    label: str
    swatch: str
    color: str
    edge: str | None = None


@dataclass(frozen=True)
class Marker:
    id: str
    label: str
    shape: str
    color: str
    km: tuple[float, float, float]


@dataclass(frozen=True)
class KeplerAnim:
    conic: str
    mu: float
    a: float | None
    e: float
    i: float
    Omega: float
    omega: float
    nu: float
    M: float | None
    p: float
    h: float
    period: float | None
    nu_min: float
    nu_max: float
    ellipse_wall_s: float
    open_arc_wall_s: float


@dataclass(frozen=True)
class Scene:
    """Geometry shared by the still PNG and the HTML viewer. Lengths are kilometres."""

    title: str
    elev_deg: float
    azim_deg: float
    roll_deg: float
    limit_km: float
    axis_length_km: float
    equatorial_radius_km: float
    polar_radius_km: float
    flattening: float
    planet_segments_u: int
    planet_segments_v: int
    planet_opacity: float
    show_wedge: bool
    wedge_km: tuple[tuple[float, float, float], ...]
    wedge_length_km: float
    ring_km: tuple[tuple[float, float, float], ...]
    spokes_km: tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]
    equator_km: tuple[tuple[float, float, float], ...]
    axes: tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...]
    orbit_km: tuple[tuple[tuple[float, float, float], ...], ...]
    markers: tuple[Marker, ...]
    craft_km: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]
    velocity_length_km: float
    legend: tuple[LegendEntry, ...]
    kepler: KeplerAnim

    def to_viewer_dict(self) -> dict[str, object]:
        def xyz(point: tuple[float, float, float]) -> list[float]:
            return [point[0], point[1], point[2]]

        return {
            "title": self.title,
            "elev_deg": self.elev_deg,
            "azim_deg": self.azim_deg,
            "roll_deg": self.roll_deg,
            "limit_km": self.limit_km,
            "axis_length_km": self.axis_length_km,
            "equatorial_radius_km": self.equatorial_radius_km,
            "polar_radius_km": self.polar_radius_km,
            "flattening": self.flattening,
            "planet_segments_u": self.planet_segments_u,
            "planet_segments_v": self.planet_segments_v,
            "planet_opacity": self.planet_opacity,
            "show_wedge": self.show_wedge,
            "wedge_km": [xyz(point) for point in self.wedge_km],
            "wedge_length_km": self.wedge_length_km,
            "wedge_steps": WEDGE_STEPS,
            "ring_km": [xyz(point) for point in self.ring_km],
            "spokes_km": [[xyz(a), xyz(b)] for a, b in self.spokes_km],
            "equator_km": [xyz(point) for point in self.equator_km],
            "axes": [
                {"label": label, "tip_km": xyz(tip), "label_km": xyz(label_at)}
                for label, tip, label_at in self.axes
            ],
            "orbit_km": [[xyz(point) for point in polyline] for polyline in self.orbit_km],
            "markers": [
                {
                    "id": marker.id,
                    "label": marker.label,
                    "shape": marker.shape,
                    "color": marker.color,
                    "km": xyz(marker.km),
                }
                for marker in self.markers
            ],
            "craft_km": xyz(self.craft_km),
            "velocity_m_s": xyz(self.velocity_m_s),
            "velocity_length_km": self.velocity_length_km,
            "legend": [
                {
                    "label": entry.label,
                    "swatch": entry.swatch,
                    "color": entry.color,
                    "edge": entry.edge,
                }
                for entry in self.legend
            ],
            "palette": dict(PALETTE),
            "kepler": {
                "conic": self.kepler.conic,
                "mu": self.kepler.mu,
                "a": self.kepler.a,
                "e": self.kepler.e,
                "i": self.kepler.i,
                "Omega": self.kepler.Omega,
                "omega": self.kepler.omega,
                "nu": self.kepler.nu,
                "M": self.kepler.M,
                "p": self.kepler.p,
                "h": self.kepler.h,
                "period": self.kepler.period,
                "nu_min": self.kepler.nu_min,
                "nu_max": self.kepler.nu_max,
                "ellipse_wall_s": self.kepler.ellipse_wall_s,
                "open_arc_wall_s": self.kepler.open_arc_wall_s,
            },
        }


def _km(meters: float) -> float:
    return meters / 1000.0


def radius_elevation(craft_km: tuple[float, float, float], Omega: float) -> tuple[float, float, float, float]:
    """Longitude basis and the signed angle of the radius above the equator."""
    horizontal = math.hypot(craft_km[0], craft_km[1])
    if horizontal < 1e-6:
        along = -math.sin(Omega)
        across = math.cos(Omega)
        elevation = math.copysign(0.5 * math.pi, craft_km[2] if craft_km[2] != 0.0 else 1.0)
    else:
        along = craft_km[0] / horizontal
        across = craft_km[1] / horizontal
        elevation = math.atan2(craft_km[2], horizontal)
    radius = math.sqrt(horizontal * horizontal + craft_km[2] * craft_km[2])
    return along, across, elevation, radius


def inclination_sector(
    craft_km: tuple[float, float, float],
    Omega: float,
) -> tuple[tuple[float, float, float], ...]:
    """Sector from the equator to the radius, with the spacecraft on that edge.

    The vertex is the planet center. One edge lies in the equatorial plane.
    The other edge is the radius, so it ends on the spacecraft.
    """
    along, across, elevation, radius = radius_elevation(craft_km, Omega)
    if radius < 1e-9:
        return ()
    points = [(0.0, 0.0, 0.0)]
    for tilt in linspace(0.0, elevation, WEDGE_STEPS):
        points.append(
            (
                radius * math.cos(tilt) * along,
                radius * math.cos(tilt) * across,
                radius * math.sin(tilt),
            )
        )
    points[-1] = craft_km
    return tuple(points)


def build_scene(body: Body, orbit: Orbit, elev: float, azim: float) -> Scene:
    """Planet, orbit samples, markers, wedge, axes, and the Kepler animation payload."""
    span = display_span_m(body, orbit)
    limit_m = LIMIT_SPAN_FRAC * span
    axis_len = min(max(1.35 * body.radius, 0.42 * span), 0.72 * span)
    ring_r = min(1.22 * body.radius, 0.98 * span)
    polar_m = body.radius * (1.0 - body.flattening)
    show_wedge = WEDGE_INCLINATION < orbit.i < math.pi - WEDGE_INCLINATION

    ring_angles = linspace(0.0, 2.0 * math.pi, 181)
    ring = tuple(
        (_km(ring_r * math.cos(angle)), _km(ring_r * math.sin(angle)), 0.0) for angle in ring_angles
    )
    equator = tuple(
        (_km(body.radius * math.cos(angle)), _km(body.radius * math.sin(angle)), 0.0)
        for angle in ring_angles
    )
    spokes: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = []
    inner = min(body.radius, ring_r)
    if ring_r > inner * (1.0 + 1e-6):
        for spoke in range(8):
            angle = spoke * math.pi / 8.0
            spokes.append(
                (
                    (_km(inner * math.cos(angle)), _km(inner * math.sin(angle)), 0.0),
                    (_km(ring_r * math.cos(angle)), _km(ring_r * math.sin(angle)), 0.0),
                )
            )

    polylines: list[tuple[tuple[float, float, float], ...]] = []
    current: list[tuple[float, float, float]] = []
    drawn_nus: list[float] = []
    for nu in sample_true_anomalies(orbit, span):
        px, py, pz, radius = position_at_true(orbit, nu)
        if radius > span * 1.02 or not math.isfinite(radius):
            if len(current) > 1:
                polylines.append(tuple(current))
            current = []
            continue
        current.append((_km(px), _km(py), _km(pz)))
        drawn_nus.append(nu)
    if len(current) > 1:
        polylines.append(tuple(current))
    nu_min = min(drawn_nus + [orbit.nu])
    nu_max = max(drawn_nus + [orbit.nu])

    markers: list[Marker] = []
    node_nu = wrap_pi(-orbit.omega)
    node_denom = 1.0 + orbit.e * math.cos(node_nu)
    if node_denom > 1e-8:
        nx, ny, nz, node_radius = position_at_true(orbit, node_nu)
        if node_radius <= span * 1.02 and math.isfinite(node_radius):
            markers.append(
                Marker("ascending_node", "ascending node", "circle", PALETTE["node"], (_km(nx), _km(ny), _km(nz)))
            )
    peri = position_at_true(orbit, 0.0)
    markers.append(
        Marker("periapsis", "periapsis", "circle", PALETTE["periapsis"], (_km(peri[0]), _km(peri[1]), _km(peri[2])))
    )
    if orbit.ra is not None:
        apo = position_at_true(orbit, math.pi)
        markers.append(
            Marker("apoapsis", "apoapsis", "square", PALETTE["apoapsis"], (_km(apo[0]), _km(apo[1]), _km(apo[2])))
        )
    craft = (_km(orbit.rx), _km(orbit.ry), _km(orbit.rz))
    markers.append(Marker("spacecraft", "spacecraft", "circle", PALETTE["craft"], craft))
    wedge_length_km = math.sqrt(craft[0] ** 2 + craft[1] ** 2 + craft[2] ** 2)
    wedge: tuple[tuple[float, float, float], ...] = ()
    if show_wedge:
        wedge = inclination_sector(craft, orbit.Omega)

    legend: list[LegendEntry] = [
        LegendEntry("planet", "planet", PALETTE["planet"], PALETTE["planet_edge"]),
        LegendEntry("equatorial plane", "line", PALETTE["equator"]),
        LegendEntry("orbit", "line", PALETTE["orbit"]),
        LegendEntry("ascending node", "circle", PALETTE["node"]),
    ]
    if show_wedge:
        legend.append(LegendEntry("inclination", "wedge", PALETTE["wedge"], PALETTE["wedge_edge"]))
    legend.append(LegendEntry("periapsis", "circle", PALETTE["periapsis"]))
    if orbit.ra is not None:
        legend.append(LegendEntry("apoapsis", "square", PALETTE["apoapsis"]))
    legend.extend(
        [
            LegendEntry("spacecraft", "circle", PALETTE["craft"]),
            LegendEntry("radius", "line", PALETTE["radius"]),
            LegendEntry("velocity", "line", PALETTE["velocity"]),
        ]
    )

    axes: list[tuple[str, tuple[float, float, float], tuple[float, float, float]]] = []
    for label, tip_m in (
        ("+X", (axis_len, 0.0, 0.0)),
        ("+Y", (0.0, axis_len, 0.0)),
        ("+Z", (0.0, 0.0, axis_len)),
    ):
        tip = (_km(tip_m[0]), _km(tip_m[1]), _km(tip_m[2]))
        axes.append((label, tip, (tip[0] * 1.06, tip[1] * 1.06, tip[2] * 1.06)))

    velocity = (orbit.vx, orbit.vy, orbit.vz)
    return Scene(
        title=PLOT_TITLE,
        elev_deg=elev,
        azim_deg=azim,
        roll_deg=CAMERA_ROLL_DEG,
        limit_km=_km(limit_m),
        axis_length_km=_km(axis_len),
        equatorial_radius_km=_km(body.radius),
        polar_radius_km=_km(polar_m),
        flattening=body.flattening,
        planet_segments_u=PLANET_SEGMENTS_U,
        planet_segments_v=PLANET_SEGMENTS_V,
        planet_opacity=0.52,
        show_wedge=show_wedge,
        wedge_km=wedge,
        wedge_length_km=wedge_length_km,
        ring_km=ring,
        spokes_km=tuple(spokes),
        equator_km=equator,
        axes=tuple(axes),
        orbit_km=tuple(polylines),
        markers=tuple(markers),
        craft_km=craft,
        velocity_m_s=velocity,
        velocity_length_km=_km(ARROW_SPAN_FRAC * span),
        legend=tuple(legend),
        kepler=KeplerAnim(
            conic=orbit.conic,
            mu=body.mu,
            a=orbit.a,
            e=orbit.e,
            i=orbit.i,
            Omega=orbit.Omega,
            omega=orbit.omega,
            nu=orbit.nu,
            M=orbit.M,
            p=orbit.p,
            h=orbit.h,
            period=orbit.period,
            nu_min=nu_min,
            nu_max=nu_max,
            ellipse_wall_s=ELLIPSE_WALL_S,
            open_arc_wall_s=OPEN_ARC_WALL_S,
        ),
    )


def _planet_arrays(scene: Scene):
    """Shaded translucent spheroid. Lighting follows the matplotlib camera."""
    import numpy as np

    right, up, outward = view_basis(scene.elev_deg, scene.azim_deg, scene.roll_deg)
    light = (
        0.72 * outward[0] + 0.48 * up[0] - 0.32 * right[0],
        0.72 * outward[1] + 0.48 * up[1] - 0.32 * right[1],
        0.72 * outward[2] + 0.48 * up[2] - 0.32 * right[2],
    )
    scale = math.sqrt(light[0] ** 2 + light[1] ** 2 + light[2] ** 2)
    light = (light[0] / scale, light[1] / scale, light[2] / scale)
    n_u = scene.planet_segments_u + 1
    n_v = scene.planet_segments_v + 1
    us = linspace(0.0, 2.0 * math.pi, n_u)
    vs = linspace(0.0, math.pi, n_v)
    radius = scene.equatorial_radius_km
    polar = scene.polar_radius_km
    xs = np.zeros((n_v, n_u))
    ys = np.zeros((n_v, n_u))
    zs = np.zeros((n_v, n_u))
    rgba = np.zeros((n_v - 1, n_u - 1, 4))
    for i, polar_angle in enumerate(vs):
        sin_v = math.sin(polar_angle)
        cos_v = math.cos(polar_angle)
        for j, azimuth in enumerate(us):
            xs[i, j] = radius * math.cos(azimuth) * sin_v
            ys[i, j] = radius * math.sin(azimuth) * sin_v
            zs[i, j] = polar * cos_v
    shadow = (0.45, 0.64, 0.78)
    highlight = (0.95, 0.98, 1.0)
    for i in range(n_v - 1):
        vang = 0.5 * (vs[i] + vs[i + 1])
        sin_v = math.sin(vang)
        cos_v = math.cos(vang)
        for j in range(n_u - 1):
            uang = 0.5 * (us[j] + us[j + 1])
            x = radius * math.cos(uang) * sin_v
            y = radius * math.sin(uang) * sin_v
            z = polar * cos_v
            nx = x / (radius * radius)
            ny = y / (radius * radius)
            nz = z / (polar * polar) if polar else 0.0
            norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / norm, ny / norm, nz / norm
            ndotl = max(0.0, nx * light[0] + ny * light[1] + nz * light[2])
            ndotv = max(0.0, nx * outward[0] + ny * outward[1] + nz * outward[2])
            rim = (1.0 - ndotv) ** 1.35
            lit = (0.32 + 0.68 * ndotl) * (1.0 - 0.30 * rim)
            rgba[i, j, 0] = shadow[0] + (highlight[0] - shadow[0]) * lit
            rgba[i, j, 1] = shadow[1] + (highlight[1] - shadow[1]) * lit
            rgba[i, j, 2] = shadow[2] + (highlight[2] - shadow[2]) * lit
            rgba[i, j, 3] = scene.planet_opacity
    return xs, ys, zs, rgba


def _legend_handle(entry: LegendEntry):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    if entry.swatch == "planet":
        return Patch(facecolor=entry.color, edgecolor=entry.edge, label=entry.label)
    if entry.swatch == "wedge":
        return Patch(facecolor=entry.color, edgecolor=entry.edge, alpha=0.75, label=entry.label)
    if entry.swatch == "circle":
        return Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=entry.color,
            markeredgecolor="white",
            markeredgewidth=1.0,
            markersize=7.5,
            label=entry.label,
        )
    if entry.swatch == "square":
        return Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor=entry.color,
            markeredgecolor="white",
            markeredgewidth=1.0,
            markersize=7,
            label=entry.label,
        )
    width = 2.2 if entry.label == "orbit" else 1.6
    return Line2D([0], [0], color=entry.color, linewidth=width, label=entry.label)


def plot_orbit(path: Path, scene: Scene) -> None:
    """Still PNG of the shared scene at the epoch state."""
    plt = ensure_matplotlib()
    from matplotlib.ticker import MaxNLocator
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(10.2, 7.9), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    try:
        ax.set_proj_type("ortho")
    except AttributeError:
        pass
    ax.computed_zorder = False

    if len(scene.ring_km) > 1:
        xs, ys, zs = zip(*scene.ring_km)
        ax.plot(xs, ys, zs, color=PALETTE["equator"], linewidth=1.25, zorder=1, solid_capstyle="round")
    for spoke in scene.spokes_km:
        xs, ys, zs = zip(*spoke)
        ax.plot(xs, ys, zs, color=PALETTE["equator_spoke"], linewidth=0.9, zorder=1)

    xs, ys, zs, rgba = _planet_arrays(scene)
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
    if len(scene.equator_km) > 1:
        ex, ey, ez = zip(*scene.equator_km)
        ax.plot(ex, ey, ez, color=PALETTE["equator_limb"], linewidth=0.95, zorder=4)

    for label, tip, label_at in scene.axes:
        ax.plot(
            [0.0, tip[0]],
            [0.0, tip[1]],
            [0.0, tip[2]],
            color=PALETTE["axis"],
            linewidth=1.2,
            zorder=4,
            solid_capstyle="round",
        )
        ax.text(
            label_at[0],
            label_at[1],
            label_at[2],
            label,
            color=PALETTE["axis"],
            fontsize=9,
        )

    _right, _up, outward = view_basis(scene.elev_deg, scene.azim_deg, scene.roll_deg)
    for polyline in scene.orbit_km:
        hidden = [
            behind_planet(x, y, z, outward[0], outward[1], outward[2], scene.equatorial_radius_km)
            for x, y, z in polyline
        ]
        near_strokes, far_strokes = split_orbit_strokes(polyline, hidden)
        for stroke in far_strokes:
            xs, ys, zs = zip(*stroke)
            ax.plot(
                xs,
                ys,
                zs,
                color=PALETTE["orbit"],
                linewidth=1.65,
                linestyle=(0, (1.8, 1.9)),
                zorder=6,
                solid_capstyle="round",
            )
        for stroke in near_strokes:
            xs, ys, zs = zip(*stroke)
            ax.plot(
                xs,
                ys,
                zs,
                color=PALETTE["orbit"],
                linewidth=2.8,
                zorder=8,
                solid_capstyle="round",
            )

    if scene.show_wedge and len(scene.wedge_km) >= 3:
        wedge = Poly3DCollection(
            [list(scene.wedge_km)],
            alpha=0.72,
            facecolor=PALETTE["wedge"],
            edgecolor=PALETTE["wedge_edge"],
            linewidths=1.1,
        )
        wedge.set_zorder(9)
        ax.add_collection3d(wedge)

    ax.plot(
        [0.0, scene.craft_km[0]],
        [0.0, scene.craft_km[1]],
        [0.0, scene.craft_km[2]],
        color=PALETTE["radius"],
        linewidth=1.15,
        zorder=5,
        solid_capstyle="round",
    )
    speed = math.sqrt(sum(component * component for component in scene.velocity_m_s))
    if speed > 0.0:
        ax.quiver(
            scene.craft_km[0],
            scene.craft_km[1],
            scene.craft_km[2],
            scene.velocity_m_s[0],
            scene.velocity_m_s[1],
            scene.velocity_m_s[2],
            length=scene.velocity_length_km,
            normalize=True,
            color=PALETTE["velocity"],
            arrow_length_ratio=0.18,
            linewidth=1.35,
        )
    sizes = {"ascending_node": 96, "periapsis": 74, "apoapsis": 80, "spacecraft": 88}
    for marker in scene.markers:
        if marker.id == "spacecraft":
            continue
        ax.scatter(
            [marker.km[0]],
            [marker.km[1]],
            [marker.km[2]],
            color=marker.color,
            s=sizes.get(marker.id, 72),
            marker="s" if marker.shape == "square" else "o",
            depthshade=False,
            edgecolors="white",
            linewidths=1.15,
            zorder=9,
        )
    craft = next(marker for marker in scene.markers if marker.id == "spacecraft")
    ax.scatter(
        [craft.km[0]],
        [craft.km[1]],
        [craft.km[2]],
        color=craft.color,
        s=sizes["spacecraft"],
        marker="o",
        depthshade=False,
        edgecolors="white",
        linewidths=1.2,
        zorder=10,
    )

    limit = scene.limit_km
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
    ax.set_xlabel(PNG_AXIS_LABELS[0], labelpad=7, fontsize=10, color=PALETTE["text"])
    ax.set_ylabel(PNG_AXIS_LABELS[1], labelpad=7, fontsize=10, color=PALETTE["text"])
    ax.set_zlabel(PNG_AXIS_LABELS[2], labelpad=6, fontsize=10, color=PALETTE["text"])
    ax.set_title(scene.title, pad=8, fontsize=15, color=PALETTE["text"])
    ax.tick_params(labelsize=8, pad=1, colors="#5d6d7e")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.zaxis.set_major_locator(MaxNLocator(nbins=4))
    apply_matplotlib_view(ax, scene.elev_deg, scene.azim_deg, scene.roll_deg)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor(PALETTE["pane"])
        axis.pane.set_edgecolor("#d5d8dc")
        axis.pane.set_alpha(0.55)
    ax.grid(False)
    ax.text2D(
        0.0,
        -0.02,
        f"elev {scene.elev_deg:.4g}°    azim {scene.azim_deg:.4g}°",
        transform=ax.transAxes,
        fontsize=9,
        color=PALETTE["caption"],
    )
    legend = ax.legend(
        handles=[_legend_handle(entry) for entry in scene.legend],
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


def viewer_path_for(png_path: Path) -> Path:
    return png_path.with_suffix(".html")


def write_viewer_html(path: Path, scene: Scene) -> None:
    """Write one offline HTML file with the vendored Three.js bundle and this scene."""
    viewer_dir = Path(__file__).resolve().parent / "viewer"
    try:
        template = (viewer_dir / "template.html").read_text(encoding="utf-8")
        three_source = (viewer_dir / "three.min.js").read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read the viewer template: {exc}") from exc
    lowered = three_source.lower()
    if "</script>" in lowered:
        three_source = three_source.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    payload = json.dumps(scene.to_viewer_dict(), allow_nan=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")
    before, placeholder, after = template.partition("__THREE_SOURCE__")
    if not placeholder:
        raise ValueError("viewer template is missing the Three.js placeholder")
    before = before.replace("__TITLE__", scene.title).replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
    after = (
        after.replace("__TITLE__", scene.title)
        .replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
        .replace("__SCENE_JSON__", payload)
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


def viewer_issues(stdout: str, png_path: str) -> str | None:
    values = parse_stdout(stdout)
    if "viewer" not in values:
        return "stdout missing viewer"
    expected = Path(png_path).resolve().with_suffix(".html")
    got = Path(values["viewer"])
    if got.resolve() != expected:
        return f"viewer path {got} != {expected}"
    if not got.is_file():
        return "viewer file missing"
    html = got.read_text(encoding="utf-8")
    if not html.startswith("<!DOCTYPE html>"):
        return "viewer is not an HTML document"
    if PLOT_TITLE not in html:
        return "viewer missing title"
    if "new THREE.OrthographicCamera" not in html:
        return "viewer missing orthographic camera"
    if "behindPlanet" not in html or "solveKepler" not in html:
        return "viewer missing occlusion or the Kepler solver"
    if "Reset to epoch" not in html or "Reset camera" not in html:
        return "viewer missing controls"
    if AXIS_UNIT_CAPTION not in html:
        return "viewer missing the kilometre axis caption"
    if "<script src=" in html.lower():
        return "viewer loads an external script"
    return None


def print_report(
    body: Body, orbit: Orbit, elev: float, azim: float, path: Path, viewer: Path
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", orbit.mode)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("flattening", body.flattening)
    print_kv("conic", orbit.conic)
    if orbit.a is None:
        print_kv("a", "none")
    else:
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
    print_kv("p_m", orbit.p)
    print_kv("energy_J_kg", orbit.energy)
    print_kv("h_m2_s", orbit.h)
    print_kv("hx_m2_s", orbit.hx)
    print_kv("hy_m2_s", orbit.hy)
    print_kv("hz_m2_s", orbit.hz)
    print_kv("rp_m", orbit.rp)
    if orbit.ra is None:
        print_kv("apoapsis", "none")
    else:
        print_kv("ra_m", orbit.ra)
    if orbit.period is None:
        print_kv("period", "none")
    else:
        print_kv("period_s", orbit.period)
    print_kv("rx_m", orbit.rx)
    print_kv("ry_m", orbit.ry)
    print_kv("rz_m", orbit.rz)
    print_kv("vx_m_s", orbit.vx)
    print_kv("vy_m_s", orbit.vy)
    print_kv("vz_m_s", orbit.vz)
    print_kv("elev_deg", elev)
    print_kv("azim_deg", azim)
    warning = surface_warning(body, orbit)
    if warning:
        print_kv("warning", warning)
    print_kv("graph", str(path))
    print_kv("viewer", str(viewer))


def resolve_body(radius_arg: float | None, flattening_arg: float | None) -> Body:
    if radius_arg is None:
        radius = R0_EARTH
        source = "default"
        flattening = F_EARTH if flattening_arg is None else flattening_arg
    else:
        require_finite(radius_arg, "--R0")
        if radius_arg <= 0.0:
            raise ValueError("--R0 must be > 0 m")
        radius = radius_arg
        source = "input"
        flattening = 0.0 if flattening_arg is None else flattening_arg
    if flattening_arg is not None:
        require_finite(flattening_arg, "--flattening")
    if flattening < 0.0 or flattening >= 1.0:
        raise ValueError("--flattening must satisfy 0 <= f < 1")
    return Body(
        radius=radius,
        g0=G0,
        mu=G0 * radius**2,
        flattening=flattening,
        radius_source=source,
    )


def resolve_camera(elev_arg: float | None, azim_arg: float | None) -> tuple[float, float]:
    elev = ELEV_DEG if elev_arg is None else elev_arg
    azim = AZIM_DEG if azim_arg is None else azim_arg
    require_finite(elev, "--elev")
    require_finite(azim, "--azim")
    return elev, azim


def resolve_request(ns: argparse.Namespace, body: Body) -> Orbit:
    element_names = ("a", "e", "i", "raan", "aop", "nu", "M")
    state_names = ("rx", "ry", "rz", "vx", "vy", "vz")
    element_used = [name for name in element_names if getattr(ns, name) is not None]
    state_used = [name for name in state_names if getattr(ns, name) is not None]
    if element_used and state_used:
        raise ValueError("pass either classical elements or an inertial state, not both")
    if state_used:
        missing = [name for name in state_names if getattr(ns, name) is None]
        if missing:
            flags = ", ".join(f"--{name}" for name in missing)
            raise ValueError(f"missing vector components: {flags}")
        return orbit_from_state(
            body.mu, ns.rx, ns.ry, ns.rz, ns.vx, ns.vy, ns.vz, "state"
        )
    if not element_used:
        raise ValueError(
            "pass --a --e --i --raan --aop and one of --nu or --M, "
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
    return orbit_from_elements(
        body.mu, ns.a, ns.e, ns.i, ns.raan, ns.aop, ns.nu, ns.M, "elements"
    )


def run(ns: argparse.Namespace) -> int:
    body = resolve_body(ns.R0, ns.flattening)
    elev, azim = resolve_camera(ns.elev, ns.azim)
    orbit = resolve_request(ns, body)
    script_dir = Path(__file__).resolve().parent
    out_path = Path(ns.out) if ns.out else script_dir / "orbital_parameters.png"
    out_path = out_path.resolve()
    viewer_path = viewer_path_for(out_path)
    scene = build_scene(body, orbit, elev, azim)
    plot_orbit(out_path, scene)
    write_viewer_html(viewer_path, scene)
    print_report(body, orbit, elev, azim, out_path, viewer_path)
    if ns.open:
        webbrowser.open(viewer_path.as_uri())
    return 0


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def angle_close(got: float, expected: float) -> bool:
    return abs(wrap_pi(got - expected)) <= ANGLE_TOL


def vector_close(got: tuple[float, ...], expected: tuple[float, ...]) -> bool:
    scale = max(math.sqrt(sum(component * component for component in expected)), 1.0)
    return all(abs(left - right) <= CHECK_TOL * scale for left, right in zip(got, expected))


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


# README examples. The visual checklist compares the PNG scene with the HTML payload.
EARTH_ELLIPSE_ARGV = [
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
EARTH_HYPERBOLA_ARGV = [
    "--a",
    "-25000000",
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
]
_UNCHANGED_WHEN_FLATTENED = (
    "mode",
    "R0_m",
    "g0_m_s2",
    "mu_m3_s2",
    "conic",
    "a_m",
    "e",
    "i_rad",
    "Omega_rad",
    "omega_rad",
    "nu_rad",
    "M_rad",
    "p_m",
    "energy_J_kg",
    "h_m2_s",
    "hx_m2_s",
    "hy_m2_s",
    "hz_m2_s",
    "rp_m",
    "ra_m",
    "period_s",
    "rx_m",
    "ry_m",
    "rz_m",
    "vx_m_s",
    "vy_m_s",
    "vz_m_s",
)


def _distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _segment_distance(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    vz = end[2] - start[2]
    length2 = vx * vx + vy * vy + vz * vz
    if length2 == 0.0:
        return _distance(point, start)
    t = ((point[0] - start[0]) * vx + (point[1] - start[1]) * vy + (point[2] - start[2]) * vz) / length2
    t = min(1.0, max(0.0, t))
    closest = (start[0] + t * vx, start[1] + t * vy, start[2] + t * vz)
    return _distance(point, closest)


def _off_drawn_curve(point: tuple[float, float, float], scene: Scene) -> float:
    best = math.inf
    for polyline in scene.orbit_km:
        for start, end in zip(polyline, polyline[1:]):
            best = min(best, _segment_distance(point, start, end))
    return best


def _png_pixel_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or not data.startswith(b"\x89PNG") or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _payload_mismatch(left: object, right: object, path: str) -> str | None:
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            missing = set(left) ^ set(right)
            return f"{path} keys {sorted(missing)}"
        for key in left:
            issue = _payload_mismatch(left[key], right[key], f"{path}.{key}")
            if issue:
                return issue
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path} length {len(left)} != {len(right)}"
        for index, (item, other) in enumerate(zip(left, right)):
            issue = _payload_mismatch(item, other, f"{path}[{index}]")
            if issue:
                return issue
        return None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)) and not isinstance(left, bool):
        if abs(float(left) - float(right)) > 1e-9 * max(1.0, abs(float(left))):
            return f"{path} {left} != {right}"
        return None
    if left != right:
        return f"{path} {left!r} != {right!r}"
    return None


def _js_function(html: str, name: str) -> str:
    token = f"function {name}"
    start = html.find(token)
    if start < 0:
        return ""
    brace = html.find("{", start)
    if brace < 0:
        return ""
    depth = 0
    for index in range(brace, len(html)):
        char = html[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return html[start : index + 1]
    return ""


def _occlusion_splits(scene: Scene) -> bool:
    cameras = [(scene.elev_deg, scene.azim_deg)]
    for elev in (12.0, 28.0, 55.0):
        for azim in (20.0, 70.0, 125.0, 210.0):
            cameras.append((elev, azim))
    radius = scene.equatorial_radius_km
    for elev, azim in cameras:
        outward = camera_direction(elev, azim)
        flags = [
            behind_planet(x, y, z, outward[0], outward[1], outward[2], radius)
            for polyline in scene.orbit_km
            for x, y, z in polyline
        ]
        if flags and any(flags) and not all(flags):
            return True
    return False


def _marker(scene: Scene, marker_id: str) -> Marker | None:
    for marker in scene.markers:
        if marker.id == marker_id:
            return marker
    return None


def _wedge_problem(scene: Scene, orbit: Orbit) -> str | None:
    """The sector vertex is the planet center and one edge ends on the spacecraft."""
    if not scene.show_wedge:
        return "wedge missing"
    points = scene.wedge_km
    if len(points) < 3:
        return "wedge too short"
    if any(abs(component) > 1e-6 for component in points[0]):
        return "wedge vertex is not the planet center"
    craft = (orbit.rx / 1000.0, orbit.ry / 1000.0, orbit.rz / 1000.0)
    if not vector_close(points[-1], craft):
        return "inclined edge does not end on the spacecraft"
    equatorial = points[1]
    if abs(equatorial[2]) > 1e-6 * max(scene.limit_km, 1.0):
        return "equatorial edge is not horizontal"
    equatorial_norm = math.sqrt(sum(component * component for component in equatorial))
    inclined_norm = math.sqrt(sum(component * component for component in craft))
    if equatorial_norm <= 0.0 or inclined_norm <= 0.0:
        return "wedge edges collapsed"
    cosine = sum(left * right for left, right in zip(equatorial, craft)) / (
        equatorial_norm * inclined_norm
    )
    _along, _across, elevation, radius = radius_elevation(craft, orbit.Omega)
    if abs(cosine - math.cos(elevation)) > 1e-5:
        return "wedge angle is not the radius elevation"
    horizontal = math.hypot(craft[0], craft[1])
    if horizontal > 1e-4:
        cross = equatorial[0] * craft[1] - equatorial[1] * craft[0]
        if abs(cross) > 1e-4 * equatorial_norm * horizontal:
            return "wedge is not in the spacecraft meridian"
    if not close_enough(scene.wedge_length_km, radius, max(radius, 1.0)):
        return "wedge length is not the spacecraft radius"
    if abs(elevation) > 1e-3 and equatorial_norm < 0.05 * scene.limit_km:
        return "wedge is too small to read"
    return None


def _visual_language_issue(html: str) -> str | None:
    """Static half of the parity checklist. The same strings drive the HTML viewer."""
    checks = (
        ("projection", "new THREE.OrthographicCamera", "viewer is not orthographic"),
        ("occlusion", "function behindPlanet", "viewer occlusion is missing"),
        ("occlusion", "rebuildOrbit", "occlusion does not follow the camera"),
        ("orbit", "dashedPieces", "far side of the orbit is not dashed"),
        ("orbit", "const nearWidth", "near side of the orbit is not the thick stroke"),
        ("orbit", "const farWidth", "far side of the orbit has no thin stroke"),
        ("background", "color-scheme: light", "viewer is not the light field"),
        ("background", "0xf7f9fb", "viewer background is not the light paper color"),
        ("motion", "function solveKepler", "ellipse motion does not solve Kepler"),
        ("motion", "K.M + meanMotion", "ellipse motion is not mean-anomaly time"),
        ("motion", "open_arc_wall_s", "open conics have no drawn-arc window"),
        ("motion", "let playing = true", "viewer does not start playing"),
        ("planet", "SCENE.polar_radius_km / SCENE.equatorial_radius_km", "planet squash is not polar"),
        ("planet", "planet.rotation.x = Math.PI / 2", "planet polar axis is not +Z"),
        ("axes", AXIS_UNIT_CAPTION, "axes are not labelled in kilometres"),
    )
    for _cue, needle, message in checks:
        if needle not in html:
            return message
    update = _js_function(html, "updateCraft")
    if "craftSprite" not in update or "setDirection" not in update or "placeWedge" not in update:
        return "motion does not update the craft, radius, velocity, and inclination"
    if "periapsis" in update or "apoapsis" in update or "ascending_node" in update:
        return "motion moves a fixed marker"
    return None


def _checklist_issue(
    name: str,
    scene: Scene,
    orbit: Orbit,
    values: dict[str, str],
    html: str,
    png: bytes,
    conic: str,
) -> str | None:
    """One known case, PNG scene beside the HTML payload."""
    mismatch = _payload_mismatch(scene.to_viewer_dict(), scene_from_html(html), name)
    if mismatch:
        return f"{name} scene drift {mismatch}"
    language = _visual_language_issue(html)
    if language:
        return f"{name} / {language}"
    size = _png_pixel_size(png)
    if size is None or size[0] < 1200 or size[1] < 900:
        return f"{name} / png is not clear at chat size {size}"
    if values.get("title") != PLOT_TITLE or scene.title != PLOT_TITLE:
        return f"{name} / title"
    if values.get("conic") != conic or scene.kepler.conic != conic:
        return f"{name} / conic"
    if PNG_AXIS_LABELS != ("X (km)", "Y (km)", "Z (km)"):
        return f"{name} / axes"
    labels = [label for label, _tip, _at in scene.axes]
    if labels != ["+X", "+Y", "+Z"]:
        return f"{name} / axis labels {labels}"
    lengths = [_distance(tip, (0.0, 0.0, 0.0)) for _label, tip, _at in scene.axes]
    if max(lengths) - min(lengths) > 1e-6 or abs(lengths[0] - scene.axis_length_km) > 1e-6:
        return f"{name} / axis length"
    if scene.limit_km <= scene.axis_length_km:
        return f"{name} / equal box"
    if not (0.3 < scene.planet_opacity < 0.7):
        return f"{name} / planet opacity {scene.planet_opacity}"
    expected_polar = scene.equatorial_radius_km * (1.0 - scene.flattening)
    if abs(scene.polar_radius_km - expected_polar) > 1e-6:
        return f"{name} / polar radius"
    if abs(scene.equatorial_radius_km - R0_EARTH / 1000.0) > 1e-6:
        return f"{name} / equatorial radius"
    if len(scene.ring_km) < 8 or len(scene.spokes_km) != 8:
        return f"{name} / equatorial plane"
    if scene.to_viewer_dict()["palette"] != PALETTE:
        return f"{name} / palette"
    if abs(scene.elev_deg - float(values["elev_deg"])) > 1e-9:
        return f"{name} / elev"
    if abs(scene.azim_deg - float(values["azim_deg"])) > 1e-9:
        return f"{name} / azim"
    if scene.roll_deg != CAMERA_ROLL_DEG:
        return f"{name} / roll"
    craft = _marker(scene, "spacecraft")
    peri = _marker(scene, "periapsis")
    node = _marker(scene, "ascending_node")
    apo = _marker(scene, "apoapsis")
    if craft is None or peri is None or node is None:
        return f"{name} / markers"
    if craft.shape != "circle" or craft.color != PALETTE["craft"]:
        return f"{name} / spacecraft marker"
    if peri.shape != "circle" or peri.color != PALETTE["periapsis"]:
        return f"{name} / periapsis marker"
    if node.shape != "circle" or node.color != PALETTE["node"]:
        return f"{name} / ascending node marker"
    if abs(node.km[2]) > 1e-4:
        return f"{name} / ascending node is off the equator"
    node_scale = math.hypot(node.km[0], node.km[1])
    if node_scale < 1e-6:
        return f"{name} / ascending node radius"
    node_hat = (node.km[0] / node_scale, node.km[1] / node_scale, 0.0)
    expected_node = (math.cos(orbit.Omega), math.sin(orbit.Omega), 0.0)
    if not vector_close(node_hat, expected_node):
        return f"{name} / ascending node is not along Omega"
    peri_radius = _distance(peri.km, (0.0, 0.0, 0.0)) * 1000.0
    if not close_enough(peri_radius, orbit.rp, orbit.rp):
        return f"{name} / periapsis radius"
    epoch = (orbit.rx / 1000.0, orbit.ry / 1000.0, orbit.rz / 1000.0)
    if not vector_close(craft.km, epoch):
        return f"{name} / craft is not the epoch state"
    if _off_drawn_curve(craft.km, scene) > 2.0:
        return f"{name} / craft is off the drawn orbit"
    if _off_drawn_curve(peri.km, scene) > 1e-3:
        return f"{name} / periapsis is off the drawn orbit"
    if not _occlusion_splits(scene):
        return f"{name} / occlusion never splits near and far"
    legend = [entry.label for entry in scene.legend]
    if legend != [item["label"] for item in scene.to_viewer_dict()["legend"]]:
        return f"{name} / legend"
    if conic == "ellipse":
        if apo is None or apo.shape != "square" or apo.color != PALETTE["apoapsis"]:
            return f"{name} / apoapsis marker"
        if orbit.ra is None or not close_enough(_distance(apo.km, (0.0, 0.0, 0.0)) * 1000.0, orbit.ra, orbit.ra):
            return f"{name} / apoapsis radius"
        if _off_drawn_curve(apo.km, scene) > 1e-3:
            return f"{name} / apoapsis is off the drawn orbit"
        if "apoapsis" not in legend or "inclination" not in legend:
            return f"{name} / legend entries"
        if scene.kepler.period is None or scene.kepler.M is None or scene.kepler.ellipse_wall_s != ELLIPSE_WALL_S:
            return f"{name} / ellipse motion"
        if "period_s" not in values or "ra_m" not in values or "M_rad" not in values:
            return f"{name} / stdout ellipse"
        if not scene.show_wedge or len(scene.wedge_km) < 3:
            return f"{name} / wedge"
    else:
        if apo is not None or "apoapsis" in legend:
            return f"{name} / hyperbola drew apoapsis"
        if scene.kepler.period is not None or scene.kepler.M is not None:
            return f"{name} / hyperbola invented a period"
        if scene.kepler.open_arc_wall_s != OPEN_ARC_WALL_S:
            return f"{name} / hyperbola rate"
        if not (scene.kepler.nu_min < orbit.nu < scene.kepler.nu_max):
            return f"{name} / hyperbola window {scene.kepler.nu_min} {orbit.nu} {scene.kepler.nu_max}"
        if values.get("period") != "none" or values.get("apoapsis") != "none" or values.get("M") != "none":
            return f"{name} / stdout hyperbola"
        if not scene.show_wedge:
            return f"{name} / wedge"
    wedge_problem = _wedge_problem(scene, orbit)
    if wedge_problem:
        return f"{name} / {wedge_problem}"
    return None


def _run_known_case(
    name: str, argv: list[str], png: str, conic: str
) -> tuple[str | None, dict[str, str], Scene | None]:
    code, text, err = invoke(argv + ["--out", png])
    if code != 0:
        return f"{name} main returned {code}: {err}", {}, None
    values = parse_stdout(text)
    issue = viewer_issues(text, png)
    if issue:
        return f"{name} / {issue}", values, None
    if "graph" not in values or Path(values["graph"]).resolve() != Path(png).resolve():
        return f"{name} / graph path", values, None
    if "viewer" not in values:
        return f"{name} / viewer path", values, None
    ns = parse_args(argv)
    body = resolve_body(ns.R0, ns.flattening)
    elev, azim = resolve_camera(ns.elev, ns.azim)
    orbit = resolve_request(ns, body)
    scene = build_scene(body, orbit, elev, azim)
    html = Path(values["viewer"]).read_text(encoding="utf-8")
    png_bytes = Path(png).read_bytes()
    return _checklist_issue(name, scene, orbit, values, html, png_bytes, conic), values, scene


def visual_checklist() -> int:
    """Side-by-side PNG/HTML checklist for the known Earth ellipse and hyperbola."""

    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    opened: list[str] = []

    def _open(url: str) -> bool:
        opened.append(url)
        return True

    previous_open = webbrowser.open
    webbrowser.open = _open
    try:
        with tempfile.TemporaryDirectory() as tmp:
            ellipse_png = str(Path(tmp) / "earth_ellipse.png")
            issue, ellipse_values, ellipse_scene = _run_known_case(
                "earth ellipse", EARTH_ELLIPSE_ARGV + ["--open"], ellipse_png, "ellipse"
            )
            if issue or ellipse_scene is None:
                return fail(issue or "earth ellipse missing")
            if opened != [Path(ellipse_values["viewer"]).resolve().as_uri()]:
                return fail(f"earth ellipse / --open {opened}")
            opened.clear()

            hyperbola_png = str(Path(tmp) / "earth_hyperbola.png")
            issue, _hyperbola_values, hyperbola_scene = _run_known_case(
                "earth hyperbola", EARTH_HYPERBOLA_ARGV, hyperbola_png, "hyperbola"
            )
            if issue or hyperbola_scene is None:
                return fail(issue or "earth hyperbola missing")
            if opened:
                return fail("--open ran without the flag")

            flat_png = str(Path(tmp) / "earth_ellipse_flat.png")
            issue, flat_values, flat_scene = _run_known_case(
                "earth ellipse flattening",
                EARTH_ELLIPSE_ARGV + ["--flattening", "0.2"],
                flat_png,
                "ellipse",
            )
            if issue or flat_scene is None:
                return fail(issue or "earth ellipse flattening missing")
            for key in _UNCHANGED_WHEN_FLATTENED:
                if ellipse_values.get(key) != flat_values.get(key):
                    return fail(f"flattening changed {key}")
            if flat_values.get("flattening") == ellipse_values.get("flattening"):
                return fail("flattening flag did not change the printed flattening")
            if abs(flat_scene.kepler.mu - ellipse_scene.kepler.mu) > 1.0:
                return fail("flattening changed mu")
            if flat_scene.polar_radius_km >= ellipse_scene.polar_radius_km:
                return fail("flattening did not squash the body")
            if abs(flat_scene.equatorial_radius_km - ellipse_scene.equatorial_radius_km) > 1e-6:
                return fail("flattening changed the equatorial radius")
            if Path(ellipse_png).read_bytes() == Path(flat_png).read_bytes():
                return fail("flattening left the PNG unchanged")
            if not hyperbola_scene.show_wedge or not ellipse_scene.show_wedge:
                return fail("known inclined cases omitted the wedge")
    finally:
        webbrowser.open = previous_open

    print("visual checklist: earth ellipse pass")
    print("visual checklist: earth hyperbola pass")
    print("visual checklist: flattening pass")
    return 0


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    body = resolve_body(None, None)
    if body.radius_source != "default" or body.radius != R0_EARTH:
        return fail("Earth radius default")
    if not close_enough(body.mu, G0 * R0_EARTH**2, body.mu):
        return fail("mu is not g0*R0^2")
    if not close_enough(body.flattening, F_EARTH, 1.0):
        return fail("default flattening")
    custom = resolve_body(1.0e6, None)
    if custom.flattening != 0.0 or custom.radius_source != "input":
        return fail("a non-default radius was not a sphere")
    forced = resolve_body(None, 0.01)
    if not close_enough(forced.flattening, 0.01, 1.0):
        return fail("flattening override")

    # Equatorial ellipse at periapsis: closed form, mu = 1, a = 4, e = 1/2.
    simple = orbit_from_elements(1.0, 4.0, 0.5, 0.0, 0.0, 0.0, 0.0, None, "elements")
    if simple.conic != "ellipse":
        return fail("periapsis case was not an ellipse")
    if not vector_close((simple.rx, simple.ry, simple.rz), (2.0, 0.0, 0.0)):
        return fail(f"periapsis position {simple.rx, simple.ry, simple.rz}")
    speed_y = math.sqrt(3.0) / 2.0
    if not vector_close((simple.vx, simple.vy, simple.vz), (0.0, speed_y, 0.0)):
        return fail(f"periapsis velocity {simple.vx, simple.vy, simple.vz}")
    if not close_enough(simple.energy, -0.125, 1.0):
        return fail("periapsis energy")
    if not close_enough(simple.p, 3.0, 1.0):
        return fail("periapsis parameter")
    if not close_enough(simple.h, math.sqrt(3.0), 1.0):
        return fail("periapsis angular momentum")
    if not close_enough(simple.rp, 2.0, 1.0) or not close_enough(simple.ra or 0.0, 6.0, 1.0):
        return fail("periapsis radii")
    expected_period = 16.0 * math.pi
    if simple.period is None or not close_enough(simple.period, expected_period, expected_period):
        return fail("periapsis period")
    from_speed = specific_orbital_energy_from_speed(speed_y, 1.0, 2.0)
    if not close_enough(from_speed, specific_orbital_energy(1.0, 4.0), 1.0):
        return fail("energy from speed does not match specific_orbital_energy")
    if not close_enough(simple.h, specific_angular_momentum(1.0, simple.p), simple.h):
        return fail("h is not sqrt(mu*p)")

    # Same ellipse at true anomaly pi/2. Position and velocity are expanded by hand.
    quarter = orbit_from_elements(1.0, 4.0, 0.5, 0.0, 0.0, 0.0, math.pi / 2.0, None, "elements")
    if not vector_close((quarter.rx, quarter.ry, quarter.rz), (0.0, 3.0, 0.0)):
        return fail(f"quarter position {quarter.rx, quarter.ry, quarter.rz}")
    quarter_v = (-math.sqrt(3.0) / 3.0, math.sqrt(3.0) / 6.0, 0.0)
    if not vector_close((quarter.vx, quarter.vy, quarter.vz), quarter_v):
        return fail(f"quarter velocity {quarter.vx, quarter.vy, quarter.vz}")
    if not angle_close(quarter.nu, math.pi / 2.0):
        return fail("quarter true anomaly")

    # Polar circle at the top of the orbit: position on +Z, velocity toward -X.
    polar = orbit_from_elements(1.0, 2.0, 0.0, math.pi / 2.0, 0.0, 0.0, math.pi / 2.0, None, "elements")
    if not vector_close((polar.rx, polar.ry, polar.rz), (0.0, 0.0, 2.0)):
        return fail(f"polar position {polar.rx, polar.ry, polar.rz}")
    polar_speed = math.sqrt(0.5)
    if not vector_close((polar.vx, polar.vy, polar.vz), (-polar_speed, 0.0, 0.0)):
        return fail(f"polar velocity {polar.vx, polar.vy, polar.vz}")
    if polar.omega != 0.0 or not angle_close(polar.nu, math.pi / 2.0):
        return fail("a circle did not put periapsis at the node")
    if polar.M is None or not angle_close(polar.M, polar.nu):
        return fail("circular mean anomaly is not the argument of latitude")
    # A supplied argument of periapsis on a circle is absorbed into the anomaly.
    circle = orbit_from_elements(1.0, 2.0, 0.0, 0.5, 0.3, 0.4, 0.2, None, "elements")
    if circle.omega != 0.0 or not angle_close(circle.nu, 0.6) or circle.M is None:
        return fail(f"circular convention {circle.omega, circle.nu, circle.M}")
    if not angle_close(circle.M, 0.6) or not angle_close(circle.Omega, 0.3):
        return fail("circular mean anomaly or node")

    # Inclined ellipse with every angle away from zero. Angles and h must return.
    inc = 0.7
    node = 1.1
    peri = 0.5
    nu = -0.4
    inclined = orbit_from_elements(1.0, 4.0, 0.3, inc, node, peri, nu, None, "elements")
    if inclined.a is None or not close_enough(inclined.a, 4.0, 4.0):
        return fail(f"round-trip semi-major {inclined.a}")
    if not close_enough(inclined.e, 0.3, 1.0):
        return fail(f"round-trip eccentricity {inclined.e}")
    if not angle_close(inclined.i, inc) or not angle_close(inclined.Omega, node):
        return fail(f"round-trip plane {inclined.i, inclined.Omega}")
    if not angle_close(inclined.omega, peri) or not angle_close(inclined.nu, nu):
        return fail(f"round-trip periapsis angles {inclined.omega, inclined.nu}")
    parameter = semi_latus_rectum(4.0, 0.3)
    h_mag = specific_angular_momentum(1.0, parameter)
    expected_h = (
        h_mag * math.sin(inc) * math.sin(node),
        -h_mag * math.sin(inc) * math.cos(node),
        h_mag * math.cos(inc),
    )
    if not vector_close((inclined.hx, inclined.hy, inclined.hz), expected_h):
        return fail(f"angular momentum direction {inclined.hx, inclined.hy, inclined.hz}")
    rebuilt = state_from_elements(
        1.0, inclined.a, inclined.e, inclined.i, inclined.Omega, inclined.omega, inclined.nu
    )
    if not vector_close(rebuilt, (inclined.rx, inclined.ry, inclined.rz, inclined.vx, inclined.vy, inclined.vz)):
        return fail("rebuilt state did not match")
    speed = math.sqrt(inclined.vx**2 + inclined.vy**2 + inclined.vz**2)
    radius = math.sqrt(inclined.rx**2 + inclined.ry**2 + inclined.rz**2)
    if not close_enough(
        specific_orbital_energy_from_speed(speed, 1.0, radius),
        specific_orbital_energy(1.0, 4.0),
        1.0,
    ):
        return fail("inclined energy")
    if not close_enough(inclined.h, h_mag, h_mag):
        return fail("inclined h")

    # On the node, the position lies in the equator along Omega.
    on_node = orbit_from_elements(1.0, 4.0, 0.3, inc, node, 0.4, -0.4, None, "elements")
    node_radius = math.sqrt(on_node.rx**2 + on_node.ry**2 + on_node.rz**2)
    if not vector_close(
        (on_node.rx, on_node.ry, on_node.rz),
        (node_radius * math.cos(node), node_radius * math.sin(node), 0.0),
    ):
        return fail("node position is not in the equator")

    # u = pi/2 puts the craft on the orbit-normal tilt of the node.
    raised = orbit_from_elements(1.0, 4.0, 0.3, inc, node, 0.0, math.pi / 2.0, None, "elements")
    raised_r = math.sqrt(raised.rx**2 + raised.ry**2 + raised.rz**2)
    expected_raised = (
        -raised_r * math.sin(node) * math.cos(inc),
        raised_r * math.cos(node) * math.cos(inc),
        raised_r * math.sin(inc),
    )
    if not vector_close((raised.rx, raised.ry, raised.rz), expected_raised):
        return fail(f"raised position {raised.rx, raised.ry, raised.rz}")

    # Equatorial prograde: Omega is conventional and longitude of periapsis is kept.
    equator = orbit_from_elements(1.0, 4.0, 0.3, 0.0, 0.8, 0.3, 0.4, None, "elements")
    if equator.Omega != 0.0:
        return fail("equatorial Omega was not 0")
    if not angle_close(equator.omega, 1.1) or not angle_close(equator.nu, 0.4):
        return fail(f"equatorial periapsis {equator.omega, equator.nu}")

    # Retrograde equator: Omega is 0 and the state repeats.
    retrograde = orbit_from_elements(1.0, 4.0, 0.3, math.pi, 0.5, 0.4, 0.2, None, "elements")
    if not angle_close(retrograde.i, math.pi) or retrograde.Omega != 0.0:
        return fail("retrograde equator convention")
    if not angle_close(retrograde.nu, 0.2):
        return fail("retrograde true anomaly")
    retrograde_state = state_from_elements(
        1.0,
        retrograde.a if retrograde.a is not None else 0.0,
        retrograde.e,
        retrograde.i,
        retrograde.Omega,
        retrograde.omega,
        retrograde.nu,
    )
    if not vector_close(
        retrograde_state,
        (retrograde.rx, retrograde.ry, retrograde.rz, retrograde.vx, retrograde.vy, retrograde.vz),
    ):
        return fail("retrograde state did not repeat")

    # Mean anomaly solves kepler_equation and matches the true-anomaly path.
    eccentric_anomaly = 1.2
    eccentricity = 0.3
    mean = kepler_equation(eccentric_anomaly, eccentricity)
    solved = solve_kepler(mean, eccentricity)
    if not close_enough(solved, eccentric_anomaly, 1.0):
        return fail(f"Kepler solve {solved} != {eccentric_anomaly}")
    solved_nu = nu_from_eccentric(eccentricity, solved)
    by_nu = orbit_from_elements(1.0, 4.0, eccentricity, inc, node, peri, solved_nu, None, "elements")
    by_mean = orbit_from_elements(1.0, 4.0, eccentricity, inc, node, peri, None, mean, "elements")
    if not vector_close(
        (by_mean.rx, by_mean.ry, by_mean.rz, by_mean.vx, by_mean.vy, by_mean.vz),
        (by_nu.rx, by_nu.ry, by_nu.rz, by_nu.vx, by_nu.vy, by_nu.vz),
    ):
        return fail("--M state does not match --nu")
    if by_mean.M is None or not angle_close(by_mean.M, wrap_pi(mean)):
        return fail("printed mean anomaly")
    if by_nu.M is None:
        return fail("ellipse did not print a mean anomaly")
    high = solve_kepler(2.5, 0.99)
    if not close_enough(kepler_equation(high, 0.99), wrap_pi(2.5), 1.0):
        return fail("high-eccentricity Kepler residual")

    # Hyperbola at periapsis, then off periapsis against the polar-equation derivative.
    hyperbola = orbit_from_elements(1.0, -4.0, 2.0, 0.0, 0.0, 0.0, 0.0, None, "elements")
    if hyperbola.conic != "hyperbola" or hyperbola.period is not None or hyperbola.ra is not None:
        return fail("hyperbola still has a period or an apoapsis")
    if hyperbola.M is not None or hyperbola.a is None:
        return fail("hyperbola mean anomaly or axis")
    if not close_enough(hyperbola.a, -4.0, 4.0):
        return fail("hyperbola axis")
    if not close_enough(hyperbola.energy, 0.125, 1.0):
        return fail("hyperbola energy")
    if not vector_close((hyperbola.rx, hyperbola.ry, hyperbola.rz), (4.0, 0.0, 0.0)):
        return fail("hyperbola periapsis position")
    if not vector_close((hyperbola.vx, hyperbola.vy, hyperbola.vz), (0.0, math.sqrt(3.0) / 2.0, 0.0)):
        return fail("hyperbola periapsis velocity")
    if not close_enough(hyperbola.rp, 4.0, 1.0) or not close_enough(hyperbola.p, 12.0, 1.0):
        return fail("hyperbola periapsis and parameter")
    branch_nu = 0.4
    branch_p = 12.0
    branch_r = branch_p / (1.0 + 2.0 * math.cos(branch_nu))
    branch_h = math.sqrt(12.0)
    branch_vr = (branch_h * 2.0 / branch_p) * math.sin(branch_nu)
    branch_vp = branch_h / branch_r
    branch_x = branch_r * math.cos(branch_nu)
    branch_y = branch_r * math.sin(branch_nu)
    branch_vx = (branch_vr / branch_r) * branch_x - branch_vp * math.sin(branch_nu)
    branch_vy = (branch_vr / branch_r) * branch_y + branch_vp * math.cos(branch_nu)
    branch = orbit_from_elements(1.0, -4.0, 2.0, 0.0, 0.0, 0.0, branch_nu, None, "elements")
    if not vector_close(
        (branch.rx, branch.ry, branch.rz, branch.vx, branch.vy, branch.vz),
        (branch_x, branch_y, 0.0, branch_vx, branch_vy, 0.0),
    ):
        return fail(f"hyperbola branch state {branch.rx, branch.ry, branch.rz, branch.vx, branch.vy, branch.vz}")
    if not angle_close(branch.nu, branch_nu) or branch.period is not None:
        return fail("hyperbola branch anomaly or period")
    turned = orbit_from_elements(1.0, -4.0, 1.5, 0.4, 0.8, 0.6, 0.3, None, "elements")
    if turned.a is None or not close_enough(turned.a, -4.0, 4.0) or not close_enough(turned.e, 1.5, 1.0):
        return fail("inclined hyperbola elements")
    if not angle_close(turned.i, 0.4) or not angle_close(turned.Omega, 0.8):
        return fail("inclined hyperbola plane")
    if not angle_close(turned.omega, 0.6) or not angle_close(turned.nu, 0.3):
        return fail("inclined hyperbola angles")

    # Parabola from an escape state. Energy is zero and there is no period.
    escape = math.sqrt(2.0 * 1.0 / 2.0)
    parabola = orbit_from_state(1.0, 2.0, 0.0, 0.0, 0.0, escape, 0.0, "state")
    if parabola.conic != "parabola" or parabola.a is not None:
        return fail("escape was not a parabola")
    if parabola.period is not None or parabola.ra is not None or parabola.M is not None:
        return fail("parabola still has a period, apoapsis, or mean anomaly")
    if not close_enough(parabola.e, 1.0, 1.0) or not close_enough(parabola.energy, 0.0, 1.0):
        return fail("parabola eccentricity or energy")
    if not close_enough(parabola.p, 4.0, 1.0) or not close_enough(parabola.rp, 2.0, 1.0):
        return fail("parabola parameter")
    if not angle_close(parabola.nu, 0.0) or not angle_close(parabola.i, 0.0):
        return fail("parabola anomaly or inclination")
    open_nu = 0.5
    open_p = 2.0
    open_h = math.sqrt(2.0)
    open_r = open_p / (1.0 + math.cos(open_nu))
    open_vr = (open_h * math.sin(open_nu)) / open_p
    open_vp = open_h / open_r
    open_x = open_r * math.cos(open_nu)
    open_y = open_r * math.sin(open_nu)
    open_vx = (open_vr / open_r) * open_x - open_vp * math.sin(open_nu)
    open_vy = (open_vr / open_r) * open_y + open_vp * math.cos(open_nu)
    open_orbit = orbit_from_state(1.0, open_x, open_y, 0.0, open_vx, open_vy, 0.0, "state")
    if open_orbit.conic != "parabola" or not angle_close(open_orbit.nu, open_nu):
        return fail(f"open parabola anomaly {open_orbit.conic} {open_orbit.nu}")
    if not close_enough(open_orbit.energy, 0.0, 1.0) or not close_enough(open_orbit.p, open_p, 1.0):
        return fail("open parabola energy or parameter")

    try:
        orbit_from_elements(1.0, 4.0, 1.0, 0.0, 0.0, 0.0, 0.0, None, "elements")
    except ValueError:
        pass
    else:
        return fail("a parabolic semi-major axis was accepted")
    try:
        orbit_from_elements(1.0, 4.0, 1.4, 0.0, 0.0, 0.0, 0.0, None, "elements")
    except ValueError:
        pass
    else:
        return fail("a positive axis was accepted for a hyperbola")
    try:
        orbit_from_state(1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, "state")
    except ValueError:
        pass
    else:
        return fail("a rectilinear state was accepted")

    for label, sample, mu in (
        ("periapsis", simple, 1.0),
        ("quarter", quarter, 1.0),
        ("inclined", inclined, 1.0),
        ("hyperbola", branch, 1.0),
        ("parabola", open_orbit, 1.0),
    ):
        del mu
        point = position_at_true(sample, sample.nu)
        speed = velocity_at_true(sample, sample.nu)
        if not vector_close(
            (point[0], point[1], point[2], speed[0], speed[1], speed[2]),
            (sample.rx, sample.ry, sample.rz, sample.vx, sample.vy, sample.vz),
        ):
            return fail(f"{label} element-to-state drift")

    strokes_near, strokes_far = split_orbit_strokes(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0)),
        [False, False, True, True],
    )
    if strokes_near != [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]]:
        return fail(f"near stroke dropped the limb {strokes_near}")
    if strokes_far != [[(2.0, 0.0, 0.0), (3.0, 0.0, 0.0)]]:
        return fail(f"far stroke dropped the limb {strokes_far}")

    plt = ensure_matplotlib()
    basis_figure = plt.figure()
    basis_ax = basis_figure.add_subplot(111, projection="3d")
    try:
        basis_ax.set_box_aspect((1.0, 1.0, 1.0))
    except (AttributeError, TypeError):
        pass
    try:
        for elev_sample, azim_sample, roll_sample in (
            (20.0, 35.0, 0.0),
            (0.0, 0.0, 0.0),
            (20.0, 35.0, 90.0),
            (-25.0, 200.0, 0.0),
        ):
            try:
                basis_ax.view_init(elev=elev_sample, azim=azim_sample, roll=roll_sample)
            except TypeError:
                if roll_sample != 0.0:
                    continue
                basis_ax.view_init(elev=elev_sample, azim=azim_sample)
            basis_ax.get_proj()
            got_right, got_up, got_out = view_basis(elev_sample, azim_sample, roll_sample)
            for name, got, mpl in (
                ("right", got_right, basis_ax._view_u),
                ("up", got_up, basis_ax._view_v),
                ("out", got_out, basis_ax._view_w),
            ):
                if any(abs(float(left) - float(right)) > 1e-6 for left, right in zip(got, mpl)):
                    return fail(f"camera {name} at elev {elev_sample} azim {azim_sample} roll {roll_sample}")
        pole_right, pole_up, pole_out = view_basis(90.0, 125.0, 0.0)
        azim_rad = math.radians(125.0)
        expected_right = (-math.sin(azim_rad), math.cos(azim_rad), 0.0)
        if any(abs(left - right) > 1e-9 for left, right in zip(pole_right, expected_right)):
            return fail(f"pole screen-right {pole_right}")
        if abs(pole_out[2] - 1.0) > 1e-9 or abs(pole_up[2]) > 1e-6:
            return fail("pole view is not looking down +Z")
        apply_matplotlib_view(basis_ax, 90.0, 125.0, 0.0)
        basis_ax.get_proj()
        for name, got, mpl in (
            ("right", pole_right, basis_ax._view_u),
            ("up", pole_up, basis_ax._view_v),
        ):
            if any(abs(float(left) - float(right)) > 1e-5 for left, right in zip(got, mpl)):
                return fail(f"pole PNG camera {name} {tuple(float(c) for c in mpl)}")
    finally:
        plt.close(basis_figure)

    earth = resolve_body(None, None)
    squashed = resolve_body(None, 0.2)
    pictured = orbit_from_elements(earth.mu, 1.0e7, 0.3, 0.9, 0.6, 1.2, 0.8, None, "elements")
    pictured_scene = build_scene(earth, pictured, 90.0, 125.0)
    squashed_scene = build_scene(squashed, pictured, 90.0, 125.0)
    if not close_enough(pictured_scene.kepler.mu, squashed_scene.kepler.mu, pictured_scene.kepler.mu):
        return fail("flattening changed mu in the scene")
    if not close_enough(squashed_scene.polar_radius_km, earth.radius * (1.0 - 0.2) / 1000.0, 1.0):
        return fail("visual polar radius")
    if squashed_scene.polar_radius_km >= pictured_scene.polar_radius_km:
        return fail("flattening did not squash the spheroid")
    if not close_enough(pictured_scene.equatorial_radius_km, squashed_scene.equatorial_radius_km, 1.0):
        return fail("flattening changed the equatorial radius")
    craft_m = (
        pictured_scene.craft_km[0] * 1000.0,
        pictured_scene.craft_km[1] * 1000.0,
        pictured_scene.craft_km[2] * 1000.0,
    )
    if not vector_close(craft_m, (pictured.rx, pictured.ry, pictured.rz)):
        return fail("scene craft is not the epoch state")
    pictured_wedge = _wedge_problem(pictured_scene, pictured)
    if pictured_wedge:
        return fail(pictured_wedge)
    node_marker = next(marker for marker in pictured_scene.markers if marker.id == "ascending_node")
    if abs(node_marker.km[2]) > 1e-6:
        return fail("ascending node is off the equator")
    if not any(marker.id == "apoapsis" for marker in pictured_scene.markers):
        return fail("ellipse scene omitted apoapsis")
    equator_scene = build_scene(
        earth,
        orbit_from_elements(earth.mu, 1.0e7, 0.2, 0.0, 0.4, 0.3, 0.2, None, "elements"),
        90.0,
        125.0,
    )
    if equator_scene.show_wedge:
        return fail("equatorial scene drew a wedge")
    open_scene = build_scene(
        earth,
        orbit_from_elements(earth.mu, -2.0e7, 1.5, 0.6, 0.4, 0.2, 0.5, None, "elements"),
        25.0,
        40.0,
    )
    if any(marker.id == "apoapsis" for marker in open_scene.markers):
        return fail("hyperbola scene drew apoapsis")
    if open_scene.kepler.period is not None or open_scene.kepler.nu_max <= open_scene.kepler.nu_min:
        return fail("hyperbola animation window")
    labels = [entry.label for entry in pictured_scene.legend]
    if labels != [
        "planet",
        "equatorial plane",
        "orbit",
        "ascending node",
        "inclination",
        "periapsis",
        "apoapsis",
        "spacecraft",
        "radius",
        "velocity",
    ]:
        return fail(f"legend order {labels}")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "orbit.png")
        code, text, err = invoke(
            [
                "--a",
                "10000000",
                "--e",
                "0.2",
                "--i",
                "0.7",
                "--raan",
                "0.5",
                "--aop",
                "0.4",
                "--nu",
                "1.0",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"elements main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("elements run did not write a PNG")
        values = parse_stdout(text)
        for key in (
            "title",
            "assumptions",
            "mode",
            "R0_m",
            "mu_m3_s2",
            "a_m",
            "e",
            "i_rad",
            "Omega_rad",
            "omega_rad",
            "nu_rad",
            "M_rad",
            "p_m",
            "energy_J_kg",
            "h_m2_s",
            "hx_m2_s",
            "hy_m2_s",
            "hz_m2_s",
            "rp_m",
            "ra_m",
            "period_s",
            "rx_m",
            "ry_m",
            "rz_m",
            "vx_m_s",
            "vy_m_s",
            "vz_m_s",
            "conic",
            "elev_deg",
            "azim_deg",
            "graph",
            "viewer",
        ):
            if key not in values:
                return fail(f"stdout missing {key}")
        if values["title"] != PLOT_TITLE or values["mode"] != "elements":
            return fail("title or mode")
        if values["conic"] != "ellipse":
            return fail("elements conic")
        if values["elev_deg"] != "20" or values["azim_deg"] != "35":
            return fail("default camera")
        if "period: none" in text or "apoapsis: none" in text:
            return fail("ellipse omitted the period or apoapsis")
        issue = viewer_issues(text, out)
        if issue:
            return fail(issue)
        ellipse_scene = scene_from_html(Path(values["viewer"]).read_text(encoding="utf-8"))
        ellipse_labels = [item["label"] for item in ellipse_scene["legend"]]
        for label in ("ascending node", "periapsis", "apoapsis", "spacecraft", "equatorial plane", "inclination"):
            if label not in ellipse_labels:
                return fail(f"ellipse viewer missing {label}")
        if ellipse_scene["title"] != PLOT_TITLE or ellipse_scene["kepler"]["conic"] != "ellipse":
            return fail("ellipse viewer payload")
        craft_marker = next(item for item in ellipse_scene["markers"] if item["id"] == "spacecraft")
        if abs(craft_marker["km"][0] - float(values["rx_m"]) / 1000.0) > 1e-4:
            return fail("viewer craft is not the printed state")
        if abs(ellipse_scene["elev_deg"] - 20.0) > 1e-9 or abs(ellipse_scene["azim_deg"] - 35.0) > 1e-9:
            return fail("viewer camera")
        if abs(ellipse_scene["roll_deg"]) > 1e-9:
            return fail("viewer roll")

        mean_out = str(Path(tmp) / "mean.png")
        code_nu, text_nu, err_nu = invoke(
            [
                "--a",
                "10000000",
                "--e",
                "0.2",
                "--i",
                "0.7",
                "--raan",
                "0.5",
                "--aop",
                "0.4",
                "--nu",
                "1.0",
                "--out",
                mean_out,
            ]
        )
        code_m, text_m, err_m = invoke(
            [
                "--a",
                "10000000",
                "--e",
                "0.2",
                "--i",
                "0.7",
                "--raan",
                "0.5",
                "--aop",
                "0.4",
                "--M",
                parse_stdout(text_nu)["M_rad"],
                "--out",
                str(Path(tmp) / "from_mean.png"),
            ]
        )
        if code_nu != 0 or code_m != 0:
            return fail(f"mean-anomaly main failed: {err_nu} {err_m}")
        nu_values = parse_stdout(text_nu)
        mean_values = parse_stdout(text_m)
        if abs(float(nu_values["rx_m"]) - float(mean_values["rx_m"])) > 1.0:
            return fail("CLI --M did not match --nu")
        if abs(float(nu_values["nu_rad"]) - float(mean_values["nu_rad"])) > 1e-5:
            return fail("CLI true anomaly disagreed")

        state_out = str(Path(tmp) / "state.png")
        code, text, err = invoke(
            [
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
                "--elev",
                "25",
                "--azim",
                "40",
                "--out",
                state_out,
            ]
        )
        if code != 0:
            return fail(f"state main returned {code}: {err}")
        if not Path(state_out).read_bytes().startswith(b"\x89PNG"):
            return fail("state run did not write a PNG")
        state_values = parse_stdout(text)
        if state_values.get("mode") != "state" or "conic" not in state_values:
            return fail("state stdout")
        if state_values.get("elev_deg") != "25" or state_values.get("azim_deg") != "40":
            return fail("camera flags")
        state_issue = viewer_issues(text, state_out)
        if state_issue:
            return fail(state_issue)

        hyper_out = str(Path(tmp) / "hyperbola.png")
        code, text, err = invoke(
            [
                "--a",
                "-20000000",
                "--e",
                "1.5",
                "--i",
                "0.6",
                "--raan",
                "0.4",
                "--aop",
                "0.2",
                "--nu",
                "0.5",
                "--out",
                hyper_out,
            ]
        )
        if code != 0:
            return fail(f"hyperbola main returned {code}: {err}")
        if not Path(hyper_out).read_bytes().startswith(b"\x89PNG"):
            return fail("hyperbola run did not write a PNG")
        if "period: none" not in text or "apoapsis: none" not in text or "M: none" not in text:
            return fail("hyperbola stdout still has a period, apoapsis, or mean anomaly")
        if parse_stdout(text).get("conic") != "hyperbola":
            return fail("hyperbola conic label")
        hyper_issue = viewer_issues(text, hyper_out)
        if hyper_issue:
            return fail(hyper_issue)
        hyper_scene = scene_from_html(Path(parse_stdout(text)["viewer"]).read_text(encoding="utf-8"))
        hyper_labels = [item["label"] for item in hyper_scene["legend"]]
        if "apoapsis" in hyper_labels or any(item["id"] == "apoapsis" for item in hyper_scene["markers"]):
            return fail("hyperbola viewer still has apoapsis")
        if "periapsis" not in hyper_labels or "spacecraft" not in hyper_labels:
            return fail("hyperbola viewer missing markers")
        if hyper_scene["kepler"]["period"] is not None or hyper_scene["kepler"]["conic"] != "hyperbola":
            return fail("hyperbola viewer kepler payload")
        if hyper_scene["show_wedge"] is not True:
            return fail("hyperbola viewer omitted the wedge")

    rejections = (
        ["--a", "1e7", "--e", "0.1", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0.2", "--M", "0.2"],
        ["--a", "1e7", "--e", "0.1", "--i", "0.2", "--raan", "0.1", "--aop", "0.1"],
        ["--a", "1e7", "--e", "0.1", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0", "--rx", "1"],
        ["--rx", "8000000", "--ry", "0", "--rz", "0", "--vx", "0", "--vy", "7000"],
        ["--a", "-2e7", "--e", "1.4", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--M", "0.2"],
        ["--a", "-2e7", "--e", "1.4", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "3"],
        ["--rx", "1", "--ry", "0", "--rz", "0", "--vx", "1", "--vy", "0", "--vz", "0"],
        [],
    )
    for argv in rejections:
        code, _text, err = invoke(argv)
        if code != 2 or not err.startswith("error:"):
            return fail(f"expected exit 2 for {argv}, got {code}: {err}")

    visual = visual_checklist()
    if visual != 0:
        return visual

    print("check: pass")
    print_kv("unit_period_s", simple.period)
    print_kv("unit_h_m2_s", simple.h)
    print_kv("inclined_nu_rad", inclined.nu)
    return 0


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _bind_negative_values(argv: list[str]) -> list[str]:
    """Keep a leading minus on a numeric value attached to its flag.

    argparse otherwise treats ``--a -2e7`` as an unknown optional argument.
    """
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
        "--R0",
        "--flattening",
        "--elev",
        "--azim",
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
        description="Classical orbital elements and the inertial state of a Keplerian conic."
    )
    parser.add_argument("--a", type=float, default=None, help="semi-major axis [m]; negative on a hyperbola")
    parser.add_argument("--e", type=float, default=None, help="eccentricity, dimensionless")
    parser.add_argument("--i", type=float, default=None, help="inclination [rad], 0 <= i <= pi")
    parser.add_argument("--raan", type=float, default=None, help="longitude of the ascending node [rad]")
    parser.add_argument("--aop", type=float, default=None, help="argument of periapsis [rad]")
    parser.add_argument("--nu", type=float, default=None, help="true anomaly [rad]")
    parser.add_argument("--M", type=float, default=None, help="mean anomaly [rad], ellipse only")
    parser.add_argument("--rx", type=float, default=None, help="inertial position x [m]")
    parser.add_argument("--ry", type=float, default=None, help="inertial position y [m]")
    parser.add_argument("--rz", type=float, default=None, help="inertial position z [m]")
    parser.add_argument("--vx", type=float, default=None, help="inertial velocity x [m/s]")
    parser.add_argument("--vy", type=float, default=None, help="inertial velocity y [m/s]")
    parser.add_argument("--vz", type=float, default=None, help="inertial velocity z [m/s]")
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"planetary radius [m]; default Earth {R0_EARTH:.8g}",
    )
    parser.add_argument(
        "--flattening",
        type=float,
        default=None,
        help="visual polar flattening; Earth default 1/298.257, otherwise 0",
    )
    parser.add_argument("--elev", type=float, default=None, help=f"camera elevation [deg]; default {ELEV_DEG:g}")
    parser.add_argument("--azim", type=float, default=None, help=f"camera azimuth [deg]; default {AZIM_DEG:g}")
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


if __name__ == "__main__":
    sys.exit(main())
