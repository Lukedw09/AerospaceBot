---
name: STRUCT - CombinedStressMohr
description: >-
  Run the combined-stress Mohr program and report its principals, max shear,
  and PNG. Use when the user already has bending plus torsion, or σx and τxy,
  and wants the plane-stress principals. Do not redraw the plot or recompute
  the numbers by hand.
---

# STRUCT - CombinedStressMohr

Use this skill when a shaft, spar, or boom has both bending and torsion. Pure bending stays on `STRUCT - BeamBendingStress`. Pure torsion stays on `STRUCT - CircularShaftTorsion`. This skill is the combined case those programs omit. Run it once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

With \(\sigma_y=0\),

\[
\sigma_{1,2}=\frac{\sigma_x}{2}\pm\sqrt{\left(\frac{\sigma_x}{2}\right)^2+\tau_{xy}^2}
\]

`principal_stress_max`, `principal_stress_min`, `mohr_center`, and `mohr_radius` (`max_shear_from_mohr`) are those quantities. Plastic Mohr is omitted.

## When to run

1. Use this skill for the extreme principals and in-plane max shear of one plane-stress point that already combines bending and torsion.
2. Convert stresses to pascals, moments to N·m, and lengths to metres. State the converted units. Do not invent a stress or a load.
3. Pass `--sigma` and `--tau` together, or the load path: `--moment` with `--section-modulus` or with `--inertia` and `--fiber`, plus `--torque` with `--radius` or `--diameter` (optional inner size, or `--polar`). Do not mix the two paths.
4. Pass `--allowable` only when the user gave an allowable normal stress. Margin uses \(\max(|\sigma_1|,|\sigma_2|)\).
5. Pass `--out` only when the user wants a chosen PNG path. The program still writes its default Mohr circle.

## Flags

Run:

```text
python "skills/STRUCT - CombinedStressMohr/combined_stress_mohr.py" [--sigma <Pa> --tau <Pa>] [--moment <N*m> (--section-modulus <m^3> | --inertia <m^4> --fiber <m>) --torque <N*m> (--radius <m> | --diameter <m>) [--polar <m^4>]] [--allowable <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--sigma` | Normal stress \(\sigma_x\) | Pa | Optional; required with `--tau` on the stress path |
| `--tau` | Shear stress \(\tau_{xy}\) | Pa | Optional; required with `--sigma` on the stress path |
| `--moment` | Bending moment | N·m | Optional; required on the load path |
| `--section-modulus` | Elastic section modulus | m³, \(> 0\) | Optional; one bending section API |
| `--inertia` | Second moment of area | m⁴, \(> 0\) | Optional; pair with `--fiber` |
| `--fiber` | Extreme-fiber distance | m, \(> 0\) | Optional; pair with `--inertia` |
| `--torque` | Torque | N·m | Optional; required on the load path |
| `--polar` | Polar second moment | m⁴, \(> 0\) | Optional |
| `--radius` | Outer radius | m, \(> 0\) | Optional; or `--diameter` |
| `--diameter` | Outer diameter | m, \(> 0\) | Optional; or `--radius` |
| `--inner-radius` | Bore radius | m | Optional |
| `--inner-diameter` | Bore diameter | m | Optional |
| `--allowable` | Allowable normal stress | Pa, \(> 0\) | Optional |
| `--out` | PNG path | file | Optional |
