# Lumped-capacitance transient formulas

Units are SI. Script records use the same style as the FormulaCatalouge: named `expr`, `family`, and `symbols`. The program implements these identities; `--check` exercises the numeric cases in [checks/identities.md](checks/identities.md). Catalogue copies live under `FormulaCatalouge` as the same ids.

Lumped thermal capacitance under convection to a fixed ambient (spatially uniform solid temperature when \(\mathrm{Bi}\ll 1\)) follows NASA Glenn T-MATS 0-D transient conduction and the Bi ≤ 0.1 usage in NASA electric-aircraft thermal notes. When Bi is not small, use distributed transient conduction (Heisler / Biot–Fourier); those charts are not transcribed here.

## Lumped thermal time constant

\[
\tau = \frac{m c}{h A}
\]

```formula
## lumped_thermal_time_constant
family: aerotherm
expr: m*c/(h*A)
symbols: m, c, h, A
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\tau\) | Thermal time constant | s |
| \(m\) | Mass | kg |
| \(c\) | Specific heat | J/(kg·K) |
| \(h\) | Convection coefficient | W/(m²·K) |
| \(A\) | Convecting surface area | m² |

Assumptions: constant properties; lumped solid temperature. Equivalent to \(\rho V c/(h A)\) when \(m=\rho V\). \(m,c,h,A>0\).

## Lumped-capacitance temperature

\[
T(t)-T_{\infty}=(T_i-T_{\infty})\exp(-t/\tau)
\]

```formula
## lumped_capacitance_temperature
family: aerotherm
expr: Tinf + (Ti - Tinf)*exp(-t/tau)
symbols: Tinf, Ti, t, tau
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T(t)\) | Solid temperature at time \(t\) | K |
| \(T_{\infty}\) | Ambient temperature (script `Tinf`) | K |
| \(T_i\) | Initial temperature (script `Ti`) | K |
| \(t\) | Elapsed time | s |
| \(\tau\) | Time constant (script `tau`) | s |

## Lumped-capacitance time to a target temperature

\[
t = -\tau\ln\left(\frac{T-T_{\infty}}{T_i-T_{\infty}}\right)
\]

```formula
## lumped_capacitance_time_to_temperature
family: aerotherm
expr: -tau*log((T - Tinf)/(Ti - Tinf))
symbols: tau, T, Tinf, Ti
```

Assumptions: \(T\) lies between \(T_i\) and \(T_{\infty}\) (inclusive of \(T_i\); exclusive of the \(T=T_{\infty}\) asymptote).

## Lumped-capacitance heat transferred

\[
Q = m c\bigl(T_i - T\bigr)
\]

```formula
## lumped_capacitance_heat_transferred
family: aerotherm
expr: m*c*(Ti - T)
symbols: m, c, Ti, T
```

Positive when the solid cools.

## Biot number

\[
\mathrm{Bi} = \frac{h L_c}{k}
\]

```formula
## biot_number
family: aerotherm
expr: h*Lc/k
symbols: h, Lc, k
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{Bi}\) | Biot number | dimensionless |
| \(h\) | Convection coefficient | W/(m²·K) |
| \(L_c\) | Characteristic length (script `Lc`), often \(V/A\) | m |
| \(k\) | Solid thermal conductivity | W/(m·K) |

Lumped capacitance is appropriate when \(\mathrm{Bi}\ll 1\) (commonly \(\mathrm{Bi}\le 0.1\)). Do not invent \(k\) or \(L_c\).
