---
name: STRUCT - EulerColumnBuckling
description: >-
  Run the elastic Euler column-buckling program and report its printed results
  and optional PNG. Use when the user wants the critical buckling load of a
  concentrically loaded long column from Young's modulus, second moment of area,
  unsupported length, and end-fix factor K, optionally with area and compressive
  yield for critical stress, slenderness, and Euler-versus-yield. Do not redraw
  the plot or recompute the numbers by hand.
---

# STRUCT - EulerColumnBuckling

Use this skill for elastic Euler buckling of a straight, concentrically loaded, prismatic long column. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Critical load is `euler_critical_load`:

\[
P_{\mathrm{cr}} = \frac{\pi^{2} E I}{(K L)^{2}}
\]

Effective length is `effective_column_length`, \(L' = K L\). End-fixity coefficient is `end_fixity_coefficient`, \(C = 1/K^{2}\), so `euler_critical_load_fixity` is \(P_{\mathrm{cr}} = C\pi^{2}EI/L^{2}\). Default \(K = 1\) (pinned–pinned). Classical ends: fixed–fixed \(K = 1/2\), fixed–pinned \(K = 1/\sqrt{2}\), fixed–free \(K = 2\).

With `--area`, radius of gyration is `radius_of_gyration`, \(\rho=\sqrt{I/A}\); slenderness is `column_slenderness`, \(KL/\rho\); critical stress is `euler_critical_stress`, \(\sigma_{\mathrm{cr}}=P_{\mathrm{cr}}/A\). With `--area` and `--yield`, `euler_regime` is `valid_euler` when \(\sigma_{\mathrm{cr}}<\sigma_y\) and `yield_first` otherwise. Elastic Euler only; no short-column or tangent-modulus curve.

## When to run

1. Use this skill when the user wants the elastic Euler critical load of a column, strut, longeron, or boom in compression, or the critical stress / slenderness / Euler-versus-yield check for that load.
2. Convert inputs to SI before the call (Pa, m⁴, m, m²). State the converted units in the reply. Do not invent \(E\), \(I\), \(L\), \(K\), \(A\), or yield.
3. Pass `--E`, `--inertia`, and `--length`. Pass `--k` and/or `--ends`. An omitted `--k` and `--ends` is pinned–pinned \(K = 1\). Do not pass disagreeing `--k` and `--ends`.
4. Pass `--area` when the user wants critical stress or slenderness. Pass `--yield` only with `--area` when they want the Euler-versus-yield regime.
5. Pass `--out` only when the user wants the PNG of critical load versus length for the fixed section. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for short-column / Johnson / tangent-modulus formulas, eccentric columns, local crippling, shell buckling, or beam bending.

## Flags

Run:

```text
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --E <Pa> --inertia <m^4> --length <m> [--k <K> | --ends <name>] [--area <m^2>] [--yield <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--E` | Young’s modulus \(E\) | Pa, \(> 0\) | Required |
| `--inertia` | Second moment of area \(I\) | m⁴, \(> 0\) | Required |
| `--length` | Unsupported length \(L\) | m, \(> 0\) | Required |
| `--k` | End-fix factor \(K=L'/L\) | dimensionless, \(> 0\) | Optional; default 1 |
| `--ends` | Classical ends: `pinned-pinned`, `fixed-fixed`, `fixed-pinned`, `fixed-free` | — | Optional; sets \(K\) |
| `--area` | Cross-sectional area \(A\) | m², \(> 0\) | Optional |
| `--yield` | Compressive yield stress \(\sigma_y\) | Pa, \(> 0\) | Optional; needs `--area` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Stress in psi uses `1 psi = 6894.757293168361 Pa`. Stress in MPa uses `1 MPa = 1e6 Pa`. Length in inches uses `1 in = 0.0254 m`, so \(I\) in in⁴ uses `(0.0254)^4` m⁴. Modulus in psi uses the same psi-to-Pa factor.

When `--out` is passed, the program writes one PNG. The plot title is `Euler column buckling`. The curve is \(P_{\mathrm{cr}}(L)\) at fixed \(E\), \(I\), and \(K\), drawn from \(0.5L\) to \(1.5L\) so the \(1/L^{2}\) singularity near zero length is off-scale. The square is the operating point. A dashed horizontal line is \(A\sigma_y\) when `--yield` and `--area` were passed. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `E_Pa`, `I_m4`, `L_m`, `K`, `ends`, `C`, `L_eff_m`, and `P_cr_N`.
4. Report `A_m2`, `rho_m`, `slenderness`, and `sigma_cr_Pa` when they are printed.
5. Report `yield_Pa` and `euler_regime` when they are printed. `valid_euler` means the Euler stress is below yield. `yield_first` means the section would yield before the elastic Euler load is reached.
6. If \(E\), \(I\), or \(L\) is missing, say so. Do not fill them in.
