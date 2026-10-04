---
name: AERO - BreguetRangeEndurance
description: >-
  Run the Breguet cruise range and endurance program and report its printed
  results. Use when the user wants jet or propeller range or endurance from
  lift-to-drag ratio, specific fuel consumption, cruise speed, propeller
  efficiency, and start and end cruise weight. Do not recompute the numbers
  by hand.
---

# AERO - BreguetRangeEndurance

Use this skill for cruise range and endurance from the Breguet integrals in `aero-formulas`. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Jet fuel flow follows thrust. Weight-based thrust-specific fuel consumption \(c_t\) has SI unit \(1/\mathrm{s}\):

\[
R_{\mathrm{jet}} = \frac{V}{c_t}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}, \quad
E_{\mathrm{jet}} = \frac{1}{c_t}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

Propeller fuel flow follows shaft power. Weight-based power-specific fuel consumption \(c\) has SI unit \(1/\mathrm{m}\), and \(\eta\) is propeller efficiency:

\[
R_{\mathrm{prop}} = \frac{\eta}{c}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}, \quad
E_{\mathrm{prop}} = \frac{\eta}{c V}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

The program prints both the jet pair and the propeller pair. Cruise speed is required because jet range and propeller endurance use it. Propeller range does not depend on speed when \(c\) and \(\eta\) are constant.

## When to run

1. Use this skill when the user wants Breguet cruise range or endurance for a jet or a propeller airplane from \(L/D\), specific fuel consumption, start and end weight, and the other cruise quantities below.
2. Convert inputs to SI before the call. State the converted units in the reply. Do not invent \(L/D\), an SFC, a speed, an efficiency, or a weight.
3. `--ct` is weight-based TSFC in \(1/\mathrm{s}\). A value in \(1/\mathrm{hr}\) is divided by \(3600\) before the call. A mass-based TSFC in \(\mathrm{kg/(N\cdot s)}\) is multiplied by \(g_0 = 9.80665\,\mathrm{m/s}^2\) first. Say which conversion was used.
4. `--c` is weight-based power-specific fuel consumption in \(1/\mathrm{m}\). A mass-based value in \(\mathrm{kg/(W\cdot s)}\) is multiplied by \(g_0\) first. Historical \(\mathrm{lb/(hp\cdot hr)}\) must be converted to \(1/\mathrm{m}\) before the call. Do not pass a jet TSFC as `--c` or a propeller SFC as `--ct`.
5. `--wi` and `--wf` are cruise start and end weights in newtons, with start greater than end. A mass in kilograms is \(W = m \times 9.80665\) newtons. Do not treat the fuel mass alone as `--wf` unless the user already gave the empty-of-fuel cruise weight.
6. `--eta` is propeller efficiency on \(0 < \eta \le 1\). If the user wants only jet results and gave no efficiency, say the propeller block needs `--eta` and `--c`, and stop rather than inventing them. This program always requires the full flag set.
7. Climb, descent, reserves, and wind are omitted. If the user wants a full-mission fuel burn, say so after quoting the cruise result.

## Flags

Run:

```text
python "skills/AERO - BreguetRangeEndurance/breguet_range_endurance.py" --ld <L/D> --wi <N> --wf <N> --speed <m/s> --ct <1/s> --c <1/m> --eta <eta>
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--ld` | Lift-to-drag ratio \(L/D\) | dimensionless, \(> 0\) | Required |
| `--wi` | Weight at the start of cruise \(W_i\) | N, \(> W_f\) | Required |
| `--wf` | Weight at the end of cruise \(W_f\) | N, \(> 0\) | Required |
| `--speed` | True airspeed \(V\) | m/s, \(> 0\) | Required |
| `--ct` | Weight-based thrust-specific fuel consumption \(c_t\) | 1/s, \(> 0\) | Required |
| `--c` | Weight-based power-specific fuel consumption \(c\) | 1/m, \(> 0\) | Required |
| `--eta` | Propeller efficiency \(\eta\) | dimensionless, \(0 < \eta \le 1\) | Required |

A weight in pounds-force uses `1 lbf = 4.4482216152605 N`. A speed in knots uses `1 kt = 1852/3600 m/s`. A speed in feet per second uses `1 ft/s = 0.3048 m/s`. A bare weight is newtons. A bare speed is metres per second.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `LD`, `Wi_N`, `Wf_N`, `weight_ratio`, and `ln_Wi_over_Wf`.
3. Report `V_m_s`, `ct_1_s`, `c_1_m`, and `eta`. State that `ct_1_s` is the jet TSFC and `c_1_m` is the propeller power SFC.
4. Report `R_jet_m` and `E_jet_s`. State that jet endurance does not use speed, and that jet range is endurance times `V_m_s`.
5. Report `R_prop_m` and `E_prop_s`. State that propeller range does not use speed when `c_1_m` and `eta` are constant, and that propeller endurance is range divided by `V_m_s`.
6. Repeat that the result is cruise only: climb, descent, reserves, and wind are omitted.
7. If a required value is missing, or a value is outside the program limits, say so. Do not fill it in.
