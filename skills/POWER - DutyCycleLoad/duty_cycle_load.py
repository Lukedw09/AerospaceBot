#!/usr/bin/env python3
"""Orbit-average electrical load from a duty-cycled power list."""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "Duty-cycle load"
CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "each load is a constant power while it is on; orbit-average power is the "
    "sum of power times on-fraction; peak power is the sum of the listed powers "
    "(coincident-on upper bound); eclipse energy uses the eclipse on-fraction "
    "when that list is given, otherwise the orbit-average power times the "
    "eclipse duration; no cell model, no regulation loss, and no CubeSat rail"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_positive(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be finite and positive")
    return value


def require_fraction(value: float, flag: str) -> float:
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{flag} must be a fraction from 0 to 1")
    return value


def average_power(powers: list[float], duties: list[float]) -> float:
    """orbit_average_load: sum of P*f."""
    return sum(p * f for p, f in zip(powers, duties, strict=True))


def peak_power(powers: list[float]) -> float:
    """coincident_peak_load: sum of the listed powers."""
    return sum(powers)


def eclipse_energy(power: float, duration_s: float) -> float:
    """eclipse_load_energy: E = P*t."""
    return power * duration_s


def resolve(
    powers: list[float],
    duties: list[float],
    eclipse_duties: list[float] | None,
    eclipse_s: float | None,
) -> dict[str, float | str]:
    if len(powers) != len(duties) or not powers:
        raise ValueError("pass the same number of --power and --duty values, at least one")
    if eclipse_duties is not None and len(eclipse_duties) != len(powers):
        raise ValueError("--eclipse-duty must match --power")
    for power in powers:
        require_positive(power, "--power")
    for duty in duties:
        require_fraction(duty, "--duty")
    if eclipse_duties is not None:
        for duty in eclipse_duties:
            require_fraction(duty, "--eclipse-duty")
    if eclipse_s is not None:
        require_positive(eclipse_s, "--eclipse")
    p_avg = average_power(powers, duties)
    p_peak = peak_power(powers)
    result: dict[str, float | str] = {
        "n_loads": float(len(powers)),
        "P_avg": p_avg,
        "P_peak": p_peak,
        "energy_source": "none",
    }
    if eclipse_s is None:
        return result
    if eclipse_duties is None:
        p_ecl = p_avg
        source = "orbit_average"
    else:
        p_ecl = average_power(powers, eclipse_duties)
        source = "eclipse_duty"
    result["P_eclipse"] = p_ecl
    result["t_eclipse"] = eclipse_s
    result["E_eclipse"] = eclipse_energy(p_ecl, eclipse_s)
    result["energy_source"] = source
    return result


def emit(state: dict[str, float | str], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "duty-cycled electrical load")
    print_kv("n_loads", int(state["n_loads"]))
    print_kv("P_avg_W", state["P_avg"])
    print_kv("P_peak_W", state["P_peak"])
    print_kv("energy_source", state["energy_source"])
    if "E_eclipse" in state:
        print_kv("P_eclipse_W", state["P_eclipse"])
        print_kv("t_eclipse_s", state["t_eclipse"])
        print_kv("E_eclipse_J", state["E_eclipse"])
        print_kv("E_eclipse_Wh", float(state["E_eclipse"]) / 3600.0)
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(powers: list[float], duties: list[float], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    labels = [f"load {i + 1}" for i in range(len(powers))]
    orbit = [p * f for p, f in zip(powers, duties)]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    xpos = list(range(len(powers)))
    ax.bar([x - 0.18 for x in xpos], powers, width=0.36, label="nameplate")
    ax.bar([x + 0.18 for x in xpos], orbit, width=0.36, label="orbit average")
    ax.set_xticks(xpos, labels)
    ax.set_ylabel("power (W)")
    ax.set_title(PLOT_TITLE)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    # Two loads: 10 W always on, 20 W on half the orbit.
    state = resolve([10.0, 20.0], [1.0, 0.5], None, 1800.0)
    if abs(float(state["P_avg"]) - 20.0) > 1e-12:
        return fail("orbit average")
    if abs(float(state["P_peak"]) - 30.0) > 1e-12:
        return fail("peak")
    if abs(float(state["E_eclipse"]) - 36000.0) > 1e-9:
        return fail("eclipse energy from orbit average")
    # Eclipse duties differ from the orbit duties.
    eclipse = resolve([10.0, 20.0], [0.2, 0.2], [1.0, 0.0], 1000.0)
    if abs(float(eclipse["P_eclipse"]) - 10.0) > 1e-12:
        return fail("eclipse duty power")
    if abs(float(eclipse["E_eclipse"]) - 10000.0) > 1e-9:
        return fail("eclipse duty energy")
    if eclipse["energy_source"] != "eclipse_duty":
        return fail("energy source")
    try:
        resolve([10.0], [1.2], None, None)
        return fail("duty above 1 was accepted")
    except ValueError:
        pass
    try:
        resolve([10.0, 5.0], [1.0], None, None)
        return fail("mismatched lists were accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "loads.png"
        if main(["--power", "10", "--duty", "1", "--power", "20", "--duty", "0.5", "--eclipse", "1800", "--out", str(path)]) != 0:
            return fail("plot run")
        if path.stat().st_size < 1000:
            return fail("plot missing")
    print("check: pass")
    print_kv("P_avg_W", state["P_avg"])
    print_kv("E_eclipse_J", state["E_eclipse"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Duty-cycled spacecraft electrical load.")
    parser.add_argument("--power", type=float, action="append", default=None, help="load power [W]")
    parser.add_argument("--duty", type=float, action="append", default=None, help="orbit on-fraction")
    parser.add_argument("--eclipse-duty", type=float, action="append", default=None, help="eclipse on-fraction")
    parser.add_argument("--eclipse", type=float, default=None, help="eclipse duration [s]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if not args.power or not args.duty:
        print("error: requires --power and --duty", file=sys.stderr)
        return 2
    try:
        powers = [require_positive(p, "--power") for p in args.power]
        duties = [require_fraction(f, "--duty") for f in args.duty]
        eclipse_duties = None
        if args.eclipse_duty is not None:
            eclipse_duties = [require_fraction(f, "--eclipse-duty") for f in args.eclipse_duty]
        eclipse_s = None if args.eclipse is None else require_positive(args.eclipse, "--eclipse")
        state = resolve(powers, duties, eclipse_duties, eclipse_s)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(powers, duties, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(state, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
