#!/usr/bin/env python3
"""Two-dimensional Prandtl-Glauert correction and critical Mach number.

prandtl_glauert_factor is beta = sqrt(1 - M**2).
prandtl_glauert_coefficient is C = C0 / beta.
critical_pressure_coefficient is the isentropic Cp at local Mach 1.
critical_mach is the freestream Mach where those last two are equal.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
DEFAULT_GAMMA = 1.4
PLOT_TITLE = "Prandtl-Glauert correction and critical Mach"
N_CURVE = 401
M_LO = 1.0e-8
M_HI = 1.0 - 1.0e-10

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "calorically perfect gas; steady inviscid shock-free subsonic flow; "
    "two-dimensional Prandtl-Glauert from NACA TN 1127: "
    "prandtl_glauert_factor beta = sqrt(1 - M**2), "
    "prandtl_glauert_coefficient C = C0/beta for lift or pressure; "
    "that 1/beta factor is not a three-dimensional correction; "
    "critical_pressure_coefficient is pressure_coefficient_from_mach at "
    "local Mach 1 on an isentropic streamline from sonic_pressure and "
    "stagnation_pressure; "
    "critical_mach is the root of prandtl_glauert_coefficient of "
    "Cp0_min minus that critical coefficient, NACA TN 1813; "
    "Cp0_min must be negative (a suction peak); "
    f"an omitted --gamma is {DEFAULT_GAMMA:g} (air); "
    "0 <= M < 1; linearized theory fails as M approaches 1"
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


def prandtl_glauert_factor(mach: float) -> float:
    """prandtl_glauert_factor."""
    if mach < 0.0 or mach >= 1.0:
        raise ValueError("freestream Mach must satisfy 0 <= M < 1")
    return math.sqrt(1.0 - mach * mach)


def prandtl_glauert_coefficient(incompressible: float, mach: float) -> float:
    """prandtl_glauert_coefficient."""
    return incompressible / prandtl_glauert_factor(mach)


def critical_pressure_coefficient(gamma: float, mach: float) -> float:
    """critical_pressure_coefficient."""
    if mach <= 0.0:
        raise ValueError("critical pressure coefficient requires M > 0")
    inner = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * mach * mach)
    return 2.0 * (inner ** (gamma / (gamma - 1.0)) - 1.0) / (gamma * mach * mach)


def critical_mach_residual(cp0_min: float, mach: float, gamma: float) -> float:
    """critical_mach record: zero at M_cr."""
    return prandtl_glauert_coefficient(cp0_min, mach) - critical_pressure_coefficient(
        gamma, mach
    )


def critical_mach(cp0_min: float, gamma: float) -> float:
    """Solve critical_mach = 0 for M in (0, 1)."""
    if cp0_min >= 0.0:
        raise ValueError("incompressible minimum pressure coefficient must be < 0")
    lo = M_LO
    hi = M_HI
    f_lo = critical_mach_residual(cp0_min, lo, gamma)
    f_hi = critical_mach_residual(cp0_min, hi, gamma)
    if f_lo == 0.0:
        return lo
    if f_hi == 0.0:
        return hi
    if f_lo * f_hi > 0.0:
        raise ValueError("could not bracket a critical Mach number")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = critical_mach_residual(cp0_min, mid, gamma)
        if f_mid == 0.0 or abs(hi - lo) <= 1e-14:
            return mid
        if f_lo * f_mid <= 0.0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)


def require_inputs(
    mach: float,
    gamma: float,
    cl0: float | None,
    cp0_min: float | None,
) -> None:
    if not math.isfinite(mach) or not math.isfinite(gamma):
        raise ValueError("Mach and gamma must be finite")
    if mach < 0.0 or mach >= 1.0:
        raise ValueError("freestream Mach must satisfy 0 <= M < 1")
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if cl0 is None and cp0_min is None:
        raise ValueError("requires --cl-inc and/or --cpmin-inc")
    if cl0 is not None and not math.isfinite(cl0):
        raise ValueError("incompressible lift coefficient must be finite")
    if cp0_min is not None and not math.isfinite(cp0_min):
        raise ValueError("incompressible minimum pressure coefficient must be finite")


def correction_state(
    mach: float,
    gamma: float,
    cl0: float | None,
    cp0_min: float | None,
) -> dict[str, float | str | None]:
    require_inputs(mach, gamma, cl0, cp0_min)
    beta = prandtl_glauert_factor(mach)
    cp_crit_m = critical_pressure_coefficient(gamma, mach) if mach > 0.0 else None
    cl = prandtl_glauert_coefficient(cl0, mach) if cl0 is not None else None
    cp_min = (
        prandtl_glauert_coefficient(cp0_min, mach) if cp0_min is not None else None
    )
    m_cr: float | None = None
    supercritical: str | None = None
    if cp0_min is not None and cp0_min < 0.0:
        m_cr = critical_mach(cp0_min, gamma)
        if cp_min is not None and cp_crit_m is not None:
            supercritical = "yes" if cp_min < cp_crit_m else "no"
    elif cp0_min is not None and cp0_min >= 0.0:
        supercritical = "n/a"
    return {
        "M": mach,
        "gamma": gamma,
        "beta": beta,
        "CL0": cl0,
        "CL": cl,
        "Cp0_min": cp0_min,
        "Cp_min": cp_min,
        "Cp_crit": cp_crit_m,
        "M_cr": m_cr,
        "supercritical": supercritical,
    }


def emit(result: dict[str, float | str | None], gamma_source: str, graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("M", result["M"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("beta", result["beta"])
    if result["CL0"] is not None:
        print_kv("CL0", result["CL0"])
        print_kv("CL", result["CL"])
    if result["Cp0_min"] is not None:
        print_kv("Cp0_min", result["Cp0_min"])
        print_kv("Cp_min", result["Cp_min"])
        if result["Cp_crit"] is not None:
            print_kv("Cp_crit", result["Cp_crit"])
        if result["M_cr"] is not None:
            print_kv("M_cr", result["M_cr"])
        else:
            print_kv(
                "warning",
                "Cp0_min is not a suction peak; critical Mach is omitted",
            )
        if result["supercritical"] is not None:
            print_kv("supercritical", result["supercritical"])
    print_kv("graph", str(graph))


def write_plot(
    result: dict[str, float | str | None],
    out_path: Path,
) -> None:
    import matplotlib.pyplot as plt

    mach = float(result["M"])
    gamma = float(result["gamma"])
    cl0 = result["CL0"]
    cp0_min = result["Cp0_min"]
    m_cr = result["M_cr"]
    has_cl = cl0 is not None
    has_cp = cp0_min is not None
    n_rows = int(has_cl) + int(has_cp)
    if n_rows == 0:
        raise ValueError("plot requires --cl-inc and/or --cpmin-inc")

    m_grid = [i / (N_CURVE - 1) * 0.98 for i in range(N_CURVE)]
    m_grid[0] = 1.0e-4

    fig, axes = plt.subplots(n_rows, 1, figsize=(7.5, 4.2 * n_rows), sharex=True)
    if n_rows == 1:
        axes = [axes]
    row = 0
    if has_cl:
        ax = axes[row]
        cl_vals = [prandtl_glauert_coefficient(float(cl0), m) for m in m_grid]
        ax.plot(m_grid, cl_vals, color="C0", label=r"$C_L = C_{L0}/\beta$")
        ax.axhline(float(cl0), color="0.5", linestyle=":", label=r"$C_{L0}$")
        ax.plot(mach, float(result["CL"]), "s", color="C0")
        ax.set_ylabel(r"$C_L$")
        ax.legend(loc="best", frameon=False)
        ax.grid(True, alpha=0.3)
        row += 1
    if has_cp:
        ax = axes[row]
        cp_vals = [prandtl_glauert_coefficient(float(cp0_min), m) for m in m_grid]
        crit_vals = [critical_pressure_coefficient(gamma, m) for m in m_grid]
        ax.plot(m_grid, cp_vals, color="C0", label=r"$C_{p,\min} = C_{p0,\min}/\beta$")
        ax.plot(m_grid, crit_vals, color="C3", label=r"$C_{p,\mathrm{crit}}$")
        ax.plot(mach, float(result["Cp_min"]), "s", color="C0")
        if result["Cp_crit"] is not None:
            ax.plot(mach, float(result["Cp_crit"]), "o", color="C3")
        if m_cr is not None:
            ax.axvline(float(m_cr), color="C2", linestyle="--", label=r"$M_{\mathrm{cr}}$")
            ax.plot(
                float(m_cr),
                prandtl_glauert_coefficient(float(cp0_min), float(m_cr)),
                "D",
                color="C2",
            )
        ax.set_ylabel(r"$C_p$")
        ax.legend(loc="best", frameon=False)
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel(r"Freestream Mach number $M_\infty$")
    axes[-1].set_xlim(0.0, 1.0)
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    gamma = 7.0 / 5.0

    if not close(prandtl_glauert_factor(0.0), 1.0):
        return fail("incompressible Prandtl-Glauert factor is not 1")
    if not close(prandtl_glauert_factor(0.6), 0.8):
        return fail("Mach 0.6 factor is not 4/5")
    if not close(prandtl_glauert_coefficient(-0.4, 0.0), -0.4):
        return fail("incompressible coefficient changed")
    if not close(prandtl_glauert_coefficient(-0.4, 0.6), -0.5):
        return fail("Mach 0.6 coefficient is not -1/2")

    if not close(critical_pressure_coefficient(gamma, 1.0), 0.0):
        return fail("Cp_crit at M = 1 is not 0")
    inner_half = (2.0 / 2.4) * (1.0 + 0.2 * 0.25)
    expected_half = (40.0 / 7.0) * (inner_half ** 3.5 - 1.0)
    if not close(critical_pressure_coefficient(gamma, 0.5), expected_half):
        return fail("air Mach 1/2 Cp_crit does not match air_half")

    # Composition: sonic_pressure * stagnation_pressure into
    # pressure_coefficient_from_mach.
    tt_over_t = 1.0 + 0.5 * (gamma - 1.0) * 0.25
    pstar_over_pt = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
    pt_over_p = tt_over_t ** (gamma / (gamma - 1.0))
    pstar_over_p = pstar_over_pt * pt_over_p
    composed = 2.0 * (pstar_over_p - 1.0) / (gamma * 0.25)
    if not close(critical_pressure_coefficient(gamma, 0.5), composed):
        return fail("Cp_crit is not the composed isentropic coefficient")

    cp0 = expected_half * math.sqrt(0.75)
    if not close(critical_mach_residual(cp0, 0.5, gamma), 0.0):
        return fail("air_half critical_mach residual is not 0")
    recovered = critical_mach(cp0, gamma)
    if not close(recovered, 0.5, tol=1e-8):
        return fail(f"critical Mach inverse returned {recovered}, expected 0.5")

    state = correction_state(0.6, gamma, 0.5, -0.4)
    if not close(float(state["CL"]), 0.5 / 0.8):
        return fail("compressible lift is not CL0/beta")
    if not close(float(state["Cp_min"]), -0.5):
        return fail("compressible Cp_min is not -1/2")
    if state["M_cr"] is None:
        return fail("critical Mach was omitted for a suction peak")
    if abs(critical_mach_residual(-0.4, float(state["M_cr"]), gamma)) > 1e-10:
        return fail("printed M_cr does not zero the residual")

    try:
        prandtl_glauert_factor(1.0)
        return fail("Mach 1 was accepted")
    except ValueError:
        pass
    try:
        critical_mach(0.1, gamma)
        return fail("positive Cp0_min was accepted")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(state, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")

    print("check: pass")
    print_kv("beta_three_fifths", 0.8)
    print_kv("Cp_min_three_fifths", -0.5)
    print_kv("Cp_crit_air_half", expected_half)
    print_kv("M_cr_air_half", recovered)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Two-dimensional Prandtl-Glauert correction of an incompressible "
            "lift or minimum pressure coefficient, and critical Mach number "
            "from that suction peak."
        )
    )
    parser.add_argument(
        "--mach",
        type=float,
        default=None,
        help="freestream Mach number, 0 <= M < 1",
    )
    parser.add_argument(
        "--cl-inc",
        type=float,
        default=None,
        help="incompressible lift coefficient",
    )
    parser.add_argument(
        "--cpmin-inc",
        type=float,
        default=None,
        help="incompressible minimum pressure coefficient (suction, < 0)",
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
    if args.cl_inc is None and args.cpmin_inc is None:
        print("error: requires --cl-inc and/or --cpmin-inc", file=sys.stderr)
        return 2

    if args.gamma is None:
        gamma = DEFAULT_GAMMA
        gamma_source = "default"
    else:
        gamma = args.gamma
        gamma_source = "flag"

    try:
        result = correction_state(args.mach, gamma, args.cl_inc, args.cpmin_inc)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = args.out if args.out is not None else SKILL_DIR / "prandtl_glauert_correction.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, gamma_source, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
