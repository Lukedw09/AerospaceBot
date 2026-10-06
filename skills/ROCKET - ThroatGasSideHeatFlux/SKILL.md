---
name: ROCKET - ThroatGasSideHeatFlux
description: >-
  Run the Bartz throat heat-flux program and report its printed results. Use
  when the user wants the gas-side coefficient or heat flux at the throat
  from chamber pressure, temperature, c*, throat size, and gas properties.
  Do not recompute the numbers by hand. Do not call CEA.
---

# ROCKET - ThroatGasSideHeatFlux

Use this skill for the Bartz gas-side coefficient and heat flux. Run the program once and quote its stdout. Do not recompute the numbers by hand. Do not call CEA.

The coefficient is NASA SP-125 equation (4-13), converted to SI. Flux is \(q = h_g (r_\mathrm{rec} T_c - T_w)\). At the throat, \(A_t/A = 1\). This is not `THERM - SonicStagnationHeatFlux`.

## When to run

1. Use this skill when the user asks for throat gas-side heat flux or the Bartz coefficient.
2. Convert all inputs to SI before the call. State the converted units in the reply. Do not invent gas properties, curvature, wall temperature, or recovery.
3. Pass `--throat` (diameter) or `--rt` (radius), and `--curvature` (contour radius at the throat). SP-125 does not fix \(R/R_t\).
4. Pass `--mu`, `--cp`, and `--pr`, or both `--mw` and `--gamma`. Those may be quoted from `ROCKET - PerformanceParameters` (`Tc_K`, `Mw_kg_kmol`, `gamma`, `cstar_m_s`). Do not look them up at reply time.
5. Omitted `--sigma` is 1. Omitted `--recovery` is 1. SP-125 quotes a turbulent recovery factor from 0.90 to 0.98; pass it when the user states one.
6. The cooled heat rate for `ROCKET - RegenerativeCoolantHeatPickUp` is `q_dot_W_m2` times the cooled area the user states. This program does not choose that area.

## Flags

Run:

```text
python "skills/ROCKET - ThroatGasSideHeatFlux/throat_gas_side_heat_flux.py" --pc <Pa> --Tc <K> --cstar <m/s> (--throat <m> | --rt <m>) --curvature <m> --tw <K> (--mu <Pa·s> --cp <J/(kg·K)> --pr <Pr> | --mw <kg/kmol> --gamma <k>) [--area-ratio <At/A>] [--sigma <sigma>] [--recovery <r>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pc` | Nozzle stagnation pressure | Pa | Required |
| `--Tc` | Nozzle stagnation temperature | K | Required |
| `--cstar` | Characteristic velocity | m/s | Required |
| `--throat` | Throat diameter | m | Exactly one of `--throat` or `--rt` |
| `--rt` | Throat radius | m | Exactly one of `--throat` or `--rt` |
| `--curvature` | Contour radius at the throat | m | Required |
| `--tw` | Gas-side wall temperature | K | Required |
| `--mu` | Gas viscosity | Pa·s | With `--cp` and `--pr` |
| `--cp` | Gas specific heat | J/(kg·K) | With `--mu` and `--pr` |
| `--pr` | Prandtl number | dimensionless | With `--mu` and `--cp` |
| `--mw` | Molecular weight | kg/kmol | With `--gamma`, instead of \(\mu,c_p,\mathrm{Pr}\) |
| `--gamma` | Ratio of specific heats | dimensionless | With `--mw` |
| `--area-ratio` | \(A_t/A\) | dimensionless | Optional. Throat default is 1 |
| `--sigma` | Property correction | dimensionless | Optional. Default 1 |
| `--recovery` | Recovery factor | dimensionless | Optional. Default 1 |
| `--out` | PNG of flux versus chamber pressure | — | Optional |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report \(h_g\) in W/(m²·K) and \(q\) in W/m², with throat diameter and curvature.
3. Quote `warning` and `warning_recovery` when they are printed.
4. State that \(\sigma\) and the recovery factor are inputs or the documented defaults, and that figure 4-24 is not applied unless the user passed `--sigma`.
5. Point `q_dot_W_m2` at `ROCKET - RegenerativeCoolantHeatPickUp` only after the user states a cooled area.
