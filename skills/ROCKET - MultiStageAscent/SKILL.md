---
name: ROCKET - MultiStageAscent
description: >-
  Run the multi-stage ascent program and report its printed losses, burnout
  state, trajectory table, PNG, and HTML. Use when the user wants a powered
  ascent with staging mass drops and an optional fairing jettison. Do not
  integrate the path by hand.
---

# ROCKET - MultiStageAscent

Use this skill for a preliminary powered ascent from the surface through staging. Run the program once; quote its stdout. Include the PNG and give `viewer:` as a markdown link.

Assumptions (also printed): same path model as `ROCKET - BasicTrajectoryLossesFromBodySurface`. Stage 1 burns first from rest. Each stage inert is dropped at burnout. An optional jettison drops a named mass at an altitude or a time. Thrust is vacuum. Steering loss is zero while thrust is along the path or the flight-path angle is held. A one-stage constant-angle case with no quadratic drag uses the closed form so it matches the single-stage program.

## When to run

1. Use this skill when the user gives ordered stages with propellant, inert, specific impulse, and burn time or mass flow, plus a flight-path angle or a gravity-turn kick.
2. Pass one `--stage` per stage, bottom stage first. Keys are `mp`, `inert`, `isp`, and `tb` or `mdot`.
3. Pass `--gamma` or `--kick`, not both. Angles are radians.
4. Pass `--cd` and `--area`, or `--drag`, when the user gives drag. Pass `--jettison mass=<kg>,alt=<m>` or `mass=<kg>,time=<s>` for a fairing drop.
5. Pass `--payload` when the useful payload is known. It stays on the stack after the last inert drop.

## Flags

Run:

```text
python "skills/ROCKET - MultiStageAscent/multi_stage_ascent.py" --stages <n> --stage <mp=kg,inert=kg,isp=s,tb=s> [--stage ...] [--payload <kg>] (--gamma <rad> | --kick <rad>) [--cd <factor> --area <m^2> | --drag <N>] [--jettison <mass=kg,alt=m>] [--table <csv>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stages` | Number of stages | — | Required |
| `--stage` | `mp`, `inert`, `isp`, and `tb` or `mdot`. Bottom stage first | kg, s, kg/s | Required |
| `--payload` | Useful payload above the last stage | kg | Optional |
| `--gamma` | Held flight-path angle from the local horizontal | rad | Or `--kick` |
| `--kick` | Gravity-turn kick from local vertical | rad | Or `--gamma` |
| `--radius` | Body radius | m | Optional |
| `--mu` | Gravitational parameter | m^3/s^2 | Optional |
| `--alt` | Ignition altitude | m | Optional |
| `--drag` | Constant drag force | N | Or `--cd` |
| `--cd` | Drag coefficient | — | Optional |
| `--area` | Reference area for `--cd` | m^2 | Optional |
| `--rho` | Constant density | kg/m^3 | Optional |
| `--rho0` | Sea-level density for an exponential atmosphere | kg/m^3 | Optional |
| `--scale-height` | Exponential scale height | m | Optional |
| `--jettison` | `mass=<kg>,alt=<m>` or `mass=<kg>,time=<s>` | — | Optional |
| `--table` | Trajectory CSV path | — | Optional |
| `--out` | PNG path. HTML and the default CSV are written beside it | — | Optional |
| `--open` | Open the HTML viewer | — | Optional |

Every successful run writes a trajectory CSV, a PNG of the vehicle on the pad, and a self-contained HTML simulation. The viewer flies the vehicle from the pad, through the atmosphere, to burnout. `table:` is the CSV. `graph:` is the PNG. `viewer:` is the HTML.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. Give `viewer:` as a markdown link.
3. Report `gravity_loss_m_s`, `drag_loss_m_s`, `steering_loss_m_s`, `V_bo_m_s`, `gamma_bo_rad`, `r_bo_m`, and `Z_bo_m`.
4. Pass the CSV to `ROCKET - MaxQAndAeroLoad`. Pass `r_bo_m`, `V_bo_m_s`, and `gamma_bo_rad` to `ASTRO - OrbitInsertionFromBurnout` with the same `--radius` and `--mu` this run used.
5. Losses may be passed back into `ROCKET - LeoDeltaVBudget` on a later pass. Do not invent a pitch program.
6. If stage masses or both gamma and kick are missing, say so. Do not fill them in.
