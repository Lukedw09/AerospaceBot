---
name: ROCKET - VehicleMassBudget
description: >-
  Run the vehicle mass-budget program and report its printed stage inert,
  stacked mass, and PNG. Use when the user is assembling per-stage inert
  from tanks, engines, fairing, interstage, and a structure law for
  PayloadtoDeltaV. Do not sum the masses by hand.
---

# ROCKET - VehicleMassBudget

Use this skill to turn component masses into per-stage `mp` and `inert` for `ROCKET - PayloadtoDeltaV`. Run the program once; quote its stdout. Include the PNG.

Assumptions (also printed): stage 1 is the bottom stage. If `k` is set, `structure_mass_linear` is \(m_s=m_H+k\,m_p\) and explicit component masses are refused. Otherwise inert is tank + engines + fairing + interstage + other + \(m_H\) + residuals. Residuals are inert. Stacked mass is useful payload plus every stage propellant and inert.

## When to run

1. Use this skill when the user has a propellant mass and either a structure factor or explicit hardware masses for each stage.
2. Pass one `--stage` per stage, bottom stage first. The count must equal `--stages`.
3. On a `--stage` line, pass `k` and `mH` or the explicit masses, not both. `engine-count` needs `engine-mass`.
4. Pass `--payload` only when the user gives a useful payload. An omitted payload is 0.

## Flags

Run:

```text
python "skills/ROCKET - VehicleMassBudget/vehicle_mass_budget.py" --stages <n> --stage <mp=kg,...> [--stage ...] [--payload <kg>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stages` | Number of stages | — | Required |
| `--stage` | One stage, bottom first. Keys: `mp`, and either `k` with optional `mH` and `residuals`, or `tank`, `engine-mass`, `engine-count`, `fairing`, `interstage`, `other`, `mH`, `residuals` | kg, except `k` and `engine-count` | Required |
| `--payload` | Useful payload | kg | Optional |
| `--out` | PNG path | — | Optional |

`--stage` may be repeated. Example: `mp=100,k=0.1,mH=10`.

Every successful run writes a PNG stacked-mass chart. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG.
3. Report each `stage_N_mp_kg`, `stage_N_inert_kg`, `payload_to_deltav_stage_N`, and `stacked_mass_kg`.
4. Pass each `payload_to_deltav_stage_N` string to `ROCKET - PayloadtoDeltaV` or the stage masses to `ROCKET - MultiStageAscent`.
5. If propellant or the structure law is missing, say so. Do not fill them in.
