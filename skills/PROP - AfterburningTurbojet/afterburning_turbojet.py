#!/usr/bin/env python3
"""Design-point afterburning turbojet.

The dry core is PROP - NonidealTurbojet. Reheat uses
afterburner_fuel_air_ratio and afterburner_exit_total_pressure.
The fully expanded exit uses nozzle_exit_velocity_efficiency.
A convergent choked exit uses sonic_pressure, sonic_temperature, and
specific_thrust_with_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Afterburning turbojet"
N_PLOT = 121

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


def afterburner_fuel(core, fuel: float, cp: float, tt7: float, tt6: float, eta_ab: float, heating: float) -> float:
    """afterburner_fuel_air_ratio."""
    core.require_efficiency("afterburner efficiency", eta_ab)
    if tt7 <= tt6:
        raise ValueError("afterburner exit temperature must exceed turbine exit temperature")
    denom = eta_ab * heating - cp * tt7
    if denom <= 0.0:
        raise ValueError("eta_ab*Q must exceed cp*Tt7")
    return (1.0 + fuel) * cp * (tt7 - tt6) / denom


def sonic_pressure_ratio(gamma: float) -> float:
    """sonic_pressure: p*/pt."""
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def sonic_temperature_ratio(gamma: float) -> float:
    """sonic_temperature: T*/Tt."""
    return 2.0 / (gamma + 1.0)


def reheat_nozzle(
    core,
    tt: float,
    pt: float,
    p0: float,
    fuel_total: float,
    v0: float,
    eta_n: float,
    cp: float,
    gamma: float,
    gas_constant: float,
    nozzle: str,
) -> dict[str, float | str]:
    npr = pt / p0
    choked = False
    if nozzle == "expanded":
        ve = core.nozzle_exit_velocity(eta_n, cp, tt, npr, gamma)
        te = core.nozzle_exit_temperature(tt, npr, gamma)
        pe = p0
        area_specific = 0.0
        fs = (1.0 + fuel_total) * ve - v0
    elif nozzle == "convergent":
        critical = 1.0 / sonic_pressure_ratio(gamma)
        if npr + 1e-12 >= critical:
            choked = True
            pe = pt * sonic_pressure_ratio(gamma)
            te = tt * sonic_temperature_ratio(gamma)
            ve = math.sqrt(eta_n * gamma * gas_constant * te)
            rho_e = pe / (gas_constant * te)
            area_specific = (1.0 + fuel_total) / (rho_e * ve)
            fs = (1.0 + fuel_total) * ve - v0 + (pe - p0) * area_specific
        else:
            ve = core.nozzle_exit_velocity(eta_n, cp, tt, npr, gamma)
            te = core.nozzle_exit_temperature(tt, npr, gamma)
            pe = p0
            area_specific = 0.0
            fs = (1.0 + fuel_total) * ve - v0
    else:
        raise ValueError("nozzle must be expanded or convergent")
    if fs <= 0.0:
        raise ValueError("reheat specific thrust is not positive")
    momentum = (1.0 + fuel_total) * ve - v0
    return {
        "NPR": npr,
        "Ve_m_s": ve,
        "Te_K": te,
        "pe_Pa": pe,
        "As_m_s_kg": area_specific,
        "Fs_m_s": fs,
        "Fs_momentum_m_s": momentum,
        "choked": "yes" if choked else "no",
    }


def efficiencies(fuel_total: float, ve: float, v0: float, fs_momentum: float, heating: float) -> tuple[float, float, float]:
    eta_th = ((1.0 + fuel_total) * ve * ve - v0 * v0) / (2.0 * fuel_total * heating)
    if v0 == 0.0:
        return eta_th, 0.0, 0.0
    denom = (1.0 + fuel_total) * ve * ve - v0 * v0
    eta_p = 2.0 * v0 * fs_momentum / denom
    eta_o = fs_momentum * v0 / (fuel_total * heating)
    return eta_th, eta_p, eta_o


def solution(
    mach: float,
    temperature: float,
    pressure: float,
    tit: float,
    opr: float,
    tt7: float,
    gamma: float,
    cp: float,
    heating_value: float,
    gas_constant: float,
    pi_d: float = 1.0,
    eta_c: float = 1.0,
    eta_t: float = 1.0,
    eta_m: float = 1.0,
    eta_b: float = 1.0,
    pi_b: float = 1.0,
    eta_n: float = 1.0,
    eta_ab: float = 1.0,
    pi_ab: float = 1.0,
    match_fuel: bool = True,
    nozzle: str = "expanded",
) -> dict[str, float | str]:
    core = load_core()
    core.require_loss_ratio("afterburner pressure ratio", pi_ab)
    dry = core.solution(
        mach,
        temperature,
        pressure,
        tit,
        opr,
        gamma,
        cp,
        heating_value,
        gas_constant,
        pi_d=pi_d,
        eta_c=eta_c,
        eta_t=eta_t,
        eta_m=eta_m,
        eta_b=eta_b,
        pi_b=pi_b,
        eta_n=eta_n,
        match_fuel=match_fuel,
    )
    tt6 = dry["Tt5_K"]
    pt6 = dry["pt5_Pa"]
    fab = afterburner_fuel(core, dry["f"], cp, tt7, tt6, eta_ab, heating_value)
    pt7 = pi_ab * pt6
    fuel_total = dry["f"] + fab
    wet = reheat_nozzle(
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
        nozzle,
    )
    eta_th, eta_p, eta_o = efficiencies(
        fuel_total,
        float(wet["Ve_m_s"]),
        dry["V0_m_s"],
        float(wet["Fs_momentum_m_s"]),
        heating_value,
    )
    ct = fuel_total / float(wet["Fs_m_s"])
    out: dict[str, float | str] = dict(dry)
    out.update(wet)
    out["Tt6_K"] = tt6
    out["pt6_Pa"] = pt6
    out["Tt7_K"] = tt7
    out["pt7_Pa"] = pt7
    out["eta_ab"] = eta_ab
    out["pi_ab"] = pi_ab
    out["f_ab"] = fab
    out["f_total"] = fuel_total
    out["Fs_dry_m_s"] = dry["Fs_m_s"]
    out["TSFC_dry_kg_N_s"] = dry["TSFC_kg_N_s"]
    out["TSFC_kg_N_s"] = ct
    out["thrust_ratio"] = float(wet["Fs_m_s"]) / dry["Fs_m_s"]
    out["eta_th"] = eta_th
    out["eta_p"] = eta_p
    out["eta_o"] = eta_o
    out["nozzle"] = nozzle
    return out


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the afterburning turbojet") from exc
    return plt


def plot_reheat(path: Path, result: dict[str, float | str], args_cycle: dict) -> None:
    plt = ensure_matplotlib()
    tt6 = float(result["Tt6_K"])
    tt7 = float(result["Tt7_K"])
    end = max(tt7 * 1.15, tt6 + 200.0)
    start = tt6 + 0.02 * (end - tt6)
    xs: list[float] = []
    ys: list[float] = []
    for i in range(N_PLOT):
        temperature = start + (end - start) * i / (N_PLOT - 1)
        try:
            point = solution(tt7=temperature, **args_cycle)
        except ValueError:
            continue
        xs.append(temperature)
        ys.append(float(point["Fs_m_s"]))
    if len(xs) < 2:
        raise ValueError("afterburner sweep produced fewer than two valid points")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, ys, color="#1a5276", linewidth=1.8, label="reheat specific thrust")
    ax.plot(tt7, float(result["Fs_m_s"]), "s", color="#1a5276", markersize=7, zorder=5, label="operating point")
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel(r"afterburner exit temperature $T_{t7}$ (K)")
    ax.set_ylabel(r"specific thrust $F_s$ (m/s)")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(result: dict[str, float | str], freestream_source: str, altitude: float | None, gamma_source: str, cp_source: str, heating_source: str, path: Path) -> None:
    print_kv("assumptions", (
        "design-point afterburning turbojet; dry core is the nonideal turbojet; "
        "f_ab from afterburner_fuel_air_ratio; pt7 from afterburner_exit_total_pressure; "
        "fully expanded exit uses nozzle_exit_velocity_efficiency; "
        "convergent choked exit uses sonic_pressure, sonic_temperature, and "
        "specific_thrust_with_pressure; efficiencies use the momentum thrust; "
        "a real afterburning nozzle is variable-area"
    ))
    print_kv("model", "design-point afterburning turbojet")
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    if result["nozzle"] == "convergent":
        print_kv(
            "warning_convergent_nozzle",
            "real afterburning nozzles are variable-area; this exit is the choked or unchoked convergent state at the mass-flow area",
        )
    for key in (
        "M",
        "T0_K",
        "p0_Pa",
        "V0_m_s",
        "pi_d",
        "Tt4_K",
        "Tt5_K",
        "Tt6_K",
        "Tt7_K",
        "pt7_Pa",
        "f",
        "f_ab",
        "f_total",
        "eta_ab",
        "pi_ab",
        "nozzle",
        "choked",
        "NPR",
        "Ve_m_s",
        "Te_K",
        "pe_Pa",
        "As_m_s_kg",
        "Fs_dry_m_s",
        "Fs_momentum_m_s",
        "Fs_m_s",
        "thrust_ratio",
        "TSFC_dry_kg_N_s",
        "TSFC_kg_N_s",
        "eta_th",
        "eta_p",
        "eta_o",
        "gamma",
    ):
        print_kv(key, result[key])
    print_kv("gamma_source", gamma_source)
    print_kv("cp_J_kgK", result["cp_J_kgK"])
    print_kv("cp_source", cp_source)
    print_kv("Q_J_kg", result["Q_J_kg"])
    print_kv("Q_source", heating_source)
    print_kv("graph", str(path))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design-point afterburning turbojet")
    parser.add_argument("--mach", type=float, default=None)
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--pressure", type=float, default=None)
    parser.add_argument("--tit", type=float, default=None)
    parser.add_argument("--opr", type=float, default=None)
    parser.add_argument("--t7", type=float, default=None, help="afterburner exit total temperature Tt7 [K]")
    parser.add_argument("--pi-d", type=float, default=1.0)
    parser.add_argument("--eta-c", type=float, default=1.0)
    parser.add_argument("--eta-t", type=float, default=1.0)
    parser.add_argument("--eta-m", type=float, default=1.0)
    parser.add_argument("--eta-b", type=float, default=1.0)
    parser.add_argument("--pi-b", type=float, default=1.0)
    parser.add_argument("--eta-n", type=float, default=1.0)
    parser.add_argument("--eta-ab", type=float, default=1.0)
    parser.add_argument("--pi-ab", type=float, default=1.0)
    parser.add_argument("--neglect-fuel-match", action="store_true")
    parser.add_argument("--nozzle", choices=("expanded", "convergent"), default="expanded")
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
    missing = [flag for flag, value in (("--mach", args.mach), ("--tit", args.tit), ("--opr", args.opr), ("--t7", args.t7)) if value is None]
    if missing:
        print("error: requires --mach, --tit, --opr, --t7, and a freestream path; missing " + ", ".join(missing), file=sys.stderr)
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
            gamma=gamma,
            cp=cp,
            heating_value=heating,
            gas_constant=core.R_AIR,
            pi_d=args.pi_d,
            eta_c=args.eta_c,
            eta_t=args.eta_t,
            eta_m=args.eta_m,
            eta_b=args.eta_b,
            pi_b=args.pi_b,
            eta_n=args.eta_n,
            eta_ab=args.eta_ab,
            pi_ab=args.pi_ab,
            match_fuel=not args.neglect_fuel_match,
            nozzle=args.nozzle,
        )
        result = solution(tt7=args.t7, **cycle)
        out_path = Path(args.out) if args.out else SKILL_DIR / "afterburning_turbojet.png"
        out_path = out_path.resolve()
        plot_reheat(out_path, result, cycle)
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
    cp = 1000.0
    fab = afterburner_fuel(core, 0.0, cp, 2000.0, 1000.0, 1.0, 42.0e6)
    if near(fab, 1.0 / 40.0, "afterburner fuel"):
        return 1
    point = solution(
        0.8,
        216.65,
        19330.0,
        1600.0,
        20.0,
        2100.0,
        gamma,
        core.default_cp(gamma),
        core.DEFAULT_HEATING_VALUE,
        core.R_AIR,
        eta_c=0.88,
        eta_t=0.9,
        eta_b=0.99,
        pi_b=0.96,
        pi_d=0.98,
        eta_ab=0.9,
        pi_ab=0.95,
    )
    if float(point["f_ab"]) <= 0.0:
        return fail("afterburner fuel not positive")
    if float(point["f_ab"]) <= float(point["f"]):
        return fail("reheat fuel should exceed core fuel at this temperature rise")
    if float(point["Fs_m_s"]) <= float(point["Fs_dry_m_s"]):
        return fail("reheat specific thrust should exceed the dry value")
    if near(float(point["thrust_ratio"]), float(point["Fs_m_s"]) / float(point["Fs_dry_m_s"]), "thrust ratio"):
        return 1
    dry = core.solution(
        0.8, 216.65, 19330.0, 1600.0, 20.0, gamma, core.default_cp(gamma), core.DEFAULT_HEATING_VALUE, core.R_AIR,
        pi_d=0.98, eta_c=0.88, eta_t=0.9, eta_b=0.99, pi_b=0.96,
    )
    if near(float(point["Fs_dry_m_s"]), dry["Fs_m_s"], "dry specific thrust"):
        return 1
    choked = solution(
        0.0, 288.15, 101325.0, 1800.0, 12.0, 2200.0, gamma, core.default_cp(gamma), core.DEFAULT_HEATING_VALUE, core.R_AIR,
        nozzle="convergent",
    )
    if choked["choked"] != "yes":
        return fail("sea-level static convergent nozzle should choke")
    if float(choked["pe_Pa"]) <= 101325.0:
        return fail("choked exit pressure should exceed freestream")
    if float(choked["As_m_s_kg"]) <= 0.0:
        return fail("choked exit area not positive")
    if float(choked["Fs_m_s"]) <= float(choked["Fs_momentum_m_s"]):
        return fail("pressure thrust should raise net specific thrust")

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
        png = Path(folder_name) / "afterburning_turbojet.png"
        code, text, err = capture(
            ["--mach", "0.8", "--alt", "11000", "--tit", "1600", "--opr", "15", "--t7", "2000", "--nozzle", "convergent", "--out", str(png)]
        )
        if code != 0:
            return fail(f"cli failed: {err}")
        if "f_ab:" not in text or "thrust_ratio:" not in text:
            return fail("cli omitted reheat results")
        if "warning_convergent_nozzle:" not in text:
            return fail("cli omitted convergent-nozzle warning")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
