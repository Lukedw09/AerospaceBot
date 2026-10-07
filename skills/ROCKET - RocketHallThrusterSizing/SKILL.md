---
name: ROCKET - RocketHallThrusterSizing
description: >-
  Run the Hall-thruster sizing program and report its printed results and
  optional PNG. Use when the user wants thrust, mass flow, input power, and
  ideal singly charged beam current from specific impulse and efficiency,
  given either thrust or power. Do not redraw the plot or recompute the
  numbers by hand.
---

# ROCKET - RocketHallThrusterSizing

Use this skill to size a Hall thruster’s thrust, mass flow, input power, and ideal beam current. It does not replace `ROCKET - ElectricPropulsionDeltaV`, which still owns propellant and burn time for a stated delta-v. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Exhaust speed is \(v_e = I_{sp} g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^{2}\). Power and thrust are `electric_propulsion_power`:

\[
P = \frac{T v_e}{2\eta}.
\]

Mass flow is \(T/v_e\). Ideal singly charged beam current is

\[
I_b = \frac{\eta_u \dot{m}\, e}{m_{\mathrm{ion}}}.
\]

The default ion is xenon at \(2.18\times 10^{-25}\,\mathrm{kg}\). `--utilization` defaults to 1 and is the ionized fraction of the propellant mass flow. There is no magnetic-field topology and no plume divergence.

The figure plots beam current versus thrust at the fixed specific impulse.

## When to run

1. Use this skill when the user wants Hall-thruster thrust, power, mass flow, or ideal beam current.
2. Convert inputs to SI before the call. Do not invent specific impulse, efficiency, thrust, or power.
3. Pass `--isp` and `--eta`. Pass exactly one of `--thrust` or `--power`.
4. Pass `--ion-mass` only when the user named an ion other than xenon. Pass `--utilization` only when the user gave it.
5. Pass `--out` only when the user wants the PNG.
6. Do not use this skill for propellant mass or burn time of a stated delta-v. That is `ROCKET - ElectricPropulsionDeltaV`.

## Flags

Run:

```text
python "skills/ROCKET - RocketHallThrusterSizing/rocket_hall_thruster_sizing.py" --isp <s> --eta <eta> (--thrust <N> | --power <W>) [--ion-mass <kg>] [--utilization <eta_u>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--isp` | Specific impulse | s | Required |
| `--eta` | Thrust efficiency | dimensionless, \((0, 1]\) | Required |
| `--thrust` | Thrust | N | Or `--power` |
| `--power` | Input power | W | Or `--thrust` |
| `--ion-mass` | Ion mass | kg | Optional; default xenon \(2.18\times 10^{-25}\) |
| `--utilization` | Divides the beam current | dimensionless, \((0, 1]\) | Optional; default 1 |
| `--out` | PNG path | — | Optional |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG when `graph:` is printed. The horizontal axis is thrust. The curve is beam current at the fixed specific impulse.
3. Report `ve_m_s`, `thrust_N`, `mdot_kg_s`, `power_W`, and `Ib_A`.
4. Report `ion_mass_kg` and `utilization`.
