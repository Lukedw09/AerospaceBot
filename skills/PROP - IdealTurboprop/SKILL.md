---
name: PROP - IdealTurboprop
description: >-
  Run the design-point ideal turboprop and report its printed results and
  PNG. Use when the user wants shaft power, propeller thrust, specific
  thrust, TSFC, and fuel-air ratio for an ideal turbojet gas generator
  driving a propeller. Static thrust is out of scope. Do not redraw the
  plot or recompute the numbers by hand.
---

# PROP - IdealTurboprop

Use this skill for a design-point ideal turboprop. The ideal turbojet gas generator drives a propeller instead of expanding the core jet to a high exhaust speed. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Compressor and burner algebra stay the ideal-turbojet records. Shaft power per unit inlet airflow is the turbine enthalpy remaining after the compressor is paid, once the residual jet is left at flight speed:

\[
P_{\mathrm{shaft}} = \tfrac{1}{2}(1+f)(V_e^{2}-V_0^{2}).
\]

Propeller thrust is \(\eta_p P_{\mathrm{shaft}}/V_0\). The residual jet thrust \(f V_0\) is omitted. The fuel–air ratio is the ideal-turbojet `burner_fuel_air_ratio`. TSFC uses `turbojet_tsfc` on that propeller thrust. Printed `shaft_power_W` and `thrust_N` are per 1 kg/s of inlet air, so `specific_thrust` equals `thrust_N`.

Mach must be greater than 0. Static thrust is out of scope because \(V_0 = 0\) makes the propeller thrust expression singular.

The figure plots thrust and TSFC versus Mach.

## When to run

1. Use this skill when the user wants ideal turboprop shaft power, thrust, specific thrust, or TSFC in forward flight.
2. Convert inputs to SI before the call. Do not invent Mach, TIT, OPR, propeller efficiency, or a freestream state.
3. Pass `--mach` (must be \(> 0\)), `--tit`, `--opr`, and `--eta-prop`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths.
4. One flight condition is one run.
5. Do not use this skill for static thrust or for a turbojet that keeps its core jet. A pure jet is `PROP - IdealTurboJet`.

## Flags

Run:

```text
python "skills/PROP - IdealTurboprop/ideal_turboprop.py" --mach <M> --tit <K> --opr <pi> --eta-prop <eta> (--alt <m> | --temperature <K> --pressure <Pa>) [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number | dimensionless, \(> 0\) | Required |
| `--tit` | Turbine inlet temperature | K | Required |
| `--opr` | Compressor pressure ratio | dimensionless, \(> 1\) | Required |
| `--eta-prop` | Propeller efficiency | dimensionless, \((0, 1]\) | Required |
| `--alt` | Geometric altitude | m | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature | K | With `--pressure` |
| `--pressure` | Freestream static pressure | Pa | With `--temperature` |
| `--heating-value` | Fuel lower heating value | J/kg | Optional |
| `--cp` | Specific heat | J/(kg·K) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless | Optional; default 1.4 |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Ideal turboprop`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is Mach. The curves are thrust per unit inlet airflow and TSFC.
3. Report `shaft_power_W`, `thrust_N`, `specific_thrust`, `tsfc`, and `f`. State that power and thrust are per 1 kg/s of inlet air.
4. Report `freestream_source`, `gamma_source`, `cp_source`, and `Q_source`.
