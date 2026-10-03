---
name: AERO - V-nDiagram
description: >-
  Run the V-n diagram program and report its printed results and PNG. Use
  when the user wants the positive stall boundary, the corner speed, or a
  plot of load factor against equivalent airspeed from weight, wing area,
  maximum lift coefficient, positive and negative limit load factors, and
  air density. Do not redraw the diagram or recompute the numbers by hand.
---

# AERO - V-nDiagram

Use this skill for the positive stall boundary and corner speed of an airplane. Run the program once; quote its stdout and include its PNG. Do not redraw the diagram or recompute the numbers by hand.

The positive stall boundary is `stall_speed` with \(W\) replaced by \(nW\):

\[
V = \sqrt{\frac{2 n W}{\rho S C_{L,\max}}}
\]

That is the same curve as `load_factor` \(n = L/W\) when `lift_force` uses \(C_{L,\max}\) and `freestream_dynamic_pressure` is \(q = \frac{1}{2}\rho V^{2}\). The corner speed is this stall speed at the positive limit load factor.

Speeds on the figure are `stall_speed` at 1976 sea-level density. That speed is `equivalent_airspeed`, because dynamic pressure is unchanged when \(\rho V^{2} = \rho_{\mathrm{sl}} V_e^{2}\). True airspeeds use the density the user supplied.

The negative line is the negative limit load factor. It is not a stall boundary. `stall_speed` has no \(C_{L,\min}\), and \(nW\) has to stay positive for a real speed. Do not draw a negative stall curve.

The right-hand end of the figure is 1.5 times the positive corner equivalent airspeed. That end is not a dive speed.

## When to run

1. Use this skill when the user wants a V-n diagram, a stall boundary, or a corner speed from weight, wing area, \(C_{L,\max}\), limit load factors, and air density.
2. Convert inputs to SI before the call (N, m², kg/m³). State the converted units in the reply. Do not invent \(C_{L,\max}\), a limit load factor, or a density.
3. Pass both `--n-pos` and `--n-neg`. `--n-pos` is greater than 0. `--n-neg` is less than 0.
4. Pass the flight density as `--rho`. The equivalent-airspeed curves still use 1976 sea-level density from `ATMOS - Standard1976`. Do not compute that sea-level density yourself.

## Flags

Run:

```text
python "skills/AERO - V-nDiagram/vn_diagram.py" --weight <N> --area <m^2> --clmax <CLmax> --n-pos <n> --n-neg <n> --rho <kg/m^3> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Required |
| `--n-pos` | Positive limit load factor | dimensionless, \(> 0\) | Required |
| `--n-neg` | Negative limit load factor | dimensionless, \(< 0\) | Required |
| `--rho` | Air density at the flight condition | kg/m³, \(> 0\) | Required |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`.

Every successful run writes one PNG. The plot title is `V-n diagram`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is equivalent airspeed. The curve is the positive stall boundary from \(n = 0\) to `--n-pos`. The corner marker is the positive corner speed. The solid red line is the positive limit. The dashed red line is the negative limit, not a negative stall boundary. The right-hand end is `plot_end_factor` times the corner equivalent airspeed.
3. Report `weight_N`, `area_m2`, `CLmax`, `n_pos`, `n_neg`, and `rho_kg_m3`.
4. Report `rho_sl_kg_m3` and `rho_sl_source`. Sea-level density is the 1976 standard at zero geometric altitude.
5. Report `V_stall_m_s` and `V_stall_eas_m_s`. The first is the 1-g true stall speed at the supplied density. The second is the 1-g point on the plotted stall boundary.
6. Report `V_corner_m_s`, `V_corner_eas_m_s`, `n_corner`, and `q_corner_Pa`. Corner speed is the positive stall speed at `n_pos`. `n_corner` is `load_factor` at that true airspeed and equals `n_pos`.
7. Report `V_plot_max_eas_m_s`. State that this end is not a dive speed.
8. If `warning` is printed, include it. A positive limit below 1 means level flight exceeds that limit.
9. If weight, area, \(C_{L,\max}\), either limit load factor, or density is missing, say so. Do not fill it in.
