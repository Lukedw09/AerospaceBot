---
name: ASTRO - SphereOfInfluence
description: >-
  Run the sphere-of-influence program and report its printed results and PNG.
  Use when the user wants the Laplace / patched-conic radius where a third
  body's gravity dominates relative to a central body, that radius in central
  body radii, whether a satellite about the third body is inside or outside,
  or a figure of the two bodies and their spheres of influence. Do not redraw
  the figure or recompute the numbers by hand.
---

# ASTRO - SphereOfInfluence

Use this skill for the classical Laplace sphere of influence of a third body relative to a central body. Run the program once; quote its stdout and include its PNG unless `--no-plot` was used. Do not redraw the figure or recompute the numbers by hand.

Assumptions (also printed by the program): inverse-square point masses and the isotropic Laplace radius `sphere_of_influence_radius`

\[
r_{\mathrm{SOI}} = D\left(\frac{\mu_3}{\mu}\right)^{2/5}
\]

with \(D\) the center-to-center distance. Masses use `gravitational_parameter` \(\mu = G M\) with NIST CODATA 2022 \(G\), or `sphere_of_influence_radius_from_mass`. Central-body radii use `sphere_of_influence_in_central_radii` \(r_{\mathrm{SOI}}/R_0\). The reciprocal central-body sphere relative to the third body is the same record with the mus swapped. Angle-dependent Tisserand corrections are omitted. \(r_{\mathrm{SOI}}\) is measured from the third-body center. An omitted central \(\mu\) uses \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\).

## When to run

1. A central body and a third body: pass `--R3`, `--D`, and either `--mu3` or `--mass3`. Omit `--R0` and `--mu` for the Earth default, or pass `--R0` with `--mu` or `--mass`.
2. Masses instead of gravitational parameters: pass `--mass` and/or `--mass3`. Do not pass `--mu` with `--mass`, or `--mu3` with `--mass3`.
3. Optional satellite check: pass `--rsat` as the distance from the third-body center. Do not invent a satellite radius.
4. Optional figure: omit `--no-plot` for the PNG. Pass `--no-plot` only when the user does not want the figure.
5. Convert inputs to SI before the call (m, m³/s², kg). State the converted units in the reply. Do not invent a missing radius, distance, \(\mu\), or mass.

## Flags

Run:

```text
python "skills/ASTRO - SphereOfInfluence/sphere_of_influence.py" --R3 <m> --D <m> (--mu3 <m^3/s^2> | --mass3 <kg>) [--R0 <m>] [--mu <m^3/s^2> | --mass <kg>] [--rsat <m>] [--out <png>] [--no-plot]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--R0` | Central-body radius | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--mu` | Central-body gravitational parameter | m³/s², \(> 0\) | Optional with `--mass` omitted. Default \(\mu = g_0 R_0^{2}\) |
| `--mass` | Central-body mass; \(\mu = G M\) | kg, \(> 0\) | Optional. Not with `--mu` |
| `--R3` | Third-body radius | m, \(> 0\) | Required |
| `--mu3` | Third-body gravitational parameter | m³/s², \(> 0\) | Or `--mass3` |
| `--mass3` | Third-body mass; \(\mu_3 = G M_3\) | kg, \(> 0\) | Or `--mu3` |
| `--D` | Distance between the two centers | m, \(> R_0 + R_3\) | Required |
| `--rsat` | Satellite radius from the third-body center | m, \(\ge R_3\) | Optional |
| `--out` | PNG path | — | Optional |
| `--no-plot` | Skip the PNG | — | Optional |

A bare length is metres. Kilometres use `1 km = 1000 m`. A bare mass is kilograms. \(\mu_3\) must be smaller than the central \(\mu\).

Every successful run without `--no-plot` writes one PNG. The plot title is `Sphere of influence`. The central body is at the origin. The third body sits at \(x = D\). Dashed and dotted circles are the third-body and central-body Laplace spheres. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG when `graph:` is printed. Do not draw a second figure.
3. Report `R0_m`, `R0_source`, `g0_m_s2`, `G_m3_kg_s2`, `mu_m3_s2`, and `mu_source`. `default` means the Earth radius. `g0_R0_sq` means \(\mu = g_0 R_0^{2}\). `mass` means \(\mu = G M\). `input` means the user supplied \(\mu\) or \(R_0\).
4. Report `R3_m`, `mu3_m3_s2`, `mu3_source`, and `D_m`. Report `M_kg` / `M3_kg` when masses were used.
5. Report `r_SOI_m` and `r_SOI_central_radii`. Those are the third-body sphere and that radius in central-body radii.
6. Report `r_SOI_central_m`, the reciprocal central-body sphere relative to the third body.
7. Report `satellite_location` when `--rsat` was passed: `inside` or `outside` the third-body sphere.
8. Repeat `warning` when it is printed.
9. If the third-body radius, distance, or third-body \(\mu\)/mass is missing, say so. Do not fill it in.
