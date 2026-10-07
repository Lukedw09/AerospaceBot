---
name: ASTRO - RelativeOrbitClohessyWiltshire
description: >-
  Run the Clohessy-Wiltshire program and report its printed results and
  optional PNG. Use when the user wants the planar relative state of a deputy
  about a circular chief at a stated time, or the impulsive delta-v that nulls
  relative velocity or sets up a closed relative ellipse. Do not redraw the
  plot or recompute the numbers by hand.
---

# ASTRO - RelativeOrbitClohessyWiltshire

Use this skill for planar Clohessy–Wiltshire motion about a circular chief. \(x\) is along-track, positive with the chief velocity. \(z\) is radial, positive away from the planet. Out-of-plane motion and chief eccentricity are omitted. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Mean motion is `mean_motion`, \(n=\sqrt{\mu/a}\). The along-track and radial positions at time \(t\) are `clohessy_wiltshire_along_track` and `clohessy_wiltshire_radial`. The impulsive hold sets the along-track rate to `clohessy_wiltshire_hold_rate`, \(\dot x=-2 n z\), and the radial rate to zero, which is a closed 2:1 ellipse about the chief. Outside the chief that rate is backward. The null impulse cancels the current relative velocity.

Coplanar phasing in a shared circular orbit stays on `ASTRO - RendezvousPhasing`.

## When to run

1. Use this skill when the user wants the relative state at a time, or the impulsive delta-v to null relative velocity or to enter a closed relative ellipse.
2. Convert positions to metres, rates to m/s, time to seconds, and the chief radius to metres. State the converted units in the reply. Do not invent the relative state, the time, or the chief orbit.
3. Pass `--x`, `--z`, `--xdot`, `--zdot`, and `--time`. Pass the chief as `--a` or `--alt`.
4. Pass `--mu` only when the user gave a gravitational parameter. Otherwise leave the Earth default.
5. Pass `--out` only when the user wants the PNG of the relative trajectory. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for an eccentric chief, out-of-plane motion, or a finite burn.

## Flags

Run:

```text
python "skills/ASTRO - RelativeOrbitClohessyWiltshire/relative_orbit_clohessy_wiltshire.py" --x <m> --z <m> --xdot <m/s> --zdot <m/s> --time <s> (--a <m> | --alt <m>) [--mu <m^3/s^2>] [--R0 <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--x` | Along-track position, positive with the chief velocity | m | Required |
| `--z` | Radial position, positive away from the planet | m | Required |
| `--xdot` | Along-track rate | m/s | Required |
| `--zdot` | Radial rate | m/s | Required |
| `--time` | Time from the initial state | s, \(\ge 0\) | Required |
| `--a` | Chief circular radius | m, \(> 0\) | One of `--a` or `--alt` |
| `--alt` | Chief altitude above `--R0` | m, \(\ge 0\) | One of `--a` or `--alt` |
| `--mu` | Gravitational parameter | m³/s², \(> 0\) | Optional. Default Earth \(g_0 R_0^{2}\) |
| `--R0` | Planet radius used with `--alt` | m, \(> 0\) | Optional. Default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Relative orbit`. The curve is the deputy path in the chief frame from the initial time through `--time`. The square is the state at `--time`. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `n_rad_s`, `x_m`, `z_m`, `xdot_m_s`, and `zdot_m_s` at the requested time.
4. Report `dv_null_x_m_s` and `dv_null_z_m_s`. That impulse zeros the initial relative velocity.
5. Report `dv_hold_x_m_s` and `dv_hold_z_m_s`. That impulse sets the initial rate to the closed-ellipse condition.
6. Report `period_s`, the chief period, which is also the period of the closed relative ellipse.
7. If a relative-state component, the time, or the chief radius is missing, say so. Do not fill them in.
