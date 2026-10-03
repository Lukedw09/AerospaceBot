---
name: ASTRO - HohmannTransfer
description: >-
  Run the Hohmann-transfer program and report its printed results and PNG.
  Use when the user wants the delta-v, time of flight, circular speed, escape
  speed, or specific energy for a transfer between two circular orbits, given
  either both radii or a departure altitude and transfer eccentricity. Do not
  redraw the orbit or recompute the numbers by hand.
---

# ASTRO - HohmannTransfer

Use this skill for an impulsive Hohmann transfer between two circular orbits. Run the program once; quote its stdout and include its PNG. Do not redraw the orbit or recompute the numbers by hand.

Assumptions (also printed by the program): spherical planet, inverse-square gravity, and no drag, thrust, or third body on the coast. Each burn is impulsive and sits at an apsis. The coast is half of the transfer ellipse. Circular speed is `circular_orbit_velocity`. Escape speed is `escape_velocity`. Coast speeds are `vis_viva`. Specific energy is `specific_orbital_energy`. Time of flight is half of `orbital_period`. \(\mu = g_0 R_0^{2}\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\). The Earth default is \(R_0 = 6.3742\times 10^{6}\,\mathrm{m}\). A radius is the distance from the center. An altitude is geometric height above \(R_0\).

`--r1` is the departure circular orbit and `--r2` is the arrival circular orbit. When `--r2` is larger, both burns are prograde and departure is periapsis. When `--r1` is larger, both burns are retrograde and departure is apoapsis. Equal radii coast for half a revolution at zero delta-v.

`--alt` and `--ecc` describe the same transfer with departure at periapsis. The departure radius is \(R_0 + h\). The arrival radius is that radius times \((1+e)/(1-e)\). This path is an outward transfer. A descent uses `--r1` and `--r2`.

## When to run

1. Two circular orbits: pass `--r1` and `--r2`. Convert altitudes to radii with \(r = R_0 + h\) before the call, using the Earth \(R_0\) unless the user gave another planetary radius. State that conversion in the reply.
2. One departure altitude and a transfer eccentricity: pass `--alt` and `--ecc`. Departure is the circular orbit at that altitude and is periapsis of the ellipse.
3. Pass `--R0` only when the user gives a planetary radius other than the Earth default.
4. Convert inputs to SI before the call (m). State the converted units in the reply. Do not invent a second radius, an eccentricity, or a planetary radius.

## Flags

Run:

```text
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --r1 <m> --r2 <m> [--R0 <m>] [--out <png>]
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --alt <m> --ecc <e> [--R0 <m>] [--out <png>]
```

Pass one input pair. Do not pass both pairs.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r1` | Departure circular radius, from the center | m, \(\ge R_0\) | With `--r2` |
| `--r2` | Arrival circular radius, from the center | m, \(\ge R_0\) | With `--r1` |
| `--alt` | Geometric altitude of the departure circular orbit | m, \(\ge 0\) | With `--ecc` |
| `--ecc` | Eccentricity of the transfer ellipse. Departure is periapsis. | dimensionless, \(0 \le e < 1\) | With `--alt` |
| `--R0` | Planetary radius used in \(\mu = g_0 R_0^{2}\) | m, \(> 0\) | Optional. Earth default \(6.3742\times 10^{6}\) |
| `--out` | PNG path | — | Optional |

A bare radius or altitude is metres. Kilometres use `1 km = 1000 m`. Statute miles use `1 mi = 1609.344 m`. Nautical miles use `1 nmi = 1852 m`. If the user gives two altitudes, convert each with \(r = R_0 + h\) and pass `--r1` and `--r2`. If the user gives geopotential altitude, convert to geometric altitude before adding \(R_0\), and say so.

Every successful run writes one PNG. The plot title is `Hohmann transfer`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. `graph:` is the file path.
3. Report `R0_m`, `R0_source`, `g0_m_s2`, and `mu_m3_s2`. `default` means the Earth radius from the circular-orbit formula.
4. Report `r_depart_m`, `r_arrive_m`, `h_depart_m`, and `h_arrive_m`. State that a radius is measured from the center and an altitude is height above \(R_0\).
5. Report `direction`. `outward` leaves from periapsis with two prograde burns. `inward` leaves from apoapsis with two retrograde burns. `coast` means the radii are equal.
6. Report `a_m` and `e` for the transfer ellipse.
7. Report `v_circular_depart_m_s`, `v_escape_depart_m_s`, `v_circular_arrive_m_s`, and `v_escape_arrive_m_s`.
8. Report `energy_depart_J_kg`, `energy_arrive_J_kg`, and `energy_transfer_J_kg`. These are specific mechanical energies of the two circular orbits and of the transfer ellipse.
9. Report `dv_depart_m_s`, `dv_depart_sense`, `dv_arrive_m_s`, `dv_arrive_sense`, and `dv_m_s`. `dv_m_s` is the sum of the two burns.
10. Report `tof_s`. That is the coast from departure to arrival. `period_s` is the full period of the transfer ellipse, twice the time of flight.
11. Repeat `warning` when it is printed.
12. If a radius, an altitude, or an eccentricity is missing, say so. Do not fill it in.
