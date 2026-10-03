# Aerospace formulas

Units below are SI. Any single consistent unit system is valid. Do not mix systems in one calculation.

In the rocket equations, \(k\) is the ratio of specific heats. It is the same quantity as \(\gamma\) in the Area-Mach relation. Standard sea-level gravitational acceleration is \(g_0 = 9.80665\,\text{m/s}^2\).

## Area-Mach relation

Local duct area compared with the sonic throat area for isentropic flow of a calorically perfect gas.

\[
\frac{A}{A^{*}} = \frac{1}{M}\left[\frac{2}{\gamma+1}\left(1+\frac{\gamma-1}{2}M^{2}\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Local cross-sectional flow area | m² |
| \(A^{*}\) | Sonic throat area, the area where \(M = 1\) | m² |
| \(M\) | Local Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats, \(c_p / c_v\) | dimensionless |

Assumptions: steady, one-dimensional, isentropic flow of a calorically perfect gas. For air, use \(\gamma = 1.4\) unless the user gives another value. For a rocket nozzle, the area ratio is \(\epsilon = A_2/A_t\), with \(A = A_2\), \(A^{*} = A_t\), \(M = M_2\), and \(\gamma = k\).

## Bernoulli's relation

Mechanical energy is constant along a streamline in steady, incompressible, inviscid flow.

\[
p + \frac{1}{2}\rho V^{2} + \rho g z = \text{constant}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Static pressure | Pa |
| \(\rho\) | Density | kg/m³ |
| \(V\) | Flow speed | m/s |
| \(g\) | Gravitational acceleration | m/s² |
| \(z\) | Elevation | m |

Assumptions: steady, incompressible, inviscid flow along a streamline. Density is constant. Use \(g = 9.80665\,\text{m/s}^2\) unless the user gives another value. When elevation change is negligible, the \(\rho g z\) term may be dropped, leaving \(p + \frac{1}{2}\rho V^{2} = \text{constant}\).

## Average exhaust velocity

Nozzle-exit velocity of an ideal rocket. The inlet velocity is taken as zero.

\[
v_2 = c - \frac{(p_2 - p_3)A_2}{\dot{m}}
\]

When \(p_2 = p_3\), this reduces to \(v_2 = c\).

Ideal isentropic expansion of a calorically perfect gas:

\[
v_2 = \sqrt{\frac{2k}{k-1} R T_1 \left[1 - \left(\frac{p_2}{p_1}\right)^{(k-1)/k}\right]}
\]

From the energy equation, with inlet velocity approximately zero:

\[
v_2 = \sqrt{2(h_1 - h_2)}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v_2\) | Average nozzle-exit velocity | m/s |
| \(c\) | Effective exhaust velocity | m/s |
| \(p_1\) | Chamber pressure | Pa |
| \(p_2\) | Nozzle-exit pressure | Pa |
| \(p_3\) | Ambient pressure | Pa |
| \(A_2\) | Nozzle-exit area | m² |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(k\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant of the chamber gas | J/(kg·K) |
| \(T_1\) | Chamber temperature | K |
| \(h_1\) | Specific enthalpy in the chamber | J/kg |
| \(h_2\) | Specific enthalpy at the nozzle exit | J/kg |

Assumptions: steady, one-dimensional flow and \(v_1 = 0\). The isentropic form also assumes a calorically perfect gas with constant \(k\). The enthalpy form assumes no shaft work or heat transfer between chamber and exit.

## Effective exhaust velocity

Exhaust velocity that accounts for both momentum and pressure thrust.

\[
c = c^{*} C_F = \frac{F}{\dot{m}} = I_s g_0
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c\) | Effective exhaust velocity | m/s |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(C_F\) | Thrust coefficient | dimensionless |
| \(F\) | Thrust | N |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(I_s\) | Specific impulse | s |
| \(g_0\) | Standard gravitational acceleration | m/s² |

Assumptions: \(c = F/\dot{m}\) defines effective exhaust velocity for any rocket. The product \(c^{*} C_F\) is the ideal decomposition into chamber and nozzle performance. \(g_0\) converts specific impulse in seconds into a velocity; it is not local gravity.

## Thrust

Force on the vehicle from exhaust momentum and the pressure imbalance at the exit plane.

\[
F = \dot{m} v_2 + (p_2 - p_3) A_2
\]

\[
F = C_F p_1 A_t
\]

For a constant burn at constant effective exhaust velocity, \(\dot{m} = m_p / t_p\), so

\[
F = \frac{c m_p}{t_p}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(F\) | Thrust | N |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(v_2\) | Average nozzle-exit velocity | m/s |
| \(p_1\) | Chamber pressure | Pa |
| \(p_2\) | Nozzle-exit pressure | Pa |
| \(p_3\) | Ambient pressure | Pa |
| \(A_2\) | Nozzle-exit area | m² |
| \(A_t\) | Nozzle throat area | m² |
| \(C_F\) | Thrust coefficient | dimensionless |
| \(c\) | Effective exhaust velocity | m/s |
| \(m_p\) | Propellant mass | kg |
| \(t_p\) | Burn time | s |

Assumptions: steady flow, uniform axial exit velocity, and negligible inlet momentum. \(F = c m_p / t_p\) requires constant mass flow and constant \(c\). \(F = \dot{m} I_s g_0\) is the same relation as \(I_s = F /(\dot{m} g_0)\) in the specific-impulse section.

## Characteristic velocity

Chamber performance parameter. It is independent of the nozzle.

\[
c^{*} = \frac{c}{C_F} = \frac{p_1 A_t}{\dot{m}}
\]

Ideal value for a calorically perfect gas:

\[
c^{*} = \frac{\sqrt{k R T_1}}{k \sqrt{\left(\dfrac{2}{k+1}\right)^{(k+1)/(k-1)}}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(c\) | Effective exhaust velocity | m/s |
| \(C_F\) | Thrust coefficient | dimensionless |
| \(p_1\) | Chamber pressure | Pa |
| \(A_t\) | Nozzle throat area | m² |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(k\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant of the chamber gas | J/(kg·K) |
| \(T_1\) | Chamber temperature | K |

Assumptions: the ideal expression assumes choked isentropic flow of a calorically perfect gas at the throat. \(c^{*} = I_s g_0 / C_F\) and \(c^{*} = F /(\dot{m} C_F)\) repeat \(c = I_s g_0 = F/\dot{m}\) and are not separate equations.

## Thrust coefficient

Dimensionless nozzle performance. It is thrust divided by chamber pressure and throat area.

\[
C_F = \frac{c}{c^{*}} = \frac{F}{p_1 A_t}
\]

Ideal nozzle, including pressure thrust:

\[
C_F = \sqrt{\frac{2k^{2}}{k-1}\left(\frac{2}{k+1}\right)^{(k+1)/(k-1)}\left[1 - \left(\frac{p_2}{p_1}\right)^{(k-1)/k}\right]} + \frac{p_2 - p_3}{p_1}\frac{A_2}{A_t}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_F\) | Thrust coefficient | dimensionless |
| \(c\) | Effective exhaust velocity | m/s |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(F\) | Thrust | N |
| \(p_1\) | Chamber pressure | Pa |
| \(p_2\) | Nozzle-exit pressure | Pa |
| \(p_3\) | Ambient pressure | Pa |
| \(A_t\) | Nozzle throat area | m² |
| \(A_2\) | Nozzle-exit area | m² |
| \(k\) | Ratio of specific heats | dimensionless |

Assumptions: the ideal expression assumes a calorically perfect gas, isentropic nozzle flow, and \(v_1 = 0\). For a fixed \(p_1/p_3\), \(C_F\) is maximum when \(p_2 = p_3\).

## Total impulse and specific impulse

Total impulse is the thrust integrated over the burn. Specific impulse is that impulse per unit propellant weight.

\[
I_t = \int F \, \mathrm{d}t
\]

For constant thrust over burn time \(t\),

\[
I_t = F t
\]

\[
I_s = \frac{c}{g_0} = \frac{c^{*} C_F}{g_0} = \frac{F}{\dot{m} g_0} = \frac{F}{\dot{w}} = \frac{I_t}{m_p g_0} = \frac{I_t}{w}
\]

Substituting the thrust equation gives the exit-condition form

\[
I_s = \frac{v_2}{g_0} + \frac{(p_2 - p_3) A_2}{\dot{m} g_0}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(I_t\) | Total impulse | N·s |
| \(I_s\) | Specific impulse | s |
| \(F\) | Thrust | N |
| \(t\) | Burn time at constant thrust | s |
| \(c\) | Effective exhaust velocity | m/s |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(C_F\) | Thrust coefficient | dimensionless |
| \(g_0\) | Standard gravitational acceleration | m/s² |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(\dot{w}\) | Propellant weight flow rate | N/s |
| \(m_p\) | Propellant mass | kg |
| \(w\) | Propellant weight, \(m_p g_0\) | N |
| \(v_2\) | Average nozzle-exit velocity | m/s |
| \(p_2\) | Nozzle-exit pressure | Pa |
| \(p_3\) | Ambient pressure | Pa |
| \(A_2\) | Nozzle-exit area | m² |

Assumptions: \(I_t = F t\) requires constant thrust. \(w = m_p g_0\) and \(\dot{w} = \dot{m} g_0\). \(g_0\) is the unit conversion for specific impulse in seconds, not the local gravitational acceleration.

## Propellant mass fraction

Fraction of the vehicle or stage initial mass that is usable propellant.

\[
\zeta = \frac{m_p}{m_0} = \frac{m_0 - m_f}{m_0} = 1 - \mathrm{MR}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\zeta\) | Propellant mass fraction | dimensionless |
| \(m_p\) | Usable propellant mass | kg |
| \(m_0\) | Initial vehicle or stage mass | kg |
| \(m_f\) | Final mass after propellant expenditure | kg |
| \(\mathrm{MR}\) | Mass ratio, \(m_f/m_0\) | dimensionless |

Assumptions: \(m_0 = m_f + m_p\). Residual propellant is part of \(m_f\), not \(m_p\).

## Mass ratio

Final mass divided by initial mass for a vehicle or stage.

\[
\mathrm{MR} = \frac{m_f}{m_0} = \frac{m_0 - m_p}{m_0} = \frac{m_f}{m_f + m_p}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{MR}\) | Mass ratio | dimensionless |
| \(m_f\) | Final mass after propellant expenditure | kg |
| \(m_0\) | Initial vehicle or stage mass | kg |
| \(m_p\) | Usable propellant mass | kg |

Assumptions: \(m_0 = m_f + m_p\). This mass ratio is less than 1. It is not the reciprocal \(m_0/m_f\).

## Vehicle velocity increase in gravity-free vacuum

Ideal speed change with no gravity loss, drag, or initial velocity.

\[
\Delta u = -c \ln \mathrm{MR} = c \ln \frac{m_0}{m_f} = c \ln \frac{m_0}{m_0 - m_p} = c \ln \frac{m_p + m_f}{m_f}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\Delta u\) | Velocity increase | m/s |
| \(c\) | Effective exhaust velocity | m/s |
| \(\mathrm{MR}\) | Mass ratio, \(m_f/m_0\) | dimensionless |
| \(m_0\) | Initial mass | kg |
| \(m_f\) | Final mass | kg |
| \(m_p\) | Usable propellant mass | kg |

Assumptions: gravity-free, drag-free vacuum, constant \(c\), and initial velocity \(u_0 = 0\). The four forms are the same equation under \(m_0 = m_f + m_p\).

## Propellant mass flow rate

Continuity through a duct, and the choked chamber flow of an ideal rocket.

\[
\dot{m} = \frac{A v}{V} = \frac{A_1 v_1}{V_1} = \frac{A_t v_t}{V_t} = \frac{A_2 v_2}{V_2}
\]

\[
\dot{m} = \frac{F}{c} = \frac{p_1 A_t}{c^{*}}
\]

Ideal choked flow:

\[
\dot{m} = p_1 A_t k \frac{\sqrt{\left(\dfrac{2}{k+1}\right)^{(k+1)/(k-1)}}}{\sqrt{k R T_1}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(A\) | Local cross-sectional area | m² |
| \(v\) | Local gas velocity | m/s |
| \(V\) | Local specific volume | m³/kg |
| \(A_1, v_1, V_1\) | Area, velocity, and specific volume at the nozzle inlet | m², m/s, m³/kg |
| \(A_t, v_t, V_t\) | Area, velocity, and specific volume at the throat | m², m/s, m³/kg |
| \(A_2, v_2, V_2\) | Area, velocity, and specific volume at the nozzle exit | m², m/s, m³/kg |
| \(F\) | Thrust | N |
| \(c\) | Effective exhaust velocity | m/s |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(p_1\) | Chamber pressure | Pa |
| \(k\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant of the chamber gas | J/(kg·K) |
| \(T_1\) | Chamber temperature | K |

Assumptions: steady flow. Here \(V\) is specific volume, not the flow speed used in Bernoulli's relation. The ideal expression assumes choked isentropic flow of a calorically perfect gas. It is the characteristic-velocity equation solved for \(\dot{m}\).

## Mach number

Flow speed divided by the local speed of sound.

\[
M = \frac{v}{a} = \frac{v}{\sqrt{k R T}}
\]

At the throat of a choked nozzle, \(v = a\) and \(M = 1\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mach number | dimensionless |
| \(v\) | Local gas velocity | m/s |
| \(a\) | Local speed of sound | m/s |
| \(k\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Local static temperature | K |

Assumptions: calorically perfect gas, so \(a = \sqrt{k R T}\).

## Nozzle area ratio

Exit area divided by throat area.

\[
\epsilon = \frac{A_2}{A_t}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\epsilon\) | Nozzle area ratio | dimensionless |
| \(A_2\) | Nozzle-exit area | m² |
| \(A_t\) | Nozzle throat area | m² |
| \(M_2\) | Nozzle-exit Mach number | dimensionless |
| \(k\) | Ratio of specific heats | dimensionless |

Assumptions: for isentropic flow, \(\epsilon(M_2, k)\) is the Area-Mach relation with \(A/A^{*} = \epsilon\), \(M = M_2\), and \(\gamma = k\). That expression is not repeated here.

## Isentropic flow relations

Stagnation and static states for a calorically perfect gas, and the same relation between the throat and the nozzle exit.

\[
\frac{T_0}{T} = \left(\frac{p_0}{p}\right)^{(k-1)/k} = \left(\frac{V}{V_0}\right)^{k-1}
\]

\[
\frac{T_t}{T_2} = \left(\frac{p_t}{p_2}\right)^{(k-1)/k} = \left(\frac{V_2}{V_t}\right)^{k-1}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T_0, T\) | Stagnation temperature and static temperature | K |
| \(p_0, p\) | Stagnation pressure and static pressure | Pa |
| \(V_0, V\) | Stagnation specific volume and static specific volume | m³/kg |
| \(T_t, T_2\) | Throat temperature and nozzle-exit temperature | K |
| \(p_t, p_2\) | Throat pressure and nozzle-exit pressure | Pa |
| \(V_t, V_2\) | Throat specific volume and nozzle-exit specific volume | m³/kg |
| \(k\) | Ratio of specific heats | dimensionless |

Assumptions: isentropic flow of a calorically perfect gas. \(V\) is specific volume. The throat-to-exit equation is the stagnation relation applied between those two stations.

## Satellite velocity in a circular orbit

Circular-orbit speed at altitude \(h\) above a spherical planet.

\[
u_s = R_0 \sqrt{\frac{g_0}{R_0 + h}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(u_s\) | Circular satellite velocity | m/s |
| \(R_0\) | Effective planetary radius | m |
| \(g_0\) | Gravitational acceleration at the planetary surface | m/s² |
| \(h\) | Altitude above the surface | m |

Assumptions: spherical planet, inverse-square gravity, and a circular orbit. For Earth, use \(R_0 = 6.3742 \times 10^{6}\,\text{m}\) unless the user gives another value.

## Escape velocity

Speed required to escape from altitude \(h\) on a parabolic path.

\[
v_e = R_0 \sqrt{\frac{2 g_0}{R_0 + h}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v_e\) | Escape velocity | m/s |
| \(R_0\) | Effective planetary radius | m |
| \(g_0\) | Gravitational acceleration at the planetary surface | m/s² |
| \(h\) | Altitude above the surface | m |

Assumptions: spherical planet and inverse-square gravity, neglecting atmosphere. \(v_e\) here is escape speed, not exhaust velocity. For Earth, use \(R_0 = 6.3742 \times 10^{6}\,\text{m}\) unless the user gives another value.

## Liquid-propellant mixture ratio

Oxidizer flow divided by fuel flow, and the split of a known total flow.

\[
r = \frac{\dot{m}_o}{\dot{m}_f}
\]

\[
\dot{m} = \dot{m}_o + \dot{m}_f
\]

\[
\dot{m}_f = \frac{\dot{m}}{r + 1}
\]

\[
\dot{m}_o = \frac{r \dot{m}}{r + 1}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r\) | Mixture ratio, oxidizer mass flow over fuel mass flow | dimensionless |
| \(\dot{m}_o\) | Oxidizer mass flow rate | kg/s |
| \(\dot{m}_f\) | Fuel mass flow rate | kg/s |
| \(\dot{m}\) | Total propellant mass flow rate | kg/s |

Assumptions: steady liquid-propellant flow. In this section \(r\) is mixture ratio, not solid-propellant burning rate, and subscript \(f\) means fuel, not final vehicle mass.

## Average propellant density

Bulk density of a liquid oxidizer and fuel stored at mixture ratio \(r\).

\[
\rho_{av} = \frac{\rho_o \rho_f (r + 1)}{r \rho_f + \rho_o}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\rho_{av}\) | Average propellant density | kg/m³ |
| \(\rho_o\) | Oxidizer density | kg/m³ |
| \(\rho_f\) | Fuel density | kg/m³ |
| \(r\) | Mixture ratio, oxidizer mass over fuel mass | dimensionless |

Assumptions: \(r\) is a mass ratio, and both densities are the stored liquid densities.

## Characteristic chamber length

Chamber volume divided by throat area.

\[
L^{*} = \frac{V_c}{A_t}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L^{*}\) | Characteristic chamber length | m |
| \(V_c\) | Combustion chamber volume | m³ |
| \(A_t\) | Nozzle throat area | m² |

Assumptions: \(V_c\) is the chamber volume used to define \(L^{*}\), conventionally through the throat plane.

## Solid-propellant mass flow rate

Mass leaving the burning surface.

\[
\dot{m} = A_b r \rho_b
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |
| \(A_b\) | Burning surface area | m² |
| \(r\) | Burning rate | m/s |
| \(\rho_b\) | Solid propellant density | kg/m³ |

Assumptions: the burning surface regresses uniformly at rate \(r\). In this section \(r\) is burning rate, not mixture ratio.

## Solid-propellant burning rate

Empirical pressure dependence of the regression rate.

\[
r = a p_1^{n}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r\) | Burning rate | m/s |
| \(a\) | Burn-rate coefficient | m/(s·Pa\(^{n}\)) |
| \(p_1\) | Chamber pressure | Pa |
| \(n\) | Burn-rate pressure exponent | dimensionless |

Assumptions: \(a\) and \(n\) are constant over the pressure interval of interest. \(a\) depends on propellant temperature.

## Burning-area ratio

Burning surface area divided by throat area. Also called \(K\).

\[
K = \frac{A_b}{A_t}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(K\) | Burning-area ratio | dimensionless |
| \(A_b\) | Burning surface area | m² |
| \(A_t\) | Nozzle throat area | m² |

Assumptions: \(A_b\) and \(A_t\) are the instantaneous values used for the motor balance.

## Temperature sensitivity of burning rate at constant pressure

Fractional change of burning rate with propellant temperature, holding chamber pressure fixed.

\[
\sigma_p = \frac{1}{r} \left( \frac{\partial r}{\partial T_b} \right)_{p_1}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\sigma_p\) | Temperature sensitivity of burning rate | 1/K |
| \(r\) | Burning rate | m/s |
| \(T_b\) | Propellant temperature | K |
| \(p_1\) | Chamber pressure held constant | Pa |

Assumptions: the derivative is at constant chamber pressure.

## Temperature sensitivity of pressure at constant \(K\)

Fractional change of equilibrium chamber pressure with propellant temperature, holding the burning-area ratio fixed.

\[
\pi_K = \frac{1}{p_1} \left( \frac{\partial p}{\partial T_b} \right)_{K}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\pi_K\) | Temperature sensitivity of pressure | 1/K |
| \(p_1\) | Chamber pressure | Pa |
| \(p\) | Equilibrium chamber pressure | Pa |
| \(T_b\) | Propellant temperature | K |
| \(K\) | Burning-area ratio held constant | dimensionless |

Assumptions: the derivative is at constant \(K\).

## Dynamic pressure

Freestream kinetic energy per unit volume. The force and moment coefficients below are normalized by this pressure.

\[
q_{\infty} = \frac{1}{2} \rho_{\infty} V_{\infty}^{2}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |
| \(\rho_{\infty}\) | Freestream density | kg/m³ |
| \(V_{\infty}\) | Freestream speed | m/s |

Assumptions: \(V_{\infty}\) is the speed far ahead of the body. It is not the specific volume \(V\) used in the rocket continuity and isentropic relations.

## Lift, drag, normal-force, axial-force, and moment coefficients

Dimensionless forces and moment on a complete three-dimensional body. Capital letters denote the whole body.

\[
C_L = \frac{L}{q_{\infty} S} \qquad
C_D = \frac{D}{q_{\infty} S} \qquad
C_N = \frac{N}{q_{\infty} S} \qquad
C_A = \frac{A}{q_{\infty} S} \qquad
C_M = \frac{M}{q_{\infty} S l}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_L\) | Lift coefficient | dimensionless |
| \(C_D\) | Drag coefficient | dimensionless |
| \(C_N\) | Normal-force coefficient | dimensionless |
| \(C_A\) | Axial-force coefficient | dimensionless |
| \(C_M\) | Moment coefficient | dimensionless |
| \(L\) | Lift, perpendicular to the freestream | N |
| \(D\) | Drag, parallel to the freestream | N |
| \(N\) | Normal force, perpendicular to the chord or body axis | N |
| \(A\) | Axial force, parallel to the chord or body axis | N |
| \(M\) | Aerodynamic moment | N·m |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |
| \(S\) | Reference area | m² |
| \(l\) | Reference length | m |

Assumptions: \(S\) and \(l\) belong to the geometry used to reduce the data. For a wing, \(S\) is the planform area and \(l\) is the mean chord. For a sphere, \(S\) is the cross-sectional area and \(l\) is the diameter. Here \(A\) is axial force, not area, and \(M\) is moment, not Mach number.

## Two-dimensional lift, drag, and moment coefficients

Forces and moment per unit span on a two-dimensional body. The reference area per unit span is the chord.

\[
c_l = \frac{L'}{q_{\infty} c} \qquad
c_d = \frac{D'}{q_{\infty} c} \qquad
c_m = \frac{M'}{q_{\infty} c^{2}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_l\) | Section lift coefficient | dimensionless |
| \(c_d\) | Section drag coefficient | dimensionless |
| \(c_m\) | Section moment coefficient | dimensionless |
| \(L'\) | Lift per unit span | N/m |
| \(D'\) | Drag per unit span | N/m |
| \(M'\) | Pitching moment per unit span | N·m/m |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |
| \(c\) | Chord | m |

Assumptions: the section is two-dimensional, so \(S = c\) per unit span. These lowercase coefficients are not the whole-body coefficients \(C_L\), \(C_D\), and \(C_M\). Here \(c\) is the chord, not effective exhaust velocity.

## Pressure coefficient

Local pressure relative to the freestream, divided by dynamic pressure.

\[
C_p = \frac{p - p_{\infty}}{q_{\infty}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_p\) | Pressure coefficient | dimensionless |
| \(p\) | Local static pressure | Pa |
| \(p_{\infty}\) | Freestream static pressure | Pa |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |

Assumptions: \(p_{\infty}\) and \(q_{\infty}\) are freestream values far ahead of the body.

## Skin friction coefficient

Local wall shear stress divided by dynamic pressure.

\[
c_f = \frac{\tau}{q_{\infty}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_f\) | Skin-friction coefficient | dimensionless |
| \(\tau\) | Local shear stress at the wall | Pa |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |

Assumptions: \(\tau\) is the shear stress acting on the surface. Subscripts \(u\) and \(l\) denote the upper and lower surfaces.

## Normal, axial, and leading-edge moment coefficients by integration

Section coefficients of a two-dimensional airfoil from the pressure and skin-friction distributions. Integration is along the chord from the leading edge to \(x = c\).

\[
c_n = \frac{1}{c}\left[\int_{0}^{c}(C_{p,l} - C_{p,u})\,\mathrm{d}x + \int_{0}^{c}\left(c_{f,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} + c_{f,l}\frac{\mathrm{d}y_l}{\mathrm{d}x}\right)\mathrm{d}x\right]
\]

\[
c_a = \frac{1}{c}\left[\int_{0}^{c}\left(C_{p,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} - C_{p,l}\frac{\mathrm{d}y_l}{\mathrm{d}x}\right)\mathrm{d}x + \int_{0}^{c}(c_{f,u} + c_{f,l})\,\mathrm{d}x\right]
\]

\[
\begin{aligned}
c_{m,\mathrm{LE}} = \frac{1}{c^{2}}\Bigg[&\int_{0}^{c}(C_{p,u} - C_{p,l}) x\,\mathrm{d}x - \int_{0}^{c}\left(c_{f,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} + c_{f,l}\frac{\mathrm{d}y_l}{\mathrm{d}x}\right) x\,\mathrm{d}x \\
&+ \int_{0}^{c}\left(C_{p,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} + c_{f,u}\right) y_u\,\mathrm{d}x + \int_{0}^{c}\left(-C_{p,l}\frac{\mathrm{d}y_l}{\mathrm{d}x} + c_{f,l}\right) y_l\,\mathrm{d}x\Bigg]
\end{aligned}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_n\) | Section normal-force coefficient | dimensionless |
| \(c_a\) | Section axial-force coefficient | dimensionless |
| \(c_{m,\mathrm{LE}}\) | Section moment coefficient about the leading edge | dimensionless |
| \(c\) | Chord | m |
| \(x\) | Distance along the chord from the leading edge | m |
| \(y_u\) | Upper-surface coordinate, positive above the chord | m |
| \(y_l\) | Lower-surface coordinate, negative below the chord | m |
| \(C_{p,u}, C_{p,l}\) | Pressure coefficients on the upper and lower surfaces | dimensionless |
| \(c_{f,u}, c_{f,l}\) | Skin-friction coefficients on the upper and lower surfaces | dimensionless |

Assumptions: \(x\) runs along the chord from the leading edge. \(y_u\) is positive and \(y_l\) is negative. The slope \(\mathrm{d}y/\mathrm{d}x\) follows the usual calculus sign on both surfaces: positive on a portion with positive slope and negative on a portion with negative slope. The moment is about the leading edge and is positive pitch-up.

## Lift and drag coefficients from the normal and axial coefficients

Section lift and drag obtained by resolving the chord-axis force coefficients through the angle of attack.

\[
c_l = c_n \cos\alpha - c_a \sin\alpha
\]

\[
c_d = c_n \sin\alpha + c_a \cos\alpha
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_l\) | Section lift coefficient | dimensionless |
| \(c_d\) | Section drag coefficient | dimensionless |
| \(c_n\) | Section normal-force coefficient | dimensionless |
| \(c_a\) | Section axial-force coefficient | dimensionless |
| \(\alpha\) | Angle of attack | rad |

Assumptions: normal force is perpendicular to the chord, axial force is parallel to the chord, lift is perpendicular to the freestream, and drag is parallel to the freestream. Use radians in the sine and cosine.

## Center of pressure of an airfoil

Chordwise location where the section normal force acts so that it reproduces the leading-edge pitching moment. The axial force lies on the chord and contributes no moment about the leading edge.

\[
x_{\mathrm{cp}} = -\frac{M'_{\mathrm{LE}}}{N'}
\]

This is the same statement as \(M'_{\mathrm{LE}} = -x_{\mathrm{cp}} N'\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x_{\mathrm{cp}}\) | Distance from the leading edge to the center of pressure, positive aft | m |
| \(M'_{\mathrm{LE}}\) | Pitching moment per unit span about the leading edge | N·m/m |
| \(N'\) | Normal force per unit span | N/m |

Assumptions: two-dimensional airfoil, with \(N'\) perpendicular to the chord and the axial force on the chord line. Positive moment is pitch-up. A positive \(N'\) acting aft of the leading edge produces a negative moment, which is why the leading minus sign makes \(x_{\mathrm{cp}}\) positive.

