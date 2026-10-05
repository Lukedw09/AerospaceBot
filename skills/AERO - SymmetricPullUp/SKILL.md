---
name: AERO - SymmetricPullUp
description: >-
  Run the symmetric pull-up program and report its printed results and PNG.
  Use when the user wants pull-up radius, pitch rate, or load factor for a
  wings-level vertical-plane pull-up from speed, weight, wing area, maximum
  lift coefficient, air density, and either a load factor, a pull-up radius,
  a pitch rate, or a sustained load factor from thrust or power on a
  parabolic polar. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - SymmetricPullUp

Use this skill for an instantaneous symmetric pull-up in the vertical plane, started from straight and level flight. Dynamic pressure is `freestream_dynamic_pressure`, \(q = \frac{1}{2}\rho V^{2}\). Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Load factor, radius, and pitch rate are `pullup_load_factor`, `pullup_radius`, and `pullup_pitch_rate`:

\[
n = 1 + \frac{V^{2}}{g R},\qquad R = \frac{V^{2}}{g(n - 1)},\qquad \omega = \frac{g(n - 1)}{V}
\]

with \(g = 9.80665\,\mathrm{m/s}^{2}\). \(\omega = V/R\). Equivalently \(n = 1 + V\omega/g\). A given `--n`, `--radius`, or `--pitch-rate` determines the others.

The stall limit at a speed is the same speed–stall relation as `AERO - V-nDiagram`: `load_factor` at `lift_force` with \(C_{L,\max}\) and `freestream_dynamic_pressure`, which is `stall_speed` with \(W\) replaced by \(nW\). That load factor is the steepest symmetric pull-up at that speed.

A second way to set \(n\) is `sustained_turn_load_factor`. On `drag_polar`, \(C_D = C_{D0} + k C_L^{2}\) with \(k = 1/(\pi\, AR\, e)\). Lift is \(nW\), so \(C_L = nW/(q S)\). Thrust equals drag:

\[
n = \sqrt{\frac{q S\,(T - q S C_{D0})\,\pi\, AR\, e}{W^{2}}}
\]

That \(n\) is the pull-up the engine can hold at that speed, not the stall geometry. Constant thrust is `--thrust`. Constant useful power is `--power`, and available thrust is `useful_thrust` \(T = P/V\).

The figure always plots pull-up radius and pitch rate against true airspeed at `--rho`. With `--thrust` or `--power` it also plots that sustained load factor against speed. The stall-limit curves use \(C_{L,\max}\) at each speed. The operating point is the given speed.

## When to run

1. Use this skill when the user wants a pull-up radius, pitch rate, load factor, a radius-versus-speed plot with the stall limit, or the sustained load factor the engine can hold versus speed in a vertical-plane pull-up.
2. Convert inputs to SI before the call (m/s, rad/s, N, m², kg/m³, W). State the converted units in the reply. Do not invent \(C_{L,\max}\), a density, \(C_{D0}\), aspect ratio, Oswald efficiency, thrust, or power.
3. Pass exactly one of `--n`, `--radius`, `--pitch-rate`, `--thrust`, or `--power`. A given `--n` must be \(> 1\). If the user gives both radius and pitch rate, convert one to load factor and confirm they match; then pass one of them. If they give an \(n\), radius, or pitch rate and also thrust or power, ask which load factor to use.
4. `--thrust` or `--power` also needs `--cd0`, `--ar`, and `--e`. Do not pass those polar flags with `--n`, `--radius`, or `--pitch-rate`. `--power` is useful power delivered to the airplane. If the user gives shaft power and propeller efficiency separately, multiply first and say so.
5. Pass the flight density as `--rho`. Speeds on the figure are true airspeed at that density, not equivalent airspeed.

## Flags

Run:

```text
python "skills/AERO - SymmetricPullUp/symmetric_pull_up.py" --speed <m/s> --weight <N> --area <m^2> --clmax <CLmax> --rho <kg/m^3> (--n <n> | --radius <m> | --pitch-rate <rad/s> | --thrust <N> | --power <W>) [--cd0 <CD0> --ar <AR> --e <e>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | True airspeed \(V\) | m/s, \(> 0\) | Required |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Required |
| `--rho` | Air density at the flight condition | kg/m³, \(> 0\) | Required |
| `--n` | Load factor \(n\) | dimensionless, \(> 1\) | One of `--n`, `--radius`, `--pitch-rate`, `--thrust`, `--power` |
| `--radius` | Pull-up flight-path radius \(R\) | m, \(> 0\) | One of `--n`, `--radius`, `--pitch-rate`, `--thrust`, `--power` |
| `--pitch-rate` | Pitch rate \(\omega = \dot{\theta}\) | rad/s, \(> 0\) | One of `--n`, `--radius`, `--pitch-rate`, `--thrust`, `--power` |
| `--thrust` | Net thrust, independent of speed | N, \(> 0\) | One of `--n`, `--radius`, `--pitch-rate`, `--thrust`, `--power` |
| `--power` | Useful power, independent of speed | W, \(> 0\) | One of `--n`, `--radius`, `--pitch-rate`, `--thrust`, `--power` |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless, \(> 0\) | With `--thrust` or `--power` |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | With `--thrust` or `--power` |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | With `--thrust` or `--power` |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Speed in knots uses `1 kt = 0.514444 m/s`. Pitch rate in degrees per second is multiplied by \(\pi/180\). Thrust in pounds-force uses the same lbf factor. Shaft horsepower uses `1 hp = 745.6998715822702 W` before multiplying by propeller efficiency. \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

Every successful run writes one PNG. The plot title is `Symmetric pull-up`. The model is incompressible; there is no Mach correction.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is true airspeed. With `--n`, `--radius`, or `--pitch-rate`, the upper panel is pull-up radius and the lower panel is pitch rate. The solid curve is the given load factor. The dashed curve is the stall limit. The square is the operating point. The right-hand end is `plot_end_factor` times the larger of the given speed and the stall speed at that load factor.
3. With `--thrust` or `--power`, the top panel is load factor versus speed. The solid curve is `sustained_turn_load_factor` (thrust equals drag, or power equals drag times speed). The dashed curve is the stall limit. The dotted line is \(n = 1\). The lower panels are radius and pitch rate at that sustained \(n\) where \(n > 1\). The right-hand end is `plot_end_factor` times the larger of the given speed and `V_parasite_m_s`, where parasite drag equals available thrust.
4. Report `n_source`. Report `V_m_s`, `n`, `R_m`, and `omega_rad_s` when they are printed. A sustained \(n \le 1\) has no radius or pitch rate.
5. Report `weight_N`, `area_m2`, `CLmax`, `rho_kg_m3`, `g0_m_s2`, `q_Pa`, and `CL` when `CL` is printed.
6. When `n_source` is `thrust` or `power`, report `CD0`, `AR`, `e`, `k`, `thrust_N` or `power_W`, `thrust_avail_N`, `D_N` when it is printed, and `V_parasite_m_s`. `D_N` equals available thrust at the operating point.
7. Report `V_stall_1g_m_s` and `V_stall_pull_m_s`. The second is `stall_speed` at this load factor, or the 1-g stall when \(n\) is not real.
8. Report `n_stall` when it is printed. That is the steepest load factor at the given speed. Report `n_above_stall` when it is printed: `true` means the asked or sustained \(n\) exceeds `n_stall`. Report `R_stall_m` and `omega_stall_rad_s` when they are printed. Those are the stall-limit radius and pitch rate at the given speed.
9. If `warning` is printed, include it. Speed below the 1-g stall, a requested or sustained load factor above `n_stall`, a sustained \(n \le 1\), or thrust at or below parasite drag means the pull-up is not available at \(C_{L,\max}\) or with that engine.
10. If speed, weight, area, \(C_{L,\max}\), density, or a way to set \(n\) is missing, say so. If `--thrust` or `--power` is missing \(C_{D0}\), aspect ratio, or Oswald efficiency, say so. Do not fill them in.
