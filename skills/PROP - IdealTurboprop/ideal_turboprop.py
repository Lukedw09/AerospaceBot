#!/usr/bin/env python3
"""Design-point ideal turboprop.

The ideal turbojet gas generator drives a propeller. Shaft power is the
turbine enthalpy remaining after the compressor is paid, expanded to
freestream static pressure. Propeller thrust is eta_p*P/V0 per unit inlet
airflow. Residual jet thrust is omitted.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Ideal turboprop"
N_PLOT = 81
MDOT = 1.0

SKILL_DIR = Path(__file__).resolve().parent
IDEAL_DIR = SKILL_DIR.parent / "PROP - IdealTurboJet"

ASSUMPTIONS = (
    "design-point ideal turboprop; the ideal turbojet gas generator drives a propeller; "
    "compressor and burner algebra are the ideal-turbojet records; "
    "shaft power per unit inlet airflow leaves the residual jet at flight speed: "
    "0.5*(1+f)*(Ve^2-V0^2), the turbojet nozzle enthalpy minus the residual kinetic energy; "
    "propeller thrust is eta_p*P_shaft/V0; residual jet thrust f*V0 is omitted; "
    "fuel-air ratio is burner_fuel_air_ratio; TSFC is turbojet_tsfc on the propeller thrust; "
    "Mach must be > 0 because the propeller thrust expression is singular at V0 = 0; "
    "static thrust is out of scope; no gearbox map"
)


def load_ideal():
    folder = str(IDEAL_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import ideal_turbojet as ideal

    return ideal


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def shaft_power(fuel: float, ve: float, v0: float) -> float:
    """Enthalpy remaining after the compressor, per unit inlet airflow.

    The residual jet keeps relative speed V0, so its kinetic energy stays in the stream.
    """
    residual = ve * ve - v0 * v0
    if residual <= 0.0:
        raise ValueError(
            "gas-generator exhaust is not faster than flight speed; no shaft power remains"
        )
    return 0.5 * (1.0 + fuel) * residual


def propeller_thrust(eta_prop: float, power: float, v0: float) -> float:
    return eta_prop * power / v0


def solution(
    mach: float,
    temperature: float,
    pressure: float,
    tit: float,
    opr: float,
    eta_prop: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
) -> dict[str, float]:
    ideal = load_ideal()
    if not math.isfinite(mach) or mach <= 0.0:
        raise ValueError("Mach must be finite and > 0; static thrust is out of scope")
    if not math.isfinite(eta_prop) or eta_prop <= 0.0 or eta_prop > 1.0:
        raise ValueError("propeller efficiency must be finite and in (0, 1]")
    core = ideal.solution(
        mach,
        temperature,
        pressure,
        tit,
        opr,
        gamma,
        cp,
        heating_value,
        gas_constant,
    )
    power = shaft_power(core["f"], core["Ve_m_s"], core["V0_m_s"])
    thrust = propeller_thrust(eta_prop, power, core["V0_m_s"])
    if thrust <= 0.0:
        raise ValueError("propeller thrust is not positive")
    specific = thrust / MDOT
    ct = ideal.tsfc(core["f"], specific)
    return {
        "M": core["M"],
        "T0_K": core["T0_K"],
        "p0_Pa": core["p0_Pa"],
        "V0_m_s": core["V0_m_s"],
        "Tt4_K": core["Tt4_K"],
        "pi_c": core["pi_c"],
        "f": core["f"],
        "eta_prop": eta_prop,
        "mdot_kg_s": MDOT,
        "shaft_power_W": power * MDOT,
        "thrust_N": thrust,
        "specific_thrust": specific,
        "tsfc": ct,
        "gamma": gamma,
        "cp_J_kgK": cp,
        "Q_J_kg": heating_value,
    }


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the turboprop") from exc
    return plt


def write_plot(result: dict[str, float], cycle: dict, out_path: Path) -> None:
    plt = ensure_matplotlib()
    mach = result["M"]
    end = max(0.9, 1.5 * mach)
    start = end / (N_PLOT + 2)
    xs: list[float] = []
    thrust: list[float] = []
    tsfc: list[float] = []
    for index in range(1, N_PLOT + 1):
        point_mach = start + (end - start) * (index - 1) / (N_PLOT - 1)
        try:
            point = solution(mach=point_mach, **cycle)
        except ValueError:
            continue
        xs.append(point_mach)
        thrust.append(point["thrust_N"])
        tsfc.append(point["tsfc"])
    if len(xs) < 2:
        raise ValueError("could not build a Mach sweep")
    fig, ax_thrust = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax_tsfc = ax_thrust.twinx()
    ax_thrust.plot(xs, thrust, color="#1a5276", linewidth=1.8, label="thrust")
    ax_tsfc.plot(xs, tsfc, color="#b9770e", linewidth=1.8, label="TSFC")
    ax_thrust.plot(mach, result["thrust_N"], "s", color="#1a5276", markersize=7)
    ax_tsfc.plot(mach, result["tsfc"], "s", color="#b9770e", markersize=7)
    ax_thrust.set_xlabel("Mach")
    ax_thrust.set_ylabel("thrust per unit inlet airflow (N)")
    ax_tsfc.set_ylabel("TSFC (kg/(N·s))")
    ax_thrust.set_title(PLOT_TITLE)
    ax_thrust.grid(True, alpha=0.35)
    handles, labels = ax_thrust.get_legend_handles_labels()
    extra_handles, extra_labels = ax_tsfc.get_legend_handles_labels()
    ax_thrust.legend(handles + extra_handles, labels + extra_labels, loc="best", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: dict[str, float], freestream_source: str, altitude: float | None, sources: dict[str, str], graph: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    for key in (
        "M",
        "T0_K",
        "p0_Pa",
        "V0_m_s",
        "Tt4_K",
        "pi_c",
        "eta_prop",
        "f",
        "mdot_kg_s",
        "shaft_power_W",
        "thrust_N",
        "specific_thrust",
        "tsfc",
    ):
        print_kv(key, result[key])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", sources["gamma"])
    print_kv("cp_J_kgK", result["cp_J_kgK"])
    print_kv("cp_source", sources["cp"])
    print_kv("Q_J_kg", result["Q_J_kg"])
    print_kv("Q_source", sources["heating"])
    print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    ideal = load_ideal()
    gamma = 1.4
    cp = ideal.default_cp(gamma)
    core = ideal.solution(0.6, 220.0, 20000.0, 1400.0, 12.0, gamma, cp, ideal.DEFAULT_HEATING_VALUE, ideal.R_AIR)
    power = shaft_power(core["f"], core["Ve_m_s"], core["V0_m_s"])
    issue = near(
        power,
        0.5 * (1.0 + core["f"]) * (core["Ve_m_s"] ** 2 - core["V0_m_s"] ** 2),
        "shaft",
    )
    if issue:
        return issue
    point = solution(0.6, 220.0, 20000.0, 1400.0, 12.0, 0.8, gamma, cp, ideal.DEFAULT_HEATING_VALUE, ideal.R_AIR)
    issue = near(point["thrust_N"], 0.8 * power / core["V0_m_s"], "thrust")
    if issue:
        return issue
    issue = near(point["f"], core["f"], "fuel")
    if issue:
        return issue
    issue = near(point["tsfc"], core["f"] / point["specific_thrust"], "tsfc")
    if issue:
        return issue
    try:
        solution(0.0, 220.0, 20000.0, 1400.0, 12.0, 0.8, gamma, cp, ideal.DEFAULT_HEATING_VALUE, ideal.R_AIR)
        return fail("static Mach was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "prop.png"
        code, text, err = capture(
            [
                "--mach",
                "0.6",
                "--tit",
                "1400",
                "--opr",
                "12",
                "--eta-prop",
                "0.8",
                "--temperature",
                "220",
                "--pressure",
                "20000",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        for key in ("shaft_power_W:", "thrust_N:", "specific_thrust:", "tsfc:", "f:"):
            if key not in text:
                return fail(f"missing {key}")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
    print("check: pass")
    print_kv("shaft_power_W", point["shaft_power_W"])
    return 0


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design-point ideal turboprop.")
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number, > 0")
    parser.add_argument("--tit", type=float, default=None, help="turbine inlet temperature [K]")
    parser.add_argument("--opr", type=float, default=None, help="compressor pressure ratio")
    parser.add_argument("--eta-prop", type=float, default=None, help="propeller efficiency (0, 1]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--temperature", type=float, default=None, help="freestream static temperature [K]")
    parser.add_argument("--pressure", type=float, default=None, help="freestream static pressure [Pa]")
    parser.add_argument("--heating-value", type=float, default=None)
    parser.add_argument("--cp", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    missing = [
        flag
        for flag, value in (
            ("--mach", args.mach),
            ("--tit", args.tit),
            ("--opr", args.opr),
            ("--eta-prop", args.eta_prop),
        )
        if value is None
    ]
    if missing:
        print("error: requires --mach, --tit, --opr, --eta-prop, and a freestream path; missing " + ", ".join(missing), file=sys.stderr)
        return 2
    ideal = load_ideal()
    has_alt = args.alt is not None
    has_tp = args.temperature is not None or args.pressure is not None
    if has_alt and has_tp:
        print("error: pass --alt or --temperature/--pressure, not both", file=sys.stderr)
        return 2
    if not has_alt and (args.temperature is None or args.pressure is None):
        print("error: requires --alt, or both --temperature and --pressure", file=sys.stderr)
        return 2
    try:
        altitude = None
        if has_alt:
            atmosphere, require_altitude = ideal.load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            temperature = float(state["T"])
            pressure = float(state["p"])
            freestream_source = "altitude"
            altitude = float(state["Z"])
        else:
            ideal.require_positive("temperature", args.temperature)
            ideal.require_positive("pressure", args.pressure)
            temperature = args.temperature
            pressure = args.pressure
            freestream_source = "temperature_pressure"
        if args.gamma is None:
            gamma = ideal.DEFAULT_GAMMA
            gamma_source = "default"
        else:
            ideal.require_gamma(args.gamma)
            gamma = args.gamma
            gamma_source = "user"
        if args.cp is None:
            cp = ideal.default_cp(gamma)
            cp_source = "gamma_air_R"
        else:
            ideal.require_positive("cp", args.cp)
            cp = args.cp
            cp_source = "user"
        if args.heating_value is None:
            heating = ideal.DEFAULT_HEATING_VALUE
            heating_source = "default"
        else:
            ideal.require_positive("heating value", args.heating_value)
            heating = args.heating_value
            heating_source = "user"
        cycle = dict(
            temperature=temperature,
            pressure=pressure,
            tit=args.tit,
            opr=args.opr,
            eta_prop=args.eta_prop,
            gamma=gamma,
            cp=cp,
            heating_value=heating,
            gas_constant=ideal.R_AIR,
        )
        result = solution(mach=args.mach, **cycle)
        out_path = Path(args.out) if args.out else SKILL_DIR / "ideal_turboprop.png"
        out_path = out_path.resolve()
        plot_cycle = dict(cycle)
        write_plot(result, plot_cycle, out_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(
        result,
        freestream_source,
        altitude,
        {"gamma": gamma_source, "cp": cp_source, "heating": heating_source},
        out_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
