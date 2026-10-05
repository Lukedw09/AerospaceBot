---
name: ROCKET - BasicTrajectoryLossesFromBodySurface
description: >-
  Run the powered-ascent loss program and report its printed results and PNG.
  Use when the user wants vacuum delta-v, gravity loss, drag loss, steering
  loss, or burnout speed, flight-path angle, and altitude of a simplified
  burn from a spherical body's surface. Constant flight-path angle is closed
  form; a gravity-turn kick integrates the ODE with thrust along velocity.
  Do not redraw the plot or recompute the numbers by hand.
---

# ROCKET - BasicTrajectoryLossesFromBodySurface

Use this skill for a simplified powered ascent from a spherical surface. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Ideal vacuum delta-v is `delta_v_vacuum` at \(c = I_s g_{0,\mathrm{std}}\) with \(g_{0,\mathrm{std}} = 9.80665\,\mathrm{m/s}^{2}\). Path acceleration is `powered_path_acceleration`,

\[
A = \frac{T}{m}-\frac{D}{m}-g\sin\theta,
\]

with \(\theta\) from the local horizontal. Gravity, drag, and steering losses are `gravity_loss_definition`, `drag_loss_definition`, and `steering_loss_definition`. Burnout speed from rest is `burnout_speed_from_losses`. Vacuum thrust is \(T=\dot{m}c\) and does not change with ambient pressure.

Pass `--gamma` or `--kick`, not both. `--gamma` holds \(\theta\) constant. With no drag or a constant drag force that case is `constant_angle_speed` (or `constant_angle_speed_const_drag`) with \(g\) frozen at ignition. `--kick` is the instantaneous pitch from local vertical. The program holds that thrust axis until the speed is \(50\,\mathrm{m/s}\), then thrust stays along the velocity and the path follows `gravity_turn_angle_rate` on the sphere. Steering loss is then zero.

Drag is omitted, `--drag` (constant force), `--cd` with `--area` and `--rho` (quadratic drag at frozen density), or `--cd` with `--area` and a density model. Off-nominal temperature or humidity uses `AERO - DensityAndPressureAltitude` at the 1976 station pressure with a constant temperature offset. Non-Earth density is `--rho0` with `--scale-height`, \(\rho=\rho_0\exp(-Z/H)\).

The figure plots geometric altitude against downrange \(R\phi\) on the density field used for drag, or the 1976 layers on Earth when that atmosphere is loaded.

## When to run

1. Use this skill when the user wants gravity, drag, or steering losses, vacuum delta-v, or burnout speed, flight-path angle, radius, or altitude for a burn from a spherical surface.
2. Convert inputs to SI before the call (kg, s, rad, m, m³/s², N, kg/m³, K). State the converted units in the reply. Do not invent mass, \(I_s\), burn time, path angle, drag, or a planet.
3. Pass `--mf` or `--mp`, not both. Pass `--tb` or `--mdot` (both is allowed when they match the propellant mass). Pass `--gamma` or `--kick`, not both. Angles are radians.
4. Pass `--r` or `--alt`, not both. Pass `--mu` or `--g0`, not both. An omitted planet is Earth: 1976 radius \(r_0=6.356766\times 10^{6}\,\mathrm{m}\) and \(g_0=9.80665\,\mathrm{m/s}^{2}\). `--g0` is surface gravity at `--radius`, not the \(I_s\) conversion.
5. Pass `--drag` or `--cd`, not both. `--cd` needs `--area`. `--oat` needs geometric altitude (default surface or `--alt`) and must not be paired with `--rho`. `--rho0` and `--scale-height` go together and must not be paired with `--rho` or `--oat`.

## Flags

Run:

```text
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --m0 <kg> (--mf <kg> | --mp <kg>) --isp <s> (--tb <s> | --mdot <kg/s>) (--gamma <rad> | --kick <rad>) [--radius <m>] [--r <m> | --alt <m>] [--mu <m^3/s^2> | --g0 <m/s^2>] [--drag <N> | --cd <CD> --area <m^2>] [--rho <kg/m^3> | --oat <K> [--rh <phi>] | --rho0 <kg/m^3> --scale-height <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--m0` | Ignition mass \(m_0\) | kg, \(> 0\) | Required |
| `--mf` | Burnout mass \(m_f\) | kg, \(> 0\), \(< m_0\) | Or `--mp` |
| `--mp` | Propellant mass \(m_p\) | kg, \(> 0\), \(< m_0\) | Or `--mf` |
| `--isp` | Vacuum specific impulse \(I_s\) | s, \(> 0\) | Required |
| `--tb` | Burn time \(t_b\) | s, \(> 0\) | Or `--mdot` |
| `--mdot` | Propellant mass flow \(\dot{m}\) | kg/s, \(> 0\) | Or `--tb` |
| `--gamma` | Constant flight-path angle above the local horizontal | rad, \(0\) to \(\pi/2\) | Or `--kick` |
| `--kick` | Gravity-turn kick from local vertical | rad, \(0\) to \(\pi/2\) | Or `--gamma` |
| `--radius` | Spherical body radius \(R\) | m, \(> 0\) | Optional. Default 1976 \(r_0\) |
| `--r` | Ignition radius | m, \(\ge R\) | Optional; or `--alt` |
| `--alt` | Geometric ignition altitude \(Z\) | m, \(\ge 0\) | Optional; or `--r` |
| `--mu` | Gravitational parameter \(\mu\) | m³/s², \(> 0\) | Optional; or `--g0` |
| `--g0` | Surface gravity at \(R\) | m/s², \(> 0\) | Optional; or `--mu` |
| `--drag` | Constant drag force | N, \(\ge 0\) | Optional; not with `--cd` |
| `--cd` | Drag coefficient \(C_D\) | dimensionless, \(> 0\) | Optional; needs `--area` |
| `--area` | Drag reference area \(S\) | m², \(> 0\) | With `--cd` |
| `--rho` | Density with no atmospheric variation | kg/m³, \(> 0\) | Optional |
| `--oat` | Outside air temperature at ignition | K, \(> 0\) | Optional, with 1976 altitude |
| `--rh` | Relative humidity \(\phi\) | dimensionless, \(0\) to \(1\) | Optional, with `--oat`. Omitted with `--oat` is dry |
| `--rho0` | Non-Earth surface density | kg/m³, \(> 0\) | With `--scale-height` |
| `--scale-height` | Exponential density scale height \(H\) | m, \(> 0\) | With `--rho0` |
| `--out` | PNG path | — | Optional |

A mass in pounds-mass uses `1 lbm = 0.45359237 kg`. Specific impulse is already seconds. Burn time is seconds. Angles in degrees use `rad = deg * pi/180`. Altitude in feet uses `1 ft = 0.3048 m`. A relative humidity in percent is the fraction on 0 to 1. `--g0` is local surface gravity; do not pass the \(I_s\) standard \(9.80665\,\mathrm{m/s}^{2}\) as a planet gravity unless that is the surface value.

Every successful run writes one PNG. The plot title is `Powered ascent`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The vertical axis is geometric altitude. The horizontal axis is downrange \(R\phi\). The background is density when a density model was used. Squares and circles mark ignition and burnout.
3. Report `method`. `constant_angle` is `--gamma`. `gravity_turn` is `--kick`. Report `solver`. `closed_form` is the constant-angle analytic speed. `ode` is the gravity turn, or constant angle when drag depends on speed or density.
4. Report masses, \(t_b\), \(\dot{m}\), \(I_s\), \(c\), thrust, body radius, ignition radius and altitude, \(\mu\), and local gravity at the surface and at ignition.
5. Report `gamma_rad` for a constant angle, or `kick_rad` and `gamma_ign_rad` for a gravity turn. Report `drag_kind` and the drag inputs that were printed. Report `density_source`.
6. Report `dv_ideal_m_s`, `gravity_loss_m_s`, `drag_loss_m_s`, `steering_loss_m_s`, `V_bo_m_s`, `gamma_bo_rad`, `r_bo_m`, and `Z_bo_m`. Steering loss is zero while thrust is along the velocity.
7. If `warning` is printed, include it. Burnout speed not positive, a path that reaches the local horizontal before burnout, remaining on the surface, or ignition thrust not greater than local weight are those warnings.
8. If ignition mass, specific impulse, burnout or propellant mass, burn time or mass flow, or both `--gamma` and `--kick` are missing, say so. Do not fill them in.
