#!/usr/bin/env python3
"""Ideal actuator-disk propeller thrust, induced velocity, and efficiency.

Disk area is propeller_disk_area. Disk speed is actuator_disk_speed.
Induced velocity is propeller_induced_velocity. Far-wake speed is
propeller_far_wake_speed. Thrust is ideal_propeller_thrust, equal to
ideal_propeller_thrust_bernoulli and ideal_propeller_thrust_from_induced.
Shaft power is ideal_actuator_power. Efficiency is
ideal_propulsive_efficiency.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Ideal propeller"
PLOT_END_FACTOR = 1.5
N_PLOT = 201
NEWTON_ITERS = 80

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "incompressible Rankine-Froude actuator disk; uniformly loaded; "
    "no swirl, tip loss, or blade profile drag; "
    "A = pi*D**2/4 from propeller_disk_area; "
    "Vp = 0.5*(Ve + V0) from actuator_disk_speed; "
    "vi = Vp - V0 from propeller_induced_velocity; "
    "Ve = V0 + 2*vi from propeller_far_wake_speed; "
    "ideal thrust T = rho*Vp*A*(Ve - V0) from ideal_propeller_thrust, "
    "equal to ideal_propeller_thrust_bernoulli and "
    "ideal_propeller_thrust_from_induced T = 2*rho*A*vi*(V0 + vi); "
    "ideal shaft power P = T*Vp from ideal_actuator_power, equal to "
    "ideal_actuator_power_from_induced; "
    "eta = T*V0/P = V0/Vp from ideal_propulsive_efficiency; "
    "useful power is T*V0 = eta*P; "
    "flight density is the 1976 atmosphere at --alt, or the supplied --rho; "
    "true airspeed V0 > 0; the plot end is "
    f"{PLOT_END_FACTOR:g} times the given speed at fixed P, D, and density"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import atmosphere, require_altitude
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for density from --alt"
        ) from exc
    return atmosphere, require_altitude


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def disk_area(diameter: float) -> float:
    """propeller_disk_area."""
    return math.pi * diameter * diameter / 4.0


def disk_speed(wake: float, speed: float) -> float:
    """actuator_disk_speed."""
    return 0.5 * (wake + speed)


def induced_from_speeds(through_disk: float, speed: float) -> float:
    """propeller_induced_velocity."""
    return through_disk - speed


def far_wake(speed: float, induced: float) -> float:
    """propeller_far_wake_speed."""
    return speed + 2.0 * induced


def thrust_momentum(rho: float, through_disk: float, area: float, wake: float, speed: float) -> float:
    """ideal_propeller_thrust."""
    return rho * through_disk * area * (wake - speed)


def thrust_bernoulli(rho: float, area: float, wake: float, speed: float) -> float:
    """ideal_propeller_thrust_bernoulli."""
    return 0.5 * rho * area * (wake * wake - speed * speed)


def thrust_from_induced(rho: float, area: float, induced: float, speed: float) -> float:
    """ideal_propeller_thrust_from_induced."""
    return 2.0 * rho * area * induced * (speed + induced)


def induced_from_thrust(speed: float, thrust: float, rho: float, area: float) -> float:
    """propeller_induced_velocity_from_thrust."""
    return 0.5 * (-speed + math.sqrt(speed * speed + 2.0 * thrust / (rho * area)))


def actuator_power(thrust: float, through_disk: float) -> float:
    """ideal_actuator_power."""
    return thrust * through_disk


def power_from_induced(rho: float, area: float, induced: float, speed: float) -> float:
    """ideal_actuator_power_from_induced."""
    through_disk = speed + induced
    return 2.0 * rho * area * induced * through_disk * through_disk


def propulsive_efficiency(thrust: float, speed: float, power: float) -> float:
    """ideal_propulsive_efficiency."""
    return thrust * speed / power


def efficiency_from_speeds(speed: float, through_disk: float) -> float:
    """ideal_propulsive_efficiency_from_speeds."""
    return speed / through_disk


def induced_from_power(power: float, rho: float, area: float, speed: float) -> float:
    """Physical root of ideal_actuator_power_from_induced = P."""
    scale = 2.0 * rho * area
    lo = 0.0
    hi = max((power / scale) ** (1.0 / 3.0), power / (scale * speed * speed))
    hi = max(hi, 1.0)
    for _ in range(40):
        if power_from_induced(rho, area, hi, speed) >= power:
            break
        hi *= 2.0
    else:
        raise ValueError("induced velocity bracket did not close")
    induced = 0.5 * (lo + hi)
    for _ in range(NEWTON_ITERS):
        through_disk = speed + induced
        residual = scale * induced * through_disk * through_disk - power
        if abs(residual) <= CHECK_TOL * max(power, 1.0):
            return induced
        deriv = scale * through_disk * (speed + 3.0 * induced)
        nxt = induced - residual / deriv
        if residual > 0.0:
            hi = induced
        else:
            lo = induced
        if nxt <= lo or nxt >= hi:
            nxt = 0.5 * (lo + hi)
        induced = nxt
    raise ValueError("induced velocity did not converge")


def solution(power: float, diameter: float, speed: float, rho: float) -> dict[str, float]:
    require_positive("shaft power", power)
    require_positive("propeller diameter", diameter)
    require_positive("speed", speed)
    require_positive("density", rho)
    area = disk_area(diameter)
    induced = induced_from_power(power, rho, area, speed)
    through_disk = speed + induced
    wake = far_wake(speed, induced)
    thrust = thrust_from_induced(rho, area, induced, speed)
    useful = thrust * speed
    return {
        "P_W": power,
        "D_m": diameter,
        "A_m2": area,
        "rho_kg_m3": rho,
        "V0_m_s": speed,
        "vi_m_s": induced,
        "Vp_m_s": through_disk,
        "Ve_m_s": wake,
        "mdot_kg_s": rho * area * through_disk,
        "T_N": thrust,
        "useful_power_W": useful,
        "eta": propulsive_efficiency(thrust, speed, power),
        "plot_end_factor": PLOT_END_FACTOR,
        "V_plot_max_m_s": PLOT_END_FACTOR * speed,
    }


def speed_grid(speed: float) -> list[float]:
    start = speed / N_PLOT
    return [start + (PLOT_END_FACTOR * speed - start) * i / (N_PLOT - 1) for i in range(N_PLOT)]


def sweep_curves(
    power: float,
    diameter: float,
    rho: float,
    speeds: list[float],
) -> tuple[list[float], list[float], list[float], list[float]]:
    area = disk_area(diameter)
    thrusts: list[float] = []
    induced: list[float] = []
    etas: list[float] = []
    for value in speeds:
        vi = induced_from_power(power, rho, area, value)
        thrust = thrust_from_induced(rho, area, vi, value)
        thrusts.append(thrust)
        induced.append(vi)
        etas.append(efficiency_from_speeds(value, value + vi))
    return speeds, thrusts, induced, etas


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the ideal propeller") from exc
    return plt


def plot_propeller(path: Path, result: dict[str, float]) -> None:
    plt = ensure_matplotlib()
    speeds, thrusts, induced, etas = sweep_curves(
        result["P_W"],
        result["D_m"],
        result["rho_kg_m3"],
        speed_grid(result["V0_m_s"]),
    )
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
    ax_t, ax_v, ax_e = axes
    ax_t.plot(speeds, thrusts, color="#1a5276", linewidth=1.8, label="ideal thrust")
    ax_v.plot(speeds, induced, color="#1a5276", linewidth=1.8, label="induced velocity")
    ax_e.plot(speeds, etas, color="#1a5276", linewidth=1.8, label="ideal efficiency")
    ax_t.plot(
        result["V0_m_s"],
        result["T_N"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax_v.plot(
        result["V0_m_s"],
        result["vi_m_s"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax_e.plot(
        result["V0_m_s"],
        result["eta"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax_t.set_title(PLOT_TITLE)
    ax_t.set_ylabel("ideal thrust (N)")
    ax_v.set_ylabel("induced velocity (m/s)")
    ax_e.set_ylabel("ideal propulsive efficiency")
    ax_e.set_xlabel("true airspeed (m/s)")
    ax_t.set_xlim(0.0, result["V_plot_max_m_s"])
    ax_t.set_ylim(bottom=0.0)
    ax_v.set_ylim(bottom=0.0)
    ax_e.set_ylim(0.0, 1.0)
    for axis in axes:
        axis.grid(True, alpha=0.35)
        axis.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(
    result: dict[str, float],
    density_source: str,
    altitude: float | None,
    path: Path,
) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "incompressible actuator disk")
    print_kv("density_source", density_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("P_W", result["P_W"])
    print_kv("D_m", result["D_m"])
    print_kv("A_m2", result["A_m2"])
    print_kv("rho_kg_m3", result["rho_kg_m3"])
    print_kv("V0_m_s", result["V0_m_s"])
    print_kv("vi_m_s", result["vi_m_s"])
    print_kv("Vp_m_s", result["Vp_m_s"])
    print_kv("Ve_m_s", result["Ve_m_s"])
    print_kv("mdot_kg_s", result["mdot_kg_s"])
    print_kv("T_N", result["T_N"])
    print_kv("useful_power_W", result["useful_power_W"])
    print_kv("eta", result["eta"])
    print_kv("plot_end_factor", result["plot_end_factor"])
    print_kv("V_plot_max_m_s", result["V_plot_max_m_s"])
    print_kv("graph", str(path))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    if near(disk_area(2.0), math.pi, "disk area of diameter two"):
        return 1
    if near(disk_speed(3.0, 1.0), 2.0, "disk speed"):
        return 1
    if near(induced_from_speeds(2.0, 1.0), 1.0, "induced from speeds"):
        return 1
    if near(far_wake(1.0, 1.0), 3.0, "far-wake speed"):
        return 1
    rho = 2.0
    area = 1.0
    speed = 1.0
    induced = 1.0
    through_disk = 2.0
    wake = 3.0
    thrust = thrust_from_induced(rho, area, induced, speed)
    if near(thrust, 8.0, "thrust from induced"):
        return 1
    if near(thrust_momentum(rho, through_disk, area, wake, speed), 8.0, "momentum thrust"):
        return 1
    if near(thrust_bernoulli(rho, area, wake, speed), 8.0, "Bernoulli thrust"):
        return 1
    if near(induced_from_thrust(speed, thrust, rho, area), induced, "induced from thrust"):
        return 1
    power = actuator_power(thrust, through_disk)
    if near(power, 16.0, "actuator power"):
        return 1
    if near(power_from_induced(rho, area, induced, speed), 16.0, "power from induced"):
        return 1
    if near(propulsive_efficiency(thrust, speed, power), 0.5, "efficiency"):
        return 1
    if near(efficiency_from_speeds(speed, through_disk), 0.5, "efficiency from speeds"):
        return 1
    recovered = induced_from_power(power, rho, area, speed)
    if near(recovered, induced, "induced from power"):
        return 1

    point = solution(16.0, 2.0 / math.sqrt(math.pi), 1.0, 2.0)
    if near(point["A_m2"], 1.0, "solution disk area"):
        return 1
    if near(point["T_N"], 8.0, "solution thrust"):
        return 1
    if near(point["vi_m_s"], 1.0, "solution induced"):
        return 1
    if near(point["eta"], 0.5, "solution efficiency"):
        return 1
    if near(point["useful_power_W"], 8.0, "useful power"):
        return 1
    if near(point["mdot_kg_s"], 4.0, "mass flow"):
        return 1

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

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "ideal_propeller.png"
        code, text, err = capture(
            [
                "--power",
                "16",
                "--diameter",
                str(2.0 / math.sqrt(math.pi)),
                "--speed",
                "1",
                "--rho",
                "2",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli unit disk failed: {err}")
        if "density_source: density" not in text:
            return fail("cli did not report a supplied density")
        if "eta: 0.5" not in text:
            return fail("cli eta was not 1/2")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
        code, text, err = capture(
            [
                "--power",
                "100000",
                "--diameter",
                "2",
                "--speed",
                "50",
                "--alt",
                "0",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"cli sea-level altitude failed: {err}")
        if "density_source: altitude" not in text:
            return fail("cli did not report altitude density")
        if "Z_m: 0" not in text:
            return fail("cli omitted sea-level altitude")
        code, _text, err = capture(
            [
                "--power",
                "100000",
                "--diameter",
                "2",
                "--speed",
                "50",
                "--alt",
                "0",
                "--rho",
                "1.225",
            ]
        )
        if code == 0:
            return fail("cli accepted both --alt and --rho")
        code, _text, err = capture(["--power", "1", "--diameter", "1", "--speed", "1"])
        if code == 0:
            return fail("cli accepted a missing density")

    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ideal actuator-disk propeller thrust, induced velocity, "
            "and propulsive efficiency from shaft power, diameter, and speed."
        )
    )
    parser.add_argument("--power", type=float, default=None, help="ideal shaft power P [W]")
    parser.add_argument("--diameter", type=float, default=None, help="propeller diameter D [m]")
    parser.add_argument("--speed", type=float, default=None, help="true airspeed V0 [m/s]")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--power": args.power,
        "--diameter": args.diameter,
        "--speed": args.speed,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --power, --diameter, --speed, and --rho or --alt; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if args.alt is None and args.rho is None:
        print("error: requires --alt or --rho", file=sys.stderr)
        return 2
    if args.alt is not None and args.rho is not None:
        print("error: pass --alt or --rho, not both", file=sys.stderr)
        return 2

    try:
        altitude = None
        if args.alt is not None:
            atmosphere, require_altitude = load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            rho = state["rho"]
            density_source = "altitude"
            altitude = float(state["Z"])
        else:
            require_positive("density", args.rho)
            rho = args.rho
            density_source = "density"
        result = solution(args.power, args.diameter, args.speed, rho)
        out_path = Path(args.out) if args.out else SKILL_DIR / "ideal_propeller.png"
        out_path = out_path.resolve()
        plot_propeller(out_path, result)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, density_source, altitude, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
