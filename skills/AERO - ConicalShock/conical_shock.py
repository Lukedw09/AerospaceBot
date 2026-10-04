#!/usr/bin/env python3
"""Attached conical shock on a right circular cone at zero incidence.

Shock-layer velocities follow NASA SP-3004 Taylor-Maccoll, with polar
components from NACA TN 3485. The conical shock jump is the oblique-shock
state at the wave angle. Surface pressure coefficient uses
pressure_coefficient_from_mach after an isentropic compression from the
state immediately behind the shock.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "AERO - ConicalShock"
DEFAULT_GAMMA = 1.4
MACH_MAX = 1.0e6
DETACH_TOL = 1.0e-8
ROOT_SPLIT = 1.0e-8
RK_STEPS = 800
CHECK_TOL = 1e-9

ASSUMPTIONS = (
    "calorically perfect gas; steady axisymmetric conical flow at zero "
    "incidence; attached conical shock of uniform strength; velocities in "
    "the shock layer are divided by the vacuum limiting speed; "
    "v = du/dtheta from conical_ray_normal_speed; "
    "a**2 = ((gamma-1)/2)*(1-u**2-v**2) from conical_vacuum_sound_speed_sq; "
    "d2u/dtheta**2 from taylor_maccoll_radial_acceleration; "
    "the shock jump is the oblique-shock state at wave angle theta, with "
    "polar components from conical_radial_speed and conical_normal_speed; "
    "surface v = 0; surface Mach from conical_resultant_mach; "
    "surface Cp from pressure_coefficient_from_mach after an isentropic "
    "compression from the post-shock Mach; the isolated cone takes the "
    "weaker attached shock; this is a circular cone, not a two-dimensional "
    "wedge; boundary layer, yaw, and shock curvature beyond the cone are "
    "not modeled"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def mach_angle(mach: float) -> float:
    """mach_angle in formulas.md. Mach is at least 1."""
    return math.asin(1.0 / mach)


def limiting_speed_ratio(mach: float, gamma: float) -> float:
    """limiting_speed_ratio in formulas.md."""
    gm = 0.5 * (gamma - 1.0) * mach * mach
    return math.sqrt(gm / (1.0 + gm))


def vacuum_sound_speed_sq(gamma: float, u: float, v: float) -> float:
    """conical_vacuum_sound_speed_sq in formulas.md."""
    return 0.5 * (gamma - 1.0) * (1.0 - u * u - v * v)


def taylor_maccoll_radial_acceleration(
    gamma: float, u: float, v: float, theta: float
) -> float:
    """taylor_maccoll_radial_acceleration in formulas.md."""
    sound = vacuum_sound_speed_sq(gamma, u, v)
    denom = v * v - sound
    if abs(denom) < 1e-18 or abs(math.sin(theta)) < 1e-18:
        raise ValueError("Taylor-Maccoll denominator vanished")
    cot = math.cos(theta) / math.sin(theta)
    return sound * (u + v * cot) / denom - u


def resultant_mach(gamma: float, u: float, v: float) -> float:
    """conical_resultant_mach in formulas.md."""
    sound = vacuum_sound_speed_sq(gamma, u, v)
    if sound <= 0.0:
        raise ValueError("local sound speed is not positive")
    return math.sqrt((u * u + v * v) / sound)


def critical_mach(gamma: float, u: float, v: float) -> float:
    """conical_critical_mach in formulas.md."""
    return math.sqrt(((gamma + 1.0) / (gamma - 1.0)) * (u * u + v * v))


def freestream_mach_sq(gamma: float, u: float, theta: float) -> float:
    """conical_freestream_mach_sq in formulas.md."""
    denom = math.cos(theta) ** 2 - u * u
    if denom <= 0.0:
        raise ValueError("shock-ray radial speed does not give a finite Mach")
    return (2.0 / (gamma - 1.0)) * u * u / denom


def shock_wave_tangent(gamma: float, u: float, v: float) -> float:
    """conical_shock_wave_tangent in formulas.md."""
    return ((gamma - 1.0) / (gamma + 1.0)) * (u * u - 1.0) / (u * v)


def polar_from_cylindrical(
    vx: float, vr: float, theta: float
) -> tuple[float, float]:
    """conical_radial_speed and conical_normal_speed in formulas.md."""
    cosine = math.cos(theta)
    sine = math.sin(theta)
    return vx * cosine + vr * sine, -vx * sine + vr * cosine


def deflection_angle(theta: float, mach: float, gamma: float) -> float:
    """Flow deflection from oblique_shock_deflection. Radians."""
    if theta <= 0.0 or theta >= math.pi / 2.0:
        return 0.0
    mn2 = (mach * math.sin(theta)) ** 2
    if mn2 <= 1.0:
        return 0.0
    cot = math.cos(theta) / math.sin(theta)
    numer = 2.0 * cot * (mn2 - 1.0)
    denom = 2.0 + mach * mach * (gamma + math.cos(2.0 * theta))
    return math.atan(numer / denom)


def shock_downstream(
    mach: float, gamma: float, theta: float, delta: float
) -> dict[str, float]:
    """State behind a straight oblique shock at wave angle theta."""
    mn2 = (mach * math.sin(theta)) ** 2
    if mn2 < 1.0 - 1e-12:
        raise ValueError("normal Mach ahead of the shock is below 1")
    pressure = (2.0 * gamma * mn2 - (gamma - 1.0)) / (gamma + 1.0)
    mn2_down = ((gamma - 1.0) * mn2 + 2.0) / (2.0 * gamma * mn2 - (gamma - 1.0))
    sine = math.sin(theta - delta)
    if sine <= 0.0 or mn2_down <= 0.0:
        raise ValueError("downstream Mach is not defined for this wave")
    m2 = math.sqrt(mn2_down) / sine
    if not math.isfinite(pressure) or not math.isfinite(m2) or pressure <= 0.0 or m2 <= 0.0:
        raise ValueError("downstream shock state is not finite")
    return {
        "Mn1": math.sqrt(mn2),
        "M2": m2,
        "p_ratio": pressure,
    }


def isentropic_pressure_ratio(mach_1: float, mach_2: float, gamma: float) -> float:
    """p2/p1 from stagnation_pressure at constant total pressure."""

    def total_over_static(mach: float) -> float:
        return (1.0 + 0.5 * (gamma - 1.0) * mach * mach) ** (gamma / (gamma - 1.0))

    return total_over_static(mach_1) / total_over_static(mach_2)


def pressure_coefficient_from_mach(
    pressure_ratio: float, mach: float, gamma: float
) -> float:
    """pressure_coefficient_from_mach in formulas.md."""
    return 2.0 * (pressure_ratio - 1.0) / (gamma * mach * mach)


def post_shock_polar(
    mach: float, gamma: float, theta: float
) -> tuple[float, float, float, dict[str, float]]:
    """Polar speeds immediately behind the conical shock."""
    delta = deflection_angle(theta, mach, gamma)
    down = shock_downstream(mach, gamma, theta, delta)
    speed = limiting_speed_ratio(down["M2"], gamma)
    vx = speed * math.cos(delta)
    vr = speed * math.sin(delta)
    radial, normal = polar_from_cylindrical(vx, vr, theta)
    return radial, normal, delta, down


def _rk4_step(
    theta: float, u: float, v: float, step: float, gamma: float
) -> tuple[float, float, float]:
    def pair(angle: float, radial: float, normal: float) -> tuple[float, float]:
        acc = taylor_maccoll_radial_acceleration(gamma, radial, normal, angle)
        return normal, acc

    k1u, k1v = pair(theta, u, v)
    k2u, k2v = pair(theta + 0.5 * step, u + 0.5 * step * k1u, v + 0.5 * step * k1v)
    k3u, k3v = pair(theta + 0.5 * step, u + 0.5 * step * k2u, v + 0.5 * step * k2v)
    k4u, k4v = pair(theta + step, u + step * k3u, v + step * k3v)
    u_new = u + step * (k1u + 2.0 * k2u + 2.0 * k3u + k4u) / 6.0
    v_new = v + step * (k1v + 2.0 * k2v + 2.0 * k3v + k4v) / 6.0
    return theta + step, u_new, v_new


def integrate_to_surface(
    gamma: float, theta_shock: float, u_shock: float, v_shock: float
) -> tuple[float, float]:
    """Integrate Taylor-Maccoll from the shock inward until v = 0."""
    theta = theta_shock
    u = u_shock
    v = v_shock
    if v >= 0.0:
        return theta, u
    floor = 1.0e-4
    step = -(theta - floor) / RK_STEPS
    if step >= 0.0:
        raise ValueError("shock angle is inside the cone")
    for _ in range(RK_STEPS * 4):
        if theta + step <= floor:
            step = 0.5 * (floor - theta)
            if abs(step) < 1e-16:
                break
        try:
            theta_next, u_next, v_next = _rk4_step(theta, u, v, step, gamma)
        except ValueError:
            step *= 0.5
            if abs(step) < 1e-12:
                raise
            continue
        if not math.isfinite(u_next) or not math.isfinite(v_next):
            step *= 0.5
            if abs(step) < 1e-12:
                raise ValueError("Taylor-Maccoll integration left the real line")
            continue
        if v_next >= 0.0:
            frac = v / (v - v_next) if v_next != v else 1.0
            frac = min(max(frac, 0.0), 1.0)
            return theta + frac * (theta_next - theta), u + frac * (u_next - u)
        theta, u, v = theta_next, u_next, v_next
        if abs(step) < abs(-(theta - floor) / RK_STEPS):
            step = -(theta - floor) / RK_STEPS
    raise ValueError("surface condition v = 0 was not reached")


def integrate_to_shock(
    gamma: float, theta_cone: float, u_surface: float
) -> tuple[float, float, float]:
    """Integrate from the cone surface outward until the SP-3004 shock condition."""
    theta = theta_cone
    u = u_surface
    v = 0.0
    ceiling = math.pi / 2.0 - 1e-6
    step = (ceiling - theta) / RK_STEPS
    previous = None
    for _ in range(RK_STEPS * 4):
        if theta + step >= ceiling:
            step = 0.5 * (ceiling - theta)
            if step <= 0.0:
                break
        theta_next, u_next, v_next = _rk4_step(theta, u, v, step, gamma)
        residual = math.tan(theta_next) - shock_wave_tangent(gamma, u_next, v_next)
        if previous is not None:
            _theta_prev, _u_prev, _v_prev, residual_prev = previous
            if residual_prev == 0.0 or residual_prev * residual <= 0.0:
                if residual == residual_prev:
                    return theta_next, u_next, v_next
                frac = residual_prev / (residual_prev - residual)
                frac = min(max(frac, 0.0), 1.0)
                return (
                    _theta_prev + frac * (theta_next - _theta_prev),
                    _u_prev + frac * (u_next - _u_prev),
                    _v_prev + frac * (v_next - _v_prev),
                )
        previous = (theta_next, u_next, v_next, residual)
        theta, u, v = theta_next, u_next, v_next
    raise ValueError("Rankine-Hugoniot shock condition was not reached")


def cone_from_shock(mach: float, gamma: float, theta: float) -> dict[str, float]:
    """Cone half-angle produced by an attached shock at wave angle theta."""
    u, v, delta, down = post_shock_polar(mach, gamma, theta)
    cone, u_s = integrate_to_surface(gamma, theta, u, v)
    return {
        "theta": theta,
        "delta_shock": delta,
        "cone": cone,
        "u_s": u_s,
        "M2": down["M2"],
        "p2_over_p1": down["p_ratio"],
        "Mn1": down["Mn1"],
        "Mc": resultant_mach(gamma, u_s, 0.0),
        "Mstar_s": critical_mach(gamma, u_s, 0.0),
    }


def maximum_cone_angle(mach: float, gamma: float) -> tuple[float, float]:
    """Shock angle and cone half-angle at the peak attached cone."""
    mu = mach_angle(mach)
    lo = mu + 1e-8
    hi = math.pi / 2.0 - 1e-6
    invphi = (math.sqrt(5.0) - 1.0) / 2.0
    left = hi - invphi * (hi - lo)
    right = lo + invphi * (hi - lo)

    def value(theta: float) -> float:
        try:
            return cone_from_shock(mach, gamma, theta)["cone"]
        except ValueError:
            return -1.0

    left_value = value(left)
    right_value = value(right)
    for _ in range(48):
        if left_value < right_value:
            lo = left
            left = right
            left_value = right_value
            right = lo + invphi * (hi - lo)
            right_value = value(right)
        else:
            hi = right
            right = left
            right_value = left_value
            left = hi - invphi * (hi - lo)
            left_value = value(left)
    theta = 0.5 * (lo + hi)
    try:
        peak = cone_from_shock(mach, gamma, theta)
    except ValueError as exc:
        raise ValueError("could not locate a maximum attached cone angle") from exc
    return peak["theta"], peak["cone"]


def _bisect_cone(
    lo: float,
    hi: float,
    target: float,
    mach: float,
    gamma: float,
) -> float:
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        try:
            cone = cone_from_shock(mach, gamma, mid)["cone"]
        except ValueError:
            hi = mid
            continue
        if cone < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def evaluate(mach: float, gamma: float, delta: float) -> dict:
    """Weak attached conical shock for cone half-angle delta."""
    mu = mach_angle(mach)
    theta_star, delta_max = maximum_cone_angle(mach, gamma)
    state: dict = {
        "mach": mach,
        "gamma": gamma,
        "delta": delta,
        "mu": mu,
        "delta_max": delta_max,
        "theta_at_max": theta_star,
        "attached": False,
        "shock": "detached",
        "theta": None,
        "Mn1": None,
        "M2": None,
        "p2_over_p1": None,
        "Mc": None,
        "Mstar_s": None,
        "pc_over_p1": None,
        "Cp": None,
        "theta_strong": None,
    }
    if delta <= 1e-15:
        speed = limiting_speed_ratio(mach, gamma)
        u = speed * math.cos(mu)
        state.update(
            attached=True,
            shock="mach-wave",
            theta=mu,
            Mn1=1.0,
            M2=mach,
            p2_over_p1=1.0,
            Mc=mach,
            Mstar_s=critical_mach(gamma, u, -speed * math.sin(mu)),
            pc_over_p1=1.0,
            Cp=0.0,
        )
        return state
    if delta > delta_max + DETACH_TOL:
        return state

    if delta >= delta_max - DETACH_TOL:
        theta = theta_star
        branch = "maximum-cone"
        theta_strong = None
    else:
        theta = _bisect_cone(mu + 1e-8, theta_star, delta, mach, gamma)
        theta_strong = _bisect_cone(
            theta_star, math.pi / 2.0 - 1e-6, delta, mach, gamma
        )
        if theta_strong - theta < ROOT_SPLIT:
            branch = "maximum-cone"
            theta_strong = None
        else:
            branch = "weak"
    field = cone_from_shock(mach, gamma, theta)
    surface_over_shock = isentropic_pressure_ratio(field["M2"], field["Mc"], gamma)
    pc_over_p1 = surface_over_shock * field["p2_over_p1"]
    state.update(
        attached=True,
        shock=branch,
        theta=field["theta"],
        Mn1=field["Mn1"],
        M2=field["M2"],
        p2_over_p1=field["p2_over_p1"],
        Mc=field["Mc"],
        Mstar_s=field["Mstar_s"],
        pc_over_p1=pc_over_p1,
        Cp=pressure_coefficient_from_mach(pc_over_p1, mach, gamma),
    )
    if theta_strong is not None:
        try:
            strong = cone_from_shock(mach, gamma, theta_strong)
        except ValueError:
            strong = None
        if strong is not None:
            state["theta_strong"] = strong["theta"]
    return state


def require_inputs(mach: float, gamma: float, delta: float) -> None:
    if not math.isfinite(mach) or mach <= 1.0 or mach > MACH_MAX:
        raise ValueError(f"--mach must be greater than 1 and at most {MACH_MAX:g}")
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("--gamma must be greater than 1")
    if not math.isfinite(delta) or delta < 0.0 or delta >= math.pi / 2.0:
        raise ValueError(
            "--delta must be a cone half-angle in radians from 0 up to pi/2 "
            "(convert degrees with pi/180)"
        )


def emit(state: dict, gamma_source: str, graph: str) -> None:
    delta = state["delta"]
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("gamma", state["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("M1", state["mach"])
    print_kv("delta_rad", delta)
    print_kv("delta_deg", math.degrees(delta))
    print_kv("mu1_rad", state["mu"])
    print_kv("mu1_deg", math.degrees(state["mu"]))
    print_kv("delta_max_rad", state["delta_max"])
    print_kv("delta_max_deg", math.degrees(state["delta_max"]))
    print_kv("attached", "yes" if state["attached"] else "no")
    print_kv("shock", state["shock"])
    if state["theta"] is not None:
        print_kv("theta_rad", state["theta"])
        print_kv("theta_deg", math.degrees(state["theta"]))
        print_kv("Mn1", state["Mn1"])
        print_kv("M2", state["M2"])
        print_kv("Mc", state["Mc"])
        print_kv("Mstar_s", state["Mstar_s"])
        print_kv("p2_over_p1", state["p2_over_p1"])
        print_kv("pc_over_p1", state["pc_over_p1"])
        print_kv("Cp", state["Cp"])
    if state["theta_strong"] is not None:
        print_kv("theta_strong_rad", state["theta_strong"])
        print_kv("theta_strong_deg", math.degrees(state["theta_strong"]))
    print_kv("graph", graph)


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def _angles(start: float, stop: float, steps: int = 32) -> list[float]:
    if steps < 1:
        return [start, stop]
    return [start + (stop - start) * i / steps for i in range(steps + 1)]


def _panel_frame(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d5d8dc")


def _flow_arrows(ax, x0: float, x1: float, ys: list[float]) -> None:
    for y_pos in ys:
        ax.annotate(
            "",
            xy=(x1, y_pos),
            xytext=(x0, y_pos),
            arrowprops={"arrowstyle": "-|>", "color": "#1a5276", "lw": 1.3},
        )


def _draw_meridian(ax, state: dict) -> None:
    delta = state["delta"]
    x_min, x_max, y_min, y_max = -0.35, 1.55, -1.25, 1.25
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    _panel_frame(ax)
    _flow_arrows(ax, -0.28, 0.12, [0.42, 0.78, 1.08])
    ax.text(-0.26, 0.12, r"$M_\infty$", color="#1a5276", fontsize=11)
    ax.plot([-0.2, 1.5], [0.0, 0.0], color="#aab7b8", lw=0.7, ls="--", zorder=1)

    length = 1.25
    if delta > 1e-8:
        upper = (length * math.cos(delta), length * math.sin(delta))
        lower = (upper[0], -upper[1])
        ax.fill(
            [0.0, upper[0], lower[0]],
            [0.0, upper[1], lower[1]],
            color="#d5d8dc",
            zorder=2,
        )
        ax.plot(
            [0.0, upper[0], lower[0], 0.0],
            [0.0, upper[1], lower[1], 0.0],
            color="#1c2833",
            lw=1.6,
            zorder=3,
        )
    else:
        ax.plot([0.0, length], [0.0, 0.0], color="#1c2833", lw=2.4, zorder=3)

    if not state["attached"] or state["theta"] is None:
        stand = 0.22
        bow_y = [y_min + (y_max - y_min) * i / 48 for i in range(49)]
        bow_x = [-stand + 0.18 * y * y for y in bow_y]
        ax.plot(bow_x, bow_y, color="#c0392b", lw=2.2, zorder=4)
        ax.text(0.35, y_min + 0.12, "detached bow\n(schematic)", color="#c0392b", fontsize=8)
        title = "Detached shock"
        detail = rf"no wave angle,  $\delta_{{\max}} = {_fmt(math.degrees(state['delta_max']))}^\circ$"
    else:
        theta = state["theta"]
        color = "#1a5276" if state["shock"] == "mach-wave" else "#c0392b"
        style = "--" if state["shock"] == "mach-wave" else "-"
        reach = 1.45
        for sign in (1.0, -1.0):
            ax.plot(
                [0.0, reach * math.cos(sign * theta)],
                [0.0, reach * math.sin(sign * theta)],
                color=color,
                lw=2.1,
                ls=style,
                zorder=4,
            )
        if theta > 0.04:
            arc_r = 0.55
            ax.plot(
                [arc_r * math.cos(a) for a in _angles(0.0, theta)],
                [arc_r * math.sin(a) for a in _angles(0.0, theta)],
                color=color,
                lw=1.0,
            )
            ax.text(
                0.68 * math.cos(0.55 * theta),
                0.68 * math.sin(0.55 * theta),
                r"$\theta$",
                color=color,
                fontsize=12,
            )
        if delta > 0.04:
            arc_r = 0.32
            ax.plot(
                [arc_r * math.cos(a) for a in _angles(0.0, delta)],
                [arc_r * math.sin(a) for a in _angles(0.0, delta)],
                color="#1c2833",
                lw=1.0,
            )
            ax.text(
                0.42 * math.cos(0.45 * delta),
                0.42 * math.sin(0.45 * delta),
                r"$\delta_c$",
                color="#1c2833",
                fontsize=12,
            )
        names = {
            "mach-wave": "Mach wave",
            "weak": "Attached conical shock",
            "maximum-cone": "Attached, maximum cone",
        }
        title = names.get(state["shock"], "Conical shock")
        if state["Mc"] is not None and state["Cp"] is not None:
            detail = (
                rf"$\theta = {_fmt(math.degrees(state['theta']))}^\circ$,  "
                rf"$M_c = {_fmt(state['Mc'])}$,  "
                rf"$C_p = {_fmt(state['Cp'])}$"
            )
        else:
            detail = rf"$\theta = {_fmt(math.degrees(state['theta']))}^\circ$"
    ax.set_title(title + "\n" + detail, fontsize=10)


def _mesh_cone(half_angle: float, length: float, n_x: int = 18, n_th: int = 28):
    import numpy as np

    x = np.linspace(0.0, length, n_x)
    ang = np.linspace(0.0, 2.0 * math.pi, n_th)
    xx, tt = np.meshgrid(x, ang)
    radius = xx * math.tan(max(half_angle, 1e-6))
    yy = radius * np.cos(tt)
    zz = radius * np.sin(tt)
    return xx, yy, zz


def _draw_solid(ax, state: dict) -> None:
    import numpy as np

    delta = max(state["delta"], 1e-4)
    length = 1.0
    cone_x, cone_y, cone_z = _mesh_cone(delta, length)
    ax.plot_surface(
        cone_x,
        cone_y,
        cone_z,
        color="#bdc3c7",
        alpha=0.95,
        linewidth=0.0,
        antialiased=True,
    )
    if state["attached"] and state["theta"] is not None:
        shock_x, shock_y, shock_z = _mesh_cone(state["theta"], 1.15)
        ax.plot_wireframe(
            shock_x,
            shock_y,
            shock_z,
            color="#c0392b",
            linewidth=0.45,
            rstride=3,
            cstride=4,
            alpha=0.85,
        )
        ax.set_title("Cone and conical shock", fontsize=10)
    else:
        bow_t = np.linspace(0.0, 2.0 * math.pi, 60)
        bow_r = np.linspace(0.0, 0.85, 12)
        tt, rr = np.meshgrid(bow_t, bow_r)
        xx = -0.18 - 0.22 * (rr ** 2)
        yy = rr * np.cos(tt)
        zz = rr * np.sin(tt)
        ax.plot_wireframe(xx, yy, zz, color="#c0392b", linewidth=0.5, alpha=0.8)
        ax.set_title("Detached bow (schematic)", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_box_aspect((1.4, 1.0, 1.0))
    ax.view_init(elev=18.0, azim=-60.0)
    ax.set_xlim(-0.3, 1.2)
    span = 0.85
    ax.set_ylim(-span, span)
    ax.set_zlim(-span, span)


def write_figure(state: dict, out_path: Path) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(11.2, 5.4))
    ax0 = fig.add_subplot(1, 2, 1)
    ax1 = fig.add_subplot(1, 2, 2, projection="3d")
    _draw_meridian(ax0, state)
    _draw_solid(ax1, state)
    fig.suptitle(
        PLOT_TITLE
        + "\n"
        + (
            f"M1 = {_fmt(state['mach'])},  "
            f"gamma = {_fmt(state['gamma'])},  "
            f"delta_c = {_fmt(math.degrees(state['delta']))}\u00b0"
        ),
        fontsize=12,
    )
    fig.text(
        0.5,
        0.02,
        "Meridian cut to scale. A detached bow is schematic, not a computed shock locus.",
        ha="center",
        fontsize=8,
        color="#566573",
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.90))
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    def near(got: float, expected: float, label: str, tol: float = CHECK_TOL) -> int | None:
        if abs(got - expected) > tol * max(1.0, abs(expected)):
            return fail(f"{label} is {got}, expected {expected}")
        return None

    gamma = 7.0 / 5.0
    if near(
        taylor_maccoll_radial_acceleration(gamma, 0.5, 0.0, math.pi / 4.0),
        -1.0,
        "surface Taylor-Maccoll",
    ):
        return 1
    if near(limiting_speed_ratio(2.0, gamma), 2.0 / 3.0, "Mach-2 limiting speed"):
        return 1
    u_wave = 1.0 / math.sqrt(3.0)
    v_wave = -1.0 / 3.0
    if near(shock_wave_tangent(gamma, u_wave, v_wave), 1.0 / math.sqrt(3.0), "Mach-wave RH"):
        return 1
    if near(freestream_mach_sq(gamma, u_wave, math.pi / 6.0), 4.0, "Mach-wave M_inf^2"):
        return 1
    if near(resultant_mach(gamma, u_wave, v_wave), 2.0, "Mach-wave local Mach"):
        return 1
    if near(pressure_coefficient_from_mach(1.0, 2.0, gamma), 0.0, "freestream Cp"):
        return 1

    wave = evaluate(2.0, gamma, 0.0)
    if wave["shock"] != "mach-wave" or not wave["attached"]:
        return fail("zero cone was not a Mach wave")
    if near(wave["theta"], math.pi / 6.0, "Mach angle", tol=1e-12):
        return 1
    if near(wave["Mc"], 2.0, "Mach-wave surface Mach", tol=1e-12):
        return 1
    if near(wave["Cp"], 0.0, "Mach-wave Cp", tol=1e-12):
        return 1

    sonic_u = math.sqrt((gamma - 1.0) / (gamma + 1.0))
    ten_deg = math.radians(10.0)
    theta_w, u_w, v_w = integrate_to_shock(gamma, ten_deg, sonic_u)
    m_min_sq = freestream_mach_sq(gamma, u_w, theta_w)
    if near(math.sqrt(m_min_sq), 1.1159051, "SP-3004 10 deg minimum Mach", tol=2e-4):
        return 1
    if near(math.tan(theta_w), shock_wave_tangent(gamma, u_w, v_w), "sonic-surface RH", tol=2e-4):
        return 1

    attached = evaluate(2.0, gamma, ten_deg)
    if not attached["attached"] or attached["shock"] != "weak":
        return fail("10 deg cone at Mach 2 did not attach")
    if attached["theta"] is None or attached["theta"] <= ten_deg:
        return fail("10 deg cone shock is not above the surface")
    recovered = cone_from_shock(2.0, gamma, attached["theta"])
    if near(recovered["cone"], ten_deg, "recovered cone angle", tol=1e-5):
        return 1
    if attached["Mc"] is None or not (1.0 < attached["Mc"] < 2.0):
        return fail("surface Mach is not between 1 and M1")
    if attached["Cp"] is None or attached["Cp"] <= 0.0:
        return fail("surface Cp is not positive")
    if attached["theta_strong"] is None or attached["theta_strong"] <= attached["theta"]:
        return fail("strong conical root missing")

    detached = evaluate(2.0, gamma, math.radians(55.0))
    if detached["attached"] or detached["shock"] != "detached":
        return fail("55 deg cone at Mach 2 attached")
    if detached["theta"] is not None or detached["Mc"] is not None:
        return fail("detached shock invented a surface state")

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    def has_key(text: str, key: str) -> bool:
        prefix = key + ":"
        return any(line.startswith(prefix) for line in text.splitlines())

    with tempfile.TemporaryDirectory() as folder:
        attached_path = str(Path(folder) / "attached.png")
        code, text, err = capture(
            ["--mach", "2", "--gamma", "1.4", "--delta", str(ten_deg), "--out", attached_path]
        )
        if code != 0:
            return fail(f"attached main returned {code}: {err}")
        for key in (
            "attached: yes",
            "shock: weak",
            "theta_deg:",
            "Mc:",
            "Cp:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if not Path(attached_path).is_file() or Path(attached_path).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            return fail("attached run did not write a PNG")

        detached_path = str(Path(folder) / "detached.png")
        code, text, err = capture(
            ["--mach", "2", "--delta", str(math.radians(55.0)), "--out", detached_path]
        )
        if code != 0 or "attached: no" not in text or "shock: detached" not in text:
            return fail(f"detached stdout failed: {err or text}")
        if has_key(text, "theta_rad") or has_key(text, "Mc") or has_key(text, "Cp"):
            return fail("detached stdout printed a shock state")
        if "gamma_source: default" not in text:
            return fail("omitted gamma was not marked default")
        if not Path(detached_path).is_file():
            return fail("detached run did not write a PNG")

        code, _text, err = capture(["--mach", "0.8", "--delta", "0.1"])
        if code != 2 or "error:" not in err:
            return fail("subsonic Mach was accepted")
        code, _text, err = capture(["--mach", "2", "--delta", "20"])
        if code != 2:
            return fail("a half-angle in radians past pi/2 was accepted")
        code, _text, err = capture(["--mach", "2"])
        if code != 2:
            return fail("missing cone angle was accepted")

    print("check: pass")
    print_kv("theta_deg", math.degrees(attached["theta"]))
    print_kv("Mc", attached["Mc"])
    print_kv("Cp", attached["Cp"])
    print_kv("delta_max_deg", math.degrees(maximum_cone_angle(2.0, gamma)[1]))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Attached conical shock on a right circular cone at zero incidence."
    )
    parser.add_argument("--mach", type=float, default=None, help="freestream Mach M1, greater than 1")
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=None,
        help="cone half-angle in radians, from 0 up to pi/2",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG output path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.mach is None or args.delta is None:
        print("error: requires --mach and --delta", file=sys.stderr)
        return 2
    gamma = DEFAULT_GAMMA if args.gamma is None else args.gamma
    gamma_source = "default" if args.gamma is None else "supplied"
    try:
        require_inputs(args.mach, gamma, args.delta)
        state = evaluate(args.mach, gamma, args.delta)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = Path(args.out) if args.out else Path(__file__).resolve().parent / "conical_shock.png"
    out_path = out_path.resolve()
    if not out_path.parent.is_dir():
        print(f"error: PNG directory does not exist: {out_path.parent}", file=sys.stderr)
        return 2
    try:
        write_figure(state, out_path)
    except Exception as exc:
        print(f"error: could not write the cone figure: {exc}", file=sys.stderr)
        return 2
    emit(state, gamma_source, str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
