#!/usr/bin/env python3
"""Single-node spacecraft radiative balance and radiator area."""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

SIGMA = 5.670374419e-8
S_DEFAULT = 1361.6
PLOT_TITLE = "Spacecraft radiative balance"
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "single isothermal node; absorbed solar, albedo, and planet infrared are "
    "balanced by gray-body emission eps*sigma*A*T^4; solar is reduced by the "
    "eclipse fraction and is zero in eclipse; albedo and planet infrared are "
    "user inputs; no conduction between nodes and no internal heat dump beyond "
    "the optional internal power"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_positive(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be finite and positive")
    return value


def require_unit(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{flag} must be in (0, 1]")
    return value


def require_closed(value: float, flag: str) -> float:
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{flag} must be in [0, 1]")
    return value


def absorbed_power(
    solar: float,
    area_sun: float,
    alpha: float,
    eclipse_fraction: float,
    albedo: float,
    area_albedo: float,
    view_albedo: float,
    planet_ir: float,
    area_planet: float,
    epsilon: float,
    view_planet: float,
    internal: float,
) -> float:
    """spacecraft_absorbed_power."""
    sun = solar * area_sun * alpha * (1.0 - eclipse_fraction)
    alb = solar * albedo * view_albedo * area_albedo * alpha
    planet = planet_ir * view_planet * area_planet * epsilon
    return sun + alb + planet + internal


def equilibrium_temperature(q_abs: float, epsilon: float, area_rad: float) -> float:
    """radiative_equilibrium_temperature: T = (Q/(eps*sigma*A))**(1/4)."""
    return (q_abs / (epsilon * SIGMA * area_rad)) ** 0.25


def radiator_area(q_abs: float, epsilon: float, temperature: float) -> float:
    """radiator_area_for_temperature: A = Q/(eps*sigma*T**4)."""
    return q_abs / (epsilon * SIGMA * temperature ** 4)


def emit(state: dict[str, float], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "single-node spacecraft radiative balance")
    for key in (
        "S_W_m2",
        "alpha",
        "epsilon",
        "fe",
        "Q_sun_W",
        "Q_albedo_W",
        "Q_planet_W",
        "Q_internal_W",
        "Q_abs_W",
    ):
        print_kv(key, state[key])
    if "T_eq_K" in state:
        print_kv("A_rad_m2", state["A_rad"])
        print_kv("T_eq_K", state["T_eq_K"])
    if "A_req_m2" in state:
        print_kv("T_hold_K", state["T_hold"])
        print_kv("A_req_m2", state["A_req_m2"])
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(q_abs: float, epsilon: float, marker: tuple[float, float] | None, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    areas = [0.05 * (i + 1) for i in range(80)]
    temps = [equilibrium_temperature(q_abs, epsilon, area) for area in areas]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(areas, temps, color="C0", label=r"$T_{\mathrm{eq}}$")
    if marker is not None:
        ax.plot(marker[0], marker[1], "s", color="C1", label="operating point")
    ax.set_xlabel(r"radiator area (m$^2$)")
    ax.set_ylabel("equilibrium temperature (K)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def build(args: argparse.Namespace) -> dict[str, float]:
    solar = S_DEFAULT if args.solar_constant is None else require_positive(args.solar_constant, "--solar-constant")
    alpha = require_unit(args.alpha, "--alpha")
    epsilon = require_unit(args.epsilon, "--epsilon")
    area_sun = require_positive(args.area_sun, "--area-sun")
    fe = 0.0 if args.eclipse_fraction is None else require_closed(args.eclipse_fraction, "--eclipse-fraction")
    albedo = 0.0 if args.albedo is None else require_closed(args.albedo, "--albedo")
    area_albedo = 0.0 if args.area_albedo is None else require_positive(args.area_albedo, "--area-albedo")
    view_albedo = 1.0 if args.view_albedo is None else require_closed(args.view_albedo, "--view-albedo")
    planet_ir = 0.0 if args.planet_ir is None else require_positive(args.planet_ir, "--planet-ir")
    area_planet = 0.0 if args.area_planet is None else require_positive(args.area_planet, "--area-planet")
    view_planet = 1.0 if args.view_planet is None else require_closed(args.view_planet, "--view-planet")
    internal = 0.0 if args.internal is None else require_positive(args.internal, "--internal")
    if (args.albedo is None) != (args.area_albedo is None):
        raise ValueError("pass --albedo and --area-albedo together")
    if (args.planet_ir is None) != (args.area_planet is None):
        raise ValueError("pass --planet-ir and --area-planet together")
    q_sun = solar * area_sun * alpha * (1.0 - fe)
    q_alb = solar * albedo * view_albedo * area_albedo * alpha
    q_planet = planet_ir * view_planet * area_planet * epsilon
    q_abs = absorbed_power(
        solar, area_sun, alpha, fe, albedo, area_albedo, view_albedo,
        planet_ir, area_planet, epsilon, view_planet, internal,
    )
    state = {
        "S_W_m2": solar,
        "alpha": alpha,
        "epsilon": epsilon,
        "fe": fe,
        "Q_sun_W": q_sun,
        "Q_albedo_W": q_alb,
        "Q_planet_W": q_planet,
        "Q_internal_W": internal,
        "Q_abs_W": q_abs,
    }
    if args.area_rad is not None:
        area = require_positive(args.area_rad, "--area-rad")
        state["A_rad"] = area
        state["T_eq_K"] = equilibrium_temperature(q_abs, epsilon, area)
    if args.temperature is not None:
        temp = require_positive(args.temperature, "--temperature")
        state["T_hold"] = temp
        state["A_req_m2"] = radiator_area(q_abs, epsilon, temp)
    if "T_eq_K" not in state and "A_req_m2" not in state:
        raise ValueError("pass --area-rad, or --temperature, or both")
    return state


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    # Full Sun, no planet inputs: Q = S*A*alpha, T from sigma.
    q = S_DEFAULT * 0.5 * 0.9
    area = 0.4
    eps = 0.8
    expected_t = (q / (eps * SIGMA * area)) ** 0.25
    got = equilibrium_temperature(q, eps, area)
    if abs(got - expected_t) > 1e-9:
        return fail("equilibrium temperature")
    area_back = radiator_area(q, eps, got)
    if abs(area_back - area) > 1e-9:
        return fail("radiator area round trip")
    # 300 K hold with a known heat load.
    t_hold = 300.0
    q_hold = eps * SIGMA * 1.0 * t_hold ** 4
    if abs(radiator_area(q_hold, eps, t_hold) - 1.0) > 1e-8:
        return fail("300 K area")
    # Eclipse fraction halves the solar term only.
    q_ecl = absorbed_power(1000.0, 1.0, 1.0, 0.4, 0.3, 2.0, 0.5, 200.0, 1.5, 0.8, 1.0, 5.0)
    manual = 1000 * 1 * 0.6 + 1000 * 0.3 * 0.5 * 2 * 1 + 200 * 1 * 1.5 * 0.8 + 5
    if abs(q_ecl - manual) > 1e-9:
        return fail(f"absorbed power {q_ecl} vs {manual}")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "therm.png"
        code = main([
            "--area-sun", "0.5", "--alpha", "0.9", "--epsilon", "0.8",
            "--area-rad", "0.4", "--out", str(path),
        ])
        if code != 0 or path.stat().st_size < 1000:
            return fail("plot")
    print("check: pass")
    print_kv("T_eq_K", got)
    print_kv("Q_abs_W", q_ecl)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-node spacecraft radiative balance.")
    parser.add_argument("--area-sun", type=float, default=None)
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--epsilon", type=float, default=None)
    parser.add_argument("--area-rad", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--eclipse-fraction", type=float, default=None)
    parser.add_argument("--solar-constant", type=float, default=None)
    parser.add_argument("--albedo", type=float, default=None)
    parser.add_argument("--area-albedo", type=float, default=None)
    parser.add_argument("--view-albedo", type=float, default=None)
    parser.add_argument("--planet-ir", type=float, default=None)
    parser.add_argument("--area-planet", type=float, default=None)
    parser.add_argument("--view-planet", type=float, default=None)
    parser.add_argument("--internal", type=float, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.area_sun is None or args.alpha is None or args.epsilon is None:
        print("error: requires --area-sun, --alpha, and --epsilon", file=sys.stderr)
        return 2
    try:
        state = build(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            marker = None
            if "T_eq_K" in state:
                marker = (float(state["A_rad"]), float(state["T_eq_K"]))
            write_plot(float(state["Q_abs_W"]), float(state["epsilon"]), marker, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(state, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
