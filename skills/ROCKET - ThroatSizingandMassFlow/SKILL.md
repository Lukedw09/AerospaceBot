---
name: ROCKET - ThroatSizingandMassFlow
description: >-
  Run the throat-sizing program and report its printed results. Use when
  the user wants throat area, throat diameter, or propellant mass flow from
  thrust, thrust coefficient, chamber pressure, and characteristic velocity.
  Do not recompute the numbers by hand.
---

# ROCKET - ThroatSizingandMassFlow

Use this skill for throat area, throat diameter, and propellant mass flow. Run the program once and quote its stdout. Do not recompute the numbers by hand.

The throat is circular. \(A_t = F / (C_F p_1)\) and \(A_t = \pi D_t^{2} / 4\). Mass flow is \(\dot{m} = p_1 A_t / c^{*}\), which is the same as \(F / (c^{*} C_F)\). \(C_F\) and \(c^{*}\) are inputs. This program does not compute either one.

## When to run

1. Use this skill when the user asks for throat diameter, throat area, or propellant mass flow from thrust and chamber pressure.
2. Convert all inputs to SI before the call (N, Pa, m/s). State the converted units in the reply. Do not invent values the user did not give.
3. Characteristic velocity \(c^{*}\) is required. If the user did not give \(c^{*}\), say so and stop. Do not take \(c^{*}\) from another skill and do not invent one.

## Flags

Run:

```text
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --thrust <N> --cf <CF> --pc <Pa> --cstar <m/s>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--thrust` | Thrust \(F\) | N | Required |
| `--cf` | Thrust coefficient \(C_F\) | dimensionless | Required |
| `--pc` | Chamber pressure \(p_1\) | Pa | Required |
| `--cstar` | Characteristic velocity \(c^{*}\) | m/s | Required |

A bare number for `--pc` is pascals. Use `pc_Pa = pc_bar * 1e5`, `1 atm = 101325 Pa`, and `1 psi = 6894.757293168361 Pa`. Thrust in pounds-force uses `1 lbf = 4.4482216152605 N`. A \(c^{*}\) in feet per second uses `1 ft/s = 0.3048 m/s`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report thrust \(F\) in N, \(C_F\), chamber pressure \(p_1\) in Pa, and \(c^{*}\) in m/s.
3. Report throat area \(A_t\) in m² and throat diameter \(D_t\) in m. State that the throat is circular.
4. Report mass flow \(\dot{m}\) in kg/s.
5. State that \(C_F\) and \(c^{*}\) were inputs. Do not describe them as values this program calculated.
6. `mdot_kg_s` can be passed to `ROCKET - InjectorOrificeFlow`. `Dt_m` can be passed to `ROCKET - ThroatGasSideHeatFlux` as `--throat`. Do not invent discharge coefficient, density, contour curvature, or wall temperature.
