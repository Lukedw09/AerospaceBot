---
name: ROCKET - PumpHydraulicPower
description: >-
  Run the pump-power program and report its printed results. Use when the
  user wants volume flow, hydraulic power, or shaft power from mass flow,
  density, pump pressure rise, and pump efficiency. Do not recompute the
  numbers by hand.
---

# ROCKET - PumpHydraulicPower

Use this skill for propellant-pump volume flow, hydraulic power, and shaft power. Run the program once and quote its stdout. Do not recompute the numbers by hand.

\(\dot{V} = \dot{m}/\rho\), \(P_\mathrm{hyd} = \dot{V}\,\Delta p\), and \(P_\mathrm{shaft} = P_\mathrm{hyd}/\eta\). An optional drive efficiency gives \(P_\mathrm{drive} = P_\mathrm{shaft}/\eta_d\). Skip this skill for a pressure-fed engine.

## When to run

1. Use this skill when the user asks for pump power, shaft power, or volume flow of a propellant pump.
2. Convert all inputs to SI before the call (kg/s, kg/m³, Pa). State the converted units in the reply. Do not invent efficiency.
3. \(\Delta p\) is the pump pressure rise: discharge pressure minus inlet pressure. Discharge can come from `ROCKET - FeedSystemPressureBudget` `p_supply_Pa`. Inlet is the user-supplied pump-inlet pressure, not the tank MEOP of a pressure-fed reading.
4. Do not run this skill for a pure pressure-fed design.

## Flags

Run:

```text
python "skills/ROCKET - PumpHydraulicPower/pump_hydraulic_power.py" --mdot <kg/s> --rho <kg/m^3> --dp <Pa> --eta <eta> [--eta-drive <eta>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mdot` | Mass flow | kg/s | Required |
| `--rho` | Density | kg/m³ | Required |
| `--dp` | Pump pressure rise | Pa | Required |
| `--eta` | Overall pump efficiency | dimensionless | Required |
| `--eta-drive` | Prime-mover efficiency | dimensionless | Optional |
| `--out` | PNG of shaft power versus pressure rise | — | Optional |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report \(\dot{V}\) in m³/s, hydraulic power in W, and shaft power in W.
3. When `--eta-drive` was passed, report drive power in W.
4. State that efficiency was an input. This program does not balance a gas generator or turbine.
