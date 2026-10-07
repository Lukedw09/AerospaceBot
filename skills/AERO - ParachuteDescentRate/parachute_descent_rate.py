#!/usr/bin/env python3
"""Steady parachute descent after the canopy is open.

parachute_descent_rate is V = sqrt(2*W/(rho*Cd*A)) with W = m*g0.
Density is the 1976 standard at --alt, unless --rho overrides it.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Parachute descent rate"
G0 = 9.80665
N_CURVE = 81
Z_PLOT_MAX = 86000.0

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "steady descent after the canopy is open; drag equals weight; "
    "parachute_descent_rate V = sqrt(2*W/(rho*Cd*A)) with W = m*g0 "
    "and g0 = 9.80665 m/s^2; NASA Glenn terminal-velocity statement; "
    "density is ATMOS - Standard1976 at --alt unless --rho overrides it; "
    "each --reef name=cd,area is another open canopy at the same density; "
    "opening shock, inflation time, and a swinging payload are omitted"
)


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    from standard_1976 import atmosphere, require_altitude

    return atmosphere, require_altitude


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


def descent_rate(weight: float, rho: float, cd: float, area: float) -> float:
    """parachute_descent_rate."""
    return math.sqrt(2.0 * weight / (rho * cd * area))


def parse_reef(text: str) -> tuple[str, float, float]:
    if "=" not in text:
        raise ValueError("--reef must be name=cd,area")
    name, rest = text.split("=", 1)
    name = name.strip()
    parts = [item.strip() for item in rest.split(",")]
    if not name or len(parts) != 2:
        raise ValueError("--reef must be name=cd,area")
    try:
        cd = float(parts[0])
        area = float(parts[1])
    except ValueError as exc:
        raise ValueError("--reef cd and area must be numbers") from exc
    require_positive(f"reef {name} Cd", cd)
    require_positive(f"reef {name} area", area)
    return name, cd, area


def evaluate(
    mass: float,
    cd: float,
    area: float,
    rho: float,
    reefs: list[tuple[str, float, float]],
) -> dict[str, float | str]:
    require_positive("mass", mass)
    require_positive("Cd", cd)
    require_positive("area", area)
    require_positive("density", rho)
    weight = mass * G0
    result: dict[str, float | str] = {
        "mass_kg": mass,
        "W_N": weight,
        "Cd": cd,
        "area_m2": area,
        "rho_kg_m3": rho,
        "V_m_s": descent_rate(weight, rho, cd, area),
    }
    seen: set[str] = set()
    for name, reef_cd, reef_area in reefs:
        if name in seen:
            raise ValueError(f"reef name {name} is repeated")
        seen.add(name)
        result[f"reef_{name}_Cd"] = reef_cd
        result[f"reef_{name}_area_m2"] = reef_area
        result[f"reef_{name}_V_m_s"] = descent_rate(weight, rho, reef_cd, reef_area)
    return result


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
        raise ValueError("matplotlib is required to plot descent rate") from exc
    return plt


def write_plot(result: dict[str, float | str], altitude: float | None, out_path: Path) -> None:
    atmosphere, require_altitude = load_atmosphere()
    plt = ensure_matplotlib()
    weight = float(result["W_N"])
    cd = float(result["Cd"])
    area = float(result["area_m2"])
    altitudes = linspace(0.0, Z_PLOT_MAX, N_CURVE)
    rates = [
        descent_rate(weight, atmosphere(z)["rho"], cd, area) for z in altitudes
    ]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(altitudes, rates, color="#1a5276", linewidth=1.8, label="descent rate")
    if altitude is not None:
        require_altitude(altitude, "--alt")
        ax.plot(
            altitude,
            float(result["V_m_s"]),
            "s",
            color="#1a5276",
            markersize=7,
            label="operating altitude",
        )
    ax.set_xlabel("geometric altitude (m)")
    ax.set_ylabel("descent rate (m/s)")
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


def emit(result: dict[str, float | str], rho_source: str, altitude: float | None, graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("rho_source", rho_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
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
    weight = 2.0 * G0
    rho = 1.0
    rate = descent_rate(weight, rho, 1.0, 2.0)
    if not close(rate, math.sqrt(2.0 * G0)):
        return fail("sea-level identity")
    result = evaluate(2.0, 1.0, 2.0, rho, [("reefed", 0.5, 2.0)])
    if not close(float(result["V_m_s"]), math.sqrt(2.0 * G0)):
        return fail("unreefed rate")
    if not close(float(result["reef_reefed_V_m_s"]), math.sqrt(4.0 * G0)):
        return fail("reefed rate")
    atmosphere, _require = load_atmosphere()
    sea = atmosphere(0.0)["rho"]
    from_alt = evaluate(80.0, 1.75, 2.0, sea, [])
    if not close(float(from_alt["rho_kg_m3"]), sea):
        return fail("altitude density")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "chute.png"
        code, text, err = capture(
            [
                "--mass",
                "80",
                "--cd",
                "1.75",
                "--area",
                "2",
                "--alt",
                "0",
                "--reef",
                "reefed=0.8,1.2",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "rho_kg_m3:" not in text or "V_m_s:" not in text or "reef_reefed_V_m_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, err = capture(["--mass", "80", "--cd", "1", "--area", "1", "--rho", "1.2", "--alt", "0"])
        if code != 2 or "override" not in err and "both" not in err:
            return fail("alt and rho together")

    print("check: pass")
    print_kv("V_m_s", rate)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Steady parachute descent rate.")
    parser.add_argument("--mass", type=float, default=None, help="payload mass [kg]")
    parser.add_argument("--cd", type=float, default=None, help="unreefed drag coefficient")
    parser.add_argument("--area", type=float, default=None, help="unreefed reference area [m^2]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--rho", type=float, default=None, help="density override [kg/m^3]")
    parser.add_argument(
        "--reef",
        action="append",
        default=[],
        help="reefed canopy name=cd,area",
    )
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.mass is None or args.cd is None or args.area is None:
        print("error: requires --mass, --cd, and --area", file=sys.stderr)
        return 2
    if args.alt is None and args.rho is None:
        print("error: requires --alt or --rho", file=sys.stderr)
        return 2
    if args.alt is not None and args.rho is not None:
        print("error: pass --alt or --rho, not both; --rho is the density override", file=sys.stderr)
        return 2
    try:
        reefs = [parse_reef(item) for item in args.reef]
        if args.rho is not None:
            rho = args.rho
            rho_source = "override"
            altitude = None
        else:
            atmosphere, require_altitude = load_atmosphere()
            altitude = require_altitude(args.alt, "--alt")
            rho = atmosphere(altitude)["rho"]
            rho_source = "altitude"
        result = evaluate(args.mass, args.cd, args.area, rho, reefs)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(result, altitude, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, rho_source, altitude, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
