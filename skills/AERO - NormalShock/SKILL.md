---
name: AERO - NormalShock
description: >-
  Run the normal-shock program and report its printed results and PNG. Use
  when the user wants the downstream Mach number, static pressure,
  temperature, or density ratio, stagnation-pressure ratio, or entropy jump
  of a simple normal shock from the upstream Mach number. Do not redraw the
  plot or recompute the numbers by hand.
---

# AERO - NormalShock

Use this skill for a steady normal shock in a calorically perfect gas. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

Downstream Mach uses `normal_shock_mach`, which is \(M_2^{2}\):

\[
M_2^{2} = \frac{(\gamma - 1) M_1^{2} + 2}{2\gamma M_1^{2} - (\gamma - 1)}
\]

Static ratios are `normal_shock_pressure`, `normal_shock_temperature`, and `normal_shock_density`. The stagnation-pressure ratio is `normal_shock_stagnation_pressure`:

\[
\frac{p_{t2}}{p_{t1}}
=
\left[\frac{(\gamma + 1) M_1^{2}}{(\gamma - 1) M_1^{2} + 2}\right]^{\gamma/(\gamma - 1)}
\left[\frac{\gamma + 1}{2\gamma M_1^{2} - (\gamma - 1)}\right]^{1/(\gamma - 1)}
\]

The entropy jump is `normal_shock_entropy_over_r`, \(\Delta s/R = -\ln(p_{t2}/p_{t1})\). Total temperature is unchanged. This is a normal shock, not an oblique wedge or a cone.

## When to run

1. Use this skill when the user wants a simple normal-shock jump: downstream Mach, static pressure, temperature, or density ratio, stagnation-pressure ratio, or entropy jump.
2. Mach number is dimensionless. Do not invent \(M_1\) or \(\gamma\).
3. One upstream Mach number is one run. Do not sweep.
4. If the Mach number is below 1, say so and stop. If the user asks for an oblique shock or a cone, use `AERO - PrandtlMeyerAndShocks` or `AERO - ConicalShock` instead.

## Flags

Run:

```text
python "skills/AERO - NormalShock/normal_shock.py" --mach <M1> [--gamma <k>] [--out <png>]
```

Pass **only** flags the user supplied. Do **not** supply a default Mach.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mach` | Upstream Mach \(M_1\) | dimensionless, \(\ge 1\) | Required |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional. Program default \(1.4\) (air). |
| `--out` | PNG path | — | Optional |

A bare `--mach` with no `--gamma` is valid. The program then uses \(\gamma = 1.4\) and prints `gamma_source: default`.

Every successful run writes one PNG. The plot title is `Normal shock ratios`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The horizontal axis is upstream Mach. The upper panel is \(M_2\), \(p_{t2}/p_{t1}\), and \(\Delta s/R\). The lower panel is \(p_2/p_1\), \(T_2/T_1\), and \(\rho_2/\rho_1\). The squares mark the given Mach.
3. Report `M1`, `gamma`, and `gamma_source`. `default` means \(\gamma = 1.4\) air.
4. Report `M2`, `p2_over_p1`, `T2_over_T1`, and `rho2_over_rho1`.
5. Report `pt2_over_pt1`. That is the total-pressure ratio across the shock, not the Rayleigh-Pitot \(p_{t2}/p_1\).
6. Report `ds_over_R`. That is the specific-entropy jump divided by \(R\).
7. If Mach is missing, or outside the program limits, say so. Do not fill it in.
