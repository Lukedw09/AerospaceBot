---
name: AERO - FlatPlateBoundaryLayer
description: >-
  Run the flat-plate boundary-layer program and report its printed friction
  coefficients and PNG. Use when the user wants laminar Blasius or
  one-seventh-power turbulent skin friction on a smooth zero-incidence
  plate. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - FlatPlateBoundaryLayer

Use this skill for a smooth flat plate at zero incidence. The user must choose laminar or turbulent. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Laminar records are `blasius_local_skin_friction`, `blasius_plate_friction`, and `blasius_thickness_ratio`. Turbulent records are `turbulent_local_skin_friction_seventh` and `turbulent_plate_friction_seventh`. Reynolds number reuses `reynolds_number` or `reynolds_number_kinematic`. There is no transition model.

## When to run

1. Use this skill when the user wants local or plate skin friction, an optional friction drag, or the laminar thickness ratio.
2. `--law` is required. Do not choose laminar or turbulent for the user.
3. Pass `--re`, or pass `--rho`, `--V`, `--L`, and either `--mu` or `--nu`. Do not invent a Reynolds number.
4. One Reynolds number is one run. Do not sweep.
5. `--span` is the plate span for one wetted side. Omit it unless the user wants a force. It needs `--rho`, `--V`, and `--L`. The chord is `--L`.

## Flags

Run:

```text
python "skills/AERO - FlatPlateBoundaryLayer/flat_plate_boundary_layer.py" --law <laminar|turbulent> [--re <Re>] [--rho <kg/m3>] [--V <m/s>] [--L <m>] [--mu <Pa-s>] [--nu <m2/s>] [--span <m>] [--out <png>]
```

Pass **only** flags the user supplied, plus `--law` when the user named the regime.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--law` | `laminar` or `turbulent` | — | Required |
| `--re` | Reynolds number based on plate length | dimensionless, \(> 0\) | Optional; required without density, speed, and length |
| `--rho` | Density | kg/m³ | Optional; required with `--V` and `--L` when `--re` is omitted |
| `--V` | Freestream speed | m/s | Optional; required with `--rho` and `--L` when `--re` is omitted |
| `--L` | Plate length (chord) | m | Optional; required with `--rho` and `--V` when `--re` is omitted |
| `--mu` | Dynamic viscosity | Pa·s | Optional. Use with `--rho`. |
| `--nu` | Kinematic viscosity | m²/s | Optional. Use instead of `--rho` and `--mu`. |
| `--span` | Span of one wetted side | m | Optional |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Flat-plate skin friction`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The curve is \(C_f\) versus Reynolds number for the chosen law. The square marks the given Reynolds number.
3. Report `law`, `Re_L`, `cf`, and `Cf`.
4. For laminar flow, report `delta_over_L`. Turbulent thickness is not printed.
5. If `--span` was passed and dynamic pressure can be formed, report `S_m2` and `Df_N`. The area is one wetted side, \(S=L\times\mathrm{span}\).
6. Report `range_note` when the Reynolds number is outside the range stated for that law.
7. If the law or the Reynolds number is missing, say so. Do not fill it in.
