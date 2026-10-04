# Identities

Named numeric checks for the script records in `../formulas.md`.
`check_formulas.py` evaluates each formula `expr` with the inputs below.
A formula is written to `check.md` when every identity under it passes.
A definition is exempt from that requirement and is still written to `check.md`.
Any other formula with no identity stays unchecked and is omitted from `check.md`.

The expected number is the physical value of the recorded quantity.
`inputs` must set every symbol listed for the formula.
Name an integration variable with `vary` and do not assign it an input.
Values may be numbers or numeric expressions such as `7/5` or `2/2.4`.
Inside those values, `pi` and `e` are the math constants. They are not implied symbols of a formula.
`log` in a formula is the natural logarithm.

A check passes when `abs(actual - expected) <= tol + rel * abs(expected)`.
If both `tol` and `rel` are omitted, each is `1e-9`.
If only one is set, the other is `0`.

`partial(...)` and an indefinite `integral(F, t)` are not numbers.
A definite `integral(lower, upper, integrand)` is integrated exactly.

Add one or more identities under a formula id:

```
- name: gamma_7_over_5
  inputs:
    g: 7/5
  expected: 5/6
  tol: 1e-12
  rel: 0
```

Then run `python check_formulas.py`.

## Compressible flow

#### thermo

### perfect_gas

<!-- family: thermo; symbols: rho, R, T; expr: rho*R*T; numeric: yes -->

- name: ideal_gas_law
  inputs:
    rho: 5/4
    R: 287
    T: 280
  expected: 100450

### cp_definition

<!-- family: thermo; symbols: h, T; expr: partial(h, T); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is the unevaluated derivative of enthalpy with respect to temperature. -->

### cv_definition

<!-- family: thermo; symbols: u, T; expr: partial(u, T); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is the unevaluated derivative of internal energy with respect to temperature. -->

### gamma_definition

<!-- family: thermo; symbols: cp, cv; expr: cp/cv; numeric: yes -->

- name: diatomic_ratio
  inputs:
    cp: 2009/2
    cv: 1435/2
  expected: 7/5

### cp_minus_cv

<!-- family: thermo; symbols: cp, cv; expr: cp - cv; numeric: yes -->

- name: perfect_gas_difference
  inputs:
    cp: 2009/2
    cv: 1435/2
  expected: 287

### cp_from_gamma

<!-- family: thermo; symbols: g, R; expr: g*R/(g - 1); numeric: yes -->

- name: air
  inputs:
    g: 7/5
    R: 287
  expected: 2009/2

### cv_from_gamma

<!-- family: thermo; symbols: g, R; expr: R/(g - 1); numeric: yes -->

- name: air
  inputs:
    g: 7/5
    R: 287
  expected: 1435/2

### enthalpy_definition

<!-- family: thermo; symbols: u, p, v; expr: u + p*v; numeric: yes -->

- name: flow_work
  inputs:
    u: 215250
    p: 86100
    v: 1
  expected: 301350

### enthalpy_perfect

<!-- family: thermo; symbols: cp, T; expr: cp*T; numeric: yes -->

- name: calorically_perfect
  inputs:
    cp: 2009/2
    T: 300
  expected: 301350

### internal_energy_perfect

<!-- family: thermo; symbols: cv, T; expr: cv*T; numeric: yes -->

- name: calorically_perfect
  inputs:
    cv: 1435/2
    T: 300
  expected: 215250

### speed_of_sound

<!-- family: thermo; symbols: g, R, T; expr: (g*R*T)**0.5; numeric: yes -->

- name: exact_square
  inputs:
    g: 7/5
    R: 250
    T: 8/7
  expected: 20

#### isentropic

### mach_number

<!-- family: isentropic; symbols: V, g, R, T; expr: V/(g*R*T)**0.5; numeric: yes -->

- name: twice_sonic
  inputs:
    V: 40
    g: 7/5
    R: 250
    T: 8/7
  expected: 2

### newtonian_shear

<!-- family: thermo; symbols: mu, dVdy; expr: mu*dVdy; numeric: yes -->

- name: linear_profile
  inputs:
    mu: 1/50000
    dVdy: 500
  expected: 1/100

### kinematic_viscosity

<!-- family: thermo; symbols: mu, rho; expr: mu/rho; numeric: yes -->

- name: sea_level_air
  inputs:
    mu: 9/500000
    rho: 6/5
  expected: 3/200000

### reynolds_number

<!-- family: thermo; symbols: rho, V, L, mu; expr: rho*V*L/mu; numeric: yes -->

- name: chord_two_metres
  inputs:
    rho: 6/5
    V: 50
    L: 2
    mu: 3/200000
  expected: 8000000

### reynolds_number_kinematic

<!-- family: thermo; symbols: V, L, nu; expr: V*L/nu; numeric: yes -->

- name: chord_two_metres
  inputs:
    V: 50
    L: 2
    nu: 3/200000
  expected: 20000000/3

### dynamic_pressure

<!-- family: isentropic; symbols: rho, V; expr: 0.5*rho*V**2; numeric: yes -->

- name: definition
  inputs:
    rho: 5/4
    V: 40
  expected: 1000

### dynamic_pressure_air

<!-- family: isentropic; symbols: M; expr: (7/10)*M**2; numeric: yes -->

- name: mach_two
  inputs:
    M: 2
  expected: 14/5

### total_enthalpy

<!-- family: isentropic; symbols: h, V; expr: h + V**2/2; numeric: yes -->

- name: stagnation_enthalpy
  inputs:
    h: 250000
    V: 100000**0.5
  expected: 300000

### total_temperature_energy

<!-- family: isentropic; symbols: cp, T, V; expr: cp*T + V**2/2; numeric: yes -->

- name: stagnation_recovery
  inputs:
    cp: 1000
    T: 250
    V: 100000**0.5
  expected: 300000

### sound_speed_energy

<!-- family: isentropic; symbols: a, g, V; expr: a**2/(g - 1) + V**2/2; numeric: yes -->

- name: finite_speed
  inputs:
    a: 20
    g: 7/5
    V: 10
  expected: 1050

### stagnation_temperature

<!-- family: isentropic; symbols: g, M; expr: 1 + ((g - 1)/2)*M**2; numeric: yes -->

- name: reservoir
  inputs:
    g: 7/5
    M: 0
  expected: 1

- name: mach_two_air
  inputs:
    g: 7/5
    M: 2
  expected: 9/5

### stagnation_pressure

<!-- family: isentropic; symbols: Tt, T, g; expr: (Tt/T)**(g/(g - 1)); numeric: yes -->

- name: reservoir
  inputs:
    Tt: 1
    T: 1
    g: 7/5
  expected: 1

- name: temperature_ratio_nine_quarters
  inputs:
    Tt: 9/4
    T: 1
    g: 7/5
  expected: 2187/128

### stagnation_density

<!-- family: isentropic; symbols: Tt, T, g; expr: (Tt/T)**(1/(g - 1)); numeric: yes -->

- name: reservoir
  inputs:
    Tt: 1
    T: 1
    g: 7/5
  expected: 1

- name: temperature_ratio_nine_quarters
  inputs:
    Tt: 9/4
    T: 1
    g: 7/5
  expected: 243/32

### stagnation_sound_speed

<!-- family: isentropic; symbols: Tt, T; expr: (Tt/T)**0.5; numeric: yes -->

- name: reservoir
  inputs:
    Tt: 1
    T: 1
  expected: 1

- name: temperature_ratio_nine_quarters
  inputs:
    Tt: 9/4
    T: 1
  expected: 3/2

### stagnation_temperature_air

<!-- family: isentropic; symbols: M; expr: 1 + M**2/5; numeric: yes -->

- name: reservoir
  inputs:
    M: 0
  expected: 1

- name: mach_two
  inputs:
    M: 2
  expected: 9/5

### stagnation_pressure_air

<!-- family: isentropic; symbols: M; expr: (1 + M**2/5)**(7/2); numeric: yes -->

- name: reservoir
  inputs:
    M: 0
  expected: 1

- name: mach_five_halves
  inputs:
    M: 5/2
  expected: 2187/128

### stagnation_density_air

<!-- family: isentropic; symbols: M; expr: (1 + M**2/5)**(5/2); numeric: yes -->

- name: reservoir
  inputs:
    M: 0
  expected: 1

- name: mach_five_halves
  inputs:
    M: 5/2
  expected: 243/32

### isentropic_state_ratio

<!-- family: isentropic; symbols: p2, p1, g; expr: (p2/p1)**((g - 1)/g); numeric: yes -->

- name: pressure_ratio_128
  inputs:
    p2: 128
    p1: 1
    g: 7/5
  expected: 4

### sonic_temperature

<!-- family: isentropic; symbols: g; expr: 2/(g + 1); numeric: yes -->

- name: air
  inputs:
    g: 7/5
  expected: 5/6

- name: monatomic
  inputs:
    g: 5/3
  expected: 3/4

### sonic_pressure

<!-- family: isentropic; symbols: g; expr: (2/(g + 1))**(g/(g - 1)); numeric: yes -->

- name: air
  inputs:
    g: 7/5
  expected: (5/6)**(7/2)

- name: gamma_three_halves
  inputs:
    g: 3/2
  expected: 64/125

### sonic_density

<!-- family: isentropic; symbols: g; expr: (2/(g + 1))**(1/(g - 1)); numeric: yes -->

- name: air
  inputs:
    g: 7/5
  expected: (5/6)**(5/2)

- name: gamma_three_halves
  inputs:
    g: 3/2
  expected: 16/25

### sonic_sound_speed

<!-- family: isentropic; symbols: g; expr: (g + 1)/2; numeric: yes -->

- name: air
  inputs:
    g: 7/5
  expected: 6/5

- name: monatomic
  inputs:
    g: 5/3
  expected: 4/3

### compressible_bernoulli

<!-- family: isentropic; symbols: g, pt, rhot; expr: (g/(g - 1))*pt/rhot; numeric: yes -->

- name: sea_level_stagnation
  inputs:
    g: 7/5
    pt: 101325
    rhot: 49/40
  expected: 289500

### area_mach

<!-- family: isentropic; symbols: M, g; expr: (1/M)*((2/(g+1))*(1+((g-1)/2)*M**2))**((g+1)/(2*(g-1))); numeric: yes -->

- name: throat
  inputs:
    M: 1
    g: 7/5
  expected: 1

- name: mach_two_air
  inputs:
    M: 2
    g: 7/5
  expected: 27/16

### area_mach_air

<!-- family: isentropic; symbols: M; expr: (216/125)*M*(1 + M**2/5)**(-3); numeric: yes -->

- name: throat
  inputs:
    M: 1
  expected: 1

- name: mach_two
  inputs:
    M: 2
  expected: 16/27

### stream_tube_continuity

<!-- family: isentropic; symbols: rho, V, A; expr: rho*V*A; numeric: yes -->

- name: mass_flow
  inputs:
    rho: 6/5
    V: 100
    A: 1/2
  expected: 60

### small_disturbance_temperature

<!-- family: isentropic; symbols: g, Minf, V, Vinf; expr: 1 - (g - 1)*Minf**2*(V - Vinf)/Vinf; numeric: yes -->

- name: ten_percent_faster
  inputs:
    g: 7/5
    Minf: 2
    V: 11
    Vinf: 10
  expected: 21/25

### small_disturbance_pressure

<!-- family: isentropic; symbols: g, Minf, V, Vinf; expr: 1 - g*Minf**2*(V - Vinf)/Vinf; numeric: yes -->

- name: ten_percent_faster
  inputs:
    g: 7/5
    Minf: 2
    V: 11
    Vinf: 10
  expected: 11/25

### small_disturbance_density

<!-- family: isentropic; symbols: Minf, V, Vinf; expr: 1 - Minf**2*(V - Vinf)/Vinf; numeric: yes -->

- name: ten_percent_faster
  inputs:
    Minf: 2
    V: 11
    Vinf: 10
  expected: 3/5

#### shock

### normal_shock_pressure

<!-- family: shock; symbols: g, M1; expr: (2*g*M1**2 - (g - 1))/(g + 1); numeric: yes -->

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: 9/2

- name: monatomic_mach_two
  inputs:
    g: 5/3
    M1: 2
  expected: 19/4

### normal_shock_density

<!-- family: shock; symbols: g, M1; expr: ((g + 1)*M1**2)/((g - 1)*M1**2 + 2); numeric: yes -->

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: 8/3

- name: monatomic_mach_two
  inputs:
    g: 5/3
    M1: 2
  expected: 16/7

### normal_shock_temperature

<!-- family: shock; symbols: g, M1; expr: (2*g*M1**2 - (g - 1))*((g - 1)*M1**2 + 2)/((g + 1)**2*M1**2); numeric: yes -->

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: 27/16

- name: monatomic_mach_two
  inputs:
    g: 5/3
    M1: 2
  expected: 133/64

### normal_shock_mach

<!-- family: shock; symbols: g, M1; expr: ((g - 1)*M1**2 + 2)/(2*g*M1**2 - (g - 1)); numeric: yes -->

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: 1/3

- name: monatomic_mach_two
  inputs:
    g: 5/3
    M1: 2
  expected: 7/19

### rayleigh_pitot

<!-- family: shock; symbols: g, M1; expr: (((g + 1)/2)*M1**2)**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1)); numeric: yes -->

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: (24/5)**(7/2)*(2/9)**(5/2)

### normal_shock_entropy

<!-- family: shock; symbols: R, pt2, pt1; expr: -R*log(pt2/pt1); numeric: yes -->

- name: total_pressure_drop_by_e
  inputs:
    R: 287
    pt2: 1
    pt1: e
  expected: 287

### normal_shock_pressure_air

<!-- family: shock; symbols: M1; expr: (7*M1**2 - 1)/6; numeric: yes -->

- name: mach_one
  inputs:
    M1: 1
  expected: 1

- name: mach_two
  inputs:
    M1: 2
  expected: 9/2

### normal_shock_density_air

<!-- family: shock; symbols: M1; expr: 6*M1**2/(M1**2 + 5); numeric: yes -->

- name: mach_one
  inputs:
    M1: 1
  expected: 1

- name: mach_two
  inputs:
    M1: 2
  expected: 8/3

### normal_shock_mach_air

<!-- family: shock; symbols: M1; expr: (M1**2 + 5)/(7*M1**2 - 1); numeric: yes -->

- name: mach_one
  inputs:
    M1: 1
  expected: 1

- name: mach_two
  inputs:
    M1: 2
  expected: 1/3

### rankine_hugoniot

<!-- family: shock; symbols: g, p2, p1, rho2, rho1; expr: g*(p2 + p1)/(rho2 + rho1); numeric: yes -->

- name: mach_two_air_state
  inputs:
    g: 7/5
    p2: 9
    p1: 2
    rho2: 8
    rho1: 3
  expected: 7/5

### prandtl_relation

<!-- family: shock; symbols: astar; expr: astar**2; numeric: yes -->

- name: critical_speed_squared
  inputs:
    astar: 30
  expected: 900

#### oblique_shock

### oblique_shock_deflection

<!-- family: oblique_shock; symbols: theta, M1, g; expr: 2*cot(theta)*(M1**2*sin(theta)**2 - 1)/(2 + M1**2*(g + cos(2*theta))); numeric: yes -->

- name: mach_wave
  inputs:
    theta: pi/6
    M1: 2
    g: 7/5
  expected: 0

- name: forty_five_degree_wave
  inputs:
    theta: pi/4
    M1: 2
    g: 7/5
  expected: 5/19

### oblique_shock_deflection_air

<!-- family: oblique_shock; symbols: M1, theta; expr: 5*(M1**2*sin(2*theta) - 2*cot(theta))/(10 + M1**2*(7 + 5*cos(2*theta))); numeric: yes -->

- name: mach_wave
  inputs:
    M1: 2
    theta: pi/6
  expected: 0

- name: forty_five_degree_wave
  inputs:
    M1: 2
    theta: pi/4
  expected: 5/19

### oblique_shock_normal_mach

<!-- family: oblique_shock; symbols: g, M1, theta; expr: ((g - 1)*M1**2*sin(theta)**2 + 2)/(2*g*M1**2*sin(theta)**2 - (g - 1)); numeric: yes -->

- name: mach_wave
  inputs:
    g: 7/5
    M1: 2
    theta: pi/6
  expected: 1

- name: forty_five_degree_wave
  inputs:
    g: 7/5
    M1: 2
    theta: pi/4
  expected: 7/13

#### expansion

### mach_angle

<!-- family: expansion; symbols: M; expr: asin(1/M); numeric: yes -->

- name: sonic
  inputs:
    M: 1
  expected: pi/2

- name: mach_two
  inputs:
    M: 2
  expected: pi/6

### prandtl_meyer

<!-- family: expansion; symbols: g, M; expr: ((g + 1)/(g - 1))**0.5*atan(((g - 1)/(g + 1)*(M**2 - 1))**0.5) - atan((M**2 - 1)**0.5); numeric: yes -->

- name: mach_one
  inputs:
    g: 7/5
    M: 1
  expected: 0

- name: monatomic_mach_sqrt_two
  inputs:
    g: 5/3
    M: 2**0.5
  expected: 2*atan(1/2) - pi/4

### prandtl_meyer_max

<!-- family: expansion; symbols: g, pi; expr: (((g + 1)/(g - 1))**0.5 - 1)*pi/2; numeric: yes -->

- name: monatomic
  inputs:
    g: 5/3
    pi: pi
  expected: pi/2

#### conical_shock

### conical_ray_normal_speed

<!-- family: conical_shock; symbols: u, theta; expr: partial(u, theta); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is the unevaluated derivative of radial speed with respect to polar angle. -->

### conical_vacuum_sound_speed_sq

<!-- family: conical_shock; symbols: g, u, v; expr: ((g - 1)/2)*(1 - u**2 - v**2); numeric: yes -->

- name: rest
  inputs:
    g: 7/5
    u: 0
    v: 0
  expected: 1/5

- name: mach_two_stream
  inputs:
    g: 7/5
    u: 1/3**0.5
    v: -1/3
  expected: 1/9

### taylor_maccoll_radial_acceleration

<!-- family: conical_shock; symbols: g, u, v, theta; expr: ((g - 1)/2*(1 - u**2 - v**2))*(u + v*cot(theta))/(v**2 - (g - 1)/2*(1 - u**2 - v**2)) - u; numeric: yes -->

- name: cone_surface
  inputs:
    g: 7/5
    u: 1/2
    v: 0
    theta: pi/4
  expected: -1

### conical_shock_wave_tangent

<!-- family: conical_shock; symbols: g, u, v; expr: ((g - 1)/(g + 1))*(u**2 - 1)/(u*v); numeric: yes -->

- name: mach_wave
  inputs:
    g: 7/5
    u: 1/3**0.5
    v: -1/3
  expected: 1/3**0.5

### conical_freestream_mach_sq

<!-- family: conical_shock; symbols: g, u, theta; expr: (2/(g - 1))*u**2/(cos(theta)**2 - u**2); numeric: yes -->

- name: mach_two_wave
  inputs:
    g: 7/5
    u: 1/3**0.5
    theta: pi/6
  expected: 4

### conical_resultant_mach

<!-- family: conical_shock; symbols: u, v, g; expr: (2*(u**2 + v**2)/((g - 1)*(1 - u**2 - v**2)))**0.5; numeric: yes -->

- name: mach_two_stream
  inputs:
    u: 1/3**0.5
    v: -1/3
    g: 7/5
  expected: 2

### conical_critical_mach

<!-- family: conical_shock; symbols: g, u, v; expr: ((g + 1)/(g - 1)*(u**2 + v**2))**0.5; numeric: yes -->

- name: mach_two_stream
  inputs:
    g: 7/5
    u: 1/3**0.5
    v: -1/3
  expected: 2*(6**0.5)/3

### limiting_speed_ratio

<!-- family: conical_shock; symbols: g, M; expr: (((g - 1)/2)*M**2/(1 + ((g - 1)/2)*M**2))**0.5; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: (1/6)**0.5

- name: mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 2/3

### conical_radial_speed

<!-- family: conical_shock; symbols: Vx, theta, Vr; expr: Vx*cos(theta) + Vr*sin(theta); numeric: yes -->

- name: axis
  inputs:
    Vx: 3/5
    theta: 0
    Vr: 4/5
  expected: 3/5

- name: ninety_degrees
  inputs:
    Vx: 3/5
    theta: pi/2
    Vr: 4/5
  expected: 4/5

### conical_normal_speed

<!-- family: conical_shock; symbols: Vx, theta, Vr; expr: -Vx*sin(theta) + Vr*cos(theta); numeric: yes -->

- name: axis
  inputs:
    Vx: 3/5
    theta: 0
    Vr: 4/5
  expected: 4/5

- name: ninety_degrees
  inputs:
    Vx: 3/5
    theta: pi/2
    Vr: 4/5
  expected: -3/5

#### imperfect

### gamma_imperfect

<!-- family: imperfect; symbols: g_perf, theta, T; expr: 1 + (g_perf - 1)/(1 + (g_perf - 1)*((theta/T)**2*exp(theta/T)/(exp(theta/T) - 1)**2)); numeric: yes -->

- name: half_excited_exponential
  inputs:
    g_perf: 7/5
    theta: log(2)
    T: 1
  expected: 1 + (2/5)/(1 + (4/5)*log(2)**2)

### speed_of_sound_imperfect

<!-- family: imperfect; symbols: g, R, T; expr: (g*R*T)**0.5; numeric: yes -->

- name: exact_square
  inputs:
    g: 7/5
    R: 250
    T: 8/7
  expected: 20

### imperfect_mach

<!-- family: imperfect; symbols: g, Tt, T, g_perf, theta; expr: (2/g)*(Tt/T)*((g_perf/(g_perf - 1))*(1 - T/Tt) + (theta/Tt)*(1/(exp(theta/Tt) - 1) - 1/(exp(theta/T) - 1))); numeric: yes -->

- name: rest
  inputs:
    g: 7/5
    Tt: 300
    T: 300
    g_perf: 7/5
    theta: 3055.6
  expected: 0

- name: temperature_ratio_two
  inputs:
    g: 1 + (2/5)/(1 + (32/45)*log(2)**2)
    Tt: 2
    T: 1
    g_perf: 7/5
    theta: log(4)
  expected: (4/(1 + (2/5)/(1 + (32/45)*log(2)**2)))*(7/4 + (2/3)*log(2))

### imperfect_density_ratio

<!-- family: imperfect; symbols: theta, Tt, T, g_perf; expr: ((exp(theta/Tt) - 1)/(exp(theta/T) - 1))*(T/Tt)**(1/(g_perf - 1))*exp((theta/T)*exp(theta/T)/(exp(theta/T) - 1) - (theta/Tt)*exp(theta/Tt)/(exp(theta/Tt) - 1)); numeric: yes -->

- name: equal_static_and_total
  inputs:
    theta: 3055.6
    Tt: 500
    T: 500
    g_perf: 7/5
  expected: 1

- name: temperature_ratio_two
  inputs:
    theta: log(4)
    Tt: 2
    T: 1
    g_perf: 7/5
  expected: 2**(-11/6)/3

### imperfect_pressure_ratio

<!-- family: imperfect; symbols: theta, Tt, T, g_perf; expr: ((exp(theta/Tt) - 1)/(exp(theta/T) - 1))*(T/Tt)**(g_perf/(g_perf - 1))*exp((theta/T)*exp(theta/T)/(exp(theta/T) - 1) - (theta/Tt)*exp(theta/Tt)/(exp(theta/Tt) - 1)); numeric: yes -->

- name: equal_static_and_total
  inputs:
    theta: 3055.6
    Tt: 500
    T: 500
    g_perf: 7/5
  expected: 1

- name: temperature_ratio_two
  inputs:
    theta: log(4)
    Tt: 2
    T: 1
    g_perf: 7/5
  expected: 2**(-17/6)/3

### imperfect_dynamic_pressure

<!-- family: imperfect; symbols: g_perf, Tt, T, theta; expr: (g_perf/(g_perf - 1))*(Tt/T - 1) + (theta/T)*(1/(exp(theta/Tt) - 1) - 1/(exp(theta/T) - 1)); numeric: yes -->

- name: rest
  inputs:
    g_perf: 7/5
    Tt: 300
    T: 300
    theta: 3055.6
  expected: 0

- name: temperature_ratio_two
  inputs:
    g_perf: 7/5
    Tt: 2
    T: 1
    theta: log(4)
  expected: 7/2 + (4/3)*log(2)

## Atmosphere

#### atmosphere

### specific_gas_constant

<!-- family: atmosphere; symbols: Rstar, M; expr: Rstar/M; numeric: yes -->

- name: dry_air_1976
  inputs:
    Rstar: 8314.32
    M: 28.9644
  expected: 8314.32/28.9644

### geopotential_altitude

<!-- family: atmosphere; symbols: r0, Z; expr: r0*Z/(r0 + Z); numeric: yes -->

- name: half_radius
  inputs:
    r0: 6
    Z: 2
  expected: 3/2

### geometric_altitude

<!-- family: atmosphere; symbols: r0, H; expr: r0*H/(r0 - H); numeric: yes -->

- name: inverse_of_half_radius
  inputs:
    r0: 6
    H: 3/2
  expected: 2

### gravity_inverse_square

<!-- family: atmosphere; symbols: g0, r0, Z; expr: g0*(r0/(r0 + Z))**2; numeric: yes -->

- name: equal_radius
  inputs:
    g0: 16
    r0: 2
    Z: 2
  expected: 4

### hydrostatic_gradient

<!-- family: atmosphere; symbols: g, rho; expr: -g*rho; numeric: yes -->

- name: sea_level_weight
  inputs:
    g: 10
    rho: 5/4
  expected: -25/2

### hydrostatic_geopotential

<!-- family: atmosphere; symbols: g0, rho; expr: -g0*rho; numeric: yes -->

- name: sea_level_weight
  inputs:
    g0: 10
    rho: 5/4
  expected: -25/2

### molecular_scale_temperature

<!-- family: atmosphere; symbols: T, M0, M; expr: T*M0/M; numeric: yes -->

- name: half_molar_mass
  inputs:
    T: 200
    M0: 30
    M: 20
  expected: 300

### kinetic_temperature

<!-- family: atmosphere; symbols: TM, M, M0; expr: TM*M/M0; numeric: yes -->

- name: inverse_half_molar_mass
  inputs:
    TM: 300
    M: 20
    M0: 30
  expected: 200

### troposphere_temperature

<!-- family: atmosphere; symbols: TMb, LMb, H, Hb; expr: TMb + LMb*(H - Hb); numeric: yes -->

- name: tropopause
  inputs:
    TMb: 288.15
    LMb: -13/2000
    H: 11000
    Hb: 0
  expected: 216.65

### atmosphere_equation_of_state

<!-- family: atmosphere; symbols: rho, Rstar, T, M; expr: rho*Rstar*T/M; numeric: yes -->

- name: unit_gas
  inputs:
    rho: 2
    Rstar: 10
    T: 300
    M: 20
  expected: 300

### atmosphere_density

<!-- family: atmosphere; symbols: p, M, Rstar, T; expr: p*M/(Rstar*T); numeric: yes -->

- name: unit_gas
  inputs:
    p: 300
    M: 20
    Rstar: 10
    T: 300
  expected: 2

### atmosphere_density_molecular

<!-- family: atmosphere; symbols: p, M0, Rstar, TM; expr: p*M0/(Rstar*TM); numeric: yes -->

- name: unit_gas
  inputs:
    p: 300
    M0: 20
    Rstar: 10
    TM: 300
  expected: 2

### gradient_layer_pressure

<!-- family: atmosphere; symbols: pb, TMb, TM, g0, M0, Rstar, LMb; expr: pb*(TMb/TM)**(g0*M0/(Rstar*LMb)); numeric: yes -->

- name: double_temperature
  inputs:
    pb: 16
    TMb: 4
    TM: 2
    g0: 1
    M0: 1
    Rstar: 1
    LMb: 1
  expected: 32

### isothermal_layer_pressure

<!-- family: atmosphere; symbols: pb, g0, M0, H, Hb, Rstar, TMb; expr: pb*exp(-g0*M0*(H - Hb)/(Rstar*TMb)); numeric: yes -->

- name: one_scale_height
  inputs:
    pb: 1
    g0: 1
    M0: 1
    H: 1
    Hb: 0
    Rstar: 1
    TMb: 1
  expected: exp(-1)

### gradient_layer_density

<!-- family: atmosphere; symbols: rhob, TMb, TM, g0, M0, Rstar, LMb; expr: rhob*(TMb/TM)**(g0*M0/(Rstar*LMb) + 1); numeric: yes -->

- name: double_temperature
  inputs:
    rhob: 1
    TMb: 4
    TM: 2
    g0: 1
    M0: 1
    Rstar: 1
    LMb: 1
  expected: 4

### isothermal_layer_density

<!-- family: atmosphere; symbols: rhob, g0, M0, H, Hb, Rstar, TMb; expr: rhob*exp(-g0*M0*(H - Hb)/(Rstar*TMb)); numeric: yes -->

- name: one_scale_height
  inputs:
    rhob: 1
    g0: 1
    M0: 1
    H: 1
    Hb: 0
    Rstar: 1
    TMb: 1
  expected: exp(-1)

### number_density

<!-- family: atmosphere; symbols: p, kB, T; expr: p/(kB*T); numeric: yes -->

- name: unit_thermal
  inputs:
    p: 200
    kB: 2
    T: 50
  expected: 2

### species_number_density

<!-- family: atmosphere; symbols: Fi, N; expr: Fi*N; numeric: yes -->

- name: nitrogen_fraction
  inputs:
    Fi: 4/5
    N: 10
  expected: 8

### atmosphere_partial_pressure

<!-- family: atmosphere; symbols: ni, kB, T; expr: ni*kB*T; numeric: yes -->

- name: unit_thermal
  inputs:
    ni: 2
    kB: 2
    T: 50
  expected: 200

### saturation_vapor_pressure_water

<!-- family: atmosphere; symbols: T; expr: 100*10**(-4.9283*log(T - 0.15)/log(10) - 2937.4/(T - 0.15) + 23.5518); numeric: yes -->

- name: ice_point
  inputs:
    T: 273.15
  expected: 610.8754428597153

### saturation_vapor_pressure_ice

<!-- family: atmosphere; symbols: T; expr: 100*10**(-0.32286*log(T - 0.15)/log(10) - 2705.21/(T - 0.15) + 11.4816); numeric: yes -->

- name: ice_point
  inputs:
    T: 273.15
  expected: 610.7540964879718

### relative_humidity

<!-- family: atmosphere; symbols: e, es; expr: e/es; numeric: yes -->

- name: quarter
  inputs:
    e: 1
    es: 4
  expected: 1/4

### vapor_partial_pressure

<!-- family: atmosphere; symbols: phi, es; expr: phi*es; numeric: yes -->

- name: quarter
  inputs:
    phi: 1/4
    es: 4
  expected: 1

### absolute_humidity

<!-- family: atmosphere; symbols: e, Rv, T; expr: e/(Rv*T); numeric: yes -->

- name: unit_vapor
  inputs:
    e: 20
    Rv: 4
    T: 5
  expected: 1

### water_molar_mass

<!-- family: atmosphere; symbols: MH2, MO2; expr: MH2 + MO2/2; numeric: yes -->

- name: standard_1976_table
  inputs:
    MH2: 2.01594
    MO2: 31.9988
  expected: 18.01534

### moist_mean_molar_mass

<!-- family: atmosphere; symbols: p, e, M0, Mw; expr: ((p - e)*M0 + e*Mw)/p; numeric: yes -->

- name: one_quarter_vapor
  inputs:
    p: 4
    e: 1
    M0: 32
    Mw: 16
  expected: 28

### moist_density

<!-- family: atmosphere; symbols: p, e, M0, Rstar, T, Mw; expr: (p - e)*M0/(Rstar*T) + e*Mw/(Rstar*T); numeric: yes -->

- name: two_partial_pressures
  inputs:
    p: 4
    e: 1
    M0: 20
    Mw: 10
    Rstar: 2
    T: 5
  expected: 7

### pressure_scale_height

<!-- family: atmosphere; symbols: Rstar, T, g, M; expr: Rstar*T/(g*M); numeric: yes -->

- name: ten_kilometres
  inputs:
    Rstar: 300
    T: 200
    g: 10
    M: 6
  expected: 1000

### geopotential_pressure_scale_height

<!-- family: atmosphere; symbols: Rstar, TM, g0, M0; expr: Rstar*TM/(g0*M0); numeric: yes -->

- name: ten_kilometres
  inputs:
    Rstar: 300
    TM: 200
    g0: 10
    M0: 6
  expected: 1000

### atmosphere_sound_speed

<!-- family: atmosphere; symbols: g, Rstar, TM, M0; expr: (g*Rstar*TM/M0)**0.5; numeric: yes -->

- name: perfect_square
  inputs:
    g: 4
    Rstar: 50
    TM: 20
    M0: 10
  expected: 20

### sutherland_viscosity

<!-- family: atmosphere; symbols: beta, T, S; expr: beta*T**1.5/(T + S); numeric: yes -->

- name: round_temperature
  inputs:
    beta: 1
    T: 400
    S: 100
  expected: 16

### thermal_conductivity_air

<!-- family: atmosphere; symbols: k0, T, C; expr: k0*T**1.5/(T + C*10**(-12/T)); numeric: yes -->

- name: twelve_kelvin
  inputs:
    k0: 1
    T: 12
    C: 10
  expected: 12**1.5/13

### mean_particle_speed

<!-- family: atmosphere; symbols: Rstar, T, M, pi; expr: (8*Rstar*T/(pi*M))**0.5; numeric: yes -->

- name: cancel_pi
  inputs:
    Rstar: pi
    T: 2
    M: 4
    pi: pi
  expected: 2

### mean_free_path

<!-- family: atmosphere; symbols: Rstar, T, sigma, NA, p, pi; expr: Rstar*T/(2**0.5*pi*sigma**2*NA*p); numeric: yes -->

- name: unit_collision
  inputs:
    Rstar: 2**0.5
    T: 1
    sigma: 1
    NA: 1
    p: 1
    pi: 1
  expected: 1

### collision_frequency

<!-- family: atmosphere; symbols: Vbar, L; expr: Vbar/L; numeric: yes -->

- name: unit_path
  inputs:
    Vbar: 400
    L: 2
  expected: 200

### kinetic_temperature_linear

<!-- family: atmosphere; symbols: Tb, LKb, Z, Zb; expr: Tb + LKb*(Z - Zb); numeric: yes -->

- name: one_hundred_twenty_km
  inputs:
    Tb: 240
    LKb: 12/1000
    Z: 120000
    Zb: 110000
  expected: 360

### mesosphere_ellipse_temperature

<!-- family: atmosphere; symbols: Tc, A, Z, Z8, a; expr: Tc + A*(1 - ((Z - Z8)/a)**2)**0.5; numeric: yes -->

- name: layer_base
  inputs:
    Tc: 10
    A: -4
    Z: 5
    Z8: 5
    a: 20
  expected: 6

### reduced_geopotential

<!-- family: atmosphere; symbols: Z, Zb, r0; expr: (Z - Zb)*(r0 + Zb)/(r0 + Z); numeric: yes -->

- name: four_over_eight
  inputs:
    Z: 5
    Zb: 1
    r0: 3
  expected: 2

### exospheric_temperature

<!-- family: atmosphere; symbols: Tinf, Tb, lam, xi; expr: Tinf - (Tinf - Tb)*exp(-lam*xi); numeric: yes -->

- name: one_e_fold
  inputs:
    Tinf: 5
    Tb: 1
    lam: 1
    xi: log(2)
  expected: 3

### glenn_zone_pressure_power

<!-- family: atmosphere; symbols: pref, T, Tref, n; expr: pref*(T/Tref)**n; numeric: yes -->

- name: square
  inputs:
    pref: 16
    T: 4
    Tref: 2
    n: 2
  expected: 64

### glenn_zone_pressure_exponential

<!-- family: atmosphere; symbols: pref, A, B, h; expr: pref*exp(A - B*h); numeric: yes -->

- name: cancel_exponent
  inputs:
    pref: 10
    A: 3
    B: 1
    h: 3
  expected: 10

### glenn_density

<!-- family: atmosphere; symbols: p, R, T; expr: p/(R*T); numeric: yes -->

- name: glenn_gas
  inputs:
    p: 287
    R: 287
    T: 1
  expected: 1

## Rocket propulsion

#### rocket

### exhaust_velocity_from_effective

<!-- family: rocket; symbols: c, p2, p3, A2, mdot; expr: c - (p2 - p3)*A2/mdot; numeric: yes -->

- name: pressure_imbalance
  inputs:
    c: 2000
    p2: 150000
    p3: 100000
    A2: 1/50
    mdot: 5
  expected: 1800

### exhaust_velocity_isentropic

<!-- family: rocket; symbols: k, R, T1, p2, p1; expr: ((2*k/(k - 1))*R*T1*(1 - (p2/p1)**((k - 1)/k)))**0.5; numeric: yes -->

- name: pressure_ratio_four
  inputs:
    k: 2
    R: 200
    T1: 400
    p2: 1
    p1: 4
  expected: 400

### exhaust_velocity_enthalpy

<!-- family: rocket; symbols: h1, h2; expr: (2*(h1 - h2))**0.5; numeric: yes -->

- name: enthalpy_drop
  inputs:
    h1: 800000
    h2: 300000
  expected: 1000

### effective_exhaust_velocity

<!-- family: rocket; symbols: F, mdot; expr: F/mdot; numeric: yes -->

- name: five_hundred_seconds
  inputs:
    F: 9.80665*1000
    mdot: 2
  expected: 9.80665*500

### equivalent_exhaust_velocity

<!-- family: rocket; symbols: v2, p2, p3, A2, mdot; expr: v2 + (p2 - p3)*A2/mdot; numeric: yes -->

- name: pressure_thrust
  inputs:
    v2: 2400
    p2: 120000
    p3: 100000
    A2: 1/2
    mdot: 10
  expected: 3400

### thrust_momentum

<!-- family: rocket; symbols: mdot, v2, p2, p3, A2; expr: mdot*v2 + (p2 - p3)*A2; numeric: yes -->

- name: momentum_and_pressure
  inputs:
    mdot: 10
    v2: 2000
    p2: 120000
    p3: 100000
    A2: 1/20
  expected: 21000

### thrust_coefficient_form

<!-- family: rocket; symbols: CF, p1, At; expr: CF*p1*At; numeric: yes -->

- name: definition
  inputs:
    CF: 3/2
    p1: 2000000
    At: 1/100
  expected: 30000

### thrust_constant_burn

<!-- family: rocket; symbols: c, mp, tp; expr: c*mp/tp; numeric: yes -->

- name: steady_burn
  inputs:
    c: 2500
    mp: 400
    tp: 20
  expected: 50000

### characteristic_velocity

<!-- family: rocket; symbols: p1, At, mdot; expr: p1*At/mdot; numeric: yes -->

- name: definition
  inputs:
    p1: 7000000
    At: 1/1000
    mdot: 14/3
  expected: 1500

### characteristic_velocity_ideal

<!-- family: rocket; symbols: k, R, T1; expr: (k*R*T1)**0.5/(k*((2/(k + 1))**((k + 1)/(k - 1)))**0.5); numeric: yes -->

- name: diatomic_closed_form
  inputs:
    k: 7/5
    R: 5/7
    T1: 5
  expected: (5**0.5)*216/175

### thrust_coefficient_definition

<!-- family: rocket; symbols: F, p1, At; expr: F/(p1*At); numeric: yes -->

- name: definition
  inputs:
    F: 30000
    p1: 2000000
    At: 1/100
  expected: 3/2

### thrust_coefficient_ideal

<!-- family: rocket; symbols: k, p2, p1, p3, A2, At; expr: ((2*k**2/(k - 1))*((2/(k + 1))**((k + 1)/(k - 1)))*(1 - (p2/p1)**((k - 1)/k)))**0.5 + (p2 - p3)/p1*A2/At; numeric: yes -->

- name: vacuum_pressure_term
  inputs:
    k: 2
    p2: 1
    p1: 4
    p3: 0
    A2: 2
    At: 1
  expected: (32/27)**0.5 + 1/2

### total_impulse

<!-- family: rocket; symbols: F, t; expr: integral(F, t); numeric: no (indefinite integral) -->

<!-- No scalar identity: the script is an indefinite integral. Constant thrust is checked on total_impulse_constant_thrust. -->

### total_impulse_constant_thrust

<!-- family: rocket; symbols: F, t; expr: F*t; numeric: yes -->

- name: steady_thrust
  inputs:
    F: 5000
    t: 12
  expected: 60000

### specific_impulse

<!-- family: rocket; symbols: c, g0; expr: c/g0; numeric: yes -->

- name: three_hundred_seconds
  inputs:
    c: 9.80665*300
    g0: 9.80665
  expected: 300

### specific_impulse_exit

<!-- family: rocket; symbols: v2, g0, p2, p3, A2, mdot; expr: v2/g0 + (p2 - p3)*A2/(mdot*g0); numeric: yes -->

- name: velocity_and_pressure
  inputs:
    v2: 9.80665*200
    g0: 9.80665
    p2: 9.80665*2
    p3: 9.80665
    A2: 1
    mdot: 1
  expected: 201

### propellant_mass_fraction

<!-- family: rocket; symbols: mp, m0; expr: mp/m0; numeric: yes -->

- name: four_fifths_propellant
  inputs:
    mp: 4
    m0: 5
  expected: 4/5

### mass_ratio

<!-- family: rocket; symbols: mf, m0; expr: mf/m0; numeric: yes -->

- name: final_over_initial
  inputs:
    mf: 1
    m0: 5
  expected: 1/5

### delta_v_vacuum

<!-- family: rocket; symbols: c, m0, mf; expr: c*log(m0/mf); numeric: yes -->

- name: mass_ratio_e
  inputs:
    c: 3000
    m0: e
    mf: 1
  expected: 3000

### mass_flow_continuity

<!-- family: rocket; symbols: A, v, V; expr: A*v/V; numeric: yes -->

- name: specific_volume
  inputs:
    A: 1/2
    v: 80
    V: 2/5
  expected: 100

### mass_flow_from_thrust

<!-- family: rocket; symbols: F, c; expr: F/c; numeric: yes -->

- name: definition
  inputs:
    F: 20000
    c: 2500
  expected: 8

### mass_flow_ideal

<!-- family: rocket; symbols: p1, At, k, R, T1; expr: p1*At*k*((2/(k + 1))**((k + 1)/(k - 1)))**0.5/(k*R*T1)**0.5; numeric: yes -->

- name: matches_ideal_characteristic_velocity
  inputs:
    p1: 216
    At: 1
    k: 7/5
    R: 5/7
    T1: 5
  expected: 35*(5**0.5)

### nozzle_area_ratio

<!-- family: rocket; symbols: A2, At; expr: A2/At; numeric: yes -->

- name: expansion_fifty
  inputs:
    A2: 1/2
    At: 1/100
  expected: 50

#### flight

### circular_orbit_velocity

<!-- family: flight; symbols: R0, g0, h; expr: R0*(g0/(R0 + h))**0.5; numeric: yes -->

- name: altitude_equal_to_radius
  inputs:
    R0: 6400000
    g0: 10
    h: 6400000
  expected: 4000*(2**0.5)

### escape_velocity

<!-- family: flight; symbols: R0, g0, h; expr: R0*(2*g0/(R0 + h))**0.5; numeric: yes -->

- name: altitude_equal_to_radius
  inputs:
    R0: 6400000
    g0: 10
    h: 6400000
  expected: 8000

### gravitational_parameter

<!-- family: flight; symbols: G, M; expr: G*M; numeric: yes -->

- name: product
  inputs:
    G: 2
    M: 8
  expected: 16

### vis_viva

<!-- family: flight; symbols: mu, r, a; expr: (mu*(2/r - 1/a))**0.5; numeric: yes -->

- name: circular
  inputs:
    mu: 16
    r: 4
    a: 4
  expected: 2

- name: periapsis_of_ellipse
  inputs:
    mu: 16
    r: 2
    a: 4
  expected: 12**0.5

### plane_change_impulse

<!-- family: flight; symbols: v, di; expr: 2*v*sin(di/2); numeric: yes -->

- name: half_turn
  inputs:
    v: 1
    di: pi
  expected: 2

- name: sixty_deg
  inputs:
    v: 1
    di: pi/3
  expected: 1

### specific_orbital_energy

<!-- family: flight; symbols: mu, a; expr: -(mu)/(2*a); numeric: yes -->

- name: circular_energy
  inputs:
    mu: 16
    a: 4
  expected: -2

### specific_orbital_energy_from_speed

<!-- family: flight; symbols: v, mu, r; expr: v**2/2 - mu/r; numeric: yes -->

- name: circular_energy
  inputs:
    v: 2
    mu: 16
    r: 4
  expected: -2

### orbital_period

<!-- family: flight; symbols: a, mu, pi; expr: 2*pi*(a**3/mu)**0.5; numeric: yes -->

- name: unit_orbit
  inputs:
    a: 1
    mu: 1
    pi: pi
  expected: 2*pi

### periapsis_radius

<!-- family: flight; symbols: a, e; expr: a*(1 - e); numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 2

### apoapsis_radius

<!-- family: flight; symbols: a, e; expr: a*(1 + e); numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 6

### orbit_eccentricity

<!-- family: flight; symbols: ra, rp; expr: (ra - rp)/(ra + rp); numeric: yes -->

- name: two_and_six
  inputs:
    ra: 6
    rp: 2
  expected: 1/2

### semi_latus_rectum

<!-- family: flight; symbols: a, e; expr: a*(1 - e**2); numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 3

### semi_minor_axis

<!-- family: flight; symbols: a, e; expr: a*(1 - e**2)**0.5; numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 2*(3**0.5)

### conic_radius

<!-- family: flight; symbols: a, e, nu; expr: a*(1 - e**2)/(1 + e*cos(nu)); numeric: yes -->

- name: periapsis
  inputs:
    a: 4
    e: 1/2
    nu: 0
  expected: 2

- name: apoapsis
  inputs:
    a: 4
    e: 1/2
    nu: pi
  expected: 6

### conic_radius_from_parameter

<!-- family: flight; symbols: p, e, nu; expr: p/(1 + e*cos(nu)); numeric: yes -->

- name: periapsis
  inputs:
    p: 3
    e: 1/2
    nu: 0
  expected: 2

### specific_angular_momentum

<!-- family: flight; symbols: mu, p; expr: (mu*p)**0.5; numeric: yes -->

- name: parameter_nine
  inputs:
    mu: 4
    p: 9
  expected: 6

### mean_motion

<!-- family: flight; symbols: mu, a; expr: (mu/a**3)**0.5; numeric: yes -->

- name: unit_rate
  inputs:
    mu: 8
    a: 2
  expected: 1

### mean_motion_from_period

<!-- family: flight; symbols: pi, T; expr: 2*pi/T; numeric: yes -->

- name: quarter_turn
  inputs:
    pi: pi
    T: 4
  expected: pi/2

### mean_anomaly

<!-- family: flight; symbols: n, t, tp; expr: n*(t - tp); numeric: yes -->

- name: four_seconds_after_periapsis
  inputs:
    n: 2
    t: 5
    tp: 1
  expected: 8

### kepler_equation

<!-- family: flight; symbols: E, e; expr: E - e*sin(E); numeric: yes -->

- name: quarter_turn
  inputs:
    E: pi/2
    e: 1/2
  expected: pi/2 - 1/2

- name: periapsis
  inputs:
    E: 0
    e: 1/2
  expected: 0

### radius_from_eccentric_anomaly

<!-- family: flight; symbols: a, e, E; expr: a*(1 - e*cos(E)); numeric: yes -->

- name: periapsis
  inputs:
    a: 4
    e: 1/2
    E: 0
  expected: 2

- name: apoapsis
  inputs:
    a: 4
    e: 1/2
    E: pi
  expected: 6

### true_anomaly_cosine

<!-- family: flight; symbols: E, e; expr: (cos(E) - e)/(1 - e*cos(E)); numeric: yes -->

- name: periapsis
  inputs:
    E: 0
    e: 1/2
  expected: 1

- name: apoapsis
  inputs:
    E: pi
    e: 1/2
  expected: -1

### true_anomaly_sine

<!-- family: flight; symbols: E, e; expr: ((1 - e**2)**0.5)*sin(E)/(1 - e*cos(E)); numeric: yes -->

- name: quarter_turn
  inputs:
    E: pi/2
    e: 1/2
  expected: (3**0.5)/2

### true_anomaly

<!-- family: flight; symbols: e, E; expr: 2*atan(((1 + e)/(1 - e))**0.5*tan(E/2)); numeric: yes -->

- name: quarter_eccentric_anomaly
  inputs:
    e: 1/2
    E: pi/2
  expected: 2*pi/3

- name: periapsis
  inputs:
    e: 1/2
    E: 0
  expected: 0

### eccentric_anomaly_cosine

<!-- family: flight; symbols: e, nu; expr: (e + cos(nu))/(1 + e*cos(nu)); numeric: yes -->

- name: periapsis
  inputs:
    e: 1/2
    nu: 0
  expected: 1

- name: apoapsis
  inputs:
    e: 1/2
    nu: pi
  expected: -1

### eccentric_anomaly_sine

<!-- family: flight; symbols: e, nu; expr: ((1 - e**2)**0.5)*sin(nu)/(1 + e*cos(nu)); numeric: yes -->

- name: quarter_turn
  inputs:
    e: 1/2
    nu: pi/2
  expected: (3**0.5)/2

### eccentric_anomaly_from_true

<!-- family: flight; symbols: e, nu; expr: 2*atan(((1 - e)/(1 + e))**0.5*tan(nu/2)); numeric: yes -->

- name: matches_quarter_eccentric_anomaly
  inputs:
    e: 1/2
    nu: 2*pi/3
  expected: pi/2

### perifocal_x

<!-- family: flight; symbols: a, E, e; expr: a*(cos(E) - e); numeric: yes -->

- name: periapsis
  inputs:
    a: 4
    E: 0
    e: 1/2
  expected: 2

- name: apoapsis
  inputs:
    a: 4
    E: pi
    e: 1/2
  expected: -6

### perifocal_y

<!-- family: flight; symbols: a, e, E; expr: a*((1 - e**2)**0.5)*sin(E); numeric: yes -->

- name: quarter_turn
  inputs:
    a: 4
    e: 1/2
    E: pi/2
  expected: 2*(3**0.5)

### argument_of_latitude

<!-- family: flight; symbols: omega, nu; expr: omega + nu; numeric: yes -->

- name: sum
  inputs:
    omega: 3/10
    nu: 7/10
  expected: 1

### parameter_from_angular_momentum

<!-- family: flight; symbols: h, mu; expr: h**2/mu; numeric: yes -->

- name: parameter_nine
  inputs:
    h: 6
    mu: 4
  expected: 9

### semimajor_axis_from_energy

<!-- family: flight; symbols: mu, eps; expr: -mu/(2*eps); numeric: yes -->

- name: ellipse_axis_four
  inputs:
    mu: 8
    eps: -1
  expected: 4

- name: hyperbola_axis
  inputs:
    mu: 8
    eps: 1
  expected: -4

### semimajor_axis_from_state

<!-- family: flight; symbols: mu, r, v; expr: mu*r/(2*mu - r*v**2); numeric: yes -->

- name: circular_radius
  inputs:
    mu: 4
    r: 4
    v: 1
  expected: 4

- name: periapsis_of_ellipse
  inputs:
    mu: 4
    r: 2
    v: 3**0.5
  expected: 4

### eccentricity_from_energy

<!-- family: flight; symbols: eps, h, mu; expr: (1 + 2*eps*h**2/mu**2)**0.5; numeric: yes -->

- name: parabola
  inputs:
    eps: 0
    h: 1
    mu: 1
  expected: 1

- name: eccentricity_one_half
  inputs:
    eps: -3/8
    h: 1
    mu: 1
  expected: 1/2

### eccentricity_from_axis

<!-- family: flight; symbols: mu, a, h; expr: ((mu*a - h**2)/(mu*a))**0.5; numeric: yes -->

- name: eccentricity_one_half
  inputs:
    mu: 4
    a: 4
    h: 12**0.5
  expected: 1/2

- name: hyperbola
  inputs:
    mu: 1
    a: -1
    h: 3**0.5
  expected: 2

### specific_angular_momentum_x

<!-- family: flight; symbols: y, vz, z, vy; expr: y*vz - z*vy; numeric: yes -->

- name: along_x
  inputs:
    y: 1
    vz: 1
    z: 0
    vy: 0
  expected: 1

### specific_angular_momentum_y

<!-- family: flight; symbols: z, vx, x, vz; expr: z*vx - x*vz; numeric: yes -->

- name: zero_for_xy_motion
  inputs:
    z: 0
    vx: 0
    x: 1
    vz: 0
  expected: 0

### specific_angular_momentum_z

<!-- family: flight; symbols: x, vy, y, vx; expr: x*vy - y*vx; numeric: yes -->

- name: unit_xy
  inputs:
    x: 1
    vy: 1
    y: 0
    vx: 0
  expected: 1

### specific_angular_momentum_magnitude

<!-- family: flight; symbols: hx, hy, hz; expr: (hx**2 + hy**2 + hz**2)**0.5; numeric: yes -->

- name: unit_polar
  inputs:
    hx: 0
    hy: 0
    hz: 1
  expected: 1

### position_velocity_dot

<!-- family: flight; symbols: x, vx, y, vy, z, vz; expr: x*vx + y*vy + z*vz; numeric: yes -->

- name: radial_climb
  inputs:
    x: 0
    vx: 0
    y: 0
    vy: 0
    z: 3
    vz: 4
  expected: 12

### inclination

<!-- family: flight; symbols: pi, hz, h; expr: pi/2 - asin(hz/h); numeric: yes -->

- name: equatorial
  inputs:
    pi: pi
    hz: 1
    h: 1
  expected: 0

- name: polar
  inputs:
    pi: pi
    hz: 0
    h: 1
  expected: pi/2

- name: retrograde_equatorial
  inputs:
    pi: pi
    hz: -1
    h: 1
  expected: pi

### ascending_node_sine

<!-- family: flight; symbols: hx, hy; expr: hx/(hx**2 + hy**2)**0.5; numeric: yes -->

- name: quarter_turn
  inputs:
    hx: 1
    hy: 0
  expected: 1

- name: third_quadrant
  inputs:
    hx: -1
    hy: 1
  expected: -(1/2)**0.5

### ascending_node_cosine

<!-- family: flight; symbols: hy, hx; expr: -hy/(hx**2 + hy**2)**0.5; numeric: yes -->

- name: on_plus_x
  inputs:
    hy: -1
    hx: 0
  expected: 1

- name: third_quadrant
  inputs:
    hy: 1
    hx: -1
  expected: -(1/2)**0.5

### true_anomaly_cosine_from_state

<!-- family: flight; symbols: h, r, mu, e; expr: (h**2/r - mu)/(mu*e); numeric: yes -->

- name: periapsis
  inputs:
    h: 12**0.5
    r: 2
    mu: 4
    e: 1/2
  expected: 1

- name: past_quadrant
  inputs:
    h: 4/5
    r: 1
    mu: 1
    e: 3/5
  expected: -3/5

### true_anomaly_tangent_from_state

<!-- family: flight; symbols: h, rdv, mu, r; expr: (h*rdv)/(h**2 - mu*r); numeric: yes -->

- name: periapsis
  inputs:
    h: 12**0.5
    rdv: 0
    mu: 4
    r: 2
  expected: 0

- name: eccentric_quadrant
  inputs:
    h: 4/5
    rdv: 3/5
    mu: 1
    r: 1
  expected: -4/3

### argument_of_latitude_cosine

<!-- family: flight; symbols: x, Omega, y, r; expr: (x*cos(Omega) + y*sin(Omega))/r; numeric: yes -->

- name: at_the_node
  inputs:
    x: 2
    Omega: 0
    y: 0
    r: 2
  expected: 1

### argument_of_latitude_sine

<!-- family: flight; symbols: z, r, i; expr: z/(r*sin(i)); numeric: yes -->

- name: polar_quarter
  inputs:
    z: 2
    r: 2
    i: pi/2
  expected: 1

### equatorial_argument_cosine

<!-- family: flight; symbols: x, r; expr: x/r; numeric: yes -->

- name: on_plus_y
  inputs:
    x: 0
    r: 3
  expected: 0

### equatorial_argument_sine

<!-- family: flight; symbols: y, r; expr: y/r; numeric: yes -->

- name: on_plus_y
  inputs:
    y: 3
    r: 3
  expected: 1

### argument_of_periapsis

<!-- family: flight; symbols: u, nu; expr: u - nu; numeric: yes -->

- name: difference
  inputs:
    u: 1
    nu: 1/4
  expected: 3/4

### perifocal_x_true

<!-- family: flight; symbols: r, nu; expr: r*cos(nu); numeric: yes -->

- name: periapsis
  inputs:
    r: 2
    nu: 0
  expected: 2

- name: quarter_turn
  inputs:
    r: 2
    nu: pi/2
  expected: 0

### perifocal_y_true

<!-- family: flight; symbols: r, nu; expr: r*sin(nu); numeric: yes -->

- name: periapsis
  inputs:
    r: 2
    nu: 0
  expected: 0

- name: quarter_turn
  inputs:
    r: 2
    nu: pi/2
  expected: 2

### node_frame_x

<!-- family: flight; symbols: r, omega, nu; expr: r*cos(omega + nu); numeric: yes -->

- name: periapsis_at_quarter
  inputs:
    r: 2
    omega: pi/2
    nu: 0
  expected: 0

### node_frame_y

<!-- family: flight; symbols: r, omega, nu; expr: r*sin(omega + nu); numeric: yes -->

- name: periapsis_at_quarter
  inputs:
    r: 2
    omega: pi/2
    nu: 0
  expected: 2

### inertial_position_x

<!-- family: flight; symbols: r, Omega, u, i; expr: r*(cos(Omega)*cos(u) - sin(Omega)*cos(i)*sin(u)); numeric: yes -->

- name: on_plus_x
  inputs:
    r: 5
    Omega: 0
    u: 0
    i: 0
  expected: 5

- name: node_on_y
  inputs:
    r: 3
    Omega: pi/2
    u: 0
    i: pi/2
  expected: 0

### inertial_position_y

<!-- family: flight; symbols: r, Omega, u, i; expr: r*(sin(Omega)*cos(u) + cos(Omega)*cos(i)*sin(u)); numeric: yes -->

- name: on_plus_x
  inputs:
    r: 5
    Omega: 0
    u: 0
    i: 0
  expected: 0

- name: node_on_y
  inputs:
    r: 3
    Omega: pi/2
    u: 0
    i: pi/2
  expected: 3

### inertial_position_z

<!-- family: flight; symbols: r, i, u; expr: r*sin(i)*sin(u); numeric: yes -->

- name: polar_quarter
  inputs:
    r: 2
    i: pi/2
    u: pi/2
  expected: 2

### radial_velocity_eccentric

<!-- family: flight; symbols: mu, a, e, E, r; expr: ((mu*a)**0.5)*e*sin(E)/r; numeric: yes -->

- name: eccentric_quadrant
  inputs:
    mu: 1
    a: 1
    e: 3/5
    E: pi/2
    r: 1
  expected: 3/5

### transverse_velocity_eccentric

<!-- family: flight; symbols: mu, a, e, r; expr: ((mu*a)**0.5)*((1 - e**2)**0.5)/r; numeric: yes -->

- name: matches_h_over_r
  inputs:
    mu: 1
    a: 1
    e: 3/5
    r: 1
  expected: 4/5

### radial_velocity

<!-- family: flight; symbols: v, gamma; expr: v*sin(gamma); numeric: yes -->

- name: horizontal
  inputs:
    v: 2
    gamma: 0
  expected: 0

- name: vertical
  inputs:
    v: 2
    gamma: pi/2
  expected: 2

### transverse_velocity

<!-- family: flight; symbols: v, gamma; expr: v*cos(gamma); numeric: yes -->

- name: horizontal
  inputs:
    v: 2
    gamma: 0
  expected: 2

### specific_angular_momentum_flight_path

<!-- family: flight; symbols: r, v, gamma; expr: r*v*cos(gamma); numeric: yes -->

- name: horizontal
  inputs:
    r: 3
    v: 2
    gamma: 0
  expected: 6

### inertial_velocity_x

<!-- family: flight; symbols: Vr, r, x, Vp, Omega, u, i; expr: (Vr/r)*x - Vp*(cos(Omega)*sin(u) + sin(Omega)*cos(i)*cos(u)); numeric: yes -->

- name: horizontal_at_periapsis
  inputs:
    Vr: 0
    r: 2
    x: 2
    Vp: 2
    Omega: 0
    u: 0
    i: 0
  expected: 0

### inertial_velocity_y

<!-- family: flight; symbols: Vr, r, y, Vp, Omega, u, i; expr: (Vr/r)*y + Vp*(-sin(Omega)*sin(u) + cos(Omega)*cos(i)*cos(u)); numeric: yes -->

- name: horizontal_at_periapsis
  inputs:
    Vr: 0
    r: 2
    y: 0
    Vp: 2
    Omega: 0
    u: 0
    i: 0
  expected: 2

### inertial_velocity_z

<!-- family: flight; symbols: Vr, r, z, Vp, i, u; expr: (Vr/r)*z + Vp*sin(i)*cos(u); numeric: yes -->

- name: equatorial
  inputs:
    Vr: 0
    r: 2
    z: 0
    Vp: 2
    i: 0
    u: 0
  expected: 0

### mean_anomaly_from_epoch

<!-- family: flight; symbols: M0, n, t, t0; expr: M0 + n*(t - t0); numeric: yes -->

- name: two_seconds
  inputs:
    M0: 0
    n: 1
    t: 2
    t0: 0
  expected: 2

- name: shifted_epoch
  inputs:
    M0: 1
    n: 2
    t: 3
    t0: 1
  expected: 5

### greenwich_angle

<!-- family: flight; symbols: theta0, omega_e, t, t0; expr: theta0 + omega_e*(t - t0); numeric: yes -->

- name: quarter_turn
  inputs:
    theta0: 0
    omega_e: 1
    t: pi/2
    t0: 0
  expected: pi/2

- name: from_epoch
  inputs:
    theta0: 1
    omega_e: 2
    t: 3
    t0: 1
  expected: 5

### earth_fixed_x

<!-- family: flight; symbols: x, y, theta; expr: x*cos(theta) + y*sin(theta); numeric: yes -->

- name: no_rotation
  inputs:
    x: 3
    y: 4
    theta: 0
  expected: 3

- name: quarter_turn
  inputs:
    x: 0
    y: 2
    theta: pi/2
  expected: 2

### earth_fixed_y

<!-- family: flight; symbols: x, y, theta; expr: -x*sin(theta) + y*cos(theta); numeric: yes -->

- name: no_rotation
  inputs:
    x: 3
    y: 4
    theta: 0
  expected: 4

- name: quarter_turn
  inputs:
    x: 2
    y: 0
    theta: pi/2
  expected: -2

### earth_fixed_z

<!-- family: flight; symbols: z; expr: z; numeric: yes -->

- name: polar_component
  inputs:
    z: 5
  expected: 5

### geocentric_latitude_sine

<!-- family: flight; symbols: z, r; expr: z/r; numeric: yes -->

- name: forty_five
  inputs:
    z: 1
    r: 2**0.5
  expected: 1/2**0.5

### geocentric_latitude_cosine

<!-- family: flight; symbols: rho, r; expr: rho/r; numeric: yes -->

- name: forty_five
  inputs:
    rho: 1
    r: 2**0.5
  expected: 1/2**0.5

### geocentric_latitude_tangent

<!-- family: flight; symbols: z, rho; expr: z/rho; numeric: yes -->

- name: forty_five
  inputs:
    z: 3
    rho: 3
  expected: 1

### longitude_sine

<!-- family: flight; symbols: y, rho; expr: y/rho; numeric: yes -->

- name: on_plus_y
  inputs:
    y: 4
    rho: 4
  expected: 1

### longitude_cosine

<!-- family: flight; symbols: x, rho; expr: x/rho; numeric: yes -->

- name: on_plus_y
  inputs:
    x: 0
    rho: 4
  expected: 0

### flattening_from_radii

<!-- family: flight; symbols: ae, b; expr: (ae - b)/ae; numeric: yes -->

- name: half
  inputs:
    ae: 2
    b: 1
  expected: 1/2

### polar_radius_from_flattening

<!-- family: flight; symbols: ae, f; expr: ae*(1 - f); numeric: yes -->

- name: half
  inputs:
    ae: 2
    f: 1/2
  expected: 1

### ellipsoid_eccentricity_squared

<!-- family: flight; symbols: f; expr: f*(2 - f); numeric: yes -->

- name: half
  inputs:
    f: 1/2
  expected: 3/4

### geodetic_latitude_tangent_surface

<!-- family: flight; symbols: phic, f; expr: tan(phic)/(1 - f)**2; numeric: yes -->

- name: sphere
  inputs:
    phic: pi/4
    f: 0
  expected: 1

- name: flatten_half
  inputs:
    phic: pi/4
    f: 1/2
  expected: 4

### geodetic_latitude_from_geocentric

<!-- family: flight; symbols: phic, f, ae, r; expr: phic + f*(ae/r)*sin(2*phic) + f**2*((ae/r)**2 - ae/(4*r))*sin(4*phic); numeric: yes -->

- name: sphere
  inputs:
    phic: pi/6
    f: 0
    ae: 1
    r: 1
  expected: pi/6

- name: equator
  inputs:
    phic: 0
    f: 1/100
    ae: 1
    r: 1
  expected: 0

- name: forty_five_surface
  inputs:
    phic: pi/4
    f: 1/100
    ae: 1
    r: 1
  expected: pi/4 + 1/100

#### rocket

### mixture_ratio

<!-- family: rocket; symbols: mdot_o, mdot_f; expr: mdot_o/mdot_f; numeric: yes -->

- name: oxidizer_six_to_one
  inputs:
    mdot_o: 12
    mdot_f: 2
  expected: 6

### propellant_flow_sum

<!-- family: rocket; symbols: mdot_o, mdot_f; expr: mdot_o + mdot_f; numeric: yes -->

- name: same_split
  inputs:
    mdot_o: 12
    mdot_f: 2
  expected: 14

### fuel_flow

<!-- family: rocket; symbols: mdot, r; expr: mdot/(r + 1); numeric: yes -->

- name: same_split
  inputs:
    mdot: 14
    r: 6
  expected: 2

### oxidizer_flow

<!-- family: rocket; symbols: r, mdot; expr: r*mdot/(r + 1); numeric: yes -->

- name: same_split
  inputs:
    r: 6
    mdot: 14
  expected: 12

### average_propellant_density

<!-- family: rocket; symbols: rho_o, rho_f, r; expr: rho_o*rho_f*(r + 1)/(r*rho_f + rho_o); numeric: yes -->

- name: mass_ratio_three
  inputs:
    rho_o: 1000
    rho_f: 200
    r: 3
  expected: 500

### characteristic_length

<!-- family: rocket; symbols: Vc, At; expr: Vc/At; numeric: yes -->

- name: definition
  inputs:
    Vc: 3/1000
    At: 1/500
  expected: 3/2

### solid_mass_flow

<!-- family: rocket; symbols: Ab, r, rho_b; expr: Ab*r*rho_b; numeric: yes -->

- name: steady_regression
  inputs:
    Ab: 1/5
    r: 1/200
    rho_b: 1800
  expected: 9/5

### burning_rate

<!-- family: rocket; symbols: a, p1, n; expr: a*p1**n; numeric: yes -->

- name: square_root_pressure
  inputs:
    a: 1/100000
    p1: 4000000
    n: 1/2
  expected: 1/50

### burning_area_ratio

<!-- family: rocket; symbols: Ab, At; expr: Ab/At; numeric: yes -->

- name: ratio_200
  inputs:
    Ab: 2/5
    At: 1/500
  expected: 200

### equilibrium_chamber_pressure

<!-- family: rocket; symbols: K, a, rho_b, cstar, n; expr: (K*a*rho_b*cstar)**(1/(1 - n)); numeric: yes -->

- name: square_root_pressure
  inputs:
    K: 200
    a: 1/100000
    rho_b: 1800
    cstar: 5000/9
    n: 1/2
  expected: 4000000

### burn_rate_temperature_sensitivity

<!-- family: rocket; symbols: r, Tb; expr: (1/r)*partial(r, Tb); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is an unevaluated derivative of burning rate with respect to propellant temperature. -->

### pressure_temperature_sensitivity

<!-- family: rocket; symbols: p1, p, Tb; expr: (1/p1)*partial(p, Tb); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is an unevaluated derivative of chamber pressure with respect to propellant temperature. -->

### circular_port_burning_area

<!-- family: rocket; symbols: r, L, pi; expr: 2*pi*r*L; numeric: yes -->

- name: unit_cylinder
  inputs:
    r: 1
    L: 1
    pi: pi
  expected: 2*pi

### circular_port_radius

<!-- family: rocket; symbols: Ab, L, pi; expr: Ab/(2*pi*L); numeric: yes -->

- name: unit_cylinder
  inputs:
    Ab: 2*pi
    L: 1
    pi: pi
  expected: 1

### circular_grain_length

<!-- family: rocket; symbols: Ab, r, pi; expr: Ab/(2*pi*r); numeric: yes -->

- name: unit_cylinder
  inputs:
    Ab: 2*pi
    r: 1
    pi: pi
  expected: 1

### initial_web

<!-- family: rocket; symbols: Ro, Rp; expr: Ro - Rp; numeric: yes -->

- name: two_centimetres
  inputs:
    Ro: 1/20
    Rp: 3/100
  expected: 1/50

### remaining_web

<!-- family: rocket; symbols: Ro, r; expr: Ro - r; numeric: yes -->

- name: one_centimetre
  inputs:
    Ro: 1/20
    r: 2/50
  expected: 1/100

### circular_port_from_remaining_web

<!-- family: rocket; symbols: Ro, wrem; expr: Ro - wrem; numeric: yes -->

- name: one_centimetre
  inputs:
    Ro: 1/20
    wrem: 1/100
  expected: 2/50

### circular_grain_volume

<!-- family: rocket; symbols: Ro, Rp, L, pi; expr: pi*(Ro**2 - Rp**2)*L; numeric: yes -->

- name: unit_tube
  inputs:
    Ro: 2
    Rp: 1
    L: 1
    pi: pi
  expected: 3*pi

### circular_remaining_volume

<!-- family: rocket; symbols: Ro, r, L, pi; expr: pi*(Ro**2 - r**2)*L; numeric: yes -->

- name: half_web
  inputs:
    Ro: 2
    r: 2**0.5
    L: 1
    pi: pi
  expected: 2*pi

### sliver_volume_fraction

<!-- family: rocket; symbols: Vsliver, V0; expr: Vsliver/V0; numeric: yes -->

- name: five_percent
  inputs:
    Vsliver: 1
    V0: 20
  expected: 1/20

### sliver_port_radius

<!-- family: rocket; symbols: Ro, s, Rp; expr: (Ro**2 - s*(Ro**2 - Rp**2))**0.5; numeric: yes -->

- name: no_sliver
  inputs:
    Ro: 5
    s: 0
    Rp: 3
  expected: 5

- name: all_sliver
  inputs:
    Ro: 5
    s: 1
    Rp: 3
  expected: 3

### remaining_web_time

<!-- family: rocket; symbols: wrem, w0, rburn; expr: integral(wrem, w0, 1/rburn); numeric: yes (definite integral) -->

- name: constant_rate
  inputs:
    wrem: 1/100
    w0: 1/20
    rburn: 1/50
  expected: 2

## Aerodynamics

#### aerodynamics

### bernoulli

<!-- family: aerodynamics; symbols: p, rho, V, g, z; expr: p + 0.5*rho*V**2 + rho*g*z; numeric: yes -->

- name: all_three_terms
  inputs:
    p: 100000
    rho: 6/5
    V: 30
    g: 10
    z: 5
  expected: 100600

### freestream_dynamic_pressure

<!-- family: aerodynamics; symbols: rho_inf, V_inf; expr: 0.5*rho_inf*V_inf**2; numeric: yes -->

- name: definition
  inputs:
    rho_inf: 5/4
    V_inf: 40
  expected: 1000

### lift_coefficient

<!-- family: aerodynamics; symbols: L, q_inf, S; expr: L/(q_inf*S); numeric: yes -->

- name: steady_load
  inputs:
    L: 16000
    q_inf: 4000
    S: 20
  expected: 1/5

### drag_coefficient

<!-- family: aerodynamics; symbols: D, q_inf, S; expr: D/(q_inf*S); numeric: yes -->

- name: steady_load
  inputs:
    D: 2400
    q_inf: 4000
    S: 20
  expected: 3/100

### normal_force_coefficient

<!-- family: aerodynamics; symbols: N, q_inf, S; expr: N/(q_inf*S); numeric: yes -->

- name: steady_load
  inputs:
    N: 10000
    q_inf: 4000
    S: 20
  expected: 1/8

### axial_force_coefficient

<!-- family: aerodynamics; symbols: A, q_inf, S; expr: A/(q_inf*S); numeric: yes -->

- name: steady_load
  inputs:
    A: 800
    q_inf: 4000
    S: 20
  expected: 1/100

### moment_coefficient

<!-- family: aerodynamics; symbols: M, q_inf, S, l; expr: M/(q_inf*S*l); numeric: yes -->

- name: steady_load
  inputs:
    M: 2000
    q_inf: 4000
    S: 20
    l: 2
  expected: 1/80

### section_lift_coefficient

<!-- family: aerodynamics; symbols: Lp, q_inf, c; expr: Lp/(q_inf*c); numeric: yes -->

- name: per_unit_span
  inputs:
    Lp: 1500
    q_inf: 5000
    c: 1/2
  expected: 3/5

### section_drag_coefficient

<!-- family: aerodynamics; symbols: Dp, q_inf, c; expr: Dp/(q_inf*c); numeric: yes -->

- name: per_unit_span
  inputs:
    Dp: 50
    q_inf: 5000
    c: 1/2
  expected: 1/50

### section_moment_coefficient

<!-- family: aerodynamics; symbols: Mp, q_inf, c; expr: Mp/(q_inf*c**2); numeric: yes -->

- name: per_unit_span
  inputs:
    Mp: 30
    q_inf: 5000
    c: 1/2
  expected: 3/125

### pressure_coefficient

<!-- family: aerodynamics; symbols: p, p_inf, q_inf; expr: (p - p_inf)/q_inf; numeric: yes -->

- name: incompressible_stagnation
  inputs:
    p: 105000
    p_inf: 100000
    q_inf: 5000
  expected: 1

- name: freestream
  inputs:
    p: 100000
    p_inf: 100000
    q_inf: 5000
  expected: 0

### pressure_coefficient_from_mach

<!-- family: aerodynamics; symbols: p, p_inf, g, M; expr: 2*(p/p_inf - 1)/(g*M**2); numeric: yes -->

- name: freestream
  inputs:
    p: 100000
    p_inf: 100000
    g: 7/5
    M: 2
  expected: 0

- name: unit_dynamic_pressure
  inputs:
    p: 380000
    p_inf: 100000
    g: 7/5
    M: 2
  expected: 1

### prandtl_glauert_factor

<!-- family: aerodynamics; symbols: M; expr: (1 - M**2)**0.5; numeric: yes -->

- name: incompressible
  inputs:
    M: 0
  expected: 1

- name: three_fifths
  inputs:
    M: 3/5
  expected: 4/5

### prandtl_glauert_coefficient

<!-- family: aerodynamics; symbols: C0, M; expr: C0/(1 - M**2)**0.5; numeric: yes -->

- name: incompressible
  inputs:
    C0: -2/5
    M: 0
  expected: -2/5

- name: three_fifths
  inputs:
    C0: -2/5
    M: 3/5
  expected: -1/2

### critical_pressure_coefficient

<!-- family: aerodynamics; symbols: g, M; expr: 2*(((2/(g + 1))*(1 + ((g - 1)/2)*M**2))**(g/(g - 1)) - 1)/(g*M**2); numeric: yes -->

- name: sonic_freestream
  inputs:
    g: 7/5
    M: 1
  expected: 0

- name: air_half
  inputs:
    g: 7/5
    M: 1/2
  expected: (40/7)*((7/8)**(7/2) - 1)

### critical_mach

<!-- family: aerodynamics; symbols: C0, M, g; expr: C0/(1 - M**2)**0.5 - 2*(((2/(g + 1))*(1 + ((g - 1)/2)*M**2))**(g/(g - 1)) - 1)/(g*M**2); numeric: yes -->

- name: air_half
  inputs:
    C0: (40/7)*((7/8)**(7/2) - 1)*(3/4)**0.5
    M: 1/2
    g: 7/5
  expected: 0

- name: air_four_fifths
  inputs:
    C0: (125/56)*((47/50)**(7/2) - 1)*(3/5)
    M: 4/5
    g: 7/5
  expected: 0

### skin_friction_coefficient

<!-- family: aerodynamics; symbols: tau, q_inf; expr: tau/q_inf; numeric: yes -->

- name: wall_shear
  inputs:
    tau: 10
    q_inf: 5000
  expected: 1/500

### section_normal_coefficient

<!-- family: aerodynamics; symbols: c, Cpl, Cpu, cfu, dydx_u, cfl, dydx_l; expr: (1/c)*(integral(0, c, Cpl - Cpu) + integral(0, c, cfu*dydx_u + cfl*dydx_l)); numeric: yes (definite integral) -->

- name: uniform_distributions
  inputs:
    c: 2
    Cpl: 4/5
    Cpu: -1/5
    cfu: 1/100
    dydx_u: 1/10
    cfl: 1/50
    dydx_l: -1/10
  expected: 999/1000

### section_axial_coefficient

<!-- family: aerodynamics; symbols: c, Cpu, dydx_u, Cpl, dydx_l, cfu, cfl; expr: (1/c)*(integral(0, c, Cpu*dydx_u - Cpl*dydx_l) + integral(0, c, cfu + cfl)); numeric: yes (definite integral) -->

- name: uniform_distributions
  inputs:
    c: 2
    Cpu: -1/5
    dydx_u: 1/10
    Cpl: 4/5
    dydx_l: -1/10
    cfu: 1/100
    cfl: 1/50
  expected: 9/100

### leading_edge_moment_coefficient

<!-- family: aerodynamics; symbols: c, Cpu, Cpl, x, cfu, dydx_u, cfl, dydx_l, yu, yl; expr: (1/c**2)*(integral(0, c, (Cpu - Cpl)*x) - integral(0, c, (cfu*dydx_u + cfl*dydx_l)*x) + integral(0, c, (Cpu*dydx_u + cfu)*yu) + integral(0, c, (-Cpl*dydx_l + cfl)*yl)); numeric: yes (definite integral) -->

- name: uniform_distributions
  vary: x
  inputs:
    c: 2
    Cpu: -1/2
    Cpl: 1/2
    cfu: 1/50
    dydx_u: 1/5
    cfl: 1/25
    dydx_l: -1/5
    yu: 1/10
    yl: -1/10
  expected: -509/1000

### section_lift_from_normal

<!-- family: aerodynamics; symbols: cn, ca, alpha; expr: cn*cos(alpha) - ca*sin(alpha); numeric: yes -->

- name: thirty_degrees
  inputs:
    cn: 4/5
    ca: 1/10
    alpha: pi/6
  expected: (2/5)*(3**0.5) - 1/20

### section_drag_from_normal

<!-- family: aerodynamics; symbols: cn, ca, alpha; expr: cn*sin(alpha) + ca*cos(alpha); numeric: yes -->

- name: thirty_degrees
  inputs:
    cn: 4/5
    ca: 1/10
    alpha: pi/6
  expected: 2/5 + (3**0.5)/20

### center_of_pressure

<!-- family: aerodynamics; symbols: M_LE, Np; expr: -M_LE/Np; numeric: yes -->

- name: nose_down_moment
  inputs:
    M_LE: -40
    Np: 100
  expected: 2/5

### lift_force

<!-- family: aerodynamics; symbols: CL, q_inf, S; expr: CL*q_inf*S; numeric: yes -->

- name: steady_load
  inputs:
    CL: 1/5
    q_inf: 4000
    S: 20
  expected: 16000

### drag_force

<!-- family: aerodynamics; symbols: CD, q_inf, S; expr: CD*q_inf*S; numeric: yes -->

- name: steady_load
  inputs:
    CD: 3/100
    q_inf: 4000
    S: 20
  expected: 2400

### aspect_ratio

<!-- family: aerodynamics; symbols: b, S; expr: b**2/S; numeric: yes -->

- name: span_ten
  inputs:
    b: 10
    S: 20
  expected: 5

### rectangular_aspect_ratio

<!-- family: aerodynamics; symbols: b, c; expr: b/c; numeric: yes -->

- name: span_ten
  inputs:
    b: 10
    c: 2
  expected: 5

### taper_ratio

<!-- family: aerodynamics; symbols: ct, cr; expr: ct/cr; numeric: yes -->

- name: half
  inputs:
    ct: 1
    cr: 2
  expected: 1/2

- name: rectangular
  inputs:
    ct: 2
    cr: 2
  expected: 1

- name: pointed
  inputs:
    ct: 0
    cr: 2
  expected: 0

### trapezoidal_wing_area

<!-- family: aerodynamics; symbols: b, cr, ct; expr: b*(cr + ct)/2; numeric: yes -->

- name: taper_half
  inputs:
    b: 10
    cr: 2
    ct: 1
  expected: 15

- name: rectangular
  inputs:
    b: 10
    cr: 2
    ct: 2
  expected: 20

- name: pointed
  inputs:
    b: 10
    cr: 2
    ct: 0
  expected: 10

### mean_aerodynamic_chord

<!-- family: aerodynamics; symbols: cr, lam; expr: (2/3)*cr*(1 + lam + lam**2)/(1 + lam); numeric: yes -->

- name: taper_half
  inputs:
    cr: 2
    lam: 1/2
  expected: 14/9

- name: rectangular
  inputs:
    cr: 2
    lam: 1
  expected: 2

- name: pointed
  inputs:
    cr: 2
    lam: 0
  expected: 4/3

### mac_spanwise_station

<!-- family: aerodynamics; symbols: b, lam; expr: (b/6)*(1 + 2*lam)/(1 + lam); numeric: yes -->

- name: taper_half
  inputs:
    b: 10
    lam: 1/2
  expected: 20/9

- name: rectangular
  inputs:
    b: 10
    lam: 1
  expected: 5/2

- name: pointed
  inputs:
    b: 10
    lam: 0
  expected: 5/3

### chord_fraction_sweep

<!-- family: aerodynamics; symbols: sweep_le, n, lam, AR; expr: atan(tan(sweep_le) - 4*n*(1 - lam)/(AR*(1 + lam))); numeric: yes -->

- name: quarter_unswept_le
  inputs:
    sweep_le: 0
    n: 1/4
    lam: 1/2
    AR: 20/3
  expected: atan(-1/20)

- name: trailing_unswept_le
  inputs:
    sweep_le: 0
    n: 1
    lam: 1/2
    AR: 20/3
  expected: atan(-1/5)

- name: rectangular
  inputs:
    sweep_le: pi/6
    n: 1/4
    lam: 1
    AR: 8
  expected: pi/6

- name: leading_edge
  inputs:
    sweep_le: pi/6
    n: 0
    lam: 1/2
    AR: 6
  expected: pi/6

### leading_edge_from_chord_sweep

<!-- family: aerodynamics; symbols: sweep_n, n, lam, AR; expr: atan(tan(sweep_n) + 4*n*(1 - lam)/(AR*(1 + lam))); numeric: yes -->

- name: from_quarter
  inputs:
    sweep_n: atan(-1/20)
    n: 1/4
    lam: 1/2
    AR: 20/3
  expected: 0

- name: rectangular
  inputs:
    sweep_n: pi/6
    n: 1/4
    lam: 1
    AR: 8
  expected: pi/6

### mac_leading_edge_x

<!-- family: aerodynamics; symbols: y, sweep_le; expr: y*tan(sweep_le); numeric: yes -->

- name: unswept
  inputs:
    y: 20/9
    sweep_le: 0
  expected: 0

- name: forty_five
  inputs:
    y: 2
    sweep_le: pi/4
  expected: 2

### induced_drag_coefficient

<!-- family: aerodynamics; symbols: CL, AR, e, pi; expr: CL**2/(pi*AR*e); numeric: yes -->

- name: elliptic_unit_lift
  inputs:
    CL: 1
    AR: 5
    e: 1
    pi: pi
  expected: 1/(5*pi)

### drag_polar

<!-- family: aerodynamics; symbols: CD0, CDi; expr: CD0 + CDi; numeric: yes -->

- name: two_term
  inputs:
    CD0: 1/50
    CDi: 1/25
  expected: 3/50

### lift_to_drag

<!-- family: aerodynamics; symbols: CL, CD; expr: CL/CD; numeric: yes -->

- name: twenty_to_one
  inputs:
    CL: 1/2
    CD: 1/40
  expected: 20

### lift_to_drag_from_forces

<!-- family: aerodynamics; symbols: L, D; expr: L/D; numeric: yes -->

- name: twenty_to_one
  inputs:
    L: 16000
    D: 800
  expected: 20

### section_lift_effective_angle

<!-- family: aerodynamics; symbols: a0, alpha_s, alpha_i; expr: a0*(alpha_s - alpha_i); numeric: yes -->

- name: two_degrees_above_induced
  inputs:
    a0: 2*pi
    alpha_s: pi/18
    alpha_i: pi/36
  expected: pi**2/18

### elliptic_induced_angle

<!-- family: aerodynamics; symbols: CL, AR, pi; expr: CL/(pi*AR); numeric: yes -->

- name: unit_lift_aspect_five
  inputs:
    CL: 1
    AR: 5
    pi: pi
  expected: 1/(5*pi)

### induced_angle

<!-- family: aerodynamics; symbols: CL, AR, e, pi; expr: CL/(pi*AR*e); numeric: yes -->

- name: elliptic_unit_lift
  inputs:
    CL: 1
    AR: 5
    e: 1
    pi: pi
  expected: 1/(5*pi)

- name: efficiency_four_fifths
  inputs:
    CL: 1
    AR: 5
    e: 4/5
    pi: pi
  expected: 1/(4*pi)

### wing_lift_curve_slope

<!-- family: aerodynamics; symbols: a0, AR, e, pi; expr: a0/(1 + a0/(pi*AR*e)); numeric: yes -->

- name: thin_elliptic_aspect_six
  inputs:
    a0: 2*pi
    AR: 6
    e: 1
    pi: pi
  expected: 3*pi/2

- name: efficiency_four_fifths
  inputs:
    a0: 5
    AR: 8
    e: 4/5
    pi: pi
  expected: 160*pi/(32*pi + 25)

### wing_lift_coefficient

<!-- family: aerodynamics; symbols: a, alpha, alpha_L0; expr: a*(alpha - alpha_L0); numeric: yes -->

- name: five_per_radian
  inputs:
    a: 5
    alpha: 1/10
    alpha_L0: 1/50
  expected: 2/5

### stall_angle

<!-- family: aerodynamics; symbols: alpha_L0, CLmax, a; expr: alpha_L0 + CLmax/a; numeric: yes -->

- name: line_reaches_clmax
  inputs:
    alpha_L0: 1/50
    CLmax: 2/5
    a: 5
  expected: 1/10

### stall_speed

<!-- family: aerodynamics; symbols: W, rho, S, CLmax; expr: (2*W/(rho*S*CLmax))**0.5; numeric: yes -->

- name: one_g_level
  inputs:
    W: 25000
    rho: 5/4
    S: 16
    CLmax: 1
  expected: 50

### equivalent_airspeed

<!-- family: aerodynamics; symbols: V, rho, rho_sl; expr: V*(rho/rho_sl)**0.5; numeric: yes -->

- name: same_dynamic_pressure
  inputs:
    V: 100
    rho: 1/4
    rho_sl: 1
  expected: 50

### load_factor

<!-- family: aerodynamics; symbols: L, W; expr: L/W; numeric: yes -->

- name: three_g
  inputs:
    L: 24000
    W: 8000
  expected: 3

### level_turn_load_factor

<!-- family: aerodynamics; symbols: phi; expr: 1/cos(phi); numeric: yes -->

- name: sixty_degrees
  inputs:
    phi: pi/3
  expected: 2

- name: forty_five_degrees
  inputs:
    phi: pi/4
  expected: 2**0.5

### level_turn_radius

<!-- family: aerodynamics; symbols: V, g, phi; expr: V**2/(g*tan(phi)); numeric: yes -->

- name: forty_five_degree_bank
  inputs:
    V: 10
    g: 10
    phi: pi/4
  expected: 10

- name: sixty_degrees
  inputs:
    V: 30
    g: 10
    phi: pi/3
  expected: 90/(3**0.5)

### level_turn_rate

<!-- family: aerodynamics; symbols: g, phi, V; expr: g*tan(phi)/V; numeric: yes -->

- name: forty_five_degree_bank
  inputs:
    g: 10
    phi: pi/4
    V: 10
  expected: 1

- name: sixty_degrees
  inputs:
    g: 10
    phi: pi/3
    V: 30
  expected: (3**0.5)/3

### useful_thrust

<!-- family: aerodynamics; symbols: P, V; expr: P/V; numeric: yes -->

- name: unit_speed
  inputs:
    P: 20
    V: 10
  expected: 2

### propeller_disk_area

<!-- family: aerodynamics; symbols: pi, D; expr: pi*D**2/4; numeric: yes -->

- name: diameter_two
  inputs:
    pi: pi
    D: 2
  expected: pi

### actuator_disk_speed

<!-- family: aerodynamics; symbols: Ve, V0; expr: 0.5*(Ve + V0); numeric: yes -->

- name: wake_three
  inputs:
    Ve: 3
    V0: 1
  expected: 2

### propeller_induced_velocity

<!-- family: aerodynamics; symbols: Vp, V0; expr: Vp - V0; numeric: yes -->

- name: unit_induced
  inputs:
    Vp: 2
    V0: 1
  expected: 1

### propeller_far_wake_speed

<!-- family: aerodynamics; symbols: V0, vi; expr: V0 + 2*vi; numeric: yes -->

- name: unit_induced
  inputs:
    V0: 1
    vi: 1
  expected: 3

### ideal_propeller_thrust

<!-- family: aerodynamics; symbols: rho, Vp, A, Ve, V0; expr: rho*Vp*A*(Ve - V0); numeric: yes -->

- name: unit_disk
  inputs:
    rho: 2
    Vp: 2
    A: 1
    Ve: 3
    V0: 1
  expected: 8

### ideal_propeller_thrust_bernoulli

<!-- family: aerodynamics; symbols: rho, A, Ve, V0; expr: 0.5*rho*A*(Ve**2 - V0**2); numeric: yes -->

- name: unit_disk
  inputs:
    rho: 2
    A: 1
    Ve: 3
    V0: 1
  expected: 8

### ideal_propeller_thrust_from_induced

<!-- family: aerodynamics; symbols: rho, A, vi, V0; expr: 2*rho*A*vi*(V0 + vi); numeric: yes -->

- name: unit_disk
  inputs:
    rho: 2
    A: 1
    vi: 1
    V0: 1
  expected: 8

### propeller_induced_velocity_from_thrust

<!-- family: aerodynamics; symbols: V0, T, rho, A; expr: 0.5*(-V0 + (V0**2 + 2*T/(rho*A))**0.5); numeric: yes -->

- name: unit_disk
  inputs:
    V0: 1
    T: 8
    rho: 2
    A: 1
  expected: 1

### ideal_actuator_power

<!-- family: aerodynamics; symbols: T, Vp; expr: T*Vp; numeric: yes -->

- name: unit_disk
  inputs:
    T: 8
    Vp: 2
  expected: 16

### ideal_actuator_power_from_induced

<!-- family: aerodynamics; symbols: rho, A, vi, V0; expr: 2*rho*A*vi*(V0 + vi)**2; numeric: yes -->

- name: unit_disk
  inputs:
    rho: 2
    A: 1
    vi: 1
    V0: 1
  expected: 16

### ideal_propulsive_efficiency

<!-- family: aerodynamics; symbols: T, V0, P; expr: T*V0/P; numeric: yes -->

- name: half
  inputs:
    T: 8
    V0: 1
    P: 16
  expected: 1/2

### ideal_propulsive_efficiency_from_speeds

<!-- family: aerodynamics; symbols: V0, Vp; expr: V0/Vp; numeric: yes -->

- name: half
  inputs:
    V0: 1
    Vp: 2
  expected: 1/2

### sustained_turn_load_factor

<!-- family: aerodynamics; symbols: q, S, T, CD0, pi, AR, e, W; expr: ((q*S*(T - q*S*CD0)*pi*AR*e)/(W**2))**0.5; numeric: yes -->

- name: two_g
  inputs:
    q: 4
    S: 1
    T: 2
    CD0: 1/4
    pi: pi
    AR: 1/pi
    e: 1
    W: 1
  expected: 2

### breguet_range_jet

<!-- family: aerodynamics; symbols: V, ct, LD, Wi, Wf; expr: (V/ct)*LD*log(Wi/Wf); numeric: yes -->

- name: weight_ratio_two
  inputs:
    V: 1
    ct: 1
    LD: 1
    Wi: 2
    Wf: 1
  expected: log(2)

### breguet_endurance_jet

<!-- family: aerodynamics; symbols: ct, LD, Wi, Wf; expr: (1/ct)*LD*log(Wi/Wf); numeric: yes -->

- name: weight_ratio_two
  inputs:
    ct: 1
    LD: 1
    Wi: 2
    Wf: 1
  expected: log(2)

### breguet_range_prop

<!-- family: aerodynamics; symbols: eta, c, LD, Wi, Wf; expr: (eta/c)*LD*log(Wi/Wf); numeric: yes -->

- name: weight_ratio_two
  inputs:
    eta: 1
    c: 1
    LD: 1
    Wi: 2
    Wf: 1
  expected: log(2)

### breguet_endurance_prop

<!-- family: aerodynamics; symbols: eta, c, V, LD, Wi, Wf; expr: (eta/(c*V))*LD*log(Wi/Wf); numeric: yes -->

- name: weight_ratio_two
  inputs:
    eta: 1
    c: 1
    V: 2
    LD: 1
    Wi: 2
    Wf: 1
  expected: log(2)/2

### stick_fixed_neutral_point

<!-- family: aerodynamics; symbols: deps, aT, a, qT, q, ST, l, S, c; expr: (1 - deps)*(aT/a)*(qT/q)*(ST*l)/(S*c); numeric: yes -->

- name: sample_tail
  inputs:
    deps: 2/5
    aT: 4
    a: 5
    qT: 9
    q: 10
    ST: 2
    l: 5
    S: 10
    c: 1
  expected: 54/125

- name: equal_slopes
  inputs:
    deps: 0
    aT: 1
    a: 1
    qT: 1
    q: 1
    ST: 1
    l: 4
    S: 8
    c: 2
  expected: 1/4

### center_of_gravity_to_neutral_point

<!-- family: aerodynamics; symbols: x0c, xpc; expr: x0c - xpc; numeric: yes -->

- name: ahead
  inputs:
    x0c: 54/125
    xpc: 1/10
  expected: 83/250

### neutral_distance_from_moment

<!-- family: aerodynamics; symbols: dCm_dCL; expr: -dCm_dCL; numeric: yes -->

- name: five_percent_chord
  inputs:
    dCm_dCL: -1/20
  expected: 1/20

### static_margin

<!-- family: aerodynamics; symbols: xc; expr: 100*xc; numeric: yes -->

- name: five_percent
  inputs:
    xc: 1/20
  expected: 5

### naca4_thickness

<!-- family: aerodynamics; symbols: t, xi; expr: (t/0.2)*(0.2969*xi**0.5 - 0.1260*xi - 0.3516*xi**2 + 0.2843*xi**3 - 0.1015*xi**4); numeric: yes -->

- name: trailing_edge_twenty_percent
  inputs:
    t: 1/5
    xi: 1
  expected: 0.0021

- name: leading_edge
  inputs:
    t: 12/100
    xi: 0
  expected: 0

### naca4_camber_forward

<!-- family: aerodynamics; symbols: m, p, xi; expr: (m/p**2)*(2*p*xi - xi**2); numeric: yes -->

- name: at_maximum
  inputs:
    m: 2/100
    p: 4/10
    xi: 4/10
  expected: 2/100

### naca4_camber_aft

<!-- family: aerodynamics; symbols: m, p, xi; expr: (m/(1-p)**2)*((1 - 2*p) + 2*p*xi - xi**2); numeric: yes -->

- name: at_maximum
  inputs:
    m: 2/100
    p: 4/10
    xi: 4/10
  expected: 2/100

- name: trailing_edge
  inputs:
    m: 4/100
    p: 4/10
    xi: 1
  expected: 0

### naca4_camber_slope_forward

<!-- family: aerodynamics; symbols: m, p, xi; expr: (2*m/p**2)*(p - xi); numeric: yes -->

- name: at_maximum
  inputs:
    m: 2/100
    p: 4/10
    xi: 4/10
  expected: 0

### naca4_camber_slope_aft

<!-- family: aerodynamics; symbols: m, p, xi; expr: (2*m/(1-p)**2)*(p - xi); numeric: yes -->

- name: at_maximum
  inputs:
    m: 2/100
    p: 4/10
    xi: 4/10
  expected: 0

### naca4_upper_x

<!-- family: aerodynamics; symbols: xi, yt, theta; expr: xi - yt*sin(theta); numeric: yes -->

- name: flat_mean
  inputs:
    xi: 3/10
    yt: 1/10
    theta: 0
  expected: 3/10

### naca4_upper_y

<!-- family: aerodynamics; symbols: yc, yt, theta; expr: yc + yt*cos(theta); numeric: yes -->

- name: flat_mean
  inputs:
    yc: 2/100
    yt: 1/10
    theta: 0
  expected: 12/100

### naca4_lower_x

<!-- family: aerodynamics; symbols: xi, yt, theta; expr: xi + yt*sin(theta); numeric: yes -->

- name: flat_mean
  inputs:
    xi: 3/10
    yt: 1/10
    theta: 0
  expected: 3/10

### naca4_lower_y

<!-- family: aerodynamics; symbols: yc, yt, theta; expr: yc - yt*cos(theta); numeric: yes -->

- name: flat_mean
  inputs:
    yc: 2/100
    yt: 1/10
    theta: 0
  expected: -8/100

### naca4_leading_edge_radius

<!-- family: aerodynamics; symbols: t, c; expr: 0.5*(0.2969*t/0.2)**2*c; numeric: yes -->

- name: twenty_percent_unit_chord
  inputs:
    t: 1/5
    c: 1
  expected: 0.5*0.2969**2

### naca4_glauert_station

<!-- family: aerodynamics; symbols: p; expr: 2*atan((p/(1-p))**0.5); numeric: yes -->

- name: mid_chord
  inputs:
    p: 1/2
  expected: pi/2

### naca4_zero_lift_angle

<!-- family: aerodynamics; symbols: m, p, theta_p, pi; expr: (1/pi)*((m/p**2)*((2*p-1-0.5)*theta_p + 2*(p*(1-p))**0.5*(1-(2*p-1)) + (2*p-1)*(p*(1-p))**0.5) + (m/(1-p)**2)*((2*p-1-0.5)*pi - ((2*p-1-0.5)*theta_p + 2*(p*(1-p))**0.5*(1-(2*p-1)) + (2*p-1)*(p*(1-p))**0.5))); numeric: yes -->

- name: circular_arc_two_percent
  inputs:
    m: 1/50
    p: 1/2
    theta_p: pi/2
    pi: pi
  expected: -1/25

### thin_airfoil_section_lift

<!-- family: aerodynamics; symbols: pi, alpha, alpha_L0; expr: 2*pi*(alpha - alpha_L0); numeric: yes -->

- name: at_zero_lift
  inputs:
    pi: pi
    alpha: -1/25
    alpha_L0: -1/25
  expected: 0

- name: symmetric_unit_angle
  inputs:
    pi: pi
    alpha: 1
    alpha_L0: 0
  expected: 2*pi

### naca4_glauert_A1

<!-- family: aerodynamics; symbols: m, p, theta_p, pi; expr: (2/pi)*((m/p**2)*((2*p-1)*(p*(1-p))**0.5 + theta_p/2) + (m/(1-p)**2)*(pi/2 - ((2*p-1)*(p*(1-p))**0.5 + theta_p/2))); numeric: yes -->

- name: circular_arc_two_percent
  inputs:
    m: 1/50
    p: 1/2
    theta_p: pi/2
    pi: pi
  expected: 4/50

### naca4_glauert_A2

<!-- family: aerodynamics; symbols: m, p, pi; expr: (2/pi)*(-2*(2*p-1)**2*(p*(1-p))**0.5 + 2*(p*(1-p))**0.5 - (16/3)*(p*(1-p))**1.5)*(m/p**2 - m/(1-p)**2); numeric: yes -->

- name: circular_arc
  inputs:
    m: 1/50
    p: 1/2
    pi: pi
  expected: 0

### naca4_quarter_chord_moment

<!-- family: aerodynamics; symbols: pi, A2, A1; expr: (pi/4)*(A2 - A1); numeric: yes -->

- name: circular_arc_two_percent
  inputs:
    pi: pi
    A2: 0
    A1: 4/50
  expected: -pi/50

## Structures

#### shell

### cylinder_hoop_stress

<!-- family: shell; symbols: p, R, t; expr: p*R/t; numeric: yes -->

- name: forty_inch_cylinder
  inputs:
    p: 1000
    R: 20
    t: 1/10
  expected: 200000

### weld_radial_mismatch

<!-- family: shell; symbols: p, R, delta, t; expr: 3*p*R*delta/t**2; numeric: yes -->

- name: five_percent_mismatch
  inputs:
    p: 1000
    R: 20
    delta: 1/200
    t: 1/10
  expected: 30000

- name: unit_offset
  inputs:
    p: 1
    R: 1
    delta: 1
    t: 1
  expected: 3

#### design

### margin_of_safety

<!-- family: design; symbols: allowable, design; expr: allowable/design - 1; numeric: yes -->

- name: zero_margin
  inputs:
    allowable: 200000
    design: 200000
  expected: 0

- name: quarter_margin
  inputs:
    allowable: 200000
    design: 160000
  expected: 1/4
