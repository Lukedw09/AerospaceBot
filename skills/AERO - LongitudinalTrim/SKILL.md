---
name: AERO - LongitudinalTrim
description: >-
  Run the stick-fixed trim program and report the 1-g angle of attack,
  elevator, and PNG. Use when the user wants cruise trim, not only the
  neutral point. Do not redraw the plot or recompute the numbers by hand.
---

# AERO - LongitudinalTrim

Use this skill for steady 1-g level flight with the stick fixed: the angle of attack that supplies the lift coefficient, and the elevator that makes pitching moment zero. If the user only wants the neutral point or static margin, use `AERO - LongitudinalStaticMargin` and do not run this program. Run it once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

\[
C_L=\frac{W}{qS},\qquad C_{m\alpha}=-a K_n,\qquad \alpha=\frac{C_L}{a},\qquad \delta_e=-\frac{C_{m0}+C_{m\alpha}\alpha}{C_{m\delta_e}}
\]

`level_flight_lift_coefficient`, `cm_alpha_from_static_margin`, `trim_angle_of_attack`, and `trim_elevator` are those relations. \(K_n=x/c\) is a fraction of chord. \(C_{m\delta_e}\) is supplied. The lift curve passes through the origin.

## When to run

1. Use this skill when the user wants trim angle of attack and elevator for level flight.
2. Pass `--a`, `--cm0`, and `--cm-de`. Do not invent elevator effectiveness.
3. Pass `--CL`, or `--q`, `--S`, and `--W`. Pass `--cm-alpha`, or `--kn` as a fraction of chord, or the same geometry flags as `AERO - LongitudinalStaticMargin` (`--at`, `--downwash`, `--q-ratio`, `--tail-area`, `--tail-length`, `--wing-area`, `--mac`, `--cg`). Do not mix those three pitching-moment sources.
4. Pass `--de-max` only when the user gave an elevator limit.
5. Do not use this skill for a flap schedule or a free-stick neutral point.

## Flags

Run:

```text
python "skills/AERO - LongitudinalTrim/longitudinal_trim.py" --a <1/rad> --cm0 <1> --cm-de <1/rad> [--CL <1>] [--kn <1>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--a` | Lift-curve slope | 1/rad, \(> 0\) | Required |
| `--cm0` | Moment at zero alpha and elevator | dimensionless | Required |
| `--cm-de` | Elevator effectiveness | 1/rad, nonzero | Required |
| `--CL` | Lift coefficient | dimensionless | Optional; or `--q` `--S` `--W` |
| `--q` | Dynamic pressure | Pa, \(> 0\) | Optional; with `--S` and `--W` |
| `--S` | Wing area | m², \(> 0\) | Optional; with `--q` and `--W` |
| `--W` | Weight | N | Optional; with `--q` and `--S` |
| `--cm-alpha` | Pitch stiffness | 1/rad | Optional; or `--kn` or geometry |
| `--kn` | Static margin \(x/c\) | fraction of chord | Optional; or `--cm-alpha` or geometry |
| `--at` | Tail lift-curve slope | 1/rad, \(> 0\) | Optional; with the geometry set |
| `--downwash` | Downwash slope | dimensionless | Optional; with the geometry set |
| `--q-ratio` | Tail dynamic-pressure ratio | dimensionless, \(> 0\) | Optional; with the geometry set |
| `--tail-area` | Horizontal-tail area | m², \(> 0\) | Optional; with the geometry set |
| `--tail-length` | Tail length | m, \(> 0\) | Optional; with the geometry set |
| `--wing-area` | Wing area | m², \(> 0\) | Optional; with the geometry set |
| `--mac` | Mean aerodynamic chord | m, \(> 0\) | Optional; with the geometry set |
| `--cg` | Center of gravity \(x'/c\) | fraction of chord | Optional; with the geometry set |
| `--de-max` | Elevator limit | rad, \(> 0\) | Optional |
| `--out` | PNG path | file | Optional |
