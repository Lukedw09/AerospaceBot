---
name: ATMOS - KineticTemperatureAbove86km
description: >-
  Run the 1976 kinetic-temperature program above 86 km and report its printed
  results and optional PNG. Use when the user wants kinetic temperature or the
  temperature-segment name at a geometric altitude from 86 km through 1000 km.
  Do not print pressure or density, and do not recompute the numbers by hand.
---

# ATMOS - KineticTemperatureAbove86km

Use this skill for the 1976 U.S. Standard Atmosphere kinetic-temperature profile above 86 km. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand. Do not report pressure or density.

Geometric altitude \(Z\) is the input. Above \(Z_7 = 86\,\mathrm{km}\) the argument stays geometric. The four continuous segments in `formulas.md` are:

1. Mesopause, \(86\)–\(91\,\mathrm{km}\): isothermal `kinetic_temperature_linear` with \(T_7 = 186.8673\,\mathrm{K}\) and \(L_{K,7} = 0\).
2. Mesosphere ellipse, \(91\)–\(110\,\mathrm{km}\): `mesosphere_ellipse_temperature`

\[
T = T_c + A\left[1 - \left(\frac{Z - Z_8}{a}\right)^2\right]^{1/2}
\]

with \(T_c = 263.1905\,\mathrm{K}\), \(A = -76.3232\,\mathrm{K}\), \(a = -19.9429\,\mathrm{km}\), and \(Z_8 = 91\,\mathrm{km}\).

3. Thermosphere linear ramp, \(110\)–\(120\,\mathrm{km}\): `kinetic_temperature_linear` with \(T_9 = 240\,\mathrm{K}\) and \(L_{K,9} = 12\,\mathrm{K/km}\), so \(T_{10} = 360\,\mathrm{K}\) at \(120\,\mathrm{km}\).
4. Exosphere, \(120\)–\(1000\,\mathrm{km}\): `reduced_geopotential` and `exospheric_temperature` toward \(T_\infty = 1000\,\mathrm{K}\) (mean solar activity) with \(\lambda = 0.01875\,\mathrm{km}^{-1}\).

This is not the hydrostatic molecular-scale model below 86 km and not the NASA Glenn three-zone fit. Pressure and density above 86 km need species number densities and belong to `ATMOS - DensityAbove86km`. They are omitted here.

## When to run

1. Use this skill when the user asks for kinetic temperature, or which temperature segment they are in, at a geometric altitude from 86 km through 1000 km.
2. Convert altitude to geometric metres before the call. State the converted units in the reply. A bare altitude is geometric metres, not geopotential. Do not invent an altitude.
3. One altitude is one run. Do not sweep.
4. Pass `--out` only when the user wants the PNG of temperature versus altitude. Do not invent a plot path when they did not ask for a figure.
5. Geometric altitudes from sea level through 86 km that need pressure, density, sound speed, or scale height belong to `ATMOS - Standard1976`. Transport properties belong to `ATMOS - TransportProperties`.

## Flags

Run:

```text
python "skills/ATMOS - KineticTemperatureAbove86km/kinetic_temperature_above_86km.py" --alt <m> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude \(Z\) | m, 86000 to 1000000 | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. If the user gives geopotential altitude \(H\), convert with \(Z = r_0 H / (r_0 - H)\) and \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\) before the call, and say so. That conversion is only meaningful while \(H < r_0\); this skill still evaluates temperature on geometric \(Z\).

When `--out` is passed, the program writes one PNG. The plot title is `Kinetic temperature above 86 km`. Temperature is on the horizontal axis and geometric altitude in kilometres is on the vertical axis. The square marks the user's altitude.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report geometric altitude `Z_m`. State that \(Z\) is geometric.
4. Report `T_K` and `segment`. Segment names are `mesopause`, `mesosphere_ellipse`, `thermosphere_linear`, and `exosphere`.
5. Do not invent or print 1976 pressure or density. This program omits them.
6. If altitude is missing, or outside 86000 to 1000000 m, say so. Do not fill it in.
