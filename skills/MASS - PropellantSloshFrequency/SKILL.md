---
name: MASS - PropellantSloshFrequency
description: >-
  Run the propellant slosh program and report its printed results and optional
  PNG. Use when the user wants the first lateral slosh frequency of a flat
  free surface in a rigid upright cylindrical tank, and the equivalent
  pendulum length. Do not redraw the plot or recompute the numbers by hand.
---

# MASS - PropellantSloshFrequency

Use this skill for the lowest lateral mode of liquid in a rigid upright cylinder with a flat free surface. It does not model baffles, a curved meniscus, axial slosh, or a control law. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The frequency is `propellant_slosh_frequency`,

\[
\omega^{2} = (g/R)\,\xi\tanh(\xi h/R),\qquad \xi = 1.841
\]

\(\xi\) is the first root of \(J_1'(\xi)=0\), fixed in the program. The equivalent pendulum length is `slosh_pendulum_length`, \(g/\omega^{2}\). A shallow fill is still computed. The program prints `shallow: yes` when \(h/R < 0.2\).

## When to run

1. Use this skill when the user wants the first lateral slosh frequency or the equivalent pendulum length of a cylindrical tank.
2. Convert radius and liquid depth to metres. State the converted units in the reply. Do not invent radius or depth.
3. Pass `--radius` and `--height`.
4. Pass `--g` only when the user gave an axial acceleration other than standard gravity. The default is \(g_0 = 9.80665\,\mathrm{m/s}^{2}\).
5. Pass `--out` only when the user wants the PNG of frequency versus fill height. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for baffles, a meniscus, axial slosh, or a control frequency.

## Flags

Run:

```text
python "skills/MASS - PropellantSloshFrequency/propellant_slosh_frequency.py" --radius <m> --height <m> [--g <m/s^2>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--radius` | Tank inner radius | m, \(> 0\) | Required |
| `--height` | Liquid depth | m, \(> 0\) | Required |
| `--g` | Axial acceleration | m/s², \(> 0\) | Optional. Default 9.80665 |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Propellant slosh frequency`. The curve is frequency versus fill height from a small fraction of the radius to several radii. The square is the operating depth. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `omega_rad_s`, `f_Hz`, `pendulum_length_m`, and `shallow`.
4. If radius or liquid depth is missing, say so. Do not fill them in.
