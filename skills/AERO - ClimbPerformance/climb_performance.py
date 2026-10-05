#!/usr/bin/env python3
"""Best-rate climb versus geometric altitude on a parabolic drag polar.

Rate of climb is rate_of_climb Ps = (T-D)*V/W, or
rate_of_climb_from_power with useful power. Climb angle is climb_angle.
Service ceiling uses service_ceiling_rate (100 ft/min) unless --cutoff.
Absolute ceiling is zero rate. Density is the 1976 atmosphere, or
AERO - DensityAndPressureAltitude with a constant temperature offset.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Rate of climb"
N_SWEEP = 401
N_PLOT = 201
PLOT_HEADROOM = 1.1
MACH_WARN = 0.3
CLIMB_WARN_RAD = math.radians(10.0)
Z_MAX = 86000.0
FT_TO_M = 0.3048
MIN_TO_S = 60.0
SERVICE_FPM = 100.0
DEFAULT_CUTOFF = SERVICE_FPM * FT_TO_M / MIN_TO_S

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"
HUMID_DIR = SKILL_DIR.parent / "AERO - DensityAndPressureAltitude"

ASSUMPTIONS = (
    "steady unaccelerated climb; L = W; parabolic polar CD = CD0 + "
    "CL**2/(pi*AR*e) from drag_polar and induced_drag_coefficient; "
    "0 < e <= 1; rate_of_climb Ps = (T-D)*V/W; "
    "rate_of_climb_from_power Ps = (P-D*V)/W with useful_thrust T = P/V; "
    "climb_angle gamma = asin((T-D)/W) = climb_angle_from_rate asin(Ps/V); "
    "jet thrust independent of speed: best rate maximizes V*(T-D); "
    "propeller useful power independent of speed: best rate at minimum "
    "power, CL = sqrt(3*CD0/k), k = 1/(pi*AR*e); "
    "incompressible freestream_dynamic_pressure; still air; "
    "1976 hydrostatic density versus geometric altitude, or a constant "
    "temperature offset from the ground with AERO - DensityAndPressureAltitude "
    "at the 1976 station pressure; humidity that would exceed local pressure "
    "is dropped (dry air at that altitude); thrust and useful power do not fall "
    "with altitude; service ceiling is best rate equal to "
    "service_ceiling_rate (100 ft/min) unless --cutoff; absolute ceiling "
    "is best rate equal to zero; a negative rate is a descent; the PNG "
    f"ends at {PLOT_HEADROOM:g} times the absolute ceiling unless --z-end "
    "is passed; weight is a force"
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
            "ATMOS - Standard1976 must be importable for density versus altitude"
        ) from exc
    return atmosphere, require_altitude, M0, RSTAR, GAMMA


def load_humidity():
    folder = str(HUMID_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from density_and_pressure_altitude import (
            altitude_from_value,
            atmosphere_density,
            load_atmosphere as load_humid_atmos,
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
            "temperature, humidity, and density-altitude inversion"
        ) from exc
    return {
        "altitude_from_value": altitude_from_value,
        "atmosphere_density": atmosphere_density,
        "load_humid_atmos": load_humid_atmos,
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


def induced_factor(aspect_ratio: float, oswald: float) -> float:
    return 1.0 / (math.pi * aspect_ratio * oswald)


def stall_speed(weight: float, rho: float, area: float, cl: float) -> float:
    """stall_speed."""
    return math.sqrt(2.0 * weight / (rho * area * cl))


def polar_drag(
    weight: float,
    rho: float,
    area: float,
    cd0: float,
    k: float,
    speed: float,
) -> tuple[float, float, float]:
    """Drag, CL, and CD on drag_polar at L = W."""
    dynamic = 0.5 * rho * speed * speed
    cl = weight / (dynamic * area)
    cd = cd0 + k * cl * cl
    drag = cd * dynamic * area
    return drag, cl, cd


def rate_of_climb(thrust: float, drag: float, speed: float, weight: float) -> float:
    """rate_of_climb."""
    return (thrust - drag) * speed / weight


def rate_of_climb_from_power(
    power: float, drag: float, speed: float, weight: float
) -> float:
    """rate_of_climb_from_power."""
    return (power - drag * speed) / weight


def climb_angle_from_sine(sine: float) -> float | None:
    if abs(sine) <= 1.0:
        return math.asin(sine)
    return None


def jet_best_rate(
    weight: float,
    rho: float,
    area: float,
    cd0: float,
    k: float,
    thrust: float,
) -> tuple[float, float, float]:
    """Speed, drag, and climb rate for constant thrust."""
    parasite = 0.5 * rho * area * cd0
    induced = 2.0 * k * weight**2 / (rho * area)
    disc = thrust**2 + 12.0 * parasite * induced
    speed_sq = (thrust + math.sqrt(disc)) / (6.0 * parasite)
    speed = math.sqrt(speed_sq)
    drag = parasite * speed_sq + induced / speed_sq
    rate = rate_of_climb(thrust, drag, speed, weight)
    return speed, drag, rate


def prop_best_rate(
    weight: float,
    rho: float,
    area: float,
    cd0: float,
    k: float,
    power: float,
) -> tuple[float, float, float, float, float]:
    """Speed, drag, rate, CL, and CD at minimum power."""
    cl = math.sqrt(3.0 * cd0 / k)
    cd = cd0 + k * cl * cl
    speed = stall_speed(weight, rho, area, cl)
    drag = weight * cd / cl
    rate = rate_of_climb_from_power(power, drag, speed, weight)
    return speed, drag, rate, cl, cd


def best_rate_point(
    weight: float,
    area: float,
    cd0: float,
    k: float,
    rho: float,
    thrust: float | None,
    power: float | None,
    clmax: float | None,
) -> dict[str, float | bool | None]:
    if thrust is not None:
        speed, drag, rate = jet_best_rate(weight, rho, area, cd0, k, thrust)
        cl = weight / (0.5 * rho * speed * speed * area)
        cd = cd0 + k * cl * cl
        available = thrust
    else:
        if power is None:
            raise ValueError("thrust or power is required")
        speed, drag, rate, cl, cd = prop_best_rate(
            weight, rho, area, cd0, k, power
        )
        available = power / speed
    stalled = False
    if clmax is not None and cl > clmax:
        speed = stall_speed(weight, rho, area, clmax)
        drag, cl, cd = polar_drag(weight, rho, area, cd0, k, speed)
        if thrust is not None:
            rate = rate_of_climb(thrust, drag, speed, weight)
            available = thrust
        else:
            rate = rate_of_climb_from_power(power, drag, speed, weight)
            available = power / speed
        stalled = True
    sine = rate / speed if speed > 0.0 else 0.0
    return {
        "V_roc_m_s": speed,
        "D_N": drag,
        "roc_m_s": rate,
        "CL_roc": cl,
        "CD_roc": cd,
        "T_N": available,
        "sin_gamma": sine,
        "gamma_rad": climb_angle_from_sine(sine),
        "stalled": stalled,
    }


def parcel_from_oat(
    pressure: float,
    temperature: float,
    rh: float | None,
    m0: float,
    rstar: float,
    gamma: float,
    humid: dict,
) -> tuple[float, float, float]:
    if rh is None:
        rho = humid["atmosphere_density"](pressure, m0, rstar, temperature)
        molar = m0
    else:
        es = humid["saturation_vapor_pressure"](temperature)
        vapor = humid["vapor_partial_pressure"](rh, es)
        if vapor >= pressure:
            # The 1976 pressure falls faster than this ground RH can follow.
            rho = humid["atmosphere_density"](pressure, m0, rstar, temperature)
            molar = m0
        else:
            mw = humid["water_molar_mass"]()
            rho = humid["moist_density"](
                pressure, vapor, m0, rstar, temperature, mw
            )
            molar = humid["moist_mean_molar_mass"](pressure, vapor, m0, mw)
    cs = humid["sound_speed"](gamma, rstar, temperature, molar)
    return rho, molar, cs


def make_air(
    atmosphere,
    require_altitude,
    z_ground: float,
    oat: float | None,
    rh: float | None,
    m0: float,
    rstar: float,
    gamma: float,
    humid: dict | None,
):
    ground = atmosphere(require_altitude(z_ground, "--alt"))
    t_offset = None if oat is None else oat - ground["T"]

    def air_at(z_m: float) -> dict[str, float]:
        altitude = require_altitude(z_m, "altitude")
        state = atmosphere(altitude)
        if t_offset is None or humid is None:
            return {
                "Z_m": altitude,
                "rho": state["rho"],
                "cs": state["cs"],
                "p": state["p"],
                "T": state["T"],
            }
        temperature = state["T"] + t_offset
        if not math.isfinite(temperature) or temperature <= 0.0:
            raise ValueError("offset temperature is not positive")
        rho, _molar, cs = parcel_from_oat(
            state["p"], temperature, rh, m0, rstar, gamma, humid
        )
        return {
            "Z_m": altitude,
            "rho": rho,
            "cs": cs,
            "p": state["p"],
            "T": temperature,
        }

    return air_at, t_offset, ground


def plot_top(
    z_ground: float,
    service: dict | None,
    absolute: dict | None,
    z_end: float | None,
    extras: list[float],
) -> tuple[float, str]:
    """Geometric altitude at the top of the PNG. Default is 10% above absolute."""
    if z_end is not None:
        top = z_end
        source = "flag"
    elif absolute is not None:
        top = PLOT_HEADROOM * absolute["Z_m"]
        source = "absolute"
    elif service is not None:
        top = PLOT_HEADROOM * service["Z_m"]
        source = "service"
    else:
        top = Z_MAX
        source = "model"
    if extras:
        top = max(top, max(extras))
    top = min(Z_MAX, max(top, z_ground))
    return top, source


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def first_decreasing_root(
    altitudes: list[float],
    rates: list[float],
    target: float,
) -> tuple[float, float] | None:
    for i in range(len(altitudes) - 1):
        a = rates[i] - target
        b = rates[i + 1] - target
        if a >= 0.0 and b <= 0.0:
            return altitudes[i], altitudes[i + 1]
    return None


def bisect_rate(
    lo: float,
    hi: float,
    target: float,
    rate_at,
) -> float:
    z_lo, z_hi = lo, hi
    for _ in range(80):
        mid = 0.5 * (z_lo + z_hi)
        if rate_at(mid) > target:
            z_lo = mid
        else:
            z_hi = mid
    return 0.5 * (z_lo + z_hi)


def warnings_for(
    points: list[dict],
    clmax: float | None,
) -> list[str]:
    notes: list[str] = []
    if clmax is not None:
        for point in points:
            if point.get("stalled"):
                notes.append(
                    f"best-rate CL at {point['Z_m']:.6g} m exceeds CLmax "
                    f"{clmax:.6g}; speed is stall speed"
                )
                break
    for point in points:
        cs = point.get("cs")
        speed = point["V_roc_m_s"]
        if cs is not None and cs > 0.0 and speed / cs > MACH_WARN:
            notes.append(
                f"incompressible polar at Mach {speed / cs:.6g}; "
                f"the checked model is used above Mach {MACH_WARN}"
            )
            break
    for point in points:
        gamma = point.get("gamma_rad")
        if gamma is None:
            notes.append(
                "climb angle is not real on the L = W model at some station"
            )
            break
        if abs(gamma) > CLIMB_WARN_RAD:
            notes.append(
                "climb is steeper than 10 degrees; induced drag still uses L = W"
            )
            break
    return notes


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot rate of climb") from exc
    return plt


def plot_climb(
    path: Path,
    altitudes: list[float],
    rates: list[float],
    cutoff: float,
    ground: dict,
    service: dict | None,
    absolute: dict | None,
) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(rates, altitudes, color="#1a5276", linewidth=1.8, label="best rate")
    ax.axvline(
        cutoff,
        color="#7f8c8d",
        linestyle="--",
        linewidth=1.2,
        label="service cutoff",
    )
    ax.plot(
        ground["roc_m_s"],
        ground["Z_m"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="ground",
    )
    if service is not None:
        ax.plot(
            service["roc_m_s"],
            service["Z_m"],
            "s",
            color="#c0392b",
            markersize=7,
            zorder=5,
            label="service ceiling",
        )
    if absolute is not None:
        ax.plot(
            absolute["roc_m_s"],
            absolute["Z_m"],
            "o",
            color="#8e44ad",
            markersize=7,
            zorder=5,
            label="absolute ceiling",
        )
    ax.set_xlabel("rate of climb (m/s)")
    ax.set_ylabel("geometric altitude (m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ymin = min(altitudes)
    ymax = max(altitudes)
    ax.set_ylim(ymin, ymax if ymax > ymin else ymin + 1.0)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit_point(prefix: str, point: dict) -> None:
    print_kv(f"{prefix}Z_m", point["Z_m"])
    print_kv(f"{prefix}rho_kg_m3", point["rho"])
    if point.get("cs") is not None:
        print_kv(f"{prefix}cs_m_s", point["cs"])
    print_kv(f"{prefix}V_roc_m_s", point["V_roc_m_s"])
    print_kv(f"{prefix}roc_m_s", point["roc_m_s"])
    print_kv(f"{prefix}CL_roc", point["CL_roc"])
    print_kv(f"{prefix}CD_roc", point["CD_roc"])
    print_kv(f"{prefix}sin_gamma", point["sin_gamma"])
    if point.get("gamma_rad") is not None:
        print_kv(f"{prefix}gamma_rad", point["gamma_rad"])


def emit(
    result: dict[str, object],
    extras: list[dict],
    notes: list[str],
    path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "engine",
        "weight_N",
        "area_m2",
        "CD0",
        "AR",
        "e",
        "k",
        "CLmax",
        "thrust_N",
        "power_W",
        "roc_cutoff_m_s",
        "roc_cutoff_source",
        "density_source",
        "T_ground_K",
        "dT_K",
        "rh",
        "rh_source",
        "Z_plot_m",
        "z_plot_source",
    ):
        if key in result:
            print_kv(key, result[key])
    emit_point("ground_", result["ground"])
    for i, extra in enumerate(extras, start=1):
        emit_point(f"z_{i}_", extra)
    if result.get("service") is not None:
        emit_point("service_", result["service"])
    if result.get("absolute") is not None:
        emit_point("absolute_", result["absolute"])
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
    atmosphere, require_altitude, m0, rstar, gamma = load_atmosphere()
    sea = atmosphere(0.0)
    weight = 10000.0
    area = 16.0
    cd0 = 0.02
    aspect_ratio = 8.0
    oswald = 0.8
    k = induced_factor(aspect_ratio, oswald)
    thrust = 1500.0
    power = 50000.0
    if near(DEFAULT_CUTOFF, SERVICE_FPM * FT_TO_M / MIN_TO_S, "cutoff"):
        return 1
    if abs(DEFAULT_CUTOFF - 0.508) > 1e-12:
        return fail(f"service_ceiling_rate is {DEFAULT_CUTOFF}, not 0.508 m/s")

    jet = best_rate_point(
        weight, area, cd0, k, sea["rho"], thrust, None, None
    )
    prop = best_rate_point(
        weight, area, cd0, k, sea["rho"], None, power, None
    )
    parasite = 0.5 * sea["rho"] * area * cd0
    induced = 2.0 * k * weight**2 / (sea["rho"] * area)
    jet_speed = jet["V_roc_m_s"]
    residual = thrust - 3.0 * parasite * jet_speed**2 + induced / jet_speed**2
    if abs(residual) / thrust > CHECK_TOL:
        return fail(f"jet climb residual {residual}")
    drag, cl, cd = polar_drag(weight, sea["rho"], area, cd0, k, jet_speed)
    if near(jet["D_N"], drag, "jet drag"):
        return 1
    if near(
        jet["roc_m_s"],
        rate_of_climb(thrust, drag, jet_speed, weight),
        "jet roc",
    ):
        return 1
    if near(prop["CL_roc"], math.sqrt(3.0 * cd0 / k), "prop CL"):
        return 1
    if near(
        prop["roc_m_s"],
        rate_of_climb_from_power(power, prop["D_N"], prop["V_roc_m_s"], weight),
        "prop roc",
    ):
        return 1
    if near(
        prop["roc_m_s"] / prop["V_roc_m_s"],
        math.sin(prop["gamma_rad"]),
        "prop climb_angle_from_rate",
    ):
        return 1

    air_at, _offset, _ground_state = make_air(
        atmosphere, require_altitude, 0.0, None, None, m0, rstar, gamma, None
    )
    high = air_at(11000.0)
    prop_high = best_rate_point(
        weight, area, cd0, k, high["rho"], None, power, None
    )
    if not prop["roc_m_s"] > prop_high["roc_m_s"]:
        return fail("propeller rate of climb did not fall at 11 km")

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
        png = str(Path(tmp) / "climb.png")
        base = [
            "--weight",
            "10000",
            "--area",
            "16",
            "--cd0",
            "0.02",
            "--ar",
            "8",
            "--e",
            "0.8",
            "--alt",
            "0",
            "--out",
            png,
        ]
        code, text, err = capture(base + ["--power", "50000"])
        if code != 0:
            return fail(f"prop main returned {code}: {err}")
        for key in (
            "engine: power",
            "roc_cutoff_source: default",
            "density_source: altitude",
            "ground_roc_m_s:",
            "service_Z_m:",
            "absolute_Z_m:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "roc_cutoff_m_s: 0.508" not in text:
            return fail("default cutoff was not 0.508 m/s")
        if "z_plot_source: absolute" not in text or "Z_plot_m:" not in text:
            return fail("default plot top was not from the absolute ceiling")
        z_abs = None
        z_plot = None
        for line in text.splitlines():
            if line.startswith("absolute_Z_m:"):
                z_abs = float(line.split(":", 1)[1])
            if line.startswith("Z_plot_m:"):
                z_plot = float(line.split(":", 1)[1])
        if z_abs is None or z_plot is None:
            return fail("could not read plot and ceiling altitudes")
        want = PLOT_HEADROOM * z_abs
        if abs(z_plot - want) / want > 1e-6:
            return fail(f"plot top {z_plot} is not 1.1 times absolute {z_abs}")
        if not Path(png).is_file():
            return fail("PNG was not written")

        code, text, err = capture(base + ["--thrust", "1500", "--z", "3000"])
        if code != 0:
            return fail(f"thrust main returned {code}: {err}")
        if "engine: thrust" not in text or "z_1_Z_m:" not in text:
            return fail("thrust extra altitude was omitted")
        code, text, err = capture(base + ["--power", "50000", "--z-end", "86000"])
        if code != 0:
            return fail(f"z-end main returned {code}: {err}")
        if "z_plot_source: flag" not in text or "Z_plot_m: 86000" not in text:
            return fail("explicit plot top was not used")

        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--cd0",
                "0.02",
                "--ar",
                "8",
                "--e",
                "0.8",
                "--power",
                "50000",
                "--alt",
                "0",
                "--oat",
                "308.15",
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"oat main returned {code}: {err}")
        if "density_source: oat" not in text or "rh_source: dry" not in text:
            return fail("oat run did not mark density_source")
        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--cd0",
                "0.02",
                "--ar",
                "8",
                "--e",
                "0.8",
                "--power",
                "50000",
                "--alt",
                "0",
                "--oat",
                "308.15",
                "--rh",
                "0.5",
                "--out",
                png,
            ]
        )
        if code != 0:
            return fail(f"humid oat main returned {code}: {err}")
        if "rh_source: flag" not in text:
            return fail("humid oat run omitted rh_source")

        humid = load_humidity()
        atmos = humid["load_humid_atmos"]()
        _h, z_rho, _layer = humid["altitude_from_value"](
            sea["rho"], atmos, "density"
        )
        if near(z_rho, 0.0, "sea-level density altitude"):
            return 1
        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--cd0",
                "0.02",
                "--ar",
                "8",
                "--e",
                "0.8",
                "--power",
                "50000",
                "--rho",
                str(sea["rho"]),
                "--out",
                png,
            ]
        )
        if code != 0 or "density_source: density" not in text:
            return fail(f"rho main failed: {err}")

        code, _text, err = capture(base + ["--thrust", "1500", "--power", "50000"])
        if code != 2 or "not both" not in err:
            return fail("both thrust and power were accepted")
        code, _text, _err = capture(
            ["--weight", "10000", "--area", "16", "--cd0", "0.02", "--ar", "8", "--e", "0.8", "--alt", "0"]
        )
        if code != 2:
            return fail("missing thrust and power were accepted")

        stalled = best_rate_point(
            weight, area, cd0, k, sea["rho"], None, power, 0.4
        )
        if not stalled["stalled"]:
            return fail("CLmax below min-power CL produced no stall clip")

    print("check: pass")
    print_kv("roc_prop_m_s", prop["roc_m_s"])
    print_kv("roc_jet_m_s", jet["roc_m_s"])
    print_kv("roc_cutoff_m_s", DEFAULT_CUTOFF)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Best-rate climb versus geometric altitude from a parabolic "
            "drag polar, with 1976 density or an off-nominal ground parcel."
        )
    )
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--cd0", type=float, default=None, help="zero-lift drag coefficient CD0")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio AR")
    parser.add_argument("--e", type=float, default=None, help="Oswald efficiency e, 0 < e <= 1")
    parser.add_argument("--thrust", type=float, default=None, help="net thrust, independent of speed [N]")
    parser.add_argument(
        "--power",
        type=float,
        default=None,
        help="useful power, independent of speed [W]",
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric ground altitude [m]")
    parser.add_argument("--rho", type=float, default=None, help="air density at the field [kg/m^3]")
    parser.add_argument("--oat", type=float, default=None, help="outside air temperature at the ground [K]")
    parser.add_argument("--rh", type=float, default=None, help="relative humidity phi from 0 to 1")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument(
        "--cutoff",
        type=float,
        default=None,
        help="service-ceiling rate of climb [m/s]; omitted is 100 ft/min",
    )
    parser.add_argument(
        "--z",
        type=float,
        action="append",
        default=None,
        help="extra geometric altitude to print [m]; repeatable",
    )
    parser.add_argument(
        "--z-end",
        type=float,
        default=None,
        help="geometric altitude at the top of the PNG [m]; omitted is 1.1 times absolute ceiling",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def attach_air(point: dict, air: dict) -> dict:
    out = dict(point)
    out["Z_m"] = air["Z_m"]
    out["rho"] = air["rho"]
    out["cs"] = air["cs"]
    return out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--weight": args.weight,
        "--area": args.area,
        "--cd0": args.cd0,
        "--ar": args.ar,
        "--e": args.e,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --weight, --area, --cd0, --ar, and --e; "
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
        require_positive("CD0", args.cd0)
        require_positive("aspect ratio", args.ar)
        if not math.isfinite(args.e) or args.e <= 0.0 or args.e > 1.0:
            raise ValueError("Oswald efficiency must be finite, > 0, and <= 1")
        if args.thrust is not None:
            require_positive("thrust", args.thrust)
        if args.power is not None:
            require_positive("power", args.power)
        if args.clmax is not None:
            require_positive("CLmax", args.clmax)
        if args.cutoff is not None:
            require_positive("cutoff rate of climb", args.cutoff)
        if args.rho is not None:
            require_positive("density", args.rho)
        if args.oat is not None:
            require_positive("outside air temperature", args.oat)
        if args.rh is not None:
            if not math.isfinite(args.rh) or args.rh < 0.0 or args.rh > 1.0:
                raise ValueError("relative humidity must be finite and between 0 and 1")

        atmosphere, require_altitude, m0, rstar, gamma = load_atmosphere()
        humid = None
        density_source = "altitude"
        rh_source = None
        z_ground = 0.0
        if args.alt is not None:
            z_ground = require_altitude(args.alt, "--alt")
            if args.oat is not None:
                humid = load_humidity()
                density_source = "oat"
                rh_source = "flag" if args.rh is not None else "dry"
        else:
            humid = load_humidity()
            atmos = humid["load_humid_atmos"]()
            _height, z_ground, _layer = humid["altitude_from_value"](
                args.rho, atmos, "density"
            )
            z_ground = require_altitude(z_ground, "--rho")
            density_source = "density"

        extras_z = []
        if args.z:
            for value in args.z:
                extras_z.append(require_altitude(value, "--z"))
        z_end = None
        if args.z_end is not None:
            z_end = require_altitude(args.z_end, "--z-end")
            if z_end < z_ground:
                raise ValueError("--z-end must be at or above the ground altitude")

        cutoff = DEFAULT_CUTOFF if args.cutoff is None else args.cutoff
        cutoff_source = "default" if args.cutoff is None else "flag"
        k = induced_factor(args.ar, args.e)
        air_at, t_offset, ground_state = make_air(
            atmosphere,
            require_altitude,
            z_ground,
            args.oat,
            args.rh,
            m0,
            rstar,
            gamma,
            humid,
        )

        def point_at(z_m: float) -> dict:
            air = air_at(z_m)
            point = best_rate_point(
                args.weight,
                args.area,
                args.cd0,
                k,
                air["rho"],
                args.thrust,
                args.power,
                args.clmax,
            )
            return attach_air(point, air)

        def rate_at(z_m: float) -> float:
            return point_at(z_m)["roc_m_s"]

        altitudes = linspace(z_ground, Z_MAX, N_SWEEP)
        rates = [rate_at(z_m) for z_m in altitudes]
        ground = point_at(z_ground)
        service = None
        absolute = None
        notes: list[str] = []
        bracket = first_decreasing_root(altitudes, rates, cutoff)
        if bracket is not None:
            z_svc = bisect_rate(bracket[0], bracket[1], cutoff, rate_at)
            service = point_at(z_svc)
        elif rates[0] < cutoff:
            notes.append(
                "best rate at the ground is below the service-ceiling cutoff"
            )
        elif min(rates) > cutoff:
            notes.append(
                "best rate stays above the service-ceiling cutoff through 86 km"
            )
        abs_bracket = first_decreasing_root(altitudes, rates, 0.0)
        if abs_bracket is not None:
            z_abs = bisect_rate(abs_bracket[0], abs_bracket[1], 0.0, rate_at)
            absolute = point_at(z_abs)
        elif rates[0] <= 0.0:
            notes.append("best rate at the ground is not a climb")
        elif min(rates) > 0.0:
            notes.append("absolute ceiling is above the 1976 hydrostatic top at 86 km")

        z_plot, z_plot_source = plot_top(
            z_ground, service, absolute, z_end, extras_z
        )
        plot_alts = linspace(z_ground, z_plot, N_PLOT)
        plot_rates = [rate_at(z_m) for z_m in plot_alts]

        extras = [point_at(z_m) for z_m in extras_z]
        warn_points = [ground] + extras
        if service is not None:
            warn_points.append(service)
        if absolute is not None:
            warn_points.append(absolute)
        notes.extend(warnings_for(warn_points, args.clmax))

        result: dict[str, object] = {
            "engine": "thrust" if args.thrust is not None else "power",
            "weight_N": args.weight,
            "area_m2": args.area,
            "CD0": args.cd0,
            "AR": args.ar,
            "e": args.e,
            "k": k,
            "roc_cutoff_m_s": cutoff,
            "roc_cutoff_source": cutoff_source,
            "density_source": density_source,
            "ground": ground,
            "service": service,
            "absolute": absolute,
            "Z_plot_m": z_plot,
            "z_plot_source": z_plot_source,
        }
        if args.clmax is not None:
            result["CLmax"] = args.clmax
        if args.thrust is not None:
            result["thrust_N"] = args.thrust
        if args.power is not None:
            result["power_W"] = args.power
        if args.oat is not None:
            result["T_ground_K"] = args.oat
            result["dT_K"] = t_offset
            result["rh"] = 0.0 if args.rh is None else args.rh
            result["rh_source"] = rh_source

        out_path = Path(args.out) if args.out else SKILL_DIR / "climb_performance.png"
        out_path = out_path.resolve()
        plot_climb(out_path, plot_alts, plot_rates, cutoff, ground, service, absolute)
        emit(result, extras, notes, out_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
