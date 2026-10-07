---
name: ROCKET - LeoDeltaVBudget
description: >-
  Run the LEO delta-v budget program and report its printed design delta-v
  and PNG. Use when the user wants the ideal delta-v a stage stack must
  meet for a circular LEO, including rotation assist, losses, circularization,
  and margin. Do not recompute the sum by hand.
---

# ROCKET - LeoDeltaVBudget

Use this skill for the design ideal \(\Delta v\) passed to `ROCKET - PayloadtoDeltaV` or `ROCKET - StagePropellantSplit`. Run the program once; quote its stdout. Include the PNG.

Assumptions (also printed): `leo_design_delta_v` is circular speed minus rotation assist plus gravity, drag, steering, circularization, and margin. Circular speed is \(\sqrt{\mu/r}\). Default \(R_0=6.3742\times 10^6\,\mathrm{m}\) and \(g_0=9.80665\,\mathrm{m/s}^2\). Omitted losses, assist, circularization, and margin are zero. This is not a trajectory.

## When to run

1. Use this skill when the user gives a target circular altitude or radius.
2. Pass `--alt` or `--r`, not both.
3. Pass `--v-rot` from `ASTRO - LaunchAzimuthInclination` when that assist is known. Pass losses from `ROCKET - MultiStageAscent` and `--circ` from `ASTRO - OrbitInsertionFromBurnout` when those runs exist. Do not invent a loss.
4. Pass `--margin` or `--margin-fraction`, not both. Omit both when the user gave no margin.

## Flags

Run:

```text
python "skills/ROCKET - LeoDeltaVBudget/leo_delta_v_budget.py" (--alt <m> | --r <m>) [--radius <m>] [--mu <m^3/s^2>] [--v-rot <m/s>] [--gravity-loss <m/s>] [--drag-loss <m/s>] [--steering-loss <m/s>] [--circ <m/s>] [--margin <m/s> | --margin-fraction <fraction>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--alt` | Target altitude above the body radius | m | Or `--r` |
| `--r` | Target circular radius from the center | m | Or `--alt` |
| `--radius` | Body radius used when `--alt` is set | m | Optional |
| `--mu` | Gravitational parameter | m^3/s^2 | Optional |
| `--v-rot` | Earth-rotation assist along the heading | m/s | Optional |
| `--gravity-loss` | Gravity loss | m/s | Optional |
| `--drag-loss` | Drag loss | m/s | Optional |
| `--steering-loss` | Steering loss | m/s | Optional |
| `--circ` | Circularization allowance | m/s | Optional |
| `--margin` | Absolute margin | m/s | Or `--margin-fraction` |
| `--margin-fraction` | Fraction of the sum before margin | — | Or `--margin` |
| `--out` | PNG path | — | Optional |

Every successful run writes a PNG bar chart. Each term, including a negative rotation credit, starts at zero. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. Each bar starts at zero. The rotation credit extends below zero.
3. Report `v_circ_m_s`, each loss, `margin_m_s`, and `dv_design_m_s`.
4. Pass `dv_design_m_s` to `ROCKET - StagePropellantSplit` or `ROCKET - PayloadtoDeltaV --dv`.
5. If the target altitude or radius is missing, say so. Do not fill it in.
