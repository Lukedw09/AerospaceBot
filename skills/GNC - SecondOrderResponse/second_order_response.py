#!/usr/bin/env python3
"""Linear second-order unit-step response metrics.

natural_frequency_mass_stiffness is wn = sqrt(k/m).
damping_ratio_mass_stiffness is zeta = c/(2*sqrt(k*m)).
damped_natural_frequency is wd = wn*sqrt(1-zeta**2).
second_order_percent_overshoot is Mp = exp(-pi*zeta/sqrt(1-zeta**2)).
second_order_peak_time is tp = pi/wd.
second_order_settling_time is ts = -log(delta)/(zeta*wn).
Rise time is 10% to 90% of the analytical unit-step response.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Second-order unit-step response"
N_CURVE = 801
DEFAULT_SETTLING_PERCENT = 2.0
CRITICAL_EPS = 1e-12
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "linear constant-coefficient single-input second-order plant "
    "G(s) = wn**2/(s**2 + 2*zeta*wn*s + wn**2); "
    "natural_frequency_mass_stiffness wn = sqrt(k/m); "
    "damping_ratio_mass_stiffness zeta = c/(2*sqrt(k*m)); "
    "damped_natural_frequency wd = wn*sqrt(1-zeta**2) when zeta < 1; "
    "second_order_percent_overshoot Mp = exp(-pi*zeta/sqrt(1-zeta**2)); "
    "second_order_peak_time tp = pi/wd; "
    "second_order_settling_time envelope ts = -ln(delta)/(zeta*wn) with "
    f"default band {DEFAULT_SETTLING_PERCENT:g} percent so delta = "
    f"{DEFAULT_SETTLING_PERCENT/100:g}; "
    "rise_time is 10% to 90% of the analytical unit-step response; "
    "underdamped when zeta < 1, critically damped when zeta = 1, "
    "overdamped when zeta > 1; zero initial conditions; unity DC gain"
)


@dataclass(frozen=True)
class Solution:
    wn: float
    zeta: float
    source: str
    mass: float | None
    stiffness: float | None
    damping: float | None
    settling_percent: float
    delta: float
    damping_case: str
    wd: float | None
    overshoot: float
    overshoot_percent: float
    peak_time: float | None
    rise_time: float
    settling_time_envelope: float | None
    settling_time: float


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


def require_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def natural_frequency_mass_stiffness(stiffness: float, mass: float) -> float:
    """natural_frequency_mass_stiffness: wn = sqrt(k/m)."""
    return math.sqrt(stiffness / mass)


def damping_ratio_mass_stiffness(
    damping: float, stiffness: float, mass: float
) -> float:
    """damping_ratio_mass_stiffness: zeta = c/(2*sqrt(k*m))."""
    return damping / (2.0 * math.sqrt(stiffness * mass))


def damped_natural_frequency(wn: float, zeta: float) -> float:
    """damped_natural_frequency: wd = wn*sqrt(1-zeta**2)."""
    return wn * math.sqrt(1.0 - zeta * zeta)


def second_order_percent_overshoot(zeta: float) -> float:
    """second_order_percent_overshoot: fractional Mp."""
    return math.exp(-math.pi * zeta / math.sqrt(1.0 - zeta * zeta))


def second_order_peak_time(wn: float, zeta: float) -> float:
    """second_order_peak_time: tp = pi/wd."""
    return math.pi / damped_natural_frequency(wn, zeta)


def second_order_settling_time(delta: float, zeta: float, wn: float) -> float:
    """second_order_settling_time: ts = -log(delta)/(zeta*wn)."""
    return -math.log(delta) / (zeta * wn)


def classify_damping(zeta: float) -> str:
    if zeta < 1.0 - CRITICAL_EPS:
        return "underdamped"
    if zeta > 1.0 + CRITICAL_EPS:
        return "overdamped"
    return "critically_damped"


def step_response(wn: float, zeta: float, time: float) -> float:
    """Unit-step response of wn**2/(s**2 + 2*zeta*wn*s + wn**2)."""
    if time <= 0.0:
        return 0.0
    case = classify_damping(zeta)
    if case == "underdamped":
        wd = damped_natural_frequency(wn, zeta)
        sigma = zeta * wn
        return 1.0 - math.exp(-sigma * time) * (
            math.cos(wd * time) + (sigma / wd) * math.sin(wd * time)
        )
    if case == "critically_damped":
        return 1.0 - math.exp(-wn * time) * (1.0 + wn * time)
    root = math.sqrt(zeta * zeta - 1.0)
    s1 = wn * (zeta + root)
    s2 = wn * (zeta - root)
    return 1.0 - (s1 * math.exp(-s2 * time) - s2 * math.exp(-s1 * time)) / (
        s1 - s2
    )


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def first_crossing(
    wn: float, zeta: float, level: float, t_end: float, samples: int = 4001
) -> float | None:
    times = linspace(0.0, t_end, samples)
    prev_t = times[0]
    prev_y = step_response(wn, zeta, prev_t)
    for time in times[1:]:
        y = step_response(wn, zeta, time)
        if (prev_y - level) * (y - level) <= 0.0 and y != prev_y:
            frac = (level - prev_y) / (y - prev_y)
            return prev_t + frac * (time - prev_t)
        prev_t = time
        prev_y = y
    return None


def rise_time_10_90(wn: float, zeta: float) -> float:
    t_end = max(20.0 / max(zeta * wn, 0.05 * wn), 20.0 / wn)
    t10 = first_crossing(wn, zeta, 0.1, t_end)
    t90 = first_crossing(wn, zeta, 0.9, t_end)
    if t10 is None or t90 is None or t90 <= t10:
        raise ValueError("could not resolve 10% to 90% rise time")
    return t90 - t10


def settling_time_from_response(
    wn: float, zeta: float, delta: float
) -> float:
    """First time after which |y-1| stays within delta through t_end."""
    t_end = max(30.0 / max(zeta * wn, 0.05 * wn), 30.0 / wn)
    times = linspace(0.0, t_end, 8001)
    values = [step_response(wn, zeta, t) for t in times]
    last_out = 0
    for i, y in enumerate(values):
        if abs(y - 1.0) > delta:
            last_out = i
    if last_out >= len(times) - 1:
        raise ValueError("could not resolve settling time in the plotted window")
    if last_out == 0 and abs(values[0] - 1.0) <= delta:
        return 0.0
    # Refine between last_out and last_out+1, then verify the tail.
    t0 = times[last_out]
    t1 = times[min(last_out + 1, len(times) - 1)]
    for _ in range(40):
        mid = 0.5 * (t0 + t1)
        if abs(step_response(wn, zeta, mid) - 1.0) > delta:
            t0 = mid
        else:
            t1 = mid
    candidate = t1
    for t in linspace(candidate, t_end, 2001):
        if abs(step_response(wn, zeta, t) - 1.0) > delta:
            raise ValueError("settling-time search left the band again")
    return candidate


def evaluate(
    wn: float | None,
    zeta: float | None,
    mass: float | None,
    stiffness: float | None,
    damping: float | None,
    settling_percent: float,
) -> Solution:
    require_positive("settling percent", settling_percent)
    if settling_percent >= 100.0:
        raise ValueError("settling percent must be < 100")
    delta = settling_percent / 100.0

    has_wn = wn is not None
    has_zeta = zeta is not None
    has_m = mass is not None
    has_k = stiffness is not None
    has_c = damping is not None
    mechanical = has_m or has_k or has_c
    modal = has_wn or has_zeta

    if mechanical and modal:
        raise ValueError(
            "pass --wn with --zeta, or --mass --stiffness --damping, not both"
        )
    if mechanical:
        if not (has_m and has_k and has_c):
            raise ValueError(
                "mechanical path requires --mass, --stiffness, and --damping"
            )
        require_positive("mass", float(mass))
        require_positive("stiffness", float(stiffness))
        require_nonnegative("damping", float(damping))
        wn_v = natural_frequency_mass_stiffness(float(stiffness), float(mass))
        zeta_v = damping_ratio_mass_stiffness(
            float(damping), float(stiffness), float(mass)
        )
        source = "mass_stiffness_damping"
        m_v: float | None = float(mass)
        k_v: float | None = float(stiffness)
        c_v: float | None = float(damping)
    elif has_wn and has_zeta:
        require_positive("natural frequency", float(wn))
        require_nonnegative("damping ratio", float(zeta))
        wn_v = float(wn)
        zeta_v = float(zeta)
        source = "wn_zeta"
        m_v = None
        k_v = None
        c_v = None
    else:
        raise ValueError(
            "requires --wn with --zeta, or --mass --stiffness --damping"
        )

    case = classify_damping(zeta_v)
    wd: float | None = None
    peak: float | None = None
    if case == "underdamped":
        wd = damped_natural_frequency(wn_v, zeta_v)
        overshoot = second_order_percent_overshoot(zeta_v)
        peak = second_order_peak_time(wn_v, zeta_v)
    else:
        overshoot = 0.0

    envelope: float | None = None
    if zeta_v > 0.0:
        envelope = second_order_settling_time(delta, zeta_v, wn_v)

    rise = rise_time_10_90(wn_v, zeta_v)
    settle = settling_time_from_response(wn_v, zeta_v, delta)

    return Solution(
        wn=wn_v,
        zeta=zeta_v,
        source=source,
        mass=m_v,
        stiffness=k_v,
        damping=c_v,
        settling_percent=settling_percent,
        delta=delta,
        damping_case=case,
        wd=wd,
        overshoot=overshoot,
        overshoot_percent=100.0 * overshoot,
        peak_time=peak,
        rise_time=rise,
        settling_time_envelope=envelope,
        settling_time=settle,
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the step response") from exc
    return plt


def plot_horizon(result: Solution) -> float:
    if result.settling_time_envelope is not None:
        return max(1.5 * result.settling_time_envelope, 1.5 * result.settling_time)
    return max(1.5 * result.settling_time, 10.0 / result.wn)


def write_plot(result: Solution, out_path: Path) -> None:
    plt = ensure_matplotlib()
    t_end = plot_horizon(result)
    times = linspace(0.0, t_end, N_CURVE)
    values = [step_response(result.wn, result.zeta, t) for t in times]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(times, values, color="#1a5276", linewidth=1.8, label="unit step")
    ax.axhline(1.0, color="#7f8c8d", linestyle=":", linewidth=1.0, label="final value")
    ax.axhline(
        1.0 + result.delta,
        color="#c0392b",
        linestyle="--",
        linewidth=1.2,
        label=f"+/- {result.settling_percent:g}% band",
    )
    ax.axhline(1.0 - result.delta, color="#c0392b", linestyle="--", linewidth=1.2)
    if result.peak_time is not None:
        y_peak = step_response(result.wn, result.zeta, result.peak_time)
        ax.plot(
            result.peak_time,
            y_peak,
            "s",
            color="#1a5276",
            markersize=6,
            zorder=5,
            label="peak",
        )
    ax.axvline(
        result.settling_time,
        color="#117a65",
        linestyle="-.",
        linewidth=1.2,
        label="settling time",
    )
    ax.set_xlabel("time (s)")
    ax.set_ylabel("output")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, t_end)
    ax.set_ylim(bottom=min(0.0, min(values) - 0.05))
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: Solution, graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("source", result.source)
    if result.mass is not None:
        print_kv("m_kg", result.mass)
        print_kv("k_N_m", result.stiffness)
        print_kv("c_N_s_m", result.damping)
    print_kv("wn_rad_s", result.wn)
    print_kv("zeta", result.zeta)
    print_kv("damping_case", result.damping_case)
    if result.wd is not None:
        print_kv("wd_rad_s", result.wd)
    print_kv("overshoot", result.overshoot)
    print_kv("overshoot_percent", result.overshoot_percent)
    if result.peak_time is not None:
        print_kv("peak_time_s", result.peak_time)
    print_kv("rise_time_s", result.rise_time)
    print_kv("rise_time_definition", "10_to_90_percent")
    print_kv("settling_percent", result.settling_percent)
    print_kv("settling_delta", result.delta)
    if result.settling_time_envelope is not None:
        print_kv("settling_time_envelope_s", result.settling_time_envelope)
    print_kv("settling_time_s", result.settling_time)
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(natural_frequency_mass_stiffness(4.0, 1.0), 2.0):
        return fail("wn from k=4, m=1 is not 2")
    if not close(damping_ratio_mass_stiffness(1.0, 1.0, 1.0), 0.5):
        return fail("half-critical zeta is not 0.5")
    if not close(damped_natural_frequency(2.0, 0.5), math.sqrt(3.0)):
        return fail("wd for wn=2, zeta=0.5 is not sqrt(3)")
    mp = second_order_percent_overshoot(0.5)
    if not close(mp, math.exp(-math.pi / math.sqrt(3.0))):
        return fail("overshoot for zeta=0.5 mismatch")
    if not close(second_order_peak_time(2.0, 0.5), math.pi / math.sqrt(3.0)):
        return fail("peak time for wn=2, zeta=0.5 mismatch")
    if not close(second_order_settling_time(math.exp(-4.0), 0.5, 2.0), 4.0):
        return fail("four-time-constant settling is not 4")

    under = evaluate(2.0, 0.5, None, None, None, 2.0)
    if under.damping_case != "underdamped":
        return fail("zeta=0.5 was not underdamped")
    if under.wd is None or under.peak_time is None:
        return fail("underdamped path omitted wd or peak time")
    if under.rise_time <= 0.0:
        return fail("rise time is not positive")
    if under.settling_time <= 0.0:
        return fail("settling time is not positive")

    mech = evaluate(None, None, 1.0, 4.0, 2.0, 2.0)
    if not close(mech.wn, 2.0) or not close(mech.zeta, 0.5):
        return fail("mechanical path did not recover wn=2, zeta=0.5")
    if mech.source != "mass_stiffness_damping":
        return fail("mechanical source label wrong")

    critical = evaluate(1.0, 1.0, None, None, None, 2.0)
    if critical.damping_case != "critically_damped":
        return fail("zeta=1 was not critically damped")
    if critical.wd is not None or critical.peak_time is not None:
        return fail("critical case printed oscillatory metrics")
    if not close(critical.overshoot, 0.0):
        return fail("critical overshoot is not 0")

    over = evaluate(1.0, 1.5, None, None, None, 2.0)
    if over.damping_case != "overdamped":
        return fail("zeta=1.5 was not overdamped")
    if not close(over.overshoot, 0.0):
        return fail("overdamped overshoot is not 0")

    # Analytic underdamped sample at peak time.
    y_peak = step_response(2.0, 0.5, under.peak_time)
    if not close(y_peak, 1.0 + under.overshoot, tol=1e-6):
        return fail("step response at peak time does not match overshoot")

    try:
        evaluate(2.0, 0.5, 1.0, 4.0, 2.0, 2.0)
        return fail("both input paths were accepted")
    except ValueError:
        pass
    try:
        evaluate(None, None, 1.0, 4.0, None, 2.0)
        return fail("incomplete mechanical path was accepted")
    except ValueError:
        pass
    try:
        evaluate(2.0, None, None, None, None, 2.0)
        return fail("wn without zeta was accepted")
    except ValueError:
        pass

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "second_order.png")
        code, text, err = capture(
            ["--wn", "2", "--zeta", "0.5", "--settling-percent", "2", "--out", out]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Second-order unit-step response",
            "damping_case: underdamped",
            "wd_rad_s:",
            "overshoot:",
            "peak_time_s:",
            "rise_time_s:",
            "settling_time_s:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            ["--mass", "1", "--stiffness", "4", "--damping", "2", "--out", out]
        )
        if code != 0:
            return fail(f"mechanical input returned {code}: {err}")
        if "source: mass_stiffness_damping" not in text:
            return fail("mechanical input did not print source")
        if "wn_rad_s:" not in text or "zeta:" not in text:
            return fail("mechanical input omitted wn or zeta")

        code, _text, err = capture(["--wn", "2", "--zeta", "0.5", "--mass", "1"])
        if code != 2 or "not both" not in err:
            return fail("both input paths were accepted on the CLI")
        code, _text, err = capture(["--wn", "2"])
        if code != 2:
            return fail("wn without zeta was accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("empty args were accepted")

    print("check: pass")
    print_kv("wn_rad_s", under.wn)
    print_kv("zeta", under.zeta)
    print_kv("wd_rad_s", under.wd)
    print_kv("overshoot", under.overshoot)
    print_kv("peak_time_s", under.peak_time)
    print_kv("rise_time_s", under.rise_time)
    print_kv("settling_time_s", under.settling_time)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Linear second-order unit-step response: damped frequency, "
            "overshoot, peak time, rise time, settling time, and damping case."
        )
    )
    parser.add_argument("--wn", type=float, default=None, help="natural frequency wn [rad/s]")
    parser.add_argument("--zeta", type=float, default=None, help="damping ratio zeta [-]")
    parser.add_argument("--mass", type=float, default=None, help="mass m [kg]")
    parser.add_argument(
        "--stiffness", type=float, default=None, help="stiffness k [N/m]"
    )
    parser.add_argument(
        "--damping", type=float, default=None, help="viscous damping c [N*s/m]"
    )
    parser.add_argument(
        "--settling-percent",
        type=float,
        default=DEFAULT_SETTLING_PERCENT,
        help=f"settling band percent (default {DEFAULT_SETTLING_PERCENT:g})",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    try:
        result = evaluate(
            args.wn,
            args.zeta,
            args.mass,
            args.stiffness,
            args.damping,
            args.settling_percent,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph: Path | None = None
    if args.out is not None:
        out_path = Path(args.out).resolve()
        try:
            write_plot(result, out_path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = out_path

    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
