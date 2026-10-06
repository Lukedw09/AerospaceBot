---
name: PROP - IdealRamjet
description: >-
  Run the ideal Brayton ramjet program and report its printed results and PNG.
  Use when the user wants specific thrust, TSFC, thermal/propulsive/overall
  efficiency, or nozzle exit speed and temperature of a simple air-breathing
  ramjet (ram compression only; no compressor or turbine) from flight Mach,
  freestream state or altitude, and combustor max total temperature. Do not
  redraw the plot or recompute the numbers by hand.
---

# PROP - IdealRamjet

Use this skill for the ideal air-breathing Brayton ramjet (ram compression only; no compressor, no turbine, no scramjet, no real inlet map). Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Freestream totals use `stagnation_temperature` and `stagnation_pressure`. The ideal diffuser gives \(T_{t2}=T_{t0}\) and \(p_{t2}=p_{t0}\). Combustor entrance is \(T_{t3}=T_{t2}\). Combustor exit / max total temperature is \(T_{t4}\). Fuel–air ratio is `burner_fuel_air_ratio`:

\[
f = \frac{c_p(T_{t4}-T_{t3})}{Q - c_p T_{t4}}.
\]

Nozzle pressure ratio is `ideal_ramjet_nozzle_pressure_ratio` (\(\mathrm{NPR}=p_{t2}/p_0\)). Exit speed and temperature are `ideal_nozzle_exit_velocity` and `ideal_nozzle_exit_temperature` with nozzle total temperature \(T_{t4}\). Specific thrust and mass-based TSFC reuse `turbojet_specific_thrust` and `turbojet_tsfc`:

\[
F_s = (1+f)V_e - V_0,\qquad c_t = \frac{f}{F_s}.
\]

Thermal, propulsive, and overall efficiencies reuse `turbojet_thermal_efficiency`, `turbojet_propulsive_efficiency`, and `turbojet_overall_efficiency`. The closed form `ideal_ramjet_brayton_thermal_efficiency` is also printed:

\[
\eta_{\mathrm{Brayton}} = 1 - \frac{1}{\tau_r}.
\]

Mach must be greater than 1 (NASA Glenn: a ramjet cannot produce static thrust and needs forward speed). The program warns for \(1 < M < 2\) (below a practical cruise band) and for \(M > 5\) (Glenn: conventional ramjet becomes inefficient; this model is not a scramjet).

The figure plots specific thrust versus Mach at the fixed max total temperature. The square is the operating point. Freestream \(T_0\) and \(p_0\) are held at the supplied flight condition while Mach varies on the curve.

## When to run

1. Use this skill when the user wants ideal ramjet specific thrust, TSFC, thermal/propulsive/overall efficiency, exit velocity, or exit temperature from Mach, freestream, and combustor max total temperature.
2. Convert inputs to SI before the call (K, Pa, m, dimensionless Mach). State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), \(T_{t4}\), \(Q\), \(c_p\), or \(\gamma\).
3. Pass `--mach` and `--tmax`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths. `--alt` is geometric metres on the 1976 standard. Do not compute that atmosphere yourself.
4. Optional `--heating-value`, `--cp`, and `--gamma` only when the user gave them. Otherwise the program defaults apply.
5. One Mach, freestream, and max total temperature is one run. The plot is a Mach sweep at that \(T_{t4}\) and freestream \(T_0,p_0\).
6. Do not use this skill for fans, turbojet spools, afterburners, scramjets, inlet starting, or pressure recovery less than 1. A turbojet or turbofan with recovery, efficiencies, an afterburner, or airflow sizing is `PROP - InletRecovery`, `PROP - NonidealTurbojet`, `PROP - AfterburningTurbojet`, `PROP - SeparateStreamTurbofan`, or `PROP - EngineAirflowSizing`.

## Flags

Run:

```text
python "skills/PROP - IdealRamjet/ideal_ramjet.py" --mach <M> --tmax <K> (--alt <m> | --temperature <K> --pressure <Pa>) [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number \(M\) | dimensionless, \(> 1\) | Required |
| `--tmax` | Combustor exit / max total temperature \(T_{t4}\) | K, \(> 0\) | Required |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature \(T_0\) | K, \(> 0\) | With `--pressure` |
| `--pressure` | Freestream static pressure \(p_0\) | Pa, \(> 0\) | With `--temperature` |
| `--heating-value` | Fuel lower heating value \(Q\) | J/kg, \(> c_p T_{t4}\) | Optional; default \(4.28\times 10^{7}\) |
| `--cp` | Specific heat at constant pressure | J/(kg·K), \(> 0\) | Optional; default \(\gamma R/(\gamma-1)\) with 1976 dry-air \(R\) |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional; default \(1.4\) |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`. Heating value in MJ/kg uses `1 MJ/kg = 1e6 J/kg`.

Every successful run writes one PNG. The plot title is `Ideal ramjet`. The model is ideal Brayton with ram compression only; there is no compressor, turbine, fan, afterburner, inlet loss, or component map.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is Mach. The curve is specific thrust at fixed \(T_{t4}\). The square is the operating point.
3. Report `freestream_source`. For `altitude`, report `Z_m`, `T0_K`, and `p0_Pa`, and state that those are the 1976 standard at that geometric altitude. For `temperature_pressure`, report the supplied `T0_K` and `p0_Pa`.
4. Report `M`, `V0_m_s`, `Tt2_K`, `pt2_Pa`, `Tt4_K`, `f`, `Fs_m_s`, `TSFC_kg_N_s`, `eta_th`, `eta_p`, `eta_o`, `eta_brayton`, `Ve_m_s`, and `Te_K`. State that `TSFC_kg_N_s` is mass-based kg/(N·s) and that `eta_brayton` is the closed-form ram-only Brayton thermal efficiency.
5. Report `gamma`, `gamma_source`, `cp_J_kgK`, `cp_source`, `Q_J_kg`, and `Q_source`.
6. If any `warning_*` lines appear, report them (low-Mach or high-Mach band).
7. If Mach, \(T_{t4}\), or a freestream path is missing, say so. Do not fill them in.
