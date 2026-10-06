---
name: PROP - InletRecovery
description: >-
  Run the inlet recovery program and report its printed results and PNG. Use
  when the user wants compressor-face total pressure and temperature from
  flight Mach, freestream state or altitude, and either a supplied recovery or
  a pitot inlet. Do not redraw the plot or recompute the numbers by hand.
---

# PROP - InletRecovery

Use this skill for the adiabatic inlet from freestream (station 0) to the compressor face (station 2). Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Freestream totals use `stagnation_temperature` and `stagnation_pressure`. Total temperature is unchanged: `adiabatic_diffuser_temperature`. Face total pressure is `inlet_exit_total_pressure`. A pitot inlet uses `pitot_inlet_recovery`: `normal_shock_stagnation_pressure` times a subsonic-diffuser factor. At Mach at or below 1 that shock ratio is 1. There is no military-spec Mach schedule in the catalog. Do not invent one.

Hand `pi_d` to `PROP - NonidealTurbojet`, `PROP - AfterburningTurbojet`, or `PROP - SeparateStreamTurbofan`. This skill does not compute thrust.

## When to run

1. Use this skill when the user wants inlet recovery, face total pressure, or face total temperature.
2. Convert inputs to SI before the call (K, Pa, m, dimensionless Mach and recovery). State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), \(\pi_d\), or \(\gamma\).
3. Pass `--mach`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths. `--alt` is geometric metres on the 1976 standard. Do not compute that atmosphere yourself.
4. Pass `--pi-d` or `--pitot`, not both. `--pi-ds` is only for `--pitot`.
5. One Mach, freestream, and recovery rule is one run. The plot is recovery versus Mach for that rule.
6. Do not use this skill for thrust, an afterburner, or airflow sizing.

## Flags

Run:

```text
python "skills/PROP - InletRecovery/inlet_recovery.py" --mach <M> (--alt <m> | --temperature <K> --pressure <Pa>) (--pi-d <pi_d> | --pitot [--pi-ds <pi>]) [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number \(M\) | dimensionless, \(\ge 0\) | Required |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature \(T_0\) | K, \(> 0\) | With `--pressure` |
| `--pressure` | Freestream static pressure \(p_0\) | Pa, \(> 0\) | With `--temperature` |
| `--pi-d` | Supplied recovery \(p_{t2}/p_{t0}\) | dimensionless, \((0,1]\) | Or `--pitot` |
| `--pitot` | One normal shock times `--pi-ds` | — | Or `--pi-d` |
| `--pi-ds` | Subsonic diffuser factor | dimensionless, \((0,1]\) | Optional with `--pitot`; default 1 |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional; default \(1.4\) |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`.

Every successful run writes one PNG. The plot title is `Inlet recovery`. The horizontal axis is Mach. The curve is \(\pi_d\). The square is the operating point.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `freestream_source`. For `altitude`, report `Z_m`, `T0_K`, and `p0_Pa`, and state that those are the 1976 standard at that geometric altitude.
4. Report `recovery_source`, `pi_d`, `Tt2_K`, and `pt2_Pa`. For `pitot`, also report `pi_ns` and `pi_ds`.
5. State that \(T_{t2}=T_{t0}\) because the inlet is adiabatic.
6. If Mach, a freestream path, or a recovery rule is missing, say so. Do not fill them in.
