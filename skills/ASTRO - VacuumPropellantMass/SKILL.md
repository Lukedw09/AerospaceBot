---
name: ASTRO - VacuumPropellantMass
description: >-
  Run the vacuum propellant program and report its printed results and optional
  PNG. Use when the user wants propellant mass and wet mass from a dry mass,
  one exhaust speed or specific impulse, and a sum of named vacuum delta-v
  contributions. Optional growth applies only to the dry mass given. Not a
  stage stack. Do not recompute the numbers by hand.
---

# ASTRO - VacuumPropellantMass

Use this skill to invert the catalogue vacuum rocket equation `delta_v_vacuum` at one exhaust speed. Run the program once; quote its stdout and include the PNG when `graph:` is printed.

Exhaust speed is \(c = I_{sp} g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^{2}\), or the user exhaust speed. Final mass is the dry mass times \(1+g\), and \(g\) defaults to 0. Propellant is `vacuum_propellant_mass`, \(m_p = m_f(\mathrm{e}^{\Delta v/c}-1)\). Wet mass is `vacuum_wet_mass`, \(m_0 = m_f\mathrm{e}^{\Delta v/c}\). Delta-v is the sum of the named pieces.

Named pieces may be a transfer from `ASTRO - HohmannTransfer` or `ASTRO - PlaneChangeImpulse`, drag makeup from `ASTRO - AerodynamicDragDeltaV`, and any disposal or control delta-v the user states. Do not invent a piece.

This is not a stage stack (`ROCKET - PayloadtoDeltaV`), a mixture ratio, or a tank wall (`ROCKET - TankStructureMass`). Growth is only the optional fraction on the dry mass given here.

## When to run

1. Use this skill when the user wants in-space propellant from a list of vacuum delta-v contributions.
2. Convert mass to kilograms and delta-v to metres per second. Do not invent dry mass, specific impulse, exhaust speed, growth, or a delta-v piece.
3. Pass `--dry` and at least one `--dv`. Pass `--name` with each `--dv` when the user named the pieces.
4. Pass exactly one of `--isp` or `--ve`.
5. Pass `--growth` only when the user stated a growth fraction. It applies only to `--dry`.
6. Pass `--out` only when the user wants propellant mass versus total delta-v.

## Flags

```text
python "skills/ASTRO - VacuumPropellantMass/vacuum_propellant_mass.py" --dry <kg> [--growth <fraction>] (--isp <s> | --ve <m/s>) [--name <text> --dv <m/s>] ...
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--dry` | Dry mass before growth | kg, \(> 0\) | Required |
| `--growth` | Fraction applied to `--dry` | \(\ge 0\) | Optional. Default 0 |
| `--isp` | Specific impulse | s, \(> 0\) | Exactly one of `--isp` or `--ve` |
| `--ve` | Exhaust speed | m/s, \(> 0\) | Exactly one of `--isp` or `--ve` |
| `--name` | Name of one delta-v piece | — | Optional, same count as `--dv` |
| `--dv` | One delta-v contribution | m/s, \(\ge 0\) | Required, at least one |
| `--out` | PNG path | — | Optional |

The plot title is `Vacuum propellant mass`.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `dv_total_m_s`, `m_final_kg`, `m_propellant_kg`, and `m_wet_kg`.
4. Report each `dv_<name>_m_s` line.
5. If dry mass, exhaust speed, or a delta-v piece is missing, say so. Do not fill it in.
