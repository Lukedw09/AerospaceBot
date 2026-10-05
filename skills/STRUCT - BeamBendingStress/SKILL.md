---
name: STRUCT - BeamBendingStress
description: >-
  Run the pure beam-bending program and report its printed results and optional
  PNG. Use when the user wants extreme-fiber bending stress of a beam, spar,
  longeron, or boom from bending moment and either section modulus or second
  moment of area with fiber distance, optionally with margin of safety from an
  allowable stress. Do not redraw the plot or recompute the numbers by hand.
---

# STRUCT - BeamBendingStress

Use this skill for elastic pure bending of a beam, spar, longeron, or boom. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Extreme-fiber bending stress is `beam_bending_stress` when section modulus is given:

\[
\sigma = \frac{M}{Z}
\]

or `beam_bending_stress_inertia` when second moment and fiber distance are given:

\[
\sigma = \frac{M c}{I}
\]

Section modulus from inertia is `section_modulus`, \(Z = I/c\). Optional margin of safety is `margin_of_safety`, \(\mathrm{MS} = S_{\mathrm{allow}}/\sigma - 1\), with bending stress as the design stress. There is no axial force, shear, or torsion in this skill.

## When to run

1. Use this skill when the user wants pure bending stress of a beam, spar, longeron, or boom, the section modulus from \(I\) and \(c\), or margin of safety against an allowable stress.
2. Convert inputs to SI before the call (N·m, m³, m⁴, m, Pa). State the converted units in the reply. Do not invent moment, section modulus, inertia, fiber distance, or allowable stress.
3. Pass `--moment`. Pass exactly one of `--section-modulus`, or both `--inertia` and `--fiber`. Do not pass `--section-modulus` with `--inertia` or `--fiber`.
4. Pass `--allowable` only when the user gave an allowable stress for margin of safety.
5. Pass `--out` only when the user wants the PNG of stress versus moment for the fixed section. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for axial-plus-bending, shear flow, torsion, buckling, or plastic section modulus.

## Flags

Run:

```text
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --moment <N*m> (--section-modulus <m^3> | --inertia <m^4> --fiber <m>) [--allowable <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--moment` | Bending moment \(M\) | N·m, \(> 0\) | Required |
| `--section-modulus` | Elastic section modulus \(Z\) | m³, \(> 0\) | One of `--section-modulus` or `--inertia` with `--fiber` |
| `--inertia` | Second moment of area \(I\) | m⁴, \(> 0\) | With `--fiber`, not with `--section-modulus` |
| `--fiber` | Distance \(c\) from neutral axis to extreme fiber | m, \(> 0\) | With `--inertia`, not with `--section-modulus` |
| `--allowable` | Allowable stress \(S_{\mathrm{allow}}\) | Pa, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare moment is N·m. Moment in N·mm uses `1 N·mm = 0.001 N·m`. Moment in lbf·in uses `1 lbf·in = 0.1129848290276167 N·m`. Length in inches uses `1 in = 0.0254 m`, so \(I\) in in⁴ uses `(0.0254)^4` m⁴ and \(Z\) in in³ uses `(0.0254)^3` m³. Stress in psi uses `1 psi = 6894.757293168361 Pa`. Stress in MPa uses `1 MPa = 1e6 Pa`.

When `--out` is passed, the program writes one PNG. The plot title is `Beam bending stress`. The curve is \(\sigma = M/Z\) versus moment for the fixed section. The square is the operating point. A dashed horizontal line is the allowable when `--allowable` was passed. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `M_N_m`, `Z_m3`, `sigma_Pa`, and `section_source`. `section_modulus` means \(Z\) was an input. `inertia` means \(Z = I/c\) from `--inertia` and `--fiber`.
4. Report `I_m4` and `c_m` when they are printed (inertia path).
5. Report `allowable_Pa` and `margin_of_safety` when they are printed. A margin of 0 means the bending stress equals the allowable. A negative margin means the stress is above the allowable.
6. If moment or a way to set the section is missing, say so. Do not fill them in.
