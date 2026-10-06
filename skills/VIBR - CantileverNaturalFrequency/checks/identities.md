# Cantilever natural-frequency identities

Named numeric checks for the script records in `../formulas.md`. The program `--check` path exercises the same cases.

## Vibration

#### vibration

### cantilever_lambda1_L

<!-- family: vibration; symbols: ; expr: 1.875104; numeric: yes -->

- name: stanek_mode1
  inputs: {}
  expected: 1.87510
  note: NASA TN D-2831 mode-1 root to five decimals; program constant agrees within 5e-6

- name: six_digit_classic
  inputs: {}
  expected: 1.875104

### cantilever_omega_bending_1

<!-- family: vibration; symbols: lambda1_L, E, I, mu, L; expr: (lambda1_L)**2 * sqrt(E*I/(mu*L**4)); numeric: yes -->

- name: unit_beam
  inputs:
    lambda1_L: 1.875104
    E: 1
    I: 1
    mu: 1
    L: 1
  expected: (1.875104)**2

- name: aluminum_sample
  inputs:
    lambda1_L: 1.875104
    E: 7e10
    I: 1e-8
    mu: 0.5
    L: 1
  expected: (1.875104)**2 * sqrt(7e10*1e-8/(0.5*1**4))

### cantilever_freq_hz

<!-- family: vibration; symbols: omega_n, pi; expr: omega_n/(2*pi); numeric: yes -->

- name: unit_hz
  inputs:
    omega_n: (1.875104)**2
    pi: pi
  expected: (1.875104)**2/(2*pi)

- name: sample_hz
  inputs:
    omega_n: (1.875104)**2 * sqrt(7e10*1e-8/(0.5*1**4))
    pi: pi
  expected: (1.875104)**2 * sqrt(7e10*1e-8/(0.5*1**4))/(2*pi)

### cantilever_mu_from_mass

<!-- family: vibration; symbols: m_beam, L; expr: m_beam/L; numeric: yes -->

- name: unit_mu
  inputs:
    m_beam: 1
    L: 1
  expected: 1

- name: half_metre_beam
  inputs:
    m_beam: 0.5
    L: 1
  expected: 0.5
