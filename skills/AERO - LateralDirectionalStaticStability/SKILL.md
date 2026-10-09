---
name: AERO - LateralDirectionalStaticStability
description: >-
  Run the lateral-directional static-stability program and report Cn_beta,
  Cl_beta, and the PNG. Use when the user wants weathercock and dihedral
  estimates, not the Dutch-roll oscillation. Do not redraw the plot or
  recompute the numbers by hand.
---

# AERO - LateralDirectionalStaticStability

Use this skill for the two static derivatives: weathercock \(C_{n\beta}\) from the vertical tail, and \(C_{l\beta}\) from unswept geometric dihedral. The Dutch-roll frequency and damping that consume those derivatives stay on `AERO - DutchRollEstimate`. Run this program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

\[
V_v=\frac{S_v l_v}{S b},\qquad C_{n\beta}=a_v V_v\eta,\qquad C_{l\beta}=-C_{L\alpha}\Gamma\frac{1+2\lambda}{6(1+\lambda)}
\]

`vertical_tail_volume`, `cn_beta_vertical_tail`, and `cl_beta_geometric_dihedral` are those estimates. \(\eta\) defaults to 1 only when it is omitted, which is the zero-attack factor in NACA Report 1049. Positive \(C_{n\beta}\) weathervanes. Negative \(C_{l\beta}\) is positive effective dihedral.

## When to run

1. Use this skill when the user wants \(C_{n\beta}\) and \(C_{l\beta}\), or a stability sign on values they already have.
2. Pass the estimate set `--span`, `--area`, `--cl-alpha`, `--sv`, `--lv`, `--av`, and `--gamma` in radians, or pass `--cn-beta` and `--cl-beta`. Do not mix the two paths. Do not invent a tail volume or a dihedral angle.
3. `--eta-v` is optional. Omit it to use 1 and read `eta_source: default_unity`. `--taper` defaults to 1 (rectangular).
4. Hand `Cn_beta_per_rad` and `Cl_beta_per_rad` to `AERO - DutchRollEstimate` only when the user also asks for the oscillation. That program still needs the other derivatives.
5. Do not use this skill for swept-wing charts, a fuselage contribution, or Dutch-roll damping.

## Flags

Run:

```text
python "skills/AERO - LateralDirectionalStaticStability/lateral_directional_static_stability.py" [--span <m> --area <m^2> --cl-alpha <1/rad> --sv <m^2> --lv <m> --av <1/rad> --gamma <rad>] [--cn-beta <1/rad> --cl-beta <1/rad>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--span` | Wing span \(b\) | m, \(> 0\) | Optional; required on the estimate path |
| `--area` | Wing area \(S\) | m², \(> 0\) | Optional; required on the estimate path |
| `--cl-alpha` | Wing lift-curve slope | 1/rad, \(> 0\) | Optional; required on the estimate path |
| `--sv` | Vertical-tail area | m², \(> 0\) | Optional; required on the estimate path |
| `--lv` | Vertical-tail length | m, \(> 0\) | Optional; required on the estimate path |
| `--av` | Vertical-tail lift-curve slope | 1/rad, \(> 0\) | Optional; required on the estimate path |
| `--gamma` | Geometric dihedral | rad | Optional; required on the estimate path |
| `--eta-v` | Tail dynamic-pressure ratio | dimensionless, \(> 0\) | Optional |
| `--taper` | Wing taper ratio | dimensionless, \(\ge 0\) | Optional |
| `--cn-beta` | Supplied \(C_{n\beta}\) | 1/rad | Optional; pair with `--cl-beta` |
| `--cl-beta` | Supplied \(C_{l\beta}\) | 1/rad | Optional; pair with `--cn-beta` |
| `--out` | PNG path | file | Optional |
