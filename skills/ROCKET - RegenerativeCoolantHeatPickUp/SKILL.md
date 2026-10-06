---
name: ROCKET - RegenerativeCoolantHeatPickUp
description: >-
  Run the regenerative-coolant program and report its printed results. Use
  when the user wants coolant outlet temperature, temperature rise, or the
  minimum flow that stays under a bulk-temperature limit. Do not recompute
  the numbers by hand.
---

# ROCKET - RegenerativeCoolantHeatPickUp

Use this skill for the coolant energy balance. Run the program once and quote its stdout. Do not recompute the numbers by hand.

\(\dot{Q} = \dot{m} c_p (T_\mathrm{out} - T_\mathrm{in})\). With `--t-max`, the run reports whether \(T_\mathrm{out}\) is at or below that limit and the minimum flow that holds the limit. SP-125 uses the coolant critical temperature as that limit. Channel geometry and boiling are not evaluated.

## When to run

1. Use this skill when the user asks for regenerative coolant outlet temperature or the flow needed to stay under a bulk limit.
2. Convert all inputs to SI before the call. State the converted units in the reply. Do not invent \(c_p\), inlet temperature, heat rate, or area.
3. Pass `--q-dot`, or both `--flux` and `--area`. Flux can be `ROCKET - ThroatGasSideHeatFlux` `q_dot_W_m2`. Area is the cooled surface the user states.
4. Coolant mass flow can be `ROCKET - PropellantLoad` `mdot_f_kg_s` or `mdot_o_kg_s`, matching the propellant that is the coolant.

## Flags

Run:

```text
python "skills/ROCKET - RegenerativeCoolantHeatPickUp/regenerative_coolant_heat_pickup.py" --mdot <kg/s> --cp <J/(kg·K)> --t-in <K> (--q-dot <W> | --flux <W/m^2> --area <m^2>) [--t-max <K>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mdot` | Coolant mass flow | kg/s | Required |
| `--cp` | Coolant specific heat | J/(kg·K) | Required |
| `--t-in` | Coolant inlet temperature | K | Required |
| `--q-dot` | Absorbed heat rate | W | Or `--flux` and `--area` |
| `--flux` | Heat flux | W/m² | With `--area` |
| `--area` | Cooled area | m² | With `--flux` |
| `--t-max` | Limiting bulk temperature | K | Optional |
| `--out` | PNG of outlet temperature versus mass flow | — | Optional |

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report \(T_\mathrm{out}\) in K, \(\Delta T\) in K, and \(\dot{Q}\) in W.
3. When `--t-max` was passed, report `limit` and `mdot_min_kg_s`.
4. State that the balance does not size cooling channels.
