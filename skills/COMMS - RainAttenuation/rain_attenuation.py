#!/usr/bin/env python3
"""Slant-path rain attenuation from NASA TP-1770 Table 3.

rain_specific_attenuation is a(f)*R**b(f) in dB/km.
rain_path_attenuation is that value times the effective path in km.
rain_power_ratio is 10**(-A/10).
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Rain attenuation"
N_CURVE = 201
# Marshall-Palmer, 0 C, NASA TP-1770 Table 3. Frequency in GHz.
TABLE = (
    (2.0, 0.000345, 0.891),
    (4.0, 0.00147, 1.016),
    (6.0, 0.00371, 1.124),
    (12.0, 0.0215, 1.136),
    (15.0, 0.0368, 1.118),
    (20.0, 0.0719, 1.097),
    (30.0, 0.186, 1.043),
    (40.0, 0.362, 0.972),
    (94.0, 1.402, 0.744),
)
ELEVATION_WARN = math.radians(10.0)
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "specific attenuation gamma = a(f)*R**b(f) dB/km from NASA TP-1770 Table 3 "
    "(Marshall-Palmer drop distribution, 0 C); coefficients are log-frequency "
    "interpolated between those nodes and are not an ITU table; "
    "rain_path_attenuation A = gamma*L_eff with L_eff the user path in km; "
    "rain_power_ratio = 10**(-A/10); "
    "elevation converts the slant length to an equivalent vertical thickness "
    "h = L_eff*sin(elevation) and does not replace the supplied path; "
    "no gaseous absorption and no free-space path loss"
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


def coefficients(freq_hz: float) -> tuple[float, float]:
    ghz = freq_hz / 1.0e9
    if not math.isfinite(ghz) or ghz < TABLE[0][0] or ghz > TABLE[-1][0]:
        raise ValueError("frequency must be from 2 to 94 GHz")
    for index in range(len(TABLE) - 1):
        f0, a0, b0 = TABLE[index]
        f1, a1, b1 = TABLE[index + 1]
        if ghz <= f1 or index == len(TABLE) - 2:
            if math.isclose(ghz, f0) or f1 == f0:
                return a0, b0
            if ghz > f1:
                continue
            weight = math.log(ghz / f0) / math.log(f1 / f0)
            a_coeff = math.exp(math.log(a0) + weight * (math.log(a1) - math.log(a0)))
            b_coeff = b0 + weight * (b1 - b0)
            return a_coeff, b_coeff
    return TABLE[-1][1], TABLE[-1][2]


def specific_attenuation(a_coeff: float, b_coeff: float, rate: float) -> float:
    """rain_specific_attenuation, dB/km."""
    return a_coeff * rate**b_coeff


def path_attenuation(gamma: float, length_km: float) -> float:
    """rain_path_attenuation, dB."""
    return gamma * length_km


def power_ratio(attenuation_db: float) -> float:
    """rain_power_ratio."""
    return 10.0 ** (-attenuation_db / 10.0)


def evaluate(rate: float, freq_hz: float, elevation: float, path_m: float) -> dict[str, float | str]:
    if not math.isfinite(rate) or rate <= 0.0:
        raise ValueError("rain rate must be finite and > 0")
    if not math.isfinite(path_m) or path_m <= 0.0:
        raise ValueError("path length must be finite and > 0")
    if not math.isfinite(elevation) or elevation <= 0.0 or elevation > 0.5 * math.pi:
        raise ValueError("elevation must be in (0, pi/2]")
    a_coeff, b_coeff = coefficients(freq_hz)
    length_km = path_m / 1000.0
    gamma = specific_attenuation(a_coeff, b_coeff, rate)
    attenuation = path_attenuation(gamma, length_km)
    result: dict[str, float | str] = {
        "rate_mm_h": rate,
        "freq_Hz": freq_hz,
        "elevation_rad": elevation,
        "path_m": path_m,
        "a_coeff": a_coeff,
        "b_coeff": b_coeff,
        "gamma_dB_per_km": gamma,
        "A_dB": attenuation,
        "power_ratio": power_ratio(attenuation),
        "h_vert_m": path_m * math.sin(elevation),
    }
    if elevation < ELEVATION_WARN:
        result["warning"] = (
            "elevation is below 10 degrees; a flat-slab cosecant path is a poor "
            "picture there, and attenuation still uses the supplied path length"
        )
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
        raise ValueError("matplotlib is required to plot rain attenuation") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    rate = float(result["rate_mm_h"])
    a_coeff = float(result["a_coeff"])
    b_coeff = float(result["b_coeff"])
    length_km = float(result["path_m"]) / 1000.0
    rates = linspace(0.05 * rate, 2.0 * rate, N_CURVE)
    losses = [path_attenuation(specific_attenuation(a_coeff, b_coeff, item), length_km) for item in rates]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(rates, losses, color="#1a5276", linewidth=1.8, label="path attenuation")
    ax.plot(rate, float(result["A_dB"]), "s", color="#1a5276", markersize=7, label="operating point")
    ax.set_xlabel("rain rate (mm/h)")
    ax.set_ylabel("attenuation (dB)")
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


def emit(result: dict[str, float | str], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "rate_mm_h",
        "freq_Hz",
        "elevation_rad",
        "path_m",
        "h_vert_m",
        "a_coeff",
        "b_coeff",
        "gamma_dB_per_km",
        "A_dB",
        "power_ratio",
    ):
        print_kv(key, result[key])
    if "warning" in result:
        print_kv("warning", result["warning"])
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
    a_coeff, b_coeff = coefficients(20.0e9)
    if not close(a_coeff, 0.0719) or not close(b_coeff, 1.097):
        return fail("20 GHz node")
    gamma = specific_attenuation(a_coeff, b_coeff, 50.0)
    # TP-1770 Table 3 lists 5.25 dB/km at 20 GHz and 50 mm/h.
    if abs(gamma - 5.25) > 0.05:
        return fail(f"20 GHz specific attenuation {gamma}")
    attenuation = path_attenuation(gamma, 4.0)
    if abs(attenuation - 21.0) > 0.2:
        return fail("4 km path is not about 21 dB")
    if not close(power_ratio(10.0), 0.1):
        return fail("10 dB power ratio")
    low, _b_low = coefficients(2.0e9)
    high, _b_high = coefficients(4.0e9)
    mid_a, _mid_b = coefficients(math.sqrt(2.0 * 4.0) * 1.0e9)
    # Log midpoint of frequency should be the geometric mean of a on a log scale
    # only if b is ignored; a is log-interpolated so at the log midpoint a = sqrt(a0*a1).
    if not close(mid_a, math.sqrt(low * high), tol=1e-6):
        return fail("log interpolation of a")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "rain.png"
        code, text, err = capture(
            ["--rate", "50", "--freq", "20e9", "--elevation", str(math.radians(30.0)), "--path", "4000", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "A_dB:" not in text or "power_ratio:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, text, err = capture(
            ["--rate", "10", "--freq", "12e9", "--elevation", "0.1", "--path", "1000"]
        )
        if code != 0:
            return fail(f"low elevation failed: {err}")
        if "warning:" not in text:
            return fail("low elevation did not warn")
        code, _text, _err = capture(["--rate", "10", "--freq", "1e9", "--elevation", "1", "--path", "1000"])
        if code == 0:
            return fail("frequency below the table was accepted")

    print("check: pass")
    print_kv("A_dB", attenuation)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Slant-path rain attenuation.")
    parser.add_argument("--rate", type=float, default=None, help="rain rate [mm/h]")
    parser.add_argument("--freq", type=float, default=None, help="carrier frequency [Hz]")
    parser.add_argument("--elevation", type=float, default=None, help="elevation above the horizon [rad]")
    parser.add_argument("--path", type=float, default=None, help="effective rainy path length [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if None in (args.rate, args.freq, args.elevation, args.path):
        print("error: requires --rate, --freq, --elevation, and --path", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.rate, args.freq, args.elevation, args.path)
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
