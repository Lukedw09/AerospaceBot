#!/usr/bin/env python3
"""Isentropic stagnation and sonic reference states for a perfect gas.

stagnation_temperature is Tt/T = 1 + ((gamma-1)/2)*M**2.
stagnation_pressure is pt/p = (Tt/T)**(gamma/(gamma-1)).
stagnation_density is rhot/rho = (Tt/T)**(1/(gamma-1)).
stagnation_sound_speed is at/a = sqrt(Tt/T).
sonic_temperature, sonic_pressure, and sonic_density are T*/Tt, p*/pt,
and rho*/rhot. speed_of_sound is a = sqrt(gamma*R*T) = sqrt(gamma*p/rho).
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
DEFAULT_GAMMA = 1.4
# 1976 dry-air R* / M0 from formulas.md (specific_gas_constant).
RSTAR = 8.31432e3
M0 = 28.9644
DEFAULT_R = RSTAR / M0
PLOT_TITLE = "Isentropic stagnation ratios"
N_CURVE = 401
MACH_MAX = 1.0e6
M_PLOT_DEFAULT_HI = 3.0

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "calorically perfect gas; steady isentropic flow; no shock; "
    "stagnation_temperature Tt/T = 1 + ((gamma-1)/2)*M**2; "
    "stagnation_pressure pt/p = (Tt/T)**(gamma/(gamma-1)); "
    "stagnation_density rhot/rho = (Tt/T)**(1/(gamma-1)); "
    "stagnation_sound_speed at/a = (Tt/T)**0.5; "
    "sonic_temperature T*/Tt = 2/(gamma+1); "
    "sonic_pressure p*/pt = (2/(gamma+1))**(gamma/(gamma-1)); "
    "sonic_density rho*/rhot = (2/(gamma+1))**(1/(gamma-1)); "
    "speed_of_sound a = sqrt(gamma*R*T) = sqrt(gamma*p/rho); "
    "absolute totals and sonic states only for each static that was given; "
    f"an omitted --gamma is {DEFAULT_GAMMA:g} (air); "
    f"an omitted R with --temperature alone is {DEFAULT_R:.8g} J/(kg*K) "
    "(1976 dry air); "
    "M >= 0"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_gamma(gamma: float) -> None:
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("gamma must be finite and > 1")


def require_mach(mach: float) -> None:
    if not math.isfinite(mach) or mach < 0.0 or mach > MACH_MAX:
        raise ValueError("Mach must satisfy 0 <= M <= 1e6")


def stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    """stagnation_temperature: Tt/T."""
    return 1.0 + 0.5 * (gamma - 1.0) * mach * mach


def stagnation_pressure_ratio(mach: float, gamma: float) -> float:
    """stagnation_pressure from stagnation_temperature."""
    t_ratio = stagnation_temperature_ratio(mach, gamma)
    return t_ratio ** (gamma / (gamma - 1.0))


def stagnation_density_ratio(mach: float, gamma: float) -> float:
    """stagnation_density from stagnation_temperature."""
    t_ratio = stagnation_temperature_ratio(mach, gamma)
    return t_ratio ** (1.0 / (gamma - 1.0))


def stagnation_sound_speed_ratio(mach: float, gamma: float) -> float:
    """stagnation_sound_speed: at/a."""
    return math.sqrt(stagnation_temperature_ratio(mach, gamma))


def sonic_temperature_ratio(gamma: float) -> float:
    """sonic_temperature: T*/Tt."""
    return 2.0 / (gamma + 1.0)


def sonic_pressure_ratio(gamma: float) -> float:
    """sonic_pressure: p*/pt."""
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def sonic_density_ratio(gamma: float) -> float:
    """sonic_density: rho*/rhot."""
    return (2.0 / (gamma + 1.0)) ** (1.0 / (gamma - 1.0))


def speed_of_sound_from_temperature(gamma: float, gas_constant: float, temperature: float) -> float:
    """speed_of_sound: a = sqrt(gamma*R*T)."""
    return math.sqrt(gamma * gas_constant * temperature)


def speed_of_sound_from_pressure_density(gamma: float, pressure: float, density: float) -> float:
    """speed_of_sound: a = sqrt(gamma*p/rho)."""
    return math.sqrt(gamma * pressure / density)


def resolve_gas_constant(
    temperature: float | None,
    pressure: float | None,
    density: float | None,
) -> tuple[float | None, str | None]:
    """R from p/(rho*T) when all three exist, else 1976 air with temperature alone."""
    if (
        temperature is not None
        and pressure is not None
        and density is not None
    ):
        return pressure / (density * temperature), "equation_of_state"
    if temperature is not None:
        return DEFAULT_R, "default_air"
    return None, None


def stagnation_state(
    mach: float,
    gamma: float,
    temperature: float | None,
    pressure: float | None,
    density: float | None,
) -> dict[str, float | str | None]:
    require_mach(mach)
    require_gamma(gamma)
    if temperature is not None:
        if not math.isfinite(temperature) or temperature <= 0.0:
            raise ValueError("static temperature must be finite and > 0 K")
    if pressure is not None:
        if not math.isfinite(pressure) or pressure <= 0.0:
            raise ValueError("static pressure must be finite and > 0 Pa")
    if density is not None:
        if not math.isfinite(density) or density <= 0.0:
            raise ValueError("static density must be finite and > 0 kg/m^3")

    tt_over_t = stagnation_temperature_ratio(mach, gamma)
    pt_over_p = stagnation_pressure_ratio(mach, gamma)
    rhot_over_rho = stagnation_density_ratio(mach, gamma)
    at_over_a = stagnation_sound_speed_ratio(mach, gamma)
    tstar_over_tt = sonic_temperature_ratio(gamma)
    pstar_over_pt = sonic_pressure_ratio(gamma)
    rhostar_over_rhot = sonic_density_ratio(gamma)

    tt = temperature * tt_over_t if temperature is not None else None
    pt = pressure * pt_over_p if pressure is not None else None
    rhot = density * rhot_over_rho if density is not None else None
    t_star = tt * tstar_over_tt if tt is not None else None
    p_star = pt * pstar_over_pt if pt is not None else None
    rho_star = rhot * rhostar_over_rhot if rhot is not None else None

    gas_constant, r_source = resolve_gas_constant(temperature, pressure, density)
    a: float | None = None
    a_source: str | None = None
    if pressure is not None and density is not None:
        a = speed_of_sound_from_pressure_density(gamma, pressure, density)
        a_source = "pressure_density"
    elif temperature is not None and gas_constant is not None:
        a = speed_of_sound_from_temperature(gamma, gas_constant, temperature)
        a_source = "temperature"
    a_t = a * at_over_a if a is not None else None

    return {
        "M": mach,
        "gamma": gamma,
        "T": temperature,
        "p": pressure,
        "rho": density,
        "Tt_over_T": tt_over_t,
        "pt_over_p": pt_over_p,
        "rhot_over_rho": rhot_over_rho,
        "at_over_a": at_over_a,
        "Tt": tt,
        "pt": pt,
        "rhot": rhot,
        "Tstar_over_Tt": tstar_over_tt,
        "pstar_over_pt": pstar_over_pt,
        "rhostar_over_rhot": rhostar_over_rhot,
        "T_star": t_star,
        "p_star": p_star,
        "rho_star": rho_star,
        "R": gas_constant,
        "R_source": r_source,
        "a": a,
        "a_source": a_source,
        "a_t": a_t,
    }


def emit(
    result: dict[str, float | str | None],
    gamma_source: str,
    graph: Path | None,
) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("M", result["M"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("Tt_over_T", result["Tt_over_T"])
    print_kv("pt_over_p", result["pt_over_p"])
    print_kv("rhot_over_rho", result["rhot_over_rho"])
    print_kv("at_over_a", result["at_over_a"])
    print_kv("Tstar_over_Tt", result["Tstar_over_Tt"])
    print_kv("pstar_over_pt", result["pstar_over_pt"])
    print_kv("rhostar_over_rhot", result["rhostar_over_rhot"])
    if result["T"] is not None:
        print_kv("T_K", result["T"])
        print_kv("Tt_K", result["Tt"])
        print_kv("T_star_K", result["T_star"])
    if result["p"] is not None:
        print_kv("p_Pa", result["p"])
        print_kv("pt_Pa", result["pt"])
        print_kv("p_star_Pa", result["p_star"])
    if result["rho"] is not None:
        print_kv("rho_kg_m3", result["rho"])
        print_kv("rhot_kg_m3", result["rhot"])
        print_kv("rho_star_kg_m3", result["rho_star"])
    if result["R"] is not None:
        print_kv("R_J_kgK", result["R"])
        print_kv("R_source", result["R_source"])
    if result["a"] is not None:
        print_kv("a_m_s", result["a"])
        print_kv("a_source", result["a_source"])
        print_kv("a_t_m_s", result["a_t"])
    if graph is not None:
        print_kv("graph", str(graph))


def plot_mach_grid(mach: float) -> list[float]:
    hi = max(M_PLOT_DEFAULT_HI, mach * 1.15 if mach > 0.0 else M_PLOT_DEFAULT_HI)
    return [i / (N_CURVE - 1) * hi for i in range(N_CURVE)]


def write_plot(result: dict[str, float | str | None], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    mach = float(result["M"])
    gamma = float(result["gamma"])
    m_grid = plot_mach_grid(mach)
    t_ratio = [stagnation_temperature_ratio(m, gamma) for m in m_grid]
    p_ratio = [stagnation_pressure_ratio(m, gamma) for m in m_grid]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(m_grid, p_ratio, color="C0", label=r"$p_t/p$")
    ax.plot(m_grid, t_ratio, color="C3", label=r"$T_t/T$")
    ax.plot(mach, float(result["pt_over_p"]), "s", color="C0")
    ax.plot(mach, float(result["Tt_over_T"]), "s", color="C3")
    ax.axvline(mach, color="0.6", linestyle=":")
    ax.axvline(1.0, color="0.7", linestyle="--", linewidth=0.9, label=r"$M=1$")
    ax.set_xlabel(r"Mach number $M$")
    ax.set_ylabel(r"Isentropic stagnation ratios")
    ax.legend(loc="best", frameon=False)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0.0, m_grid[-1])
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    gamma = 7.0 / 5.0

    rest = stagnation_state(0.0, gamma, 300.0, 101325.0, 1.225)
    if not close(float(rest["Tt_over_T"]), 1.0):
        return fail("M=0 temperature ratio is not 1")
    if not close(float(rest["pt_over_p"]), 1.0):
        return fail("M=0 pressure ratio is not 1")
    if not close(float(rest["rhot_over_rho"]), 1.0):
        return fail("M=0 density ratio is not 1")
    if not close(float(rest["Tt"]), 300.0):
        return fail("M=0 total temperature is not static temperature")

    # Air identities at M = 1: Tt/T = 1.2, pt/p = 1.2**3.5, T*/Tt = 5/6.
    sonic = stagnation_state(1.0, gamma, 250.0, None, None)
    if not close(float(sonic["Tt_over_T"]), 1.2):
        return fail("air M=1 Tt/T is not 1.2")
    if not close(float(sonic["pt_over_p"]), 1.2**3.5):
        return fail("air M=1 pt/p is not 1.2**(7/2)")
    if not close(float(sonic["rhot_over_rho"]), 1.2**2.5):
        return fail("air M=1 rhot/rho is not 1.2**(5/2)")
    if not close(float(sonic["Tstar_over_Tt"]), 5.0 / 6.0):
        return fail("air T*/Tt is not 5/6")
    if not close(float(sonic["Tt"]), 300.0):
        return fail("air M=1 Tt from T=250 K is not 300 K")
    if not close(float(sonic["T_star"]), 250.0):
        return fail("air M=1 T* is not equal to static T")

    # Air M = 2: Tt/T = 1 + 4/5 = 1.8.
    two = stagnation_state(2.0, gamma, 288.15, 101325.0, 1.225)
    if not close(float(two["Tt_over_T"]), 1.8):
        return fail("air M=2 Tt/T is not 1.8")
    expected_pt = 1.8 ** 3.5
    if not close(float(two["pt_over_p"]), expected_pt):
        return fail("air M=2 pt/p does not match")
    if not close(float(two["rhot_over_rho"]), 1.8**2.5):
        return fail("air M=2 rhot/rho does not match")
    if not close(float(two["at_over_a"]), math.sqrt(1.8)):
        return fail("air M=2 at/a is not sqrt(Tt/T)")

    # speed_of_sound identity: sqrt(gamma*p/rho) equals sqrt(gamma*R*T).
    r_eos = 101325.0 / (1.225 * 288.15)
    a_pr = speed_of_sound_from_pressure_density(gamma, 101325.0, 1.225)
    a_tr = speed_of_sound_from_temperature(gamma, r_eos, 288.15)
    if not close(a_pr, a_tr):
        return fail("pressure-density and temperature sound speeds disagree")
    if two["a_source"] != "pressure_density":
        return fail("full state did not prefer pressure-density sound speed")
    if not close(float(two["a"]), a_pr):
        return fail("reported sound speed does not match sqrt(gamma*p/rho)")
    if not close(float(two["a_t"]), a_pr * math.sqrt(1.8)):
        return fail("total sound speed is not a*sqrt(Tt/T)")

    # Sonic absolute from stagnation only when that static was given.
    p_only = stagnation_state(1.0, gamma, None, 100000.0, None)
    if p_only["Tt"] is not None or p_only["T_star"] is not None:
        return fail("temperature totals were invented without static T")
    if p_only["pt"] is None or p_only["p_star"] is None:
        return fail("pressure totals missing for given static p")
    if not close(float(p_only["p_star"]), 100000.0 * float(p_only["pt_over_p"]) * float(p_only["pstar_over_pt"])):
        return fail("p* is not pt*(p*/pt)")

    mono = stagnation_state(1.0, 5.0 / 3.0, None, None, None)
    if not close(float(mono["Tt_over_T"]), 4.0 / 3.0):
        return fail("monatomic M=1 Tt/T is not 4/3")
    if not close(float(mono["Tstar_over_Tt"]), 0.75):
        return fail("monatomic T*/Tt is not 3/4")

    try:
        stagnation_state(-0.1, gamma, None, None, None)
        return fail("negative Mach was accepted")
    except ValueError:
        pass
    try:
        stagnation_state(1.0, 1.0, None, None, None)
        return fail("gamma = 1 was accepted")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(two, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")

    print("check: pass")
    print_kv("Tt_over_T_air_two", two["Tt_over_T"])
    print_kv("pt_over_p_air_two", two["pt_over_p"])
    print_kv("a_m_s_air_two", two["a"])
    print_kv("a_t_m_s_air_two", two["a_t"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Isentropic stagnation temperature, pressure, and density, "
            "sonic reference state, and speeds of sound."
        )
    )
    parser.add_argument(
        "--mach",
        type=float,
        default=None,
        help="Mach number, M >= 0",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="static temperature T in kelvin",
    )
    parser.add_argument(
        "--pressure",
        type=float,
        default=None,
        help="static pressure p in pascals",
    )
    parser.add_argument(
        "--density",
        type=float,
        default=None,
        help="static density rho in kg/m^3",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional PNG path for pt/p and Tt/T versus Mach",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.mach is None:
        print("error: requires --mach", file=sys.stderr)
        return 2

    if args.gamma is None:
        gamma = DEFAULT_GAMMA
        gamma_source = "default"
    else:
        gamma = args.gamma
        gamma_source = "flag"

    try:
        result = stagnation_state(
            args.mach,
            gamma,
            args.temperature,
            args.pressure,
            args.density,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph: Path | None = None
    if args.out is not None:
        out_path = args.out
        try:
            write_plot(result, out_path)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = out_path

    emit(result, gamma_source, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
