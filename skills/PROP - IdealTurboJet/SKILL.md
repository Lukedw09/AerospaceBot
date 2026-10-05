---
name: PROP - IdealTurboJet
description: >-
  Run the ideal Brayton turbojet program and report its printed results and
  PNG. Use when the user wants specific thrust, TSFC, thermal/propulsive/overall
  efficiency, or nozzle exit speed and temperature of a simple air-breathing
  turbojet from flight Mach, freestream state or altitude, turbine inlet
  temperature, and compressor pressure ratio. Do not redraw the plot or
  recompute the numbers by hand.
---

# PROP - IdealTurboJet

Use this skill for the ideal air-breathing Brayton turbojet (no fan, no afterburner, no real-component maps). Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Freestream totals use `stagnation_temperature` and `stagnation_pressure`. Compressor temperature ratio is `isentropic_compressor_temperature_ratio`, \(\tau_c=\pi_c^{(\gamma-1)/\gamma}\). Compressor work is `ideal_compressor_work`. Turbine match (fuel mass neglected in the shaft balance) is `ideal_turbine_temperature_ratio` and `ideal_turbine_pressure_ratio`. Fuel–air ratio is `burner_fuel_air_ratio`:

\[
f = \frac{c_p(T_{t4}-T_{t3})}{Q - c_p T_{t4}}.
\]

Nozzle pressure ratio is `ideal_turbojet_nozzle_pressure_ratio`. Exit speed and temperature are `ideal_nozzle_exit_velocity` and `ideal_nozzle_exit_temperature`. Specific thrust and mass-based TSFC are `turbojet_specific_thrust` and `turbojet_tsfc`:

\[
F_s = (1+f)V_e - V_0,\qquad c_t = \frac{f}{F_s}.
\]

Thermal, propulsive, and overall efficiencies are `turbojet_thermal_efficiency`, `turbojet_propulsive_efficiency`, and `turbojet_overall_efficiency`. The Brayton closed form `ideal_brayton_thermal_efficiency` is also printed.

The figure plots specific thrust versus Mach at the fixed TIT and compressor pressure ratio. The square is the operating point. Freestream \(T_0\) and \(p_0\) are held at the supplied flight condition while Mach varies on the curve.

## When to run

1. Use this skill when the user wants ideal turbojet specific thrust, TSFC, thermal/propulsive/overall efficiency, exit velocity, or exit temperature from Mach, freestream, TIT, and compressor pressure ratio.
2. Convert inputs to SI before the call (K, Pa, m, dimensionless Mach and OPR). State the converted units in the reply. Do not invent Mach, altitude, \(T\), \(p\), TIT, OPR, \(Q\), \(c_p\), or \(\gamma\).
3. Pass `--mach`, `--tit`, and `--opr`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths. `--alt` is geometric metres on the 1976 standard. Do not compute that atmosphere yourself.
4. Optional `--heating-value`, `--cp`, and `--gamma` only when the user gave them. Otherwise the program defaults apply.
5. One Mach, freestream, TIT, and OPR is one run. The plot is a Mach sweep at that TIT, OPR, and freestream \(T_0,p_0\).
6. Do not use this skill for fans, afterburners, or real compressor/turbine maps.

## Flags

Run:

```text
python "skills/PROP - IdealTurboJet/ideal_turbojet.py" --mach <M> --tit <K> --opr <pi_c> (--alt <m> | --temperature <K> --pressure <Pa>) [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number \(M\) | dimensionless, \(\ge 0\) | Required |
| `--tit` | Turbine inlet total temperature \(T_{t4}\) | K, \(> 0\) | Required |
| `--opr` | Compressor pressure ratio \(\pi_c=p_{t3}/p_{t2}\) | dimensionless, \(> 1\) | Required |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature \(T_0\) | K, \(> 0\) | With `--pressure` |
| `--pressure` | Freestream static pressure \(p_0\) | Pa, \(> 0\) | With `--temperature` |
| `--heating-value` | Fuel lower heating value \(Q\) | J/kg, \(> c_p T_{t4}\) | Optional; default \(4.28\times 10^{7}\) |
| `--cp` | Specific heat at constant pressure | J/(kg·K), \(> 0\) | Optional; default \(\gamma R/(\gamma-1)\) with 1976 dry-air \(R\) |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional; default \(1.4\) |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`. Heating value in MJ/kg uses `1 MJ/kg = 1e6 J/kg`.

Every successful run writes one PNG. The plot title is `Ideal turbojet`. The model is ideal Brayton; there is no fan, afterburner, inlet loss, or component map.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is Mach. The curve is specific thrust at fixed TIT and OPR. The square is the operating point.
3. Report `freestream_source`. For `altitude`, report `Z_m`, `T0_K`, and `p0_Pa`, and state that those are the 1976 standard at that geometric altitude. For `temperature_pressure`, report the supplied `T0_K` and `p0_Pa`.
4. Report `M`, `V0_m_s`, `pi_c`, `Tt4_K`, `f`, `Fs_m_s`, `TSFC_kg_N_s`, `eta_th`, `eta_p`, `eta_o`, `eta_brayton`, `Ve_m_s`, and `Te_K`. State that `TSFC_kg_N_s` is mass-based kg/(N·s) and that `eta_brayton` is the closed-form Brayton thermal efficiency.
5. Report `gamma`, `gamma_source`, `cp_J_kgK`, `cp_source`, `Q_J_kg`, and `Q_source`.
6. If Mach, TIT, OPR, or a freestream path is missing, say so. Do not fill them in.
