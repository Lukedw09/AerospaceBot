---
name: ROCKET - PropellantLoad
description: >-
  Run the propellant-load program and report its printed results. Use when
  the user wants usable propellant mass or tank volume (total, oxidizer, and
  fuel) from mass flow, burn time, mixture ratio, and liquid densities.
  Do not recompute the numbers by hand.
---

# ROCKET - PropellantLoad

Use this skill for propellant mass and volume. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Steady flow: \(r = \dot{m}_o/\dot{m}_f\), \(\dot{m}_o = r\dot{m}/(r+1)\), \(\dot{m}_f = \dot{m}/(r+1)\), and \(m = \dot{m}\,t_b\). Volumes are \(V = m/\rho\). Average density is \(\rho_{av} = \rho_o\rho_f(r+1)/(r\rho_f+\rho_o)\). Densities the user does not give come from `ROCKET - PerformanceParameters` `scripts/pairs.json`. This program does not call CEA.

Bulk density uses only these constants when `--pair` supplies density:

| Oxidizer | Fuel | rho_ox | T_ox | rho_fuel | T_fuel |
| --- | --- | --- | --- | --- | --- |
| LOX | RP1 | 1141 kg/m³ | 90 K | 810 kg/m³ | 288 K |
| LOX | Ethanol | 1141 kg/m³ | 90 K | 789 kg/m³ | 293 K |
| LOX | CH4 | 1141 kg/m³ | 90 K | 422 kg/m³ | 111 K |
| LOX | LH2 | 1141 kg/m³ | 90 K | 71 kg/m³ | 20 K |
| N2O4 | MMH | 1443 kg/m³ | 293 K | 878 kg/m³ | 293 K |
| N2O4 | UDMH | 1443 kg/m³ | 293 K | 791 kg/m³ | 293 K |

## When to run

1. Use this skill when the user asks for propellant mass or tank volume from mass flow and burn time.
2. Convert all inputs to SI before the call (kg/s, s, kg/m³). State the converted units in the reply. Do not invent values the user did not give.
3. Mixture ratio \(r\) (oxidizer/fuel) is required. Do not invent a missing \(r\).
4. If the user gives both oxidizer and fuel density, pass those flags. If density is omitted, pass `--pair` from a listed pair. `LOX/RP-1` is `LOX/RP1`. `LCH4`, `LNG`, and `methane` are `CH4`. `NTO` is `N2O4`. `hydrazine` is `N2H4`. `Aerozine-50` is `A50`. Also listed: `LOX/Methanol` and `LOX/Propane`. Do not invent a density.

## Flags

Run:

```text
python "skills/ROCKET - PropellantLoad/propellant_load.py" --mdot <kg/s> --tb <s> --r <ox/fuel> [--pair LOX/RP1 | --rho-ox <kg/m^3> --rho-fuel <kg/m^3>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mdot` | Total propellant mass flow \(\dot{m}\) | kg/s | Required |
| `--tb` | Burn time \(t_b\) | s | Required |
| `--r` | Mixture ratio, oxidizer/fuel | dimensionless | Required |
| `--pair` | `oxName/fuelName`. Spaces around `/` are allowed. Known names fold to the card (`RP-1` is `RP1`, `Ethanol` stays `Ethanol`). | — | Optional; required when densities are omitted |
| `--rho-ox` | Oxidizer density \(\rho_o\) | kg/m³ | Optional; required with `--rho-fuel` when `--pair` is not used for density |
| `--rho-fuel` | Fuel density \(\rho_f\) | kg/m³ | Optional; required with `--rho-ox` when `--pair` is not used for density |

User densities override the pair table. `--rho-ox` and `--rho-fuel` must be given together. A listed `--pair` still prints `pair` when the user also gave densities.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report \(\dot{m}\) in kg/s, \(t_b\) in s, and \(r\).
3. Name the density source (`user` or `pairs.json`). If `pair` is printed, include it. Report \(\rho_o\), \(\rho_f\), and \(\rho_{av}\) in kg/m³. Repeat `rho_ox_T_K` and `rho_fuel_T_K` when they are printed.
4. Report propellant mass \(m_p\), \(m_o\), and \(m_f\) in kg.
5. Report propellant volume \(V_p\), \(V_o\), and \(V_f\) in m³.
6. If r, mass flow, burn time, densities, or a listed pair is missing, say so. Do not fill in a density or a mass.
