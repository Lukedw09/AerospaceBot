---
name: AERO - EquivalentAirspeed
description: >-
  Run the equivalent-airspeed program and report its printed results. Use
  when the user wants Mach number, dynamic pressure, equivalent airspeed,
  speed of sound, or Reynolds number from a geometric altitude and either
  true airspeed or Mach number on the 1976 standard atmosphere. Do not
  recompute the numbers by hand.
---

# AERO - EquivalentAirspeed

Use this skill for one flight condition on the 1976 U.S. Standard Atmosphere. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Geometric altitude and one speed are the inputs. True airspeed uses `--tas`. Mach number uses `--mach`. Pass one of them. The program reads temperature, pressure, density, and speed of sound from `ATMOS - Standard1976`.

Mach number is `mach_number`, \(M = V/c_s\). Dynamic pressure is `freestream_dynamic_pressure`,

\[
q = \frac{1}{2}\rho V^{2}.
\]

For air, `dynamic_pressure_air` is \(q/p = (7/10) M^{2}\).

Equivalent airspeed is `equivalent_airspeed`:

\[
V_e = V\sqrt{\frac{\rho}{\rho_{\mathrm{sl}}}}.
\]

That is the sea-level speed in `freestream_dynamic_pressure` with the same \(q\). \(V_e\) is not calibrated airspeed. The compressibility correction from equivalent airspeed to calibrated airspeed is not in `FormulaCatalouge`.

Viscosity is `sutherland_viscosity` with the 1976 constants \(\beta = 1.458\times 10^{-6}\,\mathrm{kg/(s\cdot m\cdot K^{1/2})}\) and \(S = 110.4\,\mathrm{K}\). Kinematic viscosity is `kinematic_viscosity`. Reynolds number is `reynolds_number`. `Re_per_m` is that formula at \(L = 1\,\mathrm{m}\). An omitted `--length` is that one metre.

## When to run

1. Use this skill when the user wants Mach number, dynamic pressure, equivalent airspeed, speed of sound, or a Reynolds number at an altitude.
2. Convert altitude to geometric metres and speed to metres per second before the call. State the converted units in the reply. A bare altitude is geometric metres, not geopotential. Do not invent an altitude or a speed.
3. Pass `--tas` or `--mach`, not both. If the user gives both a true airspeed and a Mach number, ask which one to use.
4. One altitude and one speed is one run. Do not sweep.
5. Pass `--length` only when the user gives a characteristic length. Otherwise leave it out and report the per-metre Reynolds number.

## Flags

Run:

```text
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --alt <m> (--tas <m/s> | --mach <M>) [--length <m>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Required |
| `--tas` | True airspeed \(V\) | m/s, \(> 0\) | Or `--mach` |
| `--mach` | Mach number \(M\) | dimensionless, \(> 0\) | Or `--tas` |
| `--length` | Characteristic length \(L\) | m, \(> 0\) | Optional. Omitted length is 1 m |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. If the user gives geopotential altitude \(H\), convert with \(Z = r_0 H / (r_0 - H)\) and \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\) before the call, and say so. A speed in knots uses `1 kt = 1852/3600 m/s`. A speed in feet per second uses `1 ft/s = 0.3048 m/s`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `speed_source`. `true_airspeed` means `--tas` was the input. `mach` means `--mach` was the input.
3. Report `Z_m`, `H_m`, `T_K`, `p_Pa`, `rho_kg_m3`, and `cs_m_s`. State that these are the 1976 standard at that geometric altitude.
4. Report `rho_sl_kg_m3`, `rho_sl_source`, and `rho_over_rho_sl`. Sea-level density is the 1976 standard at zero geometric altitude. `rho_over_rho_sl` is the ratio of those two densities. It is not a separate formula.
5. Report `V_m_s`, `M`, `q_Pa`, and `V_eas_m_s`. `V_eas_m_s` is the sea-level speed with the same dynamic pressure. State that it is not calibrated airspeed.
6. Report `mu_Pa_s`, `nu_m2_s`, `length_m`, `Re`, and `Re_per_m`. `Re` uses `length_m`. `Re_per_m` uses 1 m.
7. If `warning` is printed, include it. That warning applies at and above 80 km, where the atmosphere program still holds \(M = M_0\).
8. If altitude or the speed is missing, or both speeds were given, say so. Do not fill them in.
