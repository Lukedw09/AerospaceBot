---
name: ROCKET - NozzleChamberDesignLab
description: >-
  Bake an interactive 2D nozzle and chamber design page. Use only when
  the user explicitly asks for this lab, the interactive HTML designer,
  or a live slider view of a conical or bell-length nozzle and chamber.
  Do not run it just because an engine is being sized.
---

# ROCKET - NozzleChamberDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `ROCKET - NozzleChamberDesignLab`, or they clearly ask for the interactive HTML page, the live nozzle–chamber designer, or a design view with sliders. Do not run it because an engine-sizing conversation is underway. Do not run it from another rocket skill unless they explicitly said yes to that offer.

The program writes a PNG of the opening meridional section and a self-contained HTML page. The page recomputes geometry and coefficients in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. After they change the page, use the export block with the one-shot rocket skills if they want those programs quoted. This lab does not replace that CLI chain.

Gas properties come from the frozen CEA tables in `ROCKET - PerformanceParameters` (nearest table pressure, tie to the higher pressure, linear mixture ratio, no extrapolation). Default \(\gamma\) is throat gamma. A manual \(\gamma\) or \(c^{*}\) overrides the table. The nozzle is the isentropic Area-Mach relation. Delivered \(c^{*}\) and \(C_F\) use `--eta-cstar` and `--eta-cf` (default 1). Ambient pressure is always part of the design; the default seed is sea level, `101325` Pa. Pass `--pa 0` for vacuum. The divergent wall is a conical length-fraction surrogate, not a Rao bell. The convergent half-angle is fixed at \(30^\circ\). A blank chamber radius in the page means \(2.5\) throat radii.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before the call (Pa, N, m, rad). State the converted units in the reply. Half-angle is radians on the CLI; the page shows degrees.
3. Pass only flags the user supplied. Omitted flags keep the program defaults: LOX/RP-1, mixture ratio 2.3, chamber pressure \(2\,\mathrm{MPa}\), area ratio 5, ambient \(101325\,\mathrm{Pa}\), thrust \(10\,\mathrm{kN}\), \(L^{*}=1\,\mathrm{m}\), half-angle \(15^\circ\), length fraction 0.8, case thickness \(2\,\mathrm{mm}\), allowable stress \(250\,\mathrm{MPa}\), nozzle wall \(2\,\mathrm{mm}\) at \(8000\,\mathrm{kg/m^3}\), efficiencies 1, and Summerfield \(k_{\mathrm{sep}}=0.4\).
4. Pass `--pe` instead of `--epsilon` when they give an exit pressure. Do not pass both.
5. Pass `--gamma` or `--cstar` only when they override the frozen table.
6. Pass `--open` only when they ask to open the HTML file.
7. In the reply, state every assumption the user did not supply. Nozzle mass is the divergent shell only, from `nozzle_wall_m` and `rho_mat_kg_m3`. Unless they set those, say the wall is an assumed 2 mm at an assumed 8000 kg/m³, not a named material. Also state any unused-by-the-user defaults for case thickness, allowable stress, chamber radius, the fixed 30° convergent, the length-fraction cone, efficiencies, \(k_{\mathrm{sep}}\), and ambient pressure.

## Flags

Run:

```text
python "skills/ROCKET - NozzleChamberDesignLab/nozzle_chamber_lab.py" [--pair <ox/fuel>] [--of <r>] [--pc <Pa>] [--epsilon <e> | --pe <Pa>] [--pa <Pa>] [--thrust <N>] [--lstar <m>] [--chamber-radius <m>] [--thickness <m>] [--allowable <Pa>] [--half-angle <rad>] [--length-fraction <f>] [--eta-cstar <eta>] [--eta-cf <eta>] [--wall-thickness <m>] [--rho-mat <kg/m^3>] [--k-sep <k>] [--gamma <k>] [--cstar <m/s>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pair` | Frozen CEA propellant pair | ox/fuel | Optional |
| `--of` | Mixture ratio | dimensionless | Optional |
| `--pc` | Chamber pressure | Pa | Optional |
| `--epsilon` | Design area ratio | dimensionless | Optional |
| `--pe` | Design exit pressure | Pa | Optional |
| `--pa` | Ambient pressure | Pa | Optional |
| `--thrust` | Design thrust | N | Optional |
| `--lstar` | Characteristic length | m | Optional |
| `--chamber-radius` | Chamber radius; omitted uses \(2.5 R_t\) | m | Optional |
| `--thickness` | Case wall thickness | m | Optional |
| `--allowable` | Allowable case stress | Pa | Optional |
| `--half-angle` | Divergent reference half-angle | rad | Optional |
| `--length-fraction` | Divergent length over a full cone | dimensionless | Optional |
| `--eta-cstar` | \(c^{*}\) efficiency product | dimensionless | Optional |
| `--eta-cf` | Thrust-coefficient efficiency product | dimensionless | Optional |
| `--wall-thickness` | Nozzle wall thickness | m | Optional |
| `--rho-mat` | Nozzle material density | kg/m³ | Optional |
| `--k-sep` | Summerfield separation ratio | dimensionless | Optional |
| `--gamma` | Manual gamma override | dimensionless | Optional |
| `--cstar` | Manual \(c^{*}\) override | m/s | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. In the same reply, state every design assumption the user did not supply. Do not present those values as measured, and do not imply the propellant chose them. Name each one in plain language:
   - Nozzle mass is only the divergent shell. It uses `nozzle_wall_m` and `rho_mat_kg_m3`. Unless the user set them, say the wall is an assumed \(2\,\mathrm{mm}\) at an assumed \(8000\,\mathrm{kg/m^3}\) (about steel), not a named alloy.
   - Case hoop stress uses `case_thickness_m` and `allowable_Pa` (default \(2\,\mathrm{mm}\) and \(250\,\mathrm{MPa}\)). That thickness is not the nozzle wall, and the case mass is not in `m_nozzle_kg`.
   - Chamber radius is \(2.5 R_t\) when `chamber_radius_source` is `default_2.5_Rt`.
   - The convergent half-angle is fixed at \(30^\circ\). The divergent wall is a length-fraction cone, not a Rao bell.
   - Omitted efficiencies stay 1. Omitted `k_sep` stays 0.4. Omitted ambient pressure stays sea level, \(101325\,\mathrm{Pa}\).
3. Include the PNG. Give `viewer:` as a markdown link.
4. Tell them the page is where to change chamber pressure, area ratio, half-angle, length fraction, ambient pressure, wall thickness, material density, and the other inputs, and that the section and the coefficients update immediately.
5. If ambient thrust is `invalid_separated`, say the throat was sized on vacuum thrust.
6. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.
