#!/usr/bin/env python3
"""Equilibrium-glide peak deceleration and heat-flux scale.

equilibrium_glide_peak_deceleration is g/(L/D).
equilibrium_glide_entry_deceleration is the horizontal value at entry speed.
equilibrium_glide_heating_density and equilibrium_glide_heat_flux_scale
use the speed that maximizes sqrt(rho)*V**3 on the glide.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Equilibrium glide entry"
G0 = 9.80665
R0_EARTH = 6.3742e6
N_CURVE = 161
# NACA TN 4047 Earth fit, same conversion as THERM - BallisticEntryPeakLoad.
SLUG_FT3_TO_KG_M3 = 515.3788184
FT_TO_M = 0.3048
DEFAULT_RHO_REF = 0.0034 * SLUG_FT3_TO_KG_M3
DEFAULT_H = 22000.0 * FT_TO_M
DEFAULT_Z_REF = 0.0
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "Sanger-Chapman equilibrium glide; small flight-path angle; "
    "lift balances weight minus centrifugal force; constant L/D; "
    "entry speed below circular speed; "
    "equilibrium_glide_peak_deceleration a_peak = g/(L/D) "
    "is the low-speed horizontal deceleration; "
    "equilibrium_glide_entry_deceleration a_entry = g*(1 - ve^2/vc^2)/(L/D); "
    "heating speed is min(ve, vc*sqrt(2/3)); "
    "equilibrium_glide_heating_density from the lift balance at that speed; "
    "equilibrium_glide_heat_flux_scale is sqrt(rho)*V**3, not W/m^2; "
    "altitude uses the TN 4047 exponential atmosphere and does not change the load; "
    "not a ballistic Allen-Eggers entry and not a 3DOF trajectory"
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


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def circular_speed(gravity: float, radius: float) -> float:
    return math.sqrt(gravity * radius)


def peak_deceleration(gravity: float, lod: float) -> float:
    """equilibrium_glide_peak_deceleration."""
    return gravity / lod


def entry_deceleration(gravity: float, speed: float, circular: float, lod: float) -> float:
    """equilibrium_glide_entry_deceleration."""
    return gravity * (1.0 - (speed / circular) ** 2) / lod


def heating_speed(entry_speed: float, circular: float) -> float:
    """Speed of maximum sqrt(rho)*V**3 on a subcircular equilibrium glide."""
    return min(entry_speed, circular * math.sqrt(2.0 / 3.0))


def heating_density(ballistic: float, gravity: float, speed: float, circular: float, lod: float) -> float:
    """equilibrium_glide_heating_density."""
    return 2.0 * ballistic * gravity * (1.0 - (speed / circular) ** 2) / (speed**2 * lod)


def heat_flux_scale(density: float, speed: float) -> float:
    """equilibrium_glide_heat_flux_scale."""
    return math.sqrt(density) * speed**3


def altitude(density: float, rho_ref: float, z_ref: float, scale_height: float) -> float:
    return z_ref + scale_height * math.log(rho_ref / density)


def atmosphere_from_args(
    scale_height: float | None, rho_ref: float | None, z_ref: float | None
) -> tuple[float, float, float]:
    given = [scale_height is not None, rho_ref is not None, z_ref is not None]
    if any(given) and not all(given):
        raise ValueError("pass --scale-height, --rho-ref, and --z-ref together")
    if not any(given):
        return DEFAULT_H, DEFAULT_RHO_REF, DEFAULT_Z_REF
    assert scale_height is not None and rho_ref is not None and z_ref is not None
    require_positive("scale height", scale_height)
    require_positive("reference density", rho_ref)
    if not math.isfinite(z_ref):
        raise ValueError("reference altitude must be finite")
    return float(scale_height), float(rho_ref), float(z_ref)


def evaluate(
    entry_speed: float,
    lod: float,
    ballistic: float,
    planet_radius: float,
    scale_height: float,
    rho_ref: float,
    z_ref: float,
) -> dict[str, float]:
    require_positive("entry speed", entry_speed)
    require_positive("lift-to-drag ratio", lod)
    require_positive("ballistic coefficient", ballistic)
    require_positive("planet radius", planet_radius)
    circular = circular_speed(G0, planet_radius)
    if entry_speed >= circular:
        raise ValueError("entry speed must be below circular speed for this equilibrium glide")
    v_q = heating_speed(entry_speed, circular)
    rho_q = heating_density(ballistic, G0, v_q, circular, lod)
    if rho_q <= 0.0:
        raise ValueError("heating density is not positive")
    return {
        "ve_m_s": entry_speed,
        "lod": lod,
        "beta_kg_m2": ballistic,
        "R_m": planet_radius,
        "vc_m_s": circular,
        "a_peak_m_s2": peak_deceleration(G0, lod),
        "a_peak_g": peak_deceleration(G0, lod) / G0,
        "a_entry_m_s2": entry_deceleration(G0, entry_speed, circular, lod),
        "Vq_m_s": v_q,
        "rho_q_kg_m3": rho_q,
        "q_scale": heat_flux_scale(rho_q, v_q),
        "H_m": scale_height,
        "rho_ref_kg_m3": rho_ref,
        "Zref_m": z_ref,
        "Zq_m": altitude(rho_q, rho_ref, z_ref, scale_height),
    }


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot equilibrium glide") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    lod = result["lod"]
    ratios = linspace(0.25 * lod, 2.5 * lod, N_CURVE)
    loads = [peak_deceleration(G0, item) / G0 for item in ratios]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(ratios, loads, color="#1a5276", linewidth=1.8, label=r"$a_{\mathrm{peak}}/g = 1/(L/D)$")
    ax.plot(lod, result["a_peak_g"], "s", color="#1a5276", markersize=7, label="operating point")
    ax.set_xlabel("lift-to-drag ratio")
    ax.set_ylabel("peak horizontal load (g)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: dict[str, float], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key, value in result.items():
        print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def capture(argv: list[str]) -> tuple[int, str, str]:
    from io import StringIO

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    if not close(peak_deceleration(G0, 2.0), G0 / 2.0):
        return fail("peak deceleration")
    circular = circular_speed(G0, R0_EARTH)
    speed = 0.5 * circular
    if not close(entry_deceleration(G0, speed, circular, 2.0), G0 * (1.0 - 0.25) / 2.0):
        return fail("entry deceleration")
    # Heating speed sticks at vc*sqrt(2/3) when entry is faster than that.
    fast = 0.9 * circular
    if not close(heating_speed(fast, circular), circular * math.sqrt(2.0 / 3.0)):
        return fail("fast heating speed")
    slow = 0.2 * circular
    if not close(heating_speed(slow, circular), slow):
        return fail("slow heating speed")
    v_q = circular * math.sqrt(2.0 / 3.0)
    rho = heating_density(100.0, G0, v_q, circular, 1.0)
    # 1 - 2/3 = 1/3; rho = 2*100*g*(1/3) / (v_q^2 * 1) = 200*g/(3 * (2/3) * g * R) = 100 / R
    if not close(rho, 100.0 / R0_EARTH):
        return fail(f"heating density {rho}")
    if not close(heat_flux_scale(4.0, 2.0), 16.0):
        return fail("heat-flux scale")
    if abs(DEFAULT_H - 6705.6) > 1e-6:
        return fail("Earth scale height drifted")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "glide.png"
        code, text, err = capture(
            ["--ve", "7000", "--lod", "1", "--beta", "100", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "a_peak_g: 1" not in text or "q_scale:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(["--ve", "20000", "--lod", "1", "--beta", "100"])
        if code == 0:
            return fail("super-circular entry was accepted")
        code, _text, _err = capture(
            ["--ve", "7000", "--lod", "1", "--beta", "100", "--scale-height", "8000"]
        )
        if code == 0:
            return fail("partial atmosphere override was accepted")

    print("check: pass")
    print_kv("a_peak_g", 1.0)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Equilibrium-glide peak load and heat-flux scale.")
    parser.add_argument("--ve", type=float, default=None, help="entry speed [m/s]")
    parser.add_argument("--lod", type=float, default=None, help="lift-to-drag ratio")
    parser.add_argument("--beta", type=float, default=None, help="ballistic coefficient [kg/m^2]")
    parser.add_argument("--radius", type=float, default=None, help="planet radius [m]")
    parser.add_argument("--scale-height", type=float, default=None, help="density scale height [m]")
    parser.add_argument("--rho-ref", type=float, default=None, help="reference density [kg/m^3]")
    parser.add_argument("--z-ref", type=float, default=None, help="reference altitude [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.ve is None or args.lod is None or args.beta is None:
        print("error: requires --ve, --lod, and --beta", file=sys.stderr)
        return 2
    try:
        scale_height, rho_ref, z_ref = atmosphere_from_args(args.scale_height, args.rho_ref, args.z_ref)
        radius = float(args.radius) if args.radius is not None else R0_EARTH
        result = evaluate(args.ve, args.lod, args.beta, radius, scale_height, rho_ref, z_ref)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(result, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
