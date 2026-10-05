---
name: ATMOS - TransportProperties
description: >-
  Run the 1976 dry-air transport-properties program and report its printed
  results. Use when the user wants dynamic viscosity, thermal conductivity,
  mean particle speed, kinematic viscosity, mean free path, collision
  frequency, or number density from a geometric altitude or a temperature.
  Do not recompute the numbers by hand.
---

# ATMOS - TransportProperties

Use this skill for 1976 dry-air transport properties. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Pass geometric altitude `--alt` or kinetic temperature `--temp`, not both. Altitude mode reads temperature, pressure, and density from `ATMOS - Standard1976`. Temperature mode computes viscosity, conductivity, and mean particle speed from temperature alone. Add `--pressure` with `--temp` when density-dependent quantities are needed.

Dynamic viscosity is `sutherland_viscosity`,

\[
\mu = \frac{\beta T^{3/2}}{T + S},
\]

with \(\beta = 1.458\times 10^{-6}\,\mathrm{kg/(s\cdot m\cdot K^{1/2})}\) and \(S = 110.4\,\mathrm{K}\). Thermal conductivity is `thermal_conductivity_air`,

\[
k_t = \frac{k_0 T^{3/2}}{T + C\,10^{-12/T}},
\]

with \(k_0 = 2.64638\times 10^{-3}\,\mathrm{W/(m\cdot K^{3/2})}\) and \(C = 245.4\,\mathrm{K}\). Mean particle speed is `mean_particle_speed` at \(M = M_0\).

When density is known (altitude, or temperature plus pressure), density is `atmosphere_density` at \(M_0\). Kinematic viscosity is `kinematic_viscosity`. Mean free path is `mean_free_path` with \(\sigma = 3.65\times 10^{-10}\,\mathrm{m}\). Collision frequency is `collision_frequency`. Number density is `number_density`. Viscosity and conductivity are the 1976 fits tabulated to 86 km.

## When to run

1. Use this skill when the user wants viscosity, thermal conductivity, mean particle speed, mean free path, collision frequency, or number density of dry air.
2. Convert altitude to geometric metres, temperature to kelvin, and pressure to pascals before the call. State the converted units in the reply. A bare altitude is geometric metres, not geopotential. Do not invent an altitude, a temperature, or a pressure.
3. Pass `--alt` or `--temp`, not both. If the user gives both, ask which one to use.
4. Pass `--pressure` only with `--temp`. Altitude already supplies pressure. Temperature without pressure prints only \(T\), \(\mu\), \(k_t\), and \(\bar{V}\).
5. One altitude, or one temperature (with optional pressure), is one run. Do not sweep.
6. A geometric altitude that only needs \(T\), \(p\), \(\rho\), sound speed, or scale height belongs to `ATMOS - Standard1976`.

## Flags

Run:

```text
python "skills/ATMOS - TransportProperties/transport_properties.py" --alt <m>
python "skills/ATMOS - TransportProperties/transport_properties.py" --temp <K> [--pressure <Pa>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Or `--temp` |
| `--temp` | Kinetic temperature \(T\) | K, \(> 0\) | Or `--alt` |
| `--pressure` | Pressure \(p\) | Pa, \(> 0\) | Optional with `--temp` |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. If the user gives geopotential altitude \(H\), convert with \(Z = r_0 H / (r_0 - H)\) and \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\) before the call, and say so. Temperature in Celsius uses \(T(\mathrm{K}) = t(^\circ\mathrm{C}) + 273.15\). Pressure in millibars or hectopascals uses `1 mbar = 100 Pa`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `input_mode`. `altitude` means `--alt`. `temperature` means `--temp` alone. `temperature_pressure` means `--temp` with `--pressure`.
3. Always report `T_K`, `mu_Pa_s`, `kt_W_mK`, and `Vbar_m_s`.
4. When density is known, also report `p_Pa`, `rho_kg_m3`, `nu_m2_s`, `L_m`, `nu_c_s`, and `N_m3`. `L_m` is the mean free path. `nu_c_s` is the mean collision frequency. `N_m3` is number density.
5. In altitude mode, report `Z_m` and `H_m`. State that \(Z\) is geometric.
6. If `warning` is printed, include it. That warning applies at and above 80 km, where the atmosphere program still holds \(M = M_0\).
7. If altitude or temperature is missing, both were given, or `--pressure` was used without `--temp`, say so. Do not fill them in.
