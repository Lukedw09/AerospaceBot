---
name: ROCKET - KickStageNozzle
description: >-
  Run the kick-stage nozzle synthesis program and report its printed results
  and optional PNG. Use when the user wants vacuum or above-86 km nozzle
  expansion design for a kick stage: area ratio, exit Mach, vacuum CF, conical
  or length-fraction length, optional shell mass, and Summerfield separation
  margin. The 1976 hydrostatic table alone is not enough. Do not redraw the
  curve or recompute the numbers by hand.
---

# ROCKET - KickStageNozzle

Use this skill for practical vacuum / high-altitude kick-stage nozzle synthesis. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the curve or recompute the numbers by hand.

There is no finite \(p_e = p_a\) optimum in vacuum: ideal \(C_F\) keeps rising with \(\epsilon\), with diminishing returns. The 1976 U.S. Standard Atmosphere hydrostatic pressure model ends at 86 km, so this program does **not** look up ambient pressure from that table. For a design point, the user must give `--epsilon` or `--pe`. Optional `--pa` is a known ambient (including a value the user supplies for altitudes above 86 km) used only for ambient \(C_F\) and Summerfield separation. Point altitude-matched expansion on Earth from sea level through 86 km to `ROCKET - ExpansionMatchEarth`.

Me, \(\epsilon\), \(p_e\), and ideal \(C_F\) come from `ROCKET - Area-Mach Graph`. Vacuum \(C_F\) uses \(p_a = 0\). Geometry is a conical divergent wall of half-angle \(\alpha\): axial length \(L = f_L (R_e - R_t)/\tan\alpha\) with length fraction \(f_L\) (1 = full cone; 0.8 is a common 80%-bell length surrogate at the same \(\epsilon\)). Optional shell mass is frustum lateral area times thickness times material density. Separation uses \(p_{e,\mathrm{sep}} = k_{\mathrm{sep}} p_a\) with default \(k_{\mathrm{sep}} = 0.4\) (Summerfield); margin is \(p_e/p_{e,\mathrm{sep}} - 1\). This program does not call CEA and does not invent \(\epsilon\) or \(p_e\).

## When to run

Interactive lab offer: before running this program for a new engine, nozzle, or chamber design or sizing thread, ask once whether the user wants `ROCKET - NozzleChamberDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

1. Design point: the user gives chamber pressure and either a design area ratio or a design exit pressure. Pass `--pc` with exactly one of `--epsilon` or `--pe`.
2. Pass `--pa` only when the user gives a finite ambient pressure (ignition altitude residual atmosphere, test cell, etc.). Omit `--pa` for vacuum.
3. Pass `--alt` only as a note when the user named a geometric altitude. It does not set \(p_a\) from the 1976 table. If they want pe=pa matching at or below 86 km, use `ROCKET - ExpansionMatchEarth` instead.
4. Geometry / mass: pass `--throat` or `--rt` when they want length, exit radius, or thrust. Pass `--half-angle` (radians) when they give a cone angle; default is \(15^\circ\). Pass `--length-fraction` when they want a shortened bell-length surrogate (e.g. 0.8). Pass both `--thickness` and `--rho-mat` for shell mass.
5. Separation: pass `--pa` to get `pe_over_pa`, `separation_margin`, and `separation`. Pass `--k-sep` only when they override the Summerfield ratio (default 0.4).
6. Sweep: the user wants vacuum \(C_F\) (and length, if throat is given) versus \(\epsilon\). Pass `--epsilon-min` and `--epsilon-max`. Optionally mark a design with `--epsilon` or `--pe`.
7. Convert inputs to SI before the call (Pa, m, rad). State the converted units in the reply. Do not invent chamber pressure, \(\epsilon\), or \(p_e\).

## Flags

Run:

```text
python "skills/ROCKET - KickStageNozzle/kick_stage_nozzle.py" --pc <Pa> (--epsilon <e> | --pe <Pa>) [--gamma <k>] [--pa <Pa>] [--alt <m>] [--throat <m^2> | --rt <m>] [--half-angle <rad>] [--length-fraction <f>] [--thickness <m> --rho-mat <kg/m^3>] [--k-sep <k>]
python "skills/ROCKET - KickStageNozzle/kick_stage_nozzle.py" --pc <Pa> --epsilon-min <e> --epsilon-max <e> [--epsilon <e> | --pe <Pa>] [--gamma <k>] [--pa <Pa>] [--throat <m^2> | --rt <m>] [--half-angle <rad>] [--length-fraction <f>] [--out <png>]
```

Pass **only** flags the user supplied (after SI conversion), except program defaults for omitted `--gamma`, `--half-angle`, `--length-fraction`, and `--k-sep`.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pc` | Chamber pressure \(p_1\) | Pa, \(> 0\) | Required |
| `--epsilon` | Design \(A_e/A_t\) | dimensionless, \(\ge 1\) | Point: or `--pe` |
| `--pe` | Design exit pressure \(p_e\) | Pa, \(> 0\), \(< p_c\) | Point: or `--epsilon` |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Default \(1.4\) |
| `--pa` | Ambient pressure for CF and separation | Pa, \(\ge 0\) | Optional. Omit for vacuum |
| `--alt` | Geometric altitude note only | m, \(\ge 0\) | Optional. Does not set \(p_a\) |
| `--throat` | Throat area \(A_t\) | m², \(> 0\) | Optional; or `--rt` |
| `--rt` | Throat radius \(R_t\) | m, \(> 0\) | Optional; or `--throat` |
| `--half-angle` | Conical half-angle \(\alpha\) | rad, \((0,\pi/2)\) | Optional. Default \(15^\circ\) |
| `--length-fraction` | \(L / L_{\mathrm{cone}}\) | dimensionless, \(> 0\) | Optional. Default 1 |
| `--thickness` | Wall thickness | m, \(> 0\) | Optional; with `--rho-mat` |
| `--rho-mat` | Wall material density | kg/m³, \(> 0\) | Optional; with `--thickness` |
| `--k-sep` | Summerfield \(p_{e,\mathrm{sep}}/p_a\) | dimensionless, \(> 0\) | Optional. Default 0.4 |
| `--epsilon-min`, `--epsilon-max` | Sweep limits on \(\epsilon\) | dimensionless | Sweep |
| `--out` | PNG path for a sweep | — | Optional. Sweep |

A bare pressure is pascals. Use `p_Pa = p_bar * 1e5`, `1 atm = 101325 Pa`, `1 psi = 6894.757293168361 Pa`, and `1 torr = 133.3223684211 Pa`. Angles in degrees use \(\pi/180\). Length in inches uses `1 in = 0.0254 m`. Density in g/cm³ uses `1 g/cm³ = 1000 kg/m³`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG only when `graph:` is printed. The plot title is `Kick-stage nozzle: vacuum CF and length versus epsilon`.
3. Report `model`, `gamma`, `gamma_source`, `pc_Pa`, and `design_source` (`pe` or `epsilon`).
4. Report `pa_Pa`, `pa_source`, `pe_Pa`, `Me`, `epsilon`, `CF_vac`, `CF`, and `expansion`.
5. Report `k_sep`, `pe_over_pa`, `pe_sep_Pa`, `separation_margin`, and `separation`. In vacuum those pressure ratios print as `n/a` and `separation` is `not_applicable_vacuum`. When `separation` is `separated_or_at_risk`, ambient `CF` and `thrust_N` print as `invalid_separated`; still report `CF_vac` and `thrust_vac_N`.
6. When geometry is printed, report `throat_m2`, `Rt_m`, `Re_m`, `Ae_m2`, `half_angle_rad`, `length_fraction`, `L_cone_m`, `L_m`, `L_slant_m`, `thrust_vac_N`, and `thrust_N`.
7. When mass is printed, report `thickness_m`, `rho_mat_kg_m3`, and `m_nozzle_kg`.
8. On a sweep, report the marked design when present, or `epsilon_min` / `epsilon_max` with the end-point `CF_vac` (and length/mass when printed).
9. Repeat `warning` and `hint` when printed. `hint` points at `ROCKET - ExpansionMatchEarth` when `--alt` is at or below 86 km without `--pa`.
10. If chamber pressure or both of \(\epsilon\) and \(p_e\) are missing, say so. Do not fill them in. Point T/W and burn-time feasibility to `ROCKET - KickStageFeasibility`, and Earth pe=pa matching through 86 km to `ROCKET - ExpansionMatchEarth`.
