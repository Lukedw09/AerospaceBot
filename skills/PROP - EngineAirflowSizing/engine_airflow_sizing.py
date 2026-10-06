#!/usr/bin/env python3
"""Size inlet airflow, capture area, and face area from a thrust requirement.

airflow_from_thrust, capture_area, circular_capture_diameter,
compressible_mass_flow_parameter, annulus_area_from_mass_flow, and
compressor_stage_count.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Engine airflow sizing"
N_PLOT = 81
DEFAULT_GAMMA = 1.4
RSTAR = 8.31432e3
M0 = 28.9644
R_AIR = RSTAR / M0

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "sizing from net thrust and specific thrust; "
    "mdot = F/Fs from airflow_from_thrust; "
    "capture area mdot/(rho*V) from capture_area when V > 0; "
    "diameter from circular_capture_diameter; "
    "face area from annulus_area_from_mass_flow and compressible_mass_flow_parameter; "
    "stage count log(pi_c)/log(pi_stage) from compressor_stage_count; "
    "static flight skips capture area and sizes the compressor face; "
    f"default gamma = {DEFAULT_GAMMA:g}; default R is 1976 dry air; "
    "PNG is airflow and diameter versus required thrust"
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


def speed_of_sound(temperature: float, gamma: float, gas_constant: float) -> float:
    return math.sqrt(gamma * gas_constant * temperature)


def mass_flow_parameter(mach: float, gamma: float, gas_constant: float) -> float:
    """compressible_mass_flow_parameter."""
    require_nonnegative("face Mach", mach)
    if mach == 0.0:
        raise ValueError("face Mach must be > 0 to size an annulus")
    return (
        math.sqrt(gamma / gas_constant)
        * mach
        * (1.0 + 0.5 * (gamma - 1.0) * mach * mach) ** (-(gamma + 1.0) / (2.0 * (gamma - 1.0)))
    )


def diameter_from_area(area: float) -> float:
    """circular_capture_diameter."""
    return math.sqrt(4.0 * area / math.pi)


def solution(
    thrust: float,
    specific_thrust: float,
    rho: float | None,
    speed: float | None,
    face_mach: float | None,
    face_pt: float | None,
    face_tt: float | None,
    opr: float | None,
    stage_pr: float | None,
    gamma: float,
    gas_constant: float,
) -> dict[str, float | str]:
    require_positive("thrust", thrust)
    require_positive("specific thrust", specific_thrust)
    require_gamma(gamma)
    require_positive("gas constant", gas_constant)
    mdot = thrust / specific_thrust
    out: dict[str, float | str] = {
        "F_N": thrust,
        "Fs_m_s": specific_thrust,
        "mdot_kg_s": mdot,
        "gamma": gamma,
        "R_J_kgK": gas_constant,
        "sizing_diameter": "none",
    }
    flying = speed is not None and speed > 0.0
    if flying:
        if rho is None:
            raise ValueError("capture area needs density")
        require_positive("density", rho)
        area = mdot / (rho * speed)
        out["rho_kg_m3"] = rho
        out["V_m_s"] = speed
        out["A_capture_m2"] = area
        out["D_capture_m"] = diameter_from_area(area)
        out["sizing_diameter"] = "capture"
    elif speed == 0.0:
        out["V_m_s"] = 0.0
        if rho is not None:
            out["rho_kg_m3"] = rho
    face_flags = (face_mach is not None, face_pt is not None, face_tt is not None)
    if any(face_flags) and not all(face_flags):
        raise ValueError("pass --face-mach, --face-pt, and --face-tt together")
    if all(face_flags):
        assert face_mach is not None and face_pt is not None and face_tt is not None
        require_positive("face total pressure", face_pt)
        require_positive("face total temperature", face_tt)
        mfp = mass_flow_parameter(face_mach, gamma, gas_constant)
        area_face = mdot * math.sqrt(face_tt) / (face_pt * mfp)
        out["M_face"] = face_mach
        out["pt_face_Pa"] = face_pt
        out["Tt_face_K"] = face_tt
        out["mfp"] = mfp
        out["A_face_m2"] = area_face
        out["D_face_m"] = diameter_from_area(area_face)
        if out["sizing_diameter"] == "none":
            out["sizing_diameter"] = "face"
    if not flying and "A_face_m2" not in out:
        raise ValueError("static flight skips capture area; pass --face-mach, --face-pt, and --face-tt")
    if (opr is None) ^ (stage_pr is None):
        raise ValueError("pass --opr and --stage-pr together for a stage count")
    if opr is not None and stage_pr is not None:
        if opr <= 1.0 or stage_pr <= 1.0:
            raise ValueError("overall and stage pressure ratios must be > 1")
        if stage_pr > opr:
            raise ValueError("stage pressure ratio cannot exceed the overall pressure ratio")
        out["pi_c"] = opr
        out["pi_stage"] = stage_pr
        out["N_stages"] = math.log(opr) / math.log(stage_pr)
    return out


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot engine sizing") from exc
    return plt


def plot_sizing(path: Path, result: dict[str, float | str], rho: float | None, speed: float | None, face, opr, stage_pr, gamma: float, gas_constant: float) -> None:
    plt = ensure_matplotlib()
    thrust = float(result["F_N"])
    specific = float(result["Fs_m_s"])
    xs: list[float] = []
    flows: list[float] = []
    diameters: list[float] = []
    for i in range(N_PLOT):
        load = thrust * (0.25 + 1.5 * i / (N_PLOT - 1))
        point = solution(load, specific, rho, speed, face[0], face[1], face[2], opr, stage_pr, gamma, gas_constant)
        xs.append(load)
        flows.append(float(point["mdot_kg_s"]))
        if result["sizing_diameter"] == "capture":
            diameters.append(float(point["D_capture_m"]))
        else:
            diameters.append(float(point["D_face_m"]))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, flows, color="#1a5276", linewidth=1.8, label="airflow")
    ax.plot(thrust, float(result["mdot_kg_s"]), "s", color="#1a5276", markersize=7, zorder=5, label="operating point")
    ax.set_xlabel("required net thrust (N)")
    ax.set_ylabel(r"airflow $\dot{m}$ (kg/s)")
    ax2 = ax.twinx()
    ax2.plot(xs, diameters, color="#b9770e", linewidth=1.5, label="diameter")
    diameter_now = float(result["D_capture_m"] if result["sizing_diameter"] == "capture" else result["D_face_m"])
    ax2.plot(thrust, diameter_now, "s", color="#b9770e", markersize=6, zorder=5)
    ax2.set_ylabel("diameter (m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(result: dict[str, float | str], freestream_source: str, path: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "engine airflow sizing")
    print_kv("freestream_source", freestream_source)
    for key in (
        "F_N",
        "Fs_m_s",
        "mdot_kg_s",
        "V_m_s",
        "rho_kg_m3",
        "A_capture_m2",
        "D_capture_m",
        "M_face",
        "pt_face_Pa",
        "Tt_face_K",
        "mfp",
        "A_face_m2",
        "D_face_m",
        "pi_c",
        "pi_stage",
        "N_stages",
        "sizing_diameter",
        "gamma",
        "R_J_kgK",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(path))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Size airflow and inlet diameter from thrust")
    parser.add_argument("--thrust", type=float, default=None, help="required net thrust [N]")
    parser.add_argument("--fs", type=float, default=None, help="specific thrust [m/s]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude Z [m]")
    parser.add_argument("--mach", type=float, default=None, help="flight Mach number")
    parser.add_argument("--speed", type=float, default=None, help="flight speed [m/s]")
    parser.add_argument("--rho", type=float, default=None, help="freestream density [kg/m^3]")
    parser.add_argument("--face-mach", type=float, default=None, help="axial Mach at the compressor face")
    parser.add_argument("--face-pt", type=float, default=None, help="face total pressure [Pa]")
    parser.add_argument("--face-tt", type=float, default=None, help="face total temperature [K]")
    parser.add_argument("--opr", type=float, default=None, help="compressor pressure ratio for the stage count")
    parser.add_argument("--stage-pr", type=float, default=None, help="mean stage pressure ratio")
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def resolve_flight(args: argparse.Namespace) -> tuple[float | None, float | None, str]:
    has_alt = args.alt is not None
    has_rho = args.rho is not None
    has_mach = args.mach is not None
    has_speed = args.speed is not None
    if has_mach and has_speed:
        raise ValueError("pass --mach or --speed, not both")
    if has_alt and has_rho:
        raise ValueError("pass --alt or --rho, not both")
    if has_alt:
        if not has_mach and not has_speed:
            raise ValueError("--alt needs --mach or --speed")
        atmosphere, require_altitude = load_atmosphere()
        state = atmosphere(require_altitude(args.alt, "--alt"))
        rho = float(state["rho"])
        if has_speed:
            require_nonnegative("speed", args.speed)
            return rho, args.speed, "altitude"
        gamma = DEFAULT_GAMMA if args.gamma is None else args.gamma
        require_gamma(gamma)
        require_nonnegative("Mach", args.mach)
        speed = args.mach * speed_of_sound(float(state["T"]), gamma, R_AIR)
        return rho, speed, "altitude"
    if has_rho:
        if not has_speed:
            raise ValueError("--rho needs --speed")
        require_positive("density", args.rho)
        require_nonnegative("speed", args.speed)
        return args.rho, args.speed, "density_speed"
    if has_speed and args.speed == 0.0:
        return None, 0.0, "static"
    raise ValueError("pass --alt with --mach or --speed, or --rho with --speed")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.thrust is None or args.fs is None:
        print("error: requires --thrust and --fs", file=sys.stderr)
        return 2
    try:
        if args.gamma is None:
            gamma = DEFAULT_GAMMA
        else:
            require_gamma(args.gamma)
            gamma = args.gamma
        rho, speed, freestream_source = resolve_flight(args)
        result = solution(
            args.thrust,
            args.fs,
            rho,
            speed,
            args.face_mach,
            args.face_pt,
            args.face_tt,
            args.opr,
            args.stage_pr,
            gamma,
            R_AIR,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "engine_airflow_sizing.png"
        out_path = out_path.resolve()
        plot_sizing(
            out_path,
            result,
            rho,
            speed,
            (args.face_mach, args.face_pt, args.face_tt),
            args.opr,
            args.stage_pr,
            gamma,
            R_AIR,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, freestream_source, out_path)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    point = solution(5000.0, 500.0, 1.25, 80.0, None, None, None, 256.0, 2.0, 1.4, R_AIR)
    if near(float(point["mdot_kg_s"]), 10.0, "airflow"):
        return 1
    if near(float(point["F_N"]), float(point["mdot_kg_s"]) * float(point["Fs_m_s"]), "thrust product"):
        return 1
    if near(float(point["A_capture_m2"]), 10.0 / (1.25 * 80.0), "capture area"):
        return 1
    if near(float(point["D_capture_m"]), math.sqrt(4.0 * float(point["A_capture_m2"]) / math.pi), "diameter"):
        return 1
    if near(float(point["N_stages"]), 8.0, "stage count"):
        return 1
    mfp = mass_flow_parameter(1.0, 1.4, 1.0)
    if near(mfp, math.sqrt(1.4) * (1.2) ** (-3.0), "sonic mass-flow parameter"):
        return 1
    static = solution(5000.0, 500.0, None, 0.0, 0.5, 2.0e5, 300.0, None, None, 1.4, R_AIR)
    if "A_capture_m2" in static:
        return fail("static flight should skip capture area")
    if float(static["A_face_m2"]) <= 0.0:
        return fail("face area not positive")
    try:
        solution(5000.0, 500.0, 1.25, 0.0, None, None, None, None, None, 1.4, R_AIR)
    except ValueError:
        pass
    else:
        return fail("static flight without a face should fail")

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
        png = Path(folder_name) / "engine_airflow_sizing.png"
        code, text, err = capture(
            ["--thrust", "20000", "--fs", "400", "--rho", "0.3", "--speed", "250", "--out", str(png)]
        )
        if code != 0:
            return fail(f"cli failed: {err}")
        if "mdot_kg_s:" not in text or "D_capture_m:" not in text:
            return fail("cli omitted airflow or diameter")
        if not png.is_file() or png.stat().st_size < 100:
            return fail("cli did not write a PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
