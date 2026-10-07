---
name: ASTRO - OrbitInsertionFromBurnout
description: >-
  Run the orbit-insertion program and report its printed elements,
  circularization delta-v, and HTML. Use when the user gives a burnout
  radius, speed, and flight-path angle and wants a parking-orbit check and an
  impulsive circularization burn. Do not recompute the elements by hand.
---

# ASTRO - OrbitInsertionFromBurnout

Use this skill to turn a burnout state into a coast and a circularization burn. Run the program once; quote its stdout. Give `viewer:` as a markdown link. This skill does not write a PNG.

Assumptions (also printed): two-body coast, no drag. Specific energy is \(v^2/2-\mu/r\). Angular momentum is \(r v\cos\gamma\). Default \(\mu=g_0 R_0^2\) with \(R_0=6.3742\times 10^6\,\mathrm{m}\) and \(g_0=9.80665\). Periapsis altitude below 120 km is an atmosphere intersection. Circularization uses `circularization_delta_v` at apoapsis, or at burnout when the orbit is already nearly circular. A non-negative energy, or a radial burnout with no area, is not a closed parking orbit.

## When to run

1. Use this skill when burnout radius, speed, and flight-path angle are known, including `r_bo_m`, `V_bo_m_s`, and `gamma_bo_rad` from `ROCKET - MultiStageAscent`.
2. Pass `--radius` and `--mu` equal to the body used for that ascent. The ascent default radius is not this program's default \(R_0\).
3. Angles are radians. A flight-path angle is from the local horizontal.
4. Do not treat `atmosphere_intersection: yes` as a parking orbit.

## Flags

Run:

```text
python "skills/ASTRO - OrbitInsertionFromBurnout/orbit_insertion_from_burnout.py" --r <m> --v <m/s> --gamma <rad> [--mu <m^3/s^2>] [--radius <m>] [--out <html>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r` | Burnout radius from the center | m | Required |
| `--v` | Burnout speed | m/s | Required |
| `--gamma` | Burnout flight-path angle from the local horizontal | rad | Required |
| `--mu` | Gravitational parameter | m^3/s^2 | Optional |
| `--radius` | Body radius for periapsis altitude | m | Optional |
| `--out` | HTML path. A `.png` path is written as the HTML beside it | — | Optional |
| `--open` | Open the HTML viewer | — | Optional |

Every successful run writes a self-contained HTML viewer and no PNG. The coast is drawn only outside the planet. The viewer then raises that arc into a circle at the circularization radius. `viewer:` is the HTML. A burnout that is not a closed orbit still writes the viewer and exits 0.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Give `viewer:` as a markdown link.
3. Report `closed_orbit`, `e`, `hp_m`, `ha_m`, `atmosphere_intersection`, and `dv_circ_m_s` when they are printed.
4. A closed orbit with `atmosphere_intersection: no` is the parking orbit. Pass `dv_circ_m_s` back to `ROCKET - LeoDeltaVBudget` as `--circ` on a later pass.
5. After a parking orbit, `ASTRO - HohmannTransfer`, `ASTRO - MultiBurnLeoRaise`, `ROCKET - KickStageFeasibility`, and `ASTRO - VacuumPropellantMass` are the in-space follow-ons when the user asks for them.
6. If radius, speed, or flight-path angle is missing, say so. Do not fill them in.
