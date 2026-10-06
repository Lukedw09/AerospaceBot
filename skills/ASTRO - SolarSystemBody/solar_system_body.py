#!/usr/bin/env python3
"""Solar-system gravitational parameters and heliocentric elements.

Constants are the NSSDCA fact sheets in sources.md (V93), except Earth's
radius and mu, which follow the catalogue Earth used by Hohmann:
mu = g0 * R0^2.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

G0 = 9.80665
R0_EARTH = 6.3742e6
CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent
DATA_PATH = SKILL_DIR / "bodies.json"
ORBIT_ORDER = (
    "mercury",
    "venus",
    "earth",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
)
RADIUS_MODES = ("mean", "perihelion", "aphelion")
ASSUMPTIONS = (
    "point-mass gravitational parameters and Keplerian heliocentric elements "
    "from the NSSDCA planetary fact sheets; Earth radius is the catalogue "
    "value 6374200 m and Earth mu is g0*R0^2 with g0 = 9.80665 m/s^2; "
    "a radius is distance from the body center; heliocentric mean radius is "
    "the semi-major axis, perihelion is a*(1-e), and aphelion is a*(1+e); "
    "the Sun is the central body and has no heliocentric orbit; the Moon is "
    "omitted; Pluto is included as a dwarf planet"
)


@dataclass(frozen=True)
class Body:
    name: str
    kind: str
    mu: float
    radius: float
    a_helio: float | None
    e: float | None
    i_deg: float | None

    @property
    def i_rad(self) -> float | None:
        if self.i_deg is None:
            return None
        return math.radians(self.i_deg)

    def heliocentric_radius(self, mode: str) -> float:
        if self.a_helio is None or self.e is None:
            raise ValueError(f"{self.name} has no heliocentric orbit")
        if mode == "mean":
            return self.a_helio
        if mode == "perihelion":
            return self.a_helio * (1.0 - self.e)
        if mode == "aphelion":
            return self.a_helio * (1.0 + self.e)
        raise ValueError(f"unknown radius mode {mode}")


def earth_mu() -> float:
    return G0 * R0_EARTH * R0_EARTH


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = max(abs(expected), abs(got), 1.0 if scale is None else abs(scale))
    return abs(got - expected) <= CHECK_TOL * span


def load_bodies(path: Path | None = None) -> dict[str, Body]:
    data_path = path or DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    bodies: dict[str, Body] = {}
    for row in raw["bodies"]:
        name = str(row["name"]).lower()
        mu = row["mu_m3_s2"]
        if name == "earth" and mu is None:
            mu = earth_mu()
        bodies[name] = Body(
            name=name,
            kind=str(row["class"]),
            mu=float(mu),
            radius=float(row["radius_m"]),
            a_helio=None if row["a_helio_m"] is None else float(row["a_helio_m"]),
            e=None if row["e"] is None else float(row["e"]),
            i_deg=None if row["i_deg"] is None else float(row["i_deg"]),
        )
    return bodies


def require_body(bodies: dict[str, Body], name: str) -> Body:
    key = name.strip().lower()
    if key not in bodies:
        known = ", ".join(body.name for body in bodies.values())
        raise ValueError(f"unknown body {name!r}; known bodies are {known}")
    return bodies[key]


def report_body(body: Body) -> None:
    print_kv("name", body.name)
    print_kv("class", body.kind)
    print_kv("mu_m3_s2", body.mu)
    print_kv("radius_m", body.radius)
    if body.a_helio is None:
        print_kv("a_helio_m", "none")
        print_kv("e", "none")
        print_kv("i_rad", "none")
        print_kv("i_deg", "none")
        print_kv("r_mean_m", "none")
        print_kv("r_perihelion_m", "none")
        print_kv("r_aphelion_m", "none")
        print_kv("warning", "the Sun is the central body and has no heliocentric orbit")
    else:
        print_kv("a_helio_m", body.a_helio)
        print_kv("e", body.e)
        print_kv("i_rad", body.i_rad)
        print_kv("i_deg", body.i_deg)
        print_kv("r_mean_m", body.heliocentric_radius("mean"))
        print_kv("r_perihelion_m", body.heliocentric_radius("perihelion"))
        print_kv("r_aphelion_m", body.heliocentric_radius("aphelion"))
    if body.name == "earth":
        print_kv("mu_source", "g0_R0")
        print_kv("radius_source", "catalogue_R0")
    elif body.name == "sun":
        print_kv("mu_source", "V93")
        print_kv("radius_source", "V93_volumetric_mean")
    else:
        print_kv("mu_source", "V93")
        print_kv("radius_source", "V93_equatorial")
    print_kv("assumptions", ASSUMPTIONS)


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    bodies = load_bodies()
    if tuple(body.name for body in bodies.values() if body.name != "sun") != ORBIT_ORDER:
        return fail("orbit order is not Mercury through Pluto")
    previous = 0.0
    for name in ORBIT_ORDER:
        body = bodies[name]
        if not (body.mu > 0.0 and body.radius > 0.0):
            return fail(f"{name} mu or radius is not positive")
        if body.a_helio is None or body.e is None or body.i_deg is None:
            return fail(f"{name} is missing heliocentric elements")
        if not (0.0 <= body.e < 1.0):
            return fail(f"{name} eccentricity is outside [0, 1)")
        if body.a_helio <= previous:
            return fail("heliocentric semi-major axes do not increase")
        previous = body.a_helio
        peri = body.heliocentric_radius("perihelion")
        apo = body.heliocentric_radius("aphelion")
        if not (peri < body.a_helio < apo or body.e == 0.0):
            return fail(f"{name} perihelion and aphelion are inconsistent")
    earth = bodies["earth"]
    if earth.radius != R0_EARTH:
        return fail("Earth radius is not the catalogue R0")
    if not close_enough(earth.mu, earth_mu(), earth_mu()):
        return fail("Earth mu is not g0*R0^2")
    if earth.i_deg != 0.0:
        return fail("Earth inclination is not zero")
    sun = bodies["sun"]
    if sun.kind != "star" or sun.a_helio is not None:
        return fail("the Sun must be the central star")
    if bodies["pluto"].kind != "dwarf":
        return fail("Pluto must be class dwarf")
    pluto_peri = bodies["pluto"].heliocentric_radius("perihelion")
    if pluto_peri >= bodies["neptune"].a_helio:
        return fail("Pluto perihelion was expected inside Neptune's mean orbit")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Look up a solar-system body.")
    parser.add_argument("--body", type=str, default=None, help="body name")
    parser.add_argument("--list", action="store_true", help="print every body")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    args = parser.parse_args(argv)
    if args.check:
        return run_check()
    try:
        bodies = load_bodies()
        if args.list and args.body:
            raise ValueError("pass --body or --list, not both")
        if args.list:
            for body in bodies.values():
                report_body(body)
            return 0
        if not args.body:
            raise ValueError("pass --body or --list")
        report_body(require_body(bodies, args.body))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
