---
name: ROCKET - PressurantBlowdown
description: >-
  Run the pressurant blowdown program and report its printed results and
  optional PNG. Use when the user wants the end ullage pressure after a stated
  liquid volume leaves a pressure-fed tank, and optional pressurant mass of
  that fixed charge. Do not redraw the plot or recompute the numbers by hand.
---

# ROCKET - PressurantBlowdown

Use this skill for the polytropic drop of ullage pressure as liquid leaves a pressure-fed tank. It is not a regulator, a pressurant-bottle recharge, a wall thickness, or a tank mass. Tank mass stays on `ROCKET - TankStructureMass`. Propellant volume may already have come from `ROCKET - PropellantLoad`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

End ullage is \(V_2 = V_0 + V_{\mathrm{expelled}}\). End pressure is `pressurant_blowdown_pressure`, \(p_2 = p_0 (V_0/V_2)^n\). The default exponent is isothermal, \(n = 1\). A supplied \(n\) is used as the user states it; the program does not pick \(\gamma\). Pressurant mass is `pressurant_mass`, \(m = pV/(R_{\mathrm{specific}} T)\), printed at both ends only when temperature and the specific gas constant are both given. The end temperature is the fixed-mass polytropic ratio \(T_2 = T (p_2/p_0)^{(n-1)/n}\), so the two masses agree. For the default isothermal exponent they are the same temperature.

## When to run

1. Use this skill when the user wants blowdown pressure, blowdown ratio, or the fixed pressurant mass for a growing ullage.
2. Convert pressure to pascals, volume to cubic metres, temperature to kelvin, and the specific gas constant to J/(kg·K). State the converted units in the reply. Do not invent pad pressure, ullage, or expelled volume.
3. Pass `--p0`, `--v0`, and `--v-expelled`.
4. Pass `--n` only when the user gave a polytropic exponent. The default is 1.
5. Pass `--p-min` only when the user gave a pressure floor.
6. Pass `--temperature` and `--r-specific` together only when the user wants pressurant mass. Do not invent either one.
7. Pass `--out` only when the user wants the PNG of pressure versus expelled volume. Do not invent a plot path when they did not ask for a figure.
8. Do not use this skill for a regulator, a bottle recharge, wall thickness, or tank mass.
9. Interactive lab offer: before running this program for a new feed, injector, pump, blowdown, tank, or propellant-load design or sizing thread, ask once whether the user wants `ROCKET - FeedTankDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/ROCKET - PressurantBlowdown/pressurant_blowdown.py" --p0 <Pa> --v0 <m3> --v-expelled <m3> [--n <n>] [--p-min <Pa>] [--temperature <K> --r-specific <J/kg/K>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--p0` | Initial ullage pressure | Pa, \(> 0\) | Required |
| `--v0` | Initial ullage volume | m³, \(> 0\) | Required |
| `--v-expelled` | Liquid volume that leaves | m³, \(\ge 0\) | Required |
| `--n` | Polytropic exponent | dimensionless, \(> 0\) | Optional. Default 1 |
| `--p-min` | Pressure floor | Pa, \(\ge 0\) | Optional |
| `--temperature` | Gas temperature for mass | K, \(> 0\) | Optional. Required with `--r-specific` |
| `--r-specific` | Specific gas constant | J/(kg·K), \(> 0\) | Optional. Required with `--temperature` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Pressurant blowdown`. The curve is ullage pressure versus expelled volume from zero to the stated expulsion. The square is the end state. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `V2_m3`, `p2_Pa`, and `blowdown_ratio`.
4. Report `above_floor` when a pressure floor was given.
5. Report `m0_kg` and `m2_kg` when temperature and the specific gas constant were both given.
6. If pad pressure, initial ullage, or expelled volume is missing, say so. Do not fill them in.
