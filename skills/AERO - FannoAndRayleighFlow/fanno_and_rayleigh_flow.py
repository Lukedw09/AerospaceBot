#!/usr/bin/env python3
"""Fanno or Rayleigh constant-area duct ratios for a calorically perfect gas.

Fanno records: fanno_temperature_ratio, fanno_pressure_ratio,
fanno_density_ratio, fanno_velocity_ratio, fanno_stagnation_pressure_ratio,
fanno_friction_parameter.
Rayleigh records: rayleigh_stagnation_temperature_ratio,
rayleigh_temperature_ratio, rayleigh_pressure_ratio, rayleigh_density_ratio,
rayleigh_stagnation_pressure_ratio, rayleigh_velocity_ratio.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
SONIC_TOL = 1e-6
TABLE_TOL = 5e-4
DEFAULT_GAMMA = 1.4
N_CURVE = 401
MACH_MIN = 1.0e-3
MACH_MAX = 50.0
M_PLOT_LO = 0.05
M_PLOT_HI = 5.0

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "calorically perfect gas; constant-area duct; "
    "exactly one of Fanno (adiabatic, friction) or Rayleigh (frictionless, heat); "
    "ratios are to the sonic reference; "
    "fanno_temperature_ratio, fanno_pressure_ratio, fanno_density_ratio, "
    "fanno_velocity_ratio, fanno_stagnation_pressure_ratio, fanno_friction_parameter; "
    "rayleigh_stagnation_temperature_ratio, rayleigh_temperature_ratio, "
    "rayleigh_pressure_ratio, rayleigh_density_ratio, "
    "rayleigh_stagnation_pressure_ratio, rayleigh_velocity_ratio; "
    f"an omitted --gamma is {DEFAULT_GAMMA:g} (air); "
    "a duct longer than 4fL*/D is choked; "
    "Rayleigh flow is choked when Tt2 exceeds Tt*, not when Tt2/Tt1 exceeds 1; "
    "a supplied sonic length or heat ratio within 1e-6 of the limit is the sonic exit, not a choke; "
    "four_f_L_remaining_over_D is the length still available and is never negative; "
    "combined friction and heat addition is not solved"
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
    if not math.isfinite(mach) or mach < MACH_MIN or mach > MACH_MAX:
        raise ValueError("Mach must satisfy 0.001 <= M <= 50")


def fanno_temperature_ratio(mach: float, gamma: float) -> float:
    return (gamma + 1.0) / (2.0 + (gamma - 1.0) * mach * mach)


def fanno_pressure_ratio(mach: float, gamma: float) -> float:
    return (1.0 / mach) * math.sqrt(fanno_temperature_ratio(mach, gamma))


def fanno_density_ratio(mach: float, gamma: float) -> float:
    return (1.0 / mach) / math.sqrt(fanno_temperature_ratio(mach, gamma))


def fanno_velocity_ratio(mach: float, gamma: float) -> float:
    return mach * math.sqrt(fanno_temperature_ratio(mach, gamma))


def fanno_stagnation_pressure_ratio(mach: float, gamma: float) -> float:
    base = (2.0 + (gamma - 1.0) * mach * mach) / (gamma + 1.0)
    return (1.0 / mach) * base ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))


def fanno_friction_parameter(mach: float, gamma: float) -> float:
    argument = ((gamma + 1.0) * mach * mach) / (2.0 + (gamma - 1.0) * mach * mach)
    return (1.0 - mach * mach) / (gamma * mach * mach) + (
        (gamma + 1.0) / (2.0 * gamma)
    ) * math.log(argument)


def rayleigh_stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    return (
        2.0
        * (gamma + 1.0)
        * mach
        * mach
        * (1.0 + 0.5 * (gamma - 1.0) * mach * mach)
        / (1.0 + gamma * mach * mach) ** 2
    )


def rayleigh_temperature_ratio(mach: float, gamma: float) -> float:
    return (gamma + 1.0) ** 2 * mach * mach / (1.0 + gamma * mach * mach) ** 2


def rayleigh_pressure_ratio(mach: float, gamma: float) -> float:
    return (gamma + 1.0) / (1.0 + gamma * mach * mach)


def rayleigh_density_ratio(mach: float, gamma: float) -> float:
    return (1.0 + gamma * mach * mach) / ((gamma + 1.0) * mach * mach)


def rayleigh_stagnation_pressure_ratio(mach: float, gamma: float) -> float:
    return rayleigh_pressure_ratio(mach, gamma) * (
        (2.0 + (gamma - 1.0) * mach * mach) / (gamma + 1.0)
    ) ** (gamma / (gamma - 1.0))


def rayleigh_velocity_ratio(mach: float, gamma: float) -> float:
    return (gamma + 1.0) * mach * mach / (1.0 + gamma * mach * mach)


def _bisect(func, lo: float, hi: float, target: float) -> float:
    flo = func(lo) - target
    fhi = func(hi) - target
    if not math.isfinite(flo) or not math.isfinite(fhi) or flo * fhi > 0.0:
        raise ValueError("exit Mach is not on this branch")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fmid = func(mid) - target
        if abs(fmid) < 1e-12 or abs(hi - lo) < 1e-12 * max(1.0, abs(mid)):
            return mid
        if flo * fmid <= 0.0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid
    return 0.5 * (lo + hi)


def _sonic_band(limit: float) -> float:
    """Width that still round-trips through 8 significant figures or 6 decimals."""
    return SONIC_TOL * max(1.0, abs(limit))


def fanno_exit_mach(mach: float, gamma: float, fld: float) -> tuple[float | None, str]:
    remain_inlet = fanno_friction_parameter(mach, gamma)
    if fld > remain_inlet + _sonic_band(remain_inlet):
        return None, "yes"
    if fld < -1e-12:
        raise ValueError("--fld must be >= 0")
    target = remain_inlet - fld
    if target <= _sonic_band(remain_inlet):
        return 1.0, "no"
    if mach < 1.0:
        lo, hi = MACH_MIN, 1.0 - 1e-9
    else:
        lo, hi = 1.0 + 1e-9, MACH_MAX
    exit_mach = _bisect(lambda value: fanno_friction_parameter(value, gamma), lo, hi, target)
    return exit_mach, "no"


def rayleigh_exit_mach(mach: float, gamma: float, tt_ratio: float) -> tuple[float | None, str]:
    if tt_ratio <= 0.0 or not math.isfinite(tt_ratio):
        raise ValueError("--tt-ratio must be finite and > 0")
    inlet = rayleigh_stagnation_temperature_ratio(mach, gamma)
    target = tt_ratio * inlet
    if target > 1.0 + SONIC_TOL:
        return None, "yes"
    target = min(target, 1.0)
    if mach < 1.0:
        lo, hi = MACH_MIN, 1.0 - 1e-9
    else:
        lo, hi = 1.0 + 1e-9, MACH_MAX
    exit_mach = _bisect(
        lambda value: rayleigh_stagnation_temperature_ratio(value, gamma),
        lo,
        hi,
        target,
    )
    return exit_mach, "no"


def duct_state(mode: str, mach: float, gamma: float) -> dict[str, float]:
    require_mach(mach)
    require_gamma(gamma)
    if mode == "fanno":
        state = {
            "T_over_Tstar": fanno_temperature_ratio(mach, gamma),
            "p_over_pstar": fanno_pressure_ratio(mach, gamma),
            "rho_over_rhostar": fanno_density_ratio(mach, gamma),
            "pt_over_ptstar": fanno_stagnation_pressure_ratio(mach, gamma),
            "V_over_Vstar": fanno_velocity_ratio(mach, gamma),
            "four_f_Lmax_over_D": fanno_friction_parameter(mach, gamma),
        }
    elif mode == "rayleigh":
        state = {
            "Tt_over_Ttstar": rayleigh_stagnation_temperature_ratio(mach, gamma),
            "T_over_Tstar": rayleigh_temperature_ratio(mach, gamma),
            "p_over_pstar": rayleigh_pressure_ratio(mach, gamma),
            "rho_over_rhostar": rayleigh_density_ratio(mach, gamma),
            "pt_over_ptstar": rayleigh_stagnation_pressure_ratio(mach, gamma),
            "V_over_Vstar": rayleigh_velocity_ratio(mach, gamma),
        }
    else:
        raise ValueError("mode must be fanno or rayleigh")
    state["M"] = mach
    state["gamma"] = gamma
    return state


def emit(mode: str, result: dict[str, object], gamma_source: str, graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", mode)
    print_kv("M", result["M"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    for key in (
        "T_over_Tstar",
        "p_over_pstar",
        "rho_over_rhostar",
        "pt_over_ptstar",
        "V_over_Vstar",
        "four_f_Lmax_over_D",
        "Tt_over_Ttstar",
        "fld",
        "four_f_L_remaining_over_D",
        "tt_ratio",
        "exit_mach",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("choked", result["choked"])
    if "choked_by_length" in result:
        print_kv("choked_by_length", result["choked_by_length"])
    if "choked_by_heat" in result:
        print_kv("choked_by_heat", result["choked_by_heat"])
    print_kv("graph", str(graph))


def plot_grid(mach: float) -> list[float]:
    hi = max(M_PLOT_HI, mach * 1.25)
    return [M_PLOT_LO * (hi / M_PLOT_LO) ** (i / (N_CURVE - 1)) for i in range(N_CURVE)]


def write_plot(mode: str, result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    mach = float(result["M"])
    gamma = float(result["gamma"])
    grid = plot_grid(mach)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    if mode == "fanno":
        series = (
            ("T_over_Tstar", r"$T/T^{*}$", fanno_temperature_ratio),
            ("p_over_pstar", r"$p/p^{*}$", fanno_pressure_ratio),
            ("rho_over_rhostar", r"$\rho/\rho^{*}$", fanno_density_ratio),
            ("pt_over_ptstar", r"$p_t/p_t^{*}$", fanno_stagnation_pressure_ratio),
            ("V_over_Vstar", r"$V/V^{*}$", fanno_velocity_ratio),
        )
        title = "Fanno flow ratios"
    else:
        series = (
            ("Tt_over_Ttstar", r"$T_t/T_t^{*}$", rayleigh_stagnation_temperature_ratio),
            ("T_over_Tstar", r"$T/T^{*}$", rayleigh_temperature_ratio),
            ("p_over_pstar", r"$p/p^{*}$", rayleigh_pressure_ratio),
            ("rho_over_rhostar", r"$\rho/\rho^{*}$", rayleigh_density_ratio),
            ("V_over_Vstar", r"$V/V^{*}$", rayleigh_velocity_ratio),
        )
        title = "Rayleigh flow ratios"
    for index, (key, label, func) in enumerate(series):
        curve = [func(value, gamma) for value in grid]
        ax.plot(grid, curve, color=f"C{index}", label=label)
        ax.plot(mach, float(result[key]), "s", color=f"C{index}")
    ax.axvline(mach, color="0.6", linestyle=":")
    ax.set_xscale("log")
    ax.set_xlabel(r"Mach number $M$")
    ax.set_ylabel("Ratio to the sonic state")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    gamma = 7.0 / 5.0
    for mode, builder in (
        (
            "fanno",
            lambda mach: {
                "T": fanno_temperature_ratio(mach, gamma),
                "p": fanno_pressure_ratio(mach, gamma),
                "rho": fanno_density_ratio(mach, gamma),
                "V": fanno_velocity_ratio(mach, gamma),
                "pt": fanno_stagnation_pressure_ratio(mach, gamma),
            },
        ),
        (
            "rayleigh",
            lambda mach: {
                "T": rayleigh_temperature_ratio(mach, gamma),
                "p": rayleigh_pressure_ratio(mach, gamma),
                "rho": rayleigh_density_ratio(mach, gamma),
                "V": rayleigh_velocity_ratio(mach, gamma),
                "pt": rayleigh_stagnation_pressure_ratio(mach, gamma),
                "Tt": rayleigh_stagnation_temperature_ratio(mach, gamma),
            },
        ),
    ):
        sonic = builder(1.0)
        for key, value in sonic.items():
            if not close(value, 1.0):
                return fail(f"{mode} sonic {key} is not 1")
    if not close(fanno_friction_parameter(1.0, gamma), 0.0):
        return fail("sonic Fanno friction parameter is not 0")
    if not close(fanno_velocity_ratio(2.0, gamma) * fanno_density_ratio(2.0, gamma), 1.0):
        return fail("Fanno V/V* is not 1 over rho/rho*")
    if not close(fanno_temperature_ratio(2.0, gamma), 2.0 / 3.0):
        return fail("Fanno Mach 2 temperature ratio is not 2/3")
    if not close(rayleigh_pressure_ratio(2.0, gamma), 4.0 / 11.0):
        return fail("Rayleigh Mach 2 pressure ratio is not 4/11")
    if not close(rayleigh_velocity_ratio(2.0, gamma), 16.0 / 11.0):
        return fail("Rayleigh Mach 2 velocity ratio is not 16/11")

    # Melcher example 4.11, air, Mach 3.5, four printed decimals.
    melcher = duct_state("fanno", 3.5, gamma)
    expected_fanno = {
        "T_over_Tstar": 0.3478,
        "p_over_pstar": 0.1685,
        "pt_over_ptstar": 6.7896,
        "V_over_Vstar": 2.0642,
        "four_f_Lmax_over_D": 0.5864,
    }
    for key, expected in expected_fanno.items():
        if not close(float(melcher[key]), expected, TABLE_TOL):
            return fail(f"Melcher Fanno {key} is {melcher[key]}, expected {expected}")

    # Melcher example 4.24, Mach 0.72, properties 2 through 6.
    ray = duct_state("rayleigh", 0.72, gamma)
    expected_ray = {
        "Tt_over_Ttstar": 0.9221,
        "T_over_Tstar": 1.0026,
        "p_over_pstar": 1.3907,
        "pt_over_ptstar": 1.0376,
        "V_over_Vstar": 0.7209,
    }
    for key, expected in expected_ray.items():
        if not close(float(ray[key]), expected, TABLE_TOL):
            return fail(f"Melcher Rayleigh {key} is {ray[key]}, expected {expected}")

    exit_mach, choked = fanno_exit_mach(0.5, gamma, 0.0)
    if choked != "no" or exit_mach is None or not close(exit_mach, 0.5, 1e-8):
        return fail("zero friction length did not keep the inlet Mach")
    _none, choked_long = fanno_exit_mach(0.5, gamma, fanno_friction_parameter(0.5, gamma) + 0.1)
    if choked_long != "yes":
        return fail("an over-long Fanno duct was not choked")
    printed_length = float(f"{fanno_friction_parameter(0.4, gamma):.8g}")
    printed_exit, printed_choke = fanno_exit_mach(0.4, gamma, printed_length)
    if printed_choke != "no" or printed_exit is None or abs(printed_exit - 1.0) > 1e-4:
        return fail("the printed Fanno sonic length round-tripped as choked")
    # The printed Tt/Tt* has 8 figures. Its reciprocal must still be the sonic exit.
    tt_star = float(f"{rayleigh_stagnation_temperature_ratio(0.5, gamma):.8g}")
    heat_exit, heat_choke = rayleigh_exit_mach(0.5, gamma, 1.0 / tt_star)
    if heat_choke != "no" or heat_exit is None or abs(heat_exit - 1.0) > 1e-3:
        return fail("the printed Rayleigh sonic temperature ratio round-tripped as choked")
    hot, choked_heat = rayleigh_exit_mach(0.5, gamma, 1.0 / rayleigh_stagnation_temperature_ratio(0.5, gamma) + 0.1)
    if hot is not None or choked_heat != "yes":
        return fail("excess Rayleigh heat was not choked")

    try:
        duct_state("fanno", 0.0, gamma)
        return fail("zero Mach was accepted")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot("fanno", melcher, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")

    print("check: pass")
    print_kv("fanno_T_over_Tstar_mach_3p5", melcher["T_over_Tstar"])
    print_kv("fanno_four_f_Lmax_over_D_mach_3p5", melcher["four_f_Lmax_over_D"])
    print_kv("rayleigh_Tt_over_Ttstar_mach_0p72", ray["Tt_over_Ttstar"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fanno or Rayleigh sonic-reference ratios at one Mach number."
    )
    parser.add_argument("--fanno", action="store_true", help="adiabatic constant-area flow with friction")
    parser.add_argument("--rayleigh", action="store_true", help="frictionless constant-area flow with heat addition")
    parser.add_argument("--mach", type=float, default=None, help="station Mach number, M > 0")
    parser.add_argument("--gamma", type=float, default=None, help=f"ratio of specific heats (default {DEFAULT_GAMMA})")
    parser.add_argument("--fld", type=float, default=None, help="Fanno 4fL/D from this station toward Mach 1")
    parser.add_argument("--tt-ratio", type=float, default=None, dest="tt_ratio", help="Rayleigh stagnation-temperature ratio Tt2/Tt1")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.fanno == args.rayleigh:
        print("error: pass exactly one of --fanno or --rayleigh", file=sys.stderr)
        return 2
    if args.mach is None:
        print("error: requires --mach", file=sys.stderr)
        return 2
    mode = "fanno" if args.fanno else "rayleigh"
    if mode == "fanno" and args.tt_ratio is not None:
        print("error: --tt-ratio is a Rayleigh input", file=sys.stderr)
        return 2
    if mode == "rayleigh" and args.fld is not None:
        print("error: --fld is a Fanno input", file=sys.stderr)
        return 2
    if args.gamma is None:
        gamma = DEFAULT_GAMMA
        gamma_source = "default"
    else:
        gamma = args.gamma
        gamma_source = "flag"
    try:
        result: dict[str, object] = dict(duct_state(mode, args.mach, gamma))
        result["choked"] = "yes" if abs(float(result["M"]) - 1.0) <= 1e-6 else "no"
        if args.fld is not None:
            exit_mach, choked_length = fanno_exit_mach(args.mach, gamma, args.fld)
            result["fld"] = args.fld
            result["four_f_L_remaining_over_D"] = max(
                0.0, float(result["four_f_Lmax_over_D"]) - args.fld
            )
            result["choked_by_length"] = choked_length
            if exit_mach is not None:
                result["exit_mach"] = exit_mach
        if args.tt_ratio is not None:
            exit_mach, choked_heat = rayleigh_exit_mach(args.mach, gamma, args.tt_ratio)
            result["tt_ratio"] = args.tt_ratio
            result["choked_by_heat"] = choked_heat
            if exit_mach is not None:
                result["exit_mach"] = exit_mach
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = args.out if args.out is not None else SKILL_DIR / "fanno_and_rayleigh_flow.png"
    try:
        write_plot(mode, result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(mode, result, gamma_source, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
