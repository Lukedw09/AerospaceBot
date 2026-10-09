---
name: ROCKET - SolidMotorParameters
description: >-
  Run the solid-motor parameters program and report its printed results. Use
  when the user wants burning-area ratio, equilibrium chamber pressure, burn
  rate, or solid-propellant mass flow from burn-rate coefficient and exponent,
  burning area, throat area, propellant density, and characteristic velocity.
  Do not recompute the numbers by hand.
---

# ROCKET - SolidMotorParameters

Use this skill for solid-motor burning-area ratio, equilibrium chamber pressure, burn rate, and mass flow. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Burning-area ratio is \(K = A_b/A_t\). Equilibrium chamber pressure is \(p_1 = (K\, a\, \rho_b\, c^{*})^{1/(1-n)}\) from the quasi-steady mass balance with Saint Robert's law \(r = a p_1^{n}\). Mass flow is \(\dot{m} = A_b r \rho_b\), which equals \(p_1 A_t / c^{*}\). \(a\), \(n\), \(\rho_b\), and \(c^{*}\) are inputs. This program does not compute \(c^{*}\) or choose propellant constants.

## When to run

Interactive lab offer: before running this program for a new solid-grain design or sizing thread, ask once whether the user wants `ROCKET - SolidMotorGrainLab` (interactive HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

1. Use this skill when the user asks for solid-motor \(K\), equilibrium chamber pressure, burn rate, or propellant mass flow from grain and throat geometry with Saint Robert burn-rate inputs.
2. Convert all inputs to SI before the call (m², kg/m³, m/s, and \(a\) in m/(s·Pa\(^{n}\))). State the converted units in the reply. Do not invent values the user did not give.
3. Burn-rate coefficient \(a\), exponent \(n\), burning area \(A_b\), throat area \(A_t\), propellant density \(\rho_b\), and characteristic velocity \(c^{*}\) are all required. If any one is missing, say so and stop. Do not invent \(a\), \(n\), \(\rho_b\), or \(c^{*}\).

## Flags

Run:

```text
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --a <m/(s·Pa^n)> --n <n> --ab <m^2> --throat <m^2> --rho <kg/m^3> --cstar <m/s>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Burn-rate coefficient \(a\) | m/(s·Pa\(^{n}\)) | Required |
| `--n` | Burn-rate pressure exponent \(n\) | dimensionless | Required; must be \(< 1\) |
| `--ab` | Burning surface area \(A_b\) | m² | Required |
| `--throat` | Throat area \(A_t\) | m² | Required |
| `--rho` | Solid propellant density \(\rho_b\) | kg/m³ | Required |
| `--cstar` | Characteristic velocity \(c^{*}\) | m/s | Required |

A bare number for areas is m². Use `1 in² = 0.00064516 m²`. Density in g/cm³ uses `1 g/cm³ = 1000 kg/m³`. A \(c^{*}\) in feet per second uses `1 ft/s = 0.3048 m/s`. Chamber pressure is an output in Pa; report bar only as a conversion of that printed value with `1 bar = 1e5 Pa`.

The coefficient \(a\) must match pressure in pascals. If the user gives \(a\) for \(p\) in MPa or psi, convert \(a\) so that \(r = a p_1^{n}\) is consistent with \(p_1\) in Pa before the call.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report \(a\), \(n\), \(A_b\) in m², \(A_t\) in m², \(\rho_b\) in kg/m³, and \(c^{*}\) in m/s.
3. Report burning-area ratio \(K\), equilibrium chamber pressure \(p_1\) in Pa, burn rate \(r\) in m/s, and mass flow \(\dot{m}\) in kg/s.
4. State that \(a\), \(n\), \(\rho_b\), and \(c^{*}\) were inputs. Do not describe \(c^{*}\) as a value this program calculated.
5. If any required input is missing, or if \(n \ge 1\), say so and stop.
