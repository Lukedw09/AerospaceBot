---
name: ROCKET - SolidMotorGrainLab
description: >-
  Bake an interactive solid-motor grain page. Use only when the user
  explicitly asks for this lab, the interactive HTML grain designer, or a
  live slider view of a circular-port grain with chamber pressure, burn
  area, and case margin. Do not run it just because a solid motor is
  being sized.
---

# ROCKET - SolidMotorGrainLab

Run this program only when the user explicitly asks for this lab. That means they name `ROCKET - SolidMotorGrainLab`, or they clearly ask for the interactive HTML page, the live grain designer, or a design view with sliders. Do not run it because a solid-motor conversation is underway. Do not run it from another rocket skill unless they explicitly said yes to that offer.

The program writes a PNG of the opening sections and histories and a self-contained HTML page. The page recomputes in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. After they change the page, use the export block with the one-shot rocket skills if they want those programs quoted. This lab does not replace that CLI chain.

The grain is an internal-burning circular port with inhibited ends, from `ROCKET - CircularPortGrainHistory`. Saint Robert equilibrium is `ROCKET - SolidMotorParameters`: \(K = A_b/A_t\) and \(p_c = (K\, a\, \rho_b\, c^{*})^{1/(1-n)}\). Kn on the page is that ignition \(K\). Throat area is \(A_t = A_{b0}/\mathrm{Kn}\) with \(A_{b0} = 2\pi R_p L\). Outer radius is \(R_o = R_p + w_0\). Case hoop uses that outer radius as the case radius, \(\sigma_h = p_c R_o / t\), and margin of safety at the peak chamber pressure, from `ROCKET - ChamberVolumeAndCaseHoopStress`. The two sections draw ignition geometry. The curves are \(p_c(t)\) and \(A_b(t)\). Residual web and margin stay in the readout. Erosive burning is omitted. \(a\), \(n\), \(\rho_b\), and \(c^{*}\) are inputs.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before the call (m, m², Pa, kg/m³, m/s, and \(a\) in m/(s·Pa\(^{n}\))). State the converted units in the reply. Kn is dimensionless.
3. Pass only flags the user supplied. Omitted flags keep the program defaults: web \(0.08\,\mathrm{m}\), port radius \(0.05\,\mathrm{m}\), length \(1\,\mathrm{m}\), Kn \(120\), \(n = 0.5\), density \(1800\,\mathrm{kg/m^3}\), \(c^{*} = 1550\,\mathrm{m/s}\), wall thickness \(0.008\,\mathrm{m}\), allowable stress \(2.5\times 10^{8}\,\mathrm{Pa}\), sliver \(0\). The coefficient \(a\) is about \(3.78\times 10^{-6}\,\mathrm{m/(s\cdot Pa^{0.5})}\), chosen so that default grain burns for \(10\,\mathrm{s}\).
4. Pass `--open` only when they ask to open the HTML file.
5. In the reply, state every assumption the user did not supply. Unless they set them, say \(a\), \(n\), \(\rho_b\), and \(c^{*}\) are the seed defaults, not a named propellant. Say the case thickness and allowable stress are defaults when they did not set them. Say the sections are ignition geometry, ends stay inhibited, and erosive burning is omitted. Say hoop stress uses \(R_o\) as the case radius and does not apply a design factor.

## Flags

Run:

```text
python "skills/ROCKET - SolidMotorGrainLab/solid_motor_grain_lab.py" [--web <m>] [--port <m>] [--kn <K>] [--length <m>] [--a <m/(s·Pa^n)>] [--n <n>] [--rho <kg/m^3>] [--cstar <m/s>] [--thickness <m>] [--allowable <Pa>] [--sliver <percent>] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--web` | Initial web \(w_0\) | m | Optional |
| `--port` | Initial port radius \(R_p\) | m | Optional |
| `--kn` | Ignition burning-area ratio \(K_n = A_{b0}/A_t\) | dimensionless | Optional |
| `--length` | Grain length \(L\) | m | Optional |
| `--a` | Burn-rate coefficient \(a\) | m/(s·Pa\(^{n}\)) | Optional |
| `--n` | Burn-rate pressure exponent \(n\) | dimensionless, \(< 1\) | Optional |
| `--rho` | Solid propellant density \(\rho_b\) | kg/m³ | Optional |
| `--cstar` | Characteristic velocity \(c^{*}\) | m/s | Optional |
| `--thickness` | Case wall thickness \(t\) | m | Optional |
| `--allowable` | Allowable case stress | Pa | Optional |
| `--sliver` | Sliver volume percent | percent, \([0, 100)\) | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

The coefficient \(a\) must match pressure in pascals. If the user gives \(a\) for \(p\) in MPa or psi, convert \(a\) so that \(r = a p_c^{n}\) is consistent with \(p_c\) in Pa before the call.

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. In the same reply, state every design assumption the user did not supply. Do not present those values as measured, and do not imply a propellant chose them.
3. Include the PNG. Give `viewer:` as a markdown link. The figure is the lateral section, the longitudinal section, \(p_c(t)\), and \(A_b(t)\).
4. Tell them the page is where to change web, port radius, Kn, and the other inputs, and that the sections and the two curves update immediately. Residual web and case margin stay in the readout.
5. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.
