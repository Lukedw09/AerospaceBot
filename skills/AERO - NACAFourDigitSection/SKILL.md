---
name: AERO - NACAFourDigitSection
description: >-
  Run the NACA four-digit section program and report its printed results and
  PNGs. Use when the user wants the mean line, upper and lower ordinates, a
  drawing, or measured section lift, moment, and drag of a four-digit NACA
  airfoil from a designation and a chord, with an optional angle of attack
  and optional chord Reynolds number. Coefficients come from NACA Report 824
  tunnel charts, not thin-airfoil theory. Do not redraw the figures or
  recompute the numbers by hand.
---

# AERO - NACAFourDigitSection

Use this skill for a NACA four-digit airfoil. Run the program once; quote its stdout and include its PNGs. Do not redraw the section or recompute the numbers by hand.

The designation is four digits: maximum camber in percent of chord, the station of that camber in tenths of chord, and maximum thickness in percent of chord. Geometry is `naca4_thickness` on the two-parabola mean line `naca4_camber_forward` / `naca4_camber_aft`, with thickness laid off normal to the mean line.

Section \(c_l\), \(c_d\), \(c_{m,c/4}\), and \(\alpha_{L0}\) are interpolated from digitized NACA Report 824 charts (Langley two-dimensional low-turbulence pressure tunnel, smooth surface). Each airfoil has measured curves near \(3\times10^6\), \(6\times10^6\), and \(9\times10^6\). Pass `--re` for the chord Reynolds number. An omitted `--re` uses the tabulated curve nearest \(6\times10^6\). A value between two tabulated Reynolds numbers is interpolated in \(\log\mathrm{Re}\). A value outside that set is an error; do not invent a polar. The table currently holds 0012, 2412, 2415, and 4412.

## When to run

1. Use this skill when the user wants NACA four-digit ordinates, a section drawing, the measured zero-lift angle, section lift, moment, or drag at an angle of attack, coefficients versus angle of attack, or a drag polar.
2. Convert the chord to metres and the angle of attack to radians before the call. State the converted units in the reply. Do not invent a designation, a chord, or an angle of attack.
3. A symmetric section is `00xx`. Do not run five-digit, 6-series, or modified four-digit sections with this program.
4. Omit `--alpha` when the user did not give an angle of attack. The coefficient and polar figures are still written.
5. If the program reports that the Report 824 chart is not in the table, or that the Reynolds number is outside the table, say so. Do not fall back to \(2\pi(\alpha-\alpha_{L0})\) or \(c_d=0\).
6. Convert a Reynolds number written as millions (`3 million`, `Re = 6e6`) to a plain number before `--re`. Do not invent a Reynolds number. Omit `--re` when the user did not give one.

## Flags

Run:

```text
python "skills/AERO - NACAFourDigitSection/naca_four_digit_section.py" --naca <digits> --chord <m> [--alpha <rad>] [--re <Re>] [--out <png>] [--out-coeff <png>] [--out-polar <png>] [--out-ordinates <txt>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--naca` | Four-digit designation, optionally prefixed by `NACA` | — | Required |
| `--chord` | Chord \(c\) | m, \(> 0\) | Required |
| `--alpha` | Geometric angle of attack of the chord | rad, \(\lvert\alpha\rvert < \pi/2\), and inside the measured chart | Optional |
| `--re` | Chord Reynolds number \(Vc/\nu\) | —, \(> 0\), inside the Report 824 set for that airfoil | Optional |
| `--out` | Section PNG path | — | Optional |
| `--out-coeff` | Coefficients-versus-angle PNG path | — | Optional |
| `--out-polar` | Drag-polar PNG path | — | Optional |
| `--out-ordinates` | Ordinate table path | — | Optional |

A chord in inches uses `1 in = 0.0254 m`. A chord in feet uses `1 ft = 0.3048 m`. An angle in degrees uses `alpha_rad = alpha_deg * pi/180`. A bare chord is metres.

Every successful run writes three PNGs and an ordinate table. The section title is `NACA four-digit section`. The coefficient title is `NACA four-digit coefficients`. The polar title is `NACA four-digit drag polar`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the section PNG at `graph:`. The red curve is the mean line. Include the coefficient PNG at `coefficients_graph:` and the polar PNG at `polar_graph:`. The coefficient figure is \(c_l\), \(c_{m,c/4}\), and \(c_d\) against geometric angle of attack in degrees over the measured chart. The dashed vertical line is \(\alpha_{L0}\). The polar is \(c_l\) against measured \(c_d\).
3. Report `designation`, `chord_m`, `m`, `p`, and `t`.
4. Report `Rle_m`. That is the leading-edge radius of the thickness form.
5. Report `data_source`, `Re`, `Re_table`, `surface`, `alpha_L0_rad`, and `alpha_L0_deg`. `Re` is the value used (tabulated or interpolated). `Re_table` lists the digitized Reynolds numbers.
6. Report `clmax`, `alpha_clmax_deg`, `cdmin`, and `cl_cdmin`.
7. When `--alpha` was passed, report `alpha_rad`, `alpha_deg`, `cl`, `cd`, and `cm`.
8. Report `ordinates`. That file lists mean-line and surface stations at the Report 460 table abscissae.
9. If the designation or chord is missing, or the designation is not four digits, say so. Do not fill them in.
