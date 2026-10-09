---
name: AERO - PrandtlMeyerAndShocks
description: >-
  Run the oblique-shock and Prandtl-Meyer wedge program and report its
  printed results and PNG. Use when the user wants a shock angle, downstream
  Mach, static pressure ratio, whether a wedge shock is attached, or the
  Prandtl-Meyer turn through the same deflection. Do not redraw the shock
  or recompute the numbers by hand.
---

# AERO - PrandtlMeyerAndShocks

Use this skill for a two-dimensional wedge in a uniform supersonic stream. One deflection is the wedge semivertex angle and the Prandtl-Meyer turning angle. Run the program once; quote its stdout and include its PNG. Do not redraw the shock or recompute the numbers by hand.

The reported shock is the weak root of the theta-delta-Mach relation. It is attached when the deflection does not exceed the maximum turning of that relation. Zero deflection is a Mach wave. The strong root is printed only when it is a distinct second solution. The freestream expansion through the same angle uses the Prandtl-Meyer function. When `fan:` is printed, that fan turns the post-shock flow back through the same deflection.

This is a wedge, not a cone. Shock curvature, boundary layer, and separation are not modeled.

## When to run

1. Use this skill when the user asks for an oblique shock, a wedge wave angle, whether the shock is attached, a Prandtl-Meyer expansion through a known turning angle, or the shock and expansion on the same wedge.
2. Convert the deflection to radians before the call. State the converted units in the reply. Do not invent Mach, gamma, or deflection.
3. If the user asks for a cone, say this program is the two-dimensional wedge and do not run it as a cone solution.
4. Interactive lab offer: before running this program for a new oblique-shock or Prandtl-Meyer design or sizing thread, ask once whether the user wants `AERO - CompressibleFlowDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py" --mach <M1> --delta <rad> [--gamma <k>] [--out <png>]
```

Pass **only** flags the user supplied (after converting the deflection to radians). Do **not** supply a default Mach or deflection.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Upstream Mach \(M_1\) | dimensionless, \(> 1\) | Required |
| `--delta` | Deflection \(\delta\) | rad, 0 up to \(\pi/2\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

A deflection in degrees uses `delta_rad = delta_deg * pi/180`. A bare `--mach` and `--delta` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The figure title is `Oblique shock and Prandtl-Meyer wedge`. The left panel is the shock. The right panel is the Prandtl-Meyer expansion. A detached bow is marked schematic.
3. Report `gamma` and `gamma_source`. `default` means \(\gamma = 1.4\) air.
4. Report `M1`, `delta_deg`, `mu1_deg`, and `delta_max_deg`. \(\delta\) is the wedge semivertex angle.
5. When `attached: yes`, report `shock`, `theta_deg`, `M2`, `M2_regime`, and `p2_over_p1`. \(\theta\) is the wave angle from the upstream velocity. \(M_2\) and \(p_2/p_1\) are the state behind that shock.
6. When `shock: mach-wave`, say the wave angle is the Mach angle, \(M_2 = M_1\), and the static pressure ratio is 1.
7. When `attached: no`, say the shock is detached. Report `delta_max_deg`. Do not invent a shock angle, downstream Mach, or shock pressure ratio.
8. Report `theta_strong_deg`, `M2_strong`, and `p2_over_p1_strong` only when they are printed. Say that the wedge uses the weak root.
9. Report `expansion`. When it is `prandtl-meyer`, report `pm_M` and `pm_p_ratio`. Those are the freestream expansion through the same deflection, not the state behind the shock. When it is `exceeds-maximum-turn`, say a uniform Prandtl-Meyer state does not exist for that turn.
10. Report `fan`, `fan_M`, `fan_p_ratio`, and `fan_p_over_p1` only when they are printed. `fan_p_ratio` is the pressure ratio across the shoulder fan. `fan_p_over_p1` is that state relative to the freestream. `fan: subsonic` or `fan: exceeds-maximum-turn` means the post-shock flow cannot make that turn in a simple fan.
11. If Mach or deflection is missing, or outside the program limits, say so. Do not fill it in.
