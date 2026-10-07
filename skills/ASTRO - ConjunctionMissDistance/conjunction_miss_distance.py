#!/usr/bin/env python3
"""Geometric closest approach of two Keplerian trajectories over a time window.

Both paths use the two-body model in ASTRO - OrbitalParameters.
The search minimizes r·r, then reports range, time, and relative speed.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-6
PLOT_TITLE = "Conjunction miss distance"
G0 = 9.80665
R0_EARTH = 6.3742e6
N_SEARCH = 721
N_CURVE = 401
ASSUMPTIONS = (
    "two Keplerian trajectories about the same planet; "
    "spherical gravity, no drag, no J2, same model as ASTRO - OrbitalParameters; "
    "the window is searched forward from the shared epoch; "
    "the minimum of r·r is refined locally; "
    "geometric miss distance only, not a probability, a covariance, or a screening threshold"
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


def load_orbital():
    folder = Path(__file__).resolve().parents[1] / "ASTRO - OrbitalParameters"
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    import orbital_parameters as orbital

    return orbital


def hyperbolic_from_true(eccentricity: float, nu: float) -> float:
    factor = math.sqrt((eccentricity + 1.0) / (eccentricity - 1.0))
    half = math.tan(nu / 2.0) / factor
    if abs(half) >= 1.0:
        raise ValueError("true anomaly is at or beyond the hyperbola asymptote")
    return 2.0 * math.atanh(half)


def solve_hyperbolic(mean: float, eccentricity: float) -> float:
    if eccentricity <= 1.0:
        raise ValueError("hyperbolic eccentricity must be > 1")
    anomaly = math.asinh(mean / eccentricity) if eccentricity != 0.0 else mean
    for _ in range(60):
        residual = eccentricity * math.sinh(anomaly) - anomaly - mean
        slope = eccentricity * math.cosh(anomaly) - 1.0
        if abs(residual) <= 1e-12:
            return anomaly
        if slope == 0.0:
            raise ValueError("hyperbolic Kepler equation did not converge")
        anomaly -= residual / slope
    raise ValueError("hyperbolic Kepler equation did not converge")


def nu_from_hyperbolic(eccentricity: float, anomaly: float) -> float:
    return 2.0 * math.atan(math.sqrt((eccentricity + 1.0) / (eccentricity - 1.0)) * math.tanh(anomaly / 2.0))


def state_at(orbital, mu: float, orbit, dt: float) -> tuple[float, float, float, float, float, float]:
    if orbit.conic == "parabola" or orbit.a is None:
        raise ValueError("a parabolic path has no finite semi-major axis for this search")
    if orbit.conic == "ellipse":
        if orbit.M is None:
            raise ValueError("ellipse mean anomaly is missing")
        mean = orbit.M + orbital.mean_motion(mu, orbit.a) * dt
        eccentric = orbital.solve_kepler(mean, orbit.e)
        nu = orbital.nu_from_eccentric(orbit.e, eccentric)
    elif orbit.conic == "hyperbola":
        anomaly0 = hyperbolic_from_true(orbit.e, orbit.nu)
        mean0 = orbit.e * math.sinh(anomaly0) - anomaly0
        mean = mean0 + math.sqrt(mu / abs(orbit.a) ** 3) * dt
        anomaly = solve_hyperbolic(mean, orbit.e)
        nu = nu_from_hyperbolic(orbit.e, anomaly)
    else:
        raise ValueError(f"unsupported conic {orbit.conic}")
    return orbital.state_from_elements(mu, orbit.a, orbit.e, orbit.i, orbit.Omega, orbit.omega, nu)


def separation(orbital, mu: float, first, second, dt: float) -> tuple[float, float]:
    r1x, r1y, r1z, v1x, v1y, v1z = state_at(orbital, mu, first, dt)
    r2x, r2y, r2z, v2x, v2y, v2z = state_at(orbital, mu, second, dt)
    dx, dy, dz = r1x - r2x, r1y - r2y, r1z - r2z
    dvx, dvy, dvz = v1x - v2x, v1y - v2y, v1z - v2z
    return dx * dx + dy * dy + dz * dz, math.sqrt(dvx * dvx + dvy * dvy + dvz * dvz)


def refine(orbital, mu: float, first, second, left: float, right: float) -> tuple[float, float, float]:
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    lo, hi = left, right
    c = hi - golden * (hi - lo)
    d = lo + golden * (hi - lo)
    fc, _ = separation(orbital, mu, first, second, c)
    fd, _ = separation(orbital, mu, first, second, d)
    for _ in range(80):
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - golden * (hi - lo)
            fc, _ = separation(orbital, mu, first, second, c)
        else:
            lo, c, fc = c, d, fd
            d = lo + golden * (hi - lo)
            fd, _ = separation(orbital, mu, first, second, d)
    time = 0.5 * (lo + hi)
    rr, speed = separation(orbital, mu, first, second, time)
    return time, math.sqrt(rr), speed


def evaluate(mu: float, state1: tuple[float, ...], state2: tuple[float, ...], window: float) -> dict[str, float | str]:
    if not math.isfinite(mu) or mu <= 0.0:
        raise ValueError("gravitational parameter must be finite and > 0")
    if not math.isfinite(window) or window <= 0.0:
        raise ValueError("window must be finite and > 0")
    orbital = load_orbital()
    first = orbital.orbit_from_state(mu, *state1, "conjunction-1")
    second = orbital.orbit_from_state(mu, *state2, "conjunction-2")
    count = N_SEARCH
    best_i = 0
    best = None
    for index in range(count):
        time = window * index / (count - 1)
        rr, _speed = separation(orbital, mu, first, second, time)
        if best is None or rr < best:
            best = rr
            best_i = index
    if best_i == 0 or best_i == count - 1:
        time = 0.0 if best_i == 0 else window
        rr, speed = separation(orbital, mu, first, second, time)
        endpoint = "yes"
    else:
        left = window * (best_i - 1) / (count - 1)
        right = window * (best_i + 1) / (count - 1)
        time, miss, speed = refine(orbital, mu, first, second, left, right)
        rr = miss * miss
        endpoint = "no"
        if time <= window * 1e-6 or window - time <= window * 1e-6:
            endpoint = "yes"
    return {
        "mu_m3_s2": mu,
        "window_s": window,
        "miss_m": math.sqrt(rr),
        "tca_s": time,
        "v_rel_m_s": speed,
        "endpoint_minimum": endpoint,
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
        raise ValueError("matplotlib is required to plot range") from exc
    return plt


def write_plot(
    mu: float,
    state1: tuple[float, ...],
    state2: tuple[float, ...],
    result: dict[str, float | str],
    out_path: Path,
) -> None:
    plt = ensure_matplotlib()
    orbital = load_orbital()
    first = orbital.orbit_from_state(mu, *state1, "conjunction-1")
    second = orbital.orbit_from_state(mu, *state2, "conjunction-2")
    window = float(result["window_s"])
    span = linspace(0.0, window, N_CURVE)
    ranges = [math.sqrt(separation(orbital, mu, first, second, item)[0]) / 1000.0 for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, ranges, color="#1a5276", linewidth=1.8, label="range")
    ax.plot(float(result["tca_s"]), float(result["miss_m"]) / 1000.0, "s", color="#1a5276", markersize=7, label="closest approach")
    ax.set_xlabel("time after epoch (s)")
    ax.set_ylabel("range (km)")
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
    for key in ("mu_m3_s2", "window_s", "miss_m", "tca_s", "v_rel_m_s", "endpoint_minimum"):
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


def circular_pair(offset_m: float) -> tuple[float, list[str]]:
    mu = G0 * R0_EARTH**2
    radius = R0_EARTH + 400000.0
    speed = math.sqrt(mu / radius)
    outer = radius + offset_m
    speed_outer = math.sqrt(mu / outer)
    flags = [
        "--r1x",
        str(radius),
        "--r1y",
        "0",
        "--r1z",
        "0",
        "--v1x",
        "0",
        "--v1y",
        str(speed),
        "--v1z",
        "0",
        "--r2x",
        str(outer),
        "--r2y",
        "0",
        "--r2z",
        "0",
        "--v2x",
        "0",
        "--v2y",
        str(speed_outer),
        "--v2z",
        "0",
        "--window",
        "200",
    ]
    return mu, flags


def run_check() -> int:
    _mu, flags = circular_pair(1000.0)
    state1 = (float(flags[1]), 0.0, 0.0, 0.0, float(flags[9]), 0.0)
    state2 = (float(flags[13]), 0.0, 0.0, 0.0, float(flags[21]), 0.0)
    result = evaluate(G0 * R0_EARTH**2, state1, state2, 200.0)
    if not close(float(result["miss_m"]), 1000.0, tol=1e-4):
        return fail(f"aligned miss {result['miss_m']}")
    if float(result["tca_s"]) > 1.0 or result["endpoint_minimum"] != "yes":
        return fail("aligned approach should sit on the epoch")
    orbital = load_orbital()
    mu = G0 * R0_EARTH**2
    first = orbital.orbit_from_state(mu, *state1, "check")
    epoch = state_at(orbital, mu, first, 0.0)
    if math.dist(epoch[:3], state1[:3]) > 1e-4:
        return fail("epoch state")
    period = 2.0 * math.pi * math.sqrt((R0_EARTH + 400000.0) ** 3 / mu)
    returned = state_at(orbital, mu, first, period)
    if math.dist(returned[:3], state1[:3]) > 1e-3:
        return fail("period closure")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "miss.png"
        code, text, err = capture([*flags, "--out", str(png)])
        if code != 0:
            return fail(f"run failed: {err}")
        if "miss_m:" not in text or "tca_s:" not in text or "endpoint_minimum: yes" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")

    print("check: pass")
    print_kv("miss_m", result["miss_m"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Geometric miss distance of two Keplerian states.")
    parser.add_argument("--r1x", type=float, default=None, help="object 1 position x [m]")
    parser.add_argument("--r1y", type=float, default=None, help="object 1 position y [m]")
    parser.add_argument("--r1z", type=float, default=None, help="object 1 position z [m]")
    parser.add_argument("--v1x", type=float, default=None, help="object 1 velocity x [m/s]")
    parser.add_argument("--v1y", type=float, default=None, help="object 1 velocity y [m/s]")
    parser.add_argument("--v1z", type=float, default=None, help="object 1 velocity z [m/s]")
    parser.add_argument("--r2x", type=float, default=None, help="object 2 position x [m]")
    parser.add_argument("--r2y", type=float, default=None, help="object 2 position y [m]")
    parser.add_argument("--r2z", type=float, default=None, help="object 2 position z [m]")
    parser.add_argument("--v2x", type=float, default=None, help="object 2 velocity x [m/s]")
    parser.add_argument("--v2y", type=float, default=None, help="object 2 velocity y [m/s]")
    parser.add_argument("--v2z", type=float, default=None, help="object 2 velocity z [m/s]")
    parser.add_argument("--window", type=float, default=None, help="search window forward from the epoch [s]")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter [m^3/s^2]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    names = [f"r{label}{axis}" for label in ("1", "2") for axis in ("x", "y", "z")]
    names += [f"v{label}{axis}" for label in ("1", "2") for axis in ("x", "y", "z")]
    missing = [f"--{name}" for name in names if getattr(args, name) is None]
    if args.window is None:
        missing.append("--window")
    if missing:
        print("error: requires " + ", ".join(missing), file=sys.stderr)
        return 2
    mu = G0 * R0_EARTH**2 if args.mu is None else args.mu
    state1 = (args.r1x, args.r1y, args.r1z, args.v1x, args.v1y, args.v1z)
    state2 = (args.r2x, args.r2y, args.r2z, args.v2x, args.v2y, args.v2z)
    try:
        for name, value in zip(names, (*state1, *state2), strict=True):
            require_finite(name, value)
        result = evaluate(mu, state1, state2, args.window)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(mu, state1, state2, result, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
