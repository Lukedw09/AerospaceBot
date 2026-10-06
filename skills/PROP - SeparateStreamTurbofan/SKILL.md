---
name: PROP - SeparateStreamTurbofan
description: >-
  Run the design-point separate-stream turbofan and report its printed results
  and PNG. Use when the user wants core and fan specific thrust, inlet-airflow
  specific thrust, or TSFC from flight Mach, freestream state or altitude,
  turbine inlet temperature, overall pressure ratio, bypass ratio, and fan
  pressure ratio. Do not redraw the plot or recompute the numbers by hand.
---

# PROP - SeparateStreamTurbofan

Use this skill for a design-point unmixed turbofan. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The fan is a compressor on the whole inlet stream. Core compressor pressure ratio is `turbofan_core_pressure_ratio`, the overall pressure ratio divided by the fan pressure ratio. Shaft work per unit core air is `turbofan_shaft_work`: core-stream enthalpy rise from station 2 to station 3, plus bypass ratio times fan work on the bypass stream. That work goes to `turbine_temperature_ratio_from_work`. Specific thrust per inlet airflow is `turbofan_specific_thrust`. TSFC is `turbofan_tsfc`. Efficiencies are `turbofan_thermal_efficiency`, `turbofan_propulsive_efficiency`, and `turbofan_overall_efficiency`.

There is no mixer and no afterburner. Both nozzles are fully expanded.

## When to run

1. Use this skill when the user wants separate-stream turbofan specific thrust, the core and fan split, or TSFC.
2. Convert inputs to SI before the call. State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), TIT, overall pressure ratio, bypass ratio, fan pressure ratio, efficiencies, \(Q\), \(c_p\), or \(\gamma\).
3. Pass `--mach`, `--tit`, `--opr`, `--bpr`, and `--fpr`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths.
4. Optional `--pi-d`, `--eta-f`, `--eta-c`, `--eta-t`, `--eta-m`, `--eta-b`, `--pi-b`, and `--eta-n` only when the user gave them.
5. The plot is specific thrust and TSFC versus bypass ratio at the fixed fan pressure ratio.
6. Do not use this skill for a turbojet, an afterburner, or a mixed-flow turbofan.

## Flags

Run:

```text
python "skills/PROP - SeparateStreamTurbofan/separate_stream_turbofan.py" --mach <M> --tit <K> --opr <pi> --bpr <bpr> --fpr <pi_f> (--alt <m> | --temperature <K> --pressure <Pa>) [--pi-d <pi>] [--eta-f <eta>] [--eta-c <eta>] [--eta-t <eta>] [--eta-m <eta>] [--eta-b <eta>] [--pi-b <pi>] [--eta-n <eta>] [--neglect-fuel-match] [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number | dimensionless, \(\ge 0\) | Required |
| `--tit` | Turbine inlet total temperature \(T_{t4}\) | K | Required |
| `--opr` | Overall pressure ratio \(p_{t3}/p_{t2}\) | dimensionless, greater than `--fpr` | Required |
| `--bpr` | Bypass ratio \(\dot{m}_f/\dot{m}_c\) | dimensionless, \(\ge 0\) | Required |
| `--fpr` | Fan pressure ratio | dimensionless, \(> 1\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature | K | With `--pressure` |
| `--pressure` | Freestream static pressure | Pa | With `--temperature` |
| `--pi-d` | Inlet recovery | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-f` | Fan isentropic efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-c` | Core compressor isentropic efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-t`, `--eta-m`, `--eta-b`, `--pi-b`, `--eta-n` | Turbine, shaft, burner, and nozzle | — | Optional; default 1 |
| `--neglect-fuel-match` | Drop fuel mass in the shaft match | — | Optional |
| `--heating-value`, `--cp`, `--gamma` | Gas and fuel | — | Optional |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Heating value in MJ/kg uses `1 MJ/kg = 1e6 J/kg`.

Every successful run writes one PNG. The plot title is `Separate-stream turbofan`. The horizontal axis is bypass ratio. One curve is specific thrust per inlet airflow. The other is mass-based TSFC. The squares are the operating point.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `freestream_source`, and `Z_m` when the freestream came from altitude.
4. Report `bpr`, `pi_f`, `eta_f`, `pi_core`, `eta_c`, `eta_t`, `eta_m`, `eta_n`, `Fs_core_m_s`, `Fs_fan_m_s`, `Fs_m_s`, and `TSFC_kg_N_s`. State that `Fs_m_s` is per unit inlet airflow and that `TSFC_kg_N_s` is mass-based kg/(N·s) using core fuel only.
5. Report `eta_th`, `eta_p`, and `eta_o`.
6. Report `match_fuel`.
7. If Mach, TIT, overall pressure ratio, bypass ratio, fan pressure ratio, or a freestream path is missing, say so. Do not fill them in.
