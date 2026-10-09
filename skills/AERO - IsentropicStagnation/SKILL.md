---
name: AERO - IsentropicStagnation
description: >-
  Run the isentropic-stagnation program and report its printed results and
  optional PNG. Use when the user wants total temperature, pressure, or
  density from Mach number and the matching static state, the sonic
  reference state, or static and stagnation speeds of sound. Do not redraw
  the plot or recompute the numbers by hand.
---

# AERO - IsentropicStagnation

Use this skill for isentropic stagnation and the sonic reference state of a calorically perfect gas. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Total temperature uses `stagnation_temperature`:

\[
\frac{T_t}{T} = 1 + \frac{\gamma - 1}{2} M^{2}
\]

Total pressure and density use `stagnation_pressure` and `stagnation_density`:

\[
\frac{p_t}{p} = \left(\frac{T_t}{T}\right)^{\gamma/(\gamma - 1)} \qquad
\frac{\rho_t}{\rho} = \left(\frac{T_t}{T}\right)^{1/(\gamma - 1)}
\]

The stagnation sound-speed ratio is `stagnation_sound_speed`, \(a_t/a = \sqrt{T_t/T}\). Absolute totals are printed only for each static that was given.

The sonic reference state uses `sonic_temperature`, `sonic_pressure`, and `sonic_density`:

\[
\frac{T^{*}}{T_t} = \frac{2}{\gamma + 1} \qquad
\frac{p^{*}}{p_t} = \left(\frac{2}{\gamma + 1}\right)^{\gamma/(\gamma - 1)} \qquad
\frac{\rho^{*}}{\rho_t} = \left(\frac{2}{\gamma + 1}\right)^{1/(\gamma - 1)}
\]

Absolute \(T^{*}\), \(p^{*}\), and \(\rho^{*}\) need the matching total, so they appear only when that static was given. Speed of sound is `speed_of_sound`, \(a = \sqrt{\gamma p/\rho} = \sqrt{\gamma R T}\). With pressure and density both given, the program uses \(\sqrt{\gamma p/\rho}\). With temperature alone it uses the 1976 dry-air \(R = R^{*}/M_0\). There is no shock in this skill; for a normal-shock jump use `AERO - NormalShock`.

## When to run

1. Use this skill when the user wants isentropic total temperature, pressure, or density, the sonic reference state, or static and stagnation speeds of sound from Mach number.
2. Convert static temperature to kelvin, pressure to pascals, and density to kg/m³ before the call. State the converted units in the reply. Do not invent Mach, \(T\), \(p\), \(\rho\), or \(\gamma\).
3. Pass `--mach`. Pass `--temperature`, `--pressure`, and `--density` only when the user gave that static. One Mach number is one run. Do not sweep.
4. Pass `--out` only when the user wants the PNG of \(p_t/p\) and \(T_t/T\) versus Mach. Do not invent a plot path when they did not ask for a figure.
5. If the user asks for a normal-shock or Rayleigh-Pitot recovery, use `AERO - NormalShock` or `AERO - RayleighPitotMach` instead.
6. Interactive lab offer: before running this program for a new isentropic stagnation or sonic-state design or sizing thread, ask once whether the user wants `AERO - CompressibleFlowDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/AERO - IsentropicStagnation/isentropic_stagnation.py" --mach <M> [--temperature <K>] [--pressure <Pa>] [--density <kg/m^3>] [--gamma <k>] [--out <png>]
```

Pass **only** flags the user supplied. Do **not** supply a default Mach or invent static values.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Mach number \(M\) | dimensionless, \(\ge 0\) | Required |
| `--temperature` | Static temperature \(T\) | K, \(> 0\) | Optional |
| `--pressure` | Static pressure \(p\) | Pa, \(> 0\) | Optional |
| `--density` | Static density \(\rho\) | kg/m³, \(> 0\) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare `--mach` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`. Temperature in degrees Celsius uses `T_K = T_C + 273.15`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`. Pressure in pounds per square inch uses `1 psi = 6894.757293168 Pa`.

When `--out` is passed, the program writes one PNG. The plot title is `Isentropic stagnation ratios`. The curves are isentropic \(p_t/p\) and \(T_t/T\) from Mach 0 through a few supersonic points. There is no shock.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `M`, `gamma`, and `gamma_source`. `default` means \(\gamma = 1.4\) air.
4. Report `Tt_over_T`, `pt_over_p`, `rhot_over_rho`, and `at_over_a`.
5. Report `Tstar_over_Tt`, `pstar_over_pt`, and `rhostar_over_rhot`.
6. Report absolute totals and sonic values only when printed: `Tt_K` and `T_star_K` with `--temperature`; `pt_Pa` and `p_star_Pa` with `--pressure`; `rhot_kg_m3` and `rho_star_kg_m3` with `--density`.
7. Report `a_m_s`, `a_t_m_s`, and `a_source` when they are printed. `pressure_density` means \(\sqrt{\gamma p/\rho}\). `temperature` means \(\sqrt{\gamma R T}\). Report `R_J_kgK` and `R_source` when printed. `equation_of_state` means \(R = p/(\rho T)\). `default_air` means the 1976 dry-air value.
8. If Mach is missing, or a value is outside the program limits, say so. Do not fill it in.
