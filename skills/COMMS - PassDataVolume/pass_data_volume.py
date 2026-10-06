#!/usr/bin/env python3
"""Bits stored over a pass, and the bit rate the link budget must carry."""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "Pass data volume"
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "required information rate is stored bits times coding overhead divided by "
    "pass duration; volume is rate times duration divided by overhead; overhead "
    "is a user factor at or above 1; either direction uses the same relation; "
    "no atmosphere, rain, or modulation curve"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def rate_from_volume(bits: float, duration_s: float, overhead: float) -> float:
    """required_pass_bit_rate."""
    return bits * overhead / duration_s


def volume_from_rate(rate: float, duration_s: float, overhead: float) -> float:
    """pass_data_volume."""
    return rate * duration_s / overhead


def emit(rows: list[tuple[str, float | str]], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "pass data volume and required bit rate")
    for key, value in rows:
        print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(bits: float, overhead: float, duration_s: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    durations = [duration_s * (0.25 + 0.05 * i) for i in range(30)]
    rates = [rate_from_volume(bits, t, overhead) / 1.0e6 for t in durations]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(durations, rates, color="C0", label="required rate")
    ax.plot(duration_s, rate_from_volume(bits, duration_s, overhead) / 1.0e6, "s", color="C1", label="operating point")
    ax.set_xlabel("pass duration (s)")
    ax.set_ylabel("required rate (Mbit/s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    bits = 2.0e9
    duration = 480.0
    overhead = 1.2
    rate = rate_from_volume(bits, duration, overhead)
    if abs(rate - bits * overhead / duration) > 1e-6:
        return fail("rate")
    back = volume_from_rate(rate, duration, overhead)
    if abs(back - bits) > 1.0:
        return fail("round trip")
    # Overhead 1 is the bare information rate.
    if abs(rate_from_volume(8.0e6, 8.0, 1.0) - 1.0e6) > 1e-9:
        return fail("bare rate")
    if main(["--bits", "1000", "--duration", "10", "--rate", "100"]) == 0:
        return fail("both bits and rate accepted")
    if main(["--bits", "1000", "--duration", "10", "--overhead", "0.5"]) == 0:
        return fail("overhead below 1 accepted")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pass.png"
        code = main(["--bits", "2e9", "--duration", "480", "--overhead", "1.2", "--out", str(path)])
        if code != 0 or path.stat().st_size < 1000:
            return fail("plot")
    print("check: pass")
    print_kv("R_bps", rate)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pass data volume or the bit rate that volume requires.")
    parser.add_argument("--bits", type=float, default=None, help="stored information bits")
    parser.add_argument("--rate", type=float, default=None, help="information bit rate [bit/s]")
    parser.add_argument("--duration", type=float, default=None, help="pass duration [s]")
    parser.add_argument("--overhead", type=float, default=1.0, help="coding overhead factor, >= 1")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.duration is None or args.duration <= 0.0:
        print("error: requires a positive --duration", file=sys.stderr)
        return 2
    if (args.bits is None) == (args.rate is None):
        print("error: pass exactly one of --bits or --rate", file=sys.stderr)
        return 2
    if args.overhead < 1.0 or not math.isfinite(args.overhead):
        print("error: --overhead must be >= 1", file=sys.stderr)
        return 2
    if args.bits is not None:
        if args.bits <= 0.0:
            print("error: --bits must be positive", file=sys.stderr)
            return 2
        rate = rate_from_volume(args.bits, args.duration, args.overhead)
        rows: list[tuple[str, float | str]] = [
            ("direction_input", "bits"),
            ("bits", args.bits),
            ("t_pass_s", args.duration),
            ("overhead", args.overhead),
            ("R_bps", rate),
        ]
    else:
        if args.rate is None or args.rate <= 0.0:
            print("error: --rate must be positive", file=sys.stderr)
            return 2
        bits = volume_from_rate(args.rate, args.duration, args.overhead)
        rows = [
            ("direction_input", "rate"),
            ("R_bps", args.rate),
            ("t_pass_s", args.duration),
            ("overhead", args.overhead),
            ("bits", bits),
        ]
    graph = None
    if args.out is not None:
        try:
            stored = args.bits if args.bits is not None else volume_from_rate(args.rate, args.duration, args.overhead)
            write_plot(stored, args.overhead, args.duration, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(rows, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
