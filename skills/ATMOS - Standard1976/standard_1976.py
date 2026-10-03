#!/usr/bin/env python3
"""1976 U.S. Standard Atmosphere below 86 km geometric.

Temperature, pressure, density, speed of sound, and geometric pressure
scale height from formulas.md (Atmosphere). M = M0 through 86 km.
"""

from __future__ import annotations

import argparse
import math
import sys

# 1976 U.S. Standard Atmosphere constants (formulas.md, Atmosphere).
G0 = 9.80665
P0 = 101325.0
R0 = 6.356766e6
M0 = 28.9644
RSTAR = 8.31432e3
GAMMA = 1.4
H_MAX = 84852.0
Z_MAX = 86000.0
Z_MEAN_MASS_NOTE = 80000.0

# Geopotential bases in metres, lapse in K/m, base molecular-scale temperature in K.
# Layer b runs from Hb[b] to the next base. The last layer ends at H_MAX.
LAYERS = (
    (0.0, -6.5e-3, 288.15),
    (11000.0, 0.0, 216.65),
    (20000.0, 1.0e-3, 216.65),
    (32000.0, 2.8e-3, 228.65),
    (47000.0, 0.0, 270.65),
    (51000.0, -2.8e-3, 270.65),
    (71000.0, -2.0e-3, 214.65),
)

ASSUMPTIONS = (
    "1976 U.S. Standard Atmosphere hydrostatic model at geometric altitude Z "
    "from 0 to 86000 m; geopotential altitude H = r0*Z/(r0+Z) with "
    "r0 = 6356766 m; seven constant-lapse molecular-scale layers through "
    "H = 84852 m; M = M0 = 28.9644 kg/kmol, so kinetic temperature equals "
    "molecular-scale temperature; pressure from gradient_layer_pressure or "
    "isothermal_layer_pressure; density from atmosphere_density_molecular; "
    "speed of sound from atmosphere_sound_speed with gamma = 1.4; geometric "
    "pressure scale height Hp = Rstar*T/(g*M0) from pressure_scale_height, "
    "with g = g0*(r0/(r0+Z))**2 and g0 = 9.80665 m/s^2; not the NASA Glenn "
    "three-zone fit; the hydrostatic model ends at 86 km"
)

MEAN_MASS_WARNING = (
    "above 80 km the 1976 model lets M/M0 fall slightly below 1; this "
    "program keeps M = M0 through 86 km, so temperature, density, sound "
    "speed, and scale height omit that correction"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def build_base_pressures() -> tuple[float, ...]:
    """Pressure at each layer base, starting from p0 and the layer integrals."""
    bases = [P0]
    pressure = P0
    for i, (hb, lapse, temp) in enumerate(LAYERS[:-1]):
        h_top = LAYERS[i + 1][0]
        t_top = temp + lapse * (h_top - hb)
        if lapse == 0.0:
            pressure = pressure * math.exp(-G0 * M0 * (h_top - hb) / (RSTAR * temp))
        else:
            pressure = pressure * (temp / t_top) ** (G0 * M0 / (RSTAR * lapse))
        bases.append(pressure)
    return tuple(bases)


BASE_P = build_base_pressures()


def require_altitude(value: float, flag: str) -> float:
    if not math.isfinite(value) or value < 0.0 or value > Z_MAX:
        raise ValueError(
            f"{flag} must be from 0 to 86000 m geometric; "
            "the 1976 hydrostatic model ends at 86 km"
        )
    return value


def geopotential_altitude(z_m: float) -> float:
    """H = r0*Z/(r0+Z). H is limited to the hydrostatic top at 84852 m."""
    h_m = R0 * z_m / (R0 + z_m)
    if h_m > H_MAX:
        return H_MAX
    return h_m


def gravity(z_m: float) -> float:
    """g = g0*(r0/(r0+Z))**2."""
    return G0 * (R0 / (R0 + z_m)) ** 2


def layer_index(h_m: float) -> int:
    for index in range(len(LAYERS) - 1, -1, -1):
        if h_m >= LAYERS[index][0]:
            return index
    return 0


def atmosphere(z_m: float) -> dict:
    """1976 temperature, pressure, density, sound speed, and scale height."""
    h_m = geopotential_altitude(z_m)
    index = layer_index(h_m)
    hb, lapse, temp_b = LAYERS[index]
    pressure_b = BASE_P[index]
    temp = temp_b if lapse == 0.0 else temp_b + lapse * (h_m - hb)
    if temp <= 0.0:
        raise ValueError("molecular-scale temperature is not positive")
    if lapse == 0.0:
        pressure = pressure_b * math.exp(-G0 * M0 * (h_m - hb) / (RSTAR * temp_b))
    else:
        pressure = pressure_b * (temp_b / temp) ** (G0 * M0 / (RSTAR * lapse))
    if not math.isfinite(pressure) or pressure <= 0.0:
        raise ValueError("pressure is not positive")
    density = pressure * M0 / (RSTAR * temp)
    sound = math.sqrt(GAMMA * RSTAR * temp / M0)
    g_local = gravity(z_m)
    scale = RSTAR * temp / (g_local * M0)
    if not all(math.isfinite(item) and item > 0.0 for item in (density, sound, scale)):
        raise ValueError("density, sound speed, or scale height is not positive")
    return {
        "Z": z_m,
        "H": h_m,
        "layer": index,
        "layer_Hb": hb,
        "T": temp,
        "p": pressure,
        "rho": density,
        "cs": sound,
        "Hp": scale,
        "g": g_local,
    }


def emit(state: dict) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere")
    print_kv("Z_m", state["Z"])
    print_kv("H_m", state["H"])
    print_kv("layer_b", state["layer"])
    print_kv("layer_Hb_m", state["layer_Hb"])
    print_kv("T_K", state["T"])
    print_kv("p_Pa", state["p"])
    print_kv("rho_kg_m3", state["rho"])
    print_kv("cs_m_s", state["cs"])
    print_kv("Hp_m", state["Hp"])
    print_kv("gamma", GAMMA)
    if state["Z"] >= Z_MEAN_MASS_NOTE:
        print_kv("warning", MEAN_MASS_WARNING)


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    def close(got: float, expected: float, label: str, tol: float = 1e-9) -> int | None:
        if expected == 0.0:
            if abs(got) > tol:
                return fail(f"{label} is {got}, expected {expected}")
            return None
        if abs(got - expected) / abs(expected) > tol:
            return fail(f"{label} is {got}, expected {expected}")
        return None

    sea = atmosphere(0.0)
    if close(sea["p"], P0, "sea-level pressure", 1e-12):
        return 1
    if close(sea["H"], 0.0, "sea-level geopotential", 1e-12):
        return 1
    if close(sea["T"], 288.15, "sea-level temperature", 1e-12):
        return 1
    if close(sea["g"], G0, "sea-level gravity", 1e-12):
        return 1
    if abs(sea["rho"] - 1.2250) > 1e-6:
        return fail(f"sea-level density {sea['rho']} is not the adopted 1.2250 kg/m^3")
    if abs(sea["cs"] - 340.294) > 5e-4:
        return fail(f"sea-level sound speed {sea['cs']} is not 340.294 m/s")
    if abs(sea["Hp"] - 8434.51563075685) > 1e-6:
        return fail(f"sea-level scale height is {sea['Hp']}")

    # Pressures at geopotential layer bases, same anchors as ExpansionMatchEarth.
    published = (
        (11000.0, 216.65, 22632.06),
        (20000.0, 216.65, 5474.889),
        (32000.0, 228.65, 868.019),
        (47000.0, 270.65, 110.906),
        (51000.0, 270.65, 66.9389),
        (71000.0, 214.65, 3.95642),
        (84852.0, 186.946, 0.373384),
    )
    for h_m, temp, expected_p in published:
        z_m = R0 * h_m / (R0 - h_m)
        state = atmosphere(z_m)
        if abs(state["H"] - h_m) > 1e-6:
            return fail(f"H({z_m}) = {state['H']}, expected {h_m}")
        if abs(state["T"] - temp) > 1e-6:
            return fail(f"temperature at H={h_m} is {state['T']}, expected {temp}")
        if abs(state["p"] - expected_p) / expected_p > 5e-6:
            return fail(f"pressure at H={h_m} is {state['p']}, expected about {expected_p}")
        if abs(state["rho"] - state["p"] * M0 / (RSTAR * state["T"])) > 1e-12 * state["rho"]:
            return fail(f"density at H={h_m} left the equation of state")
        sound_sq = GAMMA * RSTAR * state["T"] / M0
        if abs(state["cs"] ** 2 - sound_sq) > 1e-9 * sound_sq:
            return fail(f"sound speed at H={h_m} left atmosphere_sound_speed")
        scale = RSTAR * state["T"] / (state["g"] * M0)
        if abs(state["Hp"] - scale) > 1e-9 * scale:
            return fail(f"scale height at H={h_m} left pressure_scale_height")

    five = atmosphere(5000.0)
    if close(five["T"], 255.67554322180348, "5 km temperature"):
        return 1
    if close(five["p"], 54048.28614576141, "5 km pressure"):
        return 1
    if close(five["rho"], 0.7364284207799744, "5 km density"):
        return 1
    if close(five["cs"], 320.5455196704035, "5 km sound speed"):
        return 1
    if close(five["Hp"], 7495.724959898328, "5 km scale height"):
        return 1
    if five["layer"] != 0:
        return fail("5 km is not in the troposphere layer")

    iso_z = R0 * 15000.0 / (R0 - 15000.0)
    iso = atmosphere(iso_z)
    if iso["layer"] != 1 or abs(iso["T"] - 216.65) > 1e-9:
        return fail("15 km geopotential is not the 216.65 K isothermal layer")
    if close(iso["p"], 12044.570862423197, "15 km pressure"):
        return 1
    if not iso["Hp"] < five["Hp"] < sea["Hp"]:
        return fail("scale height did not fall from sea level to 15 km")

    top = atmosphere(Z_MAX)
    if abs(top["H"] - H_MAX) > 1e-6:
        return fail(f"86 km geopotential clamped to {top['H']}")
    if abs(top["T"] - 186.946) > 1e-6:
        return fail(f"temperature at 86 km is {top['T']}")
    if close(top["p"], 0.3733835899762159, "86 km pressure"):
        return 1

    try:
        require_altitude(Z_MAX + 1.0, "--alt")
    except ValueError:
        pass
    else:
        return fail("altitude above 86 km was accepted")
    try:
        require_altitude(-1.0, "--alt")
    except ValueError:
        pass
    else:
        return fail("altitude below sea level was accepted")

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
        return fail(f"sea-level main returned {code}")
    for key in ("T_K: 288.15", "p_Pa: 101325", "rho_kg_m3:", "cs_m_s:", "Hp_m:"):
        if key not in text:
            return fail(f"sea-level stdout missing {key}")
    if "warning:" in text:
        return fail("sea level printed the mean-mass warning")

    code, text = capture(["--alt", "86000"])
    if code != 0 or "warning:" not in text:
        return fail("86 km did not print the mean-mass warning")

    err = sys.stderr
    sys.stderr = _Capture()
    try:
        missing = main([])
    finally:
        sys.stderr = err
    if missing != 2:
        return fail("missing altitude was accepted")

    print("check: pass")
    print_kv("T_K", sea["T"])
    print_kv("p_Pa", sea["p"])
    print_kv("rho_kg_m3", sea["rho"])
    print_kv("cs_m_s", sea["cs"])
    print_kv("Hp_m", sea["Hp"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="1976 U.S. Standard Atmosphere at a geometric altitude."
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.alt is None:
        print("error: requires --alt", file=sys.stderr)
        return 2
    try:
        state = atmosphere(require_altitude(args.alt, "--alt"))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
