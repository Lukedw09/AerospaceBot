---
name: POWER - DutyCycleLoad
description: >-
  Run the duty-cycled electrical-load program and report its printed results
  and optional PNG. Use when the user wants orbit-average power, coincident
  peak power, or eclipse energy from a list of load powers and on-fractions.
  Hand the orbit-average or eclipse power and the eclipse duration to
  POWER - BatteryEnergyBudget, and the orbit-average power to the end-of-life
  requirement of POWER - SolarArrayOutput. Do not recompute the numbers by hand.
---

# POWER - DutyCycleLoad

Use this skill for the electrical load of a general spacecraft from a list of constant powers and on-fractions. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Orbit-average power of one load is `orbit_average_load`, \(P f\). The printed `P_avg_W` is the sum. Coincident peak power is the sum of the nameplate powers, an upper bound if every load can be on together. Eclipse energy is `eclipse_load_energy`, \(E = P t\). When `--eclipse-duty` is omitted, that power is the orbit average. When it is given, that power is the sum of power times eclipse on-fraction.

`P_avg_W` is the continuous-equivalent load the end-of-life orbit-average power from `POWER - SolarArrayOutput` must meet. For `POWER - BatteryEnergyBudget`, pass `P_eclipse_W` as `--load` and `t_eclipse_s` as `--eclipse` when those keys are printed. If `energy_source` is `orbit_average`, `P_eclipse_W` equals `P_avg_W`.

No cell model, no regulation loss, and no bus voltage.

## When to run

1. Use this skill when the user has a list of electrical loads and wants orbit-average power, peak power, or eclipse energy.
2. Convert power to watts and durations to seconds before the call. State the converted units in the reply. Do not invent a load, a duty, or an eclipse duration.
3. Pass one `--power` and one `--duty` for each load, in the same order. Duties are orbit on-fractions from 0 to 1.
4. Pass `--eclipse` when the user gives an eclipse duration. Pass `--eclipse-duty` only when the user gave a separate on-fraction during eclipse, one value per load.
5. Pass `--out` only when the user wants the PNG.
6. Send the printed eclipse power and duration to `POWER - BatteryEnergyBudget`. Send `P_avg_W` to the orbit-average power that `POWER - SolarArrayOutput` must meet at end of life.

## Flags

Run:

```text
python "skills/POWER - DutyCycleLoad/duty_cycle_load.py" --power <W> --duty <fraction> [--power <W> --duty <fraction> ...] [--eclipse <s>] [--eclipse-duty <fraction> ...] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--power` | One load, repeatable | W, \(> 0\) | Required, once per load |
| `--duty` | Orbit on-fraction, same order as `--power` | 0 to 1 | Required, once per load |
| `--eclipse` | Eclipse duration | s, \(> 0\) | Optional |
| `--eclipse-duty` | Eclipse on-fraction, same order as `--power` | 0 to 1 | Optional, with `--eclipse` |
| `--out` | PNG path | — | Optional |

Power in milliwatts uses `1 mW = 0.001 W`. A duty given as a percent is that number divided by 100. Do not invent missing loads.

When `--out` is passed, the program writes one PNG. The plot title is `Duty-cycle load`. Bars are nameplate power and the orbit-average contribution of each load.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `P_avg_W`, `P_peak_W`, and `energy_source`.
4. When eclipse keys are printed, report `P_eclipse_W`, `t_eclipse_s`, `E_eclipse_J`, and `E_eclipse_Wh`.
5. If a load power or duty is missing, say so. Do not fill it in.
