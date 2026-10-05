---
name: AERO - TakeoffGroundRoll
description: >-
  Run the takeoff ground-roll program and report its printed results and PNG.
  Use when the user wants stall speed, lift-off speed, or ground-roll distance
  and time on a level dry runway from weight, wing area, takeoff lift
  coefficient, rolling friction, thrust or useful power, a parabolic polar,
  and density or geometric altitude. Do not redraw the plot or recompute the
  numbers by hand.
---

# AERO - TakeoffGroundRoll

Use this skill for the ground roll from brake release to lift-off on a level, dry, zero-wind runway. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Wheel load is `wheel_normal_force` \(N = W - L\). Rolling friction is `rolling_friction` \(F_r = \mu N\). Net force is `ground_roll_net_force`:

\[
F = T - D - \mu(W - L)
\]

Acceleration is `ground_roll_acceleration` \(a = g F/W\) with \(g = 9.80665\,\mathrm{m/s}^{2}\). Lift and drag use `lift_force`, `drag_force`, and `drag_polar` at a constant takeoff lift coefficient. Takeoff stall speed is `stall_speed` at \(C_{L,\max}\) when that coefficient is given, otherwise at \(C_{L,\mathrm{TO}}\). Lift-off true airspeed is `liftoff_speed`:

\[
V_{\mathrm{LO}} = k_{\mathrm{LO}} V_{\mathrm{stall}}
\]

An omitted `--k-lo` is \(1.2\). Constant thrust uses `ground_roll_A`, `ground_roll_B`, `ground_roll_distance`, and `ground_roll_time`. Useful power uses `useful_thrust` \(T = P/V\) capped at `--static`, and integrates \(V/a\) numerically.

The figure plots true airspeed against ground distance and marks lift-off. Obstacle distance, climb-out, wind, slope, a wet runway, rotation as its own segment, balanced field length, and calibrated airspeed are omitted.

## When to run

1. Use this skill when the user wants takeoff stall speed, lift-off speed, ground-roll distance or time, brake-release or lift-off forces, or a true-airspeed versus ground-distance plot on a level dry runway.
2. Convert inputs to SI before the call (N, m², K, kg/m³, W). State the converted units in the reply. Do not invent \(C_{L,\mathrm{TO}}\), \(\mu\), \(C_{D0}\), aspect ratio, Oswald efficiency, thrust, power, static thrust, altitude, or density.
3. Pass `--thrust` or `--power`, not both. `--power` also needs `--static`. `--power` is useful power delivered to the airplane. If the user gives shaft power and propeller efficiency separately, multiply first and say so.
4. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres and the program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit. Off-nominal temperature or humidity uses `--alt` with `--oat` and optional `--rh`; the program uses `AERO - DensityAndPressureAltitude` at the 1976 station pressure for that altitude. Do not pass `--oat` with `--rho`.
5. Pass `--clmax` only when the user gave a stall lift coefficient. Do not copy `--clto` into `--clmax`.

## Flags

Run:

```text
python "skills/AERO - TakeoffGroundRoll/takeoff_ground_roll.py" --weight <N> --area <m^2> --clto <CL_TO> --mu <mu> --cd0 <CD0> --ar <AR> --e <e> (--thrust <N> | --power <W> --static <N>) (--alt <m> | --rho <kg/m^3>) [--oat <K>] [--rh <phi>] [--k-lo <k>] [--clmax <CLmax>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--clto` | Takeoff lift coefficient \(C_{L,\mathrm{TO}}\) | dimensionless, \(> 0\) | Required |
| `--mu` | Rolling-friction coefficient \(\mu\) | dimensionless, \(\ge 0\) | Required |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless, \(> 0\) | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | Required |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--thrust` | Net thrust, independent of speed | N, \(> 0\) | Or `--power` |
| `--power` | Useful power, independent of speed | W, \(> 0\) | Or `--thrust` |
| `--static` | Finite static thrust | N, \(> 0\) | With `--power` |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or `--rho` |
| `--rho` | Air density | kg/m³, \(> 0\) | Or `--alt` |
| `--oat` | Outside air temperature | K, \(> 0\) | Optional, with `--alt` |
| `--rh` | Relative humidity \(\phi\) | dimensionless, \(0 \le \phi \le 1\) | Optional, with `--oat`. Omitted with `--oat` is dry |
| `--k-lo` | Lift-off factor \(k_{\mathrm{LO}}\) | dimensionless, \(> 0\) | Optional. Default \(1.2\) |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Optional. Stall \(C_L\) |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Altitude in feet uses `1 ft = 0.3048 m`. Thrust in pounds-force uses the same lbf factor. Shaft horsepower uses `1 hp = 745.6998715822702 W` before multiplying by propeller efficiency. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. A relative humidity in percent is the fraction on 0 to 1 (`50%` is `--rh 0.5`). \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

Every successful run writes one PNG. The plot title is `Takeoff ground roll`. The model is incompressible; there is no Mach correction.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is ground distance. The curve is true airspeed. The square is lift-off.
3. Report `method`. `closed-form constant thrust` is `--thrust`. `numerical` is `--power`.
4. Report `weight_N`, `area_m2`, `CL_TO`, `mu`, `CD0`, `AR`, `e`, `k`, `CD`, `k_LO`, and `g0_m_s2`. Report `CLmax` when it is printed.
5. Report `density_source`. For `altitude`, report `Z_m`, `rho_kg_m3`, and `cs_m_s`, and state that density is the 1976 standard at that geometric altitude. For `oat`, report `Z_m`, `p_Pa`, `T_K`, `rh`, `rh_source`, `rho_kg_m3`, and `cs_m_s`. `dry` means `--rh` was omitted. `flag` means `--rh` was passed. For `density`, report `rho_kg_m3` and state that the user supplied it.
6. Report `V_stall_m_s`, `stall_CL`, `V_LO_m_s`, `q_LO_Pa`, and `LD_LO`. `stall_CL` is `CLmax` when that flag was passed, otherwise `CL_TO`. Speeds are true airspeed, not calibrated airspeed.
7. At brake release report `thrust_0_N`, `Fr_0_N`, `F_0_N`, and `a_0_m_s2`. At lift-off report `thrust_LO_N`, `L_LO_N`, `D_LO_N`, `N_LO_N`, `Fr_LO_N`, `F_LO_N`, and `a_LO_m_s2`.
8. Report `s_m` and `t_s`. When `method` is `closed-form constant thrust`, also report `A_m_s2` and `B_1_m`. When it is `numerical`, report `power_W` and `static_thrust_N`.
9. If `warning` is printed, include it. A lift-off factor below 1, or an incompressible polar above Mach 0.3, is flagged. Lift above weight before lift-off is an error, not a warning.
10. If weight, area, takeoff lift coefficient, \(\mu\), \(C_{D0}\), aspect ratio, Oswald efficiency, a density path, or thrust or power is missing, say so. If `--power` is missing `--static`, say so. Do not fill them in.
