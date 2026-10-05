---
name: ASTRO - HyperbolicExcess
description: >-
  Run the hyperbolic-excess program and report its printed results and PNG.
  Use when the user wants hyperbolic excess speed, characteristic energy C3,
  the periapsis burn from a circular park onto a hyperbola, the turning angle,
  or the true anomaly of the asymptote. Pass --html when they want the 3D
  viewer. Do not redraw the orbit or recompute the numbers by hand.
---

# ASTRO - HyperbolicExcess

Use this skill for an impulsive periapsis burn from a circular park onto a planet-centered hyperbola. Run the program once; quote its stdout and include its PNG. Do not redraw the orbit or recompute the numbers by hand. Pass `--html` when the user wants the 3D viewer. Give `viewer:` as a markdown link when it is printed.

Assumptions (also printed by the program): spherical planet, inverse-square gravity, and no drag, thrust, or third body on the coast. The burn is impulsive and sits at periapsis of the hyperbola, which is also the circular-park radius. Hyperbolic excess is `hyperbolic_excess_from_axis`. Characteristic energy is `characteristic_energy`. The axis is `semimajor_from_characteristic_energy`. The energy radius is `energy_radius_from_excess`. Eccentricity is `hyperbolic_eccentricity_from_periapsis`. Periapsis speed is `vis_viva`. Circular speed is `circular_orbit_velocity`. The asymptote true anomaly is `hyperbola_asymptote_true_anomaly`. The turning angle is `hyperbola_turning_angle`. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). A radius is the distance from the center. An altitude is geometric height above \(R_0\).

`--rp` is the circular-park radius and the periapsis of the hyperbola. Pass exactly one energy input: `--vinf`, `--C3`, or `--rinf`. `--rinf` is the energy radius \(\lvert a\rvert=\mu/v_{\infty}^{2}\) implied by the excess speed; it is not a station on the path.

## When to run

1. A circular park and a hyperbolic excess speed: pass `--rp` and `--vinf`. Convert an altitude to a radius with \(r = R_0 + h\) before the call, using the Earth \(R_0\) unless the user gave another planetary radius. State that conversion in the reply.
2. A circular park and characteristic energy: pass `--rp` and `--C3`. \(C_3=v_{\infty}^{2}\).
3. A circular park and the energy radius implied by the excess speed: pass `--rp` and `--rinf`. Then \(v_{\infty}=\sqrt{\mu/r_{\infty}}\) and \(a=-r_{\infty}\).
4. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
5. Pass `--html` when the user wants the self-contained 3D HTML viewer, and `--open` only when they ask to open it.
6. Convert inputs to SI before the call (m, m/s, m²/s²). State the converted units in the reply. Do not invent a periapsis, an excess speed, a \(C_3\), or a planetary radius.

## Flags

Run:

```text
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --rp <m> --vinf <m/s> [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --rp <m> --C3 <m^2/s^2> [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --rp <m> --rinf <m> [--R0 <m>] [--out <png>] [--html] [--open]
```

Pass `--rp` and exactly one of `--vinf`, `--C3`, or `--rinf`.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--rp` | Periapsis of the hyperbola and radius of the circular park, from the center | m, \(\ge R_0\) | Required |
| `--vinf` | Hyperbolic excess speed | m/s, \(> 0\) | Exactly one of `--vinf`, `--C3`, `--rinf` |
| `--C3` | Characteristic energy \(v_{\infty}^{2}\) | m²/s², \(> 0\) | Exactly one of `--vinf`, `--C3`, `--rinf` |
| `--rinf` | Energy radius \(\lvert a\rvert=\mu/v_{\infty}^{2}\) implied by the excess speed | m, \(> 0\) | Exactly one of `--vinf`, `--C3`, `--rinf` |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional |
| `--html` | Write the 3D HTML viewer beside the PNG | — | Optional |
| `--open` | Open the HTML viewer in a browser | — | Optional |

A bare radius or altitude is metres. Kilometres use `1 km = 1000 m`. Statute miles use `1 mi = 1609.344 m`. Nautical miles use `1 nmi = 1852 m`. A bare speed is metres per second. If the user gives a park altitude, convert with \(r = R_0 + h\) and pass `--rp`. If the user gives geopotential altitude, convert to geometric altitude before adding \(R_0\), and say so.

Every successful run writes one PNG. The plot title is `Hyperbolic excess`. The camera of the optional HTML viewer looks down the orbit normal (elevation \(90^\circ\), azimuth \(-90^\circ\)). The periapsis burn is drawn as a \(\Delta v\) arrow. The HTML viewer is written only with `--html` or `--open`. It opens on the same orbit-normal camera; drag rotates, the scroll wheel zooms, and Reset camera returns to that view. Play starts on. The spacecraft parks on the circle, burns at periapsis while the path morphs from the circle onto the hyperbola, then coasts out toward the outgoing asymptote. `graph:` is the PNG. `viewer:` is the HTML when it is written.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. If `viewer:` is printed, give it as a markdown link to that HTML file. Do not draw a second figure.
3. Report `R0_m`, `R0_source`, `g0_m_s2`, and `mu_m3_s2`. `default` means the Earth radius from the circular-orbit formula.
4. Report `rp_m` and `h_park_m`. State that a radius is measured from the center and an altitude is height above \(R_0\).
5. Report `mode`. `vinf`, `C3`, or `rinf` is the energy input that was used.
6. Report `vinf_m_s`, `C3_m2_s2`, and `rinf_m`. `rinf_m` is \(\lvert a\rvert\), not a point on the trajectory.
7. Report `a_m` and `e`. The semi-major axis is negative.
8. Report `v_periapsis_m_s`, `v_circular_m_s`, and `v_escape_m_s`. Escape speed is the parabolic value at the same radius.
9. Report `dv_m_s` and `dv_sense`. The burn is prograde from the circular park onto the hyperbola.
10. Report `turn_rad` and `nu_inf_rad`. The turning angle is the heading change between the incoming and outgoing asymptotes. The true anomaly of the outgoing asymptote is \(\nu_{\infty}\); the incoming asymptote is \(-\nu_{\infty}\).
11. Report `energy_J_kg`. That is the specific mechanical energy of the hyperbola, \(v_{\infty}^{2}/2\).
12. Repeat `warning` when it is printed.
13. If the periapsis or the energy input is missing, say so. Do not fill it in.
