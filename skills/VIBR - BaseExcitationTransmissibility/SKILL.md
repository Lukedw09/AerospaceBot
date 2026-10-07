---
name: VIBR - BaseExcitationTransmissibility
description: >-
  Run the base-excitation transmissibility program and report its printed
  results and optional PNG. Use when the user wants the absolute displacement
  transmissibility of a single-degree-of-freedom mass on a spring and damper
  whose support moves at a stated frequency. Do not redraw the plot or
  recompute the numbers by hand.
---

# VIBR - BaseExcitationTransmissibility

Use this skill for steady harmonic base motion of one viscously damped oscillator. The base moves as \(y = Y\sin\omega t\). The mass coordinate \(x\) is absolute. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

The frequency ratio is `frequency_ratio`, \(r = f/f_n\). Absolute displacement transmissibility is `displacement_transmissibility`,

\[
T = \sqrt{\frac{1+(2\zeta r)^{2}}{(1-r^{2})^{2}+(2\zeta r)^{2}}}
\]

Isolation (\(T<1\)) is the region \(r>\sqrt{2}\). When \(\zeta<1/\sqrt{2}\), the peak of \(T\) is at `transmissibility_peak_ratio`, \(r_{\mathrm{peak}}=\sqrt{1-2\zeta^{2}}\).

`--fn` may be `f_Hz` from `VIBR - CantileverNaturalFrequency`. Force-driven step response stays on `GNC - SecondOrderResponse`. This skill is not force transmissibility \(F/(kY)\), not Miles' equation, and not a shock response spectrum.

## When to run

1. Use this skill when the user wants absolute displacement transmissibility, whether the mount isolates, or the frequency ratio of peak transmissibility for support motion.
2. Convert frequencies to hertz before the call. State the converted units in the reply. Do not invent natural frequency, damping ratio, or drive frequency.
3. Pass `--fn`, `--zeta`, and `--f`.
4. Pass `--out` only when the user wants the PNG of \(T\) versus \(r\). Do not invent a plot path when they did not ask for a figure.
5. Do not use this skill for multi-degree-of-freedom modes, random vibration, shock spectra, or a force applied directly to the mass.

## Flags

Run:

```text
python "skills/VIBR - BaseExcitationTransmissibility/base_excitation_transmissibility.py" --fn <Hz> --zeta <ratio> --f <Hz> [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--fn` | Undamped natural frequency \(f_n\) | Hz, \(> 0\) | Required |
| `--zeta` | Viscous damping ratio \(\zeta\) | dimensionless, \(\ge 0\) | Required |
| `--f` | Base drive frequency \(f\) | Hz, \(> 0\) | Required |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A frequency in rad/s is divided by \(2\pi\) before the call. `--fn` from the cantilever skill is already in hertz.

When `--out` is passed, the program writes one PNG. The plot title is `Base excitation transmissibility`. The curve is \(T(r)\) at the given damping. The square is the operating point. A vertical line marks \(r=\sqrt{2}\). `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `fn_Hz`, `f_Hz`, `zeta`, `r`, `T`, and `isolation`. `isolation` is `yes` when \(r>\sqrt{2}\) and `no` otherwise.
4. Report `r_peak` when it is printed. It is omitted when \(\zeta\ge 1/\sqrt{2}\), because \(T\) then has no peak at a positive frequency ratio. If damping is zero and the drive sits on \(f_n\), the program errors: that undamped resonance has no steady transmissibility.
5. If natural frequency, damping, or drive frequency is missing, say so. Do not fill them in.
