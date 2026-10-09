---
name: AERO - CompressibleFlowDesignLab
description: >-
  Bake an interactive compressible-flow classroom page. Use only when the
  user explicitly asks for this lab, the interactive HTML designer, or a
  live view of isentropic flow, shocks, a diamond airfoil, Fanno or Rayleigh
  flow, Prandtl-Glauert, or a pitot Mach. Do not run it just because a
  compressible-flow number is being computed.
---

# AERO - CompressibleFlowDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `AERO - CompressibleFlowDesignLab`, or they clearly ask for the interactive HTML page, the live compressible-flow classroom, or a design view with a mode selector. Do not run it because a shock, duct, or Mach-number conversation is underway. Do not run it from another aero skill unless they explicitly said yes to that offer.

The program writes a PNG of the opening picture and a self-contained HTML page. The page recomputes in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. After they change the page, use the export block with the one-shot skill named there. This lab does not replace those programs.

Modes are `isentropic`, `normal`, `wedge`, `cone`, `diamond`, `fanno`, `rayleigh`, `prandtl_glauert`, and `rayleigh_pitot`. The wedge, cone, and diamond pictures are the wave sketch. Normal shock is a constant-area duct with the jump drawn on the shock. Fanno, Rayleigh, and the normal-shock duct draw contours of the stream function. Those contours stay equally spaced because \(\rho V\) is constant along a constant-area duct. The ratio curves still show \(V/V^*\).

Prandtl–Glauert on this page uses the user-coefficient path only. It does not load a NACA Report 824 chart. Drag is not divided by \(\beta\).

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before the call. State the converted units in the reply. Angles are radians on the CLI. The page shows degrees.
3. Pass only flags the user supplied. Omitted flags keep the program defaults: wedge mode, Mach 2, deflection \(10^\circ\), diamond half-angle \(5^\circ\), angle of attack \(2^\circ\), \(\gamma = 1.4\), Prandtl–Glauert coefficients \(C_{L0}=0.5\), \(c_{m0}=-0.05\), \(c_{d0}=0.02\), \(C_{p0,\min}=-0.8\), and a pitot pair that recovers Mach 2 at \(101325\,\mathrm{Pa}\) static pressure. Fanno \(4fL/D\) and Rayleigh \(T_{t2}/T_{t1}\) stay omitted unless passed.
4. Pass `--open` only when they ask to open the HTML file.
5. In the reply, state every assumption the user did not supply, including the mode when they did not name one. Say that the duct lines are contours of the stream function and that equal spacing is the constant mass flux \(\rho V\). On `prandtl_glauert`, say the coefficients are the user values and drag is not divided by \(\beta\).

## Flags

Run:

```text
python "skills/AERO - CompressibleFlowDesignLab/compressible_flow_lab.py" [--mode isentropic|normal|wedge|cone|diamond|fanno|rayleigh|prandtl_glauert|rayleigh_pitot] [--mach <M>] [--delta <rad>] [--epsilon <rad>] [--alpha <rad>] [--gamma <k>] [--fld <4fL/D>] [--tt-ratio <Tt2/Tt1>] [--cl-inc <CL0>] [--cm-inc <Cm0>] [--cd-inc <Cd0>] [--cpmin-inc <Cp0min>] [--pitot <Pa>] [--static <Pa>] [--temperature <K>] [--pressure <Pa>] [--density <kg/m^3>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--mode` | Which picture opens | — | Optional |
| `--mach` | Freestream or station Mach | dimensionless | Optional |
| `--delta` | Wedge or cone angle | rad | Optional |
| `--epsilon` | Diamond half-angle | rad | Optional |
| `--alpha` | Diamond angle of attack | rad | Optional |
| `--gamma` | Ratio of specific heats | dimensionless, \(> 1\) | Optional |
| `--fld` | Fanno \(4fL/D\) | dimensionless, \(\ge 0\) | Optional |
| `--tt-ratio` | Rayleigh \(T_{t2}/T_{t1}\) | dimensionless, \(> 0\) | Optional |
| `--cl-inc` | Incompressible lift coefficient | — | Optional |
| `--cm-inc` | Incompressible moment coefficient | — | Optional |
| `--cd-inc` | Incompressible drag coefficient | — | Optional |
| `--cpmin-inc` | Incompressible minimum pressure coefficient | — | Optional |
| `--pitot` | Measured pitot pressure | Pa | Optional |
| `--static` | Freestream static pressure | Pa | Optional |
| `--temperature` | Static temperature | K | Optional |
| `--pressure` | Static pressure | Pa | Optional |
| `--density` | Static density | kg/m³ | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

An angle in degrees uses `angle_rad = angle_deg * pi/180`. A bare pressure in psi, or a temperature in °C or °F, is converted before the call.

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. In the same reply, state every assumption the user did not supply. Name the mode. Say the duct lines are contours of the stream function and that equal spacing is the constant mass flux \(\rho V\).
3. On `prandtl_glauert`, state that the coefficients are user inputs and that \(C_d\) is not divided by \(\beta\).
4. Include the PNG. Give `viewer:` as a markdown link.
5. Tell them the page is where to change the mode, Mach, angles, and the mode-specific inputs, and that the picture updates immediately.
6. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.
