---
name: ADCS - EnvironmentalTorques
description: >-
  Run the environmental-torque program and report its printed results and
  optional PNG. Use when the user wants gravity-gradient, aerodynamic, solar
  radiation, or residual magnetic torque on a general spacecraft. Density comes
  from altitude unless the user overrides it. Hand one torque magnitude and a
  duration to the disturbance mode of ADCS - SlewMomentum. Do not recompute
  the numbers by hand.
---

# ADCS - EnvironmentalTorques

Use this skill for the external torques a spacecraft must fight. Attitude determination and control is pointing. Guidance stays in `CTRL`. Run the program once; quote its stdout and include the PNG when `graph:` is printed.

Gravity-gradient torque is `gravity_gradient_torque`, \(\frac{3}{2} n^{2}(I_z-I_y)\sin 2\theta\), from NASA SP-8024. Orbit rate uses Earth \(\mu = g_0 R_0^{2}\) with \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). Inertia may come from `MASS - CenterOfMassAndInertia`.

Aerodynamic torque is `aerodynamic_disturbance_torque`, \(q C_D A d\). Density is `ATMOS - Standard1976` at or below 86 km and `ATMOS - DensityAbove86km` above 86 km. `--rho` is an override, not a required input.

Solar torque is `solar_radiation_torque`, \((S/c) A C_r d\). Magnetic torque is `magnetic_disturbance_torque`, \(M B\sin\psi\). The user supplies the field. If the angle is omitted, the program takes the perpendicular case.

No wheel, thruster, or magnetorquer catalog. The disturbance mode of `ADCS - SlewMomentum` stores \(H = T\tau\) from one of these magnitudes and a duration.

## When to run

1. Use this skill when the user wants one or more of the four disturbance torques.
2. Convert inertia to kg·m², angles to radians, altitude to metres, area to m², offsets to metres, dipole to A·m², and field to tesla. Do not invent inertia, angle, \(C_D\), area, center-of-pressure offset, reflectance, dipole, or magnetic field.
3. Pass the flag group for each torque the user asked for. Omit the others.
4. For aerodynamic torque, pass `--alt` or `--a`. Pass `--rho` only when the user supplied a density override.
5. Pass `--out` only when the user wants the bar chart of the torque magnitudes.
6. Send one printed torque and a user duration to `ADCS - SlewMomentum` disturbance mode. Do not fold the torque into the slew mode.

## Flags

```text
python "skills/ADCS - EnvironmentalTorques/environmental_torques.py" [--i-z <kg*m^2> --i-y <kg*m^2> --theta <rad> (--alt <m> | --a <m>)] [--cd <1> --area <m^2> --cp-aero <m> (--alt <m> | --a <m>) [--rho <kg/m^3>]] [--area-sun <m^2> --reflectance <1> --cp-sun <m>] [--dipole <A*m^2> --b-field <T> [--mag-angle <rad>]] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--i-z`, `--i-y` | Principal moments about the orbit-normal and pitch axes | kg·m² | Together, with `--theta` and `--alt` or `--a` |
| `--theta` | Angle from the local vertical | rad | With the inertia pair |
| `--alt` | Geometric altitude | m, \(\ge 0\) | Orbit radius, or density when `--rho` is omitted |
| `--a` | Orbit radius from the centre | m, \(> 0\) | Alternative to `--alt` |
| `--cd` | Drag coefficient | dimensionless, \(> 0\) | With `--area` and `--cp-aero` |
| `--area` | Aerodynamic reference area | m² | With `--cd` and `--cp-aero` |
| `--cp-aero` | Aerodynamic center-of-pressure offset | m | With `--cd` and `--area` |
| `--rho` | Density override | kg/m³ | Optional |
| `--area-sun` | Area for solar pressure | m² | With `--reflectance` and `--cp-sun` |
| `--reflectance` | Reflectance factor \(C_r\) | dimensionless | With `--area-sun` and `--cp-sun` |
| `--cp-sun` | Solar center-of-pressure offset | m | With `--area-sun` and `--reflectance` |
| `--solar-constant` | Solar constant | W/m² | Optional. Default 1361.6 |
| `--dipole` | Residual dipole | A·m² | With `--b-field` |
| `--b-field` | Magnetic field | T | With `--dipole` |
| `--mag-angle` | Angle between dipole and field | rad | Optional. Default \(\pi/2\) |
| `--out` | PNG path | — | Optional |

The plot title is `Environmental torques`.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report each torque that was printed: `T_gg_N_m`, `T_aero_N_m`, `T_solar_N_m`, `T_mag_N_m`.
4. When density is printed, report `rho_kg_m3` and `density_source`.
5. If a requested torque is missing an input, say so. Do not fill it in.
