---
name: THERM - LumpedCapacitanceTransient
description: >-
  Run the lumped thermal-capacitance transient program and report its printed
  results and optional PNG. Use when the user wants temperature versus time
  under convection to a fixed ambient (Biot ≪ 1), heat transferred in that
  interval, or time to a target temperature, from mass, specific heat, surface
  area, convection coefficient, initial temperature, and ambient temperature.
  Optional conductivity and characteristic length print the Biot number. Do not
  redraw the plot or recompute the numbers by hand.
---

# THERM - LumpedCapacitanceTransient

Use this skill for the lumped thermal-capacitance (spatially uniform temperature) response of a solid cooled or heated by convection to a fixed ambient. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Thermal time constant is `lumped_thermal_time_constant`:

\[
\tau = \frac{m c}{h A}
\]

(Equivalent to \(\rho V c/(h A)\) when \(m=\rho V\).) Temperature versus time is `lumped_capacitance_temperature`:

\[
T(t)-T_{\infty}=(T_i-T_{\infty})\exp(-t/\tau)
\]

Time to a target temperature is `lumped_capacitance_time_to_temperature`, \(t=-\tau\ln\bigl((T-T_{\infty})/(T_i-T_{\infty})\bigr)\), only when \(T\) lies between \(T_i\) and \(T_{\infty}\) (inclusive of \(T_i\); \(T=T_{\infty}\) is only reached as \(t\to\infty\)). Heat transferred from the solid in time mode is `lumped_capacitance_heat_transferred`, \(Q=m c\bigl(T_i-T(t)\bigr)\).

Optional Biot number is `biot_number`, \(\mathrm{Bi}=h L_c/k\). The program prints \(\mathrm{Bi}\) only when both `--k` and `--char-length` are given. It warns when \(\mathrm{Bi}>0.1\) (not ≪ 1). Do not invent \(k\) or \(L_c\).

This skill does not resolve internal conduction gradients, radiation (unless the user already linearized it into an effective \(h\)), ablation, TPS stacks, or a heat-flux boundary unless the user already reduced flux to an effective \(h\).

## When to run

1. Use this skill when the user wants lumped-capacitance \(T(t)\), heat transferred \(Q\), time to a target temperature, or an optional Biot check for that transient.
2. Convert inputs to SI before the call (kg, J/(kg·K), m², W/(m²·K), K, s, W/(m·K), m). State the converted units in the reply. Do not invent mass, specific heat, area, \(h\), \(T_i\), \(T_{\infty}\), time, target temperature, \(k\), or \(L_c\).
3. Pass `--mass`, `--c`, `--area`, `--h`, `--ti`, and `--t-inf`. Pass exactly one of `--time` or `--target-temp`.
4. Pass both `--k` and `--char-length` only when the user gave conductivity and a characteristic length for Biot. Pass neither otherwise. Do not invent them.
5. Pass `--out` only when the user wants the PNG of temperature versus time. Do not invent a plot path when they did not ask for a figure.
6. Do not use this skill for distributed transient conduction / Heisler charts as the primary model, radiation-dominated cooling without an effective \(h\), or entry heating flux fields (use the other THERM skills for stagnation flux or ballistic peak load).

## Flags

Run:

```text
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --mass <kg> --c <J/(kg*K)> --area <m^2> --h <W/(m^2*K)> --ti <K> --t-inf <K> (--time <s> | --target-temp <K>) [--k <W/(m*K)> --char-length <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mass` | Mass \(m\) | kg, \(> 0\) | Required |
| `--c` | Specific heat \(c\) | J/(kg·K), \(> 0\) | Required |
| `--area` | Convecting surface area \(A\) | m², \(> 0\) | Required |
| `--h` | Convection coefficient \(h\) | W/(m²·K), \(> 0\) | Required |
| `--ti` | Initial temperature \(T_i\) | K | Required |
| `--t-inf` | Ambient temperature \(T_{\infty}\) | K | Required |
| `--time` | Elapsed time \(t\) (mode A) | s, \(\ge 0\) | Exactly one of `--time` or `--target-temp` |
| `--target-temp` | Target temperature \(T\) (mode B) | K | Exactly one of `--time` or `--target-temp` |
| `--k` | Thermal conductivity for Biot | W/(m·K), \(> 0\) | Optional; with `--char-length` |
| `--char-length` | Characteristic length \(L_c\) for Biot (often \(V/A\)) | m, \(> 0\) | Optional; with `--k` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Mass in grams uses `1 g = 0.001 kg`. Specific heat in kJ/(kg·K) uses `1 kJ/(kg·K) = 1000 J/(kg·K)`. Area in cm² uses `1 cm² = 1e-4 m²`. Length in mm uses `1 mm = 0.001 m`. Temperature in °C uses \(T_{\mathrm{K}}=T_{\mathrm{°C}}+273.15\). Do not invent missing values.

When `--out` is passed, the program writes one PNG. The plot title is `Lumped capacitance transient`. The curve is \(T(t)\) from \(t=0\) to about \(4\tau\) (or through the operating time if longer). The square is the operating point (mode A time or mode B target). A dashed line is \(T_{\infty}\). `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `tau_s`, `Bi` (`none` when \(k\) and \(L_c\) were omitted), and `mode`.
4. Mode A (`time`): report `t_s`, `T_K`, and `Q_J`.
5. Mode B (`target_temp`): report `T_K` and `t_s`. Do not invent \(Q\).
6. Report `k_W_m_K` and `Lc_m` when they are printed. Include the printed `warning` when \(\mathrm{Bi}>0.1\).
7. If mass, specific heat, area, \(h\), \(T_i\), \(T_{\infty}\), or exactly one of time / target temperature is missing, say so. Do not fill them in.
