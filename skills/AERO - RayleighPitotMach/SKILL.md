---
name: AERO - RayleighPitotMach
description: >-
  Run the Rayleigh-Pitot Mach program and report its printed results. Use
  when the user wants freestream Mach number or dynamic pressure from a
  measured pitot pressure, freestream static pressure, and specific-heat
  ratio. Below Mach 1 use isentropic stagnation; above Mach 1 use the
  Rayleigh-Pitot normal-shock relation. Do not recompute the numbers by hand.
---

# AERO - RayleighPitotMach

Use this skill for freestream Mach number and dynamic pressure from a pitot measurement. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Measured pitot pressure, freestream static pressure, and \(\gamma\) are the inputs. Below Mach 1 the probe recovers the isentropic stagnation pressure from `stagnation_temperature` and `stagnation_pressure`:

\[
\frac{p_t}{p}
=
\left(1 + \frac{\gamma - 1}{2} M^{2}\right)^{\gamma/(\gamma - 1)}.
\]

Above Mach 1 a normal shock stands ahead of the probe. The measured pressure is the stagnation pressure behind that shock from `rayleigh_pitot`:

\[
\frac{p_{t2}}{p_1}
=
\left(\frac{\gamma + 1}{2} M_1^{2}\right)^{\gamma/(\gamma - 1)}
\left[\frac{\gamma + 1}{2\gamma M_1^{2} - (\gamma - 1)}\right]^{1/(\gamma - 1)}.
\]

The sonic pressure ratio \((( \gamma + 1)/2)^{\gamma/(\gamma - 1)}\) selects the branch. Dynamic pressure is `dynamic_pressure` as

\[
q = \frac{\gamma}{2} p M^{2}.
\]

Probe geometry, viscous loss, and thermally imperfect gas effects are omitted.

## When to run

1. Use this skill when the user wants Mach number or dynamic pressure from a pitot and static pressure pair.
2. Convert pressures to pascals before the call. State the converted units in the reply. Do not invent a pitot pressure, a static pressure, or \(\gamma\).
3. One pitot, one static pressure, and one \(\gamma\) is one run. Do not sweep.
4. If the user gives only a pressure ratio, ask for the freestream static pressure when dynamic pressure is requested. Mach number needs only the ratio and \(\gamma\); still pass both pressures when both are known.
5. If the measured pitot pressure is below freestream static pressure, say so and stop. Do not run a negative or inverted ratio.

## Flags

Run:

```text
python "skills/AERO - RayleighPitotMach/rayleigh_pitot_mach.py" --pitot <Pa> --static <Pa> [--gamma <k>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pitot` | Measured pitot pressure | Pa, \(> 0\), at least `--static` | Required |
| `--static` | Freestream static pressure \(p\) | Pa, \(> 0\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |

A bare `--pitot` and `--static` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`. Pressure in kilopascals uses `1 kPa = 1000 Pa`. Pressure in pounds per square inch uses `1 psi = 6894.757293168 Pa`. Pressure in atmospheres uses `1 atm = 101325 Pa`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `pitot_Pa`, `static_Pa`, `gamma`, and `gamma_source`. `default` means \(\gamma = 1.4\) air.
3. Report `pitot_over_static` and `sonic_pitot_over_static`. State that the sonic ratio selects the branch.
4. Report `branch` and `relation`. `subsonic` or `sonic` with `isentropic_stagnation` means the isentropic stagnation formula. `supersonic` with `rayleigh_pitot` means the normal-shock pitot formula.
5. Report `M` and `q_Pa`. `M` is freestream Mach. `q_Pa` is freestream dynamic pressure.
6. If a required value is missing, or a value is outside the program limits, say so. Do not fill it in.
