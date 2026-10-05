#!/usr/bin/env python3
"""Steady normal-shock jumps for a calorically perfect gas.

normal_shock_mach is M2**2.
normal_shock_pressure, normal_shock_temperature, and normal_shock_density
are the static ratios p2/p1, T2/T1, and rho2/rho1.
normal_shock_stagnation_pressure is pt2/pt1.
normal_shock_entropy_over_r is Delta s / R = -ln(pt2/pt1).
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
DEFAULT_GAMMA = 1.4
PLOT_TITLE = "Normal shock ratios"
N_CURVE = 401
MACH_MAX = 1.0e6
M_PLOT_MIN = 1.0
M_PLOT_DEFAULT_HI = 6.0

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "calorically perfect gas; steady normal shock; "
    "velocities relative to the shock; "
    "normal_shock_mach is M2**2 = ((gamma-1)*M1**2 + 2)/"
    "(2*gamma*M1**2 - (gamma-1)); "
    "normal_shock_pressure p2/p1 = (2*gamma*M1**2 - (gamma-1))/(gamma + 1); "
    "normal_shock_density rho2/rho1 = ((gamma+1)*M1**2)/"
    "((gamma-1)*M1**2 + 2); "
    "normal_shock_temperature T2/T1 from those two ratios; "
    "normal_shock_stagnation_pressure pt2/pt1; "
    "normal_shock_entropy_over_r is -ln(pt2/pt1); "
    "total temperature is unchanged; "
    f"an omitted --gamma is {DEFAULT_GAMMA:g} (air); "
    "M1 >= 1"
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
    if not math.isfinite(mach) or mach < 1.0 or mach > MACH_MAX:
        raise ValueError("upstream Mach must satisfy 1 <= M1 <= 1e6")


def normal_shock_mach_sq(mach: float, gamma: float) -> float:
    """normal_shock_mach: M2**2."""
    return ((gamma - 1.0) * mach * mach + 2.0) / (
        2.0 * gamma * mach * mach - (gamma - 1.0)
    )


def normal_shock_pressure(mach: float, gamma: float) -> float:
    """normal_shock_pressure: p2/p1."""
    return (2.0 * gamma * mach * mach - (gamma - 1.0)) / (gamma + 1.0)


def normal_shock_density(mach: float, gamma: float) -> float:
    """normal_shock_density: rho2/rho1."""
    return ((gamma + 1.0) * mach * mach) / ((gamma - 1.0) * mach * mach + 2.0)


def normal_shock_temperature(mach: float, gamma: float) -> float:
    """normal_shock_temperature: T2/T1."""
    return (
        (2.0 * gamma * mach * mach - (gamma - 1.0))
        * ((gamma - 1.0) * mach * mach + 2.0)
        / ((gamma + 1.0) ** 2 * mach * mach)
    )


def isentropic_stagnation_pressure(mach: float, gamma: float) -> float:
    """stagnation_pressure from stagnation_temperature at this Mach."""
    temperature_ratio = 1.0 + 0.5 * (gamma - 1.0) * mach * mach
    return temperature_ratio ** (gamma / (gamma - 1.0))


def rayleigh_pitot(mach: float, gamma: float) -> float:
    """rayleigh_pitot: pt2/p1."""
    return (
        (((gamma + 1.0) / 2.0) * mach * mach) ** (gamma / (gamma - 1.0))
        * ((gamma + 1.0) / (2.0 * gamma * mach * mach - (gamma - 1.0)))
        ** (1.0 / (gamma - 1.0))
    )


def normal_shock_stagnation_pressure(mach: float, gamma: float) -> float:
    """normal_shock_stagnation_pressure: pt2/pt1."""
    return (
        (((gamma + 1.0) * mach * mach) / ((gamma - 1.0) * mach * mach + 2.0))
        ** (gamma / (gamma - 1.0))
        * ((gamma + 1.0) / (2.0 * gamma * mach * mach - (gamma - 1.0)))
        ** (1.0 / (gamma - 1.0))
    )


def normal_shock_entropy_over_r(mach: float, gamma: float) -> float:
    """normal_shock_entropy_over_r: Delta s / R."""
    ratio = normal_shock_stagnation_pressure(mach, gamma)
    if ratio <= 0.0 or not math.isfinite(ratio):
        raise ValueError("stagnation-pressure ratio is not positive")
    return -math.log(ratio)


def shock_state(mach: float, gamma: float) -> dict[str, float]:
    require_mach(mach)
    require_gamma(gamma)
    m2_sq = normal_shock_mach_sq(mach, gamma)
    if m2_sq < 0.0 or not math.isfinite(m2_sq):
        raise ValueError("downstream Mach is not real")
    p_ratio = normal_shock_pressure(mach, gamma)
    t_ratio = normal_shock_temperature(mach, gamma)
    rho_ratio = normal_shock_density(mach, gamma)
    pt_ratio = normal_shock_stagnation_pressure(mach, gamma)
    ds_over_r = normal_shock_entropy_over_r(mach, gamma)
    return {
        "M1": mach,
        "gamma": gamma,
        "M2": math.sqrt(m2_sq),
        "p2_over_p1": p_ratio,
        "T2_over_T1": t_ratio,
        "rho2_over_rho1": rho_ratio,
        "pt2_over_pt1": pt_ratio,
        "ds_over_R": ds_over_r,
    }


def emit(result: dict[str, float], gamma_source: str, graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("M1", result["M1"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("M2", result["M2"])
    print_kv("p2_over_p1", result["p2_over_p1"])
    print_kv("T2_over_T1", result["T2_over_T1"])
    print_kv("rho2_over_rho1", result["rho2_over_rho1"])
    print_kv("pt2_over_pt1", result["pt2_over_pt1"])
    print_kv("ds_over_R", result["ds_over_R"])
    print_kv("graph", str(graph))


def plot_mach_grid(mach: float) -> list[float]:
    hi = max(M_PLOT_DEFAULT_HI, mach * 1.15)
    return [M_PLOT_MIN + i / (N_CURVE - 1) * (hi - M_PLOT_MIN) for i in range(N_CURVE)]


def write_plot(result: dict[str, float], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    mach = result["M1"]
    gamma = result["gamma"]
    m_grid = plot_mach_grid(mach)
    m2 = [math.sqrt(normal_shock_mach_sq(m, gamma)) for m in m_grid]
    p_ratio = [normal_shock_pressure(m, gamma) for m in m_grid]
    t_ratio = [normal_shock_temperature(m, gamma) for m in m_grid]
    rho_ratio = [normal_shock_density(m, gamma) for m in m_grid]
    pt_ratio = [normal_shock_stagnation_pressure(m, gamma) for m in m_grid]
    ds = [normal_shock_entropy_over_r(m, gamma) for m in m_grid]

    fig, axes = plt.subplots(2, 1, figsize=(7.5, 8.0), sharex=True)
    ax0, ax1 = axes

    ax0.plot(m_grid, m2, color="C0", label=r"$M_2$")
    ax0.plot(m_grid, pt_ratio, color="C1", label=r"$p_{t2}/p_{t1}$")
    ax0.plot(m_grid, ds, color="C2", label=r"$\Delta s/R$")
    ax0.plot(mach, result["M2"], "s", color="C0")
    ax0.plot(mach, result["pt2_over_pt1"], "s", color="C1")
    ax0.plot(mach, result["ds_over_R"], "s", color="C2")
    ax0.axvline(mach, color="0.6", linestyle=":")
    ax0.set_ylabel(r"$M_2$, $p_{t2}/p_{t1}$, $\Delta s/R$")
    ax0.legend(loc="best", frameon=False)
    ax0.grid(True, alpha=0.3)

    ax1.plot(m_grid, p_ratio, color="C3", label=r"$p_2/p_1$")
    ax1.plot(m_grid, t_ratio, color="C4", label=r"$T_2/T_1$")
    ax1.plot(m_grid, rho_ratio, color="C5", label=r"$\rho_2/\rho_1$")
    ax1.plot(mach, result["p2_over_p1"], "s", color="C3")
    ax1.plot(mach, result["T2_over_T1"], "s", color="C4")
    ax1.plot(mach, result["rho2_over_rho1"], "s", color="C5")
    ax1.axvline(mach, color="0.6", linestyle=":")
    ax1.set_xlabel(r"Upstream Mach number $M_1$")
    ax1.set_ylabel(r"Static ratios")
    ax1.legend(loc="best", frameon=False)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(M_PLOT_MIN, m_grid[-1])

    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    gamma = 7.0 / 5.0

    sonic = shock_state(1.0, gamma)
    if not close(sonic["M2"], 1.0):
        return fail("sonic downstream Mach is not 1")
    for key in ("p2_over_p1", "T2_over_T1", "rho2_over_rho1", "pt2_over_pt1"):
        if not close(sonic[key], 1.0):
            return fail(f"sonic {key} is not 1")
    if not close(sonic["ds_over_R"], 0.0):
        return fail("sonic entropy jump is not 0")

    air_two = shock_state(2.0, gamma)
    if not close(air_two["p2_over_p1"], 4.5):
        return fail("air Mach 2 pressure ratio is not 9/2")
    if not close(air_two["rho2_over_rho1"], 8.0 / 3.0):
        return fail("air Mach 2 density ratio is not 8/3")
    if not close(air_two["T2_over_T1"], 27.0 / 16.0):
        return fail("air Mach 2 temperature ratio is not 27/16")
    if not close(air_two["M2"] ** 2, 1.0 / 3.0):
        return fail("air Mach 2 M2**2 is not 1/3")
    expected_pt = (8.0 / 3.0) ** 3.5 * (2.0 / 9.0) ** 2.5
    if not close(air_two["pt2_over_pt1"], expected_pt):
        return fail("air Mach 2 stagnation-pressure ratio does not match")
    if not close(air_two["ds_over_R"], -math.log(expected_pt)):
        return fail("air Mach 2 entropy jump is not -ln(pt2/pt1)")

    composed = rayleigh_pitot(2.0, gamma) / isentropic_stagnation_pressure(2.0, gamma)
    if not close(air_two["pt2_over_pt1"], composed):
        return fail("pt2/pt1 is not rayleigh_pitot over isentropic pt/p")
    m2 = air_two["M2"]
    from_states = (
        air_two["p2_over_p1"]
        * isentropic_stagnation_pressure(m2, gamma)
        / isentropic_stagnation_pressure(2.0, gamma)
    )
    if not close(air_two["pt2_over_pt1"], from_states):
        return fail("pt2/pt1 is not (p2/p1)*(pt2/p2)/(pt1/p1)")
    if not close(
        air_two["T2_over_T1"],
        air_two["p2_over_p1"] / air_two["rho2_over_rho1"],
    ):
        return fail("temperature ratio is not p-ratio over density-ratio")

    mono = shock_state(2.0, 5.0 / 3.0)
    if not close(mono["p2_over_p1"], 19.0 / 4.0):
        return fail("monatomic Mach 2 pressure ratio is not 19/4")
    if not close(mono["rho2_over_rho1"], 16.0 / 7.0):
        return fail("monatomic Mach 2 density ratio is not 16/7")
    if not close(mono["M2"] ** 2, 7.0 / 19.0):
        return fail("monatomic Mach 2 M2**2 is not 7/19")

    try:
        shock_state(0.9, gamma)
        return fail("subsonic Mach was accepted")
    except ValueError:
        pass
    try:
        shock_state(2.0, 1.0)
        return fail("gamma = 1 was accepted")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(air_two, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")

    print("check: pass")
    print_kv("M2_air_two", air_two["M2"])
    print_kv("p2_over_p1_air_two", air_two["p2_over_p1"])
    print_kv("pt2_over_pt1_air_two", air_two["pt2_over_pt1"])
    print_kv("ds_over_R_air_two", air_two["ds_over_R"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Steady normal-shock downstream Mach, static ratios, "
            "stagnation-pressure ratio, and entropy jump."
        )
    )
    parser.add_argument(
        "--mach",
        type=float,
        default=None,
        help="upstream Mach number, M1 >= 1",
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
        help="PNG path",
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
        result = shock_state(args.mach, gamma)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = args.out if args.out is not None else SKILL_DIR / "normal_shock.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, gamma_source, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
