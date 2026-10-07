---
name: GNC - SecondOrderResponse
description: >-
  Run the linear second-order unit-step response program and report its printed
  results and optional PNG. Use when the user wants damped frequency, overshoot,
  peak time, rise time, settling time, or under/critical/over-damped class from
  natural frequency and damping ratio, or from mass, stiffness, and viscous
  damping. Do not redraw the plot or recompute the numbers by hand.
---

# GNC - SecondOrderResponse

Use this skill for a linear, constant-coefficient, single-input second-order plant with unity DC gain. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

From mass, stiffness, and damping, natural frequency is `natural_frequency_mass_stiffness` and damping ratio is `damping_ratio_mass_stiffness`:

\[
\omega_n = \sqrt{\frac{k}{m}},\qquad \zeta = \frac{c}{2\sqrt{k m}}
\]

Damped frequency, fractional overshoot, peak time, and envelope settling time (underdamped) are `damped_natural_frequency`, `second_order_percent_overshoot`, `second_order_peak_time`, and `second_order_settling_time`:

\[
\omega_d = \omega_n\sqrt{1-\zeta^{2}},\qquad
M_p = \exp\left(-\frac{\pi\zeta}{\sqrt{1-\zeta^{2}}}\right),\qquad
t_p = \frac{\pi}{\omega_d},\qquad
t_s = \frac{-\ln\delta}{\zeta\omega_n}
\]

Percent overshoot is \(100 M_p\). Default settling band is 2%, so \(\delta=0.02\). Rise time is the 10% to 90% interval on the analytical unit-step response. The damping case is underdamped when \(\zeta<1\), critically damped when \(\zeta=1\), and overdamped when \(\zeta>1\).

## When to run

1. Use this skill when the user wants second-order step-response metrics: damped frequency, overshoot, peak time, rise time, settling time, damping class, or a unit-step PNG.
2. Convert inputs to SI before the call (rad/s, kg, N/m, N·s/m). State the converted units in the reply. Do not invent \(\omega_n\), \(\zeta\), mass, stiffness, or damping.
3. Pass exactly one path: `--wn` with `--zeta`, or `--mass` with `--stiffness` and `--damping`. Do not mix the paths.
4. Pass `--settling-percent` only when the user gave a band other than 2%. A value of `5` means a 5% band (\(\delta=0.05\)).
5. Pass `--out` only when the user wants the PNG of the unit-step response. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for higher-order plants, zeros in the numerator, nonlinear damping, or MIMO systems.

## Flags

Run:

```text
python "skills/GNC - SecondOrderResponse/second_order_response.py" (--wn <rad/s> --zeta <zeta> | --mass <kg> --stiffness <N/m> --damping <N*s/m>) [--settling-percent <percent>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--wn` | Undamped natural frequency \(\omega_n\) | rad/s, \(> 0\) | With `--zeta` |
| `--zeta` | Damping ratio \(\zeta\) | dimensionless, \(\ge 0\) | With `--wn` |
| `--mass` | Mass \(m\) | kg, \(> 0\) | With `--stiffness` and `--damping` |
| `--stiffness` | Stiffness \(k\) | N/m, \(> 0\) | With `--mass` and `--damping` |
| `--damping` | Viscous damping \(c\) | N·s/m, \(\ge 0\) | With `--mass` and `--stiffness` |
| `--settling-percent` | Settling band in percent | dimensionless, \(0 < p < 100\) | Optional; default 2 |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Natural frequency in hertz uses \(\omega_n = 2\pi f_n\). Stiffness in N/mm uses `1 N/mm = 1000 N/m`. Mass in grams uses `1 g = 0.001 kg`.

When `--out` is passed, the program writes one PNG. The plot title is `Second-order unit-step response`. The curve is the unit-step output versus time. Dashed lines are the settling band. The square is the first peak when underdamped. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `source`, `wn_rad_s`, `zeta`, and `damping_case`. `wn_zeta` means modal inputs. `mass_stiffness_damping` means mechanical inputs.
4. Report `m_kg`, `k_N_m`, and `c_N_s_m` when they are printed.
5. Report `wd_rad_s`, `overshoot`, `overshoot_percent`, and `peak_time_s` when they are printed (underdamped).
6. Report `rise_time_s`, `settling_percent`, `settling_delta`, `settling_time_envelope_s` when printed, and `settling_time_s`. Rise time is 10% to 90%. `settling_time_s` is from the analytical step response staying in the band; the envelope value is the closed-form estimate.
7. If \(\omega_n\) and \(\zeta\), or mass, stiffness, and damping, are missing, say so. Do not fill them in.
