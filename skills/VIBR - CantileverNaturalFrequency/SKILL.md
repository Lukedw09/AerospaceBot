---
name: VIBR - CantileverNaturalFrequency
description: >-
  Run the uniform cantilever fundamental bending natural-frequency program and
  report its printed results and optional PNG. Use when the user wants the first
  bending natural frequency of a uniform Euler–Bernoulli cantilever boom, spar,
  or PCB from Young’s modulus, second moment of area, length, and mass per
  length (or total beam mass). Do not redraw the plot or recompute the numbers
  by hand.
---

# VIBR - CantileverNaturalFrequency

Use this skill for the undamped fundamental bending natural frequency of a uniform Euler–Bernoulli cantilever (fixed–free). Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The first fixed–free root is `cantilever_lambda1_L`, \(\lambda_1 L \approx 1.875104\). Circular frequency is `cantilever_omega_bending_1` and cyclic frequency is `cantilever_freq_hz`:

\[
\omega_n = (\lambda_1 L)^{2}\sqrt{\frac{E I}{\mu L^{4}}},\qquad
f_{\mathrm{Hz}} = \frac{\omega_n}{2\pi}
\]

Primary mass path is mass per length \(\mu\). Alternate path is total beam mass with \(\mu = m_{\mathrm{beam}}/L\). Do not invent mass. Mode tag is `cantilever_uniform_bending_1`. Tip mass, higher modes, damping, and forced response are out of scope; for a forced second-order plant use `GNC - SecondOrderResponse`.

## When to run

1. Use this skill when the user wants the first bending natural frequency of a uniform cantilever boom, spar, longeron tip, or PCB (first-cut vibration).
2. Convert inputs to SI before the call (Pa, m⁴, m, kg/m or kg). State the converted units in the reply. Do not invent \(E\), \(I\), \(L\), \(\mu\), or beam mass.
3. Pass `--E`, `--inertia`, and `--length`. Pass exactly one mass path: `--mu` (primary), or `--mass` (sets \(\mu = m_{\mathrm{beam}}/L\)). Do not pass both.
4. Pass `--out` only when the user wants the PNG of \(f_1\) versus length at fixed \(E\), \(I\), and \(\mu\). Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for tip-mass / massless-beam formulas, higher bending modes, axial or torsional modes, damping, forced response, or non-cantilever end conditions in v1.

## Flags

Run:

```text
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --E <Pa> --inertia <m^4> --length <m> (--mu <kg/m> | --mass <kg>) [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--E` | Young’s modulus \(E\) | Pa, \(> 0\) | Required |
| `--inertia` | Second moment of area \(I\) | m⁴, \(> 0\) | Required |
| `--length` | Beam length \(L\) | m, \(> 0\) | Required |
| `--mu` | Mass per length \(\mu\) | kg/m, \(> 0\) | One of `--mu` or `--mass` (primary) |
| `--mass` | Total beam mass \(m_{\mathrm{beam}}\) | kg, \(> 0\) | One of `--mu` or `--mass`; sets \(\mu = m_{\mathrm{beam}}/L\) |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Stress or modulus in psi uses `1 psi = 6894.757293168361 Pa`. Stress or modulus in MPa uses `1 MPa = 1e6 Pa`. Length in inches uses `1 in = 0.0254 m`, so \(I\) in in⁴ uses `(0.0254)^4` m⁴. Mass in grams uses `1 g = 0.001 kg`. Mass per length in g/mm uses `1 g/mm = 1 kg/m`.

When `--out` is passed, the program writes one PNG. The plot title is `Cantilever natural frequency`. The curve is \(f_1(L)\) at fixed \(E\), \(I\), and \(\mu\), drawn from \(0.5L\) to \(1.5L\). The square is the operating length. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `E_Pa`, `I_m4`, `L_m`, `mu_kg_m`, `omega_n_rad_s`, `f_Hz`, and `mode`.
4. Report `mu_source` (`mu` or `mass`), and `m_beam_kg` when the mass path was used.
5. Report `lambda1_L` when printed.
6. If \(E\), \(I\), \(L\), or mass (\(\mu\) or \(m_{\mathrm{beam}}\)) is missing, say so. Do not fill them in.
