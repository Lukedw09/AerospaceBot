#!/usr/bin/env python3
"""Finite-thrust multi-burn LEO raise with gravity loss and optional plane change.

Parking orbit from classical elements or an inertial state. Target is a higher
circular LEO. Powered arcs use tangential (raise) or velocity-to-be-gained
(circularize / plane-change) steering. Coasts are Keplerian. Gravity loss is
gravity_loss_definition along each burn. mu = g0*R0^2.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import tempfile
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

G0 = 9.80665
R0_EARTH = 6.3742e6
PLOT_TITLE = "Multi-burn LEO raise"
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
SKILL_DIR = Path(__file__).resolve().parent
CIRCULAR_E = 1e-7
DV_COLOR = "#e67e22"
BURN_COLOR = "#c0392b"
COAST_COLOR = "#7f8c8d"
TARGET_COLOR = "#1a5276"
PARK_COLOR = "#2874a6"
PNG_ELEV_DEG = 25.0
PNG_AZIM_DEG = 35.0
MAX_BURNS = 12
RK4_SUBSTEPS = 40
SAMPLE_EVERY = 8
COAST_SAMPLES = 72
CIRC_SPEED_TOL = 2.0
CIRC_E_TOL = 5e-4
INC_TOL = 1e-4
MASS_FLOOR_FRAC = 0.02
_OP = None

ASSUMPTIONS = (
    "finite-thrust multi-burn LEO raise about a spherical planet; inverse-square "
    "gravity with no drag or third body; coasts between burns are Keplerian; "
    "each burn follows the commanded steering law for a duration set by the "
    "thrust profile, so the impulsive Hohmann delta-v is not recovered; "
    "periapsis-centered raise burns thrust along the velocity; the final "
    "apoapsis burn steers toward circular velocity in the target plane "
    "(combined plane change when i_target differs); gravity loss is the path "
    "integral g*sin(theta) along the burn using the velocity direction "
    "(orbital form of gravity_loss_definition); steered delta-v is integral "
    "of T/m dt; stop checks use energy/h apoapsis and eccentricity so near-"
    "circular finite burns do not abort on element inversion; mu = g0*R0^2 "
    "with g0 = 9.80665 m/s^2; Earth default R0 = 6374200 m; a radius is "
    "distance from the center and an altitude is geometric height above R0; "
    "frame matches OrbitalParameters (+Z polar, XY equatorial, Omega from +X)"
)


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


def km(meters: float) -> float:
    return meters / 1000.0


def require_finite(value: float, flag: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def unit(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    mag = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
    if mag <= 0.0:
        raise ValueError("zero vector has no direction")
    return (vec[0] / mag, vec[1] / mag, vec[2] / mag)


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass(frozen=True)
class Body:
    radius: float
    g0: float
    mu: float
    radius_source: str


@dataclass
class ThrustProfile:
    kind: str
    thrust0: float
    isp0: float
    times: list[float] = field(default_factory=list)
    thrusts: list[float] = field(default_factory=list)
    isps: list[float] = field(default_factory=list)

    def at(self, t_mission: float) -> tuple[float, float]:
        if self.kind == "constant":
            return self.thrust0, self.isp0
        if not self.times:
            raise ValueError("thrust profile table is empty")
        if t_mission <= self.times[0]:
            return self.thrusts[0], self.isps[0]
        if t_mission >= self.times[-1]:
            return self.thrusts[-1], self.isps[-1]
        for i in range(1, len(self.times)):
            t0, t1 = self.times[i - 1], self.times[i]
            if t_mission <= t1:
                span = t1 - t0
                if span <= 0.0:
                    return self.thrusts[i], self.isps[i]
                alpha = (t_mission - t0) / span
                thrust = self.thrusts[i - 1] + alpha * (self.thrusts[i] - self.thrusts[i - 1])
                isp = self.isps[i - 1] + alpha * (self.isps[i] - self.isps[i - 1])
                return thrust, isp
        return self.thrusts[-1], self.isps[-1]


@dataclass
class BurnArc:
    index: int
    role: str
    t_start: float
    t_end: float
    nu_start: float
    nu_end: float
    dv_steered: float
    gravity_loss: float
    dv_plane: float
    path_m: list[tuple[float, float, float]]
    mid_pos_m: tuple[float, float, float]
    mid_dv_dir: tuple[float, float, float]


@dataclass
class CoastArc:
    t_start: float
    t_end: float
    path_m: list[tuple[float, float, float]]


@dataclass
class RaiseResult:
    mode: str
    body: Body
    thrust_profile: ThrustProfile
    m0: float
    mf: float
    mp_used: float
    n_burns: int
    burns: list[BurnArc]
    coasts: list[CoastArc]
    r_park: float
    h_park: float
    i_park: float
    Omega_park: float
    omega_park: float
    e_park: float
    a_park: float
    r_target: float
    h_target: float
    i_target: float
    a_target: float
    e_target: float
    v_circular_target: float
    dv_steered: float
    dv_gravity_loss: float
    dv_plane_change: float
    dv_total: float
    tof: float
    tof_burn: float
    tof_coast: float
    warnings: list[str]
    park_state: tuple[float, float, float, float, float, float]
    final_state: tuple[float, float, float, float, float, float]
    epoch_elements: dict[str, float | None]


def make_body(r0: float | None) -> Body:
    if r0 is None:
        return Body(R0_EARTH, G0, G0 * R0_EARTH**2, "default")
    require_finite(r0, "--R0")
    if r0 <= 0.0:
        raise ValueError("--R0 must be > 0 m")
    return Body(r0, G0, G0 * r0**2, "user")


def load_profile(path: Path, default_isp: float | None) -> ThrustProfile:
    times: list[float] = []
    thrusts: list[float] = []
    isps: list[float] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read thrust profile: {exc}") from exc
    rows = list(csv.reader(line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")))
    if not rows:
        raise ValueError("thrust profile table is empty")
    start = 0
    if rows[0] and not _looks_numeric(rows[0][0]):
        start = 1
    for row in rows[start:]:
        if len(row) < 2:
            raise ValueError("thrust profile rows need time_s and thrust_N")
        t = float(row[0])
        thrust = float(row[1])
        if len(row) >= 3 and row[2].strip() != "":
            isp = float(row[2])
        elif default_isp is not None:
            isp = default_isp
        else:
            raise ValueError("thrust profile needs isp_s in each row or a constant --isp")
        require_finite(t, "profile time")
        require_finite(thrust, "profile thrust")
        require_finite(isp, "profile isp")
        if thrust < 0.0:
            raise ValueError("profile thrust must be >= 0 N")
        if isp <= 0.0:
            raise ValueError("profile isp must be > 0 s")
        times.append(t)
        thrusts.append(thrust)
        isps.append(isp)
    if any(times[i] < times[i - 1] for i in range(1, len(times))):
        raise ValueError("thrust profile times must be nondecreasing")
    return ThrustProfile("table", thrusts[0], isps[0], times, thrusts, isps)


def _looks_numeric(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def parking_from_args(args: argparse.Namespace, body: Body) -> tuple[str, object, tuple[float, float, float, float, float, float]]:
    op = op_mod()
    element_flags = [args.a, args.e, args.i, args.raan, args.aop]
    state_flags = [args.rx, args.ry, args.rz, args.vx, args.vy, args.vz]
    has_elements = any(v is not None for v in element_flags) or args.nu is not None or args.M is not None
    has_state = any(v is not None for v in state_flags)
    if has_elements and has_state:
        raise ValueError("pass parking elements or a state, not both")
    if has_state:
        if any(v is None for v in state_flags):
            raise ValueError("state mode needs --rx --ry --rz --vx --vy --vz")
        for name, value in (
            ("--rx", args.rx),
            ("--ry", args.ry),
            ("--rz", args.rz),
            ("--vx", args.vx),
            ("--vy", args.vy),
            ("--vz", args.vz),
        ):
            require_finite(value, name)
        orbit = op.orbit_from_state(body.mu, args.rx, args.ry, args.rz, args.vx, args.vy, args.vz, "state")
        state = (args.rx, args.ry, args.rz, args.vx, args.vy, args.vz)
        return "state", orbit, state
    if not has_elements:
        raise ValueError("parking orbit needs classical elements or an inertial state")
    for name, value in (
        ("--a", args.a),
        ("--e", args.e),
        ("--i", args.i),
        ("--raan", args.raan),
        ("--aop", args.aop),
    ):
        if value is None:
            raise ValueError(f"elements mode needs {name}")
        require_finite(value, name)
    if (args.nu is None) == (args.M is None):
        raise ValueError("elements mode needs exactly one of --nu or --M")
    if args.e < 0.0:
        raise ValueError("--e must be >= 0")
    if not (0.0 <= args.i <= math.pi):
        raise ValueError("--i must be in [0, pi] rad")
    if args.M is not None:
        if args.a <= 0.0 or args.e >= 1.0:
            raise ValueError("--M is ellipse-only")
        orbit = op.orbit_from_elements(
            body.mu, args.a, args.e, args.i, args.raan, args.aop, None, args.M, "elements"
        )
    else:
        orbit = op.orbit_from_elements(
            body.mu, args.a, args.e, args.i, args.raan, args.aop, args.nu, None, "elements"
        )
    state = (orbit.rx, orbit.ry, orbit.rz, orbit.vx, orbit.vy, orbit.vz)
    return "elements", orbit, state


def resolve_target(args: argparse.Namespace, body: Body, i_park: float) -> tuple[float, float]:
    if (args.alt_target is None) == (args.r_target is None):
        raise ValueError("pass exactly one of --alt-target or --r-target")
    if args.alt_target is not None:
        require_finite(args.alt_target, "--alt-target")
        if args.alt_target < 0.0:
            raise ValueError("--alt-target must be >= 0 m")
        r_target = body.radius + args.alt_target
    else:
        require_finite(args.r_target, "--r-target")
        r_target = args.r_target
    if r_target < body.radius:
        raise ValueError("target radius must be >= R0")
    if args.i_target is None:
        i_target = i_park
    else:
        require_finite(args.i_target, "--i-target")
        if not (0.0 <= args.i_target <= math.pi):
            raise ValueError("--i-target must be in [0, pi] rad")
        i_target = args.i_target
    return r_target, i_target


def hohmann_impulsive(mu: float, r1: float, r2: float) -> tuple[float, float, float]:
    a_t = 0.5 * (r1 + r2)
    v1 = math.sqrt(mu / r1)
    v2 = math.sqrt(mu / r2)
    v1t = math.sqrt(mu * (2.0 / r1 - 1.0 / a_t))
    v2t = math.sqrt(mu * (2.0 / r2 - 1.0 / a_t))
    return abs(v1t - v1), abs(v2 - v2t), abs(v1t - v1) + abs(v2 - v2t)


def default_burn_count(mu: float, r1: float, r2: float, thrust: float, m0: float, isp: float) -> int:
    _dv1, _dv2, dv = hohmann_impulsive(mu, r1, r2)
    c = isp * G0
    if thrust <= 0.0 or c <= 0.0:
        return 2
    mdot = thrust / c
    dm = m0 * (1.0 - math.exp(-dv / c))
    t_burn = dm / mdot if mdot > 0.0 else 0.0
    period = 2.0 * math.pi * math.sqrt(max(r1, 1.0) ** 3 / mu)
    frac = t_burn / period if period > 0.0 else 0.0
    n = max(2, int(math.ceil(frac / 0.12)))
    return min(MAX_BURNS, n)


def keplerian_scalars(
    mu: float, state: tuple[float, float, float, float, float, float]
) -> dict[str, float | bool]:
    """Energy / angular-momentum orbit scalars that never throw on near-circular noise."""
    r_vec = (state[0], state[1], state[2])
    v_vec = (state[3], state[4], state[5])
    r = math.sqrt(dot(r_vec, r_vec))
    v2 = dot(v_vec, v_vec)
    if r <= 0.0:
        raise ValueError("position radius must be > 0")
    h_vec = cross(r_vec, v_vec)
    h2 = dot(h_vec, h_vec)
    h = math.sqrt(h2)
    energy = 0.5 * v2 - mu / r
    if h > 0.0:
        ci = max(-1.0, min(1.0, h_vec[2] / h))
        inclination = math.acos(ci)
    else:
        inclination = 0.0
    # Non-elliptic: report infinite apoapsis so a raise stop can still fire.
    if energy >= -1e-14 * mu / r:
        p = h2 / mu if mu > 0.0 else 0.0
        return {
            "r": r,
            "v": math.sqrt(v2),
            "a": float("nan"),
            "e": 1.0 if abs(energy) <= 1e-14 * mu / r else float("inf"),
            "ra": float("inf"),
            "rp": p / (1.0 + 1.0) if p > 0.0 else 0.0,
            "i": inclination,
            "elliptic": False,
        }
    a = -mu / (2.0 * energy)
    p = h2 / mu
    ecc2 = 1.0 - p / a
    if ecc2 < 0.0:
        ecc2 = 0.0
    e = math.sqrt(ecc2)
    return {
        "r": r,
        "v": math.sqrt(v2),
        "a": a,
        "e": e,
        "ra": a * (1.0 + e),
        "rp": a * (1.0 - e),
        "i": inclination,
        "elliptic": True,
    }


def orbit_metrics(mu: float, state: tuple[float, float, float, float, float, float]) -> dict[str, float]:
    op = op_mod()
    try:
        orbit = op.orbit_from_state(mu, *state, "state")
    except ValueError as exc:
        raise ValueError(
            f"state is not a usable Keplerian ellipse for coast/raise ({exc})"
        ) from exc
    return {
        "a": orbit.a if orbit.a is not None else float("nan"),
        "e": orbit.e,
        "i": orbit.i,
        "Omega": orbit.Omega,
        "omega": orbit.omega,
        "nu": orbit.nu,
        "rp": orbit.rp,
        "ra": orbit.ra if orbit.ra is not None else orbit.rp,
        "r": math.sqrt(state[0] ** 2 + state[1] ** 2 + state[2] ** 2),
        "v": math.sqrt(state[3] ** 2 + state[4] ** 2 + state[5] ** 2),
    }


def state_at_nu(mu: float, orbit_like: dict[str, float], nu: float) -> tuple[float, float, float, float, float, float]:
    op = op_mod()
    return op.state_from_elements(
        mu,
        orbit_like["a"],
        orbit_like["e"],
        orbit_like["i"],
        orbit_like["Omega"],
        orbit_like["omega"],
        nu,
    )


def coast_to_true_anomaly(
    mu: float,
    state: tuple[float, float, float, float, float, float],
    nu_target: float,
    t0: float,
) -> tuple[tuple[float, float, float, float, float, float], float, list[tuple[float, float, float]]]:
    op = op_mod()
    try:
        metrics = orbit_metrics(mu, state)
    except ValueError as exc:
        raise ValueError(f"coast aborted: {exc}") from exc
    if not math.isfinite(metrics["a"]) or metrics["a"] <= 0.0 or metrics["e"] >= 1.0 - 1e-12:
        raise ValueError(
            "coast requires an elliptical orbit; state is parabolic/hyperbolic "
            "or has non-positive semi-major axis"
        )
    nu0 = metrics["nu"]
    try:
        M0 = op.wrap_two_pi(op.kepler_equation(op.eccentric_from_true(metrics["e"], nu0), metrics["e"]))
        M1 = op.wrap_two_pi(op.kepler_equation(op.eccentric_from_true(metrics["e"], nu_target), metrics["e"]))
        tof = op.time_of_flight_ellipse(mu, metrics["a"], M0, M1)
    except ValueError as exc:
        raise ValueError(f"coast Kepler timing failed ({exc})") from exc
    path: list[tuple[float, float, float]] = []
    if tof <= 1e-9:
        pos = (state[0], state[1], state[2])
        return state, t0, [pos, pos]
    for frac in [i / (COAST_SAMPLES - 1) for i in range(COAST_SAMPLES)]:
        # Advance mean anomaly fractionally along the forward coast.
        dM = op.wrap_two_pi(M1 - M0)
        if dM == 0.0:
            dM = 2.0 * math.pi
        M = op.wrap_two_pi(M0 + frac * dM)
        E = op.solve_kepler(M, metrics["e"])
        nu = op.nu_from_eccentric(metrics["e"], E)
        x, y, z, *_ = state_at_nu(mu, metrics, nu)
        path.append((x, y, z))
    final = state_at_nu(mu, metrics, nu_target)
    return final, t0 + tof, path


def target_plane_normal(i_target: float, Omega: float) -> tuple[float, float, float]:
    return (
        math.sin(i_target) * math.sin(Omega),
        -math.sin(i_target) * math.cos(Omega),
        math.cos(i_target),
    )


def desired_circular_velocity(
    r_vec: tuple[float, float, float],
    mu: float,
    i_target: float,
    Omega: float,
    r_target: float,
) -> tuple[float, float, float]:
    radius = math.sqrt(dot(r_vec, r_vec))
    if radius <= 0.0:
        raise ValueError("position radius must be > 0")
    r_hat = unit(r_vec)
    h_hat = unit(target_plane_normal(i_target, Omega))
    t_hat = unit(cross(h_hat, r_hat))
    # Circularize near the target radius; add a soft radial rate toward r_target.
    speed = math.sqrt(mu / max(r_target, radius * 0.5))
    period = 2.0 * math.pi * math.sqrt(max(r_target, radius) ** 3 / mu)
    v_rad = 0.35 * (r_target - radius) / max(period / (2.0 * math.pi), 1e-9)
    return (
        speed * t_hat[0] + v_rad * r_hat[0],
        speed * t_hat[1] + v_rad * r_hat[1],
        speed * t_hat[2] + v_rad * r_hat[2],
    )


def thrust_direction(
    role: str,
    r_vec: tuple[float, float, float],
    v_vec: tuple[float, float, float],
    mu: float,
    i_target: float,
    Omega: float,
    r_target: float,
) -> tuple[float, float, float]:
    if role == "raise":
        return unit(v_vec)
    v_des = desired_circular_velocity(r_vec, mu, i_target, Omega, r_target)
    vg = (v_des[0] - v_vec[0], v_des[1] - v_vec[1], v_des[2] - v_vec[2])
    mag = math.sqrt(dot(vg, vg))
    if mag < 1e-9:
        return unit(v_vec)
    return unit(vg)


def derivatives(
    t: float,
    state: tuple[float, ...],
    *,
    mu: float,
    profile: ThrustProfile,
    role: str,
    i_target: float,
    Omega: float,
    r_target: float,
) -> tuple[float, ...]:
    x, y, z, vx, vy, vz, mass = state
    r2 = x * x + y * y + z * z
    r = math.sqrt(r2)
    if r <= 0.0 or mass <= 0.0:
        raise ValueError("integration left the domain")
    thrust, isp = profile.at(t)
    c = isp * G0
    mdot = thrust / c if c > 0.0 else 0.0
    r_vec = (x, y, z)
    v_vec = (vx, vy, vz)
    ux, uy, uz = thrust_direction(role, r_vec, v_vec, mu, i_target, Omega, r_target)
    ax = -mu * x / (r2 * r) + (thrust / mass) * ux
    ay = -mu * y / (r2 * r) + (thrust / mass) * uy
    az = -mu * z / (r2 * r) + (thrust / mass) * uz
    return (vx, vy, vz, ax, ay, az, -mdot)


def rk4_step(
    t: float,
    state: tuple[float, ...],
    dt: float,
    **kwargs: object,
) -> tuple[float, ...]:
    k1 = derivatives(t, state, **kwargs)  # type: ignore[arg-type]
    s2 = tuple(s + 0.5 * dt * k for s, k in zip(state, k1))
    k2 = derivatives(t + 0.5 * dt, s2, **kwargs)  # type: ignore[arg-type]
    s3 = tuple(s + 0.5 * dt * k for s, k in zip(state, k2))
    k3 = derivatives(t + 0.5 * dt, s3, **kwargs)  # type: ignore[arg-type]
    s4 = tuple(s + dt * k for s, k in zip(state, k3))
    k4 = derivatives(t + dt, s4, **kwargs)  # type: ignore[arg-type]
    return tuple(
        s + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0
        for s, a, b, c, d in zip(state, k1, k2, k3, k4)
    )


def integrate_burn(
    *,
    mu: float,
    state0: tuple[float, float, float, float, float, float],
    mass0: float,
    t0: float,
    profile: ThrustProfile,
    role: str,
    i_target: float,
    Omega: float,
    mass_floor: float,
    stop_fn,
    max_duration: float,
    r_target: float,
) -> tuple[
    tuple[float, float, float, float, float, float],
    float,
    float,
    float,
    float,
    float,
    list[tuple[float, float, float]],
    tuple[float, float, float],
    tuple[float, float, float],
    bool,
]:
    state7: tuple[float, ...] = (*state0, mass0)
    t = t0
    dv_steered = 0.0
    gravity_loss = 0.0
    dv_plane = 0.0
    path: list[tuple[float, float, float]] = [(state0[0], state0[1], state0[2])]
    mid_pos = path[0]
    mid_dir = thrust_direction(role, state0[:3], state0[3:], mu, i_target, Omega, r_target)
    hit_floor = False
    steps = max(RK4_SUBSTEPS, int(max_duration / 5.0) * RK4_SUBSTEPS)
    dt_nom = max_duration / steps
    sample_countdown = SAMPLE_EVERY
    for step in range(steps):
        x, y, z, vx, vy, vz, mass = state7
        r = math.sqrt(x * x + y * y + z * z)
        thrust, _isp = profile.at(t)
        if mass <= mass_floor + 1e-12 or thrust <= 0.0:
            hit_floor = mass <= mass_floor + 1e-12
            break
        if stop_fn((x, y, z, vx, vy, vz), mass, t - t0):
            break
        u = thrust_direction(role, (x, y, z), (vx, vy, vz), mu, i_target, Omega, r_target)
        # Plane-change share: thrust component along target-plane normal.
        n_hat = unit(target_plane_normal(i_target, Omega))
        # Out-of-plane unit from current velocity/plane vs target: use |u · n_hat|.
        plane_frac = abs(dot(u, n_hat))
        # Gravity loss: g*sin(theta) along the path (velocity direction), not thrust.
        try:
            v_hat = unit((vx, vy, vz))
            g_oppose = max(0.0, (mu / (r * r * r)) * (x * v_hat[0] + y * v_hat[1] + z * v_hat[2]))
        except ValueError:
            g_oppose = 0.0
        state7 = rk4_step(
            t,
            state7,
            dt_nom,
            mu=mu,
            profile=profile,
            role=role,
            i_target=i_target,
            Omega=Omega,
            r_target=r_target,
        )
        t += dt_nom
        dv_steered += (thrust / mass) * dt_nom
        gravity_loss += g_oppose * dt_nom
        dv_plane += (thrust / mass) * plane_frac * dt_nom
        sample_countdown -= 1
        if sample_countdown <= 0:
            path.append((state7[0], state7[1], state7[2]))
            sample_countdown = SAMPLE_EVERY
        if step == steps // 2:
            mid_pos = (state7[0], state7[1], state7[2])
            mid_dir = u
        if state7[6] <= mass_floor:
            hit_floor = True
            break
    path.append((state7[0], state7[1], state7[2]))
    final_state = (state7[0], state7[1], state7[2], state7[3], state7[4], state7[5])
    return final_state, state7[6], t, dv_steered, gravity_loss, dv_plane, path, mid_pos, mid_dir, hit_floor


def apoapsis_reached(mu: float, state: tuple[float, float, float, float, float, float], ra_goal: float) -> bool:
    """True when energy/h apoapsis has reached ra_goal (no classical-element inversion)."""
    scalars = keplerian_scalars(mu, state)
    ra = float(scalars["ra"])
    if not math.isfinite(ra):
        # Hyperbolic / escape: treat as apoapsis goal met so the raise stops.
        return True
    tol = max(1e-6 * abs(ra_goal), 1e-9)
    return ra >= ra_goal - tol


def circularized(
    mu: float,
    state: tuple[float, float, float, float, float, float],
    r_target: float,
    i_target: float,
    Omega: float,
) -> bool:
    scalars = keplerian_scalars(mu, state)
    r = float(scalars["r"])
    r_vec = (state[0], state[1], state[2])
    v_vec = (state[3], state[4], state[5])
    v_des = desired_circular_velocity(r_vec, mu, i_target, Omega, r_target)
    vg = (v_des[0] - v_vec[0], v_des[1] - v_vec[1], v_des[2] - v_vec[2])
    vg_mag = math.sqrt(dot(vg, vg))
    speed_tol = max(CIRC_SPEED_TOL, 2e-3 * math.sqrt(mu / max(r_target, 1.0)))
    radius_tol = max(0.005 * r_target, 1e-6 * r_target)
    e = float(scalars["e"])
    i = float(scalars["i"])
    if not math.isfinite(e):
        return False
    return (
        vg_mag < speed_tol
        and abs(r - r_target) < radius_tol
        and abs(i - i_target) < max(INC_TOL, 2e-3)
        and e < CIRC_E_TOL
    )


def simulate_raise(
    *,
    mode: str,
    body: Body,
    park_orbit: object,
    park_state: tuple[float, float, float, float, float, float],
    r_target: float,
    i_target: float,
    profile: ThrustProfile,
    m0: float,
    mass_floor: float,
    n_burns: int,
) -> RaiseResult:
    op = op_mod()
    warnings: list[str] = []
    metrics0 = orbit_metrics(body.mu, park_state)
    r_park = metrics0["r"]
    # Use periapsis of parking ellipse as the raise base radius when e is small use r.
    r_base = metrics0["rp"] if metrics0["e"] > CIRCULAR_E else r_park
    if r_target < r_base:
        warnings.append("target below parking periapsis; raise burns are retrograde / not a LEO raise")
    if metrics0["rp"] < body.radius:
        warnings.append("parking periapsis is inside R0")

    thrust0, isp0 = profile.at(0.0)
    if n_burns < 2:
        n_burns = 2
    n_burns = min(MAX_BURNS, n_burns)
    n_raise = n_burns - 1

    state = park_state
    mass = m0
    t = 0.0
    burns: list[BurnArc] = []
    coasts: list[CoastArc] = []
    exhausted = False

    def try_coast(nu_target: float) -> bool:
        """Coast to nu_target. On domain failure, warn and stop the raise."""
        nonlocal state, t, exhausted
        try:
            t_coast0 = t
            state, t, path = coast_to_true_anomaly(body.mu, state, nu_target, t)
            coasts.append(CoastArc(t_coast0, t, path))
            return True
        except ValueError as exc:
            exhausted = True
            warnings.append(
                f"trajectory left the elliptical domain during coast ({exc}); "
                "stopping with the last valid state"
            )
            return False

    def peek_metrics() -> dict[str, float] | None:
        try:
            return orbit_metrics(body.mu, state)
        except ValueError:
            return None

    def soft_nu(default: float = 0.0) -> float:
        metrics = peek_metrics()
        return float(metrics["nu"]) if metrics is not None else default

    def soft_Omega(default: float) -> float:
        metrics = peek_metrics()
        if metrics is not None:
            return float(metrics["Omega"])
        # Fallback: node from angular momentum.
        h_vec = cross((state[0], state[1], state[2]), (state[3], state[4], state[5]))
        n_xy = math.hypot(-h_vec[1], h_vec[0])
        if n_xy <= 0.0:
            return default
        return math.atan2(h_vec[0], -h_vec[1])

    # Coast to periapsis for the first raise burn.
    if abs(op.wrap_pi(metrics0["nu"])) > 1e-3:
        if not try_coast(0.0):
            pass

    if not exhausted:
        for k in range(1, n_raise + 1):
            metrics = peek_metrics()
            Omega = soft_Omega(metrics0["Omega"] if metrics is None else metrics["Omega"])
            scalars = keplerian_scalars(body.mu, state)
            ra_goal = r_base + (r_target - r_base) * (k / n_raise)
            # Ensure we are near periapsis before a raise burn.
            nu_now = soft_nu(0.0)
            if abs(op.wrap_pi(nu_now)) > 0.25:
                if not try_coast(0.0):
                    break
                Omega = soft_Omega(Omega)
                scalars = keplerian_scalars(body.mu, state)

            a_ref = float(scalars["a"]) if scalars["elliptic"] and math.isfinite(float(scalars["a"])) else r_base
            period = 2.0 * math.pi * math.sqrt(max(a_ref, r_base) ** 3 / body.mu)
            max_duration = min(0.45 * period, 0.45 * 2.0 * math.pi * math.sqrt(r_target**3 / body.mu))

            def stop_raise(st: tuple[float, ...], _mass: float, _dt: float, goal=ra_goal) -> bool:
                try:
                    return apoapsis_reached(body.mu, st, goal)  # type: ignore[arg-type]
                except ValueError:
                    return False

            nu_start = soft_nu(0.0)
            t_start = t
            try:
                (
                    state,
                    mass,
                    t,
                    dv_s,
                    gl,
                    dv_p,
                    path,
                    mid_pos,
                    mid_dir,
                    hit_floor,
                ) = integrate_burn(
                    mu=body.mu,
                    state0=state,
                    mass0=mass,
                    t0=t,
                    profile=profile,
                    role="raise",
                    i_target=i_target,
                    Omega=Omega,
                    mass_floor=mass_floor,
                    stop_fn=stop_raise,
                    max_duration=max_duration,
                    r_target=r_target,
                )
            except ValueError as exc:
                exhausted = True
                warnings.append(
                    f"raise burn left the integration domain ({exc}); "
                    "stopping with the last valid state"
                )
                break
            nu_end = soft_nu(nu_start)
            burns.append(
                BurnArc(
                    index=len(burns) + 1,
                    role="raise",
                    t_start=t_start,
                    t_end=t,
                    nu_start=nu_start,
                    nu_end=nu_end,
                    dv_steered=dv_s,
                    gravity_loss=gl,
                    dv_plane=dv_p,
                    path_m=path,
                    mid_pos_m=mid_pos,
                    mid_dv_dir=mid_dir,
                )
            )
            if hit_floor:
                exhausted = True
                warnings.append("propellant exhaustion before circularization")
                break
            if not apoapsis_reached(body.mu, state, ra_goal):
                warnings.append(
                    "thrust too low for the requested burn count; "
                    "raise burn hit the duration cap before the apoapsis goal"
                )
                exhausted = True
                break

            if k < n_raise:
                # Multi-rev raise: coast apoapsis → periapsis for the next raise burn.
                if not try_coast(math.pi):
                    break
                if not try_coast(0.0):
                    break
            else:
                # Last raise: coast to apoapsis for circularization.
                if not try_coast(math.pi):
                    break

    if not exhausted:
        # Be at apoapsis for circularization.
        nu_now = soft_nu(math.pi)
        if abs(abs(op.wrap_pi(nu_now)) - math.pi) > 0.2:
            if not try_coast(math.pi):
                pass
        if not exhausted:
            Omega = soft_Omega(metrics0["Omega"])
            scalars = keplerian_scalars(body.mu, state)
            a_ref = float(scalars["a"]) if scalars["elliptic"] and math.isfinite(float(scalars["a"])) else r_target
            period = 2.0 * math.pi * math.sqrt(max(a_ref, r_target) ** 3 / body.mu)
            max_duration = 1.5 * period

            def stop_circ(st: tuple[float, ...], _mass: float, _dt: float) -> bool:
                try:
                    return circularized(body.mu, st, r_target, i_target, Omega)  # type: ignore[arg-type]
                except ValueError:
                    return False

            nu_start = soft_nu(math.pi)
            t_start = t
            try:
                (
                    state,
                    mass,
                    t,
                    dv_s,
                    gl,
                    dv_p,
                    path,
                    mid_pos,
                    mid_dir,
                    hit_floor,
                ) = integrate_burn(
                    mu=body.mu,
                    state0=state,
                    mass0=mass,
                    t0=t,
                    profile=profile,
                    role="circularize",
                    i_target=i_target,
                    Omega=Omega,
                    mass_floor=mass_floor,
                    stop_fn=stop_circ,
                    max_duration=max_duration,
                    r_target=r_target,
                )
            except ValueError as exc:
                exhausted = True
                warnings.append(
                    f"circularize burn left the integration domain ({exc}); "
                    "stopping with the last valid state"
                )
            else:
                nu_end = soft_nu(nu_start)
                burns.append(
                    BurnArc(
                        index=len(burns) + 1,
                        role="circularize",
                        t_start=t_start,
                        t_end=t,
                        nu_start=nu_start,
                        nu_end=nu_end,
                        dv_steered=dv_s,
                        gravity_loss=gl,
                        dv_plane=dv_p,
                        path_m=path,
                        mid_pos_m=mid_pos,
                        mid_dv_dir=mid_dir,
                    )
                )
                try:
                    circ_ok = circularized(body.mu, state, r_target, i_target, Omega)
                except ValueError:
                    circ_ok = False
                if hit_floor and not circ_ok:
                    warnings.append("propellant exhaustion before circularization")
                elif not circ_ok:
                    warnings.append(
                        "circularization tolerance not fully met; report final state as reached"
                    )

    try:
        final_metrics = orbit_metrics(body.mu, state)
    except ValueError:
        # Energy/h scalars remain defined when classical inversion fails.
        scalars = keplerian_scalars(body.mu, state)
        final_metrics = {
            "a": float(scalars["a"]),
            "e": float(scalars["e"]),
            "i": float(scalars["i"]),
            "Omega": metrics0["Omega"],
            "omega": 0.0,
            "nu": 0.0,
            "rp": float(scalars["rp"]),
            "ra": float(scalars["ra"]),
            "r": float(scalars["r"]),
            "v": float(scalars["v"]),
        }
    if math.isfinite(final_metrics["rp"]) and final_metrics["rp"] < body.radius:
        warnings.append("periapsis inside R0")
    if math.isfinite(final_metrics["e"]) and final_metrics["e"] >= CIRC_E_TOL:
        if "circularization tolerance not fully met" not in " ".join(warnings):
            if not any("propellant exhaustion" in w for w in warnings) and not any(
                "elliptical domain" in w for w in warnings
            ) and not any("thrust too low" in w for w in warnings):
                warnings.append(
                    "circularization tolerance not fully met; report final state as reached"
                )

    dv_steered = sum(b.dv_steered for b in burns)
    dv_gravity = sum(b.gravity_loss for b in burns)
    di = i_target - metrics0["i"]
    if abs(di) <= 1e-12:
        dv_plane = 0.0
    else:
        # Out-of-plane share of steered thrust; not the pure impulsive plane-change cost.
        dv_plane = sum(b.dv_plane for b in burns)

    tof_burn = sum(b.t_end - b.t_start for b in burns)
    tof_coast = sum(c.t_end - c.t_start for c in coasts)
    epoch = {
        "a": park_orbit.a,
        "e": park_orbit.e,
        "i": park_orbit.i,
        "Omega": park_orbit.Omega,
        "omega": park_orbit.omega,
        "nu": park_orbit.nu,
        "M": park_orbit.M,
    }
    return RaiseResult(
        mode=mode,
        body=body,
        thrust_profile=profile,
        m0=m0,
        mf=mass,
        mp_used=m0 - mass,
        n_burns=len(burns),
        burns=burns,
        coasts=coasts,
        r_park=r_park,
        h_park=r_park - body.radius,
        i_park=metrics0["i"],
        Omega_park=metrics0["Omega"],
        omega_park=metrics0["omega"],
        e_park=metrics0["e"],
        a_park=metrics0["a"],
        r_target=r_target,
        h_target=r_target - body.radius,
        i_target=i_target,
        a_target=r_target,
        e_target=final_metrics["e"],
        v_circular_target=math.sqrt(body.mu / r_target),
        dv_steered=dv_steered,
        dv_gravity_loss=dv_gravity,
        dv_plane_change=dv_plane,
        dv_total=dv_steered,
        tof=t,
        tof_burn=tof_burn,
        tof_coast=tof_coast,
        warnings=warnings,
        park_state=park_state,
        final_state=state,
        epoch_elements=epoch,
    )


def sample_orbit_km(mu: float, a: float, e: float, i: float, Omega: float, omega: float, count: int = 181) -> list[list[float]]:
    op = op_mod()
    pts: list[list[float]] = []
    for j in range(count):
        nu = -math.pi + 2.0 * math.pi * j / (count - 1)
        if e >= 1.0:
            break
        x, y, z, *_ = op.state_from_elements(mu, a, e, i, Omega, omega, nu)
        pts.append([km(x), km(y), km(z)])
    return pts


def ensure_matplotlib():
    return op_mod().ensure_matplotlib()


def plot_png(path: Path, result: RaiseResult) -> None:
    plt = ensure_matplotlib()
    op = op_mod()
    fig = plt.figure(figsize=(9.0, 7.6))
    ax = fig.add_subplot(111, projection="3d")
    body = result.body
    palette = dict(op.PALETTE)

    # Planet wire sphere.
    u = [i / 24 * 2 * math.pi for i in range(25)]
    v = [i / 12 * math.pi for i in range(13)]
    for vv in v:
        xs = [km(body.radius * math.sin(vv) * math.cos(uu)) for uu in u]
        ys = [km(body.radius * math.sin(vv) * math.sin(uu)) for uu in u]
        zs = [km(body.radius * math.cos(vv)) for uu in u]
        ax.plot(xs, ys, zs, color=palette["planet_edge"], linewidth=0.4, alpha=0.55)
    for uu in u[::3]:
        xs = [km(body.radius * math.sin(vv) * math.cos(uu)) for vv in v]
        ys = [km(body.radius * math.sin(vv) * math.sin(uu)) for vv in v]
        zs = [km(body.radius * math.cos(vv)) for vv in v]
        ax.plot(xs, ys, zs, color=palette["planet_edge"], linewidth=0.4, alpha=0.55)

    park_pts = sample_orbit_km(
        body.mu, result.a_park, result.e_park, result.i_park, result.Omega_park, result.omega_park
    )
    if park_pts:
        ax.plot(
            [p[0] for p in park_pts],
            [p[1] for p in park_pts],
            [p[2] for p in park_pts],
            color=PARK_COLOR,
            linestyle="--",
            linewidth=1.2,
            label="parking orbit",
        )
    tgt_pts = sample_orbit_km(body.mu, result.a_target, 0.0, result.i_target, result.Omega_park, 0.0)
    if tgt_pts:
        ax.plot(
            [p[0] for p in tgt_pts],
            [p[1] for p in tgt_pts],
            [p[2] for p in tgt_pts],
            color=TARGET_COLOR,
            linestyle=":",
            linewidth=1.4,
            label="target orbit",
        )

    for coast in result.coasts:
        if len(coast.path_m) < 2:
            continue
        ax.plot(
            [km(p[0]) for p in coast.path_m],
            [km(p[1]) for p in coast.path_m],
            [km(p[2]) for p in coast.path_m],
            color=COAST_COLOR,
            linestyle="--",
            linewidth=1.0,
            alpha=0.9,
        )
    for burn in result.burns:
        if len(burn.path_m) < 2:
            continue
        ax.plot(
            [km(p[0]) for p in burn.path_m],
            [km(p[1]) for p in burn.path_m],
            [km(p[2]) for p in burn.path_m],
            color=BURN_COLOR,
            linestyle="-",
            linewidth=2.0,
            label="burn arc" if burn.index == 1 else None,
        )
        origin = (km(burn.mid_pos_m[0]), km(burn.mid_pos_m[1]), km(burn.mid_pos_m[2]))
        direction = burn.mid_dv_dir
        span = 0.08 * km(max(result.r_target, result.r_park))
        ax.quiver(
            origin[0],
            origin[1],
            origin[2],
            direction[0] * span,
            direction[1] * span,
            direction[2] * span,
            color=DV_COLOR,
            linewidth=1.6,
            arrow_length_ratio=0.25,
        )

    ax.scatter(
        [km(result.park_state[0])],
        [km(result.park_state[1])],
        [km(result.park_state[2])],
        color="#27ae60",
        s=35,
        label="epoch",
    )
    ax.scatter(
        [km(result.final_state[0])],
        [km(result.final_state[1])],
        [km(result.final_state[2])],
        color=palette["craft"],
        s=40,
        label="arrival",
    )

    limit = km(max(result.r_target, result.r_park, body.radius) * 1.25)
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Z (km)")
    ax.set_title(PLOT_TITLE)
    ax.view_init(elev=PNG_ELEV_DEG, azim=PNG_AZIM_DEG)
    ax.legend(loc="upper left", fontsize=8)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def build_payload(result: RaiseResult) -> dict[str, object]:
    op = op_mod()
    body = result.body
    limit_m = max(result.r_target, result.r_park, body.radius) * 1.3
    park = sample_orbit_km(
        body.mu, result.a_park, result.e_park, result.i_park, result.Omega_park, result.omega_park, 241
    )
    target = sample_orbit_km(body.mu, result.a_target, 0.0, result.i_target, result.Omega_park, 0.0, 241)
    segments: list[dict[str, object]] = []
    for coast in result.coasts:
        segments.append(
            {
                "kind": "coast",
                "color": COAST_COLOR,
                "km": [[km(p[0]), km(p[1]), km(p[2])] for p in coast.path_m],
                "t0": coast.t_start,
                "t1": coast.t_end,
            }
        )
    for burn in result.burns:
        segments.append(
            {
                "kind": "burn",
                "color": BURN_COLOR,
                "km": [[km(p[0]), km(p[1]), km(p[2])] for p in burn.path_m],
                "t0": burn.t_start,
                "t1": burn.t_end,
                "label": f"burn {burn.index} ({burn.role})",
            }
        )
    segments.sort(key=lambda s: float(s["t0"]))
    trail: list[list[float]] = []
    times: list[float] = []
    for seg in segments:
        pts = seg["km"]
        t0, t1 = float(seg["t0"]), float(seg["t1"])
        for i, p in enumerate(pts):
            alpha = 0.0 if len(pts) == 1 else i / (len(pts) - 1)
            times.append(t0 + alpha * (t1 - t0))
            trail.append(p)
    burns = []
    for burn in result.burns:
        burns.append(
            {
                "km": [km(burn.mid_pos_m[0]), km(burn.mid_pos_m[1]), km(burn.mid_pos_m[2])],
                "dv_dir": list(burn.mid_dv_dir),
                "color": DV_COLOR,
                "label": f"burn {burn.index}",
            }
        )
    palette = dict(op.PALETTE)
    palette["dv"] = DV_COLOR
    palette["burn"] = BURN_COLOR
    palette["coast"] = COAST_COLOR
    return {
        "title": PLOT_TITLE,
        "elev_deg": PNG_ELEV_DEG,
        "azim_deg": PNG_AZIM_DEG,
        "roll_deg": op.CAMERA_ROLL_DEG,
        "limit_km": km(limit_m),
        "equatorial_radius_km": km(body.radius),
        "polar_radius_km": km(body.radius),
        "planet_segments_u": op.PLANET_SEGMENTS_U,
        "planet_segments_v": op.PLANET_SEGMENTS_V,
        "planet_opacity": 0.5,
        "palette": palette,
        "parking_km": park,
        "target_km": target,
        "segments": segments,
        "trail_km": trail,
        "trail_t_s": times,
        "burns": burns,
        "craft0_km": [km(result.park_state[0]), km(result.park_state[1]), km(result.park_state[2])],
        "legend": [
            {"label": "planet", "color": palette["planet"]},
            {"label": "parking orbit", "color": PARK_COLOR},
            {"label": "target orbit", "color": TARGET_COLOR},
            {"label": "burn arc", "color": BURN_COLOR},
            {"label": "coast", "color": COAST_COLOR},
            {"label": "delta-v", "color": DV_COLOR},
        ],
    }


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
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    before, placeholder, after = template.partition("__THREE_SOURCE__")
    if not placeholder:
        raise ValueError("viewer template is missing the Three.js placeholder")
    before = (
        before.replace("__TITLE__", PLOT_TITLE)
        .replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
        .replace("__SCENE_JSON__", encoded)
    )
    after = after.replace("__TITLE__", PLOT_TITLE).replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
    if "__SCENE_JSON__" in before or "__SCENE_JSON__" in after:
        raise ValueError("viewer template still has an unreplaced scene payload")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(before + three_source + after, encoding="utf-8")


def print_report(result: RaiseResult, graph: Path, viewer: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", result.mode)
    print_kv("R0_m", result.body.radius)
    print_kv("R0_source", result.body.radius_source)
    print_kv("g0_m_s2", result.body.g0)
    print_kv("mu_m3_s2", result.body.mu)
    el = result.epoch_elements
    if el.get("a") is not None:
        print_kv("a_park_m", float(el["a"]))
    print_kv("e_park", result.e_park)
    print_kv("i_park_rad", result.i_park)
    print_kv("Omega_park_rad", result.Omega_park)
    print_kv("omega_park_rad", result.omega_park)
    if el.get("nu") is not None:
        print_kv("nu_park_rad", float(el["nu"]))
    if el.get("M") is not None:
        print_kv("M_park_rad", float(el["M"]))
    print_kv("r_park_m", result.r_park)
    print_kv("h_park_m", result.h_park)
    print_kv("rx_m", result.park_state[0])
    print_kv("ry_m", result.park_state[1])
    print_kv("rz_m", result.park_state[2])
    print_kv("vx_m_s", result.park_state[3])
    print_kv("vy_m_s", result.park_state[4])
    print_kv("vz_m_s", result.park_state[5])
    print_kv("r_target_m", result.r_target)
    print_kv("h_target_m", result.h_target)
    print_kv("i_target_rad", result.i_target)
    print_kv("i_final_rad", float(keplerian_scalars(result.body.mu, result.final_state)["i"]))
    print_kv("a_target_m", result.a_target)
    print_kv("e_target", result.e_target)
    print_kv("v_circular_target_m_s", result.v_circular_target)
    print_kv("thrust_profile", result.thrust_profile.kind)
    thrust0, isp0 = result.thrust_profile.at(0.0)
    print_kv("thrust_N", thrust0)
    print_kv("isp_s", isp0)
    print_kv("c_m_s", isp0 * G0)
    print_kv("m0_kg", result.m0)
    print_kv("mf_kg", result.mf)
    print_kv("mp_used_kg", result.mp_used)
    print_kv("n_burns", result.n_burns)
    for burn in result.burns:
        k = burn.index
        print_kv(f"burn_{k}_role", burn.role)
        print_kv(f"burn_{k}_t_start_s", burn.t_start)
        print_kv(f"burn_{k}_t_end_s", burn.t_end)
        print_kv(f"burn_{k}_dt_s", burn.t_end - burn.t_start)
        print_kv(f"burn_{k}_nu_start_rad", burn.nu_start)
        print_kv(f"burn_{k}_nu_end_rad", burn.nu_end)
        print_kv(f"burn_{k}_dv_steered_m_s", burn.dv_steered)
        print_kv(f"burn_{k}_gravity_loss_m_s", burn.gravity_loss)
    print_kv("dv_steered_m_s", result.dv_steered)
    print_kv("dv_gravity_loss_m_s", result.dv_gravity_loss)
    print_kv("dv_plane_change_m_s", result.dv_plane_change)
    print_kv("dv_total_m_s", result.dv_total)
    print_kv("tof_s", result.tof)
    print_kv("tof_burn_s", result.tof_burn)
    print_kv("tof_coast_s", result.tof_coast)
    print_kv("rx_final_m", result.final_state[0])
    print_kv("ry_final_m", result.final_state[1])
    print_kv("rz_final_m", result.final_state[2])
    print_kv("vx_final_m_s", result.final_state[3])
    print_kv("vy_final_m_s", result.final_state[4])
    print_kv("vz_final_m_s", result.final_state[5])
    for warning in result.warnings:
        print_kv("warning", warning)
    print_kv("graph", str(graph))
    if viewer is not None:
        print_kv("viewer", str(viewer))


def run(args: argparse.Namespace) -> int:
    body = make_body(args.R0)
    mode, park_orbit, park_state = parking_from_args(args, body)
    r_target, i_target = resolve_target(args, body, park_orbit.i)

    if args.m0 is None:
        raise ValueError("--m0 is required")
    require_finite(args.m0, "--m0")
    if args.m0 <= 0.0:
        raise ValueError("--m0 must be > 0 kg")

    if args.mf is not None and args.mp is not None:
        raise ValueError("pass --mf or --mp, not both")
    if args.mf is not None:
        require_finite(args.mf, "--mf")
        if not (0.0 < args.mf < args.m0):
            raise ValueError("--mf must be in (0, m0)")
        mass_floor = args.mf
    elif args.mp is not None:
        require_finite(args.mp, "--mp")
        if not (0.0 < args.mp < args.m0):
            raise ValueError("--mp must be in (0, m0)")
        mass_floor = args.m0 - args.mp
    else:
        mass_floor = MASS_FLOOR_FRAC * args.m0

    if args.profile is not None and args.thrust is not None:
        raise ValueError("pass --thrust or --profile, not both")
    if args.profile is not None:
        profile = load_profile(Path(args.profile), args.isp)
    else:
        if args.thrust is None or args.isp is None:
            raise ValueError("constant thrust needs --thrust and --isp (or pass --profile)")
        require_finite(args.thrust, "--thrust")
        require_finite(args.isp, "--isp")
        if args.thrust <= 0.0:
            raise ValueError("--thrust must be > 0 N")
        if args.isp <= 0.0:
            raise ValueError("--isp must be > 0 s")
        profile = ThrustProfile("constant", args.thrust, args.isp)

    metrics = orbit_metrics(body.mu, park_state)
    r_ref = metrics["rp"] if metrics["e"] > CIRCULAR_E else metrics["r"]
    thrust0, isp0 = profile.at(0.0)
    if args.burns is None:
        n_burns = default_burn_count(body.mu, r_ref, r_target, thrust0, args.m0, isp0)
    else:
        if args.burns < 2:
            raise ValueError(
                "--burns must be >= 2 (at least one raise burn plus circularization)"
            )
        if args.burns > MAX_BURNS:
            raise ValueError(f"--burns must be <= {MAX_BURNS}")
        n_burns = args.burns

    result = simulate_raise(
        mode=mode,
        body=body,
        park_orbit=park_orbit,
        park_state=park_state,
        r_target=r_target,
        i_target=i_target,
        profile=profile,
        m0=args.m0,
        mass_floor=mass_floor,
        n_burns=n_burns,
    )

    out_path = Path(args.out) if args.out else SKILL_DIR / "multi_burn_leo_raise.png"
    plot_png(out_path, result)
    viewer_path = out_path.with_suffix(".html")
    wrote_html = False
    if args.html or args.open:
        write_viewer_html(viewer_path, build_payload(result))
        wrote_html = True
    print_report(result, out_path, viewer_path if wrote_html else None)
    if args.open:
        webbrowser.open(viewer_path.as_uri())
    return 0


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"check: fail: {message}", file=sys.stderr)
        return 1

    # Unitless tiny planet for a fast finite-thrust raise.
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "raise.png")
        code = main(
            [
                "--a",
                "2.0",
                "--e",
                "0.0",
                "--i",
                "0.2",
                "--raan",
                "0.0",
                "--aop",
                "0.0",
                "--nu",
                "0.0",
                "--r-target",
                "2.4",
                "--i-target",
                "0.25",
                "--thrust",
                "0.25",
                "--isp",
                "300",
                "--m0",
                "1.0",
                "--mp",
                "0.5",
                "--burns",
                "2",
                "--R0",
                "1.0",
                "--out",
                out,
                "--html",
            ]
        )
        if code != 0:
            return fail(f"main returned {code}")
        if not Path(out).is_file() or not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("PNG not written")
        html = Path(out).with_suffix(".html")
        if not html.is_file():
            return fail("HTML not written")
        text = html.read_text(encoding="utf-8")
        if PLOT_TITLE not in text or "__SCENE_JSON__" in text or "__THREE_SOURCE__" in text:
            return fail("HTML placeholders remain")
        if "new THREE." not in text and "THREE.WebGLRenderer" not in text:
            return fail("Three.js is not inlined")

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
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finite-thrust multi-burn LEO raise.")
    parser.add_argument("--a", type=float, default=None, help="parking semi-major axis [m]")
    parser.add_argument("--e", type=float, default=None, help="parking eccentricity")
    parser.add_argument("--i", type=float, default=None, help="parking inclination [rad]")
    parser.add_argument("--raan", type=float, default=None, help="parking RAAN Omega [rad]")
    parser.add_argument("--aop", type=float, default=None, help="parking argument of periapsis [rad]")
    parser.add_argument("--nu", type=float, default=None, help="parking true anomaly [rad]")
    parser.add_argument("--M", type=float, default=None, help="parking mean anomaly [rad]")
    parser.add_argument("--rx", type=float, default=None, help="parking inertial x [m]")
    parser.add_argument("--ry", type=float, default=None, help="parking inertial y [m]")
    parser.add_argument("--rz", type=float, default=None, help="parking inertial z [m]")
    parser.add_argument("--vx", type=float, default=None, help="parking inertial vx [m/s]")
    parser.add_argument("--vy", type=float, default=None, help="parking inertial vy [m/s]")
    parser.add_argument("--vz", type=float, default=None, help="parking inertial vz [m/s]")
    parser.add_argument("--alt-target", type=float, default=None, help="target circular altitude [m]")
    parser.add_argument("--r-target", type=float, default=None, help="target circular radius [m]")
    parser.add_argument("--i-target", type=float, default=None, help="target inclination [rad]")
    parser.add_argument("--thrust", type=float, default=None, help="constant thrust [N]")
    parser.add_argument("--isp", type=float, default=None, help="vacuum specific impulse [s]")
    parser.add_argument("--m0", type=float, default=None, help="ignition mass [kg]")
    parser.add_argument("--mf", type=float, default=None, help="burnout mass floor [kg]")
    parser.add_argument("--mp", type=float, default=None, help="propellant mass [kg]")
    parser.add_argument("--profile", type=str, default=None, help="thrust-vs-time table path")
    parser.add_argument("--burns", type=int, default=None, help="number of powered arcs")
    parser.add_argument("--R0", type=float, default=None, help=f"planetary radius [m]; default {R0_EARTH:.8g}")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--html", action="store_true", help="write the HTML 3D viewer")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer")
    parser.add_argument("--check", action="store_true", help="run built-in checks")
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
