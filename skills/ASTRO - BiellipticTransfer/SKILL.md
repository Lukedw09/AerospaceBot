---
name: ASTRO - BiellipticTransfer
description: >-
  Run the bi-elliptic-transfer program and report its printed results and PNG.
  Use when the user wants the three-burn delta-v, time of flight, or radius
  ratio for a coplanar transfer between two circular orbits, given radii,
  classical elements, NORAD two-line element sets, or inertial states, plus the intermediate apoapsis.
  Pass --html when they want the 3D viewer. Do not redraw the orbit or
  recompute the numbers by hand.
---

# ASTRO - BiellipticTransfer

Use this skill for an impulsive coplanar bi-elliptic transfer between two circular orbits. Run the program once; quote its stdout and include its PNG. Do not redraw the orbit or recompute the numbers by hand. Pass `--html` when the user wants the 3D viewer. Give `viewer:` as a markdown link when it is printed.

Assumptions (also printed by the program): spherical planet, inverse-square gravity, and no drag, thrust, or third body on the coasts. The three burns are impulsive and coplanar. The first ellipse has periapsis at the departure circular radius and apoapsis at `--rb`. The second ellipse has apoapsis at `--rb` and periapsis at the arrival circular radius. Apsidal speeds are `apsis_speed` (`vis_viva` with `semimajor_from_apsides`). Circular speed is `circular_orbit_velocity`. Each coast is `elliptic_half_period`. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). A radius is the distance from the center. An altitude is geometric height above \(R_0\).

`--r1` and `--r2` are the departure and arrival circular radii. `--rb` is the common apoapsis and must be at least the larger of those radii. When `--rb` equals the larger radius, the unused ellipse degenerates to a circle and the burns recover the Hohmann transfer.

Classical elements or an inertial state fix each circular radius as the epoch radial distance. The burns stay coplanar; a plane change is omitted. A non-circular ellipse still contributes only that epoch radius.

## When to run

1. Two circular radii: pass `--r1`, `--r2`, and `--rb`. Convert altitudes to radii with \(r = R_0 + h\) before the call, using the Earth \(R_0\) unless the user gave another planetary radius. State that conversion in the reply.
2. Two sets of classical elements: pass `--a1 --e1 --i1 --raan1 --aop1` and one of `--nu1` or `--M1`, the matching `--a2 ...` set, and `--rb`.
3. Two inertial states: pass `--rx1 --ry1 --rz1 --vx1 --vy1 --vz1`, the matching `--rx2 ...` set, and `--rb`.
4. Two NORAD TLEs: pass `--tle1` with the departure lines and `--tle2` with the arrival lines, plus `--rb`. A name line may be the first argument of each. Do not convert those angles to radians. Each TLE still contributes only its epoch radius.
5. Pass one input family for the two orbits. Do not mix radii, elements, states, and TLEs.
6. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
7. Pass `--html` when the user wants the self-contained 3D HTML viewer, and `--open` only when they ask to open it.
8. Convert classical elements and a state to SI and radians before the call. Leave each TLE in its published lines. State the converted units in the reply. Do not invent a missing radius, element, TLE line, state component, or `--rb`.

## Flags

Run:

```text
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --r1 <m> --r2 <m> --rb <m> [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --a1 <m> --e1 <e> --i1 <rad> --raan1 <rad> --aop1 <rad> (--nu1 <rad> | --M1 <rad>) --a2 <m> --e2 <e> --i2 <rad> --raan2 <rad> --aop2 <rad> (--nu2 <rad> | --M2 <rad>) --rb <m> [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --rx1 <m> --ry1 <m> --rz1 <m> --vx1 <m/s> --vy1 <m/s> --vz1 <m/s> --rx2 <m> --ry2 <m> --rz2 <m> --vx2 <m/s> --vy2 <m/s> --vz2 <m/s> --rb <m> [--R0 <m>] [--out <png>] [--html] [--open]
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --tle1 "<line 1>" "<line 2>" --tle2 "<line 1>" "<line 2>" --rb <m> [--R0 <m>] [--out <png>] [--html] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r1` | Departure circular radius, from the center | m, \(\ge R_0\) | With `--r2` |
| `--r2` | Arrival circular radius, from the center | m, \(\ge R_0\) | With `--r1` |
| `--rb` | Common apoapsis of the two transfer ellipses, from the center | m, \(\ge \max(r_1,r_2)\) | Required |
| `--a1`, `--e1`, `--i1`, `--raan1`, `--aop1` | Departure classical elements | m, —, rad | Elements mode |
| `--nu1` or `--M1` | Departure true or mean anomaly | rad | Elements mode |
| `--a2`, `--e2`, `--i2`, `--raan2`, `--aop2` | Arrival classical elements | m, —, rad | Elements mode |
| `--nu2` or `--M2` | Arrival true or mean anomaly | rad | Elements mode |
| `--rx1`, `--ry1`, `--rz1`, `--vx1`, `--vy1`, `--vz1` | Departure inertial state | m, m/s | State mode |
| `--rx2`, `--ry2`, `--rz2`, `--vx2`, `--vy2`, `--vz2` | Arrival inertial state | m, m/s | State mode |
| `--tle1` | Departure NORAD two-line element set. Two 69-character lines. An optional name line may be first. | — | TLE mode |
| `--tle2` | Arrival NORAD two-line element set. Two 69-character lines. An optional name line may be first. | — | TLE mode |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional |
| `--html` | Write the 3D HTML viewer beside the PNG | — | Optional |
| `--open` | Open the HTML viewer in a browser | — | Optional |

A bare radius is metres. Kilometres use `1 km = 1000 m`. Element angles are radians. Degrees use \(\pi/180\). If the user gives two altitudes, convert each with \(r = R_0 + h\) and pass `--r1` and `--r2`. Convert an intermediate altitude the same way into `--rb`. A TLE is a mean-element set used as a Keplerian ellipse, then only its epoch radius is kept. Leave each TLE unchanged; line-2 angles are degrees. Semi-major axis comes from the published mean motion and this program's \(\mu\). BSTAR, the mean-motion derivatives, and SGP4 are not applied. The epoch is printed and does not move the spacecraft. A bad checksum is rejected. Report `tle1_*` and `tle2_*` when they are printed: catalog, designator, epoch year, epoch day, mean motion, BSTAR, and note, plus name when it is printed.

Every successful run writes one PNG. The plot title is `Bielliptic transfer`. The camera looks down the orbit normal (elevation \(90^\circ\), azimuth \(-90^\circ\)). The three burns are drawn as \(\Delta v\) arrows. The HTML viewer is written only with `--html` or `--open`. It opens on the same orbit-normal camera. Play starts on. The spacecraft parks on the departure circle, burns, coasts the first ellipse, burns at apoapsis, coasts the second ellipse, burns onto the arrival circle, then flies that circle. The path already flown is the solid trail in that orbit’s color; the remaining future path stays faded. Do not treat the unused rest of the current orbit as the solid line. `graph:` is the PNG. `viewer:` is the HTML when it is written.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path. If `viewer:` is printed, give it as a markdown link to that HTML file. Do not draw a second figure.
3. Report `R0_m`, `R0_source`, `g0_m_s2`, and `mu_m3_s2`.
4. Report `r_depart_m`, `r_arrive_m`, `r_b_m`, `h_depart_m`, `h_arrive_m`, and `h_b_m`.
5. Report `a1_m`, `e1`, `a2_m`, and `e2` for the two transfer ellipses.
6. Report `dv1_m_s`, `dv1_sense`, `dv2_m_s`, `dv2_sense`, `dv3_m_s`, `dv3_sense`, and `dv_m_s`. `dv_m_s` is the sum of the three burns.
7. Report `tof_s`, `tof1_s`, and `tof2_s`. The time of flight is the sum of the two half-ellipse coasts.
8. Report `r2_over_r1`. That is \(|r_{\mathrm{arrive}}|/|r_{\mathrm{depart}}|\).
9. Report `dv_hohmann_m_s`, `dv_biparabolic_m_s`, and `recommendation`. `Hohmann` means this `--rb` is not cheaper than the two-burn Hohmann path, so recommend `ASTRO - HohmannTransfer`. `bielliptic` means this three-burn path uses less delta-v than Hohmann.
10. Repeat `warning` when it is printed.
11. If `--rb` or either orbit is missing, say so. Do not fill it in.
