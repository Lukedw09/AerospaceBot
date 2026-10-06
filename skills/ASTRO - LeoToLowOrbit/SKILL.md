---
name: ASTRO - LeoToLowOrbit
description: >-
  Run the LEO-to-low-orbit program and report its printed results and PNG.
  Use when the user wants the patched-conic delta-v, time of flight, and
  phase angle from a circular low Earth orbit to a circular low orbit about
  another planet or Pluto. Do not redraw the coast or recompute the numbers
  by hand. Do not size a rocket.
---

# ASTRO - LeoToLowOrbit

Use this skill for a direct patched-conic mission from a circular LEO to a circular low orbit about another planet or Pluto. Run the program once; quote its stdout and include its PNG. Do not redraw the coast or recompute the numbers by hand.

Assumptions (also printed by the program): Earth is the only departure body. The coast is one heliocentric Hohmann half-ellipse. The rocket burns are an impulsive periapsis departure from the LEO onto an Earth hyperbola and an impulsive periapsis capture into the target circle. The whole ecliptic inclination difference is paid inside the excess speed at one apsis, whichever placement has the smaller total. There is no third burn. The LEO plane is assumed to be alignable with the departure asymptote. A same-planet circular transfer stays on `ASTRO - HohmannTransfer`. One hyperbola by itself stays on `ASTRO - HyperbolicExcess`. A vehicle sized from this delta-v stays on `ROCKET - PayloadtoDeltaV`.

The heliocentric radii come from `ASTRO - SolarSystemBody`. `--radius-mode` is `mean` unless the user names `perihelion` or `aphelion`.

## When to run

1. Pass `--to` as a planet other than Earth, or `pluto`.
2. Pass `--h-leo` and `--h-arrive` as geometric altitudes. If either altitude is missing, say so. Do not invent a LEO height or a low-orbit height.
3. Pass `--radius-mode` only when the user names it. The default is `mean`.
4. Convert altitudes to metres before the call. State the converted units in the reply.

## Flags

Run:

```text
python "skills/ASTRO - LeoToLowOrbit/leo_to_low_orbit.py" --to <name> --h-leo <m> --h-arrive <m> [--radius-mode mean|perihelion|aphelion] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--to` | Target planet or `pluto` | — | Required |
| `--h-leo` | Geometric altitude of the circular LEO | m, \(\ge 0\) | Required |
| `--h-arrive` | Geometric altitude of the circular target orbit | m, \(\ge 0\) | Required |
| `--radius-mode` | Circular heliocentric radius | — | Optional. Default `mean` |
| `--out` | PNG path | — | Optional |

A bare altitude is metres. Kilometres use `1 km = 1000 m`.

Every successful run writes one PNG. The plot title is `LEO to low orbit`. It is the heliocentric half-ellipse between the two circular orbits, with a \(\Delta v\) arrow at departure and at arrival. It is not a straight line between the planets. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. Do not draw a second figure.
3. Report `to` and `class`. Pluto is `dwarf`.
4. Report `path_1` through `path_6` in order: the circular LEO, the Earth departure hyperbola, the Earth sphere of influence, the heliocentric half-ellipse, the target sphere of influence and arrival hyperbola, and the circular low orbit.
5. Report `h_leo_m`, `r_leo_m`, `h_arrive_m`, and `r_low_m`. A radius is measured from the body center. An altitude is height above that body's radius.
6. Report `dv_depart_m_s`, `dv_capture_m_s`, and `dv_total_m_s`. `dv_total_m_s` is those two burns. Report `C3_m2_s2` for the selected Earth departure.
7. Report `plane_change_at` as `depart` or `arrive`, `di_rad`, and both candidate totals. The selected total is the smaller one.
8. Report `tof_s`, `phase_rad`, `synodic_s`, `a_m`, `e`, and `direction` for the heliocentric coast.
9. Report `soi_earth_m` and `soi_target_m`.
10. Repeat each `warning` when it is printed.
11. If `--to`, `--h-leo`, or `--h-arrive` is missing, say so. Do not fill it in.
