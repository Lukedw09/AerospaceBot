#!/usr/bin/env python3
"""Propellant mass from a sum of named vacuum delta-v contributions."""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

G0 = 9.80665
PLOT_TITLE = "Vacuum propellant mass"
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "vacuum rocket equation inverted at one exhaust speed; delta-v is the sum "
    "of the named contributions the user supplies; optional growth fraction "
    "applies only to the dry mass given here; not a stage stack, mixture ratio, "
    "or tank wall"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def exhaust_speed(isp: float | None, ve: float | None) -> float:
    if (isp is None) == (ve is None):
        raise ValueError("pass exactly one of --isp or --ve")
    if ve is not None:
        if ve <= 0.0:
            raise ValueError("--ve must be positive")
        return ve
    assert isp is not None
    if isp <= 0.0:
        raise ValueError("--isp must be positive")
    return isp * G0


def propellant_mass(dry: float, growth: float, delta_v: float, ve: float) -> tuple[float, float, float]:
    """Inverse of delta_v_vacuum. Returns final mass, propellant, wet mass."""
    if dry <= 0.0 or growth < 0.0 or delta_v < 0.0 or ve <= 0.0:
        raise ValueError("dry mass and exhaust speed must be positive; growth and delta-v >= 0")
    final = dry * (1.0 + growth)
    ratio = math.exp(delta_v / ve)
    wet = final * ratio
    return final, wet - final, wet


def emit(names: list[str], pieces: list[float], final: float, propellant: float, wet: float, ve: float, growth: float, graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "vacuum propellant from summed delta-v")
    print_kv("ve_m_s", ve)
    print_kv("growth", growth)
    print_kv("n_contributions", len(pieces))
    for name, piece in zip(names, pieces, strict=True):
        print_kv(f"dv_{name}_m_s", piece)
    print_kv("dv_total_m_s", sum(pieces))
    print_kv("m_final_kg", final)
    print_kv("m_propellant_kg", propellant)
    print_kv("m_wet_kg", wet)
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(final: float, ve: float, delta_v: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    span = max(delta_v, 100.0)
    speeds = [span * 0.05 * (i + 1) for i in range(40)]
    propellant = [final * (math.exp(dv / ve) - 1.0) for dv in speeds]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(speeds, propellant, color="C0", label="propellant")
    ax.plot(delta_v, final * (math.exp(delta_v / ve) - 1.0), "s", color="C1", label="operating point")
    ax.set_xlabel(r"total $\Delta v$ (m/s)")
    ax.set_ylabel("propellant mass (kg)")
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

    # Catalogue identity: delta_v = c*log(m0/mf), so m0/mf = exp(dv/c).
    dry = 80.0
    growth = 0.1
    pieces = [120.0, 30.0, 15.0]
    ve = 220.0 * G0
    final, propellant, wet = propellant_mass(dry, growth, sum(pieces), ve)
    ratio = math.exp(sum(pieces) / ve)
    if abs(wet / final - ratio) > 1e-12:
        return fail("mass ratio")
    if abs(propellant - final * (ratio - 1.0)) > 1e-9:
        return fail("propellant")
    if abs(final - dry * 1.1) > 1e-12:
        return fail("growth applies to dry mass only")
    # Zero delta-v leaves wet equal to the grown dry mass.
    _, zero_prop, zero_wet = propellant_mass(dry, 0.0, 0.0, ve)
    if abs(zero_prop) > 1e-12 or abs(zero_wet - dry) > 1e-12:
        return fail("zero delta-v")
    # Isp and ve must be mutually exclusive.
    if main(["--dry", "80", "--isp", "220", "--ve", "2000", "--dv", "100"]) == 0:
        return fail("both isp and ve accepted")
    if main(["--dry", "80", "--isp", "220", "--dv", "100", "--dv", "50"]) != 0:
        return fail("two contributions")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "prop.png"
        code = main(["--dry", "80", "--growth", "0.1", "--isp", "220", "--name", "transfer", "--dv", "120", "--name", "drag", "--dv", "30", "--name", "disposal", "--dv", "15", "--out", str(path)])
        if code != 0 or path.stat().st_size < 1000:
            return fail("plot")
    print("check: pass")
    print_kv("m_propellant_kg", propellant)
    print_kv("m_wet_kg", wet)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vacuum propellant mass from named delta-v pieces.")
    parser.add_argument("--dry", type=float, default=None)
    parser.add_argument("--growth", type=float, default=0.0)
    parser.add_argument("--isp", type=float, default=None)
    parser.add_argument("--ve", type=float, default=None)
    parser.add_argument("--name", action="append", default=None)
    parser.add_argument("--dv", type=float, action="append", default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.dry is None or not args.dv:
        print("error: requires --dry and at least one --dv", file=sys.stderr)
        return 2
    try:
        ve = exhaust_speed(args.isp, args.ve)
        names = args.name or []
        if names and len(names) != len(args.dv):
            raise ValueError("--name count must match --dv")
        if not names:
            names = [str(i + 1) for i in range(len(args.dv))]
        pieces = []
        for piece in args.dv:
            if piece < 0.0 or not math.isfinite(piece):
                raise ValueError("--dv must be >= 0")
            pieces.append(piece)
        final, propellant, wet = propellant_mass(args.dry, args.growth, sum(pieces), ve)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(final, ve, sum(pieces), args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(names, pieces, final, propellant, wet, ve, args.growth, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
