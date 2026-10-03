#!/usr/bin/env python3
"""True airspeed, Mach number, dynamic pressure, and equivalent airspeed.

Mach number is mach_number. Dynamic pressure is freestream_dynamic_pressure.
Equivalent airspeed is equivalent_airspeed.
Viscosity is sutherland_viscosity. Reynolds number is reynolds_number.
State comes from ATMOS - Standard1976.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

CHECK_TOL = 1e-9

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

# 1976 Sutherland constants (formulas.md, sutherland_viscosity).
SUTHERLAND_BETA = 1.458e-6
SUTHERLAND_S = 110.4

ASSUMPTIONS = (
    "1976 U.S. Standard Atmosphere at geometric altitude Z from 0 to 86000 m "
    "supplies T, p, rho, and cs; sea-level density is that model at Z = 0; "
    "Mach number is mach_number, M = V/cs, and cs is atmosphere_sound_speed; "
    "dynamic pressure is freestream_dynamic_pressure, q = 0.5*rho*V**2; "
    "for air, dynamic_pressure_air is q/p = (7/10)*M**2; "
    "equivalent airspeed is equivalent_airspeed, Ve = V*(rho/rho_sl)**0.5, "
    "so rho*V**2 = rho_sl*Ve**2 and q = 0.5*rho_sl*Ve**2; "
    "Ve is not calibrated airspeed; "
    "viscosity is sutherland_viscosity with beta = 1.458e-6 kg/(s*m*K^0.5) "
    "and S = 110.4 K; kinematic viscosity is kinematic_viscosity, nu = mu/rho; "
    "Reynolds number is reynolds_number, Re = rho*V*L/mu; "
    "Re_per_m uses L = 1 m; an omitted --length is that one metre"
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
        from standard_1976 import (
            GAMMA,
            MEAN_MASS_WARNING,
            M0,
            RSTAR,
            Z_MEAN_MASS_NOTE,
            atmosphere,
            require_altitude,
        )
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for temperature, pressure, "
            "density, and speed of sound"
        ) from exc
    return {
        "atmosphere": atmosphere,
        "require_altitude": require_altitude,
        "gamma": GAMMA,
        "gas_constant": RSTAR / M0,
        "mean_mass_warning": MEAN_MASS_WARNING,
        "mean_mass_note_m": Z_MEAN_MASS_NOTE,
    }


def mach_number(speed: float, sound: float) -> float:
    """mach_number: M = V/cs."""
    return speed / sound


def true_airspeed(mach: float, sound: float) -> float:
    """mach_number solved for V."""
    return mach * sound


def dynamic_pressure(rho: float, speed: float) -> float:
    """freestream_dynamic_pressure."""
    return 0.5 * rho * speed * speed


def dynamic_pressure_air(mach: float, pressure: float) -> float:
    """dynamic_pressure_air: q = p * (7/10) * M**2."""
    return pressure * (7.0 / 10.0) * mach * mach


def equivalent_airspeed(speed: float, rho: float, rho_sl: float) -> float:
    """equivalent_airspeed."""
    return speed * (rho / rho_sl) ** 0.5


def sutherland_viscosity(temperature: float) -> float:
    """sutherland_viscosity with the 1976 beta and S."""
    return SUTHERLAND_BETA * temperature**1.5 / (temperature + SUTHERLAND_S)


def kinematic_viscosity(mu: float, rho: float) -> float:
    """kinematic_viscosity."""
    return mu / rho


def reynolds_number(rho: float, speed: float, length: float, mu: float) -> float:
    """reynolds_number."""
    return rho * speed * length / mu


def flight_state(
    altitude: float,
    true_speed: float | None,
    mach: float | None,
    length: float,
    atmos: dict,
) -> dict[str, float | str]:
    state = atmos["atmosphere"](altitude)
    sea = atmos["atmosphere"](0.0)
    sound = state["cs"]
    if true_speed is None:
        speed = true_airspeed(mach, sound)
        speed_source = "mach"
    else:
        speed = true_speed
        speed_source = "true_airspeed"
    mach_value = mach_number(speed, sound)
    rho = state["rho"]
    q = dynamic_pressure(rho, speed)
    rho_sl = sea["rho"]
    mu = sutherland_viscosity(state["T"])
    per_metre = reynolds_number(rho, speed, 1.0, mu)
    return {
        "speed_source": speed_source,
        "Z": state["Z"],
        "H": state["H"],
        "T": state["T"],
        "p": state["p"],
        "rho": rho,
        "cs": sound,
        "rho_sl": rho_sl,
        "rho_over_rho_sl": rho / rho_sl,
        "V": speed,
        "M": mach_value,
        "q": q,
        "q_air": dynamic_pressure_air(mach_value, state["p"]),
        "Ve": equivalent_airspeed(speed, rho, rho_sl),
        "mu": mu,
        "nu": kinematic_viscosity(mu, rho),
        "length": length,
        "Re": reynolds_number(rho, speed, length, mu),
        "Re_per_m": per_metre,
        "gamma": atmos["gamma"],
    }


def emit(result: dict, atmos: dict) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere")
    print_kv("speed_source", result["speed_source"])
    print_kv("Z_m", result["Z"])
    print_kv("H_m", result["H"])
    print_kv("T_K", result["T"])
    print_kv("p_Pa", result["p"])
    print_kv("rho_kg_m3", result["rho"])
    print_kv("cs_m_s", result["cs"])
    print_kv("rho_sl_kg_m3", result["rho_sl"])
    print_kv("rho_sl_source", "1976 sea level")
    print_kv("rho_over_rho_sl", result["rho_over_rho_sl"])
    print_kv("V_m_s", result["V"])
    print_kv("M", result["M"])
    print_kv("q_Pa", result["q"])
    print_kv("V_eas_m_s", result["Ve"])
    print_kv("mu_Pa_s", result["mu"])
    print_kv("nu_m2_s", result["nu"])
    print_kv("length_m", result["length"])
    print_kv("Re", result["Re"])
    print_kv("Re_per_m", result["Re_per_m"])
    print_kv("gamma", result["gamma"])
    if result["Z"] >= atmos["mean_mass_note_m"]:
        print_kv("warning", atmos["mean_mass_warning"])


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    def close(got: float, expected: float, label: str) -> int | None:
        scale = max(abs(expected), 1.0)
        if abs(got - expected) / scale > CHECK_TOL:
            return fail(f"{label} is {got}, expected {expected}")
        return None

    atmos = load_atmosphere()
    sea = flight_state(0.0, 100.0, None, 2.0, atmos)
    sound = math.sqrt(atmos["gamma"] * atmos["gas_constant"] * sea["T"])
    if close(sea["cs"], sound, "sea-level sound speed"):
        return 1
    if close(sea["M"], 100.0 / sound, "sea-level Mach"):
        return 1
    if close(sea["Ve"], 100.0, "sea-level equivalent airspeed"):
        return 1
    if close(sea["rho_over_rho_sl"], 1.0, "sea-level density ratio"):
        return 1
    q = 0.5 * sea["rho"] * 100.0**2
    if close(sea["q"], q, "sea-level dynamic pressure"):
        return 1
    if close(sea["q_air"], sea["q"], "dynamic_pressure_air at sea level"):
        return 1
    mu = SUTHERLAND_BETA * sea["T"] ** 1.5 / (sea["T"] + SUTHERLAND_S)
    if close(sea["mu"], mu, "sea-level Sutherland viscosity"):
        return 1
    if close(sea["nu"], mu / sea["rho"], "sea-level kinematic viscosity"):
        return 1
    if close(sea["Re_per_m"], sea["rho"] * 100.0 / mu, "unit Reynolds number"):
        return 1
    if close(sea["Re"], 2.0 * sea["Re_per_m"], "Reynolds number at 2 m"):
        return 1

    trop = atmos["atmosphere"](11000.0)
    from_mach = flight_state(11000.0, None, 0.8, 1.0, atmos)
    from_tas = flight_state(11000.0, 0.8 * trop["cs"], None, 1.0, atmos)
    if close(from_mach["V"], from_tas["V"], "Mach and true airspeed at 11 km"):
        return 1
    if close(from_mach["Ve"], from_tas["Ve"], "equivalent airspeed from either speed"):
        return 1
    if close(from_mach["M"], 0.8, "Mach at 11 km"):
        return 1
    expected_ve = math.sqrt(2.0 * from_mach["q"] / from_mach["rho_sl"])
    if close(from_mach["Ve"], expected_ve, "Ve matches dynamic pressure at sea level"):
        return 1
    if close(from_mach["q_air"], from_mach["q"], "dynamic_pressure_air at 11 km"):
        return 1
    if from_mach["Ve"] >= from_mach["V"]:
        return fail("equivalent airspeed at 11 km is not below true airspeed")
    if close(from_mach["Re"], from_mach["Re_per_m"], "unit length Reynolds number"):
        return 1

    high = flight_state(80000.0, 300.0, None, 1.0, atmos)
    if high["Z"] < atmos["mean_mass_note_m"]:
        return fail("80 km did not reach the mean-mass note")

    print("check: pass")
    print_kv("V_eas_m_s", sea["Ve"])
    print_kv("M", sea["M"])
    print_kv("Re_per_m", sea["Re_per_m"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Equivalent airspeed, Mach number, dynamic pressure, and Reynolds "
            "number from the 1976 standard atmosphere."
        )
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument("--tas", type=float, default=None, help="true airspeed V [m/s]")
    parser.add_argument("--mach", type=float, default=None, help="Mach number M")
    parser.add_argument(
        "--length",
        type=float,
        default=None,
        help="characteristic length L [m]; omitted length is 1 m",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.alt is None:
        print("error: requires --alt", file=sys.stderr)
        return 2
    if args.tas is None and args.mach is None:
        print("error: requires --tas or --mach", file=sys.stderr)
        return 2
    if args.tas is not None and args.mach is not None:
        print("error: pass --tas or --mach, not both", file=sys.stderr)
        return 2

    try:
        atmos = load_atmosphere()
        altitude = atmos["require_altitude"](args.alt, "--alt")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.tas is not None and (not math.isfinite(args.tas) or args.tas <= 0.0):
        print("error: true airspeed must be > 0 m/s", file=sys.stderr)
        return 2
    if args.mach is not None and (not math.isfinite(args.mach) or args.mach <= 0.0):
        print("error: Mach number must be > 0", file=sys.stderr)
        return 2
    length = 1.0 if args.length is None else args.length
    if not math.isfinite(length) or length <= 0.0:
        print("error: length must be > 0 m", file=sys.stderr)
        return 2

    result = flight_state(altitude, args.tas, args.mach, length, atmos)
    emit(result, atmos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
