---
name: ASTRO - CoverageAndRevisit
description: >-
  Run the coverage program and report its printed results and optional PNG.
  Use when the user wants the ground swath of one satellite above an elevation
  mask, and how many orbits until that swath covers the equator again. Do not
  redraw the plot or recompute the numbers by hand.
---

# ASTRO - CoverageAndRevisit

Use this skill for one satellite: how wide a strip of Earth it can see on one pass, and how many orbits until the next pass covers the equator again. The Earth is a sphere with the same default radius as the other orbit skills. The instrument is usable only above a minimum elevation. Higher latitudes are covered more often; this skill does not compute that. It does not size a Walker constellation, overlapping planes, or a sensor field of view narrower than the elevation mask. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The Earth-central half-angle is `elevation_mask_earth_angle`,

\[
\sin\rho = \frac{R_0}{R_0+h}\cos\varepsilon,\qquad \lambda = \pi/2 - \varepsilon - \rho
\]

The swath arc is `swath_arc`, \(2 R_0\lambda\). The footprint radius is `footprint_radius`, \(R_0\lambda\). The nodal gap is Earth rotation over one orbital period. Equatorial revisit is the ceiling of that gap divided by the swath angle.

## When to run

1. Use this skill when the user wants swath, footprint radius, or equatorial revisit for one satellite.
2. Convert altitude or radius to metres and elevation to radians. State the converted units in the reply. Do not invent the orbit or the mask.
3. Pass `--elev-min` and exactly one of `--alt` or `--a`.
4. Pass `--out` only when the user wants the PNG of swath versus minimum elevation. Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for a Walker constellation or a latitude other than the equator.

## Flags

Run:

```text
python "skills/ASTRO - CoverageAndRevisit/coverage_and_revisit.py" (--alt <m> | --a <m>) --elev-min <rad> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Circular altitude | m, \(> 0\) | One of `--alt` or `--a` |
| `--a` | Circular radius | m, \(> R_0\) | One of `--alt` or `--a` |
| `--elev-min` | Minimum elevation | rad, \([0, \pi/2)\) | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Coverage and revisit`. The curve is swath versus minimum elevation at the fixed altitude. The square is the operating mask. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `swath_m`, `footprint_m`, `period_s`, `nodal_gap_rad`, `revisit_periods`, and `revisit_s`.
4. Report that the revisit is a single satellite at the equator.
5. If the orbit or the elevation mask is missing, say so. Do not fill them in.
