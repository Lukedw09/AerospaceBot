---
name: STRUCT - FatigueGoodman
description: >-
  Run the Goodman or Soderberg program and report the infinite-life factor,
  allowable alternating stress, and PNG. Use when the user has one mean and
  alternating stress plus endurance and ultimate or yield. Do not redraw the
  plot or recompute the numbers by hand.
---

# STRUCT - FatigueGoodman

Use this skill for one fluctuating stress against the classical infinite-life line. Goodman ends at ultimate tensile strength. Soderberg ends at yield. Both need the fully reversed endurance amplitude. Crack growth stays on `STRUCT - FractureCriticalCrack`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

\[
n=\frac{1}{\sigma_a/\sigma_e+\sigma_m/\sigma_{\mathrm{int}}}
\]

`goodman_factor` uses \(\sigma_{ut}\). `soderberg_factor` uses \(\sigma_y\). `goodman_allowable_alternating` is the alternating stress on that line at \(n=1\).

## When to run

1. Use this skill when the user wants a pass or fail for infinite life at one \(\sigma_a\) and \(\sigma_m\).
2. `--criterion` is required. Do not choose Goodman or Soderberg for the user.
3. Pass `--sigma-a`, `--sigma-m`, and `--se`. Goodman also needs `--sut`. Soderberg also needs `--sy`. Do not pass both intercepts.
4. Pass `--n` only when the user required a factor of safety. The load passes when the computed factor is at least that value. The default comparison is 1.
5. Do not use this skill for a Miner sum, a spectrum, or a crack-growth life.

## Flags

Run:

```text
python "skills/STRUCT - FatigueGoodman/fatigue_goodman.py" --criterion <goodman|soderberg> --sigma-a <Pa> --sigma-m <Pa> --se <Pa> [--sut <Pa>] [--sy <Pa>] [--n <factor>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--criterion` | `goodman` or `soderberg` | — | Required |
| `--sigma-a` | Alternating stress | Pa, \(\ge 0\) | Required |
| `--sigma-m` | Mean stress | Pa, \(\ge 0\) | Required |
| `--se` | Fully reversed endurance amplitude | Pa, \(> 0\) | Required |
| `--sut` | Ultimate tensile strength | Pa, \(> 0\) | Optional; required with `goodman` |
| `--sy` | Yield strength | Pa, \(> 0\) | Optional; required with `soderberg` |
| `--n` | Required factor of safety | dimensionless, \(> 0\) | Optional |
| `--out` | PNG path | file | Optional |
