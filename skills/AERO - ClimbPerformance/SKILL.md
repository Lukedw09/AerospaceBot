---
name: AERO - ClimbPerformance
description: >-
  Run the climb-performance program and report its printed results and PNG.
  Use when the user wants best-rate speed, rate of climb, climb angle, or
  service and absolute ceilings versus geometric altitude from weight, wing
  area, zero-lift drag, aspect ratio, Oswald efficiency, and constant thrust
  or useful power, with the 1976 atmosphere. Do not redraw the plot or
  recompute the numbers by hand. Companion to AERO - AirplanePerformanceParameters,
  which is sea-level only. This is not AERO - NormalShock.
---

# AERO - ClimbPerformance

Use this skill for best-rate climb versus geometric altitude on a parabolic drag polar. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand. For sea-level point speeds without an altitude sweep, use `AERO - AirplanePerformanceParameters`.

Rate of climb is `rate_of_climb` with the small-angle \(L = W\) model,

\[
P_s = \frac{(T-D)V}{W}.
\]

Constant useful power uses `rate_of_climb_from_power` \(P_s = (P - D V)/W\), which is the same statement after `useful_thrust`. Climb angle is `climb_angle` / `climb_angle_from_rate`. Drag is `drag_force` on `drag_polar` at \(C_L = W/(q S)\). Jet best-rate speed maximizes \(V(T-D)\). Propeller best-rate speed is the minimum-power point \(C_L = \sqrt{3 C_{D0}/k}\).

Service ceiling is the geometric altitude where that best rate equals `service_ceiling_rate`. An omitted `--cutoff` is the FAA-H-8083-25C Chapter 11 value of 100 feet per minute (\(0.508\,\mathrm{m/s}\)). Do not invent another default. Absolute ceiling is best rate equal to zero. Density versus altitude is the 1976 standard. Off-nominal temperature or humidity uses `AERO - DensityAndPressureAltitude` at the 1976 station pressure with a constant temperature offset from the ground. If that humidity would exceed local pressure higher up, that altitude is treated as dry.

The figure plots best rate of climb against geometric altitude and marks the cutoff, service ceiling, and absolute ceiling when they exist. An omitted `--z-end` ends the figure at 1.1 times the absolute ceiling (10 percent above it). Pass `--z-end` only when the user asked for another top, including the full 86 km model.

## When to run

1. Use this skill when the user wants rate of climb, best-rate speed, climb angle, a service or absolute ceiling, or a rate-of-climb versus geometric-altitude plot from weight, wing area, \(C_{D0}\), aspect ratio, Oswald efficiency, and thrust or useful power.
2. Convert inputs to SI before the call (N, m², K, kg/m³, W). State the converted units in the reply. Do not invent \(C_{D0}\), aspect ratio, Oswald efficiency, thrust, power, altitude, or density.
3. Pass `--thrust` or `--power`, not both. `--power` is useful power delivered to the airplane. If the user gives shaft power and propeller efficiency separately, multiply first and say so.
4. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres of the ground (start of the sweep). The program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit. Off-nominal temperature or humidity uses `--alt` with `--oat` and optional `--rh`. Do not pass `--oat` with `--rho`. `--rho` is inverted on the 1976 density profile to a geometric density altitude, then the sweep is standard 1976.
5. Pass `--clmax` only when the user gave a stall lift coefficient. Pass `--z` only for extra geometric altitudes to print. Pass `--cutoff` only when the user gave a service-ceiling rate; otherwise omit it. Pass `--z-end` only when the user asked for a plot top other than 10 percent above the absolute ceiling.

## Flags

Run:

```text
python "skills/AERO - ClimbPerformance/climb_performance.py" --weight <N> --area <m^2> --cd0 <CD0> --ar <AR> --e <e> (--thrust <N> | --power <W>) (--alt <m> | --rho <kg/m^3>) [--oat <K>] [--rh <phi>] [--clmax <CLmax>] [--cutoff <m/s>] [--z <m>] [--z-end <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--weight` | Weight \(W\) | N, \(> 0\) | Required |
| `--area` | Wing planform area \(S\) | m², \(> 0\) | Required |
| `--cd0` | Zero-lift drag coefficient \(C_{D0}\) | dimensionless, \(> 0\) | Required |
| `--ar` | Aspect ratio \(AR\) | dimensionless, \(> 0\) | Required |
| `--e` | Oswald efficiency \(e\) | dimensionless, \(0 < e \le 1\) | Required |
| `--thrust` | Net thrust, independent of speed | N, \(> 0\) | Or `--power` |
| `--power` | Useful power, independent of speed | W, \(> 0\) | Or `--thrust` |
| `--alt` | Geometric ground altitude | m, 0 to 86000 | Or `--rho` |
| `--rho` | Air density at the field | kg/m³, \(> 0\) | Or `--alt` |
| `--oat` | Outside air temperature at the ground | K, \(> 0\) | Optional, with `--alt` |
| `--rh` | Relative humidity \(\phi\) | dimensionless, \(0 \le \phi \le 1\) | Optional, with `--oat`. Omitted with `--oat` is dry |
| `--clmax` | Maximum lift coefficient \(C_{L,\max}\) | dimensionless, \(> 0\) | Optional. Stall check |
| `--cutoff` | Service-ceiling rate of climb | m/s, \(> 0\) | Optional. Default `service_ceiling_rate` (100 ft/min) |
| `--z` | Extra geometric altitude to print | m, 0 to 86000 | Optional, repeatable |
| `--z-end` | Geometric altitude at the top of the PNG | m, 0 to 86000 | Optional. Default is 1.1 times the absolute ceiling |
| `--out` | PNG path | — | Optional |

A mass in kilograms is `W = m * 9.80665` newtons. A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. Wing area in square feet uses `1 ft² = 0.09290304 m²`. Altitude in feet uses `1 ft = 0.3048 m`. Thrust in pounds-force uses the same lbf factor. Shaft horsepower uses `1 hp = 745.6998715822702 W` before multiplying by propeller efficiency. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. A relative humidity in percent is the fraction on 0 to 1 (`50%` is `--rh 0.5`). A cutoff in feet per minute uses `1 ft/min = 0.3048/60 m/s`. \(C_{D0}\) is a coefficient. A zero-lift drag force in newtons is not `--cd0`.

Every successful run writes one PNG. The plot title is `Rate of climb`. The model is incompressible; there is no Mach correction. Thrust and useful power do not fall with altitude.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The vertical axis is geometric altitude from the ground to `Z_plot_m`. `z_plot_source` is `absolute` for the default 10 percent above the absolute ceiling, `flag` when `--z-end` was passed, `service` if there is no absolute ceiling, and `model` if the hydrostatic top is used. The curve is best rate of climb. The dashed vertical line is the service-ceiling cutoff. Squares mark the ground, service ceiling, and absolute ceiling when those altitudes exist.
3. Report `engine`. `thrust` is `--thrust`. `power` is `--power`. Report `weight_N`, `area_m2`, `CD0`, `AR`, `e`, `k`, `roc_cutoff_m_s`, `roc_cutoff_source`, `Z_plot_m`, and `z_plot_source`. `default` on the cutoff means 100 ft/min from FAA-H-8083-25C. `flag` means `--cutoff` was passed. Report `CLmax` when it is printed.
4. Report `density_source`. For `altitude`, state that density follows the 1976 standard versus geometric altitude. For `oat`, report `T_ground_K`, `dT_K`, `rh`, and `rh_source`, and state that each altitude uses 1976 pressure with that constant temperature offset and `AERO - DensityAndPressureAltitude`. `dry` means `--rh` was omitted. `flag` means `--rh` was passed. For `density`, report that `--rho` was inverted to 1976 geometric density altitude as `Z_ground_m`.
5. At the ground report `Z_ground_m`, `rho_ground_kg_m3`, `cs_ground_m_s`, `V_roc_ground_m_s`, `roc_ground_m_s`, `gamma_ground_rad`, and `CL_roc_ground`. Angles are radians. Speeds are true airspeed.
6. For each printed `z_i_*` block, report that extra `--z` altitude the same way.
7. When `Z_service_m` is printed, report it with `rho_service_kg_m3`, `V_roc_service_m_s`, and `roc_service_m_s`. That altitude is where best rate equals the cutoff. When `Z_absolute_m` is printed, report it with `rho_absolute_kg_m3` and `V_roc_absolute_m_s`. Best rate there is zero.
8. If `warning` is printed, include it. Constant thrust may never reach the cutoff inside 86 km. A best-rate lift coefficient above `CLmax` is flown at stall speed. Incompressible polar above Mach 0.3 is flagged. A missing ceiling means the hydrostatic model ended first, or the rate never crossed the cutoff.
9. If weight, area, \(C_{D0}\), aspect ratio, Oswald efficiency, thrust or power, or both altitude and density are missing, say so. Do not fill them in.
