---
name: ASTRO - LaunchAzimuthInclination
description: >-
  Run the launch-azimuth program and report its printed results, PNG, and HTML.
  Use when the user wants orbital inclination from a launch latitude and
  azimuth, the azimuths that reach a target inclination, or the Earth-rotation
  assist along the launch heading. Do not recompute the angles by hand.
---

# ASTRO - LaunchAzimuthInclination

Use this skill for the orbit plane set by a launch site and for the eastward Earth-rotation speed along the heading. Run the program once; quote its stdout. Include the PNG and give `viewer:` as a markdown link.

Assumptions (also printed): spherical Earth. `launch_inclination_cosine` is \(\cos i=\cos\phi\sin A\) with \(A\) clockwise from north (NASA TN D-233). A negative sine is a westward heading and \(i>\pi/2\). `launch_azimuth_sine` inverts that. Minimum inclination is \(|\phi|\). `earth_rotation_inertial_speed` and `launch_rotation_assist` use WGS 84 \(\omega_E=7.292115\times 10^{-5}\,\mathrm{rad/s}\) and \(R=6378137\,\mathrm{m}\) unless the user overrides them.

## When to run

1. Use this skill when the user gives a launch latitude and either an azimuth or a target inclination.
2. Convert angles to radians. State the conversion. Do not invent a latitude, azimuth, or inclination.
3. Pass `--az` or `--i`, not a guessed pair. If both are given, pass both only when the user stated both; the program uses `--az` and still prints the matching inclination.
4. Pass `--radius` or `--omega` only when the user gives them.

## Flags

Run:

```text
python "skills/ASTRO - LaunchAzimuthInclination/launch_azimuth_inclination.py" --lat <rad> (--az <rad> | --i <rad>) [--radius <m>] [--omega <rad/s>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--lat` | Geocentric latitude | rad, \(-\pi/2\) to \(\pi/2\) | Required |
| `--az` | Launch azimuth clockwise from north | rad | Or `--i` |
| `--i` | Target inclination | rad, \(0\) to \(\pi\) | Or `--az` |
| `--radius` | Earth radius used for rotation speed | m | Optional |
| `--omega` | Earth rotation rate | rad/s | Optional |
| `--out` | PNG path. HTML is written beside it | — | Optional |
| `--open` | Open the HTML viewer | — | Optional |

Degrees use `rad = deg * pi/180`. A latitude in the southern hemisphere is negative.

Every successful run writes a PNG of the opening 3D view and a self-contained HTML globe. Earth has a rotation axis. The axis, equator, and orbit are solid on the near side and dotted where they pass behind the planet. `graph:` is the PNG. `viewer:` is the HTML.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG. Give `viewer:` as a markdown link.
3. Report `i_rad`, `i_min_rad`, `az_rad`, `az_alt_rad`, `v_rot_m_s`, and `v_rot_assist_m_s`.
4. `v_rot_assist_m_s` is the credit passed to `ROCKET - LeoDeltaVBudget`.
5. If latitude or both azimuth and inclination are missing, say so. Do not fill them in.
