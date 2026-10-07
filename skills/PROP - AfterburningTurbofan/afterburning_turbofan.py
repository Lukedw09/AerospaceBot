#!/usr/bin/env python3
"""Separate-stream turbofan with an afterburner on the core only.

The bypass stream stays dry. Core reheat reuses afterburner_fuel_air_ratio
and the reheat nozzle from PROP - AfterburningTurbojet. There is no mixer.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Afterburning turbofan"
N_PLOT = 41

SKILL_DIR = Path(__file__).resolve().parent
FAN_DIR = SKILL_DIR.parent / "PROP - SeparateStreamTurbofan"
AB_DIR = SKILL_DIR.parent / "PROP - AfterburningTurbojet"

ASSUMPTIONS = (
    "separate-stream turbofan with an afterburner on the core stream only; "
    "the bypass stream stays dry; there is no mixer; "
    "dry station set is PROP - SeparateStreamTurbofan; "
    "core reheat uses afterburner_fuel_air_ratio and the fully expanded reheat nozzle "
    "from PROP - AfterburningTurbojet; "
    "reheated specific thrust is per inlet airflow: "
    "((1+f+f_ab)*Ve_reheat + bpr*Vf)/(1+bpr) - V0; "
    "TSFC = (f+f_ab)/(Fs*(1+bpr)); "
    "optional efficiencies match those two skills"
)


def _import(folder: Path, name: str):
    text = str(folder)
    if text not in sys.path:
        sys.path.insert(0, text)
    return __import__(name)


def load_fan():
    return _import(FAN_DIR, "separate_stream_turbofan")


def load_ab():
    return _import(AB_DIR, "afterburning_turbojet")


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
    tt7: float,
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
    eta_ab: float = 1.0,
    pi_ab: float = 1.0,
    match_fuel: bool = True,
) -> dict[str, float | str]:
    fan_mod = load_fan()
    ab = load_ab()
    dry = fan_mod.solution(
        mach,
        temperature,
        pressure,
        tit,
        opr,
        bpr,
        pi_f,
        gamma,
        cp,
        heating_value,
        gas_constant,
        pi_d=pi_d,
        eta_f=eta_f,
        eta_c=eta_c,
        eta_t=eta_t,
        eta_m=eta_m,
        eta_b=eta_b,
        pi_b=pi_b,
        eta_n=eta_n,
        match_fuel=match_fuel,
    )
    core = ab.load_core()
    core.require_loss_ratio("afterburner pressure ratio", pi_ab)
    fab = ab.afterburner_fuel(core, dry["f"], cp, tt7, dry["Tt5_K"], eta_ab, heating_value)
    fuel_total = dry["f"] + fab
    pt7 = pi_ab * dry["pt5_Pa"]
    wet = ab.reheat_nozzle(
        core,
        tt7,
        pt7,
        pressure,
        fuel_total,
        dry["V0_m_s"],
        eta_n,
        cp,
        gamma,
        gas_constant,
        "expanded",
    )
    ve = float(wet["Ve_m_s"])
    vf = float(dry["Vf_m_s"])
    v0 = float(dry["V0_m_s"])
    fs = ((1.0 + fuel_total) * ve + bpr * vf) / (1.0 + bpr) - v0
    if fs <= 0.0:
        raise ValueError("reheated specific thrust is not positive")
    tsfc = fuel_total / (fs * (1.0 + bpr))
    return {
        "M": dry["M"],
        "T0_K": dry["T0_K"],
        "p0_Pa": dry["p0_Pa"],
        "V0_m_s": v0,
        "Tt4_K": dry["Tt4_K"],
        "pi_overall": dry["pi_overall"],
        "bpr": bpr,
        "pi_f": pi_f,
        "Tt5_K": dry["Tt5_K"],
        "Tt7_K": tt7,
        "f": dry["f"],
        "f_ab": fab,
        "f_total": fuel_total,
        "Vf_m_s": vf,
        "Ve_dry_m_s": dry["Ve_m_s"],
        "Ve_reheat_m_s": ve,
        "Fs_dry_m_s": dry["Fs_m_s"],
        "Fs_reheat_m_s": fs,
        "TSFC_kg_N_s": tsfc,
        "eta_ab": eta_ab,
        "pi_ab": pi_ab,
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
        raise ValueError("matplotlib is required to plot the afterburning turbofan") from exc
    return plt


def write_plot(result: dict[str, float | str], cycle: dict, out_path: Path) -> None:
    plt = ensure_matplotlib()
    tt5 = float(result["Tt5_K"])
    tt7 = float(result["Tt7_K"])
    start = tt5 + max(20.0, 0.02 * tt5)
    end = max(tt7 * 1.15, start + 400.0)
    xs: list[float] = []
    ys: list[float] = []
    for index in range(N_PLOT):
        point_t = start + (end - start) * index / (N_PLOT - 1)
        try:
            point = solution(tt7=point_t, **cycle)
        except ValueError:
            continue
        xs.append(point_t)
        ys.append(float(point["Fs_reheat_m_s"]))
    if len(xs) < 2:
        raise ValueError("could not build an afterburner-temperature sweep")
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(xs, ys, color="#1a5276", linewidth=1.8, label="specific thrust")
    ax.plot(tt7, float(result["Fs_reheat_m_s"]), "s", color="#1a5276", markersize=7, label="operating Tt7")
    ax.set_xlabel("afterburner temperature (K)")
    ax.set_ylabel("specific thrust per inlet airflow (m/s)")
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


def emit(result: dict[str, float | str], freestream_source: str, altitude: float | None, sources: dict[str, str], graph: Path) -> None:
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
        "pi_overall",
        "bpr",
        "pi_f",
        "Tt5_K",
        "Tt7_K",
        "f",
        "f_ab",
        "f_total",
        "Vf_m_s",
        "Ve_dry_m_s",
        "Ve_reheat_m_s",
        "Fs_dry_m_s",
        "Fs_reheat_m_s",
        "TSFC_kg_N_s",
        "eta_ab",
        "pi_ab",
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
    fan_mod = load_fan()
    ab = load_ab()
    core = ab.load_core()
    gamma = 1.4
    cp = core.default_cp(gamma)
    heating = core.DEFAULT_HEATING_VALUE
    dry = fan_mod.solution(0.8, 220.0, 20000.0, 1600.0, 20.0, 4.0, 1.6, gamma, cp, heating, core.R_AIR)
    tt7 = dry["Tt5_K"] + 400.0
    point = solution(0.8, 220.0, 20000.0, 1600.0, 20.0, 4.0, 1.6, tt7, gamma, cp, heating, core.R_AIR)
    fab = ab.afterburner_fuel(core, dry["f"], cp, tt7, dry["Tt5_K"], 1.0, heating)
    if abs(float(point["f_ab"]) - fab) > CHECK_TOL * max(1.0, abs(fab)):
        return fail("afterburner fuel")
    if abs(float(point["Fs_dry_m_s"]) - dry["Fs_m_s"]) > 1e-6:
        return fail("dry thrust")
    fuel_total = dry["f"] + fab
    ve = float(point["Ve_reheat_m_s"])
    fs = ((1.0 + fuel_total) * ve + 4.0 * dry["Vf_m_s"]) / 5.0 - dry["V0_m_s"]
    if abs(float(point["Fs_reheat_m_s"]) - fs) > CHECK_TOL * max(1.0, abs(fs)):
        return fail("reheat thrust")
    want_tsfc = fuel_total / (fs * 5.0)
    if abs(float(point["TSFC_kg_N_s"]) - want_tsfc) > CHECK_TOL * max(1.0, abs(want_tsfc)):
        return fail("tsfc")
    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "abfan.png"
        code, text, err = capture(
            [
                "--mach",
                "0.8",
                "--tit",
                "1600",
                "--opr",
                "20",
                "--bpr",
                "4",
                "--fpr",
                "1.6",
                "--t7",
                f"{tt7:.8g}",
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
        for key in ("Fs_dry_m_s:", "Fs_reheat_m_s:", "f:", "f_ab:", "TSFC_kg_N_s:"):
            if key not in text:
                return fail(f"missing {key}")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
    print("check: pass")
    print_kv("Fs_reheat_m_s", point["Fs_reheat_m_s"])
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
    parser = argparse.ArgumentParser(description="Afterburning separate-stream turbofan.")
    parser.add_argument("--mach", type=float, default=None)
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--pressure", type=float, default=None)
    parser.add_argument("--tit", type=float, default=None)
    parser.add_argument("--opr", type=float, default=None)
    parser.add_argument("--bpr", type=float, default=None)
    parser.add_argument("--fpr", type=float, default=None)
    parser.add_argument("--t7", type=float, default=None, help="core afterburner exit total temperature [K]")
    parser.add_argument("--pi-d", type=float, default=1.0)
    parser.add_argument("--eta-f", type=float, default=1.0)
    parser.add_argument("--eta-c", type=float, default=1.0)
    parser.add_argument("--eta-t", type=float, default=1.0)
    parser.add_argument("--eta-m", type=float, default=1.0)
    parser.add_argument("--eta-b", type=float, default=1.0)
    parser.add_argument("--pi-b", type=float, default=1.0)
    parser.add_argument("--eta-n", type=float, default=1.0)
    parser.add_argument("--eta-ab", type=float, default=1.0)
    parser.add_argument("--pi-ab", type=float, default=1.0)
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
        for flag, value in (
            ("--mach", args.mach),
            ("--tit", args.tit),
            ("--opr", args.opr),
            ("--bpr", args.bpr),
            ("--fpr", args.fpr),
            ("--t7", args.t7),
        )
        if value is None
    ]
    if missing:
        print(
            "error: requires --mach, --tit, --opr, --bpr, --fpr, --t7, and a freestream path; missing "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 2
    fan_mod = load_fan()
    core = load_ab().load_core()
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
            atmosphere, require_altitude = core.load_atmosphere()
            state = atmosphere(require_altitude(args.alt, "--alt"))
            temperature = float(state["T"])
            pressure = float(state["p"])
            freestream_source = "altitude"
            altitude = float(state["Z"])
        else:
            core.require_positive("temperature", args.temperature)
            core.require_positive("pressure", args.pressure)
            temperature = args.temperature
            pressure = args.pressure
            freestream_source = "temperature_pressure"
        if args.gamma is None:
            gamma = core.DEFAULT_GAMMA
            gamma_source = "default"
        else:
            core.require_gamma(args.gamma)
            gamma = args.gamma
            gamma_source = "user"
        if args.cp is None:
            cp = core.default_cp(gamma)
            cp_source = "gamma_air_R"
        else:
            core.require_positive("cp", args.cp)
            cp = args.cp
            cp_source = "user"
        if args.heating_value is None:
            heating = core.DEFAULT_HEATING_VALUE
            heating_source = "default"
        else:
            core.require_positive("heating value", args.heating_value)
            heating = args.heating_value
            heating_source = "user"
        cycle = dict(
            mach=args.mach,
            temperature=temperature,
            pressure=pressure,
            tit=args.tit,
            opr=args.opr,
            bpr=args.bpr,
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
            eta_ab=args.eta_ab,
            pi_ab=args.pi_ab,
            match_fuel=not args.neglect_fuel_match,
        )
        result = solution(tt7=args.t7, **cycle)
        out_path = Path(args.out) if args.out else SKILL_DIR / "afterburning_turbofan.png"
        out_path = out_path.resolve()
        write_plot(result, cycle, out_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, altitude, {"gamma": gamma_source, "cp": cp_source, "heating": heating_source}, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
