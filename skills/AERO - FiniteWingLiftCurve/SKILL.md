---
name: AERO - FiniteWingLiftCurve
description: >-
  Run the finite-wing lift-curve program and report its printed results and
  PDF. Use when the user wants the wing lift-curve slope, the induced angle
  at stall, or lift coefficient versus angle of attack up to stall from a
  section slope, zero-lift angle, maximum lift coefficient, aspect ratio,
  and span efficiency. Do not redraw the curve or recompute the numbers by
  hand.
---

# AERO - FiniteWingLiftCurve

Use this skill for the straight lifting-line lift curve of a wing. Run the program once; quote its stdout and include its PDF. Do not redraw the curve or recompute the numbers by hand.

The wing slope is `wing_lift_curve_slope`, per radian:

\[
a = \frac{a_0}{1 + \dfrac{a_0}{\pi\, AR\, e}}
\]

The induced angle at a lift coefficient is `induced_angle`. The printed value is that angle at \(C_{L,\max}\):

\[
\alpha_i = \frac{C_{L,\max}}{\pi\, AR\, e}
\]

At \(e = 1\) this is `elliptic_induced_angle`. The straight line is `wing_lift_coefficient`,

\[
C_L = a(\alpha - \alpha_{L0})
\]

and it ends at `stall_angle`,

\[
\alpha_{\mathrm{stall}} = \alpha_{L0} + \frac{C_{L,\max}}{a}
\]

The PDF is that line from the zero-lift angle to stall. The line is the lift coefficient while \(C_L\) is below \(C_{L,\max}\).

## When to run

1. Use this skill when the user wants a finite-wing lift curve, a wing lift-curve slope, or the induced angle from a section slope, a zero-lift angle, \(C_{L,\max}\), aspect ratio, and span efficiency.
2. Convert the zero-lift angle to radians before the call. A section slope given per degree is \(a_0 = a_{0,\mathrm{deg}}\cdot 180/\pi\) per radian. State the converted units in the reply. Do not invent \(a_0\), \(\alpha_{L0}\), \(C_{L,\max}\), aspect ratio, or \(e\).
3. Pass \(0 < e \le 1\). An elliptic wing uses \(e = 1\).

## Flags

Run:

```text
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --a0 <1/rad> --alpha-l0 <rad> --clmax <CLmax> --ar <AR> --e <e> [--out <pdf>]
```

Pass **only** flags the user supplied (after converting the zero-lift angle to radians and a per-degree section slope to per radian).

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a0` | Section lift-curve slope \(a_0\) | 1/rad, \(> 0\) | Required |
| `--alpha-l0` | Zero-lift angle \(\alpha_{L0}\) | rad | Required |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | Required |
| `--e` | Span efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--out` | PDF path | — | Optional |

A zero-lift angle in degrees uses `alpha_l0_rad = alpha_l0_deg * pi/180`. A section slope in per degree uses `a0_per_rad = a0_per_deg * 180/pi`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PDF at `graph:`. The figure title is `Finite-wing lift curve`. The line runs from the zero-lift angle to stall.
3. Report `a0_per_rad`, `alpha_L0_rad`, `CLmax`, `AR`, and `e`.
4. Report `a_per_rad` and `a_per_deg`. `a_per_deg` is `a_per_rad` times \(\pi/180\).
5. Report `alpha_i_stall_rad` and `alpha_i_stall_deg`. That induced angle is the value at \(C_{L,\max}\).
6. Report `alpha_stall_rad` and `alpha_stall_deg`. That is the geometric angle where the straight line reaches \(C_{L,\max}\).
7. If a section slope, zero-lift angle, \(C_{L,\max}\), aspect ratio, or span efficiency is missing, or outside the program limits, say so. Do not fill it in.
