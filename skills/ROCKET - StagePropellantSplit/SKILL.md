---
name: ROCKET - StagePropellantSplit
description: >-
  Run the stage propellant-split program and report its printed stage masses
  and PNG. Use when the user wants propellant and inert allocated across
  stages for an ideal delta-v at a payload or a gross liftoff mass. Do not
  solve the rocket equation by hand.
---

# ROCKET - StagePropellantSplit

Use this skill to allocate propellant across stages. Run the program once; quote its stdout. Include the PNG.

Assumptions (also printed): gravity-free `delta_v_vacuum` with \(c=I_{sp} g_0\) and \(g_0=9.80665\,\mathrm{m/s}^2\). `structural_coefficient` is \(\epsilon=m_s/(m_s+m_p)\). Glenn `mass_ratio_from_payload_and_structure` is \(m_0/m_f\). The printed `stage_N_MR` is the catalogue mass ratio \(m_f/m_0\). Stage 1 burns first. `equal_dv` shares the ideal delta-v equally. `equal_mr` uses one \(m_0/m_f\). `max_payload` searches the split at a fixed gross liftoff mass.

## When to run

1. Use this skill when the user gives a stage count, each stage \(I_{sp}\) and \(\epsilon\), a target ideal delta-v, and either a useful payload or a gross liftoff mass.
2. Pass one `--stage` per stage, bottom stage first, as `isp=<s>,eps=<fraction>`.
3. Pass `--payload` or `--glow`, not both. `max_payload` needs `--glow`.
4. Pass `--mode equal_dv`, `equal_mr`, or `max_payload`. An omitted mode is `equal_dv`.
5. Interactive lab offer: before running this program for a new stage-split, mass-budget, LEO delta-v, ascent, or max-q design or sizing thread, ask once whether the user wants `ROCKET - StageAscentDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/ROCKET - StagePropellantSplit/stage_propellant_split.py" --stages <n> --stage <isp=s,eps=fraction> [--stage ...] --dv <m/s> (--payload <kg> | --glow <kg>) [--mode equal_dv|equal_mr|max_payload] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stages` | Number of stages | — | Required |
| `--stage` | `isp` and `eps` for one stage, bottom first | s, dimensionless | Required |
| `--dv` | Target ideal delta-v | m/s | Required |
| `--payload` | Useful payload. Sizes the stack upward | kg | Or `--glow` |
| `--glow` | Gross liftoff mass. Sizes the stack downward | kg | Or `--payload` |
| `--mode` | `equal_dv`, `equal_mr`, or `max_payload` | — | Optional |
| `--out` | PNG path | — | Optional |

Every successful run writes a PNG of the split. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG.
3. Report each `stage_N_mp_kg`, `stage_N_inert_kg`, `stage_N_dv_m_s`, `stage_N_MR`, `payload_kg`, and `stacked_mass_kg`.
4. Pass each `payload_to_deltav_stage_N` string to `ROCKET - PayloadtoDeltaV`. Pass `mp` and `inert` to `ROCKET - MultiStageAscent`.
5. If \(I_{sp}\), \(\epsilon\), delta-v, or both payload and liftoff mass are missing, say so. Do not fill them in.
