---
name: ASTRO - HeliocentricHohmann
description: >-
  Run the heliocentric Hohmann program and report its printed results and PNG.
  Use when the user wants the Sun-centered half-ellipse between two planets or
  Pluto, the hyperbolic excess at each end, the phase angle, or the synodic
  period. Do not redraw the coast or recompute the numbers by hand. The excess
  speeds are not the rocket burns.
---

# ASTRO - HeliocentricHohmann

Use this skill for a Hohmann coast between two circular heliocentric orbits. Run the program once; quote its stdout and include its PNG. Do not redraw the coast or recompute the numbers by hand.

Assumptions (also printed by the program): the Sun is the primary. The coast is half of one transfer ellipse, \(180^\circ\) of true anomaly. Coplanar excess at each end is \(|v_{\mathrm{transfer}}-v_{\mathrm{planet}}|\). Inclined excess is `inclined_excess_speed` with the whole inclination difference at that end. Those excess speeds are not the planet-centered rocket burns. The program does not choose which apsis pays for \(\Delta i\). That choice belongs to `ASTRO - LeoToLowOrbit`. A same-planet transfer stays on `ASTRO - HohmannTransfer`.

`--radius-mode` selects the circular radius of a named body. `mean` uses the semi-major axis. `perihelion` uses \(a(1-e)\). `aphelion` uses \(a(1+e)\). The default is `mean`.

## When to run

1. Two bodies: pass `--from` and `--to`. Each name is a planet or `pluto`. Do not pass the Sun.
2. Two radii: pass `--r1`, `--r2`, and `--mu`. Optional `--i1` and `--i2` are inclinations in radians. Omitted inclinations are 0.
3. Pass one input pair. Do not combine names with radii.
4. Pass `--radius-mode` only when the user names `mean`, `perihelion`, or `aphelion`. Otherwise leave the default `mean`.
5. Convert inputs to SI and radians before the call. Do not invent a radius, a solar \(\mu\), or a body.

## Flags

Run:

```text
python "skills/ASTRO - HeliocentricHohmann/heliocentric_hohmann.py" --from <name> --to <name> [--radius-mode mean|perihelion|aphelion] [--out <png>]
python "skills/ASTRO - HeliocentricHohmann/heliocentric_hohmann.py" --r1 <m> --r2 <m> --mu <m^3/s^2> [--i1 <rad>] [--i2 <rad>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--from` | Departure body | — | With `--to` |
| `--to` | Arrival body | — | With `--from` |
| `--r1` | Departure heliocentric radius | m, \(> 0\) | With `--r2` and `--mu` |
| `--r2` | Arrival heliocentric radius | m, \(> 0\) | With `--r1` and `--mu` |
| `--mu` | Solar gravitational parameter | m³/s², \(> 0\) | With `--r1` and `--r2` |
| `--i1` | Departure inclination | rad | Optional with radii. Default 0 |
| `--i2` | Arrival inclination | rad | Optional with radii. Default 0 |
| `--radius-mode` | Circular radius used for a named body | — | Optional. Default `mean` |
| `--out` | PNG path | — | Optional |

A bare length is metres. Kilometres use `1 km = 1000 m`. An astronomical unit on input uses `1 AU = 149597870700 m` only when the user spoke in AU; say so. Named-body radii come from `ASTRO - SolarSystemBody`.

Every successful run writes one PNG. The plot title is `Heliocentric Hohmann`. The view looks down the ecliptic normal. Both circular orbits and the half-ellipse are drawn. The chord between the planets is not drawn. The annotation is \(\Delta i\). `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. Do not draw a second figure.
3. Report `mode`. `bodies` used names. `radii` used `--r1` and `--r2`.
4. Report `from`, `to`, `radius_mode`, `mu_m3_s2`, `r_depart_m`, and `r_arrive_m`.
5. Report `direction`. `outward` leaves from perihelion with a prograde heliocentric speed change. `inward` leaves from aphelion with a retrograde heliocentric speed change. `coast` means the radii are equal.
6. Report `a_m`, `e`, `tof_s`, `period_s`, `phase_rad`, and `synodic_s`. `phase_rad` is the target lead angle in \((-\pi, \pi]\). A positive angle means the target leads.
7. Report `di_rad`, both coplanar excess speeds, and both inclined excess speeds. State that these are not the rocket \(\Delta v\).
8. Repeat `warning` when it is printed.
9. If a body, a radius, or solar \(\mu\) is missing, say so. Do not fill it in. For the LEO departure burn plus the low-orbit capture burn, use `ASTRO - LeoToLowOrbit`.
