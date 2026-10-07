#!/usr/bin/env python3
"""Coplanar phasing ellipse in one circular orbit.

phasing_wait_catch and phasing_wait_loiter set the wait from mean motion.
phasing_semimajor_from_period is Kepler's law solved for a.
phasing_delta_v is the vis-viva speed change at the shared radius.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Rendezvous phasing"
G0 = 9.80665
R0_EARTH = 6.3742e6
N_CURVE = 361
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "coplanar vehicles already in the same circular orbit; impulsive burns; "
    "inverse-square gravity and no drag; "
    "phasing_wait_catch t = (2*pi*N - phase)/n when the target is ahead; "
    "phasing_wait_loiter t = (2*pi*N + phase)/n when the chaser is ahead; "
    "phasing_semimajor_from_period a = (mu*(T/(2*pi))**2)**(1/3) "
    "with T = t/N; "
    "phasing_delta_v is the absolute vis-viva difference at the shared radius; "
    "the departure and return burns are equal; "
    "different circular radii are a Hohmann transfer, not this ellipse"
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


def mean_motion(mu: float, radius: float) -> float:
    """mean_motion."""
    return math.sqrt(mu / radius**3)


def circular_speed(mu: float, radius: float) -> float:
    return math.sqrt(mu / radius)


def vis_viva(mu: float, radius: float, semimajor: float) -> float:
    """vis_viva."""
    return math.sqrt(mu * (2.0 / radius - 1.0 / semimajor))


def wait_catch(revs: int, phase: float, motion: float) -> float:
    """phasing_wait_catch."""
    return (2.0 * math.pi * revs - phase) / motion


def wait_loiter(revs: int, phase: float, motion: float) -> float:
    """phasing_wait_loiter."""
    return (2.0 * math.pi * revs + phase) / motion


def semimajor_from_period(mu: float, period: float) -> float:
    """phasing_semimajor_from_period."""
    return (mu * (period / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0)


def delta_v(circular: float, ellipse_speed: float) -> float:
    """phasing_delta_v."""
    return abs(circular - ellipse_speed)


def evaluate(
    radius: float,
    phase: float,
    lead: str,
    revs: int,
    mu: float,
) -> dict[str, float | str]:
    require_positive("orbit radius", radius)
    require_positive("phase angle", phase)
    require_positive("gravitational parameter", mu)
    if revs < 1:
        raise ValueError("--revs must be an integer >= 1")
    who = lead.strip().lower()
    if who not in {"target", "chaser"}:
        raise ValueError("--lead must be target or chaser")
    if phase >= 2.0 * math.pi * revs:
        raise ValueError("phase angle must be smaller than 2*pi*revs")
    motion = mean_motion(mu, radius)
    if who == "target":
        wait = wait_catch(revs, phase, motion)
    else:
        wait = wait_loiter(revs, phase, motion)
    period = wait / revs
    semimajor = semimajor_from_period(mu, period)
    # Burn point is apoapsis of a lower ellipse, periapsis of a higher ellipse.
    other = 2.0 * semimajor - radius
    if other <= 0.0:
        raise ValueError("phasing periapsis is not positive; increase --revs or reduce --phase")
    if semimajor < radius:
        periapsis, apoapsis = other, radius
    else:
        periapsis, apoapsis = radius, other
    v_c = circular_speed(mu, radius)
    v_e = vis_viva(mu, radius, semimajor)
    one = delta_v(v_c, v_e)
    return {
        "lead": who,
        "phase_rad": phase,
        "revs": float(revs),
        "mu_m3_s2": mu,
        "r_m": radius,
        "n_rad_s": motion,
        "a_m": semimajor,
        "period_s": period,
        "wait_s": wait,
        "rp_m": periapsis,
        "ra_m": apoapsis,
        "vc_m_s": v_c,
        "ve_m_s": v_e,
        "dv_in_m_s": one,
        "dv_out_m_s": one,
        "dv_total_m_s": 2.0 * one,
    }


def ellipse_radius(semimajor: float, eccentricity: float, true_anomaly: float) -> float:
    return semimajor * (1.0 - eccentricity**2) / (1.0 + eccentricity * math.cos(true_anomaly))


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot phasing") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    radius = float(result["r_m"])
    semimajor = float(result["a_m"])
    periapsis = float(result["rp_m"])
    apoapsis = float(result["ra_m"])
    eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)
    # True anomaly is measured from periapsis. The burn is at the shared radius.
    angles = [2.0 * math.pi * i / (N_CURVE - 1) for i in range(N_CURVE)]
    circle = [(radius * math.cos(a), radius * math.sin(a)) for a in angles]
    ell = []
    for anomaly in angles:
        radial = ellipse_radius(semimajor, eccentricity, anomaly)
        ell.append((radial * math.cos(anomaly), radial * math.sin(anomaly)))
    phase = float(result["phase_rad"])
    sign = 1.0 if result["lead"] == "target" else -1.0
    target = (radius * math.cos(sign * phase), radius * math.sin(sign * phase))

    fig, ax = plt.subplots(1, 1, figsize=(6.5, 6.5))
    ax.plot([p[0] / 1000.0 for p in circle], [p[1] / 1000.0 for p in circle], color="#1a5276", linewidth=1.4, label="shared circle")
    ax.plot([p[0] / 1000.0 for p in ell], [p[1] / 1000.0 for p in ell], color="#c0392b", linewidth=1.4, label="phasing ellipse")
    ax.plot(0.0, 0.0, "o", color="#2c3e50", markersize=5, label="planet")
    ax.plot(radius / 1000.0, 0.0, "s", color="#1a5276", markersize=7, label="chaser at burn")
    ax.plot(target[0] / 1000.0, target[1] / 1000.0, "o", color="#117a65", markersize=6, label="target")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
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


def emit(result: dict[str, float | str], graph: Path | None, planet_radius: float) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "lead",
        "phase_rad",
        "revs",
        "mu_m3_s2",
        "r_m",
        "n_rad_s",
        "a_m",
        "period_s",
        "wait_s",
        "rp_m",
        "ra_m",
        "vc_m_s",
        "ve_m_s",
        "dv_in_m_s",
        "dv_out_m_s",
        "dv_total_m_s",
    ):
        print_kv(key, result[key])
    if float(result["rp_m"]) < planet_radius:
        print_kv("warning", "phasing periapsis is inside the planet radius")
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


def resolve_radius(args: argparse.Namespace) -> float:
    named = [args.radius, args.alt, args.r_target, args.r_chaser, args.alt_target, args.alt_chaser]
    if all(value is None for value in named):
        raise ValueError("pass a shared --radius or --alt, or both vehicle radii")
    if (args.radius is not None or args.alt is not None) and any(
        value is not None for value in (args.r_target, args.r_chaser, args.alt_target, args.alt_chaser)
    ):
        raise ValueError("pass a shared orbit or the two vehicle orbits, not both")
    r0 = float(args.R0) if args.R0 is not None else R0_EARTH
    require_positive("planet radius", r0)

    def one(radius: float | None, altitude: float | None, label: str) -> float | None:
        if radius is not None and altitude is not None:
            raise ValueError(f"pass radius or altitude for {label}, not both")
        if radius is not None:
            require_positive(label, radius)
            return float(radius)
        if altitude is not None:
            if not math.isfinite(altitude) or altitude < 0.0:
                raise ValueError(f"{label} altitude must be >= 0")
            return r0 + float(altitude)
        return None

    if args.radius is not None or args.alt is not None:
        shared = one(args.radius, args.alt, "shared orbit")
        assert shared is not None
        return shared
    target = one(args.r_target, args.alt_target, "target")
    chaser = one(args.r_chaser, args.alt_chaser, "chaser")
    if target is None and chaser is None:
        raise ValueError("pass both vehicle radii, or one shared radius")
    if target is None:
        assert chaser is not None
        return chaser
    if chaser is None:
        return target
    if not close(target, chaser, tol=1e-9):
        raise ValueError(
            "target and chaser radii differ; this phasing ellipse stays in one circular orbit"
        )
    return target


def run_check() -> int:
    mu = 1.0
    radius = 1.0
    motion = mean_motion(mu, radius)
    phase = math.pi / 2.0
    if not close(wait_catch(1, phase, motion), (2.0 * math.pi - phase) / motion):
        return fail("catch wait")
    if not close(wait_loiter(1, phase, motion), (2.0 * math.pi + phase) / motion):
        return fail("loiter wait")
    caught = evaluate(radius, phase, "target", 1, mu)
    if float(caught["a_m"]) >= radius:
        return fail("catching up should lower the orbit")
    loiter = evaluate(radius, phase, "chaser", 1, mu)
    if float(loiter["a_m"]) <= radius:
        return fail("loitering should raise the orbit")
    if not close(float(caught["dv_in_m_s"]), float(caught["dv_out_m_s"])):
        return fail("burns differ")
    # Period of the phasing ellipse matches the wait for one revolution.
    period = float(caught["period_s"])
    if not close(semimajor_from_period(mu, period), float(caught["a_m"])):
        return fail("semimajor")
    # Zero phase is not useful; a tiny phase still returns near the circle.
    small = evaluate(radius, 1e-6, "target", 1, mu)
    if abs(float(small["dv_total_m_s"])) > 1e-3:
        return fail("tiny phase should be a small burn")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "phase.png"
        code, text, err = capture(
            ["--radius", "7000000", "--phase", str(math.pi / 6.0), "--lead", "target", "--revs", "1", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "dv_total_m_s:" not in text or "a_m:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, err = capture(
            ["--r-target", "7000000", "--r-chaser", "8000000", "--phase", "0.1", "--lead", "target"]
        )
        if code == 0:
            return fail("unequal radii were accepted")

    print("check: pass")
    print_kv("a_m", caught["a_m"])
    print_kv("dv_total_m_s", caught["dv_total_m_s"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coplanar circular phasing ellipse for rendezvous.")
    parser.add_argument("--radius", type=float, default=None, help="shared circular radius [m]")
    parser.add_argument("--alt", type=float, default=None, help="shared altitude [m]")
    parser.add_argument("--r-target", type=float, default=None, help="target circular radius [m]")
    parser.add_argument("--r-chaser", type=float, default=None, help="chaser circular radius [m]")
    parser.add_argument("--alt-target", type=float, default=None, help="target altitude [m]")
    parser.add_argument("--alt-chaser", type=float, default=None, help="chaser altitude [m]")
    parser.add_argument("--phase", type=float, default=None, help="phase angle to close [rad]")
    parser.add_argument("--lead", type=str, default=None, help="who is ahead: target or chaser")
    parser.add_argument("--revs", type=int, default=1, help="chaser revolutions on the phasing ellipse")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter [m^3/s^2]")
    parser.add_argument("--R0", type=float, default=None, help="planet radius for altitude [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.phase is None or args.lead is None:
        print("error: requires a shared orbit, --phase, and --lead", file=sys.stderr)
        return 2
    mu = float(args.mu) if args.mu is not None else G0 * R0_EARTH**2
    try:
        result = evaluate(resolve_radius(args), args.phase, args.lead, args.revs, mu)
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
    planet_radius = float(args.R0) if args.R0 is not None else R0_EARTH
    emit(result, graph, planet_radius)
    return 0


if __name__ == "__main__":
    sys.exit(main())
