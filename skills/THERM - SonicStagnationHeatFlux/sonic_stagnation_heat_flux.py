#!/usr/bin/env python3
"""Stagnation-point convective heat flux on a blunt nose (Sutton-Graves).

stagnation_convective_heat_flux_velocity is the cold-wall form
q = k*sqrt(rho/Rn)*V**3 with Earth-air k from Table II of NASA TR R-376.
stagnation_convective_heat_flux is the heat-transfer coefficient form
q = K*sqrt(ps/Rn)*(hs - hw). Optional radiative_equilibrium_wall_temperature
is Tw = (q/(eps*sigma))**0.25. Dynamic pressure is freestream_dynamic_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Sonic stagnation heat flux"
PLOT_END_FACTOR = 1.5
N_CURVE = 201

# Sutton and Graves, NASA TR R-376, Table II (Earth air).
K_AIR = 0.1113
ATM_PA = 101325.0
K_VELOCITY = K_AIR / (2.0 * math.sqrt(ATM_PA))

# NIST CODATA 2022 Stefan-Boltzmann constant.
SIGMA = 5.670374419e-8

# 1976 dry air for perfect-gas enthalpy and stagnation temperature.
GAMMA = 1.4
M0 = 28.9644
RSTAR = 8.31432e3
R_AIR = RSTAR / M0
CP_AIR = GAMMA * R_AIR / (GAMMA - 1.0)

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "Sutton-Graves stagnation-point convective heating for Earth air on an "
    "axisymmetric blunt nose; "
    f"K_air = {K_AIR:g} kg/(s*m**(3/2)*atm**(1/2)) from NASA TR R-376 "
    "Table II; "
    "cold-wall velocity form stagnation_convective_heat_flux_velocity "
    f"q = k*sqrt(rho/Rn)*V**3 with k = K/(2*sqrt({ATM_PA:g})) = "
    f"{K_VELOCITY:.8g}; "
    "optional heat-transfer coefficient form stagnation_convective_heat_flux "
    "q = K*sqrt(ps/Rn)*(hs - hw) with ps = rho*V**2 in atmospheres, "
    "hs = cp*T + V**2/2 when T is known else hs = V**2/2, and "
    "hw = cp*Tw; "
    "freestream_dynamic_pressure q_dyn = 0.5*rho*V**2; "
    "optional radiative_equilibrium_wall_temperature "
    "Tw = (q/(eps*sigma))**0.25 with CODATA 2022 sigma; "
    "optional adiabatic stagnation temperature Tt = T + V**2/(2*cp) when T "
    "is known; "
    "local sound speed a = sqrt(gamma*R*T) with 1976 dry-air R and gamma = 1.4 "
    "when T is known, so Mach is V/a; "
    "optional --mach-axis plots freestream Mach on the x-axis only when that "
    "sound speed is available; "
    "no dissociation, ionization, or shock-layer radiation model beyond the "
    "Sutton-Graves air coefficient; "
    "flight density is the 1976 atmosphere at --alt, or the supplied --rho"
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
            "ATMOS - Standard1976 must be importable for density from --alt"
        ) from exc
    return atmosphere, require_altitude


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_unit_interval(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def dynamic_pressure(rho: float, speed: float) -> float:
    """freestream_dynamic_pressure: q = 0.5*rho*V**2."""
    return 0.5 * rho * speed * speed


def freestream_kinetic_enthalpy(speed: float) -> float:
    """freestream_kinetic_enthalpy: 0.5*V**2."""
    return 0.5 * speed * speed


def wall_enthalpy(wall_temp: float, cp: float = CP_AIR) -> float:
    """wall_enthalpy_perfect: cp*Tw."""
    return cp * wall_temp


def stagnation_enthalpy(speed: float, temperature: float | None, cp: float = CP_AIR) -> float:
    """Stagnation enthalpy: cp*T + V**2/2, or freestream_kinetic_enthalpy alone."""
    kinetic = freestream_kinetic_enthalpy(speed)
    if temperature is None:
        return kinetic
    require_positive("freestream temperature", temperature)
    return cp * temperature + kinetic


def newtonian_stagnation_pressure_atm(rho: float, speed: float) -> float:
    """p_s in atmospheres from Newtonian p_s = rho*V**2."""
    return rho * speed * speed / ATM_PA


def heat_flux_coefficient(
    rho: float,
    speed: float,
    nose: float,
    wall_temp: float,
    temperature: float | None,
    k_coef: float = K_AIR,
    cp: float = CP_AIR,
) -> float:
    """stagnation_convective_heat_flux with Newtonian p_s."""
    ps_atm = newtonian_stagnation_pressure_atm(rho, speed)
    hs = stagnation_enthalpy(speed, temperature, cp)
    hw = wall_enthalpy(wall_temp, cp)
    if hs <= hw:
        raise ValueError("wall enthalpy must be below stagnation enthalpy")
    return k_coef * math.sqrt(ps_atm / nose) * (hs - hw)


def heat_flux_velocity(rho: float, speed: float, nose: float, k_coef: float = K_VELOCITY) -> float:
    """stagnation_convective_heat_flux_velocity: k*sqrt(rho/Rn)*V**3."""
    return k_coef * math.sqrt(rho / nose) * speed**3


def radiative_wall_temperature(flux: float, emissivity: float, sigma: float = SIGMA) -> float:
    """radiative_equilibrium_wall_temperature: (q/(eps*sigma))**0.25."""
    return (flux / (emissivity * sigma)) ** 0.25


def stagnation_temperature(temperature: float, speed: float, cp: float = CP_AIR) -> float:
    """Adiabatic perfect-gas stagnation temperature: T + V**2/(2*cp)."""
    return temperature + speed * speed / (2.0 * cp)


def speed_of_sound(temperature: float, gamma: float = GAMMA, gas_constant: float = R_AIR) -> float:
    """speed_of_sound: a = sqrt(gamma*R*T) for 1976 dry air."""
    return math.sqrt(gamma * gas_constant * temperature)


def freestream_mach(speed: float, sound: float) -> float:
    """mach_number: M = V/a."""
    return speed / sound


def evaluate(
    rho: float,
    speed: float,
    nose: float,
    wall_temp: float | None,
    temperature: float | None,
    emissivity: float | None,
) -> dict[str, float | str]:
    require_positive("density", rho)
    require_positive("speed", speed)
    require_positive("nose radius", nose)
    q_dyn = dynamic_pressure(rho, speed)
    if wall_temp is None:
        flux = heat_flux_velocity(rho, speed, nose)
        form = "velocity"
        result: dict[str, float | str] = {
            "rho_kg_m3": rho,
            "V_m_s": speed,
            "Rn_m": nose,
            "q_dyn_Pa": q_dyn,
            "q_dot_W_m2": flux,
            "flux_form": form,
            "k_velocity": K_VELOCITY,
            "K_air": K_AIR,
        }
    else:
        require_positive("wall temperature", wall_temp)
        flux = heat_flux_coefficient(rho, speed, nose, wall_temp, temperature)
        form = "heat_transfer_coefficient"
        hs = stagnation_enthalpy(speed, temperature)
        hw = wall_enthalpy(wall_temp)
        result = {
            "rho_kg_m3": rho,
            "V_m_s": speed,
            "Rn_m": nose,
            "q_dyn_Pa": q_dyn,
            "q_dot_W_m2": flux,
            "flux_form": form,
            "K_air": K_AIR,
            "ps_atm": newtonian_stagnation_pressure_atm(rho, speed),
            "hs_J_kg": hs,
            "hw_J_kg": hw,
            "Tw_K": wall_temp,
            "cp_J_kg_K": CP_AIR,
        }
    if temperature is not None:
        require_positive("freestream temperature", temperature)
        sound = speed_of_sound(temperature)
        result["T_K"] = temperature
        result["Tt_K"] = stagnation_temperature(temperature, speed)
        result["a_m_s"] = sound
        result["M"] = freestream_mach(speed, sound)
    if emissivity is not None:
        require_unit_interval("emissivity", emissivity)
        result["emissivity"] = emissivity
        result["Tw_rad_eq_K"] = radiative_wall_temperature(float(result["q_dot_W_m2"]), emissivity)
        result["sigma_W_m2_K4"] = SIGMA
    return result


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
        raise ValueError("matplotlib is required to plot stagnation heat flux") from exc
    return plt


def write_plot(
    result: dict[str, float | str],
    out_path: Path,
    mach_axis: bool = False,
) -> None:
    plt = ensure_matplotlib()
    rho = float(result["rho_kg_m3"])
    speed = float(result["V_m_s"])
    nose = float(result["Rn_m"])
    flux = float(result["q_dot_W_m2"])
    form = str(result["flux_form"])
    wall_temp = float(result["Tw_K"]) if "Tw_K" in result else None
    temperature = float(result["T_K"]) if "T_K" in result else None
    if mach_axis:
        if "a_m_s" not in result:
            raise ValueError(
                "--mach-axis needs local sound speed from --alt or --temperature"
            )
        sound = float(result["a_m_s"])
    else:
        sound = None

    v_max = PLOT_END_FACTOR * speed
    v_min = max(speed * 0.05, 1.0)
    if form == "heat_transfer_coefficient":
        assert wall_temp is not None
        # hs = cp*T + V^2/2 must exceed hw = cp*Tw on the curve.
        t_edge = temperature if temperature is not None else 0.0
        gap = CP_AIR * (wall_temp - t_edge)
        if gap > 0.0:
            v_min = max(v_min, math.sqrt(2.0 * gap) * 1.01)
        if v_min >= v_max:
            v_min = min(speed * 0.9, v_max * 0.5)
    speeds = linspace(v_min, v_max, N_CURVE)
    if form == "velocity":
        fluxes = [heat_flux_velocity(rho, v, nose) for v in speeds]
        label = r"$\dot{q}=k\sqrt{\rho/R_n}\,V^{3}$"
    else:
        assert wall_temp is not None
        fluxes = [
            heat_flux_coefficient(rho, v, nose, wall_temp, temperature) for v in speeds
        ]
        label = r"$\dot{q}=K\sqrt{p_s/R_n}\,(h_s-h_w)$"

    if mach_axis:
        assert sound is not None
        x_curve = [v / sound for v in speeds]
        x_point = speed / sound
        x_max = v_max / sound
        x_label = "freestream Mach"
    else:
        x_curve = speeds
        x_point = speed
        x_max = v_max
        x_label = "freestream speed (m/s)"

    fluxes_kw = [q / 1000.0 for q in fluxes]
    flux_kw = flux / 1000.0

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(x_curve, fluxes_kw, color="#1a5276", linewidth=1.8, label=label)
    ax.plot(
        x_point,
        flux_kw,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(r"stagnation convective heat flux (kW/m$^{2}$)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, x_max)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    result: dict[str, float | str],
    density_source: str,
    altitude: float | None,
    graph: Path | None,
    x_axis: str,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("density_source", density_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("rho_kg_m3", result["rho_kg_m3"])
    print_kv("V_m_s", result["V_m_s"])
    print_kv("Rn_m", result["Rn_m"])
    print_kv("q_dyn_Pa", result["q_dyn_Pa"])
    print_kv("flux_form", result["flux_form"])
    print_kv("K_air", result["K_air"])
    if "k_velocity" in result:
        print_kv("k_velocity", result["k_velocity"])
    if "ps_atm" in result:
        print_kv("ps_atm", result["ps_atm"])
        print_kv("hs_J_kg", result["hs_J_kg"])
        print_kv("hw_J_kg", result["hw_J_kg"])
        print_kv("Tw_K", result["Tw_K"])
        print_kv("cp_J_kg_K", result["cp_J_kg_K"])
    print_kv("q_dot_W_m2", result["q_dot_W_m2"])
    if "T_K" in result:
        print_kv("T_K", result["T_K"])
        print_kv("Tt_K", result["Tt_K"])
        print_kv("a_m_s", result["a_m_s"])
        print_kv("M", result["M"])
    print_kv("x_axis", x_axis)
    if "emissivity" in result:
        print_kv("emissivity", result["emissivity"])
        print_kv("sigma_W_m2_K4", result["sigma_W_m2_K4"])
        print_kv("Tw_rad_eq_K", result["Tw_rad_eq_K"])
    print_kv(
        "warning",
        "no dissociation or ionization model beyond the Sutton-Graves air "
        "coefficient; not valid as a full high-enthalpy aerothermochemistry "
        "solution",
    )
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(freestream_kinetic_enthalpy(100.0), 5000.0):
        return fail("kinetic enthalpy at 100 m/s is not 5000")
    if not close(wall_enthalpy(300.0), CP_AIR * 300.0):
        return fail("wall enthalpy mismatch")
    if not close(K_VELOCITY, K_AIR / (2.0 * math.sqrt(ATM_PA))):
        return fail("velocity-form k is not K/(2*sqrt(atm))")

    # Cold-wall velocity form equals coefficient form with hw = 0 and hs = V^2/2.
    rho = 3.1459e-4
    speed = 3535.0
    nose = 1.0
    q_v = heat_flux_velocity(rho, speed, nose)
    q_c = heat_flux_coefficient(rho, speed, nose, wall_temp=1e-12, temperature=None)
    if not close(q_v, q_c, tol=1e-6):
        return fail("velocity and coefficient cold-wall forms disagree")

    # Radiative equilibrium: blackbody at 1 K emits sigma.
    if not close(radiative_wall_temperature(SIGMA, 1.0), 1.0):
        return fail("blackbody unit radiative wall is not 1 K")

    tw = radiative_wall_temperature(136000.0, 0.8)
    expected_tw = (136000.0 / (0.8 * SIGMA)) ** 0.25
    if not close(tw, expected_tw):
        return fail("gray radiative wall temperature mismatch")

    # Stagnation temperature at rest equals static.
    if not close(stagnation_temperature(288.15, 0.0), 288.15):
        return fail("rest stagnation temperature is not static")

    sound = speed_of_sound(216.65)
    if not close(sound, math.sqrt(GAMMA * R_AIR * 216.65)):
        return fail("sound speed mismatch")
    if not close(freestream_mach(sound, sound), 1.0):
        return fail("Mach at a = V is not 1")

    point = evaluate(rho, speed, nose, None, None, 0.8)
    if point["flux_form"] != "velocity":
        return fail("cold-wall path did not set velocity form")
    if not close(float(point["q_dyn_Pa"]), 0.5 * rho * speed * speed):
        return fail("dynamic pressure mismatch")
    if "Tw_rad_eq_K" not in point:
        return fail("emissivity path did not set radiative wall temperature")
    if "a_m_s" in point or "M" in point:
        return fail("sound speed printed without temperature")

    hot = evaluate(rho, speed, nose, 300.0, 216.65, None)
    if hot["flux_form"] != "heat_transfer_coefficient":
        return fail("wall-temperature path did not set coefficient form")
    if float(hot["q_dot_W_m2"]) >= float(point["q_dot_W_m2"]):
        return fail("hot wall did not reduce heat flux")
    if "a_m_s" not in hot or "M" not in hot:
        return fail("temperature path did not set Mach")
    if not close(float(hot["M"]), speed / float(hot["a_m_s"])):
        return fail("reported Mach disagrees with V/a")

    try:
        evaluate(rho, speed, nose, 1.0e12, None, None)
        return fail("wall hotter than stagnation enthalpy was accepted")
    except ValueError:
        pass

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
        out = str(Path(tmp) / "heat_flux.png")
        code, text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--rho",
                "3.1459e-4",
                "--emissivity",
                "0.8",
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
            "title: Sonic stagnation heat flux",
            "q_dot_W_m2:",
            "q_dyn_Pa:",
            "flux_form: velocity",
            "Tw_rad_eq_K:",
            "graph:",
            "warning:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--rho",
                "3.1459e-4",
                "--wall-temp",
                "300",
                "--temperature",
                "216.65",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"wall-temp run returned {code}: {err}")
        if "flux_form: heat_transfer_coefficient" not in text:
            return fail("wall-temp run did not print coefficient form")
        if "Tt_K:" not in text:
            return fail("temperature run did not print stagnation temperature")

        code, text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--alt",
                "60000",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"altitude run returned {code}: {err}")
        if "density_source: altitude" not in text:
            return fail("altitude run did not mark density_source")
        if "Z_m:" not in text or "Tt_K:" not in text:
            return fail("altitude run did not print Z and Tt")
        if "a_m_s:" not in text or "M:" not in text:
            return fail("altitude run did not print sound speed and Mach")
        if "x_axis: speed" not in text:
            return fail("default plot axis is not speed")

        code, text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--alt",
                "60000",
                "--mach-axis",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"mach-axis altitude run returned {code}: {err}")
        if "x_axis: mach" not in text:
            return fail("mach-axis run did not mark x_axis mach")
        if not Path(out).is_file() or not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("mach-axis run did not write a PNG")

        code, _text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--rho",
                "3.1459e-4",
                "--mach-axis",
                "--out",
                out,
            ]
        )
        if code != 2 or "mach-axis" not in err:
            return fail("mach-axis without temperature was accepted")

        code, text, err = capture(
            [
                "--speed",
                "3535",
                "--nose",
                "1",
                "--rho",
                "3.1459e-4",
                "--temperature",
                "216.65",
                "--mach-axis",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"mach-axis with temperature returned {code}: {err}")
        if "x_axis: mach" not in text or "M:" not in text:
            return fail("mach-axis with temperature did not print Mach axis")

        code, _text, err = capture(
            ["--speed", "3535", "--nose", "1", "--alt", "60000", "--rho", "0.0003"]
        )
        if code != 2 or "not both" not in err:
            return fail("alt and rho together were accepted")

        code, _text, err = capture(["--speed", "3535", "--nose", "1"])
        if code != 2 or "requires --alt or --rho" not in err:
            return fail("missing density path was not rejected")

    print("check: pass")
    print_kv("k_velocity", K_VELOCITY)
    print_kv("q_dot_W_m2_example", q_v)
    print_kv("Tw_rad_eq_K_example", tw)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stagnation-point convective heat flux, dynamic pressure, and "
            "optional radiative-equilibrium wall temperature."
        )
    )
    parser.add_argument("--speed", type=float, default=None, help="freestream speed V [m/s]")
    parser.add_argument("--nose", type=float, default=None, help="effective nose radius Rn [m]")
    parser.add_argument("--rho", type=float, default=None, help="freestream density [kg/m^3]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument(
        "--wall-temp",
        type=float,
        default=None,
        help="wall temperature Tw [K] for the heat-transfer coefficient form",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="freestream static temperature T [K] (optional with --rho)",
    )
    parser.add_argument(
        "--emissivity",
        type=float,
        default=None,
        help="surface emissivity for radiative-equilibrium wall temperature",
    )
    parser.add_argument(
        "--mach-axis",
        action="store_true",
        help="plot freestream Mach on the x-axis (needs --alt or --temperature)",
    )
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.speed is None or args.nose is None:
        print("error: requires --speed and --nose", file=sys.stderr)
        return 2
    if args.alt is None and args.rho is None:
        print("error: requires --alt or --rho", file=sys.stderr)
        return 2
    if args.alt is not None and args.rho is not None:
        print("error: pass --alt or --rho, not both", file=sys.stderr)
        return 2
    if args.temperature is not None and args.alt is not None:
        print(
            "error: --temperature is only for --rho; --alt supplies 1976 T",
            file=sys.stderr,
        )
        return 2
    if args.mach_axis and args.alt is None and args.temperature is None:
        print(
            "error: --mach-axis needs local sound speed from --alt or --temperature",
            file=sys.stderr,
        )
        return 2

    try:
        altitude: float | None = None
        temperature: float | None = args.temperature
        if args.alt is not None:
            atmosphere, require_altitude = load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            rho = float(state["rho"])
            temperature = float(state["T"])
            density_source = "altitude"
            altitude = float(state["Z"])
        else:
            require_positive("density", args.rho)
            rho = float(args.rho)
            density_source = "density"
        result = evaluate(
            rho,
            args.speed,
            args.nose,
            args.wall_temp,
            temperature,
            args.emissivity,
        )
        out_path = Path(args.out) if args.out is not None else SKILL_DIR / "sonic_stagnation_heat_flux.png"
        out_path = out_path.resolve()
        write_plot(result, out_path, mach_axis=args.mach_axis)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    x_axis = "mach" if args.mach_axis else "speed"
    emit(result, density_source, altitude, out_path, x_axis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
