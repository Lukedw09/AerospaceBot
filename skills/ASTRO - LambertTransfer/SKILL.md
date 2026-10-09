---
name: ASTRO - LambertTransfer
description: >-
  Run the Lambert-transfer program and report its printed velocities, conic,
  and PNG. Use when the user wants a single-revolution two-body transfer
  between two position vectors. Do not redraw the plot or recompute the
  numbers by hand.
---

# ASTRO - LambertTransfer

Use this skill for one single-revolution Lambert transfer. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The universal-variable residual uses `lambert_geometric_parameter`, the Stumpff records, `lambert_y_parameter`, and `lambert_time_of_flight`. Endpoint velocities use `lagrange_f`, `lagrange_g`, `lagrange_gdot`, and `lambert_velocity_from_lagrange`. The conic uses `semimajor_axis_from_state`, `eccentricity_from_energy`, and `parameter_from_angular_momentum`.

A Hohmann coast between two circular radii stays on `ASTRO - HohmannTransfer`. Multi-revolution transfers are not this program.

## When to run

1. Use this skill when the user gives two position vectors and a time of flight.
2. Components are meters in one inertial frame. `--tof` is seconds.
3. `--way` is `short` unless the user asks for the long way. Short is the angle at most \(\pi\).
4. Pass `--mu`, or omit it for Earth \(\mu=g_0 R_0^2\). Pass `--R0` only when the user gives a planetary radius and no \(\mu\).
5. Pass `--v1circ` or `--v2circ` only when the user gives a parking circular speed.
6. Do not invent a position, a time, or a gravitational parameter.

## Flags

Run:

```text
python "skills/ASTRO - LambertTransfer/lambert_transfer.py" --r1x <m> --r1y <m> --r1z <m> --r2x <m> --r2y <m> --r2z <m> --tof <s> [--mu <m3/s2>] [--R0 <m>] [--way <short|long>] [--v1circ <m/s>] [--v2circ <m/s>] [--out <png>] [--html]
```

Pass **only** flags the user supplied.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r1x` | First position, x | m | Required |
| `--r1y` | First position, y | m | Required |
| `--r1z` | First position, z | m | Required |
| `--r2x` | Second position, x | m | Required |
| `--r2y` | Second position, y | m | Required |
| `--r2z` | Second position, z | m | Required |
| `--tof` | Time of flight | s | Required |
| `--mu` | Gravitational parameter | m³/s² | Optional. Omit for Earth. |
| `--R0` | Planetary radius for \(\mu=g_0 R_0^2\) | m | Optional |
| `--way` | `short` or `long` | — | Optional. Default `short`. |
| `--v1circ` | Parking circular speed at the first radius | m/s | Optional |
| `--v2circ` | Parking circular speed at the second radius | m/s | Optional |
| `--out` | PNG path | — | Optional |
| `--html` | Also write the 3D HTML viewer beside the PNG | — | Optional |

Every successful run writes one PNG. The plot title is `Lambert transfer`. `--html` writes a viewer next to that PNG. The page uses the same planet, axes, orbit ribbon, legend, and playback controls as `ASTRO - HohmannTransfer`, and it embeds its scene so it opens from disk.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. It is the first frame of the viewer: the planet, the orbits, and the spacecraft where playback starts, at the same camera angles.
3. If `viewer:` is printed, include that HTML file as well.
4. Report `v1x_m_s`, `v1y_m_s`, `v1z_m_s`, `v2x_m_s`, `v2y_m_s`, and `v2z_m_s`.
5. Report `a_m`, `e`, `p_m`, `energy_m2_s2`, and `energy_class`.
6. If parking speeds were passed, report `dv1_m_s` and `dv2_m_s`. The circular velocity lies in the transfer plane. The viewer then shows the departure orbit, the departure burn, the transfer coast, the arrival burn, and the arrival orbit. Through each burn the spacecraft stays at the burn point and the drawn orbit moves from the velocity before the burn to the velocity after it.
7. Report `mu_source`.
8. A 180 degree chord uses \(p=2 r_1 r_2/(r_1+r_2)\). Its plane normal is \(\mathbf{r}_1\times\hat{\mathbf{z}}\), or \(\mathbf{r}_1\times\hat{\mathbf{y}}\) when those are parallel. The long way flips that normal.
9. If a position, the time of flight, or a usable gravitational parameter is missing, or the time is outside one revolution, say so. Do not fill it in.

Interactive lab offer: before running this program for a new Earth-orbit transfer, station-keeping, rendezvous, or ops design or sizing thread, ask once whether the user wants `ASTRO - OrbitDesignLab` (interactive HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.
