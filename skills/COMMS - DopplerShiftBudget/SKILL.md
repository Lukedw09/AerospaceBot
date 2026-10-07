---
name: COMMS - DopplerShiftBudget
description: >-
  Run the Doppler program and report its printed results and optional PNG.
  Use when the user wants the carrier shift from a radial speed, or the
  maximum shift of a circular orbit at an elevation mask, and the two-sided
  tracking span. Do not redraw the plot or recompute the numbers by hand.
---

# COMMS - DopplerShiftBudget

Use this skill for the carrier shift between a transmitter and a receiver, and the two-sided frequency span a receiver has to track. It does not compute path loss, rain, or \(E_b/N_0\). Those stay on `COMMS - FreeSpaceLinkBudget` and `COMMS - RainAttenuation`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The shift is `doppler_shift`, \(f_d = f v_r / c\), with \(c = 299792458\,\mathrm{m/s}\). A positive radial speed increases range. The circular-orbit maximum at an elevation mask is `orbit_mask_range_rate`, \(v_{r,\max} = v_{\mathrm{circ}}(R_0/a)\cos\varepsilon_{\min}\). Earth rotation is omitted on that path, and the program prints that assumption. The tracking span is \(2|f_d|\).

## When to run

1. Use this skill when the user wants a Doppler shift or the two-sided span a receiver must track.
2. Convert frequency to hertz, radial speed to m/s, altitude or radius to metres, and elevation to radians. State the converted units in the reply. Do not invent the carrier or a speed.
3. Pass `--freq` and exactly one speed path: `--v-radial`, or `--alt` or `--a` together with `--elev-min`.
4. Pass `--out` only for the orbit path, and only when the user wants the PNG. Do not invent a plot path when they did not ask for a figure. On the radial path the program ignores `--out` (hosts may inject it).
5. Do not use this skill for path loss, rain, or \(E_b/N_0\).

## Flags

Run:

```text
python "skills/COMMS - DopplerShiftBudget/doppler_shift_budget.py" --freq <Hz> (--v-radial <m/s> | (--alt <m> | --a <m>) --elev-min <rad>) [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--freq` | Carrier frequency | Hz, \(> 0\) | Required |
| `--v-radial` | Radial speed, positive when range increases | m/s | One of `--v-radial` or the orbit path |
| `--alt` | Circular altitude | m, \(> 0\) | One of `--alt` or `--a` on the orbit path |
| `--a` | Circular radius | m, \(> R_0\) | One of `--alt` or `--a` on the orbit path |
| `--elev-min` | Minimum elevation of the mask | rad, \([0, \pi/2)\) | Required on the orbit path |
| `--out` | PNG path for the orbit path | — | Optional. Orbit path only. Ignored on the radial path. Omit unless the user wants the figure. |

When `--out` is passed on the orbit path, the program writes one PNG. The plot title is `Doppler shift`. The curve is \(|f_d|\) versus elevation from the mask up to zenith. The square is the mask. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `fd_Hz`, `fd_abs_Hz`, and `span_Hz`. On the radial path `fd_Hz` is signed. On the orbit path it is the positive maximum.
4. On the orbit path, report that Earth rotation was omitted.
5. If the carrier or a radial-speed path is missing, say so. Do not fill them in.
