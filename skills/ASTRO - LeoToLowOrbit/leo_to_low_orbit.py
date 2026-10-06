#!/usr/bin/env python3
"""Patched-conic mission from a circular LEO to a circular low orbit.

The heliocentric coast is the Hohmann half-ellipse. Each planet-centered burn
is the impulsive periapsis burn from a circular orbit onto the hyperbola with
the selected excess speed, or the reverse capture.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
HELIO_DIR = SKILL_DIR.parent / "ASTRO - HeliocentricHohmann"
BODY_DIR = SKILL_DIR.parent / "ASTRO - SolarSystemBody"
for folder in (HELIO_DIR, BODY_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import heliocentric_hohmann as helio  # noqa: E402
import solar_system_body as bodies  # noqa: E402

CHECK_TOL = 1e-9
PLOT_TITLE = "LEO to low orbit"
CHECK_H_LEO_M = 400000.0
CHECK_H_ARRIVE_M = 400000.0
ASSUMPTIONS = (
    "patched-conic transfer from a circular LEO to a circular low orbit "
    "about another planet or Pluto; Earth departure hyperbola, one "
    "heliocentric Hohmann half-ellipse, and a target arrival hyperbola; "
    "each rocket burn is impulsive at periapsis; the whole inclination "
    "difference is paid at the apsis with the smaller total delta-v; there "
    "is no third burn and no separate plane_change_impulse; the LEO plane "
    "is assumed alignable with the departure asymptote; spheres of influence "
    "use sphere_of_influence_radius; eccentricity selects only the circular "
    "heliocentric radius; this is not an integrated three-body arc and it "
    "does not size a rocket"
)


@dataclass(frozen=True)
class Burn:
    dv: float
    v_periapsis: float
    v_circular: float


@dataclass(frozen=True)
class Mission:
    transfer: helio.Hohmann
    h_leo: float
    h_arrive: float
    r_leo: float
    r_low: float
    mu_earth: float
    mu_target: float
    soi_earth: float
    soi_target: float
    plane_change_at: str
    depart: Burn
    capture: Burn
    dv_total: float
    dv_total_if_depart: float
    dv_total_if_arrive: float
    vinf_depart: float
    vinf_arrive: float
    c3: float


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = "inf" if math.isinf(value) else f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = max(abs(expected), abs(got), 1.0 if scale is None else abs(scale))
    return abs(got - expected) <= CHECK_TOL * span


def park_burn(mu: float, radius: float, vinf: float) -> Burn:
    if vinf < 0.0:
        raise ValueError("excess speed must be >= 0")
    v_periapsis = math.sqrt(vinf * vinf + 2.0 * mu / radius)
    v_circular = math.sqrt(mu / radius)
    return Burn(v_periapsis - v_circular, v_periapsis, v_circular)


def sphere_of_influence(distance: float, mu_body: float, mu_sun: float) -> float:
    """sphere_of_influence_radius."""
    return distance * (mu_body / mu_sun) ** (2.0 / 5.0)


def solve_mission(target_name: str, h_leo: float, h_arrive: float, radius_mode: str) -> Mission:
    if not math.isfinite(h_leo) or h_leo < 0.0:
        raise ValueError("h-leo must be finite and >= 0")
    if not math.isfinite(h_arrive) or h_arrive < 0.0:
        raise ValueError("h-arrive must be finite and >= 0")
    table = bodies.load_bodies()
    earth = bodies.require_body(table, "earth")
    target = bodies.require_body(table, target_name)
    sun = table["sun"]
    if target.name in {"earth", "sun"}:
        raise ValueError("the target must be another planet or pluto")
    if target.kind not in {"planet", "dwarf"}:
        raise ValueError("the target must be another planet or pluto")
    r_leo = earth.radius + h_leo
    r_low = target.radius + h_arrive
    if r_low < target.radius:
        raise ValueError("arrival radius is below the surface")
    transfer = helio.from_names("earth", target.name, radius_mode)
    depart_case_vinf = (transfer.vinf_depart_inclined, transfer.vinf_arrive_coplanar)
    arrive_case_vinf = (transfer.vinf_depart_coplanar, transfer.vinf_arrive_inclined)
    depart_case = (
        park_burn(earth.mu, r_leo, depart_case_vinf[0]),
        park_burn(target.mu, r_low, depart_case_vinf[1]),
    )
    arrive_case = (
        park_burn(earth.mu, r_leo, arrive_case_vinf[0]),
        park_burn(target.mu, r_low, arrive_case_vinf[1]),
    )
    total_depart = depart_case[0].dv + depart_case[1].dv
    total_arrive = arrive_case[0].dv + arrive_case[1].dv
    if close_enough(total_depart, total_arrive, max(total_depart, total_arrive, 1.0)) or total_depart < total_arrive:
        chosen = "depart"
        burns = depart_case
        vinfs = depart_case_vinf
        total = total_depart
    else:
        chosen = "arrive"
        burns = arrive_case
        vinfs = arrive_case_vinf
        total = total_arrive
    return Mission(
        transfer=transfer,
        h_leo=h_leo,
        h_arrive=h_arrive,
        r_leo=r_leo,
        r_low=r_low,
        mu_earth=earth.mu,
        mu_target=target.mu,
        soi_earth=sphere_of_influence(transfer.r_depart, earth.mu, sun.mu),
        soi_target=sphere_of_influence(transfer.r_arrive, target.mu, sun.mu),
        plane_change_at=chosen,
        depart=burns[0],
        capture=burns[1],
        dv_total=total,
        dv_total_if_depart=total_depart,
        dv_total_if_arrive=total_arrive,
        vinf_depart=vinfs[0],
        vinf_arrive=vinfs[1],
        c3=vinfs[0] * vinfs[0],
    )


def report(mission: Mission, graph: Path) -> None:
    transfer = mission.transfer
    print_kv("to", transfer.arrive_name)
    print_kv("class", "dwarf" if transfer.arrive_name == "pluto" else "planet")
    print_kv("radius_mode", transfer.radius_mode)
    print_kv("path_1", "circular LEO")
    print_kv("r_leo_m", mission.r_leo)
    print_kv("h_leo_m", mission.h_leo)
    print_kv("path_2", "Earth departure hyperbola")
    print_kv("vinf_depart_m_s", mission.vinf_depart)
    print_kv("C3_m2_s2", mission.c3)
    print_kv("dv_depart_m_s", mission.depart.dv)
    print_kv("v_periapsis_depart_m_s", mission.depart.v_periapsis)
    print_kv("v_circular_leo_m_s", mission.depart.v_circular)
    print_kv("path_3", "Earth sphere of influence")
    print_kv("soi_earth_m", mission.soi_earth)
    print_kv("path_4", "heliocentric half-ellipse")
    print_kv("r_helio_depart_m", transfer.r_depart)
    print_kv("r_helio_arrive_m", transfer.r_arrive)
    print_kv("a_m", transfer.a)
    print_kv("e", transfer.e)
    print_kv("direction", transfer.direction)
    print_kv("tof_s", transfer.tof)
    print_kv("period_s", transfer.period)
    print_kv("phase_rad", transfer.phase)
    print_kv("synodic_s", transfer.synodic)
    print_kv("path_5", "target sphere of influence and arrival hyperbola")
    print_kv("soi_target_m", mission.soi_target)
    print_kv("vinf_arrive_m_s", mission.vinf_arrive)
    print_kv("path_6", "circular low orbit")
    print_kv("r_low_m", mission.r_low)
    print_kv("h_arrive_m", mission.h_arrive)
    print_kv("dv_capture_m_s", mission.capture.dv)
    print_kv("v_periapsis_arrive_m_s", mission.capture.v_periapsis)
    print_kv("v_circular_low_m_s", mission.capture.v_circular)
    print_kv("di_rad", transfer.di)
    print_kv("plane_change_at", mission.plane_change_at)
    print_kv("dv_total_if_plane_change_at_depart_m_s", mission.dv_total_if_depart)
    print_kv("dv_total_if_plane_change_at_arrive_m_s", mission.dv_total_if_arrive)
    print_kv("dv_total_m_s", mission.dv_total)
    print_kv("graph", str(graph))
    print_kv("assumptions", ASSUMPTIONS)
    print_kv(
        "warning",
        "circular heliocentric orbits; eccentricity is used only to choose the radius",
    )
    print_kv("warning", "patched conic, not an integrated three-body arc")
    print_kv("warning", "the LEO plane is assumed alignable with the departure asymptote")


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    mission = solve_mission("mars", CHECK_H_LEO_M, CHECK_H_ARRIVE_M, "mean")
    transfer = mission.transfer
    if not close_enough(transfer.tof, 0.5 * transfer.period, transfer.period):
        return fail("time of flight is not half the period")
    if not close_enough(mission.c3, mission.vinf_depart ** 2, mission.c3):
        return fail("C3 is not v_inf squared")
    if not close_enough(mission.dv_total, mission.depart.dv + mission.capture.dv, mission.dv_total):
        return fail("total is not the sum of the two burns")
    smaller = min(mission.dv_total_if_depart, mission.dv_total_if_arrive)
    if not close_enough(mission.dv_total, smaller, smaller):
        return fail("selected total is not the smaller placement")
    turned = math.remainder(transfer.phase + transfer.n_arrive * transfer.tof - math.pi, 2.0 * math.pi)
    if not close_enough(turned, 0.0, 1.0):
        return fail("phase angle identity")
    flat = helio.solve_hohmann(
        transfer.mu,
        transfer.r_depart,
        transfer.r_arrive,
        0.0,
        0.0,
        "radii",
        "mean",
        "earth",
        "mars",
    )
    if not close_enough(flat.vinf_depart_inclined, flat.vinf_depart_coplanar, 1.0):
        return fail("zero inclination did not match the coplanar excess")
    if not close_enough(flat.vinf_arrive_inclined, flat.vinf_arrive_coplanar, 1.0):
        return fail("zero inclination did not match the arrival excess")
    try:
        solve_mission("earth", CHECK_H_LEO_M, CHECK_H_ARRIVE_M, "mean")
    except ValueError:
        pass
    else:
        return fail("Earth as a target was accepted")
    try:
        solve_mission("mars", -1.0, CHECK_H_ARRIVE_M, "mean")
    except ValueError:
        pass
    else:
        return fail("a negative LEO altitude was accepted")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "leo_to_low_orbit.png"
        helio.plot_hohmann(out, transfer, PLOT_TITLE, arrows=True)
        if not out.read_bytes().startswith(b"\x89PNG"):
            return fail("plot did not write a PNG")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delta-v from a circular LEO to a circular low orbit about another planet or Pluto."
    )
    parser.add_argument("--to", type=str, default=None, help="target planet or pluto")
    parser.add_argument("--h-leo", type=float, default=None, help="LEO geometric altitude, m")
    parser.add_argument("--h-arrive", type=float, default=None, help="target low-orbit geometric altitude, m")
    parser.add_argument(
        "--radius-mode",
        choices=bodies.RADIUS_MODES,
        default="mean",
        help="which circular heliocentric radius to use",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    args = parser.parse_args(argv)
    if args.check:
        return run_check()
    try:
        if args.to is None:
            raise ValueError("pass --to")
        if args.h_leo is None:
            raise ValueError("pass --h-leo")
        if args.h_arrive is None:
            raise ValueError("pass --h-arrive")
        mission = solve_mission(args.to, args.h_leo, args.h_arrive, args.radius_mode)
        out = Path(args.out) if args.out else SKILL_DIR / "leo_to_low_orbit.png"
        helio.plot_hohmann(out.resolve(), mission.transfer, PLOT_TITLE, arrows=True)
        report(mission, out.resolve())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
