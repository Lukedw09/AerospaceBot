#!/usr/bin/env python3
"""Design-point separate-stream turbofan.

Fan and core compressors use compressor_temperature_ratio_efficiency.
Core pressure ratio is turbofan_core_pressure_ratio. Shaft work is
turbofan_shaft_work. Thrust, TSFC, and efficiencies are the turbofan records.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Separate-stream turbofan"
N_PLOT = 81

SKILL_DIR = Path(__file__).resolve().parent
CORE_DIR = SKILL_DIR.parent / "PROP - NonidealTurbojet"


def load_core():
    folder = str(CORE_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import nonideal_turbojet as core

    return core


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def solution(
    mach: float,
    temperature: float,
    pressure: float,
    tit: float,
    opr: float,
    bpr: float,
    pi_f: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
    pi_d: float = 1.0,
    eta_f: float = 1.0,
    eta_c: float = 1.0,
    eta_t: float = 1.0,
    eta_m: float = 1.0,
    eta_b: float = 1.0,
    pi_b: float = 1.0,
    eta_n: float = 1.0,
    match_fuel: bool = True,
) -> dict[str, float]:
    core = load_core()
    core.require_nonnegative("Mach", mach)
    core.require_positive("temperature", temperature)
    core.require_positive("pressure", pressure)
    core.require_positive("turbine inlet temperature", tit)
    core.require_positive("overall pressure ratio", opr)
    core.require_positive("fan pressure ratio", pi_f)
    if pi_f <= 1.0:
        raise ValueError("fan pressure ratio must be > 1")
    if opr <= pi_f:
        raise ValueError("overall pressure ratio must exceed the fan pressure ratio")
    if not __import__("math").isfinite(bpr) or bpr < 0.0:
        raise ValueError("bypass ratio must be finite and >= 0")
    core.require_gamma(gamma)
    core.require_positive("cp", cp)
    core.require_positive("heating value", heating_value)
    core.require_positive("gas constant", gas_constant)
    core.require_loss_ratio("inlet recovery", pi_d)
    core.require_efficiency("fan efficiency", eta_f)
    core.require_efficiency("core compressor efficiency", eta_c)
    core.require_efficiency("turbine efficiency", eta_t)
    core.require_efficiency("mechanical efficiency", eta_m)
    core.require_efficiency("burner efficiency", eta_b)
    core.require_loss_ratio("burner pressure ratio", pi_b)
    core.require_efficiency("nozzle efficiency", eta_n)

    tau_r = core.stagnation_temperature_ratio(mach, gamma)
    pi_r = core.stagnation_pressure_ratio(tau_r, gamma)
    tt0 = temperature * tau_r
    pt0 = pressure * pi_r
    a0 = core.speed_of_sound(temperature, gamma, gas_constant)
    v0 = mach * a0
    tt2 = tt0
    pt2 = pi_d * pt0

    tau_f = core.compressor_temperature_ratio(pi_f, gamma, eta_f)
    tt13 = tt2 * tau_f
    pt13 = pi_f * pt2
    w_fan = cp * (tt13 - tt2)
    pi_core = opr / pi_f
    tau_c = core.compressor_temperature_ratio(pi_core, gamma, eta_c)
    tt3 = tt13 * tau_c
    pt3 = pi_core * pt13
    w_core = cp * (tt3 - tt2)
    w_shaft = w_core + bpr * w_fan

    tt4 = tit
    fuel = core.fuel_air_ratio(cp, tt4, tt3, eta_b, heating_value)
    pt4 = pi_b * pt3
    f_match = fuel if match_fuel else 0.0
    tau_t = core.turbine_temperature_ratio(w_shaft, f_match, eta_m, cp, tt4)
    pi_t = core.turbine_pressure_ratio(tau_t, eta_t, gamma)
    tt5 = tt4 * tau_t
    pt5 = pi_t * pt4

    npr_f = pt13 / pressure
    npr_c = pt5 / pressure
    vf = core.nozzle_exit_velocity(eta_n, cp, tt13, npr_f, gamma)
    ve = core.nozzle_exit_velocity(eta_n, cp, tt5, npr_c, gamma)
    fs_core = (1.0 + fuel) * ve - v0
    fs_fan = vf - v0
    fs = ((1.0 + fuel) * ve + bpr * vf) / (1.0 + bpr) - v0
    if fs <= 0.0:
        raise ValueError("specific thrust is not positive at this flight condition")
    ct = fuel / (fs * (1.0 + bpr))
    kinetic = (1.0 + fuel) * ve * ve + bpr * vf * vf - (1.0 + bpr) * v0 * v0
    eta_th = kinetic / (2.0 * fuel * heating_value)
    if v0 == 0.0:
        eta_p = 0.0
        eta_o = 0.0
    else:
        eta_p = 2.0 * v0 * fs / (kinetic / (1.0 + bpr))
        eta_o = fs * v0 * (1.0 + bpr) / (fuel * heating_value)

    return {
        "M": mach,
        "T0_K": temperature,
        "p0_Pa": pressure,
        "rho0_kg_m3": pressure / (gas_constant * temperature),
        "a0_m_s": a0,
        "V0_m_s": v0,
        "pi_d": pi_d,
        "Tt2_K": tt2,
        "pt2_Pa": pt2,
        "bpr": bpr,
        "pi_f": pi_f,
        "eta_f": eta_f,
        "eta_t": eta_t,
        "eta_m": eta_m,
        "eta_n": eta_n,
        "tau_f": tau_f,
        "Tt13_K": tt13,
        "pt13_Pa": pt13,
        "w_fan_J_kg": w_fan,
        "pi_core": pi_core,
        "eta_c": eta_c,
        "tau_c": tau_c,
        "Tt3_K": tt3,
        "pt3_Pa": pt3,
        "w_core_J_kg": w_core,
        "w_shaft_J_kg": w_shaft,
        "Tt4_K": tt4,
        "f": fuel,
        "eta_b": eta_b,
        "pi_b": pi_b,
        "tau_t": tau_t,
        "pi_t": pi_t,
        "Tt5_K": tt5,
        "pt5_Pa": pt5,
        "NPR_fan": npr_f,
        "NPR_core": npr_c,
        "Vf_m_s": vf,
        "Ve_m_s": ve,
        "Fs_core_m_s": fs_core,
        "Fs_fan_m_s": fs_fan,
        "Fs_m_s": fs,
        "TSFC_kg_N_s": ct,
        "eta_th": eta_th,
        "eta_p": eta_p,
        "eta_o": eta_o,
        "gamma": gamma,
        "cp_J_kgK": cp,
        "R_J_kgK": gas_constant,
        "Q_J_kg": heating_value,
        "match_fuel": 1.0 if match_fuel else 0.0,
        "pi_overall": opr,
    }


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the turbofan") from exc
    return plt


def plot_bypass(path: Path, result: dict[str, float], cycle: dict) -> None:
    plt = ensure_matplotlib()
    end = max(8.0, 1.5 * max(result["bpr"], 1.0))
    xs: list[float] = []
    thrust: list[float] = []
    tsfc: list[float] = []
    for i in range(N_PLOT):
        bpr = end * i / (N_PLOT - 1)
        try:
            point = solution(bpr=bpr, **cycle)
        except ValueError:
            continue
        xs.append(bpr)
        thrust.append(point["Fs_m_s"])
        tsfc.append(point["TSFC_kg_N_s"])
    if len(xs) < 2:
        raise ValueError("bypass sweep produced fewer than two valid points")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, thrust, color="#1a5276", linewidth=1.8, label="specific thrust")
    ax.plot(result["bpr"], result["Fs_m_s"], "s", color="#1a5276", markersize=7, zorder=5, label="operating point")
    ax.set_ylabel(r"specific thrust $F_s$ (m/s)")
    ax2 = ax.twinx()
    ax2.plot(xs, tsfc, color="#b9770e", linewidth=1.5, label="TSFC")
    ax2.plot(result["bpr"], result["TSFC_kg_N_s"], "s", color="#b9770e", markersize=6, zorder=5)
    ax2.set_ylabel(r"TSFC (kg/(N·s))")
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("bypass ratio")
    ax.grid(True, alpha=0.35)
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(result: dict[str, float], freestream_source: str, altitude: float | None, gamma_source: str, cp_source: str, heating_source: str, path: Path) -> None:
    print_kv("assumptions", (
        "design-point separate-stream turbofan; fan processes the whole inlet stream; "
        "core pressure ratio is overall/fan from turbofan_core_pressure_ratio; "
        "shaft work per core air is turbofan_shaft_work; "
        "specific thrust is turbofan_specific_thrust per inlet airflow; "
        "TSFC is turbofan_tsfc; no mixer; no afterburner; fully expanded nozzles"
    ))
    print_kv("model", "design-point separate-stream turbofan")
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("match_fuel", "yes" if result["match_fuel"] else "no")
    for key in (
        "M", "T0_K", "p0_Pa", "V0_m_s", "pi_d", "bpr", "pi_f", "eta_f", "pi_core", "eta_c", "pi_overall",
        "Tt13_K", "Tt3_K", "Tt4_K", "eta_b", "pi_b", "eta_t", "eta_m", "Tt5_K", "eta_n", "f",
        "w_fan_J_kg", "w_core_J_kg", "w_shaft_J_kg",
        "Vf_m_s", "Ve_m_s", "Fs_core_m_s", "Fs_fan_m_s", "Fs_m_s", "TSFC_kg_N_s",
        "eta_th", "eta_p", "eta_o", "gamma",
    ):
        print_kv(key, result[key])
    print_kv("gamma_source", gamma_source)
    print_kv("cp_J_kgK", result["cp_J_kgK"])
    print_kv("cp_source", cp_source)
    print_kv("Q_J_kg", result["Q_J_kg"])
    print_kv("Q_source", heating_source)
    print_kv("graph", str(path))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design-point separate-stream turbofan")
    parser.add_argument("--mach", type=float, default=None)
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--pressure", type=float, default=None)
    parser.add_argument("--tit", type=float, default=None)
    parser.add_argument("--opr", type=float, default=None, help="overall pressure ratio pt3/pt2")
    parser.add_argument("--bpr", type=float, default=None, help="bypass ratio mdot_fan/mdot_core")
    parser.add_argument("--fpr", type=float, default=None, help="fan pressure ratio")
    parser.add_argument("--pi-d", type=float, default=1.0)
    parser.add_argument("--eta-f", type=float, default=1.0)
    parser.add_argument("--eta-c", type=float, default=1.0)
    parser.add_argument("--eta-t", type=float, default=1.0)
    parser.add_argument("--eta-m", type=float, default=1.0)
    parser.add_argument("--eta-b", type=float, default=1.0)
    parser.add_argument("--pi-b", type=float, default=1.0)
    parser.add_argument("--eta-n", type=float, default=1.0)
    parser.add_argument("--neglect-fuel-match", action="store_true")
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
        for flag, value in (("--mach", args.mach), ("--tit", args.tit), ("--opr", args.opr), ("--bpr", args.bpr), ("--fpr", args.fpr))
        if value is None
    ]
    if missing:
        print("error: requires --mach, --tit, --opr, --bpr, --fpr, and a freestream path; missing " + ", ".join(missing), file=sys.stderr)
        return 2
    core = load_core()
    try:
        temperature, pressure, freestream_source, altitude = core.resolve_freestream(args)
        gamma, gamma_source, cp, cp_source, heating, heating_source = core.gas_choices(args)
        cycle = dict(
            mach=args.mach,
            temperature=temperature,
            pressure=pressure,
            tit=args.tit,
            opr=args.opr,
            pi_f=args.fpr,
            gamma=gamma,
            cp=cp,
            heating_value=heating,
            gas_constant=core.R_AIR,
            pi_d=args.pi_d,
            eta_f=args.eta_f,
            eta_c=args.eta_c,
            eta_t=args.eta_t,
            eta_m=args.eta_m,
            eta_b=args.eta_b,
            pi_b=args.pi_b,
            eta_n=args.eta_n,
            match_fuel=not args.neglect_fuel_match,
        )
        result = solution(bpr=args.bpr, **cycle)
        out_path = Path(args.out) if args.out else SKILL_DIR / "separate_stream_turbofan.png"
        out_path = out_path.resolve()
        plot_bypass(out_path, result, cycle)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, altitude, gamma_source, cp_source, heating_source, out_path)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    core = load_core()
    gamma = 1.4
    cp = core.default_cp(gamma)
    point = solution(
        0.8, 216.65, 19330.0, 1600.0, 25.0, 6.0, 1.6, gamma, cp, core.DEFAULT_HEATING_VALUE, core.R_AIR,
        eta_f=0.9, eta_c=0.88, eta_t=0.9, eta_b=0.99, pi_b=0.96, pi_d=0.98,
    )
    split = (point["Fs_core_m_s"] + point["bpr"] * point["Fs_fan_m_s"]) / (1.0 + point["bpr"])
    if near(point["Fs_m_s"], split, "thrust split"):
        return 1
    if near(point["TSFC_kg_N_s"], point["f"] / (point["Fs_m_s"] * (1.0 + point["bpr"])), "TSFC"):
        return 1
    if near(point["w_shaft_J_kg"], point["w_core_J_kg"] + point["bpr"] * point["w_fan_J_kg"], "shaft work"):
        return 1
    if near(point["pi_core"], point["pi_overall"] / point["pi_f"], "core pressure ratio"):
        return 1
    if abs(point["eta_o"] - point["eta_th"] * point["eta_p"]) > CHECK_TOL * max(1.0, abs(point["eta_o"])):
        return fail("eta_o is not eta_th*eta_p")
    zero_bypass = solution(
        0.8, 216.65, 19330.0, 1600.0, 25.0, 0.0, 1.6, gamma, cp, core.DEFAULT_HEATING_VALUE, core.R_AIR,
    )
    if near(zero_bypass["Fs_m_s"], (1.0 + zero_bypass["f"]) * zero_bypass["Ve_m_s"] - zero_bypass["V0_m_s"], "zero bypass"):
        return 1

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out, err = _Capture(), _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as folder_name:
        png = Path(folder_name) / "separate_stream_turbofan.png"
        code, text, err = capture(
            ["--mach", "0.8", "--alt", "11000", "--tit", "1600", "--opr", "30", "--bpr", "5", "--fpr", "1.5", "--out", str(png)]
        )
        if code != 0:
            return fail(f"cli failed: {err}")
        if "Fs_core_m_s:" not in text or "Fs_fan_m_s:" not in text or "TSFC_kg_N_s:" not in text:
            return fail("cli omitted thrust split or TSFC")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
