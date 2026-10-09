---
name: ROCKET - ExpansionMatchEarth
description: >-
  Run the expansion-match program and report its printed results and PNG.
  Use when the user wants the optimal nozzle expansion ratio at an altitude
  or across an altitude range on Earth. Do not redraw the curve or recompute
  the numbers by hand.
---

# ROCKET - ExpansionMatchEarth

Use this skill for the expansion ratio that matches a nozzle to Earth ambient pressure. Run the program once; quote its stdout and include its PNG when `graph:` is printed. Do not redraw the curve or recompute the numbers by hand.

The optimum is \(p_2 = p_3\). At a fixed chamber-to-ambient pressure ratio, ideal \(C_F\) is maximum there. Ambient pressure is the 1976 U.S. Standard Atmosphere at geometric altitude, from sea level through 86 km. Exit Mach is the inverse of the Area-Mach exit pressure. The area ratio is `area_mach` at that Mach. This program does not call CEA.

A choked throat (\(M_e \ge 1\)) reports \(\epsilon = A_e/A_t\) and ideal \(C_F\). An unchoked exit (\(M_e < 1\)) reports the sonic area ratio \(A/A^{*}\) and omits \(C_F\). The expansion flag is an ideal pressure comparison. It does not model separation.

There is no finite optimum in vacuum. The altitude sweep stops at 86 km, where the 1976 hydrostatic model ends.

## When to run

Interactive lab offer: before running this program for a new engine, nozzle, or chamber design or sizing thread, ask once whether the user wants `ROCKET - NozzleChamberDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

1. Point: the user gives one geometric altitude. Pass `--alt`. Do not pass sweep limits. A point does not write a PNG.
2. Sweep: the user gives an altitude range, or asks for the ratio across altitude without a single design point. Pass `--alt-min` and `--alt-max` when the user gave both ends. If an end is missing, omit that flag. If the user also names a design altitude inside the range, pass `--alt` so the curve is marked.
3. Convert inputs to SI before the call (Pa, m). State the converted units in the reply. A bare altitude is geometric metres, not geopotential. Do not invent chamber pressure, gamma, or altitude.

Pass `gamma` and `pc_Pa` from an Area-Mach printout when that run printed them. Do not pass an existing area ratio into this program. This program solves the area ratio.

## Flags

Run:

```text
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --pc <Pa> [--gamma <k>] [--alt <m>] [--alt-min <m>] [--alt-max <m>] [--throat <m^2>]
```

Pass **only** flags the user supplied (after SI conversion). Do **not** supply a default chamber pressure or altitude.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pc` | Chamber pressure \(p_1\) | Pa | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). Pass the Area-Mach gamma for hot gas. |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Point, or the marked altitude on a sweep |
| `--alt-min`, `--alt-max` | Geometric sweep limits | m | Optional. Sweep only |
| `--throat` | Throat area \(A_t\) | m² | Optional. Prints exit area and thrust when the throat is choked |
| `--out` | PNG path for a sweep | — | Optional. Sweep only |

A bare `--pc` is pascals. Use `pc_Pa = pc_bar * 1e5`, `1 atm = 101325 Pa`, and `1 psi = 6894.757293168361 Pa`. Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. If the user gives geopotential altitude \(H\), convert with \(Z = r_0 H / (r_0 - H)\) and \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\) before the call, and say so.

If the user gives no sweep range, the program prints `assumed_range`. The low end is sea level. The high end is 86000 m. Repeat `assumed_range` in the reply when it is present.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG only when `graph:` is printed. The plot title is `Optimal expansion ratio versus altitude`.
3. Report `model`, `gamma`, and `gamma_source`. `default` means \(\gamma = 1.4\) air, not a hot-gas value.
4. Report geometric altitude `Z_m` and geopotential `H_m`. State that \(Z\) is geometric.
5. Report `pa_Pa`, `pe_Pa`, `Me`, `epsilon`, `branch`, `choked`, and `expansion`.
6. When `choked: yes`, \(\epsilon\) is \(A_e/A_t\). Report `CF`. Report `throat_m2`, `Ae_m2`, and `thrust_N` when they are printed.
7. When `choked: no`, say \(\epsilon\) is the sonic area ratio \(A/A^{*}\) and that ideal \(C_F\) was omitted.
8. On a sweep, report `epsilon_at_Z_min` and `epsilon_at_Z_max` as the values at the altitude ends. They are not a minimum and maximum of the curve. Report `y_scale`. Report `sonic_Z_m` when it is printed. That is where the matched exit is sonic and \(\epsilon = 1\).
9. Repeat `assumed_range` when it is present. If `warning` is printed, include it.
10. If chamber pressure or altitude is missing, say so. Do not fill it in.
