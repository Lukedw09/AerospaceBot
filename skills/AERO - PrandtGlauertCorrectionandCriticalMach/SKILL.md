---
name: AERO - PrandtGlauertCorrectionandCriticalMach
description: >-
  Run the two-dimensional Prandtl-Glauert program and report its printed
  results and PNG. Use when the user wants a compressible lift coefficient
  or minimum pressure coefficient from an incompressible value at a
  subsonic freestream Mach number, or the critical Mach number from that
  minimum pressure coefficient. Do not redraw the plot or recompute the
  numbers by hand.
---

# AERO - PrandtGlauertCorrectionandCriticalMach

Use this skill for the two-dimensional Prandtl-Glauert correction of an incompressible lift coefficient or minimum pressure coefficient, and for the critical Mach number from that suction peak. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The Prandtl-Glauert factor is `prandtl_glauert_factor`:

\[
\beta = \sqrt{1 - M_{\infty}^{2}}
\]

The compressible coefficient is `prandtl_glauert_coefficient`:

\[
C = \frac{C_{0}}{\beta}
\]

That factor applies in two-dimensional flow. It is not a universal three-dimensional correction.

The isentropic critical pressure coefficient is `critical_pressure_coefficient`, which is `pressure_coefficient_from_mach` at local Mach 1:

\[
C_{p,\mathrm{crit}} = \frac{2}{\gamma M_{\infty}^{2}}\left[\left(\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2}M_{\infty}^{2}\right)\right)^{\gamma/(\gamma - 1)} - 1\right]
\]

Critical Mach number is `critical_mach`: the freestream Mach at which `prandtl_glauert_coefficient` of \(C_{p0,\min}\) equals that critical coefficient. There is no closed inverse; the program solves the residual. \(C_{p0,\min}\) must be negative.

## When to run

1. Use this skill when the user wants a Prandtl-Glauert compressibility correction, a compressible \(C_L\) or \(C_{p,\min}\) from an incompressible value, or a critical Mach number from a minimum pressure coefficient.
2. Convert inputs before the call. Mach number is dimensionless. Do not invent \(C_{L0}\), \(C_{p0,\min}\), or \(\gamma\).
3. Pass `--mach` and at least one of `--cl-inc` or `--cpmin-inc`. Pass both when both are known. Critical Mach is printed only from `--cpmin-inc`.
4. One Mach number is one run. Do not sweep.
5. If the Mach number is 1 or greater, say so and stop. If only a lift coefficient is given and the user also asks for critical Mach, ask for the incompressible minimum pressure coefficient.

## Flags

Run:

```text
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --mach <M> [--cl-inc <CL0>] [--cpmin-inc <Cp0min>] [--gamma <k>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Freestream Mach number \(M_{\infty}\) | dimensionless, \(0 \le M < 1\) | Required |
| `--cl-inc` | Incompressible lift coefficient \(C_{L0}\) | dimensionless | One of `--cl-inc`, `--cpmin-inc` |
| `--cpmin-inc` | Incompressible minimum pressure coefficient \(C_{p0,\min}\) | dimensionless, \(< 0\) for \(M_{\mathrm{cr}}\) | One of `--cl-inc`, `--cpmin-inc` |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

A bare `--mach` with `--cl-inc` or `--cpmin-inc` and no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

Every successful run writes one PNG. The plot title is `Prandtl-Glauert correction and critical Mach`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is freestream Mach. A lift panel plots \(C_L = C_{L0}/\beta\). A pressure panel plots the Prandtl-Glauert \(C_{p,\min}\) and \(C_{p,\mathrm{crit}}\). The square is the given Mach. The dashed line is \(M_{\mathrm{cr}}\) when it is printed.
3. Report `M`, `gamma`, `gamma_source`, and `beta`. `default` means \(\gamma = 1.4\) air.
4. Report `CL0` and `CL` when they are printed. Report `Cp0_min` and `Cp_min` when they are printed.
5. Report `Cp_crit` when it is printed. That is the sonic pressure coefficient at the given Mach, not at \(M_{\mathrm{cr}}\).
6. Report `M_cr` when it is printed. Report `supercritical`. `yes` means the corrected \(C_{p,\min}\) at the given Mach is more negative than \(C_{p,\mathrm{crit}}\) at that Mach.
7. If `warning` is printed, include it. A non-negative `--cpmin-inc` is not a suction peak, so critical Mach is omitted.
8. If Mach, and at least one incompressible coefficient, are missing, say so. Do not fill them in.
