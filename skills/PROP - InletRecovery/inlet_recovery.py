#!/usr/bin/env python3
"""Inlet total-pressure recovery from freestream to the compressor face.

adiabatic_diffuser_temperature, inlet_exit_total_pressure, and
pitot_inlet_recovery. The pitot shock ratio is normal_shock_stagnation_pressure
(1 at Mach <= 1). Freestream totals use stagnation_temperature and
stagnation_pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Inlet recovery"
N_PLOT = 201
DEFAULT_GAMMA = 1.4
RSTAR = 8.31432e3
M0 = 28.9644
R_AIR = RSTAR / M0
M_PLOT_MAX_FLOOR = 2.0
M_PLOT_END_FACTOR = 1.5

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "adiabatic inlet from station 0 to station 2; calorically perfect gas; "
    "Tt2 = Tt0 from adiabatic_diffuser_temperature; "
    "pt2 = pi_d*pt0 from inlet_exit_total_pressure; "
    "pitot recovery is normal_shock_stagnation_pressure times a subsonic "
    "diffuser factor from pitot_inlet_recovery; shock ratio is 1 at Mach <= 1; "
    "a supplied pi_d is used as given; no MIL-E-5008B schedule; "
    "no spillage, bleed, or cowl drag; "
    f"default gamma = {DEFAULT_GAMMA:g}; "
    "PNG is recovery versus Mach"
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
            "ATMOS - Standard1976 must be importable for freestream from --alt"
        ) from exc
    return atmosphere, require_altitude


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def require_gamma(gamma: float) -> None:
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("gamma must be finite and > 1")


def require_loss_ratio(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    """stagnation_temperature."""
    return 1.0 + 0.5 * (gamma - 1.0) * mach * mach


def stagnation_pressure_ratio(tau: float, gamma: float) -> float:
    """stagnation_pressure."""
    return tau ** (gamma / (gamma - 1.0))


def speed_of_sound(temperature: float, gamma: float, gas_constant: float) -> float:
    """speed_of_sound."""
    return math.sqrt(gamma * gas_constant * temperature)


def normal_shock_stagnation_pressure(mach: float, gamma: float) -> float:
    """normal_shock_stagnation_pressure. At M <= 1 the shock ratio is 1."""
    if mach <= 1.0:
        return 1.0
    g = gamma
    first = ((g + 1.0) * mach * mach) / ((g - 1.0) * mach * mach + 2.0)
    second = (g + 1.0) / (2.0 * g * mach * mach - (g - 1.0))
    return first ** (g / (g - 1.0)) * second ** (1.0 / (g - 1.0))


def recovery(mach: float, gamma: float, pi_d: float | None, pitot: bool, pi_ds: float) -> tuple[float, float, str]:
    """Return pi_d, pi_ns, and recovery_source."""
    if pitot:
        require_loss_ratio("subsonic diffuser factor", pi_ds)
        pi_ns = normal_shock_stagnation_pressure(mach, gamma)
        return pi_ns * pi_ds, pi_ns, "pitot"
    if pi_d is None:
        raise ValueError("pass --pi-d or --pitot")
    require_loss_ratio("inlet recovery", pi_d)
    return pi_d, 1.0, "user"


def solution(
    mach: float,
    temperature: float,
    pressure: float,
    gamma: float,
    gas_constant: float,
    pi_d: float | None,
    pitot: bool,
    pi_ds: float,
) -> dict[str, float | str]:
    require_nonnegative("Mach", mach)
    require_positive("temperature", temperature)
    require_positive("pressure", pressure)
    require_gamma(gamma)
    require_positive("gas constant", gas_constant)
    pi, pi_ns, source = recovery(mach, gamma, pi_d, pitot, pi_ds)
    tau_r = stagnation_temperature_ratio(mach, gamma)
    pi_r = stagnation_pressure_ratio(tau_r, gamma)
    tt0 = temperature * tau_r
    pt0 = pressure * pi_r
    a0 = speed_of_sound(temperature, gamma, gas_constant)
    return {
        "M": mach,
        "T0_K": temperature,
        "p0_Pa": pressure,
        "rho0_kg_m3": pressure / (gas_constant * temperature),
        "a0_m_s": a0,
        "V0_m_s": mach * a0,
        "tau_r": tau_r,
        "pi_r": pi_r,
        "Tt0_K": tt0,
        "pt0_Pa": pt0,
        "pi_ns": pi_ns,
        "pi_ds": pi_ds if pitot else 1.0,
        "pi_d": pi,
        "Tt2_K": tt0,
        "pt2_Pa": pi * pt0,
        "recovery_source": source,
        "gamma": gamma,
        "R_J_kgK": gas_constant,
    }


def mach_grid(mach: float) -> list[float]:
    end = max(M_PLOT_MAX_FLOOR, M_PLOT_END_FACTOR * max(mach, 0.5))
    return [end * i / (N_PLOT - 1) for i in range(N_PLOT)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot inlet recovery") from exc
    return plt


def plot_recovery(path: Path, result: dict[str, float | str]) -> None:
    plt = ensure_matplotlib()
    machs = mach_grid(float(result["M"]))
    ys: list[float] = []
    xs: list[float] = []
    pitot = result["recovery_source"] == "pitot"
    pi_d = None if pitot else float(result["pi_d"])
    for mach in machs:
        try:
            point = solution(
                mach,
                float(result["T0_K"]),
                float(result["p0_Pa"]),
                float(result["gamma"]),
                float(result["R_J_kgK"]),
                pi_d,
                pitot,
                float(result["pi_ds"]),
            )
        except ValueError:
            continue
        xs.append(mach)
        ys.append(float(point["pi_d"]))
    if len(xs) < 2:
        raise ValueError("Mach sweep produced fewer than two recovery points")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, ys, color="#1a5276", linewidth=1.8, label="pressure recovery")
    ax.plot(
        float(result["M"]),
        float(result["pi_d"]),
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("flight Mach number")
    ax.set_ylabel(r"inlet recovery $\pi_d$")
    ax.set_xlim(0.0, xs[-1])
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.35)
    ax.text(
        0.02,
        0.02,
        f"recovery from {result['recovery_source']}",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
    )
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(
    result: dict[str, float | str],
    freestream_source: str,
    altitude: float | None,
    gamma_source: str,
    path: Path,
) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "adiabatic inlet, station 0 to 2")
    print_kv("freestream_source", freestream_source)
    if altitude is not None:
        print_kv("Z_m", altitude)
    print_kv("gamma_source", gamma_source)
    for key in (
        "M",
        "T0_K",
        "p0_Pa",
        "rho0_kg_m3",
        "a0_m_s",
        "V0_m_s",
        "Tt0_K",
        "pt0_Pa",
        "recovery_source",
        "pi_ns",
        "pi_ds",
        "pi_d",
        "Tt2_K",
        "pt2_Pa",
        "gamma",
        "R_J_kgK",
    ):
        print_kv(key, result[key])
    print_kv("graph", str(path))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inlet total-pressure recovery")
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument("--temperature", type=float, default=None, help="freestream static temperature T0 [K]")
    parser.add_argument("--pressure", type=float, default=None, help="freestream static pressure p0 [Pa]")
    parser.add_argument("--pi-d", type=float, default=None, help="supplied inlet recovery pt2/pt0")
    parser.add_argument("--pitot", action="store_true", help="pitot inlet: one normal shock times --pi-ds")
    parser.add_argument("--pi-ds", type=float, default=1.0, help="subsonic diffuser factor for --pitot; default 1")
    parser.add_argument("--gamma", type=float, default=None, help="ratio of specific heats")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def resolve_freestream(args: argparse.Namespace) -> tuple[float, float, str, float | None]:
    has_alt = args.alt is not None
    has_tp = args.temperature is not None or args.pressure is not None
    if has_alt and has_tp:
        raise ValueError("pass --alt or --temperature/--pressure, not both")
    if not has_alt and (args.temperature is None or args.pressure is None):
        raise ValueError("requires --alt, or both --temperature and --pressure")
    if has_alt:
        atmosphere, require_altitude = load_atmosphere()
        state = atmosphere(require_altitude(args.alt, "--alt"))
        return float(state["T"]), float(state["p"]), "altitude", float(state["Z"])
    require_positive("temperature", args.temperature)
    require_positive("pressure", args.pressure)
    return args.temperature, args.pressure, "temperature_pressure", None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.mach is None:
        print("error: requires --mach and (--alt or both --temperature and --pressure)", file=sys.stderr)
        return 2
    if args.pitot and args.pi_d is not None:
        print("error: pass --pi-d or --pitot, not both", file=sys.stderr)
        return 2
    if not args.pitot and args.pi_d is None:
        print("error: pass --pi-d or --pitot", file=sys.stderr)
        return 2
    if args.pi_ds != 1.0 and not args.pitot:
        print("error: --pi-ds is only used with --pitot", file=sys.stderr)
        return 2
    try:
        temperature, pressure, freestream_source, altitude = resolve_freestream(args)
        if args.gamma is None:
            gamma, gamma_source = DEFAULT_GAMMA, "default"
        else:
            require_gamma(args.gamma)
            gamma, gamma_source = args.gamma, "user"
        result = solution(
            args.mach,
            temperature,
            pressure,
            gamma,
            R_AIR,
            args.pi_d,
            args.pitot,
            args.pi_ds,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "inlet_recovery.png"
        out_path = out_path.resolve()
        plot_recovery(out_path, result)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, altitude, gamma_source, out_path)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    gamma = 1.4
    shock = normal_shock_stagnation_pressure(2.0, gamma)
    g = gamma
    mach = 2.0
    analytic = (((g + 1.0) * mach * mach) / ((g - 1.0) * mach * mach + 2.0)) ** (
        g / (g - 1.0)
    ) * ((g + 1.0) / (2.0 * g * mach * mach - (g - 1.0))) ** (1.0 / (g - 1.0))
    if near(shock, analytic, "Mach 2 shock recovery"):
        return 1
    if near(normal_shock_stagnation_pressure(0.8, gamma), 1.0, "subsonic shock ratio"):
        return 1
    pitot = solution(2.0, 216.65, 19330.0, gamma, R_AIR, None, True, 0.95)
    if near(float(pitot["pi_d"]), shock * 0.95, "pitot product"):
        return 1
    if pitot["Tt2_K"] != pitot["Tt0_K"]:
        return fail("adiabatic diffuser did not keep total temperature")
    if near(float(pitot["pt2_Pa"]), float(pitot["pi_d"]) * float(pitot["pt0_Pa"]), "pt2"):
        return 1
    supplied = solution(0.8, 288.15, 101325.0, gamma, R_AIR, 0.97, False, 1.0)
    if supplied["recovery_source"] != "user":
        return fail("supplied recovery source")
    if near(float(supplied["pi_d"]), 0.97, "user pi_d"):
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
        png = Path(folder_name) / "inlet_recovery.png"
        code, text, err = capture(
            ["--mach", "2", "--alt", "11000", "--pitot", "--pi-ds", "0.98", "--out", str(png)]
        )
        if code != 0:
            return fail(f"cli pitot failed: {err}")
        if "recovery_source: pitot" not in text or "pi_d:" not in text:
            return fail("cli omitted pitot recovery")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
        code, _text, err = capture(["--mach", "0.8", "--alt", "0", "--pi-d", "0.97", "--pitot"])
        if code == 0:
            return fail("both recovery modes should fail")
    return 0


if __name__ == "__main__":
    sys.exit(main())
