#!/usr/bin/env python3
"""Design-point turbojet with inlet recovery and component efficiencies.

adiabatic_diffuser_temperature, inlet_exit_total_pressure,
compressor_temperature_ratio_efficiency, compressor_work_efficiency,
burner_fuel_air_ratio_efficiency, burner_exit_total_pressure,
turbine_temperature_ratio_from_work, turbine_pressure_ratio_from_efficiency,
nozzle_exit_velocity_efficiency, turbojet_specific_thrust, turbojet_tsfc,
and the turbojet efficiency records. Freestream totals use
stagnation_temperature and stagnation_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Nonideal turbojet"
N_PLOT = 201
DEFAULT_GAMMA = 1.4
RSTAR = 8.31432e3
M0 = 28.9644
R_AIR = RSTAR / M0
DEFAULT_HEATING_VALUE = 4.28e7
M_PLOT_MAX_FLOOR = 2.0
M_PLOT_END_FACTOR = 1.5

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"
IDEAL_DIR = SKILL_DIR.parent / "PROP - IdealTurboJet"

ASSUMPTIONS = (
    "design-point turbojet; calorically perfect gas; adiabatic inlet; "
    "isentropic compressor and turbine efficiencies; burner efficiency and "
    "burner pressure ratio; mechanical efficiency on the shaft; "
    "nozzle efficiency on the fully expanded exit speed; "
    "shaft match includes fuel mass unless --neglect-fuel-match; "
    "no fan; no afterburner; no component maps; "
    "Tt2 = Tt0 from adiabatic_diffuser_temperature; "
    "pt2 = pi_d*pt0 from inlet_exit_total_pressure; "
    "tau_c from compressor_temperature_ratio_efficiency; "
    "w_c from compressor_work_efficiency; "
    "f from burner_fuel_air_ratio_efficiency; "
    "pt4 = pi_b*pt3 from burner_exit_total_pressure; "
    "tau_t from turbine_temperature_ratio_from_work; "
    "pi_t from turbine_pressure_ratio_from_efficiency; "
    "Ve from nozzle_exit_velocity_efficiency; "
    "Fs = (1+f)*Ve - V0 from turbojet_specific_thrust; "
    "TSFC = f/Fs from turbojet_tsfc; "
    f"default gamma = {DEFAULT_GAMMA:g}; default Q = {DEFAULT_HEATING_VALUE:g} J/kg; "
    "omitted efficiencies are 1 and omitted pressure ratios that are losses are 1; "
    "PNG is specific thrust versus Mach at the fixed TIT, OPR, and efficiencies"
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


def require_efficiency(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def require_loss_ratio(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def default_cp(gamma: float) -> float:
    """cp_from_gamma with 1976 dry-air R."""
    return gamma * R_AIR / (gamma - 1.0)


def stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    """stagnation_temperature: Tt/T = 1 + 0.5*(g-1)*M**2."""
    return 1.0 + 0.5 * (gamma - 1.0) * mach * mach


def stagnation_pressure_ratio(tau: float, gamma: float) -> float:
    """stagnation_pressure: pt/p = (Tt/T)**(g/(g-1))."""
    return tau ** (gamma / (gamma - 1.0))


def speed_of_sound(temperature: float, gamma: float, gas_constant: float) -> float:
    """speed_of_sound: a = sqrt(g*R*T)."""
    return math.sqrt(gamma * gas_constant * temperature)


def compressor_temperature_ratio(pi_c: float, gamma: float, eta_c: float) -> float:
    """compressor_temperature_ratio_efficiency."""
    ideal = pi_c ** ((gamma - 1.0) / gamma)
    return 1.0 + (ideal - 1.0) / eta_c


def compressor_work(
    cp: float, tt2: float, pi_c: float, gamma: float, eta_c: float
) -> float:
    """compressor_work_efficiency."""
    ideal = pi_c ** ((gamma - 1.0) / gamma)
    return cp * tt2 * (ideal - 1.0) / eta_c


def fuel_air_ratio(
    cp: float, tt4: float, tt3: float, eta_b: float, heating_value: float
) -> float:
    """burner_fuel_air_ratio_efficiency."""
    denom = eta_b * heating_value - cp * tt4
    if denom <= 0.0:
        raise ValueError("eta_b*Q must exceed cp*Tt4")
    if tt4 <= tt3:
        raise ValueError("turbine inlet temperature must exceed compressor exit temperature")
    return cp * (tt4 - tt3) / denom


def turbine_temperature_ratio(
    work: float,
    fuel_fraction: float,
    eta_m: float,
    cp: float,
    tt4: float,
) -> float:
    """turbine_temperature_ratio_from_work."""
    denom = (1.0 + fuel_fraction) * eta_m * cp * tt4
    if denom <= 0.0:
        raise ValueError("turbine work denominator must be > 0")
    tau_t = 1.0 - work / denom
    if tau_t <= 0.0 or tau_t >= 1.0:
        raise ValueError(
            "compressor work exceeds available turbine enthalpy; "
            "lower OPR, raise TIT, or raise component efficiency"
        )
    return tau_t


def turbine_pressure_ratio(tau_t: float, eta_t: float, gamma: float) -> float:
    """turbine_pressure_ratio_from_efficiency."""
    exponent_base = 1.0 - (1.0 - tau_t) / eta_t
    if exponent_base <= 0.0 or exponent_base >= 1.0:
        raise ValueError(
            "turbine efficiency cannot supply the shaft work at this temperature ratio"
        )
    return exponent_base ** (gamma / (gamma - 1.0))


def nozzle_exit_velocity(
    eta_n: float, cp: float, tt: float, npr: float, gamma: float
) -> float:
    """nozzle_exit_velocity_efficiency."""
    if npr <= 1.0:
        raise ValueError("nozzle pressure ratio must be > 1 for a fully expanded jet")
    factor = 1.0 - npr ** (-(gamma - 1.0) / gamma)
    if factor <= 0.0:
        raise ValueError("nozzle expansion factor is not positive")
    return math.sqrt(2.0 * eta_n * cp * tt * factor)


def nozzle_exit_temperature(tt: float, npr: float, gamma: float) -> float:
    """ideal_nozzle_exit_temperature."""
    return tt * npr ** (-(gamma - 1.0) / gamma)


def specific_thrust(fuel_fraction: float, ve: float, v0: float) -> float:
    """turbojet_specific_thrust."""
    return (1.0 + fuel_fraction) * ve - v0


def tsfc(fuel_fraction: float, fs: float) -> float:
    """turbojet_tsfc."""
    if fs <= 0.0:
        raise ValueError("specific thrust must be > 0")
    return fuel_fraction / fs


def thermal_efficiency(
    fuel_fraction: float, ve: float, v0: float, heating_value: float
) -> float:
    """turbojet_thermal_efficiency."""
    return ((1.0 + fuel_fraction) * ve * ve - v0 * v0) / (2.0 * fuel_fraction * heating_value)


def propulsive_efficiency(
    v0: float, fs: float, fuel_fraction: float, ve: float
) -> float:
    """turbojet_propulsive_efficiency."""
    if v0 == 0.0:
        return 0.0
    denom = (1.0 + fuel_fraction) * ve * ve - v0 * v0
    if denom <= 0.0:
        raise ValueError("kinetic energy rise is not positive")
    return 2.0 * v0 * fs / denom


def overall_efficiency(
    fs: float, v0: float, fuel_fraction: float, heating_value: float
) -> float:
    """turbojet_overall_efficiency."""
    if v0 == 0.0:
        return 0.0
    return fs * v0 / (fuel_fraction * heating_value)


def normal_shock_stagnation_pressure(mach: float, gamma: float) -> float:
    """normal_shock_stagnation_pressure. At M <= 1 the shock ratio is 1."""
    if mach <= 1.0:
        return 1.0
    g = gamma
    first = ((g + 1.0) * mach * mach) / ((g - 1.0) * mach * mach + 2.0)
    second = (g + 1.0) / (2.0 * g * mach * mach - (g - 1.0))
    return first ** (g / (g - 1.0)) * second ** (1.0 / (g - 1.0))


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
    pi_d: float = 1.0,
    eta_c: float = 1.0,
    eta_t: float = 1.0,
    eta_m: float = 1.0,
    eta_b: float = 1.0,
    pi_b: float = 1.0,
    eta_n: float = 1.0,
    match_fuel: bool = True,
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
    require_loss_ratio("inlet recovery", pi_d)
    require_efficiency("compressor efficiency", eta_c)
    require_efficiency("turbine efficiency", eta_t)
    require_efficiency("mechanical efficiency", eta_m)
    require_efficiency("burner efficiency", eta_b)
    require_loss_ratio("burner pressure ratio", pi_b)
    require_efficiency("nozzle efficiency", eta_n)

    tau_r = stagnation_temperature_ratio(mach, gamma)
    pi_r = stagnation_pressure_ratio(tau_r, gamma)
    tt0 = temperature * tau_r
    pt0 = pressure * pi_r
    a0 = speed_of_sound(temperature, gamma, gas_constant)
    v0 = mach * a0
    rho0 = pressure / (gas_constant * temperature)

    tt2 = tt0
    pt2 = pi_d * pt0
    tau_c = compressor_temperature_ratio(opr, gamma, eta_c)
    tt3 = tt2 * tau_c
    pt3 = opr * pt2
    w_c = compressor_work(cp, tt2, opr, gamma, eta_c)

    tt4 = tit
    f = fuel_air_ratio(cp, tt4, tt3, eta_b, heating_value)
    pt4 = pi_b * pt3
    f_match = f if match_fuel else 0.0
    tau_t = turbine_temperature_ratio(w_c, f_match, eta_m, cp, tt4)
    pi_t = turbine_pressure_ratio(tau_t, eta_t, gamma)
    tt5 = tt4 * tau_t
    pt5 = pi_t * pt4

    npr = pt5 / pressure
    ve = nozzle_exit_velocity(eta_n, cp, tt5, npr, gamma)
    te = nozzle_exit_temperature(tt5, npr, gamma)
    fs = specific_thrust(f, ve, v0)
    if fs <= 0.0:
        raise ValueError("specific thrust is not positive at this flight condition")
    ct = tsfc(f, fs)
    eta_th = thermal_efficiency(f, ve, v0, heating_value)
    eta_p = propulsive_efficiency(v0, fs, f, ve)
    eta_o = overall_efficiency(fs, v0, f, heating_value)

    return {
        "M": mach,
        "T0_K": temperature,
        "p0_Pa": pressure,
        "rho0_kg_m3": rho0,
        "a0_m_s": a0,
        "V0_m_s": v0,
        "tau_r": tau_r,
        "pi_r": pi_r,
        "Tt0_K": tt0,
        "pt0_Pa": pt0,
        "pi_d": pi_d,
        "Tt2_K": tt2,
        "pt2_Pa": pt2,
        "pi_c": opr,
        "eta_c": eta_c,
        "tau_c": tau_c,
        "Tt3_K": tt3,
        "pt3_Pa": pt3,
        "w_c_J_kg": w_c,
        "eta_b": eta_b,
        "pi_b": pi_b,
        "Tt4_K": tt4,
        "pt4_Pa": pt4,
        "f": f,
        "eta_t": eta_t,
        "eta_m": eta_m,
        "tau_t": tau_t,
        "pi_t": pi_t,
        "Tt5_K": tt5,
        "pt5_Pa": pt5,
        "eta_n": eta_n,
        "NPR": npr,
        "Ve_m_s": ve,
        "Te_K": te,
        "Fs_m_s": fs,
        "TSFC_kg_N_s": ct,
        "eta_th": eta_th,
        "eta_p": eta_p,
        "eta_o": eta_o,
        "gamma": gamma,
        "cp_J_kgK": cp,
        "R_J_kgK": gas_constant,
        "Q_J_kg": heating_value,
        "match_fuel": 1.0 if match_fuel else 0.0,
    }


def mach_grid(mach: float) -> list[float]:
    end = max(M_PLOT_MAX_FLOOR, M_PLOT_END_FACTOR * max(mach, 0.5))
    return [end * i / (N_PLOT - 1) for i in range(N_PLOT)]


def sweep_specific_thrust(point: dict[str, float], machs: list[float]) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for mach in machs:
        try:
            swept = solution(
                mach,
                point["T0_K"],
                point["p0_Pa"],
                point["Tt4_K"],
                point["pi_c"],
                point["gamma"],
                point["cp_J_kgK"],
                point["Q_J_kg"],
                point["R_J_kgK"],
                pi_d=point["pi_d"],
                eta_c=point["eta_c"],
                eta_t=point["eta_t"],
                eta_m=point["eta_m"],
                eta_b=point["eta_b"],
                pi_b=point["pi_b"],
                eta_n=point["eta_n"],
                match_fuel=bool(point["match_fuel"]),
            )
        except ValueError:
            continue
        xs.append(mach)
        ys.append(swept["Fs_m_s"])
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
        raise ValueError("matplotlib is required to plot the nonideal turbojet") from exc
    return plt


def plot_turbojet(path: Path, result: dict[str, float], freestream_source: str) -> None:
    plt = ensure_matplotlib()
    machs, thrusts = sweep_specific_thrust(result, mach_grid(result["M"]))
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
        f"fixed TIT = {result['Tt4_K']:.6g} K, OPR = {result['pi_c']:.6g}, "
        f"eta_c = {result['eta_c']:.6g}; freestream from {freestream_source}"
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
    print_kv("model", "design-point nonideal turbojet")
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("match_fuel", "yes" if result["match_fuel"] else "no")
    for key in (
        "M",
        "T0_K",
        "p0_Pa",
        "rho0_kg_m3",
        "a0_m_s",
        "V0_m_s",
        "Tt0_K",
        "pt0_Pa",
        "pi_d",
        "Tt2_K",
        "pt2_Pa",
        "pi_c",
        "eta_c",
        "tau_c",
        "Tt3_K",
        "pt3_Pa",
        "w_c_J_kg",
        "eta_b",
        "pi_b",
        "Tt4_K",
        "pt4_Pa",
        "f",
        "eta_t",
        "eta_m",
        "tau_t",
        "pi_t",
        "Tt5_K",
        "pt5_Pa",
        "eta_n",
        "NPR",
        "Ve_m_s",
        "Te_K",
        "Fs_m_s",
        "TSFC_kg_N_s",
        "eta_th",
        "eta_p",
        "eta_o",
        "gamma",
    ):
        print_kv(key, result[key])
    print_kv("gamma_source", gamma_source)
    print_kv("cp_J_kgK", result["cp_J_kgK"])
    print_kv("cp_source", cp_source)
    print_kv("R_J_kgK", result["R_J_kgK"])
    print_kv("Q_J_kg", result["Q_J_kg"])
    print_kv("Q_source", heating_source)
    print_kv("graph", str(path))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design-point nonideal turbojet")
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument("--temperature", type=float, default=None, help="freestream static temperature T0 [K]")
    parser.add_argument("--pressure", type=float, default=None, help="freestream static pressure p0 [Pa]")
    parser.add_argument("--tit", type=float, default=None, help="turbine inlet total temperature Tt4 [K]")
    parser.add_argument("--opr", type=float, default=None, help="compressor pressure ratio pt3/pt2")
    parser.add_argument("--pi-d", type=float, default=1.0, help="inlet total-pressure recovery; default 1")
    parser.add_argument("--eta-c", type=float, default=1.0, help="compressor isentropic efficiency; default 1")
    parser.add_argument("--eta-t", type=float, default=1.0, help="turbine isentropic efficiency; default 1")
    parser.add_argument("--eta-m", type=float, default=1.0, help="shaft mechanical efficiency; default 1")
    parser.add_argument("--eta-b", type=float, default=1.0, help="burner efficiency; default 1")
    parser.add_argument("--pi-b", type=float, default=1.0, help="burner total-pressure ratio; default 1")
    parser.add_argument("--eta-n", type=float, default=1.0, help="nozzle efficiency; default 1")
    parser.add_argument(
        "--neglect-fuel-match",
        action="store_true",
        help="neglect fuel mass in the shaft match, as on the ideal turbojet",
    )
    parser.add_argument("--heating-value", type=float, default=None, help="fuel lower heating value Q [J/kg]")
    parser.add_argument("--cp", type=float, default=None, help="cp [J/(kg*K)]")
    parser.add_argument("--gamma", type=float, default=None, help="ratio of specific heats")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def resolve_freestream(args: argparse.Namespace) -> tuple[float, float, str, float | None]:
    has_alt = args.alt is not None
    has_tp = args.temperature is not None or args.pressure is not None
    if has_alt and has_tp:
        raise ValueError("pass --alt or --temperature/--pressure, not both")
    if not has_alt and (args.temperature is None or args.pressure is None):
        raise ValueError("requires --alt, or both --temperature and --pressure")
    if has_alt:
        atmosphere, require_altitude = load_atmosphere()
        state = atmosphere(require_altitude(args.alt, "--alt"))
        return float(state["T"]), float(state["p"]), "altitude", float(state["Z"])
    require_positive("temperature", args.temperature)
    require_positive("pressure", args.pressure)
    return args.temperature, args.pressure, "temperature_pressure", None


def gas_choices(args: argparse.Namespace) -> tuple[float, str, float, str, float, str]:
    if args.gamma is None:
        gamma, gamma_source = DEFAULT_GAMMA, "default"
    else:
        require_gamma(args.gamma)
        gamma, gamma_source = args.gamma, "user"
    if args.cp is None:
        cp, cp_source = default_cp(gamma), "gamma_air_R"
    else:
        require_positive("cp", args.cp)
        cp, cp_source = args.cp, "user"
    if args.heating_value is None:
        heating, heating_source = DEFAULT_HEATING_VALUE, "default"
    else:
        require_positive("heating value", args.heating_value)
        heating, heating_source = args.heating_value, "user"
    return gamma, gamma_source, cp, cp_source, heating, heating_source


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    missing = [flag for flag, value in (("--mach", args.mach), ("--tit", args.tit), ("--opr", args.opr)) if value is None]
    if missing:
        print(
            "error: requires --mach, --tit, --opr, and (--alt or both "
            f"--temperature and --pressure); missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    try:
        temperature, pressure, freestream_source, altitude = resolve_freestream(args)
        gamma, gamma_source, cp, cp_source, heating, heating_source = gas_choices(args)
        result = solution(
            args.mach,
            temperature,
            pressure,
            args.tit,
            args.opr,
            gamma,
            cp,
            heating,
            R_AIR,
            pi_d=args.pi_d,
            eta_c=args.eta_c,
            eta_t=args.eta_t,
            eta_m=args.eta_m,
            eta_b=args.eta_b,
            pi_b=args.pi_b,
            eta_n=args.eta_n,
            match_fuel=not args.neglect_fuel_match,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "nonideal_turbojet.png"
        out_path = out_path.resolve()
        plot_turbojet(out_path, result, freestream_source)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, altitude, gamma_source, cp_source, heating_source, out_path)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    gamma = 1.4
    if near(compressor_temperature_ratio(2.0 ** (7.0 / 2.0), gamma, 1.0), 2.0, "tau ideal"):
        return 1
    if near(compressor_temperature_ratio(2.0 ** (7.0 / 2.0), gamma, 0.5), 3.0, "tau half"):
        return 1
    if near(compressor_work(1000.0, 300.0, 2.0 ** (7.0 / 2.0), gamma, 0.5), 600000.0, "work"):
        return 1
    work = compressor_work(1000.0, 300.0, 2.0 ** (7.0 / 2.0), gamma, 0.5)
    tau = compressor_temperature_ratio(2.0 ** (7.0 / 2.0), gamma, 0.5)
    if near(work, 1000.0 * 300.0 * (tau - 1.0), "work matches enthalpy"):
        return 1
    if near(turbine_temperature_ratio(600000.0, 0.2, 1.0, 1000.0, 1200.0), 7.0 / 12.0, "tau_t"):
        return 1
    if near(turbine_pressure_ratio(0.5, 1.0, gamma), 0.5 ** (7.0 / 2.0), "pi_t"):
        return 1

    folder = str(IDEAL_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import ideal_turbojet as ideal

    t0 = 216.65
    p0 = 19330.0
    cp = default_cp(gamma)
    ideal_point = ideal.solution(0.8, t0, p0, 1600.0, 20.0, gamma, cp, DEFAULT_HEATING_VALUE, R_AIR)
    limit = solution(
        0.8,
        t0,
        p0,
        1600.0,
        20.0,
        gamma,
        cp,
        DEFAULT_HEATING_VALUE,
        R_AIR,
        match_fuel=False,
    )
    for key in ("f", "Tt3_K", "tau_t", "pi_t", "NPR", "Ve_m_s", "Fs_m_s", "TSFC_kg_N_s", "eta_th"):
        if near(limit[key], ideal_point[key], f"ideal limit {key}"):
            return 1
    fueled = solution(
        0.8, t0, p0, 1600.0, 20.0, gamma, cp, DEFAULT_HEATING_VALUE, R_AIR, match_fuel=True
    )
    if fueled["f"] <= 0.0:
        return fail("fuel-air ratio not positive")
    if not (fueled["tau_t"] > limit["tau_t"]):
        return fail("fuel in the match should reduce the turbine temperature drop")
    lossy = solution(
        0.0,
        288.15,
        101325.0,
        1600.0,
        10.0,
        gamma,
        cp,
        DEFAULT_HEATING_VALUE,
        R_AIR,
        eta_c=0.85,
        eta_t=0.9,
        eta_b=0.98,
        pi_b=0.95,
        pi_d=0.97,
        match_fuel=True,
    )
    ideal_eta = solution(
        0.0,
        288.15,
        101325.0,
        1600.0,
        10.0,
        gamma,
        cp,
        DEFAULT_HEATING_VALUE,
        R_AIR,
        match_fuel=True,
    )
    if not (lossy["Tt3_K"] > ideal_eta["Tt3_K"]):
        return fail("lower compressor efficiency should raise Tt3")
    if not (lossy["Fs_m_s"] < ideal_eta["Fs_m_s"]):
        return fail("component losses should lower specific thrust")
    if abs(lossy["eta_o"] - lossy["eta_th"] * lossy["eta_p"]) > CHECK_TOL * max(1.0, abs(lossy["eta_o"])):
        return fail("eta_o is not eta_th*eta_p")

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out, err = _Capture(), _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as folder_name:
        png = Path(folder_name) / "nonideal_turbojet.png"
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
                "--eta-c",
                "0.88",
                "--pi-d",
                "0.98",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli failed: {err}")
        if "freestream_source: temperature_pressure" not in text:
            return fail("cli did not report temperature_pressure")
        if "Fs_m_s:" not in text or "eta_c: 0.88" not in text:
            return fail("cli omitted specific thrust or eta_c")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
        code, _text, err = capture(
            ["--mach", "0.8", "--alt", "0", "--temperature", "288.15", "--pressure", "101325", "--tit", "1600", "--opr", "8"]
        )
        if code == 0:
            return fail("both freestream paths should fail")
    return 0


if __name__ == "__main__":
    sys.exit(main())
