#!/usr/bin/env python3
"""Elastic critical stress of a simply supported rectangular plate in uniaxial compression.

plate_buckling_stress uses k. A long plate (no length) uses k = 4.
simply_supported_plate_k is minimized over the half-wave count when length is given.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Panel buckling"
LONG_PLATE_K = 4.0
N_CURVE = 161
ASSUMPTIONS = (
    "elastic uniaxial compression of a rectangular plate with four simply supported edges; "
    "plate_buckling_stress sigma_cr = k*pi^2*E/(12*(1-nu^2)*(b/t)^2); "
    "compression runs along the length; b is the unloaded-edge spacing; "
    "no length uses the long-plate coefficient k = 4; "
    "with length, k = min over positive integers m of (m*b/a + a/(m*b))^2; "
    "no plasticity, shear, biaxial load, or stiffened-panel knockdown"
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


def halfwave_k(length: float, width: float, waves: int) -> float:
    """simply_supported_plate_k for one half-wave count."""
    return (waves * width / length + length / (waves * width)) ** 2


def minimize_k(length: float, width: float) -> tuple[int, float]:
    ratio = length / width
    upper = max(8, int(math.ceil(ratio)) + 4)
    best_waves = 1
    best = halfwave_k(length, width, 1)
    for waves in range(2, upper + 1):
        value = halfwave_k(length, width, waves)
        if value < best:
            best = value
            best_waves = waves
    return best_waves, best


def critical_stress(modulus: float, nu: float, width: float, thickness: float, k: float) -> float:
    """plate_buckling_stress."""
    return k * math.pi**2 * modulus / (12.0 * (1.0 - nu**2) * (width / thickness) ** 2)


def evaluate(
    modulus: float,
    nu: float,
    width: float,
    thickness: float,
    length: float | None,
    stress: float | None,
) -> dict[str, float | str | int]:
    require_positive("Young's modulus", modulus)
    if not math.isfinite(nu) or abs(nu) >= 1.0:
        raise ValueError("Poisson's ratio must be finite and have absolute value < 1")
    require_positive("width", width)
    require_positive("thickness", thickness)
    if length is None:
        waves = None
        k = LONG_PLATE_K
    else:
        require_positive("length", length)
        waves, k = minimize_k(length, width)
    sigma = critical_stress(modulus, nu, width, thickness, k)
    result: dict[str, float | str | int] = {
        "E_Pa": modulus,
        "nu": nu,
        "width_m": width,
        "thickness_m": thickness,
        "b_over_t": width / thickness,
        "k": k,
        "sigma_cr_Pa": sigma,
    }
    if length is not None and waves is not None:
        result["length_m"] = length
        result["half_waves"] = waves
    if stress is not None:
        require_positive("applied stress", stress)
        result["stress_Pa"] = stress
        result["margin_of_safety"] = sigma / stress - 1.0
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
        raise ValueError("matplotlib is required to plot critical stress") from exc
    return plt


def write_plot(result: dict[str, float | str | int], out_path: Path) -> None:
    plt = ensure_matplotlib()
    modulus = float(result["E_Pa"])
    nu = float(result["nu"])
    thickness = float(result["thickness_m"])
    k = float(result["k"])
    ratio = float(result["b_over_t"])
    span = linspace(max(5.0, 0.25 * ratio), max(ratio * 2.0, ratio + 20.0), N_CURVE)
    stresses = [critical_stress(modulus, nu, item * thickness, thickness, k) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, stresses, color="#1a5276", linewidth=1.8, label="critical stress")
    ax.plot(ratio, float(result["sigma_cr_Pa"]), "s", color="#1a5276", markersize=7, label="operating plate")
    ax.set_xlabel("b/t")
    ax.set_ylabel("critical stress (Pa)")
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


def emit(result: dict[str, float | str | int], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "E_Pa",
        "nu",
        "width_m",
        "thickness_m",
        "length_m",
        "b_over_t",
        "k",
        "half_waves",
        "sigma_cr_Pa",
        "stress_Pa",
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
    if not close(halfwave_k(1.0, 1.0, 1), 4.0):
        return fail("square k")
    waves, k = minimize_k(1.5, 1.0)
    expected = (2.0 / 1.5 + 1.5 / 2.0) ** 2
    if waves != 2 or not close(k, expected):
        return fail("half-wave search")
    sigma = critical_stress(70.0e9, 0.3, 0.5, 0.002, LONG_PLATE_K)
    hand = LONG_PLATE_K * math.pi**2 * 70.0e9 / (12.0 * (1.0 - 0.3**2) * (250.0**2))
    if not close(sigma, hand):
        return fail("stress")
    result = evaluate(70.0e9, 0.3, 0.5, 0.002, None, hand)
    if not close(float(result["margin_of_safety"]), 0.0):
        return fail("margin")
    if float(result["k"]) != LONG_PLATE_K:
        return fail("long plate k")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "panel.png"
        code, text, err = capture(
            [
                "--E",
                "70e9",
                "--nu",
                "0.3",
                "--width",
                "0.5",
                "--thickness",
                "0.002",
                "--length",
                "1.5",
                "--stress",
                "1e8",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "half_waves: 3" not in text or "k: 4" not in text or "margin_of_safety:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("sigma_cr_Pa", sigma)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simply supported plate buckling stress.")
    parser.add_argument("--E", type=float, default=None, help="Young's modulus [Pa]")
    parser.add_argument("--nu", type=float, default=None, help="Poisson's ratio")
    parser.add_argument("--width", type=float, default=None, help="unloaded-edge spacing b [m]")
    parser.add_argument("--thickness", type=float, default=None, help="plate thickness [m]")
    parser.add_argument("--length", type=float, default=None, help="loaded length a [m]; omit for a long plate")
    parser.add_argument("--stress", type=float, default=None, help="applied compressive stress [Pa]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.E is None or args.nu is None or args.width is None or args.thickness is None:
        print("error: requires --E, --nu, --width, and --thickness", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.E, args.nu, args.width, args.thickness, args.length, args.stress)
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
