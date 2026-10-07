---
name: AERO - DutchRollEstimate
description: >-
  Run the Dutch-roll program and report its printed results and optional PNG.
  Use when the user wants the lateral-oscillation frequency and damping from
  speed, density, wing size, inertia, mass, and the stability derivatives they
  already have. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - DutchRollEstimate

Use this skill for the Dutch-roll frequency and damping of an airplane. It is the lateral counterpart of `AERO - PhugoidAndShortPeriod`. It does not compute the spiral mode, the roll-subsidence mode, or the full lateral quartic. Span and area may come from `AERO - WingGeometry`. `AERO - LongitudinalStaticMargin` does not supply the lateral derivatives. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Frequency and damping are the two-degree approximation in NACA Report 589 before that report substitutes average-airplane numbers. Directional stiffness, side force, and yaw damping set

\[
\omega^{2} = N_{\beta} + \frac{Y_{\beta} N_{r}}{V}
\]

and the damping product \(\zeta\omega = -(N_r + Y_{\beta}/V)/2\). The dihedral spring \(g L_{\beta}/(V L_p)\) is kept in \(\omega^{2}\) because that report’s period depends on both directional stability and dihedral. The report’s fits \(0.14\) and \(3.2\), and its design charts, are not used. Mass is required so the side-force derivative can be written as an acceleration.

## When to run

1. Use this skill when the user wants Dutch-roll frequency, period, or damping ratio.
2. Convert speed to m/s, density to kg/m³, span to metres, area to m², inertias to kg·m², and mass to kilograms. Derivatives are dimensionless per radian. State the converted units in the reply. Do not invent a derivative.
3. Pass `--speed`, `--rho`, `--span`, `--area`, `--ix`, `--iz`, `--mass`, `--cn-beta`, `--cl-beta`, `--cy-beta`, `--cn-r`, and `--cl-p`.
4. Pass `--out` only when the user wants the PNG of period and damping versus speed. Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for the spiral mode, the roll-subsidence mode, or a DATCOM chart.

## Flags

Run:

```text
python "skills/AERO - DutchRollEstimate/dutch_roll_estimate.py" --speed <m/s> --rho <kg/m^3> --span <m> --area <m^2> --ix <kg m^2> --iz <kg m^2> --mass <kg> --cn-beta <1/rad> --cl-beta <1/rad> --cy-beta <1/rad> --cn-r <1/rad> --cl-p <1/rad> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | True airspeed | m/s, \(> 0\) | Required |
| `--rho` | Air density | kg/m³, \(> 0\) | Required |
| `--span` | Wing span | m, \(> 0\) | Required |
| `--area` | Wing area | m², \(> 0\) | Required |
| `--ix` | Roll inertia | kg·m², \(> 0\) | Required |
| `--iz` | Yaw inertia | kg·m², \(> 0\) | Required |
| `--mass` | Airplane mass | kg, \(> 0\) | Required |
| `--cn-beta` | Yawing-moment stiffness | per rad | Required |
| `--cl-beta` | Rolling-moment stiffness (dihedral) | per rad | Required |
| `--cy-beta` | Side-force derivative | per rad | Required |
| `--cn-r` | Yaw damping | per rad | Required |
| `--cl-p` | Roll damping | per rad | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Dutch roll`. Period and damping ratio are drawn against speed at the fixed derivatives, density, geometry, and inertias. The markers are the operating speed. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `omega_dr_rad_s`, `f_Hz`, `period_s`, and `zeta_dr`.
4. If any flight-state input or any derivative is missing, say so. Do not fill it in.
