---
name: AERO - WingGeometry
description: >-
  Run the trapezoidal wing-geometry program and report its printed results
  and PNG. Use when the user wants wing area, aspect ratio, taper ratio,
  mean aerodynamic chord, or the spanwise station of that chord from span,
  root chord, and tip chord, with an optional sweep angle. Do not redraw
  the planform or recompute the numbers by hand.
---

# AERO - WingGeometry

Use this skill for a straight-tapered wing. Run the program once; quote its stdout and include its PNG. Do not redraw the planform or recompute the numbers by hand.

Chords are streamwise. The root chord is \(c_r\) and the tip chord is \(c_t\). Span \(b\) is tip to tip.

\[
S = b\frac{c_r + c_t}{2}, \quad
AR = \frac{b^{2}}{S}, \quad
\lambda = \frac{c_t}{c_r}
\]

\[
\bar{c} = \frac{2}{3} c_r \frac{1 + \lambda + \lambda^{2}}{1 + \lambda}, \quad
y_{\bar{c}} = \frac{b}{6}\frac{1 + 2\lambda}{1 + \lambda}
\]

\(y_{\bar{c}}\) is the distance from the centerline to the mean aerodynamic chord. The other side is the mirror image.

Sweep is the angle from the spanwise axis toward the rear. Positive sweep puts the tip aft of the root. The program stores that angle on the chord fraction `--sweep-at`: \(0\) is the leading edge, \(0.25\) is the quarter chord, and \(1\) is the trailing edge. If the user gives a sweep and does not name the chord line, pass `--sweep` without `--sweep-at`. The program then uses the quarter chord and prints `sweep_at_source: default-quarter-chord`. Say that in the reply. If the user gives no sweep, omit `--sweep`. The leading edge is drawn unswept.

\(x\) on the sketch is positive aft of the root leading edge. \(y\) is positive to starboard. The figure is the plan view, with the leading edge toward the top of the page.

## When to run

1. Use this skill when the user wants wing area, aspect ratio, taper, mean aerodynamic chord, or the spanwise station of that chord for a straight-tapered wing.
2. Convert lengths to metres and the sweep to radians before the call. State the converted units in the reply. Do not invent a span, a chord, or a sweep.
3. A pointed tip is `--tip 0`. A tip chord larger than the root is allowed.
4. Pass `--sweep-at 0` only when the user says the sweep is the leading edge. Pass `--sweep-at 1` only when they say it is the trailing edge. Pass `--sweep-at 0.25` when they say quarter chord. Do not convert one sweep into another before the call.
5. Interactive lab offer: before running this program for a new airfoil, wing-geometry, or finite-wing lift-curve design or sizing thread, ask once whether the user wants `AERO - WingAirfoilDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/AERO - WingGeometry/wing_geometry.py" --span <m> --root <m> --tip <m> [--sweep <rad>] [--sweep-at <0 to 1>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--span` | Span \(b\), tip to tip | m, \(> 0\) | Required |
| `--root` | Streamwise root chord \(c_r\) | m, \(> 0\) | Required |
| `--tip` | Streamwise tip chord \(c_t\) | m, \(\ge 0\) | Required |
| `--sweep` | Sweep of the line named by `--sweep-at` | rad, strictly between \(-\pi/2\) and \(\pi/2\) | Optional |
| `--sweep-at` | Chord fraction of `--sweep` | dimensionless, 0 to 1 | Optional. Requires `--sweep`. Omitted value is 0.25 |
| `--out` | PNG path | — | Optional |

A length in feet uses `1 ft = 0.3048 m`. A length in inches uses `1 in = 0.0254 m`. A sweep in degrees uses `sweep_rad = sweep_deg * pi/180`. A bare span or chord is metres.

Every successful run writes one PNG. The plot title is `Wing geometry`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. The plan view has \(x\) aft and \(y\) starboard, with the leading edge toward the top. The red chords are the mean aerodynamic chord on both sides. The dotted line is the quarter chord.
3. Report `span_m`, `root_chord_m`, and `tip_chord_m`.
4. Report `area_m2`, `AR`, `taper`, `mac_m`, and `y_mac_m`. \(y_{\bar{c}}\) is measured from the centerline. The port station is the negative of that value.
5. Report `sweep_le_source`. `omitted` means the leading edge was drawn unswept. `given` means a sweep was passed.
6. When a sweep was passed, report `sweep_rad`, `sweep_deg`, `sweep_at`, and `sweep_at_source`. `default-quarter-chord` means the angle was applied at \(n = 1/4\) because no station was given. `given` means `--sweep-at` was passed.
7. Report `sweep_le_deg`, `sweep_c4_deg`, and `sweep_te_deg`. Those are the leading-edge, quarter-chord, and trailing-edge sweeps of the drawn wing.
8. Report `x_le_mac_m`. That is how far aft of the root leading edge the starboard mean chord starts.
9. If the span, either chord, or a required sweep station is missing, or a value is outside the program limits, say so. Do not fill it in.
