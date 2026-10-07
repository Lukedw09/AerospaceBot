---
name: ADCS - MagneticTorquerSizing
description: >-
  Run the magnetic torquer program and report its printed results and optional
  PNG. Use when the user wants the magnetic moment that produces a stated
  torque in a stated field, and optional coil current. Do not redraw the plot
  or recompute the numbers by hand.
---

# ADCS - MagneticTorquerSizing

Use this skill for one magnetic dipole that pushes against a local field the user states. It does not model the Earth’s field, a dipole tilt, or a multi-coil pyramid. The torque may be the magnetic line from `ADCS - EnvironmentalTorques`, or any other torque the user states. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The moment is `magnetic_moment`, \(m = T/(B\sin\psi)\), the inverse of `magnetic_disturbance_torque`. The default angle is \(\pi/2\). Coil current is `magnetic_coil_current`, \(I = m/(N A)\), printed only when turns and the one-turn area are both given. Optional dipole and current limits print margins of safety.

## When to run

1. Use this skill when the user wants a magnetic moment, a coil current, or a margin against a coil limit.
2. Convert torque to N·m, field to tesla, area to square metres, and the angle to radians. State the converted units in the reply. Do not invent torque or field.
3. Pass `--torque` and `--b-field`.
4. Pass `--mag-angle` only when the user gave an angle other than perpendicular.
5. Pass `--turns` and `--area` together only when the user wants current. Do not invent either one.
6. Pass `--m-max` and `--i-max` only when the user gave those limits. Current margin needs the coil path.
7. Pass `--out` only when the user wants the PNG of dipole versus field. Do not invent a plot path when they did not ask for a figure.
8. Do not use this skill to model the geomagnetic field.

## Flags

Run:

```text
python "skills/ADCS - MagneticTorquerSizing/magnetic_torquer_sizing.py" --torque <N m> --b-field <T> [--mag-angle <rad>] [--turns <N> --area <m^2>] [--m-max <A m^2>] [--i-max <A>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--torque` | Torque the dipole must produce | N·m, \(> 0\) | Required |
| `--b-field` | Local magnetic field | T, \(> 0\) | Required |
| `--mag-angle` | Angle between the dipole and the field | rad, \((0, \pi]\) | Optional. Default \(\pi/2\) |
| `--turns` | Coil turns | dimensionless, \(> 0\) | Optional. Required with `--area` |
| `--area` | Area enclosed by one turn | m², \(> 0\) | Optional. Required with `--turns` |
| `--m-max` | Dipole limit | A·m², \(> 0\) | Optional |
| `--i-max` | Coil current limit | A, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Magnetic torquer sizing`. The curve is required dipole versus field at the fixed torque and angle. The square is the operating field. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `m_A_m2`. Report `I_A` only when turns and area were both given.
4. Report `margin_m` and `margin_I` when those limits were given.
5. If torque or field is missing, say so. Do not fill them in.
