---
name: ASTRO - SolarSystemBody
description: >-
  Run the solar-system body program and report its printed results. Use when
  the user wants the gravitational parameter, radius, heliocentric semi-major
  axis, eccentricity, inclination, or mean, perihelion, and aphelion radii of
  the Sun, a planet, or Pluto. Do not recompute the numbers by hand. Do not
  draw a figure.
---

# ASTRO - SolarSystemBody

Use this skill for the stored constants of the Sun, the eight planets, and Pluto. Run the program once and quote its stdout. Do not recompute the numbers by hand. Do not draw a figure. The Moon is not in the table.

Assumptions (also printed by the program): point-mass \(\mu\) and Keplerian heliocentric elements from the NSSDCA fact sheets. Earth's radius is the catalogue value \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\) and Earth's \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). A radius is distance from the body center. The mean heliocentric radius is the semi-major axis. Perihelion is \(a(1-e)\) and aphelion is \(a(1+e)\). The Sun is the central body. Pluto is class `dwarf`.

## When to run

1. One body: pass `--body` with `sun`, a planet name, or `pluto`.
2. The whole table: pass `--list`. Do not pass `--body` and `--list` together.
3. Do not invent a body that is not in the table. A same-planet orbit transfer stays on `ASTRO - HohmannTransfer`. A mission from LEO to a low orbit about another planet or Pluto stays on `ASTRO - LeoToLowOrbit`.

## Flags

Run:

```text
python "skills/ASTRO - SolarSystemBody/solar_system_body.py" --body <name>
python "skills/ASTRO - SolarSystemBody/solar_system_body.py" --list
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--body` | Body name | — | Or `--list` |
| `--list` | Print every stored body | — | Or `--body` |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `name` and `class`. `planet` is one of the eight planets. `dwarf` is Pluto. `star` is the Sun.
3. Report `mu_m3_s2`, `radius_m`, `mu_source`, and `radius_source`. For Earth, `g0_R0` and `catalogue_R0` mean the catalogue Earth, not the fact-sheet Earth \(GM\).
4. For a planet or Pluto, report `a_helio_m`, `e`, `i_rad`, `i_deg`, `r_mean_m`, `r_perihelion_m`, and `r_aphelion_m`. State that a heliocentric radius is distance from the Sun and `radius_m` is distance from the body center.
5. For the Sun, report that `a_helio_m` is `none`. Repeat `warning` when it is printed.
6. If the body name is missing, say so. Do not fill it in.
