#!/usr/bin/env python3
"""Planar Clohessy-Wiltshire state about a circular chief.

x is along-track, positive with the chief velocity.
z is radial, positive away from the planet.
clohessy_wiltshire_along_track and clohessy_wiltshire_radial propagate the state.
clohessy_wiltshire_hold_rate is the along-track rate of a closed relative ellipse.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Relative orbit"
G0 = 9.80665
R0_EARTH = 6.3742e6
N_CURVE = 241
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "circular chief; deputy close enough for the linear Hill model; "
    "x along-track positive with the chief velocity; "
    "z radial positive away from the planet; no out-of-plane motion; "
    "mean_motion n = sqrt(mu/a); "
    "clohessy_wiltshire_radial and clohessy_wiltshire_along_track; "
    "null impulse cancels the initial relative velocity; "
    "clohessy_wiltshire_hold_rate xdot = -2*n*z with zdot = 0 "
    "is a closed 2:1 ellipse about the chief; "
    "not an eccentric chief and not a finite burn"
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


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def mean_motion(mu: float, radius: float) -> float:
    """mean_motion."""
    return math.sqrt(mu / radius**3)


def radial(motion: float, time_s: float, z0: float, zd0: float, xd0: float) -> float:
    """clohessy_wiltshire_radial."""
    s = math.sin(motion * time_s)
    c = math.cos(motion * time_s)
    return (4.0 - 3.0 * c) * z0 + (s / motion) * zd0 + (2.0 / motion) * (1.0 - c) * xd0


def along_track(
    motion: float, time_s: float, z0: float, x0: float, zd0: float, xd0: float
) -> float:
    """clohessy_wiltshire_along_track."""
    s = math.sin(motion * time_s)
    c = math.cos(motion * time_s)
    return (
        6.0 * (s - motion * time_s) * z0
        + x0
        + (2.0 / motion) * (c - 1.0) * zd0
        + (4.0 * s - 3.0 * motion * time_s) / motion * xd0
    )


def hold_rate(motion: float, z0: float) -> float:
    """clohessy_wiltshire_hold_rate."""
    return -2.0 * motion * z0


def rates(motion: float, time_s: float, z0: float, zd0: float, xd0: float) -> tuple[float, float]:
    s = math.sin(motion * time_s)
    c = math.cos(motion * time_s)
    xd = 6.0 * motion * (c - 1.0) * z0 - 2.0 * s * zd0 + (4.0 * c - 3.0) * xd0
    zd = 3.0 * motion * s * z0 + c * zd0 + 2.0 * s * xd0
    return xd, zd


def state(
    motion: float, time_s: float, x0: float, z0: float, xd0: float, zd0: float
) -> tuple[float, float, float, float]:
    x = along_track(motion, time_s, z0, x0, zd0, xd0)
    z = radial(motion, time_s, z0, zd0, xd0)
    xd, zd = rates(motion, time_s, z0, zd0, xd0)
    return x, z, xd, zd


def evaluate(
    x0: float,
    z0: float,
    xd0: float,
    zd0: float,
    time_s: float,
    radius: float,
    mu: float,
) -> dict[str, float]:
    for name, value in (("x", x0), ("z", z0), ("xdot", xd0), ("zdot", zd0), ("time", time_s)):
        require_finite(name, value)
    if time_s < 0.0:
        raise ValueError("time must be >= 0")
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError("chief radius must be finite and > 0")
    if not math.isfinite(mu) or mu <= 0.0:
        raise ValueError("gravitational parameter must be finite and > 0")
    motion = mean_motion(mu, radius)
    x, z, xd, zd = state(motion, time_s, x0, z0, xd0, zd0)
    return {
        "a_m": radius,
        "mu_m3_s2": mu,
        "n_rad_s": motion,
        "t_s": time_s,
        "period_s": 2.0 * math.pi / motion,
        "x0_m": x0,
        "z0_m": z0,
        "xdot0_m_s": xd0,
        "zdot0_m_s": zd0,
        "x_m": x,
        "z_m": z,
        "xdot_m_s": xd,
        "zdot_m_s": zd,
        "dv_null_x_m_s": -xd0,
        "dv_null_z_m_s": -zd0,
        "dv_hold_x_m_s": hold_rate(motion, z0) - xd0,
        "dv_hold_z_m_s": -zd0,
    }


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the relative orbit") from exc
    return plt


def write_plot(result: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    motion = result["n_rad_s"]
    time_s = result["t_s"]
    span = time_s if time_s > 0.0 else result["period_s"]
    times = [span * i / (N_CURVE - 1) for i in range(N_CURVE)]
    path = [
        state(motion, t, result["x0_m"], result["z0_m"], result["xdot0_m_s"], result["zdot0_m_s"])
        for t in times
    ]
    fig, ax = plt.subplots(1, 1, figsize=(7.0, 6.0))
    ax.plot([p[0] for p in path], [p[1] for p in path], color="#1a5276", linewidth=1.6, label="deputy")
    ax.plot(result["x0_m"], result["z0_m"], "o", color="#117a65", markersize=6, label="start")
    ax.plot(result["x_m"], result["z_m"], "s", color="#1a5276", markersize=7, label="at time t")
    ax.plot(0.0, 0.0, "+", color="#c0392b", markersize=10, label="chief")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("along-track x (m)")
    ax.set_ylabel("radial z (m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
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


def chief_radius(args: argparse.Namespace) -> float:
    if args.a is not None and args.alt is not None:
        raise ValueError("pass --a or --alt, not both")
    if args.a is None and args.alt is None:
        raise ValueError("pass --a or --alt")
    if args.a is not None:
        if args.a <= 0.0:
            raise ValueError("--a must be > 0")
        return float(args.a)
    r0 = float(args.R0) if args.R0 is not None else R0_EARTH
    if r0 <= 0.0 or args.alt < 0.0:
        raise ValueError("altitude must be >= 0 and planet radius > 0")
    return r0 + float(args.alt)


def run_check() -> int:
    motion = 1.0
    # Identity at t = 0.
    x, z, xd, zd = state(motion, 0.0, 3.0, -2.0, 0.4, -0.5)
    if not (close(x, 3.0) and close(z, -2.0) and close(xd, 0.4) and close(zd, -0.5)):
        return fail("initial state")
    # Closed ellipse: z = z0 cos, x = -2 z0 sin, with x along the chief velocity.
    z0 = 10.0
    xd0 = hold_rate(motion, z0)
    if not close(xd0, -2.0 * motion * z0):
        return fail("hold rate")
    t = 0.7
    x, z, xd, zd = state(motion, t, 0.0, z0, xd0, 0.0)
    if not close(z, z0 * math.cos(motion * t)) or not close(x, -2.0 * z0 * math.sin(motion * t)):
        return fail("closed ellipse")
    # Finite-difference velocity.
    dt = 1e-6
    x2, z2, _xd2, _zd2 = state(motion, t + dt, 0.0, z0, xd0, 0.0)
    if not close((x2 - x) / dt, xd, tol=1e-4) or not close((z2 - z) / dt, zd, tol=1e-4):
        return fail("rate derivative")
    # Hill residuals, +x with the velocity and +z outward:
    # xdd + 2 n zd = 0, zdd - 2 n xd - 3 n^2 z = 0.
    _x3, _z3, xd3, zd3 = state(motion, t + dt, 0.0, z0, xd0, 0.0)
    xdd = (xd3 - xd) / dt
    zdd = (zd3 - zd) / dt
    if abs(xdd + 2.0 * motion * zd) > 1e-3:
        return fail("along-track ODE")
    if abs(zdd - 2.0 * motion * xd - 3.0 * motion**2 * z) > 1e-3:
        return fail("radial ODE")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "cw.png"
        code, text, err = capture(
            ["--x", "0", "--z", "10", "--xdot", "-0.02", "--zdot", "0", "--time", "100", "--a", "7000000", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "dv_hold_x_m_s:" not in text or "n_rad_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("x_m", x)
    print_kv("z_m", z)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Planar Clohessy-Wiltshire relative state.")
    parser.add_argument("--x", type=float, default=None, help="along-track position [m]")
    parser.add_argument("--z", type=float, default=None, help="radial position, outward [m]")
    parser.add_argument("--xdot", type=float, default=None, help="along-track rate [m/s]")
    parser.add_argument("--zdot", type=float, default=None, help="radial rate [m/s]")
    parser.add_argument("--time", type=float, default=None, help="propagation time [s]")
    parser.add_argument("--a", type=float, default=None, help="chief circular radius [m]")
    parser.add_argument("--alt", type=float, default=None, help="chief altitude [m]")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter [m^3/s^2]")
    parser.add_argument("--R0", type=float, default=None, help="planet radius for --alt [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if None in (args.x, args.z, args.xdot, args.zdot, args.time):
        print("error: requires --x, --z, --xdot, --zdot, --time, and --a or --alt", file=sys.stderr)
        return 2
    mu = float(args.mu) if args.mu is not None else G0 * R0_EARTH**2
    try:
        result = evaluate(args.x, args.z, args.xdot, args.zdot, args.time, chief_radius(args), mu)
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
