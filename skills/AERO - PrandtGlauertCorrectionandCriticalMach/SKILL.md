---
name: AERO - PrandtGlauertCorrectionandCriticalMach
description: >-
  Run the two-dimensional Prandtl-Glauert program and report its printed
  results and PNG. Use when the user wants a compressible lift or moment
  coefficient, an uncorrected drag coefficient, or a minimum pressure
  coefficient from an incompressible value at a subsonic freestream Mach
  number, or the critical Mach number from that minimum pressure
  coefficient. Incompressible values may be supplied or taken from a NACA
  Report 824 four-digit chart. Do not redraw the plot or recompute the
  numbers by hand.
---

# AERO - PrandtGlauertCorrectionandCriticalMach

Use this skill for the two-dimensional Prandtl-Glauert correction of an incompressible lift coefficient, section moment, or minimum pressure coefficient, and for the critical Mach number from that suction peak. Drag is left at its incompressible value. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand. There is no separate compressible-lift-curve skill.

The Prandtl-Glauert factor is `prandtl_glauert_factor`:

\[
\beta = \sqrt{1 - M_{\infty}^{2}}
\]

The compressible coefficient is `prandtl_glauert_coefficient`:

\[
C = \frac{C_{0}}{\beta}
\]

That factor applies to lift and to the section moment. It does not divide the drag coefficient. It is not a universal three-dimensional correction.

User coefficients print `coeff_source: user`. `--naca` with `--alpha` fills \(c_{l0}\), \(c_{d0}\), and \(c_{m0}\) from the Report 824 lookup in `AERO - NACAFourDigitSection` (0012, 2412, 2415, and 4412) and prints `coeff_source: naca`. An omitted `--re` uses that program’s nearest-\(6\times 10^{6}\) rule. A designation or Reynolds number outside the table is an error. There is no fallback to \(2\pi\alpha\). Passing `--naca` together with `--cl-inc`, `--cm-inc`, or `--cd-inc` is an error. `--cpmin-inc` may still be passed with `--naca`, because those charts have no pressure distribution.

The isentropic critical pressure coefficient is `critical_pressure_coefficient`, which is `pressure_coefficient_from_mach` at local Mach 1:

\[
C_{p,\mathrm{crit}} = \frac{2}{\gamma M_{\infty}^{2}}\left[\left(\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2}M_{\infty}^{2}\right)\right)^{\gamma/(\gamma - 1)} - 1\right]
\]

Critical Mach number is `critical_mach`: the freestream Mach at which `prandtl_glauert_coefficient` of \(C_{p0,\min}\) equals that critical coefficient. There is no closed inverse; the program solves the residual. \(C_{p0,\min}\) must be negative.

## When to run

1. Use this skill when the user wants a Prandtl-Glauert compressibility correction, a compressible \(C_L\) or \(c_m\) from an incompressible value, an uncorrected drag coefficient, or a critical Mach number from a minimum pressure coefficient.
2. Convert inputs before the call. Mach number is dimensionless. Angle of attack for `--naca` is radians. Do not invent \(C_{L0}\), \(c_{m0}\), \(c_{d0}\), \(C_{p0,\min}\), a NACA designation, or \(\gamma\).
3. Pass `--mach`. Pass any combination of `--cl-inc`, `--cm-inc`, `--cd-inc`, and `--cpmin-inc`. Critical Mach is printed only from `--cpmin-inc`.
4. Or pass `--naca` and `--alpha` instead of those three force and moment coefficients. Pass `--re` only when the user gave a Reynolds number. `--cpmin-inc` may be added to the NACA path.
5. One Mach number is one run. Do not sweep.
6. If the Mach number is 1 or greater, say so and stop. If the user asks for critical Mach and did not give \(C_{p0,\min}\), ask for it. Do not invent a pressure coefficient from the NACA chart.

## Flags

Run:

```text
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --mach <M> [--cl-inc <CL0>] [--cm-inc <Cm0>] [--cd-inc <Cd0>] [--cpmin-inc <Cp0min>] [--naca <designation> --alpha <rad> [--re <Re>]] [--gamma <k>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Freestream Mach number \(M_{\infty}\) | dimensionless, \(0 \le M < 1\) | Required |
| `--cl-inc` | Incompressible lift coefficient \(C_{L0}\) | dimensionless | Optional. Not with `--naca` |
| `--cm-inc` | Incompressible moment coefficient \(c_{m0}\) | dimensionless | Optional. Not with `--naca` |
| `--cd-inc` | Incompressible drag coefficient \(c_{d0}\) | dimensionless | Optional. Not divided by \(\beta\). Not with `--naca` |
| `--cpmin-inc` | Incompressible minimum pressure coefficient \(C_{p0,\min}\) | dimensionless, \(< 0\) for \(M_{\mathrm{cr}}\) | Optional. May be passed with `--naca` |
| `--naca` | Report 824 four-digit designation | 0012, 2412, 2415, or 4412 | With `--alpha`. Not with user \(c_l\), \(c_m\), or \(c_d\) |
| `--alpha` | Angle of attack for `--naca` | rad | With `--naca` |
| `--re` | Reynolds number for `--naca` | dimensionless, \(> 0\) | Optional. Nearest \(6\times 10^{6}\) if omitted |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

A bare `--mach` with `--cl-inc` or `--cpmin-inc` and no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

Every successful run writes one PNG. The plot title is `Prandtl-Glauert correction and critical Mach`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is freestream Mach. A lift panel plots \(C_L = C_{L0}/\beta\) and, when a moment is present, \(c_m(M)\). A pressure panel plots the Prandtl-Glauert \(C_{p,\min}\) and \(C_{p,\mathrm{crit}}\). The square is the given Mach. The dashed line is \(M_{\mathrm{cr}}\) when it is printed.
3. Report `M`, `gamma`, `gamma_source`, and `beta`. `default` means \(\gamma = 1.4\) air.
4. Report `coeff_source` when it is printed. `user` means the coefficients were supplied. `naca` means Report 824. Report `CL0` and `CL` when they are printed. Report `Cm0` and `Cm` when they are printed. Report `Cd0`, `Cd`, and `cd_source` when they are printed. `cd_source: incompressible` means drag was not divided by \(\beta\). Report `Cp0_min` and `Cp_min` when they are printed.
5. Report `Cp_crit` when it is printed. That is the sonic pressure coefficient at the given Mach, not at \(M_{\mathrm{cr}}\).
6. Report `M_cr` when it is printed. Report `supercritical`. `yes` means the corrected \(C_{p,\min}\) at the given Mach is more negative than \(C_{p,\mathrm{crit}}\) at that Mach.
7. If `warning` is printed, include it. A non-negative `--cpmin-inc` is not a suction peak, so critical Mach is omitted.
8. If Mach, and at least one incompressible coefficient, are missing, say so. Do not fill them in.
