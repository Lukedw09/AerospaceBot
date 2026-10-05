#!/usr/bin/env python3
"""Ideal air-breathing Brayton turbojet performance.

isentropic_compressor_temperature_ratio, ideal_compressor_work,
ideal_turbine_temperature_ratio, ideal_turbine_pressure_ratio,
burner_fuel_air_ratio, ideal_turbojet_nozzle_pressure_ratio,
ideal_nozzle_exit_velocity, ideal_nozzle_exit_temperature,
turbojet_specific_thrust, turbojet_tsfc, turbojet_thermal_efficiency,
turbojet_propulsive_efficiency, turbojet_overall_efficiency, and
ideal_brayton_thermal_efficiency. Freestream totals use
stagnation_temperature and stagnation_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Ideal turbojet"
N_PLOT = 201
DEFAULT_GAMMA = 1.4
# 1976 dry-air R = R*/M0.
RSTAR = 8.31432e3
M0 = 28.9644
R_AIR = RSTAR / M0
# Typical JP-4 lower heating value used with NASA cycle HVF (about 18400 Btu/lbm).
DEFAULT_HEATING_VALUE = 4.28e7
M_PLOT_MAX_FLOOR = 2.0
M_PLOT_END_FACTOR = 1.5

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "ideal air-breathing Brayton turbojet; calorically perfect gas; "
    "perfect inlet recovery; isentropic compressor and turbine; "
    "constant-pressure burner BPR = 1 with burner efficiency 1; "
    "adiabatic fully expanded nozzle pe = p0; no fan; no afterburner; "
    "no real-component maps; "
    "tau_c = pi_c**((gamma-1)/gamma) from isentropic_compressor_temperature_ratio; "
    "w_c = cp*Tt2*(tau_c-1) from ideal_compressor_work; "
    "tau_t = 1 - (Tt2/Tt4)*(tau_c-1) from ideal_turbine_temperature_ratio "
    "(fuel mass neglected in the shaft match); "
    "pi_t = tau_t**(gamma/(gamma-1)) from ideal_turbine_pressure_ratio; "
    "f = cp*(Tt4-Tt3)/(Q-cp*Tt4) from burner_fuel_air_ratio; "
    "NPR = (pt0/p0)*pi_c*pi_t from ideal_turbojet_nozzle_pressure_ratio; "
    "Ve from ideal_nozzle_exit_velocity; Te from ideal_nozzle_exit_temperature; "
    "Fs = (1+f)*Ve - V0 from turbojet_specific_thrust; "
    "TSFC = f/Fs from turbojet_tsfc; "
    "eta_th, eta_p, eta_o from turbojet_thermal_efficiency, "
    "turbojet_propulsive_efficiency, turbojet_overall_efficiency; "
    "eta_brayton = 1 - 1/(tau_r*tau_c) from ideal_brayton_thermal_efficiency; "
    f"default gamma = {DEFAULT_GAMMA:g}; default Q = {DEFAULT_HEATING_VALUE:g} J/kg; "
    "default cp = gamma*R/(gamma-1) with 1976 dry-air R; "
    "PNG is specific thrust versus Mach at the fixed TIT and OPR"
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
            "ATMOS - Standard1976 must be importable for freestream from --alt"
        ) from exc
    return atmosphere, require_altitude


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def require_gamma(gamma: float) -> None:
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("gamma must be finite and > 1")


def default_cp(gamma: float) -> float:
    """cp_from_gamma with 1976 dry-air R."""
    return gamma * R_AIR / (gamma - 1.0)


def stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    """stagnation_temperature: Tt/T = 1 + 0.5*(g-1)*M**2."""
    return 1.0 + 0.5 * (gamma - 1.0) * mach * mach


def stagnation_pressure_ratio(tau_r: float, gamma: float) -> float:
    """stagnation_pressure: pt/p = (Tt/T)**(g/(g-1))."""
    return tau_r ** (gamma / (gamma - 1.0))


def speed_of_sound(temperature: float, gamma: float, gas_constant: float) -> float:
    """speed_of_sound: a = sqrt(g*R*T)."""
    return math.sqrt(gamma * gas_constant * temperature)


def compressor_temperature_ratio(pi_c: float, gamma: float) -> float:
    """isentropic_compressor_temperature_ratio."""
    return pi_c ** ((gamma - 1.0) / gamma)


def compressor_work(cp: float, tt2: float, tau_c: float) -> float:
    """ideal_compressor_work."""
    return cp * tt2 * (tau_c - 1.0)


def turbine_temperature_ratio(tt2: float, tt4: float, tau_c: float) -> float:
    """ideal_turbine_temperature_ratio."""
    return 1.0 - (tt2 / tt4) * (tau_c - 1.0)


def turbine_pressure_ratio(tau_t: float, gamma: float) -> float:
    """ideal_turbine_pressure_ratio."""
    return tau_t ** (gamma / (gamma - 1.0))


def fuel_air_ratio(cp: float, tt4: float, tt3: float, heating_value: float) -> float:
    """burner_fuel_air_ratio."""
    denom = heating_value - cp * tt4
    if denom <= 0.0:
        raise ValueError("heating value must exceed cp*Tt4")
    if tt4 <= tt3:
        raise ValueError("turbine inlet temperature must exceed compressor exit temperature")
    return cp * (tt4 - tt3) / denom


def nozzle_pressure_ratio(pt0: float, p0: float, pi_c: float, pi_t: float) -> float:
    """ideal_turbojet_nozzle_pressure_ratio."""
    return (pt0 / p0) * pi_c * pi_t


def nozzle_exit_velocity(cp: float, tt: float, npr: float, gamma: float) -> float:
    """ideal_nozzle_exit_velocity."""
    if npr <= 1.0:
        raise ValueError("nozzle pressure ratio must be > 1 for a fully expanded jet")
    factor = 1.0 - npr ** (-(gamma - 1.0) / gamma)
    if factor <= 0.0:
        raise ValueError("nozzle expansion factor is not positive")
    return math.sqrt(2.0 * cp * tt * factor)


def nozzle_exit_temperature(tt: float, npr: float, gamma: float) -> float:
    """ideal_nozzle_exit_temperature."""
    return tt * npr ** (-(gamma - 1.0) / gamma)


def specific_thrust(f: float, ve: float, v0: float) -> float:
    """turbojet_specific_thrust."""
    return (1.0 + f) * ve - v0


def tsfc(f: float, fs: float) -> float:
    """turbojet_tsfc."""
    if fs <= 0.0:
        raise ValueError("specific thrust must be > 0")
    return f / fs


def thermal_efficiency(f: float, ve: float, v0: float, heating_value: float) -> float:
    """turbojet_thermal_efficiency."""
    return ((1.0 + f) * ve * ve - v0 * v0) / (2.0 * f * heating_value)


def propulsive_efficiency(v0: float, fs: float, f: float, ve: float) -> float:
    """turbojet_propulsive_efficiency."""
    if v0 == 0.0:
        return 0.0
    denom = (1.0 + f) * ve * ve - v0 * v0
    if denom <= 0.0:
        raise ValueError("kinetic energy rise is not positive")
    return 2.0 * v0 * fs / denom


def overall_efficiency(fs: float, v0: float, f: float, heating_value: float) -> float:
    """turbojet_overall_efficiency."""
    if v0 == 0.0:
        return 0.0
    return fs * v0 / (f * heating_value)


def brayton_thermal_efficiency(tau_r: float, tau_c: float) -> float:
    """ideal_brayton_thermal_efficiency."""
    return 1.0 - 1.0 / (tau_r * tau_c)


def solution(
    mach: float,
    temperature: float,
    pressure: float,
    tit: float,
    opr: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
) -> dict[str, float]:
    require_nonnegative("Mach", mach)
    require_positive("temperature", temperature)
    require_positive("pressure", pressure)
    require_positive("turbine inlet temperature", tit)
    require_positive("compressor pressure ratio", opr)
    if opr <= 1.0:
        raise ValueError("compressor pressure ratio must be > 1")
    require_gamma(gamma)
    require_positive("cp", cp)
    require_positive("heating value", heating_value)
    require_positive("gas constant", gas_constant)

    tau_r = stagnation_temperature_ratio(mach, gamma)
    pi_r = stagnation_pressure_ratio(tau_r, gamma)
    tt0 = temperature * tau_r
    pt0 = pressure * pi_r
    a0 = speed_of_sound(temperature, gamma, gas_constant)
    v0 = mach * a0

    tt2 = tt0
    pt2 = pt0
    tau_c = compressor_temperature_ratio(opr, gamma)
    tt3 = tt2 * tau_c
    w_c = compressor_work(cp, tt2, tau_c)

    tt4 = tit
    if tt4 <= tt3:
        raise ValueError(
            "turbine inlet temperature must exceed compressor-exit total temperature "
            f"Tt3 = {tt3:.8g} K"
        )
    f = fuel_air_ratio(cp, tt4, tt3, heating_value)

    tau_t = turbine_temperature_ratio(tt2, tt4, tau_c)
    if tau_t <= 0.0 or tau_t >= 1.0:
        raise ValueError(
            "compressor work exceeds available turbine enthalpy; "
            "lower OPR or raise TIT"
        )
    pi_t = turbine_pressure_ratio(tau_t, gamma)
    tt5 = tt4 * tau_t

    npr = nozzle_pressure_ratio(pt0, pressure, opr, pi_t)
    ve = nozzle_exit_velocity(cp, tt5, npr, gamma)
    te = nozzle_exit_temperature(tt5, npr, gamma)
    fs = specific_thrust(f, ve, v0)
    if fs <= 0.0:
        raise ValueError("specific thrust is not positive at this flight condition")
    ct = tsfc(f, fs)
    eta_th = thermal_efficiency(f, ve, v0, heating_value)
    eta_p = propulsive_efficiency(v0, fs, f, ve)
    eta_o = overall_efficiency(fs, v0, f, heating_value)
    eta_b = brayton_thermal_efficiency(tau_r, tau_c)

    return {
        "M": mach,
        "T0_K": temperature,
        "p0_Pa": pressure,
        "a0_m_s": a0,
        "V0_m_s": v0,
        "tau_r": tau_r,
        "pi_r": pi_r,
        "Tt0_K": tt0,
        "pt0_Pa": pt0,
        "Tt2_K": tt2,
        "pt2_Pa": pt2,
        "pi_c": opr,
        "tau_c": tau_c,
        "Tt3_K": tt3,
        "w_c_J_kg": w_c,
        "Tt4_K": tt4,
        "f": f,
        "tau_t": tau_t,
        "pi_t": pi_t,
        "Tt5_K": tt5,
        "NPR": npr,
        "Ve_m_s": ve,
        "Te_K": te,
        "Fs_m_s": fs,
        "TSFC_kg_N_s": ct,
        "eta_th": eta_th,
        "eta_p": eta_p,
        "eta_o": eta_o,
        "eta_brayton": eta_b,
        "gamma": gamma,
        "cp_J_kgK": cp,
        "R_J_kgK": gas_constant,
        "Q_J_kg": heating_value,
    }


def mach_grid(mach: float) -> list[float]:
    end = max(M_PLOT_MAX_FLOOR, M_PLOT_END_FACTOR * max(mach, 0.5))
    return [end * i / (N_PLOT - 1) for i in range(N_PLOT)]


def sweep_specific_thrust(
    temperature: float,
    pressure: float,
    tit: float,
    opr: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
    machs: list[float],
) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for mach in machs:
        try:
            point = solution(
                mach,
                temperature,
                pressure,
                tit,
                opr,
                gamma,
                cp,
                heating_value,
                gas_constant,
            )
        except ValueError:
            continue
        xs.append(mach)
        ys.append(point["Fs_m_s"])
    if len(xs) < 2:
        raise ValueError("Mach sweep produced fewer than two valid specific-thrust points")
    return xs, ys


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the ideal turbojet") from exc
    return plt


def plot_turbojet(
    path: Path,
    result: dict[str, float],
    freestream_source: str,
) -> None:
    plt = ensure_matplotlib()
    machs, thrusts = sweep_specific_thrust(
        result["T0_K"],
        result["p0_Pa"],
        result["Tt4_K"],
        result["pi_c"],
        result["gamma"],
        result["cp_J_kgK"],
        result["Q_J_kg"],
        result["R_J_kgK"],
        mach_grid(result["M"]),
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(machs, thrusts, color="#1a5276", linewidth=1.8, label="specific thrust")
    ax.plot(
        result["M"],
        result["Fs_m_s"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("flight Mach number")
    ax.set_ylabel(r"specific thrust $F_s$ (m/s)")
    ax.set_xlim(0.0, machs[-1])
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.35)
    caption = (
        f"fixed TIT = {result['Tt4_K']:.6g} K, OPR = {result['pi_c']:.6g}; "
        f"freestream from {freestream_source}"
    )
    ax.text(0.02, 0.02, caption, transform=ax.transAxes, fontsize=8, va="bottom")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(
    result: dict[str, float],
    freestream_source: str,
    altitude: float | None,
    gamma_source: str,
    cp_source: str,
    heating_source: str,
    path: Path,
) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "ideal Brayton turbojet")
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("M", result["M"])
    print_kv("T0_K", result["T0_K"])
    print_kv("p0_Pa", result["p0_Pa"])
    print_kv("a0_m_s", result["a0_m_s"])
    print_kv("V0_m_s", result["V0_m_s"])
    print_kv("tau_r", result["tau_r"])
    print_kv("pi_r", result["pi_r"])
    print_kv("Tt0_K", result["Tt0_K"])
    print_kv("pt0_Pa", result["pt0_Pa"])
    print_kv("pi_c", result["pi_c"])
    print_kv("tau_c", result["tau_c"])
    print_kv("Tt3_K", result["Tt3_K"])
    print_kv("w_c_J_kg", result["w_c_J_kg"])
    print_kv("Tt4_K", result["Tt4_K"])
    print_kv("f", result["f"])
    print_kv("tau_t", result["tau_t"])
    print_kv("pi_t", result["pi_t"])
    print_kv("Tt5_K", result["Tt5_K"])
    print_kv("NPR", result["NPR"])
    print_kv("Ve_m_s", result["Ve_m_s"])
    print_kv("Te_K", result["Te_K"])
    print_kv("Fs_m_s", result["Fs_m_s"])
    print_kv("TSFC_kg_N_s", result["TSFC_kg_N_s"])
    print_kv("eta_th", result["eta_th"])
    print_kv("eta_p", result["eta_p"])
    print_kv("eta_o", result["eta_o"])
    print_kv("eta_brayton", result["eta_brayton"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("cp_J_kgK", result["cp_J_kgK"])
    print_kv("cp_source", cp_source)
    print_kv("R_J_kgK", result["R_J_kgK"])
    print_kv("Q_J_kg", result["Q_J_kg"])
    print_kv("Q_source", heating_source)
    print_kv("graph", str(path))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    gamma = 1.4
    if near(compressor_temperature_ratio(2.0 ** (7.0 / 2.0), gamma), 2.0, "tau_c"):
        return 1
    if near(compressor_work(1000.0, 300.0, 2.0), 300000.0, "compressor work"):
        return 1
    if near(turbine_temperature_ratio(300.0, 1200.0, 3.0), 0.5, "tau_t"):
        return 1
    if near(turbine_pressure_ratio(0.5, gamma), 0.5 ** (7.0 / 2.0), "pi_t"):
        return 1
    f_ref = fuel_air_ratio(1000.0, 1200.0, 600.0, 42.0e6)
    if near(f_ref, 600000.0 / (42.0e6 - 1.2e6), "fuel-air ratio"):
        return 1
    if near(nozzle_pressure_ratio(2.0, 1.0, 8.0, 0.25), 4.0, "NPR"):
        return 1
    if near(nozzle_exit_temperature(800.0, 2.0 ** (7.0 / 2.0), gamma), 400.0, "Te"):
        return 1
    if near(specific_thrust(0.0, 800.0, 200.0), 600.0, "Fs"):
        return 1
    if near(propulsive_efficiency(250.0, 500.0, 0.0, 750.0), 0.5, "eta_p"):
        return 1
    if near(brayton_thermal_efficiency(1.0, 2.0), 0.5, "eta_brayton"):
        return 1

    # Sea-level static identity path with known totals.
    t0 = 288.15
    p0 = 101325.0
    point = solution(0.0, t0, p0, 1600.0, 10.0, gamma, default_cp(gamma), DEFAULT_HEATING_VALUE, R_AIR)
    if near(point["Tt0_K"], t0, "static Tt0"):
        return 1
    if point["Fs_m_s"] <= 0.0:
        return fail("static specific thrust not positive")
    if point["eta_p"] != 0.0 or point["eta_o"] != 0.0:
        return fail("static propulsive/overall efficiency must be zero")
    if abs(point["eta_o"] - point["eta_th"] * point["eta_p"]) > CHECK_TOL:
        return fail("eta_o is not eta_th*eta_p")

    cruise = solution(0.8, t0, p0, 1600.0, 20.0, gamma, default_cp(gamma), DEFAULT_HEATING_VALUE, R_AIR)
    if abs(cruise["eta_o"] - cruise["eta_th"] * cruise["eta_p"]) > CHECK_TOL * max(
        1.0, abs(cruise["eta_o"])
    ):
        return fail("cruise eta_o is not eta_th*eta_p")
    if cruise["Ve_m_s"] <= cruise["V0_m_s"]:
        return fail("exit speed not above flight speed")

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

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "ideal_turbojet.png"
        code, text, err = capture(
            [
                "--mach",
                "0.8",
                "--temperature",
                "216.65",
                "--pressure",
                "19330",
                "--tit",
                "1600",
                "--opr",
                "20",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli freestream T,p failed: {err}")
        if "freestream_source: temperature_pressure" not in text:
            return fail("cli did not report temperature_pressure freestream")
        if "Fs_m_s:" not in text or "TSFC_kg_N_s:" not in text:
            return fail("cli omitted specific thrust or TSFC")
        if "eta_th:" not in text or "eta_p:" not in text or "eta_o:" not in text:
            return fail("cli omitted efficiencies")
        if "Ve_m_s:" not in text or "Te_K:" not in text:
            return fail("cli omitted exit state")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")

        code, text, err = capture(
            [
                "--mach",
                "0.8",
                "--alt",
                "11000",
                "--tit",
                "1600",
                "--opr",
                "20",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli altitude failed: {err}")
        if "freestream_source: altitude" not in text:
            return fail("cli did not report altitude freestream")
        if "Z_m:" not in text:
            return fail("cli omitted Z_m")

        code, _text, err = capture(
            [
                "--mach",
                "0.8",
                "--alt",
                "0",
                "--temperature",
                "288.15",
                "--pressure",
                "101325",
                "--tit",
                "1600",
                "--opr",
                "10",
            ]
        )
        if code == 0:
            return fail("cli accepted both --alt and freestream T,p")

        code, _text, err = capture(
            ["--mach", "0.8", "--tit", "1600", "--opr", "10"]
        )
        if code == 0:
            return fail("cli accepted a missing freestream")

        code, _text, err = capture(
            [
                "--mach",
                "0.8",
                "--alt",
                "0",
                "--tit",
                "300",
                "--opr",
                "10",
            ]
        )
        if code == 0:
            return fail("cli accepted TIT below compressor exit")

    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ideal Brayton turbojet specific thrust, TSFC, efficiencies, "
            "and exit state from Mach, freestream, TIT, and compressor pressure ratio."
        )
    )
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number M")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument(
        "--temperature", type=float, default=None, help="freestream static temperature T0 [K]"
    )
    parser.add_argument(
        "--pressure", type=float, default=None, help="freestream static pressure p0 [Pa]"
    )
    parser.add_argument(
        "--tit", type=float, default=None, help="turbine inlet total temperature Tt4 [K]"
    )
    parser.add_argument(
        "--opr",
        type=float,
        default=None,
        help="compressor pressure ratio pi_c = pt3/pt2",
    )
    parser.add_argument(
        "--heating-value",
        type=float,
        default=None,
        help=f"fuel lower heating value Q [J/kg]; default {DEFAULT_HEATING_VALUE:g}",
    )
    parser.add_argument(
        "--cp",
        type=float,
        default=None,
        help="specific heat at constant pressure [J/(kg*K)]; default from gamma and air R",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats; default {DEFAULT_GAMMA:g}",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--mach": args.mach,
        "--tit": args.tit,
        "--opr": args.opr,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --mach, --tit, --opr, and (--alt or both "
            f"--temperature and --pressure); missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    has_alt = args.alt is not None
    has_tp = args.temperature is not None or args.pressure is not None
    if has_alt and has_tp:
        print("error: pass --alt or --temperature/--pressure, not both", file=sys.stderr)
        return 2
    if not has_alt and (args.temperature is None or args.pressure is None):
        print(
            "error: requires --alt, or both --temperature and --pressure",
            file=sys.stderr,
        )
        return 2

    try:
        altitude = None
        if has_alt:
            atmosphere, require_altitude = load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            temperature = float(state["T"])
            pressure = float(state["p"])
            freestream_source = "altitude"
            altitude = float(state["Z"])
        else:
            require_positive("temperature", args.temperature)
            require_positive("pressure", args.pressure)
            temperature = args.temperature
            pressure = args.pressure
            freestream_source = "temperature_pressure"

        if args.gamma is None:
            gamma = DEFAULT_GAMMA
            gamma_source = "default"
        else:
            require_gamma(args.gamma)
            gamma = args.gamma
            gamma_source = "user"

        if args.cp is None:
            cp = default_cp(gamma)
            cp_source = "gamma_air_R"
        else:
            require_positive("cp", args.cp)
            cp = args.cp
            cp_source = "user"

        if args.heating_value is None:
            heating_value = DEFAULT_HEATING_VALUE
            heating_source = "default"
        else:
            require_positive("heating value", args.heating_value)
            heating_value = args.heating_value
            heating_source = "user"

        result = solution(
            args.mach,
            temperature,
            pressure,
            args.tit,
            args.opr,
            gamma,
            cp,
            heating_value,
            R_AIR,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "ideal_turbojet.png"
        out_path = out_path.resolve()
        plot_turbojet(out_path, result, freestream_source)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(
        result,
        freestream_source,
        altitude,
        gamma_source,
        cp_source,
        heating_source,
        out_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
