---
name: AERO - WindTunnelSimilarity
description: >-
  Run the wind-tunnel similarity program and report Reynolds and Mach match
  plus optional full-scale loads. Use when the user is comparing a model to
  full scale, not applying a wall or compressibility correction. Do not
  redraw the plot or recompute the numbers by hand.
---

# AERO - WindTunnelSimilarity

Use this skill to compare model and full-scale Reynolds and Mach numbers, and to scale a measured force or moment when the coefficients are taken as equal. A relative mismatch above 0.05 is reported as not matched. Wall corrections are omitted. Compressibility corrections stay on `AERO - PrandtGlauertCorrectionandCriticalMach`. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Reynolds number is `reynolds_number` or `reynolds_number_kinematic`. Mach number is `mach_number`. Dynamic pressure is `dynamic_pressure`. Force and moment scales are `force_scale_dynamic_pressure` and `moment_scale_dynamic_pressure`.

## When to run

1. Use this skill when the user asks whether a tunnel condition stands in for full scale, or how a model load scales.
2. Pass `--re-m`, `--re-f`, `--mach-m`, and `--mach-f` together, or the flow path: lengths, speeds, sound speeds, and viscosity or kinematic viscosity. Do not mix the two paths. Do not invent a Reynolds or Mach number.
3. Pass `--force-m` with areas and dynamic pressures only when the user measured a model force and wants the full-scale force at the same coefficient. A moment also needs both chords.
4. Dynamic pressure may be `--q-m` and `--q-f`, or `½ρV²` when density and speed are on the flow path.

## Flags

Run:

```text
python "skills/AERO - WindTunnelSimilarity/wind_tunnel_similarity.py" [--re-m <Re> --re-f <Re> --mach-m <M> --mach-f <M>] [--L-m <m> --L-f <m> --V-m <m/s> --V-f <m/s> --a-m <m/s> --a-f <m/s>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--re-m` | Model Reynolds number | dimensionless, \(> 0\) | Optional; required on the number path |
| `--re-f` | Full-scale Reynolds number | dimensionless, \(> 0\) | Optional; required on the number path |
| `--mach-m` | Model Mach number | dimensionless, \(> 0\) | Optional; required on the number path |
| `--mach-f` | Full-scale Mach number | dimensionless, \(> 0\) | Optional; required on the number path |
| `--L-m` | Model reference length | m, \(> 0\) | Optional; required on the flow path |
| `--L-f` | Full-scale reference length | m, \(> 0\) | Optional; required on the flow path |
| `--V-m` | Model speed | m/s, \(> 0\) | Optional; required on the flow path |
| `--V-f` | Full-scale speed | m/s, \(> 0\) | Optional; required on the flow path |
| `--a-m` | Model speed of sound | m/s, \(> 0\) | Optional; required on the flow path |
| `--a-f` | Full-scale speed of sound | m/s, \(> 0\) | Optional; required on the flow path |
| `--rho-m` | Model density | kg/m³, \(> 0\) | Optional; required with `--mu-m` |
| `--rho-f` | Full-scale density | kg/m³, \(> 0\) | Optional; required with `--mu-f` |
| `--mu-m` | Model viscosity | Pa·s, \(> 0\) | Optional; or `--nu-m` |
| `--mu-f` | Full-scale viscosity | Pa·s, \(> 0\) | Optional; or `--nu-f` |
| `--nu-m` | Model kinematic viscosity | m²/s, \(> 0\) | Optional; or `--mu-m` |
| `--nu-f` | Full-scale kinematic viscosity | m²/s, \(> 0\) | Optional; or `--mu-f` |
| `--q-m` | Model dynamic pressure | Pa, \(> 0\) | Optional |
| `--q-f` | Full-scale dynamic pressure | Pa, \(> 0\) | Optional |
| `--force-m` | Measured model force | N | Optional |
| `--moment-m` | Measured model moment | N·m | Optional |
| `--S-m` | Model reference area | m², \(> 0\) | Optional; required with a load |
| `--S-f` | Full-scale reference area | m², \(> 0\) | Optional; required with a load |
| `--c-m` | Model reference chord | m, \(> 0\) | Optional; required with `--moment-m` |
| `--c-f` | Full-scale reference chord | m, \(> 0\) | Optional; required with `--moment-m` |
| `--out` | PNG path | file | Optional |
