#!/usr/bin/env python3
"""Critical half-length of a through crack in a wide plate.

fracture_critical_half_length is a_c = (1/pi)*(KIc/(Y*sigma))**2.
An optional actual half-length prints margin_of_safety = a_c/a - 1.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Fracture critical crack"
N_CURVE = 161

ASSUMPTIONS = (
    "through crack in a wide plate; "
    "fracture_critical_half_length a_c = (1/pi)*(KIc/(Y*sigma))**2; "
    "Y is the geometry factor and defaults to 1; "
    "margin_of_safety = a_c/a - 1 when an actual half-length is given; "
    "no crack-growth rate and no spectrum loading"
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


def critical_half_length(kic: float, stress: float, geometry: float) -> float:
    """fracture_critical_half_length."""
    return (kic / (geometry * stress)) ** 2 / math.pi


def evaluate(
    kic: float,
    stress: float,
    geometry: float,
    crack: float | None,
) -> dict[str, float]:
    require_positive("fracture toughness", kic)
    require_positive("stress", stress)
    require_positive("geometry factor", geometry)
    ac = critical_half_length(kic, stress, geometry)
    result = {
        "KIc_Pa_m_sqrt": kic,
        "stress_Pa": stress,
        "Y": geometry,
        "a_c_m": ac,
    }
    if crack is not None:
        require_positive("crack half-length", crack)
        result["a_m"] = crack
        result["margin_of_safety"] = ac / crack - 1.0
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
        raise ValueError("matplotlib is required to plot critical crack length") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    kic = result["KIc_Pa_m_sqrt"]
    geometry = result["Y"]
    stress = result["stress_Pa"]
    span = linspace(0.25 * stress, 2.0 * stress, N_CURVE)
    lengths = [critical_half_length(kic, item, geometry) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, lengths, color="#1a5276", linewidth=1.8, label="critical half-length")
    ax.plot(stress, result["a_c_m"], "s", color="#1a5276", markersize=7, label="operating stress")
    ax.set_xlabel("stress (Pa)")
    ax.set_ylabel("critical half-length (m)")
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
    for key in (
        "KIc_Pa_m_sqrt",
        "stress_Pa",
        "Y",
        "a_c_m",
        "a_m",
        "margin_of_safety",
    ):
        if key in result:
            print_kv(key, result[key])
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
    ac = critical_half_length(math.sqrt(math.pi), 1.0, 1.0)
    if not close(ac, 1.0):
        return fail("unit crack")
    result = evaluate(math.sqrt(math.pi), 2.0, 1.0, 0.125)
    if not close(result["a_c_m"], 0.25) or not close(result["margin_of_safety"], 1.0):
        return fail("margin")
    if not close(critical_half_length(2.0, 1.0, 2.0), critical_half_length(1.0, 1.0, 1.0)):
        return fail("geometry factor")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "crack.png"
        code, text, err = capture(
            ["--kic", "50e6", "--stress", "200e6", "--geometry", "1.12", "--crack", "0.002", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "a_c_m:" not in text or "margin_of_safety:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("a_c_m", ac)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Critical half-length of a through crack in a wide plate.")
    parser.add_argument("--kic", type=float, default=None, help="plane-strain fracture toughness [Pa*m^0.5]")
    parser.add_argument("--stress", type=float, default=None, help="remote tensile stress [Pa]")
    parser.add_argument("--geometry", type=float, default=1.0, help="geometry factor Y; default 1")
    parser.add_argument("--crack", type=float, default=None, help="actual half-length [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.kic is None or args.stress is None:
        print("error: requires --kic and --stress", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.kic, args.stress, args.geometry, args.crack)
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
