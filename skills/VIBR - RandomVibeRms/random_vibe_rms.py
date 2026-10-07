#!/usr/bin/env python3
"""Miles rms acceleration of one resonator under a flat acceleration spectrum.

miles_rms_acceleration is sqrt((pi/2)*fn*Q*W0).
g_3sigma is 3*g_rms, the usual peak estimate, not a probability bound.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Random vibration rms"
N_CURVE = 161
PEAK_NOTE = "usual peak estimate, not a probability bound"
ASSUMPTIONS = (
    "single resonator driven by a flat acceleration spectrum at resonance; "
    "miles_rms_acceleration g_rms = sqrt((pi/2)*fn*Q*W0); "
    "Q = 1/(2*zeta) when damping ratio is the input; "
    "g_3sigma = 3*g_rms is the usual peak estimate, not a probability bound; "
    "not a sine base-shake ratio and not a shock response spectrum"
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


def quality_from_zeta(zeta: float) -> float:
    return 1.0 / (2.0 * zeta)


def rms_acceleration(fn: float, quality: float, psd: float) -> float:
    """miles_rms_acceleration, in g."""
    return math.sqrt(0.5 * math.pi * fn * quality * psd)


def evaluate(fn: float, psd: float, quality: float) -> dict[str, float | str]:
    require_positive("natural frequency", fn)
    if not math.isfinite(psd) or psd < 0.0:
        raise ValueError("PSD must be finite and >= 0")
    require_positive("quality factor", quality)
    g_rms = rms_acceleration(fn, quality, psd)
    return {
        "fn_Hz": fn,
        "psd_g2_Hz": psd,
        "Q": quality,
        "g_rms": g_rms,
        "g_3sigma": 3.0 * g_rms,
        "g_3sigma_note": PEAK_NOTE,
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
        raise ValueError("matplotlib is required to plot rms acceleration") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    fn = float(result["fn_Hz"])
    psd = float(result["psd_g2_Hz"])
    quality = float(result["Q"])
    span = linspace(0.2 * fn, 3.0 * fn, N_CURVE)
    curve = [rms_acceleration(item, quality, psd) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, curve, color="#1a5276", linewidth=1.8, label="rms acceleration")
    ax.plot(fn, float(result["g_rms"]), "s", color="#1a5276", markersize=7, label="operating frequency")
    ax.set_xlabel("natural frequency (Hz)")
    ax.set_ylabel("rms acceleration (g)")
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
    for key in ("fn_Hz", "psd_g2_Hz", "Q", "g_rms", "g_3sigma", "g_3sigma_note"):
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
    if not close(quality_from_zeta(0.05), 10.0):
        return fail("Q")
    g_rms = rms_acceleration(2.0 / math.pi, 1.0, 1.0)
    if not close(g_rms, 1.0):
        return fail("miles")
    if not close(3.0 * g_rms, 3.0):
        return fail("three sigma")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "miles.png"
        code, text, err = capture(
            ["--fn", "100", "--psd", "0.01", "--zeta", "0.05", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "Q: 10" not in text or "g_3sigma_note:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(["--fn", "100", "--psd", "0.01", "--q", "10", "--zeta", "0.05"])
        if code == 0:
            return fail("both Q and zeta were accepted")
        code, text, err = capture(["--fn", "100", "--psd", "0.01", "--q", "10"])
        if code != 0:
            return fail(f"Q path failed: {err}")
        if "Q: 10" not in text:
            return fail("Q path stdout")

    print("check: pass")
    print_kv("g_rms", g_rms)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Miles rms acceleration for a flat spectrum.")
    parser.add_argument("--fn", type=float, default=None, help="natural frequency [Hz]")
    parser.add_argument("--psd", type=float, default=None, help="flat acceleration PSD at resonance [g^2/Hz]")
    parser.add_argument("--q", type=float, default=None, help="quality factor")
    parser.add_argument("--zeta", type=float, default=None, help="damping ratio")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.fn is None or args.psd is None:
        print("error: requires --fn, --psd, and exactly one of --q or --zeta", file=sys.stderr)
        return 2
    if (args.q is None) == (args.zeta is None):
        print("error: pass exactly one of --q or --zeta", file=sys.stderr)
        return 2
    try:
        if args.q is not None:
            quality = float(args.q)
        else:
            require_positive("damping ratio", float(args.zeta))
            quality = quality_from_zeta(float(args.zeta))
        result = evaluate(args.fn, args.psd, quality)
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
