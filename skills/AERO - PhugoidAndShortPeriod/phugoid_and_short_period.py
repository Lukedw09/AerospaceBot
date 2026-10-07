#!/usr/bin/env python3
"""Classical phugoid period and static short-period approximation.

phugoid_natural_frequency is (g/V)*sqrt(2).
short_period_natural_frequency uses static pitch stiffness only.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Phugoid and short period"
G0 = 9.80665
N_CURVE = 161
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "level-flight phugoid with angle of attack held at the trim value: "
    "phugoid_natural_frequency omega_ph = (g/V)*sqrt(2) with g = 9.80665 m/s^2; "
    "phugoid_period = 2*pi/omega_ph; "
    "short_period_natural_frequency from static pitch stiffness only, "
    "omega_sp = (V/ky)*sqrt(rho*g*c*cla*kn/(2*(W/S))); "
    "kn is the static-margin fraction of the mean chord, positive stable; "
    "pitch-rate and alpha-dot derivatives are omitted; "
    "not a fourth-order longitudinal eigenvalue"
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


def phugoid_frequency(speed: float, gravity: float = G0) -> float:
    """phugoid_natural_frequency."""
    return gravity * math.sqrt(2.0) / speed


def phugoid_period(speed: float, gravity: float = G0) -> float:
    """phugoid_period."""
    return 2.0 * math.pi * speed / (gravity * math.sqrt(2.0))


def short_period_frequency(
    speed: float,
    rho: float,
    wing_loading: float,
    cla: float,
    static_margin: float,
    chord: float,
    ky: float,
    gravity: float = G0,
) -> float:
    """short_period_natural_frequency."""
    return (speed / ky) * math.sqrt(
        rho * gravity * chord * cla * static_margin / (2.0 * wing_loading)
    )


def short_period_period(frequency: float) -> float:
    """short_period_period."""
    return 2.0 * math.pi / frequency


def evaluate(
    speed: float,
    rho: float,
    wing_loading: float,
    cla: float,
    static_margin: float,
    chord: float,
    ky: float,
) -> dict[str, float]:
    require_positive("speed", speed)
    require_positive("density", rho)
    require_positive("wing loading", wing_loading)
    require_positive("lift-curve slope", cla)
    require_positive("static margin", static_margin)
    require_positive("mean chord", chord)
    require_positive("pitch radius of gyration", ky)
    omega_ph = phugoid_frequency(speed)
    omega_sp = short_period_frequency(speed, rho, wing_loading, cla, static_margin, chord, ky)
    return {
        "V_m_s": speed,
        "rho_kg_m3": rho,
        "wing_loading_N_m2": wing_loading,
        "cla_per_rad": cla,
        "kn": static_margin,
        "c_m": chord,
        "ky_m": ky,
        "g_m_s2": G0,
        "omega_ph_rad_s": omega_ph,
        "T_ph_s": phugoid_period(speed),
        "omega_sp_rad_s": omega_sp,
        "T_sp_s": short_period_period(omega_sp),
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
        raise ValueError("matplotlib is required to plot the periods") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    speed = result["V_m_s"]
    speeds = linspace(0.5 * speed, 1.5 * speed, N_CURVE)
    phugoids = [phugoid_period(item) for item in speeds]
    shorts = [
        short_period_period(
            short_period_frequency(
                item,
                result["rho_kg_m3"],
                result["wing_loading_N_m2"],
                result["cla_per_rad"],
                result["kn"],
                result["c_m"],
                result["ky_m"],
            )
        )
        for item in speeds
    ]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(speeds, phugoids, color="#1a5276", linewidth=1.8, label="phugoid")
    ax.plot(speeds, shorts, color="#922b21", linewidth=1.6, label="short period")
    ax.plot(speed, result["T_ph_s"], "s", color="#1a5276", markersize=7, label="phugoid point")
    ax.plot(speed, result["T_sp_s"], "s", color="#922b21", markersize=7, label="short-period point")
    ax.set_xlabel("true airspeed (m/s)")
    ax.set_ylabel("period (s)")
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
    for key, value in result.items():
        print_kv(key, value)
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
    speed = 100.0
    omega = phugoid_frequency(speed)
    if not close(omega, G0 * math.sqrt(2.0) / speed):
        return fail("phugoid frequency")
    if not close(phugoid_period(speed), 2.0 * math.pi / omega):
        return fail("phugoid period")
    # Unit-like short period: rho=2, g cancels with numbers chosen so the radicand is 1.
    # (V/ky)*sqrt(rho*g*c*cla*kn/(2*w)) = 50/1 * sqrt(2*9.80665*1*1*1/(2*9.80665)) = 50
    omega_sp = short_period_frequency(50.0, 2.0, 9.80665, 1.0, 1.0, 1.0, 1.0)
    if not close(omega_sp, 50.0):
        return fail(f"short-period frequency {omega_sp}")
    if not close(short_period_period(omega_sp), 2.0 * math.pi / 50.0):
        return fail("short-period period")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "modes.png"
        code, text, err = capture(
            [
                "--speed",
                "100",
                "--rho",
                "1.2",
                "--wing-loading",
                "3000",
                "--cla",
                "5",
                "--static-margin",
                "0.05",
                "--mac",
                "2",
                "--ky",
                "1",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "T_ph_s:" not in text or "T_sp_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(
            ["--speed", "100", "--rho", "1", "--wing-loading", "1000", "--cla", "5", "--static-margin", "0", "--mac", "1", "--ky", "1"]
        )
        if code == 0:
            return fail("zero static margin was accepted")

    print("check: pass")
    print_kv("omega_sp_rad_s", omega_sp)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phugoid and short-period period approximations.")
    parser.add_argument("--speed", type=float, default=None, help="true airspeed [m/s]")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--wing-loading", type=float, default=None, help="W/S [N/m^2]")
    parser.add_argument("--cla", type=float, default=None, help="lift-curve slope [1/rad]")
    parser.add_argument("--static-margin", type=float, default=None, help="static margin x/c")
    parser.add_argument("--mac", type=float, default=None, help="mean aerodynamic chord [m]")
    parser.add_argument("--ky", type=float, default=None, help="pitch radius of gyration [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if None in (args.speed, args.rho, args.wing_loading, args.cla, args.static_margin, args.mac, args.ky):
        print(
            "error: requires --speed, --rho, --wing-loading, --cla, "
            "--static-margin, --mac, and --ky",
            file=sys.stderr,
        )
        return 2
    try:
        result = evaluate(
            args.speed,
            args.rho,
            args.wing_loading,
            args.cla,
            args.static_margin,
            args.mac,
            args.ky,
        )
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
