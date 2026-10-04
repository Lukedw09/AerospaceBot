---
name: AERO - ConicalShock
description: >-
  Run the circular-cone Taylor-Maccoll program and report its printed
  results and PNG. Use when the user wants the attached shock angle, surface
  Mach, or surface pressure coefficient on a right circular cone in a
  uniform supersonic stream. Do not redraw the cone or recompute the numbers
  by hand.
---

# AERO - ConicalShock

Use this skill for a right circular cone at zero incidence in a uniform supersonic stream. Run the program once; quote its stdout and include its PNG. Do not redraw the cone or recompute the numbers by hand.

The reported shock is the weaker attached root of the Taylor–Maccoll problem in NASA SP-3004. Polar speeds in the shock layer use NACA TN 3485. The jump across the conical shock is the oblique-shock state at that wave angle. Surface pressure coefficient is `pressure_coefficient_from_mach` after an isentropic compression from the post-shock Mach. Zero half-angle is a Mach wave. The strong root is printed only when it is a distinct second solution.

This is a circular cone, not a two-dimensional wedge. Do not run `AERO - PrandtlMeyerAndShocks` as a cone solution. Boundary layer, yaw, and a detached bow shape are not modeled.

## When to run

1. Use this skill when the user asks for a conical shock, a cone wave angle, surface Mach on a cone, or the surface pressure coefficient of a circular cone in supersonic flow.
2. Convert the cone half-angle to radians before the call. State the converted units in the reply. Do not invent Mach, gamma, or half-angle.
3. If the user asks for a two-dimensional wedge, use `AERO - PrandtlMeyerAndShocks` instead.

## Flags

Run:

```text
python "skills/AERO - ConicalShock/conical_shock.py" --mach <M1> --delta <rad> [--gamma <k>] [--out <png>]
```

Pass **only** flags the user supplied (after converting the half-angle to radians). Do **not** supply a default Mach or half-angle.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Freestream Mach \(M_{\infty}\) | dimensionless, \(> 1\) | Required |
| `--delta` | Cone half-angle \(\delta_c\) | rad, 0 up to \(\pi/2\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

A half-angle in degrees uses `delta_rad = delta_deg * pi/180`. A bare `--mach` and `--delta` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The figure title is `AERO - ConicalShock`. The left panel is the meridian cut. The right panel is the cone and the conical shock. A detached bow is marked schematic.
3. Report `gamma` and `gamma_source`. `default` means \(\gamma = 1.4\) air.
4. Report `M1`, `delta_deg`, `mu1_deg`, and `delta_max_deg`. \(\delta_c\) is the cone half-angle.
5. When `attached: yes`, report `shock`, `theta_deg`, `Mc`, and `Cp`. \(\theta\) is the shock-wave angle from the cone axis. \(M_c\) and \(C_p\) are the cone-surface values.
6. When `shock: mach-wave`, say the wave angle is the Mach angle, \(M_c = M_{\infty}\), and \(C_p = 0\).
7. When `attached: no`, say the shock is detached. Report `delta_max_deg`. Do not invent a shock angle, surface Mach, or surface pressure coefficient.
8. Report `theta_strong_deg` only when it is printed. Say that the cone uses the weak root.
9. Report `M2`, `p2_over_p1`, and `pc_over_p1` when they are printed. \(M_2\) and \(p_2/p_1\) are immediately behind the shock. \(p_c/p_1\) is the surface static-pressure ratio.
10. If Mach or half-angle is missing, or outside the program limits, say so. Do not fill it in.
