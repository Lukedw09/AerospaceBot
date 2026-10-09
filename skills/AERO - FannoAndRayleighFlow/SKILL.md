---
name: AERO - FannoAndRayleighFlow
description: >-
  Run the Fanno or Rayleigh duct program and report its printed ratios and
  PNG. Use when the user wants sonic-reference temperature, pressure,
  density, stagnation, or velocity ratios, the Fanno friction length to
  choke, or the Rayleigh stagnation-temperature ratio. Do not redraw the
  plot or recompute the numbers by hand.
---

# AERO - FannoAndRayleighFlow

Use this skill for steady constant-area flow of a calorically perfect gas. One run is either Fanno flow (adiabatic, with friction) or Rayleigh flow (frictionless, with heat addition). Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Fanno ratios to the sonic state are `fanno_temperature_ratio`, `fanno_pressure_ratio`, `fanno_density_ratio`, `fanno_velocity_ratio`, `fanno_stagnation_pressure_ratio`, and `fanno_friction_parameter` (\(4fL^{*}/D\)).

Rayleigh ratios are `rayleigh_temperature_ratio`, `rayleigh_pressure_ratio`, `rayleigh_density_ratio`, `rayleigh_velocity_ratio`, `rayleigh_stagnation_pressure_ratio`, and `rayleigh_stagnation_temperature_ratio`.

Combined friction and heat addition in one duct is not this skill. A normal shock is `AERO - NormalShock`.

## When to run

1. Use this skill when the user wants Fanno or Rayleigh property ratios at one Mach number, the friction length still available before choke, or the effect of a stated stagnation-temperature ratio on a Rayleigh duct.
2. Pass exactly one of `--fanno` or `--rayleigh`. Mach number is dimensionless. Do not invent \(M\) or \(\gamma\).
3. One Mach number is one run. Do not sweep.
4. `--fld` is the duct friction parameter \(4fL/D\) measured from this station toward Mach 1. Omit it unless the user gave a length or a friction parameter.
5. `--tt-ratio` is \(T_{t2}/T_{t1}\) on a Rayleigh duct. Omit it unless the user gave that ratio.
6. Interactive lab offer: before running this program for a new Fanno or Rayleigh duct design or sizing thread, ask once whether the user wants `AERO - CompressibleFlowDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py" --fanno --mach <M> [--gamma <k>] [--fld <4fL/D>] [--out <png>]
```

or:

```text
python "skills/AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py" --rayleigh --mach <M> [--gamma <k>] [--tt-ratio <Tt2/Tt1>] [--out <png>]
```

Pass **only** flags the user supplied, plus exactly one of `--fanno` or `--rayleigh`. Do **not** supply a default Mach.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--fanno` | Adiabatic constant-area flow with friction | — | One of `--fanno` or `--rayleigh` |
| `--rayleigh` | Frictionless constant-area flow with heat addition | — | One of `--fanno` or `--rayleigh` |
| `--mach` | Station Mach number | dimensionless, \(> 0\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--fld` | Fanno \(4fL/D\) from this station | dimensionless | Optional |
| `--tt-ratio` | Rayleigh \(T_{t2}/T_{t1}\) | dimensionless, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional |

A bare `--mach` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

Every successful run writes one PNG. The plot title is `Fanno flow ratios` or `Rayleigh flow ratios`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is Mach number. The curves are the sonic-reference ratios for the selected duct. The squares mark the given Mach.
3. Report `mode`, `M`, `gamma`, and `gamma_source`.
4. Report `T_over_Tstar`, `p_over_pstar`, `rho_over_rhostar`, `pt_over_ptstar`, and `V_over_Vstar`.
5. For Fanno, report `four_f_Lmax_over_D`. If `--fld` was passed, report `four_f_L_remaining_over_D` and either `exit_mach` or `choked_by_length`.
6. For Rayleigh, report `Tt_over_Ttstar`. If `--tt-ratio` was passed, report `exit_mach` or `choked_by_heat`.
7. Report `choked`. That flag is yes when the station is already sonic.
8. If Mach or the mode is missing, or a flag is outside the program limits, say so. Do not fill it in.
