---
name: ASTRO - MultiBurnLeoRaise
description: >-
  Run the multi-burn LEO-raise program and report its printed results and PNG.
  Use when the user wants a finite-thrust raise from a parking LEO to a higher
  circular LEO, with gravity loss, steered delta-v, burn arcs, time of flight,
  or an optional inclination change, given a parking state or classical
  elements, a target circular altitude and inclination, and a thrust profile.
  Pass --html when they want the 3D viewer. Do not redraw the trajectory or
  recompute the numbers by hand.
---

# ASTRO - MultiBurnLeoRaise

Use this skill for a finite-thrust multi-burn raise from a parking LEO to a higher circular LEO, with gravity loss and an optional plane-change Δv. Run the program once; quote its stdout and include its PNG. Do not redraw the trajectory or recompute the numbers by hand. Pass `--html` when the user wants the 3D viewer. Give `viewer:` as a markdown link when it is printed.

Assumptions (also printed by the program): spherical planet, inverse-square gravity, and no drag or third body. Coasts between burns are Keplerian. Each burn is finite-thrust: raise burns thrust along the velocity near periapsis; the final apoapsis burn steers toward circular velocity in the target plane, so the impulsive Hohmann Δv is not recovered. Gravity loss is the path integral \(g\sin\theta\) along the burn using the velocity direction (orbital form of `gravity_loss_definition`). An optional target inclination different from the parking inclination adds a plane-change component; when `--i-target` is omitted the raise keeps the parking inclination. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). A radius is the distance from the center. An altitude is geometric height above \(R_0\). The frame matches OrbitalParameters: \(+Z\) is the polar axis, the \(XY\) plane is the equator, and \(\Omega\) is measured from \(+X\).

The parking orbit is the departure state. The arrival orbit is circular at `--alt-target` (or `--r-target`) with inclination `--i-target` when given. The program splits the raise into one or more powered arcs separated by coasts. Burn count and arc placement follow the program’s multi-burn LEO-raise policy for the given thrust profile; do not invent a burn schedule by hand.

## When to run

1. Parking classical elements: pass `--a`, `--e`, `--i`, `--raan`, `--aop`, and exactly one of `--nu` or `--M`, plus the target and the thrust profile.
2. Parking inertial state: pass `--rx`, `--ry`, `--rz`, `--vx`, `--vy`, `--vz`, plus the target and the thrust profile.
3. Pass one parking mode. Do not combine elements and a state.
4. Target: pass `--alt-target` or `--r-target`, not both. Pass `--i-target` when the user gives a final inclination. If `--i-target` is omitted, keep the parking inclination (coplanar raise).
5. Thrust profile: pass `--thrust` with `--isp` and `--m0`, or `--profile` with a thrust-vs-time table path. Pass `--mf` or `--mp` when the user gives burnout or propellant mass; otherwise the program integrates until the circular target is met or propellant is exhausted.
6. Pass `--burns` only when the user names a burn count (\(\ge 2\)). Omit it to use the program default for that thrust level. Do not pass `--burns 1`; a raise needs at least one raise burn plus circularization.
7. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
8. Pass `--html` when the user wants the self-contained 3D HTML viewer, and `--open` only when they ask to open it.
9. Convert inputs to SI and radians before the call. State the converted units in the reply. Do not invent a missing parking state, target altitude or radius, thrust, \(I_s\), or mass.

## Flags

Run:

```text
python "skills/ASTRO - MultiBurnLeoRaise/multi_burn_leo_raise.py" --a <m> --e <e> --i <rad> --raan <rad> --aop <rad> (--nu <rad> | --M <rad>) (--alt-target <m> | --r-target <m>) [--i-target <rad>] --thrust <N> --isp <s> --m0 <kg> [--mf <kg> | --mp <kg>] [--burns <n>] [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - MultiBurnLeoRaise/multi_burn_leo_raise.py" --rx <m> --ry <m> --rz <m> --vx <m/s> --vy <m/s> --vz <m/s> (--alt-target <m> | --r-target <m>) [--i-target <rad>] --thrust <N> --isp <s> --m0 <kg> [--mf <kg> | --mp <kg>] [--burns <n>] [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - MultiBurnLeoRaise/multi_burn_leo_raise.py" (--a ... | --rx ...) (--alt-target <m> | --r-target <m>) [--i-target <rad>] --profile <path> --m0 <kg> [--mf <kg> | --mp <kg>] [--burns <n>] [--R0 <m>] [--out <png>] [--html] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Parking semi-major axis | m | Elements mode |
| `--e` | Parking eccentricity | dimensionless, \(\ge 0\) | Elements mode |
| `--i` | Parking inclination | rad, \(0 \le i \le \pi\) | Elements mode |
| `--raan` | Parking longitude of the ascending node, \(\Omega\) | rad | Elements mode |
| `--aop` | Parking argument of periapsis, \(\omega\) | rad | Elements mode |
| `--nu` | Parking true anomaly at the printed epoch | rad | Elements mode, or `--M` |
| `--M` | Parking mean anomaly at the printed epoch. Ellipse only. | rad | Elements mode, or `--nu` |
| `--rx`, `--ry`, `--rz` | Parking inertial position at the printed epoch | m | State mode, all three |
| `--vx`, `--vy`, `--vz` | Parking inertial velocity at the printed epoch | m/s | State mode, all three |
| `--alt-target` | Target circular geometric altitude | m, \(\ge 0\) | Or `--r-target` |
| `--r-target` | Target circular radius, from the center | m, \(\ge R_0\) | Or `--alt-target` |
| `--i-target` | Target circular inclination. Omitted keeps parking \(i\). | rad, \(0 \le i \le \pi\) | Optional |
| `--thrust` | Constant thrust magnitude | N, \(> 0\) | Or `--profile` |
| `--isp` | Vacuum specific impulse \(I_s\) | s, \(> 0\) | With `--thrust` |
| `--m0` | Ignition mass | kg, \(> 0\) | Required |
| `--mf` | Burnout mass | kg, \(> 0\), \(< m_0\) | Optional; or `--mp`. If both omitted, mass floor is \(0.02\,m_0\) |
| `--mp` | Propellant mass | kg, \(> 0\), \(< m_0\) | Optional; or `--mf`. If both omitted, mass floor is \(0.02\,m_0\) |
| `--profile` | Thrust-vs-time table path (time_s, thrust_N[, isp_s]) | — | Or `--thrust` |
| `--burns` | Number of powered arcs (raise burns plus circularization) | integer, \(\ge 2\) | Optional. Program default if omitted |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional |
| `--html` | Write the 3D HTML viewer beside the PNG | — | Optional |
| `--open` | Open the HTML viewer in a browser | — | Optional |

A bare length is metres. Kilometres use `1 km = 1000 m`. Statute miles use `1 mi = 1609.344 m`. Nautical miles use `1 nmi = 1852 m`. Element angles and `--i-target` are radians. Degrees use \(\pi/180\). Mass in pounds-mass uses `1 lbm = 0.45359237 kg`. Specific impulse is already seconds. Thrust in lbf uses `1 lbf = 4.4482216152605 N`. If the user gives a target altitude, convert with \(r = R_0 + h\) only when passing `--r-target`; prefer `--alt-target` when they spoke in altitude. Do not invent a second target, a burn count, or a planetary radius.

Every successful run writes one PNG. The plot title is `Multi-burn LEO raise`. Axes are kilometres. Parking and target circles (or the parking ellipse and target circle) are drawn; powered arcs are solid in the burn color; coasts are dashed. Each burn is marked with a steered \(\Delta v\) sense. The HTML viewer is written only with `--html` or `--open`. Play starts on. The spacecraft parks on the departure orbit, flies each burn arc under thrust, coasts between burns, and circularizes on the target. In the HTML viewer the full burn/coast path is drawn faded and the path already flown is a solid trail that grows with playtime. `graph:` is the PNG. `viewer:` is the HTML when it is written.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. If `viewer:` is printed, give it as a markdown link to that HTML file. Do not draw a second figure.
3. Report `mode`. `elements` started from classical elements. `state` started from position and velocity.
4. Report `R0_m`, `R0_source`, `g0_m_s2`, and `mu_m3_s2`. `default` means the Earth radius from the circular-orbit formula.
5. Report parking `r_park_m` / elements or state as printed, and target `r_target_m`, `h_target_m`, `i_park_rad`, `i_target_rad`, and `i_final_rad` (achieved inclination from the final state).
6. Report `thrust_profile`: `constant` or `table`. Report `thrust_N`, `isp_s`, `c_m_s`, `m0_kg`, and `mf_kg` or propellant used when printed.
7. Report `n_burns`. For each burn \(k\), report `burn_k_t_start_s`, `burn_k_t_end_s`, `burn_k_dt_s`, `burn_k_nu_start_rad`, `burn_k_nu_end_rad`, `burn_k_dv_steered_m_s`, and `burn_k_gravity_loss_m_s` when printed.
8. Report `dv_steered_m_s` (sum of steered burn Δv), `dv_gravity_loss_m_s`, `dv_plane_change_m_s`, and `dv_total_m_s`. When the raise is coplanar, `dv_plane_change_m_s` is `0`. `dv_total_m_s` is the steered propulsive total the program prints (including gravity-loss accounting as defined in stdout).
9. Report `tof_s` for the full raise from the parking epoch through the final circularization, and `tof_coast_s` / `tof_burn_s` when printed.
10. Report `a_target_m`, `e_target`, and `v_circular_target_m_s` for the arrival circle.
11. Repeat `warning` when it is printed (propellant exhaustion before circularization, circularization tolerance not met, trajectory leaving the elliptical domain, periapsis inside \(R_0\), thrust too low for the requested burn count, or a target below the parking orbit).
12. If the parking state, target altitude or radius, thrust profile, \(I_s\), or ignition mass is missing, say so. Do not fill it in. Point impulsive coplanar transfers to `ASTRO - HohmannTransfer` or `ASTRO - BiellipticTransfer`, and a pure impulsive inclination change to `ASTRO - PlaneChangeImpulse`.
