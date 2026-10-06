#!/usr/bin/env python3
"""Environmental disturbance torques for a general spacecraft."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import tempfile
from pathlib import Path

G0 = 9.80665
R0_ORBIT = 6.3742e6
S_DEFAULT = 1361.6
C_LIGHT = 299792458.0
PLOT_TITLE = "Environmental torques"
SKILL_DIR = Path(__file__).resolve().parent
SKILLS = SKILL_DIR.parent
ASSUMPTIONS = (
    "gravity-gradient torque is the planar principal-axis form "
    "(3/2)*n^2*(I_z-I_y)*sin(2*theta) from NASA SP-8024; aerodynamic torque is "
    "dynamic pressure times Cd*A times the center-of-pressure offset, with "
    "density from altitude unless --rho is set; solar torque is "
    "(S/c)*A*C_r*offset; magnetic torque is M*B*sin(psi); no wheel catalog"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_module(folder: str, filename: str, name: str):
    path = SKILLS / folder / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def density_at(alt_m: float, rho_override: float | None) -> tuple[float, str]:
    if rho_override is not None:
        if not math.isfinite(rho_override) or rho_override <= 0.0:
            raise ValueError("--rho must be positive")
        return rho_override, "override"
    if alt_m <= 86000.0:
        standard = load_module("ATMOS - Standard1976", "standard_1976.py", "standard1976_env")
        return float(standard.atmosphere(alt_m)["rho"]), "standard1976"
    dense = load_module("ATMOS - DensityAbove86km", "density_above_86km.py", "density86_env")
    return float(dense.state_at(alt_m)["rho"]), "density_above_86km"


def orbit_rate_squared(radius_m: float) -> float:
    mu = G0 * R0_ORBIT * R0_ORBIT
    return mu / radius_m ** 3


def circular_speed(radius_m: float) -> float:
    return math.sqrt(orbit_rate_squared(radius_m)) * radius_m


def gravity_gradient_torque(i_z: float, i_y: float, theta: float, n2: float) -> float:
    """gravity_gradient_torque."""
    return 1.5 * n2 * (i_z - i_y) * math.sin(2.0 * theta)


def aerodynamic_torque(rho: float, speed: float, cd: float, area: float, offset: float) -> float:
    """aerodynamic_disturbance_torque."""
    return 0.5 * rho * speed * speed * cd * area * offset


def solar_torque(solar: float, area: float, reflectance: float, offset: float) -> float:
    """solar_radiation_torque."""
    return solar * area * reflectance * offset / C_LIGHT


def magnetic_torque(dipole: float, field: float, angle: float) -> float:
    """magnetic_disturbance_torque."""
    return dipole * field * math.sin(angle)


def emit(rows: list[tuple[str, float]], notes: list[str], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "environmental disturbance torques")
    for note in notes:
        print_kv("note", note)
    for key, value in rows:
        print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(labels: list[str], values: list[float], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.bar(labels, [abs(v) for v in values], color="C0")
    ax.set_ylabel("torque magnitude (N·m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    radius = R0_ORBIT + 400000.0
    n2 = orbit_rate_squared(radius)
    # 45 deg puts sin(2*theta) = 1. Inertia difference 2 kg m^2.
    torque = gravity_gradient_torque(12.0, 10.0, math.pi / 4.0, n2)
    if abs(torque - 1.5 * n2 * 2.0) > 1e-12 * max(1.0, abs(torque)):
        return fail("gravity gradient")
    # Small angle: sin(2*theta) ~ 2*theta, so T ~ 3*n^2*dI*theta.
    small = 0.01
    linear = 3.0 * n2 * 2.0 * small
    exact = gravity_gradient_torque(12.0, 10.0, small, n2)
    if abs(exact - linear) / linear > 1e-4:
        return fail("small-angle gravity gradient")
    aero = aerodynamic_torque(2.541e-10, 7780.0, 2.2, 0.5, 0.2)
    manual = 0.5 * 2.541e-10 * 7780.0 ** 2 * 2.2 * 0.5 * 0.2
    if abs(aero - manual) > 1e-18:
        return fail("aerodynamic torque")
    solar = solar_torque(1361.6, 1.0, 1.3, 0.15)
    if abs(solar - 1361.6 * 1.3 * 0.15 / C_LIGHT) > 1e-18:
        return fail("solar torque")
    magnetic = magnetic_torque(0.2, 3.0e-5, math.pi / 2.0)
    if abs(magnetic - 0.2 * 3.0e-5) > 1e-18:
        return fail("magnetic torque")
    # 200 km density path, override must win.
    rho, source = density_at(200000.0, None)
    if source != "density_above_86km" or abs(rho - 2.5403674e-10) / rho > 2e-3:
        return fail(f"200 km density {rho} {source}")
    rho_over, source_over = density_at(200000.0, 1.0e-10)
    if source_over != "override" or rho_over != 1.0e-10:
        return fail("density override")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "torques.png"
        code = main([
            "--i-z", "12", "--i-y", "10", "--theta", str(math.pi / 4.0), "--alt", "400000",
            "--cd", "2.2", "--area", "0.5", "--cp-aero", "0.2",
            "--area-sun", "1", "--reflectance", "1.3", "--cp-sun", "0.15",
            "--dipole", "0.2", "--b-field", "3e-5",
            "--out", str(path),
        ])
        if code != 0 or path.stat().st_size < 1000:
            return fail("plot")
    print("check: pass")
    print_kv("T_gg_N_m", torque)
    print_kv("rho_200", rho)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spacecraft environmental disturbance torques.")
    parser.add_argument("--i-z", type=float, default=None)
    parser.add_argument("--i-y", type=float, default=None)
    parser.add_argument("--theta", type=float, default=None, help="angle from local vertical [rad]")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--a", type=float, default=None, help="orbit radius from the centre [m]")
    parser.add_argument("--cd", type=float, default=None)
    parser.add_argument("--area", type=float, default=None)
    parser.add_argument("--cp-aero", type=float, default=None, help="aero center-of-pressure offset [m]")
    parser.add_argument("--rho", type=float, default=None, help="density override [kg/m^3]")
    parser.add_argument("--area-sun", type=float, default=None)
    parser.add_argument("--reflectance", type=float, default=None)
    parser.add_argument("--cp-sun", type=float, default=None)
    parser.add_argument("--solar-constant", type=float, default=None)
    parser.add_argument("--dipole", type=float, default=None, help="dipole moment [A*m^2]")
    parser.add_argument("--b-field", type=float, default=None, help="magnetic field [T]")
    parser.add_argument("--mag-angle", type=float, default=None, help="angle between M and B [rad]")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    rows: list[tuple[str, float]] = []
    notes: list[str] = []
    labels: list[str] = []
    values: list[float] = []
    try:
        radius = None
        if args.a is not None:
            if args.a <= 0.0:
                raise ValueError("--a must be positive")
            radius = args.a
        elif args.alt is not None:
            if args.alt < 0.0:
                raise ValueError("--alt must be >= 0")
            radius = R0_ORBIT + args.alt
        gg = args.i_z is not None or args.i_y is not None or args.theta is not None
        if gg:
            if None in (args.i_z, args.i_y, args.theta) or radius is None:
                raise ValueError("gravity gradient needs --i-z, --i-y, --theta, and --alt or --a")
            n2 = orbit_rate_squared(radius)
            torque = gravity_gradient_torque(args.i_z, args.i_y, args.theta, n2)
            rows.extend([
                ("n2_rad2_s2", n2),
                ("T_gg_N_m", torque),
            ])
            labels.append("gravity gradient")
            values.append(torque)
        aero = args.cd is not None or args.area is not None or args.cp_aero is not None or args.rho is not None
        if aero:
            if None in (args.cd, args.area, args.cp_aero):
                raise ValueError("aerodynamic torque needs --cd, --area, and --cp-aero")
            if radius is None:
                raise ValueError("aerodynamic torque needs --alt or --a so the circular speed is known")
            if args.alt is None and args.rho is None:
                raise ValueError("aerodynamic torque needs --alt or --rho for density")
            alt = args.alt if args.alt is not None else radius - R0_ORBIT
            rho, source = density_at(alt, args.rho)
            speed = circular_speed(radius if radius is not None else R0_ORBIT + alt)
            torque = aerodynamic_torque(rho, speed, args.cd, args.area, args.cp_aero)
            rows.extend([
                ("rho_kg_m3", rho),
                ("density_source", source),
                ("V_m_s", speed),
                ("T_aero_N_m", torque),
            ])
            labels.append("aerodynamic")
            values.append(torque)
        solar_on = args.area_sun is not None or args.reflectance is not None or args.cp_sun is not None
        if solar_on:
            if None in (args.area_sun, args.reflectance, args.cp_sun):
                raise ValueError("solar torque needs --area-sun, --reflectance, and --cp-sun")
            solar = S_DEFAULT if args.solar_constant is None else args.solar_constant
            if solar <= 0.0:
                raise ValueError("--solar-constant must be positive")
            torque = solar_torque(solar, args.area_sun, args.reflectance, args.cp_sun)
            rows.extend([("S_W_m2", solar), ("T_solar_N_m", torque)])
            labels.append("solar")
            values.append(torque)
        magnetic_on = args.dipole is not None or args.b_field is not None
        if magnetic_on:
            if None in (args.dipole, args.b_field):
                raise ValueError("magnetic torque needs --dipole and --b-field")
            angle = math.pi / 2.0 if args.mag_angle is None else args.mag_angle
            torque = magnetic_torque(args.dipole, args.b_field, angle)
            rows.extend([("mag_angle_rad", angle), ("T_mag_N_m", torque)])
            if args.mag_angle is None:
                notes.append("magnetic angle omitted; perpendicular M and B, maximum torque")
            labels.append("magnetic")
            values.append(torque)
        if not rows:
            raise ValueError("pass the inputs for at least one torque")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(labels, values, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    # density_source is a string stuffed into rows. emit expects floats for the second item
    # except notes. Handle mixed types.
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "environmental disturbance torques")
    for note in notes:
        print_kv("note", note)
    for key, value in rows:
        print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph))
    return 0


if __name__ == "__main__":
    sys.exit(main())
