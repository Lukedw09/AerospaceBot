---
name: AERO - PhugoidAndShortPeriod
description: >-
  Run the phugoid and short-period program and report its printed results and
  optional PNG. Use when the user wants the classical phugoid period and the
  approximate stick-fixed short-period frequency from speed, density, wing
  loading, lift-curve slope, static margin, mean chord, and pitch radius of
  gyration. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - PhugoidAndShortPeriod

Use this skill for the two classical longitudinal approximations. It is not a fourth-order state matrix. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Phugoid natural frequency is `phugoid_natural_frequency`, \(\omega_{\mathrm{ph}}=(g/V)\sqrt{2}\), and the period is `phugoid_period`. Short-period natural frequency is `short_period_natural_frequency`, from the static pitch stiffness \(-M_{\alpha}\) only:

\[
\omega_{\mathrm{sp}} = \frac{V}{k_y}\sqrt{\frac{\rho g c\, C_{L\alpha} K_n}{2(W/S)}}
\]

The period is `short_period_period`. \(K_n\) is the static-margin fraction of the mean chord. Pass `x_over_c` from `AERO - LongitudinalStaticMargin`, not `static_margin_percent`. A printed static margin of 5 percent is \(K_n = 0.05\).

Pitch damping and \(\dot{\alpha}\) derivatives are omitted. A negative or zero static margin has no oscillatory short-period frequency in this approximation.

## When to run

1. Use this skill when the user wants approximate phugoid and short-period periods or frequencies.
2. Convert speed to m/s, density to kg/m³, wing loading to N/m², chord and pitch radius of gyration to metres. State the converted units in the reply. Do not invent them.
3. Pass `--speed`, `--rho`, `--wing-loading`, `--cla`, `--static-margin`, `--mac`, and `--ky`. `--static-margin` is the fraction \(x/c\), positive when the center of gravity is ahead of the neutral point.
4. Pass `--cla` per radian. If the user has a per-degree slope, multiply by \(180/\pi\) before the call.
5. Pass `--out` only when the user wants the PNG of periods versus speed. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for a full longitudinal eigenvalue solution, lateral modes, or a control law.

## Flags

Run:

```text
python "skills/AERO - PhugoidAndShortPeriod/phugoid_and_short_period.py" --speed <m/s> --rho <kg/m^3> --wing-loading <N/m^2> --cla <1/rad> --static-margin <x/c> --mac <m> --ky <m> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | True airspeed \(V\) | m/s, \(> 0\) | Required |
| `--rho` | Air density | kg/m³, \(> 0\) | Required |
| `--wing-loading` | Weight over wing area \(W/S\) | N/m², \(> 0\) | Required |
| `--cla` | Lift-curve slope \(C_{L\alpha}\) | 1/rad, \(> 0\) | Required |
| `--static-margin` | Static margin \(K_n = x/c\) | dimensionless, \(> 0\) | Required |
| `--mac` | Mean aerodynamic chord \(c\) | m, \(> 0\) | Required |
| `--ky` | Pitch radius of gyration \(k_y\) | m, \(> 0\) | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Speed in knots uses `1 kt = 0.514444 m/s`. Wing loading in lb/ft² uses `1 lb/ft² = 47.88025898 N/m²`.

When `--out` is passed, the program writes one PNG. The plot title is `Phugoid and short period`. The curves are the two periods versus speed. Squares mark the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `omega_ph_rad_s`, `T_ph_s`, `omega_sp_rad_s`, and `T_sp_s`.
4. State that the phugoid period uses speed and \(g_0\) only, and that the short-period frequency neglects pitch damping.
5. If any required input is missing, say so. Do not fill it in.
