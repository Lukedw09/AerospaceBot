#!/usr/bin/env python3
"""Level-flight speeds and a sea-level climb estimate from a parabolic drag polar.

The polar is drag_polar with induced_drag_coefficient. Speeds are the
level-flight form of stall_speed. Lift-to-drag is lift_to_drag. Dynamic
pressure is freestream_dynamic_pressure. Sea-level density is the 1976
standard atmosphere at zero geometric altitude.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

CHECK_TOL = 1e-8
# Lift equals weight is a coarse climb model once the angle is this steep.
CLIMB_WARN_RAD = math.radians(10.0)
# The incompressible polar is the checked model. Faster flight is reported and flagged.
MACH_WARN = 0.3

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "steady unaccelerated flight; parabolic polar CD = CD0 + CL**2/(pi*AR*e) "
    "from drag_polar and induced_drag_coefficient; 0 < e <= 1; "
    "L/D = CL/CD from lift_to_drag; level flight L = W so "
    "V = sqrt(2*W/(rho*S*CL)) from stall_speed and freestream_dynamic_pressure; "
    "incompressible; (L/D)max when parasite drag equals induced drag, "
    "CL = sqrt(CD0*pi*AR*e) and CD = 2*CD0; "
    "jet thrust independent of speed and fuel flow proportional to thrust: "
    "best endurance is (L/D)max, best range maximizes V*L/D at CL = sqrt(CD0/(3*k)); "
    "propeller useful power independent of speed and fuel flow proportional to "
    "power: best range is (L/D)max, best endurance minimizes power at "
    "CL = sqrt(3*CD0/k); k = 1/(pi*AR*e); "
    "flight density is the 1976 atmosphere at --alt, or the supplied --rho; "
    "the climb estimate always uses 1976 sea-level density; "
    "jet steepest climb is at minimum drag, sin(gamma) = (T-D)/W with L = W; "
    "jet best rate of climb maximizes V*(T-D) with that same drag law; "
    "--power is useful power delivered to the airplane, not shaft power; "
    "propeller best rate of climb is at minimum power, roc = (P-D*V)/W; "
    "a negative rate is a descent; g0 = 9.80665 m/s^2 is not used because weight is a force"
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
        from standard_1976 import atmosphere, require_altitude
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for density and the sea-level climb"
        ) from exc
    return atmosphere, require_altitude


def induced_factor(aspect_ratio: float, oswald: float) -> float:
    return 1.0 / (math.pi * aspect_ratio * oswald)


def polar_points(cd0: float, aspect_ratio: float, oswald: float) -> dict[str, float]:
    """Three lift coefficients on CD = CD0 + k CL^2, and (L/D)max."""
    k = induced_factor(aspect_ratio, oswald)
    cl_ld = math.sqrt(cd0 / k)
    cl_range_jet = math.sqrt(cd0 / (3.0 * k))
    cl_endurance_prop = math.sqrt(3.0 * cd0 / k)
    cd_ld = 2.0 * cd0
    return {
        "k": k,
        "CL_LDmax": cl_ld,
        "CD_LDmax": cd_ld,
        "LD_max": cl_ld / cd_ld,
        "CL_range_jet": cl_range_jet,
        "CD_range_jet": cd0 + k * cl_range_jet**2,
        "CL_endurance_prop": cl_endurance_prop,
        "CD_endurance_prop": cd0 + k * cl_endurance_prop**2,
    }


def level_speed(weight: float, rho: float, area: float, cl: float) -> float:
    return math.sqrt(2.0 * weight / (rho * area * cl))


def level_drag(weight: float, cd: float, cl: float) -> float:
    return weight * cd / cl


def jet_best_rate(
    weight: float,
    rho: float,
    area: float,
    cd0: float,
    k: float,
    thrust: float,
) -> tuple[float, float, float]:
    """Speed, drag, and climb rate for constant thrust. Returns m/s, N, m/s."""
    parasite = 0.5 * rho * area * cd0
    induced = 2.0 * k * weight**2 / (rho * area)
    disc = thrust**2 + 12.0 * parasite * induced
    speed_sq = (thrust + math.sqrt(disc)) / (6.0 * parasite)
    speed = math.sqrt(speed_sq)
    drag = parasite * speed_sq + induced / speed_sq
    rate = speed * (thrust - drag) / weight
    return speed, drag, rate


def climb_angle(sin_gamma: float) -> float | None:
    if abs(sin_gamma) <= 1.0:
        return math.asin(sin_gamma)
    return None


def performance(
    weight: float,
    area: float,
    cd0: float,
    aspect_ratio: float,
    oswald: float,
    clmax: float,
    rho: float,
    rho_sl: float,
    thrust: float | None,
    power: float | None,
) -> dict[str, float]:
    points = polar_points(cd0, aspect_ratio, oswald)
    k = points["k"]
    out: dict[str, float] = dict(points)
    out["V_stall_m_s"] = level_speed(weight, rho, area, clmax)
    out["V_stall_sl_m_s"] = level_speed(weight, rho_sl, area, clmax)
    out["V_range_jet_m_s"] = level_speed(weight, rho, area, points["CL_range_jet"])
    out["V_endurance_jet_m_s"] = level_speed(weight, rho, area, points["CL_LDmax"])
    out["V_range_prop_m_s"] = out["V_endurance_jet_m_s"]
    out["V_endurance_prop_m_s"] = level_speed(
        weight, rho, area, points["CL_endurance_prop"]
    )
    out["V_climb_angle_sl_m_s"] = level_speed(weight, rho_sl, area, points["CL_LDmax"])
    out["thrust_level_min_sl_N"] = weight / points["LD_max"]
    out["V_climb_rate_prop_sl_m_s"] = level_speed(
        weight, rho_sl, area, points["CL_endurance_prop"]
    )
    drag_min_power = level_drag(
        weight, points["CD_endurance_prop"], points["CL_endurance_prop"]
    )
    out["power_level_min_sl_W"] = drag_min_power * out["V_climb_rate_prop_sl_m_s"]
    if thrust is not None:
        speed, drag, rate = jet_best_rate(weight, rho_sl, area, cd0, k, thrust)
        out["V_climb_rate_jet_sl_m_s"] = speed
        out["drag_at_jet_roc_sl_N"] = drag
        out["roc_jet_m_s"] = rate
        out["sin_gamma_jet_roc"] = rate / speed
        out["sin_gamma_max_angle"] = (thrust - out["thrust_level_min_sl_N"]) / weight
        out["roc_at_max_angle_m_s"] = (
            out["V_climb_angle_sl_m_s"] * out["sin_gamma_max_angle"]
        )
    if power is not None:
        excess = power - out["power_level_min_sl_W"]
        out["roc_prop_m_s"] = excess / weight
        out["sin_gamma_prop"] = excess / (weight * out["V_climb_rate_prop_sl_m_s"])
    return out


def warnings_for(
    clmax: float,
    points: dict[str, float],
    sound_speed: float | None,
    sound_speed_sl: float,
) -> list[str]:
    notes: list[str] = []
    schedules = (
        ("jet best range", points["CL_range_jet"], points["V_range_jet_m_s"]),
        ("jet best endurance", points["CL_LDmax"], points["V_endurance_jet_m_s"]),
        ("propeller best range", points["CL_LDmax"], points["V_range_prop_m_s"]),
        (
            "propeller best endurance",
            points["CL_endurance_prop"],
            points["V_endurance_prop_m_s"],
        ),
    )
    for label, cl, _speed in schedules:
        if cl > clmax:
            notes.append(
                f"{label} needs CL {cl:.6g}, above CLmax {clmax:.6g}; "
                "that speed is below stall"
            )
    if sound_speed is not None and sound_speed > 0.0:
        fastest = points["V_range_jet_m_s"]
        mach = fastest / sound_speed
        if mach > MACH_WARN:
            notes.append(
                f"incompressible polar at jet best-range Mach {mach:.6g}; "
                f"the checked model is used above Mach {MACH_WARN}"
            )
    climb_checks = (
        ("jet steepest-climb", points["V_climb_angle_sl_m_s"]),
        ("propeller best-rate", points["V_climb_rate_prop_sl_m_s"]),
    )
    if "V_climb_rate_jet_sl_m_s" in points:
        climb_checks = climb_checks + (
            ("jet best-rate", points["V_climb_rate_jet_sl_m_s"]),
        )
    for label, speed in climb_checks:
        if speed < points["V_stall_sl_m_s"]:
            notes.append(f"sea-level {label} speed is below sea-level stall")
        mach = speed / sound_speed_sl
        if mach > MACH_WARN:
            notes.append(
                f"incompressible polar at sea-level {label} Mach {mach:.6g}"
            )
    for key, label in (
        ("sin_gamma_max_angle", "jet steepest climb"),
        ("sin_gamma_jet_roc", "jet best rate of climb"),
        ("sin_gamma_prop", "propeller best rate of climb"),
    ):
        if key not in points:
            continue
        sine = points[key]
        if abs(sine) > 1.0:
            notes.append(f"{label} has no real angle on the L = W model")
        elif abs(math.asin(sine)) > CLIMB_WARN_RAD:
            notes.append(
                f"{label} is steeper than 10 degrees; induced drag still uses L = W"
            )
    return notes


def emit(
    weight: float,
    area: float,
    cd0: float,
    aspect_ratio: float,
    oswald: float,
    clmax: float,
    density_source: str,
    altitude: float | None,
    rho: float,
    sound_speed: float | None,
    rho_sl: float,
    sound_speed_sl: float,
    thrust: float | None,
    power: float | None,
    result: dict[str, float],
    notes: list[str],
) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("density_source", density_source)
    print_kv("weight_N", weight)
    print_kv("area_m2", area)
    print_kv("CD0", cd0)
    print_kv("AR", aspect_ratio)
    print_kv("e", oswald)
    print_kv("k", result["k"])
    print_kv("CLmax", clmax)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("rho_kg_m3", rho)
    if sound_speed is not None:
        print_kv("cs_m_s", sound_speed)
    print_kv("rho_sl_kg_m3", rho_sl)
    print_kv("cs_sl_m_s", sound_speed_sl)
    print_kv("LD_max", result["LD_max"])
    print_kv("CL_LDmax", result["CL_LDmax"])
    print_kv("CD_LDmax", result["CD_LDmax"])
    print_kv("CL_range_jet", result["CL_range_jet"])
    print_kv("CD_range_jet", result["CD_range_jet"])
    print_kv("CL_endurance_prop", result["CL_endurance_prop"])
    print_kv("CD_endurance_prop", result["CD_endurance_prop"])
    print_kv("V_stall_m_s", result["V_stall_m_s"])
    print_kv("V_stall_sl_m_s", result["V_stall_sl_m_s"])
    print_kv("V_range_jet_m_s", result["V_range_jet_m_s"])
    print_kv("V_endurance_jet_m_s", result["V_endurance_jet_m_s"])
    print_kv("V_range_prop_m_s", result["V_range_prop_m_s"])
    print_kv("V_endurance_prop_m_s", result["V_endurance_prop_m_s"])
    print_kv("V_climb_angle_sl_m_s", result["V_climb_angle_sl_m_s"])
    print_kv("thrust_level_min_sl_N", result["thrust_level_min_sl_N"])
    print_kv("V_climb_rate_prop_sl_m_s", result["V_climb_rate_prop_sl_m_s"])
    print_kv("power_level_min_sl_W", result["power_level_min_sl_W"])
    if thrust is not None:
        print_kv("thrust_N", thrust)
        print_kv("sin_gamma_max_angle", result["sin_gamma_max_angle"])
        angle = climb_angle(result["sin_gamma_max_angle"])
        if angle is not None:
            print_kv("gamma_max_angle_rad", angle)
        print_kv("roc_at_max_angle_m_s", result["roc_at_max_angle_m_s"])
        print_kv("V_climb_rate_jet_sl_m_s", result["V_climb_rate_jet_sl_m_s"])
        print_kv("drag_at_jet_roc_sl_N", result["drag_at_jet_roc_sl_N"])
        print_kv("sin_gamma_jet_roc", result["sin_gamma_jet_roc"])
        rate_angle = climb_angle(result["sin_gamma_jet_roc"])
        if rate_angle is not None:
            print_kv("gamma_jet_roc_rad", rate_angle)
        print_kv("roc_jet_m_s", result["roc_jet_m_s"])
    if power is not None:
        print_kv("power_W", power)
        print_kv("roc_prop_m_s", result["roc_prop_m_s"])
        print_kv("sin_gamma_prop", result["sin_gamma_prop"])
        prop_angle = climb_angle(result["sin_gamma_prop"])
        if prop_angle is not None:
            print_kv("gamma_prop_rad", prop_angle)
    if notes:
        print_kv("warning", "; ".join(notes))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL:
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    atmosphere, require_altitude = load_atmosphere()
    sea = atmosphere(0.0)
    rho = sea["rho"]
    weight = 10000.0
    area = 16.0
    cd0 = 0.02
    aspect_ratio = 8.0
    oswald = 0.8
    clmax = 1.6
    thrust = 1500.0
    power = 50000.0
    points = polar_points(cd0, aspect_ratio, oswald)
    k = points["k"]
    if near(k, 1.0 / (math.pi * aspect_ratio * oswald), "k"):
        return 1
    if near(points["CL_LDmax"], math.sqrt(cd0 / k), "CL at max L/D"):
        return 1
    if near(points["CD_LDmax"], 2.0 * cd0, "CD at max L/D"):
        return 1
    if near(points["LD_max"], 0.5 * math.sqrt(math.pi * aspect_ratio * oswald / cd0), "LD_max"):
        return 1
    if near(points["CL_range_jet"], points["CL_LDmax"] / math.sqrt(3.0), "jet range CL"):
        return 1
    if near(points["CD_range_jet"], 4.0 * cd0 / 3.0, "jet range CD"):
        return 1
    if near(
        points["CL_endurance_prop"],
        points["CL_LDmax"] * math.sqrt(3.0),
        "prop endurance CL",
    ):
        return 1
    if near(points["CD_endurance_prop"], 4.0 * cd0, "prop endurance CD"):
        return 1

    result = performance(
        weight, area, cd0, aspect_ratio, oswald, clmax, rho, rho, thrust, power
    )
    if near(result["V_endurance_jet_m_s"], result["V_range_prop_m_s"], "shared max L/D speed"):
        return 1
    if near(result["V_stall_m_s"], result["V_stall_sl_m_s"], "sea-level stall"):
        return 1
    if near(
        result["V_climb_angle_sl_m_s"],
        result["V_endurance_jet_m_s"],
        "steepest-climb speed",
    ):
        return 1
    if near(result["thrust_level_min_sl_N"], weight / result["LD_max"], "minimum thrust"):
        return 1
    for key, cl in (
        ("V_stall_m_s", clmax),
        ("V_range_jet_m_s", result["CL_range_jet"]),
        ("V_endurance_jet_m_s", result["CL_LDmax"]),
        ("V_endurance_prop_m_s", result["CL_endurance_prop"]),
    ):
        speed = level_speed(weight, rho, area, cl)
        if near(result[key], speed, key):
            return 1
        dynamic = 0.5 * rho * speed**2
        if near(weight, cl * dynamic * area, f"lift equals weight at {key}"):
            return 1

    parasite = 0.5 * rho * area * cd0
    induced = 2.0 * k * weight**2 / (rho * area)
    jet_speed = result["V_climb_rate_jet_sl_m_s"]
    residual = thrust - 3.0 * parasite * jet_speed**2 + induced / jet_speed**2
    if abs(residual) / thrust > CHECK_TOL:
        return fail(f"jet climb residual {residual}")
    drag = result["drag_at_jet_roc_sl_N"]
    if near(result["roc_jet_m_s"], jet_speed * (thrust - drag) / weight, "jet roc"):
        return 1
    if near(
        result["roc_at_max_angle_m_s"],
        result["V_climb_angle_sl_m_s"] * result["sin_gamma_max_angle"],
        "roc at max angle",
    ):
        return 1
    if near(
        result["roc_prop_m_s"],
        (power - result["power_level_min_sl_W"]) / weight,
        "prop roc",
    ):
        return 1
    if result["roc_jet_m_s"] + CHECK_TOL < result["roc_at_max_angle_m_s"]:
        return fail("jet best rate is below the rate at the steepest-climb speed")

    high = atmosphere(11000.0)
    climbed = performance(
        weight,
        area,
        cd0,
        aspect_ratio,
        oswald,
        clmax,
        high["rho"],
        rho,
        None,
        None,
    )
    if not climbed["V_stall_m_s"] > result["V_stall_m_s"]:
        return fail("stall speed did not rise at 11 km")
    if near(climbed["LD_max"], result["LD_max"], "L/D independent of altitude"):
        return 1
    if near(climbed["thrust_level_min_sl_N"], result["thrust_level_min_sl_N"], "sea-level thrust"):
        return 1
    if "roc_jet_m_s" in climbed or "roc_prop_m_s" in climbed:
        return fail("climb rate was invented without thrust or power")

    low_stall = performance(
        weight, area, cd0, aspect_ratio, oswald, 0.4, rho, rho, None, None
    )
    notes = warnings_for(0.4, low_stall, sea["cs"], sea["cs"])
    if not any("above CLmax" in note for note in notes):
        return fail("CL above CLmax produced no stall warning")

    try:
        require_altitude(86000.0 + 1.0, "--alt")
    except ValueError:
        pass
    else:
        return fail("altitude above 86 km was accepted")

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
        "--cd0",
        "0.02",
        "--ar",
        "8",
        "--e",
        "0.8",
        "--clmax",
        "1.6",
    ]
    code, text, err = capture(base + ["--alt", "0", "--thrust", "1500", "--power", "50000"])
    if code != 0:
        return fail(f"sea-level main returned {code}: {err}")
    for key in (
        "LD_max:",
        "V_stall_m_s:",
        "V_range_jet_m_s:",
        "V_endurance_jet_m_s:",
        "V_range_prop_m_s:",
        "V_endurance_prop_m_s:",
        "roc_jet_m_s:",
        "roc_prop_m_s:",
        "density_source: altitude",
    ):
        if key not in text:
            return fail(f"stdout missing {key}")
    if "warning:" in text:
        return fail("clean sea-level case printed a warning")

    code, text, err = capture(base + ["--rho", str(rho)])
    if code != 0 or "density_source: density" not in text:
        return fail("density input was rejected")
    if "roc_jet_m_s:" in text or "roc_prop_m_s:" in text:
        return fail("density-only run printed a climb rate")
    if "thrust_level_min_sl_N:" not in text or "power_level_min_sl_W:" not in text:
        return fail("density-only run omitted the sea-level climb floors")

    code, _text, err = capture(base + ["--alt", "0", "--rho", str(rho)])
    if code != 2 or "not both" not in err:
        return fail("both altitude and density were accepted")
    code, _text, _err = capture(base)
    if code != 2:
        return fail("missing altitude and density were accepted")
    code, _text, _err = capture(
        ["--weight", "10000", "--area", "16", "--cd0", "0.02", "--ar", "8", "--e", "0.8", "--alt", "0"]
    )
    if code != 2:
        return fail("missing CLmax was accepted")

    print("check: pass")
    print_kv("LD_max", result["LD_max"])
    print_kv("V_stall_m_s", result["V_stall_m_s"])
    print_kv("V_range_jet_m_s", result["V_range_jet_m_s"])
    print_kv("V_endurance_prop_m_s", result["V_endurance_prop_m_s"])
    print_kv("roc_jet_m_s", result["roc_jet_m_s"])
    print_kv("roc_prop_m_s", result["roc_prop_m_s"])
    return 0


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be > 0")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stall speed, maximum L/D, range and endurance speeds, "
            "and a sea-level climb estimate from a parabolic drag polar."
        )
    )
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--cd0", type=float, default=None, help="zero-lift drag coefficient CD0")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio AR")
    parser.add_argument("--e", type=float, default=None, help="Oswald efficiency e, 0 < e <= 1")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--thrust", type=float, default=None, help="net thrust, taken independent of speed [N]")
    parser.add_argument(
        "--power",
        type=float,
        default=None,
        help="useful power, taken independent of speed [W]",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


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
        "--clmax": args.clmax,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --weight, --area, --cd0, --ar, --e, and --clmax; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if args.alt is None and args.rho is None:
        print("error: requires --alt or --rho", file=sys.stderr)
        return 2
    if args.alt is not None and args.rho is not None:
        print("error: pass --alt or --rho, not both", file=sys.stderr)
        return 2

    try:
        require_positive("weight", args.weight)
        require_positive("wing area", args.area)
        require_positive("CD0", args.cd0)
        require_positive("aspect ratio", args.ar)
        require_positive("CLmax", args.clmax)
        if not math.isfinite(args.e) or args.e <= 0.0 or args.e > 1.0:
            raise ValueError("Oswald efficiency must be > 0 and <= 1")
        if args.thrust is not None:
            require_positive("thrust", args.thrust)
        if args.power is not None:
            require_positive("power", args.power)
        atmosphere, require_altitude = load_atmosphere()
        sea = atmosphere(0.0)
        if args.alt is not None:
            state = atmosphere(require_altitude(args.alt, "--alt"))
            rho = state["rho"]
            sound_speed = state["cs"]
            density_source = "altitude"
            altitude = args.alt
        else:
            require_positive("density", args.rho)
            rho = args.rho
            sound_speed = None
            density_source = "density"
            altitude = None
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = performance(
        args.weight,
        args.area,
        args.cd0,
        args.ar,
        args.e,
        args.clmax,
        rho,
        sea["rho"],
        args.thrust,
        args.power,
    )
    notes = warnings_for(args.clmax, result, sound_speed, sea["cs"])
    emit(
        args.weight,
        args.area,
        args.cd0,
        args.ar,
        args.e,
        args.clmax,
        density_source,
        altitude,
        rho,
        sound_speed,
        sea["rho"],
        sea["cs"],
        args.thrust,
        args.power,
        result,
        notes,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
