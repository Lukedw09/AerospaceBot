#!/usr/bin/env python3
"""Allen-Eggers nonlifting ballistic-entry peak load (exponential atmosphere).

ballistic_coefficient is B = m/(Cd*A).
exponential_atmosphere_density is rho = rhoref*exp(-(Z - Zref)/H).
allen_eggers_peak_deceleration is a_max = Ve**2*sin(th)/(2*e*H).
allen_eggers_peak_deceleration_altitude is
Z1 = Zref + H*log(rhoref*H/(B*sin(th))).
allen_eggers_speed_at_peak_deceleration is V1 = Ve/sqrt(e).
When Z1 is below the surface (Z = 0), allen_eggers_surface_speed and
allen_eggers_surface_deceleration give the in-flight maximum at impact.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Ballistic entry peak load"
N_CURVE = 201
G0 = 9.80665
EULER = math.e

# Allen and Eggers, NACA TN 4047: rho0 = 0.0034 slug/ft^3, beta = 1/22000 /ft.
SLUG_FT3_TO_KG_M3 = 515.3788184
FT_TO_M = 0.3048
DEFAULT_RHO_REF = 0.0034 * SLUG_FT3_TO_KG_M3
DEFAULT_H = 22000.0 * FT_TO_M
DEFAULT_Z_REF = 0.0
SURFACE_Z = 0.0

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "Allen-Eggers nonlifting ballistic entry (NACA TN 4047 / Report 1381); "
    "constant Cd; exponential atmosphere "
    "exponential_atmosphere_density "
    "rho = rhoref*exp(-(Z - Zref)/H); "
    "gravity neglected relative to drag so the path is a straight line at "
    "entry flight-path angle th below the local horizontal; "
    "ballistic_coefficient B = m/(Cd*A); "
    "when peak altitude is positive: "
    "allen_eggers_peak_deceleration a_max = Ve**2*sin(th)/(2*e*H), "
    "allen_eggers_peak_deceleration_altitude "
    "Z1 = Zref + H*log(rhoref*H/(B*sin(th))), "
    "allen_eggers_speed_at_peak_deceleration V1 = Ve/sqrt(e), "
    "allen_eggers_density_at_peak_deceleration rho1 = B*sin(th)/H; "
    "when Z1 is below the surface Z = 0: "
    "allen_eggers_surface_speed and allen_eggers_surface_deceleration "
    "at sea-level density; "
    "default Earth fit from TN 4047: "
    f"rhoref = {DEFAULT_RHO_REF:.8g} kg/m^3, "
    f"H = {DEFAULT_H:.8g} m, Zref = {DEFAULT_Z_REF:g}; "
    "not a lifting entry, skip trajectory, or stagnation heat-flux model"
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


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def require_entry_angle(gamma: float) -> None:
    if not math.isfinite(gamma) or gamma <= 0.0 or gamma > math.pi / 2.0:
        raise ValueError(
            "entry flight-path angle must be finite and in (0, pi/2] radians "
            "below the local horizontal"
        )


def ballistic_coefficient(mass: float, cd: float, area: float) -> float:
    """ballistic_coefficient: B = m/(Cd*A)."""
    return mass / (cd * area)


def exponential_density(
    rho_ref: float, altitude: float, z_ref: float, scale_height: float
) -> float:
    """exponential_atmosphere_density."""
    return rho_ref * math.exp(-(altitude - z_ref) / scale_height)


def inverse_scale_height(scale_height: float) -> float:
    """atmosphere_inverse_scale_height: beta = 1/H."""
    return 1.0 / scale_height


def peak_deceleration(speed: float, gamma: float, scale_height: float) -> float:
    """allen_eggers_peak_deceleration: Ve**2*sin(th)/(2*e*H)."""
    return speed * speed * math.sin(gamma) / (2.0 * EULER * scale_height)


def peak_speed(speed: float) -> float:
    """allen_eggers_speed_at_peak_deceleration: Ve/sqrt(e)."""
    return speed * math.exp(-0.5)


def peak_density(beta: float, gamma: float, scale_height: float) -> float:
    """allen_eggers_density_at_peak_deceleration: B*sin(th)/H."""
    return beta * math.sin(gamma) / scale_height


def peak_altitude(
    z_ref: float,
    scale_height: float,
    rho_ref: float,
    beta: float,
    gamma: float,
) -> float:
    """allen_eggers_peak_deceleration_altitude."""
    return z_ref + scale_height * math.log(
        rho_ref * scale_height / (beta * math.sin(gamma))
    )


def surface_speed(
    speed: float,
    rho_surface: float,
    scale_height: float,
    beta: float,
    gamma: float,
) -> float:
    """allen_eggers_surface_speed at the impact density."""
    return speed * math.exp(
        -rho_surface * scale_height / (2.0 * beta * math.sin(gamma))
    )


def surface_deceleration(rho_surface: float, beta: float, speed_s: float) -> float:
    """allen_eggers_surface_deceleration: (rho/(2*B))*Vs**2."""
    return (rho_surface / (2.0 * beta)) * speed_s * speed_s


def resolve_ballistic(
    beta: float | None,
    mass: float | None,
    cd: float | None,
    area: float | None,
) -> tuple[float, str]:
    parts = (mass is not None, cd is not None, area is not None)
    if beta is not None:
        require_positive("ballistic coefficient", beta)
        if any(parts):
            if not all(parts):
                raise ValueError(
                    "pass all of --mass, --cd, and --area when checking against --beta"
                )
            built = ballistic_coefficient(mass, cd, area)
            if not close(float(beta), built):
                raise ValueError(
                    f"--beta {beta:g} disagrees with m/(Cd*A) = {built:g}"
                )
        return float(beta), "flag"
    if all(parts):
        require_positive("mass", mass)
        require_positive("drag coefficient", cd)
        require_positive("reference area", area)
        return ballistic_coefficient(mass, cd, area), "mass_cd_area"
    if any(parts):
        raise ValueError("pass --mass, --cd, and --area together, or pass --beta")
    raise ValueError("pass --beta, or --mass with --cd and --area")


def resolve_atmosphere(
    scale_height: float | None,
    rho_ref: float | None,
    z_ref: float | None,
) -> tuple[float, float, float, str]:
    supplied = (
        scale_height is not None,
        rho_ref is not None,
        z_ref is not None,
    )
    if not any(supplied):
        return DEFAULT_H, DEFAULT_RHO_REF, DEFAULT_Z_REF, "allen_eggers_earth"
    if not all(supplied):
        raise ValueError(
            "pass --scale-height, --rho-ref, and --z-ref together to override "
            "the Allen-Eggers Earth default"
        )
    require_positive("scale height", scale_height)
    require_positive("reference density", rho_ref)
    require_finite("reference altitude", z_ref)
    return float(scale_height), float(rho_ref), float(z_ref), "user"


def evaluate(
    speed: float,
    gamma: float,
    beta: float | None,
    mass: float | None,
    cd: float | None,
    area: float | None,
    scale_height: float | None,
    rho_ref: float | None,
    z_ref: float | None,
) -> dict[str, float | str]:
    require_positive("entry speed", speed)
    require_entry_angle(gamma)
    b_use, b_source = resolve_ballistic(beta, mass, cd, area)
    h_use, rho_use, zref_use, atm_source = resolve_atmosphere(
        scale_height, rho_ref, z_ref
    )

    z_formal = peak_altitude(zref_use, h_use, rho_use, b_use, gamma)
    beta_atm = inverse_scale_height(h_use)

    result: dict[str, float | str] = {
        "method": "allen_eggers",
        "B_kg_m2": b_use,
        "B_source": b_source,
        "Ve_m_s": speed,
        "gamma_rad": gamma,
        "gamma_deg": math.degrees(gamma),
        "H_m": h_use,
        "beta_atm_1_m": beta_atm,
        "rho_ref_kg_m3": rho_use,
        "Z_ref_m": zref_use,
        "atmosphere_source": atm_source,
        "Z_formal_m": z_formal,
    }

    if z_formal > SURFACE_Z:
        a_peak = peak_deceleration(speed, gamma, h_use)
        v_peak = peak_speed(speed)
        rho_peak = peak_density(b_use, gamma, h_use)
        rho_check = exponential_density(rho_use, z_formal, zref_use, h_use)
        if not close(rho_peak, rho_check):
            raise ValueError("peak density and exponential density disagree")
        result["peak_regime"] = "altitude"
        result["Z_peak_m"] = z_formal
        result["a_peak_m_s2"] = a_peak
        result["a_peak_g"] = a_peak / G0
        result["V_peak_m_s"] = v_peak
        result["rho_peak_kg_m3"] = rho_peak
    else:
        rho_s = exponential_density(rho_use, SURFACE_Z, zref_use, h_use)
        v_s = surface_speed(speed, rho_s, h_use, b_use, gamma)
        a_s = surface_deceleration(rho_s, b_use, v_s)
        result["peak_regime"] = "surface"
        result["Z_peak_m"] = SURFACE_Z
        result["a_peak_m_s2"] = a_s
        result["a_peak_g"] = a_s / G0
        result["V_peak_m_s"] = v_s
        result["rho_peak_kg_m3"] = rho_s
        result["warning"] = (
            "formal Allen-Eggers peak altitude is below the surface; "
            "reported peak load is the sea-level (Z = 0) value"
        )

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
        raise ValueError(
            "matplotlib is required to plot ballistic entry peak load"
        ) from exc
    return plt


def peak_load_g(
    speed: float,
    gamma: float,
    beta: float,
    scale_height: float,
    rho_ref: float,
    z_ref: float,
) -> float:
    """Peak deceleration in g0 for one angle (altitude or surface regime)."""
    z_formal = peak_altitude(z_ref, scale_height, rho_ref, beta, gamma)
    if z_formal > SURFACE_Z:
        return peak_deceleration(speed, gamma, scale_height) / G0
    rho_s = exponential_density(rho_ref, SURFACE_Z, z_ref, scale_height)
    v_s = surface_speed(speed, rho_s, scale_height, beta, gamma)
    return surface_deceleration(rho_s, beta, v_s) / G0


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    speed = float(result["Ve_m_s"])
    beta = float(result["B_kg_m2"])
    scale_height = float(result["H_m"])
    rho_ref = float(result["rho_ref_kg_m3"])
    z_ref = float(result["Z_ref_m"])
    gamma = float(result["gamma_rad"])
    a_g = float(result["a_peak_g"])

    gamma_min = min(math.radians(1.0), 0.5 * gamma)
    gamma_min = max(gamma_min, 1e-4)
    gammas = linspace(gamma_min, math.pi / 2.0, N_CURVE)
    loads = [
        peak_load_g(speed, g, beta, scale_height, rho_ref, z_ref) for g in gammas
    ]
    degrees = [math.degrees(g) for g in gammas]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.plot(degrees, loads, color="#1a5276", linewidth=1.8, label="peak load")
    ax.plot(
        [math.degrees(gamma)],
        [a_g],
        marker="s",
        markersize=8,
        color="#c0392b",
        linestyle="none",
        label="operating point",
    )
    ax.set_xlabel("entry flight-path angle below horizontal (deg)")
    ax.set_ylabel(f"peak deceleration / g0  (g0 = {G0:g} m/s$^2$)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def emit(result: dict[str, float | str], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("method", result["method"])
    print_kv("assumptions", ASSUMPTIONS)
    keys = (
        "B_kg_m2",
        "B_source",
        "Ve_m_s",
        "gamma_rad",
        "gamma_deg",
        "H_m",
        "beta_atm_1_m",
        "rho_ref_kg_m3",
        "Z_ref_m",
        "atmosphere_source",
        "peak_regime",
        "Z_formal_m",
        "Z_peak_m",
        "a_peak_m_s2",
        "a_peak_g",
        "V_peak_m_s",
        "rho_peak_kg_m3",
    )
    for key in keys:
        if key in result:
            print_kv(key, result[key])
    if "warning" in result:
        print_kv("warning", result["warning"])
    if graph is not None:
        print_kv("graph", str(graph.resolve()))


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"check: fail: {message}")
        return 1

    # TN 4047 Earth constants in SI.
    if not close(DEFAULT_RHO_REF, 0.0034 * SLUG_FT3_TO_KG_M3):
        return fail("Earth rho_ref conversion drifted")
    if not close(DEFAULT_H, 22000.0 * FT_TO_M):
        return fail("Earth scale-height conversion drifted")

    # Vertical entry, B such that peak is well above the surface.
    speed = 7000.0
    gamma = math.pi / 2.0
    beta = 100.0
    a_max = peak_deceleration(speed, gamma, DEFAULT_H)
    expected_a = speed**2 / (2.0 * EULER * DEFAULT_H)
    if not close(a_max, expected_a):
        return fail(f"vertical a_max {a_max} != {expected_a}")
    z1 = peak_altitude(0.0, DEFAULT_H, DEFAULT_RHO_REF, beta, gamma)
    if z1 <= 0.0:
        return fail("expected positive peak altitude for B = 100")
    v1 = peak_speed(speed)
    if not close(v1, speed / math.sqrt(EULER)):
        return fail("V1 is not Ve/sqrt(e)")
    rho1 = peak_density(beta, gamma, DEFAULT_H)
    if not close(rho1, exponential_density(DEFAULT_RHO_REF, z1, 0.0, DEFAULT_H)):
        return fail("rho1 mismatch at Z1")

    # Peak load independent of B while altitude regime holds.
    a_other = peak_deceleration(speed, gamma, DEFAULT_H)
    if not close(a_max, a_other):
        return fail("a_max depended on something other than Ve, gamma, H")

    # Heavy vehicle: formal altitude negative, surface regime.
    heavy = evaluate(
        speed,
        gamma,
        20000.0,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    if heavy["peak_regime"] != "surface":
        return fail("heavy vehicle did not enter surface regime")
    if float(heavy["Z_peak_m"]) != 0.0:
        return fail("surface regime Z_peak is not 0")
    if float(heavy["a_peak_m_s2"]) >= a_max:
        return fail("surface peak should be below the formal altitude a_max")

    # mass/Cd/A path.
    built = ballistic_coefficient(500.0, 0.5, 2.0)
    if not close(built, 500.0):
        return fail("ballistic coefficient m/(Cd*A)")

    point = evaluate(
        speed,
        math.radians(30.0),
        None,
        500.0,
        0.5,
        2.0,
        None,
        None,
        None,
    )
    if point["B_source"] != "mass_cd_area":
        return fail("mass/Cd/A source not marked")
    if not close(float(point["B_kg_m2"]), 500.0):
        return fail("B from mass/Cd/A")
    if point["method"] != "allen_eggers":
        return fail("method name")
    if point["atmosphere_source"] != "allen_eggers_earth":
        return fail("default atmosphere source")

    # Disagreeing --beta.
    try:
        resolve_ballistic(100.0, 500.0, 0.5, 2.0)
        return fail("disagreeing beta was accepted")
    except ValueError:
        pass

    # Partial atmosphere override rejected.
    try:
        resolve_atmosphere(8000.0, None, None)
        return fail("partial atmosphere override was accepted")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ballistic_entry_peak_load.png"

        def capture(argv: list[str]) -> tuple[int, str, str]:
            from io import StringIO

            sink = StringIO()
            err = StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            try:
                sys.stdout, sys.stderr = sink, err
                code = main(argv)
            finally:
                sys.stdout, sys.stderr = old_out, old_err
            return code, sink.getvalue(), err.getvalue()

        code, text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                str(math.radians(30.0)),
                "--beta",
                "100",
                "--out",
                str(out),
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        if not out.is_file() or not out.read_bytes().startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Ballistic entry peak load",
            "method: allen_eggers",
            "peak_regime: altitude",
            "a_peak_g:",
            "Z_peak_m:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                str(math.pi / 2.0),
                "--mass",
                "500",
                "--cd",
                "0.5",
                "--area",
                "2",
            ]
        )
        if code != 0:
            return fail(f"mass path returned {code}: {err}")
        if "B_source: mass_cd_area" not in text:
            return fail("mass path did not mark B_source")
        if "graph:" in text:
            return fail("run without --out printed graph")

        code, _text, err = capture(["--speed", "7000", "--gamma", "0.5"])
        if code != 2:
            return fail("missing ballistic coefficient was accepted")
        if "beta" not in err.lower() and "mass" not in err.lower():
            return fail("missing-B error did not name beta or mass")
        code, _text, _err = capture(["--beta", "100", "--gamma", "0.5"])
        if code != 2:
            return fail("missing speed was accepted")

    print("check: pass")
    print_kv("a_peak_m_s2", a_max)
    print_kv("Z_peak_m", z1)
    print_kv("V_peak_m_s", v1)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Allen-Eggers nonlifting ballistic-entry peak deceleration and "
            "altitude in an exponential atmosphere, with optional PNG of peak "
            "load versus entry angle."
        )
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="entry speed Ve [m/s]",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help="entry flight-path angle below local horizontal [rad]",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=None,
        help="ballistic coefficient B = m/(Cd*A) [kg/m^2]",
    )
    parser.add_argument("--mass", type=float, default=None, help="vehicle mass m [kg]")
    parser.add_argument(
        "--cd",
        type=float,
        default=None,
        help="drag coefficient Cd [dimensionless]",
    )
    parser.add_argument(
        "--area",
        type=float,
        default=None,
        help="reference area A [m^2]",
    )
    parser.add_argument(
        "--scale-height",
        type=float,
        default=None,
        help=f"density scale height H [m] (default {DEFAULT_H:g})",
    )
    parser.add_argument(
        "--rho-ref",
        type=float,
        default=None,
        help=f"reference density [kg/m^3] (default {DEFAULT_RHO_REF:g})",
    )
    parser.add_argument(
        "--z-ref",
        type=float,
        default=None,
        help=f"reference altitude for rho-ref [m] (default {DEFAULT_Z_REF:g})",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.speed is None or args.gamma is None:
        print("error: requires --speed and --gamma", file=sys.stderr)
        return 2

    try:
        result = evaluate(
            args.speed,
            args.gamma,
            args.beta,
            args.mass,
            args.cd,
            args.area,
            args.scale_height,
            args.rho_ref,
            args.z_ref,
        )
        graph: Path | None = None
        if args.out is not None:
            graph = Path(args.out)
            write_plot(result, graph)
        emit(result, graph)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
