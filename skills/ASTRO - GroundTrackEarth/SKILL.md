---
name: ASTRO - GroundTrackEarth
description: >-
  Run the Earth ground-track program and report its printed results and PNG. Use
  when the user wants the latitude and longitude of the subsatellite point, or a
  map of that track over ten orbital periods by default, from classical elements, a NORAD
  two-line element set, or an inertial state plus the Greenwich angle at epoch. Do not redraw the track or recompute
  the numbers by hand.
---

# ASTRO - GroundTrackEarth

Use this skill for the subsatellite ground track of an Earth ellipse. Run the program once; quote its stdout and include its PNG. Do not redraw the track or recompute the numbers by hand.

Assumptions (also printed by the program): inverse-square mean motion on an ellipse. First-order \(J_2\) secular rates are the same records as `ASTRO - J2SecularRates`. \(\Omega\) and \(\omega\) use `j2_nodal_rate` and `j2_apsidal_rate`. Semi-major axis, eccentricity, and inclination have no secular \(J_2\) rate. Drag, third body, higher zonals, and the \(J_2\) mean-motion correction are omitted. Flattening changes the geodetic latitude of the subsatellite point only; it does not enter \(\mu\). \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). The WGS 84 ellipsoid is \(a_e = 6378137\,\mathrm{m}\), \(f = 1/298.257223563\), and \(\omega_E = 7.292115\times 10^{-5}\,\mathrm{rad/s}\). That \(a_e\) is \(R_E\) in the \(J_2\) term. The default \(J_2\) is \(1.08228\times 10^{-3}\) (GSFC, March 1986, NASA RP-1204). Pass `--j2 0` for Keplerian inertial motion. Greenwich angle is `greenwich_angle`. Earth-fixed position is `earth_fixed_x`, `earth_fixed_y`, and `earth_fixed_z`. Geocentric latitude uses `geocentric_latitude_sine` and `geocentric_latitude_cosine`. Longitude uses `longitude_sine` and `longitude_cosine`. Geodetic latitude is `geodetic_latitude_from_geocentric`. The frame is planet-centered inertial: \(+Z\) is the polar axis, and \(\Omega\) is measured from \(+X\).

An ellipse has \(a > 0\) and \(0 \le e < 1\). A hyperbola or parabola is rejected. Singular orbits use the same ELCONO conventions as OrbitalParameters.

## When to run

1. Classical elements: pass `--a`, `--e`, `--i`, `--raan`, `--aop`, and exactly one of `--nu` or `--M`.
2. Inertial state: pass `--rx`, `--ry`, `--rz`, `--vx`, `--vy`, and `--vz`.
3. NORAD TLE: pass `--tle` with line 1 and line 2. A name line may be the first argument. Do not convert those angles to radians. The TLE epoch is not `--greenwich`.
4. Pass one mode. Do not combine a TLE, elements, and a state.
5. `--greenwich` is required. It is the Greenwich angle at epoch, in radians.
6. The baseline map is 10 orbital periods from epoch. If the user names an orbit count (for example "3 orbits" or "20 revolutions"), pass that number as `--orbits`. Do not convert it to seconds by hand. If the user names a duration, pass `--span`, or pass both `--t0` and `--t1`. Do not mix `--orbits` with a time window. If they omit both a count and a duration, omit `--orbits` and let the program use 10.
7. Pass `--R0` only when the user gives a two-body radius other than the Earth default. Pass `--ae`, `--flattening`, or `--omega-e` only when the user overrides the WGS 84 ellipsoid or Earth rate. Pass `--j2` only when the user overrides the GSFC \(J_2\), including `--j2 0` for a Keplerian track.
8. Convert classical elements and a state to SI and radians before the call. Leave a TLE in its published lines. State the converted units in the reply. Do not invent a missing element, TLE line, state component, Greenwich angle, or orbit count. Do not ask for an orbit count unless the user asked to change it and did not give a number.

## Flags

Run:

```text
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --a <m> --e <e> --i <rad> --raan <rad> --aop <rad> (--nu <rad> | --M <rad>) --greenwich <rad> [--orbits <n> | --span <s> | --t0 <s> --t1 <s>] [--samples <n>] [--R0 <m>] [--ae <m>] [--flattening <f>] [--omega-e <rad/s>] [--j2 <J2>] [--out <png>]
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --rx <m> --ry <m> --rz <m> --vx <m/s> --vy <m/s> --vz <m/s> --greenwich <rad> [--orbits <n> | --span <s> | --t0 <s> --t1 <s>] [--samples <n>] [--R0 <m>] [--ae <m>] [--flattening <f>] [--omega-e <rad/s>] [--j2 <J2>] [--out <png>]
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --tle "<line 1>" "<line 2>" --greenwich <rad> [--orbits <n> | --span <s> | --t0 <s> --t1 <s>] [--samples <n>] [--R0 <m>] [--ae <m>] [--flattening <f>] [--omega-e <rad/s>] [--j2 <J2>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Semi-major axis | m, \(> 0\) | Elements mode |
| `--e` | Eccentricity | dimensionless, \(0 \le e < 1\) | Elements mode |
| `--i` | Inclination | rad, \(0 \le i \le \pi\) | Elements mode |
| `--raan` | Longitude of the ascending node, \(\Omega\) | rad | Elements mode |
| `--aop` | Argument of periapsis, \(\omega\) | rad | Elements mode |
| `--nu` | True anomaly at epoch | rad | Elements mode, or `--M` |
| `--M` | Mean anomaly at epoch | rad | Elements mode, or `--nu` |
| `--rx`, `--ry`, `--rz` | Inertial position | m | State mode, all three |
| `--vx`, `--vy`, `--vz` | Inertial velocity | m/s | State mode, all three |
| `--tle` | NORAD two-line element set. Two 69-character lines. An optional name line may be first. | — | TLE mode |
| `--greenwich` | Greenwich angle at epoch | rad | Required |
| `--orbits` | Number of orbital periods from epoch | dimensionless, \(> 0\) | Optional. Default \(10\) |
| `--span` | Duration from epoch \(t=0\) | s, \(> 0\) | Optional. Overrides `--orbits` |
| `--t0`, `--t1` | Start and end time | s, \(\mathrm{t}_1 \ne \mathrm{t}_0\) | Optional. Overrides `--orbits` |
| `--samples` | Number of track samples | integer, \(\ge 2\) | Optional. Default \(361\) samples per orbit |
| `--R0` | Radius in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--ae` | Ellipsoid equatorial radius and \(R_E\) in \(J_2\) | m, \(> 0\) | Optional. WGS 84 \(6378137\) |
| `--flattening` | Ellipsoid flattening | dimensionless, \(0 \le f < 1\) | Optional. WGS 84 \(1/298.257223563\) |
| `--omega-e` | Earth sidereal rate | rad/s, \(\ge 0\) | Optional. WGS 84 \(7.292115\times 10^{-5}\) |
| `--j2` | Second zonal harmonic | dimensionless, \(\ge 0\) | Optional. Default \(1.08228\times 10^{-3}\). `0` is Keplerian |
| `--out` | PNG path | — | Optional |

A bare length is metres. Kilometres use `1 km = 1000 m`. Element angles, `--nu`, `--M`, and `--greenwich` are radians. Degrees use \(\pi/180\). A time in minutes uses `60 s`. A time in hours uses `3600 s`. A TLE is a mean-element set used as a Keplerian ellipse. Leave its lines unchanged; line-2 angles are degrees. Semi-major axis comes from the published mean motion and this program's \(\mu\). BSTAR, the mean-motion derivatives, and SGP4 are not applied. The printed epoch is not the Greenwich angle. A bad checksum is rejected.

Every successful run writes one PNG. The plot title is `ASTRO - GroundTrackEarth`. Axes are longitude in degrees east of Greenwich and geodetic latitude in degrees. Land is Natural Earth 1:110m, which is public domain. The map is not a copyrighted satellite image. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `mode`. `elements` started from classical elements. `state` started from position and velocity. `tle` started from a NORAD two-line element set. When `mode` is `tle`, also report `tle_catalog`, `tle_designator`, `tle_epoch_year`, `tle_epoch_day`, `tle_n_rev_day`, `tle_bstar`, and `tle_note`, and `tle_name` if it is printed.
4. Report `R0_m`, `R0_source`, `g0_m_s2`, `mu_m3_s2`, `ae_m`, `ae_source`, `flattening`, `polar_radius_m`, `omega_e_rad_s`, `J2`, and `J2_source`.
5. Report `greenwich_epoch_rad`, `t0_s`, `t1_s`, `orbits`, and `samples`.
6. Report `a_m`, `e`, `i_rad`, `Omega_rad`, `omega_rad`, `nu_epoch_rad`, `M_epoch_rad`, `n_rad_s`, `period_s`, `Omega_dot_rad_s`, `omega_dot_rad_s`, `Omega_end_rad`, and `omega_end_rad`.
7. Report epoch and end `lat_geocentric`, `lat_geodetic`, and `lon`, all in radians as printed. Also report `lat_geodetic_max_rad` and `lat_geodetic_min_rad`.
8. State that geodetic latitude includes oblate geometry and that inertial \(\Omega\) and \(\omega\) use the first-order \(J_2\) rates from `ASTRO - J2SecularRates` unless `J2` is 0.
9. If an element, a state component, or Greenwich angle is missing, say so. Do not fill it in. If the time window and orbit count are omitted, the program maps 10 orbits. If the user later asks for a different count, rerun with `--orbits`.
