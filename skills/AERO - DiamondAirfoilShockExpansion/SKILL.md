---
name: AERO - DiamondAirfoilShockExpansion
description: >-
  Run the diamond-airfoil shock-expansion program and report its printed
  results and PNG. Use when the user wants the four panel pressures or the
  section lift and drag coefficients of a symmetric diamond airfoil in a
  supersonic stream, or a sketch of the shocks and expansion fans. Do not
  redraw the waves or recompute the numbers by hand.
---

# AERO - DiamondAirfoilShockExpansion

Use this skill for a symmetric diamond (double-wedge) airfoil with maximum thickness at mid-chord. Run the program once; quote its stdout and include its PNG. Do not redraw the waves or recompute the numbers by hand.

\[
\delta_{u1} = \varepsilon - \alpha, \qquad \delta_{l1} = \varepsilon + \alpha
\]

A positive turn is a weak oblique shock. A negative turn is a Prandtl-Meyer expansion. Zero turn is a Mach wave. Each shoulder expands through \(2\varepsilon\). Panel pressures are relative to freestream static pressure. Section coefficients omit skin friction:

\[
c_n = \tfrac12(C_{p,l1}+C_{p,l2}-C_{p,u1}-C_{p,u2})
\]

\[
c_a = \tfrac12\tan\varepsilon\,(C_{p,u1}+C_{p,l1}-C_{p,u2}-C_{p,l2})
\]

\[
c_l = c_n\cos\alpha - c_a\sin\alpha, \qquad
c_d = c_n\sin\alpha + c_a\cos\alpha
\]

Shock and Prandtl-Meyer numerics come from `AERO - PrandtlMeyerAndShocks`. Trailing-edge wake pressure matching is not modeled. A detached leading-edge shock or an impossible expansion sets `solution` to a failure tag and omits \(c_l\) and \(c_d\).

## When to run

1. Use this skill when the user asks for diamond-airfoil panel pressures, section lift or drag from shock-expansion theory, or a sketch of the waves on a diamond airfoil.
2. Convert the half-angle and angle of attack to radians before the call. State the converted units in the reply. Do not invent Mach, gamma, half-angle, or angle of attack.
3. If the user asks for a cone, a cambered airfoil, or subsonic flow, say this program is the two-dimensional symmetric diamond and do not run it for that case.
4. Interactive lab offer: before running this program for a new diamond-airfoil shock-expansion design or sizing thread, ask once whether the user wants `AERO - CompressibleFlowDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/AERO - DiamondAirfoilShockExpansion/diamond_airfoil_shock_expansion.py" --mach <M> --epsilon <rad> --alpha <rad> [--gamma <k>] [--out <png>]
```

Pass **only** flags the user supplied (after converting angles to radians). Do **not** supply a default Mach, half-angle, or angle of attack.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Freestream Mach \(M_\infty\) | dimensionless, \(> 1\) | Required |
| `--epsilon` | Diamond half-angle \(\varepsilon\) | rad, strictly between 0 and \(\pi/2\) | Required |
| `--alpha` | Angle of attack \(\alpha\) | rad, \(\lvert\alpha\rvert < \pi/2\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

Angles in degrees use `angle_rad = angle_deg * pi/180`. A bare `--mach`, `--epsilon`, and `--alpha` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The figure title is `Diamond airfoil shock-expansion`. Red lines are oblique shocks. Blue rays are Prandtl-Meyer fans.
3. Report `gamma` and `gamma_source`. `default` means \(\gamma = 1.4\) air.
4. Report `M_inf`, `epsilon_deg`, `alpha_deg`, `delta_u1_deg`, `delta_l1_deg`, and `shoulder_deg`.
5. Report `solution`. When it is `ok`, report the four panel pressures `p_u1_over_pinf`, `p_u2_over_pinf`, `p_l1_over_pinf`, and `p_l2_over_pinf`, the pressure coefficients `Cp_u1` through `Cp_l2`, and `cn`, `ca`, `cl`, and `cd`.
6. Report `wave_u1`, `wave_u2`, `wave_l1`, and `wave_l2`, and the panel Mach numbers when printed. Report shock angles `theta_*_deg` only when they are printed.
7. When `solution` is not `ok`, say which corner failed and report any printed `delta_max_*_deg`. Do not invent panel pressures or force coefficients that were not printed.
8. If Mach, half-angle, or angle of attack is missing, or outside the program limits, say so. Do not fill it in.
