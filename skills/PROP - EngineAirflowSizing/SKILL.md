---
name: PROP - EngineAirflowSizing
description: >-
  Run the engine airflow sizing program and report its printed results and
  PNG. Use when the user wants inlet airflow, capture area, capture or face
  diameter, or compressor stage count from a required net thrust and a
  specific thrust. Do not redraw the plot or recompute the numbers by hand.
---

# PROP - EngineAirflowSizing

Use this skill to turn a required net thrust and a specific thrust into airflow and a diameter. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Airflow is `airflow_from_thrust`. Capture area is `capture_area` when flight speed is above zero. Diameter is `circular_capture_diameter`. Compressor-face area, when a face Mach and face totals are given, is `annulus_area_from_mass_flow` with `compressible_mass_flow_parameter`. Equal-stage count is `compressor_stage_count`.

Take specific thrust from `PROP - NonidealTurbojet`, `PROP - AfterburningTurbojet`, or `PROP - SeparateStreamTurbofan`. Take face total pressure and temperature from `PROP - InletRecovery` when the user has them. Static flight has no capture area; size the face instead.

## When to run

1. Use this skill when the user wants airflow, inlet diameter, face area, or compressor stage count from a thrust requirement.
2. Convert inputs to SI before the call. State the converted units in the reply. Do not invent thrust, specific thrust, speed, density, face Mach, or pressure ratios.
3. Pass `--thrust` and `--fs`. For a flying capture area pass `--alt` with `--mach` or `--speed`, or pass `--rho` with `--speed`.
4. Pass `--face-mach`, `--face-pt`, and `--face-tt` together when a face area is wanted. Static flight (`--speed 0`) requires those three flags.
5. Pass `--opr` and `--stage-pr` together when a stage count is wanted.
6. The plot is airflow and diameter versus required thrust at the fixed specific thrust and flight state.
7. Do not use this skill to compute specific thrust. That comes from a cycle skill.

## Flags

Run:

```text
python "skills/PROP - EngineAirflowSizing/engine_airflow_sizing.py" --thrust <N> --fs <m/s> (--alt <m> (--mach <M> | --speed <m/s>) | --rho <kg/m^3> --speed <m/s>) [--face-mach <M>] [--face-pt <Pa>] [--face-tt <K>] [--opr <pi>] [--stage-pr <pi>] [--gamma <g>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--thrust` | Required net thrust | N, \(> 0\) | Required |
| `--fs` | Specific thrust | m/s, \(> 0\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | With `--mach` or `--speed` |
| `--mach` | Flight Mach number | dimensionless, \(\ge 0\) | With `--alt`, or use `--speed` |
| `--speed` | Flight speed | m/s, \(\ge 0\) | With `--alt` or `--rho` |
| `--rho` | Freestream density | kg/m³, \(> 0\) | With `--speed` |
| `--face-mach` | Axial Mach at the compressor face | dimensionless, \(> 0\) | With the face totals; required if speed is 0 |
| `--face-pt` | Face total pressure | Pa, \(> 0\) | With `--face-mach` |
| `--face-tt` | Face total temperature | K, \(> 0\) | With `--face-mach` |
| `--opr` | Compressor pressure ratio | dimensionless, \(> 1\) | With `--stage-pr` |
| `--stage-pr` | Mean stage pressure ratio | dimensionless, \(> 1\) | With `--opr` |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional; default \(1.4\) |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Thrust in kilonewtons uses `1 kN = 1000 N`. Speed in knots uses `1 kn = 0.514444 m/s`.

Every successful run writes one PNG. The plot title is `Engine airflow sizing`. The horizontal axis is required net thrust. One curve is airflow. The other is capture diameter in flight, or face diameter when the flight speed is zero. The squares are the operating point.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `mdot_kg_s`. State that it is thrust divided by specific thrust.
4. If `A_capture_m2` and `D_capture_m` are present, report them and the flight speed and density. If they are absent, state that the flight speed is zero so there is no capture area.
5. If `A_face_m2` and `D_face_m` are present, report them with `M_face`.
6. If `N_stages` is present, report it with `pi_c` and `pi_stage`.
7. Report `sizing_diameter` (`capture` or `face`).
8. If thrust, specific thrust, or a flight path is missing, say so. Do not fill them in.
