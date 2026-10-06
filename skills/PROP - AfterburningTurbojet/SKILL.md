---
name: PROP - AfterburningTurbojet
description: >-
  Run the design-point afterburning turbojet and report its printed results
  and PNG. Use when the user wants dry and reheat specific thrust, fuel-air
  ratio, or TSFC from flight Mach, freestream state or altitude, turbine inlet
  temperature, compressor pressure ratio, and afterburner exit temperature.
  Do not redraw the plot or recompute the numbers by hand.
---

# PROP - AfterburningTurbojet

Use this skill for a design-point afterburning turbojet. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The dry core is `PROP - NonidealTurbojet`. Afterburner fuel is `afterburner_fuel_air_ratio`. Afterburner exit pressure is `afterburner_exit_total_pressure`. The default nozzle is fully expanded through `nozzle_exit_velocity_efficiency`. `--nozzle convergent` uses `sonic_pressure`, `sonic_temperature`, and `specific_thrust_with_pressure` when the nozzle is choked. Efficiencies use the momentum thrust. Net specific thrust includes the pressure term when the exit is choked.

A real afterburning nozzle is variable-area. The convergent option is one exit state at the area implied by the mass flow.

## When to run

1. Use this skill when the user wants afterburner fuel flow, reheat specific thrust, thrust ratio, or reheat TSFC.
2. Convert inputs to SI before the call. State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), TIT, OPR, \(T_{t7}\), efficiencies, \(Q\), \(c_p\), or \(\gamma\).
3. Pass `--mach`, `--tit`, `--opr`, and `--t7`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths.
4. Optional component efficiencies and `--pi-d` only when the user gave them. Otherwise the defaults of the nonideal turbojet apply, including fuel mass in the shaft match.
5. `--nozzle convergent` only when the user asked for a convergent nozzle. Otherwise leave the fully expanded nozzle.
6. The plot is specific thrust versus afterburner temperature at the flight point.
7. Do not use this skill for a dry turbojet (`PROP - NonidealTurbojet`), a turbofan, or a ramjet.

## Flags

Run:

```text
python "skills/PROP - AfterburningTurbojet/afterburning_turbojet.py" --mach <M> --tit <K> --opr <pi_c> --t7 <K> (--alt <m> | --temperature <K> --pressure <Pa>) [--eta-ab <eta>] [--pi-ab <pi>] [--nozzle expanded|convergent] [--pi-d <pi>] [--eta-c <eta>] [--eta-t <eta>] [--eta-m <eta>] [--eta-b <eta>] [--pi-b <pi>] [--eta-n <eta>] [--neglect-fuel-match] [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number | dimensionless, \(\ge 0\) | Required |
| `--tit` | Turbine inlet total temperature \(T_{t4}\) | K | Required |
| `--opr` | Compressor pressure ratio | dimensionless, \(> 1\) | Required |
| `--t7` | Afterburner exit total temperature \(T_{t7}\) | K, above \(T_{t5}\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature | K | With `--pressure` |
| `--pressure` | Freestream static pressure | Pa | With `--temperature` |
| `--eta-ab` | Afterburner efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--pi-ab` | Afterburner pressure ratio | dimensionless, \((0,1]\) | Optional; default 1 |
| `--nozzle` | `expanded` or `convergent` | — | Optional; default `expanded` |
| `--pi-d`, `--eta-c`, `--eta-t`, `--eta-m`, `--eta-b`, `--pi-b`, `--eta-n` | Same as `PROP - NonidealTurbojet` | — | Optional |
| `--neglect-fuel-match` | Drop fuel mass in the shaft match | — | Optional |
| `--heating-value`, `--cp`, `--gamma` | Gas and fuel | — | Optional |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Heating value in MJ/kg uses `1 MJ/kg = 1e6 J/kg`.

Every successful run writes one PNG. The plot title is `Afterburning turbojet`. The horizontal axis is \(T_{t7}\). The curve is reheat specific thrust. The square is the operating point.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `freestream_source`, and `Z_m` when the freestream came from altitude.
4. Report `f`, `f_ab`, `f_total`, `Fs_dry_m_s`, `Fs_m_s`, `thrust_ratio`, `TSFC_dry_kg_N_s`, and `TSFC_kg_N_s`. State that both TSFC values are mass-based kg/(N·s).
5. Report `nozzle` and `choked`. If `warning_convergent_nozzle` is present, report it.
6. Report `Ve_m_s`, `Te_K`, and `pe_Pa`. If `choked` is `yes`, also report `As_m_s_kg` and state that `Fs_m_s` includes the pressure term while the efficiencies use `Fs_momentum_m_s`.
7. If Mach, TIT, OPR, \(T_{t7}\), or a freestream path is missing, say so. Do not fill them in.
