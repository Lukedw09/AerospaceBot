---
name: STRUCT - PanelBuckling
description: >-
  Run the panel buckling program and report its printed results and optional
  PNG. Use when the user wants the elastic critical compressive stress of a
  rectangular plate with four simply supported edges, and an optional margin
  against an applied stress. Do not redraw the plot or recompute the numbers
  by hand.
---

# STRUCT - PanelBuckling

Use this skill for elastic uniaxial buckling of a thin rectangular plate whose four edges are simply supported. It is not a column (`STRUCT - EulerColumnBuckling`), not a pressure vessel (`STRUCT - ThinWallPressureVessel`), and not a shear or biaxial check. Plasticity and stiffened-panel knockdowns are omitted. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The critical stress is `plate_buckling_stress`,

\[
\sigma_{\mathrm{cr}} = \frac{k\pi^{2} E}{12(1-\nu^{2})(b/t)^{2}}
\]

Compression runs along the length. \(b\) is the unloaded-edge spacing. With no length, the plate is long and \(k = 4\). With a length \(a\), \(k\) is `simply_supported_plate_k`, the minimum of \((mb/a + a/(mb))^{2}\) over positive integers \(m\). The winning half-wave count is printed. An applied compressive stress prints `margin_of_safety` \(= \sigma_{\mathrm{cr}}/\sigma - 1\).

## When to run

1. Use this skill when the user wants the elastic critical stress, the buckling coefficient, or a margin of safety for a simply supported plate in compression.
2. Convert modulus and stress to pascals, and width, thickness, and length to metres. State the converted units in the reply. Do not invent modulus, Poisson’s ratio, width, or thickness.
3. Pass `--E`, `--nu`, `--width`, and `--thickness`.
4. Pass `--length` only when the user gave the loaded-edge length. Omit it for a long plate.
5. Pass `--stress` only when the user gave an applied compressive stress.
6. Pass `--out` only when the user wants the PNG of critical stress versus \(b/t\). Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for a column, a pressure vessel, shear buckling, or a plastic knockdown.

## Flags

Run:

```text
python "skills/STRUCT - PanelBuckling/panel_buckling.py" --E <Pa> --nu <nu> --width <m> --thickness <m> [--length <m>] [--stress <Pa>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--E` | Young’s modulus | Pa, \(> 0\) | Required |
| `--nu` | Poisson’s ratio | dimensionless, \(\lvert\nu\rvert < 1\) | Required |
| `--width` | Unloaded-edge spacing \(b\) | m, \(> 0\) | Required |
| `--thickness` | Plate thickness | m, \(> 0\) | Required |
| `--length` | Loaded length \(a\) | m, \(> 0\) | Optional |
| `--stress` | Applied compressive stress | Pa, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Panel buckling`. The curve is critical stress versus \(b/t\) at the fixed modulus, Poisson’s ratio, and \(k\). The square is the operating plate. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `k`, `sigma_cr_Pa`, and `b_over_t`.
4. Report `half_waves` when a length was given. Report `margin_of_safety` when an applied stress was given.
5. If modulus, Poisson’s ratio, width, or thickness is missing, say so. Do not fill them in.
