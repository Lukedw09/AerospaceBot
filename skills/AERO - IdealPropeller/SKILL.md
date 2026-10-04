---
name: AERO - IdealPropeller
description: >-
  Run the ideal actuator-disk propeller program and report its printed
  results and PNG. Use when the user wants ideal thrust, induced velocity,
  or ideal propulsive efficiency from shaft power, propeller diameter,
  flight speed, and air density or altitude. Do not redraw the plot or
  recompute the numbers by hand.
---

# AERO - IdealPropeller

Use this skill for the incompressible Rankine–Froude actuator disk. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Disk area is `propeller_disk_area`, \(A = \pi D^{2}/4\). Axial speed through the disk is `actuator_disk_speed`, \(V_p = \frac12(V_e + V_0)\). Induced velocity is `propeller_induced_velocity`, \(v_i = V_p - V_0\). Far-wake speed is `propeller_far_wake_speed`, \(V_e = V_0 + 2 v_i\).

Ideal thrust is `ideal_propeller_thrust`, equal to `ideal_propeller_thrust_bernoulli` and to `ideal_propeller_thrust_from_induced`:

\[
T = \rho V_p A(V_e - V_0) = 2\rho A v_i(V_0 + v_i).
\]

Ideal shaft power is `ideal_actuator_power`, \(P = T V_p\), which is `ideal_actuator_power_from_induced`. The program solves that relation for \(v_i\) at the given shaft power. Ideal propulsive efficiency is `ideal_propulsive_efficiency`:

\[
\eta = \frac{T V_0}{P} = \frac{V_0}{V_p}.
\]

Useful power delivered to the airplane is \(T V_0 = \eta P\). That is the `--power` of `AERO - IncompressibleLevelTurn`. Ideal thrust \(T\) is the `--thrust` of that skill. Do not pass shaft power to the turn program as `--power`.

The figure plots ideal thrust, induced velocity, and efficiency against true airspeed at fixed shaft power, diameter, and density. The square is the operating point.

## When to run

1. Use this skill when the user wants ideal propeller thrust, induced velocity, disk speed, far-wake speed, or ideal propulsive efficiency from shaft power, diameter, and flight speed.
2. Convert inputs to SI before the call (W, m, m/s, kg/m³). State the converted units in the reply. Do not invent a power, diameter, speed, density, or altitude.
3. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres and the program looks up the 1976 density. Do not compute that density yourself and do not use the NASA Glenn three-zone fit. If the user gives both an altitude and a density, ask which one to use.
4. `--power` is shaft power in this ideal model, the power added to the slipstream. It is not useful power \(T V\).
5. One power, diameter, speed, and density is one run. The plot is a speed sweep at those other quantities held fixed.

## Flags

Run:

```text
python "skills/AERO - IdealPropeller/ideal_propeller.py" --power <W> --diameter <m> --speed <m/s> (--rho <kg/m^3> | --alt <m>) [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--power` | Ideal shaft power \(P\) | W, \(> 0\) | Required |
| `--diameter` | Propeller diameter \(D\) | m, \(> 0\) | Required |
| `--speed` | True airspeed \(V_0\) | m/s, \(> 0\) | Required |
| `--rho` | Air density at the flight condition | kg/m³, \(> 0\) | Or `--alt` |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or `--rho` |
| `--out` | PNG path | — | Optional |

Shaft horsepower uses `1 hp = 745.6998715822702 W`. Diameter in feet uses `1 ft = 0.3048 m`. Speed in knots uses `1 kt = 1852/3600 m/s`. Altitude in feet uses `1 ft = 0.3048 m`. A density in slugs per cubic foot uses `1 slug/ft³ = 515.3788184 kg/m³`.

Every successful run writes one PNG. The plot title is `Ideal propeller`. The model is incompressible; there is no Mach correction, swirl, tip loss, or blade profile drag.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is true airspeed. The panels are ideal thrust, induced velocity, and ideal propulsive efficiency. The solid curves hold `--power`, `--diameter`, and density fixed. The square is the operating point. The right-hand end is `plot_end_factor` times the given speed.
3. Report `density_source`. For `altitude`, report `Z_m` and `rho_kg_m3`, and state that density is the 1976 standard at that geometric altitude. For `density`, report `rho_kg_m3` and state that the user supplied it.
4. Report `P_W`, `D_m`, `A_m2`, `V0_m_s`, `vi_m_s`, `Vp_m_s`, `Ve_m_s`, `mdot_kg_s`, `T_N`, `useful_power_W`, and `eta`. State that `T_N` is ideal thrust and `useful_power_W` is \(T V_0 = \eta P\).
5. If the user needs a level-turn input, say that `T_N` is `--thrust` and `useful_power_W` is `--power` for `AERO - IncompressibleLevelTurn`.
6. If power, diameter, speed, or a density source is missing, say so. Do not fill them in.
