---
name: ASTRO - ConjunctionMissDistance
description: >-
  Run the conjunction program and report its printed results and optional PNG.
  Use when the user wants the geometric closest approach of two Keplerian
  states over a forward time window, the time of that approach, and the
  relative speed there. Do not redraw the plot or recompute the numbers by hand.
---

# ASTRO - ConjunctionMissDistance

Use this skill for the geometric miss distance of two objects on Keplerian orbits about the same planet. It is not a collision probability, a covariance ellipsoid, or a screening threshold. States may be converted from elements with `ASTRO - OrbitalParameters` before this call. This skill does not accept TLEs. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Both trajectories use the same two-body model as `ASTRO - OrbitalParameters`: spherical gravity, no drag, no J2. The program samples range through the window, then refines the minimum of \(r\cdot r\). If that minimum sits on a window endpoint, `endpoint_minimum` is `yes`.

## When to run

1. Use this skill when the user wants a geometric miss distance, the time of closest approach, or the relative speed at that time.
2. Convert both inertial states to metres and m/s at one shared epoch, and the window to seconds. State the converted units in the reply. Do not invent a component.
3. Pass `--r1x` through `--v1z`, `--r2x` through `--v2z`, and `--window`.
4. Pass `--mu` only when the user gave a gravitational parameter other than the Earth default \(g_0 R_0^{2}\).
5. Pass `--out` only when the user wants the PNG of range versus time. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for a collision probability or a TLE.

## Flags

Run:

```text
python "skills/ASTRO - ConjunctionMissDistance/conjunction_miss_distance.py" --r1x <m> --r1y <m> --r1z <m> --v1x <m/s> --v1y <m/s> --v1z <m/s> --r2x <m> --r2y <m> --r2z <m> --v2x <m/s> --v2y <m/s> --v2z <m/s> --window <s> [--mu <m^3/s^2>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r1x` | Object 1 position x | m | Required |
| `--r1y` | Object 1 position y | m | Required |
| `--r1z` | Object 1 position z | m | Required |
| `--v1x` | Object 1 velocity x | m/s | Required |
| `--v1y` | Object 1 velocity y | m/s | Required |
| `--v1z` | Object 1 velocity z | m/s | Required |
| `--r2x` | Object 2 position x | m | Required |
| `--r2y` | Object 2 position y | m | Required |
| `--r2z` | Object 2 position z | m | Required |
| `--v2x` | Object 2 velocity x | m/s | Required |
| `--v2y` | Object 2 velocity y | m/s | Required |
| `--v2z` | Object 2 velocity z | m/s | Required |
| `--window` | Search window forward from the epoch | s, \(> 0\) | Required |
| `--mu` | Gravitational parameter | m³/s², \(> 0\) | Optional. Default \(g_0 R_0^{2}\) |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Conjunction miss distance`. The curve is range versus time. The square is the closest approach. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `miss_m`, `tca_s`, `v_rel_m_s`, and `endpoint_minimum`.
4. If `endpoint_minimum` is `yes`, say the closest approach is on the window edge, so a longer window may be closer.
5. If any state component or the window is missing, say so. Do not fill it in.
