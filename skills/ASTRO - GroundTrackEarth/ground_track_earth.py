#!/usr/bin/env python3
"""Subsatellite ground track of an Earth ellipse.

Keplerian mean anomaly, Greenwich angle, Earth-fixed axes, and geodetic
latitude come from the flight records in formulas.md. First-order J2 secular
nodal and apsidal rates are the same records as ASTRO - J2SecularRates.
Flattening changes the footprint only; it does not enter mu.
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Two-body Earth radius and g0 match the other ASTRO programs.
# Ellipsoid a_e, f, and omega_E are WGS 84 (NIMA TR 8350.2 / NGA.STND.0036).
G0 = 9.80665
R0_EARTH = 6.3742e6
AE_WGS84 = 6378137.0
F_WGS84 = 1.0 / 298.257223563
OMEGA_E = 7.292115e-5
J2_GSFC = 1.08228e-3
PLOT_TITLE = "ASTRO - GroundTrackEarth"
CHECK_TOL = 1e-9
CIRCULAR_E = 1e-7
EQUATORIAL_FRAC = 1e-10
DEFAULT_SAMPLES_PER_ORBIT = 361
DEFAULT_ORBITS = 10
# Natural Earth 1:110m land, public domain (naturalearthdata.com terms of use).
LAND_SHAPEFILE = Path(__file__).resolve().parent / "data" / "ne_110m_land.shp"
_OP = None
ASSUMPTIONS = (
    "ellipse with inverse-square mean motion; first-order J2 secular rates from "
    "ASTRO - J2SecularRates: Omega and omega use j2_nodal_rate and j2_apsidal_rate; "
    "a, e, and i have no secular J2 rate; drag, third body, higher zonals, and the "
    "J2 mean-motion correction are omitted; planetary flattening enters the "
    "geodetic latitude of the subsatellite point only and does not enter mu; "
    "mu = g0*R0^2 with g0 = 9.80665 m/s^2; Earth default R0 = 6374200 m; WGS 84 "
    "ellipsoid ae = 6378137 m, f = 1/298.257223563, and omega_E = 7.292115e-5 rad/s; "
    "RE in the J2 term is that ae; J2 default is 1.08228e-3 (GSFC, March 1986, "
    "NASA RP-1204); Greenwich angle is greenwich_angle; Earth-fixed position is "
    "earth_fixed_x, earth_fixed_y, and earth_fixed_z; geocentric latitude uses "
    "geocentric_latitude_sine and geocentric_latitude_cosine; longitude uses "
    "longitude_sine and longitude_cosine; geodetic latitude is "
    "geodetic_latitude_from_geocentric (NASA TN D-7522 equation (36) through "
    "order f^2); polar radius is polar_radius_from_flattening; mean anomaly vs "
    "time is mean_anomaly_from_epoch; inertial position is inertial_position_x, "
    "inertial_position_y, and inertial_position_z; the frame is planet-centered "
    "inertial with +Z along the polar axis and Omega measured from +X; element "
    "angles are radians; the PNG land fill is Natural Earth 1:110m land, public domain; "
    "a NORAD two-line element set may be passed with --tle and is used as a Keplerian "
    "ellipse: line-2 angles are degrees, semi-major axis is the inverse of mean_motion "
    "from the published mean motion in revolutions per 86400 s and this mu, and BSTAR, "
    "mean-motion derivatives, SGP4, and the epoch do not change the state; the TLE epoch "
    "is not a Greenwich angle"
)
PALETTE = {
    "ocean": "#c5ddef",
    "land": "#e8dcc8",
    "coast": "#8a6a4a",
    "grid": "#9bb8d0",
    "equator": "#1a5276",
    "track": "#922b21",
    "epoch": "#117a65",
    "end": "#6c3483",
    "text": "#1b2631",
}


@dataclass(frozen=True)
class Body:
    radius: float
    g0: float
    mu: float
    ae: float
    flattening: float
    omega_e: float
    j2: float
    radius_source: str
    ae_source: str
    j2_source: str


@dataclass(frozen=True)
class Orbit:
    mode: str
    a: float
    e: float
    i: float
    Omega: float
    omega: float
    nu: float
    M: float
    n: float
    p: float
    period: float
    rx: float
    ry: float
    rz: float


@dataclass(frozen=True)
class Subsatellite:
    time: float
    greenwich: float
    lat_geocentric: float
    lat_geodetic: float
    lon: float
    radius: float


def op_mod():
    """OrbitalParameters TLE parser. This skill does not call that program's run()."""
    global _OP
    if _OP is None:
        folder = str(Path(__file__).resolve().parent.parent / "ASTRO - OrbitalParameters")
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


def wrap_two_pi(angle: float) -> float:
    twopi = 2.0 * math.pi
    wrapped = math.fmod(angle, twopi)
    if wrapped < 0.0:
        wrapped += twopi
    if wrapped >= twopi or wrapped < 1e-15:
        return 0.0
    return wrapped


def wrap_pi(angle: float) -> float:
    wrapped = wrap_two_pi(angle)
    if wrapped > math.pi:
        wrapped -= 2.0 * math.pi
    return wrapped


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


def mean_anomaly_from_epoch(mean0: float, n: float, time: float, epoch: float) -> float:
    """mean_anomaly_from_epoch."""
    return mean0 + n * (time - epoch)


def greenwich_angle(theta0: float, omega_e: float, time: float, epoch: float) -> float:
    """greenwich_angle."""
    return theta0 + omega_e * (time - epoch)


def earth_fixed_x(x: float, y: float, theta: float) -> float:
    """earth_fixed_x."""
    return x * math.cos(theta) + y * math.sin(theta)


def earth_fixed_y(x: float, y: float, theta: float) -> float:
    """earth_fixed_y."""
    return -x * math.sin(theta) + y * math.cos(theta)


def earth_fixed_z(z: float) -> float:
    """earth_fixed_z."""
    return z


def geodetic_latitude_from_geocentric(
    phic: float, flattening: float, ae: float, radius: float
) -> float:
    """geodetic_latitude_from_geocentric."""
    return (
        phic
        + flattening * (ae / radius) * math.sin(2.0 * phic)
        + flattening**2
        * ((ae / radius) ** 2 - ae / (4.0 * radius))
        * math.sin(4.0 * phic)
    )


def polar_radius_from_flattening(ae: float, flattening: float) -> float:
    """polar_radius_from_flattening."""
    return ae * (1.0 - flattening)


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
    """inclination."""
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


def true_anomaly_cosine_from_state(
    h: float, radius: float, mu: float, eccentricity: float
) -> float:
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


def specific_orbital_energy_from_speed(speed: float, mu: float, radius: float) -> float:
    """specific_orbital_energy_from_speed."""
    return speed**2 / 2.0 - mu / radius


def semimajor_axis_from_energy(mu: float, energy: float) -> float:
    """semimajor_axis_from_energy."""
    return -mu / (2.0 * energy)


def eccentricity_from_energy(energy: float, h: float, mu: float) -> float:
    """eccentricity_from_energy."""
    radicand = 1.0 + 2.0 * energy * h**2 / mu**2
    if radicand < 0.0:
        if radicand > -1e-9:
            return 0.0
        raise ValueError("eccentricity is not real for this state")
    return math.sqrt(radicand)


def semi_latus_rectum(semi_major: float, eccentricity: float) -> float:
    """semi_latus_rectum."""
    return semi_major * (1.0 - eccentricity**2)


def conic_radius_from_parameter(parameter: float, eccentricity: float, nu: float) -> float:
    """conic_radius_from_parameter."""
    return parameter / (1.0 + eccentricity * math.cos(nu))


def orbital_period(mu: float, semi_major: float) -> float:
    """orbital_period."""
    return 2.0 * math.pi * math.sqrt(semi_major**3 / mu)


def nu_from_eccentric(eccentricity: float, eccentric_anomaly: float) -> float:
    return math.atan2(
        true_anomaly_sine(eccentric_anomaly, eccentricity),
        true_anomaly_cosine(eccentric_anomaly, eccentricity),
    )


def eccentric_from_true(eccentricity: float, nu: float) -> float:
    return math.atan2(
        eccentric_anomaly_sine(eccentricity, nu),
        eccentric_anomaly_cosine(eccentricity, nu),
    )


def solve_kepler(mean_anomaly: float, eccentricity: float) -> float:
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


def true_anomaly_from_state(
    h: float, radius: float, mu: float, eccentricity: float, radial_momentum: float, speed: float
) -> float:
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
    if abs(math.sin(inc)) <= EQUATORIAL_FRAC:
        if hz >= 0.0:
            cosine = equatorial_argument_cosine(x, radius)
            sine = equatorial_argument_sine(y, radius)
        else:
            cosine = x / radius
            sine = -y / radius
        return math.atan2(sine, cosine)
    cosine = argument_of_latitude_cosine(x, Omega, y, radius)
    sine = argument_of_latitude_sine(z, radius, inc)
    return math.atan2(sine, cosine)


def position_at_true(
    a: float, e: float, i: float, Omega: float, omega: float, nu: float
) -> tuple[float, float, float, float]:
    parameter = semi_latus_rectum(a, e)
    radius = conic_radius_from_parameter(parameter, e, nu)
    argument = argument_of_latitude(omega, nu)
    return (
        inertial_position_x(radius, Omega, argument, i),
        inertial_position_y(radius, Omega, argument, i),
        inertial_position_z(radius, i, argument),
        radius,
    )


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
    radius = math.sqrt(x**2 + y**2 + z**2)
    if radius == 0.0:
        raise ValueError("position is at the attracting centre")
    hx = specific_angular_momentum_x(y, vz, z, vy)
    hy = specific_angular_momentum_y(z, vx, x, vz)
    hz = specific_angular_momentum_z(x, vy, y, vx)
    h = specific_angular_momentum_magnitude(hx, hy, hz)
    if h == 0.0:
        raise ValueError("specific angular momentum is zero")
    speed = math.sqrt(vx**2 + vy**2 + vz**2)
    energy = specific_orbital_energy_from_speed(speed, mu, radius)
    if energy >= 0.0:
        raise ValueError("ground track is defined for an ellipse; this state is not bound")
    semi_major = semimajor_axis_from_energy(mu, energy)
    eccentricity = eccentricity_from_energy(energy, h, mu)
    if eccentricity >= 1.0:
        raise ValueError("ground track is defined for an ellipse")
    parameter = h**2 / mu
    inc = inclination(hz, h)
    horizontal = math.hypot(hx, hy)
    if horizontal <= EQUATORIAL_FRAC * h:
        Omega = 0.0
    else:
        Omega = wrap_two_pi(
            math.atan2(ascending_node_sine(hx, hy), ascending_node_cosine(hx, hy))
        )
    argument = argument_from_state(x, y, z, radius, inc, Omega, hz)
    if eccentricity < CIRCULAR_E:
        eccentricity = 0.0
        omega = 0.0
        nu = wrap_pi(argument)
        mean = nu
    else:
        radial_momentum = position_velocity_dot(x, vx, y, vy, z, vz)
        nu = true_anomaly_from_state(h, radius, mu, eccentricity, radial_momentum, speed)
        omega = wrap_two_pi(argument_of_periapsis(argument, nu))
        mean = wrap_pi(kepler_equation(eccentric_from_true(eccentricity, nu), eccentricity))
    return Orbit(
        mode=mode,
        a=semi_major,
        e=eccentricity,
        i=inc,
        Omega=Omega,
        omega=omega,
        nu=nu,
        M=mean,
        n=mean_motion(mu, semi_major),
        p=parameter,
        period=orbital_period(mu, semi_major),
        rx=x,
        ry=y,
        rz=z,
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
    if inc < 0.0 or inc > math.pi:
        raise ValueError("--i must satisfy 0 <= i <= pi radians")
    if eccentricity < 0.0 or eccentricity >= 1.0:
        raise ValueError("ground track is defined for an ellipse with 0 <= e < 1")
    if semi_major <= 0.0:
        raise ValueError("an ellipse needs --a > 0 m")
    if mean_anomaly is not None:
        require_finite(mean_anomaly, "--M")
        eccentric_anomaly = solve_kepler(mean_anomaly, eccentricity)
        nu = nu_from_eccentric(eccentricity, eccentric_anomaly)
    if nu is None:
        raise ValueError("pass exactly one of --nu or --M")
    require_finite(nu, "--nu")
    Omega = wrap_two_pi(Omega)
    omega = wrap_two_pi(omega)
    nu = wrap_pi(nu)
    parameter = semi_latus_rectum(semi_major, eccentricity)
    radius = conic_radius_from_parameter(parameter, eccentricity, nu)
    argument = argument_of_latitude(omega, nu)
    x = inertial_position_x(radius, Omega, argument, inc)
    y = inertial_position_y(radius, Omega, argument, inc)
    z = inertial_position_z(radius, inc, argument)
    eccentric_anomaly = eccentric_from_true(eccentricity, nu)
    vr = (
        math.sqrt(mu * semi_major)
        * eccentricity
        * math.sin(eccentric_anomaly)
        / radius
    )
    vp = math.sqrt(mu * semi_major) * math.sqrt(1.0 - eccentricity**2) / radius
    vx = (vr / radius) * x - vp * (
        math.cos(Omega) * math.sin(argument)
        + math.sin(Omega) * math.cos(inc) * math.cos(argument)
    )
    vy = (vr / radius) * y + vp * (
        -math.sin(Omega) * math.sin(argument)
        + math.cos(Omega) * math.cos(inc) * math.cos(argument)
    )
    vz = (vr / radius) * z + vp * math.sin(inc) * math.cos(argument)
    return orbit_from_state(mu, x, y, z, vx, vy, vz, mode)


def inertial_at_time(
    body: Body, orbit: Orbit, time: float, epoch: float
) -> tuple[float, float, float, float]:
    mean = mean_anomaly_from_epoch(orbit.M, orbit.n, time, epoch)
    eccentric = solve_kepler(mean, orbit.e)
    nu = nu_from_eccentric(orbit.e, eccentric)
    elapsed = time - epoch
    node = wrap_two_pi(
        orbit.Omega + j2_nodal_rate(orbit.n, body.j2, body.ae, orbit.i, orbit.a, orbit.e) * elapsed
    )
    periapsis = wrap_two_pi(
        orbit.omega
        + j2_apsidal_rate(orbit.n, body.j2, body.ae, orbit.i, orbit.a, orbit.e) * elapsed
    )
    return position_at_true(orbit.a, orbit.e, orbit.i, node, periapsis, nu)


def subsatellite_at(
    body: Body, orbit: Orbit, time: float, epoch: float, theta0: float
) -> Subsatellite:
    x, y, z, radius = inertial_at_time(body, orbit, time, epoch)
    theta = wrap_two_pi(greenwich_angle(theta0, body.omega_e, time, epoch))
    xe = earth_fixed_x(x, y, theta)
    ye = earth_fixed_y(x, y, theta)
    ze = earth_fixed_z(z)
    rho = math.hypot(xe, ye)
    if radius <= 0.0:
        raise ValueError("geocentric distance must be > 0")
    sine = ze / radius
    cosine = rho / radius
    if sine > 1.0 or sine < -1.0:
        if abs(sine) - 1.0 > 1e-10:
            raise ValueError("geocentric latitude sine is outside [-1, 1]")
        sine = math.copysign(1.0, sine)
        cosine = 0.0
    phic = math.atan2(sine, cosine)
    if rho <= EQUATORIAL_FRAC * radius:
        lon = 0.0
    else:
        lon = math.atan2(ye / rho, xe / rho)
    phig = geodetic_latitude_from_geocentric(phic, body.flattening, body.ae, radius)
    phig = max(-math.pi / 2.0, min(math.pi / 2.0, phig))
    return Subsatellite(
        time=time,
        greenwich=theta,
        lat_geocentric=phic,
        lat_geodetic=phig,
        lon=wrap_pi(lon),
        radius=radius,
    )


def resolve_body(
    radius_arg: float | None,
    ae_arg: float | None,
    flattening_arg: float | None,
    omega_arg: float | None,
    j2_arg: float | None,
) -> Body:
    if radius_arg is None:
        radius = R0_EARTH
        source = "default"
    else:
        require_finite(radius_arg, "--R0")
        if radius_arg <= 0.0:
            raise ValueError("--R0 must be > 0 m")
        radius = radius_arg
        source = "input"
    if ae_arg is None:
        ae = AE_WGS84
        ae_source = "default"
    else:
        require_finite(ae_arg, "--ae")
        if ae_arg <= 0.0:
            raise ValueError("--ae must be > 0 m")
        ae = ae_arg
        ae_source = "input"
    flattening = F_WGS84 if flattening_arg is None else flattening_arg
    omega_e = OMEGA_E if omega_arg is None else omega_arg
    if flattening_arg is not None:
        require_finite(flattening_arg, "--flattening")
    if flattening < 0.0 or flattening >= 1.0:
        raise ValueError("--flattening must satisfy 0 <= f < 1")
    if omega_arg is not None:
        require_finite(omega_arg, "--omega-e")
        if omega_e < 0.0:
            raise ValueError("--omega-e must be >= 0 rad/s")
    if j2_arg is None:
        j2 = J2_GSFC
        j2_source = "default"
    else:
        require_finite(j2_arg, "--j2")
        if j2_arg < 0.0:
            raise ValueError("--j2 must be >= 0")
        j2 = j2_arg
        j2_source = "input"
    return Body(
        radius=radius,
        g0=G0,
        mu=G0 * radius**2,
        ae=ae,
        flattening=flattening,
        omega_e=omega_e,
        j2=j2,
        radius_source=source,
        ae_source=ae_source,
        j2_source=j2_source,
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the ground track") from exc
    return plt


def land_polygons(path: Path = LAND_SHAPEFILE) -> list[list[tuple[float, float]]]:
    """Exterior rings from a 2-D shapefile Polygon layer."""
    if not path.is_file():
        raise ValueError(f"land map is missing: {path}")
    data = path.read_bytes()
    if len(data) < 100:
        raise ValueError("land shapefile is too short")
    file_code, file_length_words = struct.unpack(">i 20x i", data[:28])
    if file_code != 9994:
        raise ValueError("land file is not an ESRI shapefile")
    if file_length_words * 2 != len(data):
        raise ValueError("land shapefile length does not match the header")
    shape_type = struct.unpack_from("<i", data, 32)[0]
    if shape_type not in (5, 15, 25):
        raise ValueError("land shapefile is not a polygon layer")
    polygons: list[list[tuple[float, float]]] = []
    offset = 100
    while offset + 8 <= len(data):
        _number, content_words = struct.unpack_from(">2i", data, offset)
        offset += 8
        nbytes = content_words * 2
        chunk = data[offset : offset + nbytes]
        offset += nbytes
        if len(chunk) < 44:
            continue
        record_type = struct.unpack_from("<i", chunk, 0)[0]
        if record_type == 0:
            continue
        if record_type not in (5, 15, 25):
            continue
        nparts, npoints = struct.unpack_from("<2i", chunk, 36)
        parts = struct.unpack_from(f"<{nparts}i", chunk, 44)
        pts_off = 44 + 4 * nparts
        points = [
            struct.unpack_from("<2d", chunk, pts_off + 16 * index)
            for index in range(npoints)
        ]
        if not parts:
            continue
        stop = parts[1] if nparts > 1 else npoints
        ring = [(float(x), float(y)) for x, y in points[parts[0] : stop]]
        if len(ring) >= 3:
            polygons.append(ring)
    if len(polygons) < 5:
        raise ValueError("land shapefile did not yield continents")
    return polygons


def split_longitude_strokes(
    lons_deg: list[float], lats_deg: list[float]
) -> list[tuple[list[float], list[float]]]:
    strokes: list[tuple[list[float], list[float]]] = []
    xs: list[float] = []
    ys: list[float] = []
    previous: float | None = None
    for lon, lat in zip(lons_deg, lats_deg):
        if previous is not None and abs(lon - previous) > 180.0:
            if len(xs) > 1:
                strokes.append((xs, ys))
            xs = []
            ys = []
        xs.append(lon)
        ys.append(lat)
        previous = lon
    if len(xs) > 1:
        strokes.append((xs, ys))
    return strokes


def write_png(path: Path, points: list[Subsatellite]) -> None:
    plt = ensure_matplotlib()
    from matplotlib.collections import PolyCollection

    lons = [math.degrees(point.lon) for point in points]
    lats = [math.degrees(point.lat_geodetic) for point in points]
    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor="white")
    ax.set_facecolor(PALETTE["ocean"])
    ax.set_xlim(-180.0, 180.0)
    ax.set_ylim(-90.0, 90.0)
    ax.set_aspect("equal", adjustable="box")
    land = PolyCollection(
        land_polygons(),
        facecolors=PALETTE["land"],
        edgecolors=PALETTE["coast"],
        linewidths=0.4,
        zorder=1,
    )
    ax.add_collection(land)
    for lon in range(-180, 181, 30):
        ax.axvline(lon, color=PALETTE["grid"], linewidth=0.6, zorder=2)
    for lat in range(-90, 91, 30):
        ax.axhline(lat, color=PALETTE["grid"], linewidth=0.6, zorder=2)
    ax.axhline(0.0, color=PALETTE["equator"], linewidth=1.1, zorder=3)
    ax.axvline(0.0, color=PALETTE["equator"], linewidth=1.1, zorder=3)
    for xs, ys in split_longitude_strokes(lons, lats):
        ax.plot(xs, ys, color=PALETTE["track"], linewidth=1.8, zorder=4)
    ax.scatter(
        [lons[0]],
        [lats[0]],
        color=PALETTE["epoch"],
        s=36,
        zorder=5,
        label="epoch",
    )
    ax.scatter(
        [lons[-1]],
        [lats[-1]],
        color=PALETTE["end"],
        s=36,
        marker="s",
        zorder=5,
        label="end",
    )
    ax.set_xlabel("Longitude (deg, east of Greenwich)")
    ax.set_ylabel("Geodetic latitude (deg)")
    ax.set_title(PLOT_TITLE)
    ax.legend(frameon=False, loc="lower left")
    ax.tick_params(colors=PALETTE["text"])
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def default_png_path() -> Path:
    return Path.cwd() / "ground_track_earth.png"


def report(
    body: Body,
    orbit: Orbit,
    theta0: float,
    t0: float,
    t1: float,
    points: list[Subsatellite],
    png: Path,
    tle: object | None = None,
) -> None:
    epoch = points[0]
    end = points[-1]
    lats = [point.lat_geodetic for point in points]
    print_kv("mode", orbit.mode)
    if tle is not None:
        op_mod().print_tle(tle)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("R0_m", body.radius)
    print_kv("R0_source", body.radius_source)
    print_kv("g0_m_s2", body.g0)
    print_kv("mu_m3_s2", body.mu)
    print_kv("ae_m", body.ae)
    print_kv("ae_source", body.ae_source)
    print_kv("flattening", body.flattening)
    print_kv("polar_radius_m", polar_radius_from_flattening(body.ae, body.flattening))
    print_kv("omega_e_rad_s", body.omega_e)
    print_kv("J2", body.j2)
    print_kv("J2_source", body.j2_source)
    print_kv("greenwich_epoch_rad", wrap_two_pi(theta0))
    print_kv("t0_s", t0)
    print_kv("t1_s", t1)
    print_kv("orbits", abs(t1 - t0) / orbit.period)
    print_kv("samples", len(points))
    print_kv("a_m", orbit.a)
    print_kv("e", orbit.e)
    print_kv("i_rad", orbit.i)
    print_kv("Omega_rad", orbit.Omega)
    print_kv("omega_rad", orbit.omega)
    print_kv("nu_epoch_rad", orbit.nu)
    print_kv("M_epoch_rad", orbit.M)
    print_kv("n_rad_s", orbit.n)
    print_kv("period_s", orbit.period)
    node_rate = j2_nodal_rate(orbit.n, body.j2, body.ae, orbit.i, orbit.a, orbit.e)
    apsis_rate = j2_apsidal_rate(orbit.n, body.j2, body.ae, orbit.i, orbit.a, orbit.e)
    elapsed = t1 - t0
    print_kv("Omega_dot_rad_s", node_rate)
    print_kv("omega_dot_rad_s", apsis_rate)
    print_kv("Omega_end_rad", wrap_two_pi(orbit.Omega + node_rate * elapsed))
    print_kv("omega_end_rad", wrap_two_pi(orbit.omega + apsis_rate * elapsed))
    print_kv("lat_geocentric_epoch_rad", epoch.lat_geocentric)
    print_kv("lat_geodetic_epoch_rad", epoch.lat_geodetic)
    print_kv("lon_epoch_rad", epoch.lon)
    print_kv("lat_geocentric_end_rad", end.lat_geocentric)
    print_kv("lat_geodetic_end_rad", end.lat_geodetic)
    print_kv("lon_end_rad", end.lon)
    print_kv("lat_geodetic_max_rad", max(lats))
    print_kv("lat_geodetic_min_rad", min(lats))
    print_kv("graph", str(png))


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def parse_stdout(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        values[key] = value
    return values


def invoke(argv: list[str]) -> tuple[int, str, str]:
    import io

    out = io.StringIO()
    err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    body = resolve_body(None, None, None, None, None)
    if body.radius != R0_EARTH or body.radius_source != "default":
        return fail("Earth radius default")
    if not close_enough(body.mu, G0 * R0_EARTH**2, body.mu):
        return fail("mu is not g0*R0^2")
    if not close_enough(body.ae, AE_WGS84, AE_WGS84) or body.ae_source != "default":
        return fail("WGS 84 equatorial radius")
    if not close_enough(body.flattening, F_WGS84, 1.0):
        return fail("WGS 84 flattening")
    if not close_enough(body.omega_e, OMEGA_E, OMEGA_E):
        return fail("WGS 84 Earth rate")
    if not close_enough(body.j2, J2_GSFC, J2_GSFC) or body.j2_source != "default":
        return fail("GSFC J2 default")
    if not close_enough(polar_radius_from_flattening(2.0, 0.5), 1.0, 1.0):
        return fail("polar_radius_from_flattening")
    if len(land_polygons()) < 20:
        return fail("Natural Earth land map")
    if not close_enough(greenwich_angle(0.0, 1.0, math.pi / 2.0, 0.0), math.pi / 2.0, 1.0):
        return fail("greenwich_angle")
    if not close_enough(earth_fixed_x(0.0, 2.0, math.pi / 2.0), 2.0, 1.0):
        return fail("earth_fixed_x quarter turn")
    if not close_enough(earth_fixed_y(2.0, 0.0, math.pi / 2.0), -2.0, 1.0):
        return fail("earth_fixed_y quarter turn")
    if not close_enough(
        geodetic_latitude_from_geocentric(math.pi / 6.0, 0.0, 1.0, 1.0),
        math.pi / 6.0,
        1.0,
    ):
        return fail("sphere geodetic equals geocentric")
    if not close_enough(
        geodetic_latitude_from_geocentric(math.pi / 4.0, 0.01, 1.0, 1.0),
        math.pi / 4.0 + 0.01,
        1.0,
    ):
        return fail("TN D-7522 forty-five degree surface series")

    mu = 1.0
    unit = orbit_from_elements(mu, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, "elements")
    if not close_enough(unit.period, 2.0 * math.pi, 1.0):
        return fail("unit circular period")
    sphere = Body(
        radius=1.0,
        g0=1.0,
        mu=1.0,
        ae=1.0,
        flattening=0.0,
        omega_e=0.0,
        j2=0.0,
        radius_source="input",
        ae_source="input",
        j2_source="input",
    )
    foot = subsatellite_at(sphere, unit, 0.0, 0.0, 0.0)
    if not close_enough(foot.lat_geocentric, 0.0, 1.0) or not close_enough(foot.lon, 0.0, 1.0):
        return fail("equatorial epoch at Greenwich")
    moved = subsatellite_at(sphere, unit, math.pi / 2.0, 0.0, 0.0)
    if not close_enough(moved.lon, math.pi / 2.0, 1.0):
        return fail("inertial motion with a frozen Earth")
    rotating = Body(
        radius=1.0,
        g0=1.0,
        mu=1.0,
        ae=1.0,
        flattening=0.0,
        omega_e=1.0,
        j2=0.0,
        radius_source="input",
        ae_source="input",
        j2_source="input",
    )
    synch = subsatellite_at(rotating, unit, math.pi / 2.0, 0.0, 0.0)
    if not close_enough(synch.lon, 0.0, 1.0):
        return fail("Earth rotation cancelled the inertial advance")

    polar = orbit_from_elements(mu, 1.0, 0.0, math.pi / 2.0, 0.0, 0.0, 0.0, None, "elements")
    pole = subsatellite_at(sphere, polar, math.pi / 2.0, 0.0, 0.0)
    if not close_enough(pole.lat_geodetic, math.pi / 2.0, 1.0):
        return fail("polar geodetic latitude")

    inclined = orbit_from_elements(
        G0 * R0_EARTH**2, 7.0e6, 0.0, 0.9, 0.4, 0.0, math.pi / 2.0, None, "elements"
    )
    earth = resolve_body(None, None, None, None, None)
    flat = Body(
        radius=earth.radius,
        g0=earth.g0,
        mu=earth.mu,
        ae=earth.ae,
        flattening=0.0,
        omega_e=earth.omega_e,
        j2=0.0,
        radius_source=earth.radius_source,
        ae_source=earth.ae_source,
        j2_source="input",
    )
    oblate = subsatellite_at(earth, inclined, 0.0, 0.0, 0.0)
    sphere_foot = subsatellite_at(flat, inclined, 0.0, 0.0, 0.0)
    if abs(oblate.lat_geodetic - sphere_foot.lat_geodetic) <= 1e-12:
        return fail("flattening did not change geodetic latitude")
    if not close_enough(oblate.lon, sphere_foot.lon, 1.0):
        return fail("flattening changed longitude")
    if not close_enough(j2_nodal_rate(1.0, 1.0, 1.0, math.pi / 2.0, 1.0, 0.0), 0.0, 1.0):
        return fail("polar nodal rate")
    if not close_enough(j2_nodal_rate(1.0, 1.0, 1.0, 0.0, 1.0, 0.0), -1.5, 1.0):
        return fail("equatorial nodal rate")
    if not close_enough(j2_apsidal_rate(1.0, 1.0, 1.0, 0.0, 1.0, 0.0), 3.0, 1.0):
        return fail("equatorial apsidal rate")
    kepler_earth = Body(
        radius=earth.radius,
        g0=earth.g0,
        mu=earth.mu,
        ae=earth.ae,
        flattening=earth.flattening,
        omega_e=earth.omega_e,
        j2=0.0,
        radius_source=earth.radius_source,
        ae_source=earth.ae_source,
        j2_source="input",
    )
    later = 6000.0
    with_j2 = subsatellite_at(earth, inclined, later, 0.0, 0.0)
    without_j2 = subsatellite_at(kepler_earth, inclined, later, 0.0, 0.0)
    if abs(with_j2.lon - without_j2.lon) <= 1e-12:
        return fail("J2 did not change longitude")
    j2_folder = str(Path(__file__).resolve().parent.parent / "ASTRO - J2SecularRates")
    if j2_folder not in sys.path:
        sys.path.insert(0, j2_folder)
    import j2_secular_rates as j2_skill

    node = j2_nodal_rate(inclined.n, earth.j2, earth.ae, inclined.i, inclined.a, inclined.e)
    apsis = j2_apsidal_rate(inclined.n, earth.j2, earth.ae, inclined.i, inclined.a, inclined.e)
    if not close_enough(
        node,
        j2_skill.j2_nodal_rate(inclined.n, earth.j2, earth.ae, inclined.i, inclined.a, inclined.e),
        max(abs(node), 1.0),
    ):
        return fail("nodal rate does not match J2SecularRates")
    if not close_enough(
        apsis,
        j2_skill.j2_apsidal_rate(inclined.n, earth.j2, earth.ae, inclined.i, inclined.a, inclined.e),
        max(abs(apsis), 1.0),
    ):
        return fail("apsidal rate does not match J2SecularRates")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "track.png")
        code, text, err = invoke(
            [
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
                "--span",
                "6000",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        if not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        values = parse_stdout(text)
        for key in (
            "mode",
            "lat_geodetic_epoch_rad",
            "lon_epoch_rad",
            "lat_geodetic_end_rad",
            "lon_end_rad",
            "Omega_dot_rad_s",
            "omega_dot_rad_s",
            "graph",
        ):
            if key not in values:
                return fail(f"stdout missing {key}")
        if values.get("mode") != "elements":
            return fail("elements mode label")
        if values.get("J2_source") != "default":
            return fail("J2 default source")
        if not close_enough(float(values.get("J2", "nan")), J2_GSFC, J2_GSFC):
            return fail("printed J2")
        default_out = str(Path(tmp) / "default.png")
        code, text, err = invoke(
            [
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
                "--out",
                default_out,
            ]
        )
        if code != 0:
            return fail(f"default-orbit main returned {code}: {err}")
        default_values = parse_stdout(text)
        if not close_enough(float(default_values.get("orbits", "nan")), float(DEFAULT_ORBITS), 1.0):
            return fail("baseline is not 10 orbits")
        state_out = str(Path(tmp) / "state.png")
        code, text, err = invoke(
            [
                "--rx",
                "7000000",
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
                "--greenwich",
                "0",
                "--span",
                "5400",
                "--out",
                state_out,
            ]
        )
        if code != 0:
            return fail(f"state main returned {code}: {err}")
        if parse_stdout(text).get("mode") != "state":
            return fail("state mode label")
        op = op_mod()
        tle_out = str(Path(tmp) / "tle.png")
        code, text, err = invoke(
            [
                "--tle",
                op.ISS_TLE_LINE1,
                op.ISS_TLE_LINE2,
                "--greenwich",
                "0",
                "--span",
                "60",
                "--samples",
                "2",
                "--out",
                tle_out,
            ]
        )
        if code != 0:
            return fail(f"TLE main returned {code}: {err}")
        tle_values = parse_stdout(text)
        if tle_values.get("mode") != "tle" or tle_values.get("tle_catalog") != "25544":
            return fail("tle mode label")

    rejections = (
        ["--a", "7e6", "--e", "0.1", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0.2"],
        ["--greenwich", "0", "--span", "10"],
        [
            "--a",
            "7e6",
            "--e",
            "0.1",
            "--i",
            "0.2",
            "--raan",
            "0.1",
            "--aop",
            "0.1",
            "--nu",
            "0.2",
            "--greenwich",
            "0",
            "--span",
            "10",
            "--rx",
            "1",
        ],
        ["--a=-2e7", "--e", "1.4", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0.2", "--greenwich", "0", "--span", "10"],
        [
            "--a",
            "7e6",
            "--e",
            "0.1",
            "--i",
            "0.2",
            "--raan",
            "0.1",
            "--aop",
            "0.1",
            "--nu",
            "0.2",
            "--greenwich",
            "0",
            "--span",
            "10",
            "--orbits",
            "10",
        ],
        ["--a", "7e6", "--e", "0.1", "--i", "0.2", "--raan", "0.1", "--aop", "0.1", "--nu", "0.2", "--M", "0.1", "--greenwich", "0", "--span", "10"],
        [],
    )
    for argv in rejections:
        code, _text, err = invoke(argv)
        if code != 2 or not err.startswith("error:"):
            return fail(f"expected exit 2 for {argv}, got {code}: {err}")

    print("check: pass")
    print_kv("unit_period_s", unit.period)
    print_kv("synch_lon_rad", synch.lon)
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
        "--span",
        "--t0",
        "--t1",
        "--orbits",
        "--R0",
        "--ae",
        "--flattening",
        "--omega-e",
        "--j2",
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


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Subsatellite ground track of an Earth ellipse with first-order J2."
    )
    parser.add_argument("--a", type=float, default=None, help="semi-major axis [m]")
    parser.add_argument("--e", type=float, default=None, help="eccentricity")
    parser.add_argument("--i", type=float, default=None, help="inclination [rad]")
    parser.add_argument("--raan", type=float, default=None, help="longitude of the ascending node [rad]")
    parser.add_argument("--aop", type=float, default=None, help="argument of periapsis [rad]")
    parser.add_argument("--nu", type=float, default=None, help="true anomaly at epoch [rad]")
    parser.add_argument("--M", type=float, default=None, help="mean anomaly at epoch [rad]")
    parser.add_argument("--rx", type=float, default=None, help="inertial x [m]")
    parser.add_argument("--ry", type=float, default=None, help="inertial y [m]")
    parser.add_argument("--rz", type=float, default=None, help="inertial z [m]")
    parser.add_argument("--vx", type=float, default=None, help="inertial vx [m/s]")
    parser.add_argument("--vy", type=float, default=None, help="inertial vy [m/s]")
    parser.add_argument("--vz", type=float, default=None, help="inertial vz [m/s]")
    parser.add_argument(
        "--tle",
        nargs="+",
        default=None,
        help="NORAD two-line elements; two 69-character lines, optional name line first",
    )
    parser.add_argument("--greenwich", type=float, default=None, help="Greenwich angle at epoch [rad]")
    parser.add_argument("--span", type=float, default=None, help="time span from epoch [s]")
    parser.add_argument("--t0", type=float, default=None, help="start time [s]")
    parser.add_argument("--t1", type=float, default=None, help="end time [s]")
    parser.add_argument(
        "--orbits",
        type=float,
        default=None,
        help=f"number of orbital periods from epoch (default {DEFAULT_ORBITS})",
    )
    parser.add_argument("--samples", type=int, default=None, help="number of track samples")
    parser.add_argument("--R0", type=float, default=None, help="two-body radius in mu = g0*R0^2 [m]")
    parser.add_argument("--ae", type=float, default=None, help="ellipsoid equatorial radius [m]")
    parser.add_argument("--flattening", type=float, default=None, help="ellipsoid flattening")
    parser.add_argument("--omega-e", type=float, default=None, help="Earth sidereal rate [rad/s]")
    parser.add_argument(
        "--j2",
        type=float,
        default=None,
        help=f"second zonal harmonic; default {J2_GSFC:.8g}; 0 is Keplerian motion",
    )
    parser.add_argument("--out", default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run identity checks")
    if argv is None:
        argv = sys.argv[1:]
    return parser.parse_args(_bind_negative_values(list(argv)))


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    if ns.check:
        return run_check()
    try:
        element_flags = (ns.a, ns.e, ns.i, ns.raan, ns.aop)
        elements_present = any(value is not None for value in element_flags) or ns.nu is not None or ns.M is not None
        state_flags = (ns.rx, ns.ry, ns.rz, ns.vx, ns.vy, ns.vz)
        state_present = any(value is not None for value in state_flags)
        tle_present = bool(ns.tle)
        if int(elements_present) + int(state_present) + int(tle_present) > 1:
            raise ValueError("pass a TLE, classical elements, or an inertial state, not more than one")
        if ns.greenwich is None:
            raise ValueError("--greenwich is required")
        require_finite(ns.greenwich, "--greenwich")
        span_given = ns.span is not None
        window_given = ns.t0 is not None or ns.t1 is not None
        orbits_given = ns.orbits is not None
        if span_given and window_given:
            raise ValueError("pass --span or --t0/--t1, not both")
        if orbits_given and (span_given or window_given):
            raise ValueError("pass --orbits or a time window, not both")
        body = resolve_body(ns.R0, ns.ae, ns.flattening, ns.omega_e, ns.j2)
        tle = None
        if elements_present:
            if any(value is None for value in element_flags):
                raise ValueError("elements mode needs --a, --e, --i, --raan, and --aop")
            if (ns.nu is None) == (ns.M is None):
                raise ValueError("elements mode needs exactly one of --nu or --M")
            orbit = orbit_from_elements(
                body.mu, ns.a, ns.e, ns.i, ns.raan, ns.aop, ns.nu, ns.M, "elements"
            )
        elif state_present:
            if any(value is None for value in state_flags):
                raise ValueError("state mode needs --rx, --ry, --rz, --vx, --vy, and --vz")
            for value, flag in zip(state_flags, ("--rx", "--ry", "--rz", "--vx", "--vy", "--vz")):
                require_finite(value, flag)
            orbit = orbit_from_state(
                body.mu, ns.rx, ns.ry, ns.rz, ns.vx, ns.vy, ns.vz, "state"
            )
        elif tle_present:
            op = op_mod()
            tle = op.parse_tle_args(ns.tle)
            semi_major, eccentricity, inc, raan, arg_perigee, mean_anomaly = op.tle_elements(body.mu, tle)
            orbit = orbit_from_elements(
                body.mu,
                semi_major,
                eccentricity,
                inc,
                raan,
                arg_perigee,
                None,
                mean_anomaly,
                "tle",
            )
        else:
            raise ValueError("pass a TLE, classical elements, or an inertial state")
        if span_given:
            require_finite(ns.span, "--span")
            if ns.span <= 0.0:
                raise ValueError("--span must be > 0 s")
            t0 = 0.0
            t1 = ns.span
        elif ns.t0 is not None and ns.t1 is not None:
            require_finite(ns.t0, "--t0")
            require_finite(ns.t1, "--t1")
            if ns.t1 == ns.t0:
                raise ValueError("--t1 must differ from --t0")
            t0 = ns.t0
            t1 = ns.t1
        elif window_given:
            raise ValueError("pass both --t0 and --t1")
        else:
            orbits = DEFAULT_ORBITS if ns.orbits is None else ns.orbits
            require_finite(orbits, "--orbits")
            if orbits <= 0.0:
                raise ValueError("--orbits must be > 0")
            t0 = 0.0
            t1 = orbits * orbit.period
        if ns.samples is None:
            n_orbits = abs(t1 - t0) / orbit.period
            samples = max(
                2,
                1
                + int(
                    round(
                        (DEFAULT_SAMPLES_PER_ORBIT - 1)
                        * max(n_orbits, 1.0 / 360.0)
                    )
                ),
            )
        else:
            samples = ns.samples
        if samples < 2:
            raise ValueError("--samples must be >= 2")
        times = linspace(t0, t1, samples)
        points = [subsatellite_at(body, orbit, time, t0, ns.greenwich) for time in times]
        png = Path(ns.out) if ns.out else default_png_path()
        write_png(png, points)
        report(body, orbit, ns.greenwich, t0, t1, points, png, tle)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
