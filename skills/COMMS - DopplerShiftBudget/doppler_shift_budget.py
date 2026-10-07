#!/usr/bin/env python3
"""Carrier Doppler shift and the two-sided span a receiver has to track.

doppler_shift is f*vr/c. The orbit path uses orbit_mask_range_rate.
Earth rotation is omitted on that path.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Doppler shift"
G0 = 9.80665
R0_EARTH = 6.3742e6
C_LIGHT = 299792458.0
N_CURVE = 161
ASSUMPTIONS = (
    "doppler_shift fd = f*vr/c with c = 299792458 m/s; "
    "positive vr increases range; "
    "orbit_mask_range_rate vr_max = v_circ*(R0/a)*cos(elev_min) on a circular orbit; "
    "Earth rotation is omitted from that range rate; "
    "span_Hz = 2*|fd|; not path loss, rain, or Eb/N0"
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


def circular_speed(radius: float) -> float:
    """circular_orbit_velocity at radius = R0 + h, with mu = g0*R0^2."""
    return math.sqrt(G0 * R0_EARTH**2 / radius)


def mask_range_rate(radius: float, elevation: float) -> float:
    """orbit_mask_range_rate."""
    return circular_speed(radius) * (R0_EARTH / radius) * math.cos(elevation)


def doppler_shift(frequency: float, radial: float) -> float:
    """doppler_shift."""
    return frequency * radial / C_LIGHT


def radius_from_inputs(alt: float | None, semi_major: float | None) -> float:
    if (alt is None) == (semi_major is None):
        raise ValueError("the orbit path needs exactly one of --alt or --a")
    if alt is not None:
        require_positive("altitude", alt)
        return R0_EARTH + alt
    require_positive("semi-major axis", float(semi_major))
    if float(semi_major) <= R0_EARTH:
        raise ValueError("semi-major axis must be above the Earth radius")
    return float(semi_major)


def evaluate_radial(frequency: float, radial: float) -> dict[str, float | str]:
    require_positive("frequency", frequency)
    if not math.isfinite(radial):
        raise ValueError("radial speed must be finite")
    fd = doppler_shift(frequency, radial)
    return {
        "path": "radial",
        "freq_Hz": frequency,
        "vr_m_s": radial,
        "fd_Hz": fd,
        "fd_abs_Hz": abs(fd),
        "span_Hz": 2.0 * abs(fd),
    }


def evaluate_orbit(frequency: float, radius: float, elevation: float) -> dict[str, float | str]:
    require_positive("frequency", frequency)
    if not math.isfinite(elevation) or elevation < 0.0 or elevation >= math.pi / 2.0:
        raise ValueError("minimum elevation must be in [0, pi/2)")
    radial = mask_range_rate(radius, elevation)
    fd = doppler_shift(frequency, radial)
    return {
        "path": "orbit",
        "freq_Hz": frequency,
        "a_m": radius,
        "elev_min_rad": elevation,
        "vr_max_m_s": radial,
        "fd_Hz": fd,
        "fd_abs_Hz": abs(fd),
        "span_Hz": 2.0 * abs(fd),
        "earth_rotation": "omitted",
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
        raise ValueError("matplotlib is required to plot Doppler shift") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    frequency = float(result["freq_Hz"])
    radius = float(result["a_m"])
    elevation = float(result["elev_min_rad"])
    span = linspace(elevation, math.pi / 2.0, N_CURVE)
    shifts = [abs(doppler_shift(frequency, mask_range_rate(radius, item))) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, shifts, color="#1a5276", linewidth=1.8, label="|Doppler|")
    ax.plot(elevation, float(result["fd_abs_Hz"]), "s", color="#1a5276", markersize=7, label="mask")
    ax.set_xlabel("elevation (rad)")
    ax.set_ylabel("|Doppler shift| (Hz)")
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
        "path",
        "freq_Hz",
        "vr_m_s",
        "a_m",
        "elev_min_rad",
        "vr_max_m_s",
        "earth_rotation",
        "fd_Hz",
        "fd_abs_Hz",
        "span_Hz",
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
    fd = doppler_shift(1.0e9, C_LIGHT * 1.0e-6)
    if not close(fd, 1000.0):
        return fail("shift")
    if not close(2.0 * abs(doppler_shift(1.0e9, -100.0)), 2.0 * abs(doppler_shift(1.0e9, 100.0))):
        return fail("span")
    radius = R0_EARTH + 600000.0
    rate = mask_range_rate(radius, 0.0)
    if not close(rate, circular_speed(radius) * R0_EARTH / radius):
        return fail("horizon rate")
    if not close(mask_range_rate(radius, math.pi / 2.0), 0.0):
        return fail("zenith rate")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "doppler.png"
        code, text, err = capture(
            ["--freq", "1e9", "--alt", "600000", "--elev-min", "0.2", "--out", str(png)]
        )
        if code != 0:
            return fail(f"orbit path failed: {err}")
        if "earth_rotation: omitted" not in text or "span_Hz:" not in text:
            return fail("orbit stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, text, err = capture(["--freq", "1e9", "--v-radial", "-100"])
        if code != 0:
            return fail(f"radial path failed: {err}")
        if "fd_Hz:" not in text or float(text.split("fd_Hz: ")[1].split()[0]) >= 0.0:
            return fail("signed shift")
        code, _text, _err = capture(["--freq", "1e9", "--v-radial", "10", "--alt", "600000", "--elev-min", "0.2"])
        if code == 0:
            return fail("both speed paths were accepted")

    print("check: pass")
    print_kv("fd_Hz", fd)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Doppler shift and two-sided tracking span.")
    parser.add_argument("--freq", type=float, default=None, help="carrier frequency [Hz]")
    parser.add_argument("--v-radial", type=float, default=None, help="radial speed [m/s], positive when range increases")
    parser.add_argument("--alt", type=float, default=None, help="circular altitude [m]")
    parser.add_argument("--a", type=float, default=None, help="circular radius [m]")
    parser.add_argument("--elev-min", type=float, default=None, help="minimum elevation [rad]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.freq is None:
        print("error: requires --freq and exactly one radial-speed path", file=sys.stderr)
        return 2
    radial_path = args.v_radial is not None
    orbit_path = args.alt is not None or args.a is not None or args.elev_min is not None
    if radial_path == orbit_path:
        print(
            "error: pass --v-radial, or --alt/--a with --elev-min, not both",
            file=sys.stderr,
        )
        return 2
    try:
        if radial_path:
            result = evaluate_radial(args.freq, args.v_radial)
            if args.out is not None:
                print("error: the Doppler plot is only drawn for the orbit path", file=sys.stderr)
                return 2
        else:
            if args.elev_min is None:
                print("error: the orbit path requires --elev-min", file=sys.stderr)
                return 2
            result = evaluate_orbit(args.freq, radius_from_inputs(args.alt, args.a), args.elev_min)
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
