---
name: ASTRO - CheckSolution
description: >-
  PROTOTYPE homework checker. Use when the user wants a typed rocket-equation
  or two-impulse Hohmann solution checked line by line. Pass the problem
  givens, the target quantity, and the solution text. Do not recompute the
  verdicts. Quote the key: value lines. Hint mode names the line and the
  error type and does not give a corrected line.
---

# ASTRO - CheckSolution

PROTOTYPE. This skill checks a typed solution to the vacuum rocket equation or a two-impulse Hohmann transfer. It does not grade any other topic, and it does not read photos.

Correctness is deterministic. The checker uses dimensional analysis, symbolic equivalence with numeric spot checks, and numeric tolerances. It does not ask a language model whether a line is right. A line it cannot parse or decide is `can't verify`. It does not guess.

The final number is compared with this repository's own tools: `vacuum_propellant_mass` for the rocket equation, and `hohmann_transfer` for the transfer. Hint mode is the only mode. A verdict names the line and the error type. It does not include a corrected line.

## Scope

Rocket equation (Tsiolkovsky), using `delta_v_vacuum` and `vacuum_propellant_mass`:

- `delta_v`: \(\Delta v = v_e \ln(m_0/m_f)\)
- `mass_ratio`: \(m_0/m_f\) (wet over final)
- `mass_ratio_final_over_initial`: catalogue \(\mathrm{MR} = m_f/m_0\)
- `propellant_mass`: propellant from `vacuum_propellant_mass`
- `exhaust_speed`: \(v_e = I_{sp} g_0\), or the given exhaust speed
- `specific_impulse`: \(I_{sp} = v_e/g_0\)

Two-impulse Hohmann only, using `hohmann_transfer`:

- `circular_speed_depart`, `circular_speed_arrive`
- `transfer_speed_depart`, `transfer_speed_arrive`
- `dv1`, `dv2`, `dv_total`
- `time_of_flight`

Burns are positive magnitudes, as `hohmann_transfer` prints them. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Hohmann \(\mu = g_0 R_0^2\). The Earth default \(R_0\) is the one in `hohmann_transfer`. Two altitudes are converted with \(r = R_0 + h\) and then solved by `hohmann_transfer.solve_transfer`. `alt` and `ecc` use `hohmann_transfer.radii_from_altitude`.

## Verdicts

One verdict per checked line:

- `correct`: the line follows from the givens and the previous lines, and the units are consistent.
- `approximation`: not exact, but inside the stated approximation tolerance (rounding, or a small dropped term).
- `error`: `units`, `sign`, `algebra`, `arithmetic`, or `wrong formula`. Emitted only when a deterministic check fails on that line.
- `can't verify`: the line could not be parsed or decided.

If every checked line passes and the final number still disagrees with the tool, the output says: "Final answer doesn't match. Likely a setup or formula error. Couldn't locate the line." It does not point at a line it cannot back up.

## Tolerances and assumptions

Printed on every run:

- correct: relative error at most \(10^{-4}\), or absolute error at most \(10^{-6}\)
- approximation: relative error at most \(10^{-2}\)
- symbolic spot checks: 8 samples, seed 0
- `log` and `ln` are natural log
- units are SI (`kg`, `m`, `s`, `m/s`, `m/s**2`, `km`, `km/s`, `N`)

Pass one family. Rocket givens are `m0`, `mf`, `mp`, `dry`, `ve`, `isp`, `dv`, and `growth`. Hohmann givens are `r1` and `r2`, or `h1` and `h2`, or `alt` and `ecc`, plus optional `R0`. An unknown parameter is rejected. Enum fields list their allowed values in the tool schema.

## When to run

1. Use this skill when the user pastes a typed solution to a rocket-equation or two-impulse Hohmann problem and wants it checked.
2. Pass `--family`, `--target`, and `--solution`. One step per line. LaTeX or plain math with units. Do not send a photo.
3. Pass only the givens the problem states, in the units named on each flag. Do not invent a mass, a speed, a radius, or an altitude.
4. Leave `--mode` at `hint`. Do not add a corrected line to the reply. Quote the `key: value` verdicts.
5. Say that the checker is a prototype. If a line is `can't verify`, say so. Do not fill in a verdict.

## Flags

```text
python "skills/ASTRO - CheckSolution/check_solution.py" --family <family> --target <target> --solution <text> [--mode hint] [givens]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--family` | `rocket_equation` or `hohmann` | enum | Required |
| `--target` | Quantity the final answer claims. Rocket: `delta_v`, `mass_ratio`, `mass_ratio_final_over_initial`, `propellant_mass`, `exhaust_speed`, `specific_impulse`. Hohmann: `circular_speed_depart`, `circular_speed_arrive`, `transfer_speed_depart`, `transfer_speed_arrive`, `dv1`, `dv2`, `dv_total`, `time_of_flight` | enum | Required |
| `--solution` | Student solution, one step per line | text | Required |
| `--mode` | Hint mode only | enum | Optional |
| `--m0-kg` | Initial mass | kg, \(> 0\) | Optional |
| `--mf-kg` | Final mass | kg, \(> 0\) | Optional |
| `--mp-kg` | Propellant mass | kg, \(> 0\) | Optional |
| `--dry-kg` | Dry mass before growth | kg, \(> 0\) | Optional |
| `--ve-m-s` | Exhaust speed | m/s, \(> 0\) | Optional |
| `--isp-s` | Specific impulse | s, \(> 0\) | Optional |
| `--dv-m-s` | Delta-v | m/s, \(\ge 0\) | Optional |
| `--growth` | Growth fraction on dry mass | dimensionless, \(\ge 0\) | Optional |
| `--r1-m` | Departure circular radius | m, \(> 0\) | Optional |
| `--r2-m` | Arrival circular radius | m, \(> 0\) | Optional |
| `--h1-m` | Departure geometric altitude | m, \(\ge 0\) | Optional |
| `--h2-m` | Arrival geometric altitude | m, \(\ge 0\) | Optional |
| `--alt-m` | Departure altitude for the alt/ecc pair | m, \(\ge 0\) | Optional |
| `--ecc` | Transfer eccentricity | dimensionless, \(0 \le e < 1\) | Optional |
| `--R0-m` | Planetary radius | m, \(> 0\) | Optional |

## Example

Input:

```text
python "skills/ASTRO - CheckSolution/check_solution.py" --family rocket_equation --target delta_v --m0-kg 1000 --mf-kg 200 --ve-m-s 3000 --solution $'\Delta v = v_e \\ln\\frac{m_0}{m_f}\n\\Delta v = 3000\\,\\mathrm{m/s}\\,\\ln\\frac{1000}{200}'
```

The solution text is:

```text
\Delta v = v_e \ln\frac{m_0}{m_f}
\Delta v = 3000\,\mathrm{m/s}\,\ln\frac{1000}{200}
```

Output (prototype; the reference comes from `vacuum_propellant_mass`):

```text
prototype: yes
banner: PROTOTYPE homework checker
mode: hint
hint: line verdicts name the line and the error type and do not include a corrected line
family: rocket_equation
target: delta_v
target_unit: m/s
assumptions: vacuum rocket equation inverted at one exhaust speed; delta-v is the sum of the named contributions the user supplies; optional growth fraction applies only to the dry mass given here; not a stage stack, mixture ratio, or tank wall
checker_assumptions: prototype; hint mode names the line and the error type and does not give a corrected line; undecidable lines are can't verify; log is natural; correct when relative error <= 0.0001 or absolute error <= 1e-06; approximation when relative error <= 0.01; symbolic spot checks use seed 0 and 8 samples; g0 = 9.80665 m/s^2 from the Astraeus tools; rocket equation is delta_v_vacuum, dv = ve*ln(m0/mf), with ve = Isp*g0; propellant and wet mass come from vacuum_propellant_mass; mass_ratio means m0/mf (wet/final); mass_ratio_final_over_initial means catalogue MR = mf/m0; optional growth applies only to dry mass, matching vacuum_propellant_mass
tolerance_correct_relative: 0.0001
tolerance_approximation_relative: 0.01
tolerance_absolute: 1e-06
symbolic_sample_seed: 0
symbolic_sample_count: 8
log_base: natural
reference_tool: vacuum_propellant_mass
reference_status: ok
g0_m_s2: 9.80665
tool_called: yes
line_1_verdict: correct
line_1_note: follows from the previous lines
line_1_text: \Delta v = v_e \ln\frac{m_0}{m_f}
line_2_verdict: correct
line_2_note: follows from the previous lines
line_2_text: \Delta v = 3000\,\mathrm{m/s}\,\ln\frac{1000}{200}
checked_line_count: 2
verdict_correct: 2
verdict_approximation: 0
verdict_error: 0
verdict_cant_verify: 0
final_check: match
final_student: 4828.3137
final_student_unit: m/s
final_reference: 4828.3137
final_reference_unit: m/s
final_reference_tool: vacuum_propellant_mass
final_note: Final answer matches the reference within the correct tolerance.
```

A wrong number on an otherwise right formula is an arithmetic error on that line, and the note does not contain the corrected line:

```text
line_1_verdict: error
line_1_error_type: arithmetic
line_1_note: the number does not match evaluation of this line
```

## What to report

1. Say this is a prototype.
2. Quote the `key: value` lines, including the tolerances, the reference tool, each line verdict, and the final check.
3. In hint mode, do not write a replacement for an error line.
4. If the final note says the final answer doesn't match and the checker couldn't locate the line, repeat that sentence and do not pick a line yourself.
5. If a given is missing, say so. Do not fill it in.
