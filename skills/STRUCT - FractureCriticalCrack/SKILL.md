---
name: STRUCT - FractureCriticalCrack
description: >-
  Run the fracture critical-crack program and report its printed results and
  optional PNG. Use when the user wants the critical half-length of a through
  crack in a wide plate from fracture toughness and remote stress, and an
  optional margin against an actual half-length. Do not redraw the plot or
  recompute the numbers by hand.
---

# STRUCT - FractureCriticalCrack

Use this skill for the critical half-length of a through crack in a wide plate. It is not a crack-growth rate and not a spectrum load. The family is STRUCT. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The critical half-length is `fracture_critical_half_length`,

\[
a_c = \frac{1}{\pi}\left(\frac{K_{Ic}}{Y\sigma}\right)^2
\]

\(Y\) is the geometry factor and defaults to 1. An actual half-length prints `margin_of_safety` \(= a_c/a - 1\).

## When to run

1. Use this skill when the user wants the critical half-length, or a margin against a stated crack, for a through crack in a wide plate.
2. Convert toughness to Pa·m\(^{1/2}\), stress to pascals, and crack length to metres. State the converted units in the reply. Do not invent toughness or stress.
3. Pass `--kic` and `--stress`.
4. Pass `--geometry` only when the user gave a geometry factor other than 1.
5. Pass `--crack` only when the user gave the actual half-length.
6. Pass `--out` only when the user wants the PNG of critical half-length versus stress. Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for a crack-growth rate or a spectrum load.

## Flags

Run:

```text
python "skills/STRUCT - FractureCriticalCrack/fracture_critical_crack.py" --kic <Pa*m^0.5> --stress <Pa> [--geometry <Y>] [--crack <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--kic` | Plane-strain fracture toughness \(K_{Ic}\) | Pa·m\(^{1/2}\), \(> 0\) | Required |
| `--stress` | Remote tensile stress | Pa, \(> 0\) | Required |
| `--geometry` | Geometry factor \(Y\) | dimensionless, \(> 0\) | Optional. Default 1 |
| `--crack` | Actual half-length \(a\) | m, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Fracture critical crack`. The curve is critical half-length versus stress at the fixed toughness and \(Y\). The square is the operating stress. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `a_c_m`, `Y`, and `stress_Pa`.
4. Report `margin_of_safety` when a crack half-length was given.
5. If toughness or stress is missing, say so. Do not fill them in.
