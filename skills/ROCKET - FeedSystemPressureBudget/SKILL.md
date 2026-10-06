---
name: ROCKET - FeedSystemPressureBudget
description: >-
  Run the feed-pressure program and report its printed results. Use when
  the user wants supply pressure or a pressure-fed MEOP from chamber
  pressure, injector drop, named line drops, and optional hydrostatic head.
  Do not recompute the numbers by hand.
---

# ROCKET - FeedSystemPressureBudget

Use this skill for the steady feed pressure of one propellant branch, or of the oxidizer and fuel branches together. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Manifold pressure is \(p_m = p_c + \Delta p_j\). Supply pressure adds named drops and \(\rho g h\). A positive height is a lift from the tank free surface to the injector. \(g_0 = 9.80665\,\mathrm{m/s}^{2}\) unless `--g` is set. `meop_Pa` is the supply pressure for a pressure-fed tank. A pump-fed tank is not at this pressure.

## When to run

1. Use this skill when the user asks for feed pressure, injector-manifold pressure, or a pressure-fed tank MEOP.
2. Convert all inputs to SI before the call (Pa, kg/m³, m). State the converted units in the reply. Do not invent drops the user did not give.
3. Pass `--dp-injector`, or both `--dp-injector-ox` and `--dp-injector-fuel`. Those drops can come from `ROCKET - InjectorOrificeFlow` `dp_Pa`.
4. Repeat `--dp name=Pa` for each line, jacket, or valve drop the user names.
5. Pass `--rho` and `--height` together for one branch. For two branches pass `--rho-ox`, `--rho-fuel`, and `--height`.
6. For a pressure-fed tank, pass `meop_Pa` to `ROCKET - TankStructureMass` `--meop`. For a pump, the pump rise is discharge pressure minus inlet pressure, not this MEOP; use `ROCKET - PumpHydraulicPower`.

## Flags

Run:

```text
python "skills/ROCKET - FeedSystemPressureBudget/feed_system_pressure_budget.py" --pc <Pa> (--dp-injector <Pa> | --dp-injector-ox <Pa> --dp-injector-fuel <Pa>) [--dp <name=Pa> ...] [--rho <kg/m^3> | --rho-ox <kg/m^3> --rho-fuel <kg/m^3>] [--height <m>] [--g <m/s^2>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pc` | Injector-end chamber pressure | Pa | Required |
| `--dp-injector` | Injector drop, one branch | Pa | One branch, or the ox/fuel pair |
| `--dp-injector-ox` | Oxidizer injector drop | Pa | With `--dp-injector-fuel` |
| `--dp-injector-fuel` | Fuel injector drop | Pa | With `--dp-injector-ox` |
| `--dp` | Named extra drop, `name=Pa` | Pa | Optional, repeatable |
| `--rho` | Density, one branch | kg/m³ | With `--height` |
| `--rho-ox` | Oxidizer density | kg/m³ | With `--height` on a pair |
| `--rho-fuel` | Fuel density | kg/m³ | With `--height` on a pair |
| `--height` | Lift to the injector | m | Optional |
| `--g` | Gravity | m/s² | Optional |

There is no PNG. The printed breakdown is the result.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report manifold pressure, each named drop, hydrostatic head, supply pressure, and `meop_Pa`.
3. State that `meop_Pa` is the pressure-fed tank suggestion for `ROCKET - TankStructureMass`. State that a pump-fed tank is not at this pressure.
