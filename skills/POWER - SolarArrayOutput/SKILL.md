---
name: POWER - SolarArrayOutput
description: >-
  Run the solar-array output program and report its printed results and optional
  PNG. Use when the user wants flat-plate spacecraft solar-array instantaneous
  beginning-of-life power, end-of-life power, orbit-average power with eclipse
  fraction, or a cosine-law power-versus-sun-angle figure. Do not redraw the
  plot or recompute the numbers by hand.
---

# POWER - SolarArrayOutput

Use this skill for flat-plate spacecraft solar-array electrical power. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand.

Ideal packed power at normal incidence is `solar_array_ideal_power`:

\[
P_{0} = S A \eta F_{\mathrm{p}}
\]

Instantaneous beginning-of-life power is `solar_array_bol_power`:

\[
P_{\mathrm{BOL}} = S A \eta F_{\mathrm{p}} I_{\mathrm{d}}\cos\theta
\]

or `solar_array_bol_power_from_specific` when BOL specific power \(p_{\mathrm{sa}}\) replaces \(S\eta F_{\mathrm{p}}\). Life remaining is `solar_array_life_degradation`, \(L_{\mathrm{d}}=(1-d)^{L}\). End-of-life power is `solar_array_eol_power`, \(P_{\mathrm{EOL}}=P_{\mathrm{BOL}}L_{\mathrm{d}}\). Orbit-average power is `solar_array_orbit_average_power`, \(P_{\mathrm{avg}}=P(1-f_{\mathrm{e}})\), with constant sunlit power and zero in eclipse. Optional circular-orbit eclipse fraction is `circular_orbit_eclipse_fraction` under a cylindrical umbra. Incident irradiance is `flat_plate_solar_irradiance`, \(G=S\cos\theta\).

The default solar constant is \(S=1361.6\,\mathrm{W/m}^{2}\) at 1 AU. Edge effects beyond about \(40^\circ\), temperature, albedo, and penumbra are omitted.

## When to run

1. Use this skill when the user wants solar-array BOL power, EOL power, orbit-average power, or a cosine-law power-versus-angle figure.
2. Convert inputs to SI before the call (m², W/m², rad, year). State the converted units in the reply. Do not invent area, efficiency, specific power, incidence angle, packing, inherent degradation, life rate, years, or eclipse inputs.
3. Pass `--area` and `--incidence`. Pass exactly one of `--efficiency` or `--specific-power`.
4. Pass `--packing` only with `--efficiency`. Omit it (default 1) or leave it at 1 with `--specific-power`.
5. Pass `--inherent`, `--life-degradation`, and `--years` when the user gave them. Defaults are \(I_{\mathrm{d}}=1\), \(d=0\), \(L=0\).
6. Pass `--solar-constant` only when the user gave irradiance at the orbit. Otherwise leave the 1 AU default.
7. For orbit-average power with eclipse: pass `--eclipse-fraction`, or pass circular-orbit radius from `ASTRO - OrbitalParameters` as `--a` (or `--alt` with optional `--R0`) together with `--beta`. Do not pass both fraction and orbit inputs.
8. Pass `--out` only when the user wants the PNG of power versus sun angle. Do not invent a plot path when they did not ask for a figure.
9. Do not use this skill for body-mounted multi-face averages, concentrators, detailed radiation-fluence cell tables, or battery sizing. For battery usable energy, eclipse fit, and required capacity, use `POWER - BatteryEnergyBudget` with this skill’s orbit-average power as `--p-avg` when needed.

## Flags

Run:

```text
python "skills/POWER - SolarArrayOutput/solar_array_output.py" --area <m^2> --incidence <rad> (--efficiency <eta> | --specific-power <W/m^2>) [--solar-constant <W/m^2>] [--packing <Fp>] [--inherent <Id>] [--life-degradation <d>] [--years <L>] [--eclipse-fraction <fe> | --a <m> --beta <rad> | --alt <m> --beta <rad>] [--R0 <m>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--area` | Array substrate area \(A\) | m², \(> 0\) | Required |
| `--incidence` | Sun incidence angle \(\theta\) from the plate normal | rad | Required |
| `--efficiency` | Cell conversion efficiency \(\eta\) | dimensionless, \(0 < \eta \le 1\) | One of `--efficiency` or `--specific-power` |
| `--specific-power` | BOL specific power before inherent degradation \(p_{\mathrm{sa}}\) | W/m², \(> 0\) | One of `--efficiency` or `--specific-power` |
| `--solar-constant` | Solar irradiance \(S\) at the orbit, normal to the Sun | W/m², \(> 0\) | Optional. Default \(1361.6\) |
| `--packing` | Packing factor \(F_{\mathrm{p}}\) | dimensionless, \(0 < F_{\mathrm{p}} \le 1\) | Optional with `--efficiency`. Default 1 |
| `--inherent` | Inherent degradation \(I_{\mathrm{d}}\) | dimensionless, \(0 < I_{\mathrm{d}} \le 1\) | Optional. Default 1 |
| `--life-degradation` | Fractional degradation per year \(d\) | 1/year, \(0 \le d < 1\) | Optional. Default 0 |
| `--years` | Mission life \(L\) | year, \(\ge 0\) | Optional. Default 0 |
| `--eclipse-fraction` | Eclipse time fraction \(f_{\mathrm{e}}\) | dimensionless, \(0 \le f_{\mathrm{e}} < 1\) | Optional. Not with orbit inputs |
| `--a` | Circular-orbit radius from planet center | m, \(> R_0\) | Optional with `--beta`. From OrbitalParameters |
| `--alt` | Circular-orbit geometric altitude | m, \(\ge 0\) | Optional with `--beta` instead of `--a` |
| `--R0` | Planet radius | m, \(> 0\) | Optional. Default WGS 84 \(6.378137\times 10^{6}\) |
| `--beta` | Orbit beta angle | rad | With `--a` or `--alt` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare length is metres. Kilometres use `1 km = 1000 m`. Incidence and beta in degrees use \(\pi/180\). Area in cm² uses `1 cm² = 1e-4 m²`. Solar constant or specific power in mW/cm² uses `1 mW/cm² = 10 W/m²`.

When `--out` is passed, the program writes one PNG. The plot title is `Solar array output`. The curves are \(P_{\mathrm{BOL}}\) and \(P_{\mathrm{EOL}}\) versus sun incidence angle for the fixed array (flat-plate cosine law only). Markers are the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `power_source`: `efficiency` or `specific_power`.
4. Report `A_m2`, `S_W_m2`, `theta_rad`, `theta_deg`, `G_W_m2`, `Fp`, `Id`, `P0_W`, `P_BOL_W`, `Ld`, `P_EOL_W`, `fe`, `P_avg_BOL_W`, and `P_avg_EOL_W`.
5. Report `eta` or `psa_W_m2` according to the path used. Report `d_per_year` and `L_year`.
6. Report `eclipse_source`: `input`, `orbit`, or `none`. When `none`, include the printed warning that orbit-average equals instantaneous sunlit power.
7. Report `r_m`, `re_m`, `beta_rad`, and `beta_deg` when the orbit eclipse path was used.
8. If area, incidence, or a power path is missing, say so. Do not fill them in.
