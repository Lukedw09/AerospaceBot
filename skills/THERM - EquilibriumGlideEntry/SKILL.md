---
name: THERM - EquilibriumGlideEntry
description: >-
  Run the equilibrium-glide entry program and report its printed results and
  optional PNG. Use when the user wants the closed-form equilibrium-glide peak
  deceleration and the characteristic convective heat-flux scale from entry
  speed, lift-to-drag ratio, and ballistic coefficient in an exponential
  atmosphere. Do not redraw the plot or recompute the numbers by hand.
---

# THERM - EquilibriumGlideEntry

Use this skill for the Sänger–Chapman equilibrium glide: lift balances weight minus centrifugal force, and the flight-path angle stays small. It is the lifting companion of `THERM - BallisticEntryPeakLoad`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Peak horizontal deceleration on the way down from a subcircular entry speed is `equilibrium_glide_peak_deceleration`, \(a_{\mathrm{peak}}=g/(L/D)\). The value at the entry speed is `equilibrium_glide_entry_deceleration`. Heating density at the speed of maximum \(\sqrt{\rho}\,V^{3}\) is `equilibrium_glide_heating_density`. The scale itself is `equilibrium_glide_heat_flux_scale`, \(\sqrt{\rho}\,V^{3}\). It is proportional to cold-wall convective flux when nose radius is fixed. Absolute stagnation flux stays on `THERM - SonicStagnationHeatFlux`.

The default exponential atmosphere is the same Earth fit as the ballistic skill (NACA TN 4047). It converts the heating density to an altitude. It does not change the deceleration, which is independent of vehicle size.

## When to run

1. Use this skill when the user wants equilibrium-glide peak deceleration or the characteristic heat-flux scale.
2. Convert entry speed to m/s and ballistic coefficient to kg/m². Lift-to-drag ratio is dimensionless. State the converted units in the reply. Do not invent them.
3. Pass `--ve`, `--lod`, and `--beta`. `--beta` is \(m/(C_D A)\), the same ballistic coefficient as `THERM - BallisticEntryPeakLoad`.
4. Pass `--scale-height`, `--rho-ref`, and `--z-ref` together only when the user overrides the Earth fit. Do not pass a partial override.
5. Pass `--radius` only when the user gave a planet radius. The default is the catalogue Earth radius used for circular speed.
6. Pass `--out` only when the user wants the PNG of peak load versus lift-to-drag ratio. Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for a nonlifting Allen–Eggers entry, a skip, or a 3-degree-of-freedom trajectory.

## Flags

Run:

```text
python "skills/THERM - EquilibriumGlideEntry/equilibrium_glide_entry.py" --ve <m/s> --lod <L/D> --beta <kg/m^2> [--radius <m>] [--scale-height <m>] [--rho-ref <kg/m^3>] [--z-ref <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--ve` | Entry speed, below circular speed | m/s, \(> 0\) | Required |
| `--lod` | Lift-to-drag ratio | dimensionless, \(> 0\) | Required |
| `--beta` | Ballistic coefficient \(m/(C_D A)\) | kg/m², \(> 0\) | Required |
| `--radius` | Planet radius for circular speed | m, \(> 0\) | Optional. Default \(6.3742\times 10^{6}\) |
| `--scale-height` | Density scale height \(H\) | m, \(> 0\) | Optional, with `--rho-ref` and `--z-ref` |
| `--rho-ref` | Reference density | kg/m³, \(> 0\) | Optional, with the other atmosphere flags |
| `--z-ref` | Altitude of the reference density | m | Optional, with the other atmosphere flags |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

An omitted atmosphere is the TN 4047 Earth fit: \(H = 6705.6\,\mathrm{m}\), \(\rho_{\mathrm{ref}} = 1.752288\,\mathrm{kg/m}^{3}\) at \(Z_{\mathrm{ref}} = 0\).

When `--out` is passed, the program writes one PNG. The plot title is `Equilibrium glide entry`. The curve is peak horizontal load in \(g\) versus lift-to-drag ratio. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `a_peak_m_s2`, `a_peak_g`, `a_entry_m_s2`, `Vq_m_s`, `rho_q_kg_m3`, `q_scale`, and `Zq_m`.
4. State that `q_scale` is \(\sqrt{\rho}\,V^{3}\), not a heat flux in W/m².
5. If entry speed, lift-to-drag ratio, or ballistic coefficient is missing, say so. Do not fill them in.
