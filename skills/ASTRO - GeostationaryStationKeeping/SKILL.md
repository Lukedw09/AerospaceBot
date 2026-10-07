---
name: ASTRO - GeostationaryStationKeeping
description: >-
  Run the geostationary station-keeping program and report its printed results
  and optional PNG. Use when the user wants the yearly north-south and
  east-west impulses that remove a stated inclination drift and eccentricity
  drift. Do not redraw the plot or recompute the numbers by hand.
---

# ASTRO - GeostationaryStationKeeping

Use this skill for the impulses that remove one year of geostationary inclination growth and eccentricity growth. It does not fly a station-keeping box, a longitude deadband, or a thruster duty cycle. The named pieces hand to `ASTRO - VacuumPropellantMass`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The orbit is the circular geostationary radius from \(\mu = g_0 R_0^{2}\) and the sidereal Earth rate. Both budgets use that one circular speed. North–south reuses `plane_change_impulse`, \(\Delta v = 2 v \sin(\Delta i/2)\). Several burns split the year’s angle into equal pieces and sum those impulses. East–west is `eccentricity_removal_impulse`, \(\Delta v = 2 v e\). `--years` scales both pieces. The figure is one year.

## When to run

1. Use this skill when the user wants the north–south, east–west, or total geostationary station-keeping impulse.
2. Convert the yearly inclination to radians. Eccentricity is dimensionless. State the converted units in the reply. Do not invent either drift, and do not use a baked yearly delta-v.
3. Pass `--di-year` and `--e-year`.
4. Pass `--ns-burns` only when the user wants the year’s inclination split. The default is 1.
5. Pass `--years` only when the user wants a budget longer than one year. The default is 1.
6. Pass `--out` only when the user wants the one-year waterfall PNG. Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for a longitude box or a thruster duty cycle.

## Flags

Run:

```text
python "skills/ASTRO - GeostationaryStationKeeping/geostationary_station_keeping.py" --di-year <rad> --e-year <e> [--ns-burns <N>] [--years <years>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--di-year` | Inclination to remove each year | rad, \(\ge 0\) | Required |
| `--e-year` | Eccentricity to remove each year | dimensionless, \(\ge 0\) | Required |
| `--ns-burns` | Equal north–south burns in the year | dimensionless, integer \(\ge 1\) | Optional. Default 1 |
| `--years` | Years that scale both pieces | dimensionless, \(> 0\) | Optional. Default 1 |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Geostationary station-keeping`. The bars are the north–south piece, the east–west piece stacked on it, and the one-year total. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `dv_ns_m_s`, `dv_ew_m_s`, and `dv_total_m_s`.
4. If either yearly drift is missing, say so. Do not fill it in.
