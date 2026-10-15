#!/usr/bin/env python3
"""Circular orbit about a custom uniform sphere.

The body is spherical, non-rotating, airless, and uniform in density.
Altitude is geometric height above the surface. Zero altitude is a
surface circular orbit. G is the CODATA 2018 Newtonian constant.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# CODATA 2018, NIST. Printed with these digits; arithmetic uses the float.
G_CODATA = 6.67430e-11
G_TEXT = "6.67430e-11"
G_SOURCE = "CODATA 2018"
CHECK_TOL = 1e-9
N_CIRCLE = 361
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Circular orbit"
IDEALIZED_NOTE = "Idealized: uniform sphere, no atmosphere, no terrain"
NO_RADIUS = "no circular-orbit radius satisfies this speed, density, and altitude"
ASSUMPTIONS = (
    "spherical non-rotating airless body of uniform density; "
    "inverse-square point-mass gravity outside the body and the same mu "
    "inside the circular-orbit formula; altitude is geometric height above "
    "the surface and zero is a surface circular orbit; "
    "G is the CODATA 2018 Newtonian constant 6.67430e-11 m^3 kg^-1 s^-2; "
    "a preset supplies either density or mass and radius, not a fit to a "
    "triaxial shape; the figure is to scale and is not a map"
)
PALETTE = {
    "body": "#b9770e",
    "body_fill": "#f5cba7",
    "reference": "#1a5276",
    "reference_fill": "#d4e6f1",
    "orbit": "#922b21",
    "grid": "#d5d8dc",
    "text": "#1b2631",
    "note": "#34495e",
}

# Printed source values, converted to SI only by powers of ten.
# Planets, Ceres, and Pluto: JPL Solar System Dynamics, Planetary Physical
# Parameters, https://ssd.jpl.nasa.gov/planets/phys_par.html
# (mass, mean radius, and bulk density are printed; masses use CODATA 2018 G).
# Moon: NASA NSSDCA Moon Fact Sheet,
# https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
# (mass 0.07346e24 kg, volumetric mean radius 1737.4 km, density 3344 kg/m^3).
# Phobos, Deimos, Mimas, Enceladus: JPL Solar System Dynamics, Planetary
# Satellite Physical Parameters, https://ssd.jpl.nasa.gov/sats/phys_par/
# The page prints mean radius and mean density. It prints GM, not mass.
# Mass stored here is the sphere mass of those two printed numbers.
# Vesta: JPL SBDB phys-par for 4 Vesta. The page prints effective diameter
# 522.77 km and bulk density 3.460 g/cm^3. Mean radius is half that diameter.
# Mass is the sphere mass of that radius and density.
JPL_PLANET_URL = "https://ssd.jpl.nasa.gov/planets/phys_par.html"
JPL_PLANET_CITE = (
    "JPL Solar System Dynamics, Planetary Physical Parameters "
    "(mass, mean radius, and bulk density; masses use CODATA 2018 G)"
)
JPL_SAT_URL = "https://ssd.jpl.nasa.gov/sats/phys_par/"
MOON_URL = "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html"
MOON_CITE = (
    "NASA NSSDCA Moon Fact Sheet, D.R. Williams, updated 11 January 2024"
)
VESTA_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=4&phys-par=1"
VESTA_CITE = (
    "JPL Solar System Dynamics SBDB physical parameters for 4 Vesta; "
    "mean radius is half the printed effective diameter 522.77 km; "
    "mass is the sphere mass of that radius and the printed bulk density 3.460 g/cm^3"
)


@dataclass(frozen=True)
class Preset:
    name: str
    display: str
    mass_kg: float
    radius_m: float
    density_kg_m3: float
    citation: str
    url: str

    @property
    def diameter_m(self) -> float:
        return 2.0 * self.radius_m


def sphere_mass(radius_m: float, density_kg_m3: float) -> float:
    """Mass of a uniform sphere from a printed mean radius and density."""
    return (4.0 / 3.0) * math.pi * radius_m**3 * density_kg_m3


def _sat(name: str, display: str, radius_km: float, density_g_cm3: float) -> Preset:
    radius_m = radius_km * 1000.0
    density = density_g_cm3 * 1000.0
    return Preset(
        name=name,
        display=display,
        mass_kg=sphere_mass(radius_m, density),
        radius_m=radius_m,
        density_kg_m3=density,
        citation=(
            "JPL Solar System Dynamics, Planetary Satellite Physical Parameters; "
            f"mass is the sphere mass of the printed mean radius {radius_km} km "
            f"and mean density {density_g_cm3} g/cm^3"
        ),
        url=JPL_SAT_URL,
    )


def _planet(name: str, display: str, mass_kg: float, radius_km: float, density_g_cm3: float) -> Preset:
    return Preset(
        name=name,
        display=display,
        mass_kg=mass_kg,
        radius_m=radius_km * 1000.0,
        density_kg_m3=density_g_cm3 * 1000.0,
        citation=JPL_PLANET_CITE,
        url=JPL_PLANET_URL,
    )


# Increasing mean radius. Comparison picks the smallest strictly larger entry.
PRESETS: tuple[Preset, ...] = (
    _sat("deimos", "Deimos", 6.2, 1.471),
    _sat("phobos", "Phobos", 11.08, 1.872),
    _sat("mimas", "Mimas", 198.20, 1.1501),
    _sat("enceladus", "Enceladus", 252.10, 1.6097),
    Preset(
        name="vesta",
        display="Vesta",
        mass_kg=sphere_mass(522.77e3 / 2.0, 3460.0),
        radius_m=522.77e3 / 2.0,
        density_kg_m3=3460.0,
        citation=VESTA_CITE,
        url=VESTA_URL,
    ),
    _planet("ceres", "Ceres", 938.416e18, 469.7, 2.162),
    _planet("pluto", "Pluto", 13024.6e18, 1188.3, 1.853),
    Preset(
        name="moon",
        display="Moon",
        mass_kg=0.07346e24,
        radius_m=1737.4e3,
        density_kg_m3=3344.0,
        citation=MOON_CITE,
        url=MOON_URL,
    ),
    _planet("mercury", "Mercury", 0.330103e24, 2439.4, 5.4289),
    _planet("mars", "Mars", 0.641691e24, 3389.50, 3.9340),
    _planet("venus", "Venus", 4.86731e24, 6051.8, 5.243),
    _planet("earth", "Earth", 5.97217e24, 6371.0084, 5.5134),
    _planet("neptune", "Neptune", 102.4092e24, 24622.0, 1.638),
    _planet("uranus", "Uranus", 86.8099e24, 25362.0, 1.270),
    _planet("saturn", "Saturn", 568.317e24, 58232.0, 0.6871),
    _planet("jupiter", "Jupiter", 1898.125e24, 69911.0, 1.3262),
)
PRESET_BY_NAME = {preset.name: preset for preset in PRESETS}


@dataclass(frozen=True)
class Solution:
    mode: str
    radius_m: float
    mass_kg: float
    density_kg_m3: float
    density_source: str
    altitude_m: float
    mu: float
    orbit_radius_m: float
    circular_speed: float
    escape_orbit: float
    escape_surface: float
    surface_gravity: float
    period_s: float
    preset_name: str | None
    preset_role: str
    body_label: str
    compare: Preset
    compare_rule: str


def print_kv(key: str, value: object) -> None:
    # Twelve significant digits keep a parsed stdout value inside 1e-9 relative.
    if isinstance(value, float):
        text = f"{value:.12g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def known_body_text() -> str:
    return ", ".join(preset.name for preset in sorted(PRESETS, key=lambda item: item.name))


def require_preset(name: str, flag: str) -> Preset:
    key = name.strip().lower()
    preset = PRESET_BY_NAME.get(key)
    if preset is None:
        raise ValueError(f"unknown body {name.strip()!r} for {flag}; known bodies are {known_body_text()}")
    return preset


def require_finite(flag: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def require_positive(flag: str, value: float) -> None:
    require_finite(flag, value)
    if value <= 0.0:
        raise ValueError(f"{flag} must be > 0")


def gravitational_parameter(mass_kg: float) -> float:
    return G_CODATA * mass_kg


def density_from_mass(mass_kg: float, radius_m: float) -> float:
    return mass_kg / ((4.0 / 3.0) * math.pi * radius_m**3)


def circular_speed(mu: float, orbit_radius_m: float) -> float:
    return math.sqrt(mu / orbit_radius_m)


def escape_speed(mu: float, radius_m: float) -> float:
    return math.sqrt(2.0 * mu / radius_m)


def orbital_period(mu: float, orbit_radius_m: float) -> float:
    return 2.0 * math.pi * math.sqrt(orbit_radius_m**3 / mu)


def surface_radius_from_speed_density(speed: float, density: float) -> float:
    """Closed form R = v / sqrt(4/3 * pi * G * rho) at zero altitude."""
    factor = (4.0 / 3.0) * math.pi * G_CODATA * density
    radius = speed / math.sqrt(factor)
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError(NO_RADIUS)
    return radius


def radius_from_speed_density(speed: float, density: float, altitude: float) -> float:
    """Solve v^2 = G * (4/3 * pi * R^3 * rho) / (R + alt).

    Zero altitude uses the closed form. A positive altitude uses bisection
    on a bracket that starts at the surface solution and expands until the
    residual changes sign.
    """
    require_positive("circular speed", speed)
    require_positive("density", density)
    if altitude < 0.0 or not math.isfinite(altitude):
        raise ValueError("--alt must be >= 0")
    if altitude == 0.0:
        return surface_radius_from_speed_density(speed, density)
    factor = (4.0 / 3.0) * math.pi * G_CODATA * density
    if not math.isfinite(factor) or factor <= 0.0:
        raise ValueError(NO_RADIUS)
    v2 = speed * speed

    def residual(radius: float) -> float:
        return factor * radius**3 - v2 * radius - v2 * altitude

    lo = 0.0
    hi = speed / math.sqrt(factor)
    if not math.isfinite(hi) or hi <= 0.0:
        raise ValueError(NO_RADIUS)
    signed = residual(hi)
    if not math.isfinite(signed):
        raise ValueError(NO_RADIUS)
    for _ in range(80):
        if signed > 0.0:
            break
        nxt = hi * 2.0
        if not math.isfinite(nxt) or nxt <= hi:
            raise ValueError(NO_RADIUS)
        hi = nxt
        signed = residual(hi)
        if not math.isfinite(signed):
            raise ValueError(NO_RADIUS)
    else:
        raise ValueError(NO_RADIUS)
    if signed <= 0.0:
        raise ValueError(NO_RADIUS)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        value = residual(mid)
        if not math.isfinite(value):
            raise ValueError(NO_RADIUS)
        if value > 0.0:
            hi = mid
        else:
            lo = mid
        if hi - lo <= 1e-14 * max(1.0, hi):
            break
    radius = 0.5 * (lo + hi)
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError(NO_RADIUS)
    return radius


def choose_compare(body_radius: float, override: str | None) -> tuple[Preset, str]:
    if override is not None:
        return require_preset(override, "--compare"), "named"
    larger = [preset for preset in PRESETS if preset.radius_m > body_radius]
    if larger:
        return min(larger, key=lambda preset: preset.radius_m), "smallest_larger"
    return max(PRESETS, key=lambda preset: preset.radius_m), "largest_preset"


def _flag_set(*pairs: tuple[str, float | str | None]) -> list[str]:
    return [flag for flag, value in pairs if value is not None]


def resolve_body(
    *,
    speed: float | None,
    density: float | None,
    mass: float | None,
    radius: float | None,
    altitude: float,
    body: str | None,
    compare: str | None,
) -> Solution:
    if speed is not None:
        require_positive("--v", speed)
    if density is not None:
        require_positive("--rho", density)
    if mass is not None:
        require_positive("--mass", mass)
    if radius is not None:
        require_positive("--radius", radius)
    require_finite("--alt", altitude)
    if altitude < 0.0:
        raise ValueError("--alt must be >= 0")

    preset: Preset | None = None
    if body is not None:
        preset = require_preset(body, "--body")
    if compare is not None:
        require_preset(compare, "--compare")

    has_v = speed is not None
    has_rho = density is not None
    has_mass = mass is not None
    has_radius = radius is not None
    has_body = preset is not None
    if has_body and has_rho:
        raise ValueError("--body and --rho both set density; pass only one")
    if has_body and has_mass:
        raise ValueError("--body and --mass both set mass; pass only one")

    mode_speed = has_v and (has_rho or has_body) and not has_mass and not has_radius
    mode_mass = has_mass and has_radius and not has_v and not has_rho and not has_body
    mode_preset = has_body and not has_v and not has_rho and not has_mass and not has_radius
    mode_radius = has_radius and (has_rho or has_body) and not has_v and not has_mass
    chosen = [mode_speed, mode_mass, mode_preset, mode_radius]
    if sum(bool(item) for item in chosen) != 1:
        supplied: set[str] = set()
        if has_v:
            supplied.add("v")
        if has_rho:
            supplied.add("rho")
        if has_mass:
            supplied.add("mass")
        if has_radius:
            supplied.add("radius")
        if has_body:
            supplied.add("body")
        valid_modes = (
            {"v", "rho"},
            {"v", "body"},
            {"mass", "radius"},
            {"body"},
            {"radius", "rho"},
            {"radius", "body"},
        )
        given = _flag_set(
            ("--v", speed),
            ("--rho", density),
            ("--mass", mass),
            ("--radius", radius),
            ("--body", body),
        )
        incomplete = any(supplied < mode for mode in valid_modes)
        if not supplied or incomplete:
            if has_v and not has_rho and not has_body:
                raise ValueError("missing density: pass --rho or --body with --v")
            if has_mass and not has_radius:
                raise ValueError("missing --radius to go with --mass")
            if has_radius and not has_mass and not has_rho and not has_body:
                raise ValueError("missing --mass, --rho, or --body to go with --radius")
            if has_rho and not has_v and not has_radius:
                raise ValueError("missing --v or --radius to go with --rho")
            raise ValueError(
                "missing a complete input mode: pass --v with --rho or --body, "
                "--mass with --radius, --radius with --rho or --body, or --body alone"
            )
        joined = ", ".join(given)
        raise ValueError(
            "pass exactly one input mode (--v with density, --mass with --radius, "
            f"--radius with density, or --body alone); got {joined}"
        )

    preset_role = "none"
    preset_name = None
    if mode_speed or mode_radius:
        if preset is not None:
            density = preset.density_kg_m3
            density_source = preset.citation
            preset_role = "density"
            preset_name = preset.name
        else:
            density_source = "typed"
        assert density is not None
        if mode_speed:
            assert speed is not None
            radius = radius_from_speed_density(speed, density, altitude)
            mass = sphere_mass(radius, density)
            mode = "speed_density"
            body_label = "Custom body"
        else:
            assert radius is not None
            mass = sphere_mass(radius, density)
            mode = "radius_density"
            body_label = "Custom body"
    elif mode_preset:
        assert preset is not None
        mass = preset.mass_kg
        radius = preset.radius_m
        density = density_from_mass(mass, radius)
        density_source = preset.citation
        preset_role = "mass_radius"
        preset_name = preset.name
        mode = "mass_radius"
        body_label = preset.display
    else:
        assert mass is not None and radius is not None
        density = density_from_mass(mass, radius)
        density_source = "typed"
        mode = "mass_radius"
        body_label = "Custom body"

    assert mass is not None and radius is not None and density is not None
    mu = gravitational_parameter(mass)
    orbit_radius = radius + altitude
    speed_circ = circular_speed(mu, orbit_radius)
    if not math.isfinite(speed_circ) or speed_circ <= 0.0:
        raise ValueError(NO_RADIUS)
    compare_body, compare_rule = choose_compare(radius, compare)
    return Solution(
        mode=mode,
        radius_m=radius,
        mass_kg=mass,
        density_kg_m3=density,
        density_source=density_source,
        altitude_m=altitude,
        mu=mu,
        orbit_radius_m=orbit_radius,
        circular_speed=speed_circ,
        escape_orbit=escape_speed(mu, orbit_radius),
        escape_surface=escape_speed(mu, radius),
        surface_gravity=mu / (radius * radius),
        period_s=orbital_period(mu, orbit_radius),
        preset_name=preset_name,
        preset_role=preset_role,
        body_label=body_label,
        compare=compare_body,
        compare_rule=compare_rule,
    )


def diameter_label(meters: float) -> str:
    km = meters / 1000.0
    if km >= 10000.0:
        return f"{km:,.0f} km"
    if km >= 100.0:
        return f"{km:.1f} km"
    if km >= 1.0:
        return f"{km:.2f} km"
    if meters >= 1.0:
        return f"{meters:.2f} m"
    return f"{meters:.3g} m"


def circle_xy(center_x: float, radius: float, count: int = N_CIRCLE) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for i in range(count):
        angle = 2.0 * math.pi * i / (count - 1)
        xs.append(center_x + radius * math.cos(angle))
        ys.append(radius * math.sin(angle))
    return xs, ys


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the circular orbit") from exc
    return plt, Circle


# A gap thinner than this fraction of the comparison span is a stroke on the
# limb. It stays in the same PNG as an enlarged inset, not a second file.
INSET_GAP_FRACTION = 0.025


def comparison_layout(body_km: float, orbit_km: float, ref_km: float) -> tuple[float, float, float, float]:
    gap = 0.28 * max(orbit_km, ref_km, body_km, 1e-6)
    ref_x = orbit_km + gap + ref_km
    left = -orbit_km
    right = ref_x + ref_km
    span = max(right - left, 1e-6)
    return ref_x, left, right, span


def orbit_hidden_at_comparison_scale(body_km: float, orbit_km: float, span_km: float) -> bool:
    """True when the altitude gap would not read as an orbit beside the reference."""
    gap = max(0.0, orbit_km - body_km)
    return gap / max(span_km, 1e-6) < INSET_GAP_FRACTION


def draw_dashed_orbit(ax, center_x: float, orbit_km: float, *, width: float, under: float) -> None:
    xs, ys = circle_xy(center_x, orbit_km)
    # White understroke keeps the dashes readable when the orbit lies on the limb.
    ax.plot(xs, ys, color="white", linewidth=under, linestyle=(0, (6, 4)), zorder=4)
    ax.plot(
        xs,
        ys,
        color=PALETTE["orbit"],
        linewidth=width,
        linestyle=(0, (6, 4)),
        zorder=5,
    )


def draw_orbit_inset(ax, Circle, result: Solution, body_km: float, orbit_km: float) -> None:
    """Enlarged custom body. Same PNG; not a second file and not the comparison scale."""
    ax.set_facecolor("white")
    ax.add_patch(
        Circle(
            (0.0, 0.0),
            body_km,
            facecolor=PALETTE["body_fill"],
            edgecolor=PALETTE["body"],
            linewidth=1.4,
            zorder=3,
        )
    )
    draw_dashed_orbit(ax, 0.0, orbit_km, width=2.4, under=4.6)
    pad = max(0.55 * orbit_km, 0.35 * body_km)
    limit = orbit_km + pad
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-1.42 * limit, 1.08 * limit)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(PALETTE["note"])
        spine.set_linewidth(0.8)
    alt_km = result.altitude_m / 1000.0
    if alt_km == 0.0:
        detail = "surface orbit"
    elif alt_km >= 1.0:
        detail = f"altitude {alt_km:.4g} km"
    else:
        detail = f"altitude {result.altitude_m:.4g} m"
    ax.set_title("Enlarged orbit", color=PALETTE["text"], fontsize=10)
    ax.text(
        0.0,
        -1.28 * limit,
        detail,
        ha="center",
        va="top",
        color=PALETTE["orbit"],
        fontsize=8,
    )


def plot_png(path: Path, result: Solution) -> bool:
    plt, Circle = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(9.4, 6.6))
    body_km = result.radius_m / 1000.0
    orbit_km = result.orbit_radius_m / 1000.0
    ref_km = result.compare.radius_m / 1000.0
    ref_x, left, right, span = comparison_layout(body_km, orbit_km, ref_km)
    half = max(orbit_km, ref_km, body_km)
    show_inset = orbit_hidden_at_comparison_scale(body_km, orbit_km, span)

    ax.add_patch(
        Circle(
            (ref_x, 0.0),
            ref_km,
            facecolor=PALETTE["reference_fill"],
            edgecolor=PALETTE["reference"],
            linewidth=1.6,
            zorder=3,
        )
    )
    ax.add_patch(
        Circle(
            (0.0, 0.0),
            body_km,
            facecolor=PALETTE["body_fill"],
            edgecolor=PALETTE["body"],
            linewidth=1.6,
            zorder=3,
        )
    )
    draw_dashed_orbit(ax, 0.0, orbit_km, width=1.8, under=3.4)
    ax.plot([], [], color=PALETTE["orbit"], linewidth=1.8, linestyle=(0, (6, 4)), label="circular orbit")
    ax.plot([], [], color=PALETTE["body"], linewidth=6, label=result.body_label)
    ax.plot([], [], color=PALETTE["reference"], linewidth=6, label=result.compare.display)

    label_drop = 0.08 * half + 0.02 * max(half, 1.0)
    ax.text(
        0.0,
        -(max(orbit_km, body_km) + label_drop),
        f"{result.body_label}\n{diameter_label(2.0 * result.radius_m)} diameter",
        ha="center",
        va="top",
        color=PALETTE["body"],
        fontsize=10,
    )
    ax.text(
        ref_x,
        -(ref_km + label_drop),
        f"{result.compare.display}\n{diameter_label(result.compare.diameter_m)} diameter",
        ha="center",
        va="top",
        color=PALETTE["reference"],
        fontsize=10,
    )
    pad = 0.08 * span
    ax.set_xlim(left - pad, right + pad)
    ax.set_ylim(-1.55 * half, 1.28 * half)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("distance (km)")
    ax.set_ylabel("distance (km)")
    fig.suptitle(PLOT_TITLE, color=PALETTE["text"], fontsize=14)
    ax.set_title(IDEALIZED_NOTE, color=PALETTE["note"], fontsize=9, style="italic")
    ax.grid(True, color=PALETTE["grid"], alpha=0.7)
    ax.legend(loc="upper right", fontsize=8.5)
    if show_inset:
        # Leave a column on the right of this same figure. Do not open a second PNG.
        fig.subplots_adjust(left=0.07, right=0.64, bottom=0.10, top=0.88)
        inset = fig.add_axes([0.68, 0.16, 0.28, 0.62])
        draw_orbit_inset(inset, Circle, result, body_km, orbit_km)
    else:
        fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)
    return show_inset


def emit(result: Solution, path: Path | None, orbit_inset: bool = False) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("input_mode", result.mode)
    print_kv("body_radius_m", result.radius_m)
    print_kv("body_diameter_m", 2.0 * result.radius_m)
    print_kv("body_mass_kg", result.mass_kg)
    print_kv("density_kg_m3", result.density_kg_m3)
    print_kv("surface_gravity_m_s2", result.surface_gravity)
    print_kv("mu_m3_s2", result.mu)
    print_kv("orbit_radius_m", result.orbit_radius_m)
    print_kv("altitude_m", result.altitude_m)
    print_kv("circular_speed_m_s", result.circular_speed)
    print_kv("escape_speed_at_orbit_m_s", result.escape_orbit)
    print_kv("escape_speed_surface_m_s", result.escape_surface)
    print_kv("period_s", result.period_s)
    print_kv("period_h", result.period_s / 3600.0)
    print_kv("density_source", result.density_source)
    print(f"G_m3_kg_s2: {G_TEXT}")
    print_kv("G_source", G_SOURCE)
    print_kv("preset_name", result.preset_name if result.preset_name is not None else "none")
    print_kv("preset_role", result.preset_role)
    print_kv("compare_body", result.compare.name)
    print_kv("compare_radius_m", result.compare.radius_m)
    print_kv("compare_diameter_m", result.compare.diameter_m)
    print_kv("compare_rule", result.compare_rule)
    if path is not None:
        print_kv("orbit_inset", "yes" if orbit_inset else "no")
        print_kv("graph", str(path))


def run(ns: argparse.Namespace) -> int:
    altitude = 0.0 if ns.alt is None else ns.alt
    result = resolve_body(
        speed=ns.v,
        density=ns.rho,
        mass=ns.mass,
        radius=ns.radius,
        altitude=altitude,
        body=ns.body,
        compare=ns.compare,
    )
    path: Path | None = None
    orbit_inset = False
    if not ns.no_plot:
        path = Path(ns.out) if ns.out else SKILL_DIR / "body_circular_orbit.png"
        path = path.resolve()
        orbit_inset = plot_png(path, result)
    elif ns.out is not None:
        raise ValueError("pass --out only when a PNG is written")
    emit(result, path, orbit_inset)
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


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


def _values(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        found[key] = value
    return found


def _close(got: float, expected: float) -> bool:
    span = max(abs(expected), abs(got), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def run_check() -> int:
    for preset in PRESETS:
        if not preset.url.startswith("https://"):
            return fail(f"{preset.name} citation URL is missing")
        host = preset.url.split("/")[2]
        if not (host.endswith("nasa.gov") or host.endswith("jpl.nasa.gov")):
            return fail(f"{preset.name} citation URL is not NASA or JPL")
        if not preset.citation.strip():
            return fail(f"{preset.name} citation is empty")
        if preset.mass_kg <= 0.0 or preset.radius_m <= 0.0 or preset.density_kg_m3 <= 0.0:
            return fail(f"{preset.name} mass, radius, or density is not positive")
    moon = PRESET_BY_NAME["moon"]
    expected_speed = math.sqrt(G_CODATA * moon.mass_kg / moon.radius_m)
    if not (1670.0 < expected_speed < 1690.0):
        return fail("Moon surface circular speed is not about 1.68 km/s")

    with tempfile.TemporaryDirectory() as folder:
        folder_path = Path(folder)
        code, text, err = capture(["--body", "moon", "--alt", "0", "--no-plot"])
        if code != 0:
            return fail(f"Moon preset failed: {err}")
        values = _values(text)
        got = float(values["circular_speed_m_s"])
        if not _close(got, expected_speed):
            return fail("Moon speed is not sqrt(GM/R)")
        if abs(got - 1680.0) > 15.0:
            return fail("Moon speed is not about 1.68 km/s")
        if values["density_source"] != moon.citation:
            return fail("Moon density_source is not the citation")
        if values["G_m3_kg_s2"] != G_TEXT:
            return fail("G was not printed as the CODATA 2018 value")
        escape = float(values["escape_speed_at_orbit_m_s"])
        if not _close(escape, math.sqrt(2.0) * got):
            return fail("surface escape speed is not sqrt(2) times circular speed")

        for rho, km in ((2700.0, 54.4), (1900.0, 64.9)):
            code, text, err = capture(["--v", "47.30", "--rho", str(rho), "--alt", "0", "--no-plot"])
            if code != 0:
                return fail(f"speed-density rho={rho} failed: {err}")
            radius_km = float(_values(text)["body_radius_m"]) / 1000.0
            if abs(radius_km - km) > 0.1:
                return fail(f"rho={rho} radius {radius_km} km is outside {km} ± 0.1")
            if _values(text)["density_source"] != "typed":
                return fail("typed density was not labeled typed")

        code, text, err = capture(
            ["--v", "80", "--rho", "2500", "--alt", "20000", "--no-plot"]
        )
        if code != 0:
            return fail(f"altitude root find failed: {err}")
        solved = float(_values(text)["body_radius_m"])
        code, text, err = capture(
            ["--radius", str(solved), "--rho", "2500", "--alt", "20000", "--no-plot"]
        )
        if code != 0:
            return fail(f"round trip mode 3 failed: {err}")
        recovered = float(_values(text)["circular_speed_m_s"])
        if not _close(recovered, 80.0):
            return fail("altitude round trip did not recover the speed")

        periods = []
        for radius in ("100000", "250000"):
            code, text, err = capture(
                ["--radius", radius, "--rho", "2500", "--alt", "0", "--no-plot"]
            )
            if code != 0:
                return fail(f"period case failed: {err}")
            periods.append(float(_values(text)["period_s"]))
        if not _close(periods[0], periods[1]):
            return fail("surface period depended on radius at fixed density")

        for argv in (
            [],
            ["--v", "10"],
            ["--rho", "2000"],
            ["--mass", "1e18"],
            ["--radius", "1000"],
            ["--v", "10", "--mass", "1e18"],
            ["--v", "10", "--radius", "1000"],
            ["--mass", "1e18", "--rho", "2000"],
            ["--body", "moon", "--rho", "2000"],
            ["--body", "moon", "--mass", "1e18"],
            ["--body", "moon", "--v", "10", "--rho", "2000"],
            ["--v", "0", "--rho", "2000"],
            ["--v", "-1", "--rho", "2000"],
            ["--rho", "0", "--radius", "1000"],
            ["--mass", "-5", "--radius", "1000"],
            ["--radius", "0", "--rho", "2000"],
            ["--alt", "-1", "--body", "moon"],
            ["--body", "unknown"],
            ["--compare", "unknown", "--body", "moon"],
        ):
            code, _text, err = capture([*argv, "--no-plot"] if argv else argv)
            if code == 0 or not err.startswith("error:"):
                return fail(f"invalid input was accepted: {argv}")

        tiny = folder_path / "tiny.png"
        code, text, err = capture(
            ["--radius", "50000", "--rho", "2700", "--out", str(tiny)]
        )
        if code != 0:
            return fail(f"tiny-body PNG failed: {err}")
        if _values(text).get("compare_body") != "mimas":
            return fail("a 50 km body was not compared with Mimas")
        graphs = [line for line in text.splitlines() if line.startswith("graph:")]
        if len(graphs) != 1:
            return fail(f"one call printed {len(graphs)} graph lines")
        if _values(text).get("orbit_inset") != "yes":
            return fail("a surface orbit beside Mimas did not include an inset")
        moon_png = folder_path / "moon.png"
        code, text, err = capture(["--body", "Moon", "--out", str(moon_png)])
        if code != 0:
            return fail(f"Moon PNG failed: {err}")
        if _values(text).get("compare_body") != "mercury":
            return fail("the Moon was not compared with Mercury")
        for png in (tiny, moon_png):
            if not png.is_file() or png.stat().st_size < 1000 or png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                return fail(f"PNG was not written: {png.name}")

    print("check: pass")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Circular orbit about a uniform sphere from speed and density, "
            "mass and radius, or radius and density. A preset may supply "
            "the density or the mass and radius."
        )
    )
    parser.add_argument(
        "--v",
        type=float,
        default=None,
        help="circular orbit speed [m/s]; with density, solves the body radius",
    )
    parser.add_argument("--rho", type=float, default=None, help="uniform density [kg/m^3]")
    parser.add_argument("--mass", type=float, default=None, help="body mass [kg]; with --radius")
    parser.add_argument("--radius", type=float, default=None, help="body radius [m]")
    parser.add_argument(
        "--alt",
        type=float,
        default=None,
        help="geometric altitude above the surface [m]; default 0",
    )
    parser.add_argument(
        "--body",
        type=str,
        default=None,
        help="preset name; supplies density, or mass and radius when used alone",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="preset drawn to scale beside the body; default is the smallest larger preset",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--no-plot", action="store_true", help="skip the PNG")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
