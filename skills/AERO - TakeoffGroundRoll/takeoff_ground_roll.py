#!/usr/bin/env python3
"""Level dry-runway ground roll from brake release to lift-off.

Wheel load is wheel_normal_force N = W - L. Rolling friction is
rolling_friction mu*N. Net force is ground_roll_net_force
T - D - mu*(W - L). Acceleration is ground_roll_acceleration a = g*F/W.
Lift-off speed is liftoff_speed kLO*Vs. Constant thrust uses
ground_roll_A, ground_roll_B, ground_roll_distance, and ground_roll_time.
Useful power with a static thrust cap integrates V/a numerically.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
G0 = 9.80665
PLOT_TITLE = "Takeoff ground roll"
N_PLOT = 201
N_INT = 4001
MACH_WARN = 0.3
DEFAULT_K_LO = 1.2

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"
HUMID_DIR = SKILL_DIR.parent / "AERO - DensityAndPressureAltitude"

ASSUMPTIONS = (
    "level dry zero-wind runway; rotation is not a separate segment; "
    "no obstacle, slope, or wet-runway model; "
    "wheel_normal_force N = W - L; rolling_friction Fr = mu*N; "
    "ground_roll_net_force F = T - D - mu*(W - L); "
    "ground_roll_acceleration a = g*F/W with "
    f"g = g0 = {G0:g} m/s^2; "
    "L and D from lift_force, drag_force, and drag_polar at constant "
    "takeoff CL; freestream_dynamic_pressure q = 0.5*rho*V**2; "
    "takeoff stall_speed at CLmax when given, else at CL_TO; "
    f"liftoff_speed V_LO = k_LO*V_stall, default k_LO = {DEFAULT_K_LO:g}; "
    "constant thrust uses ground_roll_A, ground_roll_B, "
    "ground_roll_distance, and ground_roll_time; "
    "useful power uses useful_thrust T = P/V capped at static thrust, "
    "and integrates V/a numerically; still air so TAS equals ground speed; "
    "incompressible; weight is a force, so m = W/g0"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import GAMMA, M0, RSTAR, atmosphere, require_altitude
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for density at --alt"
        ) from exc
    return atmosphere, require_altitude, M0, RSTAR, GAMMA


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
    }


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def induced_factor(aspect_ratio: float, oswald: float) -> float:
    return 1.0 / (math.pi * aspect_ratio * oswald)


def polar_cd(cd0: float, k: float, cl: float) -> float:
    return cd0 + k * cl * cl


def dynamic_pressure(rho: float, speed: float) -> float:
    """freestream_dynamic_pressure."""
    return 0.5 * rho * speed * speed


def stall_speed(weight: float, rho: float, area: float, cl: float) -> float:
    """stall_speed."""
    return math.sqrt(2.0 * weight / (rho * area * cl))


def liftoff_speed(k_lo: float, v_stall: float) -> float:
    """liftoff_speed."""
    return k_lo * v_stall


def lift_force(cl: float, q: float, area: float) -> float:
    """lift_force."""
    return cl * q * area


def drag_force(cd: float, q: float, area: float) -> float:
    """drag_force."""
    return cd * q * area


def wheel_normal_force(weight: float, lift: float) -> float:
    """wheel_normal_force."""
    return weight - lift


def rolling_friction(mu: float, normal: float) -> float:
    """rolling_friction."""
    return mu * normal


def net_force(thrust: float, drag: float, mu: float, weight: float, lift: float) -> float:
    """ground_roll_net_force."""
    return thrust - drag - mu * (weight - lift)


def acceleration(g: float, force: float, weight: float) -> float:
    """ground_roll_acceleration."""
    return g * force / weight


def accel_const(g: float, thrust: float, weight: float, mu: float) -> float:
    """ground_roll_A."""
    return g * (thrust / weight - mu)


def accel_v2(
    g: float,
    rho: float,
    area: float,
    cd: float,
    mu: float,
    cl: float,
    weight: float,
) -> float:
    """ground_roll_B."""
    return g * rho * area * (cd - mu * cl) / (2.0 * weight)


def distance_closed(a_coef: float, b_coef: float, speed: float) -> float:
    """ground_roll_distance, including B = 0."""
    if speed == 0.0:
        return 0.0
    if abs(b_coef) <= 1e-18 * max(1.0, abs(a_coef)):
        return speed * speed / (2.0 * a_coef)
    disc = a_coef - b_coef * speed * speed
    if disc <= 0.0:
        raise ValueError("net force is not positive through lift-off")
    ratio = a_coef / disc
    if ratio <= 0.0:
        raise ValueError("ground-roll log argument is not positive")
    return math.log(ratio) / (2.0 * b_coef)


def time_closed(a_coef: float, b_coef: float, speed: float) -> float:
    """ground_roll_time, with B <= 0 handled separately."""
    if speed == 0.0:
        return 0.0
    if a_coef <= 0.0:
        raise ValueError("static acceleration is not positive")
    if abs(b_coef) <= 1e-18 * max(1.0, abs(a_coef)):
        return speed / a_coef
    if b_coef > 0.0:
        root = math.sqrt(a_coef * b_coef)
        num = math.sqrt(a_coef) + speed * math.sqrt(b_coef)
        den = math.sqrt(a_coef) - speed * math.sqrt(b_coef)
        if den <= 0.0 or num <= 0.0:
            raise ValueError("net force is not positive through lift-off")
        return math.log(num / den) / (2.0 * root)
    c_coef = -b_coef
    return math.atan(speed * math.sqrt(c_coef / a_coef)) / math.sqrt(a_coef * c_coef)


def speed_from_distance(a_coef: float, b_coef: float, distance: float) -> float:
    """Invert ground_roll_distance for V(s)."""
    if distance <= 0.0:
        return 0.0
    if abs(b_coef) <= 1e-18 * max(1.0, abs(a_coef)):
        return math.sqrt(2.0 * a_coef * distance)
    expo = math.exp(-2.0 * b_coef * distance)
    inside = a_coef * (1.0 - expo) / b_coef
    if inside < 0.0:
        raise ValueError("speed from distance is not real")
    return math.sqrt(inside)


def useful_thrust(power: float, speed: float) -> float:
    """useful_thrust."""
    return power / speed


def available_thrust(
    speed: float,
    thrust: float | None,
    power: float | None,
    static: float | None,
) -> float:
    if thrust is not None:
        return thrust
    if power is None or static is None:
        raise ValueError("power needs static thrust")
    if speed <= 0.0:
        return static
    return min(static, useful_thrust(power, speed))


def forces_at(
    speed: float,
    weight: float,
    area: float,
    cl: float,
    cd: float,
    mu: float,
    rho: float,
    thrust: float | None,
    power: float | None,
    static: float | None,
) -> dict[str, float]:
    q = dynamic_pressure(rho, speed)
    lift = lift_force(cl, q, area)
    drag = drag_force(cd, q, area)
    thrust_now = available_thrust(speed, thrust, power, static)
    normal = wheel_normal_force(weight, lift)
    friction = rolling_friction(mu, normal)
    force = net_force(thrust_now, drag, mu, weight, lift)
    accel = acceleration(G0, force, weight)
    return {
        "V_m_s": speed,
        "q_Pa": q,
        "thrust_N": thrust_now,
        "L_N": lift,
        "D_N": drag,
        "N_N": normal,
        "Fr_N": friction,
        "F_N": force,
        "a_m_s2": accel,
    }


def integrate_roll(
    v_lo: float,
    weight: float,
    area: float,
    cl: float,
    cd: float,
    mu: float,
    rho: float,
    thrust: float | None,
    power: float | None,
    static: float | None,
) -> tuple[float, float, list[float], list[float]]:
    """Trapezoid of V/a and 1/a from rest to V_LO. Returns s, t, V[], s[]."""
    speeds = [v_lo * i / (N_INT - 1) for i in range(N_INT)]
    accels: list[float] = []
    for speed in speeds:
        point = forces_at(
            speed, weight, area, cl, cd, mu, rho, thrust, power, static
        )
        if point["N_N"] < -CHECK_TOL:
            raise ValueError(
                "lift exceeds weight before lift-off; lower CL_TO or k_LO"
            )
        if point["a_m_s2"] <= 0.0:
            raise ValueError("net force is not positive through lift-off")
        accels.append(point["a_m_s2"])
    distance = 0.0
    duration = 0.0
    distances = [0.0]
    for i in range(1, N_INT):
        dv = speeds[i] - speeds[i - 1]
        a0 = accels[i - 1]
        a1 = accels[i]
        v0 = speeds[i - 1]
        v1 = speeds[i]
        duration += 0.5 * (1.0 / a0 + 1.0 / a1) * dv
        distance += 0.5 * (v0 / a0 + v1 / a1) * dv
        distances.append(distance)
    return distance, duration, speeds, distances


def parcel_from_oat(
    pressure: float,
    temperature: float,
    rh: float | None,
    m0: float,
    rstar: float,
    gamma: float,
    humid: dict,
) -> tuple[float, float, float]:
    """Density, molar mass, and sound speed at station pressure and OAT."""
    if rh is None:
        rho = humid["atmosphere_density"](pressure, m0, rstar, temperature)
        molar = m0
    else:
        es = humid["saturation_vapor_pressure"](temperature)
        vapor = humid["vapor_partial_pressure"](rh, es)
        if vapor >= pressure:
            raise ValueError("vapor partial pressure at or above station pressure")
        mw = humid["water_molar_mass"]()
        rho = humid["moist_density"](pressure, vapor, m0, rstar, temperature, mw)
        molar = humid["moist_mean_molar_mass"](pressure, vapor, m0, mw)
    cs = humid["sound_speed"](gamma, rstar, temperature, molar)
    return rho, molar, cs


def warnings_for(
    k_lo: float,
    cl_to: float,
    clmax: float | None,
    v_lo: float,
    sound_speed: float | None,
    normal_lo: float,
) -> list[str]:
    notes: list[str] = []
    if k_lo < 1.0:
        notes.append(
            f"lift-off factor {k_lo:.6g} is below 1; V_LO is below takeoff stall"
        )
    if clmax is not None and cl_to > clmax:
        notes.append(
            f"takeoff CL {cl_to:.6g} is above CLmax {clmax:.6g}"
        )
    if normal_lo <= 0.0:
        notes.append("wheel load at lift-off is not positive")
    if sound_speed is not None and sound_speed > 0.0:
        mach = v_lo / sound_speed
        if mach > MACH_WARN:
            notes.append(
                f"incompressible polar at Mach {mach:.6g}; "
                f"the checked model is used above Mach {MACH_WARN}"
            )
    return notes


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the ground roll") from exc
    return plt


def plot_roll(
    path: Path,
    distances: list[float],
    speeds: list[float],
    s_lo: float,
    v_lo: float,
) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(distances, speeds, color="#1a5276", linewidth=1.8, label="ground roll")
    ax.plot(
        s_lo,
        v_lo,
        "s",
        color="#c0392b",
        markersize=7,
        zorder=5,
        label="lift-off",
    )
    ax.axvline(s_lo, color="#c0392b", linestyle="--", linewidth=1.2)
    ax.set_xlim(0.0, max(s_lo * 1.05, distances[-1] if distances else s_lo))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel("ground distance (m)")
    ax.set_ylabel("true airspeed (m/s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    result: dict[str, object],
    notes: list[str],
    path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    order = (
        "method",
        "weight_N",
        "area_m2",
        "CL_TO",
        "CLmax",
        "mu",
        "CD0",
        "AR",
        "e",
        "k",
        "CD",
        "k_LO",
        "density_source",
        "Z_m",
        "T_K",
        "rh",
        "rh_source",
        "p_Pa",
        "rho_kg_m3",
        "cs_m_s",
        "g0_m_s2",
        "thrust_N",
        "power_W",
        "static_thrust_N",
        "V_stall_m_s",
        "stall_CL",
        "V_LO_m_s",
        "q_LO_Pa",
        "LD_LO",
        "thrust_0_N",
        "Fr_0_N",
        "F_0_N",
        "a_0_m_s2",
        "thrust_LO_N",
        "L_LO_N",
        "D_LO_N",
        "N_LO_N",
        "Fr_LO_N",
        "F_LO_N",
        "a_LO_m_s2",
        "s_m",
        "t_s",
        "A_m_s2",
        "B_1_m",
    )
    for key in order:
        if key in result:
            print_kv(key, result[key])
    for note in notes:
        print_kv("warning", note)
    print_kv("graph", str(path))


def fail(message: str) -> int:
    print(f"check: fail: {message}", file=sys.stderr)
    return 1


def near(actual: float, expected: float, label: str) -> bool:
    if abs(actual - expected) <= CHECK_TOL + 1e-8 * abs(expected):
        return False
    print(f"check: fail: {label}: {actual} != {expected}", file=sys.stderr)
    return True


def run_check() -> int:
    weight = 10000.0
    area = 16.0
    cl_to = 0.8
    mu = 0.02
    cd0 = 0.02
    aspect_ratio = 8.0
    oswald = 0.8
    clmax = 1.6
    k_lo = DEFAULT_K_LO
    thrust = 2500.0
    atmosphere, require_altitude, _m0, _rstar, _gamma = load_atmosphere()
    state = atmosphere(0.0)
    rho = state["rho"]
    k = induced_factor(aspect_ratio, oswald)
    cd = polar_cd(cd0, k, cl_to)
    v_stall = stall_speed(weight, rho, area, clmax)
    v_lo = liftoff_speed(k_lo, v_stall)
    a_coef = accel_const(G0, thrust, weight, mu)
    b_coef = accel_v2(G0, rho, area, cd, mu, cl_to, weight)
    s_closed = distance_closed(a_coef, b_coef, v_lo)
    t_closed = time_closed(a_coef, b_coef, v_lo)
    if near(a_coef, G0 * (thrust / weight - mu), "A"):
        return 1
    if near(
        b_coef,
        G0 * rho * area * (cd - mu * cl_to) / (2.0 * weight),
        "B",
    ):
        return 1
    disc = a_coef - b_coef * v_lo * v_lo
    s_log = math.log(a_coef / disc) / (2.0 * b_coef)
    if near(s_closed, s_log, "distance closed form"):
        return 1
    root = math.sqrt(a_coef * b_coef)
    t_log = math.log(
        (math.sqrt(a_coef) + v_lo * math.sqrt(b_coef))
        / (math.sqrt(a_coef) - v_lo * math.sqrt(b_coef))
    ) / (2.0 * root)
    if near(t_closed, t_log, "time closed form"):
        return 1
    start = forces_at(0.0, weight, area, cl_to, cd, mu, rho, thrust, None, None)
    if near(start["Fr_N"], mu * weight, "static friction"):
        return 1
    if near(start["F_N"], thrust - mu * weight, "static net force"):
        return 1
    if near(start["a_m_s2"], a_coef, "static acceleration"):
        return 1
    loft = forces_at(v_lo, weight, area, cl_to, cd, mu, rho, thrust, None, None)
    if loft["N_N"] <= 0.0:
        return fail("sample lift-off wheel load was not positive")
    if near(loft["L_N"] / loft["D_N"], cl_to / cd, "L/D"):
        return 1
    s_num, t_num, _speeds, _dist = integrate_roll(
        v_lo, weight, area, cl_to, cd, mu, rho, thrust, None, None
    )
    if abs(s_num - s_closed) > 1e-3 * s_closed:
        return fail(f"numerical distance {s_num} != closed {s_closed}")
    if abs(t_num - t_closed) > 1e-3 * t_closed:
        return fail(f"numerical time {t_num} != closed {t_closed}")
    if near(speed_from_distance(a_coef, b_coef, s_closed), v_lo, "V(s) invert"):
        return 1
    if near(distance_closed(4.0, 1.0, 1.0), 0.5 * math.log(4.0 / 3.0), "A=4 B=1 s"):
        return 1
    if near(time_closed(4.0, 1.0, 1.0), 0.25 * math.log(3.0), "A=4 B=1 t"):
        return 1
    if near(distance_closed(4.0, 0.0, 2.0), 0.5, "B=0 distance"):
        return 1
    if near(time_closed(4.0, -1.0, 1.0), math.atan(0.5) / 2.0, "B<0 time"):
        return 1

    power = 1.0e7
    s_pow, t_pow, _, _ = integrate_roll(
        v_lo, weight, area, cl_to, cd, mu, rho, None, power, thrust
    )
    if abs(s_pow - s_closed) > 1e-3 * s_closed:
        return fail("high-power numerical distance did not match constant thrust")
    if abs(t_pow - t_closed) > 1e-3 * t_closed:
        return fail("high-power numerical time did not match constant thrust")

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

    base = [
        "--weight",
        "10000",
        "--area",
        "16",
        "--clto",
        "0.8",
        "--mu",
        "0.02",
        "--cd0",
        "0.02",
        "--ar",
        "8",
        "--e",
        "0.8",
        "--alt",
        "0",
        "--clmax",
        "1.6",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "roll.png")
        code, text, err = capture(base + ["--thrust", "2500", "--out", out])
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Takeoff ground roll",
            "method: closed-form constant thrust",
            "V_stall_m_s:",
            "V_LO_m_s:",
            "q_LO_Pa:",
            "LD_LO:",
            "a_0_m_s2:",
            "a_LO_m_s2:",
            "s_m:",
            "t_s:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "warning:" in text:
            return fail("clean sea-level case printed a warning")

        code, text, err = capture(
            base + ["--power", "80000", "--static", "2500", "--out", out]
        )
        if code != 0:
            return fail(f"power run returned {code}: {err}")
        if "method: numerical" not in text:
            return fail("power run did not print numerical method")
        if not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("power run did not write a PNG")

        code, text, err = capture(
            base
            + [
                "--thrust",
                "2500",
                "--oat",
                "310",
                "--rh",
                "0.5",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"oat run returned {code}: {err}")
        if "density_source: oat" not in text:
            return fail("oat run did not mark density_source")
        if "T_K:" not in text or "rh:" not in text:
            return fail("oat run missing T or rh")

        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--clto",
                "0.8",
                "--mu",
                "0.02",
                "--cd0",
                "0.02",
                "--ar",
                "8",
                "--e",
                "0.8",
                "--clmax",
                "1.6",
                "--rho",
                str(rho),
                "--thrust",
                "2500",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"rho run returned {code}: {err}")
        if "density_source: density" not in text:
            return fail("rho run did not mark density_source")

        code, text, err = capture(base + ["--thrust", "2500", "--k-lo", "0.9", "--out", out])
        if code != 0 or "warning:" not in text:
            return fail("k_LO below 1 produced no warning")

    code, _text, err = capture(base)
    if code != 2 or "--thrust" not in err:
        return fail("missing thrust and power was accepted")
    code, _text, err = capture(base + ["--thrust", "2500", "--power", "80000"])
    if code != 2 or "not both" not in err:
        return fail("thrust and power were accepted together")
    code, _text, err = capture(base + ["--power", "80000"])
    if code != 2 or "--static" not in err:
        return fail("power without static thrust was accepted")
    code, _text, err = capture(base + ["--thrust", "2500", "--rho", "1.225"])
    if code != 2 or "not both" not in err:
        return fail("alt and rho were accepted together")
    code, _text, err = capture(
        [
            "--weight",
            "10000",
            "--area",
            "16",
            "--clto",
            "0.8",
            "--mu",
            "0.02",
            "--cd0",
            "0.02",
            "--ar",
            "8",
            "--e",
            "0.8",
            "--rho",
            "1.225",
            "--thrust",
            "2500",
            "--oat",
            "288.15",
        ]
    )
    if code != 2 or "--alt" not in err:
        return fail("oat with rho was accepted")
    code, _text, err = capture(base + ["--thrust", "100"])
    if code != 2:
        return fail("weak thrust was accepted")
    code, _text, err = capture(base + ["--thrust", "2500", "--clto", "2", "--clmax", "1.6"])
    if code != 2:
        return fail("CL_TO above CLmax was accepted")

    print("check: pass")
    print_kv("s_m", s_closed)
    print_kv("t_s", t_closed)
    print_kv("V_LO_m_s", v_lo)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ground-roll distance and time to lift-off on a level dry runway, "
            "with constant thrust or useful power capped at static thrust."
        )
    )
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--clto", type=float, default=None, help="takeoff lift coefficient CL_TO")
    parser.add_argument("--mu", type=float, default=None, help="rolling-friction coefficient")
    parser.add_argument("--cd0", type=float, default=None, help="zero-lift drag coefficient CD0")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio AR")
    parser.add_argument("--e", type=float, default=None, help="Oswald efficiency e, 0 < e <= 1")
    parser.add_argument("--thrust", type=float, default=None, help="net thrust, independent of speed [N]")
    parser.add_argument("--power", type=float, default=None, help="useful power, independent of speed [W]")
    parser.add_argument(
        "--static",
        type=float,
        default=None,
        help="finite static thrust [N], required with --power",
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--oat", type=float, default=None, help="outside air temperature [K]")
    parser.add_argument(
        "--rh",
        type=float,
        default=None,
        help="relative humidity 0 to 1, with --oat",
    )
    parser.add_argument(
        "--k-lo",
        type=float,
        default=DEFAULT_K_LO,
        help=f"lift-off speed / stall speed, default {DEFAULT_K_LO:g}",
    )
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--weight": args.weight,
        "--area": args.area,
        "--clto": args.clto,
        "--mu": args.mu,
        "--cd0": args.cd0,
        "--ar": args.ar,
        "--e": args.e,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --weight, --area, --clto, --mu, --cd0, --ar, and --e; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if args.thrust is None and args.power is None:
        print("error: requires --thrust or --power", file=sys.stderr)
        return 2
    if args.thrust is not None and args.power is not None:
        print("error: pass --thrust or --power, not both", file=sys.stderr)
        return 2
    if args.power is not None and args.static is None:
        print("error: --power requires --static", file=sys.stderr)
        return 2
    if args.thrust is not None and args.static is not None:
        print("error: --static is only used with --power", file=sys.stderr)
        return 2
    if args.alt is None and args.rho is None:
        print("error: requires --alt or --rho", file=sys.stderr)
        return 2
    if args.alt is not None and args.rho is not None:
        print("error: pass --alt or --rho, not both", file=sys.stderr)
        return 2
    if args.oat is not None and args.alt is None:
        print("error: --oat requires --alt", file=sys.stderr)
        return 2
    if args.rh is not None and args.oat is None:
        print("error: --rh requires --oat", file=sys.stderr)
        return 2

    try:
        require_positive("weight", args.weight)
        require_positive("wing area", args.area)
        require_positive("takeoff CL", args.clto)
        require_nonnegative("rolling-friction coefficient", args.mu)
        require_positive("CD0", args.cd0)
        require_positive("aspect ratio", args.ar)
        if not math.isfinite(args.e) or args.e <= 0.0 or args.e > 1.0:
            raise ValueError("Oswald efficiency must be finite, > 0, and <= 1")
        require_positive("k_LO", args.k_lo)
        if args.clmax is not None:
            require_positive("CLmax", args.clmax)
            if args.clto > args.clmax:
                raise ValueError("takeoff CL is above CLmax")
        if args.thrust is not None:
            require_positive("thrust", args.thrust)
        if args.power is not None:
            require_positive("power", args.power)
            require_positive("static thrust", args.static)
        if args.rho is not None:
            require_positive("density", args.rho)
        if args.oat is not None:
            require_positive("outside air temperature", args.oat)
        if args.rh is not None:
            if not math.isfinite(args.rh) or args.rh < 0.0 or args.rh > 1.0:
                raise ValueError("relative humidity must be finite and between 0 and 1")

        atmosphere, require_altitude, m0, rstar, gamma = load_atmosphere()
        sound = None
        altitude = None
        pressure = None
        density_source = "density"
        rh_source = None
        molar = m0
        if args.alt is not None:
            altitude = require_altitude(args.alt, "--alt")
            state = atmosphere(altitude)
            pressure = state["p"]
            if args.oat is None:
                rho = state["rho"]
                sound = state["cs"]
                density_source = "altitude"
            else:
                humid = load_humidity()
                rho, molar, sound = parcel_from_oat(
                    pressure, args.oat, args.rh, m0, rstar, gamma, humid
                )
                density_source = "oat"
                rh_source = "flag" if args.rh is not None else "dry"
        else:
            rho = args.rho

        cl_stall = args.clmax if args.clmax is not None else args.clto
        k = induced_factor(args.ar, args.e)
        cd = polar_cd(args.cd0, k, args.clto)
        v_stall = stall_speed(args.weight, rho, args.area, cl_stall)
        v_lo = liftoff_speed(args.k_lo, v_stall)
        start = forces_at(
            0.0,
            args.weight,
            args.area,
            args.clto,
            cd,
            args.mu,
            rho,
            args.thrust,
            args.power,
            args.static,
        )
        loft = forces_at(
            v_lo,
            args.weight,
            args.area,
            args.clto,
            cd,
            args.mu,
            rho,
            args.thrust,
            args.power,
            args.static,
        )
        if start["F_N"] <= 0.0:
            raise ValueError("static net force is not positive")
        if loft["N_N"] < 0.0:
            raise ValueError("lift exceeds weight before lift-off; lower CL_TO or k_LO")
        if loft["F_N"] <= 0.0:
            raise ValueError("net force at lift-off is not positive")
        if loft["D_N"] <= 0.0:
            raise ValueError("drag at lift-off is not positive")

        if args.thrust is not None:
            method = "closed-form constant thrust"
            a_coef = accel_const(G0, args.thrust, args.weight, args.mu)
            b_coef = accel_v2(G0, rho, args.area, cd, args.mu, args.clto, args.weight)
            s_lo = distance_closed(a_coef, b_coef, v_lo)
            t_lo = time_closed(a_coef, b_coef, v_lo)
            distances = linspace(0.0, s_lo, N_PLOT)
            speeds = [speed_from_distance(a_coef, b_coef, dist) for dist in distances]
        else:
            method = "numerical"
            s_lo, t_lo, speeds, distances = integrate_roll(
                v_lo,
                args.weight,
                args.area,
                args.clto,
                cd,
                args.mu,
                rho,
                args.thrust,
                args.power,
                args.static,
            )
            a_coef = None
            b_coef = None

        result: dict[str, object] = {
            "method": method,
            "weight_N": args.weight,
            "area_m2": args.area,
            "CL_TO": args.clto,
            "mu": args.mu,
            "CD0": args.cd0,
            "AR": args.ar,
            "e": args.e,
            "k": k,
            "CD": cd,
            "k_LO": args.k_lo,
            "density_source": density_source,
            "rho_kg_m3": rho,
            "g0_m_s2": G0,
            "V_stall_m_s": v_stall,
            "stall_CL": cl_stall,
            "V_LO_m_s": v_lo,
            "q_LO_Pa": loft["q_Pa"],
            "LD_LO": loft["L_N"] / loft["D_N"],
            "thrust_0_N": start["thrust_N"],
            "Fr_0_N": start["Fr_N"],
            "F_0_N": start["F_N"],
            "a_0_m_s2": start["a_m_s2"],
            "thrust_LO_N": loft["thrust_N"],
            "L_LO_N": loft["L_N"],
            "D_LO_N": loft["D_N"],
            "N_LO_N": loft["N_N"],
            "Fr_LO_N": loft["Fr_N"],
            "F_LO_N": loft["F_N"],
            "a_LO_m_s2": loft["a_m_s2"],
            "s_m": s_lo,
            "t_s": t_lo,
        }
        if args.clmax is not None:
            result["CLmax"] = args.clmax
        if altitude is not None:
            result["Z_m"] = altitude
        if args.oat is not None:
            result["T_K"] = args.oat
            result["rh"] = 0.0 if args.rh is None else args.rh
            result["rh_source"] = rh_source
        if pressure is not None:
            result["p_Pa"] = pressure
        if sound is not None:
            result["cs_m_s"] = sound
        if args.thrust is not None:
            result["thrust_N"] = args.thrust
            result["A_m_s2"] = a_coef
            result["B_1_m"] = b_coef
        if args.power is not None:
            result["power_W"] = args.power
            result["static_thrust_N"] = args.static
        notes = warnings_for(
            args.k_lo,
            args.clto,
            args.clmax,
            v_lo,
            sound,
            loft["N_N"],
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "takeoff_ground_roll.png"
        out_path = out_path.resolve()
        plot_roll(out_path, distances, speeds, s_lo, v_lo)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, notes, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
