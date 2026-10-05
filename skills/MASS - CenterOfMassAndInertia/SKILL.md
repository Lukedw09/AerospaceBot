---
name: MASS - CenterOfMassAndInertia
description: >-
  Run the center-of-mass and inertia program and report its printed results and
  PNG. Use when the user wants total mass, center of mass, or the inertia tensor
  of a rigid assembly of point masses or uniform parts with stated CGs, optional
  own-CG principal inertias, and optional parallel-axis transfer. Do not redraw
  the plot or recompute the numbers by hand.
---

# MASS - CenterOfMassAndInertia

Use this skill for the balance and rigid-body mass properties of a collection of masses in one body frame. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Total mass is `total_mass`. Each part contributes `mass_first_moment` on each axis. The center of mass is `center_of_mass_coordinate` on each axis:

\[
m = \sum_i m_i,\qquad
\bar{x} = \frac{\sum_i m_i x_i}{m}
\]

and likewise for \(\bar{y}\) and \(\bar{z}\).

Point masses use `point_mass_moment` and `point_mass_product` about the system CG. Optional own-CG inertias use `parallel_axis_moment` and `parallel_axis_product` when that part’s parallel-axis flag is on (NASA TM X-1754):

\[
I_{xx} = I_{xx,\mathrm{cg}} + m(y^{2}+z^{2}),\qquad
P_{xy} = P_{xy,\mathrm{cg}} + m x y
\]

with \(x,y,z\) measured from the system CG. The printed inertia tensor places the moments on the diagonal and \(-P_{xy}\), \(-P_{xz}\), \(-P_{yz}\) off-diagonal. With `--about-origin`, the same sums are also reported about the user origin; `inertia_shift_to_cg` relates those two tensors when every part used parallel-axis transfer.

The assembly is rigid and non-rotating. There is no fuel slosh and no time-varying CG.

## When to run

1. Use this skill when the user wants total mass, center of mass, the inertia tensor about the CG, optionally about a user origin, or a PNG of the point masses and CG in the body frame.
2. Convert inputs to SI before the call (kg, m, kg·m²). State the converted units in the reply. Do not invent part masses, positions, or own inertias.
3. Pass one `--part` for each mass. A bare point mass is `m,x,y,z`. Own-CG principal inertias are `m,x,y,z,Ixx,Iyy,Izz`. Full own-CG products are `m,x,y,z,Ixx,Iyy,Izz,Ixy,Ixz,Iyz`. Append `,0` or `,1` to turn parallel-axis transfer off or on for that part (default on when inertias are given).
4. Pass `--about-origin` only when the user also wants the inertia tensor about the body-frame origin.
5. Pass `--out` only when the user wants a non-default PNG path. Every successful run writes one PNG.

## Flags

Run:

```text
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --part <m,x,y,z[,Ixx,Iyy,Izz[,Ixy,Ixz,Iyz]][,parallel]> [--part ...] [--about-origin] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--part` | One part: mass and CG position, optional own-CG inertias, optional parallel flag | kg, m, kg·m²; parallel is 0/1 | Required; repeat once per part |
| `--about-origin` | Also print inertia about the body-frame origin | — | Optional |
| `--out` | PNG path | — | Optional. Default is `center_of_mass_and_inertia.png` in this skill folder |

Mass in grams uses `1 g = 0.001 kg`. Length in inches uses `1 in = 0.0254 m`. Inertia in slug·ft² uses `1 slug·ft² = 1.3558179619 kg·m²`. Weight in newtons is not a mass; convert with \(m = W/g_0\) and \(g_0 = 9.80665\,\mathrm{m/s}^2\) only when the user clearly gave weight.

Every successful run writes one PNG. The plot title is `Center of mass and inertia`. Markers are the part CGs (size scales with mass) and the system CG (star).

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `m_kg`, `x_cg_m`, `y_cg_m`, `z_cg_m`, and the CG inertia components `Ixx_cg_kg_m2` through `Iyz_cg_kg_m2`.
4. Report the `tensor_cg_*` entries when they are printed. Off-diagonal entries are the negatives of the products of inertia.
5. Report `Ixx_O_kg_m2` through `Iyz_O_kg_m2` when `--about-origin` was used.
6. If any part mass or position is missing, say so. Do not fill them in.
