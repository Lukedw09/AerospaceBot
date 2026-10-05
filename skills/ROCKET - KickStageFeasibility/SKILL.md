---
name: ROCKET - KickStageFeasibility
description: >-
  Run the kick-stage feasibility program and report its printed results and PNG.
  Use when the user wants thrust-to-weight and burn-time feasibility for an
  in-space kick stage, including coast attitude-control limits, maximum
  continuous burn duration, and main-engine restart count. Do not redraw the
  plot or recompute the numbers by hand.
---

# ROCKET - KickStageFeasibility

Use this skill for T/W and burn-time feasibility of a kick stage. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Assumptions (also printed by the program): in-space kick stage; vacuum; constant thrust and constant \(I_s\) over each powered arc; ideal rocket equation with \(c = I_s g_0\); no gravity loss, drag, or trajectory integration. \(\mathrm{T/W} = T/(m g_0)\) uses \(g_0 = 9.80665\,\mathrm{m/s}^2\) as the weight reference only (not a lift-off constraint). T/W bounds are checked at every equal-split burn ignition mass. Total burn time is \(t_b = (m_0 - m_f) c / T\). When `--burns` is omitted, the program chooses the fewest equal-duration burns that each stay within `--tb-max`. Restarts used are \(n_{\mathrm{burns}} - 1\). `--coast-max` is a per-coast duration limit checked against the peak coast. `--acs-mp` / `--acs-mdot` give a total ACS propellant budget checked against the sum of coast durations. Multi-burn plans with a coast limit but no `--coast` are not feasible. Coast durations between burns come from repeated `--coast`.

This program does not size tanks, integrate a trajectory, or replace `ASTRO - MultiBurnLeoRaise` for a finite-thrust LEO raise.

## When to run

1. Use this skill when the user asks whether a kick stage thrust, burn time, coast ACS limit, or restart budget is feasible.
2. Convert all inputs to SI before the call (N, s, kg, m/s). State the converted units in the reply. Do not invent values the user did not give.
3. Pass `--thrust`, `--isp`, `--m0`, `--tb-max`, and `--restarts-max`.
4. Pass exactly one of `--mf`, `--mp`, or `--dv` for the main-engine propellant / ideal Δv.
5. Pass `--burns` only when the user names a planned burn count. Omit it so the program picks the fewest burns that fit `--tb-max`.
6. Pass `--coast` once per coast between burns, in order, when the user gives coast durations. The count must equal `restarts_used` (`n_burns - 1`).
7. Pass `--coast-max` when the user gives a maximum single-coast duration. Pass `--acs-mp` with `--acs-mdot` when the limit is total ACS propellant over effective ACS mass-flow (sum of coasts). Both may be given; each is checked on its own rule (peak vs `--coast-max`, sum vs ACS capacity).
8. Pass `--tw-min` and/or `--tw-max` only when the user states ignition T/W bounds. Bounds apply to every equal-split burn ignition, not only the first. Do not invent a T/W band.
9. Do not invent a missing thrust, \(I_s\), ignition mass, propellant / burnout / Δv, maximum burn duration, or restart count.

## Flags

Run:

```text
python "skills/ROCKET - KickStageFeasibility/kick_stage_feasibility.py" --thrust <N> --isp <s> --m0 <kg> (--mf <kg> | --mp <kg> | --dv <m/s>) --tb-max <s> --restarts-max <n> [--burns <n>] [--coast <s> ...] [--coast-max <s>] [--acs-mp <kg> --acs-mdot <kg/s>] [--tw-min <TW>] [--tw-max <TW>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--thrust` | Vacuum thrust \(T\) | N, \(> 0\) | Required |
| `--isp` | Vacuum specific impulse \(I_s\) | s, \(> 0\) | Required |
| `--m0` | Ignition mass | kg, \(> 0\) | Required |
| `--mf` | Burnout mass | kg, \(> 0\), \(< m_0\) | Or `--mp` / `--dv` |
| `--mp` | Usable main-engine propellant mass | kg, \(> 0\), \(< m_0\) | Or `--mf` / `--dv` |
| `--dv` | Ideal vacuum delta-v | m/s, \(> 0\) | Or `--mf` / `--mp` |
| `--tb-max` | Maximum continuous burn duration per powered arc | s, \(> 0\) | Required |
| `--restarts-max` | Maximum main-engine restarts after first ignition | integer, \(\ge 0\) | Required |
| `--burns` | Planned number of powered arcs | integer, \(\ge 1\) | Optional. Fewest that fit `--tb-max` if omitted |
| `--coast` | Coast duration between burns, in order | s, \(\ge 0\) | Optional; repeat once per gap |
| `--coast-max` | Maximum coast the attitude-control system can support | s, \(> 0\) | Optional |
| `--acs-mp` | Usable ACS propellant for coast attitude control | kg, \(> 0\) | Optional; with `--acs-mdot` |
| `--acs-mdot` | ACS effective propellant mass-flow during coast control | kg/s, \(> 0\) | Optional; with `--acs-mp` |
| `--tw-min` | Minimum allowed ignition T/W | dimensionless, \(\ge 0\) | Optional |
| `--tw-max` | Maximum allowed ignition T/W | dimensionless, \(> 0\) | Optional |
| `--out` | PNG path | — | Optional |

Mass in pounds-mass uses `1 lbm = 0.45359237 kg`. Thrust in lbf uses `1 lbf = 4.4482216152605 N`. Specific impulse is already seconds. Delta-v in feet per second uses `1 ft/s = 0.3048 m/s`. If the user gives effective exhaust velocity \(c\) in m/s, pass \(I_s = c / g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\) and say so. Do not put \(c\) in `--isp`.

`--restarts-max` is restarts after the first ignition. One burn uses zero restarts. Two burns use one restart. The implied ignition budget is `restarts-max + 1`.

Every successful run writes one PNG. The plot title is `Kick-stage T/W and burn-time feasibility`. The horizontal axis is burn time per powered arc; the vertical axis is T/W. The `--tb-max` limit and any T/W band are shaded. Ignition and burnout T/W are marked at `tb_each_s`. `graph:` is the PNG path.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. Do not draw a second figure.
3. Report `thrust_N`, `isp_s`, `c_m_s`, `m0_kg`, `mf_kg`, `mp_kg`, `mass_source`, `dv_ideal_m_s`, and `mdot_kg_s`.
4. Report `tb_total_s`, `TW0`, `TWf`, `TW_ignition_min`, `TW_ignition_max`, each `TW_ignition_k`, `TW_min`, `TW_max`, and `TW_check`.
5. Report `tb_max_s`, `n_burns_min_for_tb_max`, `n_burns`, `n_burns_source`, `tb_each_s`, `mp_each_kg`, and `burn_duration_check`.
6. Report `restarts_max`, `ignitions_max`, `restarts_used`, and `restart_check`.
7. Report coast fields: `coast_max_s`, `coast_max_source`, each `coast_k_s` when printed, `coast_peak_s`, `coast_sum_s`, `coast_peak_check`, `coast_acs_check`, and `coast_check`. When ACS inputs were given, also report `acs_mp_kg`, `acs_mdot_kg_s`, and `coast_capacity_from_acs_s`.
8. Report `feasible` as printed (`yes` or `no`).
9. Repeat every `warning` when printed.
10. If thrust, \(I_s\), ignition mass, propellant / burnout / Δv, `--tb-max`, or `--restarts-max` is missing, say so. Do not fill it in. Point a finite-thrust LEO raise with gravity loss to `ASTRO - MultiBurnLeoRaise`, ideal staged payload/Δv to `ROCKET - PayloadtoDeltaV`, and propellant volume from mass flow and burn time to `ROCKET - PropellantLoad`.
