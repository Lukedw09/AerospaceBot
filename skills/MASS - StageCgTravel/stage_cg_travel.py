#!/usr/bin/env python3
"""Center-of-mass travel of a burning stage along one axis.

At burn fraction f the propellant mass is mp0*(1-f) and its station moves
linearly from x_full to x_empty. The stage station is center_of_mass_coordinate.
The stack is that sum over every stage. Inert hardware stays in the dry mass.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Stage CG travel"
N_CURVE = 101

ASSUMPTIONS = (
    "one-axis burn; propellant mass mp = mp0*(1-f); "
    "propellant station xp = x_full + f*(x_empty-x_full); "
    "stage station is center_of_mass_coordinate of dry mass and remaining propellant; "
    "the stack is the same sum over every stage at one burn fraction; "
    "dry mass and its station stay fixed; "
    "inert mass and tank shells stay in ROCKET - VehicleMassBudget; "
    "no products of inertia"
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


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def propellant_mass(mp0: float, fraction: float) -> float:
    """stage_propellant_remaining."""
    return mp0 * (1.0 - fraction)


def propellant_station(x_full: float, x_empty: float, fraction: float) -> float:
    """stage_propellant_station."""
    return x_full + fraction * (x_empty - x_full)


def stage_station(dry: float, x_dry: float, mp: float, xp: float) -> float:
    """center_of_mass_coordinate of dry hardware and remaining propellant."""
    return (dry * x_dry + mp * xp) / (dry + mp)


def parse_stage(text: str) -> tuple[float, float, float, float, float]:
    parts = [item.strip() for item in text.split(",")]
    if len(parts) != 5:
        raise ValueError("--stage must be dry,x_dry,mp,x_full,x_empty")
    try:
        dry, x_dry, mp, x_full, x_empty = (float(item) for item in parts)
    except ValueError as exc:
        raise ValueError("--stage values must be numbers") from exc
    require_positive("dry mass", dry)
    require_finite("dry station", x_dry)
    require_positive("propellant mass", mp)
    require_finite("full station", x_full)
    require_finite("empty station", x_empty)
    return dry, x_dry, mp, x_full, x_empty


def stack_at(
    stages: list[tuple[float, float, float, float, float]],
    fraction: float,
) -> tuple[float, list[float]]:
    if not math.isfinite(fraction) or fraction < 0.0 or fraction > 1.0:
        raise ValueError("burn fraction must be from 0 to 1")
    moment = 0.0
    mass = 0.0
    stations: list[float] = []
    for dry, x_dry, mp0, x_full, x_empty in stages:
        mp = propellant_mass(mp0, fraction)
        xp = propellant_station(x_full, x_empty, fraction)
        x = stage_station(dry, x_dry, mp, xp)
        stations.append(x)
        moment += (dry + mp) * x
        mass += dry + mp
    return moment / mass, stations


def evaluate(
    stages: list[tuple[float, float, float, float, float]],
    fraction: float,
) -> dict[str, float]:
    if not stages:
        raise ValueError("at least one --stage is required")
    stack, stations = stack_at(stages, fraction)
    result: dict[str, float] = {"fraction": fraction, "stack_x_m": stack}
    total = 0.0
    for index, ((dry, x_dry, mp0, x_full, x_empty), station) in enumerate(zip(stages, stations), start=1):
        mp = propellant_mass(mp0, fraction)
        result[f"stage_{index}_dry_kg"] = dry
        result[f"stage_{index}_x_dry_m"] = x_dry
        result[f"stage_{index}_mp_kg"] = mp
        result[f"stage_{index}_x_m"] = station
        total += dry + mp
    result["stack_mass_kg"] = total
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
        raise ValueError("matplotlib is required to plot CG travel") from exc
    return plt


def write_plot(
    stages: list[tuple[float, float, float, float, float]],
    fraction: float,
    out_path: Path,
) -> None:
    plt = ensure_matplotlib()
    fractions = linspace(0.0, 1.0, N_CURVE)
    stack = [stack_at(stages, item)[0] for item in fractions]
    mark, _stations = stack_at(stages, fraction)
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(fractions, stack, color="#1a5276", linewidth=1.8, label="stack station")
    ax.plot(fraction, mark, "s", color="#1a5276", markersize=7, label="printed fraction")
    ax.set_xlabel("burn fraction")
    ax.set_ylabel("stack station (m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
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
    if not close(propellant_mass(10.0, 0.25), 7.5):
        return fail("remaining propellant")
    if not close(propellant_station(0.0, 4.0, 0.25), 1.0):
        return fail("propellant station")
    if not close(stage_station(2.0, 1.0, 2.0, 3.0), 2.0):
        return fail("stage station")
    stages = [(2.0, 0.0, 2.0, 4.0, 0.0), (1.0, 10.0, 1.0, 10.0, 8.0)]
    full, _stations = stack_at(stages, 0.0)
    # masses 2 at 0, prop 2 at 4, dry 1 at 10, prop 1 at 10 -> moment 8+10+10 = 28, mass 6
    if not close(full, 28.0 / 6.0):
        return fail("full stack")
    empty, stations = stack_at(stages, 1.0)
    if not close(stations[0], 0.0) or not close(stations[1], 10.0):
        return fail("empty stations")
    if not close(empty, 10.0 / 3.0):
        return fail("empty stack")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "cg.png"
        code, text, err = capture(
            [
                "--stage",
                "2,0,2,4,0",
                "--stage",
                "1,10,1,10,8",
                "--fraction",
                "0.5",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "stack_x_m:" not in text or "stage_1_x_m:" not in text or "stage_2_mp_kg: 0.5" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("stack_x_m", full)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage center-of-mass travel during a burn.")
    parser.add_argument(
        "--stage",
        action="append",
        default=[],
        help="dry,x_dry,mp,x_full,x_empty in kilograms and metres",
    )
    parser.add_argument("--fraction", type=float, default=None, help="burn fraction from 0 to 1")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if not args.stage:
        print("error: at least one --stage is required", file=sys.stderr)
        return 2
    if args.fraction is None:
        print("error: requires --fraction", file=sys.stderr)
        return 2
    try:
        stages = [parse_stage(item) for item in args.stage]
        result = evaluate(stages, args.fraction)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(stages, args.fraction, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
