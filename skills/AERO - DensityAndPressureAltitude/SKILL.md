---
name: AERO - DensityAndPressureAltitude
description: >-
  Run the density and pressure altitude program and report its printed
  results. Use when the user wants pressure altitude, density altitude,
  dry or moist density, or speed of sound from station pressure and outside
  air temperature, with optional relative humidity and equivalent airspeed.
  Do not recompute the numbers by hand and do not use the NASA Glenn
  three-zone fit.
---

# AERO - DensityAndPressureAltitude

Use this skill for one station condition. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Station pressure and outside air temperature are the inputs. An omitted `--rh` is dry air, so the vapor partial pressure is zero. With `--rh`, saturation vapor pressure is `saturation_vapor_pressure_water` when \(T > 273.15\,\mathrm{K}\) and `saturation_vapor_pressure_ice` when \(T \le 273.15\,\mathrm{K}\). Vapor partial pressure is `vapor_partial_pressure`,

\[
e = \phi\, e_s.
\]

Dry density is `atmosphere_density` at the 1976 sea-level molar mass \(M_0\). Moist density is `moist_density`. Water molar mass is `water_molar_mass`. Mean molar mass is \(M_0\) when `--rh` is omitted and `moist_mean_molar_mass` when `--rh` is set. Speed of sound is `atmosphere_sound_speed` with \(\gamma = 1.4\) and that molar mass.

Pressure altitude inverts `gradient_layer_pressure` or `isothermal_layer_pressure` on the 1976 layers. Outside air temperature does not enter pressure altitude. Density altitude inverts `gradient_layer_density` or `isothermal_layer_density` for the parcel density. Geometric altitude is `geometric_altitude`, \(Z = r_0 H / (r_0 - H)\). There is no `pressure_altitude` or `density_altitude` formula. Do not use an aviation rule-of-thumb density altitude.

Station pressure above the 1976 sea-level pressure, or parcel density above the 1976 sea-level density, extrapolates troposphere layer 0 below \(H = 0\). Negative \(H\) and \(Z\) are printed. The hydrostatic model ends at \(H = 84852\,\mathrm{m}\). This is not the NASA Glenn three-zone fit.

Optional `--eas` inverts `equivalent_airspeed` for true airspeed. Sea-level density is the 1976 model at zero geometric altitude. \(V_e\) is not calibrated airspeed.

## When to run

1. Use this skill when the user wants pressure altitude, density altitude, density, or speed of sound from a station pressure and an outside air temperature.
2. Convert pressure to pascals, temperature to kelvin, relative humidity to a fraction from 0 to 1, and equivalent airspeed to metres per second before the call. State the converted units in the reply. Do not invent a pressure or a temperature.
3. One pressure and one temperature is one run. Do not sweep.
4. Omit `--rh` when the user does not give a humidity. That run is dry. Pass `--rh` only for a stated relative humidity.
5. Pass `--eas` only when the user gives an equivalent airspeed and wants true airspeed. \(V_e\) is not calibrated airspeed.
6. A geometric altitude on the 1976 standard, with no station pressure, belongs to `ATMOS - Standard1976`.

## Flags

Run:

```text
python "skills/AERO - DensityAndPressureAltitude/density_and_pressure_altitude.py" --pressure <Pa> --oat <K> [--rh <phi>] [--eas <m/s>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pressure` | Station / static pressure \(p\) | Pa, \(> 0\) | Required |
| `--oat` | Outside air temperature \(T\) | K, \(> 0\) | Required |
| `--eas` | Equivalent airspeed \(V_e\) | m/s, \(> 0\) | Optional |
| `--rh` | Relative humidity \(\phi\) | dimensionless, \(0 \le \phi \le 1\) | Optional. Omitted is dry (\(e = 0\)) |

Pressure in hectopascals uses `1 hPa = 100 Pa`. Pressure in inches of mercury uses `1 inHg = 3386.389 Pa`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Temperature in degrees Fahrenheit uses `T_K = (T_F - 32) * 5/9 + 273.15`. A relative humidity in percent is the fraction on 0 to 1 (`50%` is `--rh 0.5`). Equivalent airspeed in knots uses `1 kt = 1852/3600 m/s`. Printed altitudes are metres. A request in feet uses `1 ft = 0.3048 m` on the printed `Zp_m` and `Zd_m`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `p_Pa`, `T_K`, `rh`, and `rh_source`. `dry` means `--rh` was omitted. `flag` means `--rh` was passed.
3. When `rh_source` is `flag`, report `e_Pa` and `es_Pa`. State that \(e_s\) uses the water script above \(273.15\,\mathrm{K}\) and the ice script at and below \(273.15\,\mathrm{K}\).
4. Report `M_kg_kmol`, `rho_kg_m3`, and `cs_m_s`. State that \(c_s\) uses \(\gamma = 1.4\) and the printed molar mass.
5. Report `Hp_m`, `Zp_m`, and `layer_p`. `Hp_m` is geopotential pressure altitude from station pressure alone. `Zp_m` is the geometric altitude of that \(H\). `layer_p` is the 1976 layer index. This `Hp_m` is not the geometric pressure scale height from `ATMOS - Standard1976`.
6. Report `Hd_m`, `Zd_m`, and `layer_d`. Those are the geopotential and geometric density altitudes of the parcel density, and the 1976 layer index of that density.
7. If `--eas` was passed, report `V_eas_m_s`, `rho_sl_kg_m3`, and `V_m_s`. `V_m_s` is true airspeed. State that it is not calibrated airspeed. `rho_sl_kg_m3` is the 1976 density at zero geometric altitude.
8. Negative `Hp_m` or `Zp_m` means the station pressure is above the 1976 sea-level pressure and the troposphere was extended below \(H = 0\).
9. If a required value is missing, or the program prints `error:` and exits 2, say so. Do not fill a pressure or a temperature in. Vapor partial pressure at or above station pressure is that exit.
