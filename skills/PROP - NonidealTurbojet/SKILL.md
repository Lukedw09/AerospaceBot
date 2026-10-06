---
name: PROP - NonidealTurbojet
description: >-
  Run the design-point nonideal turbojet and report its printed results and
  PNG. Use when the user wants specific thrust, TSFC, or station temperatures
  of an air-breathing turbojet with inlet recovery and component efficiencies
  from flight Mach, freestream state or altitude, turbine inlet temperature,
  and compressor pressure ratio. Do not redraw the plot or recompute the
  numbers by hand. Do not use this skill for an afterburner or a turbofan.
---

# PROP - NonidealTurbojet

Use this skill for a design-point air-breathing turbojet with inlet recovery and component efficiencies. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Freestream totals use `stagnation_temperature` and `stagnation_pressure`. The inlet is `adiabatic_diffuser_temperature` and `inlet_exit_total_pressure`. Compressor temperature ratio and work are `compressor_temperature_ratio_efficiency` and `compressor_work_efficiency`. Fuel-air ratio is `burner_fuel_air_ratio_efficiency`. Burner exit pressure is `burner_exit_total_pressure`. The shaft match is `turbine_temperature_ratio_from_work` with the fuel mass included unless `--neglect-fuel-match` is passed. Turbine pressure ratio is `turbine_pressure_ratio_from_efficiency`. Exit speed is `nozzle_exit_velocity_efficiency`. Specific thrust, TSFC, and the three efficiencies reuse `turbojet_specific_thrust`, `turbojet_tsfc`, `turbojet_thermal_efficiency`, `turbojet_propulsive_efficiency`, and `turbojet_overall_efficiency`.

Omitted efficiencies stay 1 and omitted loss ratios stay 1. With `--neglect-fuel-match` and those defaults, the result is the ideal turbojet. The default match includes fuel mass, so it is not identical to `PROP - IdealTurboJet`. There is no fan and no afterburner. Polytropic efficiency is not an input; pass the isentropic efficiency.

Hand \(\pi_d\) in from `PROP - InletRecovery` when the user has a recovery or a pitot inlet. The default \(\pi_d=1\) is a perfect inlet.

## When to run

1. Use this skill when the user wants design-point turbojet specific thrust, TSFC, efficiencies, or station totals with inlet recovery or component efficiencies.
2. Convert inputs to SI before the call (K, Pa, m, dimensionless Mach, pressure ratios, and efficiencies). State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), TIT, OPR, recovery, efficiencies, \(Q\), \(c_p\), or \(\gamma\).
3. Pass `--mach`, `--tit`, and `--opr`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths. `--alt` is geometric metres on the 1976 standard. Do not compute that atmosphere yourself.
4. Optional `--pi-d`, `--eta-c`, `--eta-t`, `--eta-m`, `--eta-b`, `--pi-b`, `--eta-n`, `--heating-value`, `--cp`, and `--gamma` only when the user gave them. Otherwise the program defaults apply.
5. Pass `--neglect-fuel-match` only when the user wants the ideal shaft match that drops the fuel mass.
6. One Mach, freestream, TIT, and OPR is one run. The plot is a Mach sweep at that TIT, OPR, recovery, and efficiencies.
7. Do not use this skill for an afterburner (`PROP - AfterburningTurbojet`), a turbofan (`PROP - SeparateStreamTurbofan`), or airflow sizing (`PROP - EngineAirflowSizing`).

## Flags

Run:

```text
python "skills/PROP - NonidealTurbojet/nonideal_turbojet.py" --mach <M> --tit <K> --opr <pi_c> (--alt <m> | --temperature <K> --pressure <Pa>) [--pi-d <pi_d>] [--eta-c <eta>] [--eta-t <eta>] [--eta-m <eta>] [--eta-b <eta>] [--pi-b <pi>] [--eta-n <eta>] [--neglect-fuel-match] [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number \(M\) | dimensionless, \(\ge 0\) | Required |
| `--tit` | Turbine inlet total temperature \(T_{t4}\) | K, \(> 0\) | Required |
| `--opr` | Compressor pressure ratio \(\pi_c=p_{t3}/p_{t2}\) | dimensionless, \(> 1\) | Required |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature \(T_0\) | K, \(> 0\) | With `--pressure` |
| `--pressure` | Freestream static pressure \(p_0\) | Pa, \(> 0\) | With `--temperature` |
| `--pi-d` | Inlet recovery \(p_{t2}/p_{t0}\) | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-c` | Compressor isentropic efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-t` | Turbine isentropic efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-m` | Shaft mechanical efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-b` | Burner efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--pi-b` | Burner pressure ratio \(p_{t4}/p_{t3}\) | dimensionless, \((0,1]\) | Optional; default 1 |
| `--eta-n` | Nozzle efficiency | dimensionless, \((0,1]\) | Optional; default 1 |
| `--neglect-fuel-match` | Drop fuel mass in the shaft match | — | Optional |
| `--heating-value` | Fuel lower heating value \(Q\) | J/kg | Optional; default \(4.28\times 10^{7}\) |
| `--cp` | Specific heat at constant pressure | J/(kg·K), \(> 0\) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional; default \(1.4\) |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`. Heating value in MJ/kg uses `1 MJ/kg = 1e6 J/kg`.

Every successful run writes one PNG. The plot title is `Nonideal turbojet`. The nozzle is fully expanded. There is no fan and no afterburner.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is Mach. The curve is specific thrust at fixed TIT, OPR, recovery, and efficiencies. The square is the operating point.
3. Report `freestream_source`. For `altitude`, report `Z_m`, `T0_K`, and `p0_Pa`, and state that those are the 1976 standard at that geometric altitude. For `temperature_pressure`, report the supplied `T0_K` and `p0_Pa`.
4. Report `pi_d`, `tau_c`, `Tt3_K`, `f`, `tau_t`, `pi_t`, `Fs_m_s`, `TSFC_kg_N_s`, `eta_th`, `eta_p`, `eta_o`, `Ve_m_s`, and `Te_K`. State that `TSFC_kg_N_s` is mass-based kg/(N·s).
5. Report `match_fuel`. `yes` means the shaft match includes fuel mass. `no` means `--neglect-fuel-match`.
6. Report `gamma`, `gamma_source`, `cp_J_kgK`, `cp_source`, `Q_J_kg`, and `Q_source`.
7. If Mach, TIT, OPR, or a freestream path is missing, say so. Do not fill them in.
