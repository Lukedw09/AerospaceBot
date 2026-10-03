#!/usr/bin/env python3
"""Oblique shock and Prandtl-Meyer turn through one wedge deflection.

The deflection is the semivertex angle in oblique_shock_deflection and the
turning angle in prandtl_meyer. Downstream shock Mach uses
oblique_shock_normal_mach. Static pressure ratio uses normal_shock_pressure
with upstream Mach M1*sin(theta). Expansion pressure uses stagnation_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "Oblique shock and Prandtl-Meyer wedge"
DEFAULT_GAMMA = 1.4
MACH_MAX = 1.0e6
DETACH_TOL = 1.0e-10
ROOT_SPLIT = 1.0e-8

ASSUMPTIONS = (
    "calorically perfect gas; steady two-dimensional supersonic flow; "
    "the deflection is both the wedge semivertex angle and the "
    "Prandtl-Meyer turning angle; theta is the weak root of "
    "oblique_shock_deflection, between the Mach angle and 90 deg; "
    "downstream Mach uses oblique_shock_normal_mach, "
    "M2 = Mn2/sin(theta-delta); static pressure ratio uses "
    "normal_shock_pressure with upstream Mach M1*sin(theta); "
    "the shock is attached when the deflection does not exceed the "
    "maximum of that theta-delta relation; an isolated wedge takes the "
    "weak root, which is the wave drawn; the strong root is printed "
    "when it is distinct; zero deflection is a Mach wave; "
    "the expansion uses prandtl_meyer and stagnation_pressure; "
    "fan keys turn the post-shock flow back through the same deflection; "
    "this is a wedge, not a cone; shock curvature, boundary layer, and "
    "separation are not modeled"
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


def prandtl_meyer(mach: float, gamma: float) -> float:
    """prandtl_meyer in formulas.md. Angle from Mach 1, in radians."""
    if mach < 1.0:
        raise ValueError("Prandtl-Meyer Mach must be at least 1")
    if mach <= 1.0 + 1e-15:
        return 0.0
    gp = gamma + 1.0
    gm = gamma - 1.0
    return (
        math.sqrt(gp / gm) * math.atan(math.sqrt((gm / gp) * (mach * mach - 1.0)))
        - math.atan(math.sqrt(mach * mach - 1.0))
    )


def nu_max(gamma: float) -> float:
    """prandtl_meyer_max in formulas.md."""
    return (math.sqrt((gamma + 1.0) / (gamma - 1.0)) - 1.0) * math.pi / 2.0


def invert_prandtl_meyer(nu: float, gamma: float) -> float:
    """Mach whose Prandtl-Meyer angle is nu."""
    if nu <= 0.0:
        return 1.0
    limit = nu_max(gamma)
    if nu >= limit - 1e-14:
        raise ValueError("turn exceeds the maximum Prandtl-Meyer angle")
    lo = 1.0
    hi = 2.0
    while prandtl_meyer(hi, gamma) < nu:
        hi *= 2.0
        if hi > MACH_MAX:
            raise ValueError("downstream Mach is unbounded")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if prandtl_meyer(mid, gamma) < nu:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


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


def deflection_air(theta: float, mach: float) -> float:
    """oblique_shock_deflection_air, gamma = 7/5."""
    if theta <= 0.0 or theta >= math.pi / 2.0:
        return 0.0
    cot = math.cos(theta) / math.sin(theta)
    numer = 5.0 * (mach * mach * math.sin(2.0 * theta) - 2.0 * cot)
    denom = 10.0 + mach * mach * (7.0 + 5.0 * math.cos(2.0 * theta))
    return math.atan(numer / denom)


def maximum_deflection(mach: float, gamma: float) -> tuple[float, float]:
    """Wave angle and deflection at the peak of the theta-delta relation."""
    mu = mach_angle(mach)
    lo = mu + 1e-14
    hi = math.pi / 2.0 - 1e-14
    invphi = (math.sqrt(5.0) - 1.0) / 2.0
    left = hi - invphi * (hi - lo)
    right = lo + invphi * (hi - lo)
    left_value = deflection_angle(left, mach, gamma)
    right_value = deflection_angle(right, mach, gamma)
    for _ in range(80):
        if left_value < right_value:
            lo = left
            left = right
            left_value = right_value
            right = lo + invphi * (hi - lo)
            right_value = deflection_angle(right, mach, gamma)
        else:
            hi = right
            right = left
            right_value = left_value
            left = hi - invphi * (hi - lo)
            left_value = deflection_angle(left, mach, gamma)
    theta = 0.5 * (lo + hi)
    return theta, deflection_angle(theta, mach, gamma)


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
        "Mn2_sq": mn2_down,
        "M2": m2,
        "p_ratio": pressure,
    }


def isentropic_pressure_ratio(mach_1: float, mach_2: float, gamma: float) -> float:
    """p2/p1 from stagnation_pressure at constant total pressure."""

    def total_over_static(mach: float) -> float:
        return (1.0 + 0.5 * (gamma - 1.0) * mach * mach) ** (gamma / (gamma - 1.0))

    return total_over_static(mach_1) / total_over_static(mach_2)


def regime(mach: float) -> str:
    if mach > 1.0 + 1e-8:
        return "supersonic"
    if mach < 1.0 - 1e-8:
        return "subsonic"
    return "sonic"


def _bisect(lo: float, hi: float, target: float, mach: float, gamma: float, decreasing: bool) -> float:
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        value = deflection_angle(mid, mach, gamma)
        if decreasing:
            if value > target:
                lo = mid
            else:
                hi = mid
        elif value < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def freestream_expansion(mach: float, gamma: float, delta: float) -> dict[str, float | str | None]:
    """Prandtl-Meyer turn of the freestream through the wedge deflection."""
    nu1 = prandtl_meyer(mach, gamma)
    limit = nu_max(gamma)
    result: dict[str, float | str | None] = {"nu1": nu1, "nu_max": limit}
    if delta > limit - nu1 - 1e-12:
        result["expansion"] = "exceeds-maximum-turn"
        result["pm_M"] = None
        result["pm_p_ratio"] = None
        return result
    pm_m = invert_prandtl_meyer(nu1 + delta, gamma)
    result["expansion"] = "prandtl-meyer"
    result["pm_M"] = pm_m
    result["pm_p_ratio"] = isentropic_pressure_ratio(mach, pm_m, gamma)
    return result


def shoulder_fan(
    mach_2: float, gamma: float, delta: float, shock_pressure: float
) -> dict[str, float | str | None]:
    """Expand the post-shock flow back through the same deflection."""
    if mach_2 <= 1.0:
        return {"fan": "subsonic", "fan_M": None, "fan_p_ratio": None, "fan_p_over_p1": None}
    nu_post = prandtl_meyer(mach_2, gamma)
    if delta > nu_max(gamma) - nu_post - 1e-12:
        return {
            "fan": "exceeds-maximum-turn",
            "fan_M": None,
            "fan_p_ratio": None,
            "fan_p_over_p1": None,
        }
    fan_m = invert_prandtl_meyer(nu_post + delta, gamma)
    fan_ratio = isentropic_pressure_ratio(mach_2, fan_m, gamma)
    return {
        "fan": "yes",
        "fan_M": fan_m,
        "fan_p_ratio": fan_ratio,
        "fan_p_over_p1": fan_ratio * shock_pressure,
    }


def evaluate(mach: float, gamma: float, delta: float) -> dict:
    """Weak oblique shock, freestream expansion, and post-shock fan."""
    mu = mach_angle(mach)
    theta_star, delta_max = maximum_deflection(mach, gamma)
    expansion = freestream_expansion(mach, gamma, delta)
    state: dict = {
        "mach": mach,
        "gamma": gamma,
        "delta": delta,
        "mu": mu,
        "delta_max": delta_max,
        "theta_at_max": theta_star,
        "nu1": expansion["nu1"],
        "nu_max": expansion["nu_max"],
        "expansion": expansion["expansion"],
        "pm_M": expansion["pm_M"],
        "pm_p_ratio": expansion["pm_p_ratio"],
        "theta": None,
        "Mn1": None,
        "M2": None,
        "p2_over_p1": None,
        "M2_regime": None,
        "theta_strong": None,
        "M2_strong": None,
        "p2_over_p1_strong": None,
        "fan": None,
        "fan_M": None,
        "fan_p_ratio": None,
        "fan_p_over_p1": None,
    }
    if delta <= 1e-15:
        down = shock_downstream(mach, gamma, mu, 0.0)
        state.update(
            attached=True,
            shock="mach-wave",
            theta=mu,
            Mn1=down["Mn1"],
            M2=down["M2"],
            p2_over_p1=down["p_ratio"],
            M2_regime=regime(down["M2"]),
        )
        return state
    if delta > delta_max + DETACH_TOL:
        state.update(attached=False, shock="detached")
        return state

    if delta >= delta_max - DETACH_TOL:
        theta = theta_star
        branch = "maximum-deflection"
        theta_strong = None
    else:
        theta = _bisect(mu, theta_star, delta, mach, gamma, decreasing=False)
        theta_strong = _bisect(
            theta_star, math.pi / 2.0 - 1e-14, delta, mach, gamma, decreasing=True
        )
        if theta_strong - theta < ROOT_SPLIT:
            branch = "maximum-deflection"
            theta_strong = None
        else:
            branch = "weak"
    solved_delta = deflection_angle(theta, mach, gamma)
    down = shock_downstream(mach, gamma, theta, solved_delta)
    state.update(
        attached=True,
        shock=branch,
        theta=theta,
        Mn1=down["Mn1"],
        M2=down["M2"],
        p2_over_p1=down["p_ratio"],
        M2_regime=regime(down["M2"]),
    )
    if theta_strong is not None:
        strong_delta = deflection_angle(theta_strong, mach, gamma)
        try:
            strong = shock_downstream(mach, gamma, theta_strong, strong_delta)
        except ValueError:
            strong = None
        if strong is not None:
            state.update(
                theta_strong=theta_strong,
                M2_strong=strong["M2"],
                p2_over_p1_strong=strong["p_ratio"],
            )
    fan = shoulder_fan(down["M2"], gamma, delta, down["p_ratio"])
    state.update(fan)
    return state


def require_inputs(mach: float, gamma: float, delta: float) -> None:
    if not math.isfinite(mach) or mach <= 1.0 or mach > MACH_MAX:
        raise ValueError(f"--mach must be greater than 1 and at most {MACH_MAX:g}")
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("--gamma must be greater than 1")
    if not math.isfinite(delta) or delta < 0.0 or delta >= math.pi / 2.0:
        raise ValueError(
            "--delta must be a deflection in radians from 0 up to pi/2 "
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
    print_kv("nu1_rad", state["nu1"])
    print_kv("nu1_deg", math.degrees(state["nu1"]))
    print_kv("nu_max_rad", state["nu_max"])
    print_kv("nu_max_deg", math.degrees(state["nu_max"]))
    print_kv("attached", "yes" if state["attached"] else "no")
    print_kv("shock", state["shock"])
    if state["theta"] is not None:
        print_kv("theta_rad", state["theta"])
        print_kv("theta_deg", math.degrees(state["theta"]))
        print_kv("Mn1", state["Mn1"])
        print_kv("M2", state["M2"])
        print_kv("M2_regime", state["M2_regime"])
        print_kv("p2_over_p1", state["p2_over_p1"])
    if state["theta_strong"] is not None:
        print_kv("theta_strong_rad", state["theta_strong"])
        print_kv("theta_strong_deg", math.degrees(state["theta_strong"]))
        print_kv("M2_strong", state["M2_strong"])
        print_kv("p2_over_p1_strong", state["p2_over_p1_strong"])
    print_kv("expansion", state["expansion"])
    if state["pm_M"] is not None:
        print_kv("pm_M", state["pm_M"])
        print_kv("pm_p_ratio", state["pm_p_ratio"])
        print_kv("mu_pm_rad", mach_angle(state["pm_M"]))
        print_kv("mu_pm_deg", math.degrees(mach_angle(state["pm_M"])))
    if state["fan"] is not None:
        print_kv("fan", state["fan"])
        if state["fan_M"] is not None:
            print_kv("fan_M", state["fan_M"])
            print_kv("fan_p_ratio", state["fan_p_ratio"])
            print_kv("fan_p_over_p1", state["fan_p_over_p1"])
    print_kv("graph", graph)


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def _clip_length(
    angle: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    origin: tuple[float, float] = (0.0, 0.0),
) -> float:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x0, y0 = origin
    spans: list[float] = []
    if cosine > 1e-8:
        spans.append((x_max - x0) / cosine)
    elif cosine < -1e-8:
        spans.append((x_min - x0) / cosine)
    if sine > 1e-8:
        spans.append((y_max - y0) / sine)
    elif sine < -1e-8:
        spans.append((y_min - y0) / sine)
    positive = [span for span in spans if span > 0.0]
    if not positive:
        return 0.35
    return min(positive) * 0.9


def _sector(radius: float, start: float, stop: float, steps: int = 24) -> list[tuple[float, float]]:
    points = [(0.0, 0.0)]
    for index in range(steps + 1):
        angle = start + (stop - start) * index / steps
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def _flow_arrows(ax, x0: float, x1: float, ys: list[float]) -> None:
    for y_pos in ys:
        ax.annotate(
            "",
            xy=(x1, y_pos),
            xytext=(x0, y_pos),
            arrowprops={"arrowstyle": "-|>", "color": "#1a5276", "lw": 1.3},
        )


def _panel_frame(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d5d8dc")


def _draw_shock(ax, state: dict) -> None:
    delta = state["delta"]
    limits = (-1.15, 1.45, -1.2, 1.25)
    x_min, x_max, y_min, y_max = limits
    length = 0.92
    if delta > 1e-8:
        length = min(0.92, 0.95 / max(math.sin(delta), 0.2))
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    _panel_frame(ax)
    _flow_arrows(ax, -1.05, -0.58, [0.42, 0.78, 1.05])
    ax.text(-1.02, 0.12, r"$M_1$", color="#1a5276", fontsize=11)

    if delta <= 1e-8:
        ax.plot([0.0, length], [0.0, 0.0], color="#1c2833", lw=2.5, solid_capstyle="round")
    else:
        upper = (length * math.cos(delta), length * math.sin(delta))
        lower = (upper[0], -upper[1])
        wedge = [(0.0, 0.0), upper, lower]
        ax.fill([p[0] for p in wedge], [p[1] for p in wedge], color="#d5d8dc", zorder=1)
        ax.plot([0.0, upper[0], lower[0], 0.0], [0.0, upper[1], lower[1], 0.0], color="#1c2833", lw=1.6, zorder=3)
        ax.plot([0.0, 1.15], [0.0, 0.0], color="#aab7b8", lw=0.7, ls="--", zorder=2)

    if not state["attached"] or state["theta"] is None:
        stand = 0.32
        edge = max(abs(y_min), abs(y_max))
        # Stay upstream of the nose (x = 0) over the whole frame.
        curvature = (stand - 0.05) / (edge * edge)
        bow_y = [y_min + (y_max - y_min) * i / 48 for i in range(49)]
        bow_x = [-stand + curvature * y * y for y in bow_y]
        ax.plot(bow_x, bow_y, color="#c0392b", lw=2.2, zorder=4)
        ax.text(0.35, y_min + 0.12, "detached bow\n(schematic)", color="#c0392b", fontsize=8, ha="left")
        title = "Detached shock"
        detail = rf"no wave angle,  $\delta_{{\max}} = {_fmt(math.degrees(state['delta_max']))}^\circ$"
    else:
        theta = state["theta"]
        color = "#1a5276" if state["shock"] == "mach-wave" else "#c0392b"
        style = "--" if state["shock"] == "mach-wave" else "-"
        for sign in (1.0, -1.0):
            angle = sign * theta
            reach = _clip_length(angle, x_min, x_max, y_min, y_max)
            ax.plot(
                [0.0, reach * math.cos(angle)],
                [0.0, reach * math.sin(angle)],
                color=color,
                lw=2.1,
                ls=style,
                zorder=4,
            )
        if delta > 1e-8 and theta > delta:
            for sign in (1.0, -1.0):
                band = _sector(0.72, sign * delta, sign * theta)
                ax.fill(
                    [p[0] for p in band],
                    [p[1] for p in band],
                    color="#f5b7b1",
                    alpha=0.55,
                    zorder=0,
                )
        if theta > 0.04:
            arc_r = 0.50
            ax.plot(
                [arc_r * math.cos(a) for a in _angles(0.0, theta)],
                [arc_r * math.sin(a) for a in _angles(0.0, theta)],
                color=color,
                lw=1.0,
            )
            ax.text(
                0.62 * math.cos(0.55 * theta),
                0.62 * math.sin(0.55 * theta),
                r"$\theta$",
                color=color,
                fontsize=12,
            )
        if delta > 0.04:
            arc_r = 0.30
            ax.plot(
                [arc_r * math.cos(a) for a in _angles(0.0, delta)],
                [arc_r * math.sin(a) for a in _angles(0.0, delta)],
                color="#1c2833",
                lw=1.0,
            )
            ax.text(
                0.40 * math.cos(0.45 * delta),
                0.40 * math.sin(0.45 * delta),
                r"$\delta$",
                color="#1c2833",
                fontsize=12,
            )
        if state["shock"] != "mach-wave" and state["M2"] is not None and theta > delta + 0.18:
            mid = 0.5 * (theta + delta)
            ax.text(0.84 * math.cos(mid), 0.84 * math.sin(mid), r"$M_2$", color="#6b2d2d", fontsize=11)
        names = {
            "mach-wave": "Mach wave",
            "weak": "Attached weak shock",
            "maximum-deflection": "Attached, maximum deflection",
        }
        title = names.get(state["shock"], "Oblique shock")
        detail = (
            rf"$\theta = {_fmt(math.degrees(state['theta']))}^\circ$,  "
            rf"$M_2 = {_fmt(state['M2'])}$,  "
            rf"$p_2/p_1 = {_fmt(state['p2_over_p1'])}$"
        )
    ax.set_title(title + "\n" + detail, fontsize=10)


def _angles(start: float, stop: float, steps: int = 32) -> list[float]:
    if steps < 1:
        return [start, stop]
    return [start + (stop - start) * i / steps for i in range(steps + 1)]


def _draw_expansion(ax, state: dict) -> None:
    delta = state["delta"]
    x_min, x_max = -1.15, 1.45
    y_max = 1.25
    y_min = min(-0.55, -1.2 * math.sin(delta) - 0.25)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    _panel_frame(ax)
    _flow_arrows(ax, -1.05, -0.55, [0.28, 0.62, 0.96])
    ax.text(-1.02, 0.05, r"$M_1$", color="#1a5276", fontsize=11)

    wall_end = (1.05 * math.cos(-delta), 1.05 * math.sin(-delta))
    ax.plot([-0.85, 0.0], [0.0, 0.0], color="#1c2833", lw=2.4, solid_capstyle="butt")
    ax.plot([0.0, wall_end[0]], [0.0, wall_end[1]], color="#1c2833", lw=2.4, solid_capstyle="butt")
    if delta > 0.04:
        arc_r = 0.28
        ax.plot(
            [arc_r * math.cos(a) for a in _angles(0.0, -delta)],
            [arc_r * math.sin(a) for a in _angles(0.0, -delta)],
            color="#1c2833",
            lw=1.0,
        )
        ax.text(
            0.40 * math.cos(-0.55 * delta),
            0.40 * math.sin(-0.55 * delta),
            r"$\delta$",
            color="#1c2833",
            fontsize=12,
        )

    if state["expansion"] != "prandtl-meyer" or state["pm_M"] is None:
        ax.text(
            0.15,
            max(0.35, 0.5 * y_max),
            "turn exceeds\n" + r"$\nu_{\max}$",
            color="#1a5276",
            fontsize=10,
        )
        title = "Prandtl-Meyer expansion"
        detail = rf"no uniform downstream state,  $\nu_{{\max}} = {_fmt(math.degrees(state['nu_max']))}^\circ$"
        ax.set_title(title + "\n" + detail, fontsize=10)
        return

    pm_m = float(state["pm_M"])
    mu_up = state["mu"]
    mu_down = mach_angle(pm_m)
    leading = mu_up
    trailing = -delta + mu_down
    rays = 7
    for index in range(rays + 1):
        fraction = index / rays
        if delta <= 1e-8:
            angle = leading
        else:
            turned = -fraction * delta
            nu = float(state["nu1"]) + fraction * delta
            local_mach = invert_prandtl_meyer(nu, state["gamma"])
            angle = turned + mach_angle(local_mach)
        reach = _clip_length(angle, x_min, x_max, y_min, y_max)
        width = 2.0 if index in (0, rays) else 1.0
        ax.plot(
            [0.0, reach * math.cos(angle)],
            [0.0, reach * math.sin(angle)],
            color="#1a5276",
            lw=width,
            zorder=3,
        )
        if delta <= 1e-8:
            break
    if trailing < leading:
        fan = _sector(0.78, trailing, leading)
        ax.fill([p[0] for p in fan], [p[1] for p in fan], color="#d4e6f1", alpha=0.7, zorder=0)
    title = "Prandtl-Meyer expansion"
    if delta <= 1e-8:
        detail = rf"zero turning,  $M = {_fmt(pm_m)}$"
    else:
        detail = (
            rf"$M = {_fmt(pm_m)}$,  "
            rf"$p_2/p_1 = {_fmt(float(state['pm_p_ratio']))}$"
        )
    ax.set_title(title + "\n" + detail, fontsize=10)


def write_figure(state: dict, out_path: Path) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.3))
    _draw_shock(axes[0], state)
    _draw_expansion(axes[1], state)
    fig.suptitle(
        PLOT_TITLE
        + "\n"
        + (
            f"M1 = {_fmt(state['mach'])},  "
            f"gamma = {_fmt(state['gamma'])},  "
            f"delta = {_fmt(math.degrees(state['delta']))}\u00b0"
        ),
        fontsize=12,
    )
    fig.text(
        0.5,
        0.02,
        "Wave angles are drawn to scale. A detached bow is schematic, not a computed shock locus.",
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

    def near(got: float, expected: float, label: str, tol: float = 1e-9) -> int | None:
        if abs(got - expected) > tol * max(1.0, abs(expected)):
            return fail(f"{label} is {got}, expected {expected}")
        return None

    gamma = 7.0 / 5.0
    theta = math.pi / 4.0
    delta = math.atan(5.0 / 19.0)
    if near(deflection_angle(theta, 2.0, gamma), delta, "deflection at 45 deg"):
        return 1
    if near(deflection_air(theta, 2.0), delta, "air deflection at 45 deg"):
        return 1
    if near(deflection_angle(math.pi / 6.0, 2.0, gamma), 0.0, "Mach-wave deflection", tol=1e-12):
        return 1
    down = shock_downstream(2.0, gamma, theta, delta)
    if near(down["p_ratio"], 13.0 / 6.0, "pressure ratio"):
        return 1
    if near(down["Mn2_sq"], 7.0 / 13.0, "normal downstream Mach squared"):
        return 1
    if near(down["Mn1"], math.sqrt(2.0), "normal upstream Mach"):
        return 1
    if near(down["M2"], math.sqrt(193.0 / 91.0), "downstream Mach", tol=1e-12):
        return 1

    solved = evaluate(2.0, gamma, delta)
    if solved["shock"] != "weak" or not solved["attached"]:
        return fail(f"45 deg wave was {solved['shock']}, attached={solved['attached']}")
    if near(solved["theta"], theta, "solved wave angle", tol=1e-10):
        return 1
    if near(solved["M2"], math.sqrt(193.0 / 91.0), "solved M2", tol=1e-10):
        return 1
    if near(solved["p2_over_p1"], 13.0 / 6.0, "solved pressure ratio", tol=1e-10):
        return 1
    if solved["theta_strong"] is None:
        return fail("strong root missing")
    if not (solved["theta_strong"] > solved["theta"]):
        return fail("strong root is not above the weak root")
    strong_delta = deflection_angle(solved["theta_strong"], 2.0, gamma)
    if near(strong_delta, delta, "strong-root deflection", tol=1e-9):
        return 1
    if not (solved["M2_strong"] < 1.0 and solved["p2_over_p1_strong"] > solved["p2_over_p1"]):
        return fail("strong root is not the slower, higher-pressure wave")
    if solved["expansion"] != "prandtl-meyer":
        return fail("expansion through atan(5/19) was rejected")
    pm_turn = prandtl_meyer(solved["pm_M"], gamma) - prandtl_meyer(2.0, gamma)
    if near(pm_turn, delta, "Prandtl-Meyer turning", tol=1e-9):
        return 1
    if not (0.0 < solved["pm_p_ratio"] < 1.0):
        return fail("expansion pressure ratio is not below 1")
    if solved["fan"] != "yes":
        return fail(f"shoulder fan was {solved['fan']}")
    fan_turn = prandtl_meyer(solved["fan_M"], gamma) - prandtl_meyer(solved["M2"], gamma)
    if near(fan_turn, delta, "shoulder turning", tol=1e-8):
        return 1
    if near(
        solved["fan_p_over_p1"],
        solved["fan_p_ratio"] * solved["p2_over_p1"],
        "fan pressure chain",
        tol=1e-12,
    ):
        return 1

    wave = evaluate(2.0, gamma, 0.0)
    if wave["shock"] != "mach-wave" or not wave["attached"]:
        return fail("zero deflection was not a Mach wave")
    if near(wave["theta"], math.pi / 6.0, "Mach angle", tol=1e-12):
        return 1
    if near(wave["M2"], 2.0, "Mach-wave downstream Mach", tol=1e-12):
        return 1
    if near(wave["p2_over_p1"], 1.0, "Mach-wave pressure", tol=1e-12):
        return 1
    if near(wave["pm_M"], 2.0, "zero-turn expansion Mach", tol=1e-10):
        return 1

    normal = shock_downstream(2.0, gamma, math.pi / 2.0 - 1e-12, 0.0)
    if near(normal["M2"] ** 2, 1.0 / 3.0, "normal-shock Mach squared", tol=1e-8):
        return 1
    if near(normal["p_ratio"], 4.5, "normal-shock pressure", tol=1e-8):
        return 1

    analytic = math.atan(1.0 / math.sqrt(gamma * gamma - 1.0))
    _theta_inf, delta_inf = maximum_deflection(1.0e4, gamma)
    if near(delta_inf, analytic, "infinite-Mach maximum deflection", tol=1e-6):
        return 1
    theta_analytic = 0.5 * math.acos(-1.0 / gamma)
    if near(_theta_inf, theta_analytic, "infinite-Mach wave angle", tol=1e-4):
        return 1
    for sample_mach in (2.0, 5.0):
        _peak, peak_delta = maximum_deflection(sample_mach, gamma)
        mu = mach_angle(sample_mach)
        for index in range(1, 360):
            sample = mu + (math.pi / 2.0 - mu) * index / 360.0
            if deflection_angle(sample, sample_mach, gamma) > peak_delta + 1e-8:
                return fail(f"deflection peak missed at M={sample_mach}")

    attached = evaluate(2.0, gamma, math.radians(10.0))
    if not attached["attached"] or attached["theta"] <= math.radians(10.0):
        return fail("10 deg wedge at Mach 2 did not attach above the surface")
    detached = evaluate(2.0, gamma, math.radians(30.0))
    if detached["attached"] or detached["shock"] != "detached":
        return fail("30 deg wedge at Mach 2 attached")
    if detached["theta"] is not None or detached["M2"] is not None:
        return fail("detached shock invented a wave angle")

    limited = evaluate(math.sqrt(2.0), 5.0 / 3.0, 1.5)
    if limited["expansion"] != "exceeds-maximum-turn" or limited["pm_M"] is not None:
        return fail("expansion past nu_max was accepted")
    if limited["attached"]:
        return fail("1.5 rad turn at Mach sqrt(2) attached")
    if near(prandtl_meyer(math.sqrt(2.0), 5.0 / 3.0), 2.0 * math.atan(0.5) - math.pi / 4.0, "PM identity"):
        return 1
    if near(nu_max(5.0 / 3.0), math.pi / 2.0, "monatomic nu_max"):
        return 1
    recovered = invert_prandtl_meyer(prandtl_meyer(math.sqrt(2.0), 5.0 / 3.0), 5.0 / 3.0)
    if near(recovered, math.sqrt(2.0), "inverted Prandtl-Meyer Mach", tol=1e-10):
        return 1
    if shoulder_fan(0.8, gamma, 0.1, 2.0)["fan"] != "subsonic":
        return fail("subsonic shoulder was expanded")

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
            ["--mach", "2", "--gamma", "1.4", "--delta", str(delta), "--out", attached_path]
        )
        if code != 0:
            return fail(f"attached main returned {code}: {err}")
        for key in (
            "attached: yes",
            "shock: weak",
            "theta_deg:",
            "M2:",
            "p2_over_p1:",
            "expansion: prandtl-meyer",
            "pm_M:",
            "fan: yes",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if not Path(attached_path).is_file() or Path(attached_path).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            return fail("attached run did not write a PNG")

        detached_path = str(Path(folder) / "detached.png")
        code, text, err = capture(
            ["--mach", "2", "--delta", str(math.radians(30.0)), "--out", detached_path]
        )
        if code != 0 or "attached: no" not in text or "shock: detached" not in text:
            return fail(f"detached stdout failed: {err or text}")
        if has_key(text, "theta_rad") or has_key(text, "M2") or has_key(text, "p2_over_p1"):
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
            return fail("a deflection in radians past pi/2 was accepted")
        code, _text, err = capture(["--mach", "2"])
        if code != 2:
            return fail("missing deflection was accepted")

    print("check: pass")
    print_kv("theta_deg", math.degrees(solved["theta"]))
    print_kv("M2", solved["M2"])
    print_kv("p2_over_p1", solved["p2_over_p1"])
    print_kv("delta_max_deg", math.degrees(maximum_deflection(2.0, gamma)[1]))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Oblique shock and Prandtl-Meyer wedge for one deflection."
    )
    parser.add_argument("--mach", type=float, default=None, help="upstream Mach M1, greater than 1")
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
        help="wedge deflection in radians, from 0 up to pi/2",
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
    out_path = Path(args.out) if args.out else Path(__file__).resolve().parent / "prandtl_meyer_and_shocks.png"
    out_path = out_path.resolve()
    if not out_path.parent.is_dir():
        print(f"error: PNG directory does not exist: {out_path.parent}", file=sys.stderr)
        return 2
    try:
        write_figure(state, out_path)
    except Exception as exc:
        print(f"error: could not write the shock figure: {exc}", file=sys.stderr)
        return 2
    emit(state, gamma_source, str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
