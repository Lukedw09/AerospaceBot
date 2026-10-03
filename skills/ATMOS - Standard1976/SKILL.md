---
name: ATMOS - Standard1976
description: >-
  Run the 1976 standard-atmosphere program and report its printed results.
  Use when the user wants temperature, pressure, density, speed of sound, or
  scale height at a geometric altitude from sea level through 86 km. Do not
  recompute the profile by hand and do not use the NASA Glenn three-zone fit.
---

# ATMOS - Standard1976

Use this skill for the 1976 U.S. Standard Atmosphere below 86 km. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Geometric altitude \(Z\) is the input. Geopotential altitude is \(H = r_0 Z/(r_0+Z)\) with \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\). Temperature, pressure, and density come from the seven constant-lapse layers in `formulas.md`. Mean molar mass stays at the sea-level value \(M_0\), so kinetic temperature equals molecular-scale temperature. Speed of sound uses \(\gamma = 1.4\). Scale height is the geometric pressure scale height

\[
H_p = \frac{R^{*} T}{g M_0}, \quad g = g_0\left(\frac{r_0}{r_0+Z}\right)^2
\]

with \(g_0 = 9.80665\,\mathrm{m/s}^2\). This is not the NASA Glenn three-zone curve fit. The hydrostatic model ends at 86 km. There is no result above that altitude.

## When to run

1. Use this skill when the user asks for atmospheric temperature, pressure, density, speed of sound, or scale height at an altitude on Earth.
2. Convert altitude to geometric metres before the call. State the converted units in the reply. A bare altitude is geometric metres, not geopotential. Do not invent an altitude.
3. One altitude is one run. Do not sweep.

## Flags

Run:

```text
python "skills/ATMOS - Standard1976/standard_1976.py" --alt <m>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Geometric altitude \(Z\) | m, 0 to 86000 | Required |

Altitude in kilometres uses `1 km = 1000 m`. Altitude in feet uses `1 ft = 0.3048 m`. If the user gives geopotential altitude \(H\), convert with \(Z = r_0 H / (r_0 - H)\) and \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\) before the call, and say so.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report geometric altitude `Z_m` and geopotential `H_m`. State that \(Z\) is geometric.
3. Report `T_K`, `p_Pa`, `rho_kg_m3`, `cs_m_s`, and `Hp_m`.
4. State that `Hp_m` is the geometric pressure scale height, using local gravity at `Z_m`.
5. Report `layer_b` and `layer_Hb_m` when the user asks which layer they are in.
6. If `warning` is printed, include it. That warning applies at and above 80 km, where this program still holds \(M = M_0\).
7. If altitude is missing, or outside 0 to 86000 m, say so. Do not fill it in.
