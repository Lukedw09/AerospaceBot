---
name: ROCKET - CircularPortGrainHistory
description: >-
  Run the circular-port grain-history program and report its printed results
  and PNG. Use when the user wants chamber pressure, burning-area ratio, or
  remaining web versus time for an internal-burning circular grain with
  inhibited ends. Do not redraw the histories or recompute the numbers by
  hand.
---

# ROCKET - CircularPortGrainHistory

Use this skill for a circular-port solid-grain history. Run the program once; quote its stdout and include its PNG. Do not redraw the curves or recompute the numbers by hand.

Initial burning area is `circular_port_burning_area` with inhibited ends:

\[
A_b = 2\pi r L
\]

Pass the initial \(A_b\), or pass initial port radius \(R_p\) and grain length \(L\). Remaining web is `remaining_web` \(w_{\mathrm{rem}} = R_o - r\). \(K\) is `burning_area_ratio`. Chamber pressure is `equilibrium_chamber_pressure` at the instantaneous \(K\). Time is `remaining_web_time` along the local `burning_rate`.

The figure plots \(p_1\), \(K\), and remaining web against time from ignition to web burnout. An omitted `--sliver` is 0. A positive sliver percent stops the history at `sliver_port_radius` for that volume fraction. Erosive burning is omitted. Ends stay inhibited. \(a\) and \(n\) stay constant.

## When to run

1. Use this skill when the user wants circular-port \(p_1(t)\), \(K(t)\), remaining web versus time, or web-burnout time.
2. Convert inputs to SI before the call (m, m², kg/m³, m/s, and \(a\) in m/(s·Pa\(^{n}\))). State the converted units in the reply. Do not invent \(a\), \(n\), \(\rho_b\), or \(c^{*}\).
3. Required: `--a`, `--n`, `--outer`, `--throat`, `--rho`, `--cstar`, and grain geometry. Geometry is `--port` and `--length`, or `--ab` with `--port` or `--length`. If `--ab`, `--port`, and `--length` are all given, they must match \(A_b = 2\pi R_p L\).
4. `--sliver` is a volume percent in \([0, 100)\). Omit it for no sliver.

## Flags

Run:

```text
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --a <m/(s·Pa^n)> --n <n> --outer <m> --throat <m^2> --rho <kg/m^3> --cstar <m/s> (--port <m> --length <m> | --ab <m^2> --length <m> | --ab <m^2> --port <m>) [--sliver <percent>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Burn-rate coefficient \(a\) | m/(s·Pa\(^{n}\)) | Required |
| `--n` | Burn-rate pressure exponent \(n\) | dimensionless, \(< 1\) | Required |
| `--outer` | Outer propellant radius \(R_o\) | m, \(> R_p\) | Required |
| `--throat` | Throat area \(A_t\) | m² | Required |
| `--rho` | Solid propellant density \(\rho_b\) | kg/m³ | Required |
| `--cstar` | Characteristic velocity \(c^{*}\) | m/s | Required |
| `--port` | Initial port radius \(R_p\) | m | With `--length`, or with `--ab` |
| `--length` | Grain length \(L\) | m | With `--port`, or with `--ab` |
| `--ab` | Initial burning area \(A_b\) | m² | With `--port` or `--length` |
| `--sliver` | Sliver volume percent | percent, \([0, 100)\) | Optional; default 0 |
| `--out` | PNG path | — | Optional |

The coefficient \(a\) must match pressure in pascals. If the user gives \(a\) for \(p\) in MPa or psi, convert \(a\) so that \(r = a p_1^{n}\) is consistent with \(p_1\) in Pa before the call. Lengths in inches use `1 in = 0.0254 m`. Areas in square inches use `1 in² = 0.00064516 m²`. Density in g/cm³ uses `1 g/cm³ = 1000 kg/m³`.

Every successful run writes one PNG. The plot title is `Circular-port grain history`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The horizontal axis is time. The three panels are chamber pressure, burning-area ratio \(K\), and remaining web.
3. Report \(a\), \(n\), \(R_p\), \(L\), \(R_o\), initial \(A_b\), \(A_t\), \(\rho_b\), and \(c^{*}\) in SI.
4. Report `w0_m`, `t_burn_s`, `K_initial`, `K_burnout`, `pc_initial_Pa`, `pc_burnout_Pa`, `wrem_initial_m`, and `wrem_burnout_m`.
5. Report `sliver_percent`. Zero means web burnout with no leftover volume.
6. State that \(a\), \(n\), \(\rho_b\), and \(c^{*}\) were inputs, that ends stay inhibited, and that erosive burning is omitted.
7. If required inputs are missing, if \(n \ge 1\), or if geometry is inconsistent, say so and stop.
