---
name: PROP - ScramjetIdealCycle
description: >-
  Run the ideal scramjet Brayton program and report its printed results and
  PNG. Use when the user wants fuel-air ratio, specific thrust, and TSFC for
  ram compression that stops at a supersonic combustor Mach, constant-pressure
  heat addition, and ideal expansion back to freestream pressure. Do not
  redraw the plot or recompute the numbers by hand.
---

# PROP - ScramjetIdealCycle

Use this skill for an ideal scramjet Brayton cycle. It is the `PROP - IdealRamjet` station set with one change: combustor entrance Mach is `--combustor-mach` and must be greater than 1. Flight Mach must be greater than that combustor Mach. A combustor Mach at or below 1 is rejected; that case is the ramjet skill. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

NASA Glenn: a scramjet has no terminal normal shock, so the diffuser stops while the flow is still supersonic. Combustion is at constant pressure. The nozzle expands isentropically back to freestream pressure. This program holds the combustor entrance speed through the burner (constant-velocity heat addition) so the combustor Mach falls as the gas is heated.

Fuel–air ratio, specific thrust, and TSFC reuse `burner_fuel_air_ratio`, `turbojet_specific_thrust`, and `turbojet_tsfc`. There is no inlet schedule and no finite-rate chemistry.

The figure plots specific thrust versus flight Mach at the fixed combustor Mach and \(T_{t4}\).

## When to run

1. Use this skill when the user wants an ideal scramjet cycle with a stated supersonic combustor Mach.
2. Convert inputs to SI before the call. Do not invent flight Mach, combustor Mach, \(T_{t4}\), or a freestream state.
3. Pass `--mach`, `--combustor-mach`, and `--tmax`. Pass `--alt` or both `--temperature` and `--pressure`, not both paths.
4. Reject the request here only by running the program: combustor Mach at or below 1, or flight Mach at or below the combustor Mach, is an error from the program.
5. Do not use this skill for a subsonic-burner ramjet. That is `PROP - IdealRamjet`.

## Flags

Run:

```text
python "skills/PROP - ScramjetIdealCycle/scramjet_ideal_cycle.py" --mach <M> --combustor-mach <Mc> --tmax <K> (--alt <m> | --temperature <K> --pressure <Pa>) [--heating-value <J/kg>] [--cp <J/(kg*K)>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Flight Mach number | dimensionless, \(> M_c\) | Required |
| `--combustor-mach` | Combustor entrance Mach | dimensionless, \(> 1\) | Required |
| `--tmax` | Combustor exit total temperature \(T_{t4}\) | K | Required |
| `--alt` | Geometric altitude | m | Or freestream \(T,p\) |
| `--temperature` | Freestream static temperature | K | With `--pressure` |
| `--pressure` | Freestream static pressure | Pa | With `--temperature` |
| `--heating-value` | Fuel lower heating value | J/kg | Optional |
| `--cp` | Specific heat | J/(kg·K) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless | Optional; default 1.4 |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Ideal scramjet`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is flight Mach. The curve is specific thrust at the fixed combustor Mach and \(T_{t4}\).
3. Report `M`, `Mc`, `f`, `Fs_m_s`, and `TSFC_kg_N_s`.
4. Report `freestream_source`, `gamma_source`, `cp_source`, and `Q_source`.
