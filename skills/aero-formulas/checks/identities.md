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

### burn_rate_temperature_sensitivity

<!-- family: rocket; symbols: r, Tb; expr: (1/r)*partial(r, Tb); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is an unevaluated derivative of burning rate with respect to propellant temperature. -->

### pressure_temperature_sensitivity

<!-- family: rocket; symbols: p1, p, Tb; expr: (1/p1)*partial(p, Tb); numeric: no (unevaluated derivative) -->

<!-- No scalar identity: the script is an unevaluated derivative of chamber pressure with respect to propellant temperature. -->

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
