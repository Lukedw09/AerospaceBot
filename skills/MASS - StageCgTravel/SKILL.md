---
name: MASS - StageCgTravel
description: >-
  Run the stage center-of-mass travel program and report its printed results
  and optional PNG. Use when the user wants how a burning stage, or a stack of
  stages, moves its center of mass along one axis as propellant is consumed.
  Do not redraw the plot or recompute the numbers by hand.
---

# MASS - StageCgTravel

Use this skill for the one-axis center of mass of a stage as it burns. Inert mass and tank shells stay in `ROCKET - VehicleMassBudget`. This skill does not compute products of inertia. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Each `--stage` carries dry mass, the dry station, propellant mass, and the full and empty propellant stations, in metres along one axis. At burn fraction \(f\),

\[
m_p = m_{p0}(1-f),\qquad x_p = x_{\mathrm{full}} + f(x_{\mathrm{empty}}-x_{\mathrm{full}})
\]

The stage station is `center_of_mass_coordinate` of the dry mass and the remaining propellant:

\[
x = \frac{m_{\mathrm{dry}} x_{\mathrm{dry}} + m_p x_p}{m_{\mathrm{dry}}+m_p}
\]

The stack station is that same sum over every stage at one fraction. At least one stage is required.

## When to run

1. Use this skill when the user wants the center-of-mass station of a burning stage or of a stack at a burn fraction.
2. Convert masses to kilograms and stations to metres. State the converted units in the reply. Do not invent a dry mass, a propellant mass, or a station.
3. Repeat `--stage dry,x_dry,mp,x_full,x_empty` once per stage. At least one stage is required.
4. Pass `--fraction` from 0 (full) to 1 (empty).
5. Pass `--out` only when the user wants the PNG of stack station versus burn fraction. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for products of inertia or for a vehicle mass budget.

## Flags

Run:

```text
python "skills/MASS - StageCgTravel/stage_cg_travel.py" --stage <dry,x_dry,mp,x_full,x_empty> [--stage <dry,x_dry,mp,x_full,x_empty>] --fraction <f> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stage` | `dry,x_dry,mp,x_full,x_empty` | kg and m | Required. Repeat for each stage. |
| `--fraction` | Burn fraction \(f\) | dimensionless, 0 to 1 | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Stage CG travel`. The curve is stack station versus burn fraction from 0 to 1. The square is the printed fraction. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `fraction`, `stack_x_m`, and `stack_mass_kg`.
4. Report each `stage_<n>_x_m` and `stage_<n>_mp_kg`.
5. If a stage or the burn fraction is missing, say so. Do not fill them in.
