---
name: ROCKET - TankStructureMass
description: >-
  Run the tank-and-structure mass program and report its printed results. Use
  when the user wants tank shell mass, structure mass, residual propellant, or
  an inert-mass breakdown from propellant volume, MEOP, material allowables,
  and residuals fraction, for use as PayloadtoDeltaV inert. Do not recompute
  the numbers by hand.
---

# ROCKET - TankStructureMass

Use this skill for tank and structure inert mass from propellant volume. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Loaded propellant mass is \(m_{\mathrm{loaded}}=\rho V_p\). Residuals fraction \(f_r\) is of that loaded mass: \(m_{\mathrm{residual}}=f_r m_{\mathrm{loaded}}\) and usable propellant \(m_p=(1-f_r)m_{\mathrm{loaded}}\). Design pressure is \(p=f_{\mathrm{design}}\times\mathrm{MEOP}\) with default \(f_{\mathrm{design}}=1\) (MEOP used directly; the program does not invent a burst factor). Spherical membrane thickness is \(t=p R/(2 S\eta)\) with \(R=(3V_p/(4\pi))^{1/3}\). For a cylinder, barrel hoop thickness is \(t_{\mathrm{barrel}}=p R/(S\eta)\) with barrel length \(L=V_p/(\pi R^{2})\), and each flat head uses the integral plate formula \(t_{\mathrm{head}}=R\sqrt{p/(S\eta)}\) (ASME UG-34 with \(C=0.25\) on diameter). The program refuses when the governing \(t/R\ge 0.1\). Tank shell mass includes optional `--boss-factor`. Structure mass is `--structure` kg or `--structure-factor` times the tank shell. Total inert is

\[
m_{\mathrm{inert}}=m_{\mathrm{tank}}+m_{\mathrm{structure}}+m_{\mathrm{residual}}
\]

`payload_to_deltav_mp_kg` and `payload_to_deltav_inert_kg` are the `mp` and `inert` values for `ROCKET - PayloadtoDeltaV` (residual propellant is part of inert). Volume is treated as tank internal volume; there is no separate ullage model—fold ullage into `--volume` when the user gives it that way.

## When to run

1. Use this skill when the user wants tank shell mass, structure mass, residual mass, or an inert breakdown from propellant volume, MEOP, material allowables, and residuals fraction, especially to feed `ROCKET - PayloadtoDeltaV`.
2. Convert all inputs to SI before the call (m³, kg/m³, Pa). State the converted units in the reply. Do not invent volume, density, residuals fraction, MEOP, allowable stress, or material density.
3. Pass `--volume`, `--rho`, `--residuals`, `--meop`, `--allowable`, and `--rho-mat`.
4. Pass `--shape cylinder` with `--radius` only when the user specifies a cylindrical tank. Default shape is `sphere` (no `--radius`).
5. Pass `--design-factor` only when the user gives a factor on MEOP (burst or design). Omit it to use MEOP as the design pressure.
6. Pass `--structure` or `--structure-factor` only when the user gives additional structure beyond the tank shell. Do not invent skirts, bosses, or intertank mass. `--boss-factor` is only for a stated boss/weld multiplier on the shell.
7. Pass `--eta` only when the user gives weld efficiency. Default is 1.
8. Point propellant volume from mass flow and burn time to `ROCKET - PropellantLoad` first when that is how volume was obtained. Point hoop stress of a known thickness case to `ROCKET - ChamberVolumeAndCaseHoopStress`.
9. Interactive lab offer: before running this program for a new feed, injector, pump, blowdown, tank, or propellant-load design or sizing thread, ask once whether the user wants `ROCKET - FeedTankDesignLab` (interactive 2D HTML) instead of or before this one-shot CLI. Ask only when they are designing, sizing, or trading parameters. Do not ask for a single named number, a formula identity, or a clear request to run this CLI only. If they decline, or ignore the offer and continue with this CLI, do not offer the lab again for 4 hours in this conversation. Say once that you will not offer the lab again for a while, then run this program. Do not run the lab unless they explicitly say yes. A new chat, or about 4 hours later, may offer once again.

## Flags

Run:

```text
python "skills/ROCKET - TankStructureMass/tank_structure_mass.py" --volume <m^3> --rho <kg/m^3> --residuals <f_r> --meop <Pa> --allowable <Pa> --rho-mat <kg/m^3> [--shape sphere|cylinder] [--radius <m>] [--eta <eta>] [--design-factor <f>] [--boss-factor <f>] [--structure <kg> | --structure-factor <f>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--volume` | Loaded propellant (tank internal) volume \(V_p\) | m³, \(> 0\) | Required |
| `--rho` | Propellant density \(\rho\) | kg/m³, \(> 0\) | Required |
| `--residuals` | Residuals fraction \(f_r=m_{\mathrm{residual}}/m_{\mathrm{loaded}}\) | dimensionless, \(0\le f_r<1\) | Required |
| `--meop` | Maximum expected operating pressure | Pa, \(> 0\) | Required |
| `--allowable` | Material allowable stress \(S\) | Pa, \(> 0\) | Required |
| `--rho-mat` | Tank material density | kg/m³, \(> 0\) | Required |
| `--shape` | `sphere` (default) or `cylinder` | — | Optional |
| `--radius` | Inner radius \(R\) | m, \(> 0\) | Required for `cylinder` |
| `--eta` | Weld efficiency \(\eta\) | dimensionless, \(0<\eta\le 1\) | Optional; default 1 |
| `--design-factor` | Multiplies MEOP to design pressure | dimensionless, \(> 0\) | Optional; default 1 |
| `--boss-factor` | Multiplies tank shell mass | dimensionless, \(> 0\) | Optional; default 1 |
| `--structure` | Additional structure mass | kg, \(\ge 0\) | Optional; or `--structure-factor` |
| `--structure-factor` | Additional structure as a factor of tank shell | dimensionless, \(\ge 0\) | Optional; or `--structure` |

A bare pressure is pascals. Use `p_Pa = p_bar * 1e5`, `1 atm = 101325 Pa`, `1 psi = 6894.757293168361 Pa`, and `1 MPa = 1e6 Pa`. Volume in litres uses `1 L = 0.001 m³`. Mass in pounds-mass uses `1 lbm = 0.45359237 kg`. Density in g/cm³ uses `1 g/cm³ = 1000 kg/m³`. Length in inches uses `1 in = 0.0254 m`.

If the user gives MEOP and a separate design or burst factor, pass `--meop` and `--design-factor`, or pass their product as `--meop` with factor omitted (and say which). If they give one pressure and no factor, pass that pressure as `--meop`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report `V_p_m3`, `rho_kg_m3`, `residuals_fraction`, `MEOP_Pa`, `design_factor`, `p_design_Pa`, `allowable_Pa`, and `rho_mat_kg_m3`.
3. Report `shape`, `R_m`, `t_m`, `t_over_R`, and `thin_wall`. Report `L_m`, `t_barrel_m`, `t_head_m`, and `flat_head_C` for a cylinder. `t_m` is the governing thickness (max of barrel and head). `thin_wall` is `yes` when governing \(t/R < 0.1\); the program errors instead of printing a mass when \(t/R \ge 0.1\).
4. Report the mass breakdown: `m_loaded_kg`, `m_usable_kg`, `m_residual_kg`, `m_tank_kg`, `m_structure_kg`, `structure_source`, and `m_inert_kg`.
5. Report `payload_to_deltav_mp_kg`, `payload_to_deltav_inert_kg`, and `payload_to_deltav_stage`. Those are the usable propellant and inert (including residual) for `ROCKET - PayloadtoDeltaV`.
6. State that design pressure was not given an invented burst factor inside the program, and that residual propellant is counted in inert, not in usable \(m_p\).
7. If volume, density, residuals fraction, MEOP, allowable stress, or material density is missing, say so. Do not fill them in.
8. For a pressure-fed tank, `meop_Pa` from `ROCKET - FeedSystemPressureBudget` can be passed as `--meop`. Do not use that supply pressure as the MEOP of a pump-fed tank.
