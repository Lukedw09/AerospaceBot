# Aerospace formulas

Units below are SI unless a section says otherwise. Any single consistent unit system is valid. Do not mix systems in one calculation.

The file is grouped so a search can start in one category:

- Compressible flow: perfect-gas thermodynamics, isentropic flow, area-Mach, shocks, Prandtl-Meyer expansion, Taylor–Maccoll flow on a circular cone, calorically imperfect air, Newtonian viscosity, and Reynolds number.
- Atmosphere: the 1976 U.S. Standard Atmosphere from the surface to 1000 km, including geopotential and gravity, the seven hydrostatic layers below 86 km, kinetic temperature above 86 km, and the transport properties of that model. Moist-air point properties (saturation vapor pressure, humidity, and the density of one dry-air-plus-water parcel) are recorded separately from those dry hydrostatic layers and from the Glenn fit. A three-zone NASA Glenn curve fit is recorded separately.
- Rocket propulsion: thrust, impulse, mass ratio, nozzles, solid- and liquid-propellant relations, powered-ascent gravity, drag, and steering losses from a spherical body, two-body orbital speed, period, half-period coast, energy, plane-change impulse, Laplace sphere of influence, anomalies, mean motion, the conversion between classical elements and an inertial state, Greenwich angle, Earth-fixed axes, and geodetic latitude on an oblate spheroid.
- Aerodynamics: incompressible Bernoulli, force and moment coefficients, the two-dimensional Prandtl–Glauert compressibility correction, the isentropic critical pressure coefficient and critical Mach number, trapezoidal wing planform, aspect ratio, induced drag, finite-wing lift-curve slope and induced angle, NACA four-digit mean-line and thickness ordinates, thin-section lift and quarter-chord moment, stall speed, equivalent airspeed, load factor, coordinated level-turn bank, radius, and rate, the sustained-turn load factor from a parabolic polar with thrust equal to drag, symmetric pull-up load factor, radius, and pitch rate, takeoff and landing ground-roll force, acceleration, and the constant-thrust distance and time integrals, ideal actuator-disk propeller thrust, induced velocity, and propulsive efficiency, ideal air-breathing Brayton turbojet specific thrust, TSFC, and thermal/propulsive/overall efficiency, steady unpowered glide angle, sink rate, and range from height, Breguet range and endurance for jet and propeller cruise, and the stick-fixed neutral point and static margin.
- Structures: pure beam / spar bending stress and elastic section modulus, elastic Euler column buckling with end-fix factor, thin-wall motor-case hoop stress, margin of safety, and longitudinal-weld radial mismatch.
- Mass properties: total mass, center-of-mass coordinate, point-mass moments and products of inertia, parallel-axis transfer of a part inertia to a parallel axis, and the shift of a reference-origin inertia to the system CG.
- Aerothermodynamics: stagnation-point convective heating on a blunt nose (Sutton–Graves heat-transfer coefficient and cold-wall freestream-density form), radiative-equilibrium wall temperature, and Allen–Eggers nonlifting ballistic-entry peak deceleration in an exponential atmosphere.
- Spacecraft power: flat-plate solar-array beginning- and end-of-life power with packing and inherent degradation, compound life degradation, circular-orbit eclipse fraction for orbit-average power, and battery energy budget with depth of discharge, charge and discharge efficiencies, and orbit energy balance.
- Space communications: vacuum free-space path loss, Friis received power, circular-aperture antenna gain with aperture efficiency, thermal noise \(kTB\), carrier-to-noise density, \(E_b/N_0\), and link margin against a required \(E_b/N_0\).
- Dynamics and control: linear constant-coefficient second-order unit-step metrics from natural frequency and damping ratio, or from mass, stiffness, and viscous damping (damped frequency, percent overshoot, peak time, envelope settling time).

The rocket symbol \(k\) is the same ratio of specific heats as \(\gamma\). In the dynamics-and-control records \(k\) is stiffness (N/m), not that ratio. Standard sea-level gravitational acceleration is \(g_0 = 9.80665\,\mathrm{m/s}^2\).

Each formula is also written as a script record. In those records \(\gamma\) is `g`, powers are `**`, and the expression is the quantity named by the record. `partial`, `integral`, `log`, `exp`, `sin`, `cos`, `tan`, `cot`, `atan`, `asin`, and `acos` are function calls.

# Compressible flow

Perfect-gas and shock relations for steady inviscid flow, from NACA Report 1135. Circular-cone Taylor–Maccoll flow is from NASA SP-3004 and NACA TN 3485. Numerical Mach-number tables and charts in those reports are not copied here. In this category \(V\) is flow speed and \(v\) is specific volume. \(\gamma\) and the rocket-propulsion symbol \(k\) are the same ratio of specific heats. For air as a calorically perfect gas, use \(\gamma = 1.4 = 7/5\) unless the user gives another value. Above roughly \(550\,\text{K}\), use the air \(\gamma(T)\) table at the end of this category.

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
\frac{p_{t2}}{p_{t1}}
=
\left[\frac{(\gamma + 1) M_1^{2}}{(\gamma - 1) M_1^{2} + 2}\right]^{\gamma/(\gamma - 1)}
\left[\frac{\gamma + 1}{2\gamma M_1^{2} - (\gamma - 1)}\right]^{1/(\gamma - 1)}
\]

```formula
## normal_shock_stagnation_pressure
family: shock
expr: (((g + 1)*M1**2)/((g - 1)*M1**2 + 2))**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1))
symbols: g, M1
```

That ratio is `rayleigh_pitot` divided by the isentropic `stagnation_pressure` at \(M_1\). Total temperature is unchanged, so the same factor is \(p_{t2}/p_{t1} = \rho_{t2}/\rho_{t1}\).

\[
\Delta s = - R \ln\frac{p_{t2}}{p_{t1}}
\qquad
\frac{\Delta s}{R} = -\ln\frac{p_{t2}}{p_{t1}}
\]

```formula
## normal_shock_entropy
family: shock
expr: -R*log(pt2/pt1)
symbols: R, pt2, pt1
```

```formula
## normal_shock_entropy_over_r
family: shock
expr: -log((((g + 1)*M1**2)/((g - 1)*M1**2 + 2))**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1)))
symbols: g, M1
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

Prandtl's relation, with \(a^{*}\) the critical sound speed. Divided by the upstream sound speed, both sides are the same function of the upstream Mach number:

\[
\frac{a^{*\,2}}{a_1^{2}} = \frac{V_1 V_2}{a_1^{2}} = \frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2} M_1^{2}\right)
\]

```formula
## prandtl_relation
family: shock
expr: (2/(g+1))*(1+((g-1)/2)*M1**2)
symbols: g, M1
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p, \rho, T, M, V\) | Static pressure, density, temperature, Mach number, and speed | Pa, kg/m³, K, dimensionless, m/s |
| \(p_t\) | Total pressure | Pa |
| \(\Delta s\) | Specific-entropy increase | J/(kg·K) |
| \(\Delta s/R\) | Specific-entropy increase divided by \(R\) | dimensionless |
| \(R\) | Specific gas constant | J/(kg·K) |
| \(\gamma\) | Ratio of specific heats | dimensionless |
| \(a^{*}\) | Critical sound speed | m/s |

Assumptions: steady normal shock in a perfect gas. Velocities are measured relative to the shock, so the same relations apply to an unsteady wave. Entropy must not decrease, which requires \(M_1 \ge 1\). Total temperature is unchanged. The Rayleigh-Pitot formula is the expression for \(p_{t2}/p_1\). `normal_shock_stagnation_pressure` is \(p_{t2}/p_{t1}\). `normal_shock_entropy_over_r` is that entropy jump divided by \(R\). `prandtl_relation` is \(a^{*2}/a_1^{2}\), which equals \(V_1 V_2/a_1^{2}\).

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

## Conical shock on a circular cone

Steady, inviscid, calorically perfect flow over a right circular cone at zero angle of attack, with an attached conical shock. NASA SP-3004 (Sims) writes the Taylor–Maccoll problem in spherical coordinates. Velocities \(u\) and \(v\) are divided by the limiting speed reached by adiabatic expansion into a vacuum. \(u\) is along a ray from the vertex; \(v\) is normal to that ray, positive with increasing polar angle \(\theta\) from the cone axis.

NACA TN 3485 states the same second-order equation as the first-order system \(\mathrm{d}u/\mathrm{d}\theta = v\) together with the polar resolution of the axial and cylindrical-radial speeds.

\[
v = \frac{\mathrm{d}u}{\mathrm{d}\theta}
\]

```formula
## conical_ray_normal_speed
family: conical_shock
expr: partial(u, theta)
symbols: u, theta
```

\[
a^{2} = \frac{\gamma - 1}{2}\left(1 - u^{2} - v^{2}\right)
\]

```formula
## conical_vacuum_sound_speed_sq
family: conical_shock
expr: ((g - 1)/2)*(1 - u**2 - v**2)
symbols: g, u, v
```

\[
\frac{\mathrm{d}^{2}u}{\mathrm{d}\theta^{2}} + u = \frac{a^{2}(u + v\cot\theta)}{v^{2} - a^{2}}
\]

The recorded quantity is \(\mathrm{d}^{2}u/\mathrm{d}\theta^{2}\).

```formula
## taylor_maccoll_radial_acceleration
family: conical_shock
expr: ((g - 1)/2*(1 - u**2 - v**2))*(u + v*cot(theta))/(v**2 - (g - 1)/2*(1 - u**2 - v**2)) - u
symbols: g, u, v, theta
```

On the cone surface, \(v_{s} = 0\) and the flow follows the generator. Immediately behind the shock the Rankine–Hugoniot condition of SP-3004 is

\[
\tan\theta = \frac{\gamma - 1}{\gamma + 1}\frac{u^{2} - 1}{u v}
\]

```formula
## conical_shock_wave_tangent
family: conical_shock
expr: ((g - 1)/(g + 1))*(u**2 - 1)/(u*v)
symbols: g, u, v
```

When that shock condition holds, the freestream Mach number on the shock ray is

\[
M_{\infty}^{2} = \frac{2}{\gamma - 1}\frac{u^{2}}{\cos^{2}\theta - u^{2}}
\]

```formula
## conical_freestream_mach_sq
family: conical_shock
expr: (2/(g - 1))*u**2/(cos(theta)**2 - u**2)
symbols: g, u, theta
```

The local Mach number and the critical Mach number \(M^{*} = V/a^{*}\) are

\[
M^{2} = \frac{2(u^{2} + v^{2})}{(\gamma - 1)(1 - u^{2} - v^{2})} \qquad
M^{*} = \sqrt{\frac{\gamma + 1}{\gamma - 1}\left(u^{2} + v^{2}\right)}
\]

```formula
## conical_resultant_mach
family: conical_shock
expr: (2*(u**2 + v**2)/((g - 1)*(1 - u**2 - v**2)))**0.5
symbols: u, v, g
```

```formula
## conical_critical_mach
family: conical_shock
expr: ((g + 1)/(g - 1)*(u**2 + v**2))**0.5
symbols: g, u, v
```

The same vacuum normalization from the adiabatic energy equation is

\[
\frac{V}{V_{\max}} = \sqrt{\frac{\frac{\gamma - 1}{2}M^{2}}{1 + \frac{\gamma - 1}{2}M^{2}}}
\]

```formula
## limiting_speed_ratio
family: conical_shock
expr: (((g - 1)/2)*M**2/(1 + ((g - 1)/2)*M**2))**0.5
symbols: g, M
```

TN 3485 resolves the polar components from the axial speed \(V_{x}\) and the cylindrical-radial speed \(V_{r}\), both divided by \(V_{\max}\):

\[
u = V_{x}\cos\theta + V_{r}\sin\theta \qquad
v = -V_{x}\sin\theta + V_{r}\cos\theta
\]

```formula
## conical_radial_speed
family: conical_shock
expr: Vx*cos(theta) + Vr*sin(theta)
symbols: Vx, theta, Vr
```

```formula
## conical_normal_speed
family: conical_shock
expr: -Vx*sin(theta) + Vr*cos(theta)
symbols: Vx, theta, Vr
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(u, v\) | Polar velocity components divided by \(V_{\max}\) | dimensionless |
| \(V_{x}, V_{r}\) | Axial and cylindrical-radial speeds divided by \(V_{\max}\) | dimensionless |
| \(a\) | Local sound speed divided by \(V_{\max}\) | dimensionless |
| \(\theta\) | Polar angle from the cone axis | rad |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |
| \(M\) | Local Mach number | dimensionless |
| \(M^{*}\) | Speed divided by the critical sound speed | dimensionless |
| \(V_{\max}\) | Limiting speed of adiabatic expansion into vacuum | m/s |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: calorically perfect gas; steady axisymmetric conical flow; attached conical shock; zero incidence. The shock layer is irrotational and isentropic because the conical shock has uniform strength. SP-3004 tables use \(\gamma = 1.4\). Sine, cosine, cotangent, and tangent expect radians. Do not replace the cone half-angle by the two-dimensional wedge deflection in `oblique_shock_deflection`. The isolated cone takes the weaker attached shock.

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

Defining relations of the U.S. Standard Atmosphere, 1976 (NASA TM-X-74335 / NOAA-S/T-76-1562), with the same closed-form layer equations as NASA TR R-459. Moist-air saturation pressure and humidity of one parcel follow NASA TN D-8401, combined with the 1976 mixture sums. Keep both of those apart from the NASA Glenn three-zone curve fit at the end of the category. In this category \(R^{*}\) is the universal gas constant and \(M\) is molar mass. Geometric altitude is \(Z\); geopotential altitude is \(H\).

The 1976 model air is dry and, below about 80 km, homogeneously mixed at constant mean molar mass \(M_0\). Hydrostatic balance and the perfect-gas law then give pressure and density from a piecewise-linear molecular-scale temperature in \(H\). That hydrostatic argument runs to \(Z = 86\,\mathrm{km}\) (\(H = 84.8520\,\mathrm{km}\)). Above 86 km the model switches to geometric altitude, a four-segment kinetic-temperature profile, and species number densities; total pressure is then the sum of partial pressures. Species diffusion above 86 km is not reduced to a single algebraic script here. Moist-parcel relations recorded after the Dalton section apply at one pressure and temperature and leave these dry layer integrals on \(M_0\).

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

## Moist-air point properties

Saturation vapor pressure, humidity, and the density of one parcel of dry air plus water vapor. Saturation pressure is from NASA TN D-8401 (Parish and Putnam, 1977). The mixture molar mass and density use the 1976 Dalton partial pressure, the 1976 mean-molar-mass sum, and `atmosphere_density` on each partial pressure. The 1976 hydrostatic layers stay dry air at \(M_0\).

The note gives saturation pressure in millibars on an absolute temperature that places the ice point at 273. In thermodynamic kelvin that argument is \(T - 0.15\), and the pressure in pascals is 100 times the millibar value. Use the water coefficients when \(T > 273.15\,\mathrm{K}\) and the ice coefficients when \(T \le 273.15\,\mathrm{K}\). The note assigns the water coefficients above freezing and the ice coefficients at and below freezing. Its comparison ranges are \(-50^\circ\mathrm{C}\) to \(100^\circ\mathrm{C}\) over water and \(-50^\circ\mathrm{C}\) to \(0^\circ\mathrm{C}\) over ice.

\[
e_{s,w} = 100 \times 10^{-4.9283\,\log_{10}(T - 0.15) - 2937.4/(T - 0.15) + 23.5518}
\]

\[
e_{s,i} = 100 \times 10^{-0.32286\,\log_{10}(T - 0.15) - 2705.21/(T - 0.15) + 11.4816}
\]

```formula
## saturation_vapor_pressure_water
family: atmosphere
expr: 100*10**(-4.9283*log(T - 0.15)/log(10) - 2937.4/(T - 0.15) + 23.5518)
symbols: T
```

```formula
## saturation_vapor_pressure_ice
family: atmosphere
expr: 100*10**(-0.32286*log(T - 0.15)/log(10) - 2705.21/(T - 0.15) + 11.4816)
symbols: T
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(e_{s,w}\) | Saturation vapor pressure over liquid water | Pa |
| \(e_{s,i}\) | Saturation vapor pressure over ice | Pa |
| \(T\) | Thermodynamic temperature | K |

Assumptions: NASA TN D-8401, with that note’s evaluated coefficients. \(T > 0.15\,\mathrm{K}\) so the logarithm argument stays positive. Water script above \(273.15\,\mathrm{K}\); ice script at and below \(273.15\,\mathrm{K}\). The scripts use the SI coefficients from the note. The note’s U.S. customary-unit coefficients are a unit conversion of those values and are omitted here.

Relative humidity in the note is the vapor partial pressure divided by the saturation vapor pressure at the same temperature, as a fraction from 0 to 1. The vapor partial pressure that belongs to a stated relative humidity is the product.

\[
\phi = \frac{e}{e_s} \qquad
e = \phi\, e_s
\]

```formula
## relative_humidity
family: atmosphere
expr: e/es
symbols: e, es
```

```formula
## vapor_partial_pressure
family: atmosphere
expr: phi*es
symbols: phi, es
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\phi\) | Relative humidity | dimensionless, \(0 \le \phi \le 1\) |
| \(e\) | Partial pressure of water vapor | Pa |
| \(e_s\) | Saturation vapor pressure at the same temperature | Pa |

Assumptions: NASA TN D-8401. \(e_s\) is `saturation_vapor_pressure_water` or `saturation_vapor_pressure_ice` at the parcel temperature, chosen with the freeze split above. When the known temperature is the dewpoint, \(e\) is that saturation pressure evaluated at the dewpoint, with the ice script when the dewpoint is at or below freezing.

Absolute humidity is the mass of water vapor in a unit volume. The note writes it from the perfect-gas law for the vapor and takes the compressibility factor as 1 over ordinary atmospheric temperatures and pressures.

\[
H = \frac{e}{R_v T}
\]

```formula
## absolute_humidity
family: atmosphere
expr: e/(Rv*T)
symbols: e, Rv, T
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(H\) | Absolute humidity | kg/m³ |
| \(e\) | Partial pressure of water vapor | Pa |
| \(R_v\) | Specific gas constant of water vapor | J/(kg·K) |
| \(T\) | Thermodynamic temperature | K |

Assumptions: NASA TN D-8401, compressibility factor 1. \(R_v = R^{*}/M_w\) from `specific_gas_constant` with the water molar mass below and the 1976 \(R^{*}\). \(T > 0\).

Water is not a constituent in the 1976 dry-air list. That list does give \(M(\mathrm{H}_2) = 2.01594\,\mathrm{kg/kmol}\) and \(M(\mathrm{O}_2) = 31.9988\,\mathrm{kg/kmol}\) on the carbon-12 scale. The molar mass of water on that same list is

\[
M_w = M(\mathrm{H}_2) + \frac{1}{2} M(\mathrm{O}_2) = 18.01534\,\mathrm{kg/kmol}
\]

```formula
## water_molar_mass
family: atmosphere
expr: MH2 + MO2/2
symbols: MH2, MO2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M_w\) | Molar mass of water | kg/kmol |
| \(M(\mathrm{H}_2)\) | Molar mass of hydrogen in the 1976 dry-air list | kg/kmol |
| \(M(\mathrm{O}_2)\) | Molar mass of oxygen in the 1976 dry-air list | kg/kmol |

Assumptions: U.S. Standard Atmosphere, 1976, Table 3. Use \(M(\mathrm{H}_2) = 2.01594\,\mathrm{kg/kmol}\) and \(M(\mathrm{O}_2) = 31.9988\,\mathrm{kg/kmol}\) unless the user gives other values from that table’s scale.

The 1976 mean molar mass of a mixture is the mole-fraction sum of the species molar masses. Dalton’s law makes the mole fraction of each ideal-gas constituent equal to its partial-pressure fraction. Dry air is one constituent at partial pressure \(p - e\) with molar mass \(M_0\); water is the other at partial pressure \(e\).

\[
M = \frac{(p - e)\,M_0 + e\,M_w}{p}
\]

```formula
## moist_mean_molar_mass
family: atmosphere
expr: ((p - e)*M0 + e*Mw)/p
symbols: p, e, M0, Mw
```

Mass density is `atmosphere_density` on each partial pressure, which is the 1976 species sum \(\rho = \sum n_i M_i / N_A\).

\[
\rho = \frac{(p - e)\,M_0}{R^{*} T} + \frac{e\,M_w}{R^{*} T}
\]

```formula
## moist_density
family: atmosphere
expr: (p - e)*M0/(Rstar*T) + e*Mw/(Rstar*T)
symbols: p, e, M0, Rstar, T, Mw
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mean molar mass of the moist parcel | kg/kmol |
| \(\rho\) | Mass density of the moist parcel | kg/m³ |
| \(p\) | Total pressure | Pa |
| \(e\) | Partial pressure of water vapor | Pa |
| \(T\) | Kinetic temperature of the parcel | K |
| \(M_0\) | Sea-level mean molar mass of dry air | kg/kmol |
| \(M_w\) | Molar mass of water | kg/kmol |
| \(R^{*}\) | Universal gas constant | J/(kmol·K) |

Assumptions: U.S. Standard Atmosphere, 1976, ideal mixture at one temperature, with \(0 \le e < p\) and \(T > 0\). \(M_0 = 28.9644\,\mathrm{kg/kmol}\) and \(R^{*} = 8.31432\times 10^{3}\,\mathrm{J/(kmol\cdot K)}\) are the 1976 constants. \(M_w\) is `water_molar_mass`. The dry-air term is `atmosphere_density` at partial pressure \(p - e\). The water term is `atmosphere_density` at partial pressure \(e\), and it equals `absolute_humidity` when \(R_v = R^{*}/M_w\). This parcel calculation leaves the 1976 layer pressure and density integrals on dry air.

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

Vehicle and motor performance. In this category \(k\) is the ratio of specific heats. Nozzle area ratio and isentropic exit state use the Area-Mach and stagnation relations in Compressible flow. In the mass-flow section, \(V\) is specific volume. Circular-port grain area, web, and sliver fraction follow NASA SP-8076.

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

## Surface gravitational parameter

Inverse-square field matched to surface gravity \(g_0\) on a sphere of radius \(R\). Combined with `gravity_inverse_square`, \(g=\mu/r^{2}\) at radius \(r=R+Z\).

\[
\mu = g_0 R^{2}
\]

```formula
## gravitational_parameter_surface
family: rocket
expr: g0*R**2
symbols: g0, R
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(g_0\) | Gravitational acceleration at radius \(R\) | m/s² |
| \(R\) | Spherical body radius | m |

Assumptions: spherical body and inverse-square gravity. For Earth, the 1976 hydrostatic radius \(r_0=6.356766\times 10^{6}\,\mathrm{m}\) and \(g_0=9.80665\,\mathrm{m/s}^{2}\) give the default \(\mu\) of the powered-ascent program. A user \(\mu\) replaces this product.

## Powered-ascent acceleration along the path

NASA TM X-52396 writes the net force along the flight path as thrust minus the weight component \(W\sin\theta\) minus drag. Dividing by mass, with \(W=mg\),

\[
A = \frac{T}{m}-\frac{D}{m}-g\sin\theta
\]

```formula
## powered_path_acceleration
family: rocket
expr: T/m - D/m - g*sin(th)
symbols: T, m, D, g, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Acceleration along the velocity | m/s² |
| \(T\) | Thrust along the velocity | N |
| \(m\) | Instantaneous vehicle mass | kg |
| \(D\) | Drag along the velocity, opposite the motion | N |
| \(g\) | Local gravitational acceleration | m/s² |
| \(\theta\) | Flight-path angle above the local horizontal | rad |

Assumptions: planar motion. \(\theta=\pi/2\) is vertical. Thrust is along the velocity (zero angle of attack after a gravity-turn kick, or along the path in the constant-angle model). Drag is `drag_force` \(D=C_D q S\), a constant force, or zero. \(g=\mu/r^{2}\) on a sphere. The \(I_{sp}\) conversion \(c=I_s g_{0,\mathrm{std}}\) still uses \(g_{0,\mathrm{std}}=9.80665\,\mathrm{m/s}^{2}\), not this local \(g\). Vacuum thrust is \(T=\dot{m}c\) and does not vary with ambient pressure.

## Gravity, drag, and steering losses

Integrating `powered_path_acceleration` from rest splits the vacuum rocket equation into burnout speed and three losses. Gravity loss is the weight component along the path. Drag loss is drag over mass. Steering (cosine) loss is the unused thrust when the thrust vector is at an angle \(\varepsilon\) from the velocity:

\[
\Delta v_g = \int g\sin\theta\,\mathrm{d}t \qquad
\Delta v_D = \int \frac{D}{m}\,\mathrm{d}t \qquad
\Delta v_{\varepsilon} = \int \frac{T}{m}(1-\cos\varepsilon)\,\mathrm{d}t
\]

```formula
## gravity_loss_definition
family: rocket
expr: integral(g*sin(th), t)
symbols: g, th, t
```

```formula
## drag_loss_definition
family: rocket
expr: integral(D/m, t)
symbols: D, m, t
```

```formula
## steering_loss_definition
family: rocket
expr: integral((T/m)*(1 - cos(eps)), t)
symbols: T, m, eps, t
```

Then, from rest,

\[
V_{\mathrm{bo}} = c\ln\frac{m_0}{m_f}-\Delta v_g-\Delta v_D-\Delta v_{\varepsilon}
\]

```formula
## burnout_speed_from_losses
family: rocket
expr: c*log(m0/mf) - dvg - dvD - dve
symbols: c, m0, mf, dvg, dvD, dve
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\Delta v_g\) | Gravity loss | m/s |
| \(\Delta v_D\) | Drag loss | m/s |
| \(\Delta v_{\varepsilon}\) | Steering / cosine loss | m/s |
| \(V_{\mathrm{bo}}\) | Inertial speed at burnout | m/s |
| \(\varepsilon\) | Angle from the velocity to the thrust | rad |
| \(t\) | Time from ignition | s |

Assumptions: start from rest. \(c\) and \(\dot{m}\) are constant. After a gravity-turn kick, and in the constant-angle model, thrust stays along the velocity, so \(\varepsilon=0\) and \(\Delta v_{\varepsilon}=0\). A constant-angle path is held by a normal force that is not counted as drag. Local \(g\) may vary with radius.

## Constant flight-path-angle speed

Closed form of `powered_path_acceleration` at constant \(\theta\), constant \(g\), constant \(\dot{m}\), constant \(c\), and either no drag or a constant drag force \(D\). Mass is \(m=m_0-\dot{m}t\). The no-drag speed is NASA TM X-52396 at constant \(\theta\):

\[
V = c\ln\frac{m_0}{m}-g t\sin\theta
\]

```formula
## constant_angle_speed
family: rocket
expr: c*log(m0/m) - g*t*sin(th)
symbols: c, m0, m, g, t, th
```

A constant drag force adds `drag_loss` evaluated at constant \(\dot{m}\):

\[
\Delta v_D = \frac{D}{\dot{m}}\ln\frac{m_0}{m}
\]

```formula
## constant_drag_loss
family: rocket
expr: (D/mdot)*log(m0/m)
symbols: D, mdot, m0, m
```

```formula
## constant_angle_speed_const_drag
family: rocket
expr: c*log(m0/m) - g*t*sin(th) - (D/mdot)*log(m0/m)
symbols: c, m0, m, g, t, th, D, mdot
```

Path length from ignition, no drag:

\[
s = \int_0^{t_b} V\,\mathrm{d}t = \frac{c}{\dot{m}}\left(m_0-m_f-m_f\ln\frac{m_0}{m_f}\right)-\frac12 g t_b^{2}\sin\theta
\]

```formula
## constant_angle_path_length
family: rocket
expr: c*(m0 - mf - mf*log(m0/mf))/mdot - 0.5*g*tb**2*sin(th)
symbols: c, m0, mf, mdot, g, tb, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V\) | Speed along the path | m/s |
| \(s\) | Distance along the path from ignition | m |
| \(t_b\) | Burn time | s |
| \(\dot{m}\) | Propellant mass flow | kg/s |
| \(D\) | Constant drag force | N |

Assumptions: \(\theta\) held constant, \(g\) held at the ignition radius, \(\dot{m}>0\), and \(0<m\le m_0\). Vertical flight is \(\theta=\pi/2\) (NASA TM X-52390). Quadratic drag, a density that varies with altitude, and inverse-square \(g(r)\) during the burn are not this closed form; those cases integrate `powered_path_acceleration` numerically at fixed \(\theta\).

## Radial and local-horizontal speed

NASA TM X-52396 splits the path speed on the local vertical and horizontal. On a sphere those are the polar components, with \(r\) the radius from the body center:

\[
\dot{r}=V\sin\theta \qquad r\dot{\phi}=V\cos\theta
\]

```formula
## powered_radial_velocity
family: rocket
expr: V*sin(th)
symbols: V, th
```

```formula
## powered_horizontal_velocity
family: rocket
expr: V*cos(th)
symbols: V, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{r}\) | Radial speed, positive outward | m/s |
| \(r\dot{\phi}\) | Speed along the local horizontal | m/s |
| \(r\) | Radius from the body center | m |
| \(\phi\) | Downrange central angle | rad |

Assumptions: planar motion. \(\theta=0\) is local-horizontal flight. Combined with constant \(\theta\), \(\mathrm{d}\phi/\mathrm{d}r=\cot\theta/r\) when \(\sin\theta\neq 0\).

## Gravity-turn path-angle rate

With thrust along the velocity and no lift, NASA TM X-52396 steps the path angle as \(\Delta\theta=(g\cos\theta/V)\Delta t\) on a flat planet (the local horizontal does not rotate). On a sphere the same polar split adds the kinematic turn of that horizontal, \(V/r\), and \(g=\mu/r^{2}\):

\[
\dot{\theta}=\left(\frac{V}{r}-\frac{g}{V}\right)\cos\theta
\]

```formula
## gravity_turn_angle_rate
family: rocket
expr: (V/r - g/V)*cos(th)
symbols: V, r, g, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{\theta}\) | Rate of flight-path angle | rad/s |
| \(V\) | Speed | m/s |
| \(r\) | Radius from the body center | m |
| \(g\) | Local gravity, \(\mu/r^{2}\) | m/s² |
| \(\theta\) | Flight-path angle above the local horizontal | rad |

Assumptions: thrust along the velocity after an instantaneous kick from vertical, no lift, planar spherical kinematics. The rate is singular at \(V=0\); ignition uses polar accelerations with the kick direction as the thrust axis. A kick angle \(\alpha\) from vertical starts the path at \(\theta=\pi/2-\alpha\). The flat-planet TM X-52396 rate is the same formula with the \(V/r\) term dropped.

## Gravity-turn kick to a flight-path angle

Instantaneous pitch from local vertical onto a gravity-turn path.

\[
\theta = \frac{\pi}{2}-\alpha
\]

```formula
## kick_flight_path_angle
family: rocket
expr: pi/2 - alpha
symbols: pi, alpha
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\theta\) | Flight-path angle above the local horizontal | rad |
| \(\alpha\) | Kick angle from local vertical | rad |

Assumptions: \(\alpha=0\) is vertical. \(\alpha=\pi/2\) is a horizontal kick. Do not combine this kick with a prescribed constant \(\theta\).

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

## Sphere of influence

Classical Laplace radius of the sphere of influence of a secondary body of gravitational parameter \(\mu_2\) about a primary of gravitational parameter \(\mu_1\), separated by center-to-center distance \(D\). Burrows, NASA TM X-53485, derives the exact non-spherical activity surface and records the isotropic patched-conic approximation that keeps the leading mass-ratio power.

\[
r_{\mathrm{SOI}} = D\left(\frac{\mu_2}{\mu_1}\right)^{2/5} = D\left(\frac{m_2}{m_1}\right)^{2/5}
\]

```formula
## sphere_of_influence_radius
family: flight
expr: D*(mu2/mu1)**(2/5)
symbols: D, mu2, mu1
```

```formula
## sphere_of_influence_radius_from_mass
family: flight
expr: D*(m2/m1)**(2/5)
symbols: D, m2, m1
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r_{\mathrm{SOI}}\) | Sphere-of-influence radius about the secondary | m |
| \(D\) | Distance between the two body centers | m |
| \(\mu_1\) | Gravitational parameter of the primary (central) body | m³/s² |
| \(\mu_2\) | Gravitational parameter of the secondary (third) body | m³/s² |
| \(m_1\) | Mass of the primary | kg |
| \(m_2\) | Mass of the secondary | kg |

Assumptions: restricted three-body patched-conic handoff. Inverse-square point masses, \(\mu_2<\mu_1\) (equivalently \(m_2<m_1\)), and the isotropic Laplace form that omits Burrows’ angle-dependent Tisserand corrections. \(r_{\mathrm{SOI}}\) is measured from the secondary center. With \(\mu=GM\), the mass and \(\mu\) forms are identical. Swapping the labels gives the reciprocal sphere of the primary relative to the secondary, \(D(\mu_1/\mu_2)^{2/5}\).

## Sphere of influence in central-body radii

Laplace sphere-of-influence radius divided by the central-body radius \(R_0\).

\[
\frac{r_{\mathrm{SOI}}}{R_0}
\]

```formula
## sphere_of_influence_in_central_radii
family: flight
expr: rsoi/R0
symbols: rsoi, R0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r_{\mathrm{SOI}}/R_0\) | Sphere of influence in central-body radii | dimensionless |
| \(r_{\mathrm{SOI}}\) | Sphere-of-influence radius about the secondary | m |
| \(R_0\) | Central-body radius | m |

Assumptions: same Laplace radius as `sphere_of_influence_radius`. \(R_0>0\). For Earth, the default two-body radius is \(R_0=6.3742\times 10^{6}\,\mathrm{m}\) unless the user gives another value.

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

Assumptions: two-body inverse-square gravity and no drag or thrust. \(a > 0\) on an ellipse, \(1/a = 0\) on a parabola, and \(a < 0\) on a hyperbola. A circular orbit has \(a = r\), which recovers \(v = \sqrt{\mu/r}\). Escape speed is the parabolic case \(v = \sqrt{2\mu/r}\). On a hyperbola the same vis-viva limit as \(r\to\infty\) is the hyperbolic excess speed.

## Plane-change impulse

Impulsive cost of a pure inclination change that turns the velocity through an angle \(\Delta i\) at constant speed. Mesarch, Navigation and Mission Design Branch, NASA Goddard, *GDC Orbit Primer* (10 October 2018).

\[
\Delta v = 2 v \sin(\Delta i / 2)
\]

```formula
## plane_change_impulse
family: flight
expr: 2*v*sin(di/2)
symbols: v, di
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\Delta v\) | Plane-change impulse | m/s |
| \(v\) | Speed at the burn | m/s |
| \(\Delta i\) | Inclination change | rad |

Assumptions: the burn is impulsive and the speed is unchanged, so the turn is an equal-speed heading change. \(\Delta i\) is in radians. This record is only that pure inclination change. It does not combine a plane change with a radius change, and it does not include the primer’s combined inclination-and-node cost. The primer’s J2 rates are the records that follow.

## J2 nodal rate

First-order secular rate of the right ascension of the ascending node from Earth’s \(J_2\). Mesarch, Navigation and Mission Design Branch, NASA Goddard, *GDC Orbit Primer* (10 October 2018). Polar orbits have no nodal precession.

\[
\dot{\Omega} = -\frac{3 n J_2 R_E^{2} \cos i}{2 a^{2}(1-e^{2})^{2}}
\]

```formula
## j2_nodal_rate
family: flight
expr: -3*n*J2*RE**2*cos(i)/(2*a**2*(1-e**2)**2)
symbols: n, J2, RE, i, a, e
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{\Omega}\) | Secular nodal rate | rad/s |
| \(n\) | Mean motion \(\sqrt{\mu/a^{3}}\) | rad/s |
| \(J_2\) | Second zonal harmonic | dimensionless |
| \(R_E\) | Equatorial radius in the \(J_2\) term | m |
| \(i\) | Inclination | rad |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |

Assumptions: first-order \(J_2\) only; \(a\), \(e\), and \(i\) have no secular \(J_2\) rate. Ellipse, \(a > 0\), \(0 \le e < 1\). Mean motion is `mean_motion`. Earth defaults: \(R_E = 6378137\,\mathrm{m}\) (WGS 84), \(J_2 = 1.08228\times 10^{-3}\) (GSFC, March 1986, NASA RP-1204). \(\mu\) in \(n\) is still \(g_0 R_0^{2}\). A positive rate is eastward.

## J2 apsidal rate

First-order secular rate of the argument of periapsis from Earth’s \(J_2\). Same primer.

\[
\dot{\omega} = \frac{3 n J_2 R_E^{2} (4 - 5\sin^{2} i)}{4 a^{2}(1-e^{2})^{2}}
\]

```formula
## j2_apsidal_rate
family: flight
expr: 3*n*J2*RE**2*(4 - 5*sin(i)**2)/(4*a**2*(1-e**2)**2)
symbols: n, J2, RE, i, a, e
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{\omega}\) | Secular apsidal rate | rad/s |
| \(n\) | Mean motion | rad/s |
| \(J_2\) | Second zonal harmonic | dimensionless |
| \(R_E\) | Equatorial radius in the \(J_2\) term | m |
| \(i\) | Inclination | rad |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |

Assumptions: the same first-order \(J_2\) ellipse as `j2_nodal_rate`. The rate is zero at the critical inclinations \(\sin^{2} i = 4/5\). Perigee and apogee then stay at fixed latitudes under this model.

## Sun-synchronous nodal rate

Apparent mean solar motion that a sun-synchronous orbit matches with its nodal rate. Same primer: \(0.9856\,\mathrm{deg/day}\), which is \(360\,\mathrm{deg}\) in \(365.2422\) days.

\[
\dot{\Omega}_{\mathrm{ss}} = \frac{2\pi}{Y \times 86400}
\]

```formula
## sun_sync_nodal_rate
family: flight
expr: 2*pi/(Y*86400)
symbols: pi, Y
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{\Omega}_{\mathrm{ss}}\) | Target nodal rate for sun-synchronism | rad/s |
| \(Y\) | Mean solar year used in the primer | day |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: one day is \(86400\,\mathrm{s}\). The primer’s year is \(Y = 365.2422\,\mathrm{day}\). This is the apparent motion of the Sun, not Earth’s sidereal spin `omega_E`.

## Sun-synchronous inclination cosine

Cosine of the inclination at which `j2_nodal_rate` equals `sun_sync_nodal_rate`. Invert \(\dot{\Omega}\) for \(\cos i\).

\[
\cos i_{\mathrm{ss}} = -\frac{2 \dot{\Omega}_{\mathrm{ss}} a^{2}(1-e^{2})^{2}}{3 n J_2 R_E^{2}}
\]

```formula
## sun_sync_inclination_cosine
family: flight
expr: -2*Omegadot*a**2*(1-e**2)**2/(3*n*J2*RE**2)
symbols: Omegadot, a, e, n, J2, RE
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\cos i_{\mathrm{ss}}\) | Cosine of the sun-synchronous inclination | dimensionless |
| \(\dot{\Omega}_{\mathrm{ss}}\) | Target nodal rate | rad/s |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |
| \(n\) | Mean motion | rad/s |
| \(J_2\) | Second zonal harmonic | dimensionless |
| \(R_E\) | Equatorial radius in the \(J_2\) term | m |

Assumptions: the same first-order \(J_2\) ellipse. A real inclination exists only when the cosine lies in \([-1, 1]\). Then \(i_{\mathrm{ss}} = \arccos(\cos i_{\mathrm{ss}})\) on \([0, \pi]\). Earth sun-synchronism is retrograde. The primer’s \(700\,\mathrm{km}\) circular example is \(i_{\mathrm{ss}} = 98.2\,\mathrm{deg}\).

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

## Half-period elliptic coast

Time of flight along half of an elliptic two-body orbit, from one apsis to the other. That interval is half of `orbital_period`. NASA TM X-64662 uses two such coasts, one on each of the cotangential transfer ellipses of a coplanar three-impulse circle-to-circle transfer.

\[
t_{1/2} = \pi\sqrt{\frac{a^{3}}{\mu}}
\]

```formula
## elliptic_half_period
family: flight
expr: pi*(a**3/mu)**0.5
symbols: pi, a, mu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t_{1/2}\) | Coast from periapsis to apoapsis, or the reverse | s |
| \(a\) | Semi-major axis | m |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: unperturbed elliptic two-body motion, \(a > 0\). A Hohmann coast is one half-period. A coplanar bi-elliptic coast is the sum of two half-periods. A circle has \(a = r\), so this interval is half a revolution.

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

```formula
## semimajor_from_apsides
family: flight
expr: (ra + rp)/2
symbols: ra, rp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(r_p\) | Periapsis radius | m |
| \(r_a\) | Apoapsis radius | m |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |

Assumptions: \(r_p = a(1-e)\) is the periapsis of an ellipse or a hyperbola. The apoapsis and eccentricity-from-apsides records are ellipses, \(0 \le e < 1\) and \(r_a \ge r_p > 0\). Then \(a = (r_a + r_p)/2\). In this section \(e\) is eccentricity, not Oswald efficiency and not the base of the natural logarithm.

## Speed at an apsis

Vis-viva speed at one apsis of an ellipse whose other apsis is \(r_{\mathrm{far}}\). NASA TM X-64662 writes the periapsis and apoapsis forms of this identity for the two transfer ellipses of a three-impulse circular transfer. It is `vis_viva` with \(a = (r + r_{\mathrm{far}})/2\).

\[
v = \sqrt{\frac{2\mu r_{\mathrm{far}}}{r(r + r_{\mathrm{far}})}}
\]

```formula
## apsis_speed
family: flight
expr: (2*mu*rfar/(r*(r + rfar)))**0.5
symbols: mu, rfar, r
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v\) | Speed at radius \(r\) | m/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(r\) | Radius of the occupied apsis | m |
| \(r_{\mathrm{far}}\) | Radius of the opposite apsis | m |

Assumptions: ellipse, \(r > 0\), \(r_{\mathrm{far}} > 0\). Periapsis speed uses \(r = r_p\) and \(r_{\mathrm{far}} = r_a\). Apoapsis speed uses \(r = r_a\) and \(r_{\mathrm{far}} = r_p\). A circle has \(r = r_{\mathrm{far}}\) and recovers \(v = \sqrt{\mu/r}\).

## Classical orbital elements

Six quantities fix a Keplerian ellipse in space. NASA SP-325 and Plummer (1918) use the same set, with the names in NASA *Basics of Space Flight*:

- semi-major axis \(a\) and eccentricity \(e\), which fix the size and shape
- inclination \(i\) of the orbit plane to the reference plane
- longitude of the ascending node \(\Omega\)
- argument of periapsis \(\omega\), measured in the orbit plane from the ascending node to periapsis
- a time element: the time of periapsis passage \(t_p\), or the mean anomaly at a chosen epoch

The position in the orbit plane is the true anomaly \(\nu\), measured from periapsis in the direction of motion. The eccentric anomaly \(E\) is the angle at the centre of the auxiliary circle. The mean anomaly \(M\) grows uniformly with time. All three anomalies below are in radians. In these records \(M\) is mean anomaly, not mass or Mach number; \(n\) is mean motion; \(p\) is the semi-latus rectum, not pressure; and \(h\) is specific angular momentum, not altitude.

Records after the argument of latitude convert an inertial position and velocity into these elements and convert the elements back into that state. The inertial frame has \(+Z\) along the reference polar axis and \(+X\) as the origin of node longitude. NASA TM X-58153 and the Goddard ELCONO routine state the singular cases: \(\Omega = 0\) when \(i = 0\), and \(\omega = 0\) when \(e = 0\). On a circle, ELCONO sets the mean anomaly equal to the argument of latitude. SP-325 and ELCONO give the scalar eccentricity. They do not print an eccentricity vector.

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

## Parameter from specific angular momentum

The semi-latus rectum from the specific angular momentum. NASA SP-325 equation (1-36) is the inverse of `specific_angular_momentum`.

\[
p = \frac{h^{2}}{\mu}
\]

```formula
## parameter_from_angular_momentum
family: flight
expr: h**2/mu
symbols: h, mu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Semi-latus rectum | m |
| \(h\) | Specific angular momentum | m²/s |
| \(\mu\) | Gravitational parameter | m³/s² |

Assumptions: two-body inverse-square gravity. The relation holds for an ellipse, a parabola, and a hyperbola. \(h\) here is not altitude.

## Semi-major axis from energy and from the state

NASA SP-325 equation (1-47) rearranges the specific-energy relation for an ellipse. The Goddard ELCONO routine computes the same axis from radius and speed, \(a = \mu r/(2\mu - r v^{2})\).

\[
a = -\frac{\mu}{2\varepsilon} = \frac{\mu r}{2\mu - r v^{2}}
\]

```formula
## semimajor_axis_from_energy
family: flight
expr: -mu/(2*eps)
symbols: mu, eps
```

```formula
## semimajor_axis_from_state
family: flight
expr: mu*r/(2*mu - r*v**2)
symbols: mu, r, v
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a\) | Semi-major axis | m |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(\varepsilon\) | Specific orbital energy | J/kg |
| \(r\) | Radial distance | m |
| \(v\) | Relative orbital speed | m/s |

Assumptions: \(\varepsilon \neq 0\), so the path is an ellipse or a hyperbola. A parabola has \(\varepsilon = 0\) and no finite \(a\). SP-325 derives \(a = -\mu/(2\varepsilon)\) for the ellipse. The same rearrangement gives \(a < 0\) when \(\varepsilon > 0\), which is the hyperbolic sign already used with vis-viva. ELCONO’s form in \(r\) and \(v\) has the same split: the denominator is positive on an ellipse and negative on a hyperbola.

## Eccentricity from energy and from the axis

Scalar eccentricity of a conic. NASA SP-325 equation (1-37) uses specific energy and specific angular momentum. ELCONO uses the semi-major axis and the same angular momentum. The magnitude of an eccentricity vector is not printed in either source.

\[
e = \left(1 + \frac{2\varepsilon h^{2}}{\mu^{2}}\right)^{1/2} = \left(\frac{\mu a - h^{2}}{\mu a}\right)^{1/2}
\]

```formula
## eccentricity_from_energy
family: flight
expr: (1 + 2*eps*h**2/mu**2)**0.5
symbols: eps, h, mu
```

```formula
## eccentricity_from_axis
family: flight
expr: ((mu*a - h**2)/(mu*a))**0.5
symbols: mu, a, h
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(e\) | Eccentricity | dimensionless |
| \(\varepsilon\) | Specific orbital energy | J/kg |
| \(h\) | Specific angular momentum | m²/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(a\) | Semi-major axis | m |

Assumptions: the energy form covers every conic. \(\varepsilon < 0\) gives \(e < 1\), \(\varepsilon = 0\) gives \(e = 1\), and \(\varepsilon > 0\) gives \(e > 1\). The axis form needs a finite \(a \neq 0\), so it excludes the parabola. On that domain it agrees with \(h^{2} = \mu a(1-e^{2})\). In this section \(e\) is eccentricity.

## Hyperbolic excess and characteristic energy

Speed remaining as \(r\to\infty\) on a hyperbola, and the characteristic energy \(C_3\) of that planet-centered conic. NASA SP-325 vis-viva and specific energy give \(v_{\infty}^{2}=2\varepsilon=-\mu/a\). Bullock, NASA TM X-53319, names \(C_3\) as the square of the hyperbolic excess velocity.

\[
v_{\infty} = \sqrt{2\varepsilon} = \sqrt{-\mu/a} \qquad C_3 = v_{\infty}^{2} \qquad a = -\frac{\mu}{C_3} \qquad r_{\infty} = \frac{\mu}{v_{\infty}^{2}}
\]

```formula
## hyperbolic_excess_from_energy
family: flight
expr: (2*eps)**0.5
symbols: eps
```

```formula
## hyperbolic_excess_from_axis
family: flight
expr: (mu*(-1/a))**0.5
symbols: mu, a
```

```formula
## characteristic_energy
family: flight
expr: vinf**2
symbols: vinf
```

```formula
## semimajor_from_characteristic_energy
family: flight
expr: -mu/C3
symbols: mu, C3
```

```formula
## energy_radius_from_excess
family: flight
expr: mu/vinf**2
symbols: mu, vinf
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v_{\infty}\) | Hyperbolic excess speed | m/s |
| \(\varepsilon\) | Specific orbital energy | J/kg |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(a\) | Semi-major axis | m |
| \(C_3\) | Characteristic energy | m²/s² |
| \(r_{\infty}\) | Energy radius \(\lvert a\rvert=\mu/v_{\infty}^{2}\) | m |

Assumptions: hyperbola, \(\varepsilon>0\) and \(a<0\). \(r_{\infty}\) is the length implied by the excess speed alone; it is not a physical station on the path. Periapsis speed is `vis_viva` at \(r=r_p\). A circular park at that radius uses `circular_orbit_velocity`. The impulsive periapsis burn from that circle onto the hyperbola is the difference of those speeds.

## Hyperbolic eccentricity from periapsis

Scalar eccentricity of a hyperbola that has periapsis \(r_p\) and excess speed \(v_{\infty}\). Rearrange `periapsis_radius` with `semimajor_from_characteristic_energy`.

\[
e = 1 + \frac{r_p v_{\infty}^{2}}{\mu}
\]

```formula
## hyperbolic_eccentricity_from_periapsis
family: flight
expr: 1 + rp*vinf**2/mu
symbols: rp, vinf, mu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(e\) | Eccentricity | dimensionless |
| \(r_p\) | Periapsis radius | m |
| \(v_{\infty}\) | Hyperbolic excess speed | m/s |
| \(\mu\) | Gravitational parameter | m³/s² |

Assumptions: \(e>1\), so \(v_{\infty}>0\) and \(r_p>0\). Then \(r_p=a(1-e)\) with \(a=-\mu/v_{\infty}^{2}\).

## Hyperbola asymptote and turning angle

True anomaly at which the polar orbit equation of NASA SP-325 goes to infinity, \(1+e\cos\nu_{\infty}=0\), and the heading change between the incoming and outgoing asymptotes. At infinity the velocity is parallel to the radius, so that heading change is \(2\nu_{\infty}-\pi\), which is \(2\arcsin(1/e)\).

\[
\nu_{\infty} = \arccos(-1/e) \qquad \delta = 2\arcsin(1/e)
\]

```formula
## hyperbola_asymptote_true_anomaly
family: flight
expr: acos(-1/e)
symbols: e
```

```formula
## hyperbola_turning_angle
family: flight
expr: 2*asin(1/e)
symbols: e
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\nu_{\infty}\) | True anomaly of either asymptote | rad |
| \(\delta\) | Turning angle between the incoming and outgoing asymptotes | rad |
| \(e\) | Eccentricity | dimensionless |

Assumptions: hyperbola, \(e>1\). The incoming asymptote is \(-\nu_{\infty}\) and the outgoing asymptote is \(+\nu_{\infty}\). Both angles are in radians. \(\nu_{\infty}\) lies in \((\pi/2,\pi)\). As \(e\to 1^{+}\), \(\delta\to\pi\); as \(e\to\infty\), \(\delta\to 0\).

## Specific angular momentum vector

Plummer’s integrals of area are the components of angular momentum. For the specific angular momentum of one vehicle about the attracting centre they are the components of \(\mathbf{r}\times\mathbf{v}\). ELCONO writes that vector as \(\mathbf{h} = \mathbf{r}\times\dot{\mathbf{r}}\) and uses \(h^{2} = h_x^{2}+h_y^{2}+h_z^{2}\). The dot product \(\mathbf{r}\cdot\dot{\mathbf{r}}\) is the quantity ELCONO places in the true-anomaly formula.

\[
h_x = y v_z - z v_y \qquad
h_y = z v_x - x v_z \qquad
h_z = x v_y - y v_x
\]

\[
h = \sqrt{h_x^{2}+h_y^{2}+h_z^{2}} \qquad
\mathbf{r}\cdot\mathbf{v} = x v_x + y v_y + z v_z
\]

```formula
## specific_angular_momentum_x
family: flight
expr: y*vz - z*vy
symbols: y, vz, z, vy
```

```formula
## specific_angular_momentum_y
family: flight
expr: z*vx - x*vz
symbols: z, vx, x, vz
```

```formula
## specific_angular_momentum_z
family: flight
expr: x*vy - y*vx
symbols: x, vy, y, vx
```

```formula
## specific_angular_momentum_magnitude
family: flight
expr: (hx**2 + hy**2 + hz**2)**0.5
symbols: hx, hy, hz
```

```formula
## position_velocity_dot
family: flight
expr: x*vx + y*vy + z*vz
symbols: x, vx, y, vy, z, vz
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h_x, h_y, h_z\) | Specific-angular-momentum components | m²/s |
| \(h\) | Specific-angular-momentum magnitude | m²/s |
| \(x, y, z\) | Inertial position components | m |
| \(v_x, v_y, v_z\) | Inertial velocity components | m/s |
| \(\mathbf{r}\cdot\mathbf{v}\) | Position-velocity dot product | m²/s |

Assumptions: origin at the attracting centre, and \(+Z\) along the reference polar axis. The components are Plummer’s areal integrands for a single specific angular momentum. \(h = 0\) is a rectilinear path and does not define a plane.

## Inclination

Davis defines inclination as the angle between the north polar axis and the orbital angular-momentum vector. ELCONO writes the same angle as

\[
i = \tan^{-1}\left[\frac{(h_x^{2}+h_y^{2})^{1/2}}{h_z}\right]
\]

with \(0 \le i < \pi\). That two-argument angle is \(\cos^{-1}(h_z/h)\).

\[
i = \frac{\pi}{2} - \sin^{-1}\left(\frac{h_z}{h}\right)
\]

```formula
## inclination
family: flight
expr: pi/2 - asin(hz/h)
symbols: pi, hz, h
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(i\) | Inclination | rad |
| \(h_z\) | Polar component of specific angular momentum | m²/s |
| \(h\) | Specific-angular-momentum magnitude | m²/s |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: \(h > 0\). The result lies on \([0, \pi]\). It is \(0\) when \(\mathbf{h}\) points along \(+Z\) and \(\pi\) when \(\mathbf{h}\) points along \(-Z\). ELCONO’s printed interval is \(0 \le i < \pi\).

## Longitude of the ascending node

ELCONO, for \(i \neq 0\),

\[
\Omega = \tan^{-1}\left[\frac{h_x}{-h_y}\right], \qquad 0 \le \Omega < 2\pi
\]

and \(\Omega = 0\) when \(i = 0\). Davis states the same equatorial convention: the ascending node is the reference \(X\) axis. The sine and cosine below are the two-argument reading of that ratio. They are undefined when \(h_x = h_y = 0\), which is \(i = 0\) or \(i = \pi\).

\[
\sin\Omega = \frac{h_x}{\sqrt{h_x^{2}+h_y^{2}}} \qquad
\cos\Omega = \frac{-h_y}{\sqrt{h_x^{2}+h_y^{2}}}
\]

```formula
## ascending_node_sine
family: flight
expr: hx/(hx**2 + hy**2)**0.5
symbols: hx, hy
```

```formula
## ascending_node_cosine
family: flight
expr: -hy/(hx**2 + hy**2)**0.5
symbols: hy, hx
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\Omega\) | Longitude of the ascending node | rad |
| \(h_x, h_y\) | Equatorial components of specific angular momentum | m²/s |

Assumptions: \(h_x^{2}+h_y^{2} > 0\). The pair fixes \(\Omega\) on \([0, 2\pi)\). When \(i = 0\), do not evaluate these records; set \(\Omega = 0\).

## True anomaly from the state

SP-325 equation (1-34) is the inverse cosine of the combination below, so \(\cos\nu = (h^{2}/r - \mu)/(\mu e)\). ELCONO gives the tangent from the radial momentum,

\[
\tan\nu = \frac{h\,(\mathbf{r}\cdot\mathbf{v})}{h^{2} - \mu r}.
\]

The numerator has the sign of \(\sin\nu\) and the denominator has the sign of \(\cos\nu\).

```formula
## true_anomaly_cosine_from_state
family: flight
expr: (h**2/r - mu)/(mu*e)
symbols: h, r, mu, e
```

```formula
## true_anomaly_tangent_from_state
family: flight
expr: (h*rdv)/(h**2 - mu*r)
symbols: h, rdv, mu, r
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\nu\) | True anomaly | rad |
| \(h\) | Specific angular momentum | m²/s |
| \(r\) | Radial distance | m |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(e\) | Eccentricity | dimensionless |
| \(\mathbf{r}\cdot\mathbf{v}\) | Position-velocity dot product | m²/s |

Assumptions: \(e > 0\) for the cosine. The tangent denominator vanishes when \(\cos\nu = 0\). Together, the sign of \(\mathbf{r}\cdot\mathbf{v}\) and the cosine fix \(\nu\). On a circle, ELCONO does not separate \(\nu\) from the argument of latitude.

## Argument of latitude from inertial position

ELCONO, for \(i \neq 0\),

\[
u = \tan^{-1}\left[\frac{z}{\sin i\,(x\cos\Omega + y\sin\Omega)}\right].
\]

The sine and cosine are the two-argument reading of that ratio. On the equator, \(i = 0\), ELCONO uses \(u = \tan^{-1}(y/x)\).

```formula
## argument_of_latitude_cosine
family: flight
expr: (x*cos(Omega) + y*sin(Omega))/r
symbols: x, Omega, y, r
```

```formula
## argument_of_latitude_sine
family: flight
expr: z/(r*sin(i))
symbols: z, r, i
```

```formula
## equatorial_argument_cosine
family: flight
expr: x/r
symbols: x, r
```

```formula
## equatorial_argument_sine
family: flight
expr: y/r
symbols: y, r
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(u\) | Argument of latitude | rad |
| \(x, y, z\) | Inertial position | m |
| \(r\) | Radial distance | m |
| \(i\) | Inclination | rad |
| \(\Omega\) | Longitude of the ascending node | rad |

Assumptions: \(r > 0\). The inclined pair needs \(\sin i \neq 0\). The equatorial pair is the \(i = 0\) formula, with the spacecraft in the reference plane. In these records \(u\) is not specific internal energy.

## Argument of periapsis

ELCONO sets \(\omega = u - \nu\) when \(e \neq 0\), and \(\omega = 0\) when \(e = 0\). Davis states the circular convention as perigee at the ascending node.

\[
\omega = u - \nu
\]

```formula
## argument_of_periapsis
family: flight
expr: u - nu
symbols: u, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\omega\) | Argument of periapsis | rad |
| \(u\) | Argument of latitude | rad |
| \(\nu\) | True anomaly | rad |

Assumptions: \(e \neq 0\), with \(u\) and \(\nu\) in radians on one common branch. ELCONO places \(\omega\) on \([0, 2\pi)\). When \(e = 0\), set \(\omega = 0\) and set the mean anomaly equal to \(u\).

## Perifocal position on a general conic

Rectangular coordinates in the orbit plane, with the origin at the focus and \(+x\) toward periapsis. They are the polar resolution of SP-325 equation (1-38), whose angle \(\theta-\theta_0\) is the true anomaly. Plummer’s node-frame coordinates reduce to the same pair when the angle is measured from periapsis.

\[
x = r\cos\nu \qquad y = r\sin\nu
\]

```formula
## perifocal_x_true
family: flight
expr: r*cos(nu)
symbols: r, nu
```

```formula
## perifocal_y_true
family: flight
expr: r*sin(nu)
symbols: r, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x\) | Perifocal coordinate toward periapsis | m |
| \(y\) | Perifocal coordinate along the motion at periapsis | m |
| \(r\) | Radial distance | m |
| \(\nu\) | True anomaly | rad |

Assumptions: every conic with a defined periapsis, so \(e > 0\). The existing `perifocal_x` and `perifocal_y` remain the ellipse formulas in the eccentric anomaly. SP-325 and ELCONO do not print the compact perifocal velocity \(\sqrt{\mu/p}(-\sin\nu,\ e+\cos\nu,\ 0)\).

## Node-frame position

Plummer, section 65: axes with \(x_1\) through the ascending node and \(y_1\) in the orbit plane.

\[
x_1 = r\cos(\omega+\nu) \qquad y_1 = r\sin(\omega+\nu)
\]

The out-of-plane node-frame coordinate is \(0\).

```formula
## node_frame_x
family: flight
expr: r*cos(omega + nu)
symbols: r, omega, nu
```

```formula
## node_frame_y
family: flight
expr: r*sin(omega + nu)
symbols: r, omega, nu
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x_1, y_1\) | Position in the node frame | m |
| \(r\) | Radial distance | m |
| \(\omega\) | Argument of periapsis | rad |
| \(\nu\) | True anomaly | rad |

Assumptions: \(\omega+\nu\) is the argument of latitude. The same expressions are the inertial coordinates of a zero-inclination orbit whose node lies on \(+X\).

## Inertial position

ELCONO and Plummer’s section 65, with \(u = \omega+\nu\) and \(+Z\) toward the reference pole:

\[
\begin{aligned}
x &= r[\cos\Omega\cos u - \sin\Omega\cos i\sin u] \\
y &= r[\sin\Omega\cos u + \cos\Omega\cos i\sin u] \\
z &= r\sin i\sin u
\end{aligned}
\]

```formula
## inertial_position_x
family: flight
expr: r*(cos(Omega)*cos(u) - sin(Omega)*cos(i)*sin(u))
symbols: r, Omega, u, i
```

```formula
## inertial_position_y
family: flight
expr: r*(sin(Omega)*cos(u) + cos(Omega)*cos(i)*sin(u))
symbols: r, Omega, u, i
```

```formula
## inertial_position_z
family: flight
expr: r*sin(i)*sin(u)
symbols: r, i, u
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x, y, z\) | Inertial position | m |
| \(r\) | Radial distance | m |
| \(u\) | Argument of latitude | rad |
| \(i\) | Inclination | rad |
| \(\Omega\) | Longitude of the ascending node | rad |

Assumptions: angles in radians. SP-325 equation (1-100) is a different frame: its polar axis is \(+Y\). Use these three records for the \(+Z\) polar frame.

## Radial and transverse speed

ELCONO’s ellipse formulas, from the eccentric anomaly. NASA SP-325 equations (2-4) and (2-5) give the same split on any conic from the flight-path angle \(\gamma\) above the local horizontal. Specific angular momentum is then \(h = r V\cos\gamma\), from SP-325 equations (1-23) and (2-4).

\[
V_r = \frac{\sqrt{\mu a}}{r}\,e\sin E \qquad
V_p = \frac{\sqrt{\mu a}}{r}\sqrt{1-e^{2}}
\]

\[
\dot r = V\sin\gamma \qquad r\dot\theta = V\cos\gamma \qquad h = r V\cos\gamma
\]

```formula
## radial_velocity_eccentric
family: flight
expr: ((mu*a)**0.5)*e*sin(E)/r
symbols: mu, a, e, E, r
```

```formula
## transverse_velocity_eccentric
family: flight
expr: ((mu*a)**0.5)*((1 - e**2)**0.5)/r
symbols: mu, a, e, r
```

```formula
## radial_velocity
family: flight
expr: v*sin(gamma)
symbols: v, gamma
```

```formula
## transverse_velocity
family: flight
expr: v*cos(gamma)
symbols: v, gamma
```

```formula
## specific_angular_momentum_flight_path
family: flight
expr: r*v*cos(gamma)
symbols: r, v, gamma
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_r\) | Radial speed | m/s |
| \(V_p\) | Transverse speed | m/s |
| \(\dot r\) | Radial speed | m/s |
| \(r\dot\theta\) | Transverse speed | m/s |
| \(h\) | Specific angular momentum | m²/s |
| \(\mu\) | Gravitational parameter | m³/s² |
| \(a\) | Semi-major axis | m |
| \(e\) | Eccentricity | dimensionless |
| \(E\) | Eccentric anomaly | rad |
| \(r\) | Radial distance | m |
| \(V\) | Orbital speed | m/s |
| \(\gamma\) | Flight-path angle above the local horizontal | rad |

Assumptions: the eccentric-anomaly pair is an ellipse, \(a > 0\) and \(0 \le e < 1\). The flight-path trio holds for an ellipse, a parabola, and a hyperbola. \(\gamma = 0\) is horizontal flight. Those radial and transverse speeds are the \(V_r\) and \(V_p\) used in the inertial velocity below.

## Inertial velocity

ELCONO rotates the radial and transverse speeds into the inertial frame. Here \(u = \omega+\nu\), and \(x, y, z\) are the inertial position.

\[
\begin{aligned}
\dot x &= \frac{V_r}{r} x - V_p[\cos\Omega\sin u + \sin\Omega\cos i\cos u] \\
\dot y &= \frac{V_r}{r} y + V_p[-\sin\Omega\sin u + \cos\Omega\cos i\cos u] \\
\dot z &= \frac{V_r}{r} z + V_p\sin i\cos u
\end{aligned}
\]

```formula
## inertial_velocity_x
family: flight
expr: (Vr/r)*x - Vp*(cos(Omega)*sin(u) + sin(Omega)*cos(i)*cos(u))
symbols: Vr, r, x, Vp, Omega, u, i
```

```formula
## inertial_velocity_y
family: flight
expr: (Vr/r)*y + Vp*(-sin(Omega)*sin(u) + cos(Omega)*cos(i)*cos(u))
symbols: Vr, r, y, Vp, Omega, u, i
```

```formula
## inertial_velocity_z
family: flight
expr: (Vr/r)*z + Vp*sin(i)*cos(u)
symbols: Vr, r, z, Vp, i, u
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot x, \dot y, \dot z\) | Inertial velocity | m/s |
| \(V_r\) | Radial speed | m/s |
| \(V_p\) | Transverse speed | m/s |
| \(x, y, z\) | Inertial position | m |
| \(r\) | Radial distance | m |
| \(u\) | Argument of latitude | rad |
| \(i\) | Inclination | rad |
| \(\Omega\) | Longitude of the ascending node | rad |

Assumptions: \(r > 0\), and \(V_p\) is positive in the direction of increasing \(u\). On an ellipse, take \(V_r\) and \(V_p\) from the eccentric-anomaly records. On a parabola or a hyperbola, take them from the flight-path records.

## Mean anomaly from an epoch

Mean anomaly at a later time when the value at epoch is known. NASA SP-325 and Plummer write \(M = n(t-t_p)\). Shifting the zero from periapsis to an epoch \(t_0\) with mean anomaly \(M_0\) gives the same uniform rate.

\[
M = M_0 + n(t - t_0)
\]

```formula
## mean_anomaly_from_epoch
family: flight
expr: M0 + n*(t - t0)
symbols: M0, n, t, t0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Mean anomaly at time \(t\) | rad |
| \(M_0\) | Mean anomaly at epoch | rad |
| \(n\) | Mean motion | rad/s |
| \(t\) | Time | s |
| \(t_0\) | Epoch | s |

Assumptions: unperturbed elliptic two-body motion. \(n\) is `mean_motion`.

## Greenwich angle

Location of the Greenwich meridian east of the inertial \(+X\) axis (the vernal equinox in NASA RP-1204). With a constant Earth rotation rate the angle at a later time is the epoch value plus that rate times elapsed time. The WGS 84 nominal mean angular velocity is \(\omega_E = 7.292115\times 10^{-5}\,\mathrm{rad/s}\) (NIMA TR 8350.2 / NGA.STND.0036).

\[
\theta_G = \theta_{G0} + \omega_E(t - t_0)
\]

```formula
## greenwich_angle
family: flight
expr: theta0 + omega_e*(t - t0)
symbols: theta0, omega_e, t, t0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\theta_G\) | Greenwich angle at time \(t\) | rad |
| \(\theta_{G0}\) | Greenwich angle at epoch | rad |
| \(\omega_E\) | Nominal mean Earth angular velocity | rad/s |
| \(t\) | Time | s |
| \(t_0\) | Epoch | s |

Assumptions: uniform sidereal rotation about \(+Z\). The user supplies \(\theta_{G0}\). Do not take \(J_2\) or polar motion from this record.

## Earth-fixed position

Inertial position rotated about \(+Z\) by the Greenwich angle so that Earth-fixed \(+X\) lies in the Greenwich meridian. NASA RP-1204 relates the Earth-fixed axes to the inertial equator–equinox frame by that angle. The inverse of \(x = x_E\cos\theta_G - y_E\sin\theta_G\), \(y = x_E\sin\theta_G + y_E\cos\theta_G\) is

\[
\begin{aligned}
x_E &= x\cos\theta_G + y\sin\theta_G \\
y_E &= -x\sin\theta_G + y\cos\theta_G \\
z_E &= z
\end{aligned}
\]

```formula
## earth_fixed_x
family: flight
expr: x*cos(theta) + y*sin(theta)
symbols: x, y, theta
```

```formula
## earth_fixed_y
family: flight
expr: -x*sin(theta) + y*cos(theta)
symbols: x, y, theta
```

```formula
## earth_fixed_z
family: flight
expr: z
symbols: z
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(x_E, y_E, z_E\) | Earth-fixed position | m |
| \(x, y, z\) | Inertial position | m |
| \(\theta_G\) | Greenwich angle | rad |

Assumptions: the same \(+Z\) polar axis in both frames. \(\theta_G\) is `greenwich_angle`.

## Geocentric latitude and longitude

NASA RP-1204: geocentric latitude is the angle from the equatorial plane to the radius. Longitude is measured east from Greenwich in the Earth-fixed equator. NASA TM X-58153 uses the same longitude sense.

\[
\sin\phi_c = \frac{z_E}{r} \qquad
\cos\phi_c = \frac{\rho}{r} \qquad
\tan\phi_c = \frac{z_E}{\rho}
\]

\[
\sin\lambda = \frac{y_E}{\rho} \qquad
\cos\lambda = \frac{x_E}{\rho}
\]

```formula
## geocentric_latitude_sine
family: flight
expr: z/r
symbols: z, r
```

```formula
## geocentric_latitude_cosine
family: flight
expr: rho/r
symbols: rho, r
```

```formula
## geocentric_latitude_tangent
family: flight
expr: z/rho
symbols: z, rho
```

```formula
## longitude_sine
family: flight
expr: y/rho
symbols: y, rho
```

```formula
## longitude_cosine
family: flight
expr: x/rho
symbols: x, rho
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\phi_c\) | Geocentric latitude | rad |
| \(\lambda\) | East longitude from Greenwich | rad |
| \(r\) | Geocentric distance | m |
| \(\rho\) | Distance from the polar axis, \(\sqrt{x_E^2+y_E^2}\) | m |
| \(x_E, y_E, z_E\) | Earth-fixed position | m |

Assumptions: \(r > 0\). The tangent and the longitude pair need \(\rho > 0\). Two-argument reading of sine and cosine places \(\phi_c\) in \([-\pi/2,\pi/2]\) and \(\lambda\) in \((-\pi,\pi]\).

## Oblate spheroid flattening

NASA TN D-7522 equations (2)–(4). The WGS 84 ellipsoid uses equatorial radius \(a_e = 6378137.0\,\mathrm{m}\) and flattening \(1/f = 298.257223563\) (NIMA TR 8350.2).

\[
f = \frac{a_e - b}{a_e} \qquad b = a_e(1 - f) \qquad e^2 = f(2 - f)
\]

```formula
## flattening_from_radii
family: flight
expr: (ae - b)/ae
symbols: ae, b
```

```formula
## polar_radius_from_flattening
family: flight
expr: ae*(1 - f)
symbols: ae, f
```

```formula
## ellipsoid_eccentricity_squared
family: flight
expr: f*(2 - f)
symbols: f
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(f\) | Flattening | dimensionless |
| \(a_e\) | Equatorial radius of the spheroid | m |
| \(b\) | Polar radius of the spheroid | m |
| \(e^2\) | Square of the spheroid eccentricity | dimensionless |

Assumptions: \(a_e > b > 0\), so \(0 \le f < 1\). This \(e\) is spheroid eccentricity, not orbital eccentricity. These records do not change two-body \(\mu\).

## Geodetic latitude of the subsatellite point

NASA RP-1204: the subsatellite point is the foot of the local vertical on the spheroid. Geodetic latitude is the angle between the equatorial plane and that vertical. NASA TN D-7522 equation (8) on the surface, and equation (36) at geocentric distance \(r\), with \(p = r/a_e\) restored to dimensioned symbols, give

\[
\tan\phi_g = \frac{\tan\phi_c}{(1-f)^2}
\]

\[
\phi_g = \phi_c + f\frac{a_e}{r}\sin 2\phi_c + f^{2}\left(\frac{a_e^{2}}{r^{2}} - \frac{a_e}{4r}\right)\sin 4\phi_c
\]

The tangent form is exact for a point on the ellipsoid. The series is the altitude form of equation (36); third-order terms in \(f\) are omitted (order \(1\) in \(3\times 10^{7}\)).

```formula
## geodetic_latitude_tangent_surface
family: flight
expr: tan(phic)/(1 - f)**2
symbols: phic, f
```

```formula
## geodetic_latitude_from_geocentric
family: flight
expr: phic + f*(ae/r)*sin(2*phic) + f**2*((ae/r)**2 - ae/(4*r))*sin(4*phic)
symbols: phic, f, ae, r
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\phi_g\) | Geodetic latitude | rad |
| \(\phi_c\) | Geocentric latitude | rad |
| \(f\) | Flattening | dimensionless |
| \(a_e\) | Equatorial radius | m |
| \(r\) | Geocentric distance | m |

Assumptions: the series is NASA TN D-7522 equation (36) through order \(f^{2}\). Use it at the satellite radius; the resulting \(\phi_g\) is the geodetic latitude of the subsatellite point. A sphere has \(f = 0\) and \(\phi_g = \phi_c\). Longitude of the subsatellite point is the Earth-fixed longitude. Motion remains spherical two-body; flattening does not enter \(\mu\).

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

## Equilibrium chamber pressure

Steady solid-motor mass balance with Saint Robert's burning law. Grain generation \(\dot{m} = A_b r \rho_b\) equals nozzle throughput \(\dot{m} = p_1 A_t / c^{*}\), with \(r = a p_1^{n}\) and \(K = A_b/A_t\).

\[
p_1 = \left(K\, a\, \rho_b\, c^{*}\right)^{\frac{1}{1-n}}
\]

```formula
## equilibrium_chamber_pressure
family: rocket
expr: (K*a*rho_b*cstar)**(1/(1 - n))
symbols: K, a, rho_b, cstar, n
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p_1\) | Equilibrium chamber pressure | Pa |
| \(K\) | Burning-area ratio \(A_b/A_t\) | dimensionless |
| \(a\) | Burn-rate coefficient | m/(s·Pa\(^{n}\)) |
| \(\rho_b\) | Solid propellant density | kg/m³ |
| \(c^{*}\) | Characteristic velocity | m/s |
| \(n\) | Burn-rate pressure exponent | dimensionless |

Assumptions: quasi-steady mass balance (no free-volume accumulation), uniform regression at \(r = a p_1^{n}\), constant \(a\), \(n\), \(\rho_b\), and \(c^{*}\), and no erosive burning. Requires \(n < 1\) for a stable finite equilibrium. The script symbol for \(c^{*}\) is `cstar`.

## Circular-port burning area

Internal-burning circular perforation with inhibited ends. The burning surface is the cylindrical port wall.

\[
A_b = 2\pi r L
\]

```formula
## circular_port_burning_area
family: rocket
expr: 2*pi*r*L
symbols: r, L, pi
```

The same surface inverted for port radius or grain length:

\[
r = \frac{A_b}{2\pi L} \qquad L = \frac{A_b}{2\pi r}
\]

```formula
## circular_port_radius
family: rocket
expr: Ab/(2*pi*L)
symbols: Ab, L, pi
```

```formula
## circular_grain_length
family: rocket
expr: Ab/(2*pi*r)
symbols: Ab, r, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A_b\) | Burning surface area | m² |
| \(r\) | Instantaneous port radius | m |
| \(L\) | Grain length | m |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: concentric circular port, uniform length, ends inhibited so they do not burn. The outer radius does not enter \(A_b\) until the web is gone. In these records \(r\) is port radius, not burning rate.

## Web of a circular grain

Propellant thickness from the port to the outer radius. Initial web is the value at the starting port. Remaining web is the value at the current port.

\[
w_0 = R_o - R_p \qquad w_{\mathrm{rem}} = R_o - r \qquad r = R_o - w_{\mathrm{rem}}
\]

```formula
## initial_web
family: rocket
expr: Ro - Rp
symbols: Ro, Rp
```

```formula
## remaining_web
family: rocket
expr: Ro - r
symbols: Ro, r
```

```formula
## circular_port_from_remaining_web
family: rocket
expr: Ro - wrem
symbols: Ro, wrem
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(w_0\) | Initial web | m |
| \(w_{\mathrm{rem}}\) | Remaining web | m |
| \(R_o\) | Outer propellant radius | m |
| \(R_p\) | Initial port radius | m |
| \(r\) | Instantaneous port radius | m |

Assumptions: concentric circular port inside a circular outer radius. \(R_o > r \ge R_p > 0\). Web burnout with no sliver is \(r = R_o\) and \(w_{\mathrm{rem}} = 0\). The script symbol for remaining web is `wrem`.

## Circular-grain propellant volume

Loaded volume of a circular tube, and the volume still unburned at port radius \(r\).

\[
V_0 = \pi(R_o^{2} - R_p^{2})L \qquad V = \pi(R_o^{2} - r^{2})L
\]

```formula
## circular_grain_volume
family: rocket
expr: pi*(Ro**2 - Rp**2)*L
symbols: Ro, Rp, L, pi
```

```formula
## circular_remaining_volume
family: rocket
expr: pi*(Ro**2 - r**2)*L
symbols: Ro, r, L, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_0\) | Initial propellant volume | m³ |
| \(V\) | Remaining propellant volume | m³ |
| \(R_o\) | Outer propellant radius | m |
| \(R_p\) | Initial port radius | m |
| \(r\) | Instantaneous port radius | m |
| \(L\) | Grain length | m |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: concentric circular port, inhibited ends, no voids. Ends stay the same length.

## Sliver volume fraction

Unburned propellant volume after web burnout, divided by the loaded grain volume. NASA SP-8076 calls that remainder the sliver.

\[
s = \frac{V_{\mathrm{sliver}}}{V_0}
\]

```formula
## sliver_volume_fraction
family: rocket
expr: Vsliver/V0
symbols: Vsliver, V0
```

For a circular grain the port radius at that leftover volume is

\[
r_s = \sqrt{R_o^{2} - s(R_o^{2} - R_p^{2})}
\]

```formula
## sliver_port_radius
family: rocket
expr: (Ro**2 - s*(Ro**2 - Rp**2))**0.5
symbols: Ro, s, Rp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(s\) | Sliver volume fraction | dimensionless |
| \(V_{\mathrm{sliver}}\) | Sliver volume | m³ |
| \(V_0\) | Initial propellant volume | m³ |
| \(r_s\) | Port radius at the sliver volume | m |
| \(R_o\) | Outer propellant radius | m |
| \(R_p\) | Initial port radius | m |

Assumptions: \(0 \le s < 1\). A concentric circular port in a circular case has geometric sliver \(s = 0\) at \(r = R_o\). A prescribed \(s > 0\) stops the web history when the remaining volume fraction is \(s\). The script symbols are `Vsliver`, `V0`, and `s`. Percent sliver is \(100s\).

## Remaining-web time

Time for remaining web to fall from \(w_0\) to \(w_{\mathrm{rem}}\) at the local regression rate.

\[
t = \int_{w_{\mathrm{rem}}}^{w_0} \frac{\mathrm{d}w}{r}
\]

```formula
## remaining_web_time
family: rocket
expr: integral(wrem, w0, 1/rburn)
symbols: wrem, w0, rburn
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t\) | Time from ignition | s |
| \(w_{\mathrm{rem}}\) | Remaining web | m |
| \(w_0\) | Initial web | m |
| \(r\) | Burning rate | m/s |

Assumptions: remaining web decreases at the burning rate, \(\mathrm{d}w_{\mathrm{rem}}/\mathrm{d}t = -r\). The script symbol for that rate is `rburn` so it is not the port radius. When \(r\) varies, evaluate the integrand along the grain. A constant \(r\) recovers \(t = (w_0 - w_{\mathrm{rem}})/r\).

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

Incompressible flow and the dimensionless force and moment coefficients. Freestream dynamic pressure \(q_{\infty}\) is the dynamic-pressure relation in Compressible flow evaluated far ahead of the body. In this category \(V\) is flow speed. The two-dimensional Prandtl–Glauert factor follows NACA TN 1127. The isentropic critical pressure coefficient is `pressure_coefficient_from_mach` at local Mach 1 on the same stagnation streamline as NACA Report 1135. Critical Mach number follows NACA TN 1813: the freestream Mach at which that critical coefficient equals the Prandtl–Glauert correction of the incompressible minimum pressure coefficient. Wing geometry and induced drag follow NASA Glenn's Beginner's Guide (public-domain educational pages). The finite-wing lift curve follows NASA TP-2414 and NACA TN 1862. NACA four-digit thickness and mean-line ordinates follow NACA Report 460 and NASA TM X-3284. Thin-section lift, zero-lift angle, and quarter-chord moment follow Munk, NACA Report 142, applied to that mean line. Stall speed and load factor follow the usual force definitions used in FAA-H-8083 and NASA SP-367. Unaccelerated rate of climb is the specific excess power \((T-D)V/W\) of the X-57 power-off-glide note, with climb angle from that vertical component as in FAA-H-8083-25C Chapter 11. Coordinated level-turn bank, radius, and rate follow FAA-H-8083-25C Chapter 5. The sustained-turn load factor is that level-turn \(n\) with `drag_polar` when thrust equals drag. Symmetric pull-up load factor, flight-path radius, and pitch rate follow Johnson, NASA/TP-2009-215402 (NDARC), for an instantaneous wings-level pull-up from level flight. Takeoff ground roll on a level dry runway follows Diehl, NACA Report 450, with Hartman TN 557 resistance \(\mu(W-L)+D\) and Wetmore Report 583 rolling friction. Landing ground roll from contact to rest follows Gustafson, NACA WR L-245, with the same resistance, the same \(a=gF/W\), and Diehl’s integrals run from touchdown speed to zero. The default touchdown factor \(1.3\) is the FAA-H-8083-3C final-approach multiple of landing stall. Ideal propeller thrust, disk speed, induced velocity, and propulsive efficiency follow NASA Glenn's actuator-disk pages, with the incompressible ideal-efficiency definition of NACA RM L53A07. Steady unpowered glide angle, horizontal range from a height, and the force balance \(L=W\cos a\), \(D=W\sin a\) follow those same Glenn glide pages. Sink rate is the vertical component of true airspeed on that path. Breguet propeller range and endurance follow NACA Report 234. Breguet jet range follows Guynn (NASA Langley) and the cruise derivation in NASA TN D-6707. The stick-fixed neutral point and static margin follow NACA TN 1670.

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

With freestream dynamic pressure \(q_{\infty} = \gamma p_{\infty} M_{\infty}^{2}/2\) from `dynamic_pressure`,

\[
C_p = \frac{2}{\gamma M_{\infty}^{2}}\left(\frac{p}{p_{\infty}} - 1\right)
\]

```formula
## pressure_coefficient_from_mach
family: aerodynamics
expr: 2*(p/p_inf - 1)/(g*M**2)
symbols: p, p_inf, g, M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_p\) | Pressure coefficient | dimensionless |
| \(p\) | Local static pressure | Pa |
| \(p_{\infty}\) | Freestream static pressure | Pa |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: perfect-gas dynamic pressure \(q_{\infty} = \gamma p_{\infty} M_{\infty}^{2}/2\). On a circular cone, \(p\) is the surface static pressure after the conical shock and the isentropic shock-layer compression.

## Prandtl–Glauert factor

Two-dimensional linearized subsonic similarity factor from NACA TN 1127. For two-dimensional flow the surface pressures, and the lift coefficient they integrate to, are larger than the incompressible values by \(1/\beta\). That factor is not a universal three-dimensional correction.

\[
\beta = \sqrt{1 - M_{\infty}^{2}}
\]

```formula
## prandtl_glauert_factor
family: aerodynamics
expr: (1 - M**2)**0.5
symbols: M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\beta\) | Prandtl–Glauert factor | dimensionless |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |

Assumptions: steady, inviscid, shock-free subsonic flow, \(0 \le M_{\infty} < 1\). Disturbances are small. Two-dimensional flow only.

## Prandtl–Glauert coefficient

Incompressible pressure or lift coefficient corrected to a subsonic Mach number. NACA TN 1127 states that, in two-dimensional flow, the pressures on a thin cylindrical body at a given small angle of attack are increased by \(1/\beta\) over the incompressible values. The same factor applies to the lift coefficient obtained by integrating those pressures.

\[
C = \frac{C_{0}}{\sqrt{1 - M_{\infty}^{2}}}
\]

```formula
## prandtl_glauert_coefficient
family: aerodynamics
expr: C0/(1 - M**2)**0.5
symbols: C0, M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C\) | Compressible pressure or lift coefficient | dimensionless |
| \(C_{0}\) | Incompressible pressure or lift coefficient | dimensionless |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |

Assumptions: two-dimensional linearized subsonic flow, \(0 \le M_{\infty} < 1\). \(C_{0}\) is the incompressible value on the same geometry and angle of attack. The record is `prandtl_glauert_coefficient` \(= C_{0}/\)`prandtl_glauert_factor`. It is not the Göthert three-dimensional rule. The linearized correction fails as \(M_{\infty}\) approaches 1.

## Critical pressure coefficient

Pressure coefficient at a surface point where the local Mach number is 1, on an isentropic streamline from the freestream. Combine `sonic_pressure` and `stagnation_temperature` with `stagnation_pressure` to form \(p^{*}/p_{\infty}\), then `pressure_coefficient_from_mach`.

\[
C_{p,\mathrm{crit}} = \frac{2}{\gamma M_{\infty}^{2}}\left[\left(\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2}M_{\infty}^{2}\right)\right)^{\gamma/(\gamma - 1)} - 1\right]
\]

```formula
## critical_pressure_coefficient
family: aerodynamics
expr: 2*(((2/(g + 1))*(1 + ((g - 1)/2)*M**2))**(g/(g - 1)) - 1)/(g*M**2)
symbols: g, M
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_{p,\mathrm{crit}}\) | Pressure coefficient at local Mach 1 | dimensionless |
| \(M_{\infty}\) | Freestream Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: calorically perfect gas; isentropic flow from the freestream to the sonic point. \(C_{p,\mathrm{crit}} < 0\) for \(0 < M_{\infty} < 1\). At \(M_{\infty} = 1\), \(C_{p,\mathrm{crit}} = 0\). This is the exact isentropic coefficient, not the small-perturbation \(C_{p}^{*}\).

## Critical Mach number

Freestream Mach number at which sonic speed is first reached on the surface. NACA TN 1813 defines that Mach number and estimates it by applying the Prandtl–Glauert factor to a low-speed pressure distribution. Equate `prandtl_glauert_coefficient` of the incompressible minimum pressure coefficient to `critical_pressure_coefficient`. There is no closed algebraic inverse. The record is zero at the critical Mach number. Given \(C_{p0,\min}\), solve that equation for \(M_{\mathrm{cr}}\).

\[
\frac{C_{p0,\min}}{\sqrt{1 - M_{\mathrm{cr}}^{2}}}
-
\frac{2}{\gamma M_{\mathrm{cr}}^{2}}\left[\left(\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2}M_{\mathrm{cr}}^{2}\right)\right)^{\gamma/(\gamma - 1)} - 1\right]
= 0
\]

```formula
## critical_mach
family: aerodynamics
expr: C0/(1 - M**2)**0.5 - 2*(((2/(g + 1))*(1 + ((g - 1)/2)*M**2))**(g/(g - 1)) - 1)/(g*M**2)
symbols: C0, M, g
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M_{\mathrm{cr}}\) | Critical Mach number | dimensionless |
| \(C_{p0,\min}\) | Incompressible minimum pressure coefficient | dimensionless |
| \(M\) | Script Mach; \(M_{\mathrm{cr}}\) when the record is zero | dimensionless |
| \(\gamma\) | Ratio of specific heats | dimensionless |

Assumptions: two-dimensional Prandtl–Glauert correction of a suction peak, \(C_{p0,\min} < 0\), and isentropic local sonic flow. The first surface point to reach Mach 1 is taken as the minimum-pressure point. NACA TN 1813 also discusses a crest-sonic estimate of drag-divergence Mach number; that crest station is not this record. A positive \(C_{p0}\) is not a suction peak and does not define \(M_{\mathrm{cr}}\).

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

On `drag_polar`, \(C_D = C_{D0} + C_L^{2}/(\pi\, AR\, e)\). The ratio \(C_L/C_D\) is largest when parasite drag equals induced drag, \(C_D = 2 C_{D0}\) and \(C_L = \sqrt{\pi\, AR\, e\, C_{D0}}\):

\[
\left(\frac{L}{D}\right)_{\max} = \frac{1}{2}\sqrt{\frac{\pi\, AR\, e}{C_{D0}}}
\]

```formula
## max_lift_to_drag
family: aerodynamics
expr: 0.5*(pi*AR*e/CD0)**0.5
symbols: pi, AR, e, CD0
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \((L/D)_{\max}\) | Maximum lift-to-drag ratio on the two-term polar | dimensionless |
| \(\pi\) | Circle constant | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(e\) | Oswald efficiency | dimensionless |
| \(C_{D0}\) | Zero-lift drag coefficient | dimensionless |

Assumptions: \(C_{D0} > 0\), \(AR > 0\), and \(0 < e \le 1\). This value does not depend on weight, area, or density. It is `lift_to_drag` at that \(C_L\) and \(C_D\).

## Steady unpowered glide

Steady, unaccelerated descent with no thrust. NASA Glenn writes the glide angle \(a\) from the horizontal as the angle of a straight flight path. The tangent of that angle is the height lost over the horizontal distance flown, and the same tangent is the drag-to-lift ratio:

\[
\tan a = \frac{h}{d} = \frac{D}{L} = \frac{C_D}{C_L}
\]

\[
a = \operatorname{atan}\!\left(\frac{D}{L}\right)
\]

```formula
## glide_angle
family: aerodynamics
expr: atan(D/L)
symbols: D, L
```

```formula
## glide_angle_from_coefficients
family: aerodynamics
expr: atan(CD/CL)
symbols: CD, CL
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a\) | Glide angle below the horizontal | rad |
| \(h\) | Height lost | m |
| \(d\) | Horizontal distance flown | m |
| \(D\) | Drag | N |
| \(L\) | Lift | N |
| \(C_D\) | Drag coefficient | dimensionless |
| \(C_L\) | Lift coefficient | dimensionless |

Assumptions: constant-velocity glide, no wind, and a straight path. \(L > 0\) and \(D > 0\), so \(0 < a < \pi/2\). Glenn's glider-trajectory force balance is \(L\cos a + D\sin a = W\) and \(L\sin a = D\cos a\). Those two statements are \(L = W\cos a\) and \(D = W\sin a\).

\[
L = W\cos a
\]

```formula
## glide_lift
family: aerodynamics
expr: W*cos(a)
symbols: W, a
```

\[
D = W\sin a
\]

```formula
## glide_drag
family: aerodynamics
expr: W*sin(a)
symbols: W, a
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L\) | Lift, perpendicular to the flight path | N |
| \(D\) | Drag, along the flight path | N |
| \(W\) | Weight | N |
| \(a\) | Glide angle below the horizontal | rad |

Assumptions: the same steady unpowered balance as `glide_angle`. Weight is a force. \(0 < a < \pi/2\).

True airspeed follows `lift_force` with that lift and `freestream_dynamic_pressure`:

\[
V = \sqrt{\frac{2 W\cos a}{\rho S C_L}}
\]

```formula
## glide_speed
family: aerodynamics
expr: (2*W*cos(a)/(rho*S*CL))**0.5
symbols: W, a, rho, S, CL
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V\) | True airspeed along the flight path | m/s |
| \(W\) | Weight | N |
| \(a\) | Glide angle | rad |
| \(\rho\) | Air density | kg/m³ |
| \(S\) | Wing planform area | m² |
| \(C_L\) | Lift coefficient | dimensionless |

Assumptions: incompressible \(q=\frac12\rho V^{2}\). \(C_L > 0\), \(\cos a > 0\). At \(a = 0\) this is `stall_speed` with \(C_{L,\max}\) replaced by \(C_L\).

The sink rate is the vertical component of that airspeed. It is the height lost per unit time on Glenn's right triangle. At a small glide angle it equals the power-off specific excess power \(D V/W\) of the X-57 power-off-glide note.

\[
v_s = V\sin a
\]

```formula
## sink_rate
family: aerodynamics
expr: V*sin(a)
symbols: V, a
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(v_s\) | Sink rate, positive downward | m/s |
| \(V\) | True airspeed | m/s |
| \(a\) | Glide angle | rad |

Assumptions: still air. \(v_s > 0\) in a descent. The shallowest \(a\) on `drag_polar` is at `max_lift_to_drag`. That condition is the best-range glide. Minimum sink is a different \(C_L\), near the minimum-power point \(C_L = \sqrt{3 C_{D0}/k}\) of the same polar.

Horizontal range from a height drop \(h\) is Glenn's \(d = h/\tan a\). With \(\tan a = 1/(L/D)\) that is \(h\) times the lift-to-drag ratio. The largest range uses \((L/D)_{\max}\).

\[
d = \frac{h}{\tan a}
\]

```formula
## glide_range
family: aerodynamics
expr: h/tan(a)
symbols: h, a
```

\[
d = h\,\frac{L}{D}
\]

```formula
## glide_range_from_ld
family: aerodynamics
expr: h*LD
symbols: h, LD
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(d\) | Horizontal distance | m |
| \(h\) | Height lost | m |
| \(a\) | Glide angle | rad |
| \(L/D\) | Lift-to-drag ratio | dimensionless |
| \(LD\) | Script symbol for \(L/D\) | dimensionless |

Assumptions: constant \(a\) and constant density over the height drop. Still air. \(0 < a < \pi/2\) and \(h > 0\). This is not Breguet cruise range. Geometric altitude used for the 1976 density is a separate input from this height.

## Steady climb

Unaccelerated climb with thrust or useful power. NASA’s X-57 power-off-glide note writes the specific excess power and identifies it with rate of climb (or descent). With \(L = W\),

\[
P_s = \frac{(T-D)V}{W}
\]

That vertical speed is the rate of climb. FAA-H-8083-25C Chapter 11 states the same quantity as the vertical component of the flight-path speed.

```formula
## rate_of_climb
family: aerodynamics
expr: (T-D)*V/W
symbols: T, D, V, W
```

Useful power delivered to the airplane is `useful_thrust` times speed, \(P = T V\), so the same rate is

\[
P_s = \frac{P - D V}{W}
\]

```formula
## rate_of_climb_from_power
family: aerodynamics
expr: (P - D*V)/W
symbols: P, D, V, W
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_s\) | Rate of climb (specific excess power) | m/s |
| \(T\) | Available thrust | N |
| \(D\) | Drag | N |
| \(V\) | True airspeed along the flight path | m/s |
| \(W\) | Weight | N |
| \(P\) | Useful power | W |

Assumptions: steady, unaccelerated flight, still air, and the small-angle model \(L = W\) used in that X-57 Method 1. Weight is a force. A negative value is a descent. Constant thrust uses `rate_of_climb` with \(T\) independent of speed. Constant useful power uses `rate_of_climb_from_power`, or equivalently `rate_of_climb` after `useful_thrust`. Drag is `drag_force` on `drag_polar` at \(C_L = W/(q S)\) with `freestream_dynamic_pressure` \(q\). This is not a zoom or an accelerated climb.

The climb angle above the horizontal then satisfies \(P_s = V\sin\gamma\), so \(\sin\gamma = (T-D)/W\):

\[
\gamma = \operatorname{asin}\!\left(\frac{T-D}{W}\right)
\]

```formula
## climb_angle
family: aerodynamics
expr: asin((T-D)/W)
symbols: T, D, W
```

\[
\gamma = \operatorname{asin}\!\left(\frac{P_s}{V}\right)
\]

```formula
## climb_angle_from_rate
family: aerodynamics
expr: asin(roc/V)
symbols: roc, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\gamma\) | Climb angle above the horizontal | rad |
| \(T\) | Available thrust | N |
| \(D\) | Drag | N |
| \(W\) | Weight | N |
| \(P_s\) | Rate of climb | m/s |
| \(roc\) | Script symbol for \(P_s\) | m/s |
| \(V\) | True airspeed | m/s |

Assumptions: still air and the same \(L = W\) model as `rate_of_climb`. \(\lvert(T-D)/W\rvert\le 1\) or the angle is not real on that model. \(\gamma > 0\) is a climb. This \(\gamma\) is not the unpowered `glide_angle` \(a\) below the horizontal.

FAA-H-8083-25C Chapter 11 defines the service ceiling as the altitude at which the airplane cannot climb at a rate greater than 100 feet per minute, and the absolute ceiling as zero rate of climb. In SI that cutoff is

\[
\left(\frac{\mathrm{d}h}{\mathrm{d}t}\right)_{\mathrm{svc}} = \frac{100\times 0.3048}{60}
\]

```formula
## service_ceiling_rate
family: aerodynamics
expr: n*ft_to_m/min_to_s
symbols: n, ft_to_m, min_to_s
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \((\mathrm{d}h/\mathrm{d}t)_{\mathrm{svc}}\) | Service-ceiling rate of climb | m/s |
| \(n\) | Handbook cutoff in feet per minute | ft/min |
| \(ft\_to\_m\) | Metre per foot | m/ft |
| \(min\_to\_s\) | Second per minute | s/min |

Assumptions: \(n = 100\), \(ft\_to\_m = 0.3048\), and \(min\_to\_s = 60\), so the SI cutoff is \(0.508\,\mathrm{m/s}\). Absolute ceiling is `rate_of_climb` equal to zero, not this cutoff. Density versus geometric altitude is the 1976 standard unless the station uses `AERO - DensityAndPressureAltitude`.

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

Assumptions: \(W\) is the vehicle weight, not mass times a local \(g\) different from the weight definition in use. Straight and level flight has \(n = 1\) when \(L = W\). In a coordinated level turn, \(n = 1/\cos\phi\) from `level_turn_load_factor`.

## Coordinated level turn

Steady, coordinated, constant-altitude turn. The lift vector is tilted by the bank angle \(\phi\). The vertical component balances weight, \(L\cos\phi = W\), so the load factor is \(n = L/W = 1/\cos\phi\). The horizontal component \(L\sin\phi\) is the centripetal force \(m V^{2}/R\) with \(m = W/g\). FAA-H-8083-25C Chapter 5 states that load factor, and the radius and rate of turn (there with knot, foot, and degree conversion constants 11.26 and 1091). The records below are the same relations in SI.

\[
n = \frac{1}{\cos\phi}
\]

```formula
## level_turn_load_factor
family: aerodynamics
expr: 1/cos(phi)
symbols: phi
```

\[
R = \frac{V^{2}}{g\tan\phi}
\]

```formula
## level_turn_radius
family: aerodynamics
expr: V**2/(g*tan(phi))
symbols: V, g, phi
```

\[
\omega = \frac{g\tan\phi}{V}
\]

```formula
## level_turn_rate
family: aerodynamics
expr: g*tan(phi)/V
symbols: g, phi, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(n\) | Load factor | dimensionless |
| \(\phi\) | Bank angle | rad |
| \(R\) | Turn radius | m |
| \(\omega\) | Turn rate | rad/s |
| \(V\) | True airspeed | m/s |
| \(g\) | Gravitational acceleration | m/s² |

Assumptions: coordinated, constant-altitude turn with \(L\cos\phi = W\) and no sideslip. \(0 < \phi < \pi/2\) so \(n > 1\) and \(\tan\phi\) is finite and positive. \(\omega = V/R\). Equivalently \(\tan\phi = \sqrt{n^{2}-1}\), \(R = V^{2}/(g\sqrt{n^{2}-1})\), and \(\omega = g\sqrt{n^{2}-1}/V\). Use \(g = 9.80665\,\mathrm{m/s}^{2}\) unless the user gives another value. Incompressible dynamic pressure \(\frac{1}{2}\rho V^{2}\) sets the stall limit: the steepest bank at a speed is `level_turn_load_factor` at the `load_factor` from `lift_force` with \(C_{L,\max}\). That is the same speed–stall relation as `stall_speed` with \(W\) replaced by \(nW\). The bank the engine can hold at a speed is a different load factor: `sustained_turn_load_factor`, with thrust equal to drag at \(L = nW\).

Useful power delivered to the airplane is thrust times speed, so the constant-power case uses \(T = P/V\).

\[
T = \frac{P}{V}
\]

```formula
## useful_thrust
family: aerodynamics
expr: P/V
symbols: P, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T\) | Useful thrust | N |
| \(P\) | Useful power | W |
| \(V\) | True airspeed | m/s |

Assumptions: \(P\) is the power that becomes \(T V\), after propeller efficiency if the user started from shaft power. For the ideal actuator disk that efficiency is `ideal_propulsive_efficiency` and the thrust is `ideal_propeller_thrust`. Jet thrust that does not change with speed is not this record; pass that thrust directly.

On `drag_polar`, \(C_D = C_{D0} + k C_L^{2}\) with \(k = 1/(\pi\, AR\, e)\) from `induced_drag_coefficient`. A coordinated level turn has \(L = nW\), so \(C_L = nW/(q S)\) at `freestream_dynamic_pressure` \(q\). Setting thrust equal to drag and solving for the load factor gives

\[
n = \sqrt{\frac{q S\,(T - q S C_{D0})\,\pi\, AR\, e}{W^{2}}}
\]

```formula
## sustained_turn_load_factor
family: aerodynamics
expr: ((q*S*(T - q*S*CD0)*pi*AR*e)/(W**2))**0.5
symbols: q, S, T, CD0, pi, AR, e, W
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(n\) | Sustained load factor at thrust equal to drag | dimensionless |
| \(q\) | Freestream dynamic pressure | Pa |
| \(S\) | Wing planform area | m² |
| \(T\) | Available thrust | N |
| \(C_{D0}\) | Zero-lift drag coefficient | dimensionless |
| \(\pi\) | Circle constant | dimensionless |
| \(AR\) | Aspect ratio | dimensionless |
| \(e\) | Oswald efficiency | dimensionless |
| \(W\) | Weight | N |

Assumptions: steady, coordinated, constant-altitude flight so \(L\cos\phi = W\) and \(T = D\). \(T > q S C_{D0}\) or \(n\) is not real. \(0 < e \le 1\). This \(n\) is the bank the engine can hold at that speed. It is not the stall limit. A turn still needs \(n > 1\). For constant useful power, replace \(T\) by `useful_thrust`. At the maximum-\(L/D\) condition \(C_D = 2 C_{D0}\), constant thrust gives the peak \(n = (T/W)(L/D)_{\max}\). The same \(n\) at \(T = D\) and \(L = nW\) is the sustained load factor available in a symmetric pull-up at that speed.

## Symmetric pull-up

Instantaneous wings-level pull-up in the vertical plane, started from straight and level flight. Lift exceeds weight, so the path curves upward with flight-path radius \(R\). With flight-path angle \(\gamma = 0\) at initiation, the normal force balance is \(L - W = m V^{2}/R\) with \(m = W/g\). Johnson, NASA/TP-2009-215402 (NDARC), writes that balance as \(n = 1 + V^{2}/(gR)\) for a constant-load-factor pull-up segment, with pitch rate \(\dot{\theta} = V/R\).

\[
n = 1 + \frac{V^{2}}{g R}
\]

```formula
## pullup_load_factor
family: aerodynamics
expr: 1 + V**2/(g*R)
symbols: V, g, R
```

\[
R = \frac{V^{2}}{g(n - 1)}
\]

```formula
## pullup_radius
family: aerodynamics
expr: V**2/(g*(n - 1))
symbols: V, g, n
```

\[
\omega = \frac{g(n - 1)}{V}
\]

```formula
## pullup_pitch_rate
family: aerodynamics
expr: g*(n - 1)/V
symbols: g, n, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(n\) | Load factor | dimensionless |
| \(R\) | Pull-up flight-path radius | m |
| \(\omega\) | Pitch rate \(\dot{\theta}\) | rad/s |
| \(V\) | True airspeed | m/s |
| \(g\) | Gravitational acceleration | m/s² |

Assumptions: wings-level symmetric pull-up initiated from horizontal flight so \(\gamma = 0\) and \(L - W = m V^{2}/R\). \(n > 1\) so the radius is finite and positive. \(\omega = V/R\). Equivalently \(n = 1 + V\omega/g\). Use \(g = 9.80665\,\mathrm{m/s}^{2}\) unless the user gives another value. This is an instantaneous (point) performance statement at the given speed; a sustained circular loop at constant properties is not implied. Incompressible dynamic pressure \(\frac{1}{2}\rho V^{2}\) sets the stall limit: the largest \(n\) at a speed is `load_factor` from `lift_force` with \(C_{L,\max}\), the same speed–stall relation as `stall_speed` with \(W\) replaced by \(nW\). The engine-limited sustained \(n\) at a speed is `sustained_turn_load_factor`, with thrust equal to drag at \(L = nW\).

## Takeoff ground roll

Level, dry, zero-wind runway from brake release to lift-off. Diehl, NACA Report 450, writes the net accelerating force as thrust minus air drag minus rolling friction, with friction following the wheel load. Hartman, NACA TN 557, writes that resistance as \(\mu(W-L)+D\). Wetmore, NACA Report 583, takes rolling friction as a coefficient times the load on the wheels. Lift and drag are `lift_force` and `drag_force` at `freestream_dynamic_pressure`. On a level runway the wheel normal force is the weight that lift has not yet carried:

\[
N = W - L
\]

```formula
## wheel_normal_force
family: aerodynamics
expr: W - L
symbols: W, L
```

\[
F_r = \mu N
\]

```formula
## rolling_friction
family: aerodynamics
expr: mu*N
symbols: mu, N
```

\[
F = T - D - \mu(W - L)
\]

```formula
## ground_roll_net_force
family: aerodynamics
expr: T - D - mu*(W - L)
symbols: T, D, mu, W, L
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(N\) | Wheel normal force | N |
| \(W\) | Weight | N |
| \(L\) | Lift | N |
| \(F_r\) | Rolling friction | N |
| \(\mu\) | Rolling-friction coefficient | dimensionless |
| \(F\) | Net accelerating force along the runway | N |
| \(T\) | Thrust along the runway | N |
| \(D\) | Aerodynamic drag | N |

Assumptions: level dry runway, no wind, no slope, and no braking. \(L < W\) while the wheels are on the runway. \(\mu \ge 0\). Rotation is not a separate segment; \(C_L\) is the takeoff (ground-attitude) lift coefficient, constant. Ground effect is omitted.

Diehl's acceleration along the run is \(a = g F/W\), with mass \(W/g\):

\[
a = \frac{g F}{W}
\]

```formula
## ground_roll_acceleration
family: aerodynamics
expr: g*F/W
symbols: g, F, W
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a\) | Acceleration along the runway | m/s² |
| \(g\) | Gravitational acceleration | m/s² |
| \(F\) | Net accelerating force | N |
| \(W\) | Weight | N |

Assumptions: weight is a force. Use \(g = 9.80665\,\mathrm{m/s}^{2}\) unless the user gives another value. \(F > 0\) or the airplane does not accelerate toward lift-off.

Lift-off true airspeed is a factor times takeoff stall speed. Stall speed is `stall_speed` at \(C_{L,\max}\) when that coefficient is given, otherwise at the takeoff lift coefficient. The program default factor is \(1.2\).

\[
V_{\mathrm{LO}} = k_{\mathrm{LO}} V_{\mathrm{stall}}
\]

```formula
## liftoff_speed
family: aerodynamics
expr: kLO*Vs
symbols: kLO, Vs
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_{\mathrm{LO}}\) | Lift-off true airspeed | m/s |
| \(k_{\mathrm{LO}}\) | Lift-off speed factor | dimensionless |
| \(V_{\mathrm{stall}}\) | Takeoff stall speed | m/s |
| \(kLO\) | Script symbol for \(k_{\mathrm{LO}}\) | dimensionless |
| \(Vs\) | Script symbol for \(V_{\mathrm{stall}}\) | m/s |

Assumptions: still air, so true airspeed equals ground speed. \(k_{\mathrm{LO}} > 0\). This is not calibrated airspeed. Obstacle clearance, climb-out, and balanced field length are omitted.

Constant thrust, constant \(C_L\), and `drag_polar` make \(F\) quadratic in speed. With \(q=\frac12\rho V^{2}\),

\[
A = g\left(\frac{T}{W}-\mu\right),\qquad
B = \frac{g\rho S}{2W}(C_D-\mu C_L),\qquad
a = A - B V^{2}.
\]

```formula
## ground_roll_A
family: aerodynamics
expr: g*(T/W - mu)
symbols: g, T, W, mu
```

```formula
## ground_roll_B
family: aerodynamics
expr: g*rho*S*(CD - mu*CL)/(2*W)
symbols: g, rho, S, CD, mu, CL, W
```

Diehl's distance and time are \(\displaystyle s=\int_0^{V} V\,\mathrm{d}V/a\) and \(\displaystyle t=\int_0^{V}\mathrm{d}V/a\). For constant \(A\) and \(B\neq 0\),

\[
s = \frac{1}{2B}\log\frac{A}{A-B V^{2}}
\]

```formula
## ground_roll_distance
family: aerodynamics
expr: (1/(2*B))*log(A/(A - B*V**2))
symbols: B, A, V
```

When \(A>0\), \(B>0\), and \(A>B V^{2}\),

\[
t = \frac{1}{2\sqrt{A B}}\log\frac{\sqrt{A}+V\sqrt{B}}{\sqrt{A}-V\sqrt{B}}
\]

```formula
## ground_roll_time
family: aerodynamics
expr: (1/(2*(A*B)**0.5))*log((A**0.5 + V*B**0.5)/(A**0.5 - V*B**0.5))
symbols: A, B, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Acceleration at zero speed | m/s² |
| \(B\) | Coefficient of \(V^{2}\) in \(a=A-BV^{2}\) | 1/m |
| \(T\) | Constant thrust | N |
| \(W\) | Weight | N |
| \(\mu\) | Rolling-friction coefficient | dimensionless |
| \(g\) | Gravitational acceleration | m/s² |
| \(\rho\) | Air density | kg/m³ |
| \(S\) | Wing planform area | m² |
| \(C_D\) | Drag coefficient at the takeoff \(C_L\) | dimensionless |
| \(C_L\) | Takeoff lift coefficient | dimensionless |
| \(V\) | True airspeed, equal to ground speed | m/s |
| \(s\) | Ground-roll distance from rest | m |
| \(t\) | Ground-roll time from rest | s |

Assumptions: constant thrust, constant attitude, incompressible \(q\), level dry runway, still air. \(A>0\) and \(A-B V^{2}>0\) through lift-off. \(B\neq 0\) in `ground_roll_distance`; if \(B=0\) then \(s=V^{2}/(2A)\) and \(t=V/A\). `ground_roll_time` as written needs \(B>0\). If \(B<0\), time is \(\operatorname{atan}\!\left(V\sqrt{|B|/A}\right)/\sqrt{A|B|}\). Useful power that varies thrust as `useful_thrust`, with a finite static cap, is not this closed form; integrate \(V/a(V)\) numerically. Diehl's linear-in-\(V\) chart method is not these records.

## Landing ground roll

Level, dry, zero-wind runway from touchdown to rest. Gustafson, NACA WR L-245, writes the decelerating force as air drag plus wheel friction \(\mu(W-L)\). That is Diehl's `ground_roll_net_force` with idle or other constant thrust \(T\) left in:

\[
F = T - D - \mu(W - L)
\]

Wheel load is `wheel_normal_force`. Friction is `rolling_friction` with \(\mu\) the braking-friction coefficient. Acceleration is `ground_roll_acceleration` \(a = g F/W\). Lift and drag stay `lift_force` and `drag_force` at a constant touchdown lift coefficient. \(F\) is negative through the stop. Idle thrust is omitted as \(T = 0\).

Touchdown true airspeed is a factor times landing stall speed. Stall speed is `stall_speed` at \(C_{L,\max}\) when that coefficient is given, otherwise at the touchdown lift coefficient. The program default factor is \(1.3\), the FAA-H-8083-3C final-approach multiple of landing stall, applied at contact. Flare, float, and a 50-foot obstacle are omitted.

\[
V_{\mathrm{TD}} = k_{\mathrm{TD}} V_{\mathrm{stall}}
\]

```formula
## touchdown_speed
family: aerodynamics
expr: kTD*Vs
symbols: kTD, Vs
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_{\mathrm{TD}}\) | Touchdown true airspeed | m/s |
| \(k_{\mathrm{TD}}\) | Touchdown speed factor | dimensionless |
| \(V_{\mathrm{stall}}\) | Landing stall speed | m/s |
| \(kTD\) | Script symbol for \(k_{\mathrm{TD}}\) | dimensionless |
| \(Vs\) | Script symbol for \(V_{\mathrm{stall}}\) | m/s |

Assumptions: still air, so true airspeed equals ground speed. \(k_{\mathrm{TD}} > 0\). This is not calibrated airspeed. \(L < W\) at contact or the wheels are not loaded.

Constant thrust, constant \(C_L\), and `drag_polar` again make \(a = A - B V^{2}\) with `ground_roll_A` and `ground_roll_B`. Diehl's distance and time from a speed \(V\) to rest are \(\displaystyle s=\int_{V}^{0} V\,\mathrm{d}V/a\) and \(\displaystyle t=\int_{V}^{0}\mathrm{d}V/a\). For constant \(A\) and \(B\neq 0\),

\[
s = \frac{1}{2B}\log\frac{A-B V^{2}}{A}
\]

```formula
## landing_ground_roll_distance
family: aerodynamics
expr: (1/(2*B))*log((A - B*V**2)/A)
symbols: B, A, V
```

When \(A<0\), \(B<0\), and \(A-B V^{2}<0\),

\[
t = \frac{1}{2\sqrt{(-A)(-B)}}\log\frac{\sqrt{-A}+V\sqrt{-B}}{\sqrt{-A}-V\sqrt{-B}}
\]

```formula
## landing_ground_roll_time
family: aerodynamics
expr: (1/(2*((-A)*(-B))**0.5))*log(((-A)**0.5 + V*(-B)**0.5)/((-A)**0.5 - V*(-B)**0.5))
symbols: A, B, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Acceleration at zero speed | m/s² |
| \(B\) | Coefficient of \(V^{2}\) in \(a=A-BV^{2}\) | 1/m |
| \(V\) | Touchdown true airspeed | m/s |
| \(s\) | Ground-roll distance from touchdown to rest | m |
| \(t\) | Ground-roll time from touchdown to rest | s |

Assumptions: constant thrust, constant attitude, incompressible \(q\), level dry runway, still air, brakes applied from contact. \(A<0\) and \(A-B V^{2}<0\) through the stop. \(B\neq 0\) in `landing_ground_roll_distance`; if \(B=0\) then \(s=-V^{2}/(2A)\) and \(t=-V/A\). `landing_ground_roll_time` as written needs \(B<0\). If \(B>0\), time is \(\operatorname{atan}\!\left(V\sqrt{B/(-A)}\right)/\sqrt{(-A)B}\). A reverse-thrust schedule that is not a single constant \(T\) is omitted. Gustafson's attitude-change chart is not these records.

## Ideal actuator-disk propeller

Incompressible Rankine–Froude momentum theory. NASA Glenn treats the spinning propeller as a disk of area \(A\) through which the air passes. Subscripts \(0\), \(p\), and \(e\) are freestream, the disk, and the far wake. There is no pressure-area term because the far-wake static pressure returns to freestream. Combining the momentum thrust with Bernoulli applied upstream and downstream of the disk, but not through it, gives the disk speed as the average of the freestream and far-wake speeds. NACA RM L53A07 records the same uniformly loaded disk with a constant axial interference velocity and no slipstream rotation. Shaft power in this model is the power added to the slipstream. Blade profile drag, tip loss, swirl, and compressibility are omitted, so the thrust and the efficiency are ideal.

\[
A = \frac{\pi D^{2}}{4}
\]

```formula
## propeller_disk_area
family: aerodynamics
expr: pi*D**2/4
symbols: pi, D
```

\[
V_p = \frac{1}{2}(V_e + V_0)
\]

```formula
## actuator_disk_speed
family: aerodynamics
expr: 0.5*(Ve + V0)
symbols: Ve, V0
```

The axial induced velocity at the disk is the interference velocity of the simple momentum theory, half the far-wake increment.

\[
v_i = V_p - V_0 = \frac{1}{2}(V_e - V_0)
\]

```formula
## propeller_induced_velocity
family: aerodynamics
expr: Vp - V0
symbols: Vp, V0
```

```formula
## propeller_far_wake_speed
family: aerodynamics
expr: V0 + 2*vi
symbols: V0, vi
```

Glenn's two expressions for ideal thrust are identical once \(V_p\) is the average. With \(v_i\) they are \(T = 2\rho A v_i(V_0 + v_i)\).

\[
T = \rho V_p A(V_e - V_0) = \frac{1}{2}\rho A(V_e^{2} - V_0^{2})
\]

```formula
## ideal_propeller_thrust
family: aerodynamics
expr: rho*Vp*A*(Ve - V0)
symbols: rho, Vp, A, Ve, V0
```

```formula
## ideal_propeller_thrust_bernoulli
family: aerodynamics
expr: 0.5*rho*A*(Ve**2 - V0**2)
symbols: rho, A, Ve, V0
```

```formula
## ideal_propeller_thrust_from_induced
family: aerodynamics
expr: 2*rho*A*vi*(V0 + vi)
symbols: rho, A, vi, V0
```

Given thrust, the physical root of that quadratic is

\[
v_i = \frac{1}{2}\left(-V_0 + \sqrt{V_0^{2} + \frac{2T}{\rho A}}\right).
\]

```formula
## propeller_induced_velocity_from_thrust
family: aerodynamics
expr: 0.5*(-V0 + (V0**2 + 2*T/(rho*A))**0.5)
symbols: V0, T, rho, A
```

The power added to the slipstream is the thrust times the speed through the disk. That is the ideal shaft power: the kinetic-energy rise \(\frac12\dot m(V_e^{2}-V_0^{2})\) equals \(T V_p\).

\[
P = T V_p = 2\rho A v_i(V_0 + v_i)^{2}
\]

```formula
## ideal_actuator_power
family: aerodynamics
expr: T*Vp
symbols: T, Vp
```

```formula
## ideal_actuator_power_from_induced
family: aerodynamics
expr: 2*rho*A*vi*(V0 + vi)**2
symbols: rho, A, vi, V0
```

Ideal propulsive efficiency is thrust power over that shaft power, \(\eta = T_c/P_c\) in RM L53A07.

\[
\eta = \frac{T V_0}{P} = \frac{V_0}{V_p}
\]

```formula
## ideal_propulsive_efficiency
family: aerodynamics
expr: T*V0/P
symbols: T, V0, P
```

```formula
## ideal_propulsive_efficiency_from_speeds
family: aerodynamics
expr: V0/Vp
symbols: V0, Vp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Propeller disk area | m² |
| \(D\) | Propeller diameter | m |
| \(\pi\) | Circle constant | dimensionless |
| \(V_0\) | True airspeed, far ahead of the disk | m/s |
| \(V_p\) | Axial speed through the disk | m/s |
| \(V_e\) | Far-wake axial speed | m/s |
| \(v_i\) | Axial induced velocity at the disk | m/s |
| \(T\) | Ideal thrust | N |
| \(\rho\) | Freestream density | kg/m³ |
| \(P\) | Ideal shaft power added to the slipstream | W |
| \(\eta\) | Ideal propulsive efficiency | dimensionless |

Assumptions: incompressible, inviscid, uniformly loaded actuator disk of zero thickness. No swirl, no tip loss, and no blade profile drag. \(D > 0\), \(A > 0\), \(\rho > 0\), \(V_0 > 0\), \(V_e > V_0\), and \(v_i > 0\). Then \(0 < \eta < 1\). \(P\) is shaft power in this ideal model, not the useful power \(T V_0\). Useful power is `useful_thrust` times speed after this \(\eta\), or equivalently \(T V_0\). Static hover \(V_0 = 0\) makes \(\eta = 0\) and is not these flight records. Compressible actuator-disk solutions in RM L53A07 are not these records.

## Ideal turbojet (Brayton)

Parametric ideal air-breathing turbojet from the NASA Glenn Brayton / component pages (V77), with efficiency and TSFC definitions from Morris TM 78653 (V78). Calorically perfect gas with constant \(c_p\) and \(\gamma\). Perfect inlet recovery, isentropic compressor and turbine, constant-pressure burner with \(\mathrm{BPR}=1\) and burner efficiency 1, adiabatic fully expanded nozzle (\(p_e=p_0\)), no fan, and no afterburner. Freestream totals use `stagnation_temperature` and `stagnation_pressure`. \(T_{t2}=T_{t0}\) and \(p_{t2}=p_{t0}\). Turbine inlet temperature is \(T_{t4}\). Compressor pressure ratio is \(\pi_c=p_{t3}/p_{t2}\).

Isentropic compressor temperature ratio and work per unit airflow:

\[
\tau_c = \pi_c^{(\gamma-1)/\gamma},\qquad
w_c = c_p T_{t2}(\tau_c - 1) = c_p(T_{t3}-T_{t2})
\]

```formula
## isentropic_compressor_temperature_ratio
family: aerodynamics
expr: pi_c**((g - 1)/g)
symbols: pi_c, g
```

```formula
## ideal_compressor_work
family: aerodynamics
expr: cp*Tt2*(tau_c - 1)
symbols: cp, Tt2, tau_c
```

Ideal compressor–turbine shaft match (component efficiencies 1; fuel mass neglected in the match, as on the Glenn matching page):

\[
\pi_t^{(\gamma-1)/\gamma} = 1 - \frac{T_{t2}}{T_{t4}}(\tau_c - 1)
\]

```formula
## ideal_turbine_temperature_ratio
family: aerodynamics
expr: 1 - (Tt2/Tt4)*(tau_c - 1)
symbols: Tt2, Tt4, tau_c
```

```formula
## ideal_turbine_pressure_ratio
family: aerodynamics
expr: tau_t**(g/(g - 1))
symbols: tau_t, g
```

Burner fuel–air ratio from the energy balance with heating value \(Q\) and burner efficiency 1:

\[
f = \frac{c_p(T_{t4}-T_{t3})}{Q - c_p T_{t4}}
\]

```formula
## burner_fuel_air_ratio
family: aerodynamics
expr: cp*(Tt4 - Tt3)/(Q - cp*Tt4)
symbols: cp, Tt4, Tt3, Q
```

Nozzle pressure ratio for the ideal single-spool turbojet (\(\mathrm{BPR}=1\), perfect nozzle) and exit velocity and static temperature:

\[
\mathrm{NPR} = \frac{p_{t0}}{p_0}\,\pi_c\,\pi_t,\qquad
V_e = \sqrt{2 c_p T_{t5}\left(1 - \mathrm{NPR}^{-(\gamma-1)/\gamma}\right)},\qquad
T_e = T_{t5}\,\mathrm{NPR}^{-(\gamma-1)/\gamma}
\]

with \(T_{t5}=T_{t4}\tau_t\) and \(T_{t8}=T_{t5}\).

```formula
## ideal_turbojet_nozzle_pressure_ratio
family: aerodynamics
expr: (pt0/p0)*pi_c*pi_t
symbols: pt0, p0, pi_c, pi_t
```

```formula
## ideal_nozzle_exit_velocity
family: aerodynamics
expr: (2*cp*Tt*(1 - NPR**(-(g - 1)/g)))**0.5
symbols: cp, Tt, NPR, g
```

```formula
## ideal_nozzle_exit_temperature
family: aerodynamics
expr: Tt*NPR**(-(g - 1)/g)
symbols: Tt, NPR, g
```

Specific thrust and mass-based thrust-specific fuel consumption:

\[
F_s = (1+f)V_e - V_0,\qquad
c_t = \frac{f}{F_s}
\]

```formula
## turbojet_specific_thrust
family: aerodynamics
expr: (1 + f)*Ve - V0
symbols: f, Ve, V0
```

```formula
## turbojet_tsfc
family: aerodynamics
expr: f/Fs
symbols: f, Fs
```

Thermal, propulsive, and overall efficiencies (Morris; fuel heat \(f Q\) per unit airflow):

\[
\eta_{\mathrm{th}} = \frac{(1+f)V_e^{2}-V_0^{2}}{2 f Q},\qquad
\eta_p = \frac{2 V_0 F_s}{(1+f)V_e^{2}-V_0^{2}},\qquad
\eta_o = \frac{F_s V_0}{f Q} = \eta_{\mathrm{th}}\eta_p
\]

```formula
## turbojet_thermal_efficiency
family: aerodynamics
expr: ((1 + f)*Ve**2 - V0**2)/(2*f*Q)
symbols: f, Ve, V0, Q
```

```formula
## turbojet_propulsive_efficiency
family: aerodynamics
expr: 2*V0*Fs/((1 + f)*Ve**2 - V0**2)
symbols: V0, Fs, f, Ve
```

```formula
## turbojet_overall_efficiency
family: aerodynamics
expr: Fs*V0/(f*Q)
symbols: Fs, V0, f, Q
```

Ideal Brayton cycle thermal efficiency from the overall compression ratio \(\pi_r\pi_c\), with ram temperature ratio \(\tau_r=T_{t0}/T_0\):

\[
\eta_{\mathrm{Brayton}} = 1 - \frac{1}{(\pi_r\pi_c)^{(\gamma-1)/\gamma}} = 1 - \frac{1}{\tau_r\tau_c}
\]

```formula
## ideal_brayton_thermal_efficiency
family: aerodynamics
expr: 1 - 1/(tau_r*tau_c)
symbols: tau_r, tau_c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\pi_c\) | Compressor pressure ratio \(p_{t3}/p_{t2}\) (script `pi_c`) | dimensionless |
| \(\tau_c\) | Compressor total-temperature ratio \(T_{t3}/T_{t2}\) (script `tau_c`) | dimensionless |
| \(\pi_t\) | Turbine pressure ratio \(p_{t5}/p_{t4}\) (script `pi_t`) | dimensionless |
| \(\tau_t\) | Turbine total-temperature ratio \(T_{t5}/T_{t4}\) (script `tau_t`) | dimensionless |
| \(\tau_r\) | Ram total-temperature ratio \(T_{t0}/T_0\) (script `tau_r`) | dimensionless |
| \(T_{t2}, T_{t3}, T_{t4}, T_{t5}\) | Station total temperatures (scripts `Tt2`, `Tt3`, `Tt4`, `Tt`) | K |
| \(p_{t0}, p_0\) | Freestream total and static pressure (scripts `pt0`, `p0`) | Pa |
| \(\mathrm{NPR}\) | Nozzle pressure ratio \(p_{t8}/p_0\) (script `NPR`) | dimensionless |
| \(c_p\) | Specific heat at constant pressure (script `cp`) | J/(kg·K) |
| \(Q\) | Fuel lower heating value | J/kg |
| \(f\) | Fuel–air mass ratio | dimensionless |
| \(V_0, V_e\) | Flight speed and fully expanded exit speed (scripts `V0`, `Ve`) | m/s |
| \(F_s\) | Specific thrust (script `Fs`) | m/s |
| \(c_t\) | Mass-based TSFC | kg/(N·s) |
| \(\gamma\) | Ratio of specific heats (script `g`) | dimensionless |
| \(\eta_{\mathrm{th}}, \eta_p, \eta_o\) | Thermal, propulsive, and overall efficiency | dimensionless |

Assumptions: calorically perfect gas; ideal components; fully expanded nozzle; no afterburner; no fan; no real maps. \(T_{t4}>T_{t3}\), \(Q>c_p T_{t4}\), \(\pi_c>1\), \(\mathrm{NPR}>1\), and \(F_s>0\). Static \(V_0=0\) makes \(\eta_p=\eta_o=0\). The Brayton closed form is the heat-engine thermal efficiency of the same overall pressure ratio; the kinetic `turbojet_thermal_efficiency` is the flight definition used with TSFC.

## Breguet range and endurance

Cruise distance and time while fuel burn lowers the airplane weight. Lift equals weight and thrust equals drag. \(L/D\), speed, and specific fuel consumption are taken constant over the segment. The weight ratio uses the same weight unit at the start and end of cruise. \(\log\) in the script records is the natural logarithm.

For a jet, fuel flow follows thrust. Thrust-specific fuel consumption \(c_t\) is fuel weight flow divided by thrust, so its SI unit is \(1/\mathrm{s}\). Guynn states the range. Endurance is that range divided by the constant cruise speed, which is the integral of \(\mathrm{d}t = -\mathrm{d}W/(c_t D)\) with \(D = W/(L/D)\).

\[
R_{\mathrm{jet}} = \frac{V}{c_t}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

```formula
## breguet_range_jet
family: aerodynamics
expr: (V/ct)*LD*log(Wi/Wf)
symbols: V, ct, LD, Wi, Wf
```

\[
E_{\mathrm{jet}} = \frac{1}{c_t}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

```formula
## breguet_endurance_jet
family: aerodynamics
expr: (1/ct)*LD*log(Wi/Wf)
symbols: ct, LD, Wi, Wf
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(R_{\mathrm{jet}}\) | Cruise range | m |
| \(E_{\mathrm{jet}}\) | Cruise endurance | s |
| \(V\) | True airspeed | m/s |
| \(c_t\) | Thrust-specific fuel consumption, fuel weight flow per unit thrust | 1/s |
| \(L/D\) | Lift-to-drag ratio | dimensionless |
| \(LD\) | Script symbol for \(L/D\) | dimensionless |
| \(W_i\) | Weight at the start of cruise | N |
| \(W_f\) | Weight at the end of cruise | N |

Assumptions: steady cruise with \(L = W\) and \(T = D\). \(V\), \(L/D\), and \(c_t\) are constant. \(W_i > W_f > 0\). \(c_t > 0\). A value of \(c_t\) quoted in \(1/\mathrm{hr}\) is divided by \(3600\) before use. If the user gives a mass-based TSFC in \(\mathrm{kg/(N\cdot s)}\), multiply by \(g_0 = 9.80665\,\mathrm{m/s}^2\) to obtain this weight-based \(c_t\). NASA TN D-6707 derives the same cruise integral for constant-velocity flight with fuel flow from thrust-specific fuel consumption.

For a propeller airplane, fuel flow follows shaft power. Power-specific fuel consumption \(c\) is fuel weight flow divided by shaft power, so its SI unit is \(1/\mathrm{m}\). Propeller efficiency \(\eta\) converts shaft power to useful propulsive power. NACA Report 234 states Breguet’s equations in historical English units; the records below are the same relations in SI with the natural logarithm.

\[
R_{\mathrm{prop}} = \frac{\eta}{c}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

```formula
## breguet_range_prop
family: aerodynamics
expr: (eta/c)*LD*log(Wi/Wf)
symbols: eta, c, LD, Wi, Wf
```

\[
E_{\mathrm{prop}} = \frac{\eta}{c V}\,\frac{L}{D}\,\ln\frac{W_i}{W_f}
\]

```formula
## breguet_endurance_prop
family: aerodynamics
expr: (eta/(c*V))*LD*log(Wi/Wf)
symbols: eta, c, V, LD, Wi, Wf
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(R_{\mathrm{prop}}\) | Cruise range | m |
| \(E_{\mathrm{prop}}\) | Cruise endurance | s |
| \(\eta\) | Propeller efficiency | dimensionless |
| \(c\) | Power-specific fuel consumption, fuel weight flow per unit shaft power | 1/m |
| \(V\) | True airspeed | m/s |
| \(L/D\) | Lift-to-drag ratio | dimensionless |
| \(LD\) | Script symbol for \(L/D\) | dimensionless |
| \(W_i\) | Weight at the start of cruise | N |
| \(W_f\) | Weight at the end of cruise | N |

Assumptions: steady cruise with \(L = W\) and thrust power equal to drag times speed. \(\eta\), \(c\), \(L/D\), and for endurance \(V\) are constant. \(0 < \eta \le 1\), \(c > 0\), and \(W_i > W_f > 0\). In this section \(c\) is power-specific fuel consumption, not mean aerodynamic chord and not the rocket effective exhaust velocity. A value of \(c\) in historical units such as \(\mathrm{lb/(hp\cdot hr)}\) must be converted to \(1/\mathrm{m}\) before the call. If the user gives a mass-based power-specific fuel consumption in \(\mathrm{kg/(W\cdot s)}\), multiply by \(g_0 = 9.80665\,\mathrm{m/s}^2\) to obtain this weight-based \(c\). Propeller range does not contain \(V\) when \(c\) and \(\eta\) are constant. Propeller endurance and both jet results need the cruise speed shown above.

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

## NACA four-digit thickness and mean line

The four-digit family of NACA Report 460. The first digit is maximum camber in percent of chord, the second is the chordwise station of that camber in tenths of chord, and the last two digits are maximum thickness in percent of chord. Chordwise station \(\xi = x/c\) runs from the leading edge to the trailing edge. NASA TM X-3284 records the same thickness polynomial and the same two-parabola camber line.

The basic thickness is a 20-percent-chord section. Any other thickness scales those ordinates by \(t/0.20\):

\[
\frac{y_t}{c} = \frac{t}{0.20}\left(0.2969\,\xi^{1/2} - 0.1260\,\xi - 0.3516\,\xi^{2} + 0.2843\,\xi^{3} - 0.1015\,\xi^{4}\right)
\]

```formula
## naca4_thickness
family: aerodynamics
expr: (t/0.2)*(0.2969*xi**0.5 - 0.1260*xi - 0.3516*xi**2 + 0.2843*xi**3 - 0.1015*xi**4)
symbols: t, xi
```

Forward of maximum camber, and aft of it,

\[
\frac{y_c}{c} = \frac{m}{p^{2}}\left(2p\xi - \xi^{2}\right)
\qquad 0 \le \xi \le p
\]

```formula
## naca4_camber_forward
family: aerodynamics
expr: (m/p**2)*(2*p*xi - xi**2)
symbols: m, p, xi
```

\[
\frac{y_c}{c} = \frac{m}{(1-p)^{2}}\left((1-2p) + 2p\xi - \xi^{2}\right)
\qquad p \le \xi \le 1
\]

```formula
## naca4_camber_aft
family: aerodynamics
expr: (m/(1-p)**2)*((1 - 2*p) + 2*p*xi - xi**2)
symbols: m, p, xi
```

The mean-line slopes that set the surface normal are

\[
\frac{\mathrm{d}(y_c/c)}{\mathrm{d}\xi} = \frac{2m}{p^{2}}(p - \xi)
\qquad 0 \le \xi \le p
\]

```formula
## naca4_camber_slope_forward
family: aerodynamics
expr: (2*m/p**2)*(p - xi)
symbols: m, p, xi
```

\[
\frac{\mathrm{d}(y_c/c)}{\mathrm{d}\xi} = \frac{2m}{(1-p)^{2}}(p - \xi)
\qquad p \le \xi \le 1
\]

```formula
## naca4_camber_slope_aft
family: aerodynamics
expr: (2*m/(1-p)**2)*(p - xi)
symbols: m, p, xi
```

Thickness is laid off along the local normal. \(\theta = \tan^{-1}(\mathrm{d}y_c/\mathrm{d}x)\).

\[
\frac{x_u}{c} = \xi - \frac{y_t}{c}\sin\theta
\qquad
\frac{y_u}{c} = \frac{y_c}{c} + \frac{y_t}{c}\cos\theta
\]

```formula
## naca4_upper_x
family: aerodynamics
expr: xi - yt*sin(theta)
symbols: xi, yt, theta
```

```formula
## naca4_upper_y
family: aerodynamics
expr: yc + yt*cos(theta)
symbols: yc, yt, theta
```

\[
\frac{x_l}{c} = \xi + \frac{y_t}{c}\sin\theta
\qquad
\frac{y_l}{c} = \frac{y_c}{c} - \frac{y_t}{c}\cos\theta
\]

```formula
## naca4_lower_x
family: aerodynamics
expr: xi + yt*sin(theta)
symbols: xi, yt, theta
```

```formula
## naca4_lower_y
family: aerodynamics
expr: yc - yt*cos(theta)
symbols: yc, yt, theta
```

The leading-edge radius of the thickness form follows the \(a_0\sqrt{\xi}\) term in NASA TM X-3284, with \(a_0\) scaled from the 20-percent model:

\[
\frac{R_{\mathrm{le}}}{c} = \frac{1}{2}\left(0.2969\,\frac{t}{0.20}\right)^{2}
\]

```formula
## naca4_leading_edge_radius
family: aerodynamics
expr: 0.5*(0.2969*t/0.2)**2*c
symbols: t, c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(y_t\) | Half-thickness, measured normal to the mean line | m |
| \(y_c\) | Mean-line ordinate above the chord | m |
| \(t\) | Maximum thickness divided by chord | dimensionless |
| \(m\) | Maximum camber divided by chord | dimensionless |
| \(p\) | Chord fraction of maximum camber | dimensionless |
| \(\xi\) | Chord fraction from the leading edge | dimensionless |
| \(\theta\) | Mean-line slope angle | rad |
| \(x_u, y_u\) | Upper-surface station and ordinate | m |
| \(x_l, y_l\) | Lower-surface station and ordinate | m |
| \(R_{\mathrm{le}}\) | Leading-edge radius of the thickness form | m |
| \(c\) | Chord | m |

Assumptions: \(\xi\) is the chordwise station at which the thickness polynomial is evaluated. \(0 \le t < 1\), \(0 \le m < 1\), and \(0 < p < 1\) when \(m > 0\). A symmetric section has \(m = 0\) and a straight mean line. The trailing-edge half-thickness is finite because \(a_4 = -0.1015\). Script symbols `yt` and `yc` in the surface records are already divided by \(c\). `naca4_leading_edge_radius` returns \(R_{\mathrm{le}}\), not the ratio.

## Thin-section lift and moment of a NACA four-digit mean line

Munk’s thin-wing result: the two-dimensional lift-curve slope is \(2\pi\) per radian. The geometric angle that produces zero lift, and the moment at zero geometric angle, come from the mean-line slope. Map the chord by \(\xi = (1-\cos\theta)/2\). The Glauert station of maximum camber is

\[
\theta_p = 2\tan^{-1}\sqrt{\frac{p}{1-p}}
\]

```formula
## naca4_glauert_station
family: aerodynamics
expr: 2*atan((p/(1-p))**0.5)
symbols: p
```

Zero-lift angle from the Fourier integral of \(\mathrm{d}y_c/\mathrm{d}x\) on that map, written with the two-parabola slope:

\[
\alpha_{L0} = \frac{1}{\pi}\left[f_f L(\theta_p) + f_a\bigl(L(\pi)-L(\theta_p)\bigr)\right]
\]

with \(f_f = m/p^{2}\), \(f_a = m/(1-p)^{2}\), \(B = 2p-1\), \(s=\sqrt{p(1-p)}\), and \(L(\theta) = (B-1/2)\theta + (1-B)\sin\theta - (\sin\theta\cos\theta)/2\).

```formula
## naca4_zero_lift_angle
family: aerodynamics
expr: (1/pi)*((m/p**2)*((2*p-1-0.5)*theta_p + 2*(p*(1-p))**0.5*(1-(2*p-1)) + (2*p-1)*(p*(1-p))**0.5) + (m/(1-p)**2)*((2*p-1-0.5)*pi - ((2*p-1-0.5)*theta_p + 2*(p*(1-p))**0.5*(1-(2*p-1)) + (2*p-1)*(p*(1-p))**0.5)))
symbols: m, p, theta_p, pi
```

Section lift at a geometric angle of attack is then `section_lift_effective_angle` with slope \(2\pi\) and zero induced angle:

\[
c_l = 2\pi\,(\alpha - \alpha_{L0})
\]

```formula
## thin_airfoil_section_lift
family: aerodynamics
expr: 2*pi*(alpha - alpha_L0)
symbols: pi, alpha, alpha_L0
```

The first two Glauert cosine coefficients of the same slope are

\[
A_1 = \frac{2}{\pi}\left[f_f J(\theta_p) + f_a\bigl(\pi/2 - J(\theta_p)\bigr)\right]
\]

```formula
## naca4_glauert_A1
family: aerodynamics
expr: (2/pi)*((m/p**2)*((2*p-1)*(p*(1-p))**0.5 + theta_p/2) + (m/(1-p)**2)*(pi/2 - ((2*p-1)*(p*(1-p))**0.5 + theta_p/2)))
symbols: m, p, theta_p, pi
```

\[
A_2 = \frac{2}{\pi}K(\theta_p)\,(f_f - f_a)
\]

```formula
## naca4_glauert_A2
family: aerodynamics
expr: (2/pi)*(-2*(2*p-1)**2*(p*(1-p))**0.5 + 2*(p*(1-p))**0.5 - (16/3)*(p*(1-p))**1.5)*(m/p**2 - m/(1-p)**2)
symbols: m, p, pi
```

The quarter-chord moment coefficient is independent of angle of attack:

\[
c_{m,c/4} = \frac{\pi}{4}(A_2 - A_1)
\]

```formula
## naca4_quarter_chord_moment
family: aerodynamics
expr: (pi/4)*(A2 - A1)
symbols: pi, A2, A1
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\theta_p\) | Glauert angle at \(\xi = p\) | rad |
| \(\alpha_{L0}\) | Geometric angle of attack for zero section lift | rad |
| \(c_l\) | Section lift coefficient | dimensionless |
| \(\alpha\) | Geometric angle of attack of the chord | rad |
| \(A_1, A_2\) | Glauert cosine coefficients of mean-line slope | dimensionless |
| \(c_{m,c/4}\) | Section pitching-moment coefficient about the quarter chord | dimensionless |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: two-dimensional, inviscid, incompressible thin-section flow. Camber and angle of attack are small. Thickness does not enter \(\alpha_{L0}\), \(c_l\), or \(c_{m,c/4}\). Two-dimensional inviscid pressure drag is zero. Munk notes that a useful profile drag still requires an empirical friction estimate; that estimate is not this record. \(0 < p < 1\) and \(m \ge 0\). A symmetric mean line is \(m = 0\), so \(\alpha_{L0} = 0\) and \(c_{m,c/4} = 0\). Positive moment is pitch-up. Script `theta_p` is `naca4_glauert_station`. Script `s**1.5` in \(A_2\) is \(s^{3}\) with \(s=\sqrt{p(1-p)}\).

# Structures

Pure bending of a beam, spar, longeron, or boom follows NACA Report 82 and NACA TN 2754. Elastic Euler column buckling of a concentrically loaded prismatic strut follows the AFFDL Stress Analysis Manual with the effective-length form restated in NASA TM X-73305; NACA Report 82 states the pin-ended Euler load for high slenderness. Thin-shell motor-case relations are written out in NASA SP-8025, *Solid Rocket Motor Metal Cases* (April 1970). Shell buckling, fracture mechanics, and weight scaling in that monograph are cited to other documents and are not recorded here. In the shell records \(R\) is cylinder radius. The load ratio in the margin-of-safety definition is not called \(R\). In the beam and column records \(I\) is the second moment of area about the buckling or bending axis, not polar moment and not impulse.

## Pure bending stress

Elastic normal stress from a bending moment alone on a prismatic member. NACA Report 82 writes the extreme-fiber form

\[
\sigma = \frac{M c}{I}
\]

and the section-modulus form used for spars

\[
\sigma = \frac{M}{Z}
\]

```formula
## beam_bending_stress
family: beam
expr: M/Z
symbols: M, Z
```

```formula
## beam_bending_stress_inertia
family: beam
expr: M*c/I
symbols: M, c, I
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\sigma\) | Extreme-fiber bending stress (tension or compression) | Pa |
| \(M\) | Bending moment about the neutral axis | N·m |
| \(Z\) | Elastic section modulus | m³ |
| \(I\) | Second moment of area about the neutral axis | m⁴ |
| \(c\) | Distance from the neutral axis to the extreme fiber | m |

Assumptions: linear-elastic material, plane sections remain plane, the moment is about a principal neutral axis, the cross section is prismatic at the station, and there is no axial force in this record. Axial-plus-bending \(P/A + M/Z\) from Report 82 is a separate combination. Shear and torsion are omitted. \(\sigma\) is the magnitude of the extreme-fiber normal stress; sign convention (tension versus compression) is left to the user. Historical English units in the report are restated in SI here.

## Section modulus

Elastic section modulus of a cross section. NACA TN 2754 defines the wing-root section modulus as the second moment of area of the root section divided by the greatest distance from the neutral axis. With that \(Z\), Report 82’s \(M/Z\) matches \(Mc/I\).

\[
Z = \frac{I}{c}
\]

```formula
## section_modulus
family: beam
expr: I/c
symbols: I, c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(Z\) | Elastic section modulus | m³ |
| \(I\) | Second moment of area about the neutral axis | m⁴ |
| \(c\) | Distance from the neutral axis to the extreme fiber | m |

Assumptions: elastic (not plastic) section modulus. \(c > 0\). The TN 2754 wing-sizing charts that use this definition are not part of this record.

## Elastic Euler column buckling

Critical compressive load of a straight, concentrically loaded, prismatic long column that buckles while the material is still linear-elastic. NACA Report 82 writes the pin-ended form \(P=\pi^{2}EI/L^{2}\). NASA TM X-73305 writes the same load with an effective length \(L'\) that accounts for end fixity:

\[
P_{\mathrm{cr}} = \frac{\pi^{2} E I}{(L')^{2}}
\]

The AFFDL Stress Analysis Manual writes the equivalent stress forms

\[
\frac{P_{\mathrm{cr}}}{A} = \frac{C \pi^{2} E}{(L/\rho)^{2}} = \frac{\pi^{2} E}{(L'/\rho)^{2}}
\]

with radius of gyration \(\rho=\sqrt{I/A}\) and coefficient of constraint \(C=(L/L')^{2}\). The program end-fix factor is \(K=L'/L=1/\sqrt{C}\), so

\[
P_{\mathrm{cr}} = \frac{\pi^{2} E I}{(K L)^{2}},\qquad
L' = K L,\qquad
C = \frac{1}{K^{2}}.
\]

Idealized classical ends (AFFDL Table 2-1, with fixed–pinned taken as the usual \(C=2\) rather than the table’s \(2.05\)): pinned–pinned \(K=1\), fixed–fixed \(K=1/2\), fixed–pinned \(K=1/\sqrt{2}\), fixed–free \(K=2\).

```formula
## euler_critical_load
family: column
expr: pi**2*E*I/(K*L)**2
symbols: E, I, K, L, pi
```

```formula
## euler_critical_load_fixity
family: column
expr: C*pi**2*E*I/L**2
symbols: C, E, I, L, pi
```

```formula
## effective_column_length
family: column
expr: K*L
symbols: K, L
```

```formula
## end_fixity_coefficient
family: column
expr: 1/K**2
symbols: K
```

```formula
## radius_of_gyration
family: column
expr: (I/A)**0.5
symbols: I, A
```

```formula
## column_slenderness
family: column
expr: K*L/(I/A)**0.5
symbols: K, L, I, A
```

```formula
## euler_critical_stress
family: column
expr: pi**2*E/(K*L/(I/A)**0.5)**2
symbols: E, K, L, I, A, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{\mathrm{cr}}\) | Elastic Euler critical compressive load | N |
| \(E\) | Young’s modulus | Pa |
| \(I\) | Second moment of area about the buckling axis | m⁴ |
| \(L\) | Unsupported length between ends | m |
| \(L'\) | Effective length, distance between inflection points | m |
| \(K\) | End-fix factor, \(L'/L\) | dimensionless |
| \(C\) | Coefficient of constraint (end-fixity), \((L/L')^{2}\) | dimensionless |
| \(A\) | Cross-sectional area | m² |
| \(\rho\) | Radius of gyration, \(\sqrt{I/A}\) | m |
| \(K L/\rho\) | Effective slenderness ratio | dimensionless |
| \(\sigma_{\mathrm{cr}}\) | Average critical stress, \(P_{\mathrm{cr}}/A\) | Pa |

Assumptions: concentric axial compression, initially straight prismatic member, stable cross section (no local crippling), homogeneous isotropic linear-elastic material, and critical stress below the proportional limit (and below compressive yield when that stress is supplied). The Euler load alone does not replace a short-column or tangent-modulus curve. Eccentricity, initial crookedness, and inelastic Engesser–von Kármán / Johnson formulas are omitted. \(E,I,L,K,A>0\).

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

# Mass properties

Rigid, non-rotating assemblies of point masses or uniform parts with a stated CG follow NASA TM X-1754 and NACA TN 575. Positions are in one common body frame. Fuel slosh and time-varying CG are omitted. In these records \(I\) is a mass moment of inertia (kg·m²), not a second moment of area. Products of inertia use the \(P_{xy}=\int x y\,\mathrm{d}m\) convention of TM X-1754; the inertia tensor places \(-P_{xy}\) in the off-diagonal slots.

## Total mass

Sum of the part masses. For two parts the script is the two-term sum; the program sums every part.

\[
m = m_1 + m_2
\]

```formula
## total_mass
family: mass
expr: m1 + m2
symbols: m1, m2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(m\) | Total mass | kg |
| \(m_1, m_2\) | Part masses | kg |

Assumptions: rigid assembly. Masses are positive. The program accepts one or more parts and sums them all.

## Mass first moment

First mass moment of one part about a reference plane (or axis origin) along one body axis.

\[
M_x = m x
\]

```formula
## mass_first_moment
family: mass
expr: m*x
symbols: m, x
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M_x\) | First mass moment (script result) | kg·m |
| \(m\) | Part mass | kg |
| \(x\) | Part CG coordinate along that axis | m |

Assumptions: the coordinate is measured in the common body frame from the user origin.

## Center-of-mass coordinate

One body-axis coordinate of the system center of mass. NASA TM X-1754 and NACA TN 575 both divide the summed first moment by the total mass.

\[
\bar{x} = \frac{M_x}{m}
\]

```formula
## center_of_mass_coordinate
family: mass
expr: Mx/m
symbols: Mx, m
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\bar{x}\) | Center-of-mass coordinate on that axis | m |
| \(M_x\) | Summed first mass moment on that axis (script `Mx`) | kg·m |
| \(m\) | Total mass | kg |

Assumptions: \(m > 0\). The \(y\) and \(z\) coordinates use the same record with their first moments. Uniform gravity is not required; this is the mass centroid.

## Point-mass moment of inertia

Moment of inertia of a concentrated mass about a reference axis parallel to a body axis. NACA TN 575 writes \(w(y^{2}+z^{2})\) for the \(x\)-axis contribution; with mass in place of weight the SI form is

\[
I_{xx} = m(d_1^{2} + d_2^{2})
\]

```formula
## point_mass_moment
family: mass
expr: m*(d1**2 + d2**2)
symbols: m, d1, d2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(I_{xx}\) | Moment about the axis (script result) | kg·m² |
| \(m\) | Part mass | kg |
| \(d_1, d_2\) | The two coordinates perpendicular to that axis | m |

Assumptions: the mass is concentrated at the stated CG. For \(I_{xx}\) take \(d_1=y\) and \(d_2=z\); for \(I_{yy}\) take \(x\) and \(z\); for \(I_{zz}\) take \(x\) and \(y\). Coordinates are from the axis origin in use (user origin or system CG).

## Point-mass product of inertia

Product of inertia of a concentrated mass for a pair of body axes. NASA TM X-1754 adds \(m x y\) (and cyclic) when transferring to the system CG.

\[
P_{xy} = m\, d_1 d_2
\]

```formula
## point_mass_product
family: mass
expr: m*d1*d2
symbols: m, d1, d2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{xy}\) | Product of inertia (script result) | kg·m² |
| \(m\) | Part mass | kg |
| \(d_1, d_2\) | The two coordinates for that product pair | m |

Assumptions: concentrated mass. For \(P_{xy}\) take \(d_1=x\) and \(d_2=y\); likewise \(P_{xz}\) and \(P_{yz}\).

## Parallel-axis moment transfer

Moment of inertia about a parallel axis through a chosen origin from the moment about a parallel axis through the part CG. NASA TM X-1754 writes \(I_{xx}=I_{xx,\mathrm{cg}}+m(y^{2}+z^{2})\) with \(x,y,z\) measured from the system CG.

\[
I = I_{\mathrm{cg}} + m(d_1^{2} + d_2^{2})
\]

```formula
## parallel_axis_moment
family: mass
expr: Icg + m*(d1**2 + d2**2)
symbols: Icg, m, d1, d2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(I\) | Moment about the parallel target axis | kg·m² |
| \(I_{\mathrm{cg}}\) | Moment about the parallel axis through the part CG (script `Icg`) | kg·m² |
| \(m\) | Part mass | kg |
| \(d_1, d_2\) | Part-CG coordinates relative to the target origin, perpendicular to the axis | m |

Assumptions: the two axes are parallel. \(I_{\mathrm{cg}}\) is already resolved into axes parallel to the body frame. A point mass has \(I_{\mathrm{cg}}=0\).

## Parallel-axis product transfer

Product of inertia about a parallel pair of axes through a chosen origin from the product about the parallel pair through the part CG. NASA TM X-1754 writes \(P_{xy}=P_{xy,\mathrm{cg}}+m x y\).

\[
P = P_{\mathrm{cg}} + m\, d_1 d_2
\]

```formula
## parallel_axis_product
family: mass
expr: Pcg + m*d1*d2
symbols: Pcg, m, d1, d2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P\) | Product about the target origin | kg·m² |
| \(P_{\mathrm{cg}}\) | Product about the part CG (script `Pcg`) | kg·m² |
| \(m\) | Part mass | kg |
| \(d_1, d_2\) | Part-CG coordinates relative to the target origin for that product pair | m |

Assumptions: axes remain parallel to the body frame. A point mass has \(P_{\mathrm{cg}}=0\).

## Inertia shift from origin to CG

Moment of inertia about a parallel axis through the system CG from the same moment about a parallel axis through the user origin. NACA TN 575 writes \(I_y = I_{y'} - W(x_{\mathrm{cg}}^{2}+z_{\mathrm{cg}}^{2})\); with mass in place of weight,

\[
I_{\mathrm{cg}} = I_O - m(d_1^{2} + d_2^{2})
\]

```formula
## inertia_shift_to_cg
family: mass
expr: IO - m*(d1**2 + d2**2)
symbols: IO, m, d1, d2
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(I_{\mathrm{cg}}\) | Moment about the parallel CG axis | kg·m² |
| \(I_O\) | Moment about the parallel origin axis (script `IO`) | kg·m² |
| \(m\) | Total mass | kg |
| \(d_1, d_2\) | System-CG coordinates from the origin, perpendicular to the axis | m |

Assumptions: the origin and CG axes are parallel. The same shift applies to each diagonal moment. Off-diagonal products shift by subtracting \(m\,\bar{x}\bar{y}\) (and cyclic).

# Aerothermodynamics

Stagnation-point convective heating on an axisymmetric blunt nose follows Sutton and Graves, NASA TR R-376. The Stefan–Boltzmann constant is the NIST CODATA 2022 value. Radiative-equilibrium wall temperature for an insulated gray surface against a cold sink follows the NASA Goddard thermal-design short course. Freestream dynamic pressure is `freestream_dynamic_pressure` in Aerodynamics. Perfect-gas freestream enthalpy uses the 1976 dry-air gas constant when temperature is known. These records do not add a separate dissociation or ionization model beyond what is already folded into the Sutton–Graves air coefficient.

Nonlifting ballistic entry in an exponential atmosphere follows Allen and Eggers, NACA TN 4047 (Report 1381). Constant \(C_D\), gravity neglected relative to drag, and a straight path at the entry flight-path angle give closed forms for peak deceleration and its altitude. That motion analysis is a companion to stagnation heat flux, not a full trajectory or a heating integral.

## Stagnation-point convective heat flux (heat-transfer coefficient)

Convective heat flux at the stagnation point of a blunt axisymmetric body. Equation (33) of NASA TR R-376 defines the heat-transfer coefficient \(K\) by

\[
\dot{q} = K \sqrt{\frac{p_s}{R_n}}\,(h_s - h_w)
\]

with \(p_s\) in atmospheres (\(1\,\mathrm{atm} = 101325\,\mathrm{Pa}\)). Table II of that report gives \(K = 0.1113\,\mathrm{kg/(s\cdot m^{3/2}\cdot atm^{1/2})}\) for Earth air.

```formula
## stagnation_convective_heat_flux
family: aerotherm
expr: K*((ps/Rn)**0.5)*(hs - hw)
symbols: K, ps, Rn, hs, hw
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{q}\) | Stagnation-point convective heat flux | W/m² |
| \(K\) | Sutton–Graves heat-transfer coefficient | kg/(s·m^{3/2}·atm^{1/2}) |
| \(p_s\) | Stagnation pressure (script `ps`) | atm |
| \(R_n\) | Effective nose radius (script `Rn`) | m |
| \(h_s\) | Stagnation-edge specific enthalpy | J/kg |
| \(h_w\) | Wall specific enthalpy | J/kg |

Assumptions: laminar stagnation-point boundary layer on an axisymmetric blunt body; chemical equilibrium gas mixture as in TR R-376; \(p_s\) is in atmospheres. The program that uses freestream density and speed for \(p_s\) takes the Newtonian / strong-shock estimate \(p_s = \rho_\infty V_\infty^{2}/(101325\,\mathrm{Pa/atm})\). Perfect-gas wall and freestream enthalpies below do not model dissociation of molecules at very high speed beyond that estimate.

## Freestream kinetic enthalpy

Specific kinetic enthalpy of the freestream, used as the hypersonic cold-wall stagnation enthalpy when freestream thermal enthalpy is omitted:

\[
h_{\mathrm{kin}} = \frac{1}{2} V^{2}
\]

```formula
## freestream_kinetic_enthalpy
family: aerotherm
expr: 0.5*V**2
symbols: V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h_{\mathrm{kin}}\) | Freestream kinetic enthalpy | J/kg |
| \(V\) | Freestream speed | m/s |

Assumptions: adiabatic energy equation with freestream static enthalpy neglected relative to \(V^{2}/2\), or added separately as \(c_p T\). No dissociation.

## Wall enthalpy (perfect gas)

\[
h_w = c_p T_w
\]

```formula
## wall_enthalpy_perfect
family: aerotherm
expr: cp*Tw
symbols: cp, Tw
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(h_w\) | Wall specific enthalpy | J/kg |
| \(c_p\) | Specific heat at constant pressure (script `cp`) | J/(kg·K) |
| \(T_w\) | Wall temperature (script `Tw`) | K |

Assumptions: calorically perfect gas at the wall. For 1976 dry air, \(c_p = \gamma R^{*} /(M_0(\gamma-1))\) with \(\gamma = 1.4\). No wall catalysis model beyond the Sutton–Graves fully catalytic correlation already in \(K\).

## Stagnation-point convective heat flux (cold-wall velocity form)

Cold-wall engineering form used when freestream density and speed are the known state. With \(h_s - h_w = V^{2}/2\) and \(p_s = \rho V^{2}/(101325\,\mathrm{Pa/atm})\), `stagnation_convective_heat_flux` reduces to

\[
\dot{q} = k \sqrt{\frac{\rho}{R_n}}\, V^{3}, \qquad k = \frac{K}{2\sqrt{101325}}
\]

For Earth air, \(K = 0.1113\) gives \(k = 1.74826\times 10^{-4}\) in SI (\(\dot{q}\) in W/m², \(\rho\) in kg/m³, \(R_n\) in m, \(V\) in m/s).

```formula
## stagnation_convective_heat_flux_velocity
family: aerotherm
expr: k*((rho/Rn)**0.5)*V**3
symbols: k, rho, Rn, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{q}\) | Cold-wall stagnation convective heat flux | W/m² |
| \(k\) | Earth-air velocity-form coefficient | kg^{1/2}/m |
| \(\rho\) | Freestream density (script `rho`) | kg/m³ |
| \(R_n\) | Effective nose radius (script `Rn`) | m |
| \(V\) | Freestream speed | m/s |

Assumptions: cold wall (\(h_w \ll h_s\)); freestream thermal enthalpy neglected in \(h_s\); Newtonian \(p_s = \rho V^{2}\). Does not account for dissociation of molecules or other real-gas effects beyond the Sutton–Graves air \(K\). Not a radiative heating rate.

## Radiative-equilibrium wall temperature

For an insulated gray surface that reradiates the absorbed convective flux to a cold sink,

\[
T_w = \left(\frac{\dot{q}}{\varepsilon\,\sigma}\right)^{1/4}
\]

with the CODATA 2022 Stefan–Boltzmann constant \(\sigma = 5.670374419\times 10^{-8}\,\mathrm{W/(m^{2}\cdot K^{4})}\).

```formula
## radiative_equilibrium_wall_temperature
family: aerotherm
expr: (q/(eps*sigma))**0.25
symbols: q, eps, sigma
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(T_w\) | Radiative-equilibrium wall temperature | K |
| \(\dot{q}\) | Net heat flux into the surface (script `q`) | W/m² |
| \(\varepsilon\) | Hemispherical emissivity (script `eps`) | dimensionless |
| \(\sigma\) | Stefan–Boltzmann constant (script `sigma`) | W/(m²·K⁴) |

Assumptions: steady state, no conduction into the wall, no incident solar or shock-layer radiation, and sink temperature negligible compared with \(T_w\). \(0 < \varepsilon \le 1\).

## Ballistic coefficient

Mass over drag area. With SI mass this is

\[
B = \frac{m}{C_D A}
\]

Allen and Eggers write the same grouping as \(m/(C_D A)\) inside the exponential atmosphere solution (TN 4047). Weight-based ballistic coefficients \(W/(C_D A)\) are not this record.

```formula
## ballistic_coefficient
family: aerotherm
expr: m/(Cd*A)
symbols: m, Cd, A
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(B\) | Ballistic coefficient | kg/m² |
| \(m\) | Vehicle mass | kg |
| \(C_D\) | Drag coefficient (script `Cd`) | dimensionless |
| \(A\) | Reference area for drag | m² |

Assumptions: \(C_D\) and \(A\) use the same reference as the drag force \(D=C_D q A\). \(m>0\), \(C_D>0\), \(A>0\).

## Exponential atmosphere density

Isothermal / constant scale-height density used by Allen and Eggers,

\[
\rho = \rho_{\mathrm{ref}}\exp\left(-\frac{Z-Z_{\mathrm{ref}}}{H}\right)
\]

with density scale height \(H=1/\beta\) when their inverse scale height is \(\beta\).

```formula
## exponential_atmosphere_density
family: aerotherm
expr: rhoref*exp(-(Z - Zref)/H)
symbols: rhoref, Z, Zref, H
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\rho\) | Density at geometric altitude \(Z\) | kg/m³ |
| \(\rho_{\mathrm{ref}}\) | Reference density (script `rhoref`) | kg/m³ |
| \(Z\) | Geometric altitude | m |
| \(Z_{\mathrm{ref}}\) | Reference altitude for \(\rho_{\mathrm{ref}}\) (script `Zref`) | m |
| \(H\) | Density scale height | m |

Assumptions: constant \(H\). TN 4047 Earth fit uses \(\rho_{\mathrm{ref}}=0.0034\,\mathrm{slug/ft}^{3}\) at \(Z_{\mathrm{ref}}=0\) with \(H=22000\,\mathrm{ft}\) (\(\rho_{\mathrm{ref}}=1.752288\,\mathrm{kg/m}^{3}\), \(H=6705.6\,\mathrm{m}\) in SI). This is not the piecewise 1976 hydrostatic atmosphere.

## Atmosphere inverse scale height

\[
\beta = \frac{1}{H}
\]

```formula
## atmosphere_inverse_scale_height
family: aerotherm
expr: 1/H
symbols: H
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\beta\) | Inverse density scale height | 1/m |
| \(H\) | Density scale height | m |

Assumptions: \(H>0\). Allen–Eggers \(\beta\) in TN 4047 is this quantity, not the ballistic coefficient.

## Allen–Eggers peak deceleration

Peak drag deceleration for a nonlifting ballistic entry when that peak occurs above the surface (TN 4047 eqs. (15)–(17)). With scale height \(H=1/\beta\),

\[
a_{\max} = \frac{V_E^{2}\sin\theta_E}{2 e H}
\]

Independent of \(m\), \(C_D\), and \(A\). \(\theta_E\) is the entry flight-path angle below the local horizontal. \(e=\exp(1)\).

```formula
## allen_eggers_peak_deceleration
family: aerotherm
expr: Ve**2*sin(th)/(2*exp(1)*H)
symbols: Ve, th, H
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a_{\max}\) | Peak deceleration magnitude | m/s² |
| \(V_E\) | Entry speed (script `Ve`) | m/s |
| \(\theta_E\) | Entry flight-path angle below local horizontal (script `th`) | rad |
| \(H\) | Density scale height | m |

Assumptions: constant \(C_D\); exponential atmosphere; gravity neglected relative to drag; straight path at \(\theta_E\); peak altitude positive. \(0<\theta_E\le\pi/2\). Not a lifting entry and not a full trajectory integration.

## Allen–Eggers speed at peak deceleration

Speed at the altitude of peak deceleration when that altitude is positive (TN 4047 eq. (16)):

\[
V_1 = \frac{V_E}{\sqrt{e}} = V_E\exp(-1/2)
\]

```formula
## allen_eggers_speed_at_peak_deceleration
family: aerotherm
expr: Ve*exp(-0.5)
symbols: Ve
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_1\) | Speed at peak deceleration | m/s |
| \(V_E\) | Entry speed (script `Ve`) | m/s |

Assumptions: same as `allen_eggers_peak_deceleration` with positive peak altitude. About 60.65% of entry speed.

## Allen–Eggers density at peak deceleration

Density at the altitude of peak deceleration when that altitude is positive:

\[
\rho_1 = \frac{B\sin\theta_E}{H}
\]

with ballistic coefficient \(B=m/(C_D A)\).

```formula
## allen_eggers_density_at_peak_deceleration
family: aerotherm
expr: B*sin(th)/H
symbols: B, th, H
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\rho_1\) | Density at peak deceleration | kg/m³ |
| \(B\) | Ballistic coefficient \(m/(C_D A)\) | kg/m² |
| \(\theta_E\) | Entry flight-path angle (script `th`) | rad |
| \(H\) | Density scale height | m |

Assumptions: same straight-path Allen–Eggers model. Equivalent to \(\rho_1=\beta m\sin\theta_E/(C_D A)\).

## Allen–Eggers peak-deceleration altitude

Geometric altitude of peak deceleration when that altitude is above the reference surface (TN 4047 eq. (15), restated with \(H=1/\beta\) and \(B=m/(C_D A)\)):

\[
Z_1 = Z_{\mathrm{ref}} + H\ln\left(\frac{\rho_{\mathrm{ref}} H}{B\sin\theta_E}\right)
\]

```formula
## allen_eggers_peak_deceleration_altitude
family: aerotherm
expr: Zref + H*log(rhoref*H/(B*sin(th)))
symbols: Zref, H, rhoref, B, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(Z_1\) | Altitude of peak deceleration | m |
| \(Z_{\mathrm{ref}}\) | Reference altitude for \(\rho_{\mathrm{ref}}\) (script `Zref`) | m |
| \(H\) | Density scale height | m |
| \(\rho_{\mathrm{ref}}\) | Reference density (script `rhoref`) | kg/m³ |
| \(B\) | Ballistic coefficient | kg/m² |
| \(\theta_E\) | Entry flight-path angle (script `th`) | rad |

Assumptions: same as `allen_eggers_peak_deceleration`. Valid only when \(Z_1\) is above the impact surface (usually \(Z=0\)). Independent of entry speed. If \(Z_1\) is negative, the in-flight maximum is at the surface and the sea-level records below apply.

## Allen–Eggers surface speed (heavy vehicle)

When the formal peak altitude is below the surface, the maximum in-flight deceleration is at \(Z=Z_{\mathrm{imp}}\) (TN 4047 sea-level case). With \(Z_{\mathrm{imp}}=Z_{\mathrm{ref}}=0\),

\[
V_s = V_E\exp\left(-\frac{\rho_{\mathrm{ref}} H}{2 B\sin\theta_E}\right)
\]

```formula
## allen_eggers_surface_speed
family: aerotherm
expr: Ve*exp(-rhoref*H/(2*B*sin(th)))
symbols: Ve, rhoref, H, B, th
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_s\) | Speed at the surface (impact altitude) | m/s |
| \(V_E\) | Entry speed (script `Ve`) | m/s |
| \(\rho_{\mathrm{ref}}\) | Surface / reference density (script `rhoref`) | kg/m³ |
| \(H\) | Density scale height | m |
| \(B\) | Ballistic coefficient | kg/m² |
| \(\theta_E\) | Entry flight-path angle (script `th`) | rad |

Assumptions: \(Z_{\mathrm{ref}}=0\) and impact at sea level, as in TN 4047. For a nonzero reference altitude, evaluate density at the impact altitude with `exponential_atmosphere_density` and replace \(\rho_{\mathrm{ref}}\) by that density with the same \(H\).

## Allen–Eggers surface deceleration (heavy vehicle)

Deceleration magnitude at the surface for the heavy-vehicle case,

\[
a_s = \frac{\rho_{\mathrm{ref}}}{2 B}\, V_s^{2}
\]

```formula
## allen_eggers_surface_deceleration
family: aerotherm
expr: (rhoref/(2*B))*Vs**2
symbols: rhoref, B, Vs
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a_s\) | Surface deceleration magnitude | m/s² |
| \(\rho_{\mathrm{ref}}\) | Surface density (script `rhoref`) | kg/m³ |
| \(B\) | Ballistic coefficient | kg/m² |
| \(V_s\) | Speed at the surface (script `Vs`) | m/s |

Assumptions: drag deceleration \(a=(C_D\rho A/(2m))V^{2}=\rho V^{2}/(2B)\). Use with `allen_eggers_surface_speed` when the formal \(Z_1\) is below the surface.

# Spacecraft power

Flat-plate solar-array electrical power for preliminary sizing. Cell efficiency, cosine incidence, packing of cells on the substrate, and multiplicative beginning- and end-of-life degradation follow NASA SP-8074. The default 1 AU solar constant is the NASA GSFC / TSIS-1 value \(S = 1361.6\,\mathrm{W/m}^{2}\). Circular-orbit eclipse fraction under a cylindrical umbra is from Rickman (NASA JSC). Battery nameplate energy, depth of discharge, usable energy with discharge efficiency, required capacity for an eclipse load, recharge power, and sunlit array power for orbit energy balance follow NASA MSFC *Electrical Power Systems for Cubesats* (NTRS 20180007969). Cell electrochemistry, thermal runaway, and Peukert beyond a single efficiency factor are omitted.

## Flat-plate solar irradiance

Incident solar irradiance on a flat plate whose outward normal is at angle \(\theta\) from the Sun. NASA SP-8074 states that incident energy varies nearly as \(\cos\theta\), and array output is reduced by approximately the same factor (edge effects beyond about \(40^\circ\) are omitted here).

\[
G = S\cos\theta
\]

```formula
## flat_plate_solar_irradiance
family: power
expr: S*cos(theta)
symbols: S, theta
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(G\) | Incident irradiance on the plate | W/m² |
| \(S\) | Solar constant (irradiance at the orbit, normal to the Sun) | W/m² |
| \(\theta\) | Sun incidence angle from the plate normal (script `theta`) | rad |

Assumptions: flat plate, no albedo or Earth IR, \(\lvert\theta\rvert\le\pi/2\). For \(\lvert\theta\rvert>\pi/2\) the plate is dark and \(G=0\) in the program. Edge-effect departure from the cosine law is omitted.

## Ideal array power (packed cells)

Electrical power of an array of area \(A\) at normal incidence before inherent and life degradation. Cell efficiency is maximum power per unit cell area over incident sunlight power per unit area (SP-8074). Packing factor \(F_{\mathrm{p}}\) is the fraction of substrate area occupied by active cells after spacing.

\[
P_{0} = S A \eta F_{\mathrm{p}}
\]

```formula
## solar_array_ideal_power
family: power
expr: S*A*eta*Fp
symbols: S, A, eta, Fp
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{0}\) | Ideal packed-array power at normal incidence | W |
| \(S\) | Solar constant | W/m² |
| \(A\) | Array (substrate) area | m² |
| \(\eta\) | Cell conversion efficiency (script `eta`) | dimensionless |
| \(F_{\mathrm{p}}\) | Packing factor (script `Fp`) | dimensionless |

Assumptions: \(0 < \eta \le 1\), \(0 < F_{\mathrm{p}} \le 1\), \(A>0\), \(S>0\). Temperature and spectral corrections beyond \(\eta\) are omitted.

## Beginning-of-life array power

Instantaneous beginning-of-life (BOL) array power with inherent degradation \(I_{\mathrm{d}}\) (assembly, mismatch, coverslide, and related knockdowns at the start of life) and cosine incidence.

\[
P_{\mathrm{BOL}} = P_{0}\, I_{\mathrm{d}}\cos\theta = S A \eta F_{\mathrm{p}} I_{\mathrm{d}}\cos\theta
\]

```formula
## solar_array_bol_power
family: power
expr: S*A*eta*Fp*Id*cos(theta)
symbols: S, A, eta, Fp, Id, theta
```

When the user supplies a beginning-of-life specific power \(p_{\mathrm{sa}}\) (W/m²) that already equals \(S\eta F_{\mathrm{p}}\) at the stated solar constant and normal incidence,

\[
P_{\mathrm{BOL}} = p_{\mathrm{sa}} A\, I_{\mathrm{d}}\cos\theta
\]

```formula
## solar_array_bol_power_from_specific
family: power
expr: psa*A*Id*cos(theta)
symbols: psa, A, Id, theta
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{\mathrm{BOL}}\) | Instantaneous BOL array power | W |
| \(I_{\mathrm{d}}\) | Inherent degradation factor (script `Id`) | dimensionless |
| \(p_{\mathrm{sa}}\) | BOL specific power before inherent degradation (script `psa`) | W/m² |
| \(\theta\) | Sun incidence angle from the plate normal | rad |

Assumptions: \(0 < I_{\mathrm{d}} \le 1\). Same cosine limits as `flat_plate_solar_irradiance`. No temperature model beyond what is folded into \(\eta\) or \(p_{\mathrm{sa}}\).

## Life degradation factor

Remaining power fraction after \(L\) years at a constant fractional degradation rate \(d\) per year (compound).

\[
L_{\mathrm{d}} = (1 - d)^{L}
\]

```formula
## solar_array_life_degradation
family: power
expr: (1 - d)**L
symbols: d, L
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L_{\mathrm{d}}\) | Life degradation (remaining fraction) at end of life | dimensionless |
| \(d\) | Fractional degradation per year | 1/year |
| \(L\) | Mission life | year |

Assumptions: \(0 \le d < 1\), \(L \ge 0\). Radiation is represented only by this constant annual rate, not by an equivalent-fluence calculation.

## End-of-life array power

\[
P_{\mathrm{EOL}} = P_{\mathrm{BOL}}\, L_{\mathrm{d}}
\]

```formula
## solar_array_eol_power
family: power
expr: Pbol*Ld
symbols: Pbol, Ld
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{\mathrm{EOL}}\) | Instantaneous end-of-life array power | W |
| \(P_{\mathrm{BOL}}\) | Instantaneous BOL array power (script `Pbol`) | W |
| \(L_{\mathrm{d}}\) | Life degradation factor (script `Ld`) | dimensionless |

Assumptions: life degradation multiplies the instantaneous BOL power at the same incidence angle.

## Orbit-average array power

Orbit-average electrical power when the array produces constant power \(P\) in sunlight and zero in eclipse (sun-tracking flat plate at fixed incidence during the sunlit arc).

\[
P_{\mathrm{avg}} = P\,(1 - f_{\mathrm{e}})
\]

```formula
## solar_array_orbit_average_power
family: power
expr: P*(1 - fe)
symbols: P, fe
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{\mathrm{avg}}\) | Orbit-average array power | W |
| \(P\) | Instantaneous sunlit array power (BOL or EOL) | W |
| \(f_{\mathrm{e}}\) | Eclipse fraction of the orbit (script `fe`) | dimensionless |

Assumptions: power is zero in umbra and constant in sunlight. Penumbra is omitted. \(0 \le f_{\mathrm{e}} < 1\).

## Circular-orbit eclipse fraction

Fraction of a circular orbit spent in a cylindrical planetary umbra. Rickman: terminator half-angle \(\phi\) from

\[
\cos\phi = \frac{\sqrt{1-(r_{e}/r)^{2}}}{\cos\beta}, \qquad f_{\mathrm{e}} = \frac{\phi}{\pi}
\]

with \(r = r_{e}+h\). No eclipse when \(\lvert\beta\rvert \ge \arcsin(r_{e}/r)\).

```formula
## circular_orbit_eclipse_fraction
family: power
expr: acos(((1 - (re/r)**2)**0.5)/cos(beta))/pi
symbols: re, r, beta, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(f_{\mathrm{e}}\) | Eclipse time fraction | dimensionless |
| \(r_{e}\) | Planet radius (script `re`) | m |
| \(r\) | Circular-orbit radius from the planet center (script `r`) | m |
| \(\beta\) | Beta angle (Sun to orbit plane) (script `beta`) | rad |

Assumptions: circular orbit, spherical planet, cylindrical umbra (no penumbra), \(\lvert\beta\rvert < \arcsin(r_{e}/r)\), and \(r > r_{e}\). The expression is undefined outside that beta range; the program then sets \(f_{\mathrm{e}}=0\).

## Battery nameplate energy from ampere-hours

Nameplate stored energy of a battery rated at ampere-hour capacity \(C_{\mathrm{Ah}}\) on a bus (or average discharge) voltage \(V\). NASA MSFC Electrical Power Systems for Cubesats treats capacity in ampere-hours and energy in watt-hours; the SI form multiplies by \(3600\,\mathrm{s/h}\).

\[
E = 3600\, C_{\mathrm{Ah}} V
\]

```formula
## battery_energy_from_capacity_ah
family: power
expr: 3600*C_Ah*V
symbols: C_Ah, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E\) | Nameplate battery energy | J |
| \(C_{\mathrm{Ah}}\) | Nameplate ampere-hour capacity (script `C_Ah`) | A·h |
| \(V\) | Bus or average discharge voltage | V |

Assumptions: \(C_{\mathrm{Ah}}>0\), \(V>0\). One watt-hour is \(3600\,\mathrm{J}\). No Peukert rate correction beyond efficiencies supplied elsewhere.

## Battery depth of discharge

Fraction of nameplate capacity removed during a discharge. MSFC: ampere-hours removed over nameplate ampere-hours. With energy, the same ratio is

\[
\mathrm{DOD} = \frac{E_{\mathrm{removed}}}{E}
\]

```formula
## battery_depth_of_discharge
family: power
expr: E_removed/E
symbols: E_removed, E
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{DOD}\) | Depth of discharge (script `DOD`) | dimensionless |
| \(E_{\mathrm{removed}}\) | Chemical energy removed from the nameplate store (script `E_removed`) | J |
| \(E\) | Nameplate battery energy | J |

Assumptions: \(E>0\), \(0\le E_{\mathrm{removed}}\le E\). Cycle-life limits that choose a design \(\mathrm{DOD}\) are not this definition.

## Battery usable energy at the load

Energy that can be delivered to the load when nameplate energy \(E\) is used only down to a design depth of discharge \(\mathrm{DOD}\) and the discharge path efficiency is \(\eta_d\).

\[
E_{\mathrm{u}} = E\,\mathrm{DOD}\,\eta_d
\]

```formula
## battery_usable_energy
family: power
expr: E*DOD*eta_d
symbols: E, DOD, eta_d
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E_{\mathrm{u}}\) | Usable energy at the load | J |
| \(E\) | Nameplate battery energy | J |
| \(\mathrm{DOD}\) | Allowed depth of discharge | dimensionless |
| \(\eta_d\) | Discharge efficiency (script `eta_d`) | dimensionless |

Assumptions: \(0<\mathrm{DOD}\le 1\), \(0<\eta_d\le 1\). No cell electrochemistry or thermal-runaway model. Peukert effects enter only through the single factor \(\eta_d\).

## Time at continuous load

Duration a constant load \(P\) can be supplied from usable energy \(E_{\mathrm{u}}\).

\[
t = \frac{E_{\mathrm{u}}}{P}
\]

```formula
## battery_time_at_continuous_load
family: power
expr: Eu/P
symbols: Eu, P
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t\) | Time at continuous load | s |
| \(E_{\mathrm{u}}\) | Usable energy at the load (script `Eu`) | J |
| \(P\) | Continuous load power | W |

Assumptions: \(P>0\), \(E_{\mathrm{u}}\ge 0\).

## Battery discharge energy for a load interval

Chemical energy that must be removed from the nameplate store to deliver constant power \(P\) to the load for duration \(t_e\) through discharge efficiency \(\eta_d\). MSFC stored-energy form with the separate ampere-hour battery efficiency of that course folded into the user-supplied \(\eta_d\) (and \(\eta_c\) on charge).

\[
E_s = \frac{P\, t_e}{\eta_d}
\]

```formula
## battery_discharge_energy
family: power
expr: P*te/eta_d
symbols: P, te, eta_d
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E_s\) | Chemical energy removed from the store | J |
| \(P\) | Load power during the interval | W |
| \(t_e\) | Interval duration (script `te`) | s |
| \(\eta_d\) | Discharge efficiency | dimensionless |

Assumptions: \(P>0\), \(t_e>0\), \(0<\eta_d\le 1\).

## Required nameplate battery energy

Nameplate energy required so that a discharge of energy \(E_s\) does not exceed the design depth of discharge.

\[
E_{\mathrm{req}} = \frac{E_s}{\mathrm{DOD}} = \frac{P\, t_e}{\eta_d\,\mathrm{DOD}}
\]

```formula
## battery_required_nameplate_energy
family: power
expr: P*te/(eta_d*DOD)
symbols: P, te, eta_d, DOD
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E_{\mathrm{req}}\) | Required nameplate energy | J |
| \(\mathrm{DOD}\) | Allowed depth of discharge | dimensionless |

Assumptions: same as `battery_discharge_energy`, and \(0<\mathrm{DOD}\le 1\).

## Required ampere-hour capacity

\[
C_{\mathrm{Ah,req}} = \frac{E_{\mathrm{req}}}{3600\, V}
\]

```formula
## battery_required_capacity_ah
family: power
expr: Ereq/(3600*V)
symbols: Ereq, V
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C_{\mathrm{Ah,req}}\) | Required nameplate ampere-hour capacity | A·h |
| \(E_{\mathrm{req}}\) | Required nameplate energy (script `Ereq`) | J |
| \(V\) | Bus or average discharge voltage | V |

Assumptions: \(V>0\), \(E_{\mathrm{req}}>0\).

## Battery charge energy from the array

Array-side energy that must be delivered into the charger to restore chemical energy \(E_s\) at charge efficiency \(\eta_c\).

\[
E_c = \frac{E_s}{\eta_c}
\]

```formula
## battery_charge_energy
family: power
expr: Es/eta_c
symbols: Es, eta_c
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E_c\) | Energy drawn from the array for recharge | J |
| \(E_s\) | Chemical energy to restore (script `Es`) | J |
| \(\eta_c\) | Charge (charger) efficiency (script `eta_c`) | dimensionless |

Assumptions: \(0<\eta_c\le 1\), \(E_s\ge 0\).

## Battery recharge power during sunlight

Average power that must be available above the load during the sunlit interval \(t_d\) to restore \(E_c\).

\[
P_R = \frac{E_c}{t_d} = \frac{P\, t_e}{\eta_c\eta_d\, t_d}
\]

```formula
## battery_recharge_power
family: power
expr: P*te/(eta_c*eta_d*td)
symbols: P, te, eta_c, eta_d, td
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_R\) | Average recharge power during sunlight | W |
| \(t_d\) | Sunlit duration (script `td`) | s |

Assumptions: \(t_d>0\). Same efficiency limits as above.

## Orbit-average array power for energy balance

Sunlit array power that closes the energy balance for a constant load \(P\) over one orbit of eclipse duration \(t_e\) and sunlight duration \(t_d\), with charge and discharge efficiencies. MSFC top-level form without additional distribution knockdowns; those knockdowns are omitted here and must be folded into \(P\) or the efficiencies if needed.

\[
P_{\mathrm{sa}} = P\left(1+\frac{t_e}{\eta_c\eta_d\, t_d}\right)
\]

```formula
## battery_orbit_source_power
family: power
expr: P*(1 + te/(eta_c*eta_d*td))
symbols: P, te, eta_c, eta_d, td
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_{\mathrm{sa}}\) | Required constant sunlit array power | W |
| \(P\) | Constant spacecraft load | W |

Assumptions: constant load in sun and eclipse, zero array power in eclipse, and surplus sunlit power goes to charging. If the sunlit array is below the load, the battery supplies that difference at \(\eta_d\). Distribution and converter efficiencies outside \(\eta_c\) and \(\eta_d\) are omitted. Orbit-average array power from `solar_array_orbit_average_power` is \(P_{\mathrm{sa}}(1-f_{\mathrm{e}})\) with \(f_{\mathrm{e}}=t_e/(t_e+t_d)\).

# Space communications

Vacuum free-space radio link budget. Wavelength and frequency use the NIST CODATA 2022 speed of light \(c = 299792458\,\mathrm{m/s}\). Boltzmann’s constant is the CODATA 2022 value \(k = 1.380649\times 10^{-23}\,\mathrm{J/K}\). Free-space path loss and Friis received power follow Jamnejad. Circular-aperture gain with aperture efficiency follows Dabul, NASA TN D-3405. Thermal noise \(P_n=kTB\) is the same note; carrier-to-noise is Kalil’s \(\mathrm{CNR}=P_r/(kTB)\). \(E_b/N_0=(C/N_0)/R_b\) and margin against a required \(E_b/N_0\) follow Kerczewski, NASA TM 89898. Atmosphere, rain, polarization mismatch, pointing loss, and modulation details beyond a supplied \(E_b/N_0\) requirement are omitted.

## Wavelength from frequency

\[
\lambda = \frac{c}{f}
\]

```formula
## wavelength_from_frequency
family: comms
expr: c/f
symbols: c, f
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\lambda\) | Wavelength (script `lam` in related records) | m |
| \(c\) | Speed of light in vacuum | m/s |
| \(f\) | Carrier frequency | Hz |

Assumptions: \(f>0\). Use \(c=299792458\,\mathrm{m/s}\) unless the user gives another value.

## Frequency from wavelength

\[
f = \frac{c}{\lambda}
\]

```formula
## frequency_from_wavelength
family: comms
expr: c/lam
symbols: c, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(f\) | Carrier frequency | Hz |
| \(c\) | Speed of light in vacuum | m/s |
| \(\lambda\) | Wavelength (script `lam`) | m |

Assumptions: \(\lambda>0\).

## Free-space path loss

Multiplying free-space (space) loss between isotropic antennas at range \(R\):

\[
L_{\mathrm{fs}} = \left(\frac{4\pi R}{\lambda}\right)^{2}
\]

```formula
## free_space_path_loss
family: comms
expr: (4*pi*R/lam)**2
symbols: pi, R, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L_{\mathrm{fs}}\) | Free-space path loss (power ratio \(>1\)) | dimensionless |
| \(R\) | Slant range | m |
| \(\lambda\) | Wavelength (script `lam`) | m |
| \(\pi\) | Circle constant | dimensionless |

Assumptions: vacuum free space; far-field plane-wave Friis geometry; \(R>0\), \(\lambda>0\). No atmosphere or rain.

## Free-space path loss in decibels

\[
L_{\mathrm{fs,dB}} = 10\log_{10} L_{\mathrm{fs}} = 20\log_{10}\!\left(\frac{4\pi R}{\lambda}\right)
\]

```formula
## free_space_path_loss_db
family: comms
expr: 20*log(4*pi*R/lam)/log(10)
symbols: pi, R, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(L_{\mathrm{fs,dB}}\) | Free-space path loss | dB |
| \(R\) | Slant range | m |
| \(\lambda\) | Wavelength (script `lam`) | m |

Assumptions: same as `free_space_path_loss`. Script `log` is the natural logarithm.

## Antenna gain from effective aperture

\[
G = \frac{4\pi A_e}{\lambda^{2}}
\]

```formula
## antenna_gain_from_effective_aperture
family: comms
expr: 4*pi*Ae/(lam**2)
symbols: pi, Ae, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(G\) | Antenna power gain relative to isotropic | dimensionless |
| \(A_e\) | Effective aperture area (script `Ae`) | m² |
| \(\lambda\) | Wavelength (script `lam`) | m |

Assumptions: \(A_e>0\), \(\lambda>0\). Perfect polarization match when used in Friis.

## Circular-aperture antenna gain

Ideal uniform illumination gives \(G=(\pi D/\lambda)^{2}\). With aperture efficiency \(\eta\),

\[
G = \eta\left(\frac{\pi D}{\lambda}\right)^{2}
\]

```formula
## antenna_gain_circular_aperture
family: comms
expr: eta*(pi*D/lam)**2
symbols: eta, pi, D, lam
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(G\) | Antenna power gain relative to isotropic | dimensionless |
| \(\eta\) | Aperture efficiency (script `eta`) | dimensionless |
| \(D\) | Antenna diameter | m |
| \(\lambda\) | Wavelength (script `lam`) | m |

Assumptions: circular projected aperture; \(0 < \eta \le 1\); \(D>0\); \(\lambda>0\). Equivalent to `antenna_gain_from_effective_aperture` with \(A_e=\eta\pi D^{2}/4\).

## Effective isotropic radiated power

\[
\mathrm{EIRP} = P_t G_t
\]

```formula
## eirp
family: comms
expr: Pt*Gt
symbols: Pt, Gt
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mathrm{EIRP}\) | Effective isotropic radiated power | W |
| \(P_t\) | Transmitter power into the antenna (script `Pt`) | W |
| \(G_t\) | Transmit antenna gain (script `Gt`) | dimensionless |

Assumptions: \(P_t>0\), \(G_t>0\). No transmitter line loss beyond what is already folded into \(P_t\) or \(G_t\).

## Friis received power

\[
P_r = \frac{P_t G_t G_r}{L_{\mathrm{fs}}} = P_t G_t G_r\left(\frac{\lambda}{4\pi R}\right)^{2}
\]

```formula
## friis_received_power
family: comms
expr: Pt*Gt*Gr*(lam/(4*pi*R))**2
symbols: Pt, Gt, Gr, lam, pi, R
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_r\) | Received power at the antenna terminals | W |
| \(P_t\) | Transmit power (script `Pt`) | W |
| \(G_t\) | Transmit antenna gain (script `Gt`) | dimensionless |
| \(G_r\) | Receive antenna gain (script `Gr`) | dimensionless |
| \(\lambda\) | Wavelength (script `lam`) | m |
| \(R\) | Slant range | m |

Assumptions: vacuum free space; matched polarization; no atmosphere, rain, pointing, or circuit loss beyond the stated gains and power. \(P_t,G_t,G_r,R,\lambda>0\).

## Thermal noise power

\[
P_n = k T_s B
\]

```formula
## thermal_noise_power
family: comms
expr: k*Ts*B
symbols: k, Ts, B
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(P_n\) | Noise power in bandwidth \(B\) | W |
| \(k\) | Boltzmann constant | J/K |
| \(T_s\) | System noise temperature (script `Ts`) | K |
| \(B\) | Noise bandwidth | Hz |

Assumptions: \(T_s>0\), \(B>0\). Use \(k=1.380649\times 10^{-23}\,\mathrm{J/K}\) unless the user gives another value. \(T_s\) is the equivalent system temperature referred to the receiver input.

## Noise spectral density

\[
N_0 = k T_s
\]

```formula
## noise_spectral_density
family: comms
expr: k*Ts
symbols: k, Ts
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(N_0\) | One-sided noise power spectral density (script `N0`) | W/Hz |
| \(k\) | Boltzmann constant | J/K |
| \(T_s\) | System noise temperature (script `Ts`) | K |

Assumptions: \(T_s>0\).

## Carrier-to-noise density

\[
\frac{C}{N_0} = \frac{P_r}{k T_s}
\]

```formula
## carrier_to_noise_density
family: comms
expr: Pr/(k*Ts)
symbols: Pr, k, Ts
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C/N_0\) | Carrier-to-noise density ratio | 1/Hz |
| \(P_r\) | Received carrier power (script `Pr`) | W |
| \(k\) | Boltzmann constant | J/K |
| \(T_s\) | System noise temperature (script `Ts`) | K |

Assumptions: \(P_r>0\), \(T_s>0\). Carrier power equals Friis received power when no other receive losses are stated.

## Carrier-to-noise ratio

\[
\frac{C}{N} = \frac{P_r}{k T_s B}
\]

```formula
## carrier_to_noise_ratio
family: comms
expr: Pr/(k*Ts*B)
symbols: Pr, k, Ts, B
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(C/N\) | Carrier-to-noise power ratio | dimensionless |
| \(P_r\) | Received carrier power (script `Pr`) | W |
| \(k\) | Boltzmann constant | J/K |
| \(T_s\) | System noise temperature (script `Ts`) | K |
| \(B\) | Noise bandwidth | Hz |

Assumptions: \(B>0\). Equals Kalil’s \(\mathrm{CNR}=P_r/(kTB)\).

## Energy per bit to noise density

\[
\frac{E_b}{N_0} = \frac{C/N_0}{R_b}
\]

```formula
## eb_n0_from_cn0
family: comms
expr: CN0/Rb
symbols: CN0, Rb
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(E_b/N_0\) | Energy per bit over noise density | dimensionless |
| \(C/N_0\) | Carrier-to-noise density (script `CN0`) | 1/Hz |
| \(R_b\) | Information bit rate (script `Rb`) | bit/s |

Assumptions: \(R_b>0\). Equivalent to \(E_b/N_0=P_r/(k T_s R_b)\) when \(C/N_0=P_r/(k T_s)\). No coding or modulation model beyond the user’s bit rate and required \(E_b/N_0\).

## Link margin on \(E_b/N_0\)

Ratio of achieved \(E_b/N_0\) to a required value:

\[
M = \frac{(E_b/N_0)}{(E_b/N_0)_{\mathrm{req}}}
\]

```formula
## link_margin_eb_n0
family: comms
expr: EbN0/EbN0req
symbols: EbN0, EbN0req
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M\) | Link margin (power ratio) | dimensionless |
| \(E_b/N_0\) | Achieved ratio (script `EbN0`) | dimensionless |
| \((E_b/N_0)_{\mathrm{req}}\) | Required ratio (script `EbN0req`) | dimensionless |

Assumptions: \((E_b/N_0)_{\mathrm{req}}>0\). Margin in decibels is \(10\log_{10} M\). The requirement is supplied by the user; modulation BER curves are not computed here.

# Dynamics and control

Linear, constant-coefficient, single-input second-order response follows NASA/TM-2016-218227 (Casiano), NASA TM X-53036 (Garner), NASA/TM-2010-216897 (Connolly and Kopasakis), and the NASA Glenn loop-shaping note NTRS 20070034948. The plant is the unity-gain form

\[
G(s)=\frac{\omega_n^{2}}{s^{2}+2\zeta\omega_n s+\omega_n^{2}}
\]

or the mechanical SDOF \(m\ddot{x}+c\dot{x}+kx=F\). In this category \(k\) is stiffness, not the rocket ratio of specific heats. Rise time from 10% to 90% of the final value is read from the unit-step solution in the program and is not a separate closed-form record here.

## Natural frequency from mass and stiffness

Undamped natural frequency of a single-degree-of-freedom spring–mass plant. Matching Casiano’s normalized oscillator to \(m\ddot{x}+c\dot{x}+kx=F\) gives

\[
\omega_n = \sqrt{\frac{k}{m}}
\]

```formula
## natural_frequency_mass_stiffness
family: control
expr: (k/m)**0.5
symbols: k, m
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\omega_n\) | Undamped natural frequency | rad/s |
| \(k\) | Stiffness | N/m |
| \(m\) | Mass | kg |

Assumptions: linear spring, constant mass, no Coulomb friction. \(m>0\), \(k>0\).

## Damping ratio from mass, stiffness, and damping

Viscous damping ratio of that same SDOF plant:

\[
\zeta = \frac{c}{2\sqrt{k m}}
\]

```formula
## damping_ratio_mass_stiffness
family: control
expr: c/(2*(k*m)**0.5)
symbols: c, k, m
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\zeta\) | Damping ratio | dimensionless |
| \(c\) | Viscous damping coefficient | N·s/m |
| \(k\) | Stiffness | N/m |
| \(m\) | Mass | kg |

Assumptions: linear viscous damper in parallel with the spring. Critical damping is \(c_c=2\sqrt{km}\), so \(\zeta=c/c_c\). The case is underdamped when \(0\le\zeta<1\), critically damped when \(\zeta=1\), and overdamped when \(\zeta>1\). \(m>0\), \(k>0\), \(c\ge 0\).

## Damped natural frequency

Oscillation frequency of the underdamped free or step response (Casiano equation (7); Garner’s \(\omega_d\)):

\[
\omega_d = \omega_n\sqrt{1-\zeta^{2}}
\]

```formula
## damped_natural_frequency
family: control
expr: wn*(1 - zeta**2)**0.5
symbols: wn, zeta
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\omega_d\) | Damped natural frequency | rad/s |
| \(\omega_n\) | Undamped natural frequency (script `wn`) | rad/s |
| \(\zeta\) | Damping ratio (script `zeta`) | dimensionless |

Assumptions: \(0\le\zeta<1\) and \(\omega_n>0\). Not used when \(\zeta\ge 1\).

## Second-order percent overshoot

Fractional peak overshoot of the underdamped unit-step response (Garner; Connolly and Kopasakis). Percent overshoot is 100 times this value:

\[
M_p = \exp\left(-\frac{\pi\zeta}{\sqrt{1-\zeta^{2}}}\right)
\]

```formula
## second_order_percent_overshoot
family: control
expr: exp(-pi*zeta/(1 - zeta**2)**0.5)
symbols: zeta, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(M_p\) | Fractional overshoot \((y_{\max}-1)/1\) | dimensionless |
| \(\zeta\) | Damping ratio (script `zeta`) | dimensionless |
| \(\pi\) | Circle constant (script `pi`) | dimensionless |

Assumptions: underdamped unity-gain second-order plant, unit step, zero initial conditions. \(0\le\zeta<1\). Overshoot is zero when \(\zeta\ge 1\).

## Second-order peak time

Time of the first peak of the underdamped unit-step response. Garner states that the peak occurs when \(\omega_d t_p=\pi\):

\[
t_p = \frac{\pi}{\omega_n\sqrt{1-\zeta^{2}}}
\]

```formula
## second_order_peak_time
family: control
expr: pi/(wn*(1 - zeta**2)**0.5)
symbols: wn, zeta, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t_p\) | Peak time | s |
| \(\omega_n\) | Undamped natural frequency (script `wn`) | rad/s |
| \(\zeta\) | Damping ratio (script `zeta`) | dimensionless |
| \(\pi\) | Circle constant (script `pi`) | dimensionless |

Assumptions: underdamped unity-gain second-order plant, unit step. \(0\le\zeta<1\), \(\omega_n>0\). Not used when \(\zeta\ge 1\).

## Second-order settling time

Envelope settling time to a fractional band \(\delta\) about the final value (Garner’s \(t_s=k/(\zeta\omega_n)\) with \(k=-\ln\delta\); Connolly’s \(4.6/\sigma\) is the \(\delta=0.01\) case; the Glenn loop-shaping note’s four time constants is the \(\delta=0.02\) case):

\[
t_s = \frac{-\ln\delta}{\zeta\omega_n}
\]

```formula
## second_order_settling_time
family: control
expr: -log(delta)/(zeta*wn)
symbols: delta, zeta, wn
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t_s\) | Settling time | s |
| \(\delta\) | Fractional settling band (script `delta`) | dimensionless |
| \(\zeta\) | Damping ratio (script `zeta`) | dimensionless |
| \(\omega_n\) | Undamped natural frequency (script `wn`) | rad/s |

Assumptions: underdamped or lightly damped envelope \(e^{-\zeta\omega_n t}\). Default band is 2% so \(\delta=0.02\). A 5% band uses \(\delta=0.05\). Requires \(\zeta>0\), \(\omega_n>0\), and \(0<\delta<1\). This is an envelope estimate; the program may also report the first time the analytical step response stays inside the band.
