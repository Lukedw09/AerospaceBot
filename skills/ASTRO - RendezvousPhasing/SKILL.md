---
name: ASTRO - RendezvousPhasing
description: >-
  Run the rendezvous-phasing program and report its printed results and
  optional PNG. Use when the user wants the phasing ellipse, wait, and
  impulsive delta-v that close a phase angle between two vehicles already in
  the same circular orbit, in an integer number of chaser revolutions. Do not
  redraw the plot or recompute the numbers by hand.
---

# ASTRO - RendezvousPhasing

Use this skill for coplanar phasing in one circular orbit. The chaser leaves that circle on an ellipse, completes an integer number of revolutions, and returns to the same circle at the target. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The wait is `phasing_wait_catch` when the target is ahead and `phasing_wait_loiter` when the chaser is ahead. The phasing semi-major axis is `phasing_semimajor_from_period`. Each burn is `phasing_delta_v`, the vis-viva difference at the shared radius. The two burns are equal, so the total impulse is twice one burn.

Hand each burn, or the total, to `ASTRO - VacuumPropellantMass` when the user wants propellant. A transfer between two different circular radii stays on `ASTRO - HohmannTransfer`. Terminal relative motion stays on `ASTRO - RelativeOrbitClohessyWiltshire`.

## When to run

1. Use this skill when the user wants the phasing orbit, wait, and impulsive delta-v that close a phase angle in a shared circular orbit.
2. Convert radii to metres, altitude to metres, phase angle to radians, and \(\mu\) to m³/s². State the converted units in the reply. Do not invent a radius, a phase angle, or \(\mu\).
3. Pass the shared orbit as `--radius` or `--alt`, or pass `--r-target` and `--r-chaser` (or the altitude pair). If both vehicles are named and the radii differ, stop: this skill does not change orbit radius.
4. Pass `--phase` and `--lead` (`target` if the target is ahead of the chaser, `chaser` if the chaser is ahead).
5. Pass `--revs` only when the user asked for a number of chaser revolutions other than 1.
6. Pass `--mu` only when the user gave a gravitational parameter. Otherwise leave the Earth default \(g_0 R_0^{2}\).
7. Pass `--out` only when the user wants the top-down PNG. Do not invent a plot path when they did not ask for a figure.

## Flags

Run:

```text
python "skills/ASTRO - RendezvousPhasing/rendezvous_phasing.py" (--radius <m> | --alt <m> | --r-target <m> --r-chaser <m> | --alt-target <m> --alt-chaser <m>) --phase <rad> --lead <target|chaser> [--revs <N>] [--mu <m^3/s^2>] [--R0 <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--radius` | Shared circular radius | m, \(> 0\) | One orbit specification |
| `--alt` | Shared altitude above `--R0` | m, \(\ge 0\) | One orbit specification |
| `--r-target` | Target circular radius | m, \(> 0\) | With `--r-chaser`, equal to it |
| `--r-chaser` | Chaser circular radius | m, \(> 0\) | With `--r-target`, equal to it |
| `--alt-target` | Target altitude | m, \(\ge 0\) | With `--alt-chaser` |
| `--alt-chaser` | Chaser altitude | m, \(\ge 0\) | With `--alt-target` |
| `--phase` | Phase angle to close | rad, \(> 0\) | Required |
| `--lead` | Who is ahead: `target` or `chaser` | — | Required |
| `--revs` | Chaser revolutions on the phasing ellipse | integer, \(\ge 1\) | Optional. Default 1 |
| `--mu` | Gravitational parameter | m³/s², \(> 0\) | Optional. Default Earth \(g_0 R_0^{2}\) |
| `--R0` | Planet radius used with altitude | m, \(> 0\) | Optional. Default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare length is metres. Kilometres use `1 km = 1000 m`. A phase angle in degrees uses \(\pi/180\).

When `--out` is passed, the program writes one PNG. The plot title is `Rendezvous phasing`. The view is down the orbit normal. The circle is the shared orbit and the ellipse is the phasing orbit, with the planet at the focus. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `lead`, `phase_rad`, `revs`, `r_m`, `a_m`, `period_s`, `wait_s`, `rp_m`, `ra_m`, `dv_in_m_s`, `dv_out_m_s`, and `dv_total_m_s`.
4. The two burns are equal. `dv_total_m_s` is their sum. Pass one burn or the total to `ASTRO - VacuumPropellantMass` only as the user directs.
5. Report `warning` when it is printed. Periapsis is then inside the planet radius: `--R0` when that flag was passed, otherwise the catalogue Earth radius.
6. If the orbit, the phase angle, or who is ahead is missing, say so. Do not fill them in.
