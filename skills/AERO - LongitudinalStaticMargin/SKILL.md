---
name: AERO - LongitudinalStaticMargin
description: >-
  Run the stick-fixed longitudinal static-margin program and report its
  printed results. Use when the user wants the neutral point or the static
  margin from wing-fuselage and tail lift-curve slopes, downwash slope,
  tail dynamic-pressure ratio, tail area and length, wing area, mean
  aerodynamic chord, and center-of-gravity position. Do not recompute the
  numbers by hand.
---

# AERO - LongitudinalStaticMargin

Use this skill for the stick-fixed neutral point and static margin of the simplified airplane in NACA TN 1670. Run the program once and quote its stdout. Do not recompute the numbers by hand.

The neutral point is `stick_fixed_neutral_point`. \(x_0\) is measured aft from the wing-fuselage aerodynamic center:

\[
\frac{x_0}{c}
= \left(1 - \frac{\mathrm{d}\epsilon}{\mathrm{d}\alpha}\right)
\frac{(\mathrm{d}C_L/\mathrm{d}\alpha)_T}{\mathrm{d}C_L/\mathrm{d}\alpha}
\frac{q_T}{q}
\frac{S_T}{S}
\frac{l}{c}
\]

The distance from the center of gravity to that neutral point is `center_of_gravity_to_neutral_point`:

\[
\frac{x}{c} = \frac{x_0}{c} - \frac{x'}{c}
\]

The static margin is `static_margin`, that distance in percent of the mean aerodynamic chord:

\[
\text{static margin} = 100\,\frac{x}{c}
\]

A positive static margin means the center of gravity is ahead of the neutral point. \(q_T/q\) is the tail dynamic-pressure ratio. In TN 1670 the symbol \(\eta\) is propeller efficiency, not this ratio. \(l\) is the tail length from the neutral point to the tail quarter-chord.

## When to run

1. Use this skill when the user wants a stick-fixed neutral point or a static margin for this simplified wing-fuselage-tail airplane.
2. Convert lengths to metres and areas to square metres before the call. State the converted units in the reply. Do not invent a slope, a downwash, a dynamic-pressure ratio, a length, or a center-of-gravity position.
3. Pass both lift-curve slopes in the same angle unit. The program does not convert per degree to per radian. The ratio is unchanged either way. Pass \(\mathrm{d}\epsilon/\mathrm{d}\alpha\) in that same angle measure.
4. `--cg` is \(x'/c\), the center of gravity aft of the wing-fuselage aerodynamic center. If the user gives the center of gravity and the aerodynamic center as fractions of the mean aerodynamic chord from the leading edge, pass their difference. If either location is missing, say so and stop. Do not assume the aerodynamic center is at the quarter chord.
5. `--tail-length` is measured from the neutral point, not from the supplied center of gravity. If the user gives an arm from the current center of gravity only, say so and stop. Do not shift that arm yourself.
6. If the user gives one number they call tail volume, do not pass it in place of area, length, wing area, and chord unless it is exactly \((S_T/S)(l/c)\) and the four geometry values are still known. This program has no tail-volume flag.

## Flags

Run:

```text
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --a <slope> --at <slope> --downwash <dε/dα> --q-ratio <qT/q> --tail-area <m^2> --tail-length <m> --wing-area <m^2> --mac <m> --cg <x'/c>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Wing-fuselage lift-curve slope \(\mathrm{d}C_L/\mathrm{d}\alpha\) | same angle unit as `--at`, \(> 0\) | Required |
| `--at` | Tail lift-curve slope \((\mathrm{d}C_L/\mathrm{d}\alpha)_T\), elevator fixed | same angle unit as `--a` | Required |
| `--downwash` | Downwash slope \(\mathrm{d}\epsilon/\mathrm{d}\alpha\) | dimensionless | Required |
| `--q-ratio` | Tail dynamic-pressure ratio \(q_T/q\) | dimensionless, \(> 0\) | Required |
| `--tail-area` | Horizontal-tail area \(S_T\) | m², \(> 0\) | Required |
| `--tail-length` | Tail length \(l\) from the neutral point to the tail quarter-chord | m, \(> 0\) | Required |
| `--wing-area` | Wing area \(S\) | m², \(> 0\) | Required |
| `--mac` | Wing mean aerodynamic chord \(c\) | m, \(> 0\) | Required |
| `--cg` | \(x'/c\), center of gravity aft of the wing-fuselage aerodynamic center | dimensionless | Required |

A length in feet uses `1 ft = 0.3048 m`. A length in inches uses `1 in = 0.0254 m`. An area in square feet uses `1 ft² = 0.09290304 m²`. A bare length is metres.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `a`, `aT`, `downwash`, and `qT_over_q`. State that both slopes were passed in the same angle unit and that `qT_over_q` is the dynamic-pressure ratio.
3. Report `tail_area_m2`, `tail_length_m`, `wing_area_m2`, `mac_m`, and `tail_volume`. `tail_volume` is \((S_T/S)(l/c)\). State that `tail_length_m` is measured from the neutral point.
4. Report `cg_over_c`. State that it is measured aft from the wing-fuselage aerodynamic center.
5. Report `neutral_point_x0_over_c`. That is the stick-fixed neutral point aft of the same aerodynamic center.
6. Report `x_over_c` and `static_margin_percent`. A static margin of 5 is five percent of the mean aerodynamic chord. Report `stability`. `stable` means the center of gravity is ahead of the neutral point. `unstable` means it is behind. `neutral` means the two coincide.
7. State that drag and propeller forces are omitted, and that the result is the stick-fixed value for the simplified airplane.
8. If a required value is missing, or a value is outside the program limits, say so. Do not fill it in.
