---
name: ROCKET - Area-Mach Graph
description: >-
  Run the area-Mach nozzle program and report its printed results and PNG.
  Use when the user wants a nozzle area-Mach curve, exit Mach from area ratio,
  exit pressure, ideal thrust, or underexpanded/overexpanded/perfectly expanded
  state. Do not redraw the curve or recompute the numbers by hand.
---

# ROCKET - Area-Mach Graph

Use this skill for a nozzle area-Mach curve, exit pressure, thrust, or expansion state. Run the program once; quote its stdout and include its PNG. Do not redraw the curve or recompute the numbers by hand.

Assumptions (also printed by the program): calorically perfect gas, steady one-dimensional isentropic nozzle, choked throat, negligible inlet velocity. The marked exit is the supersonic root (\(M_e \ge 1\)). The curve still shows the subsonic branch. The expansion flag is an ideal pressure comparison; it does not model separation.

## When to run

1. Use this skill when the user asks for an area-Mach plot, exit Mach from \(A_e/A_t\), nozzle exit pressure, ideal thrust, or expansion state.
2. Convert all inputs to SI before the call (Pa, m²). State the converted units in the reply. Do not invent values the user did not give.

## Flags

Run:

```text
python "skills/ROCKET - Area-Mach Graph/area_mach.py" [flags]
```

Pass **only** flags the user supplied (after SI conversion). Do **not** supply a default area ratio, ambient pressure, or throat area.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pc` | Chamber pressure \(p_1\) | Pa | Optional |
| `--epsilon` | Exit-to-throat area ratio \(A_2/A_t\) | dimensionless, \(\ge 1\) | Optional |
| `--gamma` | Ratio of specific heats | dimensionless | Optional; program default \(1.4\) (air). Pass a lower value for hot rocket gas. |
| `--pa` | Ambient pressure \(p_3\) | Pa | Optional; no assumed atmosphere |
| `--throat` | Throat area \(A_t\) | m² | Optional |

A run with only `--pc`, only `--gamma`, or no arguments is valid. That run plots how \(A/A^{*}\) varies with Mach. It does not invent an area ratio.

## What to report

1. Read the printed `key: value` summary and the PNG at `graph:`.
2. Include that PNG in the reply so the user sees the graph.
3. Always report the gamma used.
4. Report exit Mach, the area-ratio point, exit pressure, thrust, and the expansion flag **only when the program printed them**. Define each symbol and its unit.
5. If the user gave no area ratio, say the curve is the isentropic behavior at the gamma used, and that exit pressure, thrust, the expansion flag, and the marked exit point need an area ratio.

Conditional program outputs (do not invent missing keys):

- `--epsilon` → supersonic \(M_e\), exit point \((M_e, \epsilon)\)
- `--epsilon` and `--pc` → exit pressure \(p_e\) in Pa
- `--epsilon`, `--pc`, and `--throat` → thrust in N; if `--pa` omitted, vacuum thrust with \(p_3 = 0\)
- exit pressure and `--pa` both known → `underexpanded` / `overexpanded` / `perfectly expanded`

The plot title and stdout heading are `Area ratio versus Mach number` (not this skill's folder name).
