---
name: VIBR - RandomVibeRms
description: >-
  Run the random-vibration program and report its printed results and optional
  PNG. Use when the user wants Miles rms acceleration of one resonator under a
  flat acceleration spectrum, and the usual three-sigma peak estimate. Do not
  redraw the plot or recompute the numbers by hand.
---

# VIBR - RandomVibeRms

Use this skill for the rms acceleration of a single resonator — a bracket, a board, or a boom reduced to one mode — driven by a flat acceleration spectrum in g²/Hz. It is not the sine base-shake ratio in `VIBR - BaseExcitationTransmissibility`, and it is not a shock response spectrum. `--fn` may be `f_Hz` from `VIBR - CantileverNaturalFrequency`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The rms acceleration in g is `miles_rms_acceleration`,

\[
g_{\mathrm{rms}} = \sqrt{\frac{\pi}{2} f_n Q\, W_0}
\]

\(Q = 1/(2\zeta)\) when the damping ratio is the input. The program also prints `g_3sigma = 3 g_{\mathrm{rms}}` and labels it as the usual peak estimate, not a probability bound.

## When to run

1. Use this skill when the user wants Miles rms acceleration or the usual three-sigma peak for a flat spectrum at one resonance.
2. Convert natural frequency to hertz and the spectrum level to g²/Hz. State the converted units in the reply. Do not invent frequency, spectrum level, or damping.
3. Pass `--fn`, `--psd`, and exactly one of `--q` or `--zeta`.
4. Pass `--out` only when the user wants the PNG of rms acceleration versus natural frequency. Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for sine transmissibility or a shock spectrum.

## Flags

Run:

```text
python "skills/VIBR - RandomVibeRms/random_vibe_rms.py" --fn <Hz> --psd <g^2/Hz> (--q <Q> | --zeta <zeta>) [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--fn` | Natural frequency | Hz, \(> 0\) | Required |
| `--psd` | Flat spectrum level \(W_0\) at that resonance | g²/Hz, \(\ge 0\) | Required |
| `--q` | Quality factor | dimensionless, \(> 0\) | One of `--q` or `--zeta` |
| `--zeta` | Damping ratio | dimensionless, \(> 0\) | One of `--q` or `--zeta` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

When `--out` is passed, the program writes one PNG. The plot title is `Random vibration rms`. The curve is \(g_{\mathrm{rms}}\) versus natural frequency at the fixed spectrum and \(Q\). The square is the operating frequency. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `Q`, `g_rms`, `g_3sigma`, and `g_3sigma_note`.
4. If frequency, spectrum level, or a damping path is missing, say so. Do not fill them in.
