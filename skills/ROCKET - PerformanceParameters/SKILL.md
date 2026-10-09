---
name: ROCKET - PerformanceParameters
description: >-
  Run the performance-parameters program and report its printed results.
  Use when the user wants c-star, chamber temperature, gamma, ideal thrust
  coefficient, specific impulse, density impulse, bulk density, or a
  performance plot for a listed liquid propellant pair. Do not call CEA
  and do not redraw plots.
---

# ROCKET - PerformanceParameters

Use this skill for propellant performance from frozen CEA tables. Run the program and quote its stdout. CEA is not called on a user request. Do not redraw a plot by hand, and do not run `scripts/build_table.py` to fill a missing table.

Tables are frozen CEA output. The loader picks the nearest frozen pressure among the tables on disk, built at 10, 20, and 40 bar. An exact tie uses the higher table pressure (15 bar selects 20; 30 bar selects 40). Both gammas are stored. Throat gamma is the default for exit Mach, exit pressure, and ideal Cf. Pass `--gamma-source chamber` only when the user asks for chamber gamma. `cstar_perfect` is a check column. Delivered c* is `cstar_m_s`.

Bulk density uses only these constants:

| Oxidizer | Fuel | rho_ox | T_ox | rho_fuel | T_fuel |
| --- | --- | --- | --- | --- | --- |
| LOX | RP1 | 1141 kg/m³ | 90 K | 810 kg/m³ | 288 K |
| LOX | Ethanol | 1141 kg/m³ | 90 K | 789 kg/m³ | 293 K |
| LOX | CH4 | 1141 kg/m³ | 90 K | 422 kg/m³ | 111 K |
| LOX | LH2 | 1141 kg/m³ | 90 K | 71 kg/m³ | 20 K |
| N2O4 | MMH | 1443 kg/m³ | 293 K | 878 kg/m³ | 293 K |
| N2O4 | UDMH | 1443 kg/m³ | 293 K | 791 kg/m³ | 293 K |
| N2O4 | N2H4 | 1443 kg/m³ | 293 K | 1008 kg/m³ | 293 K |
| N2O4 | A50 | 1443 kg/m³ | 293 K | 899 kg/m³ | 298 K |
| LOX | Methanol | 1141 kg/m³ | 90 K | 792 kg/m³ | 293 K |
| LOX | Propane | 1141 kg/m³ | 90 K | 582 kg/m³ | 231 K |

`RP-1` is `RP1`. `LCH4`, `LNG`, and `methane` are `CH4`. `NTO` is `N2O4`. `hydrazine` is `N2H4`. `Aerozine-50` is `A50`. Case and hyphens do not matter. `N2H4`, `A50`, `Methanol`, and `Propane` supply liquid density only. They have no frozen performance table.

`1/rho_b = r/((r+1)*rho_ox) + 1/((r+1)*rho_f)`. Density impulse is `rho_b * Isp`.

Mixture ratio `r` (oxidizer/fuel) is required for a point. Do not invent a missing r. Do not invent a missing table. If the program names `scripts/build_table.py`, report that and stop. Do not fabricate Tc, c*, Mw, or gamma.

Chamber pressure and ambient pressure are pascals. Convert pc and pa to Pa before the call. A bare number is pascals. Use `pc_Pa = pc_bar * 1e5` and `1 atm = 101325 Pa`. Bar in the reply is only `pc_table_bar` and `pc_offset_bar`.

## When to run

Interactive lab offer: before running this program for a new engine, nozzle, or chamber design or sizing thread, ask once whether the user wants `ROCKET - NozzleChamberDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

1. Point: the user gives a pair, chamber pressure, area ratio, ambient pressure, and mixture ratio. Missing `r` is an error, not a sweep. A point request does not write a PNG.
2. `--pair` is one `oxName/fuelName` string per propellant combination (example `LOX/RP1`). On MCP, `pair` is an array of those strings: pass `["LOX/RP1"]` for one pair, not oxidizer and fuel as separate list items. `["LOX","RP1"]` is also accepted and joined to `LOX/RP1`. Repeat the array element (or CLI `--pair`) only to overlay several pairs on a plot.
3. Plot: the user asks for one quantity against another. The name before `vs` is the vertical axis. The name after `vs` is the horizontal axis. Exactly one axis must be mixture ratio, pc, eps, or pa.

## Flags

```text
python "skills/ROCKET - PerformanceParameters/src/performance.py" --pair LOX/RP1 --pc <Pa> --eps <Ae/At> --pa <Pa> --r <ox/fuel> [--gamma-source throat|chamber] [--plot "Y vs X"]
```

| Flag | Meaning |
| --- | --- |
| `--pair` | Repeatable. One value per pair: `oxName/fuelName` (e.g. `LOX/RP1`). MCP array shape is `["LOX/RP1"]`, or `["LOX","RP1"]` joined to the same. Spaces around `/` are allowed. Known names fold to the card (`RP-1` is `RP1`). Several pairs are overlaid on one plot. |
| `--pc` | Chamber pressure, Pa. Required on a point call. |
| `--eps` | \(A_e/A_t\), at least 1. Required on a point call. |
| `--pa` | Ambient pressure, Pa. Required on a point call. Omitted `pa` is an error. |
| `--r` | Mixture ratio, oxidizer/fuel. Required on a point call. |
| `--gamma-source` | `throat` (default) or `chamber`. |
| `--plot` | Repeatable. A PNG is written only when this flag is present. |
| `--r-min`, `--r-max` | Mixture-ratio sweep limits. Override the table range. |
| `--pc-min`, `--pc-max` | Chamber-pressure sweep limits, Pa. |
| `--eps-min`, `--eps-max` | Area-ratio sweep limits. |
| `--pa-min`, `--pa-max` | Ambient-pressure sweep limits, Pa. |
| `--mark-peak` | Mark the peak of the computed curve. Pass this only when the user asked for the peak. |
| `--out` | Optional directory for PNG files. |

Accepted names: mixture ratio, pc, eps, pa, c*, Tc, gamma_throat, gamma_chamber, Cf, Isp sea level, Isp vacuum, density Isp, density Isp vacuum, bulk density.

If the user gives no sweep range, the program prints `assumed_range`. Mixture ratio uses that table's `of_min` to `of_max`. pc uses 10–40 bar, plotted in Pa (`1e6`–`4e6`). eps uses 5–40. pa uses 0–1 atm (`0`–`101325` Pa). Repeat `assumed_range` in the reply when it is present.

c*, Tc, gamma, and bulk density do not need eps or pa. Cf and sea-level Isp need eps and pa. Vacuum Isp needs eps and does not use pa. Fixed inputs the plotted quantity depends on are still required.

On a pc sweep the program re-picks the nearest frozen table at each sample. c*, Tc, and gamma stay constant between table pressures and step at the midpoints. An eps or pa sweep holds the one table chosen from `--pc`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include a PNG only when `graph:` is printed. A point request has no PNG.
3. Name the gamma used for Cf (`gamma_source` and `gamma` when both are printed).
4. Report `pc_table_bar` and `pc_offset_bar`. If `warning` is printed, include it. On a pc sweep, say the table is re-picked when `pc_table` says so.
5. Report `Isp_s` together with `pa_Pa`. That pair is specific impulse at the ambient the user gave. `Isp_vac_s` is vacuum and is always labeled vacuum.
6. Report expansion as `perfectly expanded`, `underexpanded`, or `overexpanded` when it is printed.
7. Repeat `assumed_range` when it is present.
8. If `mark_r` or `peak` is printed, include it. Do not mark a peak unless the user asked for one.
9. If r or a table is missing, say so. Do not fill in a mixture ratio or a performance number.
10. `Tc_K`, `Mw_kg_kmol`, `gamma`, and `cstar_m_s` can be quoted into `ROCKET - ThroatGasSideHeatFlux`. Do not call CEA to fill a missing heat-flux input.
