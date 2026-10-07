#!/usr/bin/env python3
"""Absolute displacement transmissibility of a base-excited SDOF oscillator.

frequency_ratio is r = f/fn.
displacement_transmissibility is |X/Y|.
transmissibility_peak_ratio is r_peak = sqrt(1 - 2*zeta^2) when zeta < 1/sqrt(2).
Isolation is r > sqrt(2).
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Base excitation transmissibility"
N_CURVE = 400
R_ISOLATION = math.sqrt(2.0)
ZETA_PEAK_LIMIT = 1.0 / math.sqrt(2.0)
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "single degree of freedom; linear spring and viscous damper in parallel; "
    "base motion y = Y*sin(omega*t); mass motion x is absolute; "
    "frequency_ratio r = f/fn; "
    "displacement_transmissibility "
    "T = sqrt((1+(2*zeta*r)**2)/((1-r**2)**2+(2*zeta*r)**2)); "
    "isolation when r > sqrt(2), where T < 1; "
    "transmissibility_peak_ratio r_peak = sqrt(1-2*zeta**2) when zeta < 1/sqrt(2); "
    "not force transmissibility, random vibration, or a shock response spectrum"
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


def frequency_ratio(drive_hz: float, natural_hz: float) -> float:
    """frequency_ratio."""
    return drive_hz / natural_hz


def displacement_transmissibility(ratio: float, zeta: float) -> float:
    """displacement_transmissibility."""
    two = 2.0 * zeta * ratio
    numer = 1.0 + two * two
    denom = (1.0 - ratio * ratio) ** 2 + two * two
    return math.sqrt(numer / denom)


def peak_ratio(zeta: float) -> float | None:
    """transmissibility_peak_ratio, or None when damping removes the peak."""
    if zeta >= ZETA_PEAK_LIMIT:
        return None
    return math.sqrt(1.0 - 2.0 * zeta * zeta)


def isolation(ratio: float) -> str:
    return "yes" if ratio > R_ISOLATION else "no"


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def evaluate(natural_hz: float, zeta: float, drive_hz: float) -> dict[str, float | str]:
    require_positive("natural frequency", natural_hz)
    require_positive("drive frequency", drive_hz)
    if not math.isfinite(zeta) or zeta < 0.0:
        raise ValueError("damping ratio must be finite and >= 0")
    ratio = frequency_ratio(drive_hz, natural_hz)
    if zeta == 0.0 and math.isclose(ratio, 1.0):
        raise ValueError(
            "undamped resonance has no steady transmissibility; raise damping or move off fn"
        )
    result: dict[str, float | str] = {
        "fn_Hz": natural_hz,
        "f_Hz": drive_hz,
        "zeta": zeta,
        "r": ratio,
        "T": displacement_transmissibility(ratio, zeta),
        "isolation": isolation(ratio),
    }
    r_peak = peak_ratio(zeta)
    if r_peak is not None:
        result["r_peak"] = r_peak
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
        raise ValueError("matplotlib is required to plot transmissibility") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    zeta = float(result["zeta"])
    ratio = float(result["r"])
    r_max = max(3.0, ratio * 1.25)
    ratios = linspace(0.0, r_max, N_CURVE)
    values = [displacement_transmissibility(r, zeta) if r > 0.0 else 1.0 for r in ratios]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(ratios, values, color="#1a5276", linewidth=1.8, label=r"$T(r)$")
    ax.plot(ratio, float(result["T"]), "s", color="#1a5276", markersize=7, zorder=5, label="operating point")
    ax.axvline(R_ISOLATION, color="#c0392b", linestyle="--", linewidth=1.2, label=r"$r=\sqrt{2}$")
    ax.axhline(1.0, color="#7f8c8d", linestyle=":", linewidth=1.0)
    ax.set_xlabel("frequency ratio r")
    ax.set_ylabel("displacement transmissibility T")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, r_max)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: dict[str, float | str], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("fn_Hz", result["fn_Hz"])
    print_kv("f_Hz", result["f_Hz"])
    print_kv("zeta", result["zeta"])
    print_kv("r", result["r"])
    print_kv("T", result["T"])
    print_kv("isolation", result["isolation"])
    if "r_peak" in result:
        print_kv("r_peak", result["r_peak"])
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
    if not close(frequency_ratio(20.0, 10.0), 2.0):
        return fail("frequency ratio")
    if not close(displacement_transmissibility(0.0, 0.1), 1.0):
        return fail("static transmissibility")
    # At r = sqrt(2), T = 1 for any zeta.
    if not close(displacement_transmissibility(R_ISOLATION, 0.05), 1.0):
        return fail("isolation boundary")
    if not close(displacement_transmissibility(R_ISOLATION, 0.4), 1.0):
        return fail("isolation boundary at higher damping")
    if isolation(R_ISOLATION) != "no" or isolation(R_ISOLATION + 0.01) != "yes":
        return fail("isolation flag")
    zeta = 0.1
    r_peak = peak_ratio(zeta)
    if r_peak is None or not close(r_peak, math.sqrt(1.0 - 2.0 * zeta * zeta)):
        return fail("peak ratio")
    if peak_ratio(0.8) is not None:
        return fail("overdamped peak should be absent")
    # Peak is a maximum: T(r_peak) >= T at a nearby ratio.
    t_peak = displacement_transmissibility(r_peak, zeta)
    if t_peak < displacement_transmissibility(r_peak * 0.9, zeta):
        return fail("peak is not above the left neighbor")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "t.png"
        code, text, err = capture(["--fn", "10", "--zeta", "0.1", "--f", "20", "--out", str(png)])
        if code != 0:
            return fail(f"run failed: {err}")
        if "isolation: yes" not in text or "r: 2" not in text:
            return fail("stdout")
        if "r_peak:" not in text:
            return fail("missing peak ratio")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, text, err = capture(["--fn", "10", "--zeta", "0.9", "--f", "5"])
        if code != 0:
            return fail(f"high damping failed: {err}")
        if "r_peak:" in text:
            return fail("high damping printed a peak ratio")
        if "isolation: no" not in text:
            return fail("r = 0.5 should not isolate")

    print("check: pass")
    print_kv("T", displacement_transmissibility(2.0, 0.1))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Absolute displacement transmissibility for harmonic base excitation."
    )
    parser.add_argument("--fn", type=float, default=None, help="undamped natural frequency [Hz]")
    parser.add_argument("--zeta", type=float, default=None, help="damping ratio")
    parser.add_argument("--f", type=float, default=None, help="base drive frequency [Hz]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.fn is None or args.zeta is None or args.f is None:
        print("error: requires --fn, --zeta, and --f", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.fn, args.zeta, args.f)
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
