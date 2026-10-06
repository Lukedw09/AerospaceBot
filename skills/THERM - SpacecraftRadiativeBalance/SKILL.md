---
name: THERM - SpacecraftRadiativeBalance
description: >-
  Run the single-node spacecraft radiative-balance program and report its
  printed results and optional PNG. Use when the user wants equilibrium
  temperature at a stated radiator area, or the radiator area that holds a
  stated temperature, from absorbed solar, albedo, and planet infrared.
  Eclipse fraction may come from POWER - SolarArrayOutput. Do not recompute
  the numbers by hand. Not entry heating and not in-air lumped convection.
---

# THERM - SpacecraftRadiativeBalance

Use this skill for a single isothermal spacecraft node. Absorbed solar, albedo, and planet infrared, plus optional internal power, are balanced by gray-body emission. Run the program once; quote its stdout and include the PNG when `graph:` is printed.

Absorbed power is `spacecraft_absorbed_power`. Equilibrium temperature at a given radiator area is `spacecraft_equilibrium_temperature`. Radiator area that holds a stated temperature is `radiator_area_for_temperature`. Solar is multiplied by \(1-f_e\). Albedo and planet infrared are user inputs; they are not reduced by the eclipse fraction.

An eclipse fraction already computed by `POWER - SolarArrayOutput` may be passed as `--eclipse-fraction`. Do not re-derive the umbra.

This skill is not entry heating (`THERM - SonicStagnationHeatFlux`, `THERM - BallisticEntryPeakLoad`) and not in-air lumped convection (`THERM - LumpedCapacitanceTransient`).

## When to run

1. Use this skill when the user wants spacecraft equilibrium temperature or the radiator area that holds a temperature.
2. Convert areas to square metres, temperatures to kelvin, and fluxes to watts per square metre. State the converted units. Do not invent absorptance, emittance, areas, albedo, planet infrared, view factors, or internal power.
3. Pass `--area-sun`, `--alpha`, and `--epsilon`. Pass `--area-rad` to solve temperature, `--temperature` to solve area, or both.
4. Pass `--albedo` with `--area-albedo`, and `--planet-ir` with `--area-planet`, only when the user supplied those heating terms. Optional view factors default to 1.
5. Pass `--eclipse-fraction` when the user or `POWER - SolarArrayOutput` already has it.
6. Pass `--out` only when the user wants temperature versus radiator area.

## Flags

```text
python "skills/THERM - SpacecraftRadiativeBalance/spacecraft_radiative_balance.py" --area-sun <m^2> --alpha <fraction> --epsilon <fraction> (--area-rad <m^2> | --temperature <K>) [--eclipse-fraction <fraction>] [--albedo <fraction> --area-albedo <m^2>] [--planet-ir <W/m^2> --area-planet <m^2>] [--internal <W>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--area-sun` | Projected sunlit area | m², \(> 0\) | Required |
| `--alpha` | Solar absorptance | (0, 1] | Required |
| `--epsilon` | Infrared emittance | (0, 1] | Required |
| `--area-rad` | Radiator area | m², \(> 0\) | One or both of `--area-rad` and `--temperature` |
| `--temperature` | Temperature to hold | K, \(> 0\) | One or both of `--area-rad` and `--temperature` |
| `--eclipse-fraction` | Fraction of the orbit in eclipse | [0, 1] | Optional |
| `--solar-constant` | Solar constant | W/m² | Optional. Default 1361.6 |
| `--albedo` | Planetary albedo | [0, 1] | With `--area-albedo` |
| `--area-albedo` | Area seeing albedo | m² | With `--albedo` |
| `--view-albedo` | Albedo view factor | [0, 1] | Optional. Default 1 |
| `--planet-ir` | Planet infrared flux | W/m² | With `--area-planet` |
| `--area-planet` | Area seeing planet infrared | m² | With `--planet-ir` |
| `--view-planet` | Planet-infrared view factor | [0, 1] | Optional. Default 1 |
| `--internal` | Internal heat | W, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional |

The plot title is `Spacecraft radiative balance`. The curve is equilibrium temperature versus radiator area. The square is the operating point when `--area-rad` was passed.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `Q_abs_W` and, when printed, `T_eq_K` and `A_req_m2`.
4. If absorptance, emittance, or sunlit area is missing, say so. Do not fill them in.
