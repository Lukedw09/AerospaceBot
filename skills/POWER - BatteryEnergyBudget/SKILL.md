---
name: POWER - BatteryEnergyBudget
description: >-
  Run the spacecraft battery energy-budget program and report its printed
  results and optional PNG. Use when the user wants usable battery energy from
  nameplate capacity and depth of discharge, time at a continuous load, whether
  an eclipse or peak pulse fits, required capacity from load and eclipse
  duration, or a one-orbit state-of-charge figure with optional solar
  orbit-average power from POWER - SolarArrayOutput. Do not redraw the plot or
  recompute the numbers by hand.
---

# POWER - BatteryEnergyBudget

Use this skill for a spacecraft battery energy budget with depth of discharge and charge/discharge efficiencies. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand. Eclipse load and duration may come from `POWER - DutyCycleLoad` (`P_eclipse_W` as `--load`, `t_eclipse_s` as `--eclipse`).

Nameplate energy from ampere-hours is `battery_energy_from_capacity_ah`:

\[
E = 3600\, C_{\mathrm{Ah}} V
\]

Usable energy at the load is `battery_usable_energy`:

\[
E_{\mathrm{u}} = E\,\mathrm{DOD}\,\eta_d
\]

Time at continuous load is `battery_time_at_continuous_load`, \(t=E_{\mathrm{u}}/P\). Chemical energy removed for an eclipse or peak is `battery_discharge_energy`, \(E_s=P t_e/\eta_d\). Required nameplate energy is `battery_required_nameplate_energy`, \(E_{\mathrm{req}}=P t_e/(\eta_d\,\mathrm{DOD})\). With bus voltage, required ampere-hours are `battery_required_capacity_ah`. Recharge uses `battery_charge_energy` and `battery_recharge_power`. Sunlit array power that closes the orbit energy balance is `battery_orbit_source_power`. Surplus sunlit power charges the battery. If that sunlit power is below the load, the battery covers the difference and `balance_margin_J` includes it.

This skill does not model cell electrochemistry, thermal runaway, or Peukert beyond the single charge and discharge efficiency factors supplied. The printed `warning` states that limit.

## When to run

1. Use this skill when the user wants usable battery energy, time at load, eclipse or peak fit, required capacity for a load and eclipse, orbit energy balance with solar array power, or a SoC-versus-time figure.
2. Convert inputs to SI before the call (W, s, V). Nameplate energy may be given as watt-hours (`--energy`) or as ampere-hours with bus voltage (`--ah` and `--voltage`). State the converted units in the reply. Do not invent capacity, DoD, efficiencies, load, eclipse, or solar power.
3. Always pass `--dod`, `--eta-c`, and `--eta-d`.
4. Pass exactly one capacity path: `--energy`, or `--ah` with `--voltage`. Omit both only when sizing required capacity from `--load` and an eclipse duration.
5. Pass `--load` for continuous-load time and for eclipse/peak checks. Pass `--eclipse`, or `--eclipse-fraction` with `--orbit` or `--day`, when an eclipse interval is known.
6. For orbit balance or the SoC PNG, pass sunlit duration as `--day`, or `--orbit` with `--eclipse` / `--eclipse-fraction`. Pass `--p-avg` only when the user has orbit-average array power from `POWER - SolarArrayOutput` (or an equivalent).
7. Pass `--peak` and `--peak-duration` together when a peak pulse is stated. Peak duration must not exceed the eclipse when a SoC orbit is built.
8. Pass `--out` only when the user wants the PNG of state of charge versus time for one orbit.
9. Do not use this skill for cell-level electrochemistry, thermal runaway, or Peukert rate equations beyond the supplied efficiencies. Do not use `POWER - SolarArrayOutput` alone for battery sizing.

## Flags

Run:

```text
python "skills/POWER - BatteryEnergyBudget/battery_energy_budget.py" --dod <DOD> --eta-c <eta_c> --eta-d <eta_d> (--energy <W·h> | --ah <A·h> --voltage <V> | --load <W> with eclipse timing) [--load <W>] [--eclipse <s>] [--day <s>] [--orbit <s>] [--eclipse-fraction <fe>] [--peak <W> --peak-duration <s>] [--p-avg <W>] [--voltage <V>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--dod` | Allowed depth of discharge \(\mathrm{DOD}\) | dimensionless, \(0 < \mathrm{DOD} \le 1\) | Required |
| `--eta-c` | Charge (charger) efficiency \(\eta_c\) | dimensionless, \(0 < \eta_c \le 1\) | Required |
| `--eta-d` | Discharge efficiency \(\eta_d\) | dimensionless, \(0 < \eta_d \le 1\) | Required |
| `--energy` | Nameplate energy | W·h, \(> 0\) | One capacity path, or omit when sizing |
| `--ah` | Nameplate ampere-hour capacity | A·h, \(> 0\) | With `--voltage`; not with `--energy` |
| `--voltage` | Bus or average discharge voltage \(V\) | V, \(> 0\) | With `--ah`; optional with `--energy` or sizing for Ah |
| `--load` | Continuous load \(P\) | W, \(> 0\) | For time-at-load, fit, sizing, orbit |
| `--eclipse` | Eclipse duration \(t_e\) | s, \(> 0\) | Optional; or use fraction with period |
| `--day` | Sunlit duration \(t_d\) | s, \(> 0\) | Optional with eclipse for orbit |
| `--orbit` | Orbit period \(T\) | s, \(> 0\) | Optional with eclipse or fraction |
| `--eclipse-fraction` | Eclipse fraction \(f_{\mathrm{e}}\) | dimensionless, \(0 \le f_{\mathrm{e}} < 1\) | Optional |
| `--peak` | Peak load power | W, \(> 0\) | With `--peak-duration` |
| `--peak-duration` | Peak duration | s, \(> 0\) | With `--peak` |
| `--p-avg` | Orbit-average array power from SolarArrayOutput | W, \(\ge 0\) | Optional |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

Watt-hours to joules use \(1\,\mathrm{W\cdot h}=3600\,\mathrm{J}\). Minutes use \(1\,\mathrm{min}=60\,\mathrm{s}\).

When `--out` is passed, the program writes one PNG. The plot title is `Battery energy budget`. The curve is state of charge versus time from eclipse entry over one orbit. The dashed line is the \(1-\mathrm{DOD}\) floor. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `DOD`, `eta_c`, `eta_d`, `E_J` / `E_Wh`, `Eu_J` / `Eu_Wh`, and `capacity_source`.
4. Report `P_W`, `t_load_s`, `te_s`, `Es_J`, `DOD_achieved`, and `eclipse_fits` when they are printed.
5. Report `Ereq_J` / `Ereq_Wh` and `C_Ah_req` when sizing without a stated capacity.
6. Report `P_peak_W`, `t_peak_s`, `E_peak_J`, and `peak_fits` when a peak was given.
7. Report `Ec_J`, `PR_W`, `Psa_req_W`, `Pavg_req_W`, `Pavg_W`, `Psa_W`, `energy_balance`, `balance_margin_J`, `SoC_min`, and `SoC_end` when orbit timing was used.
8. Include the printed `warning` about omitted electrochemistry and Peukert.
9. If DoD, efficiencies, or a capacity/sizing path is missing, say so. Do not fill them in.
