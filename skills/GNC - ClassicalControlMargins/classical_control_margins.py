#!/usr/bin/env python3
"""Bode gain and phase margins of a polynomial loop transfer.

bode_magnitude_db, bode_phase_deg, phase_margin_deg, and gain_margin_db
evaluate the complex value at a crossover. series_pid_real and
series_pid_imag are the optional series compensator. The program finds
the crossover frequencies.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-6
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Classical control margins"
W_MIN = 1.0e-3
W_MAX = 1.0e4
N_GRID = 600

ASSUMPTIONS = (
    "unity-feedback open-loop L(s) is a ratio of real polynomials; "
    "coefficients are highest power first; "
    "bode_magnitude_db is 20*log10(|L|); "
    "phase uses a four-quadrant argument in degrees; "
    "phase_margin_deg is 180 plus the phase at the first gain crossover; "
    "gain_margin_db is -20*log10(|L|) at the first phase crossover of -180 deg; "
    "a series PID is C = kd*s + kp + ki/s when any of --kp, --ki, --kd is set; "
    "omitted PID gains are 0; "
    "stability is the closed-loop characteristic polynomial den(L)+num(L); "
    "root-locus geometry is not computed"
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


def horner(coeffs: list[float], re: float, im: float) -> tuple[float, float]:
    out_re = 0.0
    out_im = 0.0
    for coeff in coeffs:
        next_re = out_re * re - out_im * im + coeff
        next_im = out_re * im + out_im * re
        out_re, out_im = next_re, next_im
    return out_re, out_im


def eval_ratio(num: list[float], den: list[float], omega: float) -> tuple[float, float]:
    num_re, num_im = horner(num, 0.0, omega)
    den_re, den_im = horner(den, 0.0, omega)
    scale = den_re * den_re + den_im * den_im
    if scale == 0.0:
        raise ValueError("the loop transfer is singular at this frequency")
    return (num_re * den_re + num_im * den_im) / scale, (num_im * den_re - num_re * den_im) / scale


def bode_magnitude_db(re: float, im: float) -> float:
    return 20.0 * math.log(math.hypot(re, im)) / math.log(10.0)


def convolve(left: list[float], right: list[float]) -> list[float]:
    out = [0.0] * (len(left) + len(right) - 1)
    for i, a_coeff in enumerate(left):
        for j, b_coeff in enumerate(right):
            out[i + j] += a_coeff * b_coeff
    return out


def strip_leading(coeffs: list[float]) -> list[float]:
    index = 0
    while index < len(coeffs) - 1 and abs(coeffs[index]) <= 1e-14 * max(1.0, max(abs(c) for c in coeffs)):
        index += 1
    return coeffs[index:]


def loop_transfer(
    num: list[float], den: list[float], kp: float | None, ki: float | None, kd: float | None
) -> tuple[list[float], list[float], str]:
    if not num or not den:
        raise ValueError("--num and --den each need at least one coefficient")
    if any(not math.isfinite(value) for value in num + den):
        raise ValueError("coefficients must be finite")
    if abs(den[0]) == 0.0:
        raise ValueError("the leading denominator coefficient must be nonzero")
    if kp is None and ki is None and kd is None:
        return strip_leading(num), strip_leading(den), "plant"
    gains = (0.0 if kp is None else kp, 0.0 if ki is None else ki, 0.0 if kd is None else kd)
    if any(not math.isfinite(value) for value in gains):
        raise ValueError("PID gains must be finite")
    proportional, integral, derivative = gains
    num_l = strip_leading(convolve([derivative, proportional, integral], num))
    den_l = strip_leading(convolve([1.0, 0.0], den))
    while len(num_l) > 1 and len(den_l) > 1 and num_l[-1] == 0.0 and den_l[-1] == 0.0:
        num_l = num_l[:-1]
        den_l = den_l[:-1]
    return num_l, den_l, "series_pid"


def characteristic(num: list[float], den: list[float]) -> list[float]:
    width = max(len(num), len(den))
    num_p = [0.0] * (width - len(num)) + num
    den_p = [0.0] * (width - len(den)) + den
    return strip_leading([a_coeff + b_coeff for a_coeff, b_coeff in zip(den_p, num_p)])


def polynomial_roots(coeffs: list[float]) -> list[complex]:
    coeffs = strip_leading(coeffs)
    degree = len(coeffs) - 1
    if degree <= 0:
        return []
    if degree == 1:
        return [-coeffs[1] / coeffs[0]]
    if degree == 2:
        a_coeff, b_coeff, c_coeff = coeffs
        disc = b_coeff * b_coeff - 4.0 * a_coeff * c_coeff
        root = math.sqrt(abs(disc))
        if disc >= 0.0:
            return [(-b_coeff + root) / (2 * a_coeff), (-b_coeff - root) / (2 * a_coeff)]
        return [
            complex(-b_coeff / (2 * a_coeff), root / (2 * a_coeff)),
            complex(-b_coeff / (2 * a_coeff), -root / (2 * a_coeff)),
        ]
    lead = coeffs[0]
    monic = [value / lead for value in coeffs]
    radius = 1.0 + max(abs(value) for value in monic[1:])
    guesses = [
        complex(
            radius * math.cos(2.0 * math.pi * k / degree),
            radius * math.sin(2.0 * math.pi * k / degree),
        )
        for k in range(degree)
    ]
    for _ in range(80):
        updated: list[complex] = []
        for index, guess in enumerate(guesses):
            value = complex(monic[0], 0.0)
            for coeff in monic[1:]:
                value = value * guess + coeff
            denom = 1.0 + 0.0j
            for other_index, other in enumerate(guesses):
                if other_index != index:
                    denom *= guess - other
            if denom == 0:
                updated.append(guess + 1e-3)
            else:
                updated.append(guess - value / denom)
        guesses = updated
    return guesses


def stability(num: list[float], den: list[float]) -> str:
    roots = polynomial_roots(characteristic(num, den))
    if any(root.real > 1e-7 for root in roots):
        return "no"
    if any(abs(root.real) <= 1e-7 for root in roots):
        return "marginal"
    return "yes"


def dc_gain(num: list[float], den: list[float]) -> float:
    if abs(den[-1]) <= 1e-14 * max(1.0, abs(num[-1])):
        return math.inf
    return num[-1] / den[-1]


def response_grid(num: list[float], den: list[float]) -> list[tuple[float, float, float, float]]:
    rows: list[tuple[float, float, float, float]] = []
    phase = 0.0
    previous = None
    for index in range(N_GRID):
        omega = W_MIN * (W_MAX / W_MIN) ** (index / (N_GRID - 1))
        re, im = eval_ratio(num, den, omega)
        angle = math.atan2(im, re)
        if previous is None:
            phase = angle
        else:
            phase += (angle - previous + math.pi) % (2.0 * math.pi) - math.pi
        previous = angle
        rows.append((omega, math.hypot(re, im), phase, bode_magnitude_db(re, im)))
    return rows


def continuous_phase(angle: float, reference: float) -> float:
    while angle - reference > math.pi:
        angle -= 2.0 * math.pi
    while reference - angle > math.pi:
        angle += 2.0 * math.pi
    return angle


def first_crossing(
    rows: list[tuple[float, float, float, float]],
    kind: str,
    num: list[float],
    den: list[float],
) -> float | None:
    for left, right in zip(rows, rows[1:]):
        if kind == "gain":
            y0, y1 = math.log(max(left[1], 1e-30)), math.log(max(right[1], 1e-30))
            target = 0.0
        else:
            y0, y1 = left[2], right[2]
            target = -math.pi
        if (y0 - target) == 0.0:
            return left[0]
        if (y0 - target) * (y1 - target) < 0.0:
            lo, hi = left[0], right[0]
            for _ in range(60):
                mid = math.sqrt(lo * hi)
                re, im = eval_ratio(num, den, mid)
                if kind == "gain":
                    value = math.log(max(math.hypot(re, im), 1e-30))
                else:
                    value = continuous_phase(math.atan2(im, re), y0)
                if (y0 - target) * (value - target) <= 0.0:
                    hi = mid
                    y1 = value
                else:
                    lo = mid
                    y0 = value
            return math.sqrt(lo * hi)
    return None


def unwrapped_phase(
    omega: float,
    rows: list[tuple[float, float, float, float]],
    phase_at,
) -> float:
    reference = rows[0][2]
    for row in rows:
        if row[0] <= omega:
            reference = row[2]
    return continuous_phase(phase_at(omega), reference)


def margins(num: list[float], den: list[float]) -> dict[str, object]:
    rows = response_grid(num, den)

    def phase_at(omega: float) -> float:
        re, im = eval_ratio(num, den, omega)
        return math.atan2(im, re)

    def mag_at(omega: float) -> float:
        re, im = eval_ratio(num, den, omega)
        return math.hypot(re, im)

    wc = first_crossing(rows, "gain", num, den)
    wpc = first_crossing(rows, "phase", num, den)
    result: dict[str, object] = {
        "dc_gain": dc_gain(num, den),
        "stable": stability(num, den),
        "curve": rows,
    }
    if wc is None:
        result["wc"] = "none"
        result["phase_margin_deg"] = "none"
    else:
        result["wc"] = wc
        result["phase_margin_deg"] = 180.0 + math.degrees(unwrapped_phase(wc, rows, phase_at))
    if wpc is None:
        result["wpc"] = "none"
        result["gain_margin_db"] = "inf"
    else:
        result["wpc"] = wpc
        result["gain_margin_db"] = -20.0 * math.log(mag_at(wpc)) / math.log(10.0)
    return result


def emit(result: dict[str, object], graph: Path, compensator: str) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("compensator", compensator)
    for key in ("wc", "phase_margin_deg", "wpc", "gain_margin_db", "stable", "dc_gain"):
        print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    rows = result["curve"]
    freq = [row[0] for row in rows]
    mag = [row[3] for row in rows]
    phase = [math.degrees(row[2]) for row in rows]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.2), sharex=True)
    axes[0].semilogx(freq, mag, color="C0")
    axes[1].semilogx(freq, phase, color="C1")
    if isinstance(result["wc"], float):
        axes[0].axvline(result["wc"], color="0.4", linestyle="--")
        axes[1].axvline(result["wc"], color="0.4", linestyle="--")
    if isinstance(result["wpc"], float):
        axes[0].axvline(result["wpc"], color="0.55", linestyle=":")
        axes[1].axvline(result["wpc"], color="0.55", linestyle=":")
    axes[0].axhline(0.0, color="0.5", linewidth=0.8)
    axes[1].axhline(-180.0, color="0.5", linewidth=0.8)
    axes[0].set_ylabel("Magnitude [dB]")
    axes[1].set_ylabel("Phase [deg]")
    axes[1].set_xlabel(r"Frequency $\omega$ [rad/s]")
    axes[0].set_title(PLOT_TITLE)
    axes[0].grid(True, which="both", alpha=0.3)
    axes[1].grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    re, im = 1.0, 1.0
    if not close(bode_magnitude_db(re, im), 20.0 * math.log(math.sqrt(2.0)) / math.log(10.0), 1e-12):
        return fail("bode magnitude of 1+j is not 20*log10(sqrt(2))")
    num, den, kind = loop_transfer([1.0], [1.0, 1.0, 0.0], None, None, None)
    if kind != "plant":
        return fail("the bare plant was marked as PID")
    result = margins(num, den)
    omega_c = math.sqrt((math.sqrt(5.0) - 1.0) / 2.0)
    if not isinstance(result["wc"], float) or not close(float(result["wc"]), omega_c, 1e-4):
        return fail("gain crossover of 1/(s(s+1)) is wrong")
    phase = math.atan2(-omega_c, -(omega_c**2))
    expected_pm = 180.0 + math.degrees(phase)
    if not close(float(result["phase_margin_deg"]), expected_pm, 1e-4):
        return fail("phase margin of 1/(s(s+1)) is wrong")
    if result["wpc"] != "none" or result["gain_margin_db"] != "inf":
        return fail("1/(s(s+1)) should have no finite gain margin")
    if result["stable"] != "yes":
        return fail("s^2+s+1 was not stable")
    if not math.isinf(float(result["dc_gain"])):
        return fail("integrator DC gain is finite")
    same, _, _ = loop_transfer([1.0], [1.0, 1.0, 0.0], 1.0, 0.0, 0.0)
    if same != [1.0]:
        return fail("unit proportional PID changed the numerator")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(result, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("wc", result["wc"])
    print_kv("phase_margin_deg", result["phase_margin_deg"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bode gain and phase margins of a loop transfer.")
    parser.add_argument("--num", type=float, nargs="+", default=None, help="numerator, highest power first")
    parser.add_argument("--den", type=float, nargs="+", default=None, help="denominator, highest power first")
    parser.add_argument("--kp", type=float, default=None, help="series proportional gain")
    parser.add_argument("--ki", type=float, default=None, help="series integral gain")
    parser.add_argument("--kd", type=float, default=None, help="series derivative gain")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.num is None or args.den is None:
        print("error: requires --num and --den", file=sys.stderr)
        return 2
    try:
        num, den, kind = loop_transfer(args.num, args.den, args.kp, args.ki, args.kd)
        result = margins(num, den)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "classical_control_margins.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path, kind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
