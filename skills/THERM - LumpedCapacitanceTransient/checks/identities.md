# Lumped-capacitance transient identities

Named numeric checks for the script records in `../formulas.md`. The program `--check` path exercises the same cases.

## Aerothermodynamics

#### aerotherm

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
