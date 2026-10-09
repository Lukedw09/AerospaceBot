---
name: ADCS - AttitudeKinematics
description: >-
  Run the attitude-kinematics program and report its printed map and PNG.
  Use when the user wants a 3-2-1 direction-cosine matrix, a scalar-first
  quaternion, or the kinematic angle and quaternion rates. Do not redraw
  the plot or recompute the numbers by hand.
---

# ADCS - AttitudeKinematics

Use this skill for rigid-body attitude kinematics. One run is one conversion. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

The 3-2-1 matrix is `dcm_321_c11` through `dcm_321_c33`. The scalar-first quaternion matrix is `quaternion_to_dcm_c11` through `quaternion_to_dcm_c33`. Body rates map through `euler_rate_roll`, `euler_rate_pitch`, `euler_rate_yaw`, and `quaternion_rate_0` through `quaternion_rate_3`.

This is not dynamics. Torques and momentum stay on `ADCS - EnvironmentalTorques` and `ADCS - SlewMomentum`. Only the 3-2-1 sequence is supported.

## When to run

1. Use this skill to convert 3-2-1 Euler angles, a direction-cosine matrix, or a scalar-first quaternion, or to map body rates into Euler rates or quaternion rates.
2. Pass exactly one `--mode`. Angles and rates are radians.
3. Do not invent an angle, a matrix element, a quaternion component, or a rate.
4. Yaw, then pitch, then roll. Pitch near \(\pm\pi/2\) is gimbal lock.

## Flags

Run:

```text
python "skills/ADCS - AttitudeKinematics/attitude_kinematics.py" --mode <mode> [--yaw <rad>] [--pitch <rad>] [--roll <rad>] [--q0 <q0>] [--q1 <q1>] [--q2 <q2>] [--q3 <q3>] [--wx <rad/s>] [--wy <rad/s>] [--wz <rad/s>] [--c11 <c11>] [--c12 <c12>] [--c13 <c13>] [--c21 <c21>] [--c22 <c22>] [--c23 <c23>] [--c31 <c31>] [--c32 <c32>] [--c33 <c33>] [--out <png>]
```

Pass **only** flags the chosen mode needs.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mode` | `euler_to_dcm`, `dcm_to_euler`, `quat_to_dcm`, `dcm_to_quat`, `euler_rates`, or `quat_rates` | — | Required |
| `--yaw` | Yaw, axis 3 | rad | Required for `euler_to_dcm` and `euler_rates` |
| `--pitch` | Pitch, axis 2 | rad | Required for `euler_to_dcm` and `euler_rates` |
| `--roll` | Roll, axis 1 | rad | Required for `euler_to_dcm` and `euler_rates` |
| `--q0` | Quaternion scalar | dimensionless | Required for `quat_to_dcm` and `quat_rates` |
| `--q1` | Quaternion vector x | dimensionless | Required for `quat_to_dcm` and `quat_rates` |
| `--q2` | Quaternion vector y | dimensionless | Required for `quat_to_dcm` and `quat_rates` |
| `--q3` | Quaternion vector z | dimensionless | Required for `quat_to_dcm` and `quat_rates` |
| `--wx` | Body rate about x | rad/s | Required for `euler_rates` and `quat_rates` |
| `--wy` | Body rate about y | rad/s | Required for `euler_rates` and `quat_rates` |
| `--wz` | Body rate about z | rad/s | Required for `euler_rates` and `quat_rates` |
| `--c11` | Direction-cosine row 1 column 1 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c12` | Direction-cosine row 1 column 2 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c13` | Direction-cosine row 1 column 3 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c21` | Direction-cosine row 2 column 1 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c22` | Direction-cosine row 2 column 2 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c23` | Direction-cosine row 2 column 3 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c31` | Direction-cosine row 3 column 1 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c32` | Direction-cosine row 3 column 2 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--c33` | Direction-cosine row 3 column 3 | dimensionless | Required for `dcm_to_euler` and `dcm_to_quat` |
| `--out` | PNG path | — | Optional |

The Required cells above are conditional on `--mode`, so the program rejects a missing input for the selected mode.

Every successful run writes one PNG. The plot title is `Attitude kinematics`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The three arrows are the body axes drawn in the reference frame.
3. Report `mode`. For a matrix conversion, report `c11` through `c33`.
4. For Euler output, report `yaw`, `pitch`, `roll`, and `gimbal_lock` when it is printed.
5. For a quaternion, report `q0`, `q1`, `q2`, and `q3`. The scalar is first. The program flips the sign so `q0` is not negative.
6. For `euler_rates`, report `roll_rate`, `pitch_rate`, and `yaw_rate`.
7. For `quat_rates`, report `q0_dot`, `q1_dot`, `q2_dot`, and `q3_dot`.
8. If the mode or one of its inputs is missing, or the pitch is at gimbal lock, say so. Do not fill it in.
