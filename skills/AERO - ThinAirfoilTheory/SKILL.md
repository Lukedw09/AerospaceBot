---
name: AERO - ThinAirfoilTheory
description: >-
  Run the thin-airfoil program and report its printed section lift and PNG.
  Use when the user wants inviscid thin-section lift from angle of attack,
  or the zero-lift angle and quarter-chord moment of a NACA four-digit mean
  line. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - ThinAirfoilTheory

Use this skill for inviscid, incompressible, two-dimensional thin-section theory. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Section lift is `thin_airfoil_section_lift`, \(c_l=2\pi(\alpha-\alpha_{L0})\). A NACA four-digit mean line uses `naca4_glauert_station`, `naca4_zero_lift_angle`, `naca4_glauert_A1`, `naca4_glauert_A2`, and `naca4_quarter_chord_moment`.

Measured tunnel polars stay on `AERO - NACAFourDigitSection`. A sealed-flap effectiveness is not in the recorded government expressions, so flap angle is not an input.

## When to run

1. Use this skill for inviscid section lift, zero-lift angle, or quarter-chord moment. Do not use it for a wind-tunnel \(c_l\), \(c_d\), or \(c_m\).
2. Path A is `--alpha` with optional `--alpha-l0`. Path B is a four-digit mean line `--m` and `--p`, with optional `--alpha`.
3. Angles are radians. \(m\) and \(p\) are fractions of chord, not the NACA percent digits. NACA 2412 is `--m 0.02 --p 0.4`.
4. Do not invent \(\alpha\), \(\alpha_{L0}\), \(m\), or \(p\). One section state is one run.

## Flags

Run:

```text
python "skills/AERO - ThinAirfoilTheory/thin_airfoil_theory.py" [--alpha <rad>] [--alpha-l0 <rad>] [--m <fraction>] [--p <fraction>] [--out <png>]
```

Pass **only** flags the user supplied.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alpha` | Geometric angle of attack | rad | Optional; required on path A |
| `--alpha-l0` | Angle of attack for zero lift | rad | Optional. Path A default is 0. |
| `--m` | Maximum camber as a fraction of chord | dimensionless | Optional; required with `--p` on path B |
| `--p` | Chordwise station of maximum camber | dimensionless | Optional; required with `--m` on path B |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Thin airfoil section lift`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The line is \(c_l\) versus \(\alpha\) in radians. The square marks the given angle when one was supplied. Path B annotates \(c_{m,c/4}\).
3. Report `path`, `cl_alpha`, and `cl` when an angle was supplied.
4. On path A, report `alpha`, `alpha_L0`, and `alpha_L0_source`.
5. On path B, report `m`, `p`, `alpha_L0`, `A1`, `A2`, and `cm_c4`. Report `alpha` and `cl` when `--alpha` was passed.
6. If the path is incomplete, say so. Do not fill it in. If the user asks for a flap or for tunnel data, say this skill does not cover that.
