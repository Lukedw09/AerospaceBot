---
name: COMMS - RainAttenuation
description: >-
  Run the rain-attenuation program and report its printed results and optional
  PNG. Use when the user wants slant-path rain attenuation in decibels and the
  matching linear power ratio from rain rate, frequency, elevation, and
  effective rainy path length. Do not redraw the plot or recompute the numbers
  by hand.
---

# COMMS - RainAttenuation

Use this skill for rain loss on an Earth-space path. Vacuum path loss stays on `COMMS - FreeSpaceLinkBudget`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Specific attenuation is `rain_specific_attenuation`, \(\gamma = a(f) R^{b(f)}\) in dB/km. Path attenuation is `rain_path_attenuation`, \(A = \gamma L_{\mathrm{eff}}\). The fraction of power that remains is `rain_power_ratio`, \(10^{-A/10}\). The coefficients \(a(f)\) and \(b(f)\) are the Marshall–Palmer, \(0^\circ\mathrm{C}\) nodes in NASA TP-1770 Table 3, interpolated in the logarithm of frequency. That table is not an ITU recommendation.

## When to run

1. Use this skill when the user wants rain attenuation or the linear power ratio for a rainy slant path.
2. Convert rain rate to mm/h, frequency to hertz, elevation to radians, and path length to metres. State the converted units in the reply. Do not invent rain rate, frequency, elevation, or path length.
3. Pass `--rate`, `--freq`, `--elevation`, and `--path`. `--path` is the effective rainy path length along the link, not a geometric range to the satellite.
4. Pass `--out` only when the user wants the PNG of attenuation versus rain rate. Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for gaseous absorption, free-space path loss, or a frequency outside 2–94 GHz.

## Flags

Run:

```text
python "skills/COMMS - RainAttenuation/rain_attenuation.py" --rate <mm/h> --freq <Hz> --elevation <rad> --path <m> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--rate` | Rain rate \(R\) | mm/h, \(> 0\) | Required |
| `--freq` | Carrier frequency | Hz, 2–94 GHz | Required |
| `--elevation` | Path elevation above the horizon | rad, \(0 < \theta \le \pi/2\) | Required |
| `--path` | Effective rainy path length \(L_{\mathrm{eff}}\) | m, \(> 0\) | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Frequency in GHz uses `1 GHz = 1e9 Hz`. Elevation in degrees uses \(\pi/180\). A path in kilometres uses `1 km = 1000 m`.

When `--out` is passed, the program writes one PNG. The plot title is `Rain attenuation`. The curve is path attenuation versus rain rate at the fixed frequency and path. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `a_coeff`, `b_coeff`, `gamma_dB_per_km`, `A_dB`, and `power_ratio`.
4. Report `elevation_rad` and `h_vert_m`. `h_vert_m` is \(L_{\mathrm{eff}}\sin\theta\), the vertical thickness of a horizontally stratified slab with that slant length.
5. Report the printed warning when elevation is below 10 degrees. The cosecant picture of a flat slab is weak there; the attenuation still uses the path length the user supplied.
6. If rain rate, frequency, elevation, or path length is missing, say so. Do not fill them in.
