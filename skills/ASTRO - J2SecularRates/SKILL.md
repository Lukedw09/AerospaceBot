---
name: ASTRO - J2SecularRates
description: >-
  Run the J2 secular-rate program and report its printed results and PNG. Use
  when the user wants first-order J2 nodal or apsidal precession, or the
  sun-synchronous inclination of an Earth ellipse, from the same classical
  elements, NORAD two-line element set, or inertial state used by
  GroundTrackEarth or PlaneChangeImpulse.
  Do not redraw the rate curves or recompute the numbers by hand.
---

# ASTRO - J2SecularRates

Use this skill for first-order \(J_2\) nodal and apsidal rates on one Keplerian ellipse, and for the sun-synchronous inclination that matches those nodal rates to the apparent solar motion. Run the program once; quote its stdout and include its PNG. Do not redraw the curves or recompute the numbers by hand.

Assumptions (also printed by the program): first-order \(J_2\) only. Semi-major axis, eccentricity, and inclination have no secular \(J_2\) rate. Drag, third body, and higher zonals are omitted. Nodal rate is `j2_nodal_rate`. Apsidal rate is `j2_apsidal_rate`. Mean motion is `mean_motion`. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). The equatorial radius in the \(J_2\) term is `ae`, default WGS 84 \(6378137\,\mathrm{m}\). The default \(J_2\) is \(1.08228\times 10^{-3}\) (GSFC, March 1986, NASA RP-1204). Sun-synchronous nodal rate is `sun_sync_nodal_rate` with \(Y = 365.2422\) days from the GDC Orbit Primer (\(0.9856\,\mathrm{deg/day}\)). The matching inclination cosine is `sun_sync_inclination_cosine`. Element angles are radians. `--greenwich` and `--di` are accepted so a GroundTrackEarth or PlaneChangeImpulse command can be reused; they do not enter the rates.

An ellipse has \(a > 0\) and \(0 \le e < 1\). A hyperbola or parabola is rejected. Singular orbits use the same ELCONO conventions as OrbitalParameters.

## When to run

1. Classical elements, the same set as GroundTrackEarth or PlaneChangeImpulse: pass `--a`, `--e`, `--i`, `--raan`, `--aop`, and exactly one of `--nu` or `--M`.
2. Inertial state, the same set as those skills: pass `--rx`, `--ry`, `--rz`, `--vx`, `--vy`, and `--vz`.
3. NORAD TLE: pass `--tle` with line 1 and line 2. A name line may be the first argument. Do not convert those angles to radians.
4. Pass one mode. Do not combine a TLE, elements, and a state.
5. `--greenwich` and `--di` are optional. Pass them when the user copied a GroundTrackEarth or PlaneChangeImpulse command. Do not invent them.
6. Pass `--R0` only when the user gives a two-body radius other than the Earth default. Pass `--ae` only when the user overrides the WGS 84 equatorial radius in the \(J_2\) term. Pass `--j2` or `--year` only when the user overrides those defaults.
7. Convert classical elements and a state to SI and radians before the call. Leave a TLE in its published lines. State the converted units in the reply. Do not invent a missing element, TLE line, or state component.

## Flags

Run:

```text
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --a <m> --e <e> --i <rad> --raan <rad> --aop <rad> (--nu <rad> | --M <rad>) [--greenwich <rad>] [--di <rad>] [--R0 <m>] [--ae <m>] [--j2 <J2>] [--year <day>] [--out <png>]
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --rx <m> --ry <m> --rz <m> --vx <m/s> --vy <m/s> --vz <m/s> [--greenwich <rad>] [--di <rad>] [--R0 <m>] [--ae <m>] [--j2 <J2>] [--year <day>] [--out <png>]
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --tle "<line 1>" "<line 2>" [--greenwich <rad>] [--di <rad>] [--R0 <m>] [--ae <m>] [--j2 <J2>] [--year <day>] [--out <png>]
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
| `--greenwich` | Greenwich angle at epoch. Accepted unused. | rad | Optional |
| `--di` | Inclination change. Accepted unused. | rad | Optional |
| `--R0` | Radius in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--ae` | Equatorial radius in the \(J_2\) term | m, \(> 0\) | Optional. WGS 84 \(6378137\) |
| `--j2` | Second zonal harmonic | dimensionless, \(> 0\) | Optional. GSFC \(1.08228\times 10^{-3}\) |
| `--year` | Mean solar year in `sun_sync_nodal_rate` | day, \(> 0\) | Optional. Primer \(365.2422\) |
| `--out` | PNG path | — | Optional |

A bare length is metres. Kilometres use `1 km = 1000 m`. Element angles, `--nu`, `--M`, `--greenwich`, and `--di` are radians. Degrees use \(\pi/180\). A TLE is a mean-element set used as a Keplerian ellipse. Leave its lines unchanged; line-2 angles are degrees. Semi-major axis comes from the published mean motion and this program's \(\mu\). BSTAR, the mean-motion derivatives, and SGP4 are not applied. The epoch is printed and does not enter the rates. A bad checksum is rejected.

Every successful run writes one PNG. The plot title is `ASTRO - J2SecularRates`. Axes are inclination in degrees and rates in degrees per day. The upper panel is nodal rate with the sun-synchronous rate and the sun-synchronous inclination marked when that inclination exists. The lower panel is apsidal rate with the critical inclinations marked. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `mode`. `elements` started from classical elements. `state` started from position and velocity. `tle` started from a NORAD two-line element set. When `mode` is `tle`, also report `tle_catalog`, `tle_designator`, `tle_epoch_year`, `tle_epoch_day`, `tle_n_rev_day`, `tle_bstar`, and `tle_note`, and `tle_name` if it is printed.
4. Report `R0_m`, `R0_source`, `g0_m_s2`, `mu_m3_s2`, `ae_m`, `ae_source`, `J2`, `J2_source`, `year_days`, and `year_source`.
5. Report `a_m`, `e`, `i_rad`, `Omega_rad`, `omega_rad`, `nu_rad`, `n_rad_s`, `period_s`, and `p_m`. Report `M_rad` on an ellipse.
6. Report `Omega_dot_rad_s`, `Omega_dot_deg_day`, `omega_dot_rad_s`, and `omega_dot_deg_day`.
7. Report `sun_sync_rate_rad_s`, `sun_sync_rate_deg_day`, and `sun_sync_inclination_cosine`. Report `i_ss_rad` and `i_ss_deg` when they are printed. Report `i_ss: none` when no real sun-synchronous inclination exists at that \(a\) and \(e\).
8. Repeat `warning` when it is printed. Repeat `greenwich_unused_rad` or `di_unused_rad` when they are printed.
9. If an element or a state component is missing, say so. Do not fill it in.

Interactive lab offer: before running this program for a new Earth-orbit transfer, station-keeping, rendezvous, or ops design or sizing thread, ask once whether the user wants `ASTRO - OrbitDesignLab` (interactive HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.
