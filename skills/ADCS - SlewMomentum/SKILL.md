---
name: ADCS - SlewMomentum
description: >-
  Run the slew-momentum program in exactly one mode and report its printed
  results and optional PNG. Slew mode is the rest-to-rest torque and angular
  impulse from inertia, angle, and time. Disturbance mode stores H = T*tau
  from one torque and a duration. Do not pass both modes in one run. Do not
  recompute the numbers by hand.
---

# ADCS - SlewMomentum

Use this skill for one of two separate actuator demands. Do not combine them in one run.

Slew mode is a rest-to-rest turn about one principal axis, with equal acceleration and deceleration. Torque is `rest_to_rest_slew_torque`, \(\tau = 4 I \theta / t^{2}\). Angular impulse of one half is `rest_to_rest_slew_impulse`, \(H = 2 I \theta / t\), which is also \(I\) times the peak rate \(2\theta/t\). This mode does not take environmental torques. Inertia may come from `MASS - CenterOfMassAndInertia`.

Disturbance mode stores `disturbance_momentum_storage`, \(H = T \tau\), from one torque magnitude and a duration. The torque may be one value printed by `ADCS - EnvironmentalTorques`. The duration is the interval the user states, or one orbit period from `ASTRO - OrbitalParameters`.

Closed-loop settling stays in `CTRL - SecondOrderResponse`. No wheel, thruster, or magnetorquer catalog. The actuator must cover both demands, computed in two runs.

## When to run

1. Use slew mode when the user wants the torque and impulse of a rest-to-rest turn.
2. Use disturbance mode when the user wants the momentum to store against one constant disturbance.
3. Convert inertia to kg·m², angle to radians, torque to N·m, and time to seconds. Do not invent them.
4. Pass either `--inertia`, `--angle`, and `--time`, or `--torque` and `--duration`. Never both sets.
5. Pass `--out` only when the user wants the PNG.

## Flags

```text
python "skills/ADCS - SlewMomentum/slew_momentum.py" --inertia <kg*m^2> --angle <rad> --time <s> [--out <png>]
python "skills/ADCS - SlewMomentum/slew_momentum.py" --torque <N*m> --duration <s> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--inertia` | Principal inertia | kg·m², \(> 0\) | Slew mode |
| `--angle` | Turn angle | rad, \(> 0\) | Slew mode |
| `--time` | Turn time | s, \(> 0\) | Slew mode |
| `--torque` | Constant disturbance torque | N·m | Disturbance mode |
| `--duration` | Time that torque is stored | s, \(> 0\) | Disturbance mode |
| `--out` | PNG path | — | Optional |

The plot title is `Slew momentum`. Slew mode plots torque versus slew time. Disturbance mode plots stored momentum versus duration.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `mode`. Slew mode: `tau_N_m` and `H_N_m_s`. Disturbance mode: `H_N_m_s`.
4. If the user asked for both modes, run the program twice. Do not add the impulses in one call.
