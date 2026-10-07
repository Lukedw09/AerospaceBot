---
name: ROCKET - FairingAndInterstageMass
description: >-
  Run the fairing and interstage program and report its printed masses.
  Use when the user wants jettisonable payload-fairing mass and
  interstage or skirt shell mass from diameter, length, wall thickness, and
  density. Do not recompute the shell areas by hand.
---

# ROCKET - FairingAndInterstageMass

Use this skill for geometry-based fairing and interstage shell masses. Run the program once; quote its stdout. This skill does not write a figure.

Assumptions (also printed): constant-thickness open shells. `cylinder_shell_mass` is the lateral cylinder. `cone_shell_mass` is the cone lateral area. `tangent_ogive_shell_mass` is the tangent-ogive surface of revolution. Bulkheads are omitted. `jettison_kg` is the fairing.

## When to run

1. Use this skill when the user gives a fairing diameter, cylindrical length, nose length, and an interstage diameter and length.
2. Pass `--thickness` and `--rho`, or `--areal`, not a guessed wall. State the unit conversion if the user gave inches or pounds.
3. Pass `--nose cone` or `--nose ogive` only when the user named the shape. An omitted nose is a cone.
4. Pass `--design-factor` only when the user gives one.

## Flags

Run:

```text
python "skills/ROCKET - FairingAndInterstageMass/fairing_and_interstage_mass.py" --fairing-diameter <m> --cylinder-length <m> --nose-length <m> [--nose cone|ogive] --interstage-diameter <m> --interstage-length <m> (--thickness <m> --rho <kg/m^3> | --areal <kg/m^2>) [--design-factor <factor>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--fairing-diameter` | Fairing outside diameter | m | Required |
| `--cylinder-length` | Cylindrical barrel length | m | Required |
| `--nose-length` | Nose length | m | Required |
| `--nose` | `cone` or `ogive` | — | Optional |
| `--interstage-diameter` | Interstage diameter | m | Required |
| `--interstage-length` | Interstage length | m | Required |
| `--thickness` | Wall thickness | m | Or `--areal` |
| `--rho` | Material density | kg/m^3 | Or `--areal` |
| `--areal` | Areal density, instead of thickness times density | kg/m^2 | Or `--thickness` and `--rho` |
| `--design-factor` | Multiplier on both masses | — | Optional |

The program prints masses only. It does not write a PNG or an HTML file.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `fairing_kg`, `interstage_kg`, and `jettison_kg`.
3. Pass `fairing_kg` and `interstage_kg` into `ROCKET - VehicleMassBudget`. Pass `jettison_kg` to `ROCKET - MultiStageAscent` as the jettison mass.
4. If a diameter, length, or a wall (`--thickness` with `--rho`, or `--areal`) is missing, say so. Do not fill them in.
