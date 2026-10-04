---
name: ASTRO - PlaneChangeImpulse
description: >-
  Run the plane-change impulse program and report its printed results, PNG, and
  HTML viewer. Use when the user wants the impulsive delta-v of a pure
  inclination change at the ascending or descending node of one Keplerian
  conic. Do not redraw the orbits, recompute the burn, or animate the
  spacecraft by hand.
---

# ASTRO - PlaneChangeImpulse

Use this skill for one impulsive pure inclination change on a Keplerian conic. The burn is at a node. Semi-major axis, eccentricity, node, and argument of periapsis stay the same. Run the program once; quote its stdout, include its PNG, and give the HTML path printed as `viewer:`. Do not redraw the orbits, recompute the burn, or animate the spacecraft by hand.

Assumptions (also printed by the program): spherical inverse-square gravity and no drag, coast thrust, or third body. The turn is impulsive and equal-speed. Radius is `conic_radius`. Speed is `vis_viva`. The impulse is `plane_change_impulse`, \(\Delta v = 2 v \sin(\Delta i / 2)\). This is not a combined plane and radius change. Planetary flattening is drawn only and does not enter \(\mu\). \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\) and a visual flattening \(1/298.257\). Any other \(R_0\) is drawn as a sphere unless `--flattening` is set. The frame matches OrbitalParameters: \(+Z\) is the polar axis, the \(XY\) plane is the equator, and \(\Omega\) is measured from \(+X\).

The ascending node is \(\nu = -\omega\). The descending node is \(\nu = \pi - \omega\). An ellipse has both nodes. On a hyperbola or parabola a node is printed only when that true anomaly lies on the drawn branch; otherwise its radius, speed, and impulse are `none`. From an equatorial orbit with the ELCONO node \(\Omega = 0\), the burns sit on \(\pm X\).

`--nu` or `--M` fixes the printed epoch state. It is not the burn. The PNG and the HTML reset state put the spacecraft at the selected node.

## When to run

1. Classical elements: pass `--a`, `--e`, `--i`, `--raan`, `--aop`, exactly one of `--nu` or `--M`, and `--di`.
2. Inertial state: pass `--rx`, `--ry`, `--rz`, `--vx`, `--vy`, `--vz`, and `--di`.
3. Pass one orbit mode. Do not pass elements and a state together.
4. Pass `--di` in radians. \(i_f = i + \Delta i\) must stay in \([0, \pi]\).
5. Pass `--burn an` or `--burn dn` when the user names the node. Omit it to burn at the slower node. The program still prints both nodes.
6. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
7. Pass `--flattening` only when the user wants a visual polar squash other than the default. It does not change the numbers.
8. Pass `--elev` and `--azim` when the user wants another initial camera angle. The PNG is the still at that angle. The HTML viewer opens on the same angle. Pass `--open` when the user wants that file opened in a browser.
9. Convert inputs to SI and radians before the call. State the converted units in the reply. Do not invent a missing element, a missing state component, a missing \(\Delta i\), or a planetary radius.

## Flags

Run:

```text
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --a <m> --e <e> --i <rad> --raan <rad> --aop <rad> (--nu <rad> | --M <rad>) --di <rad> [--burn an|dn] [--R0 <m>] [--flattening <f>] [--elev <deg>] [--azim <deg>] [--out <png>] [--open]
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --rx <m> --ry <m> --rz <m> --vx <m/s> --vy <m/s> --vz <m/s> --di <rad> [--burn an|dn] [--R0 <m>] [--flattening <f>] [--elev <deg>] [--azim <deg>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Semi-major axis. Positive on an ellipse, negative on a hyperbola. | m | Elements mode |
| `--e` | Eccentricity | dimensionless, \(\ge 0\) | Elements mode |
| `--i` | Initial inclination | rad, \(0 \le i \le \pi\) | Elements mode |
| `--raan` | Longitude of the ascending node, \(\Omega\) | rad | Elements mode |
| `--aop` | Argument of periapsis, \(\omega\) | rad | Elements mode |
| `--nu` | True anomaly of the printed epoch. Not the burn. | rad | Elements mode, or `--M` |
| `--M` | Mean anomaly of the printed epoch. Ellipse only. Not the burn. | rad | Elements mode, or `--nu` |
| `--rx`, `--ry`, `--rz` | Inertial position of the printed epoch | m | State mode, all three |
| `--vx`, `--vy`, `--vz` | Inertial velocity of the printed epoch | m/s | State mode, all three |
| `--di` | Inclination change. \(i_f = i + \Delta i\) stays in \([0, \pi]\). | rad | Yes |
| `--burn` | Node drawn as the maneuver. `an` or `dn`. Default is the slower node. | — | Optional |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--flattening` | Visual polar flattening | dimensionless, \(0 \le f < 1\) | Optional |
| `--elev` | Camera elevation | deg | Optional. Default \(20\) |
| `--azim` | Camera azimuth | deg | Optional. Default \(35\) |
| `--out` | PNG path. The HTML viewer is the same path with a `.html` suffix. | — | Optional |
| `--open` | Open the HTML viewer in a browser. | — | Optional |

A negative semi-major axis may be written `--a=-2e7` or `--a -2e7`. A negative inclination change may be written `--di=-0.2` or `--di -0.2`. A bare length is metres. Kilometres use `1 km = 1000 m`. Statute miles use `1 mi = 1609.344 m`. Nautical miles use `1 nmi = 1852 m`. Element angles, `--nu`, `--M`, and `--di` are radians. Degrees use \(\pi/180\). `--elev` and `--azim` are degrees.

Every successful run writes one PNG and one HTML file. `graph:` is the PNG. `viewer:` is the HTML. The plot title on both is `ASTRO - PlaneChangeImpulse`. Axes are kilometres. The planet is a translucent spheroid. Both orbits are drawn, the far side dashed. The line of nodes and both node markers are drawn when those nodes lie on the branch. The spacecraft and the \(\Delta v\) arrow sit at the selected node. The PNG is that burn still. The HTML file is self-contained and opens offline. Drag rotates the camera, the scroll wheel zooms, and Reset camera returns to `--elev`, `--azim`, and roll \(0^\circ\). Play starts on. The spacecraft flies one revolution on the initial orbit, easing to a stop at the selected node. The inclination then hinges about the line of nodes from \(i\) to \(i_f\). It eases away on the final conic and flies four revolutions there, then the sequence repeats. The orbit the spacecraft is on is solid; the other is faded. The orange arrow fixed at the burn is the plane-change impulse. The blue arrow on the spacecraft is its velocity. Cruise speed is one revolution in 8 s of wall time. Reset to epoch restarts that sequence at the node on the initial orbit. Do not recompute that motion by hand. Pass `--open` only when the user wants the HTML opened in a browser. Give `viewer:` as a local file path the user can open.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG image. `graph:` is the file path.
3. Give `viewer:` as a markdown link to that HTML file. Keep the printed path as the link target so it can be opened and copied. Do not draw a second figure. Pass `--open` only when the user asks to open the viewer.
4. Report `mode`. `elements` started from classical elements. `state` started from position and velocity.
5. Report `R0_m`, `R0_source`, `g0_m_s2`, `mu_m3_s2`, and `flattening`. `default` means the Earth radius. Flattening is visual only.
6. Report `conic`: `ellipse`, `parabola`, or `hyperbola`.
7. Report `a_m` when it is printed. Report `a: none` for a parabola.
8. Report `e`, `i_rad`, `Omega_rad`, `omega_rad`, and `nu_rad` for the printed epoch. Report `di_rad`, `i_initial_rad`, and `i_final_rad`.
9. Report `M_rad` on an ellipse. Report `M: none` otherwise.
10. Report `p_m`, `energy_J_kg`, `h_m2_s`, `hx_m2_s`, `hy_m2_s`, and `hz_m2_s`.
11. Report `rp_m`. Report `ra_m` on an ellipse. Report `apoapsis: none` otherwise.
12. Report `period_s` on an ellipse. Report `period: none` otherwise.
13. Report `rx_m`, `ry_m`, `rz_m`, `vx_m_s`, `vy_m_s`, and `vz_m_s` for the printed epoch, not the burn.
14. Report `nu_an_rad`, `nu_dn_rad`, `r_an_m`, `r_dn_m`, `v_an_m_s`, `v_dn_m_s`, `dv_an_m_s`, and `dv_dn_m_s`. A node off the drawn branch has `none` for its radius, speed, and impulse.
15. Report `burn`: `an` or `dn`.
16. Report `elev_deg` and `azim_deg`.
17. Repeat `warning` when it is printed. A periapsis inside \(R_0\) does not change the conic.
18. If an element, an anomaly, a state component, or \(\Delta i\) is missing, say so. Do not fill it in.
