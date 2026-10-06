---
name: ATMOS - DensityAbove86km
description: >-
  Run the 1976 density program above 86 km and report its printed results and
  optional PNG. Use when the user wants mass density, pressure, or species
  number densities at one geometric altitude from just above 86 km through
  1000 km. Do not recompute the numbers by hand. Altitudes at or below 86 km
  belong to ATMOS - Standard1976.
---

# ATMOS - DensityAbove86km

Use this skill for the 1976 U.S. Standard Atmosphere mass density above 86 km. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Kinetic temperature is the same four-segment profile as `ATMOS - KineticTemperatureAbove86km`. Number densities of N2, O, O2, Ar, and He are integrated from the 86 km boundary values in NASA TR R-459. Atomic hydrogen starts at 150 km from the 500 km anchor and escape flux in that report. Mass density is the species sum. Mean solar activity only, exospheric temperature 1000 K. This is not NRLMSISE-00 and not Earth-GRAM.

`ASTRO - AerodynamicDragDeltaV` and the aerodynamic torque in `ADCS - EnvironmentalTorques` call this skill when the altitude is above 86 km. A user-supplied density on those skills is an override, not the default.

## When to run

1. Use this skill when the user wants 1976 mass density, pressure, mean molar mass, or species number densities above 86 km.
2. Convert altitude to geometric metres before the call. State the converted units in the reply. Do not invent an altitude.
3. One altitude is one run. Do not sweep unless the user asks for the PNG, which the program draws itself.
4. Pass `--out` only when the user wants the PNG of density versus altitude.
5. Geometric altitudes from sea level through 86 km that need density belong to `ATMOS - Standard1976`. Temperature alone above 86 km belongs to `ATMOS - KineticTemperatureAbove86km`.

## Flags

Run:

```text
python "skills/ATMOS - DensityAbove86km/density_above_86km.py" --alt <m> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude \(Z\) | m, greater than 86000 and at most 1000000 | Required |
| `--out` | PNG path | — | Optional |

Altitude in kilometres uses `1 km = 1000 m`.

When `--out` is passed, the program writes one PNG. The plot title is `Density above 86 km`. Mass density is on a logarithmic horizontal axis and geometric altitude in kilometres is on the vertical axis. The square marks the user's altitude. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `Z_m`, `T_K`, `segment`, `rho_kg_m3`, `p_Pa`, `N_m3`, and `M_kg_kmol`.
4. Report the species number densities `n_N2_m3`, `n_O_m3`, `n_O2_m3`, `n_Ar_m3`, `n_He_m3`, and `n_H_m3`. Hydrogen is 0 below 150 km.
5. State that the model is the 1976 mean-solar profile, not a daily solar-weather forecast.
6. If altitude is missing, or not above 86 km through 1000 km, say so. Do not fill it in.
