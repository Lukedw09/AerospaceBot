---
name: ADCS - ReactionWheelSizing
description: >-
  Run the reaction-wheel sizing program and report its printed results and
  optional PNG. Use when the user wants the single-axis wheel inertia that
  stores a stated angular momentum at a maximum wheel speed, the torque the
  wheel must match, and optional margins against wheel momentum and torque
  limits. Do not redraw the plot or recompute the numbers by hand.
---

# ADCS - ReactionWheelSizing

Use this skill for one reaction wheel on a principal axis. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Wheel inertia is `reaction_wheel_inertia`, \(I_w = H/\omega_{\max}\), from \(H = I\omega\) at the speed limit. The torque demand is the value the user passes. It is not recomputed here. When a wheel momentum limit or torque limit is passed, each margin is `margin_of_safety`.

Take \(H\) and the torque from two separate runs of `ADCS - SlewMomentum`: slew impulse and disturbance storage are not added inside that skill. Inertia of the spacecraft, if needed to form those demands, may come from `MASS - CenterOfMassAndInertia`. This skill does not size a wheel pyramid, a motor, or a desaturation system.

## When to run

1. Use this skill when the user wants the wheel inertia for a stored momentum and a maximum wheel speed, or the margin of that wheel against a momentum or torque limit.
2. Convert momentum to N·m·s, torque to N·m, and wheel speed to rad/s. State the converted units in the reply. Do not invent momentum, torque, or wheel speed.
3. Pass `--H`, `--tau`, and `--omega-max`. Obtain `--H` and `--tau` from `ADCS - SlewMomentum` when the user has those runs. If the user asked for both a slew and a disturbance, pass the larger demand they name, or say both numbers and ask which wheel case to size. Do not add the two impulses unless the user already did.
4. Pass `--H-max` or `--tau-max` only when the user gave that wheel limit.
5. Pass `--out` only when the user wants the PNG of required inertia versus maximum wheel speed. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for a multi-wheel pyramid, magnetic torquers, or thruster desaturation.

## Flags

Run:

```text
python "skills/ADCS - ReactionWheelSizing/reaction_wheel_sizing.py" --H <N*m*s> --tau <N*m> --omega-max <rad/s> [--H-max <N*m*s>] [--tau-max <N*m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--H` | Angular momentum the wheel must store | N·m·s, \(> 0\) | Required |
| `--tau` | Peak torque the wheel must supply | N·m, \(> 0\) | Required |
| `--omega-max` | Maximum wheel speed \(\omega_{\max}\) | rad/s, \(> 0\) | Required |
| `--H-max` | Wheel momentum limit | N·m·s, \(> 0\) | Optional |
| `--tau-max` | Wheel torque limit | N·m, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A wheel speed in rpm uses \(2\pi/60\) rad/s per rpm.

When `--out` is passed, the program writes one PNG. The plot title is `Reaction wheel sizing`. The curve is \(I_w = H/\omega\) versus maximum wheel speed for the fixed momentum. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `H_N_m_s`, `tau_N_m`, `omega_max_rad_s`, and `I_w_kg_m2`.
4. Report `H_max_N_m_s` and `margin_H` when they are printed. Report `tau_max_N_m` and `margin_tau` when they are printed. A margin of 0 means the demand equals the limit. A negative margin means the demand is above the limit.
5. If momentum, torque, or maximum wheel speed is missing, say so. Do not fill them in.
