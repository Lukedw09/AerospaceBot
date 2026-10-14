---
name: ASTRO - BodyCircularOrbit
description: >-
  Run the body-circular-orbit program and report its printed results and PNG.
  Use when the user wants the radius, mass, surface gravity, circular speed,
  escape speed, or period of a circular orbit about a custom spherical
  uniform body, or a named preset such as the Moon, Phobos, Ceres, or a
  planet. Do not redraw the figure or recompute the numbers by hand.
---

# ASTRO - BodyCircularOrbit

Use this skill for a circular orbit about a custom spherical, non-rotating, airless, uniform-density body. Run the program once; quote its stdout and include its PNG unless `--no-plot` was used. Do not redraw the figure or recompute the numbers by hand.

Assumptions (also printed by the program): the body is a uniform sphere. Gravity outside the body is the inverse-square field of the total mass. Altitude is geometric height above the surface. Zero altitude is a circular orbit at the surface. \(G = 6.67430\times 10^{-11}\,\mathrm{m^3\,kg^{-1}\,s^{-2}}\) (CODATA 2018). The figure is to scale and carries the note "Idealized: uniform sphere, no atmosphere, no terrain".

The circular speed at geometric altitude \(h\) is

\[
v = \sqrt{\frac{GM}{R+h}}, \qquad M = \frac{4}{3}\pi R^{3}\rho
\]

At \(h = 0\),

\[
R = \frac{v}{\sqrt{\frac{4}{3}\pi G\rho}}
\]

A positive altitude solves the same speed equation by bisection. Escape speed at a given radius is \(\sqrt{2}\) times the circular speed there. On the surface the period depends only on density.

## When to run

1. Speed and density, solving for the body radius: pass `--v` and `--rho`. Optional `--alt` defaults to 0. At zero altitude the radius is the closed form above. A positive altitude is a bracketed root. If no positive radius satisfies the speed, report the program error and stop.
2. Mass and radius: pass `--mass` and `--radius`. Optional `--alt`.
3. Radius and density: pass `--radius` and `--rho`. Optional `--alt`.
4. A preset stands in for density, or for mass and radius when `--body` is the only body input. Do not also pass a typed value for a quantity the preset is supplying.
5. Pass exactly one of those modes. Do not invent a radius, mass, density, speed, or altitude.
6. The PNG is drawn unless `--no-plot` is set. `--compare` names the reference body. Otherwise the reference is the smallest preset that is still larger than the custom body.

## Flags

Run:

```text
python "skills/ASTRO - BodyCircularOrbit/body_circular_orbit.py" --v <m/s> (--rho <kg/m^3> | --body <name>) [--alt <m>] [--compare <name>] [--out <png>] [--no-plot]
python "skills/ASTRO - BodyCircularOrbit/body_circular_orbit.py" --mass <kg> --radius <m> [--alt <m>] [--compare <name>] [--out <png>] [--no-plot]
python "skills/ASTRO - BodyCircularOrbit/body_circular_orbit.py" --radius <m> (--rho <kg/m^3> | --body <name>) [--alt <m>] [--compare <name>] [--out <png>] [--no-plot]
python "skills/ASTRO - BodyCircularOrbit/body_circular_orbit.py" --body <name> [--alt <m>] [--compare <name>] [--out <png>] [--no-plot]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--v` | Circular-orbit speed; with density, solves the body radius | m/s, \(> 0\) | Optional. With `--rho` or `--body` |
| `--rho` | Uniform density | kg/m³, \(> 0\) | Optional. Not with `--body` |
| `--mass` | Body mass | kg, \(> 0\) | Optional. With `--radius`, and not with `--body` |
| `--radius` | Body radius | m, \(> 0\) | Optional. With `--mass`, or with `--rho` or `--body` |
| `--alt` | Geometric altitude above the surface | m, \(\ge 0\) | Optional. Default 0 |
| `--body` | Preset name. Supplies density, or mass and radius when it is the only body input | — | Optional |
| `--compare` | Reference body drawn to scale | — | Optional |
| `--out` | PNG path | — | Optional |
| `--no-plot` | Skip the PNG | — | Optional |

Pass exactly one input mode. `--body` and a typed value for the same quantity is an error. Radius, mass, density, and speed must be positive. Altitude must not be negative.

Presets, smallest first: Deimos, Phobos, Mimas, Enceladus, Vesta, Ceres, Pluto, the Moon, Mercury, Mars, Venus, Earth, Neptune, Uranus, Saturn, Jupiter. Deimos, Phobos, Mimas, and Enceladus take mean radius and mean density from the JPL satellite table; the stored mass is the sphere mass of those two printed numbers. Vesta's mean radius is half the JPL SBDB effective diameter. The Moon is the NASA NSSDCA Moon Fact Sheet. Ceres, Pluto, and the planets are the JPL planetary physical-parameter table. Each preset keeps that page's URL.

Every successful run without `--no-plot` writes one PNG. The custom body and the reference body are circles to scale, each labeled with its diameter. The orbit is a dashed circle at the stated altitude. The title note is "Idealized: uniform sphere, no atmosphere, no terrain". `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG when `graph:` is printed. Do not draw a second figure.
3. Report `body_radius_m`, `body_diameter_m`, `body_mass_kg`, `density_kg_m3`, `surface_gravity_m_s2`, and `mu_m3_s2`.
4. Report `orbit_radius_m`, `altitude_m`, `circular_speed_m_s`, `escape_speed_at_orbit_m_s`, `escape_speed_surface_m_s`, `period_s`, and `period_h`.
5. Report `density_source` and `G_m3_kg_s2`. `typed` means the user supplied the density, or the mass and radius. Any other text is the preset citation.
6. Report `compare_body` when it is printed. That is the reference circle in the PNG.
7. If a required piece of the chosen mode is missing, say so. Do not fill it in.
