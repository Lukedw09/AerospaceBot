---
name: AERO - LandingGroundRoll
description: >-
  Run the landing ground-roll program and report its printed results and PNG.
  Use when the user wants stall speed, touchdown speed, or ground-roll distance
  and time on a level dry runway from weight, wing area, touchdown lift
  coefficient, braking friction, a parabolic polar, optional idle thrust, and
  density or geometric altitude. Do not redraw the plot or recompute the
  numbers by hand.
---

# AERO - LandingGroundRoll

Use this skill for the ground roll from touchdown to rest on a level, dry, zero-wind runway. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Wheel load is `wheel_normal_force` \(N = W - L\). Braking friction is `rolling_friction` \(F_r = \mu N\). Net force is `ground_roll_net_force`:

\[
F = T - D - \mu(W - L)
\]

Acceleration is `ground_roll_acceleration` \(a = g F/W\) with \(g = 9.80665\,\mathrm{m/s}^{2}\). Lift and drag use `lift_force`, `drag_force`, and `drag_polar` at a constant touchdown lift coefficient. Landing stall speed is `stall_speed` at \(C_{L,\max}\) when that coefficient is given, otherwise at \(C_{L,\mathrm{TD}}\). Touchdown true airspeed is `touchdown_speed`:

\[
V_{\mathrm{TD}} = k_{\mathrm{TD}} V_{\mathrm{stall}}
\]

An omitted `--k-td` is \(1.3\). An omitted `--thrust` is idle \(T = 0\). Constant thrust uses `ground_roll_A`, `ground_roll_B`, `landing_ground_roll_distance`, and `landing_ground_roll_time`.

The figure plots true airspeed against ground distance and marks rest. Flare, float, obstacle distance, wind, slope, a wet runway, a reverse-thrust schedule, and calibrated airspeed are omitted.

## When to run

1. Use this skill when the user wants landing stall speed, touchdown speed, ground-roll distance or time, touchdown or rest forces, or a true-airspeed versus ground-distance plot on a level dry runway.
2. Convert inputs to SI before the call (N, m², K, kg/m³). State the converted units in the reply. Do not invent \(C_{L,\mathrm{TD}}\), \(\mu\), \(C_{D0}\), aspect ratio, Oswald efficiency, altitude, or density.
3. Omit `--thrust` when the user does not give idle or reverse thrust. That run is \(T = 0\). Pass `--thrust` for a single constant value, including reverse (negative). Do not invent a reverse-thrust schedule.
4. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres and the program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit. Off-nominal temperature or humidity uses `--alt` with `--oat` and optional `--rh`; the program uses `AERO - DensityAndPressureAltitude` at the 1976 station pressure for that altitude. Do not pass `--oat` with `--rho`.
5. Pass `--clmax` only when the user gave a stall lift coefficient. Do not copy `--cltd` into `--clmax`. Default \(k_{\mathrm{TD}} = 1.3\) with stall at \(C_{L,\mathrm{TD}}\) lifts the airplane; that case needs a larger stall \(C_L\).

## Flags

Run:

```text
python "skills/AERO - LandingGroundRoll/landing_ground_roll.py" --weight <N> --area <m^2> --cltd <CL_TD> --mu <mu> --cd0 <CD0> --ar <AR> --e <e> (--alt <m> | --rho <kg/m^3>) [--thrust <N>] [--oat <K>] [--rh <phi>] [--k-td <k>] [--clmax <CLmax>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--cltd` | Touchdown lift coefficient \(C_{L,\mathrm{TD}}\) | dimensionless, \(> 0\) | Required |
| `--mu` | Braking-friction coefficient \(\mu\) | dimensionless, \(\ge 0\) | Required |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless, \(> 0\) | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | Required |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or `--rho` |
| `--rho` | Air density | kg/m³, \(> 0\) | Or `--alt` |
| `--thrust` | Net thrust, independent of speed | N | Optional. Omitted is \(0\) |
| `--oat` | Outside air temperature | K, \(> 0\) | Optional, with `--alt` |
| `--rh` | Relative humidity \(\phi\) | dimensionless, \(0 \le \phi \le 1\) | Optional, with `--oat`. Omitted with `--oat` is dry |
| `--k-td` | Touchdown factor \(k_{\mathrm{TD}}\) | dimensionless, \(> 0\) | Optional. Default \(1.3\) |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Optional. Stall \(C_L\) |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Altitude in feet uses `1 ft = 0.3048 m`. Thrust in pounds-force uses the same lbf factor. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. A relative humidity in percent is the fraction on 0 to 1 (`50%` is `--rh 0.5`). \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

Every successful run writes one PNG. The plot title is `Landing ground roll`. The model is incompressible; there is no Mach correction.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is ground distance. The curve is true airspeed. The square is rest.
3. Report `method`. Constant thrust, including omitted idle \(T = 0\), is `closed-form constant thrust`.
4. Report `weight_N`, `area_m2`, `CL_TD`, `mu`, `CD0`, `AR`, `e`, `k`, `CD`, `k_TD`, `thrust_N`, and `g0_m_s2`. Report `CLmax` when it is printed.
5. Report `density_source`. For `altitude`, report `Z_m`, `rho_kg_m3`, and `cs_m_s`, and state that density is the 1976 standard at that geometric altitude. For `oat`, report `Z_m`, `p_Pa`, `T_K`, `rh`, `rh_source`, `rho_kg_m3`, and `cs_m_s`. `dry` means `--rh` was omitted. `flag` means `--rh` was passed. For `density`, report `rho_kg_m3` and state that the user supplied it.
6. Report `V_stall_m_s`, `stall_CL`, `V_TD_m_s`, `q_TD_Pa`, and `LD_TD`. `stall_CL` is `CLmax` when that flag was passed, otherwise `CL_TD`. Speeds are true airspeed, not calibrated airspeed.
7. At touchdown report `thrust_TD_N`, `L_TD_N`, `D_TD_N`, `N_TD_N`, `Fr_TD_N`, `F_TD_N`, and `a_TD_m_s2`. At rest report `thrust_0_N`, `L_0_N`, `D_0_N`, `N_0_N`, `Fr_0_N`, `F_0_N`, and `a_0_m_s2`.
8. Report `s_m`, `t_s`, `A_m_s2`, and `B_1_m`.
9. If `warning` is printed, include it. A touchdown factor below 1, or an incompressible polar above Mach 0.3, is flagged. Lift above weight at touchdown is an error, not a warning.
10. If weight, area, touchdown lift coefficient, \(\mu\), \(C_{D0}\), aspect ratio, Oswald efficiency, or a density path is missing, say so. Do not fill them in.
