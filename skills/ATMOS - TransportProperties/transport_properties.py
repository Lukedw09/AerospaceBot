#!/usr/bin/env python3
"""1976 dry-air transport properties at altitude or temperature.

Dynamic viscosity is sutherland_viscosity. Thermal conductivity is
thermal_conductivity_air. Mean particle speed is mean_particle_speed.
With density (altitude, or temperature plus pressure): kinematic_viscosity,
mean_free_path, collision_frequency, number_density, and atmosphere_density.
Altitude state comes from ATMOS - Standard1976.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

CHECK_TOL = 1e-9

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

# 1976 U.S. Standard Atmosphere constants (formulas.md, Atmosphere).
M0 = 28.9644
RSTAR = 8.31432e3
KB = 1.380622e-23
NA = 6.022169e26
SIGMA = 3.65e-10
SUTHERLAND_BETA = 1.458e-6
SUTHERLAND_S = 110.4
K0 = 2.64638e-3
C_COND = 245.4

ASSUMPTIONS = (
    "dry air, continuum; dynamic viscosity is sutherland_viscosity with "
    "beta = 1.458e-6 kg/(s*m*K^0.5) and S = 110.4 K; thermal conductivity "
    "is thermal_conductivity_air with k0 = 2.64638e-3 W/(m*K^1.5) and "
    "C = 245.4 K; mean particle speed is mean_particle_speed at M = M0 = "
    "28.9644 kg/kmol and Rstar = 8.31432e3 N*m/(kmol*K); viscosity and "
    "conductivity are the 1976 fits tabulated to 86 km; "
    "altitude mode takes T, p, and rho from ATMOS - Standard1976 at "
    "geometric Z from 0 to 86000 m, with M = M0 through 86 km; "
    "temperature-plus-pressure mode uses atmosphere_density at M0; "
    "when density is known, kinematic viscosity is kinematic_viscosity, "
    "mean free path is mean_free_path with sigma = 3.65e-10 m, collision "
    "frequency is collision_frequency, and number density is number_density "
    "with k = 1.380622e-23 J/K; sigma is a sea-level dry-air value"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_atmosphere() -> dict:
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import (
            MEAN_MASS_WARNING,
            Z_MEAN_MASS_NOTE,
            atmosphere,
            require_altitude,
        )
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for altitude-mode "
            "temperature, pressure, and density"
        ) from exc
    return {
        "atmosphere": atmosphere,
        "require_altitude": require_altitude,
        "mean_mass_warning": MEAN_MASS_WARNING,
        "mean_mass_note_m": Z_MEAN_MASS_NOTE,
    }


def require_temperature(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be > 0 K")
    return value


def require_pressure(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be > 0 Pa")
    return value


def sutherland_viscosity(temperature: float) -> float:
    """sutherland_viscosity with the 1976 beta and S."""
    return SUTHERLAND_BETA * temperature**1.5 / (temperature + SUTHERLAND_S)


def thermal_conductivity_air(temperature: float) -> float:
    """thermal_conductivity_air with the 1976 k0 and C."""
    return K0 * temperature**1.5 / (
        temperature + C_COND * 10.0 ** (-12.0 / temperature)
    )


def mean_particle_speed(temperature: float) -> float:
    """mean_particle_speed at M = M0."""
    return math.sqrt(8.0 * RSTAR * temperature / (math.pi * M0))


def atmosphere_density(pressure: float, temperature: float) -> float:
    """atmosphere_density at M = M0."""
    return pressure * M0 / (RSTAR * temperature)


def kinematic_viscosity(mu: float, rho: float) -> float:
    """kinematic_viscosity."""
    return mu / rho


def mean_free_path(temperature: float, pressure: float) -> float:
    """mean_free_path with the 1976 collision diameter."""
    return RSTAR * temperature / (
        math.sqrt(2.0) * math.pi * SIGMA**2 * NA * pressure
    )


def collision_frequency(speed: float, path: float) -> float:
    """collision_frequency."""
    return speed / path


def number_density(pressure: float, temperature: float) -> float:
    """number_density."""
    return pressure / (KB * temperature)


def transport_from_temperature(temperature: float) -> dict:
    mu = sutherland_viscosity(temperature)
    conductivity = thermal_conductivity_air(temperature)
    speed = mean_particle_speed(temperature)
    if not all(
        math.isfinite(item) and item > 0.0 for item in (mu, conductivity, speed)
    ):
        raise ValueError(
            "dynamic viscosity, thermal conductivity, or mean particle speed "
            "is not positive"
        )
    return {
        "T": temperature,
        "mu": mu,
        "kt": conductivity,
        "Vbar": speed,
    }


def attach_density_quantities(
    result: dict, pressure: float, density: float
) -> dict:
    if not math.isfinite(pressure) or pressure <= 0.0:
        raise ValueError("pressure is not positive")
    if not math.isfinite(density) or density <= 0.0:
        raise ValueError("density is not positive")
    path = mean_free_path(result["T"], pressure)
    nu = kinematic_viscosity(result["mu"], density)
    collisions = collision_frequency(result["Vbar"], path)
    number = number_density(pressure, result["T"])
    if not all(
        math.isfinite(item) and item > 0.0
        for item in (nu, path, collisions, number)
    ):
        raise ValueError(
            "kinematic viscosity, mean free path, collision frequency, "
            "or number density is not positive"
        )
    result["p"] = pressure
    result["rho"] = density
    result["nu"] = nu
    result["L"] = path
    result["nu_c"] = collisions
    result["N"] = number
    return result


def from_altitude(z_m: float, atmos: dict) -> dict:
    state = atmos["atmosphere"](z_m)
    result = transport_from_temperature(state["T"])
    attach_density_quantities(result, state["p"], state["rho"])
    result["mode"] = "altitude"
    result["Z"] = state["Z"]
    result["H"] = state["H"]
    return result


def from_temperature(
    temperature: float, pressure: float | None
) -> dict:
    result = transport_from_temperature(temperature)
    if pressure is None:
        result["mode"] = "temperature"
        return result
    density = atmosphere_density(pressure, temperature)
    attach_density_quantities(result, pressure, density)
    result["mode"] = "temperature_pressure"
    return result


def emit(result: dict, atmos: dict | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere transport")
    print_kv("input_mode", result["mode"])
    if result["mode"] == "altitude":
        print_kv("Z_m", result["Z"])
        print_kv("H_m", result["H"])
    print_kv("T_K", result["T"])
    print_kv("mu_Pa_s", result["mu"])
    print_kv("kt_W_mK", result["kt"])
    print_kv("Vbar_m_s", result["Vbar"])
    if "rho" in result:
        print_kv("p_Pa", result["p"])
        print_kv("rho_kg_m3", result["rho"])
        print_kv("nu_m2_s", result["nu"])
        print_kv("L_m", result["L"])
        print_kv("nu_c_s", result["nu_c"])
        print_kv("N_m3", result["N"])
        print_kv("M_kg_kmol", M0)
        print_kv("sigma_m", SIGMA)
    if (
        result["mode"] == "altitude"
        and atmos is not None
        and result["Z"] >= atmos["mean_mass_note_m"]
    ):
        print_kv("warning", atmos["mean_mass_warning"])


def run_check() -> int:
    def fail(message: str) -> None:
        print(f"CHECK FAIL: {message}", file=sys.stderr)

    def close(got: float, expected: float, label: str) -> bool:
        scale = max(abs(expected), 1.0)
        if abs(got - expected) / scale > CHECK_TOL:
            fail(f"{label} is {got}, expected {expected}")
            return True
        return False

    atmos = load_atmosphere()
    sea = from_altitude(0.0, atmos)
    if close(sea["T"], 288.15, "sea-level temperature"):
        return 1
    mu = SUTHERLAND_BETA * 288.15**1.5 / (288.15 + SUTHERLAND_S)
    if close(sea["mu"], mu, "sea-level Sutherland viscosity"):
        return 1
    kt = K0 * 288.15**1.5 / (288.15 + C_COND * 10.0 ** (-12.0 / 288.15))
    if close(sea["kt"], kt, "sea-level thermal conductivity"):
        return 1
    speed = math.sqrt(8.0 * RSTAR * 288.15 / (math.pi * M0))
    if close(sea["Vbar"], speed, "sea-level mean particle speed"):
        return 1
    if close(sea["nu"], mu / sea["rho"], "sea-level kinematic viscosity"):
        return 1
    path = RSTAR * 288.15 / (math.sqrt(2.0) * math.pi * SIGMA**2 * NA * sea["p"])
    if close(sea["L"], path, "sea-level mean free path"):
        return 1
    if close(sea["nu_c"], speed / path, "sea-level collision frequency"):
        return 1
    if close(sea["N"], sea["p"] / (KB * 288.15), "sea-level number density"):
        return 1
    if abs(sea["rho"] - 1.2250) > 1e-6:
        fail(f"sea-level density {sea['rho']} is not the adopted 1.2250 kg/m^3")
        return 1

    trop = from_altitude(11000.0, atmos)
    if trop["T"] >= sea["T"] or trop["mu"] >= sea["mu"]:
        fail("11 km viscosity did not fall with temperature")
        return 1
    if trop["L"] <= sea["L"]:
        fail("11 km mean free path did not rise")
        return 1

    high = from_altitude(80000.0, atmos)
    if high["Z"] < atmos["mean_mass_note_m"]:
        fail("80 km did not reach the mean-mass note")
        return 1

    temp_only = from_temperature(288.15, None)
    if "rho" in temp_only:
        fail("temperature-only mode printed density quantities")
        return 1
    if close(temp_only["mu"], sea["mu"], "temperature-only viscosity"):
        return 1
    if close(temp_only["kt"], sea["kt"], "temperature-only conductivity"):
        return 1
    if close(temp_only["Vbar"], sea["Vbar"], "temperature-only mean speed"):
        return 1

    with_p = from_temperature(288.15, 101325.0)
    if close(with_p["rho"], sea["rho"], "T+p sea-level density"):
        return 1
    if close(with_p["L"], sea["L"], "T+p sea-level mean free path"):
        return 1
    if close(with_p["N"], sea["N"], "T+p sea-level number density"):
        return 1

    ident_mu = sutherland_viscosity(400.0)
    if close(ident_mu, SUTHERLAND_BETA * 8000.0 / 510.4, "Sutherland identity T=400 K"):
        return 1
    ident_kt = thermal_conductivity_air(12.0)
    expected_kt = K0 * 12.0**1.5 / (12.0 + C_COND * 10.0 ** (-1.0))
    if close(ident_kt, expected_kt, "conductivity identity T=12 K"):
        return 1
    ident_speed = mean_particle_speed(math.pi * M0 / 8.0)
    if close(ident_speed, math.sqrt(RSTAR), "mean speed identity"):
        return 1

    try:
        require_temperature(0.0, "--temp")
    except ValueError:
        pass
    else:
        fail("non-positive temperature was accepted")
        return 1
    try:
        require_pressure(-1.0, "--pressure")
    except ValueError:
        pass
    else:
        fail("non-positive pressure was accepted")
        return 1

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str]:
        sink = _Capture()
        old_out = sys.stdout
        sys.stdout = sink
        try:
            code = main(argv)
        finally:
            sys.stdout = old_out
        return code, "".join(sink.parts)

    code, text = capture(["--alt", "0"])
    if code != 0:
        fail(f"sea-level main returned {code}")
        return 1
    for key in (
        "input_mode: altitude",
        "T_K: 288.15",
        "mu_Pa_s:",
        "kt_W_mK:",
        "Vbar_m_s:",
        "p_Pa:",
        "rho_kg_m3:",
        "nu_m2_s:",
        "L_m:",
        "nu_c_s:",
        "N_m3:",
        "Z_m:",
        "H_m:",
    ):
        if key not in text:
            fail(f"sea-level stdout missing {key}")
            return 1
    if "warning:" in text:
        fail("sea level printed the mean-mass warning")
        return 1

    code, text = capture(["--alt", "86000"])
    if code != 0 or "warning:" not in text:
        fail("86 km did not print the mean-mass warning")
        return 1

    code, text = capture(["--temp", "288.15"])
    if code != 0:
        fail(f"temperature-only main returned {code}")
        return 1
    if "input_mode: temperature" not in text:
        fail("temperature-only stdout missing input_mode")
        return 1
    if "p_Pa:" in text or "rho_kg_m3:" in text or "Z_m:" in text:
        fail("temperature-only stdout included density or altitude keys")
        return 1

    code, text = capture(["--temp", "288.15", "--pressure", "101325"])
    if code != 0 or "input_mode: temperature_pressure" not in text:
        fail("temperature-plus-pressure stdout was wrong")
        return 1
    if "Z_m:" in text:
        fail("temperature-plus-pressure printed geometric altitude")
        return 1
    if "N_m3:" not in text:
        fail("temperature-plus-pressure omitted number density")
        return 1

    err = sys.stderr
    sys.stderr = _Capture()
    try:
        missing = main([])
        both = main(["--alt", "0", "--temp", "288.15"])
        pressure_only = main(["--pressure", "101325"])
    finally:
        sys.stderr = err
    if missing != 2:
        fail("missing input was accepted")
        return 1
    if both != 2:
        fail("altitude and temperature together were accepted")
        return 1
    if pressure_only != 2:
        fail("pressure without temperature was accepted")
        return 1

    print("check: pass")
    print_kv("T_K", sea["T"])
    print_kv("mu_Pa_s", sea["mu"])
    print_kv("kt_W_mK", sea["kt"])
    print_kv("Vbar_m_s", sea["Vbar"])
    print_kv("nu_m2_s", sea["nu"])
    print_kv("L_m", sea["L"])
    print_kv("N_m3", sea["N"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "1976 dry-air viscosity, conductivity, and kinetic-theory lengths "
            "from geometric altitude or temperature."
        )
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument("--temp", type=float, default=None, help="kinetic temperature T [K]")
    parser.add_argument(
        "--pressure",
        type=float,
        default=None,
        help="pressure p [Pa]; with --temp, enables density-dependent outputs",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.alt is not None and args.temp is not None:
        print("error: pass --alt or --temp, not both", file=sys.stderr)
        return 2
    if args.alt is None and args.temp is None:
        print("error: requires --alt or --temp", file=sys.stderr)
        return 2
    if args.alt is not None and args.pressure is not None:
        print("error: --pressure is for --temp only; altitude supplies pressure", file=sys.stderr)
        return 2
    if args.temp is None and args.pressure is not None:
        print("error: --pressure requires --temp", file=sys.stderr)
        return 2

    try:
        if args.alt is not None:
            atmos = load_atmosphere()
            result = from_altitude(atmos["require_altitude"](args.alt, "--alt"), atmos)
            emit(result, atmos)
            return 0
        temperature = require_temperature(args.temp, "--temp")
        pressure = (
            None
            if args.pressure is None
            else require_pressure(args.pressure, "--pressure")
        )
        result = from_temperature(temperature, pressure)
        emit(result, None)
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
