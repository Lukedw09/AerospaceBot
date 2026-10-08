---
name: THERM - LiftingEntryTrajectory
description: >-
  Run the planar point-mass lifting-entry program and report its printed
  results. Use when the user wants a 3-degree-of-freedom entry with lift
  and bank: peak aerodynamic load, where that peak happens, and whether the
  vehicle skips back out, including above circular speed. bank_schedule is
  a list of {t_s, bank_deg} objects or that same list as a JSON string.
  heading_deg is the inertial heading from north. Pass out only when a PNG
  is wanted; omit it and no figure is written. Unknown parameters are
  rejected. Do not redraw the plot or recompute the numbers by hand.
---

# THERM - LiftingEntryTrajectory

Use this skill for a planar point-mass entry with constant ballistic coefficient and lift-to-drag ratio. Flight-path angle is positive below the local horizontal, the same convention as `THERM - BallisticEntryPeakLoad`. The program integrates the trajectory, reports the peak aerodynamic load, and says whether the path skips back above the skip altitude. It is valid above circular speed. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Pass only values the user gave, after converting to SI. Do not invent speed, flight-path angle, altitude, lift-to-drag ratio, ballistic coefficient, or bank.

Ballistic coefficient is \(B = m/(C_D A)\). Pass `--beta`, or pass `--mass`, `--cd`, and `--area`. Bank is either a constant `--bank-deg` or a `--bank-schedule`: a list of objects `{"t_s": number, "bank_deg": number}`, or that same list as a JSON string. The list is sorted by time, linearly interpolated, and held at the last value. Do not pass pair arrays.

The default planet is the catalogue Earth radius and \(\mu = g_0 R_0^2\). Pass `--radius` or `--mu` only when the user gave them. The default atmosphere is the TN 4047 exponential Earth fit, the same all-three-or-none override as `THERM - BallisticEntryPeakLoad`. `--atmosphere us1976` uses `ATMOS - Standard1976` at or below 86 km and `ATMOS - DensityAbove86km` above 86 km.

Optional Earth rotation needs `--latitude-deg` and `--heading-deg` together. `--heading-deg` is the inertial heading from north. `--omega` defaults to \(7.2921159\times 10^{-5}\,\mathrm{rad/s}\) only in that case. The program converts the inertial entry speed, flight-path angle, and heading to air-relative values, prints `heading_air_deg` with those entry values, integrates in the rotating frame, and holds latitude and the inertial heading constant. Without those inputs the run is non-rotating.

Pass only parameters named on this skill. An unknown parameter is an error that names it and lists the valid parameters. Do not pass `integrator`; omit `--dt` for adaptive RK45, or pass `--dt` to select fixed-step RK4. Program errors use the parameter names `scale_height`, `rho_ref`, `z_ref`, and `beta`.

This is not the Allen–Eggers closed form and not the equilibrium-glide closed form. Those stay on their own skills.

## When to run

1. Use this skill when the user wants a lifting or banked entry trajectory, the peak aerodynamic load and where it occurs, or a skip-out check, including a supercircular entry.
2. Convert inputs to SI before the call (m/s, rad, m, kg/m², kg, m²). State the converted units in the reply. Bank angles stay in degrees because that flag is in degrees. Do not invent any vehicle or trajectory input.
3. Pass `--speed`, `--gamma`, `--altitude`, and `--lod`. Pass `--beta`, or all of `--mass`, `--cd`, and `--area`. Do not pass a `--beta` that disagrees with mass, \(C_D\), and area.
4. Pass exactly one of `--bank-deg` or `--bank-schedule`. `--bank-schedule` may be a list of `{t_s, bank_deg}` objects or a JSON string of that list. Do not pass pair arrays.
5. Pass `--latitude-deg` and `--heading-deg` together only when the user wants Earth rotation. `--heading-deg` is the inertial heading from north. Pass `--omega` only with those two. Report `heading_air_deg` with the other air-relative entry values.
6. Pass `--atmosphere us1976` only when the user asked for the 1976 atmosphere. For the exponential fit, pass `--scale-height`, `--rho-ref`, and `--z-ref` together or omit all three.
7. Pass `--end-altitude`, `--max-time-s`, or `--skip-altitude` only when the user set them. Omitted values are program defaults: stop at 0 m, 3000 s, and skip at the entry altitude.
8. Pass `--out` only when the user wants the PNG. Omit it and the program does not write a figure or print `graph:`. Do not invent a plot path. The hosted tool returns the PNG only when `out` is passed.
9. Do not use this skill for a nonlifting Allen–Eggers peak, an equilibrium-glide closed form, or stagnation heat flux.

## Flags

Run:

```text
python "skills/THERM - LiftingEntryTrajectory/lifting_entry_trajectory.py" --speed <m/s> --gamma <rad> --altitude <m> --lod <L/D> (--beta <kg/m^2> | --mass <kg> --cd <CD> --area <m^2>) (--bank-deg <deg> | --bank-schedule <json>) [--radius <m>] [--mu <m^3/s^2>] [--atmosphere exponential|us1976] [--scale-height <m>] [--rho-ref <kg/m^3>] [--z-ref <m>] [--end-altitude <m>] [--max-time-s <s>] [--skip-altitude <m>] [--latitude-deg <deg>] [--heading-deg <deg>] [--omega <rad/s>] [--rtol <tol>] [--dt <s>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | Entry speed. Inertial when rotation is on | m/s, \(> 0\) | Required |
| `--gamma` | Entry flight-path angle, positive below the local horizontal | rad, \([-\pi/2, \pi/2]\) | Required |
| `--altitude` | Entry-interface altitude | m, above `--end-altitude` | Required |
| `--lod` | Lift-to-drag ratio, constant | dimensionless, \(\ge 0\) | Required |
| `--beta` | Ballistic coefficient \(B=m/(C_D A)\) | kg/m², \(> 0\) | One of `--beta` or mass/\(C_D\)/area |
| `--mass` | Vehicle mass \(m\) | kg, \(> 0\) | With `--cd` and `--area` when `--beta` omitted |
| `--cd` | Drag coefficient \(C_D\) | dimensionless, \(> 0\) | With `--mass` and `--area` |
| `--area` | Reference area \(A\) | m², \(> 0\) | With `--mass` and `--cd` |
| `--bank-deg` | Constant bank angle | deg | One of `--bank-deg` or `--bank-schedule` |
| `--bank-schedule` | List of `{"t_s", "bank_deg"}` objects, or that list as JSON, sorted by time | s, deg | One of `--bank-deg` or `--bank-schedule` |
| `--radius` | Planet radius | m, \(> 0\) | Optional. Default \(6.3742\times 10^{6}\) |
| `--mu` | Gravitational parameter | m³/s², \(> 0\) | Optional. Default \(g_0 R_0^2\) |
| `--atmosphere` | `exponential` or `us1976` | — | Optional. Default `exponential` |
| `--scale-height` | Density scale height \(H\) | m, \(> 0\) | Optional, with `--rho-ref` and `--z-ref` |
| `--rho-ref` | Reference density | kg/m³, \(> 0\) | Optional, with the other atmosphere flags |
| `--z-ref` | Altitude of the reference density | m | Optional, with the other atmosphere flags |
| `--end-altitude` | Stop when altitude falls to this | m | Optional. Default \(0\) |
| `--max-time-s` | Stop time | s, \(> 0\) | Optional. Default \(3000\) |
| `--skip-altitude` | Skip-out altitude | m | Optional. Default is the entry altitude |
| `--latitude-deg` | Geodetic latitude, held constant | deg, \([-90, 90]\) | Optional, with `--heading-deg` |
| `--heading-deg` | Inertial heading from north, held constant | deg | Optional, with `--latitude-deg` |
| `--omega` | Planet rotation rate | rad/s | Optional with rotation. Default \(7.2921159\times 10^{-5}\) |
| `--rtol` | Adaptive RK45 relative tolerance | — | Optional. Default \(10^{-6}\). Not with `--dt` |
| `--dt` | Fixed RK4 step | s, \(> 0\) | Optional. Selects RK4. Not with `--rtol` |
| `--out` | PNG path. Omit it and no figure is written | — | Optional. Omit unless the user wants the figure. |

An omitted exponential atmosphere is the TN 4047 Earth fit: \(H = 6705.6\,\mathrm{m}\), \(\rho_{\mathrm{ref}} = 1.752288\,\mathrm{kg/m}^{3}\) at \(Z_{\mathrm{ref}} = 0\).

When `--out` is passed, the program writes one PNG with two panels: aerodynamic load in \(g\) versus time, and altitude versus speed. The plot title is `Lifting entry trajectory`. The square marks the peak load. `graph:` is the PNG. Without `--out` there is no PNG and no `graph:` line.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `method`, `assumptions`, `B_kg_m2`, `peak_g`, `t_peak_s`, `Z_peak_m`, `V_peak_m_s`, `load_peaks`, `min_altitude_m`, `skip_out`, `end_reason`, `V_final_m_s`, `gamma_final_rad`, `altitude_final_m`, `downrange_m`, `flight_time_s`, and `convergence_peak_g_rel`.
4. When `skip_out` is true, also report `t_skip_s`.
5. When rotation is on, report `speed_inertial_m_s`, `gamma_inertial_rad`, `speed_air_m_s`, `gamma_air_rad`, and `heading_air_deg`. `heading_deg` is the inertial heading from north. Latitude and that inertial heading were held constant.
6. If a required input or the bank choice is missing, say so. Do not fill it in.
