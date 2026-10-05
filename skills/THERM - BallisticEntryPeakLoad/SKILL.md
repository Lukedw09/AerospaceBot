---
name: THERM - BallisticEntryPeakLoad
description: >-
  Run the Allen-Eggers nonlifting ballistic-entry peak-load program and report
  its printed results and optional PNG. Use when the user wants peak deceleration
  and the altitude of that peak for a ballistic entry in an exponential
  atmosphere from ballistic coefficient (or mass, Cd, and area), entry speed,
  and entry flight-path angle below the local horizontal. Companion to
  stagnation heat flux; not a full trajectory. Do not redraw the plot or
  recompute the numbers by hand.
---

# THERM - BallisticEntryPeakLoad

Use this skill for Allen–Eggers closed-form peak drag load on a nonlifting ballistic entry in an exponential atmosphere. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Ballistic coefficient is `ballistic_coefficient`:

\[
B = \frac{m}{C_D A}
\]

Pass `--beta` for \(B\) directly, or pass `--mass`, `--cd`, and `--area`. Density is `exponential_atmosphere_density`, \(\rho=\rho_{\mathrm{ref}}\exp(-(Z-Z_{\mathrm{ref}})/H)\). Default Earth atmosphere is the TN 4047 fit: \(\rho_{\mathrm{ref}}=1.752288\,\mathrm{kg/m}^{3}\) at \(Z_{\mathrm{ref}}=0\) with \(H=6705.6\,\mathrm{m}\).

When the formal peak is above the surface, peak deceleration is `allen_eggers_peak_deceleration`:

\[
a_{\max} = \frac{V_E^{2}\sin\theta_E}{2 e H}
\]

Altitude is `allen_eggers_peak_deceleration_altitude`, speed there is `allen_eggers_speed_at_peak_deceleration` \(V_1=V_E/\sqrt{e}\), and density is `allen_eggers_density_at_peak_deceleration`. If that altitude is below the surface, the program uses the heavy-vehicle surface records `allen_eggers_surface_speed` and `allen_eggers_surface_deceleration` at \(Z=0\).

Method name is `allen_eggers`. This skill does not integrate a trajectory, model lift, or compute stagnation heat flux (use `THERM - SonicStagnationHeatFlux` for flux at a freestream state).

## When to run

1. Use this skill when the user wants ballistic-entry peak deceleration (peak load), the altitude of that peak, or the Allen–Eggers exponential-atmosphere closed form for a nonlifting entry.
2. Convert inputs to SI before the call (kg/m², m/s, rad, m, kg, m²). State the converted units in the reply. Do not invent ballistic coefficient, mass, \(C_D\), area, entry speed, or flight-path angle.
3. Pass `--speed` and `--gamma`. Pass `--beta`, or pass all of `--mass`, `--cd`, and `--area`. Do not pass disagreeing `--beta` with mass/\(C_D\)/area.
4. Optional atmosphere: `--scale-height`, `--rho-ref`, `--z-ref`. An omitted set is the TN 4047 Earth default. Pass a custom set together when overriding; do not mix a partial override with the default silently—if the user gave only one atmosphere constant, ask for the others or use all defaults.
5. Pass `--out` only when the user wants the PNG of peak load versus entry angle at fixed speed and \(B\). Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for lifting entry, skip trajectories, full ODE trajectories, or stagnation heating rates.

## Flags

Run:

```text
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --speed <m/s> --gamma <rad> (--beta <kg/m^2> | --mass <kg> --cd <CD> --area <m^2>) [--scale-height <m>] [--rho-ref <kg/m^3>] [--z-ref <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | Entry speed \(V_E\) | m/s, \(> 0\) | Required |
| `--gamma` | Entry flight-path angle below the local horizontal \(\theta_E\) | rad, \(0 < \theta_E \le \pi/2\) | Required |
| `--beta` | Ballistic coefficient \(B=m/(C_D A)\) | kg/m², \(> 0\) | One of `--beta` or mass/\(C_D\)/area |
| `--mass` | Vehicle mass \(m\) | kg, \(> 0\) | With `--cd` and `--area` when `--beta` omitted |
| `--cd` | Drag coefficient \(C_D\) | dimensionless, \(> 0\) | With `--mass` and `--area` |
| `--area` | Reference area \(A\) | m², \(> 0\) | With `--mass` and `--cd` |
| `--scale-height` | Density scale height \(H\) | m, \(> 0\) | Optional; default Allen–Eggers Earth \(6705.6\,\mathrm{m}\) |
| `--rho-ref` | Reference density \(\rho_{\mathrm{ref}}\) | kg/m³, \(> 0\) | Optional; default \(1.752288\,\mathrm{kg/m}^{3}\) |
| `--z-ref` | Reference altitude for \(\rho_{\mathrm{ref}}\) | m | Optional; default \(0\) |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Speed in km/s uses `1 km/s = 1000 m/s`. Angle in degrees uses \(\pi/180\). Scale height or altitude in kilometres uses `1 km = 1000 m`. Ballistic coefficient in lb/ft² is not converted by the program; convert to kg/m² first (`1 lb/ft² ≈ 4.88243 kg/m²` for mass-based \(B\) after converting weight to mass carefully—prefer SI).

When `--out` is passed, the program writes one PNG. The plot title is `Ballistic entry peak load`. The curve is peak deceleration in \(g_0\) versus entry angle (degrees) at the fixed entry speed and ballistic coefficient. The square marks the user’s angle. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `method`, `B_kg_m2`, `Ve_m_s`, `gamma_rad`, `gamma_deg`, `H_m`, `rho_ref_kg_m3`, `Z_ref_m`, `a_peak_m_s2`, `a_peak_g`, `Z_peak_m`, and `peak_regime`.
4. Report `V_peak_m_s` and `rho_peak_kg_m3` when they are printed. `altitude` means the closed-form peak is above the surface. `surface` means the heavy-vehicle sea-level case.
5. Report `B_source`: `flag` when `--beta` was given; `mass_cd_area` when mass, \(C_D\), and area were used.
6. If speed, flight-path angle, or a ballistic-coefficient path is missing, say so. Do not fill them in.
