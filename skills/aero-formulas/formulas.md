# Aerospace formulas

Units below are SI unless a section says otherwise. Any single consistent unit system is valid. Do not mix systems in one calculation.

The file is grouped so a search can start in one category:

- Compressible flow: perfect-gas thermodynamics, isentropic flow, area-Mach, shocks, Prandtl-Meyer expansion, calorically imperfect air, Newtonian viscosity, and Reynolds number.
- Atmosphere: the 1976 U.S. Standard Atmosphere from the surface to 1000 km, including geopotential and gravity, the seven hydrostatic layers below 86 km, kinetic temperature above 86 km, and the transport properties of that model. A three-zone NASA Glenn curve fit is recorded separately.
- Rocket propulsion: thrust, impulse, mass ratio, nozzles, solid- and liquid-propellant relations, and two-body orbital speed, period, energy, anomalies, and mean motion.
- Aerodynamics: incompressible Bernoulli, force and moment coefficients, trapezoidal wing planform, aspect ratio, induced drag, finite-wing lift-curve slope and induced angle, stall speed, equivalent airspeed, load factor, and the stick-fixed neutral point and static margin.
- Structures: thin-wall motor-case hoop stress, margin of safety, and longitudinal-weld radial mismatch.

The rocket symbol \(k\) is the same ratio of specific heats as \(\gamma\). Standard sea-level gravitational acceleration is \(g_0 = 9.80665\,\mathrm{m/s}^2\).

Each formula is also written as a script record. In those records \(\gamma\) is `g`, powers are `**`, and the expression is the quantity named by the record. `partial`, `integral`, `log`, `exp`, `sin`, `cos`, `tan`, `cot`, `atan`, and `asin` are function calls.

# Compressible flow

Perfect-gas and shock relations for steady inviscid flow, from NACA Report 1135. Numerical Mach-number tables and charts in that report are not copied here. In this category \(V\) is flow speed and \(v\) is specific volume. \(\gamma\) and the rocket-propulsion symbol \(k\) are the same ratio of specific heats. For air as a calorically perfect gas, use \(\gamma = 1.4 = 7/5\) unless the user gives another value. Above roughly \(550\,\text{K}\), use the air \(\gamma(T)\) table at the end of this category.

## Perfect-gas equation of state

Thermal equation of state for a thermally perfect gas.

\[
p = \rho R T = \frac{R T}{v}
\]

```formula
## perfect_gas
family: thermo
expr: rho*R*T
symbols: rho, R, T
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Static pressure | Pa |
| \(\rho\) | Static density | kg/m³ |
| \(v\) | Specific volume | m³/kg |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Static temperature | K |

Assumptions: thermally perfect gas, \(p = \rho R T\).

## Specific heats

Definitions and the perfect-gas relations among \(c_p\), \(c_v\), \(R\), and \(\gamma\).

\[
c_p = \left(\frac{\partial h}{\partial T}\right)_p \qquad
c_v = \left(\frac{\partial u}{\partial T}\right)_v \qquad
\gamma = \frac{c_p}{c_v}
\]

```formula
## cp_definition
family: thermo
expr: partial(h, T)
symbols: h, T
```

```formula
## cv_definition
family: thermo
expr: partial(u, T)
symbols: u, T
```

```formula
## gamma_definition
family: thermo
expr: cp/cv
symbols: cp, cv
```

\[
c_p - c_v = R \qquad
c_p = \frac{\gamma R}{\gamma - 1} \qquad
c_v = \frac{R}{\gamma - 1}
\]

```formula
## cp_minus_cv
family: thermo
expr: cp - cv
symbols: cp, cv
```

```formula
## cp_from_gamma
family: thermo
expr: g*R/(g - 1)
symbols: g, R
```

```formula
## cv_from_gamma
family: thermo
expr: R/(g - 1)
symbols: g, R
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_p\) | Specific heat at constant pressure | J/(kg·K) |
| \(c_v\) | Specific heat at constant volume | J/(kg·K) |
| \(h\) | Specific enthalpy | J/kg |
| \(u\) | Specific internal energy | J/kg |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Temperature | K |

Assumptions: \(c_p - c_v = R\) requires a thermally perfect gas. The expressions that contain \(\gamma\) also require a calorically perfect gas, so \(c_p\) and \(c_v\) are constant.

## Enthalpy and internal energy

\[
h = u + p v
\]

```formula
## enthalpy_definition
family: thermo
expr: u + p*v
symbols: u, p, v
```

For a calorically perfect gas, with the energy zero chosen so the constants may be dropped when only differences matter,

\[
h = c_p T \qquad u = c_v T
\]

```formula
## enthalpy_perfect
family: thermo
expr: cp*T
symbols: cp, T
```

```formula
## internal_energy_perfect
family: thermo
expr: cv*T
symbols: cv, T
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h\) | Specific enthalpy | J/kg |
| \(u\) | Specific internal energy | J/kg |
| \(p\) | Static pressure | Pa |
| \(v\) | Specific volume | m³/kg |
| \(c_p\) | Specific heat at constant pressure | J/(kg·K) |
| \(c_v\) | Specific heat at constant volume | J/(kg·K) |
| \(T\) | Static temperature | K |

Assumptions: \(h = c_p T\) and \(u = c_v T\) are differences from a constant reference for a calorically perfect gas.

## Speed of sound

\[
a = \sqrt{\left(\frac{\partial p}{\partial \rho}\right)_s} = \sqrt{\gamma \frac{p}{\rho}} = \sqrt{\gamma R T}
\]

```formula
## speed_of_sound
family: thermo
expr: (g*R*T)**0.5
symbols: g, R, T
```

For air with \(T\) in degrees Rankine, \(a \approx 49.0 \sqrt{T}\) in ft/s.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a\) | Speed of sound | m/s |
| \(p\) | Static pressure | Pa |
| \(\rho\) | Static density | kg/m³ |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Static temperature | K |

Assumptions: the forms with \(\gamma\) require a perfect gas. The derivative is at constant entropy.

## Mach number

\[
M = \frac{V}{a} = \frac{V}{\sqrt{\gamma R T}}
\]

```formula
## mach_number
family: isentropic
expr: V/(g*R*T)**0.5
symbols: V, g, R, T
```

At a choked throat, \(V = a\) and \(M = 1\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mach number | dimensionless |
| \(V\) | Flow speed | m/s |
| \(a\) | Local speed of sound | m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Static temperature | K |

Assumptions: perfect gas. In the rocket-propulsion category the same definition is written with speed \(v\) and specific-heat ratio \(k\).

## Newtonian viscosity and Reynolds number

Shear stress in a Newtonian fluid, kinematic viscosity, and the Reynolds number. The viscosity page of NASA Glenn's Beginner's Guide to Aeronautics states \(\tau = \mu\,\mathrm{d}V/\mathrm{d}y\) and \(Re = \rho V L/\mu\).

\[
\tau = \mu \frac{\mathrm{d}V}{\mathrm{d}y}
\]

```formula
## newtonian_shear
family: thermo
expr: mu*dVdy
symbols: mu, dVdy
```

\[
\nu = \frac{\mu}{\rho}
\]

```formula
## kinematic_viscosity
family: thermo
expr: mu/rho
symbols: mu, rho
```

\[
Re = \frac{\rho V L}{\mu} = \frac{V L}{\nu}
\]

```formula
## reynolds_number
family: thermo
expr: rho*V*L/mu
symbols: rho, V, L, mu
```

```formula
## reynolds_number_kinematic
family: thermo
expr: V*L/nu
symbols: V, L, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\tau\) | Shear stress | Pa |
| \(\mu\) | Dynamic viscosity | Pa·s |
| \(\mathrm{d}V/\mathrm{d}y\) | Velocity gradient normal to the surface | 1/s |
| \(\nu\) | Kinematic viscosity | m²/s |
| \(\rho\) | Density | kg/m³ |
| \(Re\) | Reynolds number | dimensionless |
| \(V\) | Flow speed | m/s |
| \(L\) | Characteristic length | m |

Assumptions: Newtonian fluid, so shear stress is proportional to the velocity gradient. \(Re\) compares inertial to viscous effects. Matching \(Re\) is required if a test is to represent viscous forces correctly. In this section \(L\) is a length, not characteristic chamber length, and \(\nu\) is kinematic viscosity, not Prandtl-Meyer angle.

## Dynamic pressure

\[
q = \frac{1}{2}\rho V^{2} = \frac{\gamma}{2} p M^{2}
\]

```formula
## dynamic_pressure
family: isentropic
expr: 0.5*rho*V**2
symbols: rho, V
```

For air with \(\gamma = 7/5\),

\[
\frac{q}{p} = \frac{7}{10} M^{2}
\]

```formula
## dynamic_pressure_air
family: isentropic
expr: (7/10)*M**2
symbols: M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(q\) | Dynamic pressure | Pa |
| \(\rho\) | Static density | kg/m³ |
| \(V\) | Flow speed | m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(p\) | Static pressure | Pa |
| \(M\) | Mach number | dimensionless |

Assumptions: \(q = (\gamma/2) p M^{2}\) requires a perfect gas. The freestream value used by the aerodynamic coefficients is \(q_{\infty}\).

## Adiabatic energy equation

Steady adiabatic flow with no shaft work. Total enthalpy is constant.

\[
h + \frac{V^{2}}{2} = h_t
\]

```formula
## total_enthalpy
family: isentropic
expr: h + V**2/2
symbols: h, V
```

For a perfect gas,

\[
c_p T + \frac{V^{2}}{2} = c_p T_t
\]

```formula
## total_temperature_energy
family: isentropic
expr: cp*T + V**2/2
symbols: cp, T, V
```

\[
\frac{a^{2}}{\gamma - 1} + \frac{V^{2}}{2} = \frac{a_t^{2}}{\gamma - 1}
\]

```formula
## sound_speed_energy
family: isentropic
expr: a**2/(g - 1) + V**2/2
symbols: a, g, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h\) | Static specific enthalpy | J/kg |
| \(h_t\) | Total specific enthalpy | J/kg |
| \(V\) | Flow speed | m/s |
| \(c_p\) | Specific heat at constant pressure | J/(kg·K) |
| \(T\) | Static temperature | K |
| \(T_t\) | Total temperature | K |
| \(a\) | Local speed of sound | m/s |
| \(a_t\) | Total, or stagnation, speed of sound | m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: steady and adiabatic. The perfect-gas forms also require constant specific heats. This relation holds across a shock as well as in isentropic flow. Total temperature is therefore unchanged by a shock.

## Isentropic stagnation relations

Static state compared with the state reached by isentropic deceleration to rest.

\[
\frac{T_t}{T} = 1 + \frac{\gamma - 1}{2} M^{2}
\]

```formula
## stagnation_temperature
family: isentropic
expr: 1 + ((g - 1)/2)*M**2
symbols: g, M
```

\[
\frac{p_t}{p} = \left(\frac{T_t}{T}\right)^{\gamma/(\gamma - 1)} \qquad
\frac{\rho_t}{\rho} = \left(\frac{T_t}{T}\right)^{1/(\gamma - 1)} \qquad
\frac{a_t}{a} = \sqrt{\frac{T_t}{T}}
\]

```formula
## stagnation_pressure
family: isentropic
expr: (Tt/T)**(g/(g - 1))
symbols: Tt, T, g
```

```formula
## stagnation_density
family: isentropic
expr: (Tt/T)**(1/(g - 1))
symbols: Tt, T, g
```

```formula
## stagnation_sound_speed
family: isentropic
expr: (Tt/T)**0.5
symbols: Tt, T
```

For air with \(\gamma = 7/5\),

\[
\frac{T_t}{T} = 1 + \frac{M^{2}}{5} \qquad
\frac{p_t}{p} = \left(1 + \frac{M^{2}}{5}\right)^{7/2} \qquad
\frac{\rho_t}{\rho} = \left(1 + \frac{M^{2}}{5}\right)^{5/2}
\]

```formula
## stagnation_temperature_air
family: isentropic
expr: 1 + M**2/5
symbols: M
```

```formula
## stagnation_pressure_air
family: isentropic
expr: (1 + M**2/5)**(7/2)
symbols: M
```

```formula
## stagnation_density_air
family: isentropic
expr: (1 + M**2/5)**(5/2)
symbols: M
```

Between any two points on the same isentropic streamline, including a nozzle throat and exit,

\[
\frac{T_2}{T_1} = \left(\frac{p_2}{p_1}\right)^{(\gamma - 1)/\gamma} = \left(\frac{\rho_2}{\rho_1}\right)^{\gamma - 1} = \left(\frac{v_1}{v_2}\right)^{\gamma - 1}
\]

```formula
## isentropic_state_ratio
family: isentropic
expr: (p2/p1)**((g - 1)/g)
symbols: p2, p1, g
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T_t, T\) | Total temperature and static temperature | K |
| \(p_t, p\) | Total pressure and static pressure | Pa |
| \(\rho_t, \rho\) | Total density and static density | kg/m³ |
| \(a_t, a\) | Total and local speeds of sound | m/s |
| \(M\) | Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(v\) | Specific volume | m³/kg |

Assumptions: isentropic flow of a perfect gas. Do not apply the stagnation-pressure or stagnation-density ratios across a shock. Total temperature still follows the adiabatic energy equation through a shock.

## Sonic reference state

Ratios at the critical state, where \(M = 1\), to the stagnation state. Subscript \(*\) denotes that state.

\[
\frac{T^{*}}{T_t} = \frac{2}{\gamma + 1} \qquad
\frac{p^{*}}{p_t} = \left(\frac{2}{\gamma + 1}\right)^{\gamma/(\gamma - 1)} \qquad
\frac{\rho^{*}}{\rho_t} = \left(\frac{2}{\gamma + 1}\right)^{1/(\gamma - 1)}
\]

```formula
## sonic_temperature
family: isentropic
expr: 2/(g + 1)
symbols: g
```

```formula
## sonic_pressure
family: isentropic
expr: (2/(g + 1))**(g/(g - 1))
symbols: g
```

```formula
## sonic_density
family: isentropic
expr: (2/(g + 1))**(1/(g - 1))
symbols: g
```

\[
\left(\frac{a_t}{a^{*}}\right)^{2} = \frac{\gamma + 1}{2}
\]

```formula
## sonic_sound_speed
family: isentropic
expr: (g + 1)/2
symbols: g
```

For air with \(\gamma = 7/5\), \(T^{*}/T_t = 5/6\) and \((a_t/a^{*})^{2} = 6/5\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T^{*}, p^{*}, \rho^{*}, a^{*}\) | Temperature, pressure, density, and sound speed at \(M = 1\) | K, Pa, kg/m³, m/s |
| \(T_t, p_t, \rho_t, a_t\) | Stagnation temperature, pressure, density, and sound speed | K, Pa, kg/m³, m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: isentropic flow of a perfect gas.

## Compressible Bernoulli equation

Integrated isentropic Euler equation for a perfect gas.

\[
\frac{\gamma}{\gamma - 1}\frac{p_t}{\rho_t} = \frac{\gamma}{\gamma - 1}\frac{p}{\rho} + \frac{V^{2}}{2}
\]

```formula
## compressible_bernoulli
family: isentropic
expr: (g/(g - 1))*pt/rhot
symbols: g, pt, rhot
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(p_t, \rho_t\) | Stagnation pressure and stagnation density | Pa, kg/m³ |
| \(p, \rho\) | Static pressure and static density | Pa, kg/m³ |
| \(V\) | Flow speed | m/s |

Assumptions: isentropic perfect-gas flow. The incompressible Bernoulli equation is in the Aerodynamics category.

## Area-Mach relation

Local duct area compared with the sonic throat area.

\[
\frac{A}{A^{*}} = \frac{1}{M}\left[\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2} M^{2}\right)\right]^{\frac{\gamma + 1}{2(\gamma - 1)}}
\]

```formula
## area_mach
family: isentropic
expr: (1/M)*((2/(g+1))*(1+((g-1)/2)*M**2))**((g+1)/(2*(g-1)))
symbols: M, g
```

For air with \(\gamma = 7/5\),

\[
\frac{A^{*}}{A} = \frac{216}{125}\, M \left(1 + \frac{M^{2}}{5}\right)^{-3}
\]

```formula
## area_mach_air
family: isentropic
expr: (216/125)*M*(1 + M**2/5)**(-3)
symbols: M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Local cross-sectional area | m² |
| \(A^{*}\) | Sonic throat area, where \(M = 1\) | m² |
| \(M\) | Local Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: steady, one-dimensional, isentropic flow of a perfect gas. For a rocket nozzle this ratio is \(\epsilon = A_2/A_t\), with \(A = A_2\), \(A^{*} = A_t\), \(M = M_2\), and \(\gamma = k\).

## Stream-tube continuity

\[
\rho V A = \text{constant}
\]

```formula
## stream_tube_continuity
family: isentropic
expr: rho*V*A
symbols: rho, V, A
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\rho\) | Static density | kg/m³ |
| \(V\) | Flow speed normal to the area | m/s |
| \(A\) | Cross-sectional area | m² |

Assumptions: steady flow with uniform properties across each section. The rocket mass-flow statement \(\dot{m} = A v / V_{\text{specific}}\) is this equation written with specific volume.

## Small-disturbance approximations

First-order changes from a uniform freestream when the disturbance speed is small compared with \(V_{\infty}\).

\[
\frac{T}{T_{\infty}} \approx 1 - (\gamma - 1) M_{\infty}^{2} \frac{V - V_{\infty}}{V_{\infty}}
\]

```formula
## small_disturbance_temperature
family: isentropic
expr: 1 - (g - 1)*Minf**2*(V - Vinf)/Vinf
symbols: g, Minf, V, Vinf
```

\[
\frac{p}{p_{\infty}} \approx 1 - \gamma M_{\infty}^{2} \frac{V - V_{\infty}}{V_{\infty}}
\]

```formula
## small_disturbance_pressure
family: isentropic
expr: 1 - g*Minf**2*(V - Vinf)/Vinf
symbols: g, Minf, V, Vinf
```

\[
\frac{\rho}{\rho_{\infty}} \approx 1 - M_{\infty}^{2} \frac{V - V_{\infty}}{V_{\infty}}
\]

```formula
## small_disturbance_density
family: isentropic
expr: 1 - Minf**2*(V - Vinf)/Vinf
symbols: Minf, V, Vinf
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T, p, \rho, V\) | Local static temperature, pressure, density, and speed | K, Pa, kg/m³, m/s |
| \(T_{\infty}, p_{\infty}, \rho_{\infty}, V_{\infty}\) | Freestream values | K, Pa, kg/m³, m/s |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: perfect gas, isentropic for the pressure and density forms, and \(\lvert V - V_{\infty}\rvert \ll V_{\infty}\).

## Normal shock waves

A steady normal shock. Subscript 1 is upstream and subscript 2 is downstream. The upstream Mach number must be greater than 1.

\[
\frac{p_2}{p_1} = \frac{2\gamma M_1^{2} - (\gamma - 1)}{\gamma + 1}
\]

```formula
## normal_shock_pressure
family: shock
expr: (2*g*M1**2 - (g - 1))/(g + 1)
symbols: g, M1
```

\[
\frac{\rho_2}{\rho_1} = \frac{(\gamma + 1) M_1^{2}}{(\gamma - 1) M_1^{2} + 2}
\]

```formula
## normal_shock_density
family: shock
expr: ((g + 1)*M1**2)/((g - 1)*M1**2 + 2)
symbols: g, M1
```

\[
\frac{T_2}{T_1} = \frac{[2\gamma M_1^{2} - (\gamma - 1)][(\gamma - 1) M_1^{2} + 2]}{(\gamma + 1)^{2} M_1^{2}}
\]

```formula
## normal_shock_temperature
family: shock
expr: (2*g*M1**2 - (g - 1))*((g - 1)*M1**2 + 2)/((g + 1)**2*M1**2)
symbols: g, M1
```

\[
M_2^{2} = \frac{(\gamma - 1) M_1^{2} + 2}{2\gamma M_1^{2} - (\gamma - 1)}
\]

```formula
## normal_shock_mach
family: shock
expr: ((g - 1)*M1**2 + 2)/(2*g*M1**2 - (g - 1))
symbols: g, M1
```

\[
\frac{p_{t2}}{p_1} = \left(\frac{\gamma + 1}{2} M_1^{2}\right)^{\gamma/(\gamma - 1)}\left[\frac{\gamma + 1}{2\gamma M_1^{2} - (\gamma - 1)}\right]^{1/(\gamma - 1)}
\]

```formula
## rayleigh_pitot
family: shock
expr: (((g + 1)/2)*M1**2)**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1))
symbols: g, M1
```

\[
\Delta s = - R \ln\frac{p_{t2}}{p_{t1}}
\]

```formula
## normal_shock_entropy
family: shock
expr: -R*log(pt2/pt1)
symbols: R, pt2, pt1
```

For air with \(\gamma = 7/5\),

\[
\frac{p_2}{p_1} = \frac{7 M_1^{2} - 1}{6} \qquad
\frac{\rho_2}{\rho_1} = \frac{6 M_1^{2}}{M_1^{2} + 5} \qquad
M_2^{2} = \frac{M_1^{2} + 5}{7 M_1^{2} - 1}
\]

```formula
## normal_shock_pressure_air
family: shock
expr: (7*M1**2 - 1)/6
symbols: M1
```

```formula
## normal_shock_density_air
family: shock
expr: 6*M1**2/(M1**2 + 5)
symbols: M1
```

```formula
## normal_shock_mach_air
family: shock
expr: (M1**2 + 5)/(7*M1**2 - 1)
symbols: M1
```

Rankine-Hugoniot relation, without using Mach number:

\[
\frac{p_2 - p_1}{\rho_2 - \rho_1} = \gamma \frac{p_2 + p_1}{\rho_2 + \rho_1}
\]

```formula
## rankine_hugoniot
family: shock
expr: g*(p2 + p1)/(rho2 + rho1)
symbols: g, p2, p1, rho2, rho1
```

Prandtl's relation, with \(a^{*}\) the critical sound speed:

\[
V_1 V_2 = a^{*\,2}
\]

```formula
## prandtl_relation
family: shock
expr: astar**2
symbols: astar
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p, \rho, T, M, V\) | Static pressure, density, temperature, Mach number, and speed | Pa, kg/m³, K, dimensionless, m/s |
| \(p_t\) | Total pressure | Pa |
| \(\Delta s\) | Specific-entropy increase | J/(kg·K) |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(a^{*}\) | Critical sound speed | m/s |

Assumptions: steady normal shock in a perfect gas. Velocities are measured relative to the shock, so the same relations apply to an unsteady wave. Entropy must not decrease, which requires \(M_1 \ge 1\). Total temperature is unchanged. The Rayleigh-Pitot formula is the expression for \(p_{t2}/p_1\).

## Oblique shock waves

A straight oblique shock in a uniform supersonic stream. \(\theta\) is the shock angle from the upstream velocity, and \(\delta\) is the flow deflection.

The tangential velocity is unchanged. The velocity component normal to the shock obeys the normal-shock relations, with upstream Mach number \(M_1 \sin\theta\).

\[
\tan\delta = \frac{2\cot\theta\,(M_1^{2}\sin^{2}\theta - 1)}{2 + M_1^{2}(\gamma + \cos 2\theta)}
\]

```formula
## oblique_shock_deflection
family: oblique_shock
expr: 2*cot(theta)*(M1**2*sin(theta)**2 - 1)/(2 + M1**2*(g + cos(2*theta)))
symbols: theta, M1, g
```

For air with \(\gamma = 7/5\),

\[
\tan\delta = \frac{5(M_1^{2}\sin 2\theta - 2\cot\theta)}{10 + M_1^{2}(7 + 5\cos 2\theta)}
\]

```formula
## oblique_shock_deflection_air
family: oblique_shock
expr: 5*(M1**2*sin(2*theta) - 2*cot(theta))/(10 + M1**2*(7 + 5*cos(2*theta)))
symbols: M1, theta
```

Downstream static ratios follow by replacing \(M_1\) with \(M_1\sin\theta\) in the normal-shock formulas. The downstream Mach number is then

\[
M_2^{2}\sin^{2}(\theta - \delta) = \frac{(\gamma - 1) M_1^{2}\sin^{2}\theta + 2}{2\gamma M_1^{2}\sin^{2}\theta - (\gamma - 1)}
\]

```formula
## oblique_shock_normal_mach
family: oblique_shock
expr: ((g - 1)*M1**2*sin(theta)**2 + 2)/(2*g*M1**2*sin(theta)**2 - (g - 1))
symbols: g, M1, theta
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\theta\) | Shock-wave angle from the upstream velocity | rad |
| \(\delta\) | Flow deflection through the shock | rad |
| \(M_1\) | Upstream Mach number | dimensionless |
| \(M_2\) | Downstream Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: perfect gas, and \(\theta\) between the Mach angle and \(90^\circ\). Two wave angles can satisfy a given deflection. On an isolated convex body only the weaker shock, the one with the smaller \(\theta\), occurs. For air, a wedge shock stays attached only for a semivertex angle below about \(45.6^\circ\), and a cone shock only below about \(57.5^\circ\). Sine and tangent above expect radians.

## Mach angle

Angle of a Mach line in a uniform supersonic stream.

\[
\mu = \arcsin\frac{1}{M}
\]

```formula
## mach_angle
family: expansion
expr: asin(1/M)
symbols: M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mu\) | Mach angle | rad |
| \(M\) | Mach number | dimensionless |

Assumptions: \(M \ge 1\).

## Prandtl-Meyer expansion

Isentropic turning of a perfect gas from Mach 1 to Mach \(M\). The angle \(\nu\) is measured in radians when the inverse tangents return radians.

\[
\nu = \sqrt{\frac{\gamma + 1}{\gamma - 1}}\arctan\sqrt{\frac{\gamma - 1}{\gamma + 1}(M^{2} - 1)} - \arctan\sqrt{M^{2} - 1}
\]

```formula
## prandtl_meyer
family: expansion
expr: ((g + 1)/(g - 1))**0.5*atan(((g - 1)/(g + 1)*(M**2 - 1))**0.5) - atan((M**2 - 1)**0.5)
symbols: g, M
```

The maximum turning angle, from Mach 1 to infinite Mach number, is

\[
\nu_{\max} = \left(\sqrt{\frac{\gamma + 1}{\gamma - 1}} - 1\right)\frac{\pi}{2}
\]

```formula
## prandtl_meyer_max
family: expansion
expr: (((g + 1)/(g - 1))**0.5 - 1)*pi/2
symbols: g, pi
```

For air with \(\gamma = 7/5\), \(\nu_{\max} = 130.45^\circ\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\nu\) | Prandtl-Meyer angle from Mach 1 | rad |
| \(\nu_{\max}\) | Maximum Prandtl-Meyer angle | rad |
| \(M\) | Mach number after the expansion | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: isentropic supersonic expansion of a perfect gas. The turning from an upstream Mach \(M_1\) to a downstream Mach \(M_2\) is \(\nu(M_2) - \nu(M_1)\). Static-to-total pressure still follows the isentropic stagnation relation.

## Calorically imperfect isentropic flow

First-order vibrational correction for a thermally perfect gas, such as air at hypersonic temperature. \(\gamma_{\mathrm{perf}}\) is the perfect-gas ratio. The local ratio \(\gamma\) includes vibration. For air, \(\gamma_{\mathrm{perf}} = 1.4\) and \(\theta = 5500^\circ\mathrm{R} = 3055.6\,\mathrm{K}\). Use the same temperature unit for \(T\), \(T_t\), and \(\theta\).

\[
\gamma = 1 + \frac{\gamma_{\mathrm{perf}} - 1}{1 + (\gamma_{\mathrm{perf}} - 1)\dfrac{(\theta/T)^{2} e^{\theta/T}}{\left(e^{\theta/T} - 1\right)^{2}}}
\]

```formula
## gamma_imperfect
family: imperfect
expr: 1 + (g_perf - 1)/(1 + (g_perf - 1)*((theta/T)**2*exp(theta/T)/(exp(theta/T) - 1)**2))
symbols: g_perf, theta, T
```

\[
a = \sqrt{\gamma R T}
\]

```formula
## speed_of_sound_imperfect
family: imperfect
expr: (g*R*T)**0.5
symbols: g, R, T
```

\[
M^{2} = \frac{2}{\gamma}\frac{T_t}{T}\left[\frac{\gamma_{\mathrm{perf}}}{\gamma_{\mathrm{perf}} - 1}\left(1 - \frac{T}{T_t}\right) + \frac{\theta}{T_t}\left(\frac{1}{e^{\theta/T_t} - 1} - \frac{1}{e^{\theta/T} - 1}\right)\right]
\]

```formula
## imperfect_mach
family: imperfect
expr: (2/g)*(Tt/T)*((g_perf/(g_perf - 1))*(1 - T/Tt) + (theta/Tt)*(1/(exp(theta/Tt) - 1) - 1/(exp(theta/T) - 1)))
symbols: g, Tt, T, g_perf, theta
```

\[
\frac{\rho}{\rho_t} = \frac{e^{\theta/T_t} - 1}{e^{\theta/T} - 1}\left(\frac{T}{T_t}\right)^{1/(\gamma_{\mathrm{perf}} - 1)}\exp\left[\frac{\theta}{T}\frac{e^{\theta/T}}{e^{\theta/T} - 1} - \frac{\theta}{T_t}\frac{e^{\theta/T_t}}{e^{\theta/T_t} - 1}\right]
\]

```formula
## imperfect_density_ratio
family: imperfect
expr: ((exp(theta/Tt) - 1)/(exp(theta/T) - 1))*(T/Tt)**(1/(g_perf - 1))*exp((theta/T)*exp(theta/T)/(exp(theta/T) - 1) - (theta/Tt)*exp(theta/Tt)/(exp(theta/Tt) - 1))
symbols: theta, Tt, T, g_perf
```

\[
\frac{p}{p_t} = \frac{e^{\theta/T_t} - 1}{e^{\theta/T} - 1}\left(\frac{T}{T_t}\right)^{\gamma_{\mathrm{perf}}/(\gamma_{\mathrm{perf}} - 1)}\exp\left[\frac{\theta}{T}\frac{e^{\theta/T}}{e^{\theta/T} - 1} - \frac{\theta}{T_t}\frac{e^{\theta/T_t}}{e^{\theta/T_t} - 1}\right]
\]

```formula
## imperfect_pressure_ratio
family: imperfect
expr: ((exp(theta/Tt) - 1)/(exp(theta/T) - 1))*(T/Tt)**(g_perf/(g_perf - 1))*exp((theta/T)*exp(theta/T)/(exp(theta/T) - 1) - (theta/Tt)*exp(theta/Tt)/(exp(theta/Tt) - 1))
symbols: theta, Tt, T, g_perf
```

\[
\frac{q}{p} = \frac{\gamma_{\mathrm{perf}}}{\gamma_{\mathrm{perf}} - 1}\left(\frac{T_t}{T} - 1\right) + \frac{\theta}{T}\left(\frac{1}{e^{\theta/T_t} - 1} - \frac{1}{e^{\theta/T} - 1}\right)
\]

```formula
## imperfect_dynamic_pressure
family: imperfect
expr: (g_perf/(g_perf - 1))*(Tt/T - 1) + (theta/T)*(1/(exp(theta/Tt) - 1) - 1/(exp(theta/T) - 1))
symbols: g_perf, Tt, T, theta
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\gamma\) | Local ratio of specific heats, including vibration | dimensionless |
| \(\gamma_{\mathrm{perf}}\) | Perfect-gas ratio of specific heats | dimensionless |
| \(\theta\) | Vibrational temperature constant | K |
| \(T\) | Static temperature | K |
| \(T_t\) | Total temperature | K |
| \(a\) | Speed of sound | m/s |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(M\) | Mach number | dimensionless |
| \(p, p_t\) | Static pressure and total pressure | Pa |
| \(\rho, \rho_t\) | Static density and total density | kg/m³ |
| \(q\) | Dynamic pressure | Pa |

Assumptions: thermally perfect gas with a simple-harmonic vibrational mode. Dissociation is not included. The Mach-number equation is solved iteratively for \(T_t\) when \(M\) and \(T\) are known. \(\gamma\) in that equation is the corrected ratio at the static temperature. These corrections matter for hypersonic air; at subsonic and low supersonic Mach numbers, use the perfect-gas isentropic relations instead.

## Ratio of specific heats for air

Engineering values of the corrected ratio \(\gamma\) for dry air. Temperatures in the source table are degrees Rankine; kelvin is \(T_{\mathrm{R}}\times 5/9\).

| \(T\) (°R) | \(T\) (K) | \(\gamma\) |
| --- | --- | --- |
| 500 | 278 | 1.400 |
| 600 | 333 | 1.399 |
| 700 | 389 | 1.398 |
| 800 | 444 | 1.396 |
| 900 | 500 | 1.392 |
| 1000 | 556 | 1.387 |
| 1100 | 611 | 1.375 |
| 1200 | 667 | 1.365 |
| 1300 | 722 | 1.361 |
| 1400 | 778 | 1.355 |
| 1500 | 833 | 1.349 |
| 1600 | 889 | 1.344 |
| 1700 | 944 | 1.339 |
| 1800 | 1000 | 1.335 |
| 1900 | 1056 | 1.330 |
| 2000 | 1111 | 1.326 |
| 2200 | 1222 | 1.322 |
| 2400 | 1333 | 1.317 |
| 2600 | 1444 | 1.313 |
| 2800 | 1556 | 1.309 |
| 3000 | 1667 | 1.306 |
| 3200 | 1778 | 1.305 |
| 3400 | 1889 | 1.304 |
| 3600 | 2000 | 1.301 |
| 3800 | 2111 | 1.301 |
| 4000 | 2222 | 1.298 |
| 4500 | 2500 | 1.296 |
| 5000 | 2778 | 1.294 |
| 5500 | 3056 | 1.294 |

Assumptions: these values are the NACA Report 1135 engineering approximation for air from \(400^\circ\mathrm{R}\) to \(5500^\circ\mathrm{R}\). They do not include chemical dissociation. Interpolate between neighboring rows. Below about \(500^\circ\mathrm{R}\), \(\gamma = 1.400\).

# Atmosphere

Defining relations of the U.S. Standard Atmosphere, 1976 (NASA TM-X-74335 / NOAA-S/T-76-1562), with the same closed-form layer equations as NASA TR R-459. Do not mix this model with the NASA Glenn three-zone curve fit at the end of the category. In this category \(R^{*}\) is the universal gas constant and \(M\) is molar mass. Geometric altitude is \(Z\); geopotential altitude is \(H\).

The air is dry and, below about 80 km, homogeneously mixed at constant mean molar mass \(M_0\). Hydrostatic balance and the perfect-gas law then give pressure and density from a piecewise-linear molecular-scale temperature in \(H\). That hydrostatic argument runs to \(Z = 86\,\mathrm{km}\) (\(H = 84.8520\,\mathrm{km}\)). Above 86 km the model switches to geometric altitude, a four-segment kinetic-temperature profile, and species number densities; total pressure is then the sum of partial pressures. Species diffusion above 86 km is not reduced to a single algebraic script here.

Adopted 1976 constants, unless the user gives others: \(g_0 = 9.80665\,\mathrm{m/s}^2\), \(T_0 = 288.15\,\mathrm{K}\), \(p_0 = 1.01325\times 10^{5}\,\mathrm{Pa}\), \(\rho_0 = 1.2250\,\mathrm{kg/m}^3\), \(r_0 = 6.356766\times 10^{6}\,\mathrm{m}\), \(M_0 = 28.9644\,\mathrm{kg/kmol}\), \(R^{*} = 8.31432\times 10^{3}\,\mathrm{N\cdot m/(kmol\cdot K)}\), \(\gamma = 1.4\), Boltzmann \(k = 1.380622\times 10^{-23}\,\mathrm{J/K}\), Avogadro \(N_A = 6.022169\times 10^{26}\,\mathrm{kmol}^{-1}\), collision diameter \(\sigma = 3.65\times 10^{-10}\,\mathrm{m}\). The 1976 \(R^{*}\) is the value adopted then; NIST CODATA 2022 lists the molar gas constant as exactly \(8.314462618\,\mathrm{J/(mol\cdot K)}\). Do not mix the two in one calculation.

Defining molecular-scale layers for \(0 \le H \le 84.8520\,\mathrm{km}\). Heights and gradients are in geopotential kilometres and kelvin per geopotential kilometre; convert to metres and K/m before substituting in the scripts.

| \(b\) | \(H_b\) (km) | \(L_{M,b}\) (K/km) | \(T_{M,b}\) (K) |
| --- | --- | --- | --- |
| 0 | 0 | \(-6.5\) | 288.15 |
| 1 | 11 | 0 | 216.65 |
| 2 | 20 | \(+1.0\) | 216.65 |
| 3 | 32 | \(+2.8\) | 228.65 |
| 4 | 47 | 0 | 270.65 |
| 5 | 51 | \(-2.8\) | 270.65 |
| 6 | 71 | \(-2.0\) | 214.65 |
| 7 | 84.8520 | — | 186.946 |

Each \(T_{M,b}\) after sea level follows from the linear layer that ends at that \(H_b\). Base pressures \(p_b\) for \(b \ge 1\) are the pressure at the top of the previous layer, starting from \(p_0\). Between 80 and 86 km the model lets \(M/M_0\) fall slightly below 1; for flight work take \(M = M_0\) through 86 km unless the user asks for that correction.

## Specific gas constant

Specific gas constant of a perfect gas of molar mass \(M\).

\[
R = \frac{R^{*}}{M}
\]

```formula
## specific_gas_constant
family: atmosphere
expr: Rstar/M
symbols: Rstar, M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(R^{*}\) | Universal (molar) gas constant | J/(kmol·K) |
| \(M\) | Molar mass | kg/kmol |

Assumptions: thermally perfect gas. With the 1976 dry-air \(M_0\) and \(R^{*}\), \(R = R^{*}/M_0 \approx 287.05\,\mathrm{J/(kg\cdot K)}\).

## Geopotential and geometric altitude

Geopotential altitude \(H\) from geometric altitude \(Z\) above the adopted Earth radius \(r_0\), and the inverse.

\[
H = \frac{r_0 Z}{r_0 + Z} \qquad
Z = \frac{r_0 H}{r_0 - H}
\]

```formula
## geopotential_altitude
family: atmosphere
expr: r0*Z/(r0 + Z)
symbols: r0, Z
```

```formula
## geometric_altitude
family: atmosphere
expr: r0*H/(r0 - H)
symbols: r0, H
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(H\) | Geopotential altitude | m |
| \(Z\) | Geometric altitude above \(r_0\) | m |
| \(r_0\) | Effective Earth radius used by the 1976 model | m |

Assumptions: the 1976 spherical conversion. At \(Z = 0\), \(H = 0\). \(H\) must stay below \(r_0\). Geopotential is the working argument only below 86 km.

## Gravity

Inverse-square gravity used to relate \(g\,\mathrm{d}Z\) to \(g_0\,\mathrm{d}H\).

\[
g = g_0\left(\frac{r_0}{r_0 + Z}\right)^2
\]

```formula
## gravity_inverse_square
family: atmosphere
expr: g0*(r0/(r0 + Z))**2
symbols: g0, r0, Z
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(g\) | Acceleration of gravity | m/s² |
| \(g_0\) | Sea-level gravity of the 1976 model | m/s² |
| \(r_0\) | Effective Earth radius | m |
| \(Z\) | Geometric altitude | m |

Assumptions: inverse-square field with the 1976 \(r_0\) that already includes the centrifugal contribution at the latitude where \(g_0 = 9.80665\,\mathrm{m/s}^2\).

## Hydrostatic balance

Vertical derivative of pressure in a still atmosphere, in geometric and geopotential altitude.

\[
\frac{\mathrm{d}p}{\mathrm{d}Z} = -g \rho \qquad
\frac{\mathrm{d}p}{\mathrm{d}H} = -g_0 \rho
\]

```formula
## hydrostatic_gradient
family: atmosphere
expr: -g*rho
symbols: g, rho
```

```formula
## hydrostatic_geopotential
family: atmosphere
expr: -g0*rho
symbols: g0, rho
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{d}p/\mathrm{d}Z\) | Pressure change with geometric altitude | Pa/m |
| \(\mathrm{d}p/\mathrm{d}H\) | Pressure change with geopotential altitude | Pa/m |
| \(g\) | Gravitational acceleration | m/s² |
| \(g_0\) | Sea-level gravity of the model | m/s² |
| \(\rho\) | Density | kg/m³ |

Assumptions: hydrostatic balance, no vertical acceleration. The geopotential form is the one integrated for \(H \le 84.8520\,\mathrm{km}\).

## Molecular-scale and kinetic temperature

Molecular-scale temperature folds a changing molar mass into the hydrostatic integral. While \(M = M_0\), it equals kinetic temperature.

\[
T_M = T\frac{M_0}{M} \qquad
T = T_M\frac{M}{M_0}
\]

```formula
## molecular_scale_temperature
family: atmosphere
expr: T*M0/M
symbols: T, M0, M
```

```formula
## kinetic_temperature
family: atmosphere
expr: TM*M/M0
symbols: TM, M, M0
```

Linear molecular-scale temperature in every constant-lapse layer below 86 km.

\[
T_M = T_{M,b} + L_{M,b}(H - H_b)
\]

```formula
## troposphere_temperature
family: atmosphere
expr: TMb + LMb*(H - Hb)
symbols: TMb, LMb, H, Hb
```

In the lowest 1976 layer, \(H_b = 0\), \(T_{M,b} = 288.15\,\mathrm{K}\), and \(L_{M,b} = -6.5\times 10^{-3}\,\mathrm{K/m}\), so \(T = 288.15 - 0.0065\,H\) with \(H\) in metres up to \(H = 11\,\mathrm{km}\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T_M\) | Molecular-scale temperature | K |
| \(T\) | Kinetic temperature | K |
| \(M\) | Mean molar mass | kg/kmol |
| \(M_0\) | Sea-level mean molar mass | kg/kmol |
| \(T_{M,b}\) | Molecular-scale temperature at the base of the layer | K |
| \(L_{M,b}\) | Molecular-scale temperature gradient of the layer | K/m |
| \(H\) | Geopotential altitude | m |
| \(H_b\) | Geopotential altitude at the base of the layer | m |

Assumptions: 1976 lower-atmosphere layers with constant \(L_{M,b}\). Below about 80 km, \(M = M_0\) and \(T_M = T\). The tropopause is at \(H = 11\,\mathrm{km}\), where \(T = 216.65\,\mathrm{K}\).

## Equation of state

Perfect-gas law for the mixture, and the molecular-scale form used below 86 km.

\[
p = \frac{\rho R^{*} T}{M} \qquad
\rho = \frac{p M}{R^{*} T} = \frac{p M_0}{R^{*} T_M}
\]

```formula
## atmosphere_equation_of_state
family: atmosphere
expr: rho*Rstar*T/M
symbols: rho, Rstar, T, M
```

```formula
## atmosphere_density
family: atmosphere
expr: p*M/(Rstar*T)
symbols: p, M, Rstar, T
```

```formula
## atmosphere_density_molecular
family: atmosphere
expr: p*M0/(Rstar*TM)
symbols: p, M0, Rstar, TM
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Pressure | Pa |
| \(\rho\) | Mass density | kg/m³ |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |
| \(T\) | Kinetic temperature | K |
| \(T_M\) | Molecular-scale temperature | K |
| \(M\) | Mean molar mass | kg/kmol |
| \(M_0\) | Sea-level mean molar mass | kg/kmol |

Assumptions: thermally perfect gas. The \(T_M\) density form is the working relation below 86 km.

## Layer pressure and density

Integrals of hydrostatic balance in a layer of constant \(L_{M,b}\). Use the power form when \(L_{M,b} \ne 0\) (layers \(b = 0,2,3,5,6\)) and the exponential form when \(L_{M,b} = 0\) (layers \(b = 1,4\)).

\[
p = p_b\left(\frac{T_{M,b}}{T_M}\right)^{g_0 M_0/(R^{*} L_{M,b})}
\qquad
p = p_b\exp\left(-\frac{g_0 M_0(H - H_b)}{R^{*} T_{M,b}}\right)
\]

```formula
## gradient_layer_pressure
family: atmosphere
expr: pb*(TMb/TM)**(g0*M0/(Rstar*LMb))
symbols: pb, TMb, TM, g0, M0, Rstar, LMb
```

```formula
## isothermal_layer_pressure
family: atmosphere
expr: pb*exp(-g0*M0*(H - Hb)/(Rstar*TMb))
symbols: pb, g0, M0, H, Hb, Rstar, TMb
```

\[
\rho = \rho_b\left(\frac{T_{M,b}}{T_M}\right)^{g_0 M_0/(R^{*} L_{M,b})+1}
\qquad
\rho = \rho_b\exp\left(-\frac{g_0 M_0(H - H_b)}{R^{*} T_{M,b}}\right)
\]

```formula
## gradient_layer_density
family: atmosphere
expr: rhob*(TMb/TM)**(g0*M0/(Rstar*LMb) + 1)
symbols: rhob, TMb, TM, g0, M0, Rstar, LMb
```

```formula
## isothermal_layer_density
family: atmosphere
expr: rhob*exp(-g0*M0*(H - Hb)/(Rstar*TMb))
symbols: rhob, g0, M0, H, Hb, Rstar, TMb
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Pressure | Pa |
| \(p_b\) | Pressure at the base of the layer | Pa |
| \(\rho\) | Density | kg/m³ |
| \(\rho_b\) | Density at the base of the layer | kg/m³ |
| \(T_M\) | Molecular-scale temperature in the layer | K |
| \(T_{M,b}\) | Molecular-scale temperature at the base | K |
| \(L_{M,b}\) | Molecular-scale lapse of the layer | K/m |
| \(H\), \(H_b\) | Geopotential altitude and layer base | m |
| \(g_0\) | Sea-level gravity | m/s² |
| \(M_0\) | Sea-level molar mass | kg/kmol |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |

Assumptions: hydrostatic perfect gas, \(M = M_0\), \(T_M\) linear or constant in the layer. Evaluate \(T_M\) from `troposphere_temperature` at the same \(H\). Do not use the power form at \(L_{M,b} = 0\).

## Number density and partial pressure

Total number density of neutral particles, mixing-region species density, and Dalton partial pressure.

\[
N = \frac{p}{k T} \qquad
n_i = F_i N \qquad
p_i = n_i k T
\]

```formula
## number_density
family: atmosphere
expr: p/(kB*T)
symbols: p, kB, T
```

```formula
## species_number_density
family: atmosphere
expr: Fi*N
symbols: Fi, N
```

```formula
## atmosphere_partial_pressure
family: atmosphere
expr: ni*kB*T
symbols: ni, kB, T
```

Sea-level volume fractions of the 1976 dry-air mixture include \(F(\mathrm{N}_2) = 0.78084\), \(F(\mathrm{O}_2) = 0.209476\), and \(F(\mathrm{Ar}) = 0.00934\). Above 86 km, \(p = N k T\) still holds, but each \(n_i\) is integrated from the species flux equation rather than from a constant \(F_i\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(N\) | Total number density | m\(^{-3}\) |
| \(n_i\) | Number density of species \(i\) | m\(^{-3}\) |
| \(F_i\) | Volume fraction of species \(i\) | dimensionless |
| \(p_i\) | Partial pressure of species \(i\) | Pa |
| \(p\) | Total pressure | Pa |
| \(k\) | Boltzmann constant | J/K |
| \(T\) | Kinetic temperature | K |

Assumptions: ideal mixture. \(n_i = F_i N\) applies in the mixed region below about 80 km.

## Pressure scale height

Geometric and geopotential pressure scale heights of the mixture.

\[
H_p = \frac{R^{*} T}{g M} = \frac{R^{*} T_M}{g M_0}
\qquad
H_p' = \frac{R^{*} T_M}{g_0 M_0}
\]

```formula
## pressure_scale_height
family: atmosphere
expr: Rstar*T/(g*M)
symbols: Rstar, T, g, M
```

```formula
## geopotential_pressure_scale_height
family: atmosphere
expr: Rstar*TM/(g0*M0)
symbols: Rstar, TM, g0, M0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(H_p\) | Geometric pressure scale height | m |
| \(H_p'\) | Geopotential pressure scale height | m |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |
| \(T\) | Kinetic temperature | K |
| \(T_M\) | Molecular-scale temperature | K |
| \(g\) | Local gravity | m/s² |
| \(g_0\) | Sea-level gravity | m/s² |
| \(M\), \(M_0\) | Local and sea-level molar mass | kg/kmol |

Assumptions: local hydrostatic slope of \(\ln p\). In an isothermal geopotential layer, pressure falls by \(1/e\) over one \(H_p'\). \(H_p\) is only approximate in the 80–120 km mixing-to-diffusion transition and in the exosphere.

## Speed of sound

\[
c_s = \sqrt{\frac{\gamma R^{*} T_M}{M_0}} = \sqrt{\gamma R T}
\]

```formula
## atmosphere_sound_speed
family: atmosphere
expr: (g*Rstar*TM/M0)**0.5
symbols: g, Rstar, TM, M0
```

The 1976 model takes \(\gamma = 1.4\). At sea level this gives \(c_s \approx 340.29\,\mathrm{m/s}\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_s\) | Speed of sound | m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |
| \(T_M\) | Molecular-scale temperature | K |
| \(M_0\) | Sea-level molar mass | kg/kmol |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(T\) | Kinetic temperature | K |

Assumptions: small perturbation, calorically perfect air. The 1976 tables stop listing \(c_s\) above 86 km because attenuation grows with mean free path.

## Viscosity, conductivity, and kinetic-theory lengths

Dynamic viscosity of air from the 1976 Sutherland fit.

\[
\mu = \frac{\beta T^{3/2}}{T + S}
\]

```formula
## sutherland_viscosity
family: atmosphere
expr: beta*T**1.5/(T + S)
symbols: beta, T, S
```

The 1976 constants are \(\beta = 1.458\times 10^{-6}\,\mathrm{kg/(s\cdot m\cdot K^{1/2})}\) and \(S = 110.4\,\mathrm{K}\). Kinematic viscosity is \(\nu = \mu/\rho\), already recorded as `kinematic_viscosity` in Compressible flow.

Thermal conductivity of air in the same tables.

\[
k_t = \frac{k_0 T^{3/2}}{T + C\,10^{-12/T}}
\]

```formula
## thermal_conductivity_air
family: atmosphere
expr: k0*T**1.5/(T + C*10**(-12/T))
symbols: k0, T, C
```

The 1976 constants are \(k_0 = 2.64638\times 10^{-3}\,\mathrm{W/(m\cdot K^{3/2})}\) and \(C = 245.4\,\mathrm{K}\).

Mean thermal speed, mean free path, and collision frequency of the neutral mixture.

\[
\bar{V} = \sqrt{\frac{8 R^{*} T}{\pi M}}
\qquad
L = \frac{R^{*} T}{\sqrt{2}\,\pi\sigma^2 N_A p}
\qquad
\nu_c = \frac{\bar{V}}{L}
\]

```formula
## mean_particle_speed
family: atmosphere
expr: (8*Rstar*T/(pi*M))**0.5
symbols: Rstar, T, M, pi
```

```formula
## mean_free_path
family: atmosphere
expr: Rstar*T/(2**0.5*pi*sigma**2*NA*p)
symbols: Rstar, T, sigma, NA, p, pi
```

```formula
## collision_frequency
family: atmosphere
expr: Vbar/L
symbols: Vbar, L
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mu\) | Dynamic viscosity | Pa·s |
| \(\beta\) | Sutherland coefficient | kg/(s·m·K\(^{1/2}\)) |
| \(S\) | Sutherland temperature | K |
| \(k_t\) | Thermal conductivity | W/(m·K) |
| \(k_0\) | Conductivity coefficient | W/(m·K\(^{3/2}\)) |
| \(C\) | Conductivity temperature constant | K |
| \(T\) | Kinetic temperature | K |
| \(\bar{V}\) | Mean particle speed | m/s |
| \(L\) | Mean free path | m |
| \(\nu_c\) | Mean collision frequency | s\(^{-1}\) |
| \(\sigma\) | Effective collision diameter | m |
| \(N_A\) | Avogadro constant | kmol\(^{-1}\) |
| \(p\) | Pressure | Pa |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |
| \(M\) | Mean molar mass | kg/kmol |

Assumptions: dry air, continuum. Viscosity and conductivity are tabulated only to 86 km. \(\sigma = 3.65\times 10^{-10}\,\mathrm{m}\) is a sea-level dry-air value; it is a poorer constant once atomic oxygen dominates. NASA Glenn's educational viscosity page writes Sutherland's law in Rankine; convert units before mixing that form with SI.

## Kinetic temperature above 86 km

Above \(Z_7 = 86\,\mathrm{km}\) the argument is geometric altitude. Kinetic temperature is continuous with a continuous first derivative. Linear segments cover the isothermal mesopause \(86\)–\(91\,\mathrm{km}\) (\(T_7 = 186.8673\,\mathrm{K}\), \(L_{K,7} = 0\)) and the \(110\)–\(120\,\mathrm{km}\) ramp (\(T_9 = 240\,\mathrm{K}\), \(L_{K,9} = 12\,\mathrm{K/km}\)).

\[
T = T_b + L_{K,b}(Z - Z_b)
\]

```formula
## kinetic_temperature_linear
family: atmosphere
expr: Tb + LKb*(Z - Zb)
symbols: Tb, LKb, Z, Zb
```

From 91 to 110 km the profile is an ellipse segment that matches \(T_8 = T_7\) with zero slope at 91 km and \(T_9\), \(L_{K,9}\) at 110 km.

\[
T = T_c + A\left[1 - \left(\frac{Z - Z_8}{a}\right)^2\right]^{1/2}
\]

```formula
## mesosphere_ellipse_temperature
family: atmosphere
expr: Tc + A*(1 - ((Z - Z8)/a)**2)**0.5
symbols: Tc, A, Z, Z8, a
```

The 1976 constants are \(T_c = 263.1905\,\mathrm{K}\), \(A = -76.3232\,\mathrm{K}\), \(a = -19.9429\,\mathrm{km}\), and \(Z_8 = 91\,\mathrm{km}\). Keep \(Z\) and \(a\) in the same length unit.

From 120 to 1000 km the temperature approaches the exospheric value \(T_\infty = 1000\,\mathrm{K}\) (mean solar activity) from \(T_{10} = 360\,\mathrm{K}\) at \(Z_{10} = 120\,\mathrm{km}\).

\[
\xi = (Z - Z_{10})\frac{r_0 + Z_{10}}{r_0 + Z}
\qquad
T = T_\infty - (T_\infty - T_{10})\exp(-\lambda\xi)
\]

with \(\lambda = L_{K,9}/(T_\infty - T_{10}) = 0.01875\,\mathrm{km}^{-1}\).

```formula
## reduced_geopotential
family: atmosphere
expr: (Z - Zb)*(r0 + Zb)/(r0 + Z)
symbols: Z, Zb, r0
```

```formula
## exospheric_temperature
family: atmosphere
expr: Tinf - (Tinf - Tb)*exp(-lam*xi)
symbols: Tinf, Tb, lam, xi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T\) | Kinetic temperature | K |
| \(T_b\) | Temperature at the base of a linear or Bates layer | K |
| \(L_{K,b}\) | Kinetic-temperature gradient | K/m |
| \(Z\), \(Z_b\) | Geometric altitude and layer base | m |
| \(T_c\), \(A\), \(a\) | Ellipse centre temperature, amplitude, and semi-axis | K, K, m |
| \(Z_8\) | Base of the ellipse layer | m |
| \(\xi\) | Reduced height above \(Z_{10}\) | m |
| \(T_\infty\) | Exospheric temperature | K |
| \(\lambda\) | Bates inverse-length | m\(^{-1}\) |
| \(r_0\) | Effective Earth radius | m |

Assumptions: 1976 four-segment profile. Pressure and density above 86 km are not closed algebraic functions of \(Z\) alone; they need the species number densities of that model.

## Glenn three-zone curve fit

NASA Glenn's educational Earth-atmosphere model is a 1960s three-zone fit in geometric altitude \(h\), not the 1976 standard. Convert Glenn's published Celsius temperatures with their offset \(273.1\) so the scripts stay in kelvin and pascal. Do not mix these constants with the 1976 layer table.

Troposphere, \(0 \le h \le 11000\,\mathrm{m}\): \(T = 288.14 - 0.00649\,h\) (use `troposphere_temperature` with those constants). Lower stratosphere, \(11000\,\mathrm{m} < h \le 25000\,\mathrm{m}\): \(T = 216.64\,\mathrm{K}\). Upper stratosphere, \(h > 25000\,\mathrm{m}\): \(T = 141.89 + 0.00299\,h\).

\[
p = p_{\mathrm{ref}}\left(\frac{T}{T_{\mathrm{ref}}}\right)^{n}
\qquad
p = p_{\mathrm{ref}}\exp(A - B h)
\qquad
\rho = \frac{p}{R T}
\]

```formula
## glenn_zone_pressure_power
family: atmosphere
expr: pref*(T/Tref)**n
symbols: pref, T, Tref, n
```

```formula
## glenn_zone_pressure_exponential
family: atmosphere
expr: pref*exp(A - B*h)
symbols: pref, A, B, h
```

```formula
## glenn_density
family: atmosphere
expr: p/(R*T)
symbols: p, R, T
```

Glenn's published metric constants, after conversion to Pa and K: troposphere \(p_{\mathrm{ref}} = 1.0129\times 10^{5}\,\mathrm{Pa}\), \(T_{\mathrm{ref}} = 288.08\,\mathrm{K}\), \(n = 5.256\); lower stratosphere \(p_{\mathrm{ref}} = 2.265\times 10^{4}\,\mathrm{Pa}\), \(A = 1.73\), \(B = 1.57\times 10^{-4}\,\mathrm{m}^{-1}\); upper stratosphere \(p_{\mathrm{ref}} = 2.488\times 10^{3}\,\mathrm{Pa}\), \(T_{\mathrm{ref}} = 216.6\,\mathrm{K}\), \(n = -11.388\); \(R = 286.9\,\mathrm{J/(kg\cdot K)}\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Pressure | Pa |
| \(p_{\mathrm{ref}}\) | Zone reference pressure | Pa |
| \(T\) | Temperature on Glenn's \(t + 273.1\) scale | K |
| \(T_{\mathrm{ref}}\) | Zone reference temperature | K |
| \(n\) | Zone pressure exponent | dimensionless |
| \(A\), \(B\) | Lower-stratosphere exponential coefficients | dimensionless, m\(^{-1}\) |
| \(h\) | Geometric altitude | m |
| \(\rho\) | Density | kg/m³ |
| \(R\) | Glenn specific gas constant | J/(kg·K) |

Assumptions: altitude-only curve fit for FoilSim-type estimates. Temperature and pressure change only with height. The fit is not hydrostatic 1976 and is not valid as a thermosphere model.

# Rocket propulsion

Vehicle and motor performance. In this category \(k\) is the ratio of specific heats. Nozzle area ratio and isentropic exit state use the Area-Mach and stagnation relations in Compressible flow. In the mass-flow section, \(V\) is specific volume.

## Average exhaust velocity

Nozzle-exit velocity of an ideal rocket. The inlet velocity is taken as zero.

\[
v_2 = c - \frac{(p_2 - p_3)A_2}{\dot{m}}
\]

```formula
## exhaust_velocity_from_effective
family: rocket
expr: c - (p2 - p3)*A2/mdot
symbols: c, p2, p3, A2, mdot
```

When \(p_2 = p_3\), this reduces to \(v_2 = c\).

Ideal isentropic expansion of a calorically perfect gas:

\[
v_2 = \sqrt{\frac{2k}{k-1} R T_1 \left[1 - \left(\frac{p_2}{p_1}\right)^{(k-1)/k}\right]}
\]

```formula
## exhaust_velocity_isentropic
family: rocket
expr: ((2*k/(k - 1))*R*T1*(1 - (p2/p1)**((k - 1)/k)))**0.5
symbols: k, R, T1, p2, p1
```

From the energy equation, with inlet velocity approximately zero:

\[
v_2 = \sqrt{2(h_1 - h_2)}
\]

```formula
## exhaust_velocity_enthalpy
family: rocket
expr: (2*(h1 - h2))**0.5
symbols: h1, h2
```

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

```formula
## effective_exhaust_velocity
family: rocket
expr: F/mdot
symbols: F, mdot
```

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

## Equivalent exhaust velocity

Nozzle-exit speed plus the pressure-thrust contribution used on NASA Glenn's specific-impulse page.

\[
V_{\mathrm{eq}} = v_2 + \frac{(p_2 - p_3)A_2}{\dot{m}}
\]

```formula
## equivalent_exhaust_velocity
family: rocket
expr: v2 + (p2 - p3)*A2/mdot
symbols: v2, p2, p3, A2, mdot
```

Then \(F = \dot{m} V_{\mathrm{eq}}\) and \(I_s = V_{\mathrm{eq}}/g_0\). \(V_{\mathrm{eq}}\) is the same quantity as effective exhaust velocity \(c\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_{\mathrm{eq}}\) | Equivalent exhaust velocity | m/s |
| \(v_2\) | Average nozzle-exit velocity | m/s |
| \(p_2\) | Nozzle-exit pressure | Pa |
| \(p_3\) | Ambient pressure | Pa |
| \(A_2\) | Nozzle-exit area | m² |
| \(\dot{m}\) | Propellant mass flow rate | kg/s |

Assumptions: steady one-dimensional rocket thrust with negligible inlet momentum. When \(p_2 = p_3\), \(V_{\mathrm{eq}} = v_2\).

## Thrust

Force on the vehicle from exhaust momentum and the pressure imbalance at the exit plane.

\[
F = \dot{m} v_2 + (p_2 - p_3) A_2
\]

```formula
## thrust_momentum
family: rocket
expr: mdot*v2 + (p2 - p3)*A2
symbols: mdot, v2, p2, p3, A2
```

\[
F = C_F p_1 A_t
\]

```formula
## thrust_coefficient_form
family: rocket
expr: CF*p1*At
symbols: CF, p1, At
```

For a constant burn at constant effective exhaust velocity, \(\dot{m} = m_p / t_p\), so

\[
F = \frac{c m_p}{t_p}
\]

```formula
## thrust_constant_burn
family: rocket
expr: c*mp/tp
symbols: c, mp, tp
```

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

```formula
## characteristic_velocity
family: rocket
expr: p1*At/mdot
symbols: p1, At, mdot
```

Ideal value for a calorically perfect gas:

\[
c^{*} = \frac{\sqrt{k R T_1}}{k \sqrt{\left(\dfrac{2}{k+1}\right)^{(k+1)/(k-1)}}}
\]

```formula
## characteristic_velocity_ideal
family: rocket
expr: (k*R*T1)**0.5/(k*((2/(k + 1))**((k + 1)/(k - 1)))**0.5)
symbols: k, R, T1
```

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

```formula
## thrust_coefficient_definition
family: rocket
expr: F/(p1*At)
symbols: F, p1, At
```

Ideal nozzle, including pressure thrust:

\[
C_F = \sqrt{\frac{2k^{2}}{k-1}\left(\frac{2}{k+1}\right)^{(k+1)/(k-1)}\left[1 - \left(\frac{p_2}{p_1}\right)^{(k-1)/k}\right]} + \frac{p_2 - p_3}{p_1}\frac{A_2}{A_t}
\]

```formula
## thrust_coefficient_ideal
family: rocket
expr: ((2*k**2/(k - 1))*((2/(k + 1))**((k + 1)/(k - 1)))*(1 - (p2/p1)**((k - 1)/k)))**0.5 + (p2 - p3)/p1*A2/At
symbols: k, p2, p1, p3, A2, At
```

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

```formula
## total_impulse
family: rocket
expr: integral(F, t)
symbols: F, t
```

For constant thrust over burn time \(t\),

\[
I_t = F t
\]

```formula
## total_impulse_constant_thrust
family: rocket
expr: F*t
symbols: F, t
```

\[
I_s = \frac{c}{g_0} = \frac{c^{*} C_F}{g_0} = \frac{F}{\dot{m} g_0} = \frac{F}{\dot{w}} = \frac{I_t}{m_p g_0} = \frac{I_t}{w}
\]

```formula
## specific_impulse
family: rocket
expr: c/g0
symbols: c, g0
```

Substituting the thrust equation gives the exit-condition form

\[
I_s = \frac{v_2}{g_0} + \frac{(p_2 - p_3) A_2}{\dot{m} g_0}
\]

```formula
## specific_impulse_exit
family: rocket
expr: v2/g0 + (p2 - p3)*A2/(mdot*g0)
symbols: v2, g0, p2, p3, A2, mdot
```

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

```formula
## propellant_mass_fraction
family: rocket
expr: mp/m0
symbols: mp, m0
```

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

```formula
## mass_ratio
family: rocket
expr: mf/m0
symbols: mf, m0
```

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

```formula
## delta_v_vacuum
family: rocket
expr: c*log(m0/mf)
symbols: c, m0, mf
```

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

```formula
## mass_flow_continuity
family: rocket
expr: A*v/V
symbols: A, v, V
```

\[
\dot{m} = \frac{F}{c} = \frac{p_1 A_t}{c^{*}}
\]

```formula
## mass_flow_from_thrust
family: rocket
expr: F/c
symbols: F, c
```

Ideal choked flow:

\[
\dot{m} = p_1 A_t k \frac{\sqrt{\left(\dfrac{2}{k+1}\right)^{(k+1)/(k-1)}}}{\sqrt{k R T_1}}
\]

```formula
## mass_flow_ideal
family: rocket
expr: p1*At*k*((2/(k + 1))**((k + 1)/(k - 1)))**0.5/(k*R*T1)**0.5
symbols: p1, At, k, R, T1
```

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

## Nozzle area ratio

Exit area divided by throat area.

\[
\epsilon = \frac{A_2}{A_t}
\]

```formula
## nozzle_area_ratio
family: rocket
expr: A2/At
symbols: A2, At
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\epsilon\) | Nozzle area ratio | dimensionless |
| \(A_2\) | Nozzle-exit area | m² |
| \(A_t\) | Nozzle throat area | m² |
| \(M_2\) | Nozzle-exit Mach number | dimensionless |
| \(k\) | Ratio of specific heats | dimensionless |

Assumptions: for isentropic flow, \(\epsilon(M_2, k)\) is the Area-Mach relation with \(A/A^{*} = \epsilon\), \(M = M_2\), and \(\gamma = k\). That expression is not repeated here.

## Satellite velocity in a circular orbit

Circular-orbit speed at altitude \(h\) above a spherical planet.

\[
u_s = R_0 \sqrt{\frac{g_0}{R_0 + h}}
\]

```formula
## circular_orbit_velocity
family: flight
expr: R0*(g0/(R0 + h))**0.5
symbols: R0, g0, h
```

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

```formula
## escape_velocity
family: flight
expr: R0*(2*g0/(R0 + h))**0.5
symbols: R0, g0, h
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v_e\) | Escape velocity | m/s |
| \(R_0\) | Effective planetary radius | m |
| \(g_0\) | Gravitational acceleration at the planetary surface | m/s² |
| \(h\) | Altitude above the surface | m |

Assumptions: spherical planet and inverse-square gravity, neglecting atmosphere. \(v_e\) here is escape speed, not exhaust velocity. For Earth, use \(R_0 = 6.3742 \times 10^{6}\,\text{m}\) unless the user gives another value.

## Gravitational parameter

Standard gravitational parameter of a central body, \(\mu = GM\).

\[
\mu = G M
\]

```formula
## gravitational_parameter
family: flight
expr: G*M
symbols: G, M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(G\) | Newtonian gravitational constant | m³/(kg·s²) |
| \(M\) | Mass of the central body | kg |

Assumptions: point-mass or spherical inverse-square gravity. NIST CODATA 2022 gives \(G = 6.67430\times 10^{-11}\,\mathrm{m}^3\,\mathrm{kg}^{-1}\,\mathrm{s}^{-2}\). For Earth, \(\mu \approx g_0 R_0^{2}\) with the radius used in the circular-orbit and escape formulas. In this section \(M\) is mass, not Mach number or moment.

## Vis-viva speed

Relative speed on a Keplerian two-body orbit, from conservation of specific mechanical energy. NASA SP *The Orbital Mechanics of Flight Mechanics* develops the inverse-square two-body problem from which this follows.

\[
v = \sqrt{\mu\left(\frac{2}{r} - \frac{1}{a}\right)}
\]

```formula
## vis_viva
family: flight
expr: (mu*(2/r - 1/a))**0.5
symbols: mu, r, a
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v\) | Relative orbital speed | m/s |
| \(\mu\) | Gravitational parameter of the central body | m³/s² |
| \(r\) | Radial distance from the attracting centre | m |
| \(a\) | Semi-major axis | m |

Assumptions: two-body inverse-square gravity and no drag or thrust. \(a > 0\) on an ellipse, \(1/a = 0\) on a parabola, and \(a < 0\) on a hyperbola. A circular orbit has \(a = r\), which recovers \(v = \sqrt{\mu/r}\). Escape speed is the parabolic case \(v = \sqrt{2\mu/r}\).

## Specific orbital energy

Specific mechanical energy of a two-body orbit.

\[
\varepsilon = \frac{v^{2}}{2} - \frac{\mu}{r} = -\frac{\mu}{2a}
\]

```formula
## specific_orbital_energy
family: flight
expr: -(mu)/(2*a)
symbols: mu, a
```

```formula
## specific_orbital_energy_from_speed
family: flight
expr: v**2/2 - mu/r
symbols: v, mu, r
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\varepsilon\) | Specific orbital energy | J/kg |
| \(v\) | Relative orbital speed | m/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(r\) | Radial distance | m |
| \(a\) | Semi-major axis | m |

Assumptions: two-body inverse-square gravity. \(\varepsilon < 0\) is an ellipse, \(\varepsilon = 0\) a parabola, and \(\varepsilon > 0\) a hyperbola.

## Orbital period

Period of an elliptic two-body orbit (Kepler's third law in Newtonian form).

\[
T = 2\pi\sqrt{\frac{a^{3}}{\mu}}
\]

```formula
## orbital_period
family: flight
expr: 2*pi*(a**3/mu)**0.5
symbols: a, mu, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T\) | Orbital period | s |
| \(a\) | Semi-major axis | m |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: unperturbed elliptic two-body motion. For two comparable masses replace \(\mu\) by \(G(m_1+m_2)\). A circular orbit uses \(a = r\).

## Periapsis, apoapsis, and eccentricity

Radial extremes of an ellipse, and eccentricity from those radii.

\[
r_p = a(1 - e) \qquad r_a = a(1 + e) \qquad e = \frac{r_a - r_p}{r_a + r_p}
\]

```formula
## periapsis_radius
family: flight
expr: a*(1 - e)
symbols: a, e
```

```formula
## apoapsis_radius
family: flight
expr: a*(1 + e)
symbols: a, e
```

```formula
## orbit_eccentricity
family: flight
expr: (ra - rp)/(ra + rp)
symbols: ra, rp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r_p\) | Periapsis radius | m |
| \(r_a\) | Apoapsis radius | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |

Assumptions: elliptic orbit with \(0 \le e < 1\) and \(r_a \ge r_p > 0\). Then \(a = (r_a + r_p)/2\). In this section \(e\) is eccentricity, not Oswald efficiency and not the base of the natural logarithm.

## Classical orbital elements

Six quantities fix a Keplerian ellipse in space. NASA SP-325 and Plummer (1918) use the same set, with the names in NASA *Basics of Space Flight*:

- semi-major axis \(a\) and eccentricity \(e\), which fix the size and shape
- inclination \(i\) of the orbit plane to the reference plane
- longitude of the ascending node \(\Omega\)
- argument of periapsis \(\omega\), measured in the orbit plane from the ascending node to periapsis
- a time element: the time of periapsis passage \(t_p\), or the mean anomaly at a chosen epoch

The position in the orbit plane is the true anomaly \(\nu\), measured from periapsis in the direction of motion. The eccentric anomaly \(E\) is the angle at the centre of the auxiliary circle. The mean anomaly \(M\) grows uniformly with time. All three anomalies below are in radians. In these records \(M\) is mean anomaly, not mass or Mach number; \(n\) is mean motion; \(p\) is the semi-latus rectum, not pressure; and \(h\) is specific angular momentum, not altitude.

## Semi-latus rectum and semi-minor axis

The parameter of the conic, and the semi-minor axis of an ellipse. NASA SP-325 writes \(p = a(1-e^{2})\) and \(p = h^{2}/\mu\).

\[
p = a(1 - e^{2}) \qquad b = a\sqrt{1 - e^{2}}
\]

```formula
## semi_latus_rectum
family: flight
expr: a*(1 - e**2)
symbols: a, e
```

```formula
## semi_minor_axis
family: flight
expr: a*(1 - e**2)**0.5
symbols: a, e
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Semi-latus rectum | m |
| \(b\) | Semi-minor axis | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |

Assumptions: ellipse with \(0 \le e < 1\). Then \(p = b^{2}/a\), and \(p = r_p(1+e) = r_a(1-e)\).

## Orbit equation

Radial distance on a conic with one focus at the attracting centre. NASA SP-325 gives the polar equation \(r = p/(1+e\cos\nu)\) and, on an ellipse, \(r = a(1-e^{2})/(1+e\cos\nu)\).

\[
r = \frac{p}{1 + e\cos\nu} = \frac{a(1 - e^{2})}{1 + e\cos\nu}
\]

```formula
## conic_radius
family: flight
expr: a*(1 - e**2)/(1 + e*cos(nu))
symbols: a, e, nu
```

```formula
## conic_radius_from_parameter
family: flight
expr: p/(1 + e*cos(nu))
symbols: p, e, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r\) | Radial distance from the attracting focus | m |
| \(p\) | Semi-latus rectum | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |
| \(\nu\) | True anomaly | rad |

Assumptions: two-body inverse-square gravity. \(\nu = 0\) at periapsis. The form in \(a\) is for an ellipse, \(0 \le e < 1\). The form in \(p\) is the conic itself: \(e = 0\) a circle, \(0 < e < 1\) an ellipse, \(e = 1\) a parabola, and \(e > 1\) a hyperbola, provided the denominator stays positive.

## Specific angular momentum

Magnitude of the specific angular momentum on a Keplerian conic. NASA SP-325 defines the semi-latus rectum by \(p = h^{2}/\mu\).

\[
h = \sqrt{\mu p}
\]

```formula
## specific_angular_momentum
family: flight
expr: (mu*p)**0.5
symbols: mu, p
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h\) | Specific angular momentum | m²/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(p\) | Semi-latus rectum | m |

Assumptions: planar two-body motion. \(h\) here is not altitude. The direction is normal to the orbit plane.

## Mean motion

Constant average angular rate of an elliptic orbit. NASA SP-325 defines \(n = 2\pi/T\) and the same rate from the semi-major axis. Plummer writes \(n^{2}a^{3} = \mu\).

\[
n = \sqrt{\frac{\mu}{a^{3}}} = \frac{2\pi}{T}
\]

```formula
## mean_motion
family: flight
expr: (mu/a**3)**0.5
symbols: mu, a
```

```formula
## mean_motion_from_period
family: flight
expr: 2*pi/T
symbols: pi, T
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(n\) | Mean motion | rad/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(a\) | Semi-major axis | m |
| \(T\) | Orbital period | s |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: unperturbed elliptic two-body motion, \(a > 0\). The two expressions agree with `orbital_period`. For two comparable masses replace \(\mu\) by \(G(m_1+m_2)\).

## Mean anomaly

Angle that advances uniformly at the mean motion, zero at periapsis. NASA SP-325 and Plummer both write \(M = n(t - t_p)\).

\[
M = n(t - t_p)
\]

```formula
## mean_anomaly
family: flight
expr: n*(t - tp)
symbols: n, t, tp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mean anomaly | rad |
| \(n\) | Mean motion | rad/s |
| \(t\) | Time | s |
| \(t_p\) | Time of periapsis passage | s |

Assumptions: \(M = 0\) at periapsis. If the epoch \(t_0\) is not periapsis, use \(M = M_0 + n(t - t_0)\) with \(M_0\) the mean anomaly at \(t_0\). In this record \(M\) is not mass and not Mach number.

## Kepler's equation

Relation between mean anomaly and eccentric anomaly on an ellipse. NASA SP-325 and NASA TN D-6712 state \(M = E - e\sin E\). The eccentric anomaly is defined by this equation; it is not an algebraic explicit function of \(M\).

\[
M = E - e\sin E
\]

```formula
## kepler_equation
family: flight
expr: E - e*sin(E)
symbols: E, e
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mean anomaly | rad |
| \(E\) | Eccentric anomaly | rad |
| \(e\) | Eccentricity | dimensionless |

Assumptions: ellipse, \(0 \le e < 1\), with \(M\) and \(E\) in radians and in the same branch. The record evaluates \(M\) from a known \(E\). Given \(M\), solve the same equation for \(E\). At periapsis, \(M = E = 0\). A circular orbit has \(E = M = \nu\).

## Radius from the eccentric anomaly

Distance from the focus in terms of the eccentric anomaly. NASA SP-325 equation (1-81).

\[
r = a(1 - e\cos E)
\]

```formula
## radius_from_eccentric_anomaly
family: flight
expr: a*(1 - e*cos(E))
symbols: a, e, E
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r\) | Radial distance from the attracting focus | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |
| \(E\) | Eccentric anomaly | rad |

Assumptions: ellipse, \(0 \le e < 1\). \(E = 0\) gives periapsis \(r = a(1-e)\), and \(E = \pi\) gives apoapsis \(r = a(1+e)\).

## True anomaly from the eccentric anomaly

NASA SP-325 equations (1-90) and (1-91). Plummer’s half-angle relation, with his auxiliary angle removed, is the third formula. It returns \(\nu\) itself on \((-\pi, \pi)\).

\[
\cos\nu = \frac{\cos E - e}{1 - e\cos E} \qquad
\sin\nu = \frac{\sqrt{1 - e^{2}}\,\sin E}{1 - e\cos E} \qquad
\nu = 2\arctan\left(\sqrt{\frac{1+e}{1-e}}\tan\frac{E}{2}\right)
\]

```formula
## true_anomaly_cosine
family: flight
expr: (cos(E) - e)/(1 - e*cos(E))
symbols: E, e
```

```formula
## true_anomaly_sine
family: flight
expr: ((1 - e**2)**0.5)*sin(E)/(1 - e*cos(E))
symbols: E, e
```

```formula
## true_anomaly
family: flight
expr: 2*atan(((1 + e)/(1 - e))**0.5*tan(E/2))
symbols: e, E
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\nu\) | True anomaly | rad |
| \(E\) | Eccentric anomaly | rad |
| \(e\) | Eccentricity | dimensionless |

Assumptions: ellipse, \(0 \le e < 1\). The sine and cosine pair fixes the quadrant. `true_anomaly` is valid for \(-\pi < E < \pi\); \(\tan(E/2)\) is undefined at \(E = \pm\pi\), where \(\nu = \pm\pi\) as well. \(E = 0\) gives \(\nu = 0\).

## Eccentric anomaly from the true anomaly

The inverse of the previous trio. Plummer states the cosine form and the half-angle form.

\[
\cos E = \frac{e + \cos\nu}{1 + e\cos\nu} \qquad
\sin E = \frac{\sqrt{1 - e^{2}}\,\sin\nu}{1 + e\cos\nu} \qquad
E = 2\arctan\left(\sqrt{\frac{1-e}{1+e}}\tan\frac{\nu}{2}\right)
\]

```formula
## eccentric_anomaly_cosine
family: flight
expr: (e + cos(nu))/(1 + e*cos(nu))
symbols: e, nu
```

```formula
## eccentric_anomaly_sine
family: flight
expr: ((1 - e**2)**0.5)*sin(nu)/(1 + e*cos(nu))
symbols: e, nu
```

```formula
## eccentric_anomaly_from_true
family: flight
expr: 2*atan(((1 - e)/(1 + e))**0.5*tan(nu/2))
symbols: e, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E\) | Eccentric anomaly | rad |
| \(\nu\) | True anomaly | rad |
| \(e\) | Eccentricity | dimensionless |

Assumptions: ellipse, \(0 \le e < 1\). `eccentric_anomaly_from_true` is valid for \(-\pi < \nu < \pi\). On a circle, \(E = \nu\).

## Perifocal coordinates

Position in the orbit plane, with \(x\) from the focus toward periapsis and \(y\) along the motion at periapsis. They follow from NASA SP-325 equation (1-80), \(ae + r\cos\nu = a\cos E\), together with the sine formula for \(\nu\).

\[
x = a(\cos E - e) \qquad y = a\sqrt{1 - e^{2}}\,\sin E
\]

```formula
## perifocal_x
family: flight
expr: a*(cos(E) - e)
symbols: a, E, e
```

```formula
## perifocal_y
family: flight
expr: a*((1 - e**2)**0.5)*sin(E)
symbols: a, e, E
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x\) | Coordinate from the focus toward periapsis | m |
| \(y\) | Coordinate completing the right-handed perifocal frame | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |
| \(E\) | Eccentric anomaly | rad |

Assumptions: ellipse, \(0 \le e < 1\). Then \(r = \sqrt{x^{2} + y^{2}}\) and \(\nu = \operatorname{atan2}(y, x)\). Equivalently, \(x = r\cos\nu\) and \(y = r\sin\nu\).

## Argument of latitude

Angle in the orbit plane from the ascending node to the spacecraft. Plummer defines it as the sum of the argument of periapsis and the true anomaly.

\[
u = \omega + \nu
\]

```formula
## argument_of_latitude
family: flight
expr: omega + nu
symbols: omega, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(u\) | Argument of latitude | rad |
| \(\omega\) | Argument of periapsis | rad |
| \(\nu\) | True anomaly | rad |

Assumptions: angles in radians, measured in the direction of motion. In this record \(u\) is not specific internal energy.

## Liquid-propellant mixture ratio

Oxidizer flow divided by fuel flow, and the split of a known total flow.

\[
r = \frac{\dot{m}_o}{\dot{m}_f}
\]

```formula
## mixture_ratio
family: rocket
expr: mdot_o/mdot_f
symbols: mdot_o, mdot_f
```

\[
\dot{m} = \dot{m}_o + \dot{m}_f
\]

```formula
## propellant_flow_sum
family: rocket
expr: mdot_o + mdot_f
symbols: mdot_o, mdot_f
```

\[
\dot{m}_f = \frac{\dot{m}}{r + 1}
\]

```formula
## fuel_flow
family: rocket
expr: mdot/(r + 1)
symbols: mdot, r
```

\[
\dot{m}_o = \frac{r \dot{m}}{r + 1}
\]

```formula
## oxidizer_flow
family: rocket
expr: r*mdot/(r + 1)
symbols: r, mdot
```

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

```formula
## average_propellant_density
family: rocket
expr: rho_o*rho_f*(r + 1)/(r*rho_f + rho_o)
symbols: rho_o, rho_f, r
```

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

```formula
## characteristic_length
family: rocket
expr: Vc/At
symbols: Vc, At
```

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

```formula
## solid_mass_flow
family: rocket
expr: Ab*r*rho_b
symbols: Ab, r, rho_b
```

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

```formula
## burning_rate
family: rocket
expr: a*p1**n
symbols: a, p1, n
```

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

```formula
## burning_area_ratio
family: rocket
expr: Ab/At
symbols: Ab, At
```

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

```formula
## burn_rate_temperature_sensitivity
family: rocket
expr: (1/r)*partial(r, Tb)
symbols: r, Tb
```

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

```formula
## pressure_temperature_sensitivity
family: rocket
expr: (1/p1)*partial(p, Tb)
symbols: p1, p, Tb
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\pi_K\) | Temperature sensitivity of pressure | 1/K |
| \(p_1\) | Chamber pressure | Pa |
| \(p\) | Equilibrium chamber pressure | Pa |
| \(T_b\) | Propellant temperature | K |
| \(K\) | Burning-area ratio held constant | dimensionless |

Assumptions: the derivative is at constant \(K\).

# Aerodynamics

Incompressible flow and the dimensionless force and moment coefficients. Freestream dynamic pressure \(q_{\infty}\) is the dynamic-pressure relation in Compressible flow evaluated far ahead of the body. In this category \(V\) is flow speed. Wing geometry and induced drag follow NASA Glenn's Beginner's Guide (public-domain educational pages). The finite-wing lift curve follows NASA TP-2414 and NACA TN 1862. Stall speed and load factor follow the usual force definitions used in FAA-H-8083 and NASA SP-367. The stick-fixed neutral point and static margin follow NACA TN 1670.

## Bernoulli's relation

Mechanical energy is constant along a streamline in steady, incompressible, inviscid flow.

\[
p + \frac{1}{2}\rho V^{2} + \rho g z = \text{constant}
\]

```formula
## bernoulli
family: aerodynamics
expr: p + 0.5*rho*V**2 + rho*g*z
symbols: p, rho, V, g, z
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Static pressure | Pa |
| \(\rho\) | Density | kg/m³ |
| \(V\) | Flow speed | m/s |
| \(g\) | Gravitational acceleration | m/s² |
| \(z\) | Elevation | m |

Assumptions: steady, incompressible, inviscid flow along a streamline. Density is constant. Use \(g = 9.80665\,\text{m/s}^2\) unless the user gives another value. When elevation change is negligible, the \(\rho g z\) term may be dropped, leaving \(p + \frac{1}{2}\rho V^{2} = \text{constant}\).

## Dynamic pressure

Freestream kinetic energy per unit volume. The force and moment coefficients below are normalized by this pressure.

\[
q_{\infty} = \frac{1}{2} \rho_{\infty} V_{\infty}^{2}
\]

```formula
## freestream_dynamic_pressure
family: aerodynamics
expr: 0.5*rho_inf*V_inf**2
symbols: rho_inf, V_inf
```

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

```formula
## lift_coefficient
family: aerodynamics
expr: L/(q_inf*S)
symbols: L, q_inf, S
```

```formula
## drag_coefficient
family: aerodynamics
expr: D/(q_inf*S)
symbols: D, q_inf, S
```

```formula
## normal_force_coefficient
family: aerodynamics
expr: N/(q_inf*S)
symbols: N, q_inf, S
```

```formula
## axial_force_coefficient
family: aerodynamics
expr: A/(q_inf*S)
symbols: A, q_inf, S
```

```formula
## moment_coefficient
family: aerodynamics
expr: M/(q_inf*S*l)
symbols: M, q_inf, S, l
```

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

```formula
## section_lift_coefficient
family: aerodynamics
expr: Lp/(q_inf*c)
symbols: Lp, q_inf, c
```

```formula
## section_drag_coefficient
family: aerodynamics
expr: Dp/(q_inf*c)
symbols: Dp, q_inf, c
```

```formula
## section_moment_coefficient
family: aerodynamics
expr: Mp/(q_inf*c**2)
symbols: Mp, q_inf, c
```

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

```formula
## pressure_coefficient
family: aerodynamics
expr: (p - p_inf)/q_inf
symbols: p, p_inf, q_inf
```

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

```formula
## skin_friction_coefficient
family: aerodynamics
expr: tau/q_inf
symbols: tau, q_inf
```

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

```formula
## section_normal_coefficient
family: aerodynamics
expr: (1/c)*(integral(0, c, Cpl - Cpu) + integral(0, c, cfu*dydx_u + cfl*dydx_l))
symbols: c, Cpl, Cpu, cfu, dydx_u, cfl, dydx_l
```

\[
c_a = \frac{1}{c}\left[\int_{0}^{c}\left(C_{p,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} - C_{p,l}\frac{\mathrm{d}y_l}{\mathrm{d}x}\right)\mathrm{d}x + \int_{0}^{c}(c_{f,u} + c_{f,l})\,\mathrm{d}x\right]
\]

```formula
## section_axial_coefficient
family: aerodynamics
expr: (1/c)*(integral(0, c, Cpu*dydx_u - Cpl*dydx_l) + integral(0, c, cfu + cfl))
symbols: c, Cpu, dydx_u, Cpl, dydx_l, cfu, cfl
```

\[
\begin{aligned}
c_{m,\mathrm{LE}} = \frac{1}{c^{2}}\Bigg[&\int_{0}^{c}(C_{p,u} - C_{p,l}) x\,\mathrm{d}x - \int_{0}^{c}\left(c_{f,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} + c_{f,l}\frac{\mathrm{d}y_l}{\mathrm{d}x}\right) x\,\mathrm{d}x \\
&+ \int_{0}^{c}\left(C_{p,u}\frac{\mathrm{d}y_u}{\mathrm{d}x} + c_{f,u}\right) y_u\,\mathrm{d}x + \int_{0}^{c}\left(-C_{p,l}\frac{\mathrm{d}y_l}{\mathrm{d}x} + c_{f,l}\right) y_l\,\mathrm{d}x\Bigg]
\end{aligned}
\]

```formula
## leading_edge_moment_coefficient
family: aerodynamics
expr: (1/c**2)*(integral(0, c, (Cpu - Cpl)*x) - integral(0, c, (cfu*dydx_u + cfl*dydx_l)*x) + integral(0, c, (Cpu*dydx_u + cfu)*yu) + integral(0, c, (-Cpl*dydx_l + cfl)*yl))
symbols: c, Cpu, Cpl, x, cfu, dydx_u, cfl, dydx_l, yu, yl
```

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

```formula
## section_lift_from_normal
family: aerodynamics
expr: cn*cos(alpha) - ca*sin(alpha)
symbols: cn, ca, alpha
```

\[
c_d = c_n \sin\alpha + c_a \cos\alpha
\]

```formula
## section_drag_from_normal
family: aerodynamics
expr: cn*sin(alpha) + ca*cos(alpha)
symbols: cn, ca, alpha
```

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

```formula
## center_of_pressure
family: aerodynamics
expr: -M_LE/Np
symbols: M_LE, Np
```

This is the same statement as \(M'_{\mathrm{LE}} = -x_{\mathrm{cp}} N'\).

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x_{\mathrm{cp}}\) | Distance from the leading edge to the center of pressure, positive aft | m |
| \(M'_{\mathrm{LE}}\) | Pitching moment per unit span about the leading edge | N·m/m |
| \(N'\) | Normal force per unit span | N/m |

Assumptions: two-dimensional airfoil, with \(N'\) perpendicular to the chord and the axial force on the chord line. Positive moment is pitch-up. A positive \(N'\) acting aft of the leading edge produces a negative moment, which is why the leading minus sign makes \(x_{\mathrm{cp}}\) positive.

## Lift and drag forces

The modern lift and drag equations from NASA Glenn: force equals coefficient times dynamic pressure times reference area.

\[
L = C_L q_{\infty} S \qquad D = C_D q_{\infty} S
\]

```formula
## lift_force
family: aerodynamics
expr: CL*q_inf*S
symbols: CL, q_inf, S
```

```formula
## drag_force
family: aerodynamics
expr: CD*q_inf*S
symbols: CD, q_inf, S
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L\) | Lift, perpendicular to the freestream | N |
| \(D\) | Drag, parallel to the freestream | N |
| \(C_L\) | Lift coefficient | dimensionless |
| \(C_D\) | Drag coefficient | dimensionless |
| \(q_{\infty}\) | Freestream dynamic pressure | Pa |
| \(S\) | Reference area | m² |

Assumptions: the same \(S\) used to define \(C_L\) and \(C_D\). These invert the coefficient definitions above.

## Aspect ratio

Wing aspect ratio is the square of the span divided by the planform area. For a rectangular wing that is span over chord.

\[
AR = \frac{b^{2}}{S}
\]

```formula
## aspect_ratio
family: aerodynamics
expr: b**2/S
symbols: b, S
```

```formula
## rectangular_aspect_ratio
family: aerodynamics
expr: b/c
symbols: b, c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(AR\) | Aspect ratio | dimensionless |
| \(b\) | Wing span | m |
| \(S\) | Wing planform area | m² |
| \(c\) | Chord of a rectangular wing | m |

Assumptions: \(S\) is the reference planform area used with the force coefficients. The rectangular form requires constant chord.

## Trapezoidal planform

A straight-tapered wing. \(c_r\) and \(c_t\) are streamwise chords, not chords perpendicular to the leading edge. The taper ratio and the trapezoidal planform area are

\[
\lambda = \frac{c_t}{c_r} \qquad
S = b\,\frac{c_r + c_t}{2}
\]

```formula
## taper_ratio
family: aerodynamics
expr: ct/cr
symbols: ct, cr
```

```formula
## trapezoidal_wing_area
family: aerodynamics
expr: b*(cr + ct)/2
symbols: b, cr, ct
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\lambda\) | Taper ratio | dimensionless |
| \(c_t\) | Streamwise tip chord | m |
| \(c_r\) | Streamwise root chord | m |
| \(S\) | Planform area | m² |
| \(b\) | Span, tip to tip | m |

Assumptions: the leading and trailing edges are straight. \(b > 0\), \(c_r > 0\), and \(c_t \ge 0\). A pointed tip has \(c_t = 0\). Aspect ratio is still \(AR = b^{2}/S\). These chords are the ones used with the lift and drag equations.

The mean aerodynamic chord is the streamwise chord at the centroid of one half of that planform. For this linear taper

\[
\bar{c} = \frac{2}{3}\,c_r\,\frac{1 + \lambda + \lambda^{2}}{1 + \lambda}
\]

and the centroid lies outboard of the centerline at

\[
y_{\bar{c}} = \frac{b}{6}\,\frac{1 + 2\lambda}{1 + \lambda}
\]

```formula
## mean_aerodynamic_chord
family: aerodynamics
expr: (2/3)*cr*(1 + lam + lam**2)/(1 + lam)
symbols: cr, lam
```

```formula
## mac_spanwise_station
family: aerodynamics
expr: (b/6)*(1 + 2*lam)/(1 + lam)
symbols: b, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\bar{c}\) | Mean aerodynamic chord | m |
| \(y_{\bar{c}}\) | Spanwise station of \(\bar{c}\), measured from the centerline | m |
| \(\lambda\) | Taper ratio | dimensionless |
| \(c_r\) | Streamwise root chord | m |
| \(b\) | Span | m |

Assumptions: \(\lambda \ge 0\). The same station on the other side is \(-y_{\bar{c}}\). For \(\lambda = 1\), \(\bar{c} = c_r\) and \(y_{\bar{c}} = b/4\). \(\bar{c}\) is also \((2/S)\int_0^{b/2} c(y)^{2}\,\mathrm{d}y\), and \(y_{\bar{c}}\) is \((2/S)\int_0^{b/2} y\,c(y)\,\mathrm{d}y\).

Sweep \(\Lambda\) is the angle from the spanwise axis toward the rear, positive when the tip is aft of the root. On the line at fraction \(n\) of the local streamwise chord, \(n = 0\) is the leading edge, \(n = 1/4\) is the quarter chord, and \(n = 1\) is the trailing edge.

\[
\tan\Lambda_n = \tan\Lambda_{\mathrm{LE}} - \frac{4n}{AR}\,\frac{1 - \lambda}{1 + \lambda}
\]

\[
\tan\Lambda_{\mathrm{LE}} = \tan\Lambda_n + \frac{4n}{AR}\,\frac{1 - \lambda}{1 + \lambda}
\]

```formula
## chord_fraction_sweep
family: aerodynamics
expr: atan(tan(sweep_le) - 4*n*(1 - lam)/(AR*(1 + lam)))
symbols: sweep_le, n, lam, AR
```

```formula
## leading_edge_from_chord_sweep
family: aerodynamics
expr: atan(tan(sweep_n) + 4*n*(1 - lam)/(AR*(1 + lam)))
symbols: sweep_n, n, lam, AR
```

The starboard leading edge at \(y_{\bar{c}}\) is aft of the root leading edge by

\[
x_{\mathrm{LE}} = y_{\bar{c}}\tan\Lambda_{\mathrm{LE}}
\]

```formula
## mac_leading_edge_x
family: aerodynamics
expr: y*tan(sweep_le)
symbols: y, sweep_le
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\Lambda_n\) | Sweep of the constant-fraction chord line | rad |
| \(\Lambda_{\mathrm{LE}}\) | Leading-edge sweep | rad |
| \(n\) | Fraction of the local streamwise chord, from 0 to 1 | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(\lambda\) | Taper ratio | dimensionless |
| \(x_{\mathrm{LE}}\) | Streamwise station of the leading edge, positive aft | m |
| \(y_{\bar{c}}\) | Spanwise station of the mean aerodynamic chord | m |

Assumptions: \(0 \le n \le 1\), \(\lambda \ge 0\), and \(AR > 0\). Each sweep is strictly between \(-\pi/2\) and \(\pi/2\), so the tangent form has one result. \(x\) is zero at the root leading edge. A rectangular wing has the same sweep at every chord fraction.

## Induced drag and the drag polar

Induced-drag coefficient and the two-term drag polar from NASA Glenn. \(e = 1\) for an elliptic spanwise lift distribution.

\[
C_{D_i} = \frac{C_L^{2}}{\pi\, AR\, e} \qquad C_D = C_{D0} + C_{D_i}
\]

```formula
## induced_drag_coefficient
family: aerodynamics
expr: CL**2/(pi*AR*e)
symbols: CL, AR, e, pi
```

```formula
## drag_polar
family: aerodynamics
expr: CD0 + CDi
symbols: CD0, CDi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_{D_i}\) | Induced-drag coefficient | dimensionless |
| \(C_L\) | Lift coefficient | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(e\) | Span efficiency, or airplane efficiency factor | dimensionless |
| \(\pi\) | Circle constant | dimensionless |
| \(C_D\) | Total drag coefficient | dimensionless |
| \(C_{D0}\) | Zero-lift drag coefficient | dimensionless |

Assumptions: coefficients use the same wing area. \(0 < e \le 1\). NACA Report 408 includes non-elliptic loading and fuselage effects in \(e\). In this section \(e\) is efficiency, not eccentricity.

## Finite-wing lift curve

Straight-wing lifting line. NASA TP-2414, equation (4), writes the section lift coefficient at a spanwise station as the section slope times the section angle of attack minus the induced angle. Equation (3) of that paper defines the induced angle by \(\alpha_i \approx w_i/V\), so the angle is in radians and the slope is per radian.

\[
c_l = a_0\,(\alpha_s - \alpha_i)
\]

```formula
## section_lift_effective_angle
family: aerodynamics
expr: a0*(alpha_s - alpha_i)
symbols: a0, alpha_s, alpha_i
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(c_l\) | Section lift coefficient | dimensionless |
| \(a_0\) | Section lift-curve slope, TP-2414's \(c_{l_\alpha}\) | 1/rad |
| \(\alpha_s\) | Section angle of attack in TP-2414 equation (4) | rad |
| \(\alpha_i\) | Induced angle of attack | rad |

Assumptions: the flow at the station is treated as two-dimensional. \(\alpha_s\) is the argument of equation (4). It is zero at the section attitude that produces zero lift when \(\alpha_i = 0\). A geometric angle \(\alpha\) and a zero-lift angle \(\alpha_{L0}\) use that same origin through \(\alpha_s = \alpha - \alpha_{L0}\).

For elliptic loading, TP-2414 substitutes its equation (6) into equation (3) and finds the induced angle constant along the span:

\[
\alpha_i = \frac{C_L}{\pi\, AR}
\]

```formula
## elliptic_induced_angle
family: aerodynamics
expr: CL/(pi*AR)
symbols: CL, AR, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\alpha_i\) | Induced angle, constant along an elliptic wing | rad |
| \(C_L\) | Wing lift coefficient | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: straight lifting line, elliptic loading, symmetric loading, and chord small relative to span, as stated for this result in TP-2414. The same paragraph says the local section lift coefficient is then constant along the span.

The induced-drag formula already recorded replaces \(\pi\, AR\) by \(\pi\, AR\, e\), with \(e = 1\) on an elliptic wing. The induced angle that keeps \(C_{D_i} = C_L\alpha_i\) is therefore

\[
\alpha_i = \frac{C_L}{\pi\, AR\, e}
\]

```formula
## induced_angle
family: aerodynamics
expr: CL/(pi*AR*e)
symbols: CL, AR, e, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\alpha_i\) | Induced angle consistent with \(C_{D_i}=C_L\alpha_i\) | rad |
| \(C_L\) | Wing lift coefficient | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(e\) | Span efficiency in `induced_drag_coefficient` | dimensionless |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: \(0 < e \le 1\), and \(\alpha_i\) is in radians so the product \(C_L\alpha_i\) is the induced-drag coefficient. At \(e = 1\) this is `elliptic_induced_angle`, the constant spanwise value from TP-2414. This record is that single angle, tied to the wing lift coefficient through the induced-drag formula.

On the elliptic wing the section lift equals the wing lift coefficient. With \(\alpha_s = \alpha - \alpha_{L0}\) and \(\alpha_i = C_L/(\pi\, AR\, e)\),

\[
C_L = a_0\left(\alpha - \alpha_{L0} - \frac{C_L}{\pi\, AR\, e}\right)
\]

Solve for the slope \(a = C_L/(\alpha - \alpha_{L0})\):

\[
a = \frac{a_0}{1 + \dfrac{a_0}{\pi\, AR\, e}}
\]

```formula
## wing_lift_curve_slope
family: aerodynamics
expr: a0/(1 + a0/(pi*AR*e))
symbols: a0, AR, e, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a\) | Wing lift-curve slope | 1/rad |
| \(a_0\) | Section lift-curve slope | 1/rad |
| \(AR\) | Aspect ratio | dimensionless |
| \(e\) | Span efficiency | dimensionless |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: \(a_0 > 0\), \(AR > 0\), and \(0 < e \le 1\). The wing lift coefficient equals the section lift coefficient, which is the constant-section result TP-2414 states for elliptic loading. NACA TN 1862, equation (1), states the same elliptic slope for a section slope of \(2\pi\) per radian: the per-degree slope is \((2\pi/57.3)\, AR/(AR+2)\). Multiplying that per-degree slope by the same \(57.3\) gives \(2\pi\, AR/(AR+2)\) per radian. The record above equals that value at \(a_0 = 2\pi\) and \(e = 1\), because \(2\pi/(1+2/AR) = 2\pi\, AR/(AR+2)\). TN 1862 equation (3) is a separate low-aspect-ratio estimate and is not this lifting-line slope. TP-2414 limits the underlying angle to a chord that is small relative to the span.

The straight lift line through the zero-lift angle is

\[
C_L = a\,(\alpha - \alpha_{L0})
\]

```formula
## wing_lift_coefficient
family: aerodynamics
expr: a*(alpha - alpha_L0)
symbols: a, alpha, alpha_L0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_L\) | Wing lift coefficient on the straight line | dimensionless |
| \(a\) | Wing lift-curve slope | 1/rad |
| \(\alpha\) | Geometric angle of attack | rad |
| \(\alpha_{L0}\) | Geometric angle at which section lift is zero when \(\alpha_i = 0\) | rad |

Assumptions: \(\alpha - \alpha_{L0}\) is the section angle \(\alpha_s\) in `section_lift_effective_angle`. FAA-H-8083-25C, chapter 5, says the lift coefficient increases with angle of attack until \(C_{L,\max}\) and then falls. This straight line is the lift coefficient while \(C_L\) is below \(C_{L,\max}\).

That peak is reached on the straight line at

\[
\alpha_{\mathrm{stall}} = \alpha_{L0} + \frac{C_{L,\max}}{a}
\]

```formula
## stall_angle
family: aerodynamics
expr: alpha_L0 + CLmax/a
symbols: alpha_L0, CLmax, a
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\alpha_{\mathrm{stall}}\) | Geometric angle at which the straight line equals \(C_{L,\max}\) | rad |
| \(\alpha_{L0}\) | Zero-lift angle | rad |
| \(C_{L,\max}\) | Maximum lift coefficient | dimensionless |
| \(a\) | Wing lift-curve slope | 1/rad |

Assumptions: \(a > 0\). This is the angle on `wing_lift_coefficient` at which \(C_L = C_{L,\max}\). It is the critical angle in the sense of FAA-H-8083-25C chapter 5 when the lift curve follows the straight line up to that peak.

## Lift-to-drag ratio

\[
\frac{L}{D} = \frac{C_L}{C_D}
\]

```formula
## lift_to_drag
family: aerodynamics
expr: CL/CD
symbols: CL, CD
```

```formula
## lift_to_drag_from_forces
family: aerodynamics
expr: L/D
symbols: L, D
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L/D\) | Lift-to-drag ratio | dimensionless |
| \(C_L\) | Lift coefficient | dimensionless |
| \(C_D\) | Drag coefficient | dimensionless |
| \(L\) | Lift | N |
| \(D\) | Drag | N |

Assumptions: lift and drag (or their coefficients) are taken at the same flight condition and use the same reference area.

## Stall speed

Level unaccelerated stall when lift equals weight at \(C_{L,\max}\).

\[
V_{\mathrm{stall}} = \sqrt{\frac{2W}{\rho S C_{L,\max}}}
\]

```formula
## stall_speed
family: aerodynamics
expr: (2*W/(rho*S*CLmax))**0.5
symbols: W, rho, S, CLmax
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_{\mathrm{stall}}\) | Stall speed | m/s |
| \(W\) | Weight | N |
| \(\rho\) | Air density | kg/m³ |
| \(S\) | Wing planform area | m² |
| \(C_{L,\max}\) | Maximum lift coefficient | dimensionless |

Assumptions: unaccelerated 1-g flight, \(L = W\), and incompressible dynamic pressure \(\frac{1}{2}\rho V^{2}\). Use the density at the altitude of interest. In a coordinated level turn at load factor \(n\), replace \(W\) by \(nW\).

## Equivalent airspeed

Speed at sea-level density with the same dynamic pressure as the true airspeed. `freestream_dynamic_pressure` is unchanged when \(\rho V^{2} = \rho_{\mathrm{sl}} V_e^{2}\), so

\[
V_e = V\sqrt{\frac{\rho}{\rho_{\mathrm{sl}}}}
\]

```formula
## equivalent_airspeed
family: aerodynamics
expr: V*(rho/rho_sl)**0.5
symbols: V, rho, rho_sl
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_e\) | Equivalent airspeed | m/s |
| \(V\) | True airspeed | m/s |
| \(\rho\) | Air density at the flight condition | kg/m³ |
| \(\rho_{\mathrm{sl}}\) | Sea-level air density | kg/m³ |

Assumptions: \(q = \frac{1}{2}\rho V^{2} = \frac{1}{2}\rho_{\mathrm{sl}} V_e^{2}\) from `freestream_dynamic_pressure`. Evaluating `stall_speed` at sea-level density is this speed for the 1-g stall: it equals the true stall speed times \(\sqrt{\rho/\rho_{\mathrm{sl}}}\). \(\rho_{\mathrm{sl}}\) is the 1976 sea-level density when the atmosphere is the 1976 standard. This is not calibrated airspeed.

## Load factor

Lift divided by weight.

\[
n = \frac{L}{W}
\]

```formula
## load_factor
family: aerodynamics
expr: L/W
symbols: L, W
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(n\) | Load factor | dimensionless |
| \(L\) | Lift | N |
| \(W\) | Weight | N |

Assumptions: \(W\) is the vehicle weight, not mass times a local \(g\) different from the weight definition in use. Straight and level flight has \(n = 1\) when \(L = W\).

## Stick-fixed neutral point

For the simplified airplane in NACA TN 1670, drag and propeller forces are left out of the pitching moment. The wing-fuselage lift and a constant moment act at the aerodynamic center of that combination. The tail lift acts at the tail quarter-chord. With the elevator fixed, the distance from that aerodynamic center to the neutral point, divided by the wing mean aerodynamic chord, is

\[
\frac{x_0}{c}
= \left(1 - \frac{\mathrm{d}\epsilon}{\mathrm{d}\alpha}\right)
\frac{(\mathrm{d}C_L/\mathrm{d}\alpha)_T}{\mathrm{d}C_L/\mathrm{d}\alpha}
\frac{q_T}{q}
\frac{S_T}{S}
\frac{l}{c}
\]

```formula
## stick_fixed_neutral_point
family: aerodynamics
expr: (1 - deps)*(aT/a)*(qT/q)*(ST*l)/(S*c)
symbols: deps, aT, a, qT, q, ST, l, S, c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x_0/c\) | Distance from the wing-fuselage aerodynamic center to the stick-fixed neutral point, positive aft | dimensionless |
| \(\mathrm{d}\epsilon/\mathrm{d}\alpha\) | Downwash slope | dimensionless |
| \((\mathrm{d}C_L/\mathrm{d}\alpha)_T\) | Tail lift-curve slope, elevator fixed | 1/rad |
| \(\mathrm{d}C_L/\mathrm{d}\alpha\) | Wing-fuselage lift-curve slope | 1/rad |
| \(q_T/q\) | Tail dynamic pressure divided by freestream dynamic pressure | dimensionless |
| \(S_T\) | Horizontal-tail area | m² |
| \(S\) | Wing area | m² |
| \(l\) | Tail length from the center of gravity to the tail quarter-chord | m |
| \(c\) | Wing mean aerodynamic chord | m |

Assumptions: the two lift-curve slopes use the same angle measure, so their ratio is unchanged if both are taken per degree instead of per radian. \(\mathrm{d}\epsilon/\mathrm{d}\alpha\) uses that same measure. \(l\) and \(c\) use the same length unit. In equation (6) of TN 1670 the center of gravity is the neutral point, so \(l\) is measured from the neutral point to the tail quarter-chord. \(q_T/q\) is the dynamic-pressure ratio at the tail. The symbol \(\eta\) in that note is propeller efficiency, not this ratio. The same expression gives the stick-free neutral point when \((\mathrm{d}C_L/\mathrm{d}\alpha)_T\) is the elevator-free tail slope. The note states that this theory is approximate for gliding flight at low angle of attack, and that power-on flight or flight near stall can move the neutral point with angle of attack.

The distance from the center of gravity to that neutral point follows by subtracting the center-of-gravity position from \(x_0\). Both distances are measured from the wing-fuselage aerodynamic center, positive aft.

\[
\frac{x}{c} = \frac{x_0}{c} - \frac{x'}{c}
\]

```formula
## center_of_gravity_to_neutral_point
family: aerodynamics
expr: x0c - xpc
symbols: x0c, xpc
```

TN 1670 also writes that distance from the pitching-moment slope. A positive value is the center of gravity ahead of the neutral point.

\[
\frac{x}{c} = -\frac{\mathrm{d}C_m}{\mathrm{d}C_L}
\]

```formula
## neutral_distance_from_moment
family: aerodynamics
expr: -dCm_dCL
symbols: dCm_dCL
```

The same distance, expressed in percent of the mean aerodynamic chord, is the static margin.

\[
\text{static margin} = 100\,\frac{x}{c}
\]

```formula
## static_margin
family: aerodynamics
expr: 100*xc
symbols: xc
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x/c\) | Distance from the center of gravity to the neutral point, positive when the neutral point is aft | dimensionless |
| \(x'/c\) | Distance from the wing-fuselage aerodynamic center to the center of gravity, positive aft | dimensionless |
| \(x_0/c\) | Distance from that aerodynamic center to the neutral point, positive aft | dimensionless |
| \(\mathrm{d}C_m/\mathrm{d}C_L\) | Pitching-moment slope with lift coefficient | dimensionless |
| static margin | \(x\) in percent of the mean aerodynamic chord | percent |

Assumptions: \(x'\) is the arm in TN 1670 equation (4). A positive \(x'\) adds a positive increment to \(\mathrm{d}C_m/\mathrm{d}\alpha\), which is the center of gravity aft of the wing-fuselage aerodynamic center. A positive \(x/c\), and therefore a positive static margin, is the arrangement in which the center of gravity is ahead of the neutral point and \(\mathrm{d}C_m/\mathrm{d}\alpha\) is negative. A static margin of 5 is five percent of the mean aerodynamic chord, so \(x/c = 0.05\).

# Structures

Thin-shell relations written out in NASA SP-8025, *Solid Rocket Motor Metal Cases* (April 1970). Buckling, fracture mechanics, and weight scaling in that monograph are cited to other documents and are not recorded here. In this category \(R\) is cylinder radius. The load ratio in the margin-of-safety definition is not called \(R\).

## Cylinder hoop stress

Hoop, or circumferential, membrane stress in a thin cylindrical motor case under internal pressure. Section 2.3.1.1 works an example with \(\sigma_h = pD/(2t)\). Section 3.3.6.3 calls \(pR/t\) the basic membrane stress. With \(R = D/2\) the two statements are the same.

\[
\sigma_h = \frac{p D}{2 t} = \frac{p R}{t}
\]

```formula
## cylinder_hoop_stress
family: shell
expr: p*R/t
symbols: p, R, t
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\sigma_h\) | Hoop membrane stress | Pa |
| \(p\) | Internal design pressure | Pa |
| \(D\) | Cylinder inner diameter | m |
| \(R\) | Cylinder radius, \(D/2\) | m |
| \(t\) | Wall thickness | m |

Assumptions: thin cylindrical membrane, with thickness small compared with \(R\), away from openings, welds, and thickness changes. \(p\) is the design pressure, the maximum expected operating pressure times the design safety factor. The SP-8025 sample uses \(800\,\mathrm{psi} \times 1.25 = 1000\,\mathrm{psi}\), \(D = 40\,\mathrm{in}\), and \(t = 0.1\,\mathrm{in}\), which gives \(\sigma_h = 200000\,\mathrm{psi}\). The recorded expression uses \(R\).

## Margin of safety

Fractional amount by which the allowable load or stress exceeds the design load or stress. Section 2.3.1.1 defines

\[
\mathrm{MS} = \frac{S_{\mathrm{allow}}}{S_{\mathrm{design}}} - 1
\]

```formula
## margin_of_safety
family: design
expr: allowable/design - 1
symbols: allowable, design
```

SP-8025 also writes \(\mathrm{MS} = 1/R - 1\), where \(R = S_{\mathrm{design}}/S_{\mathrm{allow}}\). That ratio is not the cylinder radius used above.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{MS}\) | Margin of safety | dimensionless |
| \(S_{\mathrm{allow}}\) | Allowable load or stress | same unit as \(S_{\mathrm{design}}\) |
| \(S_{\mathrm{design}}\) | Design load or stress | same unit as \(S_{\mathrm{allow}}\) |
| \(\mathrm{allowable}\) | Script symbol for \(S_{\mathrm{allow}}\) | same unit as \(\mathrm{design}\) |
| \(\mathrm{design}\) | Script symbol for \(S_{\mathrm{design}}\) | same unit as \(\mathrm{allowable}\) |

Assumptions: failure is the chosen allowable, such as yield, ultimate, or buckling. \(\mathrm{MS}\) is a fraction. The SP-8025 sample with design stress \(160000\,\mathrm{psi}\) and allowable stress \(200000\,\mathrm{psi}\) gives \(\mathrm{MS} = 0.25\). Equal design and allowable stresses give \(\mathrm{MS} = 0\).

## Longitudinal-weld radial mismatch

Elastic hoop bending stress from a radial offset across a longitudinal weld, for a weld designed to the full elastic stress. Section 3.3.6.3 writes

\[
\sigma_h = \frac{3 p R \delta}{t^{2}}
\]

```formula
## weld_radial_mismatch
family: shell
expr: 3*p*R*delta/t**2
symbols: p, R, delta, t
```

Dividing by the membrane hoop stress \(pR/t\) shows that the bending stress is \(3(\delta/t)\) times the membrane stress. A mismatch of 5 percent of the thickness is 15 percent of the membrane stress.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\sigma_h\) | Elastic hoop bending stress from radial mismatch | Pa |
| \(p\) | Internal pressure | Pa |
| \(R\) | Cylinder radius | m |
| \(\delta\) | Radial mismatch across the longitudinal weld | m |
| \(t\) | Wall thickness | m |

Assumptions: elastic bending from radial mismatch at a longitudinal weld in a thin cylinder. Residual stress and angular mismatch are separate effects. SP-8025 adds example fractions of yield strength for those effects and states that the fractions change with the design, so they are not part of this expression. On the sample cylinder \(p = 1000\,\mathrm{psi}\), \(R = 20\,\mathrm{in}\), \(t = 0.1\,\mathrm{in}\), a 5 percent mismatch is \(\delta = 0.005\,\mathrm{in}\) and \(\sigma_h = 30000\,\mathrm{psi}\).
