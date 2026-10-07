---
name: ROCKET - ElectricPropulsionDeltaV
description: >-
  Run the electric-propulsion delta-v program and report its printed results
  and optional PNG. Use when the user wants propellant and wet mass from the
  vacuum rocket equation, the burn time at a stated thrust and duty cycle, and
  the input electrical power and specific power. Do not redraw the plot or
  recompute the numbers by hand.
---

# ROCKET - ElectricPropulsionDeltaV

Use this skill for a low-thrust electric stage with constant exhaust speed and constant thrust. It is not a chemical in-space burn: `ASTRO - VacuumPropellantMass` does not print burn time or electrical power. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Propellant mass is `vacuum_propellant_mass` and wet mass is `vacuum_wet_mass`. Thrusting time is `electric_propulsion_burn_time`, \(t_b = m_p v_e / T\). Calendar time divides that by the duty cycle. Input electrical power is `electric_propulsion_power`, \(P = T v_e /(2\eta)\). Specific power is `electric_propulsion_specific_power`, \(P/m_0\).

No Hall plume, no throttle table, and no power-processing loss beyond the single efficiency.

## When to run

1. Use this skill when the user wants electric-propulsion propellant, burn time, input power, or specific power for a vacuum delta-v.
2. Convert mass to kilograms, thrust to newtons, delta-v and exhaust speed to m/s, and specific impulse to seconds. State the converted units in the reply. Do not invent dry mass, thrust, delta-v, or a specific impulse.
3. Pass `--dry`, `--thrust`, `--dv`, and exactly one of `--isp` or `--ve`.
4. Pass `--eta` and `--duty` only when the user gave them. Defaults are 1.
5. Pass `--out` only when the user wants the PNG of propellant mass versus delta-v. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for a chemical stage, a gravity loss, or a plume model.

## Flags

Run:

```text
python "skills/ROCKET - ElectricPropulsionDeltaV/electric_propulsion_delta_v.py" --dry <kg> --thrust <N> --dv <m/s> (--isp <s> | --ve <m/s>) [--eta <eta>] [--duty <duty>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--dry` | Dry mass \(m_f\), after the burn | kg, \(> 0\) | Required |
| `--thrust` | Constant thrust \(T\) | N, \(> 0\) | Required |
| `--dv` | Vacuum delta-v | m/s, \(> 0\) | Required |
| `--isp` | Specific impulse | s, \(> 0\) | One of `--isp` or `--ve` |
| `--ve` | Exhaust speed | m/s, \(> 0\) | One of `--isp` or `--ve` |
| `--eta` | Thrust efficiency, jet power over input power | dimensionless, \(0 < \eta \le 1\) | Optional. Default 1 |
| `--duty` | Thrusting fraction of calendar time | dimensionless, \(0 < \mathrm{duty} \le 1\) | Optional. Default 1 |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Specific impulse uses \(v_e = I_{sp} g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^{2}\).

When `--out` is passed, the program writes one PNG. The plot title is `Electric propulsion delta-v`. The curve is propellant mass versus delta-v at the fixed dry mass and exhaust speed. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `mf_kg`, `ve_m_s`, `mp_kg`, `m0_kg`, `tb_thrust_s`, `tb_s`, `P_W`, and `specific_power_W_kg`.
4. Report `Isp_s` when specific impulse was the input. Report `eta` and `duty`.
5. If dry mass, thrust, delta-v, or an exhaust-speed path is missing, say so. Do not fill them in.
