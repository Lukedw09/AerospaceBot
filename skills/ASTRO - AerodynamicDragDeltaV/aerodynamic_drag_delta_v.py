#!/usr/bin/env python3
"""Drag acceleration and delta-v per revolution at constant density."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import tempfile
from pathlib import Path

G0 = 9.80665
R0 = 6.3742e6
PLOT_TITLE = "Drag delta-v per revolution"
SKILL_DIR = Path(__file__).resolve().parent
SKILLS = SKILL_DIR.parent
ASSUMPTIONS = (
    "circular orbit; drag D = Cd*q*A with q = 0.5*rho*V^2 held constant over "
    "one revolution; delta-v per revolution is (D/m)*period; speed and period "
    "use Earth mu = g0*R0^2 with R0 = 6.3742e6 m; density comes from altitude "
    "(Standard1976 at or below 86 km, DensityAbove86km above) unless --rho is set"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


_LOADED: dict[str, object] = {}


def load_module(folder: str, filename: str, name: str):
    """Load a skill module once. Reloading would rebuild the 86 km density grid."""
    cached = _LOADED.get(name)
    if cached is not None:
        return cached
    path = SKILLS / folder / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _LOADED[name] = module
    return module


def mu_earth() -> float:
    return G0 * R0 * R0


def circular_speed(alt_m: float) -> float:
    return R0 * math.sqrt(G0 / (R0 + alt_m))


def orbital_period(alt_m: float) -> float:
    a = R0 + alt_m
    return 2.0 * math.pi * math.sqrt(a ** 3 / mu_earth())


def density_at(alt_m: float, rho_override: float | None) -> tuple[float, str]:
    if rho_override is not None:
        if not math.isfinite(rho_override) or rho_override <= 0.0:
            raise ValueError("--rho must be positive")
        return rho_override, "override"
    if alt_m < 0.0:
        raise ValueError("--alt must be >= 0")
    if alt_m <= 86000.0:
        standard = load_module("ATMOS - Standard1976", "standard_1976.py", "standard1976_drag")
        return float(standard.atmosphere(alt_m)["rho"]), "standard1976"
    dense = load_module("ATMOS - DensityAbove86km", "density_above_86km.py", "density86_drag")
    return float(dense.state_at(alt_m)["rho"]), "density_above_86km"


def drag_force(rho: float, speed: float, cd: float, area: float) -> float:
    """drag_force at constant density."""
    return cd * 0.5 * rho * speed * speed * area


def delta_v_per_rev(force: float, mass: float, period: float) -> float:
    """drag_delta_v_per_revolution."""
    return force / mass * period


def evaluate(alt_m: float, mass: float, cd: float, area: float, rho_override: float | None) -> dict[str, float | str]:
    if min(mass, cd, area) <= 0.0 or alt_m < 0.0:
        raise ValueError("mass, Cd, and area must be positive and altitude >= 0")
    rho, source = density_at(alt_m, rho_override)
    speed = circular_speed(alt_m)
    period = orbital_period(alt_m)
    force = drag_force(rho, speed, cd, area)
    accel = force / mass
    return {
        "alt_m": alt_m,
        "rho_kg_m3": rho,
        "density_source": source,
        "V_m_s": speed,
        "period_s": period,
        "D_N": force,
        "a_m_s2": accel,
        "dv_per_rev_m_s": delta_v_per_rev(force, mass, period),
    }


def emit(state: dict[str, float | str], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "constant-density drag delta-v per revolution")
    for key in ("alt_m", "rho_kg_m3", "density_source", "V_m_s", "period_s", "D_N", "a_m_s2", "dv_per_rev_m_s"):
        print_kv(key, state[key])
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(mass: float, cd: float, area: float, marker_alt: float, marker_dv: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    # Sample the thermosphere. Building the density grid once, then querying it.
    dense = load_module("ATMOS - DensityAbove86km", "density_above_86km.py", "density86_plot")
    altitudes = [90000.0 + 10000.0 * i for i in range(42)]
    delta_vs = []
    for alt in altitudes:
        rho = float(dense.state_at(alt)["rho"])
        speed = circular_speed(alt)
        period = orbital_period(alt)
        delta_vs.append(delta_v_per_rev(drag_force(rho, speed, cd, area), mass, period))
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.semilogy([z / 1000.0 for z in altitudes], delta_vs, color="C0", label="1976 model")
    if 90000.0 <= marker_alt <= 500000.0:
        ax.plot(marker_alt / 1000.0, marker_dv, "s", color="C1", label="operating point")
    ax.set_xlabel("altitude (km)")
    ax.set_ylabel(r"$\Delta v$ per revolution (m/s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    alt = 400000.0
    rho = 1.0e-11
    mass = 50.0
    cd = 2.2
    area = 0.8
    speed = circular_speed(alt)
    period = orbital_period(alt)
    force = drag_force(rho, speed, cd, area)
    dv = delta_v_per_rev(force, mass, period)
    manual = (cd * 0.5 * rho * speed ** 2 * area) / mass * period
    if abs(dv - manual) > 1e-12 * max(1.0, abs(dv)):
        return fail("delta-v identity")
    # Period identity: 2*pi*sqrt(a^3/mu).
    a = R0 + alt
    if abs(period - 2.0 * math.pi * math.sqrt(a ** 3 / mu_earth())) > 1e-6:
        return fail("period")
    state = evaluate(alt, mass, cd, area, rho)
    if state["density_source"] != "override" or abs(float(state["dv_per_rev_m_s"]) - dv) > 1e-12:
        return fail("override path")
    # Below 86 km must use Standard1976, not the thermosphere model.
    low = evaluate(20000.0, mass, cd, area, None)
    if low["density_source"] != "standard1976":
        return fail(f"low altitude source {low['density_source']}")
    if not (1.0e-2 < float(low["rho_kg_m3"]) < 2.0e-1):
        return fail(f"20 km density {low['rho_kg_m3']}")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "drag.png"
        code = main([
            "--alt", "400000", "--mass", "50", "--cd", "2.2", "--area", "0.8",
            "--rho", "1e-11", "--out", str(path),
        ])
        if code != 0 or path.stat().st_size < 1000:
            return fail("plot")
    print("check: pass")
    print_kv("dv_override", dv)
    print_kv("rho_20km", low["rho_kg_m3"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aerodynamic drag delta-v per circular revolution.")
    parser.add_argument("--alt", type=float, required=False)
    parser.add_argument("--mass", type=float, required=False)
    parser.add_argument("--cd", type=float, required=False)
    parser.add_argument("--area", type=float, required=False)
    parser.add_argument("--rho", type=float, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if None in (args.alt, args.mass, args.cd, args.area):
        print("error: requires --alt, --mass, --cd, and --area", file=sys.stderr)
        return 2
    try:
        state = evaluate(args.alt, args.mass, args.cd, args.area, args.rho)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(args.mass, args.cd, args.area, args.alt, float(state["dv_per_rev_m_s"]), args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(state, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
