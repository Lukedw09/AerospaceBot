# Aerospace formulas

Units below are SI unless a section says otherwise. Any single consistent unit system is valid. Do not mix systems in one calculation.

The file is grouped so a search can start in one category:

- Compressible flow: perfect-gas thermodynamics, isentropic flow, area-Mach, shocks, Prandtl-Meyer expansion, and calorically imperfect air.
- Rocket propulsion: thrust, impulse, mass ratio, nozzles, and solid- and liquid-propellant relations.
- Aerodynamics: incompressible Bernoulli and the force, moment, pressure, and skin-friction coefficients.

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

Incompressible flow and the dimensionless force and moment coefficients. Freestream dynamic pressure \(q_{\infty}\) is the dynamic-pressure relation in Compressible flow evaluated far ahead of the body. In this category \(V\) is flow speed.

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
