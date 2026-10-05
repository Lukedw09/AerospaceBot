#!/usr/bin/env python3
"""Symmetric pull-up radius, pitch rate, and load factor.

pullup_load_factor is n = 1 + V**2/(g*R). pullup_radius is
R = V**2/(g*(n - 1)). pullup_pitch_rate is omega = g*(n - 1)/V.
The stall limit at a speed is load_factor at lift_force with CLmax and
freestream_dynamic_pressure, the same stall_speed relation used on the
V-n diagram with W replaced by n*W.

A second load factor is sustained_turn_load_factor: thrust equals drag
on drag_polar with L = n*W. Constant-power thrust is useful_thrust T = P/V.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
G0 = 9.80665
PLOT_TITLE = "Symmetric pull-up"
PLOT_END_FACTOR = 1.5
N_PLOT = 201

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "wings-level symmetric pull-up initiated from horizontal flight so "
    "gamma = 0 and L - W = m*V**2/R; "
    "pullup_load_factor n = 1 + V**2/(g*R); "
    "pullup_radius R = V**2/(g*(n - 1)); "
    "pullup_pitch_rate omega = g*(n - 1)/V; omega = V/R; "
    f"g = g0 = {G0:g} m/s^2 unless stated otherwise; "
    "n > 1 so the radius is finite and positive; "
    "instantaneous (point) performance at the given speed; "
    "stall limit is load_factor n = L/W at lift_force L = CLmax*q*S and "
    "freestream_dynamic_pressure q = 0.5*rho*V**2, which is stall_speed "
    "with W replaced by n*W; that n is the steepest pull-up at that speed; "
    "sustained load factor is sustained_turn_load_factor: the n at which "
    "thrust equals drag on drag_polar CD = CD0 + k*CL**2 with "
    "k = 1/(pi*AR*e) and L = n*W; that n is the pull-up the engine can "
    "hold at that speed; "
    "constant-power available thrust is useful_thrust T = P/V; "
    "true airspeed at the supplied density; incompressible "
    "freestream_dynamic_pressure q = 0.5*rho*V**2; the plot end is "
    f"{PLOT_END_FACTOR:g} times the larger of the given speed and, for a "
    "given n, radius, or pitch rate, the stall speed at this load factor, "
    "or for thrust or power, the speed where parasite drag equals "
    "available thrust; weight is a force, so m = W/g0"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    print(f"{key}: {text}")


def pullup_radius(speed: float, g: float, n: float) -> float:
    """pullup_radius."""
    return speed * speed / (g * (n - 1.0))


def pullup_pitch_rate(g: float, n: float, speed: float) -> float:
    """pullup_pitch_rate."""
    return g * (n - 1.0) / speed


def load_from_radius(speed: float, g: float, radius: float) -> float:
    """pullup_load_factor."""
    return 1.0 + speed * speed / (g * radius)


def load_from_pitch_rate(speed: float, g: float, omega: float) -> float:
    """Inverse of pullup_pitch_rate: n = 1 + V*omega/g."""
    return 1.0 + speed * omega / g


def dynamic_pressure(rho: float, speed: float) -> float:
    """freestream_dynamic_pressure."""
    return 0.5 * rho * speed * speed


def stall_speed(weight: float, rho: float, area: float, clmax: float, load_factor: float) -> float:
    """stall_speed with W replaced by n*W."""
    return math.sqrt(2.0 * load_factor * weight / (rho * area * clmax))


def stall_load(speed: float, rho: float, area: float, clmax: float, weight: float) -> float:
    """load_factor at lift_force with CLmax."""
    return clmax * dynamic_pressure(rho, speed) * area / weight


def induced_factor(aspect_ratio: float, oswald: float) -> float:
    """k in CD = CD0 + k CL**2 from induced_drag_coefficient."""
    return 1.0 / (math.pi * aspect_ratio * oswald)


def useful_thrust(power: float, speed: float) -> float:
    """useful_thrust."""
    return power / speed


def available_thrust(speed: float, thrust: float | None, power: float | None) -> float:
    if thrust is not None:
        return thrust
    if power is None:
        raise ValueError("requires --thrust or --power")
    return useful_thrust(power, speed)


def sustained_load(
    q: float,
    area: float,
    thrust_avail: float,
    cd0: float,
    k: float,
    weight: float,
) -> float | None:
    """sustained_turn_load_factor, or None when T <= parasite drag."""
    excess = thrust_avail - q * area * cd0
    if excess <= 0.0:
        return None
    n_sq = q * area * excess / (k * weight * weight)
    if n_sq <= 0.0:
        return None
    return math.sqrt(n_sq)


def sustained_n_at(
    speed: float,
    rho: float,
    area: float,
    weight: float,
    cd0: float,
    k: float,
    thrust: float | None,
    power: float | None,
) -> float | None:
    if speed <= 0.0:
        return None
    return sustained_load(
        dynamic_pressure(rho, speed),
        area,
        available_thrust(speed, thrust, power),
        cd0,
        k,
        weight,
    )


def parasite_limit_speed(
    rho: float,
    area: float,
    cd0: float,
    thrust: float | None,
    power: float | None,
) -> float:
    """Speed where available thrust equals parasite drag, n = 0."""
    if thrust is not None:
        return math.sqrt(2.0 * thrust / (rho * area * cd0))
    return (2.0 * power / (rho * area * cd0)) ** (1.0 / 3.0)


def polar_drag(q: float, area: float, cd0: float, k: float, cl: float) -> float:
    return q * area * (cd0 + k * cl * cl)


def resolve_n(
    n: float | None,
    radius: float | None,
    pitch_rate: float | None,
    speed: float,
) -> float:
    chosen = [
        name
        for name, value in (("--n", n), ("--radius", radius), ("--pitch-rate", pitch_rate))
        if value is not None
    ]
    if len(chosen) != 1:
        raise ValueError(
            "pass one of --n, --radius, or --pitch-rate, not both"
            if chosen
            else "requires --n, --radius, or --pitch-rate"
        )
    if n is not None:
        if not math.isfinite(n) or n <= 1.0:
            raise ValueError("load factor must be finite and > 1")
        return n
    if radius is not None:
        require_positive("radius", radius)
        n_from_r = load_from_radius(speed, G0, radius)
        if n_from_r <= 1.0:
            raise ValueError("radius must give load factor > 1")
        return n_from_r
    require_positive("pitch rate", pitch_rate)
    n_from_w = load_from_pitch_rate(speed, G0, pitch_rate)
    if n_from_w <= 1.0:
        raise ValueError("pitch rate must give load factor > 1")
    return n_from_w


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def validate(speed: float, weight: float, area: float, clmax: float, rho: float) -> None:
    require_positive("speed", speed)
    require_positive("weight", weight)
    require_positive("wing area", area)
    require_positive("CLmax", clmax)
    require_positive("density", rho)


def validate_polar(cd0: float, aspect_ratio: float, oswald: float) -> None:
    require_positive("CD0", cd0)
    require_positive("aspect ratio", aspect_ratio)
    if not math.isfinite(oswald) or oswald <= 0.0 or oswald > 1.0:
        raise ValueError("Oswald efficiency must be finite, > 0, and <= 1")


def n_source_from_args(args: argparse.Namespace) -> str:
    flags = [
        ("--n", args.n is not None),
        ("--radius", args.radius is not None),
        ("--pitch-rate", args.pitch_rate is not None),
        ("--thrust", args.thrust is not None),
        ("--power", args.power is not None),
    ]
    chosen = [name for name, present in flags if present]
    if len(chosen) != 1:
        raise ValueError(
            "pass one of --n, --radius, --pitch-rate, --thrust, or --power, not both"
            if chosen
            else "requires --n, --radius, --pitch-rate, --thrust, or --power"
        )
    return chosen[0].lstrip("-")


def warnings_for(
    speed: float,
    n: float | None,
    v_stall_1g: float,
    n_stall: float,
) -> list[str]:
    notes: list[str] = []
    if speed < v_stall_1g:
        notes.append(
            f"speed {speed:.6g} m/s is below the 1-g stall {v_stall_1g:.6g} m/s"
        )
    if n is None:
        notes.append(
            "available thrust is at or below parasite drag; no real "
            "sustained load factor at this speed"
        )
        return notes
    if n_stall > 1.0 and n > n_stall:
        notes.append(
            f"load factor {n:.6g} exceeds the stall limit {n_stall:.6g} at this speed"
        )
    elif n_stall <= 1.0:
        notes.append(
            f"stall load factor {n_stall:.6g} is not above 1; no symmetric "
            "pull-up is available at this speed"
        )
    if n <= 1.0:
        notes.append(
            f"sustained load factor {n:.6g} is not above 1; the engine cannot "
            "hold a symmetric pull-up at this speed"
        )
    return notes


def solution(
    speed: float,
    weight: float,
    area: float,
    clmax: float,
    rho: float,
    n: float | None,
    v_plot_max: float | None = None,
) -> dict[str, float | bool]:
    q = dynamic_pressure(rho, speed)
    v_stall_1g = stall_speed(weight, rho, area, clmax, 1.0)
    n_stall = stall_load(speed, rho, area, clmax, weight)
    result: dict[str, float | bool] = {
        "V_m_s": speed,
        "q_Pa": q,
        "V_stall_1g_m_s": v_stall_1g,
        "n_stall": n_stall,
    }
    if n is not None:
        result["n"] = n
        result["CL"] = n * weight / (q * area)
        result["n_above_stall"] = n > n_stall
        v_stall_pull = stall_speed(weight, rho, area, clmax, max(n, 1.0))
        result["V_stall_pull_m_s"] = v_stall_pull
        if n > 1.0:
            result["R_m"] = pullup_radius(speed, G0, n)
            result["omega_rad_s"] = pullup_pitch_rate(G0, n, speed)
    else:
        v_stall_pull = v_stall_1g
        result["V_stall_pull_m_s"] = v_stall_pull
    if n_stall > 1.0:
        result["R_stall_m"] = pullup_radius(speed, G0, n_stall)
        result["omega_stall_rad_s"] = pullup_pitch_rate(G0, n_stall, speed)
    if v_plot_max is None:
        v_plot_max = PLOT_END_FACTOR * max(speed, v_stall_pull)
    result["V_plot_max_m_s"] = v_plot_max
    return result


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def commanded_curves(
    v_stall_pull: float,
    v_max: float,
    n: float,
) -> tuple[list[float], list[float], list[float]]:
    speeds = linspace(v_stall_pull, v_max, N_PLOT)
    radii = [pullup_radius(speed, G0, n) for speed in speeds]
    rates = [pullup_pitch_rate(G0, n, speed) for speed in speeds]
    return speeds, radii, rates


def stall_curves(
    weight: float,
    area: float,
    clmax: float,
    rho: float,
    v_stall_1g: float,
    v_max: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    start = v_stall_1g * (1.0 + 1.0 / (N_PLOT - 1))
    if start >= v_max:
        start = min(v_max, v_stall_1g * 1.001)
    speeds = linspace(start, v_max, N_PLOT)
    radii: list[float] = []
    rates: list[float] = []
    loads: list[float] = []
    kept: list[float] = []
    for speed in speeds:
        n_max = stall_load(speed, rho, area, clmax, weight)
        if n_max <= 1.0:
            continue
        kept.append(speed)
        loads.append(n_max)
        radii.append(pullup_radius(speed, G0, n_max))
        rates.append(pullup_pitch_rate(G0, n_max, speed))
    return kept, radii, rates, loads


def sustained_curves(
    weight: float,
    area: float,
    rho: float,
    cd0: float,
    k: float,
    v_max: float,
    thrust: float | None,
    power: float | None,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    start = v_max / N_PLOT
    speeds = linspace(start, v_max, N_PLOT)
    kept_n: list[float] = []
    loads: list[float] = []
    kept_pull: list[float] = []
    radii: list[float] = []
    rates: list[float] = []
    for speed in speeds:
        n = sustained_n_at(speed, rho, area, weight, cd0, k, thrust, power)
        if n is None:
            continue
        kept_n.append(speed)
        loads.append(n)
        if n <= 1.0:
            continue
        kept_pull.append(speed)
        radii.append(pullup_radius(speed, G0, n))
        rates.append(pullup_pitch_rate(G0, n, speed))
    return kept_n, loads, kept_pull, radii, rates


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the pull-up") from exc
    return plt


def plot_pullup(
    path: Path,
    weight: float,
    area: float,
    clmax: float,
    rho: float,
    n: float | None,
    result: dict[str, float | bool],
    polar: dict[str, float] | None = None,
    thrust: float | None = None,
    power: float | None = None,
) -> None:
    plt = ensure_matplotlib()
    v_max = float(result["V_plot_max_m_s"])
    stall_v, stall_r, stall_w, stall_n = stall_curves(
        weight, area, clmax, rho, float(result["V_stall_1g_m_s"]), v_max
    )
    engine = polar is not None
    if engine:
        fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 9))
        ax_n, ax_r, ax_w = axes
        n_v, n_vals, cmd_v, cmd_r, cmd_w = sustained_curves(
            weight,
            area,
            rho,
            polar["CD0"],
            polar["k"],
            v_max,
            thrust,
            power,
        )
        n_label = "thrust = drag" if thrust is not None else "power = drag*V"
        if n_v:
            ax_n.plot(n_v, n_vals, color="#1a5276", linewidth=1.8, label=n_label)
        if cmd_v:
            ax_r.plot(cmd_v, cmd_r, color="#1a5276", linewidth=1.8, label=n_label)
            ax_w.plot(cmd_v, cmd_w, color="#1a5276", linewidth=1.8, label=n_label)
        if stall_v:
            ax_n.plot(
                stall_v,
                stall_n,
                color="#c0392b",
                linestyle="--",
                linewidth=1.5,
                label="stall limit",
            )
    else:
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 7))
        ax_n = None
        ax_r, ax_w = axes
        cmd_v, cmd_r, cmd_w = commanded_curves(
            float(result["V_stall_pull_m_s"]), v_max, float(n)
        )
        ax_r.plot(cmd_v, cmd_r, color="#1a5276", linewidth=1.8, label="given n")
        ax_w.plot(cmd_v, cmd_w, color="#1a5276", linewidth=1.8, label="given n")
    if stall_v:
        ax_r.plot(
            stall_v,
            stall_r,
            color="#c0392b",
            linestyle="--",
            linewidth=1.5,
            label="stall limit",
        )
        ax_w.plot(
            stall_v,
            stall_w,
            color="#c0392b",
            linestyle="--",
            linewidth=1.5,
            label="stall limit",
        )
    if "R_m" in result:
        ax_r.plot(
            float(result["V_m_s"]),
            float(result["R_m"]),
            "s",
            color="#1a5276",
            markersize=7,
            zorder=5,
            label="operating point",
        )
        ax_w.plot(
            float(result["V_m_s"]),
            float(result["omega_rad_s"]),
            "s",
            color="#1a5276",
            markersize=7,
            zorder=5,
            label="operating point",
        )
    if ax_n is not None and "n" in result:
        ax_n.plot(
            float(result["V_m_s"]),
            float(result["n"]),
            "s",
            color="#1a5276",
            markersize=7,
            zorder=5,
            label="operating point",
        )
        ax_n.axhline(1.0, color="#7f8c8d", linestyle=":", linewidth=1.0, label="n = 1")
        ax_n.set_ylabel("load factor")
        ax_n.set_title(PLOT_TITLE)
        ax_n.grid(True, alpha=0.35)
        ax_n.legend(loc="best", fontsize=8)
        ax_n.set_ylim(bottom=0.0)
        ax_n.set_xlim(0.0, v_max)
    if "V_stall_pull_m_s" in result and not engine:
        ax_r.axvline(float(result["V_stall_pull_m_s"]), color="#7f8c8d", linestyle=":", linewidth=1.0)
        ax_w.axvline(
            float(result["V_stall_pull_m_s"]),
            color="#7f8c8d",
            linestyle=":",
            linewidth=1.0,
            label="stall speed at this n",
        )
    ax_r.set_xlim(0.0, v_max)
    ax_r.set_ylabel("pull-up radius (m)")
    ax_w.set_ylabel("pitch rate (rad/s)")
    ax_w.set_xlabel("true airspeed (m/s)")
    if ax_n is None:
        ax_r.set_title(PLOT_TITLE)
    ax_r.grid(True, alpha=0.35)
    ax_w.grid(True, alpha=0.35)
    ax_r.legend(loc="best", fontsize=8)
    ax_w.legend(loc="best", fontsize=8)
    ax_r.set_ylim(bottom=0.0)
    ax_w.set_ylim(bottom=0.0)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    weight: float,
    area: float,
    clmax: float,
    rho: float,
    result: dict[str, float | bool],
    notes: list[str],
    path: Path,
    extra: dict[str, object] | None = None,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("weight_N", weight)
    print_kv("area_m2", area)
    print_kv("CLmax", clmax)
    print_kv("rho_kg_m3", rho)
    print_kv("g0_m_s2", G0)
    if extra:
        for key, value in extra.items():
            print_kv(key, value)
    print_kv("V_m_s", result["V_m_s"])
    if "n" in result:
        print_kv("n", result["n"])
    if "R_m" in result:
        print_kv("R_m", result["R_m"])
        print_kv("omega_rad_s", result["omega_rad_s"])
    print_kv("q_Pa", result["q_Pa"])
    if "CL" in result:
        print_kv("CL", result["CL"])
    print_kv("V_stall_1g_m_s", result["V_stall_1g_m_s"])
    print_kv("V_stall_pull_m_s", result["V_stall_pull_m_s"])
    print_kv("n_stall", result["n_stall"])
    if "n_above_stall" in result:
        print_kv("n_above_stall", result["n_above_stall"])
    if "R_stall_m" in result:
        print_kv("R_stall_m", result["R_stall_m"])
        print_kv("omega_stall_rad_s", result["omega_stall_rad_s"])
    print_kv("plot_end_factor", PLOT_END_FACTOR)
    print_kv("V_plot_max_m_s", result["V_plot_max_m_s"])
    print_kv("graph", str(path))
    if notes:
        print_kv("warning", "; ".join(notes))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    weight = 10000.0
    area = 16.0
    clmax = 1.6
    rho = 1.225
    speed = 50.0
    n = 2.0
    result = solution(speed, weight, area, clmax, rho, n)
    want_r = speed * speed / (G0 * (n - 1.0))
    want_w = G0 * (n - 1.0) / speed
    if near(float(result["R_m"]), want_r, "radius"):
        return 1
    if near(float(result["omega_rad_s"]), want_w, "pitch rate"):
        return 1
    if near(float(result["omega_rad_s"]), speed / float(result["R_m"]), "rate from V/R"):
        return 1
    if near(float(result["n"]), n, "n"):
        return 1
    if result["n_above_stall"] is not False:
        return fail("clean case should not be above stall")
    v_stall_1g = math.sqrt(2.0 * weight / (rho * area * clmax))
    v_stall_pull = math.sqrt(2.0 * n * weight / (rho * area * clmax))
    if near(float(result["V_stall_1g_m_s"]), v_stall_1g, "1-g stall"):
        return 1
    if near(float(result["V_stall_pull_m_s"]), v_stall_pull, "pull-up stall"):
        return 1
    n_at_pull_stall = stall_load(v_stall_pull, rho, area, clmax, weight)
    if near(n_at_pull_stall, n, "stall load at pull-up stall speed"):
        return 1
    q = 0.5 * rho * speed * speed
    if near(float(result["q_Pa"]), q, "dynamic pressure"):
        return 1
    if near(float(result["CL"]), n * weight / (q * area), "CL"):
        return 1

    if near(load_from_radius(10.0, 10.0, 10.0), 2.0, "unit load from radius"):
        return 1
    if near(pullup_radius(10.0, 10.0, 2.0), 10.0, "unit radius"):
        return 1
    if near(pullup_pitch_rate(10.0, 2.0, 10.0), 1.0, "unit pitch rate"):
        return 1
    if near(load_from_pitch_rate(10.0, 10.0, 1.0), 2.0, "unit load from pitch rate"):
        return 1

    from_n = resolve_n(2.0, None, None, speed)
    if near(from_n, 2.0, "resolve n"):
        return 1
    from_r = resolve_n(None, want_r, None, speed)
    if near(from_r, 2.0, "resolve radius"):
        return 1
    from_w = resolve_n(None, None, want_w, speed)
    if near(from_w, 2.0, "resolve pitch rate"):
        return 1

    notes = warnings_for(v_stall_1g * 0.5, 2.0, v_stall_1g, 0.25)
    if not any("below the 1-g stall" in note for note in notes):
        return fail("speed below 1-g stall produced no warning")
    notes = warnings_for(speed, 8.0, v_stall_1g, stall_load(speed, rho, area, clmax, weight))
    if not any("exceeds the stall limit" in note for note in notes):
        return fail("over-stall load factor produced no warning")
    if warnings_for(v_stall_pull * 1.2, 2.0, v_stall_1g, stall_load(v_stall_pull * 1.2, rho, area, clmax, weight)):
        return fail("available pull-up produced a warning")

    cd0 = 0.02
    aspect_ratio = 8.0
    oswald = 0.8
    k = induced_factor(aspect_ratio, oswald)
    if near(useful_thrust(20.0, 10.0), 2.0, "useful thrust"):
        return 1
    unit_n = sustained_load(4.0, 1.0, 2.0, 0.25, 1.0, 1.0)
    if unit_n is None or near(unit_n, 2.0, "unit sustained n"):
        return 1
    ld_max = 1.0 / (2.0 * math.sqrt(k * cd0))
    thrust = 1500.0
    n_peak = (thrust / weight) * ld_max
    q_peak = thrust / (2.0 * area * cd0)
    n_at_peak = sustained_load(q_peak, area, thrust, cd0, k, weight)
    if n_at_peak is None or near(n_at_peak, n_peak, "peak sustained n"):
        return 1
    n_jet = sustained_n_at(speed, rho, area, weight, cd0, k, thrust, None)
    if n_jet is None:
        return fail("jet sustained n was not real")
    cl_jet = n_jet * weight / (q * area)
    drag_jet = polar_drag(q, area, cd0, k, cl_jet)
    if near(drag_jet, thrust, "jet thrust equals drag"):
        return 1
    power = thrust * speed
    n_prop = sustained_n_at(speed, rho, area, weight, cd0, k, None, power)
    if n_prop is None or near(n_prop, n_jet, "power sustained n"):
        return 1
    if sustained_load(q, area, q * area * cd0, cd0, k, weight) is not None:
        return fail("parasite-only thrust produced a load factor")
    notes = warnings_for(speed, 0.8, v_stall_1g, stall_load(speed, rho, area, clmax, weight))
    if not any("engine cannot hold" in note for note in notes):
        return fail("sub-1 sustained n produced no warning")

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

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "pullup.png")
        code, text, err = capture(
            [
                "--speed",
                "50",
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--rho",
                "1.225",
                "--n",
                "2",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Symmetric pull-up",
            "n:",
            "R_m:",
            "omega_rad_s:",
            "V_stall_pull_m_s:",
            "n_stall:",
            "n_above_stall: false",
            "n_source: n",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "warning:" in text:
            return fail("clean case printed a warning")

        code, text, err = capture(
            [
                "--speed",
                "50",
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--rho",
                "1.225",
                "--radius",
                f"{want_r:.12g}",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"radius input returned {code}: {err}")
        if "n_source: radius" not in text:
            return fail("radius input did not print n_source")
        if "n: 2" not in text:
            return fail("radius input did not print n = 2")

        code, text, err = capture(
            [
                "--speed",
                "50",
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--rho",
                "1.225",
                "--pitch-rate",
                f"{want_w:.12g}",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"pitch-rate input returned {code}: {err}")
        if "n_source: pitch-rate" not in text:
            return fail("pitch-rate input did not print n_source")

        code, text, err = capture(
            [
                "--speed",
                "30",
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--rho",
                "1.225",
                "--n",
                "2",
                "--out",
                out,
            ]
        )
        if code != 0 or "warning:" not in text or "n_above_stall: true" not in text:
            return fail("over-stall case did not warn and mark n_above_stall")

        polar_flags = [
            "--speed",
            "50",
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--rho",
            "1.225",
            "--cd0",
            "0.02",
            "--ar",
            "8",
            "--e",
            "0.8",
            "--out",
            out,
        ]
        code, text, err = capture(polar_flags + ["--thrust", "1500"])
        if code != 0:
            return fail(f"thrust input returned {code}: {err}")
        if "n_source: thrust" not in text:
            return fail("thrust input did not print n_source")
        if "thrust_N: 1500" not in text:
            return fail("thrust input did not print thrust")
        if "n:" not in text:
            return fail("thrust input did not print n")
        if "warning:" in text:
            return fail("clean thrust case printed a warning")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("thrust run did not write a PNG")

        code, text, err = capture(polar_flags + ["--power", str(power)])
        if code != 0:
            return fail(f"power input returned {code}: {err}")
        if "n_source: power" not in text:
            return fail("power input did not print n_source")
        if "warning:" in text:
            return fail("clean power case printed a warning")

        code, text, err = capture(polar_flags + ["--thrust", "400"])
        if code != 0 or "warning:" not in text:
            return fail("weak thrust did not warn on stdout")

    code, _text, err = capture(
        ["--speed", "50", "--weight", "10000", "--area", "16", "--clmax", "1.6", "--rho", "1.225"]
    )
    if code != 2 or "--n" not in err:
        return fail("missing n/radius/pitch-rate was accepted")
    code, _text, err = capture(
        [
            "--speed",
            "50",
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--rho",
            "1.225",
            "--n",
            "2",
            "--radius",
            "100",
        ]
    )
    if code != 2 or "not both" not in err:
        return fail("both n and radius were accepted")
    code, _text, err = capture(
        [
            "--speed",
            "50",
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--rho",
            "1.225",
            "--n",
            "2",
            "--thrust",
            "1500",
        ]
    )
    if code != 2 or "not both" not in err:
        return fail("n and thrust were accepted together")
    code, _text, err = capture(
        [
            "--speed",
            "50",
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--rho",
            "1.225",
            "--thrust",
            "1500",
        ]
    )
    if code != 2 or "--cd0" not in err:
        return fail("thrust without a polar was accepted")
    code, _text, err = capture(
        [
            "--speed",
            "50",
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--rho",
            "1.225",
            "--n",
            "0.8",
        ]
    )
    if code != 2:
        return fail("load factor below 1 was accepted")
    code, _text, _err = capture([])
    if code != 2:
        return fail("missing inputs were accepted")

    print("check: pass")
    print_kv("n", result["n"])
    print_kv("R_m", result["R_m"])
    print_kv("omega_rad_s", result["omega_rad_s"])
    print_kv("V_stall_pull_m_s", result["V_stall_pull_m_s"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Symmetric pull-up radius and pitch rate, with radius and pitch "
            "rate plotted against true airspeed. Thrust or power with a "
            "parabolic polar sets the sustained load factor instead of a "
            "given n, radius, or pitch rate."
        )
    )
    parser.add_argument("--speed", type=float, default=None, help="true airspeed V [m/s]")
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--n", type=float, default=None, help="load factor n")
    parser.add_argument("--radius", type=float, default=None, help="pull-up flight-path radius R [m]")
    parser.add_argument(
        "--pitch-rate",
        type=float,
        default=None,
        help="pitch rate omega = d(theta)/dt [rad/s]",
    )
    parser.add_argument("--thrust", type=float, default=None, help="net thrust, taken independent of speed [N]")
    parser.add_argument(
        "--power",
        type=float,
        default=None,
        help="useful power, taken independent of speed [W]",
    )
    parser.add_argument("--cd0", type=float, default=None, help="zero-lift drag coefficient CD0")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio AR")
    parser.add_argument("--e", type=float, default=None, help="Oswald efficiency e, 0 < e <= 1")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def polar_from_args(args: argparse.Namespace) -> dict[str, float]:
    missing = [
        flag
        for flag, value in (("--cd0", args.cd0), ("--ar", args.ar), ("--e", args.e))
        if value is None
    ]
    if missing:
        raise ValueError(
            "--thrust or --power requires --cd0, --ar, and --e; "
            f"missing {', '.join(missing)}"
        )
    validate_polar(args.cd0, args.ar, args.e)
    if args.thrust is not None:
        require_positive("thrust", args.thrust)
    if args.power is not None:
        require_positive("power", args.power)
    k = induced_factor(args.ar, args.e)
    return {
        "CD0": args.cd0,
        "AR": args.ar,
        "e": args.e,
        "k": k,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--speed": args.speed,
        "--weight": args.weight,
        "--area": args.area,
        "--clmax": args.clmax,
        "--rho": args.rho,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --speed, --weight, --area, --clmax, --rho, and "
            f"--n, --radius, --pitch-rate, --thrust, or --power; missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        validate(args.speed, args.weight, args.area, args.clmax, args.rho)
        source = n_source_from_args(args)
        extra: dict[str, object] = {"n_source": source}
        polar = None
        thrust = args.thrust
        power = args.power
        v_plot_max = None
        if source in ("n", "radius", "pitch-rate"):
            if any(value is not None for value in (args.cd0, args.ar, args.e)):
                raise ValueError("--cd0, --ar, and --e are used with --thrust or --power")
            n = resolve_n(args.n, args.radius, args.pitch_rate, args.speed)
        else:
            polar = polar_from_args(args)
            extra.update(
                {
                    "CD0": polar["CD0"],
                    "AR": polar["AR"],
                    "e": polar["e"],
                    "k": polar["k"],
                }
            )
            if thrust is not None:
                extra["thrust_N"] = thrust
            else:
                extra["power_W"] = power
            n = sustained_n_at(
                args.speed,
                args.rho,
                args.area,
                args.weight,
                polar["CD0"],
                polar["k"],
                thrust,
                power,
            )
            thrust_avail = available_thrust(args.speed, thrust, power)
            extra["thrust_avail_N"] = thrust_avail
            if n is not None:
                extra["D_N"] = polar_drag(
                    dynamic_pressure(args.rho, args.speed),
                    args.area,
                    polar["CD0"],
                    polar["k"],
                    n * args.weight / (dynamic_pressure(args.rho, args.speed) * args.area),
                )
            v_n0 = parasite_limit_speed(args.rho, args.area, polar["CD0"], thrust, power)
            extra["V_parasite_m_s"] = v_n0
            v_plot_max = PLOT_END_FACTOR * max(args.speed, v_n0)
        result = solution(
            args.speed,
            args.weight,
            args.area,
            args.clmax,
            args.rho,
            n,
            v_plot_max,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "symmetric_pull_up.png"
        out_path = out_path.resolve()
        plot_pullup(
            out_path,
            args.weight,
            args.area,
            args.clmax,
            args.rho,
            n if n is not None and n > 1.0 else None,
            result,
            polar=polar,
            thrust=thrust,
            power=power,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    notes = warnings_for(
        args.speed,
        n,
        float(result["V_stall_1g_m_s"]),
        float(result["n_stall"]),
    )
    emit(
        args.weight,
        args.area,
        args.clmax,
        args.rho,
        result,
        notes,
        out_path,
        extra=extra,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
