#!/usr/bin/env python3
"""Bartz gas-side heat-transfer coefficient and heat flux at a stated station.

bartz_gas_side_coefficient is the SP-125 equation (4-13) restated in SI.
gas_side_heat_flux is q = hg * (recovery * Tc - Tw).
sp125_prandtl, sp125_specific_heat, and sp125_viscosity fill gas properties
when mu, cp, and Pr are not supplied.
At the throat, area_ratio = At/A = 1.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-6
BARTZ_C = 0.026016775834104906
MU_C = 1.1840810853327972e-07
CP_C = 4616.123393316195
PLOT_TITLE = "Throat gas-side heat flux"


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def sp125_gas(gamma: float, molar_mass: float, temperature: float) -> tuple[float, float, float]:
    prandtl = 4.0 * gamma / (9.0 * gamma - 5.0)
    cp = (gamma / (gamma - 1.0)) * CP_C / molar_mass
    mu = MU_C * molar_mass**0.5 * temperature**0.6
    return mu, cp, prandtl


def bartz_coefficient(
    diameter: float,
    mu: float,
    cp: float,
    prandtl: float,
    pc: float,
    cstar: float,
    curvature: float,
    area_ratio: float,
    sigma: float,
) -> float:
    return (
        BARTZ_C
        * diameter ** (-0.2)
        * mu**0.2
        * cp
        * prandtl ** (-0.6)
        * (pc / cstar) ** 0.8
        * (diameter / curvature) ** 0.1
        * area_ratio**0.9
        * sigma
    )


def heat_flux(hg: float, recovery: float, tc: float, tw: float) -> float:
    return hg * (recovery * tc - tw)


def write_plot(
    diameter: float,
    mu: float,
    cp: float,
    prandtl: float,
    pc: float,
    cstar: float,
    curvature: float,
    area_ratio: float,
    sigma: float,
    recovery: float,
    tc: float,
    tw: float,
    out_path: Path,
) -> None:
    import matplotlib.pyplot as plt

    pressures = [pc * (0.25 + 1.75 * i / 40.0) for i in range(41)]
    fluxes = []
    for pressure in pressures:
        hg = bartz_coefficient(
            diameter, mu, cp, prandtl, pressure, cstar, curvature, area_ratio, sigma
        )
        fluxes.append(heat_flux(hg, recovery, tc, tw) / 1.0e6)
    hg_user = bartz_coefficient(
        diameter, mu, cp, prandtl, pc, cstar, curvature, area_ratio, sigma
    )
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot([item / 1.0e6 for item in pressures], fluxes, color="C0")
    ax.plot(
        pc / 1.0e6,
        heat_flux(hg_user, recovery, tc, tw) / 1.0e6,
        "s",
        color="C3",
    )
    ax.set_xlabel("Chamber pressure [MPa]")
    ax.set_ylabel("Heat flux [MW/m$^2$]")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def run_check() -> int:
    diameter = 0.63246
    curvature = 0.297434
    mu = 7.464630340944881e-05
    cp = 1128.11
    prandtl = 0.816
    pc = 6894757.29316836
    cstar = 1725.168
    hg = bartz_coefficient(diameter, mu, cp, prandtl, pc, cstar, curvature, 1.0, 1.0)
    expected = 4457.590750448887
    if abs(hg - expected) / expected > 1e-9:
        print(f"CHECK FAIL: hg = {hg}", file=sys.stderr)
        return 1
    q = heat_flux(1000.0, 0.9, 3000.0, 500.0)
    if abs(q - 2.2e6) > CHECK_TOL:
        print(f"CHECK FAIL: q = {q}", file=sys.stderr)
        return 1
    mu2, cp2, pr2 = sp125_gas(1.222, 22.5, 6140.0 * 5.0 / 9.0)
    if abs(pr2 - 4.0 * 1.222 / (9.0 * 1.222 - 5.0)) > CHECK_TOL:
        print(f"CHECK FAIL: Pr = {pr2}", file=sys.stderr)
        return 1
    if abs(cp2 - (1.222 / 0.222) * CP_C / 22.5) > CHECK_TOL:
        print(f"CHECK FAIL: cp = {cp2}", file=sys.stderr)
        return 1
    if abs(mu2 - MU_C * (22.5**0.5) * (6140.0 * 5.0 / 9.0) ** 0.6) > CHECK_TOL:
        print(f"CHECK FAIL: mu = {mu2}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "flux.png"
        write_plot(
            diameter, mu, cp, prandtl, pc, cstar, curvature, 1.0, 1.0, 0.9, 3000.0, 500.0, path
        )
        if not path.is_file() or path.stat().st_size <= 0:
            print("CHECK FAIL: plot was not written", file=sys.stderr)
            return 1
    print("check: pass")
    print_kv("h_g_W_m2_K", hg)
    print_kv("q_dot_W_m2", heat_flux(hg, 1.0, 3411.111111111111, 800.0))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bartz gas-side coefficient and heat flux at the throat."
    )
    parser.add_argument("--pc", type=float, default=None, help="nozzle stagnation pressure [Pa]")
    parser.add_argument("--Tc", type=float, default=None, help="nozzle stagnation temperature [K]")
    parser.add_argument("--cstar", type=float, default=None, help="characteristic velocity [m/s]")
    parser.add_argument("--throat", type=float, default=None, help="throat diameter [m]")
    parser.add_argument("--rt", type=float, default=None, help="throat radius [m]")
    parser.add_argument(
        "--curvature",
        type=float,
        default=None,
        help="nozzle-contour radius of curvature at the throat [m]",
    )
    parser.add_argument("--mu", type=float, default=None, help="gas viscosity [Pa·s]")
    parser.add_argument("--cp", type=float, default=None, help="gas specific heat [J/(kg·K)]")
    parser.add_argument("--pr", type=float, default=None, help="Prandtl number")
    parser.add_argument("--mw", type=float, default=None, help="molecular weight [kg/kmol]")
    parser.add_argument("--gamma", type=float, default=None, help="ratio of specific heats")
    parser.add_argument(
        "--area-ratio",
        type=float,
        default=None,
        help="At/A at the station; throat default is 1",
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=None,
        help="boundary-layer property factor; omitted value is 1",
    )
    parser.add_argument(
        "--recovery",
        type=float,
        default=None,
        help="turbulent recovery factor; omitted value is 1",
    )
    parser.add_argument("--tw", type=float, default=None, help="gas-side wall temperature [K]")
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    missing = [
        flag
        for flag, value in (
            ("--pc", args.pc),
            ("--Tc", args.Tc),
            ("--cstar", args.cstar),
            ("--curvature", args.curvature),
            ("--tw", args.tw),
        )
        if value is None
    ]
    if missing:
        print(
            "error: requires --pc, --Tc, --cstar, --curvature, and --tw; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if (args.throat is None) == (args.rt is None):
        print("error: pass exactly one of --throat or --rt", file=sys.stderr)
        return 2
    if args.pc <= 0 or args.Tc <= 0 or args.cstar <= 0 or args.curvature <= 0:
        print("error: pc, Tc, cstar, and curvature must be > 0", file=sys.stderr)
        return 2
    if args.tw < 0:
        print("error: tw must be >= 0 K", file=sys.stderr)
        return 2
    diameter = args.throat if args.throat is not None else 2.0 * args.rt
    supplied = [args.pc, args.Tc, args.cstar, args.curvature, args.tw, diameter]
    for optional in (
        args.mu,
        args.cp,
        args.pr,
        args.mw,
        args.gamma,
        args.area_ratio,
        args.sigma,
        args.recovery,
    ):
        if optional is not None:
            supplied.append(optional)
    if any(not math.isfinite(value) for value in supplied):
        print("error: inputs must be finite", file=sys.stderr)
        return 2
    if diameter <= 0:
        print("error: throat diameter must be > 0 m", file=sys.stderr)
        return 2

    props = (args.mu, args.cp, args.pr)
    given_props = sum(item is not None for item in props)
    given_fit = args.mw is not None or args.gamma is not None
    if given_props == 3 and given_fit:
        print("error: pass --mu --cp --pr or --mw --gamma, not both", file=sys.stderr)
        return 2
    if given_props not in (0, 3):
        print("error: --mu, --cp, and --pr must be passed together", file=sys.stderr)
        return 2
    if given_props == 0:
        if args.mw is None or args.gamma is None:
            print(
                "error: pass --mu, --cp, and --pr, or both --mw and --gamma",
                file=sys.stderr,
            )
            return 2
        if args.mw <= 0 or args.gamma <= 1:
            print("error: mw must be > 0 and gamma must be > 1", file=sys.stderr)
            return 2
        mu, cp, prandtl = sp125_gas(args.gamma, args.mw, args.Tc)
        prop_source = "sp125_mw_gamma"
    else:
        assert args.mu is not None and args.cp is not None and args.pr is not None
        if args.mu <= 0 or args.cp <= 0 or args.pr <= 0:
            print("error: mu, cp, and pr must be > 0", file=sys.stderr)
            return 2
        mu, cp, prandtl = args.mu, args.cp, args.pr
        prop_source = "user"

    area_ratio = 1.0 if args.area_ratio is None else args.area_ratio
    sigma = 1.0 if args.sigma is None else args.sigma
    recovery = 1.0 if args.recovery is None else args.recovery
    if area_ratio <= 0 or sigma <= 0:
        print("error: area-ratio and sigma must be > 0", file=sys.stderr)
        return 2
    if recovery <= 0 or recovery > 1:
        print("error: recovery must be in (0, 1]", file=sys.stderr)
        return 2
    driving = recovery * args.Tc - args.tw
    if driving <= 0:
        print("error: recovery*Tc must exceed tw", file=sys.stderr)
        return 2

    hg = bartz_coefficient(
        diameter, mu, cp, prandtl, args.pc, args.cstar, args.curvature, area_ratio, sigma
    )
    q = heat_flux(hg, recovery, args.Tc, args.tw)
    if not math.isfinite(hg) or not math.isfinite(q) or not math.isfinite(mu):
        print("error: result is not finite", file=sys.stderr)
        return 2
    print_kv(
        "assumptions",
        (
            "SP-125 Bartz equation (4-13) in SI; q = hg*(recovery*Tc - Tw); "
            "throat uses At/A = 1 unless --area-ratio is set; "
            "sigma defaults to 1 because figure 4-24 is not digitized; "
            "recovery defaults to 1 (SP-125 quotes 0.90 to 0.98); "
            "not Sutton-Graves; no carbon deposit and no coolant-side coefficient"
        ),
    )
    print_kv("pc_Pa", args.pc)
    print_kv("Tc_K", args.Tc)
    print_kv("cstar_m_s", args.cstar)
    print_kv("Dt_m", diameter)
    print_kv("R_m", args.curvature)
    print_kv("area_ratio_At_over_A", area_ratio)
    print_kv("sigma", sigma)
    print_kv("recovery", recovery)
    print_kv("Tw_K", args.tw)
    print_kv("prop_source", prop_source)
    print_kv("mu_Pa_s", mu)
    print_kv("cp_J_kg_K", cp)
    print_kv("Pr", prandtl)
    print_kv("h_g_W_m2_K", hg)
    print_kv("q_dot_W_m2", q)
    if args.sigma is None:
        print_kv("warning", "sigma=1 omits the SP-125 figure 4-24 property correction")
    if args.recovery is None:
        print_kv(
            "warning_recovery",
            "recovery=1; SP-125 quotes a turbulent recovery factor from 0.90 to 0.98",
        )
    if args.out:
        write_plot(
            diameter,
            mu,
            cp,
            prandtl,
            args.pc,
            args.cstar,
            args.curvature,
            area_ratio,
            sigma,
            recovery,
            args.Tc,
            args.tw,
            Path(args.out),
        )
        print_kv("graph", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
