#!/usr/bin/env python3
"""Area ratio versus Mach number for an isentropic choked nozzle."""

from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

PLOT_TITLE = "Area ratio versus Mach number"
DEFAULT_GAMMA = 1.4
MACH_MIN = 0.2
MACH_MAX_DEFAULT = 5.0
CHECK_TOL = 1e-6
EXPANSION_REL_TOL = 0.005


def area_ratio(M: float, gamma: float) -> float:
    """Isentropic A/A* from area_mach (formulas.md)."""
    if M <= 0:
        raise ValueError("Mach number must be positive")
    g = gamma
    return (1.0 / M) * (
        (2.0 / (g + 1.0)) * (1.0 + ((g - 1.0) / 2.0) * M**2)
    ) ** ((g + 1.0) / (2.0 * (g - 1.0)))


def exit_pressure(pc: float, Me: float, gamma: float) -> float:
    """Exit static pressure from stagnation_pressure with p1 as pt."""
    g = gamma
    return pc * (1.0 + ((g - 1.0) / 2.0) * Me**2) ** (-g / (g - 1.0))


def thrust_coefficient_ideal(
    gamma: float, pe: float, pc: float, pa: float, Ae: float, At: float
) -> float:
    """Ideal CF from thrust_coefficient_ideal (formulas.md)."""
    k = gamma
    momentum = math.sqrt(
        (2.0 * k**2 / (k - 1.0))
        * ((2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))
        * (1.0 - (pe / pc) ** ((k - 1.0) / k))
    )
    return momentum + (pe - pa) / pc * (Ae / At)


def invert_supersonic_mach(epsilon: float, gamma: float) -> float:
    """Supersonic Me for A/A* = epsilon by bisection on M > 1."""
    if epsilon < 1.0:
        raise ValueError("epsilon must be >= 1")
    if abs(epsilon - 1.0) < 1e-14:
        return 1.0

    lo = 1.0 + 1e-12
    hi = 2.0
    while area_ratio(hi, gamma) < epsilon:
        hi *= 2.0
        if hi > 1e6:
            raise ValueError("could not bracket supersonic Mach for given epsilon")

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if area_ratio(mid, gamma) > epsilon:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def expansion_flag(pe: float, pa: float) -> str:
    rel = abs(pe - pa) / max(pa, pe, 1e-30)
    if rel <= EXPANSION_REL_TOL:
        return "perfectly expanded"
    if pe > pa:
        return "underexpanded"
    return "overexpanded"


def plot_curve(
    gamma: float,
    out_path: str,
    Me: Optional[float] = None,
    epsilon: Optional[float] = None,
) -> None:
    mach_max = MACH_MAX_DEFAULT
    if Me is not None:
        mach_max = max(MACH_MAX_DEFAULT, Me * 1.15)

    # Dense sampling; avoid M→0 where A/A* → ∞.
    M_sub = np.linspace(MACH_MIN, 1.0, 400, endpoint=False)
    M_sup = np.linspace(1.0, mach_max, 600)
    M = np.concatenate([M_sub, M_sup])
    A_over_Astar = np.array([area_ratio(float(m), gamma) for m in M])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(M, A_over_Astar, color="#1a5276", linewidth=1.8, label=r"$A/A^{*}$")
    ax.plot(1.0, 1.0, "o", color="#c0392b", markersize=7, zorder=5, label="throat $(1,1)$")

    if Me is not None and epsilon is not None:
        ax.axhline(epsilon, color="#7f8c8d", linestyle="--", linewidth=1.0, label=rf"$\epsilon={epsilon:g}$")
        ax.plot(Me, epsilon, "s", color="#27ae60", markersize=7, zorder=5, label=rf"exit $({Me:.3g},\ {epsilon:g})$")

    ax.set_xlabel("Mach number $M$")
    ax.set_ylabel(r"Area ratio $A/A^{*}$")
    ax.set_title(PLOT_TITLE)
    ax.set_xlim(MACH_MIN, mach_max)
    ymax = float(np.nanmax(A_over_Astar[M >= MACH_MIN]))
    if epsilon is not None:
        ymax = max(ymax, epsilon * 1.1)
    ax.set_ylim(0.0, ymax * 1.05)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def print_kv(key: str, value: object) -> None:
    print(f"{key}: {value}")


def run_check() -> int:
    gamma = 1.4
    expected = 1.6875  # 27/16
    got = area_ratio(2.0, gamma)
    if abs(got - expected) > CHECK_TOL:
        print(f"CHECK FAIL: area_ratio(2, 1.4) = {got}, expected {expected}", file=sys.stderr)
        return 1
    Me = invert_supersonic_mach(expected, gamma)
    if abs(Me - 2.0) > 1e-4:
        print(f"CHECK FAIL: invert(1.6875) = {Me}, expected 2", file=sys.stderr)
        return 1
    print("check: pass")
    print_kv("area_ratio_M2", f"{got:.6f}")
    print_kv("inverted_Me", f"{Me:.6f}")
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plot and evaluate isentropic nozzle area-Mach relations."
    )
    p.add_argument("--pc", type=float, default=None, help="chamber pressure p1 [Pa]")
    p.add_argument("--epsilon", type=float, default=None, help="exit-to-throat area ratio A2/At")
    p.add_argument(
        "--gamma",
        type=float,
        default=DEFAULT_GAMMA,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    p.add_argument("--pa", type=float, default=None, help="ambient pressure p3 [Pa]")
    p.add_argument("--throat", type=float, default=None, help="throat area At [m^2]")
    p.add_argument("--check", action="store_true", help="run built-in consistency checks")
    p.add_argument(
        "--out",
        type=str,
        default=None,
        help="PNG output path (default: area_mach_graph.png beside this script)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.check:
        return run_check()

    if args.gamma <= 1.0:
        print("error: --gamma must be > 1", file=sys.stderr)
        return 2
    if args.epsilon is not None and args.epsilon < 1.0:
        print("error: --epsilon must be >= 1", file=sys.stderr)
        return 2
    if args.pc is not None and args.pc <= 0:
        print("error: --pc must be > 0", file=sys.stderr)
        return 2
    if args.pa is not None and args.pa < 0:
        print("error: --pa must be >= 0", file=sys.stderr)
        return 2
    if args.throat is not None and args.throat <= 0:
        print("error: --throat must be > 0", file=sys.stderr)
        return 2

    gamma = args.gamma
    Me: Optional[float] = None
    epsilon = args.epsilon

    if epsilon is not None:
        Me = invert_supersonic_mach(epsilon, gamma)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = args.out or os.path.join(script_dir, "area_mach_graph.png")
    out_path = os.path.abspath(out_path)
    plot_curve(gamma, out_path, Me=Me, epsilon=epsilon)

    # Fixed key: value summary for the skill bot.
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", (
        "calorically perfect gas; steady one-dimensional isentropic nozzle; "
        "choked throat; negligible inlet velocity; marked exit is the "
        "supersonic root (Me >= 1); expansion flag is ideal pressure "
        "comparison and does not model separation"
    ))
    print_kv("gamma", gamma)
    print_kv("graph", out_path)

    pe: Optional[float] = None
    if Me is not None and epsilon is not None:
        print_kv("epsilon", epsilon)
        print_kv("Me", Me)
        print_kv("exit_point", f"({Me}, {epsilon})")

        if args.pc is not None:
            pe = exit_pressure(args.pc, Me, gamma)
            print_kv("pc_Pa", args.pc)
            print_kv("pe_Pa", pe)

            if args.throat is not None:
                Ae = epsilon * args.throat
                pa = 0.0 if args.pa is None else args.pa
                cf = thrust_coefficient_ideal(gamma, pe, args.pc, pa, Ae, args.throat)
                F = cf * args.pc * args.throat
                print_kv("throat_m2", args.throat)
                print_kv("Ae_m2", Ae)
                print_kv("CF", cf)
                print_kv("thrust_N", F)
                if args.pa is None:
                    print_kv("pa_Pa", 0)
                    print_kv("thrust_label", "vacuum (p3 = 0)")

        if pe is not None and args.pa is not None:
            print_kv("pa_Pa", args.pa)
            print_kv("expansion", expansion_flag(pe, args.pa))

    return 0


if __name__ == "__main__":
    sys.exit(main())
