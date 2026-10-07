#!/usr/bin/env python3
"""Dutch-roll frequency and damping from the two-degree lateral approximation.

The frequency keeps directional stiffness, side force, yaw damping, and the
dihedral spring g*L_beta/(V*L_p). Damping keeps yaw damping and side force.
NACA Report 589 states that the period depends on directional stability and
dihedral and that damping depends on the damping derivatives. The report's
average-airplane numbers and design charts are not used.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Dutch roll"
G0 = 9.80665
N_CURVE = 121
ASSUMPTIONS = (
    "two-degree lateral approximation of NACA Report 589 before its average-airplane substitution; "
    "dutch_roll_omega_sq = N_beta + Y_beta*N_r/V + g*L_beta/(V*L_p); "
    "dutch_roll_damping_product = -(N_r + Y_beta/V)/2; "
    "derivatives are dimensionless per radian; "
    "spiral and roll-subsidence roots are not computed; "
    "not the full lateral quartic; design charts are not used"
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


def dynamic_pressure(rho: float, speed: float) -> float:
    return 0.5 * rho * speed**2


def side_acceleration(rho: float, speed: float, area: float, cy_beta: float, mass: float) -> float:
    """dutch_roll_side_acceleration."""
    return dynamic_pressure(rho, speed) * area * cy_beta / mass


def directional_stiffness(
    rho: float, speed: float, area: float, span: float, cn_beta: float, iz: float
) -> float:
    """dutch_roll_directional_stiffness."""
    return dynamic_pressure(rho, speed) * area * span * cn_beta / iz


def yaw_damping(
    rho: float, speed: float, area: float, span: float, cn_r: float, iz: float
) -> float:
    """dutch_roll_yaw_damping."""
    return dynamic_pressure(rho, speed) * area * span**2 * cn_r / (2.0 * speed * iz)


def roll_stiffness(
    rho: float, speed: float, area: float, span: float, cl_beta: float, ix: float
) -> float:
    """dutch_roll_roll_stiffness."""
    return dynamic_pressure(rho, speed) * area * span * cl_beta / ix


def roll_damping(
    rho: float, speed: float, area: float, span: float, cl_p: float, ix: float
) -> float:
    """dutch_roll_roll_damping."""
    return dynamic_pressure(rho, speed) * area * span**2 * cl_p / (2.0 * speed * ix)


def omega_squared(n_beta: float, y_beta: float, n_r: float, speed: float, gravity: float, l_beta: float, l_p: float) -> float:
    """dutch_roll_omega_sq."""
    return n_beta + y_beta * n_r / speed + gravity * l_beta / (speed * l_p)


def damping_product(n_r: float, y_beta: float, speed: float) -> float:
    """dutch_roll_damping_product, equal to zeta*omega."""
    return -(n_r + y_beta / speed) / 2.0


def evaluate(
    speed: float,
    rho: float,
    span: float,
    area: float,
    ix: float,
    iz: float,
    mass: float,
    cn_beta: float,
    cl_beta: float,
    cy_beta: float,
    cn_r: float,
    cl_p: float,
    gravity: float = G0,
) -> dict[str, float]:
    require_positive("speed", speed)
    require_positive("density", rho)
    require_positive("span", span)
    require_positive("area", area)
    require_positive("roll inertia", ix)
    require_positive("yaw inertia", iz)
    require_positive("mass", mass)
    for name, value in (
        ("Cn_beta", cn_beta),
        ("Cl_beta", cl_beta),
        ("Cy_beta", cy_beta),
        ("Cn_r", cn_r),
        ("Cl_p", cl_p),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    require_positive("acceleration", gravity)
    y_beta = side_acceleration(rho, speed, area, cy_beta, mass)
    n_beta = directional_stiffness(rho, speed, area, span, cn_beta, iz)
    n_r = yaw_damping(rho, speed, area, span, cn_r, iz)
    l_beta = roll_stiffness(rho, speed, area, span, cl_beta, ix)
    l_p = roll_damping(rho, speed, area, span, cl_p, ix)
    if l_p == 0.0:
        raise ValueError("roll damping is zero; the dihedral spring is undefined")
    w2 = omega_squared(n_beta, y_beta, n_r, speed, gravity, l_beta, l_p)
    if not math.isfinite(w2) or w2 <= 0.0:
        raise ValueError("the approximation is not an oscillation at this speed")
    omega = math.sqrt(w2)
    zeta = damping_product(n_r, y_beta, speed) / omega
    return {
        "speed_m_s": speed,
        "rho_kg_m3": rho,
        "span_m": span,
        "area_m2": area,
        "Ix_kg_m2": ix,
        "Iz_kg_m2": iz,
        "mass_kg": mass,
        "omega_dr_rad_s": omega,
        "f_Hz": omega / (2.0 * math.pi),
        "period_s": 2.0 * math.pi / omega,
        "zeta_dr": zeta,
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
        raise ValueError("matplotlib is required to plot Dutch roll") from exc
    return plt


def write_plot(result: dict[str, float], derivatives: dict[str, float], out_path: Path) -> None:
    plt = ensure_matplotlib()
    speed = float(result["speed_m_s"])
    span = linspace(0.6 * speed, 1.6 * speed, N_CURVE)
    periods: list[float] = []
    zetas: list[float] = []
    speeds: list[float] = []
    for item in span:
        try:
            point = evaluate(
                item,
                result["rho_kg_m3"],
                result["span_m"],
                result["area_m2"],
                result["Ix_kg_m2"],
                result["Iz_kg_m2"],
                result["mass_kg"],
                derivatives["cn_beta"],
                derivatives["cl_beta"],
                derivatives["cy_beta"],
                derivatives["cn_r"],
                derivatives["cl_p"],
            )
        except ValueError:
            continue
        speeds.append(item)
        periods.append(float(point["period_s"]))
        zetas.append(float(point["zeta_dr"]))
    if not speeds:
        raise ValueError("the speed sweep is not oscillatory")
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(speeds, periods, color="#1a5276", linewidth=1.8, label="period")
    ax.plot(speed, float(result["period_s"]), "s", color="#1a5276", markersize=7)
    ax.set_xlabel("speed (m/s)")
    ax.set_ylabel("period (s)")
    ax.set_title(PLOT_TITLE)
    twin = ax.twinx()
    twin.plot(speeds, zetas, color="#b9770e", linewidth=1.6, label="damping ratio")
    twin.plot(speed, float(result["zeta_dr"]), "o", color="#b9770e", markersize=6)
    twin.set_ylabel("damping ratio")
    ax.grid(True, alpha=0.35)
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = twin.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="best", fontsize=8)
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
        "speed_m_s",
        "rho_kg_m3",
        "span_m",
        "area_m2",
        "Ix_kg_m2",
        "Iz_kg_m2",
        "mass_kg",
        "omega_dr_rad_s",
        "f_Hz",
        "period_s",
        "zeta_dr",
    ):
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


def sample_case() -> dict[str, float]:
    return evaluate(
        150.0,
        1.0,
        20.0,
        50.0,
        1.0e5,
        2.0e5,
        5000.0,
        0.1,
        -0.1,
        -0.5,
        -0.2,
        -0.4,
    )


def run_check() -> int:
    q = 0.5 * 1.0 * 150.0**2
    y_beta = q * 50.0 * (-0.5) / 5000.0
    n_beta = q * 50.0 * 20.0 * 0.1 / 2.0e5
    n_r = q * 50.0 * 400.0 * (-0.2) / (2.0 * 150.0 * 2.0e5)
    l_beta = q * 50.0 * 20.0 * (-0.1) / 1.0e5
    l_p = q * 50.0 * 400.0 * (-0.4) / (2.0 * 150.0 * 1.0e5)
    w2 = omega_squared(n_beta, y_beta, n_r, 150.0, G0, l_beta, l_p)
    result = sample_case()
    if not close(float(result["omega_dr_rad_s"]), math.sqrt(w2)):
        return fail("frequency")
    zeta = damping_product(n_r, y_beta, 150.0) / math.sqrt(w2)
    if not close(float(result["zeta_dr"]), zeta):
        return fail("damping")
    if not close(float(result["period_s"]), 2.0 * math.pi / math.sqrt(w2)):
        return fail("period")
    if w2 <= n_beta:
        return fail("dihedral did not raise the frequency")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "dutch.png"
        code, text, err = capture(
            [
                "--speed",
                "150",
                "--rho",
                "1",
                "--span",
                "20",
                "--area",
                "50",
                "--ix",
                "1e5",
                "--iz",
                "2e5",
                "--mass",
                "5000",
                "--cn-beta",
                "0.1",
                "--cl-beta",
                "-0.1",
                "--cy-beta",
                "-0.5",
                "--cn-r",
                "-0.2",
                "--cl-p",
                "-0.4",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "omega_dr_rad_s:" not in text or "zeta_dr:" not in text or "period_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(
            [
                "--speed",
                "150",
                "--rho",
                "1",
                "--span",
                "20",
                "--area",
                "50",
                "--ix",
                "1e5",
                "--iz",
                "2e5",
                "--mass",
                "5000",
                "--cn-beta",
                "0.1",
                "--cy-beta",
                "-0.5",
                "--cn-r",
                "-0.2",
                "--cl-p",
                "-0.4",
            ]
        )
        if code == 0:
            return fail("missing Cl_beta was accepted")

    print("check: pass")
    print_kv("omega_dr_rad_s", result["omega_dr_rad_s"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dutch-roll frequency and damping.")
    parser.add_argument("--speed", type=float, default=None, help="true airspeed [m/s]")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--span", type=float, default=None, help="wing span [m]")
    parser.add_argument("--area", type=float, default=None, help="wing area [m^2]")
    parser.add_argument("--ix", type=float, default=None, help="roll inertia [kg m^2]")
    parser.add_argument("--iz", type=float, default=None, help="yaw inertia [kg m^2]")
    parser.add_argument("--mass", type=float, default=None, help="airplane mass [kg]")
    parser.add_argument("--cn-beta", type=float, default=None, help="yaw stiffness per rad")
    parser.add_argument("--cl-beta", type=float, default=None, help="dihedral derivative per rad")
    parser.add_argument("--cy-beta", type=float, default=None, help="side-force derivative per rad")
    parser.add_argument("--cn-r", type=float, default=None, help="yaw damping per rad")
    parser.add_argument("--cl-p", type=float, default=None, help="roll damping per rad")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    required = {
        "--speed": args.speed,
        "--rho": args.rho,
        "--span": args.span,
        "--area": args.area,
        "--ix": args.ix,
        "--iz": args.iz,
        "--mass": args.mass,
        "--cn-beta": args.cn_beta,
        "--cl-beta": args.cl_beta,
        "--cy-beta": args.cy_beta,
        "--cn-r": args.cn_r,
        "--cl-p": args.cl_p,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        print("error: requires " + ", ".join(missing), file=sys.stderr)
        return 2
    try:
        result = evaluate(
            args.speed,
            args.rho,
            args.span,
            args.area,
            args.ix,
            args.iz,
            args.mass,
            args.cn_beta,
            args.cl_beta,
            args.cy_beta,
            args.cn_r,
            args.cl_p,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(
                result,
                {
                    "cn_beta": args.cn_beta,
                    "cl_beta": args.cl_beta,
                    "cy_beta": args.cy_beta,
                    "cn_r": args.cn_r,
                    "cl_p": args.cl_p,
                },
                Path(args.out).resolve(),
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
