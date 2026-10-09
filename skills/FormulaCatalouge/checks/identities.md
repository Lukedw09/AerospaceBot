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
    v: 2
  expected: 387450

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

### normal_shock_stagnation_pressure

<!-- family: shock; symbols: g, M1; expr: (((g + 1)*M1**2)/((g - 1)*M1**2 + 2))**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1)); numeric: yes -->

- name: air_mach_one
  inputs:
    g: 7/5
    M1: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: (8/3)**(7/2)*(2/9)**(5/2)

### normal_shock_entropy

<!-- family: shock; symbols: R, pt2, pt1; expr: -R*log(pt2/pt1); numeric: yes -->

- name: total_pressure_drop_by_e
  inputs:
    R: 287
    pt2: 1
    pt1: e
  expected: 287

### normal_shock_entropy_over_r

<!-- family: shock; symbols: g, M1; expr: -log((((g + 1)*M1**2)/((g - 1)*M1**2 + 2))**(g/(g - 1))*((g + 1)/(2*g*M1**2 - (g - 1)))**(1/(g - 1))); numeric: yes -->

- name: air_mach_one
  inputs:
    g: 7/5
    M1: 1
  expected: 0

- name: air_mach_two
  inputs:
    g: 7/5
    M1: 2
  expected: -log((8/3)**(7/2)*(2/9)**(5/2))

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

- name: mach_three_air
  inputs:
    g: 7/5
    p2: 31/3
    p1: 1
    rho2: 27/7
    rho1: 1
  expected: 49/15

- name: monatomic_mach_two
  inputs:
    g: 5/3
    p2: 19/4
    p1: 1
    rho2: 16/7
    rho1: 1
  expected: 35/12

### prandtl_relation

<!-- family: shock; symbols: g, M1; expr: (2/(g+1))*(1+((g-1)/2)*M1**2); numeric: yes -->

- name: mach_one
  inputs:
    g: 5/3
    M1: 1
  expected: 1

- name: mach_two_air
  inputs:
    g: 7/5
    M1: 2
  expected: 3/2

- name: monatomic_mach_two
  inputs:
    g: 5/3
    M1: 2
  expected: 7/4

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

- name: off_surface
  inputs:
    g: 7/5
    u: 0
    v: 1/2
    theta: pi/4
  expected: 3/4

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

### fanno_temperature_ratio

<!-- family: duct; symbols: g, M; expr: (g+1)/(2+(g-1)*M**2); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 2/3

### fanno_pressure_ratio

<!-- family: duct; symbols: g, M; expr: (1/M)*((g+1)/(2+(g-1)*M**2))**0.5; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: (1/2)*(2/3)**0.5

### fanno_density_ratio

<!-- family: duct; symbols: g, M; expr: (1/M)*((2+(g-1)*M**2)/(g+1))**0.5; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: (1/2)*(3/2)**0.5

### fanno_velocity_ratio

<!-- family: duct; symbols: g, M; expr: M*((g+1)/(2+(g-1)*M**2))**0.5; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 2*(2/3)**0.5

### fanno_stagnation_pressure_ratio

<!-- family: duct; symbols: g, M; expr: (1/M)*((2+(g-1)*M**2)/(g+1))**((g+1)/(2*(g-1))); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 27/16

### fanno_friction_parameter

<!-- family: duct; symbols: g, M; expr: (1-M**2)/(g*M**2)+((g+1)/(2*g))*log(((g+1)*M**2)/(2+(g-1)*M**2)); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 0

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: -15/28+(6/7)*log(8/3)

### rayleigh_stagnation_temperature_ratio

<!-- family: duct; symbols: g, M; expr: 2*(g+1)*M**2*(1+((g-1)/2)*M**2)/(1+g*M**2)**2; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 96/121

### rayleigh_temperature_ratio

<!-- family: duct; symbols: g, M; expr: (g+1)**2*M**2/(1+g*M**2)**2; numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 64/121

### rayleigh_pressure_ratio

<!-- family: duct; symbols: g, M; expr: (g+1)/(1+g*M**2); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 4/11

### rayleigh_density_ratio

<!-- family: duct; symbols: g, M; expr: (1+g*M**2)/((g+1)*M**2); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 11/16

### rayleigh_stagnation_pressure_ratio

<!-- family: duct; symbols: g, M; expr: ((g+1)/(1+g*M**2))*((2+(g-1)*M**2)/(g+1))**(g/(g-1)); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: (4/11)*(3/2)**(7/2)

### rayleigh_velocity_ratio

<!-- family: duct; symbols: g, M; expr: (g+1)*M**2/(1+g*M**2); numeric: yes -->

- name: sonic
  inputs:
    g: 7/5
    M: 1
  expected: 1

- name: air_mach_two
  inputs:
    g: 7/5
    M: 2
  expected: 16/11

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

- name: exponent_two
  inputs:
    pb: 16
    TMb: 4
    TM: 2
    g0: 2
    M0: 1
    Rstar: 1
    LMb: 1
  expected: 64

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

- name: two_scale_heights
  inputs:
    pb: 1
    g0: 2
    M0: 1
    H: 1
    Hb: 0
    Rstar: 1
    TMb: 1
  expected: exp(-2)

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

- name: exponent_two
  inputs:
    rhob: 1
    TMb: 4
    TM: 2
    g0: 2
    M0: 1
    Rstar: 1
    LMb: 1
  expected: 8

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

- name: two_scale_heights
  inputs:
    rhob: 1
    g0: 2
    M0: 1
    H: 1
    Hb: 0
    Rstar: 1
    TMb: 1
  expected: exp(-2)

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

- name: off_base
  inputs:
    Tc: 10
    A: -4
    Z: 17
    Z8: 5
    a: 20
  expected: 34/5

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

- name: one_e_fold_drop
  inputs:
    pref: 10
    A: 0
    B: 1
    h: log(2)
  expected: 5

### glenn_density

<!-- family: atmosphere; symbols: p, R, T; expr: p/(R*T); numeric: yes -->

- name: glenn_gas
  inputs:
    p: 287
    R: 287
    T: 1
  expected: 1

### molecular_diffusion_coefficient

<!-- family: atmosphere; symbols: a, N, T, b; expr: (a/N)*(T/273.15)**b; numeric: yes -->

- name: reference_temperature
  inputs:
    a: 6.986e20
    N: 1e20
    T: 273.15
    b: 0.75
  expected: 6.986

### species_mass_density

<!-- family: atmosphere; symbols: n, M, NA; expr: n*M/NA; numeric: yes -->

- name: one_kmol_per_cubic_metre
  inputs:
    n: 6.022169e26
    M: 16
    NA: 6.022169e26
  expected: 16

### thermosphere_pressure

<!-- family: atmosphere; symbols: N, kB, T; expr: N*kB*T; numeric: yes -->

- name: unit_density
  inputs:
    N: 1e20
    kB: 1.380622e-23
    T: 200
  expected: 1e20*1.380622e-23*200

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

### payload_ratio

<!-- family: rocket; symbols: md, mp, ms; expr: md/(mp + ms); numeric: yes -->

- name: one_quarter
  inputs:
    md: 2
    mp: 6
    ms: 2
  expected: 1/4

### structural_coefficient

<!-- family: rocket; symbols: ms, mp; expr: ms/(ms + mp); numeric: yes -->

- name: one_quarter
  inputs:
    ms: 2
    mp: 6
  expected: 1/4

### mass_ratio_from_payload_and_structure

<!-- family: rocket; symbols: lam, eps; expr: (1 + lam)/(eps + lam); numeric: yes -->

- name: two_and_a_half
  inputs:
    lam: 1/4
    eps: 1/4
  expected: 5/2

### structure_mass_linear

<!-- family: rocket; symbols: mH, k, mp; expr: mH + k*mp; numeric: yes -->

- name: ten_plus_tenth
  inputs:
    mH: 10
    k: 1/10
    mp: 100
  expected: 20

### leo_design_delta_v

<!-- family: rocket; symbols: vcirc, vrot, Lg, Ld, Ls, dvc, margin; expr: vcirc - vrot + Lg + Ld + Ls + dvc + margin; numeric: yes -->

- name: stacked_budget
  inputs:
    vcirc: 8000
    vrot: 400
    Lg: 1000
    Ld: 100
    Ls: 50
    dvc: 200
    margin: 150
  expected: 9100

### cylinder_shell_mass

<!-- family: rocket; symbols: rho, t, pi, D, L; expr: rho*t*pi*D*L; numeric: yes -->

- name: unit_wall
  inputs:
    rho: 2
    t: 1/10
    pi: pi
    D: 2
    L: 3
  expected: 6/5*pi

### cone_shell_mass

<!-- family: rocket; symbols: rho, t, pi, R, Ln; expr: rho*t*pi*R*(R**2 + Ln**2)**0.5; numeric: yes -->

- name: three_four_five
  inputs:
    rho: 2
    t: 1/10
    pi: pi
    R: 3
    Ln: 4
  expected: 3*pi

### tangent_ogive_shell_mass

<!-- family: rocket; symbols: rho, t, pi, R, Ln; expr: rho*t*2*pi*((R**2 + Ln**2)/(2*R))*(Ln + (R - (R**2 + Ln**2)/(2*R))*asin(Ln/((R**2 + Ln**2)/(2*R)))); numeric: yes -->

- name: hemisphere
  inputs:
    rho: 2
    t: 1/2
    pi: pi
    R: 1
    Ln: 1
  expected: 2*pi

### gravitational_parameter_surface

<!-- family: rocket; symbols: g0, R; expr: g0*R**2; numeric: yes -->

- name: unit_sphere
  inputs:
    g0: 10
    R: 3
  expected: 90

### powered_path_acceleration

<!-- family: rocket; symbols: T, m, D, g, th; expr: T/m - D/m - g*sin(th); numeric: yes -->

- name: vertical_with_drag
  inputs:
    T: 20
    m: 2
    D: 6
    g: 10
    th: pi/2
  expected: -3

### gravity_loss_definition

<!-- family: rocket; symbols: g, th, t; expr: integral(g*sin(th), t); numeric: no (indefinite integral) -->

<!-- No scalar identity: the script is the indefinite integral of g sin theta along the burn. -->

### drag_loss_definition

<!-- family: rocket; symbols: D, m, t; expr: integral(D/m, t); numeric: no (indefinite integral) -->

<!-- No scalar identity: the script is the indefinite integral of drag over mass. -->

### steering_loss_definition

<!-- family: rocket; symbols: T, m, eps, t; expr: integral((T/m)*(1 - cos(eps)), t); numeric: no (indefinite integral) -->

<!-- No scalar identity: the script is the indefinite integral of unused thrust acceleration. -->

### burnout_speed_from_losses

<!-- family: rocket; symbols: c, m0, mf, dvg, dvD, dve; expr: c*log(m0/mf) - dvg - dvD - dve; numeric: yes -->

- name: vacuum_identity
  inputs:
    c: 3000
    m0: e
    mf: 1
    dvg: 100
    dvD: 40
    dve: 10
  expected: 2850

### constant_angle_speed

<!-- family: rocket; symbols: c, m0, m, g, t, th; expr: c*log(m0/m) - g*t*sin(th); numeric: yes -->

- name: vertical_mass_ratio_e
  inputs:
    c: 3000
    m0: e
    m: 1
    g: 10
    t: 20
    th: pi/2
  expected: 2800

### constant_drag_loss

<!-- family: rocket; symbols: D, mdot, m0, m; expr: (D/mdot)*log(m0/m); numeric: yes -->

- name: mass_ratio_e
  inputs:
    D: 50
    mdot: 2
    m0: e
    m: 1
  expected: 25

### constant_angle_speed_const_drag

<!-- family: rocket; symbols: c, m0, m, g, t, th, D, mdot; expr: c*log(m0/m) - g*t*sin(th) - (D/mdot)*log(m0/m); numeric: yes -->

- name: vertical_mass_ratio_e
  inputs:
    c: 3000
    m0: e
    m: 1
    g: 10
    t: 20
    th: pi/2
    D: 50
    mdot: 2
  expected: 2775

### constant_angle_path_length

<!-- family: rocket; symbols: c, m0, mf, mdot, g, tb, th; expr: c*(m0 - mf - mf*log(m0/mf))/mdot - 0.5*g*tb**2*sin(th); numeric: yes -->

- name: no_gravity_halved_mass
  inputs:
    c: 1
    m0: 2
    mf: 1
    mdot: 1
    g: 0
    tb: 1
    th: pi/2
  expected: 1 - log(2)

- name: vertical_with_gravity
  inputs:
    c: 1
    m0: 2
    mf: 1
    mdot: 1
    g: 2
    tb: 1
    th: pi/2
  expected: -log(2)

### powered_radial_velocity

<!-- family: rocket; symbols: V, th; expr: V*sin(th); numeric: yes -->

- name: vertical
  inputs:
    V: 10
    th: pi/2
  expected: 10

- name: thirty_degrees
  inputs:
    V: 10
    th: pi/6
  expected: 5

### powered_horizontal_velocity

<!-- family: rocket; symbols: V, th; expr: V*cos(th); numeric: yes -->

- name: vertical
  inputs:
    V: 10
    th: pi/2
  expected: 0

- name: sixty_degrees
  inputs:
    V: 10
    th: pi/3
  expected: 5

### gravity_turn_angle_rate

<!-- family: rocket; symbols: V, r, g, th; expr: (V/r - g/V)*cos(th); numeric: yes -->

- name: horizontal_flat
  inputs:
    V: 10
    r: 100
    g: 5
    th: 0
  expected: -2/5

- name: sixty_degree_pitch
  inputs:
    V: 10
    r: 100
    g: 5
    th: pi/3
  expected: -1/5

### kick_flight_path_angle

<!-- family: rocket; symbols: pi, alpha; expr: pi/2 - alpha; numeric: yes -->

- name: ten_degree_kick
  inputs:
    pi: pi
    alpha: pi/18
  expected: 4*pi/9

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

### sphere_of_influence_radius

<!-- family: flight; symbols: D, mu2, mu1; expr: D*(mu2/mu1)**(2/5); numeric: yes -->

- name: unit_ratio
  inputs:
    D: 32
    mu2: 1
    mu1: 1
  expected: 32

- name: thirty_two_over_one
  inputs:
    D: 32
    mu2: 1
    mu1: 32
  expected: 8

### sphere_of_influence_radius_from_mass

<!-- family: flight; symbols: D, m2, m1; expr: D*(m2/m1)**(2/5); numeric: yes -->

- name: thirty_two_over_one
  inputs:
    D: 32
    m2: 1
    m1: 32
  expected: 8

### sphere_of_influence_in_central_radii

<!-- family: flight; symbols: rsoi, R0; expr: rsoi/R0; numeric: yes -->

- name: ten_radii
  inputs:
    rsoi: 20
    R0: 2
  expected: 10

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

- name: periapsis_of_hyperbola
  inputs:
    mu: 16
    r: 2
    a: -4
  expected: 20**0.5

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

### j2_nodal_rate

<!-- family: flight; symbols: n, J2, RE, i, a, e; expr: -3*n*J2*RE**2*cos(i)/(2*a**2*(1-e**2)**2); numeric: yes -->

- name: polar
  inputs:
    n: 1
    J2: 1
    RE: 1
    i: pi/2
    a: 1
    e: 0
  expected: 0

- name: equatorial_unit
  inputs:
    n: 1
    J2: 1
    RE: 1
    i: 0
    a: 1
    e: 0
  expected: -3/2

- name: scaled_ellipse
  inputs:
    n: 2
    J2: 1/2
    RE: 2
    i: 0
    a: 2
    e: 1/2
  expected: -8/3

### j2_apsidal_rate

<!-- family: flight; symbols: n, J2, RE, i, a, e; expr: 3*n*J2*RE**2*(4 - 5*sin(i)**2)/(4*a**2*(1-e**2)**2); numeric: yes -->

- name: equatorial_unit
  inputs:
    n: 1
    J2: 1
    RE: 1
    i: 0
    a: 1
    e: 0
  expected: 3

- name: critical
  inputs:
    n: 1
    J2: 1
    RE: 1
    i: asin((4/5)**0.5)
    a: 1
    e: 0
  expected: 0

- name: scaled_equator
  inputs:
    n: 2
    J2: 1/2
    RE: 2
    i: 0
    a: 2
    e: 1/2
  expected: 16/3

### j2_mean_motion

<!-- family: flight; symbols: n0, J2, RE, a, e, i; expr: n0*(1 + 1.5*J2*(RE/a)**2*(1 - e**2)**(-1.5)*(1 - 1.5*sin(i)**2)); numeric: yes -->

- name: equatorial_unit
  inputs:
    n0: 1
    J2: 0.001
    RE: 1
    a: 2
    e: 0
    i: 0
  expected: 1.000375

- name: polar_cancels
  inputs:
    n0: 2
    J2: 0.001
    RE: 2
    a: 2
    e: 0
    i: asin((2/3)**0.5)
  expected: 2

### sun_sync_nodal_rate

<!-- family: flight; symbols: pi, Y; expr: 2*pi/(Y*86400); numeric: yes -->

- name: primer_year
  inputs:
    pi: pi
    Y: 365.2422
  expected: 2*pi/(365.2422*86400)

### sun_sync_inclination_cosine

<!-- family: flight; symbols: Omegadot, a, e, n, J2, RE; expr: -2*Omegadot*a**2*(1-e**2)**2/(3*n*J2*RE**2); numeric: yes -->

- name: minus_one
  inputs:
    Omegadot: 3/2
    a: 1
    e: 0
    n: 1
    J2: 1
    RE: 1
  expected: -1

- name: minus_half
  inputs:
    Omegadot: 3/4
    a: 1
    e: 0
    n: 1
    J2: 1
    RE: 1
  expected: -1/2

- name: scaled_orbit
  inputs:
    Omegadot: 3/2
    a: 2
    e: 0
    n: 2
    J2: 1
    RE: 1
  expected: -2

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

### launch_inclination_cosine

<!-- family: flight; symbols: phi, az; expr: cos(phi)*sin(az); numeric: yes -->

- name: due_east_equator
  inputs:
    phi: 0
    az: pi/2
  expected: 1

### launch_azimuth_sine

<!-- family: flight; symbols: i, phi; expr: cos(i)/cos(phi); numeric: yes -->

- name: equatorial_from_equator
  inputs:
    i: 0
    phi: 0
  expected: 1

### earth_rotation_inertial_speed

<!-- family: flight; symbols: omega, R, phi; expr: omega*R*cos(phi); numeric: yes -->

- name: equator
  inputs:
    omega: 1/10000
    R: 6000000
    phi: 0
  expected: 600

### launch_rotation_assist

<!-- family: flight; symbols: omega, R, phi, az; expr: omega*R*cos(phi)*sin(az); numeric: yes -->

- name: due_east
  inputs:
    omega: 1/10000
    R: 6000000
    phi: 0
    az: pi/2
  expected: 600

### circularization_delta_v

<!-- family: flight; symbols: mu, r, v; expr: (mu/r)**0.5 - v; numeric: yes -->

- name: speed_up_by_one
  inputs:
    mu: 16
    r: 4
    v: 1
  expected: 1

### orbital_period

<!-- family: flight; symbols: a, mu, pi; expr: 2*pi*(a**3/mu)**0.5; numeric: yes -->

- name: unit_orbit
  inputs:
    a: 1
    mu: 1
    pi: pi
  expected: 2*pi

- name: axis_four
  inputs:
    a: 4
    mu: 1
    pi: pi
  expected: 16*pi

### elliptic_half_period

<!-- family: flight; symbols: pi, a, mu; expr: pi*(a**3/mu)**0.5; numeric: yes -->

- name: unit_coast
  inputs:
    pi: pi
    a: 1
    mu: 1
  expected: pi

- name: axis_four
  inputs:
    pi: pi
    a: 4
    mu: 1
  expected: 8*pi

### hohmann_phase_angle

<!-- family: flight; symbols: pi, n2, tof; expr: pi - n2*tof; numeric: yes -->

- name: quarter_coast
  inputs:
    pi: pi
    n2: 1
    tof: pi/2
  expected: pi/2

- name: fast_target
  inputs:
    pi: pi
    n2: 2
    tof: pi
  expected: -pi

### synodic_period

<!-- family: flight; symbols: pi, n1, n2; expr: 2*pi/abs(n1 - n2); numeric: yes -->

- name: twice_and_one
  inputs:
    pi: pi
    n1: 2
    n2: 1
  expected: 2*pi

- name: either_order
  inputs:
    pi: pi
    n1: 1
    n2: 3
  expected: pi

### inclined_excess_speed

<!-- family: flight; symbols: v1, v2, di; expr: (v1**2 + v2**2 - 2*v1*v2*cos(di))**0.5; numeric: yes -->

- name: coplanar_reduction
  inputs:
    v1: 3
    v2: 1
    di: 0
  expected: 2

- name: equal_speed_half_turn
  inputs:
    v1: 1
    v2: 1
    di: pi
  expected: 2

### periapsis_radius

<!-- family: flight; symbols: a, e; expr: a*(1 - e); numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 2

- name: hyperbola
  inputs:
    a: -4
    e: 2
  expected: 4

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

### semimajor_from_apsides

<!-- family: flight; symbols: ra, rp; expr: (ra + rp)/2; numeric: yes -->

- name: two_and_six
  inputs:
    ra: 6
    rp: 2
  expected: 4

### apsis_speed

<!-- family: flight; symbols: mu, rfar, r; expr: (2*mu*rfar/(r*(r + rfar)))**0.5; numeric: yes -->

- name: periapsis_of_ellipse
  inputs:
    mu: 16
    rfar: 6
    r: 2
  expected: 12**0.5

- name: circular
  inputs:
    mu: 16
    rfar: 4
    r: 4
  expected: 2

### semi_latus_rectum

<!-- family: flight; symbols: a, e; expr: a*(1 - e**2); numeric: yes -->

- name: eccentricity_one_half
  inputs:
    a: 4
    e: 1/2
  expected: 3

- name: hyperbola
  inputs:
    a: -4
    e: 2
  expected: 12

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

- name: mu_four
  inputs:
    mu: 4
    a: 1
  expected: 2

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

### hyperbolic_excess_from_energy

<!-- family: flight; symbols: eps; expr: (2*eps)**0.5; numeric: yes -->

- name: unit_energy
  inputs:
    eps: 8
  expected: 4

### hyperbolic_excess_from_axis

<!-- family: flight; symbols: mu, a; expr: (mu*(-1/a))**0.5; numeric: yes -->

- name: unit_hyperbola
  inputs:
    mu: 4
    a: -1
  expected: 2

### characteristic_energy

<!-- family: flight; symbols: vinf; expr: vinf**2; numeric: yes -->

- name: three
  inputs:
    vinf: 3
  expected: 9

### semimajor_from_characteristic_energy

<!-- family: flight; symbols: mu, C3; expr: -mu/C3; numeric: yes -->

- name: unit_hyperbola
  inputs:
    mu: 4
    C3: 4
  expected: -1

### energy_radius_from_excess

<!-- family: flight; symbols: mu, vinf; expr: mu/vinf**2; numeric: yes -->

- name: unit_hyperbola
  inputs:
    mu: 4
    vinf: 2
  expected: 1

### hyperbolic_eccentricity_from_periapsis

<!-- family: flight; symbols: rp, vinf, mu; expr: 1 + rp*vinf**2/mu; numeric: yes -->

- name: unit_hyperbola
  inputs:
    rp: 1
    vinf: 1
    mu: 1
  expected: 2

### hyperbola_asymptote_true_anomaly

<!-- family: flight; symbols: e; expr: acos(-1/e); numeric: yes -->

- name: eccentricity_two
  inputs:
    e: 2
  expected: 2*pi/3

### hyperbola_turning_angle

<!-- family: flight; symbols: e; expr: 2*asin(1/e); numeric: yes -->

- name: eccentricity_two
  inputs:
    e: 2
  expected: pi/3

### specific_angular_momentum_x

<!-- family: flight; symbols: y, vz, z, vy; expr: y*vz - z*vy; numeric: yes -->

- name: along_x
  inputs:
    y: 1
    vz: 1
    z: 0
    vy: 0
  expected: 1

- name: both_components
  inputs:
    y: 2
    vz: 3
    z: 4
    vy: 5
  expected: -14

### specific_angular_momentum_y

<!-- family: flight; symbols: z, vx, x, vz; expr: z*vx - x*vz; numeric: yes -->

- name: zero_for_xy_motion
  inputs:
    z: 0
    vx: 0
    x: 1
    vz: 0
  expected: 0

- name: both_components
  inputs:
    z: 2
    vx: 3
    x: 4
    vz: 5
  expected: -14

### specific_angular_momentum_z

<!-- family: flight; symbols: x, vy, y, vx; expr: x*vy - y*vx; numeric: yes -->

- name: unit_xy
  inputs:
    x: 1
    vy: 1
    y: 0
    vx: 0
  expected: 1

- name: both_components
  inputs:
    x: 2
    vy: 3
    y: 4
    vx: 5
  expected: -14

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

- name: all_axes
  inputs:
    x: 1
    vx: 2
    y: 3
    vy: 4
    z: 5
    vz: 6
  expected: 44

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

- name: sixty_degree_true_anomaly
  inputs:
    h: 12**0.5
    rdv: 6/5
    mu: 4
    r: 12/5
  expected: 3**0.5

### argument_of_latitude_cosine

<!-- family: flight; symbols: x, Omega, y, r; expr: (x*cos(Omega) + y*sin(Omega))/r; numeric: yes -->

- name: at_the_node
  inputs:
    x: 2
    Omega: 0
    y: 0
    r: 2
  expected: 1

- name: node_on_y
  inputs:
    x: 3
    Omega: pi/2
    y: 4
    r: 5
  expected: 4/5

### argument_of_latitude_sine

<!-- family: flight; symbols: z, r, i; expr: z/(r*sin(i)); numeric: yes -->

- name: polar_quarter
  inputs:
    z: 2
    r: 2
    i: pi/2
  expected: 1

- name: thirty_degree_inclination
  inputs:
    z: 1
    r: 2
    i: pi/6
  expected: 1

### equatorial_argument_cosine

<!-- family: flight; symbols: x, r; expr: x/r; numeric: yes -->

- name: on_plus_y
  inputs:
    x: 0
    r: 3
  expected: 0

- name: forty_five
  inputs:
    x: 1
    r: 2**0.5
  expected: 1/2**0.5

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

- name: periapsis_on_x
  inputs:
    r: 2
    omega: 0
    nu: 0
  expected: 2

### node_frame_y

<!-- family: flight; symbols: r, omega, nu; expr: r*sin(omega + nu); numeric: yes -->

- name: periapsis_at_quarter
  inputs:
    r: 2
    omega: pi/2
    nu: 0
  expected: 2

- name: thirty_degrees
  inputs:
    r: 2
    omega: pi/6
    nu: 0
  expected: 1

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

- name: thirty_degree_inclination
  inputs:
    r: 2
    i: pi/6
    u: pi/2
  expected: 1

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

- name: sixty_degrees
  inputs:
    v: 2
    gamma: pi/3
  expected: 1

### specific_angular_momentum_flight_path

<!-- family: flight; symbols: r, v, gamma; expr: r*v*cos(gamma); numeric: yes -->

- name: horizontal
  inputs:
    r: 3
    v: 2
    gamma: 0
  expected: 6

- name: sixty_degrees
  inputs:
    r: 3
    v: 2
    gamma: pi/3
  expected: 3

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

- name: radial_and_transverse
  inputs:
    Vr: 4
    r: 2
    x: 2
    Vp: 3
    Omega: 0
    u: pi/2
    i: 0
  expected: 1

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

- name: sixty_degree_inclination
  inputs:
    Vr: 0
    r: 2
    y: 0
    Vp: 2
    Omega: 0
    u: 0
    i: pi/3
  expected: 1

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

- name: polar_radial_and_transverse
  inputs:
    Vr: 3
    r: 2
    z: 2
    Vp: 4
    i: pi/2
    u: 0
  expected: 7

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

- name: forty_five
  inputs:
    x: 1
    rho: 2**0.5
  expected: 1/2**0.5

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

- name: thirty_degrees_second_order
  inputs:
    phic: pi/6
    f: 1/10
    ae: 1
    r: 2
  expected: pi/6 + 41*(3**0.5)/1600

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

### injector_orifice_mass_flow

<!-- family: rocket; symbols: Cd, A, rho, dp; expr: Cd*A*(2*rho*dp)**0.5; numeric: yes -->

- name: round_trip
  inputs:
    Cd: 3/4
    A: 1/10000
    rho: 1000
    dp: 3200000/9
  expected: 2

### injector_orifice_area

<!-- family: rocket; symbols: mdot, Cd, rho, dp; expr: mdot/(Cd*(2*rho*dp)**0.5); numeric: yes -->

- name: round_trip
  inputs:
    mdot: 2
    Cd: 3/4
    rho: 1000
    dp: 3200000/9
  expected: 1/10000

### injector_jet_velocity

<!-- family: rocket; symbols: mdot, rho, A; expr: mdot/(rho*A); numeric: yes -->

- name: twenty
  inputs:
    mdot: 2
    rho: 1000
    A: 1/10000
  expected: 20

### injector_pressure_drop

<!-- family: rocket; symbols: mdot, Cd, A, rho; expr: (mdot/(Cd*A))**2/(2*rho); numeric: yes -->

- name: round_trip
  inputs:
    mdot: 2
    Cd: 3/4
    A: 1/10000
    rho: 1000
  expected: 3200000/9

### circular_orifice_diameter

<!-- family: rocket; symbols: A, N, pi; expr: (4*A/(N*pi))**0.5; numeric: yes -->

- name: four_holes
  inputs:
    A: 1/10000
    N: 4
    pi: pi
  expected: (1/10000/pi)**0.5

### injector_manifold_pressure

<!-- family: rocket; symbols: pc, dp_inj; expr: pc + dp_inj; numeric: yes -->

- name: chamber_plus_drop
  inputs:
    pc: 2000000
    dp_inj: 200000
  expected: 2200000

### feed_supply_pressure

<!-- family: rocket; symbols: pc, dp_inj, dp_extra, rho, g, h; expr: pc + dp_inj + dp_extra + rho*g*h; numeric: yes -->

- name: two_metre_lift
  inputs:
    pc: 2000000
    dp_inj: 200000
    dp_extra: 50000
    rho: 1000
    g: 9.80665
    h: 2
  expected: 2250000 + 19613.3

### pump_volume_flow

<!-- family: rocket; symbols: mdot, rho; expr: mdot/rho; numeric: yes -->

- name: two_kg_s
  inputs:
    mdot: 2
    rho: 1000
  expected: 1/500

### pump_hydraulic_power

<!-- family: rocket; symbols: mdot, dp, rho; expr: mdot*dp/rho; numeric: yes -->

- name: four_hundred_watts
  inputs:
    mdot: 2
    dp: 200000
    rho: 1000
  expected: 400

### pump_shaft_power

<!-- family: rocket; symbols: mdot, dp, rho, eta; expr: mdot*dp/(rho*eta); numeric: yes -->

- name: seventy_percent
  inputs:
    mdot: 2
    dp: 200000
    rho: 1000
    eta: 7/10
  expected: 4000/7

### pump_drive_power

<!-- family: rocket; symbols: mdot, dp, rho, eta, eta_drive; expr: mdot*dp/(rho*eta*eta_drive); numeric: yes -->

- name: pump_and_drive
  inputs:
    mdot: 2
    dp: 200000
    rho: 1000
    eta: 7/10
    eta_drive: 4/5
  expected: 5000/7

### bartz_gas_side_coefficient

<!-- family: rocket; symbols: Dt, mu, cp, Pr, pc, cstar, R, area_ratio, sigma; expr: 0.026016775834104906*Dt**(-0.2)*mu**0.2*cp*Pr**(-0.6)*(pc/cstar)**0.8*(Dt/R)**0.1*area_ratio**0.9*sigma; numeric: yes -->

- name: sp125_a1_throat
  inputs:
    Dt: 0.63246
    mu: 7.464630340944881e-05
    cp: 1128.11
    Pr: 0.816
    pc: 6894757.29316836
    cstar: 1725.168
    R: 0.297434
    area_ratio: 1
    sigma: 1
  expected: 4457.590750448887
  rel: 1e-9

### gas_side_heat_flux

<!-- family: rocket; symbols: hg, recovery, Tc, Tw; expr: hg*(recovery*Tc - Tw); numeric: yes -->

- name: stated_wall
  inputs:
    hg: 1000
    recovery: 9/10
    Tc: 3000
    Tw: 500
  expected: 2200000

### sp125_prandtl

<!-- family: rocket; symbols: gamma; expr: 4*gamma/(9*gamma - 5); numeric: yes -->

- name: gamma_1_222
  inputs:
    gamma: 1.222
  expected: 4*1.222/(9*1.222 - 5)

### sp125_specific_heat

<!-- family: rocket; symbols: gamma, M; expr: (gamma/(gamma - 1))*4616.123393316195/M; numeric: yes -->

- name: lox_rp1_sample
  inputs:
    gamma: 1.222
    M: 22.5
  expected: (1.222/(1.222 - 1))*4616.123393316195/22.5

### sp125_viscosity

<!-- family: rocket; symbols: M, T; expr: 1.1840810853327972e-07*M**0.5*T**0.6; numeric: yes -->

- name: sample_6140_R
  inputs:
    M: 22.5
    T: 6140*5/9
  expected: 1.1840810853327972e-07*(22.5)**0.5*(6140*5/9)**0.6

### coolant_heat_rate

<!-- family: rocket; symbols: mdot, cp, Tout, Tin; expr: mdot*cp*(Tout - Tin); numeric: yes -->

- name: hundred_kelvin
  inputs:
    mdot: 2
    cp: 2000
    Tout: 400
    Tin: 300
  expected: 400000

### coolant_outlet_temperature

<!-- family: rocket; symbols: Tin, Q, mdot, cp; expr: Tin + Q/(mdot*cp); numeric: yes -->

- name: hundred_kelvin
  inputs:
    Tin: 300
    Q: 400000
    mdot: 2
    cp: 2000
  expected: 400

### coolant_capacity

<!-- family: rocket; symbols: mdot, cp, Tmax, Tin; expr: mdot*cp*(Tmax - Tin); numeric: yes -->

- name: one_hundred_fifty
  inputs:
    mdot: 2
    cp: 2000
    Tmax: 450
    Tin: 300
  expected: 600000

### coolant_min_flow

<!-- family: rocket; symbols: Q, cp, Tmax, Tin; expr: Q/(cp*(Tmax - Tin)); numeric: yes -->

- name: hold_450
  inputs:
    Q: 400000
    cp: 2000
    Tmax: 450
    Tin: 300
  expected: 4/3

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

### vacuum_propellant_mass

<!-- family: rocket; symbols: mf, dv, c; expr: mf*(exp(dv/c) - 1); numeric: yes -->

- name: mass_ratio_e
  inputs:
    mf: 10
    dv: 100
    c: 100
  expected: 10*(e - 1)

### vacuum_wet_mass

<!-- family: rocket; symbols: mf, dv, c; expr: mf*exp(dv/c); numeric: yes -->

- name: mass_ratio_e
  inputs:
    mf: 10
    dv: 100
    c: 100
  expected: 10*e

### electric_propulsion_burn_time

<!-- family: rocket; symbols: mp, ve, T; expr: mp*ve/T; numeric: yes -->

- name: two_kilograms
  inputs:
    mp: 2
    ve: 10
    T: 4
  expected: 5

### electric_propulsion_power

<!-- family: rocket; symbols: T, ve, eta; expr: T*ve/(2*eta); numeric: yes -->

- name: half_efficient
  inputs:
    T: 2
    ve: 10
    eta: 0.5
  expected: 20

### hall_beam_current

<!-- family: rocket; symbols: mdot, qe, m_ion, eta_u; expr: eta_u*mdot*qe/m_ion; numeric: yes -->

- name: xenon_unit_flow
  inputs:
    mdot: 2.18e-25
    qe: 1.602176634e-19
    m_ion: 2.18e-25
    eta_u: 1
  expected: 1.602176634e-19

- name: half_utilization
  inputs:
    mdot: 2
    qe: 3
    m_ion: 4
    eta_u: 0.5
  expected: 0.75

### electric_propulsion_specific_power

<!-- family: rocket; symbols: P, m0; expr: P/m0; numeric: yes -->

- name: ten_watts
  inputs:
    P: 10
    m0: 2
  expected: 5

### phasing_wait_catch

<!-- family: flight; symbols: pi, N, phi, n; expr: (2*pi*N - phi)/n; numeric: yes -->

- name: quarter_revolution
  inputs:
    pi: pi
    N: 1
    phi: pi/2
    n: 1
  expected: 3*pi/2

### phasing_wait_loiter

<!-- family: flight; symbols: pi, N, phi, n; expr: (2*pi*N + phi)/n; numeric: yes -->

- name: quarter_revolution
  inputs:
    pi: pi
    N: 1
    phi: pi/2
    n: 1
  expected: 5*pi/2

### phasing_semimajor_from_period

<!-- family: flight; symbols: mu, T, pi; expr: (mu*(T/(2*pi))**2)**(1/3); numeric: yes -->

- name: unit_orbit
  inputs:
    mu: 1
    T: 2*pi
    pi: pi
  expected: 1

### phasing_delta_v

<!-- family: flight; symbols: vc, ve; expr: abs(vc - ve); numeric: yes -->

- name: two_metres_per_second
  inputs:
    vc: 3
    ve: 1
  expected: 2

### clohessy_wiltshire_radial

<!-- family: flight; symbols: n, t, z0, zd0, xd0; expr: (4 - 3*cos(n*t))*z0 + sin(n*t)/n*zd0 + 2*(1 - cos(n*t))/n*xd0; numeric: yes -->

- name: along_track_rate_coupling
  inputs:
    n: 1
    t: pi/2
    z0: 0
    zd0: 0
    xd0: 2
  expected: 4

### clohessy_wiltshire_along_track

<!-- family: flight; symbols: n, t, z0, x0, zd0, xd0; expr: 6*(sin(n*t) - n*t)*z0 + x0 + 2*(cos(n*t) - 1)/n*zd0 + (4*sin(n*t) - 3*n*t)/n*xd0; numeric: yes -->

- name: radial_offset_quarter_period
  inputs:
    n: 1
    t: pi/2
    z0: 1
    x0: 0
    zd0: 0
    xd0: 0
  expected: 6*(1 - pi/2)

### clohessy_wiltshire_hold_rate

<!-- family: flight; symbols: n, z; expr: -2*n*z; numeric: yes -->

- name: outward_offset
  inputs:
    n: 1
    z: 2
  expected: -4

### pressurant_blowdown_pressure

<!-- family: rocket; symbols: p0, V0, V2, n; expr: p0*(V0/V2)**n; numeric: yes -->

- name: isothermal_half
  inputs:
    p0: 2e6
    V0: 1
    V2: 2
    n: 1
  expected: 1e6

### pressurant_mass

<!-- family: rocket; symbols: p, V, R, T; expr: p*V/(R*T); numeric: yes -->

- name: unit_mass
  inputs:
    p: 300
    V: 2
    R: 3
    T: 200
  expected: 1

### eccentricity_removal_impulse

<!-- family: flight; symbols: v, e; expr: 2*v*e; numeric: yes -->

- name: two_burns
  inputs:
    v: 3000
    e: 0.001
  expected: 6

### elevation_mask_earth_angle

<!-- family: flight; symbols: pi, eps, R, h; expr: pi/2 - eps - asin((R/(R+h))*cos(eps)); numeric: yes -->

- name: horizon_half
  inputs:
    pi: pi
    eps: 0
    R: 2
    h: 2
  expected: pi/3

### swath_arc

<!-- family: flight; symbols: R, lam; expr: 2*R*lam; numeric: yes -->

- name: twice_footprint
  inputs:
    R: 2
    lam: pi/3
  expected: 4*pi/3

### footprint_radius

<!-- family: flight; symbols: R, lam; expr: R*lam; numeric: yes -->

- name: one_radian
  inputs:
    R: 6374200
    lam: 0.1
  expected: 637420

### lambert_chord

<!-- family: flight; symbols: x1, y1, z1, x2, y2, z2; expr: ((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)**0.5; numeric: yes -->

- name: unit_axes
  inputs:
    x1: 1
    y1: 0
    z1: 0
    x2: 0
    y2: 1
    z2: 0
  expected: 2**0.5

### lambert_transfer_cosine

<!-- family: flight; symbols: x1, y1, z1, x2, y2, z2, r1, r2; expr: (x1*x2+y1*y2+z1*z2)/(r1*r2); numeric: yes -->

- name: perpendicular
  inputs:
    x1: 1
    y1: 0
    z1: 0
    x2: 0
    y2: 1
    z2: 0
    r1: 1
    r2: 1
  expected: 0

### lambert_semiperimeter

<!-- family: flight; symbols: r1, r2, c; expr: (r1+r2+c)/2; numeric: yes -->

- name: unit_chord
  inputs:
    r1: 1
    r2: 1
    c: 2**0.5
  expected: 1+2**0.5/2

### lambert_geometric_parameter

<!-- family: flight; symbols: dth, r1, r2; expr: sin(dth)*((r1*r2)/(1-cos(dth)))**0.5; numeric: yes -->

- name: quarter_turn
  inputs:
    dth: pi/2
    r1: 1
    r2: 1
  expected: 1

### stumpff_c_elliptic

<!-- family: flight; symbols: z; expr: (1-cos(z**0.5))/z; numeric: yes -->

- name: half_turn
  inputs:
    z: pi**2
  expected: 2/pi**2

### stumpff_s_elliptic

<!-- family: flight; symbols: z; expr: (z**0.5-sin(z**0.5))/z**1.5; numeric: yes -->

- name: half_turn
  inputs:
    z: pi**2
  expected: 1/pi**2

### stumpff_c_hyperbolic

<!-- family: flight; symbols: z; expr: (((exp((-z)**0.5)+exp(-((-z)**0.5)))/2)-1)/(-z); numeric: yes -->

- name: unit
  inputs:
    z: -1
  expected: (exp(1)+exp(-1))/2-1

### stumpff_s_hyperbolic

<!-- family: flight; symbols: z; expr: (((exp((-z)**0.5)-exp(-((-z)**0.5)))/2)-(-z)**0.5)/((-z)**1.5); numeric: yes -->

- name: unit
  inputs:
    z: -1
  expected: (exp(1)-exp(-1))/2-1

### lambert_y_parameter

<!-- family: flight; symbols: r1, r2, A, z, S, C; expr: r1+r2+A*(z*S-1)/C**0.5; numeric: yes -->

- name: cancels
  inputs:
    r1: 1
    r2: 1
    A: 1
    z: pi**2
    S: 1/pi**2
    C: 2/pi**2
  expected: 2

### lambert_time_of_flight

<!-- family: flight; symbols: y, C, S, A, mu; expr: ((y/C)**1.5*S+A*y**0.5)/mu**0.5; numeric: yes -->

- name: unit_mu
  inputs:
    y: 2
    C: 2/pi**2
    S: 1/pi**2
    A: 1
    mu: 1
  expected: pi+2**0.5

### lambert_tof_residual

<!-- family: flight; symbols: y, C, S, A, mu, tof; expr: ((y/C)**1.5*S+A*y**0.5)/mu**0.5-tof; numeric: yes -->

- name: matched
  inputs:
    y: 2
    C: 2/pi**2
    S: 1/pi**2
    A: 1
    mu: 1
    tof: pi+2**0.5
  expected: 0

### lagrange_f

<!-- family: flight; symbols: y, r1; expr: 1-y/r1; numeric: yes -->

- name: twice_radius
  inputs:
    y: 2
    r1: 1
  expected: -1

### lagrange_g

<!-- family: flight; symbols: A, y, mu; expr: A*(y/mu)**0.5; numeric: yes -->

- name: unit
  inputs:
    A: 1
    y: 2
    mu: 1
  expected: 2**0.5

### lagrange_gdot

<!-- family: flight; symbols: y, r2; expr: 1-y/r2; numeric: yes -->

- name: twice_radius
  inputs:
    y: 2
    r2: 1
  expected: -1

### lambert_velocity_from_lagrange

<!-- family: flight; symbols: r2c, f, r1c, g; expr: (r2c-f*r1c)/g; numeric: yes -->

- name: unit
  inputs:
    r2c: 0
    f: -1
    r1c: 1
    g: 2**0.5
  expected: 2**(-0.5)

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

- name: off_design_three_fifths
  inputs:
    C0: -2/5
    M: 3/5
    g: 7/5
  expected: -1/2 - (250/63)*((67/75)**(7/2) - 1)

### skin_friction_coefficient

<!-- family: aerodynamics; symbols: tau, q_inf; expr: tau/q_inf; numeric: yes -->

- name: wall_shear
  inputs:
    tau: 10
    q_inf: 5000
  expected: 1/500

### blasius_local_skin_friction

<!-- family: aerodynamics; symbols: Re; expr: 0.664/Re**0.5; numeric: yes -->

- name: ten_thousand
  inputs:
    Re: 10000
  expected: 0.664/100

### blasius_plate_friction

<!-- family: aerodynamics; symbols: Re; expr: 1.328/Re**0.5; numeric: yes -->

- name: ten_thousand
  inputs:
    Re: 10000
  expected: 1.328/100

### blasius_thickness_ratio

<!-- family: aerodynamics; symbols: Re; expr: 5/Re**0.5; numeric: yes -->

- name: one_hundred
  inputs:
    Re: 100
  expected: 1/2

### turbulent_plate_friction_seventh

<!-- family: aerodynamics; symbols: Re; expr: 0.074/Re**0.2; numeric: yes -->

- name: one_hundred_thousand
  inputs:
    Re: 100000
  expected: 0.074/10

### turbulent_local_skin_friction_seventh

<!-- family: aerodynamics; symbols: Re; expr: 0.0592/Re**0.2; numeric: yes -->

- name: one_hundred_thousand
  inputs:
    Re: 100000
  expected: 0.0592/10

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

- name: squared_lift_and_efficiency
  inputs:
    CL: 2
    AR: 5
    e: 4/5
    pi: pi
  expected: 1/pi

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

### max_lift_to_drag

<!-- family: aerodynamics; symbols: pi, AR, e, CD0; expr: 0.5*(pi*AR*e/CD0)**0.5; numeric: yes -->

- name: elliptic_aspect_eight
  inputs:
    pi: pi
    AR: 8
    e: 1
    CD0: 1/50
  expected: 10*pi**0.5

- name: efficiency_two
  inputs:
    pi: pi
    AR: 2
    e: 2
    CD0: 1
  expected: pi**0.5

### glide_angle

<!-- family: aerodynamics; symbols: D, L; expr: atan(D/L); numeric: yes -->

- name: forty_five_degrees
  inputs:
    D: 1
    L: 1
  expected: pi/4

- name: thirty_degrees
  inputs:
    D: 1
    L: 3**0.5
  expected: pi/6

### glide_angle_from_coefficients

<!-- family: aerodynamics; symbols: CD, CL; expr: atan(CD/CL); numeric: yes -->

- name: forty_five_degrees
  inputs:
    CD: 1/20
    CL: 1/20
  expected: pi/4

- name: thirty_degrees
  inputs:
    CD: 1
    CL: 3**0.5
  expected: pi/6

### glide_lift

<!-- family: aerodynamics; symbols: W, a; expr: W*cos(a); numeric: yes -->

- name: sixty_degrees
  inputs:
    W: 2
    a: pi/3
  expected: 1

### glide_drag

<!-- family: aerodynamics; symbols: W, a; expr: W*sin(a); numeric: yes -->

- name: thirty_degrees
  inputs:
    W: 2
    a: pi/6
  expected: 1

### glide_speed

<!-- family: aerodynamics; symbols: W, a, rho, S, CL; expr: (2*W*cos(a)/(rho*S*CL))**0.5; numeric: yes -->

- name: level_limit
  inputs:
    W: 25000
    a: 0
    rho: 5/4
    S: 16
    CL: 1
  expected: 50

- name: sixty_degree_glide
  inputs:
    W: 25000
    a: pi/3
    rho: 5/4
    S: 16
    CL: 1
  expected: 25*(2**0.5)

### sink_rate

<!-- family: aerodynamics; symbols: V, a; expr: V*sin(a); numeric: yes -->

- name: thirty_degrees
  inputs:
    V: 10
    a: pi/6
  expected: 5

### glide_range

<!-- family: aerodynamics; symbols: h, a; expr: h/tan(a); numeric: yes -->

- name: forty_five_degrees
  inputs:
    h: 10
    a: pi/4
  expected: 10

### glide_range_from_ld

<!-- family: aerodynamics; symbols: h, LD; expr: h*LD; numeric: yes -->

- name: twenty_to_one
  inputs:
    h: 10
    LD: 20
  expected: 200

### rate_of_climb

<!-- family: aerodynamics; symbols: T, D, V, W; expr: (T-D)*V/W; numeric: yes -->

- name: two_metres
  inputs:
    T: 2000
    D: 1000
    V: 20
    W: 10000
  expected: 2

### rate_of_climb_from_power

<!-- family: aerodynamics; symbols: P, D, V, W; expr: (P - D*V)/W; numeric: yes -->

- name: two_metres
  inputs:
    P: 40000
    D: 1000
    V: 20
    W: 10000
  expected: 2

### climb_angle

<!-- family: aerodynamics; symbols: T, D, W; expr: asin((T-D)/W); numeric: yes -->

- name: thirty_degrees
  inputs:
    T: 6000
    D: 1000
    W: 10000
  expected: pi/6

### climb_angle_from_rate

<!-- family: aerodynamics; symbols: roc, V; expr: asin(roc/V); numeric: yes -->

- name: thirty_degrees
  inputs:
    roc: 5
    V: 10
  expected: pi/6

### service_ceiling_rate

<!-- family: aerodynamics; symbols: n, ft_to_m, min_to_s; expr: n*ft_to_m/min_to_s; numeric: yes -->

- name: hundred_fpm
  inputs:
    n: 100
    ft_to_m: 0.3048
    min_to_s: 60
  expected: 0.508

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

- name: twice_lift
  inputs:
    CL: 2
    AR: 4
    pi: pi
  expected: 1/(2*pi)

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

- name: twice_lift
  inputs:
    CL: 2
    AR: 5
    e: 1
    pi: pi
  expected: 2/(5*pi)

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

- name: clmax_four
  inputs:
    W: 25000
    rho: 5/4
    S: 16
    CLmax: 4
  expected: 25

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

### wheel_normal_force

<!-- family: aerodynamics; symbols: W, L; expr: W - L; numeric: yes -->

- name: half_weight
  inputs:
    W: 10000
    L: 4000
  expected: 6000

### rolling_friction

<!-- family: aerodynamics; symbols: mu, N; expr: mu*N; numeric: yes -->

- name: two_percent
  inputs:
    mu: 1/50
    N: 10000
  expected: 200

### ground_roll_net_force

<!-- family: aerodynamics; symbols: T, D, mu, W, L; expr: T - D - mu*(W - L); numeric: yes -->

- name: static_start
  inputs:
    T: 2500
    D: 0
    mu: 1/50
    W: 10000
    L: 0
  expected: 2300

### ground_roll_acceleration

<!-- family: aerodynamics; symbols: g, F, W; expr: g*F/W; numeric: yes -->

- name: tenth_g
  inputs:
    g: 10
    F: 1000
    W: 10000
  expected: 1

### liftoff_speed

<!-- family: aerodynamics; symbols: kLO, Vs; expr: kLO*Vs; numeric: yes -->

- name: twelve_tenths
  inputs:
    kLO: 6/5
    Vs: 50
  expected: 60

### ground_roll_A

<!-- family: aerodynamics; symbols: g, T, W, mu; expr: g*(T/W - mu); numeric: yes -->

- name: static_accel
  inputs:
    g: 10
    T: 3000
    W: 10000
    mu: 1/50
  expected: 2.8

### ground_roll_B

<!-- family: aerodynamics; symbols: g, rho, S, CD, mu, CL, W; expr: g*rho*S*(CD - mu*CL)/(2*W); numeric: yes -->

- name: unit_polar
  inputs:
    g: 10
    rho: 1
    S: 20
    CD: 1/10
    mu: 1/50
    CL: 1
    W: 10000
  expected: 8/10000

### ground_roll_distance

<!-- family: aerodynamics; symbols: B, A, V; expr: (1/(2*B))*log(A/(A - B*V**2)); numeric: yes -->

- name: log_four_thirds
  inputs:
    B: 1
    A: 4
    V: 1
  expected: 0.5*log(4/3)

### ground_roll_time

<!-- family: aerodynamics; symbols: A, B, V; expr: (1/(2*(A*B)**0.5))*log((A**0.5 + V*B**0.5)/(A**0.5 - V*B**0.5)); numeric: yes -->

- name: artanh_half
  inputs:
    A: 4
    B: 1
    V: 1
  expected: 0.25*log(3)

### touchdown_speed

<!-- family: aerodynamics; symbols: kTD, Vs; expr: kTD*Vs; numeric: yes -->

- name: thirteen_tenths
  inputs:
    kTD: 13/10
    Vs: 50
  expected: 65

### landing_ground_roll_distance

<!-- family: aerodynamics; symbols: B, A, V; expr: (1/(2*B))*log((A - B*V**2)/A); numeric: yes -->

- name: log_five_fourths
  inputs:
    B: 1
    A: -4
    V: 1
  expected: 0.5*log(5/4)

- name: log_four_thirds
  inputs:
    B: -1
    A: -4
    V: 1
  expected: 0.5*log(4/3)

### landing_ground_roll_time

<!-- family: aerodynamics; symbols: A, B, V; expr: (1/(2*((-A)*(-B))**0.5))*log(((-A)**0.5 + V*(-B)**0.5)/((-A)**0.5 - V*(-B)**0.5)); numeric: yes -->

- name: artanh_half
  inputs:
    A: -4
    B: -1
    V: 1
  expected: 0.25*log(3)

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

### isentropic_compressor_temperature_ratio

<!-- family: aerodynamics; symbols: pi_c, g; expr: pi_c**((g - 1)/g); numeric: yes -->

- name: air_two
  inputs:
    pi_c: 2**(7/2)
    g: 7/5
  expected: 2

### ideal_compressor_work

<!-- family: aerodynamics; symbols: cp, Tt2, tau_c; expr: cp*Tt2*(tau_c - 1); numeric: yes -->

- name: unit_rise
  inputs:
    cp: 1000
    Tt2: 300
    tau_c: 2
  expected: 300000

### ideal_turbine_temperature_ratio

<!-- family: aerodynamics; symbols: Tt2, Tt4, tau_c; expr: 1 - (Tt2/Tt4)*(tau_c - 1); numeric: yes -->

- name: half_drop
  inputs:
    Tt2: 300
    Tt4: 1200
    tau_c: 3
  expected: 1/2

### ideal_turbine_pressure_ratio

<!-- family: aerodynamics; symbols: tau_t, g; expr: tau_t**(g/(g - 1)); numeric: yes -->

- name: air_half
  inputs:
    tau_t: 1/2
    g: 7/5
  expected: (1/2)**(7/2)

### burner_fuel_air_ratio

<!-- family: aerodynamics; symbols: cp, Tt4, Tt3, Q; expr: cp*(Tt4 - Tt3)/(Q - cp*Tt4); numeric: yes -->

- name: unit_delta
  inputs:
    cp: 1000
    Tt4: 1200
    Tt3: 600
    Q: 42000000
  expected: 600000/(42000000 - 1200000)

### ideal_turbojet_nozzle_pressure_ratio

<!-- family: aerodynamics; symbols: pt0, p0, pi_c, pi_t; expr: (pt0/p0)*pi_c*pi_t; numeric: yes -->

- name: product
  inputs:
    pt0: 2
    p0: 1
    pi_c: 8
    pi_t: 1/4
  expected: 4

### ideal_nozzle_exit_velocity

<!-- family: aerodynamics; symbols: cp, Tt, NPR, g; expr: (2*cp*Tt*(1 - NPR**(-(g - 1)/g)))**0.5; numeric: yes -->

- name: air_npr_sixteen
  inputs:
    cp: 1004.5
    Tt: 600
    NPR: 16
    g: 7/5
  expected: (2*1004.5*600*(1 - 16**(-2/7)))**0.5

### ideal_nozzle_exit_temperature

<!-- family: aerodynamics; symbols: Tt, NPR, g; expr: Tt*NPR**(-(g - 1)/g); numeric: yes -->

- name: air_half
  inputs:
    Tt: 800
    NPR: 2**(7/2)
    g: 7/5
  expected: 400

### turbojet_specific_thrust

<!-- family: aerodynamics; symbols: f, Ve, V0; expr: (1 + f)*Ve - V0; numeric: yes -->

- name: unit_fuel
  inputs:
    f: 0
    Ve: 800
    V0: 200
  expected: 600

- name: with_fuel
  inputs:
    f: 1/50
    Ve: 1000
    V0: 250
  expected: (51/50)*1000 - 250

### turbojet_tsfc

<!-- family: aerodynamics; symbols: f, Fs; expr: f/Fs; numeric: yes -->

- name: reciprocal
  inputs:
    f: 0.02
    Fs: 500
  expected: 0.00004

### turbojet_thermal_efficiency

<!-- family: aerodynamics; symbols: f, Ve, V0, Q; expr: ((1 + f)*Ve**2 - V0**2)/(2*f*Q); numeric: yes -->

- name: static_point
  inputs:
    f: 0.02
    Ve: 1000
    V0: 0
    Q: 4e7
  expected: (1.02*1000**2)/(2*0.02*4e7)

### turbojet_propulsive_efficiency

<!-- family: aerodynamics; symbols: V0, Fs, f, Ve; expr: 2*V0*Fs/((1 + f)*Ve**2 - V0**2); numeric: yes -->

- name: classic_half
  inputs:
    V0: 250
    Fs: 500
    f: 0
    Ve: 750
  expected: 1/2

### turbojet_overall_efficiency

<!-- family: aerodynamics; symbols: Fs, V0, f, Q; expr: Fs*V0/(f*Q); numeric: yes -->

- name: product_path
  inputs:
    Fs: 500
    V0: 250
    f: 0.02
    Q: 4e7
  expected: 500*250/(0.02*4e7)

### ideal_brayton_thermal_efficiency

<!-- family: aerodynamics; symbols: tau_r, tau_c; expr: 1 - 1/(tau_r*tau_c); numeric: yes -->

- name: double
  inputs:
    tau_r: 1
    tau_c: 2
  expected: 1/2

### ideal_ramjet_nozzle_pressure_ratio

<!-- family: aerodynamics; symbols: pt2, p0; expr: pt2/p0; numeric: yes -->

- name: ram_four
  inputs:
    pt2: 4
    p0: 1
  expected: 4

### ideal_ramjet_brayton_thermal_efficiency

<!-- family: aerodynamics; symbols: tau_r; expr: 1 - 1/tau_r; numeric: yes -->

- name: double_ram
  inputs:
    tau_r: 2
  expected: 1/2

### adiabatic_diffuser_temperature

<!-- family: aerodynamics; symbols: Tt0; expr: Tt0; numeric: yes -->

- name: three_hundred
  inputs:
    Tt0: 300
  expected: 300

- name: static_sea
  inputs:
    Tt0: 28815/100
  expected: 28815/100

### inlet_exit_total_pressure

<!-- family: aerodynamics; symbols: pi_d, pt0; expr: pi_d*pt0; numeric: yes -->

- name: half
  inputs:
    pi_d: 1/2
    pt0: 200000
  expected: 100000

- name: perfect
  inputs:
    pi_d: 1
    pt0: 101325
  expected: 101325

### pitot_inlet_recovery

<!-- family: aerodynamics; symbols: pi_ns, pi_ds; expr: pi_ns*pi_ds; numeric: yes -->

- name: shock_only
  inputs:
    pi_ns: 4/5
    pi_ds: 1
  expected: 4/5

- name: with_duct
  inputs:
    pi_ns: 4/5
    pi_ds: 19/20
  expected: 19/25

### compressor_temperature_ratio_efficiency

<!-- family: aerodynamics; symbols: pi_c, g, eta_c; expr: 1 + (pi_c**((g - 1)/g) - 1)/eta_c; numeric: yes -->

- name: ideal_air_two
  inputs:
    pi_c: 2**(7/2)
    g: 7/5
    eta_c: 1
  expected: 2

- name: half_efficient
  inputs:
    pi_c: 2**(7/2)
    g: 7/5
    eta_c: 1/2
  expected: 3

### compressor_work_efficiency

<!-- family: aerodynamics; symbols: cp, Tt2, pi_c, g, eta_c; expr: cp*Tt2*(pi_c**((g - 1)/g) - 1)/eta_c; numeric: yes -->

- name: unit_rise
  inputs:
    cp: 1000
    Tt2: 300
    pi_c: 2**(7/2)
    g: 7/5
    eta_c: 1
  expected: 300000

- name: half_efficient
  inputs:
    cp: 1000
    Tt2: 300
    pi_c: 2**(7/2)
    g: 7/5
    eta_c: 1/2
  expected: 600000

### compressor_stage_count

<!-- family: aerodynamics; symbols: pi_c, pi_stage; expr: log(pi_c)/log(pi_stage); numeric: yes -->

- name: eight_from_two
  inputs:
    pi_c: 256
    pi_stage: 2
  expected: 8

- name: two_stages
  inputs:
    pi_c: 9
    pi_stage: 3
  expected: 2

### burner_fuel_air_ratio_efficiency

<!-- family: aerodynamics; symbols: cp, Tt4, Tt3, eta_b, Q; expr: cp*(Tt4 - Tt3)/(eta_b*Q - cp*Tt4); numeric: yes -->

- name: unit_delta
  inputs:
    cp: 1000
    Tt4: 1200
    Tt3: 600
    eta_b: 1
    Q: 42000000
  expected: 600000/(42000000 - 1200000)

- name: half_burner
  inputs:
    cp: 1000
    Tt4: 1200
    Tt3: 600
    eta_b: 1/2
    Q: 42000000
  expected: 600000/(21000000 - 1200000)

### burner_exit_total_pressure

<!-- family: aerodynamics; symbols: pi_b, pt3; expr: pi_b*pt3; numeric: yes -->

- name: lossless
  inputs:
    pi_b: 1
    pt3: 8
  expected: 8

- name: two_percent
  inputs:
    pi_b: 98/100
    pt3: 100
  expected: 98

### turbine_temperature_ratio_from_work

<!-- family: aerodynamics; symbols: wc, f, eta_m, cp, Tt4; expr: 1 - wc/((1 + f)*eta_m*cp*Tt4); numeric: yes -->

- name: ideal_half
  inputs:
    wc: 600000
    f: 0
    eta_m: 1
    cp: 1000
    Tt4: 1200
  expected: 1/2

- name: with_fuel
  inputs:
    wc: 600000
    f: 1/5
    eta_m: 1
    cp: 1000
    Tt4: 1200
  expected: 7/12

### turbine_pressure_ratio_from_efficiency

<!-- family: aerodynamics; symbols: tau_t, eta_t, g; expr: (1 - (1 - tau_t)/eta_t)**(g/(g - 1)); numeric: yes -->

- name: air_half
  inputs:
    tau_t: 1/2
    eta_t: 1
    g: 7/5
  expected: (1/2)**(7/2)

- name: four_fifths
  inputs:
    tau_t: 3/5
    eta_t: 4/5
    g: 7/5
  expected: (1/2)**(7/2)

### afterburner_fuel_air_ratio

<!-- family: aerodynamics; symbols: f, cp, Tt7, Tt6, eta_ab, Q; expr: (1 + f)*cp*(Tt7 - Tt6)/(eta_ab*Q - cp*Tt7); numeric: yes -->

- name: no_core_fuel
  inputs:
    f: 0
    cp: 1000
    Tt7: 2000
    Tt6: 1000
    eta_ab: 1
    Q: 42000000
  expected: 1/40

- name: with_core_fuel
  inputs:
    f: 1/50
    cp: 1000
    Tt7: 2000
    Tt6: 1000
    eta_ab: 1
    Q: 42000000
  expected: 51/2000

### afterburner_exit_total_pressure

<!-- family: aerodynamics; symbols: pi_ab, pt6; expr: pi_ab*pt6; numeric: yes -->

- name: lossless
  inputs:
    pi_ab: 1
    pt6: 50
  expected: 50

- name: five_percent
  inputs:
    pi_ab: 19/20
    pt6: 20
  expected: 19

### nozzle_exit_velocity_efficiency

<!-- family: aerodynamics; symbols: eta_n, cp, Tt, NPR, g; expr: (2*eta_n*cp*Tt*(1 - NPR**(-(g - 1)/g)))**0.5; numeric: yes -->

- name: ideal_half_drop
  inputs:
    eta_n: 1
    cp: 2
    Tt: 1
    NPR: 2**(7/2)
    g: 7/5
  expected: 2**0.5

- name: quarter_efficiency
  inputs:
    eta_n: 1/4
    cp: 2
    Tt: 1
    NPR: 2**(7/2)
    g: 7/5
  expected: (1/2)**0.5

### specific_thrust_with_pressure

<!-- family: aerodynamics; symbols: f, Ve, V0, pe, p0, As; expr: (1 + f)*Ve - V0 + (pe - p0)*As; numeric: yes -->

- name: balanced
  inputs:
    f: 0
    Ve: 800
    V0: 200
    pe: 1
    p0: 1
    As: 5
  expected: 600

- name: unbalanced
  inputs:
    f: 0
    Ve: 800
    V0: 200
    pe: 3
    p0: 1
    As: 10
  expected: 620

### turbofan_core_pressure_ratio

<!-- family: aerodynamics; symbols: opr, pi_f; expr: opr/pi_f; numeric: yes -->

- name: ten
  inputs:
    opr: 20
    pi_f: 2
  expected: 10

- name: four
  inputs:
    opr: 12
    pi_f: 3
  expected: 4

### turbofan_shaft_work

<!-- family: aerodynamics; symbols: wc, bpr, wf; expr: wc + bpr*wf; numeric: yes -->

- name: core_only
  inputs:
    wc: 10
    bpr: 0
    wf: 3
  expected: 10

- name: with_bypass
  inputs:
    wc: 10
    bpr: 2
    wf: 3
  expected: 16

### turbofan_specific_thrust

<!-- family: aerodynamics; symbols: f, Ve, bpr, Vf, V0; expr: ((1 + f)*Ve + bpr*Vf)/(1 + bpr) - V0; numeric: yes -->

- name: no_bypass
  inputs:
    f: 0
    Ve: 800
    bpr: 0
    Vf: 0
    V0: 200
  expected: 600

- name: equal_streams
  inputs:
    f: 0
    Ve: 300
    bpr: 1
    Vf: 200
    V0: 100
  expected: 150

### turbofan_tsfc

<!-- family: aerodynamics; symbols: f, Fs, bpr; expr: f/(Fs*(1 + bpr)); numeric: yes -->

- name: no_bypass
  inputs:
    f: 1/50
    Fs: 500
    bpr: 0
  expected: 1/25000

- name: bypass
  inputs:
    f: 1/50
    Fs: 200
    bpr: 1
  expected: 1/20000

### turbofan_thermal_efficiency

<!-- family: aerodynamics; symbols: f, Ve, bpr, Vf, V0, Q; expr: ((1 + f)*Ve**2 + bpr*Vf**2 - (1 + bpr)*V0**2)/(2*f*Q); numeric: yes -->

- name: static_core
  inputs:
    f: 1/50
    Ve: 100
    bpr: 0
    Vf: 0
    V0: 0
    Q: 50000
  expected: 51/10

- name: bypass_only_jet
  inputs:
    f: 1/50
    Ve: 0
    bpr: 1
    Vf: 100
    V0: 0
    Q: 50000
  expected: 5

### turbofan_propulsive_efficiency

<!-- family: aerodynamics; symbols: V0, Fs, f, Ve, bpr, Vf; expr: 2*V0*Fs/(((1 + f)*Ve**2 + bpr*Vf**2)/(1 + bpr) - V0**2); numeric: yes -->

- name: classic_half
  inputs:
    V0: 250
    Fs: 500
    f: 0
    Ve: 750
    bpr: 0
    Vf: 0
  expected: 1/2

- name: static
  inputs:
    V0: 0
    Fs: 100
    f: 0
    Ve: 200
    bpr: 1
    Vf: 100
  expected: 0

### turbofan_overall_efficiency

<!-- family: aerodynamics; symbols: Fs, V0, bpr, f, Q; expr: Fs*V0*(1 + bpr)/(f*Q); numeric: yes -->

- name: no_bypass
  inputs:
    Fs: 500
    V0: 200
    bpr: 0
    f: 1/50
    Q: 1000000
  expected: 5

- name: with_bypass
  inputs:
    Fs: 100
    V0: 50
    bpr: 1
    f: 1/25
    Q: 100000
  expected: 5/2

### airflow_from_thrust

<!-- family: aerodynamics; symbols: F, Fs; expr: F/Fs; numeric: yes -->

- name: ten
  inputs:
    F: 5000
    Fs: 500
  expected: 10

- name: two
  inputs:
    F: 100
    Fs: 25
  expected: 4

### capture_area

<!-- family: aerodynamics; symbols: mdot, rho, V; expr: mdot/(rho*V); numeric: yes -->

- name: unit
  inputs:
    mdot: 2
    rho: 1
    V: 4
  expected: 1/2

- name: sea_level
  inputs:
    mdot: 49/4
    rho: 49/40
    V: 10
  expected: 1

### circular_capture_diameter

<!-- family: aerodynamics; symbols: A, pi; expr: (4*A/pi)**0.5; numeric: yes -->

- name: unit_area
  inputs:
    A: pi
    pi: pi
  expected: 2

- name: four
  inputs:
    A: 4*pi
    pi: pi
  expected: 4

### compressible_mass_flow_parameter

<!-- family: aerodynamics; symbols: g, R, M; expr: (g/R)**0.5*M*(1 + ((g - 1)/2)*M**2)**(-(g + 1)/(2*(g - 1))); numeric: yes -->

- name: sonic_unit_gas
  inputs:
    g: 7/5
    R: 1
    M: 1
  expected: (7/5)**0.5*(6/5)**(-3)

- name: rest
  inputs:
    g: 7/5
    R: 1
    M: 0
  expected: 0

### annulus_area_from_mass_flow

<!-- family: aerodynamics; symbols: mdot, Tt, pt, mfp; expr: mdot*(Tt**0.5)/(pt*mfp); numeric: yes -->

- name: unit
  inputs:
    mdot: 2
    Tt: 4
    pt: 1
    mfp: 1
  expected: 4

- name: half
  inputs:
    mdot: 1
    Tt: 1
    pt: 2
    mfp: 1
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

- name: scaled_polar
  inputs:
    q: 1
    S: 2
    T: 2
    CD0: 1/2
    pi: pi
    AR: 2
    e: 1/2
    W: 2
  expected: (pi/2)**0.5

### pullup_load_factor

<!-- family: aerodynamics; symbols: V, g, R; expr: 1 + V**2/(g*R); numeric: yes -->

- name: unit_two_g
  inputs:
    V: 10
    g: 10
    R: 10
  expected: 2

- name: n_equals_three
  inputs:
    V: 30
    g: 10
    R: 45
  expected: 3

### pullup_radius

<!-- family: aerodynamics; symbols: V, g, n; expr: V**2/(g*(n - 1)); numeric: yes -->

- name: unit_two_g
  inputs:
    V: 10
    g: 10
    n: 2
  expected: 10

- name: n_equals_three
  inputs:
    V: 30
    g: 10
    n: 3
  expected: 45

### pullup_pitch_rate

<!-- family: aerodynamics; symbols: g, n, V; expr: g*(n - 1)/V; numeric: yes -->

- name: unit_two_g
  inputs:
    g: 10
    n: 2
    V: 10
  expected: 1

- name: n_equals_three
  inputs:
    g: 10
    n: 3
    V: 30
  expected: 2/3

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

- name: scaled_cruise
  inputs:
    V: 2
    ct: 4
    LD: 3
    Wi: e
    Wf: 1
  expected: 3/2

### breguet_endurance_jet

<!-- family: aerodynamics; symbols: ct, LD, Wi, Wf; expr: (1/ct)*LD*log(Wi/Wf); numeric: yes -->

- name: weight_ratio_two
  inputs:
    ct: 1
    LD: 1
    Wi: 2
    Wf: 1
  expected: log(2)

- name: scaled_cruise
  inputs:
    ct: 2
    LD: 4
    Wi: e
    Wf: 1
  expected: 2

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

- name: scaled_cruise
  inputs:
    eta: 3
    c: 2
    LD: 4
    Wi: e
    Wf: 1
  expected: 6

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

- name: scaled_cruise
  inputs:
    eta: 3
    c: 2
    V: 2
    LD: 4
    Wi: e
    Wf: 1
  expected: 3

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

- name: ahead_of_crest
  inputs:
    m: 1/50
    p: 2/5
    xi: 1/5
  expected: 3/200

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

- name: ahead_of_crest
  inputs:
    m: 1/50
    p: 2/5
    xi: 1/5
  expected: 1/20

### naca4_camber_slope_aft

<!-- family: aerodynamics; symbols: m, p, xi; expr: (2*m/(1-p)**2)*(p - xi); numeric: yes -->

- name: at_maximum
  inputs:
    m: 2/100
    p: 4/10
    xi: 4/10
  expected: 0

- name: aft_of_crest
  inputs:
    m: 1/50
    p: 2/5
    xi: 7/10
  expected: -1/30

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

- name: quarter_chord_camber
  inputs:
    m: 1/50
    p: 1/4
    pi: pi
  expected: 16*(3**0.5)/(225*pi)

### naca4_quarter_chord_moment

<!-- family: aerodynamics; symbols: pi, A2, A1; expr: (pi/4)*(A2 - A1); numeric: yes -->

- name: circular_arc_two_percent
  inputs:
    pi: pi
    A2: 0
    A1: 4/50
  expected: -pi/50

### drag_delta_v_per_revolution

<!-- family: aerodynamics; symbols: Cd, rho, V, A, m, period; expr: Cd*0.5*rho*V**2*A/m*period; numeric: yes -->

- name: unit_case
  inputs:
    Cd: 2
    rho: 1
    V: 2
    A: 1
    m: 4
    period: 10
  expected: 10

### phugoid_natural_frequency

<!-- family: aerodynamics; symbols: g, V; expr: g*(2**0.5)/V; numeric: yes -->

- name: unit_speed
  inputs:
    g: 9.80665
    V: 9.80665
  expected: 2**0.5

### phugoid_period

<!-- family: aerodynamics; symbols: pi, V, g; expr: 2*pi*V/(g*(2**0.5)); numeric: yes -->

- name: unit_speed
  inputs:
    pi: pi
    V: 9.80665
    g: 9.80665
  expected: 2*pi/(2**0.5)

### short_period_natural_frequency

<!-- family: aerodynamics; symbols: V, ky, rho, g, c, cla, kn, w; expr: (V/ky)*((rho*g*c*cla*kn)/(2*w))**0.5; numeric: yes -->

- name: fifty_radians_per_second
  inputs:
    V: 50
    ky: 1
    rho: 2
    g: 9.80665
    c: 1
    cla: 1
    kn: 1
    w: 9.80665
  expected: 50

### short_period_period

<!-- family: aerodynamics; symbols: pi, ky, V, rho, g, c, cla, kn, w; expr: 2*pi*ky/(V*((rho*g*c*cla*kn)/(2*w))**0.5); numeric: yes -->

- name: matches_frequency
  inputs:
    pi: pi
    ky: 1
    V: 2
    rho: 2
    g: 1
    c: 1
    cla: 1
    kn: 1
    w: 1
  expected: pi

### dutch_roll_side_acceleration

<!-- family: aerodynamics; symbols: rho, V, S, Cyb, m; expr: 0.5*rho*V**2*S*Cyb/m; numeric: yes -->

- name: unit_side
  inputs:
    rho: 2
    V: 2
    S: 1
    Cyb: -1
    m: 2
  expected: -2

### dutch_roll_directional_stiffness

<!-- family: aerodynamics; symbols: rho, V, S, b, Cnb, Iz; expr: 0.5*rho*V**2*S*b*Cnb/Iz; numeric: yes -->

- name: unit_yaw_stiffness
  inputs:
    rho: 2
    V: 2
    S: 1
    b: 2
    Cnb: 1
    Iz: 4
  expected: 2

### dutch_roll_yaw_damping

<!-- family: aerodynamics; symbols: rho, V, S, b, Cnr, Iz; expr: 0.5*rho*V**2*S*b**2*Cnr/(2*V*Iz); numeric: yes -->

- name: unit_yaw_damping
  inputs:
    rho: 2
    V: 2
    S: 1
    b: 2
    Cnr: -1
    Iz: 2
  expected: -2

### dutch_roll_roll_stiffness

<!-- family: aerodynamics; symbols: rho, V, S, b, Clb, Ix; expr: 0.5*rho*V**2*S*b*Clb/Ix; numeric: yes -->

- name: unit_roll_stiffness
  inputs:
    rho: 2
    V: 2
    S: 1
    b: 2
    Clb: -1
    Ix: 4
  expected: -2

### dutch_roll_roll_damping

<!-- family: aerodynamics; symbols: rho, V, S, b, Clp, Ix; expr: 0.5*rho*V**2*S*b**2*Clp/(2*V*Ix); numeric: yes -->

- name: unit_roll_damping
  inputs:
    rho: 2
    V: 2
    S: 1
    b: 2
    Clp: -1
    Ix: 2
  expected: -2

### dutch_roll_omega_sq

<!-- family: aerodynamics; symbols: Nb, Yb, Nr, V, g, Lb, Lp; expr: Nb + Yb*Nr/V + g*Lb/(V*Lp); numeric: yes -->

- name: both_springs
  inputs:
    Nb: 4
    Yb: -1
    Nr: -1
    V: 2
    g: 2
    Lb: -2
    Lp: -1
  expected: 13/2

### dutch_roll_damping_product

<!-- family: aerodynamics; symbols: Nr, Yb, V; expr: -(Nr + Yb/V)/2; numeric: yes -->

- name: yaw_and_side
  inputs:
    Nr: -1
    Yb: -1
    V: 2
  expected: 3/4

### parachute_descent_rate

<!-- family: aerodynamics; symbols: W, rho, Cd, A; expr: (2*W/(rho*Cd*A))**0.5; numeric: yes -->

- name: unit_balance
  inputs:
    W: 2
    rho: 1
    Cd: 1
    A: 1
  expected: 2

### propeller_shaft_power

<!-- family: aerodynamics; symbols: f, Ve, V0; expr: 0.5*(1+f)*(Ve**2 - V0**2); numeric: yes -->

- name: dry_unit_jet
  inputs:
    f: 0
    Ve: 2
    V0: 0
  expected: 2

- name: residual_flight_speed
  inputs:
    f: 0
    Ve: 2
    V0: 1
  expected: 1.5

### propeller_thrust

<!-- family: aerodynamics; symbols: eta, P, V0; expr: eta*P/V0; numeric: yes -->

- name: half_efficient
  inputs:
    eta: 0.5
    P: 4
    V0: 2
  expected: 1

## Structures

#### beam

### beam_bending_stress

<!-- family: beam; symbols: M, Z; expr: M/Z; numeric: yes -->

- name: unit_section
  inputs:
    M: 1
    Z: 1
  expected: 1

- name: spar_sample
  inputs:
    M: 856
    Z: 1.16
  expected: 856/1.16

### beam_bending_stress_inertia

<!-- family: beam; symbols: M, c, I; expr: M*c/I; numeric: yes -->

- name: unit_inertia
  inputs:
    M: 1
    c: 1
    I: 1
  expected: 1

- name: matches_section_modulus
  inputs:
    M: 1200
    c: 3/100
    I: 9/100000
  expected: 4e5

### section_modulus

<!-- family: beam; symbols: I, c; expr: I/c; numeric: yes -->

- name: unit_modulus
  inputs:
    I: 1
    c: 1
  expected: 1

- name: from_inertia_sample
  inputs:
    I: 9/100000
    c: 3/100
  expected: 3/1000

#### column

### euler_critical_load

<!-- family: column; symbols: E, I, K, L, pi; expr: pi**2*E*I/(K*L)**2; numeric: yes -->

- name: unit_pinned
  inputs:
    E: 1
    I: 1
    K: 1
    L: 1
    pi: pi
  expected: pi**2

- name: steel_sample
  inputs:
    E: 2e11
    I: 1e-6
    K: 1
    L: 2
    pi: pi
  expected: pi**2*5e4

- name: fixed_fixed_fourfold
  inputs:
    E: 1
    I: 1
    K: 1/2
    L: 1
    pi: pi
  expected: 4*pi**2

### euler_critical_load_fixity

<!-- family: column; symbols: C, E, I, L, pi; expr: C*pi**2*E*I/L**2; numeric: yes -->

- name: unit_pinned_fixity
  inputs:
    C: 1
    E: 1
    I: 1
    L: 1
    pi: pi
  expected: pi**2

- name: matches_end_fix_half
  inputs:
    C: 4
    E: 1
    I: 1
    L: 1
    pi: pi
  expected: 4*pi**2

### effective_column_length

<!-- family: column; symbols: K, L; expr: K*L; numeric: yes -->

- name: pinned_unit
  inputs:
    K: 1
    L: 1
  expected: 1

- name: fixed_half
  inputs:
    K: 1/2
    L: 2
  expected: 1

### end_fixity_coefficient

<!-- family: column; symbols: K; expr: 1/K**2; numeric: yes -->

- name: pinned_unity
  inputs:
    K: 1
  expected: 1

- name: fixed_four
  inputs:
    K: 1/2
  expected: 4

### radius_of_gyration

<!-- family: column; symbols: I, A; expr: (I/A)**0.5; numeric: yes -->

- name: unit_gyration
  inputs:
    I: 1
    A: 1
  expected: 1

- name: square_sample
  inputs:
    I: 1e-6
    A: 1e-3
  expected: (1e-3)**0.5

### column_slenderness

<!-- family: column; symbols: K, L, I, A; expr: K*L/(I/A)**0.5; numeric: yes -->

- name: unit_slenderness
  inputs:
    K: 1
    L: 1
    I: 1
    A: 1
  expected: 1

- name: steel_sample_slenderness
  inputs:
    K: 1
    L: 2
    I: 1e-6
    A: 1e-3
  expected: 2/(1e-3)**0.5

### euler_critical_stress

<!-- family: column; symbols: E, K, L, I, A, pi; expr: pi**2*E/(K*L/(I/A)**0.5)**2; numeric: yes -->

- name: unit_stress
  inputs:
    E: 1
    K: 1
    L: 1
    I: 1
    A: 1
    pi: pi
  expected: pi**2

- name: steel_sample_stress
  inputs:
    E: 2e11
    K: 1
    L: 2
    I: 1e-6
    A: 1e-3
    pi: pi
  expected: pi**2*5e4/1e-3

#### shaft

### polar_second_moment_solid

<!-- family: shaft; symbols: Ro, pi; expr: pi/2*Ro**4; numeric: yes -->

- name: unit_solid
  inputs:
    Ro: 1
    pi: pi
  expected: pi/2

- name: twenty_mm_radius
  inputs:
    Ro: 2/100
    pi: pi
  expected: pi/2*(2/100)**4

### polar_second_moment_hollow

<!-- family: shaft; symbols: Ro, Ri, pi; expr: pi/2*(Ro**4 - Ri**4); numeric: yes -->

- name: unit_hollow_annulus
  inputs:
    Ro: 2
    Ri: 1
    pi: pi
  expected: pi/2*(16 - 1)

- name: matches_solid_when_ri_zero
  inputs:
    Ro: 1
    Ri: 0
    pi: pi
  expected: pi/2

### circular_shaft_shear

<!-- family: shaft; symbols: T, r, J; expr: T*r/J; numeric: yes -->

- name: unit_shear
  inputs:
    T: 1
    r: 1
    J: 1
  expected: 1

- name: affdl_outer_fiber
  inputs:
    T: 1000
    r: 2
    J: pi/2*(16 - 1)
  expected: 2*1000*2/(pi*(16 - 1))

### circular_shaft_twist

<!-- family: shaft; symbols: T, L, G, J; expr: T*L/(G*J); numeric: yes -->

- name: unit_twist
  inputs:
    T: 1
    L: 1
    G: 1
    J: 1
  expected: 1

- name: affdl_hollow_sample
  inputs:
    T: 1000
    L: 1/2
    G: 8e10
    J: pi/2*(16 - 1)
  expected: 2*1000*(1/2)/(pi*(16 - 1)*8e10)

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

### cylinder_longitudinal_stress

<!-- family: shell; symbols: p, R, t; expr: p*R/(2*t); numeric: yes -->

- name: sample_cylinder
  inputs:
    p: 1000
    R: 20
    t: 1/10
  expected: 100000

### sphere_membrane_stress

<!-- family: shell; symbols: p, R, t; expr: p*R/(2*t); numeric: yes -->

- name: same_numbers
  inputs:
    p: 1000
    R: 20
    t: 1/10
  expected: 100000

### thin_wall_hoop_thickness

<!-- family: shell; symbols: p, R, sigma; expr: p*R/sigma; numeric: yes -->

- name: fifty_kilopascal
  inputs:
    p: 1000
    R: 1/2
    sigma: 50000
  expected: 1/100

### thin_wall_membrane_thickness

<!-- family: shell; symbols: p, R, sigma; expr: p*R/(2*sigma); numeric: yes -->

- name: half_the_hoop_wall
  inputs:
    p: 1000
    R: 1/2
    sigma: 25000
  expected: 1/100

### simply_supported_plate_k

<!-- family: shell; symbols: m, b, a; expr: (m*b/a + a/(m*b))**2; numeric: yes -->

- name: square_plate
  inputs:
    m: 1
    b: 1
    a: 1
  expected: 4

### plate_buckling_stress

<!-- family: shell; symbols: k, pi, E, nu, b, t; expr: k*pi**2*E/(12*(1-nu**2)*(b/t)**2); numeric: yes -->

- name: long_plate_sample
  inputs:
    k: 4
    pi: pi
    E: 70e9
    nu: 0.3
    b: 0.5
    t: 0.002
  expected: 4*pi**2*70e9/(12*(1-0.3**2)*(0.5/0.002)**2)

### fracture_critical_half_length

<!-- family: shell; symbols: pi, Kic, Y, sigma; expr: (1/pi)*(Kic/(Y*sigma))**2; numeric: yes -->

- name: unit_plate
  inputs:
    pi: pi
    Kic: pi**0.5
    Y: 1
    sigma: 1
  expected: 1

## Mass properties

#### mass

### total_mass

<!-- family: mass; symbols: m1, m2; expr: m1 + m2; numeric: yes -->

- name: unit_parts
  inputs:
    m1: 1
    m2: 1
  expected: 2

- name: unequal_parts
  inputs:
    m1: 2
    m2: 3
  expected: 5

### mass_first_moment

<!-- family: mass; symbols: m, x; expr: m*x; numeric: yes -->

- name: unit_arm
  inputs:
    m: 1
    x: 1
  expected: 1

- name: two_kg_at_half_metre
  inputs:
    m: 2
    x: 1/2
  expected: 1

### stage_propellant_mass

<!-- family: mass; symbols: mp0, f; expr: mp0*(1-f); numeric: yes -->

- name: half_burned
  inputs:
    mp0: 4
    f: 1/2
  expected: 2

### stage_propellant_station

<!-- family: mass; symbols: x_full, f, x_empty; expr: x_full + f*(x_empty - x_full); numeric: yes -->

- name: halfway
  inputs:
    x_full: 4
    f: 1/2
    x_empty: 0
  expected: 2

### center_of_mass_coordinate

<!-- family: mass; symbols: Mx, m; expr: Mx/m; numeric: yes -->

- name: unit_centroid
  inputs:
    Mx: 1
    m: 1
  expected: 1

- name: two_equal_masses
  inputs:
    Mx: 2
    m: 4
  expected: 1/2

### point_mass_moment

<!-- family: mass; symbols: m, d1, d2; expr: m*(d1**2 + d2**2); numeric: yes -->

- name: unit_offset
  inputs:
    m: 1
    d1: 1
    d2: 0
  expected: 1

- name: two_metre_diagonal
  inputs:
    m: 2
    d1: 3
    d2: 4
  expected: 50

### point_mass_product

<!-- family: mass; symbols: m, d1, d2; expr: m*d1*d2; numeric: yes -->

- name: unit_product
  inputs:
    m: 1
    d1: 1
    d2: 1
  expected: 1

- name: offset_pair
  inputs:
    m: 2
    d1: 3
    d2: -1
  expected: -6

### parallel_axis_moment

<!-- family: mass; symbols: Icg, m, d1, d2; expr: Icg + m*(d1**2 + d2**2); numeric: yes -->

- name: point_mass_transfer
  inputs:
    Icg: 0
    m: 1
    d1: 1
    d2: 0
  expected: 1

- name: own_plus_transfer
  inputs:
    Icg: 2
    m: 3
    d1: 1
    d2: 2
  expected: 17

### parallel_axis_product

<!-- family: mass; symbols: Pcg, m, d1, d2; expr: Pcg + m*d1*d2; numeric: yes -->

- name: point_mass_product_transfer
  inputs:
    Pcg: 0
    m: 1
    d1: 2
    d2: 3
  expected: 6

- name: own_plus_product
  inputs:
    Pcg: 1
    m: 2
    d1: -1
    d2: 4
  expected: -7

### inertia_shift_to_cg

<!-- family: mass; symbols: IO, m, d1, d2; expr: IO - m*(d1**2 + d2**2); numeric: yes -->

- name: unit_shift
  inputs:
    IO: 2
    m: 1
    d1: 1
    d2: 0
  expected: 1

- name: tn575_style_shift
  inputs:
    IO: 50
    m: 2
    d1: 3
    d2: 4
  expected: 0

### propellant_slosh_frequency

<!-- family: mass; symbols: g, R, xi, h; expr: ((g/R)*xi*tanh(xi*h/R))**0.5; numeric: yes -->

- name: unit_cylinder
  inputs:
    g: 9.80665
    R: 1
    xi: 1.841
    h: 1
  expected: ((9.80665/1)*1.841*tanh(1.841*1/1))**0.5

### slosh_pendulum_length

<!-- family: mass; symbols: g, omega; expr: g/omega**2; numeric: yes -->

- name: one_radian
  inputs:
    g: 9.80665
    omega: 1
  expected: 9.80665

## Aerothermodynamics

#### aerotherm

### stagnation_convective_heat_flux

<!-- family: aerotherm; symbols: K, ps, Rn, hs, hw; expr: K*((ps/Rn)**0.5)*(hs - hw); numeric: yes -->

- name: unit_coefficient
  inputs:
    K: 1
    ps: 1
    Rn: 1
    hs: 2
    hw: 1
  expected: 1

- name: air_table_coefficient
  inputs:
    K: 0.1113
    ps: 1
    Rn: 1
    hs: 1e6
    hw: 0
  expected: 111300

### freestream_kinetic_enthalpy

<!-- family: aerotherm; symbols: V; expr: 0.5*V**2; numeric: yes -->

- name: hundred_m_s
  inputs:
    V: 100
  expected: 5000

### wall_enthalpy_perfect

<!-- family: aerotherm; symbols: cp, Tw; expr: cp*Tw; numeric: yes -->

- name: unit_wall
  inputs:
    cp: 1004.7
    Tw: 300
  expected: 301410

### stagnation_convective_heat_flux_velocity

<!-- family: aerotherm; symbols: k, rho, Rn, V; expr: k*((rho/Rn)**0.5)*V**3; numeric: yes -->

- name: unit_velocity_form
  inputs:
    k: 1
    rho: 1
    Rn: 1
    V: 1
  expected: 1

- name: earth_air_derived_k
  inputs:
    k: 0.1113/(2*(101325)**0.5)
    rho: 3.1459e-4
    Rn: 1
    V: 3535
  expected: 0.1113/(2*(101325)**0.5)*((3.1459e-4)**0.5)*(3535)**3

### radiative_equilibrium_wall_temperature

<!-- family: aerotherm; symbols: q, eps, sigma; expr: (q/(eps*sigma))**0.25; numeric: yes -->

- name: blackbody_unit
  inputs:
    q: 5.670374419e-8
    eps: 1
    sigma: 5.670374419e-8
  expected: 1

- name: gray_shuttle_like
  inputs:
    q: 136000
    eps: 0.8
    sigma: 5.670374419e-8
  expected: (136000/(0.8*5.670374419e-8))**0.25

### ballistic_coefficient

<!-- family: aerotherm; symbols: m, Cd, A; expr: m/(Cd*A); numeric: yes -->

- name: unit_mass_area
  inputs:
    m: 1000
    Cd: 1
    A: 1
  expected: 1000

- name: half_drag
  inputs:
    m: 500
    Cd: 0.5
    A: 2
  expected: 500

### exponential_atmosphere_density

<!-- family: aerotherm; symbols: rhoref, Z, Zref, H; expr: rhoref*exp(-(Z - Zref)/H); numeric: yes -->

- name: at_reference
  inputs:
    rhoref: 1.752288
    Z: 0
    Zref: 0
    H: 6705.6
  expected: 1.752288

- name: one_scale_height
  inputs:
    rhoref: 1.752288
    Z: 6705.6
    Zref: 0
    H: 6705.6
  expected: 1.752288*exp(-1)

### atmosphere_inverse_scale_height

<!-- family: aerotherm; symbols: H; expr: 1/H; numeric: yes -->

- name: allen_eggers_earth
  inputs:
    H: 6705.6
  expected: 1/6705.6

### allen_eggers_peak_deceleration

<!-- family: aerotherm; symbols: Ve, th, H; expr: Ve**2*sin(th)/(2*exp(1)*H); numeric: yes -->

- name: vertical_unit
  inputs:
    Ve: 1000
    th: 1.5707963267948966
    H: 6705.6
  expected: 1000**2*sin(1.5707963267948966)/(2*exp(1)*6705.6)

- name: thirty_degrees
  inputs:
    Ve: 7000
    th: 0.5235987755982988
    H: 6705.6
  expected: 7000**2*sin(0.5235987755982988)/(2*exp(1)*6705.6)

### allen_eggers_speed_at_peak_deceleration

<!-- family: aerotherm; symbols: Ve; expr: Ve*exp(-0.5); numeric: yes -->

- name: seven_km_s
  inputs:
    Ve: 7000
  expected: 7000*exp(-0.5)

### allen_eggers_density_at_peak_deceleration

<!-- family: aerotherm; symbols: B, th, H; expr: B*sin(th)/H; numeric: yes -->

- name: vertical_ballistic
  inputs:
    B: 100
    th: 1.5707963267948966
    H: 6705.6
  expected: 100*sin(1.5707963267948966)/6705.6

### allen_eggers_peak_deceleration_altitude

<!-- family: aerotherm; symbols: Zref, H, rhoref, B, th; expr: Zref + H*log(rhoref*H/(B*sin(th))); numeric: yes -->

- name: sea_level_reference
  inputs:
    Zref: 0
    H: 6705.6
    rhoref: 1.752288
    B: 100
    th: 0.5235987755982988
  expected: 0 + 6705.6*log(1.752288*6705.6/(100*sin(0.5235987755982988)))

### allen_eggers_surface_speed

<!-- family: aerotherm; symbols: Ve, rhoref, H, B, th; expr: Ve*exp(-rhoref*H/(2*B*sin(th))); numeric: yes -->

- name: heavy_vertical
  inputs:
    Ve: 7000
    rhoref: 1.752288
    H: 6705.6
    B: 5000
    th: 1.5707963267948966
  expected: 7000*exp(-1.752288*6705.6/(2*5000*sin(1.5707963267948966)))

### allen_eggers_surface_deceleration

<!-- family: aerotherm; symbols: rhoref, B, Vs; expr: (rhoref/(2*B))*Vs**2; numeric: yes -->

- name: unit_surface
  inputs:
    rhoref: 1.225
    B: 100
    Vs: 1000
  expected: (1.225/(2*100))*1000**2

### lumped_thermal_time_constant

<!-- family: aerotherm; symbols: m, c, h, A; expr: m*c/(h*A); numeric: yes -->

- name: unit_mass
  inputs:
    m: 1
    c: 1
    h: 1
    A: 1
  expected: 1

- name: twenty_seconds
  inputs:
    m: 2
    c: 500
    h: 10
    A: 5
  expected: 20

### lumped_capacitance_temperature

<!-- family: aerotherm; symbols: Tinf, Ti, t, tau; expr: Tinf + (Ti - Tinf)*exp(-t/tau); numeric: yes -->

- name: at_one_time_constant
  inputs:
    Tinf: 300
    Ti: 400
    t: 20
    tau: 20
  expected: 300 + 100/exp(1)

- name: initial_instant
  inputs:
    Tinf: 300
    Ti: 400
    t: 0
    tau: 20
  expected: 400

### lumped_capacitance_time_to_temperature

<!-- family: aerotherm; symbols: tau, T, Tinf, Ti; expr: -tau*log((T - Tinf)/(Ti - Tinf)); numeric: yes -->

- name: one_time_constant
  inputs:
    tau: 20
    T: 300 + 100/exp(1)
    Tinf: 300
    Ti: 400
  expected: 20

- name: halfway_excess
  inputs:
    tau: 10
    T: 350
    Tinf: 300
    Ti: 400
  expected: -10*log(1/2)

### lumped_capacitance_heat_transferred

<!-- family: aerotherm; symbols: m, c, Ti, T; expr: m*c*(Ti - T); numeric: yes -->

- name: cool_by_one_kelvin
  inputs:
    m: 2
    c: 500
    Ti: 400
    T: 399
  expected: 1000

- name: at_one_time_constant
  inputs:
    m: 2
    c: 500
    Ti: 400
    T: 300 + 100/exp(1)
  expected: 2*500*(100 - 100/exp(1))

### biot_number

<!-- family: aerotherm; symbols: h, Lc, k; expr: h*Lc/k; numeric: yes -->

- name: small_biot
  inputs:
    h: 10
    Lc: 0.01
    k: 200
  expected: 5/10000

- name: warn_threshold
  inputs:
    h: 10
    Lc: 0.05
    k: 5
  expected: 1/10

### spacecraft_absorbed_power

<!-- family: aerotherm; symbols: S, Asun, alpha, fe, albedo, Falb, Aalb, qir, eps, Air, Fir, Qint; expr: S*Asun*alpha*(1 - fe) + S*albedo*Falb*Aalb*alpha + qir*eps*Air*Fir + Qint; numeric: yes -->

- name: sun_only
  inputs:
    S: 1000
    Asun: 1
    alpha: 1
    fe: 0.4
    albedo: 0
    Falb: 1
    Aalb: 0
    qir: 0
    eps: 1
    Air: 0
    Fir: 1
    Qint: 0
  expected: 600

### spacecraft_equilibrium_temperature

<!-- family: aerotherm; symbols: Q, eps, sigma, Arad; expr: (Q/(eps*sigma*Arad))**0.25; numeric: yes -->

- name: three_hundred_kelvin
  inputs:
    Q: 0.8*5.670374419e-8*300**4
    eps: 0.8
    sigma: 5.670374419e-8
    Arad: 1
  expected: 300

### radiator_area_for_temperature

<!-- family: aerotherm; symbols: Q, eps, sigma, T; expr: Q/(eps*sigma*T**4); numeric: yes -->

- name: one_square_metre
  inputs:
    Q: 0.8*5.670374419e-8*300**4
    eps: 0.8
    sigma: 5.670374419e-8
    T: 300
  expected: 1

### equilibrium_glide_peak_deceleration

<!-- family: aerotherm; symbols: g, lod; expr: g/lod; numeric: yes -->

- name: lift_equals_twice_drag
  inputs:
    g: 9.80665
    lod: 2
  expected: 9.80665/2

### equilibrium_glide_entry_deceleration

<!-- family: aerotherm; symbols: g, ve, vc, lod; expr: g*(1 - ve*ve/(vc*vc))/lod; numeric: yes -->

- name: half_circular
  inputs:
    g: 10
    ve: 1
    vc: 2
    lod: 2
  expected: 15/4

### equilibrium_glide_heating_density

<!-- family: aerotherm; symbols: B, g, V, vc, lod; expr: 2*B*g*(1 - V*V/(vc*vc))/(V*V*lod); numeric: yes -->

- name: three_quarters
  inputs:
    B: 1
    g: 2
    V: 2
    vc: 4
    lod: 1
  expected: 3/4

### equilibrium_glide_heat_flux_scale

<!-- family: aerotherm; symbols: rho, V; expr: (rho**0.5)*V**3; numeric: yes -->

- name: two_and_four
  inputs:
    rho: 4
    V: 2
  expected: 16

### equilibrium_glide_heating_speed

<!-- family: aerotherm; symbols: vc; expr: vc*(2/3)**0.5; numeric: yes -->

- name: three_metres_per_second
  inputs:
    vc: 3
  expected: 3*(2/3)**0.5

## Spacecraft power

#### power

### flat_plate_solar_irradiance

<!-- family: power; symbols: S, theta; expr: S*cos(theta); numeric: yes -->

- name: normal_incidence
  inputs:
    S: 1361.6
    theta: 0
  expected: 1361.6

- name: sixty_degrees
  inputs:
    S: 1000
    theta: pi/3
  expected: 500

### solar_array_ideal_power

<!-- family: power; symbols: S, A, eta, Fp; expr: S*A*eta*Fp; numeric: yes -->

- name: unit_panel
  inputs:
    S: 1361.6
    A: 1
    eta: 0.3
    Fp: 0.85
  expected: 1361.6*0.3*0.85

### solar_array_bol_power

<!-- family: power; symbols: S, A, eta, Fp, Id, theta; expr: S*A*eta*Fp*Id*cos(theta); numeric: yes -->

- name: normal_with_knockdowns
  inputs:
    S: 1361.6
    A: 2
    eta: 0.28
    Fp: 0.9
    Id: 0.85
    theta: 0
  expected: 1361.6*2*0.28*0.9*0.85

- name: cosine_half
  inputs:
    S: 1000
    A: 1
    eta: 1
    Fp: 1
    Id: 1
    theta: pi/3
  expected: 500

### solar_array_bol_power_from_specific

<!-- family: power; symbols: psa, A, Id, theta; expr: psa*A*Id*cos(theta); numeric: yes -->

- name: specific_normal
  inputs:
    psa: 300
    A: 2
    Id: 0.9
    theta: 0
  expected: 540

### solar_array_life_degradation

<!-- family: power; symbols: d, L; expr: (1 - d)**L; numeric: yes -->

- name: five_years_half_percent
  inputs:
    d: 0.005
    L: 5
  expected: 0.995**5

- name: zero_life
  inputs:
    d: 0.02
    L: 0
  expected: 1

### solar_array_eol_power

<!-- family: power; symbols: Pbol, Ld; expr: Pbol*Ld; numeric: yes -->

- name: ten_percent_life_loss
  inputs:
    Pbol: 1000
    Ld: 0.9
  expected: 900

### solar_array_orbit_average_power

<!-- family: power; symbols: P, fe; expr: P*(1 - fe); numeric: yes -->

- name: thirty_five_percent_eclipse
  inputs:
    P: 100
    fe: 0.35
  expected: 65

### circular_orbit_eclipse_fraction

<!-- family: power; symbols: re, r, beta, pi; expr: acos(((1 - (re/r)**2)**0.5)/cos(beta))/pi; numeric: yes -->

- name: beta_zero_unit
  inputs:
    re: 3
    r: 5
    beta: 0
    pi: pi
  expected: acos((1 - (3/5)**2)**0.5)/pi

- name: elevated_beta
  inputs:
    re: 6378137
    r: 6378137 + 400000
    beta: 0.2
    pi: pi
  expected: acos(((1 - (6378137/(6378137 + 400000))**2)**0.5)/cos(0.2))/pi

### circular_orbit_eclipse_duration

<!-- family: power; symbols: T, re, r, beta, pi; expr: T*acos(((1 - (re/r)**2)**0.5)/cos(beta))/pi; numeric: yes -->

- name: beta_zero_unit_period
  inputs:
    T: 10
    re: 3
    r: 5
    beta: 0
    pi: pi
  expected: 10*acos((1 - (3/5)**2)**0.5)/pi

- name: elevated_beta_leo_period
  inputs:
    T: 5553.6
    re: 6378137
    r: 6378137 + 400000
    beta: 0.2
    pi: pi
  expected: 5553.6*acos(((1 - (6378137/(6378137 + 400000))**2)**0.5)/cos(0.2))/pi

### battery_energy_from_capacity_ah

<!-- family: power; symbols: C_Ah, V; expr: 3600*C_Ah*V; numeric: yes -->

- name: one_hundred_ah_at_twenty_eight_v
  inputs:
    C_Ah: 100
    V: 28
  expected: 3600*100*28

- name: unit_wh
  inputs:
    C_Ah: 1
    V: 1
  expected: 3600

### battery_depth_of_discharge

<!-- family: power; symbols: E_removed, E; expr: E_removed/E; numeric: yes -->

- name: twenty_percent
  inputs:
    E_removed: 20
    E: 100
  expected: 0.2

- name: full_nameplate
  inputs:
    E_removed: 50
    E: 50
  expected: 1

### battery_usable_energy

<!-- family: power; symbols: E, DOD, eta_d; expr: E*DOD*eta_d; numeric: yes -->

- name: half_dod_ninety_discharge
  inputs:
    E: 100000
    DOD: 0.5
    eta_d: 0.9
  expected: 45000

### battery_time_at_continuous_load

<!-- family: power; symbols: Eu, P; expr: Eu/P; numeric: yes -->

- name: forty_five_kj_at_fifty_w
  inputs:
    Eu: 45000
    P: 50
  expected: 900

### battery_discharge_energy

<!-- family: power; symbols: P, te, eta_d; expr: P*te/eta_d; numeric: yes -->

- name: hundred_w_half_hour_at_point_eight_eight
  inputs:
    P: 100
    te: 1800
    eta_d: 0.88
  expected: 100*1800/0.88

### battery_required_nameplate_energy

<!-- family: power; symbols: P, te, eta_d, DOD; expr: P*te/(eta_d*DOD); numeric: yes -->

- name: twenty_percent_dod
  inputs:
    P: 100
    te: 1800
    eta_d: 0.88
    DOD: 0.2
  expected: 100*1800/(0.88*0.2)

### battery_required_capacity_ah

<!-- family: power; symbols: Ereq, V; expr: Ereq/(3600*V); numeric: yes -->

- name: thirty_volt_bus
  inputs:
    Ereq: 3600*100*28
    V: 28
  expected: 100

### battery_charge_energy

<!-- family: power; symbols: Es, eta_c; expr: Es/eta_c; numeric: yes -->

- name: ninety_two_percent_charger
  inputs:
    Es: 184000
    eta_c: 0.92
  expected: 184000/0.92

### battery_recharge_power

<!-- family: power; symbols: P, te, eta_c, eta_d, td; expr: P*te/(eta_c*eta_d*td); numeric: yes -->

- name: leo_thirty_sixty
  inputs:
    P: 1000
    te: 1800
    eta_c: 0.92
    eta_d: 0.88
    td: 3600
  expected: 1000*1800/(0.92*0.88*3600)

### battery_orbit_source_power

<!-- family: power; symbols: P, te, eta_c, eta_d, td; expr: P*(1 + te/(eta_c*eta_d*td)); numeric: yes -->

- name: leo_thousand_watt_load
  inputs:
    P: 1000
    te: 1800
    eta_c: 0.92
    eta_d: 0.88
    td: 3600
  expected: 1000*(1 + 1800/(0.92*0.88*3600))

### orbit_average_load

<!-- family: power; symbols: P, f; expr: P*f; numeric: yes -->

- name: half_on
  inputs:
    P: 20
    f: 0.5
  expected: 10

### eclipse_load_energy

<!-- family: power; symbols: P, t; expr: P*t; numeric: yes -->

- name: twenty_watts_half_hour
  inputs:
    P: 20
    t: 1800
  expected: 36000

## Space communications

#### comms

### wavelength_from_frequency

<!-- family: comms; symbols: c, f; expr: c/f; numeric: yes -->

- name: three_hundred_megahertz
  inputs:
    c: 3e8
    f: 3e8
  expected: 1

- name: codata_speed
  inputs:
    c: 299792458
    f: 299792458
  expected: 1

### frequency_from_wavelength

<!-- family: comms; symbols: c, lam; expr: c/lam; numeric: yes -->

- name: one_metre
  inputs:
    c: 3e8
    lam: 1
  expected: 3e8

### free_space_path_loss

<!-- family: comms; symbols: pi, R, lam; expr: (4*pi*R/lam)**2; numeric: yes -->

- name: unit_geometry
  inputs:
    pi: pi
    R: 1
    lam: 4*pi
  expected: 1

- name: ten_wavelengths
  inputs:
    pi: pi
    R: 10
    lam: 1
  expected: (40*pi)**2

### free_space_path_loss_db

<!-- family: comms; symbols: pi, R, lam; expr: 20*log(4*pi*R/lam)/log(10); numeric: yes -->

- name: unit_geometry
  inputs:
    pi: pi
    R: 1
    lam: 4*pi
  expected: 0

### antenna_gain_from_effective_aperture

<!-- family: comms; symbols: pi, Ae, lam; expr: 4*pi*Ae/(lam**2); numeric: yes -->

- name: isotropic_unit
  inputs:
    pi: pi
    Ae: 1/(4*pi)
    lam: 1
  expected: 1

### antenna_gain_circular_aperture

<!-- family: comms; symbols: eta, pi, D, lam; expr: eta*(pi*D/lam)**2; numeric: yes -->

- name: half_efficiency_unit
  inputs:
    eta: 1/2
    pi: pi
    D: 2
    lam: pi
  expected: 2

- name: ideal_uniform
  inputs:
    eta: 1
    pi: pi
    D: 1
    lam: pi
  expected: 1

### eirp

<!-- family: comms; symbols: Pt, Gt; expr: Pt*Gt; numeric: yes -->

- name: ten_watts_unity_gain
  inputs:
    Pt: 10
    Gt: 1
  expected: 10

### friis_received_power

<!-- family: comms; symbols: Pt, Gt, Gr, lam, pi, R; expr: Pt*Gt*Gr*(lam/(4*pi*R))**2; numeric: yes -->

- name: unit_link
  inputs:
    Pt: 16
    Gt: 1
    Gr: 1
    lam: 4*pi
    pi: pi
    R: 1
  expected: 16

- name: with_gains
  inputs:
    Pt: 4
    Gt: 2
    Gr: 2
    lam: 4*pi
    pi: pi
    R: 1
  expected: 16

### thermal_noise_power

<!-- family: comms; symbols: k, Ts, B; expr: k*Ts*B; numeric: yes -->

- name: unit_kelvin_hertz
  inputs:
    k: 1.380649e-23
    Ts: 1
    B: 1
  expected: 1.380649e-23

### noise_spectral_density

<!-- family: comms; symbols: k, Ts; expr: k*Ts; numeric: yes -->

- name: room_like
  inputs:
    k: 1e-23
    Ts: 290
  expected: 2.9e-21

### carrier_to_noise_density

<!-- family: comms; symbols: Pr, k, Ts; expr: Pr/(k*Ts); numeric: yes -->

- name: unit_density
  inputs:
    Pr: 1.380649e-20
    k: 1.380649e-23
    Ts: 100
  expected: 10

### carrier_to_noise_ratio

<!-- family: comms; symbols: Pr, k, Ts, B; expr: Pr/(k*Ts*B); numeric: yes -->

- name: ten_to_one
  inputs:
    Pr: 1.380649e-17
    k: 1.380649e-23
    Ts: 100
    B: 1000
  expected: 10

### eb_n0_from_cn0

<!-- family: comms; symbols: CN0, Rb; expr: CN0/Rb; numeric: yes -->

- name: megabit_link
  inputs:
    CN0: 1e7
    Rb: 1e6
  expected: 10

### link_margin_eb_n0

<!-- family: comms; symbols: EbN0, EbN0req; expr: EbN0/EbN0req; numeric: yes -->

- name: three_db_linear
  inputs:
    EbN0: 20
    EbN0req: 10
  expected: 2

### required_pass_bit_rate

<!-- family: comms; symbols: bits, overhead, t; expr: bits*overhead/t; numeric: yes -->

- name: two_gigabits
  inputs:
    bits: 2e9
    overhead: 1.2
    t: 480
  expected: 5e6

### pass_data_volume

<!-- family: comms; symbols: rate, t, overhead; expr: rate*t/overhead; numeric: yes -->

- name: round_trip
  inputs:
    rate: 5e6
    t: 480
    overhead: 1.2
  expected: 2e9

### rain_specific_attenuation

<!-- family: comms; symbols: a, R, b; expr: a*R**b; numeric: yes -->

- name: square_law
  inputs:
    a: 2
    R: 3
    b: 2
  expected: 18

### rain_path_attenuation

<!-- family: comms; symbols: gamma, L; expr: gamma*L; numeric: yes -->

- name: four_kilometres
  inputs:
    gamma: 2
    L: 4
  expected: 8

### rain_power_ratio

<!-- family: comms; symbols: A; expr: 10**(-A/10); numeric: yes -->

- name: ten_decibels
  inputs:
    A: 10
  expected: 1/10

### doppler_shift

<!-- family: comms; symbols: f, vr, c; expr: f*vr/c; numeric: yes -->

- name: one_part_per_million
  inputs:
    f: 1e9
    vr: 299.792458
    c: 299792458
  expected: 1000

### orbit_mask_range_rate

<!-- family: comms; symbols: v, R, a, eps; expr: v*(R/a)*cos(eps); numeric: yes -->

- name: horizon
  inputs:
    v: 7000
    R: 2
    a: 4
    eps: 0
  expected: 3500

## Dynamics and control

#### control

### natural_frequency_mass_stiffness

<!-- family: control; symbols: k, m; expr: (k/m)**0.5; numeric: yes -->

- name: unit_mass_stiffness
  inputs:
    k: 1
    m: 1
  expected: 1

- name: four_over_one
  inputs:
    k: 4
    m: 1
  expected: 2

### damping_ratio_mass_stiffness

<!-- family: control; symbols: c, k, m; expr: c/(2*(k*m)**0.5); numeric: yes -->

- name: critical_unit
  inputs:
    c: 2
    k: 1
    m: 1
  expected: 1

- name: half_critical
  inputs:
    c: 1
    k: 1
    m: 1
  expected: 1/2

### damped_natural_frequency

<!-- family: control; symbols: wn, zeta; expr: wn*(1 - zeta**2)**0.5; numeric: yes -->

- name: undamped_unit
  inputs:
    wn: 1
    zeta: 0
  expected: 1

- name: half_damping
  inputs:
    wn: 2
    zeta: 1/2
  expected: 3**0.5

### second_order_percent_overshoot

<!-- family: control; symbols: zeta, pi; expr: exp(-pi*zeta/(1 - zeta**2)**0.5); numeric: yes -->

- name: zero_damping
  inputs:
    zeta: 0
    pi: pi
  expected: 1

- name: half_damping
  inputs:
    zeta: 1/2
    pi: pi
  expected: exp(-pi/(3**0.5))

### second_order_peak_time

<!-- family: control; symbols: wn, zeta, pi; expr: pi/(wn*(1 - zeta**2)**0.5); numeric: yes -->

- name: unit_undamped
  inputs:
    wn: 1
    zeta: 0
    pi: pi
  expected: pi

- name: half_damping
  inputs:
    wn: 2
    zeta: 1/2
    pi: pi
  expected: pi/(3**0.5)

### second_order_settling_time

<!-- family: control; symbols: delta, zeta, wn; expr: -log(delta)/(zeta*wn); numeric: yes -->

- name: two_percent_unit
  inputs:
    delta: 2/100
    zeta: 1
    wn: 1
  expected: -log(2/100)

- name: two_percent_four_time_constants
  inputs:
    delta: exp(-4)
    zeta: 1/2
    wn: 2
  expected: 4

### true_pn_commanded_acceleration

<!-- family: control; symbols: N_prime, Vc, lambda_dot; expr: N_prime*Vc*lambda_dot; numeric: yes -->

- name: three_times_thousand_times_hundredth
  inputs:
    N_prime: 3
    Vc: 1000
    lambda_dot: 1/100
  expected: 30

- name: signed_four_times_half_thousand
  inputs:
    N_prime: 4
    Vc: 500
    lambda_dot: -2/100
  expected: -40

### closing_speed

<!-- family: control; symbols: R_dot; expr: -R_dot; numeric: yes -->

- name: approaching_two_fifty
  inputs:
    R_dot: -250
  expected: 250

### los_rate

<!-- family: control; symbols: Rx, Ry, Vx, Vy, R; expr: (Rx*Vy - Ry*Vx)/R**2; numeric: yes -->

- name: three_four_closing_x
  inputs:
    Rx: 3
    Ry: 4
    Vx: -1
    Vy: 0
    R: 5
  expected: 4/25

### gravity_gradient_torque

<!-- family: control; symbols: n2, Iz, Iy, theta; expr: 1.5*n2*(Iz - Iy)*sin(2*theta); numeric: yes -->

- name: forty_five_degrees
  inputs:
    n2: 1e-6
    Iz: 12
    Iy: 10
    theta: pi/4
  expected: 3e-6

### aerodynamic_disturbance_torque

<!-- family: control; symbols: rho, V, Cd, A, d; expr: 0.5*rho*V**2*Cd*A*d; numeric: yes -->

- name: unit_dynamic_pressure
  inputs:
    rho: 2
    V: 1
    Cd: 1
    A: 1
    d: 1
  expected: 1

### solar_radiation_torque

<!-- family: control; symbols: S, A, Cr, d, c; expr: S*A*Cr*d/c; numeric: yes -->

- name: unit_factors
  inputs:
    S: 299792458
    A: 1
    Cr: 1
    d: 1
    c: 299792458
  expected: 1

### magnetic_disturbance_torque

<!-- family: control; symbols: M, B, psi; expr: M*B*sin(psi); numeric: yes -->

- name: perpendicular
  inputs:
    M: 0.2
    B: 3e-5
    psi: pi/2
  expected: 6e-6

### rest_to_rest_slew_torque

<!-- family: control; symbols: I, theta, t; expr: 4*I*theta/t**2; numeric: yes -->

- name: two_radian_ten_seconds
  inputs:
    I: 2
    theta: 1
    t: 10
  expected: 0.08

### rest_to_rest_slew_impulse

<!-- family: control; symbols: I, theta, t; expr: 2*I*theta/t; numeric: yes -->

- name: matches_half_time
  inputs:
    I: 2
    theta: 1
    t: 10
  expected: 0.4

### disturbance_momentum_storage

<!-- family: control; symbols: T, tau; expr: T*tau; numeric: yes -->

- name: one_orbit
  inputs:
    T: 1e-4
    tau: 5400
  expected: 0.54

### reaction_wheel_inertia

<!-- family: control; symbols: H, omega; expr: H/omega; numeric: yes -->

- name: hundred_radians_per_second
  inputs:
    H: 0.54
    omega: 100
  expected: 0.0054

### frequency_ratio

<!-- family: control; symbols: f, fn; expr: f/fn; numeric: yes -->

- name: twice_natural
  inputs:
    f: 2
    fn: 1
  expected: 2

### displacement_transmissibility

<!-- family: control; symbols: zeta, r; expr: ((1+(2*zeta*r)**2)/((1-r**2)**2+(2*zeta*r)**2))**0.5; numeric: yes -->

- name: isolation_corner
  inputs:
    zeta: 0.1
    r: 2**0.5
  expected: 1

### transmissibility_peak_ratio

<!-- family: control; symbols: zeta; expr: (1-2*zeta**2)**0.5; numeric: yes -->

- name: five_percent
  inputs:
    zeta: 0.5
  expected: (1/2)**0.5

### miles_rms_acceleration

<!-- family: control; symbols: pi, fn, Q, W0; expr: ((pi/2)*fn*Q*W0)**0.5; numeric: yes -->

- name: unit_rms
  inputs:
    pi: pi
    fn: 2/pi
    Q: 1
    W0: 1
  expected: 1

### magnetic_moment

<!-- family: control; symbols: T, B, psi; expr: T/(B*sin(psi)); numeric: yes -->

- name: perpendicular
  inputs:
    T: 0.01
    B: 5e-5
    psi: pi/2
  expected: 200

### magnetic_coil_current

<!-- family: control; symbols: m, N, A; expr: m/(N*A); numeric: yes -->

- name: hundred_amperes
  inputs:
    m: 200
    N: 100
    A: 0.02
  expected: 100

### bode_magnitude_db

<!-- family: control; symbols: re, im; expr: 20*log((re**2+im**2)**0.5)/log(10); numeric: yes -->

- name: unit
  inputs:
    re: 1
    im: 0
  expected: 0

- name: decade
  inputs:
    re: 10
    im: 0
  expected: 20

### bode_phase_deg

<!-- family: control; symbols: im, re, pi; expr: 2*atan(im/((re**2+im**2)**0.5+re))*180/pi; numeric: yes -->

- name: forty_five
  inputs:
    im: 1
    re: 1
    pi: pi
  expected: 45

### phase_margin_deg

<!-- family: control; symbols: phase; expr: 180+phase; numeric: yes -->

- name: typical
  inputs:
    phase: -135
  expected: 45

### gain_margin_db

<!-- family: control; symbols: mag; expr: -20*log(mag)/log(10); numeric: yes -->

- name: tenth
  inputs:
    mag: 1/10
  expected: 20

### series_pid_real

<!-- family: control; symbols: kp; expr: kp; numeric: yes -->

- name: two
  inputs:
    kp: 2
  expected: 2

### series_pid_imag

<!-- family: control; symbols: w, kd, ki; expr: w*kd-ki/w; numeric: yes -->

- name: mixed
  inputs:
    w: 2
    kd: 4
    ki: 3
  expected: 13/2

### dcm_321_c11

<!-- family: control; symbols: th, ps; expr: cos(th)*cos(ps); numeric: yes -->

- name: level
  inputs:
    th: 0
    ps: 0
  expected: 1

### dcm_321_c12

<!-- family: control; symbols: th, ps; expr: cos(th)*sin(ps); numeric: yes -->

- name: yaw_right
  inputs:
    th: 0
    ps: pi/2
  expected: 1

### dcm_321_c13

<!-- family: control; symbols: th; expr: -sin(th); numeric: yes -->

- name: level
  inputs:
    th: 0
  expected: 0

### dcm_321_c21

<!-- family: control; symbols: ph, th, ps; expr: sin(ph)*sin(th)*cos(ps)-cos(ph)*sin(ps); numeric: yes -->

- name: yaw_right
  inputs:
    ph: 0
    th: 0
    ps: pi/2
  expected: -1

### dcm_321_c22

<!-- family: control; symbols: ph, th, ps; expr: sin(ph)*sin(th)*sin(ps)+cos(ph)*cos(ps); numeric: yes -->

- name: level
  inputs:
    ph: 0
    th: 0
    ps: 0
  expected: 1

### dcm_321_c23

<!-- family: control; symbols: ph, th; expr: sin(ph)*cos(th); numeric: yes -->

- name: level
  inputs:
    ph: 0
    th: 0
  expected: 0

### dcm_321_c31

<!-- family: control; symbols: ph, th, ps; expr: cos(ph)*sin(th)*cos(ps)+sin(ph)*sin(ps); numeric: yes -->

- name: level
  inputs:
    ph: 0
    th: 0
    ps: 0
  expected: 0

### dcm_321_c32

<!-- family: control; symbols: ph, th, ps; expr: cos(ph)*sin(th)*sin(ps)-sin(ph)*cos(ps); numeric: yes -->

- name: level
  inputs:
    ph: 0
    th: 0
    ps: 0
  expected: 0

### dcm_321_c33

<!-- family: control; symbols: ph, th; expr: cos(ph)*cos(th); numeric: yes -->

- name: level
  inputs:
    ph: 0
    th: 0
  expected: 1

### quaternion_to_dcm_c11

<!-- family: control; symbols: q0, q1, q2, q3; expr: q0**2+q1**2-q2**2-q3**2; numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 1

### quaternion_to_dcm_c12

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q1*q2+q0*q3); numeric: yes -->

- name: yaw_right
  inputs:
    q0: 2**(-0.5)
    q1: 0
    q2: 0
    q3: 2**(-0.5)
  expected: 1

### quaternion_to_dcm_c13

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q1*q3-q0*q2); numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 0

### quaternion_to_dcm_c21

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q1*q2-q0*q3); numeric: yes -->

- name: yaw_right
  inputs:
    q0: 2**(-0.5)
    q1: 0
    q2: 0
    q3: 2**(-0.5)
  expected: -1

### quaternion_to_dcm_c22

<!-- family: control; symbols: q0, q1, q2, q3; expr: q0**2-q1**2+q2**2-q3**2; numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 1

### quaternion_to_dcm_c23

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q2*q3+q0*q1); numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 0

### quaternion_to_dcm_c31

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q1*q3+q0*q2); numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 0

### quaternion_to_dcm_c32

<!-- family: control; symbols: q0, q1, q2, q3; expr: 2*(q2*q3-q0*q1); numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 0

### quaternion_to_dcm_c33

<!-- family: control; symbols: q0, q1, q2, q3; expr: q0**2-q1**2-q2**2+q3**2; numeric: yes -->

- name: identity
  inputs:
    q0: 1
    q1: 0
    q2: 0
    q3: 0
  expected: 1

### quaternion_rate_0

<!-- family: control; symbols: wx, wy, wz, q1, q2, q3; expr: 0.5*(-wx*q1-wy*q2-wz*q3); numeric: yes -->

- name: identity_roll
  inputs:
    wx: 2
    wy: 0
    wz: 0
    q1: 0
    q2: 0
    q3: 0
  expected: 0

### quaternion_rate_1

<!-- family: control; symbols: wx, wy, wz, q0, q2, q3; expr: 0.5*(wx*q0+wz*q2-wy*q3); numeric: yes -->

- name: identity_roll
  inputs:
    wx: 2
    wy: 0
    wz: 0
    q0: 1
    q2: 0
    q3: 0
  expected: 1

### quaternion_rate_2

<!-- family: control; symbols: wx, wy, wz, q0, q1, q3; expr: 0.5*(wy*q0-wz*q1+wx*q3); numeric: yes -->

- name: identity_roll
  inputs:
    wx: 2
    wy: 0
    wz: 0
    q0: 1
    q1: 0
    q3: 0
  expected: 0

### quaternion_rate_3

<!-- family: control; symbols: wx, wy, wz, q0, q1, q2; expr: 0.5*(wz*q0+wy*q1-wx*q2); numeric: yes -->

- name: identity_roll
  inputs:
    wx: 2
    wy: 0
    wz: 0
    q0: 1
    q1: 0
    q2: 0
  expected: 0

### euler_rate_roll

<!-- family: control; symbols: wx, wy, wz, ph, th; expr: wx+sin(ph)*tan(th)*wy+cos(ph)*tan(th)*wz; numeric: yes -->

- name: level
  inputs:
    wx: 1
    wy: 2
    wz: 3
    ph: 0
    th: 0
  expected: 1

### euler_rate_pitch

<!-- family: control; symbols: wy, wz, ph; expr: cos(ph)*wy-sin(ph)*wz; numeric: yes -->

- name: level
  inputs:
    wy: 2
    wz: 3
    ph: 0
  expected: 2

### euler_rate_yaw

<!-- family: control; symbols: wy, wz, ph, th; expr: sin(ph)*wy/cos(th)+cos(ph)*wz/cos(th); numeric: yes -->

- name: level
  inputs:
    wy: 2
    wz: 3
    ph: 0
    th: 0
  expected: 3

### euler_pitch_from_dcm

<!-- family: control; symbols: c13; expr: asin(-c13); numeric: yes -->

- name: level
  inputs:
    c13: 0
  expected: 0

### euler_roll_from_dcm

<!-- family: control; symbols: c23, c33; expr: atan(c23/c33); numeric: yes -->

- name: level
  inputs:
    c23: 0
    c33: 1
  expected: 0

### euler_yaw_from_dcm

<!-- family: control; symbols: c12, c11; expr: atan(c12/c11); numeric: yes -->

- name: yaw_right
  inputs:
    c12: 1
    c11: 1
  expected: pi/4

### quaternion_scalar_from_dcm

<!-- family: control; symbols: c11, c22, c33; expr: 0.5*(1+c11+c22+c33)**0.5; numeric: yes -->

- name: identity
  inputs:
    c11: 1
    c22: 1
    c33: 1
  expected: 1

### quaternion_q1_from_dcm

<!-- family: control; symbols: c23, c32, q0; expr: (c23-c32)/(4*q0); numeric: yes -->

- name: identity
  inputs:
    c23: 0
    c32: 0
    q0: 1
  expected: 0

### quaternion_q2_from_dcm

<!-- family: control; symbols: c31, c13, q0; expr: (c31-c13)/(4*q0); numeric: yes -->

- name: identity
  inputs:
    c31: 0
    c13: 0
    q0: 1
  expected: 0

### quaternion_q3_from_dcm

<!-- family: control; symbols: c12, c21, q0; expr: (c12-c21)/(4*q0); numeric: yes -->

- name: yaw_right
  inputs:
    c12: 1
    c21: -1
    q0: 2**(-0.5)
  expected: 2**(-0.5)

## Structures

### principal_stress_max

- name: bending_plus_shear
  inputs:
    sx: 100
    sy: 0
    tau: 50
  expected: 50 + (50**2 + 50**2)**0.5

### principal_stress_min

- name: bending_plus_shear
  inputs:
    sx: 100
    sy: 0
    tau: 50
  expected: 50 - (50**2 + 50**2)**0.5

### mohr_center

- name: uniaxial
  inputs:
    sx: 100
    sy: 0
  expected: 50

### mohr_radius

- name: bending_plus_shear
  inputs:
    sx: 100
    sy: 0
    tau: 50
  expected: (50**2 + 50**2)**0.5

### max_shear_from_mohr

- name: bending_plus_shear
  inputs:
    sx: 100
    sy: 0
    tau: 50
  expected: (50**2 + 50**2)**0.5

### goodman_factor

- name: quarter_mean
  inputs:
    sa: 100
    se: 200
    sm: 100
    sut: 400
  expected: 1/(0.5 + 0.25)

### soderberg_factor

- name: yield_intercept
  inputs:
    sa: 100
    se: 200
    sm: 100
    sy: 300
  expected: 1/(0.5 + 100/300)

### goodman_allowable_alternating

- name: quarter_mean
  inputs:
    se: 200
    sm: 100
    sut: 400
  expected: 150

## Aerodynamics

### vertical_tail_volume

- name: sample
  inputs:
    sv: 2
    lv: 5
    S: 20
    b: 10
  expected: 0.05

### cn_beta_vertical_tail

- name: sample
  inputs:
    av: 2
    Vv: 0.05
    eta: 1
  expected: 0.1

### cl_beta_geometric_dihedral

- name: rectangular
  inputs:
    aw: 4
    gamma: 0.1
    lam: 1
  expected: -0.1

### level_flight_lift_coefficient

- name: cruise
  inputs:
    W: 1000
    q: 500
    S: 10
  expected: 0.2

### cm_alpha_from_static_margin

- name: ten_percent
  inputs:
    a: 5
    kn: 0.1
  expected: -0.5

### trim_angle_of_attack

- name: cruise
  inputs:
    CL: 0.2
    a: 5
  expected: 0.04

### trim_elevator

- name: sample
  inputs:
    cm0: 0.05
    cma: -0.5
    alpha: 0.04
    cmde: -0.8
  expected: 0.0375

### force_scale_dynamic_pressure

- name: double_q
  inputs:
    q2: 2
    S2: 3
    q1: 1
    S1: 2
  expected: 3

### moment_scale_dynamic_pressure

- name: chord_ratio
  inputs:
    q2: 2
    S2: 3
    c2: 4
    q1: 1
    S1: 2
    c1: 2
  expected: 6

### relative_mismatch

- name: ten_percent
  inputs:
    a: 1.1
    b: 1
  expected: 0.1

## Rocket propulsion

### planar_rotate_x

- name: quarter_turn
  inputs:
    vx: 3
    vy: 4
    ang: pi/2
  expected: -4

### planar_rotate_y

- name: quarter_turn
  inputs:
    vx: 3
    vy: 4
    ang: pi/2
  expected: 3

### planar_speed

- name: three_four
  inputs:
    vx: 3
    vy: 4
  expected: 5

### vector_difference_speed

- name: unit_step
  inputs:
    vx2: 1
    vy2: 0
    vx1: 0
    vy1: 0
  expected: 1

### flyby_kinetic_change

- name: faster
  inputs:
    vout: 3
    vin: 1
  expected: 4
