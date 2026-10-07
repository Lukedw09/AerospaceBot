---
name: STRUCT - ThinWallPressureVessel
description: >-
  Run the thin-wall pressure-vessel program and report its printed results and
  optional PNG. Use when the user wants membrane hoop and longitudinal stress
  in a closed cylinder, or membrane stress in a sphere, from pressure, radius,
  and wall thickness, or the wall that puts the governing stress on an
  allowable. Do not redraw the plot or recompute the numbers by hand.
---

# STRUCT - ThinWallPressureVessel

Use this skill for thin-wall membrane stress in a closed circular cylinder or a sphere. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Cylinder hoop stress is `cylinder_hoop_stress`, \(\sigma_h = p R/t\). Cylinder longitudinal stress is `cylinder_longitudinal_stress`, \(\sigma_l = p R/(2t)\). Sphere membrane stress is `sphere_membrane_stress`, \(\sigma = p R/(2t)\). The wall that puts that governing stress on an allowable (margin of safety zero) is `thin_wall_hoop_thickness` for a cylinder and `thin_wall_membrane_thickness` for a sphere. When a wall and an allowable are both supplied, margin of safety is `margin_of_safety` on the governing stress.

This is a general thin shell. Motor-case samples stay on `ROCKET - ChamberVolumeAndCaseHoopStress`. Tank mass stays on `ROCKET - TankStructureMass`.

## When to run

1. Use this skill when the user wants thin-wall hoop or longitudinal stress, sphere membrane stress, margin of safety, or the wall thickness for zero margin.
2. Convert inputs to SI before the call (Pa, m). State the converted units in the reply. Do not invent pressure, radius, thickness, or allowable stress.
3. Pass `--p`, `--radius`, and `--shape` (`cylinder` or `sphere`).
4. Pass `--thickness` to report stress. Pass `--allowable` to report the zero-margin thickness. Pass both to report stress and margin of safety for that wall.
5. Pass `--out` only when the user wants the PNG. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for thick-wall Lamé solutions, openings, welds, buckling, or a motor case that belongs on the chamber-hoop skill.

## Flags

Run:

```text
python "skills/STRUCT - ThinWallPressureVessel/thin_wall_pressure_vessel.py" --p <Pa> --radius <m> --shape <cylinder|sphere> [--thickness <m>] [--allowable <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--p` | Internal pressure \(p\) | Pa, \(> 0\) | Required |
| `--radius` | Mid-wall radius \(R\) | m, \(> 0\) | Required |
| `--shape` | `cylinder` or `sphere` | — | Required |
| `--thickness` | Wall thickness \(t\) | m, \(> 0\) | Optional. Required for a stress report unless `--allowable` sizes the wall |
| `--allowable` | Allowable membrane stress | Pa, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare length is metres. Pressure in MPa uses `1 MPa = 1e6 Pa`. Pressure in psi uses `1 psi = 6894.757293168361 Pa`.

When `--out` is passed, the program writes one PNG. The plot title is `Thin-wall pressure vessel`. With a wall thickness, the curve is governing stress versus radius. With only an allowable, the curve is the zero-margin thickness versus radius. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `shape`, `p_Pa`, `R_m`, and `governing`.
4. Report `t_m`, `sigma_hoop_Pa`, and `sigma_long_Pa` for a cylinder. Report `t_m` and `sigma_Pa` for a sphere.
5. Report `allowable_Pa`, `t_zero_ms_m`, and `margin_of_safety` when they are printed. A margin of 0 means the governing stress equals the allowable.
6. If pressure, radius, shape, or both thickness and allowable are missing, say so. Do not fill them in.
