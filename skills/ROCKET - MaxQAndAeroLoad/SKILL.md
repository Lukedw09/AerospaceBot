---
name: ROCKET - MaxQAndAeroLoad
description: >-
  Run the max-q program and report its printed peak dynamic pressure, PNG, and
  HTML. Use when the user has an ascent table and wants q_max, the time and
  altitude of that peak, and an optional angle-of-attack times q. Do not
  recompute the peak by hand.
---

# ROCKET - MaxQAndAeroLoad

Use this skill for dynamic pressure along an ascent table. Run the program once; quote its stdout. Include the PNG and give `viewer:` as a markdown link.

Assumptions (also printed): \(q=\frac12\rho V^2\). The table supplies time, speed, and density, or time, speed, and altitude with the 1976 atmosphere below 86 km. `alpha_q` is angle of attack in radians times \(q\). Axial load factor is thrust over weight when both columns exist. \(g_0=9.80665\,\mathrm{m/s}^2\).

## When to run

1. Use this skill when a trajectory CSV from `ROCKET - MultiStageAscent` exists, or the user supplies columns `t_s`, `V_m_s`, and `rho_kg_m3` or `Z_m`.
2. Pass `--alpha` in radians only when the user gives an angle of attack.
3. Do not invent a \(C_D(\mathrm{Mach})\) table. This skill does not apply one.
4. Interactive lab offer: before running this program for a new stage-split, mass-budget, LEO delta-v, ascent, or max-q design or sizing thread, ask once whether the user wants `ROCKET - StageAscentDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/ROCKET - MaxQAndAeroLoad/max_q_and_aero_load.py" --table <csv> [--alpha <rad>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--table` | Ascent CSV | — | Required |
| `--alpha` | Angle of attack | rad | Optional |
| `--out` | PNG path. HTML is written beside it | — | Optional |
| `--open` | Open the HTML chart | — | Optional |

The CSV header from `ROCKET - MultiStageAscent` is `t_s,Z_m,V_m_s,gamma_rad,rho_kg_m3,q_Pa,m_kg`. A thrust column named `thrust_N` with `m_kg` also prints axial load factor.

Every successful run writes a PNG and a self-contained HTML chart of \(q\) versus time with the peak marked. `graph:` is the PNG. `viewer:` is the HTML.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. Give `viewer:` as a markdown link.
3. Report `q_max_Pa`, `t_maxq_s`, `Z_maxq_m`, and `q_max_interior`.
4. If `--alpha` was passed, report `alpha_q_max`. That product times a stated area and moment arm is a bending moment for `STRUCT - BeamBendingStress` when the user supplies the section.
5. If the table path is missing, say so. Do not fill it in.
