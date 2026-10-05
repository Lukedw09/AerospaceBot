---
name: THERM - SonicStagnationHeatFlux
description: >-
  Run the stagnation-point convective heat-flux program and report its printed
  results and PNG. Use when the user wants blunt-nose stagnation convective heat
  flux, freestream dynamic pressure, optional radiative-equilibrium wall
  temperature from emissivity, or optional hot-wall heat-transfer coefficient
  form from wall temperature, from freestream density and speed or 1976 altitude
  and speed plus nose radius. Do not redraw the plot or recompute the numbers by
  hand.
---

# THERM - SonicStagnationHeatFlux

Use this skill for Sutton–Graves stagnation-point convective heating on an axisymmetric blunt nose in Earth air. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Cold-wall flux (default) is `stagnation_convective_heat_flux_velocity`:

\[
\dot{q} = k \sqrt{\frac{\rho}{R_n}}\, V^{3}
\]

with Earth-air \(k = K/(2\sqrt{101325})\) and \(K = 0.1113\,\mathrm{kg/(s\cdot m^{3/2}\cdot atm^{1/2})}\) from NASA TR R-376 Table II.

Optional `--wall-temp` uses the heat-transfer coefficient form `stagnation_convective_heat_flux`:

\[
\dot{q} = K \sqrt{\frac{p_s}{R_n}}\,(h_s - h_w)
\]

with Newtonian \(p_s = \rho V^{2}\) in atmospheres, \(h_s = c_p T + V^{2}/2\) when temperature is known (otherwise \(h_s = V^{2}/2\)), and \(h_w = c_p T_w\). Dynamic pressure is `freestream_dynamic_pressure`, \(q = \frac12\rho V^{2}\).

Optional `--emissivity` prints `radiative_equilibrium_wall_temperature`, \(T_w = (\dot{q}/(\varepsilon\sigma))^{1/4}\) with the CODATA 2022 Stefan–Boltzmann constant. When altitude or `--temperature` supplies static \(T\), the program also prints adiabatic stagnation temperature \(T_t = T + V^{2}/(2 c_p)\).

This skill does not model dissociation of molecules, ionization, or shock-layer radiation beyond the Sutton–Graves air coefficient. The printed `warning` states that limit.

## When to run

1. Use this skill when the user wants stagnation convective heat flux on a blunt nose, dynamic pressure at that freestream state, radiative-equilibrium wall temperature from emissivity, or the hot-wall coefficient form from a wall temperature.
2. Convert inputs to SI before the call (m/s, m, kg/m³, K). State the converted units in the reply. Do not invent density, altitude, speed, nose radius, wall temperature, or emissivity.
3. Pass `--speed` and `--nose`. Pass exactly one of `--alt` or `--rho`.
4. Pass `--wall-temp` only when the user gave a wall temperature for the coefficient form. Pass `--temperature` only with `--rho` when they gave freestream static temperature; `--alt` already supplies 1976 \(T\).
5. Pass `--emissivity` only when the user wants radiative-equilibrium wall temperature.
6. Pass `--mach-axis` only when the user wants the PNG x-axis in freestream Mach. That needs local sound speed from `--alt` or `--temperature` with `--rho`. Without temperature, omit `--mach-axis` and keep speed in m/s.
7. Do not use this skill for Fay–Riddell with Lewis-number tables, shock-layer radiation (Tauber–Sutton), ablating walls, or atmospheres other than Earth air.

## Flags

Run:

```text
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed <m/s> --nose <m> (--rho <kg/m^3> | --alt <m>) [--wall-temp <K>] [--temperature <K>] [--emissivity <eps>] [--mach-axis] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--speed` | Freestream speed \(V\) | m/s, \(> 0\) | Required |
| `--nose` | Effective nose radius \(R_n\) | m, \(> 0\) | Required |
| `--rho` | Freestream density \(\rho\) | kg/m³, \(> 0\) | One of `--rho` or `--alt` |
| `--alt` | Geometric altitude \(Z\) on the 1976 standard | m, 0 to 86000 | One of `--rho` or `--alt` |
| `--wall-temp` | Wall temperature \(T_w\) for the coefficient form | K, \(> 0\) | Optional |
| `--temperature` | Freestream static temperature \(T\) | K, \(> 0\) | Optional, only with `--rho` |
| `--emissivity` | Surface emissivity \(\varepsilon\) | dimensionless, \(0 < \varepsilon \le 1\) | Optional |
| `--mach-axis` | Plot freestream Mach on the x-axis | flag | Optional. Needs `--alt` or `--temperature`. |
| `--out` | PNG path | — | Optional. Default is `sonic_stagnation_heat_flux.png` in this skill folder. |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. Speed in km/s uses `1 km/s = 1000 m/s`. Nose radius in centimetres uses `1 cm = 0.01 m`.

Every successful run writes one PNG. The plot title is `Sonic stagnation heat flux`. The curve is convective heat flux versus freestream speed (m/s) at the fixed density and nose radius, or versus freestream Mach when `--mach-axis` is set. The vertical axis is kW/m². The square is the operating point. Local sound speed is \(a = \sqrt{\gamma R T}\) with 1976 dry-air \(R\) and \(\gamma = 1.4\). Printed `q_dot_W_m2` stays in W/m².

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `rho_kg_m3`, `V_m_s`, `Rn_m`, `q_dyn_Pa`, `q_dot_W_m2`, and `flux_form`. `velocity` means the cold-wall \(V^{3}\) form. `heat_transfer_coefficient` means `--wall-temp` was used.
4. Report `density_source` and `Z_m` when altitude was used. Report `T_K`, `Tt_K`, `a_m_s`, and `M` when they are printed.
5. Report `x_axis`: `speed` means m/s; `mach` means `--mach-axis` was used.
6. Report `Tw_K`, `hs_J_kg`, `hw_J_kg`, and `ps_atm` when the coefficient form was used.
7. Report `emissivity` and `Tw_rad_eq_K` when they are printed.
8. Include the printed `warning` about dissociation and high-enthalpy limits.
9. If speed, nose radius, or a density path is missing, say so. If `--mach-axis` was asked without temperature, say sound speed is unavailable. Do not fill them in.
