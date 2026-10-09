---
name: ASTRO - OrbitDesignLab
description: >-
  Bake an interactive Earth-orbit design page. Use only when the user
  explicitly asks for this lab, the orbit design studio, or a live globe
  that compares Hohmann and bielliptic transfers. Do not run it just
  because an orbit is being sized.
---

# ASTRO - OrbitDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `ASTRO - OrbitDesignLab`, or they clearly ask for the interactive HTML page, the orbit design studio, or a live globe of a transfer. Do not run it because a Hohmann, plane-change, station-keeping, or rendezvous conversation is underway. Do not run it from another astrodynamics skill unless they explicitly said yes to that offer.

The program writes a PNG of the seed Hohmann and bielliptic paths and a self-contained HTML page. The page recomputes in the browser. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. After they change the page, use the export block with `ASTRO - VacuumPropellantMass` and the one-shot orbit skills if they want those programs quoted. This lab does not replace that CLI chain.

The hero view is a Hohmann versus bielliptic comparison on one globe, with burn markers. Strategy `auto` follows the bielliptic program: use bielliptic when its delta-v is lower, otherwise Hohmann. Secondary tabs cover plane change, geostationary station-keeping, Clohessy–Wiltshire relative motion, phasing to a target on the same circular orbit, Lambert, an impulsive LEO raise, insertion, elements and eclipse fraction, ground track, coverage, J2 rates, and launch azimuth. Orbit sizes on the page are heights above the surface.

Coverage uses the same latitude–longitude map as the ground track. It traces a wide corridor along the subsatellite track. The half-width is the Earth-central angle from `ASTRO - CoverageAndRevisit`. The revisit count is still the single-satellite equatorial count. The map is not the swath-versus-elevation chart.

The LEO-raise tab is `hohmann_impulsive` from `ASTRO - MultiBurnLeoRaise` plus `plane_change_impulse` at the slower circular radius. Gravity loss is 0. It is not the finite-thrust integrator. Say that if they export `leo_raise`, so they do not also count propellant from `ASTRO - MultiBurnLeoRaise`.

The Clohessy–Wiltshire budget piece is the hypotenuse of the null components, or of the hold components when that piece is selected. The one-shot program does not print a scalar total.

Checked budget rows become `--name` and `--dv` arguments for `ASTRO - VacuumPropellantMass`. The page can preview propellant when dry mass and specific impulse are set. Quote `ASTRO - VacuumPropellantMass` for the propellant result they want reported. Dry mass and specific impulse are not invented by the orbit skills.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before the call (m, rad). State the converted units in the reply. The page shows plane change, station-keeping drift, phase, flight-path angle, inclination, elevation, and launch angles in degrees.
3. Pass only flags the user supplied. Omitted flags keep the program defaults: Earth \(R_0\), a 400 km circular departure, geostationary arrival, bielliptic apoapsis at twice that arrival radius, and strategy `auto`.
4. Pass `--alt` and `--ecc` together when they describe the Hohmann path that way. Do not also pass `--r1` or `--r2`. The baked page stores the resulting radii.
5. Pass `--rb` only when they give the intermediate apoapsis. It must be at least the larger circular radius.
6. Pass `--R0` only when they give a planetary radius other than the Earth default. That radius rebuilds the default 400 km departure, the geostationary arrival from the new \(\mu\), and the other default orbits that must lie outside the body. Geostationary station-keeping, drag, coverage, and launch azimuth stay on the Earth constants of those skills.
7. Pass `--open` only when they ask to open the HTML file.
8. In the reply, state every assumption the user did not supply, including the default radii, the bielliptic apoapsis, the secondary-tab seeds, dry mass 500 kg, and specific impulse 310 s when those budget fields were not set.

## Flags

Run:

```text
python "skills/ASTRO - OrbitDesignLab/orbit_design_lab.py" [--r1 <m> --r2 <m> | --alt <m> --ecc <e>] [--rb <m>] [--R0 <m>] [--strategy auto|hohmann|bielliptic] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--r1` | Departure circular radius | m | With `--r2`, unless `--alt` |
| `--r2` | Arrival circular radius | m | With `--r1`, unless `--alt` |
| `--alt` | Departure altitude for the Hohmann eccentricity form | m | With `--ecc` |
| `--ecc` | Transfer eccentricity; departure is periapsis | dimensionless | With `--alt` |
| `--rb` | Common bielliptic apoapsis | m | Optional |
| `--R0` | Planetary radius in \(\mu = g_0 R_0^2\) | m | Optional |
| `--strategy` | `auto`, `hohmann`, or `bielliptic` | — | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. State the radii, the strategy, and that a radius is measured from the center.
3. Include the PNG. Give `viewer:` as a markdown link.
4. Tell them the globe is where to compare Hohmann and bielliptic, and that the other tabs and the budget checkboxes update immediately.
5. If they use the LEO-raise tab, say gravity loss is not included.
6. If they use Clohessy–Wiltshire, say the budget scalar is the hypotenuse of the selected components.
7. If they use coverage, say the map traces the swath corridor and the revisit number is equatorial.
8. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.
