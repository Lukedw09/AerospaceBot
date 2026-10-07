#!/usr/bin/env python3
"""Single-axis reaction-wheel inertia from stored momentum and speed limit.

reaction_wheel_inertia is I_w = H/omega_max.
Optional margins use margin_of_safety on momentum and on torque.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Reaction wheel sizing"
N_CURVE = 201
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "one wheel on a principal axis; H = I*omega from NASA SP-8024; "
    "reaction_wheel_inertia I_w = H/omega_max at the wheel speed limit; "
    "tau is the peak torque demand and is not recomputed here; "
    "margin_of_safety MS = limit/demand - 1 when --H-max or --tau-max is set; "
    "no wheel pyramid, motor catalog, or desaturation"
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


def wheel_inertia(momentum: float, omega_max: float) -> float:
    """reaction_wheel_inertia."""
    return momentum / omega_max


def margin_of_safety(limit: float, demand: float) -> float:
    """margin_of_safety."""
    return limit / demand - 1.0


def evaluate(
    momentum: float,
    torque: float,
    omega_max: float,
    momentum_limit: float | None,
    torque_limit: float | None,
) -> dict[str, float]:
    require_positive("momentum", momentum)
    require_positive("torque", torque)
    require_positive("maximum wheel speed", omega_max)
    result: dict[str, float] = {
        "H_N_m_s": momentum,
        "tau_N_m": torque,
        "omega_max_rad_s": omega_max,
        "I_w_kg_m2": wheel_inertia(momentum, omega_max),
    }
    if momentum_limit is not None:
        require_positive("momentum limit", momentum_limit)
        result["H_max_N_m_s"] = momentum_limit
        result["margin_H"] = margin_of_safety(momentum_limit, momentum)
    if torque_limit is not None:
        require_positive("torque limit", torque_limit)
        result["tau_max_N_m"] = torque_limit
        result["margin_tau"] = margin_of_safety(torque_limit, torque)
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
        raise ValueError("matplotlib is required to plot wheel inertia") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    momentum = result["H_N_m_s"]
    omega = result["omega_max_rad_s"]
    speeds = linspace(0.4 * omega, 1.8 * omega, N_CURVE)
    inertias = [wheel_inertia(momentum, speed) for speed in speeds]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(speeds, inertias, color="#1a5276", linewidth=1.8, label=r"$I_w = H/\omega_{\max}$")
    ax.plot(omega, result["I_w_kg_m2"], "s", color="#1a5276", markersize=7, zorder=5, label="operating point")
    ax.set_xlabel("maximum wheel speed (rad/s)")
    ax.set_ylabel("wheel inertia (kg·m²)")
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


def emit(result: dict[str, float], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "H_N_m_s",
        "tau_N_m",
        "omega_max_rad_s",
        "I_w_kg_m2",
        "H_max_N_m_s",
        "margin_H",
        "tau_max_N_m",
        "margin_tau",
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
    if not close(wheel_inertia(0.54, 100.0), 0.0054):
        return fail("inertia")
    if not close(margin_of_safety(1.0, 0.5), 1.0):
        return fail("margin")
    result = evaluate(0.54, 0.01, 100.0, 1.0, 0.02)
    if not close(result["margin_H"], 1.0 / 0.54 - 1.0):
        return fail("momentum margin")
    if not close(result["margin_tau"], 1.0):
        return fail("torque margin")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "wheel.png"
        code, text, err = capture(
            ["--H", "0.54", "--tau", "0.01", "--omega-max", "100", "--H-max", "1", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "I_w_kg_m2: 0.0054" not in text or "margin_H:" not in text:
            return fail("stdout")
        if "margin_tau:" in text:
            return fail("torque margin without a torque limit")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(["--H", "1", "--tau", "1"])
        if code == 0:
            return fail("missing wheel speed was accepted")

    print("check: pass")
    print_kv("I_w_kg_m2", result["I_w_kg_m2"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-axis reaction-wheel inertia and margins.")
    parser.add_argument("--H", type=float, default=None, help="stored angular momentum [N*m*s]")
    parser.add_argument("--tau", type=float, default=None, help="peak torque demand [N*m]")
    parser.add_argument("--omega-max", type=float, default=None, help="maximum wheel speed [rad/s]")
    parser.add_argument("--H-max", type=float, default=None, help="wheel momentum limit [N*m*s]")
    parser.add_argument("--tau-max", type=float, default=None, help="wheel torque limit [N*m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.H is None or args.tau is None or args.omega_max is None:
        print("error: requires --H, --tau, and --omega-max", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.H, args.tau, args.omega_max, args.H_max, args.tau_max)
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
