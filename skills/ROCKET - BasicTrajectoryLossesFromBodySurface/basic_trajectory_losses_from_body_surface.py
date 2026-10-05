#!/usr/bin/env python3
"""Simplified powered ascent from a spherical body surface.

Ideal vacuum delta-v is delta_v_vacuum. Path acceleration is
powered_path_acceleration. Constant flight-path angle uses
constant_angle_speed (and constant_angle_speed_const_drag). A gravity-turn
kick uses kick_flight_path_angle then gravity_turn_angle_rate with thrust
along the velocity. Losses are gravity_loss_definition, drag_loss_definition,
and steering_loss_definition.
"""

from __future__ import annotations

import argparse
import io
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-6
G0_STD = 9.80665
R_EARTH = 6.356766e6
Z_MAX_1976 = 86000.0
V_MIN = 1e-9
V_ALIGN = 50.0
N_PLOT = 401
N_STEP = 8000
PLOT_TITLE = "Powered ascent"

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"
HUMID_DIR = SKILL_DIR.parent / "AERO - DensityAndPressureAltitude"

ASSUMPTIONS = (
    "spherical body; inverse-square g = mu/r**2 from "
    "gravitational_parameter_surface and gravity_inverse_square; "
    "start from rest at the surface radius; vacuum thrust T = mdot*c with "
    f"c = Isp*g0_std and g0_std = {G0_STD:g} m/s^2; constant mdot; "
    "powered_path_acceleration A = T/m - D/m - g*sin(theta); "
    "theta from the local horizontal; powered_radial_velocity V*sin(theta) and "
    "powered_horizontal_velocity V*cos(theta); "
    "constant_angle holds theta and, with no drag or a constant drag force, "
    "uses constant_angle_speed with g frozen at ignition; "
    "gravity_turn uses an instantaneous kick, holds that thrust axis until "
    f"speed exceeds {V_ALIGN:g} m/s so gravity_turn_angle_rate is not singular "
    "at rest, then thrust along the velocity; "
    "steering_loss is zero while thrust is along the velocity; "
    "drag is zero, a constant force, CD*q*S at frozen density, or CD*q*S "
    "with density from the 1976 atmosphere, an oat offset through "
    "AERO - DensityAndPressureAltitude, or an exponential rho0*exp(-Z/H); "
    "ambient pressure does not change thrust; no lift in the gravity turn; "
    "a constant-angle path is held by a normal force that is not drag"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_nonneg(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import (
            H_MAX,
            LAYERS,
            R0,
            atmosphere,
            geopotential_altitude,
            require_altitude,
        )
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for density versus altitude"
        ) from exc
    return atmosphere, require_altitude, LAYERS, R0, H_MAX, geopotential_altitude


def load_humidity():
    folder = str(HUMID_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from density_and_pressure_altitude import (
            atmosphere_density,
            moist_density,
            moist_mean_molar_mass,
            saturation_vapor_pressure,
            sound_speed,
            vapor_partial_pressure,
            water_molar_mass,
        )
        from standard_1976 import GAMMA, M0, RSTAR
    except ImportError as exc:
        raise ValueError(
            "AERO - DensityAndPressureAltitude must be importable for "
            "temperature and humidity"
        ) from exc
    return {
        "atmosphere_density": atmosphere_density,
        "moist_density": moist_density,
        "moist_mean_molar_mass": moist_mean_molar_mass,
        "saturation_vapor_pressure": saturation_vapor_pressure,
        "sound_speed": sound_speed,
        "vapor_partial_pressure": vapor_partial_pressure,
        "water_molar_mass": water_molar_mass,
        "M0": M0,
        "RSTAR": RSTAR,
        "GAMMA": GAMMA,
    }


def parcel_from_oat(
    pressure: float,
    temperature: float,
    rh: float | None,
    humid: dict,
) -> float:
    m0 = humid["M0"]
    rstar = humid["RSTAR"]
    if rh is None:
        return humid["atmosphere_density"](pressure, m0, rstar, temperature)
    es = humid["saturation_vapor_pressure"](temperature)
    vapor = humid["vapor_partial_pressure"](rh, es)
    if vapor >= pressure:
        return humid["atmosphere_density"](pressure, m0, rstar, temperature)
    mw = humid["water_molar_mass"]()
    return humid["moist_density"](pressure, vapor, m0, rstar, temperature, mw)


def gravitational_parameter_surface(g0: float, radius: float) -> float:
    """gravitational_parameter_surface."""
    return g0 * radius * radius


def gravity_at_radius(mu: float, radius: float) -> float:
    """gravity_inverse_square as mu/r**2."""
    return mu / (radius * radius)


def delta_v_vacuum(c: float, m0: float, mf: float) -> float:
    """delta_v_vacuum."""
    return c * math.log(m0 / mf)


def kick_flight_path_angle(alpha: float) -> float:
    """kick_flight_path_angle."""
    return math.pi / 2.0 - alpha


def constant_angle_speed(
    c: float, m0: float, mass: float, g: float, time: float, theta: float
) -> float:
    """constant_angle_speed."""
    return c * math.log(m0 / mass) - g * time * math.sin(theta)


def constant_drag_loss(drag: float, mdot: float, m0: float, mass: float) -> float:
    """constant_drag_loss."""
    return (drag / mdot) * math.log(m0 / mass)


def constant_angle_speed_const_drag(
    c: float,
    m0: float,
    mass: float,
    g: float,
    time: float,
    theta: float,
    drag: float,
    mdot: float,
) -> float:
    """constant_angle_speed_const_drag."""
    return constant_angle_speed(c, m0, mass, g, time, theta) - constant_drag_loss(
        drag, mdot, m0, mass
    )


def mass_integral(m0: float, mass: float, mdot: float) -> float:
    """integral of ln(m0/m) dt = (m0 - m - m ln(m0/m))/mdot."""
    return (m0 - mass - mass * math.log(m0 / mass)) / mdot


def constant_angle_path_length(
    c: float,
    m0: float,
    mf: float,
    mdot: float,
    g: float,
    tb: float,
    theta: float,
    drag: float = 0.0,
) -> float:
    """constant_angle_path_length plus a constant-drag path correction."""
    length = c * mass_integral(m0, mf, mdot) - 0.5 * g * tb * tb * math.sin(theta)
    if drag != 0.0:
        length -= (drag / mdot) * mass_integral(m0, mf, mdot)
    return length


def burnout_speed_from_losses(
    c: float, m0: float, mf: float, dvg: float, dvd: float, dve: float
) -> float:
    """burnout_speed_from_losses."""
    return delta_v_vacuum(c, m0, mf) - dvg - dvd - dve


def path_direction(ur: float, ut: float, theta_ref: float) -> tuple[float, float, float]:
    speed = math.hypot(ur, ut)
    if speed > V_ALIGN:
        return ur / speed, ut / speed, speed
    return math.sin(theta_ref), math.cos(theta_ref), speed


def drag_force_quadratic(cd: float, rho: float, area: float, speed: float) -> float:
    """drag_force with freestream_dynamic_pressure."""
    return cd * 0.5 * rho * speed * speed * area


def derivatives(
    _t: float,
    state: tuple[float, float, float, float, float, float],
    *,
    m0: float,
    mdot: float,
    thrust: float,
    mu: float,
    radius_body: float,
    theta_ref: float,
    drag_value: float | None,
    cd: float | None,
    area: float | None,
    density_at,
    hold_theta: bool = False,
) -> tuple[float, float, float, float, float, float]:
    radius, _phi, ur, ut, _lg, _ld = state
    mass = m0 - mdot * _t
    if mass <= 0.0:
        raise ValueError("mass reached zero during the burn")
    radius = max(radius, radius_body)
    g_local = gravity_at_radius(mu, radius)
    # A held flight-path angle is a constraint. Thrust and drag stay along the
    # path; the normal force that keeps theta fixed does no work, so it is not
    # a steering loss and it does not enter the speed equation.
    if hold_theta:
        sinth = math.sin(theta_ref)
        costh = math.cos(theta_ref)
        speed = math.hypot(ur, ut)
    else:
        sinth, costh, speed = path_direction(ur, ut, theta_ref)
    altitude = radius - radius_body
    if drag_value is not None:
        drag = drag_value
    elif cd is not None and area is not None:
        rho = 0.0 if density_at is None else density_at(altitude)
        drag = drag_force_quadratic(cd, max(rho, 0.0), area, speed)
    else:
        drag = 0.0
    accel_path = thrust / mass - drag / mass
    if hold_theta:
        d_speed = accel_path - g_local * sinth
        if radius <= radius_body + 1e-12 and speed <= V_MIN and d_speed < 0.0:
            d_speed = 0.0
        dur = d_speed * sinth
        dut = d_speed * costh
    else:
        dur = accel_path * sinth - g_local + ut * ut / radius
        dut = accel_path * costh - ur * ut / radius
        if radius <= radius_body + 1e-12 and dur < 0.0:
            dur = 0.0
    return (
        ur,
        ut / radius,
        dur,
        dut,
        g_local * sinth,
        drag / mass,
    )


def rk4_step(t: float, state: tuple, dt: float, kwargs: dict) -> tuple:
    k1 = derivatives(t, state, **kwargs)
    s2 = tuple(s + 0.5 * dt * k for s, k in zip(state, k1))
    k2 = derivatives(t + 0.5 * dt, s2, **kwargs)
    s3 = tuple(s + 0.5 * dt * k for s, k in zip(state, k2))
    k3 = derivatives(t + 0.5 * dt, s3, **kwargs)
    s4 = tuple(s + dt * k for s, k in zip(state, k3))
    k4 = derivatives(t + dt, s4, **kwargs)
    return tuple(
        s + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0
        for s, a, b, c, d in zip(state, k1, k2, k3, k4)
    )


def integrate_ode(
    *,
    m0: float,
    mf: float,
    mdot: float,
    tb: float,
    thrust: float,
    mu: float,
    radius_body: float,
    r_start: float,
    theta0: float,
    hold_theta: bool,
    drag_value: float | None,
    cd: float | None,
    area: float | None,
    density_at,
) -> dict:
    dt = tb / N_STEP
    ur = 0.0
    ut = 0.0
    state = (r_start, 0.0, ur, ut, 0.0, 0.0)
    times = [0.0]
    radii = [r_start]
    phis = [0.0]
    speeds = [0.0]
    thetas = [theta0]
    horizontal = False
    theta_ref = theta0
    kwargs = {
        "m0": m0,
        "mdot": mdot,
        "thrust": thrust,
        "mu": mu,
        "radius_body": radius_body,
        "theta_ref": theta_ref,
        "drag_value": drag_value,
        "cd": cd,
        "area": area,
        "density_at": density_at,
        "hold_theta": hold_theta,
    }
    t = 0.0
    for _ in range(N_STEP):
        if hold_theta:
            kwargs["theta_ref"] = theta0
        else:
            kwargs["theta_ref"] = theta_ref
        state = rk4_step(t, state, dt, kwargs)
        t += dt
        radius, phi, ur, ut, loss_g, loss_d = state
        if radius < radius_body:
            radius = radius_body
            if ur < 0.0:
                ur = 0.0
            state = (radius, phi, ur, ut, loss_g, loss_d)
        speed = math.hypot(ur, ut)
        if hold_theta and radius > radius_body + 1e-9:
            ur = speed * math.sin(theta0)
            ut = speed * math.cos(theta0)
            state = (radius, phi, ur, ut, loss_g, loss_d)
            theta = theta0
        elif speed > V_ALIGN:
            theta = math.atan2(ur, ut)
        else:
            theta = theta_ref
        if not hold_theta and speed > V_ALIGN:
            theta_ref = theta
        if theta <= 0.0:
            horizontal = True
        times.append(t)
        radii.append(radius)
        phis.append(phi)
        speeds.append(speed)
        thetas.append(theta)
    radius, phi, ur, ut, loss_g, loss_d = state
    speed = math.hypot(ur, ut)
    theta = math.atan2(ur, ut) if speed > V_ALIGN else thetas[-1]
    mass_end = m0 - mdot * tb
    if abs(mass_end - mf) > 1e-6 * m0:
        mass_end = mf
    c = thrust / mdot
    dve = 0.0
    v_from_losses = burnout_speed_from_losses(c, m0, mf, loss_g, loss_d, dve)
    return {
        "times": times,
        "radii": radii,
        "phis": phis,
        "speeds": speeds,
        "thetas": thetas,
        "V_bo": speed,
        "theta_bo": theta,
        "r_bo": radius,
        "phi_bo": phi,
        "dvg": loss_g,
        "dvD": loss_d,
        "dve": dve,
        "V_from_losses": v_from_losses,
        "horizontal": horizontal,
        "solver": "ode",
    }


def closed_constant_angle(
    *,
    m0: float,
    mf: float,
    mdot: float,
    tb: float,
    c: float,
    g: float,
    r_start: float,
    radius_body: float,
    theta: float,
    drag: float,
) -> dict:
    times = [tb * i / (N_PLOT - 1) for i in range(N_PLOT)]
    radii: list[float] = []
    phis: list[float] = []
    speeds: list[float] = []
    thetas = [theta] * N_PLOT
    sinth = math.sin(theta)
    costh = math.cos(theta)
    for time in times:
        mass = m0 - mdot * time
        if time <= 0.0:
            speed = 0.0
            path = 0.0
        else:
            if drag == 0.0:
                speed = constant_angle_speed(c, m0, mass, g, time, theta)
            else:
                speed = constant_angle_speed_const_drag(
                    c, m0, mass, g, time, theta, drag, mdot
                )
            path = constant_angle_path_length(
                c, m0, mass, mdot, g, time, theta, drag
            )
        radius = r_start + sinth * path
        if radius < radius_body:
            radius = radius_body
        if abs(sinth) < 1e-12:
            phi = path * costh / r_start
        else:
            phi = costh / sinth * math.log(radius / r_start) if radius > 0.0 else 0.0
        radii.append(radius)
        phis.append(phi)
        speeds.append(speed)
    dvg = g * math.sin(theta) * tb
    dvd = constant_drag_loss(drag, mdot, m0, mf) if drag != 0.0 else 0.0
    dve = 0.0
    v_bo = speeds[-1]
    return {
        "times": times,
        "radii": radii,
        "phis": phis,
        "speeds": speeds,
        "thetas": thetas,
        "V_bo": v_bo,
        "theta_bo": theta,
        "r_bo": radii[-1],
        "phi_bo": phis[-1],
        "dvg": dvg,
        "dvD": dvd,
        "dve": dve,
        "V_from_losses": burnout_speed_from_losses(c, m0, mf, dvg, dvd, dve),
        "horizontal": theta <= 0.0,
        "solver": "closed_form",
    }


def make_density_at(args: argparse.Namespace, radius_body: float, r_start: float):
    source = "none"
    density_at = None
    oat_meta: dict[str, object] = {}
    uses_cd = args.cd is not None
    frozen = args.rho is not None
    exponential = args.rho0 is not None or args.scale_height is not None
    oat = args.oat is not None
    if exponential and (args.rho0 is None or args.scale_height is None):
        raise ValueError("--rho0 and --scale-height must be given together")
    if frozen and exponential:
        raise ValueError("pass --rho or --rho0/--scale-height, not both")
    if oat and frozen:
        raise ValueError("pass --oat with geometric altitude, not with --rho")
    if oat and exponential:
        raise ValueError("pass --oat or --rho0/--scale-height, not both")
    if args.rh is not None and args.oat is None:
        raise ValueError("--rh requires --oat")

    if frozen:
        require_positive("density", args.rho)

        def density_at(z_m: float, rho=args.rho) -> float:
            return rho if z_m >= 0.0 else rho

        source = "frozen"
        return density_at, source, oat_meta

    if exponential:
        require_positive("surface density", args.rho0)
        require_positive("scale height", args.scale_height)

        def density_at(z_m: float, rho0=args.rho0, scale=args.scale_height) -> float:
            if z_m < 0.0:
                z_m = 0.0
            return rho0 * math.exp(-z_m / scale)

        source = "exponential"
        return density_at, source, oat_meta

    earthlike = math.isclose(radius_body, R_EARTH, rel_tol=1e-6, abs_tol=1.0)
    want_1976 = uses_cd or oat or args.alt is not None or earthlike
    if not want_1976:
        return None, source, oat_meta

    atmosphere, require_altitude, _layers, _r0, _hmax, _geo = load_atmosphere()
    z_ground = r_start - radius_body
    if z_ground < 0.0:
        z_ground = 0.0
    if z_ground > Z_MAX_1976:
        raise ValueError("start geometric altitude is above the 1976 hydrostatic top")
    require_altitude(z_ground, "--alt")
    humid = None
    t_offset = None
    if oat:
        require_positive("outside air temperature", args.oat)
        if args.rh is not None:
            if not math.isfinite(args.rh) or args.rh < 0.0 or args.rh > 1.0:
                raise ValueError("relative humidity must be finite and between 0 and 1")
        humid = load_humidity()
        ground = atmosphere(z_ground)
        t_offset = args.oat - ground["T"]
        source = "oat"
        oat_meta = {
            "T_ground_K": args.oat,
            "dT_K": t_offset,
            "rh": 0.0 if args.rh is None else args.rh,
            "rh_source": "flag" if args.rh is not None else "dry",
        }
    else:
        source = "1976"

    def density_at(
        z_m: float,
        atmosphere=atmosphere,
        require_altitude=require_altitude,
        t_offset=t_offset,
        rh=args.rh,
        humid=humid,
    ) -> float:
        if z_m < 0.0:
            z_m = 0.0
        if z_m > Z_MAX_1976:
            return 0.0
        state = atmosphere(require_altitude(z_m, "altitude"))
        if t_offset is None or humid is None:
            return state["rho"]
        temperature = state["T"] + t_offset
        if not math.isfinite(temperature) or temperature <= 0.0:
            raise ValueError("offset temperature is not positive")
        return parcel_from_oat(state["p"], temperature, rh, humid)

    return density_at, source, oat_meta


def layer_geometric_edges(layers, r0: float, h_max: float) -> list[tuple[float, float, int]]:
    edges: list[tuple[float, float, int]] = []
    heights = [row[0] for row in layers] + [h_max]
    for index in range(len(heights) - 1):
        h0 = heights[index]
        h1 = heights[index + 1]
        z0 = r0 * h0 / (r0 - h0) if h0 < r0 else Z_MAX_1976
        z1 = r0 * h1 / (r0 - h1) if h1 < r0 else Z_MAX_1976
        edges.append((z0, z1, index))
    return edges


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm
        from matplotlib.cm import ScalarMappable
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the trajectory") from exc
    return plt, LogNorm, ScalarMappable


def plot_trajectory(
    path: Path,
    *,
    radii: list[float],
    phis: list[float],
    radius_body: float,
    density_at,
    density_source: str,
) -> None:
    plt, log_norm, scalar_mappable = ensure_matplotlib()
    downrange = [radius_body * phi for phi in phis]
    altitude = [radius - radius_body for radius in radii]
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    z_top = max(max(altitude), 1000.0)
    x_max = max(max(downrange), 1.0)
    if density_at is not None:
        n_z = 240
        z_vals = [z_top * i / (n_z - 1) for i in range(n_z)]
        rhos = [max(density_at(z_m), 1e-16) for z_m in z_vals]
        grid = [rhos for _ in range(2)]
        try:
            import numpy as np

            zz = np.array(z_vals)
            xx = np.array([0.0, x_max])
            gg = np.array(grid).T
            norm = log_norm(vmin=min(rhos), vmax=max(rhos))
            mesh = ax.pcolormesh(
                xx,
                zz,
                gg,
                shading="auto",
                cmap="YlGnBu",
                norm=norm,
                zorder=0,
            )
            fig.colorbar(mesh, ax=ax, label="density (kg/m$^3$)")
        except ImportError:
            colors = plt.cm.YlGnBu
            lo = math.log(min(rhos))
            hi = math.log(max(rhos))
            span = hi - lo if hi > lo else 1.0
            for i in range(len(z_vals) - 1):
                frac = (math.log(rhos[i]) - lo) / span
                ax.axhspan(
                    z_vals[i],
                    z_vals[i + 1],
                    color=colors(frac),
                    zorder=0,
                    linewidth=0,
                )
            mappable = scalar_mappable(
                cmap=colors, norm=log_norm(vmin=min(rhos), vmax=max(rhos))
            )
            mappable.set_array([])
            fig.colorbar(mappable, ax=ax, label="density (kg/m$^3$)")
        if density_source in {"1976", "oat"}:
            atmosphere, _req, layers, r0, h_max, _geo = load_atmosphere()
            del atmosphere
            for z0, z1, index in layer_geometric_edges(layers, r0, h_max):
                if z0 > z_top:
                    continue
                ax.axhline(z0, color="#34495e", linewidth=0.4, alpha=0.45, zorder=1)
                if z0 < z_top:
                    ax.text(
                        x_max * 0.01,
                        min(0.5 * (z0 + min(z1, z_top)), z_top),
                        f"L{index}",
                        fontsize=7,
                        color="#2c3e50",
                        alpha=0.7,
                        zorder=2,
                    )
    ax.plot(
        downrange,
        altitude,
        color="#1a1a1a",
        linewidth=2.0,
        zorder=3,
        label="trajectory",
    )
    ax.plot(downrange[0], altitude[0], "o", color="#1a5276", zorder=4, label="ignition")
    ax.plot(downrange[-1], altitude[-1], "s", color="#c0392b", zorder=4, label="burnout")
    ax.set_xlabel("downrange (m)")
    ax.set_ylabel("geometric altitude (m)")
    ax.set_title(PLOT_TITLE)
    ax.set_xlim(0.0, x_max * 1.02)
    ax.set_ylim(min(0.0, min(altitude)), z_top * 1.05 if z_top > 0.0 else 1.0)
    ax.grid(True, alpha=0.35, zorder=2)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def resolve_mass_time(args: argparse.Namespace) -> tuple[float, float, float, float, float]:
    require_positive("ignition mass", args.m0)
    if args.mf is not None and args.mp is not None:
        raise ValueError("pass --mf or --mp, not both")
    if args.mf is None and args.mp is None:
        raise ValueError("burnout mass --mf or propellant mass --mp is required")
    if args.mf is not None:
        require_positive("burnout mass", args.mf)
        if args.mf >= args.m0:
            raise ValueError("burnout mass must be less than ignition mass")
        mp = args.m0 - args.mf
        mf = args.mf
    else:
        require_positive("propellant mass", args.mp)
        if args.mp >= args.m0:
            raise ValueError("propellant mass must be less than ignition mass")
        mp = args.mp
        mf = args.m0 - mp
    if args.tb is None and args.mdot is None:
        raise ValueError("burn time --tb or mass flow --mdot is required")
    if args.tb is not None:
        require_positive("burn time", args.tb)
    if args.mdot is not None:
        require_positive("mass flow", args.mdot)
    if args.tb is not None and args.mdot is not None:
        expected = args.mdot * args.tb
        if abs(expected - mp) > 1e-6 * max(mp, expected):
            raise ValueError(
                "mass flow times burn time must equal propellant mass "
                f"({expected:.8g} kg vs {mp:.8g} kg)"
            )
        tb = args.tb
        mdot = args.mdot
    elif args.tb is not None:
        tb = args.tb
        mdot = mp / tb
    else:
        mdot = args.mdot
        tb = mp / mdot
    return args.m0, mf, mp, tb, mdot


def resolve_body(args: argparse.Namespace) -> tuple[float, float, float, float]:
    radius = R_EARTH if args.radius is None else args.radius
    require_positive("body radius", radius)
    if args.r is not None and args.alt is not None:
        raise ValueError("pass --r or --alt, not both")
    if args.alt is not None:
        require_nonneg("geometric altitude", args.alt)
        r_start = radius + args.alt
    elif args.r is not None:
        require_positive("start radius", args.r)
        if args.r < radius:
            raise ValueError("start radius is inside the body")
        r_start = args.r
    else:
        r_start = radius
    if args.mu is not None and args.g0 is not None:
        raise ValueError("pass --mu or --g0, not both")
    if args.mu is not None:
        require_positive("gravitational parameter", args.mu)
        mu = args.mu
        g_surface = mu / (radius * radius)
    elif args.g0 is not None:
        require_positive("surface gravity", args.g0)
        g_surface = args.g0
        mu = gravitational_parameter_surface(g_surface, radius)
    else:
        g_surface = G0_STD
        mu = gravitational_parameter_surface(g_surface, radius)
    return radius, r_start, mu, g_surface


def resolve_method(args: argparse.Namespace) -> tuple[str, float]:
    if args.gamma is not None and args.kick is not None:
        raise ValueError("pass --gamma or --kick, not both")
    if args.gamma is None and args.kick is None:
        raise ValueError("constant-angle --gamma or gravity-turn --kick is required")
    if args.gamma is not None:
        if not math.isfinite(args.gamma) or args.gamma < 0.0 or args.gamma > math.pi / 2.0:
            raise ValueError("flight-path angle must be from 0 to pi/2 rad")
        return "constant_angle", args.gamma
    require_nonneg("kick angle", args.kick)
    if args.kick > math.pi / 2.0:
        raise ValueError("kick angle must be from 0 to pi/2 rad")
    return "gravity_turn", kick_flight_path_angle(args.kick)


def resolve_drag(args: argparse.Namespace) -> tuple[str, float | None, float | None, float | None]:
    if args.drag is not None and args.cd is not None:
        raise ValueError("pass --drag or --cd, not both")
    if args.drag is not None:
        require_nonneg("constant drag force", args.drag)
        return "constant_force", args.drag, None, None
    if args.cd is not None:
        require_positive("drag coefficient", args.cd)
        if args.area is None:
            raise ValueError("--cd requires reference area --area")
        require_positive("reference area", args.area)
        kind = "frozen_cd" if args.rho is not None else "atmospheric_cd"
        return kind, None, args.cd, args.area
    if args.area is not None:
        raise ValueError("--area requires --cd")
    return "none", None, None, None


def run(args: argparse.Namespace) -> int:
    require_positive("specific impulse", args.isp)
    m0, mf, mp, tb, mdot = resolve_mass_time(args)
    radius_body, r_start, mu, g_surface = resolve_body(args)
    method, theta0 = resolve_method(args)
    drag_kind, drag_value, cd, area = resolve_drag(args)
    c = args.isp * G0_STD
    thrust = mdot * c
    density_at, density_source, oat_meta = make_density_at(args, radius_body, r_start)
    if drag_kind == "atmospheric_cd" and density_at is None:
        raise ValueError(
            "atmospheric drag needs 1976 altitude, --oat, --rho, or "
            "--rho0 and --scale-height"
        )
    g_ign = gravity_at_radius(mu, r_start)
    closed = (
        method == "constant_angle"
        and drag_kind in {"none", "constant_force"}
    )
    if closed:
        result = closed_constant_angle(
            m0=m0,
            mf=mf,
            mdot=mdot,
            tb=tb,
            c=c,
            g=g_ign,
            r_start=r_start,
            radius_body=radius_body,
            theta=theta0,
            drag=0.0 if drag_value is None else drag_value,
        )
    else:
        result = integrate_ode(
            m0=m0,
            mf=mf,
            mdot=mdot,
            tb=tb,
            thrust=thrust,
            mu=mu,
            radius_body=radius_body,
            r_start=r_start,
            theta0=theta0,
            hold_theta=method == "constant_angle",
            drag_value=drag_value,
            cd=cd,
            area=area,
            density_at=density_at,
        )
    notes: list[str] = []
    if result["V_bo"] <= 0.0:
        notes.append("burnout speed is not positive")
    if result["horizontal"]:
        notes.append("the flight path reached the local horizontal before burnout")
    if result["r_bo"] <= radius_body + 1e-6:
        notes.append("the vehicle is still on the surface at burnout")
    if thrust <= m0 * g_ign:
        notes.append("ignition thrust is not greater than local weight")
    z_bo = result["r_bo"] - radius_body
    z_start = r_start - radius_body
    out_path = (
        Path(args.out)
        if args.out
        else SKILL_DIR / "basic_trajectory_losses_from_body_surface.png"
    )
    out_path = out_path.resolve()
    plot_trajectory(
        out_path,
        radii=result["radii"],
        phis=result["phis"],
        radius_body=radius_body,
        density_at=density_at,
        density_source=density_source,
    )
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("method", method)
    print_kv("solver", result["solver"])
    print_kv("m0_kg", m0)
    print_kv("mf_kg", mf)
    print_kv("mp_kg", mp)
    print_kv("tb_s", tb)
    print_kv("mdot_kg_s", mdot)
    print_kv("Isp_s", args.isp)
    print_kv("c_m_s", c)
    print_kv("thrust_N", thrust)
    print_kv("R_m", radius_body)
    print_kv("r_ign_m", r_start)
    print_kv("Z_ign_m", z_start)
    print_kv("mu_m3_s2", mu)
    print_kv("g_surface_m_s2", g_surface)
    print_kv("g_ign_m_s2", g_ign)
    if method == "constant_angle":
        print_kv("gamma_rad", theta0)
    else:
        print_kv("kick_rad", args.kick)
        print_kv("gamma_ign_rad", theta0)
    print_kv("drag_kind", drag_kind)
    if drag_value is not None:
        print_kv("D_N", drag_value)
    if cd is not None:
        print_kv("CD", cd)
        print_kv("area_m2", area)
    print_kv("density_source", density_source)
    for key, value in oat_meta.items():
        print_kv(key, value)
    if args.rho is not None:
        print_kv("rho_kg_m3", args.rho)
    if args.rho0 is not None:
        print_kv("rho0_kg_m3", args.rho0)
        print_kv("scale_height_m", args.scale_height)
    print_kv("dv_ideal_m_s", delta_v_vacuum(c, m0, mf))
    print_kv("gravity_loss_m_s", result["dvg"])
    print_kv("drag_loss_m_s", result["dvD"])
    print_kv("steering_loss_m_s", result["dve"])
    print_kv("V_bo_m_s", result["V_bo"])
    print_kv("V_from_losses_m_s", result["V_from_losses"])
    print_kv("gamma_bo_rad", result["theta_bo"])
    print_kv("r_bo_m", result["r_bo"])
    print_kv("Z_bo_m", z_bo)
    print_kv("phi_bo_rad", result["phi_bo"])
    print_kv("downrange_m", radius_body * result["phi_bo"])
    print_kv("graph", str(out_path))
    if notes:
        print_kv("warning", "; ".join(notes))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str, tol: float = CHECK_TOL) -> int | None:
    if abs(got - want) > tol * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def capture(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    c = 3000.0
    isp = c / G0_STD
    m0 = math.e
    mf = 1.0
    if near(delta_v_vacuum(c, m0, mf), c, "delta_v_vacuum"):
        return 1
    mu = gravitational_parameter_surface(10.0, 3.0)
    if near(mu, 90.0, "gravitational_parameter_surface"):
        return 1
    th = math.pi / 2.0
    if near(constant_angle_speed(c, m0, mf, 10.0, 20.0, th), 2800.0, "constant_angle_speed"):
        return 1
    if near(constant_drag_loss(50.0, 2.0, m0, mf), 25.0, "constant_drag_loss"):
        return 1
    if near(
        kick_flight_path_angle(math.pi / 18.0),
        4.0 * math.pi / 9.0,
        "kick_flight_path_angle",
    ):
        return 1
    path = constant_angle_path_length(1.0, 2.0, 1.0, 1.0, 0.0, 1.0, th)
    if near(path, 1.0 - math.log(2.0), "constant_angle_path_length"):
        return 1

    # Closed form vs ODE on a huge planet so g and the horizon are frozen.
    radius = 1e12
    g0 = 10.0
    m0c = 2.0
    mfc = 1.0
    tb = 1.0
    c_check = 50.0
    ispc = c_check / G0_STD
    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "check.png")
        code, text, err = capture(
            [
                "--m0",
                str(m0c),
                "--mf",
                str(mfc),
                "--isp",
                str(ispc),
                "--tb",
                str(tb),
                "--gamma",
                str(th),
                "--radius",
                str(radius),
                "--g0",
                str(g0),
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"vertical closed main returned {code}: {err}")
        if "method: constant_angle" not in text or "solver: closed_form" not in text:
            return fail("vertical closed run did not print the closed solver")
        want = constant_angle_speed(c_check, m0c, mfc, g0, tb, th)
        got = None
        for line in text.splitlines():
            if line.startswith("V_bo_m_s:"):
                got = float(line.split(":", 1)[1])
        if got is None:
            return fail("vertical closed run omitted V_bo_m_s")
        if near(got, want, "closed vertical V_bo"):
            return 1

        code, text, err = capture(
            [
                "--m0",
                str(m0c),
                "--mp",
                str(m0c - mfc),
                "--isp",
                str(ispc),
                "--mdot",
                str((m0c - mfc) / tb),
                "--kick",
                "0",
                "--radius",
                str(radius),
                "--g0",
                str(g0),
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"vertical gravity-turn main returned {code}: {err}")
        if "method: gravity_turn" not in text or "solver: ode" not in text:
            return fail("gravity-turn run did not print the ODE solver")
        got_g = None
        got_gamma = None
        for line in text.splitlines():
            if line.startswith("V_bo_m_s:"):
                got_g = float(line.split(":", 1)[1])
            if line.startswith("gamma_bo_rad:"):
                got_gamma = float(line.split(":", 1)[1])
        if got_g is None or got_gamma is None:
            return fail("gravity-turn run omitted burnout speed or angle")
        if near(got_g, want, "ode vertical V_bo", tol=2e-3):
            return 1
        if abs(got_gamma - th) > 0.02:
            return fail(f"zero-kick burnout angle {got_gamma}, expected vertical")

        code, text, err = capture(
            [
                "--m0",
                "10000",
                "--mp",
                "6000",
                "--isp",
                "300",
                "--tb",
                "80",
                "--kick",
                "0.05",
                "--alt",
                "0",
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"Earth gravity-turn returned {code}: {err}")
        gamma_bo = None
        gamma_ign = None
        z_bo = None
        for line in text.splitlines():
            if line.startswith("gamma_bo_rad:"):
                gamma_bo = float(line.split(":", 1)[1])
            if line.startswith("gamma_ign_rad:"):
                gamma_ign = float(line.split(":", 1)[1])
            if line.startswith("Z_bo_m:"):
                z_bo = float(line.split(":", 1)[1])
        if gamma_bo is None or gamma_ign is None:
            return fail("Earth gravity-turn omitted path angles")
        if not gamma_bo < gamma_ign:
            return fail("gravity turn did not reduce the flight-path angle")
        if z_bo is None or z_bo <= 0.0:
            return fail("Earth gravity-turn did not leave the surface")

        code, text, err = capture(
            [
                "--m0",
                str(m0c),
                "--mf",
                str(mfc),
                "--isp",
                str(ispc),
                "--tb",
                str(tb),
                "--gamma",
                str(th),
                "--drag",
                "0.2",
                "--radius",
                str(radius),
                "--g0",
                str(g0),
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"constant-drag run returned {code}: {err}")
        want_d = constant_angle_speed_const_drag(
            c_check, m0c, mfc, g0, tb, th, 0.2, 1.0
        )
        got_d = None
        loss_d = None
        for line in text.splitlines():
            if line.startswith("V_bo_m_s:"):
                got_d = float(line.split(":", 1)[1])
            if line.startswith("drag_loss_m_s:"):
                loss_d = float(line.split(":", 1)[1])
        if got_d is None or loss_d is None:
            return fail("constant-drag run omitted speed or drag loss")
        if near(got_d, want_d, "constant-drag V_bo"):
            return 1
        if near(loss_d, constant_drag_loss(0.2, 1.0, m0c, mfc), "printed drag loss"):
            return 1

        # Quadratic drag cannot use the frozen-g closed form. The ODE must
        # still hold the flight-path angle, and burnout speed must match an
        # independent along-track integration.
        theta_hold = math.pi / 6.0
        c_hold = 500.0
        isp_hold = c_hold / G0_STD
        m0_hold = 2.0
        mf_hold = 1.0
        tb_hold = 4.0
        mdot_hold = (m0_hold - mf_hold) / tb_hold
        cd_hold = 0.2
        area_hold = 0.001
        rho_hold = 1.0
        code, text, err = capture(
            [
                "--m0",
                str(m0_hold),
                "--mf",
                str(mf_hold),
                "--isp",
                str(isp_hold),
                "--tb",
                str(tb_hold),
                "--gamma",
                str(theta_hold),
                "--cd",
                str(cd_hold),
                "--area",
                str(area_hold),
                "--rho",
                str(rho_hold),
                "--radius",
                str(radius),
                "--g0",
                str(g0),
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"held-angle quadratic-drag run returned {code}: {err}")
        if "solver: ode" not in text:
            return fail("quadratic drag on a constant angle did not use the ODE")
        got_hold = None
        got_angle = None
        got_from_losses = None
        for line in text.splitlines():
            if line.startswith("V_bo_m_s:"):
                got_hold = float(line.split(":", 1)[1])
            if line.startswith("gamma_bo_rad:"):
                got_angle = float(line.split(":", 1)[1])
            if line.startswith("V_from_losses_m_s:"):
                got_from_losses = float(line.split(":", 1)[1])
        if got_hold is None or got_angle is None or got_from_losses is None:
            return fail("held-angle run omitted speed or flight-path angle")
        if abs(got_angle - theta_hold) > 1e-6:
            return fail(
                f"constant-angle burnout gamma {got_angle}, expected {theta_hold}"
            )
        v_ref = 0.0
        t_ref = 0.0
        n_ref = 40000
        dt_ref = tb_hold / n_ref
        sin_hold = math.sin(theta_hold)
        for _ in range(n_ref):
            mass_ref = m0_hold - mdot_hold * (t_ref + 0.5 * dt_ref)
            drag_ref = cd_hold * 0.5 * rho_hold * v_ref * v_ref * area_hold
            d_speed = c_hold * mdot_hold / mass_ref - drag_ref / mass_ref - g0 * sin_hold
            v_ref += d_speed * dt_ref
            t_ref += dt_ref
        if abs(got_hold - v_ref) > 1e-3 * max(1.0, abs(v_ref)):
            return fail(
                f"held-angle V_bo {got_hold} disagrees with along-track "
                f"integration {v_ref}"
            )
        if abs(got_hold - got_from_losses) > 1e-3 * max(1.0, abs(got_hold)):
            return fail(
                f"held-angle V_bo {got_hold} disagrees with loss accounting "
                f"{got_from_losses}"
            )

        code, _text, err = capture(
            [
                "--m0",
                "2",
                "--mf",
                "1",
                "--isp",
                str(ispc),
                "--tb",
                "1",
                "--gamma",
                "1",
                "--kick",
                "0.1",
                "--out",
                png,
            ]
        )
        if code != 2 or "not both" not in err:
            return fail("both --gamma and --kick were accepted")
        code, _text, err = capture(
            ["--m0", "2", "--isp", str(ispc), "--tb", "1", "--gamma", "1.0"]
        )
        if code != 2:
            return fail("missing burnout mass was accepted")

    print("check: pass")
    print_kv("delta_v_vacuum_m_s", c)
    print_kv("constant_angle_speed_m_s", 2800.0)
    print_kv("kick_flight_path_rad", 4.0 * math.pi / 9.0)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gravity, drag, and steering losses of a simplified powered "
            "ascent from a spherical body."
        )
    )
    parser.add_argument("--m0", type=float, default=None, help="ignition mass m0 [kg]")
    parser.add_argument("--mf", type=float, default=None, help="burnout mass mf [kg]")
    parser.add_argument("--mp", type=float, default=None, help="propellant mass mp [kg]")
    parser.add_argument("--isp", type=float, default=None, help="vacuum specific impulse Isp [s]")
    parser.add_argument("--tb", type=float, default=None, help="burn time tb [s]")
    parser.add_argument("--mdot", type=float, default=None, help="propellant mass flow [kg/s]")
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help="constant flight-path angle above the local horizontal [rad]",
    )
    parser.add_argument(
        "--kick",
        type=float,
        default=None,
        help="gravity-turn kick from local vertical [rad]",
    )
    parser.add_argument("--radius", type=float, default=None, help="spherical body radius R [m]")
    parser.add_argument("--r", type=float, default=None, help="ignition radius r [m]")
    parser.add_argument("--alt", type=float, default=None, help="geometric ignition altitude Z [m]")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter mu [m^3/s^2]")
    parser.add_argument(
        "--g0",
        type=float,
        default=None,
        help="surface gravity at radius R [m/s^2]",
    )
    parser.add_argument("--cd", type=float, default=None, help="drag coefficient CD")
    parser.add_argument("--area", type=float, default=None, help="drag reference area S [m^2]")
    parser.add_argument("--drag", type=float, default=None, help="constant drag force D [N]")
    parser.add_argument(
        "--rho",
        type=float,
        default=None,
        help="density with no atmospheric variation [kg/m^3]",
    )
    parser.add_argument("--oat", type=float, default=None, help="outside air temperature at ignition [K]")
    parser.add_argument("--rh", type=float, default=None, help="relative humidity at ignition, 0 to 1")
    parser.add_argument("--rho0", type=float, default=None, help="non-Earth surface density [kg/m^3]")
    parser.add_argument(
        "--scale-height",
        type=float,
        default=None,
        help="non-Earth exponential scale height H [m]",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path for the trajectory")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        if args.m0 is None or args.isp is None:
            raise ValueError("ignition mass --m0 and specific impulse --isp are required")
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
