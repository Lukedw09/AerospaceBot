---
name: AERO - SteadyGlide
description: >-
  Run the steady-glide program and report its printed results and PNG. Use when
  the user wants best L/D, sink rate, glide angle, or unpowered range from a
  height, from weight, wing area, zero-lift drag coefficient, aspect ratio,
  Oswald efficiency, and geometric altitude. Do not redraw the plot or
  recompute the numbers by hand.
---

# AERO - SteadyGlide

Use this skill for a steady, unpowered, unaccelerated glide on a parabolic drag polar. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The polar is `drag_polar` with `induced_drag_coefficient`. Best \(L/D\) is `max_lift_to_drag`:

\[
\left(\frac{L}{D}\right)_{\max} = \frac{1}{2}\sqrt{\frac{\pi\, AR\, e}{C_{D0}}}
\]

at \(C_L = \sqrt{\pi\, AR\, e\, C_{D0}}\) and \(C_D = 2 C_{D0}\). The glide angle is `glide_angle`:

\[
a = \operatorname{atan}\!\left(\frac{D}{L}\right)
\]

so the shallowest path is at that best \(L/D\). True airspeed is `glide_speed` with `glide_lift` \(L = W\cos a\):

\[
V = \sqrt{\frac{2 W\cos a}{\rho S C_L}}
\]

Sink rate is `sink_rate` \(v_s = V\sin a\). Horizontal range from a height is `glide_range` \(d = h/\tan a\), which is `glide_range_from_ld` \(d = h(L/D)\). Density is the 1976 standard at `--alt`. `--height` is the height drop for range; it is not that geometric altitude.

The figure plots sink rate against true airspeed at that density. The square is best \(L/D\). The circle is minimum sink.

## When to run

1. Use this skill when the user wants best \(L/D\), a glide angle, a sink rate, unpowered range from a height, or a sink-rate versus true-airspeed plot from weight, wing area, \(C_{D0}\), aspect ratio, Oswald efficiency, and geometric altitude.
2. Convert inputs to SI before the call (N, m², m). State the converted units in the reply. Do not invent \(C_{D0}\), aspect ratio, Oswald efficiency, altitude, \(C_{L,\max}\), or a height.
3. `--alt` is geometric metres. The program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit.
4. Pass `--clmax` only when the user gave a stall lift coefficient. Pass `--height` only when the user gave a height to glide from. Do not copy `--alt` into `--height`.

## Flags

Run:

```text
python "skills/AERO - SteadyGlide/steady_glide.py" --weight <N> --area <m^2> --cd0 <CD0> --ar <AR> --e <e> --alt <m> [--clmax <CLmax>] [--height <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless, \(> 0\) | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | Required |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Required |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Optional. Stall check |
| `--height` | Height drop \(h\) | m, \(> 0\) | Optional. Range |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Altitude or height in feet uses `1 ft = 0.3048 m`. \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

Every successful run writes one PNG. The plot title is `Steady glide`. The model is incompressible; there is no Mach correction.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is true airspeed. The curve is sink rate on the polar. The square is best \(L/D\). The circle is minimum sink. The right-hand end is `plot_end_factor` times the best-\(L/D\) true airspeed. If `CLmax` is printed, a dashed stall mark is the glide speed at that lift coefficient.
3. Report `weight_N`, `area_m2`, `CD0`, `AR`, `e`, `k`, `Z_m`, `rho_kg_m3`, and `cs_m_s`. State that density is the 1976 standard at that geometric altitude.
4. Report `LD_max`, `CL_LDmax`, `CD_LDmax`, `gamma_rad`, `V_LDmax_m_s`, and `vs_LDmax_m_s`. Those angle, speed, and sink values are the best-range glide. `gamma_rad` is radians below the horizontal.
5. Report `CL_min_sink`, `CD_min_sink`, `LD_min_sink`, `gamma_min_sink_rad`, `V_min_sink_m_s`, and `vs_min_m_s`. Minimum sink is not the best-\(L/D\) point.
6. When `h_m` is printed, report `R_m` and `R_min_sink_m`. `R_m` is the best-range glide from that height. `R_min_sink_m` is the shorter range at minimum sink.
7. When `CLmax` is printed, report `V_stall_glide_m_s`. That is `glide_speed` at \(C_{L,\max}\), not the level-flight `stall_speed`.
8. If `warning` is printed, include it. A best-\(L/D\) or min-sink lift coefficient above `CLmax` is below stall. Incompressible polar above Mach 0.3 is flagged.
9. If weight, area, \(C_{D0}\), aspect ratio, Oswald efficiency, or geometric altitude is missing, say so. Do not fill them in. If range was asked for and `--height` is missing, say so and still run the rest.
