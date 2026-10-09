---
name: STRUCT - CircularShaftTorsion
description: >-
  Run the circular-shaft torsion program and report its printed results and
  optional PNG. Use when the user wants elastic torsion of a solid or hollow
  circular shaft, torque tube, actuator shaft, or round boom in twist: polar
  second moment, max shear stress, optional angle of twist from length and
  shear modulus, and optional margin of safety from an allowable shear. Do not
  redraw the plot or recompute the numbers by hand.
---

# STRUCT - CircularShaftTorsion

Use this skill for elastic torsion of a solid or concentrically hollow circular shaft (torque tube, actuator shaft, round boom in twist). Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Polar second moment is `polar_second_moment_solid` when the bore is omitted:

\[
J = \frac{\pi}{2} R_o^{4} = \frac{\pi}{32} D_o^{4}
\]

or `polar_second_moment_hollow` when an inner size is given:

\[
J = \frac{\pi}{2}\bigl(R_o^{4}-R_i^{4}\bigr) = \frac{\pi}{32}\bigl(D_o^{4}-D_i^{4}\bigr)
\]

Max shear stress is `circular_shaft_shear` at the outer fiber, \(\tau_{\max}=T R_o/J\). Angle of twist is `circular_shaft_twist`, \(\theta=T L/(G J)\), only when both length and shear modulus are given. Optional margin of safety is `margin_of_safety`, \(\mathrm{MS}=S_{\mathrm{allow}}/\tau_{\max}-1\), with max shear as the design stress. There is no bending, open thin-wall warping, or plastic torsion in this skill.

## When to run

1. Use this skill when the user wants elastic torsion stress (and optional twist or margin) of a circular shaft, torque tube, actuator shaft, or round boom.
2. Convert inputs to SI before the call (N·m, m, Pa). State the converted units in the reply. Do not invent torque or outer size.
3. Pass `--torque`. Pass exactly one outer size API: `--radius`, or `--diameter`. For a hollow shaft, pass the matching inner flag (`--inner-radius` with `--radius`, or `--inner-diameter` with `--diameter`). Omit the inner flag for a solid shaft. Do not mix radius and diameter flags.
4. Pass both `--length` and `--G` only when the user wants angle of twist. Do not pass one without the other.
5. Pass `--allowable` only when the user gave an allowable shear stress for margin of safety.
6. Pass `--out` only when the user wants the PNG of max shear versus torque for the fixed section. Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for non-circular sections, open thin-wall warping, or plastic torsion. Combined bending-plus-torsion principals belong to `STRUCT - CombinedStressMohr`.

## Flags

Run:

```text
python "skills/STRUCT - CircularShaftTorsion/circular_shaft_torsion.py" --torque <N*m> (--radius <m> [--inner-radius <m>] | --diameter <m> [--inner-diameter <m>]) [--length <m> --G <Pa>] [--allowable <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--torque` | Torque \(T\) | N·m, \(> 0\) | Required |
| `--radius` | Outer radius \(R_o\) | m, \(> 0\) | One of `--radius` or `--diameter` |
| `--diameter` | Outer diameter \(D_o\) | m, \(> 0\) | One of `--radius` or `--diameter` |
| `--inner-radius` | Inner radius \(R_i\) (hollow; radius API) | m, \(> 0\), \(< R_o\) | Optional with `--radius` |
| `--inner-diameter` | Inner diameter \(D_i\) (hollow; diameter API) | m, \(> 0\), \(< D_o\) | Optional with `--diameter` |
| `--length` | Shaft length \(L\) | m, \(> 0\) | With `--G` for twist |
| `--G` | Shear modulus \(G\) | Pa, \(> 0\) | With `--length` for twist |
| `--allowable` | Allowable shear stress \(S_{\mathrm{allow}}\) | Pa, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare torque is N·m. Torque in N·mm uses `1 N·mm = 0.001 N·m`. Torque in lbf·in uses `1 lbf·in = 0.1129848290276167 N·m`. Length in inches uses `1 in = 0.0254 m`. Stress or modulus in psi uses `1 psi = 6894.757293168361 Pa`. Stress or modulus in MPa uses `1 MPa = 1e6 Pa`.

When `--out` is passed, the program writes one PNG. The plot title is `Circular shaft torsion`. The curve is \(\tau_{\max}=T R_o/J\) versus torque for the fixed section. The square is the operating point. A dashed horizontal line is the allowable when `--allowable` was passed. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `T_N_m`, `Ro_m`, `J_m4`, `tau_max_Pa`, `section`, and `size_mode`. `section` is `solid` or `hollow`. `size_mode` is `radius` or `diameter`.
4. Report `Ri_m` when it is printed (hollow path).
5. Report `G_Pa`, `L_m`, and `theta_rad` when they are printed (twist path).
6. Report `allowable_Pa` and `margin_of_safety` when they are printed. A margin of 0 means the max shear equals the allowable. A negative margin means the stress is above the allowable.
7. If torque or outer size is missing, say so. Do not fill them in.
