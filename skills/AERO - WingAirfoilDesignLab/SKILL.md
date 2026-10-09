---
name: AERO - WingAirfoilDesignLab
description: >-
  Bake an interactive 2D wing and airfoil design page. Use only when the
  user explicitly asks for this lab, the interactive HTML designer, or a
  live slider view of a NACA section, planform, and wing lift curve. Do not
  run it just because an airfoil or wing is being sized.
---

# AERO - WingAirfoilDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `AERO - WingAirfoilDesignLab`, or they clearly ask for the interactive HTML page, the live wing and airfoil designer, or a design view with sliders. Do not run it because a wing or airfoil conversation is underway. Do not run it from another aero skill unless they explicitly said yes to that offer.

The program writes a PNG of the opening planform and lift line, and a self-contained HTML page. The page recomputes the section, planform, and coefficients in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. After they change the page, use the export block with `AERO - NACAFourDigitSection`, `AERO - WingGeometry`, and `AERO - FiniteWingLiftCurve` if they want those programs quoted. This lab does not replace those programs.

If the designation is 0012, 2412, 2415, or 4412, section \(c_l\), \(\alpha_{L0}\), \(c_{l,\max}\), and profile \(c_d\) come from the NACA Report 824 chart at the selected Reynolds number. The section slope \(a_0\) is the measured \(c_l\) slope from \(\alpha_{L0}\) through the linear portion of that chart. Any other four-digit section is drawn from the NACA geometry formulas, with \(a_0 = 2\pi\), \(\alpha_{L0}\) from `naca4_zero_lift_angle`, profile drag from the zero-lift-drag input, and \(C_{L,\max}\) from that input.

Planform sweep, on the chord line the user names, sets \(a_{0,\mathrm{eff}} = a_0\cos\Lambda\). That effective slope is the \(a_0\) passed to `wing_lift_curve_slope`. Induced drag at a given \(C_L\) is \(C_L^2/(\pi\,AR\,e)\). Sweep changes induced drag only by changing \(C_L(\alpha)\). The cosine factor is not a catalogue identity. Say that in the reply. Wing \(C_{L,\max}\) is the section \(C_{L,\max}\) with no extra finite-wing stall credit.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before the call (m, rad). State the converted units in the reply. Sweep and the marked angle of attack are radians on the CLI; the page shows degrees.
3. Pass only flags the user supplied. Omitted flags keep the program defaults: NACA 2412, Reynolds number omitted so the chart nearest \(6\times10^6\) is used, span \(10\,\mathrm{m}\), root chord \(1.5\,\mathrm{m}\), tip chord \(1.0\,\mathrm{m}\), unswept, \(e = 1\), marked angle \(4^\circ\), and, on the thin-airfoil path only, \(C_{D0} = 0.008\) and \(C_{L,\max} = 1.2\).
4. Pass `--re` only when they give a Reynolds number and the section has a Report 824 chart. A value outside that airfoil's chart span is an error. Do not extrapolate.
5. Pass `--sweep-at` only together with `--sweep`. Omit both when they give no sweep.
6. Pass `--cd0` and `--clmax` only when the section has no Report 824 chart, or when they set those theory-path inputs. On a chart section the program ignores them.
7. Pass `--open` only when they ask to open the HTML file.
8. In the reply, state every assumption the user did not supply. Name the coefficient source (`report824` or `thin_airfoil`). State that \(a_{0,\mathrm{eff}} = a_0\cos\Lambda\) is not a catalogue identity. On the thin-airfoil path, state the zero-lift drag and \(C_{L,\max}\) that were assumed when they did not set them.

## Flags

Run:

```text
python "skills/AERO - WingAirfoilDesignLab/wing_airfoil_lab.py" [--naca <digits>] [--re <Re>] [--span <m>] [--root <m>] [--tip <m>] [--sweep <rad>] [--sweep-at <0 to 1>] [--e <e>] [--cd0 <CD0>] [--clmax <CLmax>] [--alpha <rad>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--naca` | Four-digit designation | — | Optional |
| `--re` | Chord Reynolds number | —, \(> 0\), inside the chart span when a chart exists | Optional |
| `--span` | Span, tip to tip | m, \(> 0\) | Optional |
| `--root` | Root chord | m, \(> 0\) | Optional |
| `--tip` | Tip chord | m, \(\ge 0\) | Optional |
| `--sweep` | Sweep of the line named by `--sweep-at` | rad | Optional |
| `--sweep-at` | Chord fraction of `--sweep` | dimensionless, 0 to 1 | Optional |
| `--e` | Span efficiency | dimensionless, \(0 < e \le 1\) | Optional |
| `--cd0` | Thin-airfoil zero-lift drag | dimensionless, \(\ge 0\) | Optional |
| `--clmax` | Thin-airfoil section \(C_{L,\max}\) | dimensionless, \(> 0\) | Optional |
| `--alpha` | Marked angle of attack | rad | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

A length in feet uses `1 ft = 0.3048 m`. A length in inches uses `1 in = 0.0254 m`. An angle in degrees uses `angle_rad = angle_deg * pi/180`. A bare length is metres.

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. In the same reply, state every assumption the user did not supply. Name `data_source`. State that \(a_{0,\mathrm{eff}} = a_0\cos\Lambda\) is applied before `wing_lift_curve_slope` and is not a catalogue identity. Induced drag at a given \(C_L\) stays \(C_L^2/(\pi\,AR\,e)\).
3. On `thin_airfoil`, state \(C_{D0}\) and \(C_{L,\max}\) (`CD0` and the theory \(C_{L,\max}\)). Unless the user set them, those defaults are \(0.008\) and \(1.2\). On `report824`, say the chart supplied \(\alpha_{L0}\), \(c_{l,\max}\), the measured slope, and profile \(c_d\), and that the zero-lift-drag and \(C_{L,\max}\) inputs were not used.
4. Include the PNG. Give `viewer:` as a markdown link.
5. Tell them the page is where to change the designation, Reynolds number, span, chords, sweep, span efficiency, and the marked angle, and that the planform, section, and curves update immediately.
6. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.
