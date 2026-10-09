---
name: ASTRO - AerodynamicDragDeltaV
description: >-
  Run the drag delta-v program and report its printed results and optional PNG.
  Use when the user wants drag acceleration and delta-v over one circular
  revolution at constant density, from altitude, mass, drag coefficient, and
  area. Density comes from altitude unless the user overrides it. The printed
  delta-v is one named contribution to ASTRO - VacuumPropellantMass. Do not
  recompute the numbers by hand.
---

# ASTRO - AerodynamicDragDeltaV

Use this skill for the drag delta-v of one circular revolution at constant density. Run the program once; quote its stdout and include the PNG when `graph:` is printed.

Drag is the catalogue `drag_force`, \(D = C_D q A\), with \(q = \tfrac12\rho V^{2}\). Delta-v per revolution is `drag_delta_v_per_revolution`, \((D/m)\) times the orbital period. Speed is `circular_orbit_velocity` and period is `orbital_period`, both with Earth \(\mu = g_0 R_0^{2}\) and \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\).

Density is `ATMOS - Standard1976` at or below 86 km and `ATMOS - DensityAbove86km` above 86 km. `--rho` is an override.

The printed `dv_per_rev_m_s` is one named piece the user may pass to `ASTRO - VacuumPropellantMass`. It is not a lifetime integral.

## When to run

1. Use this skill when the user wants drag acceleration or delta-v per revolution on a circular orbit.
2. Convert altitude to metres, mass to kilograms, and area to square metres. Do not invent mass, \(C_D\), area, altitude, or a density override.
3. Pass `--alt`, `--mass`, `--cd`, and `--area`. Pass `--rho` only when the user supplied an override.
4. Pass `--out` only when the user wants delta-v per revolution versus altitude. The curve is the 1976 thermosphere model from 90 km to 500 km. The square is this run, and it lies on that curve only when `--rho` was omitted and the altitude is inside that range.

## Flags

```text
python "skills/ASTRO - AerodynamicDragDeltaV/aerodynamic_drag_delta_v.py" --alt <m> --mass <kg> --cd <1> --area <m^2> [--rho <kg/m^3>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude | m, \(\ge 0\) | Required |
| `--mass` | Spacecraft mass | kg, \(> 0\) | Required |
| `--cd` | Drag coefficient | dimensionless, \(> 0\) | Required |
| `--area` | Drag reference area | m², \(> 0\) | Required |
| `--rho` | Density override | kg/m³, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional |

The plot title is `Drag delta-v per revolution`.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `rho_kg_m3`, `density_source`, `V_m_s`, `period_s`, `D_N`, `a_m_s2`, and `dv_per_rev_m_s`.
4. If mass, \(C_D\), area, or altitude is missing, say so. Do not fill them in.

Interactive lab offer: before running this program for a new Earth-orbit transfer, station-keeping, rendezvous, or ops design or sizing thread, ask once whether the user wants `ASTRO - OrbitDesignLab` (interactive HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.
