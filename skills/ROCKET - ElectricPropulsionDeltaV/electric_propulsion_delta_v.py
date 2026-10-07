#!/usr/bin/env python3
"""Low-thrust electric propulsion: vacuum rocket equation, burn time, and power.

vacuum_propellant_mass and vacuum_wet_mass use the exhaust speed.
electric_propulsion_burn_time is m_p*ve/T.
electric_propulsion_power is T*ve/(2*eta).
electric_propulsion_specific_power is P/m0.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Electric propulsion delta-v"
G0 = 9.80665
N_CURVE = 201
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "vacuum, constant exhaust speed, constant thrust; "
    "vacuum_propellant_mass mp = mf*(exp(dv/ve)-1); "
    "vacuum_wet_mass m0 = mf*exp(dv/ve); "
    "electric_propulsion_burn_time tb = mp*ve/T while thrusting; "
    "calendar time is that burn divided by the duty cycle; "
    "electric_propulsion_power P = T*ve/(2*eta) from jet power 0.5*T*ve; "
    "electric_propulsion_specific_power P/m0; "
    "no gravity loss, no plume model, no throttle table"
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


def propellant_mass(dry: float, delta_v: float, exhaust: float) -> float:
    """vacuum_propellant_mass."""
    return dry * (math.exp(delta_v / exhaust) - 1.0)


def wet_mass(dry: float, delta_v: float, exhaust: float) -> float:
    """vacuum_wet_mass."""
    return dry * math.exp(delta_v / exhaust)


def burn_time(propellant: float, exhaust: float, thrust: float) -> float:
    """electric_propulsion_burn_time."""
    return propellant * exhaust / thrust


def input_power(thrust: float, exhaust: float, eta: float) -> float:
    """electric_propulsion_power."""
    return thrust * exhaust / (2.0 * eta)


def specific_power(power: float, wet: float) -> float:
    """electric_propulsion_specific_power."""
    return power / wet


def evaluate(
    dry: float,
    thrust: float,
    delta_v: float,
    exhaust: float,
    isp: float | None,
    eta: float,
    duty: float,
) -> dict[str, float | str]:
    require_positive("dry mass", dry)
    require_positive("thrust", thrust)
    require_positive("delta-v", delta_v)
    require_positive("exhaust speed", exhaust)
    if not math.isfinite(eta) or eta <= 0.0 or eta > 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    if not math.isfinite(duty) or duty <= 0.0 or duty > 1.0:
        raise ValueError("duty cycle must be in (0, 1]")
    mp = propellant_mass(dry, delta_v, exhaust)
    m0 = wet_mass(dry, delta_v, exhaust)
    tb = burn_time(mp, exhaust, thrust)
    power = input_power(thrust, exhaust, eta)
    result: dict[str, float | str] = {
        "mf_kg": dry,
        "T_N": thrust,
        "dv_m_s": delta_v,
        "ve_m_s": exhaust,
        "eta": eta,
        "duty": duty,
        "mp_kg": mp,
        "m0_kg": m0,
        "tb_thrust_s": tb,
        "tb_s": tb / duty,
        "P_W": power,
        "specific_power_W_kg": specific_power(power, m0),
    }
    if isp is not None:
        result["Isp_s"] = isp
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
        raise ValueError("matplotlib is required to plot propellant mass") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    dry = float(result["mf_kg"])
    exhaust = float(result["ve_m_s"])
    delta_v = float(result["dv_m_s"])
    span = linspace(0.0, 1.5 * delta_v, N_CURVE)
    masses = [propellant_mass(dry, dv, exhaust) for dv in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, masses, color="#1a5276", linewidth=1.8, label="propellant")
    ax.plot(delta_v, float(result["mp_kg"]), "s", color="#1a5276", markersize=7, label="operating point")
    ax.set_xlabel("delta-v (m/s)")
    ax.set_ylabel("propellant mass (kg)")
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
        "mf_kg",
        "T_N",
        "dv_m_s",
        "ve_m_s",
        "Isp_s",
        "eta",
        "duty",
        "mp_kg",
        "m0_kg",
        "tb_thrust_s",
        "tb_s",
        "P_W",
        "specific_power_W_kg",
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
    dry, thrust, delta_v, exhaust, eta, duty = 10.0, 0.02, 1000.0, 20000.0, 0.5, 0.5
    mp = propellant_mass(dry, delta_v, exhaust)
    if not close(mp, dry * (math.exp(delta_v / exhaust) - 1.0)):
        return fail("propellant")
    m0 = wet_mass(dry, delta_v, exhaust)
    if not close(m0, dry + mp):
        return fail("wet mass")
    tb = burn_time(mp, exhaust, thrust)
    if not close(tb, mp * exhaust / thrust):
        return fail("burn time")
    power = input_power(thrust, exhaust, eta)
    if not close(power, 400.0):
        return fail("power")
    if not close(specific_power(power, m0), power / m0):
        return fail("specific power")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "ep.png"
        code, text, err = capture(
            [
                "--dry",
                "10",
                "--thrust",
                "0.02",
                "--dv",
                "1000",
                "--ve",
                "20000",
                "--eta",
                "0.5",
                "--duty",
                "0.5",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "P_W: 400" not in text or "tb_s:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, _err = capture(
            ["--dry", "10", "--thrust", "0.02", "--dv", "1000", "--ve", "20000", "--isp", "2000"]
        )
        if code == 0:
            return fail("both isp and ve were accepted")
        code, text, err = capture(["--dry", "10", "--thrust", "1", "--dv", "1000", "--isp", "2000"])
        if code != 0:
            return fail(f"isp path failed: {err}")
        if "Isp_s: 2000" not in text:
            return fail("isp not printed")
        if not close(float(text.split("ve_m_s: ")[1].split()[0]), 2000.0 * G0):
            return fail("isp conversion")

    print("check: pass")
    print_kv("P_W", power)
    print_kv("mp_kg", mp)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Electric-propulsion propellant, burn time, and power.")
    parser.add_argument("--dry", type=float, default=None, help="dry mass [kg]")
    parser.add_argument("--thrust", type=float, default=None, help="thrust [N]")
    parser.add_argument("--dv", type=float, default=None, help="vacuum delta-v [m/s]")
    parser.add_argument("--isp", type=float, default=None, help="specific impulse [s]")
    parser.add_argument("--ve", type=float, default=None, help="exhaust speed [m/s]")
    parser.add_argument("--eta", type=float, default=1.0, help="thrust efficiency (0, 1]")
    parser.add_argument("--duty", type=float, default=1.0, help="duty cycle (0, 1]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.dry is None or args.thrust is None or args.dv is None:
        print("error: requires --dry, --thrust, --dv, and --isp or --ve", file=sys.stderr)
        return 2
    if (args.isp is None) == (args.ve is None):
        print("error: pass exactly one of --isp or --ve", file=sys.stderr)
        return 2
    try:
        if args.ve is not None:
            exhaust = float(args.ve)
            isp = None
        else:
            require_positive("specific impulse", float(args.isp))
            isp = float(args.isp)
            exhaust = isp * G0
        result = evaluate(args.dry, args.thrust, args.dv, exhaust, isp, args.eta, args.duty)
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
