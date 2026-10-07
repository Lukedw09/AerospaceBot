#!/usr/bin/env python3
"""Ideal scramjet Brayton cycle.

Ram compression stops at a supersonic combustor Mach. Heat addition is at
constant pressure and constant velocity. The nozzle expands ideally back to
freestream pressure. Fuel-air ratio, specific thrust, and TSFC reuse the
ramjet records. A combustor Mach at or below 1 is the ramjet skill.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Ideal scramjet"
N_PLOT = 61

SKILL_DIR = Path(__file__).resolve().parent
RAM_DIR = SKILL_DIR.parent / "PROP - IdealRamjet"

ASSUMPTIONS = (
    "ideal scramjet Brayton cycle; calorically perfect gas; "
    "NASA Glenn: a scramjet has no terminal normal shock, so the diffuser stops "
    "while the flow is still supersonic; combustion is at constant pressure; "
    "the nozzle expands isentropically back to freestream pressure; "
    "combustor entrance Mach is --combustor-mach and must be > 1; "
    "flight Mach must be greater than that combustor Mach; "
    "constant-velocity heat addition keeps the entrance speed through the burner; "
    "f is burner_fuel_air_ratio; Fs is turbojet_specific_thrust; TSFC is turbojet_tsfc; "
    "a combustor Mach at or below 1 is rejected; that case is PROP - IdealRamjet; "
    "no inlet schedule and no finite-rate chemistry"
)


def load_ram():
    folder = str(RAM_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import ideal_ramjet as ram

    return ram


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def solution(
    mach: float,
    combustor_mach: float,
    temperature: float,
    pressure: float,
    tmax: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
) -> dict[str, float]:
    ram = load_ram()
    ram.require_positive("temperature", temperature)
    ram.require_positive("pressure", pressure)
    ram.require_positive("max total temperature", tmax)
    ram.require_gamma(gamma)
    ram.require_positive("cp", cp)
    ram.require_positive("heating value", heating_value)
    ram.require_positive("gas constant", gas_constant)
    if not math.isfinite(combustor_mach) or combustor_mach <= 1.0:
        raise ValueError("combustor Mach must be > 1; a subsonic burner is PROP - IdealRamjet")
    if not math.isfinite(mach) or mach <= combustor_mach:
        raise ValueError("flight Mach must be greater than the combustor Mach")

    tau0 = ram.stagnation_temperature_ratio(mach, gamma)
    tau_c = ram.stagnation_temperature_ratio(combustor_mach, gamma)
    tt2 = temperature * tau0
    t2 = tt2 / tau_c
    p2 = pressure * (t2 / temperature) ** (gamma / (gamma - 1.0))
    a2 = ram.speed_of_sound(t2, gamma, gas_constant)
    v2 = combustor_mach * a2
    t4 = tmax - v2 * v2 / (2.0 * cp)
    if t4 <= t2:
        raise ValueError("max total temperature does not heat the combustor")
    a4 = ram.speed_of_sound(t4, gamma, gas_constant)
    m4 = v2 / a4
    pt4 = p2 * ram.stagnation_pressure_ratio(1.0 + 0.5 * (gamma - 1.0) * m4 * m4, gamma)
    f = ram.fuel_air_ratio(cp, tmax, tt2, heating_value)
    npr = ram.nozzle_pressure_ratio(pt4, pressure)
    ve = ram.nozzle_exit_velocity(cp, tmax, npr, gamma)
    v0 = mach * ram.speed_of_sound(temperature, gamma, gas_constant)
    fs = ram.specific_thrust(f, ve, v0)
    if fs <= 0.0:
        raise ValueError("specific thrust is not positive at this flight condition")
    ct = ram.tsfc(f, fs)
    return {
        "M": mach,
        "Mc": combustor_mach,
        "T0_K": temperature,
        "p0_Pa": pressure,
        "V0_m_s": v0,
        "Tt2_K": tt2,
        "T2_K": t2,
        "p2_Pa": p2,
        "M4": m4,
        "Tt4_K": tmax,
        "pt4_Pa": pt4,
        "f": f,
        "NPR": npr,
        "Ve_m_s": ve,
        "Fs_m_s": fs,
        "TSFC_kg_N_s": ct,
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
        raise ValueError("matplotlib is required to plot the scramjet") from exc
    return plt


def write_plot(result: dict[str, float], cycle: dict, out_path: Path) -> None:
    plt = ensure_matplotlib()
    mach = result["M"]
    start = result["Mc"] * 1.02
    end = max(mach * 1.25, start + 1.0)
    xs: list[float] = []
    ys: list[float] = []
    for index in range(N_PLOT):
        point_mach = start + (end - start) * index / (N_PLOT - 1)
        try:
            point = solution(mach=point_mach, **cycle)
        except ValueError:
            continue
        xs.append(point_mach)
        ys.append(point["Fs_m_s"])
    if len(xs) < 2:
        raise ValueError("could not build a Mach sweep")
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(xs, ys, color="#1a5276", linewidth=1.8, label="specific thrust")
    ax.plot(mach, result["Fs_m_s"], "s", color="#1a5276", markersize=7, label="operating Mach")
    ax.set_xlabel("flight Mach")
    ax.set_ylabel("specific thrust (m/s)")
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


def emit(result: dict[str, float], freestream_source: str, altitude: float | None, sources: dict[str, str], graph: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    for key in (
        "M",
        "Mc",
        "T0_K",
        "p0_Pa",
        "V0_m_s",
        "Tt2_K",
        "T2_K",
        "p2_Pa",
        "M4",
        "Tt4_K",
        "f",
        "NPR",
        "Ve_m_s",
        "Fs_m_s",
        "TSFC_kg_N_s",
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


def run_check() -> int:
    ram = load_ram()
    gamma = 1.4
    cp = ram.default_cp(gamma)
    point = solution(6.0, 2.0, 220.0, 2000.0, 2500.0, gamma, cp, ram.DEFAULT_HEATING_VALUE, ram.R_AIR)
    tt2 = 220.0 * ram.stagnation_temperature_ratio(6.0, gamma)
    fuel = ram.fuel_air_ratio(cp, 2500.0, tt2, ram.DEFAULT_HEATING_VALUE)
    if abs(point["f"] - fuel) > CHECK_TOL * max(1.0, abs(fuel)):
        return fail("fuel-air ratio")
    thrust = ram.specific_thrust(point["f"], point["Ve_m_s"], point["V0_m_s"])
    if abs(point["Fs_m_s"] - thrust) > CHECK_TOL * max(1.0, abs(thrust)):
        return fail("specific thrust")
    if abs(point["TSFC_kg_N_s"] - ram.tsfc(point["f"], point["Fs_m_s"])) > 1e-12:
        return fail("tsfc")
    if point["M4"] >= point["Mc"]:
        return fail("heat addition did not slow the combustor")
    try:
        solution(6.0, 1.0, 220.0, 2000.0, 2500.0, gamma, cp, ram.DEFAULT_HEATING_VALUE, ram.R_AIR)
        return fail("combustor Mach 1 was accepted")
    except ValueError:
        pass
    try:
        solution(1.5, 2.0, 220.0, 2000.0, 2500.0, gamma, cp, ram.DEFAULT_HEATING_VALUE, ram.R_AIR)
        return fail("flight Mach below combustor Mach was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "scram.png"
        code, text, err = capture(
            [
                "--mach",
                "6",
                "--combustor-mach",
                "2",
                "--tmax",
                "2500",
                "--temperature",
                "220",
                "--pressure",
                "2000",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "Fs_m_s:" not in text or "f:" not in text or "Mc:" not in text:
            return fail("stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
    print("check: pass")
    print_kv("Fs_m_s", point["Fs_m_s"])
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
    parser = argparse.ArgumentParser(description="Ideal scramjet Brayton cycle.")
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number")
    parser.add_argument("--combustor-mach", type=float, default=None, help="combustor entrance Mach, > 1")
    parser.add_argument("--tmax", type=float, default=None, help="combustor exit total temperature Tt4 [K]")
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--pressure", type=float, default=None)
    parser.add_argument("--heating-value", type=float, default=None)
    parser.add_argument("--cp", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    missing = [
        flag
        for flag, value in (("--mach", args.mach), ("--combustor-mach", args.combustor_mach), ("--tmax", args.tmax))
        if value is None
    ]
    if missing:
        print("error: requires --mach, --combustor-mach, --tmax, and a freestream path; missing " + ", ".join(missing), file=sys.stderr)
        return 2
    ram = load_ram()
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
            atmosphere, require_altitude = ram.load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            temperature = float(state["T"])
            pressure = float(state["p"])
            freestream_source = "altitude"
            altitude = float(state["Z"])
        else:
            ram.require_positive("temperature", args.temperature)
            ram.require_positive("pressure", args.pressure)
            temperature = args.temperature
            pressure = args.pressure
            freestream_source = "temperature_pressure"
        if args.gamma is None:
            gamma = ram.DEFAULT_GAMMA
            gamma_source = "default"
        else:
            ram.require_gamma(args.gamma)
            gamma = args.gamma
            gamma_source = "user"
        if args.cp is None:
            cp = ram.default_cp(gamma)
            cp_source = "gamma_air_R"
        else:
            ram.require_positive("cp", args.cp)
            cp = args.cp
            cp_source = "user"
        if args.heating_value is None:
            heating = ram.DEFAULT_HEATING_VALUE
            heating_source = "default"
        else:
            ram.require_positive("heating value", args.heating_value)
            heating = args.heating_value
            heating_source = "user"
        cycle = dict(
            combustor_mach=args.combustor_mach,
            temperature=temperature,
            pressure=pressure,
            tmax=args.tmax,
            gamma=gamma,
            cp=cp,
            heating_value=heating,
            gas_constant=ram.R_AIR,
        )
        result = solution(mach=args.mach, **cycle)
        out_path = Path(args.out) if args.out else SKILL_DIR / "scramjet_ideal_cycle.png"
        out_path = out_path.resolve()
        write_plot(result, cycle, out_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, altitude, {"gamma": gamma_source, "cp": cp_source, "heating": heating_source}, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
