---
name: ASTRO - GravityAssistFlyby
description: >-
  Run the planar gravity-assist program and report the turned excess velocity,
  heliocentric delta-v, and figure. Use when the user wants the patched-conic
  assist, not a park-orbit burn. Do not redraw the plot or recompute the
  numbers by hand.
---

# ASTRO - GravityAssistFlyby

Use this skill for the gravity-assist patch: the same excess speed, a new direction, and the heliocentric velocity change. Planet-centered hyperbola sizing without that patch stays on `ASTRO - HyperbolicExcess`. Named-body \(\mu\) and radius come from `ASTRO - SolarSystemBody` before this call. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Eccentricity is `hyperbolic_eccentricity_from_periapsis`. The turn is `hyperbola_turning_angle`, \(\delta=2\arcsin(1/e)\). A left turn rotates the inbound excess velocity by \(+\delta\). Heliocentric velocity is the planet velocity plus the excess velocity. `flyby_kinetic_change` is the specific-energy change at fixed heliocentric radius.

## When to run

1. Use this skill when the user wants the heliocentric effect of a planar flyby.
2. Pass `--rp`, `--turn` (`left` or `right`), `--vp-x`, and `--vp-y`. Pass `--mu` or `--R0`, and `--vinf` or `--C3`. Do not invent a planet.
3. Pass `--ux` and `--uy` for the inbound excess direction, or `--psi` as that direction’s angle from the planet velocity. Do not pass both.
4. Pass `--html` when the user wants the viewer. It is the same self-contained Three.js page as `ASTRO - OrbitalParameters`: a lit planet, the hyperbola, and the spacecraft coasting from the inbound asymptote through periapsis. Coast time follows the hyperbolic Kepler equation, so the spacecraft is fastest at closest approach. Pass `--radius` for that surface, or `--R0`, which is also the drawn radius. Do not invent a radius.
5. Pass `--out` only for a chosen PNG path.
6. Do not use this skill for a B-plane target or for the propellant to reach the hyperbola.

## Flags

Run:

```text
python "skills/ASTRO - GravityAssistFlyby/gravity_assist_flyby.py" --rp <m> --turn <left|right> --vp-x <m/s> --vp-y <m/s> (--mu <m^3/s^2> | --R0 <m>) (--vinf <m/s> | --C3 <m^2/s^2>) (--ux <1> --uy <1> | --psi <rad>) [--radius <m>] [--html] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--rp` | Periapsis radius from the planet center | m, \(> 0\) | Required |
| `--turn` | `left` or `right` | — | Required |
| `--vp-x` | Planet heliocentric velocity, x | m/s | Required |
| `--vp-y` | Planet heliocentric velocity, y | m/s | Required |
| `--mu` | Gravitational parameter | m³/s², \(> 0\) | Optional; or `--R0` |
| `--R0` | Radius for \(\mu=g_0 R_0^2\), and the drawn planet if `--radius` is omitted | m, \(> 0\) | Optional; or `--mu` |
| `--radius` | Planetary surface drawn in the viewer | m, \(> 0\) | Optional; required with `--html` unless `--R0` is set |
| `--vinf` | Hyperbolic excess speed | m/s, \(> 0\) | Optional; or `--C3` |
| `--C3` | Characteristic energy | m²/s², \(> 0\) | Optional; or `--vinf` |
| `--ux` | Inbound excess direction, x | dimensionless | Optional; pair with `--uy` |
| `--uy` | Inbound excess direction, y | dimensionless | Optional; pair with `--ux` |
| `--psi` | Inbound excess angle from the planet velocity | rad | Optional; instead of `--ux` `--uy` |
| `--html` | Write the animated planet viewer | flag | Optional |
| `--out` | PNG path | file | Optional |
