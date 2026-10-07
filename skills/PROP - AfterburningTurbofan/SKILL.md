---
name: PROP - AfterburningTurbofan
description: >-
  Run the afterburning separate-stream turbofan and report its printed
  results and PNG. Use when the user wants dry and reheated specific thrust
  per inlet airflow, core and afterburner fuel-air ratios, and TSFC for a
  fan with reheat on the core only. Do not redraw the plot or recompute the
  numbers by hand.
---

# PROP - AfterburningTurbofan

Use this skill for a separate-stream turbofan with an afterburner on the core stream only. The bypass stream stays dry. There is no mixer. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The dry station set is `PROP - SeparateStreamTurbofan`. Core reheat reuses `afterburner_fuel_air_ratio` and the fully expanded reheat nozzle from `PROP - AfterburningTurbojet`. Reheated specific thrust per inlet airflow is

\[
F_s = \frac{(1+f+f_{ab})V_{e,\mathrm{reheat}} + \alpha V_f}{1+\alpha} - V_0,
\]

and

\[
c_t = \frac{f+f_{ab}}{F_s(1+\alpha)}.
\]

The figure plots reheated specific thrust versus afterburner temperature at the fixed bypass ratio and fan pressure ratio.

## When to run

1. Use this skill when the user wants an afterburning turbofan with reheat on the core only.
2. Convert inputs to SI before the call. Do not invent Mach, TIT, OPR, bypass ratio, fan pressure ratio, afterburner temperature, or a freestream state.
3. Pass `--mach`, `--tit`, `--opr`, `--bpr`, `--fpr`, and `--t7`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths.
4. Optional efficiencies match `PROP - SeparateStreamTurbofan` and `PROP - AfterburningTurbojet`. Pass them only when the user gave them.
5. One flight condition is one run. Do not use this skill for a mixed-flow fan or for an afterburning turbojet with no fan.

## Flags

Run:

```text
python "skills/PROP - AfterburningTurbofan/afterburning_turbofan.py" --mach <M> --tit <K> --opr <pi> --bpr <alpha> --fpr <pi_f> --t7 <K> (--alt <m> | --temperature <K> --pressure <Pa>) [--pi-d <pi>] [--eta-f <eta>] [--eta-c <eta>] [--eta-t <eta>] [--eta-m <eta>] [--eta-b <eta>] [--pi-b <pi>] [--eta-n <eta>] [--eta-ab <eta>] [--pi-ab <pi>] [--neglect-fuel-match] [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number | dimensionless, \(\ge 0\) | Required |
| `--tit` | Turbine inlet temperature | K | Required |
| `--opr` | Overall pressure ratio | dimensionless | Required |
| `--bpr` | Bypass ratio | dimensionless, \(\ge 0\) | Required |
| `--fpr` | Fan pressure ratio | dimensionless, \(> 1\) | Required |
| `--t7` | Core afterburner exit total temperature | K | Required |
| `--alt` | Geometric altitude | m | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature | K | With `--pressure` |
| `--pressure` | Freestream static pressure | Pa | With `--temperature` |
| `--pi-d` | Inlet recovery | dimensionless | Optional; default 1 |
| `--eta-f` | Fan efficiency | dimensionless | Optional; default 1 |
| `--eta-c` | Core compressor efficiency | dimensionless | Optional; default 1 |
| `--eta-t` | Turbine efficiency | dimensionless | Optional; default 1 |
| `--eta-m` | Mechanical efficiency | dimensionless | Optional; default 1 |
| `--eta-b` | Burner efficiency | dimensionless | Optional; default 1 |
| `--pi-b` | Burner pressure ratio | dimensionless | Optional; default 1 |
| `--eta-n` | Nozzle efficiency | dimensionless | Optional; default 1 |
| `--eta-ab` | Afterburner efficiency | dimensionless | Optional; default 1 |
| `--pi-ab` | Afterburner pressure ratio | dimensionless | Optional; default 1 |
| `--neglect-fuel-match` | Omit fuel mass in the shaft match | — | Optional |
| `--heating-value` | Fuel lower heating value | J/kg | Optional |
| `--cp` | Specific heat | J/(kg·K) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless | Optional; default 1.4 |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Afterburning turbofan`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is afterburner temperature. The curve is reheated specific thrust at the fixed bypass and fan pressure ratios.
3. Report `Fs_dry_m_s`, `Fs_reheat_m_s`, `f`, `f_ab`, and `TSFC_kg_N_s`. `Fs_reheat_m_s` is specific thrust per inlet airflow. `f` is the core fuel–air ratio. `f_ab` is the afterburner fuel–air ratio.
4. Report `freestream_source`, `gamma_source`, `cp_source`, and `Q_source`.
