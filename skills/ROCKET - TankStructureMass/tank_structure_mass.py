#!/usr/bin/env python3
"""Tank and structure inert mass from propellant volume, MEOP, and allowables.

Thin-wall membrane sizing at design pressure p = design_factor * MEOP.
Sphere: t = p R / (2 S eta), m_tank = 4 pi R^2 t rho_mat * boss.
Cylinder: barrel hoop t_barrel = p R / (S eta); flat heads use
t_head = R * sqrt(p / (S eta)) (UG-34 C=0.25 on diameter).
Refuses when governing t/R >= 0.1. Residuals are inert.
Total inert = tank + structure + residual, for ROCKET - PayloadtoDeltaV.
"""

from __future__ import annotations

import argparse
import math
import sys

CHECK_TOL = 1e-9
THIN_WALL_LIMIT = 0.1

# ASME UG-34-style integral flat-head coefficient for t = d * sqrt(C p / (S eta)).
# With d = 2 R this is t_head = R * sqrt(4 C p / (S eta)); C = 0.25 => t_head = R * sqrt(p/(S eta)).
FLAT_HEAD_C = 0.25

ASSUMPTIONS = (
    "thin-wall membrane tank; "
    "design pressure p = design_factor * MEOP (factor default 1, not invented); "
    "sphere t = p R / (2 S eta); "
    "cylinder barrel hoop t_barrel = p R / (S eta); "
    "cylinder flat heads use plate formula t_head = R * sqrt(p / (S eta)) "
    "(ASME UG-34 integral flat head with C = 0.25 on diameter); "
    "volume is loaded liquid propellant volume used as tank internal barrel volume "
    "(flat heads add no internal volume; no ullage unless folded into volume); "
    "residuals fraction f_r is m_residual / m_loaded; "
    "usable propellant mp = (1 - f_r) * m_loaded; "
    "residual propellant is inert; "
    "structure mass is --structure kg or --structure-factor times tank shell; "
    "inert = tank + structure + residual for PayloadtoDeltaV inert; "
    "refuses when governing t/R >= 0.1 (thin-wall model not valid)"
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


def require_fraction(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0 or value >= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1)")


def sphere_radius(volume: float) -> float:
    """Inner radius of a sphere with internal volume V."""
    return (3.0 * volume / (4.0 * math.pi)) ** (1.0 / 3.0)


def sphere_thickness(pressure: float, radius: float, allowable: float, eta: float) -> float:
    """Thin sphere: t = p R / (2 S eta)."""
    return pressure * radius / (2.0 * allowable * eta)


def sphere_tank_mass(
    volume: float,
    pressure: float,
    allowable: float,
    rho_mat: float,
    eta: float,
    boss: float,
) -> tuple[float, float, float]:
    """Return (R, t, m_tank) for a thin spherical tank."""
    radius = sphere_radius(volume)
    thickness = sphere_thickness(pressure, radius, allowable, eta)
    area = 4.0 * math.pi * radius * radius
    mass = area * thickness * rho_mat * boss
    # Closed form: m = (3/2) * p * V * rho_mat * boss / (S eta)
    closed = 1.5 * pressure * volume * rho_mat * boss / (allowable * eta)
    if not close(mass, closed):
        raise ValueError("sphere shell mass disagrees with (3/2) p V rho / (S eta)")
    return radius, thickness, mass


def cylinder_length(volume: float, radius: float) -> float:
    """Barrel length for a right circular cylinder of volume V."""
    return volume / (math.pi * radius * radius)


def cylinder_thickness(pressure: float, radius: float, allowable: float, eta: float) -> float:
    """Thin cylinder hoop: t = p R / (S eta)."""
    return pressure * radius / (allowable * eta)


def flat_head_thickness(pressure: float, radius: float, allowable: float, eta: float) -> float:
    """Integral flat circular head: t = R * sqrt(p / (S eta)) for C = 0.25 on diameter."""
    return radius * math.sqrt(pressure / (allowable * eta))


def cylinder_tank_mass(
    volume: float,
    radius: float,
    pressure: float,
    allowable: float,
    rho_mat: float,
    eta: float,
    boss: float,
) -> tuple[float, float, float, float]:
    """Return (L, t_barrel, t_head, m_tank) for a cylinder with two flat heads."""
    length = cylinder_length(volume, radius)
    if length <= 0.0:
        raise ValueError("cylinder barrel length must be > 0; reduce --radius or increase --volume")
    t_barrel = cylinder_thickness(pressure, radius, allowable, eta)
    t_head = flat_head_thickness(pressure, radius, allowable, eta)
    lateral = 2.0 * math.pi * radius * length
    heads = 2.0 * math.pi * radius * radius
    mass = (lateral * t_barrel + heads * t_head) * rho_mat * boss
    return length, t_barrel, t_head, mass


def propellant_masses(volume: float, rho: float, residuals: float) -> tuple[float, float, float]:
    """Loaded, residual, and usable propellant mass."""
    loaded = rho * volume
    residual = residuals * loaded
    usable = loaded - residual
    return loaded, residual, usable


def structure_mass(
    tank_mass: float,
    structure_kg: float | None,
    structure_factor: float | None,
) -> tuple[float, str]:
    if structure_kg is not None and structure_factor is not None:
        raise ValueError("pass --structure or --structure-factor, not both")
    if structure_kg is not None:
        if not math.isfinite(structure_kg) or structure_kg < 0.0:
            raise ValueError("structure mass must be finite and >= 0")
        return structure_kg, "absolute"
    if structure_factor is not None:
        if not math.isfinite(structure_factor) or structure_factor < 0.0:
            raise ValueError("structure factor must be finite and >= 0")
        return structure_factor * tank_mass, "factor"
    return 0.0, "none"


def thin_wall_flag(radius: float, thickness: float) -> str:
    if thickness / radius < THIN_WALL_LIMIT:
        return "yes"
    return "no"


def evaluate(
    volume: float,
    rho: float,
    residuals: float,
    meop: float,
    allowable: float,
    rho_mat: float,
    shape: str,
    radius: float | None,
    eta: float,
    design_factor: float,
    boss: float,
    structure_kg: float | None,
    structure_factor: float | None,
) -> dict[str, float | str]:
    require_positive("propellant volume", volume)
    require_positive("propellant density", rho)
    require_fraction("residuals fraction", residuals)
    require_positive("MEOP", meop)
    require_positive("allowable stress", allowable)
    require_positive("material density", rho_mat)
    require_positive("weld efficiency", eta)
    if eta > 1.0:
        raise ValueError("weld efficiency must be <= 1")
    require_positive("design factor", design_factor)
    require_positive("boss factor", boss)

    pressure = design_factor * meop
    loaded, residual, usable = propellant_masses(volume, rho, residuals)

    shape_key = shape.strip().lower()
    t_head: float | None = None
    if shape_key == "sphere":
        if radius is not None:
            raise ValueError("do not pass --radius with --shape sphere")
        r, thickness, m_tank = sphere_tank_mass(
            volume, pressure, allowable, rho_mat, eta, boss
        )
        length: float | None = None
        geom_radius = r
        t_governing = thickness
    elif shape_key == "cylinder":
        if radius is None:
            raise ValueError("cylinder shape requires --radius")
        require_positive("tank radius", radius)
        length, thickness, t_head, m_tank = cylinder_tank_mass(
            volume, radius, pressure, allowable, rho_mat, eta, boss
        )
        geom_radius = radius
        t_governing = max(thickness, t_head)
    else:
        raise ValueError("shape must be sphere or cylinder")

    t_over_r = t_governing / geom_radius
    if t_over_r >= THIN_WALL_LIMIT:
        raise ValueError(
            f"governing t/R = {t_over_r:.6g} >= {THIN_WALL_LIMIT}; "
            "thin-wall tank model is not valid (reduce MEOP/design-factor or raise allowable)"
        )

    m_struct, struct_source = structure_mass(m_tank, structure_kg, structure_factor)
    m_inert = m_tank + m_struct + residual

    result: dict[str, float | str] = {
        "shape": shape_key,
        "V_p_m3": volume,
        "rho_kg_m3": rho,
        "residuals_fraction": residuals,
        "MEOP_Pa": meop,
        "design_factor": design_factor,
        "p_design_Pa": pressure,
        "allowable_Pa": allowable,
        "rho_mat_kg_m3": rho_mat,
        "eta": eta,
        "boss_factor": boss,
        "R_m": geom_radius,
        "t_m": t_governing,
        "t_over_R": t_over_r,
        "thin_wall": thin_wall_flag(geom_radius, t_governing),
        "m_loaded_kg": loaded,
        "m_usable_kg": usable,
        "m_residual_kg": residual,
        "m_tank_kg": m_tank,
        "m_structure_kg": m_struct,
        "structure_source": struct_source,
        "m_inert_kg": m_inert,
        "payload_to_deltav_mp_kg": usable,
        "payload_to_deltav_inert_kg": m_inert,
    }
    if length is not None:
        result["L_m"] = length
        result["t_barrel_m"] = thickness
        if t_head is not None:
            result["t_head_m"] = t_head
            result["flat_head_C"] = FLAT_HEAD_C
    if struct_source == "factor" and structure_factor is not None:
        result["structure_factor"] = structure_factor
    return result


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def run_check() -> int:
    # Sphere closed form: V=1, p=2e6, S=2e8, rho_mat=2700, eta=1, boss=1
    # R = (3/(4 pi))^(1/3), t = p R /(2 S), m = 1.5 p V rho / S
    volume = 1.0
    pressure = 2.0e6
    allowable = 2.0e8
    rho_mat = 2700.0
    r, t, m_tank = sphere_tank_mass(volume, pressure, allowable, rho_mat, 1.0, 1.0)
    m_closed = 1.5 * pressure * volume * rho_mat / allowable
    if not close(m_tank, m_closed):
        return fail(f"CHECK FAIL: sphere mass {m_tank}, expected {m_closed}")
    if not close(r, sphere_radius(volume)):
        return fail("CHECK FAIL: sphere radius")
    if not close(t, sphere_thickness(pressure, r, allowable, 1.0)):
        return fail("CHECK FAIL: sphere thickness")
    if not close((4.0 / 3.0) * math.pi * r**3, volume):
        return fail("CHECK FAIL: sphere volume round-trip")

    # Cylinder: V = pi R^2 L with R=0.5, L=2 => V = pi/2
    radius = 0.5
    length_want = 2.0
    vol_cyl = math.pi * radius * radius * length_want
    length, t_barrel, t_head, m_c = cylinder_tank_mass(
        vol_cyl, radius, pressure, allowable, rho_mat, 1.0, 1.0
    )
    if not close(length, length_want):
        return fail(f"CHECK FAIL: cylinder L = {length}, expected {length_want}")
    t_barrel_expect = pressure * radius / allowable
    t_head_expect = radius * math.sqrt(pressure / allowable)
    if not close(t_barrel, t_barrel_expect):
        return fail(f"CHECK FAIL: cylinder t_barrel = {t_barrel}, expected {t_barrel_expect}")
    if not close(t_head, t_head_expect):
        return fail(f"CHECK FAIL: cylinder t_head = {t_head}, expected {t_head_expect}")
    # Flat heads must be thicker than hoop for this pressure ratio.
    if t_head <= t_barrel_expect:
        return fail("CHECK FAIL: flat head should be thicker than hoop wall")
    lateral = 2.0 * math.pi * radius * length_want
    heads = 2.0 * math.pi * radius * radius
    m_expect = (lateral * t_barrel_expect + heads * t_head_expect) * rho_mat
    if not close(m_c, m_expect):
        return fail("CHECK FAIL: cylinder mass with plate heads")
    # Same hoop t on heads would under-predict mass (regression guard).
    m_wrong = (lateral + heads) * t_barrel_expect * rho_mat
    if m_c <= m_wrong:
        return fail("CHECK FAIL: plate-head mass not heavier than hoop-on-heads")

    # Residuals and inert stack
    rho = 1000.0
    residuals = 0.02
    loaded, residual, usable = propellant_masses(volume, rho, residuals)
    if not close(loaded, 1000.0) or not close(residual, 20.0) or not close(usable, 980.0):
        return fail("CHECK FAIL: propellant mass split")
    m_struct, src = structure_mass(m_tank, None, 0.1)
    if src != "factor" or not close(m_struct, 0.1 * m_tank):
        return fail("CHECK FAIL: structure factor")
    m_inert = m_tank + m_struct + residual
    out = evaluate(
        volume=volume,
        rho=rho,
        residuals=residuals,
        meop=pressure,
        allowable=allowable,
        rho_mat=rho_mat,
        shape="sphere",
        radius=None,
        eta=1.0,
        design_factor=1.0,
        boss=1.0,
        structure_kg=None,
        structure_factor=0.1,
    )
    if not close(float(out["m_inert_kg"]), m_inert):
        return fail("CHECK FAIL: evaluate inert")
    if not close(float(out["payload_to_deltav_mp_kg"]), usable):
        return fail("CHECK FAIL: payload mp")
    if not close(float(out["payload_to_deltav_inert_kg"]), m_inert):
        return fail("CHECK FAIL: payload inert")
    if out["thin_wall"] != "yes":
        return fail("CHECK FAIL: thin_wall expected yes")

    # Thick-wall must be refused (not silently returned).
    try:
        evaluate(
            volume=0.001,
            rho=1000.0,
            residuals=0.0,
            meop=5.0e8,
            allowable=1.0e8,
            rho_mat=rho_mat,
            shape="sphere",
            radius=None,
            eta=1.0,
            design_factor=1.0,
            boss=1.0,
            structure_kg=None,
            structure_factor=None,
        )
    except ValueError as exc:
        if "thin-wall" not in str(exc):
            return fail(f"CHECK FAIL: thick-wall error text: {exc}")
    else:
        return fail("CHECK FAIL: thick-wall sphere was accepted")

    # Design factor doubles pressure and mass for a sphere
    out2 = evaluate(
        volume=volume,
        rho=rho,
        residuals=0.0,
        meop=pressure,
        allowable=allowable,
        rho_mat=rho_mat,
        shape="sphere",
        radius=None,
        eta=1.0,
        design_factor=2.0,
        boss=1.0,
        structure_kg=0.0,
        structure_factor=None,
    )
    if not close(float(out2["p_design_Pa"]), 2.0 * pressure):
        return fail("CHECK FAIL: design pressure")
    if not close(float(out2["m_tank_kg"]), 2.0 * m_tank):
        return fail("CHECK FAIL: design factor mass scaling")

    print("check: pass")
    print_kv("sphere_m_tank_kg", m_tank)
    print_kv("cylinder_m_tank_kg", m_c)
    print_kv("m_inert_kg", m_inert)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Tank and structure inert mass from propellant volume, MEOP, "
            "material allowables, and residuals fraction."
        )
    )
    parser.add_argument("--volume", type=float, default=None, help="loaded propellant volume [m^3]")
    parser.add_argument("--rho", type=float, default=None, help="propellant density [kg/m^3]")
    parser.add_argument(
        "--residuals",
        type=float,
        default=None,
        help="residuals fraction of loaded propellant mass [0, 1)",
    )
    parser.add_argument("--meop", type=float, default=None, help="maximum expected operating pressure [Pa]")
    parser.add_argument("--allowable", type=float, default=None, help="material allowable stress [Pa]")
    parser.add_argument("--rho-mat", type=float, default=None, help="tank material density [kg/m^3]")
    parser.add_argument(
        "--shape",
        type=str,
        default="sphere",
        help="tank shape: sphere (default) or cylinder",
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=None,
        help="inner radius [m]; required for cylinder",
    )
    parser.add_argument(
        "--eta",
        type=float,
        default=1.0,
        help="weld efficiency (default 1)",
    )
    parser.add_argument(
        "--design-factor",
        type=float,
        default=1.0,
        help="multiplies MEOP to design pressure (default 1)",
    )
    parser.add_argument(
        "--boss-factor",
        type=float,
        default=1.0,
        help="multiplies tank shell mass for bosses/welds (default 1)",
    )
    parser.add_argument(
        "--structure",
        type=float,
        default=None,
        help="additional structure mass [kg]",
    )
    parser.add_argument(
        "--structure-factor",
        type=float,
        default=None,
        help="additional structure mass as a factor of tank shell mass",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--volume": args.volume,
        "--rho": args.rho,
        "--residuals": args.residuals,
        "--meop": args.meop,
        "--allowable": args.allowable,
        "--rho-mat": args.rho_mat,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --volume, --rho, --residuals, --meop, --allowable, "
            f"and --rho-mat; missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(
            volume=args.volume,
            rho=args.rho,
            residuals=args.residuals,
            meop=args.meop,
            allowable=args.allowable,
            rho_mat=args.rho_mat,
            shape=args.shape,
            radius=args.radius,
            eta=args.eta,
            design_factor=args.design_factor,
            boss=args.boss_factor,
            structure_kg=args.structure,
            structure_factor=args.structure_factor,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "shape",
        "V_p_m3",
        "rho_kg_m3",
        "residuals_fraction",
        "MEOP_Pa",
        "design_factor",
        "p_design_Pa",
        "allowable_Pa",
        "rho_mat_kg_m3",
        "eta",
        "boss_factor",
        "R_m",
        "L_m",
        "t_barrel_m",
        "t_head_m",
        "flat_head_C",
        "t_m",
        "t_over_R",
        "thin_wall",
        "m_loaded_kg",
        "m_usable_kg",
        "m_residual_kg",
        "m_tank_kg",
        "m_structure_kg",
        "structure_source",
        "structure_factor",
        "m_inert_kg",
        "payload_to_deltav_mp_kg",
        "payload_to_deltav_inert_kg",
    ):
        if key in result:
            print_kv(key, result[key])

    print_kv(
        "payload_to_deltav_stage",
        (
            f"mp={result['payload_to_deltav_mp_kg']:.8g},"
            f"inert={result['payload_to_deltav_inert_kg']:.8g}"
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
