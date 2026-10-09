---
name: ROCKET - ChamberVolumeAndCaseHoopStress
description: >-
  Run the chamber-volume and case-hoop program and report its printed
  results. Use when the user wants combustion-chamber volume from throat
  area and characteristic length, or thin-wall hoop stress and margin of
  safety from chamber pressure, case radius, wall thickness, and allowable
  stress. Do not recompute the numbers by hand.
---

# ROCKET - ChamberVolumeAndCaseHoopStress

Use this skill for chamber volume, case hoop stress, and margin of safety. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Chamber volume is \(V_c = L^{*} A_t\), from \(L^{*} = V_c / A_t\). \(V_c\) is the chamber volume through the throat plane. Hoop stress is the thin-cylinder membrane stress \(\sigma_h = p R / t\). Margin of safety is \(\mathrm{MS} = S_{\mathrm{allow}} / \sigma_h - 1\), with hoop stress as the design stress. \(L^{*}\) and the allowable stress are inputs. This program does not choose either one.

The pressure passed as `--pc` is the \(p\) in \(\sigma_h = p R / t\). NASA SP-8025 calls that pressure the design pressure. This program does not multiply by a design factor.

## When to run

Interactive lab offer: before running this program for a new engine, nozzle, or chamber design or sizing thread, ask once whether the user wants `ROCKET - NozzleChamberDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

A solid circular-port grain thread can use `ROCKET - SolidMotorGrainLab` instead. Offer that lab once, with the same 4-hour rule, and do not run it unless they explicitly say yes. Keep the nozzle–chamber lab offer for liquid engine threads.

1. Use this skill when the user asks for chamber volume from throat area and \(L^{*}\), or for case hoop stress and margin of safety.
2. Convert all inputs to SI before the call (m², m, Pa). State the converted units in the reply. Do not invent values the user did not give.
3. Throat area, \(L^{*}\), chamber pressure, case radius, wall thickness, and allowable stress are all required. If any one is missing, say so and stop. Do not take throat area from another skill unless the user asked to use that result, and do not invent an \(L^{*}\) or an allowable stress.

## Flags

Run:

```text
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --throat <m^2> --lstar <m> --pc <Pa> --radius <m> --thickness <m> --allowable <Pa>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--throat` | Throat area \(A_t\) | m² | Required |
| `--lstar` | Characteristic length \(L^{*}\) | m | Required |
| `--pc` | Pressure \(p\) used in the hoop formula | Pa | Required |
| `--radius` | Case radius \(R\) | m | Required |
| `--thickness` | Wall thickness \(t\) | m | Required |
| `--allowable` | Allowable stress \(S_{\mathrm{allow}}\) | Pa | Required |

A bare number for `--pc` or `--allowable` is pascals. Use `p_Pa = p_bar * 1e5`, `1 atm = 101325 Pa`, `1 psi = 6894.757293168361 Pa`, and `1 MPa = 1e6 Pa`. Throat area in square inches uses `1 in² = 0.00064516 m²`. Lengths in inches use `1 in = 0.0254 m`.

If the user gives a maximum expected operating pressure and a separate design factor, pass their product as `--pc`. If the user gives one chamber pressure and no factor, pass that pressure as `--pc`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report throat area \(A_t\) in m², \(L^{*}\) in m, chamber pressure in Pa, case radius \(R\) in m, wall thickness \(t\) in m, and allowable stress in Pa.
3. Report chamber volume \(V_c\) in m³.
4. Report hoop stress in Pa and margin of safety as a fraction. A margin of 0 means the hoop stress equals the allowable. A negative margin means the hoop stress is above the allowable.
5. Report `t_over_R` and `thin_wall`. `thin_wall` is `yes` when \(t/R < 0.1\). State that the hoop formula is a thin-membrane result.
6. State that \(L^{*}\) and the allowable stress were inputs, and that `--pc` was not multiplied by a design factor inside the program.
7. After the throat and chamber geometry are known, gas-side heat flux is `ROCKET - ThroatGasSideHeatFlux`. This program does not compute heat flux.
