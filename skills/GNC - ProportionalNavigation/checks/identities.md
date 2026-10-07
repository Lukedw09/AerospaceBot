# Proportional navigation identities

Named numeric checks for the script records in `../formulas.md`. The program `--check` path exercises the same Mode 1 cases and one Mode 2 engagement regression.

## Dynamics and control

#### control

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
