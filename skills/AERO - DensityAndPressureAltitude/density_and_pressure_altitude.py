#!/usr/bin/env python3
"""Pressure altitude, density altitude, density, and speed of sound.

Dry density is atmosphere_density. Moist density is moist_density.
Saturation vapor pressure is saturation_vapor_pressure_water or
saturation_vapor_pressure_ice. Vapor pressure is vapor_partial_pressure.
Sound speed is atmosphere_sound_speed with the parcel molar mass.
Pressure and density altitudes invert the 1976 layer formulas.
True airspeed inverts equivalent_airspeed.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

CHECK_TOL = 1e-9

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

# NASA TN D-8401. The note's absolute temperature places the ice point at 273.
# Thermodynamic kelvin enters as T - 0.15. Pascals are 100 times the millibar value.
SAT_OFFSET_K = 0.15
FREEZE_K = 273.15
# saturation_vapor_pressure_water, T > 273.15 K.
WATER_LOG = -4.9283
WATER_INV = -2937.4
WATER_CONST = 23.5518
# saturation_vapor_pressure_ice, T <= 273.15 K.
ICE_LOG = -0.32286
ICE_INV = -2705.21
ICE_CONST = 11.4816

# U.S. Standard Atmosphere, 1976, Table 3 (formulas.md, water_molar_mass).
M_H2 = 2.01594
M_O2 = 31.9988
M_W = M_H2 + M_O2 / 2.0

ASSUMPTIONS = (
    "station pressure and outside air temperature define one parcel; "
    "an omitted relative humidity is dry air with vapor partial pressure 0; "
    "with --rh, saturation vapor pressure is saturation_vapor_pressure_water "
    "above 273.15 K and saturation_vapor_pressure_ice at and below 273.15 K "
    "from NASA TN D-8401; vapor partial pressure is vapor_partial_pressure, "
    "e = phi*es; water molar mass is water_molar_mass, "
    "Mw = M(H2) + M(O2)/2 with the 1976 Table 3 constituents; "
    "dry density is atmosphere_density at M0; moist density is moist_density; "
    "mean molar mass is M0 when --rh is omitted and moist_mean_molar_mass "
    "when --rh is set; speed of sound is atmosphere_sound_speed with "
    "gamma = 1.4 and that molar mass; "
    "pressure altitude inverts gradient_layer_pressure or "
    "isothermal_layer_pressure, and outside air temperature does not enter; "
    "density altitude inverts gradient_layer_density or "
    "isothermal_layer_density for the parcel density; "
    "layer 0 extends below H = 0 when pressure exceeds p0 or density exceeds "
    "the 1976 sea-level density; geometric altitude is geometric_altitude; "
    "the 1976 hydrostatic model ends at H = 84852 m; "
    "sea-level density for equivalent airspeed is the 1976 model at Z = 0; "
    "true airspeed inverts equivalent_airspeed; "
    "Ve is not calibrated airspeed; not the NASA Glenn three-zone fit"
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
            BASE_P,
            GAMMA,
            G0,
            H_MAX,
            LAYERS,
            M0,
            P0,
            R0,
            RSTAR,
            atmosphere,
        )
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for the 1976 layers, "
            "sea-level density, and gas constants"
        ) from exc
    edges = build_edges(LAYERS, BASE_P, G0, M0, RSTAR, H_MAX)
    sea = atmosphere(0.0)
    return {
        "layers": LAYERS,
        "base_p": BASE_P,
        "g0": G0,
        "p0": P0,
        "r0": R0,
        "m0": M0,
        "rstar": RSTAR,
        "gamma": GAMMA,
        "h_max": H_MAX,
        "edges": edges,
        "rho_sl": sea["rho"],
        "atmosphere": atmosphere,
    }


def build_edges(layers, base_p, g0, m0, rstar, h_max) -> tuple:
    """Base-to-top pressure and density of each 1976 layer, decreasing with height."""
    edges = []
    for index, (hb, lapse, tmb) in enumerate(layers):
        p_hi = base_p[index]
        rho_hi = p_hi * m0 / (rstar * tmb)
        if index + 1 < len(layers):
            h_top = layers[index + 1][0]
            t_top = layers[index + 1][2]
            p_lo = base_p[index + 1]
        else:
            h_top = h_max
            t_top = tmb + lapse * (h_top - hb)
            if lapse == 0.0:
                p_lo = p_hi * math.exp(-g0 * m0 * (h_top - hb) / (rstar * tmb))
            else:
                p_lo = p_hi * (tmb / t_top) ** (g0 * m0 / (rstar * lapse))
        rho_lo = p_lo * m0 / (rstar * t_top)
        if not (p_hi > p_lo > 0.0 and rho_hi > rho_lo > 0.0):
            raise ValueError("1976 layer edges are not decreasing")
        if edges:
            previous = edges[-1]
            if abs(previous["p_lo"] - p_hi) > 1e-9 * p_hi:
                raise ValueError("1976 pressure edges do not meet")
            if abs(previous["rho_lo"] - rho_hi) > 1e-9 * rho_hi:
                raise ValueError("1976 density edges do not meet")
        edges.append(
            {
                "index": index,
                "h_top": h_top,
                "p_hi": p_hi,
                "p_lo": p_lo,
                "rho_hi": rho_hi,
                "rho_lo": rho_lo,
            }
        )
    return tuple(edges)


def saturation_vapor_pressure(temperature: float) -> float:
    """saturation_vapor_pressure_water above freezing, else saturation_vapor_pressure_ice."""
    if not math.isfinite(temperature) or temperature <= SAT_OFFSET_K:
        raise ValueError("temperature must be above 0.15 K for saturation vapor pressure")
    theta = temperature - SAT_OFFSET_K
    if temperature > FREEZE_K:
        log_coef, inv_coef, const = WATER_LOG, WATER_INV, WATER_CONST
    else:
        log_coef, inv_coef, const = ICE_LOG, ICE_INV, ICE_CONST
    exponent = log_coef * math.log(theta) / math.log(10.0) + inv_coef / theta + const
    return 100.0 * (10.0 ** exponent)


def vapor_partial_pressure(phi: float, es: float) -> float:
    """vapor_partial_pressure: e = phi*es."""
    return phi * es


def water_molar_mass() -> float:
    """water_molar_mass: Mw = M(H2) + M(O2)/2."""
    return M_W


def atmosphere_density(pressure: float, molar_mass: float, rstar: float, temperature: float) -> float:
    """atmosphere_density: rho = p*M/(Rstar*T)."""
    return pressure * molar_mass / (rstar * temperature)


def moist_mean_molar_mass(pressure: float, vapor: float, m0: float, mw: float) -> float:
    """moist_mean_molar_mass."""
    return ((pressure - vapor) * m0 + vapor * mw) / pressure


def moist_density(
    pressure: float,
    vapor: float,
    m0: float,
    rstar: float,
    temperature: float,
    mw: float,
) -> float:
    """moist_density."""
    return (pressure - vapor) * m0 / (rstar * temperature) + vapor * mw / (rstar * temperature)


def sound_speed(gamma: float, rstar: float, temperature: float, molar_mass: float) -> float:
    """atmosphere_sound_speed with gamma = 1.4 and the parcel molar mass."""
    return math.sqrt(gamma * rstar * temperature / molar_mass)


def true_airspeed(eas: float, rho: float, rho_sl: float) -> float:
    """equivalent_airspeed solved for V."""
    return eas * math.sqrt(rho_sl / rho)


def find_layer(value: float, edges: tuple, hi_key: str, lo_key: str, message: str) -> int:
    """Layer whose base-to-top bracket contains value. Layer 0 extends below H = 0."""
    if value >= edges[0][hi_key]:
        return 0
    if value < edges[-1][lo_key]:
        raise ValueError(message)
    for edge in edges:
        if edge[lo_key] <= value <= edge[hi_key]:
            return edge["index"]
    raise ValueError(message)


def invert_layer(
    target: float,
    base: float,
    hb: float,
    lapse: float,
    tmb: float,
    g0: float,
    m0: float,
    rstar: float,
    r0: float,
    h_max: float,
    density: bool,
) -> tuple[float, float]:
    """Invert a 1976 gradient or isothermal layer. Returns geopotential H and geometric Z."""
    if lapse == 0.0:
        # isothermal_layer_pressure or isothermal_layer_density.
        height = hb + math.log(base / target) * rstar * tmb / (g0 * m0)
    else:
        # gradient_layer_pressure, or gradient_layer_density with the extra +1.
        power = g0 * m0 / (rstar * lapse)
        if density:
            power += 1.0
        if power == 0.0 or not math.isfinite(power):
            raise ValueError("layer exponent is zero")
        tm = tmb * (base / target) ** (1.0 / power)
        if not math.isfinite(tm) or tm <= 0.0:
            raise ValueError("molecular-scale temperature is not positive")
        # troposphere_temperature solved for H.
        height = hb + (tm - tmb) / lapse
    if not math.isfinite(height) or height > h_max:
        raise ValueError("geopotential altitude is above 84852 m")
    if height >= r0:
        raise ValueError("geopotential altitude is not below the Earth radius")
    # geometric_altitude.
    geometric = r0 * height / (r0 - height)
    if not math.isfinite(geometric):
        raise ValueError("geometric altitude is not finite")
    return height, geometric


def altitude_from_value(
    value: float,
    atmos: dict,
    kind: str,
) -> tuple[float, float, int]:
    density = kind == "density"
    if density:
        layer = find_layer(
            value,
            atmos["edges"],
            "rho_hi",
            "rho_lo",
            "density is below the 1976 hydrostatic model at 86 km",
        )
        base = atmos["edges"][layer]["rho_hi"]
    else:
        layer = find_layer(
            value,
            atmos["edges"],
            "p_hi",
            "p_lo",
            "pressure is below the 1976 hydrostatic model at 86 km",
        )
        base = atmos["base_p"][layer]
    hb, lapse, tmb = atmos["layers"][layer]
    height, geometric = invert_layer(
        value,
        base,
        hb,
        lapse,
        tmb,
        atmos["g0"],
        atmos["m0"],
        atmos["rstar"],
        atmos["r0"],
        atmos["h_max"],
        density,
    )
    return height, geometric, layer


def station_state(
    pressure: float,
    temperature: float,
    relative_humidity: float | None,
    eas: float | None,
    atmos: dict,
) -> dict:
    m0 = atmos["m0"]
    rstar = atmos["rstar"]
    mw = water_molar_mass()
    if relative_humidity is None:
        vapor = 0.0
        es = None
        molar = m0
        rho = atmosphere_density(pressure, m0, rstar, temperature)
        rh_source = "dry"
        rh = 0.0
    else:
        es = saturation_vapor_pressure(temperature)
        vapor = vapor_partial_pressure(relative_humidity, es)
        if not math.isfinite(vapor) or vapor >= pressure:
            raise ValueError("vapor partial pressure is not below total pressure")
        molar = moist_mean_molar_mass(pressure, vapor, m0, mw)
        rho = moist_density(pressure, vapor, m0, rstar, temperature, mw)
        rh_source = "flag"
        rh = relative_humidity
    if not math.isfinite(rho) or rho <= 0.0:
        raise ValueError("density is not positive")
    sound = sound_speed(atmos["gamma"], rstar, temperature, molar)
    if not math.isfinite(sound) or sound <= 0.0:
        raise ValueError("speed of sound is not positive")
    hp, zp, layer_p = altitude_from_value(pressure, atmos, "pressure")
    hd, zd, layer_d = altitude_from_value(rho, atmos, "density")
    speed = None
    if eas is not None:
        speed = true_airspeed(eas, rho, atmos["rho_sl"])
    return {
        "p": pressure,
        "T": temperature,
        "rh": rh,
        "rh_source": rh_source,
        "e": vapor,
        "es": es,
        "M": molar,
        "rho": rho,
        "cs": sound,
        "Hp": hp,
        "Zp": zp,
        "layer_p": layer_p,
        "Hd": hd,
        "Zd": zd,
        "layer_d": layer_d,
        "Ve": eas,
        "rho_sl": atmos["rho_sl"],
        "V": speed,
    }


def emit(result: dict) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere")
    print_kv("p_Pa", result["p"])
    print_kv("T_K", result["T"])
    print_kv("rh", result["rh"])
    print_kv("rh_source", result["rh_source"])
    if result["rh_source"] == "flag":
        print_kv("e_Pa", result["e"])
        print_kv("es_Pa", result["es"])
    print_kv("M_kg_kmol", result["M"])
    print_kv("rho_kg_m3", result["rho"])
    print_kv("cs_m_s", result["cs"])
    print_kv("Hp_m", result["Hp"])
    print_kv("Zp_m", result["Zp"])
    print_kv("layer_p", result["layer_p"])
    print_kv("Hd_m", result["Hd"])
    print_kv("Zd_m", result["Zd"])
    print_kv("layer_d", result["layer_d"])
    if result["Ve"] is not None:
        print_kv("V_eas_m_s", result["Ve"])
        print_kv("rho_sl_kg_m3", result["rho_sl"])
        print_kv("V_m_s", result["V"])


def run_check(atmos: dict) -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    def close(got: float, expected: float, label: str) -> int | None:
        scale = max(abs(expected), 1.0)
        if abs(got - expected) / scale > CHECK_TOL:
            return fail(f"{label} is {got}, expected {expected}")
        return None

    def script(temperature: float, log_coef: float, inv_coef: float, const: float) -> float:
        theta = temperature - SAT_OFFSET_K
        exponent = log_coef * math.log(theta) / math.log(10.0) + inv_coef / theta + const
        return 100.0 * (10.0 ** exponent)

    p0 = atmos["p0"]
    t0 = atmos["layers"][0][2]
    sea = station_state(p0, t0, None, None, atmos)
    rho_eos = p0 * atmos["m0"] / (atmos["rstar"] * t0)
    if close(sea["rho"], rho_eos, "sea-level dry density"):
        return 1
    if close(sea["rho"], atmos["rho_sl"], "sea-level density against the 1976 model"):
        return 1
    if abs(sea["rho"] - 1.225) > 1e-6:
        return fail(f"sea-level density {sea['rho']} is not 1.225 kg/m^3")
    sound = math.sqrt(atmos["gamma"] * atmos["rstar"] * t0 / atmos["m0"])
    if close(sea["cs"], sound, "sea-level sound speed"):
        return 1
    if abs(sea["cs"] - 340.294) > 5e-4:
        return fail(f"sea-level sound speed {sea['cs']} is not about 340.29 m/s")
    if close(sea["Zp"], 0.0, "sea-level geometric pressure altitude"):
        return 1
    if close(sea["Zd"], 0.0, "sea-level geometric density altitude"):
        return 1
    if close(sea["Hp"], 0.0, "sea-level geopotential pressure altitude"):
        return 1
    if close(sea["Hd"], 0.0, "sea-level geopotential density altitude"):
        return 1
    if sea["rh_source"] != "dry" or sea["e"] != 0.0:
        return fail("omitted relative humidity was not dry")

    level = station_state(p0, t0, None, 80.0, atmos)
    if close(level["V"], 80.0, "true airspeed at sea-level density"):
        return 1

    state_11 = atmos["atmosphere"](11000.0)
    back_11 = station_state(state_11["p"], state_11["T"], None, 100.0, atmos)
    if close(back_11["Zp"], 11000.0, "pressure altitude at 11 km"):
        return 1
    if close(back_11["Zd"], 11000.0, "density altitude at 11 km"):
        return 1
    expected_v = 100.0 * math.sqrt(atmos["rho_sl"] / back_11["rho"])
    if close(back_11["V"], expected_v, "true airspeed from equivalent airspeed at 11 km"):
        return 1
    if not back_11["V"] > back_11["Ve"]:
        return fail("true airspeed at 11 km is not above equivalent airspeed")
    warm = station_state(state_11["p"], state_11["T"] + 10.0, None, None, atmos)
    if close(warm["Hp"], back_11["Hp"], "pressure altitude ignores outside air temperature"):
        return 1
    if close(warm["Zp"], back_11["Zp"], "geometric pressure altitude ignores outside air temperature"):
        return 1
    if not warm["Hd"] > back_11["Hd"]:
        return fail("outside air temperature did not raise density altitude")

    for geopotential in (15000.0, 25000.0, 40000.0, 49000.0, 60000.0, 80000.0):
        geometric = atmos["r0"] * geopotential / (atmos["r0"] - geopotential)
        state = atmos["atmosphere"](geometric)
        back = station_state(state["p"], state["T"], None, None, atmos)
        if close(back["Zp"], geometric, f"pressure altitude at H = {geopotential:.0f} m"):
            return 1
        if close(back["Zd"], geometric, f"density altitude at H = {geopotential:.0f} m"):
            return 1

    h_top = atmos["h_max"]
    z_top = atmos["r0"] * h_top / (atmos["r0"] - h_top)
    top = atmos["atmosphere"](z_top)
    back_top = station_state(top["p"], top["T"], None, None, atmos)
    if close(back_top["Hp"], h_top, "pressure altitude at 86 km"):
        return 1
    if close(back_top["Zp"], z_top, "geometric pressure altitude at 86 km"):
        return 1

    below = station_state(p0 + 1000.0, t0, None, None, atmos)
    if not (below["Hp"] < 0.0 and below["Zp"] < 0.0):
        return fail("pressure above p0 did not extrapolate the troposphere below H = 0")
    if below["layer_p"] != 0:
        return fail("pressure above p0 was not in the troposphere layer")

    if close(script(FREEZE_K, WATER_LOG, WATER_INV, WATER_CONST), 610.8754428597153, "water script at the ice point"):
        return 1
    if close(script(FREEZE_K, ICE_LOG, ICE_INV, ICE_CONST), 610.7540964879718, "ice script at the ice point"):
        return 1
    if close(saturation_vapor_pressure(FREEZE_K), 610.7540964879718, "saturation pressure at freezing"):
        return 1
    if close(
        saturation_vapor_pressure(t0),
        script(t0, WATER_LOG, WATER_INV, WATER_CONST),
        "saturation pressure at 288.15 K",
    ):
        return 1

    wet = station_state(p0, t0, 1.0, None, atmos)
    if not wet["e"] > sea["e"]:
        return fail("saturated air did not raise the vapor pressure")
    if not wet["rho"] < sea["rho"]:
        return fail("saturated air did not lower the density")
    if not wet["Hd"] > sea["Hd"]:
        return fail("saturated air did not raise the density altitude")
    if wet["rh_source"] != "flag":
        return fail("relative humidity source was not flag")

    cold = station_state(90000.0, 260.0, 1.0, None, atmos)
    cold_dry = station_state(90000.0, 260.0, None, None, atmos)
    if not cold["e"] > 0.0 or not cold["rho"] < cold_dry["rho"]:
        return fail("ice-branch humidity did not lower the density")
    if close(cold["es"], script(260.0, ICE_LOG, ICE_INV, ICE_CONST), "saturation pressure at 260 K"):
        return 1

    try:
        station_state(1000.0, 373.15, 1.0, None, atmos)
    except ValueError as exc:
        if "vapor partial pressure" not in str(exc):
            return fail(f"e >= p raised the wrong error: {exc}")
    else:
        return fail("vapor partial pressure at or above total pressure was accepted")

    try:
        station_state(0.01, t0, None, None, atmos)
    except ValueError as exc:
        if "86 km" not in str(exc):
            return fail(f"pressure below the model raised the wrong error: {exc}")
    else:
        return fail("pressure below the 86 km model was accepted")

    if abs(water_molar_mass() - 18.01534) > 1e-9:
        return fail(f"water molar mass is {water_molar_mass()}")

    print("check: pass")
    print_kv("rho_kg_m3", sea["rho"])
    print_kv("cs_m_s", sea["cs"])
    print_kv("Zp_m", sea["Zp"])
    print_kv("Zd_m", sea["Zd"])
    print_kv("rho_moist_kg_m3", wet["rho"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pressure altitude, density altitude, density, and speed of sound "
            "from station pressure and outside air temperature."
        )
    )
    parser.add_argument("--pressure", type=float, default=None, help="station pressure p [Pa]")
    parser.add_argument("--oat", type=float, default=None, help="outside air temperature T [K]")
    parser.add_argument("--eas", type=float, default=None, help="equivalent airspeed Ve [m/s]")
    parser.add_argument(
        "--rh",
        type=float,
        default=None,
        help="relative humidity phi from 0 to 1; omitted is dry air",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        atmos = load_atmosphere()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        return run_check(atmos)

    if args.pressure is None:
        print("error: requires --pressure", file=sys.stderr)
        return 2
    if args.oat is None:
        print("error: requires --oat", file=sys.stderr)
        return 2
    if not math.isfinite(args.pressure) or args.pressure <= 0.0:
        print("error: pressure must be > 0 Pa", file=sys.stderr)
        return 2
    if not math.isfinite(args.oat) or args.oat <= 0.0:
        print("error: outside air temperature must be > 0 K", file=sys.stderr)
        return 2
    if args.eas is not None and (not math.isfinite(args.eas) or args.eas <= 0.0):
        print("error: equivalent airspeed must be > 0 m/s", file=sys.stderr)
        return 2
    if args.rh is not None and (not math.isfinite(args.rh) or args.rh < 0.0 or args.rh > 1.0):
        print("error: relative humidity must be from 0 to 1", file=sys.stderr)
        return 2

    try:
        result = station_state(args.pressure, args.oat, args.rh, args.eas, atmos)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
