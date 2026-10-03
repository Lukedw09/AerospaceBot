---
name: AERO - AirplanePerformanceParameters
description: >-
  Run the airplane point-performance program and report its printed results.
  Use when the user wants stall speed, maximum lift-to-drag ratio, best-range
  or best-endurance speed, or a sea-level climb estimate from weight, wing
  area, zero-lift drag coefficient, aspect ratio, and Oswald efficiency.
  Do not recompute the numbers by hand.
---

# AERO - AirplanePerformanceParameters

Use this skill for point performance of an airplane with a parabolic drag polar. Run the program once and quote its stdout. Do not recompute the numbers by hand.

\[
C_D = C_{D0} + \frac{C_L^{2}}{\pi\, AR\, e}, \quad k = \frac{1}{\pi\, AR\, e}
\]

\[
\left(\frac{L}{D}\right)_{\max} = \frac{1}{2}\sqrt{\frac{\pi\, AR\, e}{C_{D0}}}
\]

at \(C_L = \sqrt{C_{D0}/k}\) and \(C_D = 2 C_{D0}\). Level-flight speed at a lift coefficient is the stall-speed relation with that coefficient in place of \(C_{L,\max}\):

\[
V = \sqrt{\frac{2W}{\rho S C_L}}
\]

Jet means thrust does not change with speed, and fuel flow follows thrust. Propeller means useful power does not change with speed, and fuel flow follows power.

| Schedule | Jet | Propeller |
| --- | --- | --- |
| Best range | \(C_L = \sqrt{C_{D0}/(3k)}\) | \((L/D)_{\max}\) |
| Best endurance | \((L/D)_{\max}\) | \(C_L = \sqrt{3 C_{D0}/k}\) |

Jet best endurance and propeller best range are the same speed. The climb block always uses 1976 sea-level density, including when the speeds above use another altitude or a density the user supplied. A climb rate is printed only when `--thrust` or `--power` is passed. Without them the program still prints the sea-level speed and the thrust or power of level flight at that speed.

## When to run

1. Use this skill when the user wants stall speed, maximum \(L/D\), best-range speed, best-endurance speed, or a sea-level climb estimate from weight, wing area, zero-lift drag, aspect ratio, and Oswald efficiency.
2. Convert inputs to SI before the call (N, m², kg/m³, m, W). State the converted units in the reply. Do not invent \(C_{L,\max}\), thrust, power, altitude, or density.
3. Stall speed needs \(C_{L,\max}\). If it is missing, say so and stop.
4. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres and the program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit. If the user gives both an altitude and a density, ask which one to use.
5. Pass `--thrust` only for a net thrust the user gave, in newtons. Pass `--power` only for a useful power the user gave, in watts. Useful power is thrust times speed, or shaft power times propeller efficiency after the user has already applied that efficiency. If they give shaft power and efficiency separately, multiply first and say so. If they want a climb rate and gave neither, run without those flags and say the rate was not printed.

## Flags

Run:

```text
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --weight <N> --area <m^2> --cd0 <CD0> --ar <AR> --e <e> --clmax <CLmax> (--alt <m> | --rho <kg/m^3>) [--thrust <N>] [--power <W>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N | Required |
| `--area` | Wing planform area \(S\) | m² | Required |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless | Required |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or `--rho` |
| `--rho` | Air density | kg/m³ | Or `--alt` |
| `--thrust` | Net thrust, independent of speed | N | Optional. Jet climb angle and rate |
| `--power` | Useful power, independent of speed | W | Optional. Propeller climb rate |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Altitude in feet uses `1 ft = 0.3048 m`. Thrust in pounds-force uses the same lbf factor. Shaft horsepower uses `1 hp = 745.6998715822702 W` before multiplying by propeller efficiency. \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `weight_N`, `area_m2`, `CD0`, `AR`, `e`, `k`, and `CLmax`.
3. Report `density_source`. For `altitude`, report `Z_m`, `rho_kg_m3`, and `cs_m_s`, and state that density is the 1976 standard at that geometric altitude. For `density`, report `rho_kg_m3` and state that the user supplied it.
4. Report `LD_max`, `CL_LDmax`, and `CD_LDmax`. Maximum \(L/D\) does not depend on weight, area, or density.
5. Report `V_stall_m_s` at the flight density and `V_stall_sl_m_s` at sea level.
6. Report `V_range_jet_m_s`, `V_endurance_jet_m_s`, `V_range_prop_m_s`, and `V_endurance_prop_m_s`. State that jet endurance and propeller range are the maximum-\(L/D\) speed, jet range is faster, and propeller endurance is slower. Report `CL_range_jet`, `CD_range_jet`, `CL_endurance_prop`, and `CD_endurance_prop` with those speeds.
7. Report the sea-level climb estimate: `rho_sl_kg_m3`, `V_climb_angle_sl_m_s`, `thrust_level_min_sl_N`, `V_climb_rate_prop_sl_m_s`, and `power_level_min_sl_W`. The first pair is the jet steepest-climb speed and the thrust of level flight there. The second pair is the propeller best-rate speed and the useful power of level flight there. Climb starts above those level-flight values.
8. When `thrust_N` is printed, report `sin_gamma_max_angle`, `gamma_max_angle_rad`, `roc_at_max_angle_m_s`, `V_climb_rate_jet_sl_m_s`, `roc_jet_m_s`, and `gamma_jet_roc_rad` when it is printed. `roc_jet_m_s` is the best rate. `roc_at_max_angle_m_s` is the rate at the steepest climb, which is a different speed. Angles are radians.
9. When `power_W` is printed, report `roc_prop_m_s` and `gamma_prop_rad` when it is printed. That rate is at `V_climb_rate_prop_sl_m_s`.
10. A negative rate is a descent at that speed. Omit thrust, power, angles, and rates that were not printed.
11. If `warning` is printed, include it. A schedule whose lift coefficient is above `CLmax` is below stall. A climb rate is absent until thrust or power is passed.
12. If weight, area, \(C_{D0}\), aspect ratio, Oswald efficiency, \(C_{L,\max}\), or both altitude and density are missing, say so. Do not fill them in.
