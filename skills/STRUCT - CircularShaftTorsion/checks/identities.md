# Circular shaft torsion identities

Named numeric checks for the script records in `../formulas.md`. The program `--check` path exercises the same cases.

## Structures

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
