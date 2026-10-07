#!/usr/bin/env python3
"""Hall-thruster thrust, mass flow, input power, and ideal beam current.

Exhaust speed is Isp*g0. Power and thrust are electric_propulsion_power.
Mass flow is T/ve. Ideal singly charged beam current is mdot*e/m_ion,
multiplied by --utilization, the ionized fraction of the propellant.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Hall thruster beam current"
G0 = 9.80665
# CODATA 2022 exact elementary charge.
ELEMENTARY_CHARGE_C = 1.602176634e-19
# Xenon atom mass used for a singly charged Hall-thruster beam, 2.18e-25 kg.
XENON_MASS_KG = 2.18e-25
N_CURVE = 81

ASSUMPTIONS = (
    "ideal Hall thruster sizing; ve = Isp*g0 with g0 = 9.80665 m/s^2; "
    "electric_propulsion_power P = T*ve/(2*eta); mdot = T/ve; "
    "ideal singly charged beam current Ib = utilization*mdot*e/m_ion; "
    "default ion is xenon at 2.18e-25 kg; elementary charge is the CODATA exact value; "
    "utilization defaults to 1 and is the ionized fraction of the propellant; "
    "no magnetic-field topology and no plume divergence; "
    "propellant mass and burn time stay in ROCKET - ElectricPropulsionDeltaV"
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


def exhaust_speed(isp: float) -> float:
    return isp * G0


def input_power(thrust: float, ve: float, eta: float) -> float:
    """electric_propulsion_power."""
    return thrust * ve / (2.0 * eta)


def thrust_from_power(power: float, ve: float, eta: float) -> float:
    return power * 2.0 * eta / ve


def beam_current(mdot: float, ion_mass: float, utilization: float) -> float:
    """hall_beam_current."""
    return mdot * utilization * ELEMENTARY_CHARGE_C / ion_mass


def evaluate(
    isp: float,
    eta: float,
    thrust: float | None,
    power: float | None,
    ion_mass: float,
    utilization: float,
) -> dict[str, float | str]:
    require_positive("specific impulse", isp)
    if not math.isfinite(eta) or eta <= 0.0 or eta > 1.0:
        raise ValueError("efficiency must be finite and in (0, 1]")
    if (thrust is None) == (power is None):
        raise ValueError("pass exactly one of --thrust or --power")
    require_positive("ion mass", ion_mass)
    if not math.isfinite(utilization) or utilization <= 0.0 or utilization > 1.0:
        raise ValueError("utilization must be finite and in (0, 1]")
    ve = exhaust_speed(isp)
    if thrust is None:
        require_positive("power", power)
        assert power is not None
        thrust = thrust_from_power(power, ve, eta)
        given = "power"
    else:
        require_positive("thrust", thrust)
        power = input_power(thrust, ve, eta)
        given = "thrust"
    mdot = thrust / ve
    return {
        "given": given,
        "Isp_s": isp,
        "eta": eta,
        "ion_mass_kg": ion_mass,
        "utilization": utilization,
        "ve_m_s": ve,
        "thrust_N": thrust,
        "mdot_kg_s": mdot,
        "power_W": power,
        "Ib_A": beam_current(mdot, ion_mass, utilization),
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
        raise ValueError("matplotlib is required to plot beam current") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    thrust = float(result["thrust_N"])
    ve = float(result["ve_m_s"])
    ion_mass = float(result["ion_mass_kg"])
    utilization = float(result["utilization"])
    span = linspace(0.25 * thrust, 2.0 * thrust, N_CURVE)
    currents = [beam_current(item / ve, ion_mass, utilization) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, currents, color="#1a5276", linewidth=1.8, label="beam current")
    ax.plot(thrust, float(result["Ib_A"]), "s", color="#1a5276", markersize=7, label="operating thrust")
    ax.set_xlabel("thrust (N)")
    ax.set_ylabel("beam current (A)")
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
    for key in (
        "given",
        "Isp_s",
        "eta",
        "ion_mass_kg",
        "utilization",
        "ve_m_s",
        "thrust_N",
        "mdot_kg_s",
        "power_W",
        "Ib_A",
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


def run_check() -> int:
    ve = 2000.0 * G0
    thrust = 0.08
    eta = 0.5
    power = input_power(thrust, ve, eta)
    if not close(power, thrust * ve):
        return fail("power pair")
    mdot = thrust / ve
    current = beam_current(mdot, XENON_MASS_KG, 1.0)
    if not close(current, mdot * ELEMENTARY_CHARGE_C / XENON_MASS_KG):
        return fail("beam current")
    halved = beam_current(mdot, XENON_MASS_KG, 0.5)
    if not close(halved, 0.5 * current):
        return fail("utilization")
    from_power = evaluate(2000.0, eta, None, power, XENON_MASS_KG, 1.0)
    if not close(float(from_power["thrust_N"]), thrust):
        return fail("thrust from power")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "hall.png"
        code, text, err = capture(
            ["--isp", "2000", "--eta", "0.5", "--thrust", "0.08", "--out", str(png)]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "ve_m_s:" not in text or "Ib_A:" not in text or "power_W:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, err = capture(["--isp", "2000", "--eta", "0.5", "--thrust", "0.08", "--power", "1000"])
        if code != 2:
            return fail("both thrust and power were accepted")

    print("check: pass")
    print_kv("Ib_A", current)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hall thruster thrust, power, and beam current.")
    parser.add_argument("--isp", type=float, default=None, help="specific impulse [s]")
    parser.add_argument("--eta", type=float, default=None, help="thrust efficiency (0, 1]")
    parser.add_argument("--thrust", type=float, default=None, help="thrust [N]")
    parser.add_argument("--power", type=float, default=None, help="input power [W]")
    parser.add_argument("--ion-mass", type=float, default=None, help="ion mass [kg]; default xenon")
    parser.add_argument("--utilization", type=float, default=1.0, help="ionized fraction of the propellant; default 1")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.isp is None or args.eta is None:
        print("error: requires --isp and --eta", file=sys.stderr)
        return 2
    ion_mass = XENON_MASS_KG if args.ion_mass is None else args.ion_mass
    try:
        result = evaluate(args.isp, args.eta, args.thrust, args.power, ion_mass, args.utilization)
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
