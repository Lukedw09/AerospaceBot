---
name: AERO - ParachuteDescentRate
description: >-
  Run the parachute descent-rate program and report its printed results and
  optional PNG. Use when the user wants the steady terminal descent speed of
  an open canopy, or of named reefed canopies, from mass, drag coefficient,
  and area. Density comes from altitude unless the user overrides it. Do not
  redraw the plot or recompute the numbers by hand.
---

# AERO - ParachuteDescentRate

Use this skill for steady descent after the canopy is open and the drag equals the weight. It is not an opening shock, an inflation transient, or a swinging payload. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The terminal rate is `parachute_descent_rate`. Weight is \(W = m g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^{2}\):

\[
V = \sqrt{\frac{2W}{\rho C_D A}}
\]

Density is `ATMOS - Standard1976` at `--alt`. `--rho` replaces that density. Repeat `--reef name=cd,area` for reefed canopies. Each reef prints its own rate at the same density. One unreefed canopy, from `--cd` and `--area`, is the default path.

## When to run

1. Use this skill when the user wants the steady open-canopy descent rate, or the rate of a named reefed canopy.
2. Convert mass to kilograms, area to square metres, and altitude to metres. State the converted units in the reply. Do not invent mass, \(C_D\), or area.
3. Pass `--mass`, `--cd`, and `--area`.
4. Pass `--alt` or `--rho`, not both. `--alt` is geometric metres on the 1976 standard, from 0 to 86000. `--rho` is a density override.
5. Repeat `--reef name=cd,area` only for reef stages the user named.
6. Pass `--out` only when the user wants the PNG of rate versus altitude at the unreefed \(C_D A\). Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for opening shock, inflation time, or a swinging payload.

## Flags

Run:

```text
python "skills/AERO - ParachuteDescentRate/parachute_descent_rate.py" --mass <kg> --cd <Cd> --area <m^2> (--alt <m> | --rho <kg/m^3>) [--reef <name=cd,area>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mass` | Payload mass. Weight is \(mg_0\). | kg, \(> 0\) | Required |
| `--cd` | Unreefed drag coefficient | dimensionless, \(> 0\) | Required |
| `--area` | Unreefed reference area | m², \(> 0\) | Required |
| `--alt` | Geometric altitude | m, 0 to 86000 | Or `--rho` |
| `--rho` | Density override | kg/m³, \(> 0\) | Or `--alt` |
| `--reef` | Reefed canopy `name=cd,area` | — | Optional. Repeat for each reef. |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Parachute descent rate`. The curve is rate versus geometric altitude at the fixed unreefed \(C_D A\), using the 1976 density. The square is the operating altitude when `--alt` was passed. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `rho_kg_m3`, `rho_source`, and `V_m_s`. `altitude` means the 1976 standard. `override` means the user density.
4. Report each `reef_<name>_V_m_s` that is printed.
5. If mass, \(C_D\), area, or a density path is missing, say so. Do not fill them in.
