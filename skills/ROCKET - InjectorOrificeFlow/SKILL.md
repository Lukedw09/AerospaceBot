---
name: ROCKET - InjectorOrificeFlow
description: >-
  Run the injector-orifice program and report its printed results. Use when
  the user wants orifice area, jet speed, injection pressure drop, or orifice
  diameter from mass flow, density, and discharge coefficient. Do not
  recompute the numbers by hand.
---

# ROCKET - InjectorOrificeFlow

Use this skill for injector orifice area, geometric-area jet speed, injection pressure drop, and optional circular orifice diameter. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Mass flow is \(\dot{m} = C_d A \sqrt{2\rho\Delta p}\). Jet speed is \(v = \dot{m}/(\rho A)\). Dynamic pressure is \(\frac12\rho v^{2}\). With a count, \(d = \sqrt{4A/(N\pi)}\). \(C_d\) is an input.

## When to run

1. Use this skill when the user asks for injector orifice area, injection speed, injection pressure drop, or orifice diameter.
2. Convert all inputs to SI before the call (kg/s, kg/m³, Pa, m/s). State the converted units in the reply. Do not invent values the user did not give.
3. Pass exactly one of `--dp` or `--velocity`.
4. Mass flow can come from `ROCKET - ThroatSizingandMassFlow` `mdot_kg_s`, from `ROCKET - LossStack` `mdot_kg_s`, or from one branch of `ROCKET - PropellantLoad` (`mdot_o_kg_s` or `mdot_f_kg_s`). Do not invent a split.
5. Pass the printed `dp_Pa` to `ROCKET - FeedSystemPressureBudget` as `--dp-injector` or the matching ox/fuel flag.

## Flags

Run:

```text
python "skills/ROCKET - InjectorOrificeFlow/injector_orifice_flow.py" --mdot <kg/s> --rho <kg/m^3> --cd <Cd> (--dp <Pa> | --velocity <m/s>) [--count <N>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mdot` | Mass flow | kg/s | Required |
| `--rho` | Density | kg/m³ | Required |
| `--cd` | Discharge coefficient | dimensionless | Required |
| `--dp` | Injection pressure drop | Pa | Exactly one of `--dp` or `--velocity` |
| `--velocity` | Mean speed through the geometric area | m/s | Exactly one of `--dp` or `--velocity` |
| `--count` | Number of orifices | dimensionless | Optional |
| `--out` | PNG of diameter versus count | — | Optional |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report area \(A\) in m², speed \(v\) in m/s, drop \(\Delta p\) in Pa, and jet dynamic pressure \(q\) in Pa.
3. When a count was passed, report \(N\) and diameter \(d\) in m.
4. State that \(C_d\) was an input. Quote `warning` when it is printed.
5. Point `dp_Pa` at `ROCKET - FeedSystemPressureBudget`.
