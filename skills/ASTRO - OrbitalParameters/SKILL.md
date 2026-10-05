---
name: ASTRO - OrbitalParameters
description: >-
  Run the orbital-parameters program and report its printed results, PNG, and
  HTML viewer. Use when the user wants classical orbital elements, a NORAD
  two-line element set, the inertial state, specific energy, angular momentum,
  periapsis, apoapsis, or the period of a Keplerian conic, or a 3D view of that
  orbit. Do not redraw the orbit,
  recompute the numbers, or animate the spacecraft by hand.
---

# ASTRO - OrbitalParameters

Use this skill for one Keplerian conic about a planet: classical elements, a NORAD two-line element set, or the inertial state. Run the program once; quote its stdout, include its PNG, and give the HTML path printed as `viewer:`. Do not redraw the orbit, recompute the numbers, or animate the spacecraft by hand.

Assumptions (also printed by the program): inverse-square gravity and no drag, thrust, or third body. Planetary flattening is drawn only and does not enter \(\mu\) or the epoch state. Optional first-order \(J_2\) is off unless `--j2` is passed. Then the HTML viewer advances \(\Omega\) and \(\omega\) with `j2_nodal_rate` and `j2_apsidal_rate` from `ASTRO - J2SecularRates`. Semi-major axis, eccentricity, and inclination have no secular \(J_2\) rate. Drag, third body, higher zonals, and the \(J_2\) mean-motion correction are omitted. \(J_2\) is ellipse-only. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\) and a visual flattening \(1/298.257\). Any other \(R_0\) is drawn as a sphere unless `--flattening` is set. A bare `--j2` uses Earth \(J_2 = 1.08228\times 10^{-3}\) (GSFC, March 1986, NASA RP-1204) and \(R_E =\) WGS 84 \(6378137\,\mathrm{m}\). Another planet needs `--j2` and `--R0`, and `--ae` when \(R_E\) is not that \(R_0\). The frame is planet-centered inertial: \(+Z\) is the polar axis, the \(XY\) plane is the equator, and \(\Omega\) is measured from \(+X\) to the ascending node.

An ellipse has \(a > 0\) and \(0 \le e < 1\). A hyperbola has \(a < 0\) and \(e > 1\). A parabola has no finite semi-major axis; pass the inertial state. Period and apoapsis are printed only for an ellipse. On an ellipse the program prints both the true anomaly and the mean anomaly. `--M` is rejected off an ellipse.

A `--tle` is a NORAD two-line element set, used as a Keplerian ellipse. Pass the two 69-character lines. An optional name line may come first. Line-2 angles stay in degrees; the program converts them. Semi-major axis is the inverse of `mean_motion` from the published mean motion, in revolutions per 86400 s, and this program's \(\mu\). BSTAR, the mean-motion derivatives, and SGP4 are not applied. The epoch is printed and does not move the spacecraft. A bad checksum is rejected.

Singular orbits use the ELCONO conventions. \(\Omega = 0\) when the orbit is equatorial (\(i = 0\) or \(i = \pi\)). \(\omega = 0\) when \(e < 10^{-7}\), and on that circle the mean anomaly equals the argument of latitude. A supplied \(\omega\) on a circle is absorbed into the anomaly. On an equator, a supplied \(\Omega\) is absorbed into the argument of periapsis.

## When to run

1. Classical elements: pass `--a`, `--e`, `--i`, `--raan`, `--aop`, and exactly one of `--nu` or `--M`.
2. Inertial state: pass `--rx`, `--ry`, `--rz`, `--vx`, `--vy`, and `--vz`.
3. NORAD TLE: pass `--tle` with line 1 and line 2. A name line may be the first argument. Do not convert those angles to radians. Do not also pass elements or a state.
4. Pass one mode. Do not combine a TLE, elements, and a state.
5. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
6. Pass `--flattening` only when the user wants a visual polar squash other than the default. It does not change the numbers.
7. Pass `--j2` only when the user wants first-order \(J_2\) secular rates in the HTML viewer. A bare `--j2` is Earth. For another planet pass `--j2` with that planet's \(J_2\) and `--R0`. Pass `--ae` only when \(R_E\) in the \(J_2\) term is not the Earth WGS 84 default and not `--R0`. Do not pass `--j2` on a hyperbola or parabola. `--ae` without `--j2` is an error.
8. Pass `--elev` and `--azim` when the user wants another initial camera angle. The PNG is the still at that angle. The HTML viewer opens on the same angle and can be rotated without another run. Pass `--open` when the user wants that file opened in a browser.
9. Convert classical elements and a state to SI and radians before the call. Leave a TLE in its published lines. State the converted units in the reply. Do not invent a missing element, a missing state component, a missing TLE line, or a planetary radius.

## Flags

Run:

```text
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --a <m> --e <e> --i <rad> --raan <rad> --aop <rad> (--nu <rad> | --M <rad>) [--R0 <m>] [--flattening <f>] [--j2 [J2]] [--ae <m>] [--elev <deg>] [--azim <deg>] [--out <png>] [--open]
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --rx <m> --ry <m> --rz <m> --vx <m/s> --vy <m/s> --vz <m/s> [--R0 <m>] [--flattening <f>] [--j2 [J2]] [--ae <m>] [--elev <deg>] [--azim <deg>] [--out <png>] [--open]
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --tle "<line 1>" "<line 2>" [--R0 <m>] [--flattening <f>] [--j2 [J2]] [--ae <m>] [--elev <deg>] [--azim <deg>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Semi-major axis. Positive on an ellipse, negative on a hyperbola. | m | Elements mode |
| `--e` | Eccentricity | dimensionless, \(\ge 0\) | Elements mode |
| `--i` | Inclination | rad, \(0 \le i \le \pi\) | Elements mode |
| `--raan` | Longitude of the ascending node, \(\Omega\) | rad | Elements mode |
| `--aop` | Argument of periapsis, \(\omega\) | rad | Elements mode |
| `--nu` | True anomaly | rad | Elements mode, or `--M` |
| `--M` | Mean anomaly. Ellipse only. | rad | Elements mode, or `--nu` |
| `--rx`, `--ry`, `--rz` | Inertial position | m | State mode, all three |
| `--vx`, `--vy`, `--vz` | Inertial velocity | m/s | State mode, all three |
| `--tle` | NORAD two-line element set. Two 69-character lines. An optional name line may be first. | — | TLE mode |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--flattening` | Visual polar flattening | dimensionless, \(0 \le f < 1\) | Optional |
| `--j2` | Optional first-order \(J_2\). Bare `--j2` is Earth GSFC. | dimensionless, \(> 0\) | Optional. Off if omitted |
| `--ae` | Equatorial radius in the \(J_2\) term | m, \(> 0\) | Optional. Needs `--j2`. Earth default WGS 84; else `--R0` |
| `--elev` | Camera elevation | deg | Optional. Default \(20\) |
| `--azim` | Camera azimuth | deg | Optional. Default \(35\) |
| `--out` | PNG path. The HTML viewer is the same path with a `.html` suffix. | — | Optional |
| `--open` | Open the HTML viewer in a browser. | — | Optional |

A negative semi-major axis may be written `--a=-2e7` or `--a -2e7`. A bare length is metres. Kilometres use `1 km = 1000 m`. Statute miles use `1 mi = 1609.344 m`. Nautical miles use `1 nmi = 1852 m`. Element angles and `--nu` and `--M` are radians. Degrees use \(\pi/180\). `--elev` and `--azim` are degrees. A TLE line is passed unchanged, including its degree fields and checksum.

Every successful run writes one PNG and one HTML file. `graph:` is the PNG. `viewer:` is the HTML. The plot title on both is `ASTRO - OrbitalParameters`. Axes are kilometres. The planet is a translucent spheroid. The inclination sector has its vertex at the planet center. One edge lies in the equatorial plane and the other is the radius, so that edge ends on the spacecraft. The PNG draws that sector at the epoch position. In the HTML viewer the sector follows the spacecraft. The ascending node, periapsis, and, on an ellipse, apoapsis are points on the orbit. The far side of the orbit is dashed. The PNG is the epoch state. The HTML file is self-contained and opens offline. Drag rotates the camera, the scroll wheel zooms, and Reset camera returns to `--elev`, `--azim`, and roll \(0^\circ\). At elev \(= 90^\circ\) the view looks down \(+Z\); screen-right is the azimuth turned \(90^\circ\) about that axis, which is the matplotlib limit a Z-up camera leaves undefined on the pole. Play starts on. The spacecraft begins at the epoch state and then moves on the conic: an ellipse advances mean anomaly and loops each period in 8 s of wall time; a hyperbola or parabola ping-pongs along the drawn arc. With `--j2` on an ellipse, the HTML draws one faded ellipse that follows \(\Omega\) and \(\omega\). The spacecraft leaves a trail in the orbit colour that is opaque at the satellite and transparent by three-quarters of an orbit, with no leftover from earlier revolutions. The PNG remains the epoch state. Reset to epoch returns the craft, orbit, and trail to the PNG state. Pause stops the motion. Do not recompute that motion by hand. Pass `--open` only when the user wants the HTML opened in a browser. Give `viewer:` as a local file path the user can open.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG image. `graph:` is the file path.
3. Give `viewer:` as a markdown link to that HTML file. Keep the printed path as the link target so it can be opened and copied. Do not draw a second figure. Pass `--open` only when the user asks to open the viewer. That flag launches the HTML in a browser after both files are written and does not change the numbers.
4. Report `mode`. `elements` started from classical elements. `state` started from position and velocity. `tle` started from a NORAD two-line element set.
5. When `mode` is `tle`, also report `tle_name` if it is printed, plus `tle_catalog`, `tle_designator`, `tle_epoch_year`, `tle_epoch_day`, `tle_n_rev_day`, `tle_bstar`, and `tle_note`.
6. Report `R0_m`, `R0_source`, `g0_m_s2`, `mu_m3_s2`, `flattening`, `ae_m`, `ae_source`, `J2`, `J2_source`, `Omega_dot_rad_s`, and `omega_dot_rad_s`. `default` on `R0_source` means the Earth radius. Flattening is visual only. `J2_source: off` means Keplerian viewer motion.
7. Report `conic`: `ellipse`, `parabola`, or `hyperbola`.
8. Report `a_m` when it is printed. Report `a: none` for a parabola.
9. Report `e`, `i_rad`, `Omega_rad`, `omega_rad`, and `nu_rad`. Inclination is in \([0, \pi]\). \(\Omega\) and \(\omega\) are in \([0, 2\pi)\). The true anomaly is in \((-\pi, \pi]\).
10. Report `M_rad` on an ellipse. Report `M: none` otherwise. On an ellipse, `M_rad` is in \((-\pi, \pi]\).
11. Report `p_m`, `energy_J_kg`, `h_m2_s`, `hx_m2_s`, `hy_m2_s`, and `hz_m2_s`.
12. Report `rp_m`. Report `ra_m` on an ellipse. Report `apoapsis: none` otherwise.
13. Report `period_s` on an ellipse. Report `period: none` otherwise.
14. Report `rx_m`, `ry_m`, `rz_m`, `vx_m_s`, `vy_m_s`, and `vz_m_s`.
15. Report `elev_deg` and `azim_deg`.
16. Repeat `warning` when it is printed. A periapsis inside \(R_0\) does not change the conic.
17. If an element, an anomaly, a TLE line, or a state component is missing, say so. Do not fill it in.
