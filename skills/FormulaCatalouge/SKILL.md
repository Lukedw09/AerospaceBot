---
name: FormulaCatalouge
description: >-
  Select a checked aerospace formula from the skill reference using the user's
  context, then either calculate with it or present it with every variable and
  unit defined. Use when the user asks for an aerospace equation, a flight or
  orbital calculation, atmosphere properties, a motor-case stress or margin of
  safety, elastic Euler column buckling load or critical stress, center of mass or rigid-body inertia, stagnation-point heating,
  radiative-equilibrium wall temperature, Allen-Eggers ballistic-entry peak
  deceleration or peak-load altitude in an exponential atmosphere, solar-array beginning- or end-of-life
  power, circular-orbit eclipse fraction, battery usable energy or required
  capacity with depth of discharge and charge/discharge efficiency, vacuum
  free-space path loss, Friis received power, antenna gain from aperture
  efficiency, carrier-to-noise, Eb/N0, link margin, linear second-order step
  overshoot or settling time, true proportional navigation commanded
  acceleration or closing speed, Hohmann phase angle, synodic period, inclined
  excess speed,   ideal Brayton turbojet specific thrust or TSFC,
  ideal Brayton ramjet specific thrust or TSFC, design-point inlet
  recovery, non-ideal turbojet or afterburner fuel flow, separate-stream
  turbofan thrust, or engine airflow sizing, 1976 density above 86 km,
  spacecraft radiative balance, disturbance torques, drag delta-v, in-space
  propellant, pass data volume, duty-cycled load, or what a formula's symbols and
  units mean. Use only formulas listed in checks/check.md. Definitions listed
  there are exempt from the identity check.
---

# Aero Formulas

Read [formulas.md](formulas.md) before answering. Use only a formula whose id is listed in [checks/check.md](checks/check.md). A definition listed there is exempt from the identity check. Any other listed formula passed its identity checks. If `checks/check.md` is missing, or the id is not listed there, say the formula is not allowed. Do not calculate with it, and do not present it as an allowed formula.

## Select the formula

1. Start in the category that matches the question: Compressible flow, Atmosphere (including 1976 density above 86 km), Rocket propulsion (including two-body orbits and anomalies, injector orifice flow, feed-system pressure, pump power, Bartz throat heat flux, regenerative coolant heat pickup, and in-space propellant), Aerodynamics (including ideal propeller, ideal Brayton turbojet, ideal Brayton ramjet, design-point inlet recovery, non-ideal turbojet, afterburner, separate-stream turbofan, airflow sizing, and drag delta-v), Structures, Mass properties, Aerothermodynamics (including spacecraft radiative balance), Spacecraft power (including duty-cycled load), Space communications (including pass data volume), or Dynamics and control (including second-order response, true proportional navigation, and disturbance torques). Read another category only if that one does not contain a fit.
2. Use the user's wording, known quantities, and requested result to choose the formula that fits.
3. Reject any formula that is not listed in [checks/check.md](checks/check.md). A listed definition is allowed.
4. If more than one listed formula fits, choose the one that uses the quantities the user already has. If the choice is still ambiguous, ask which result they want before calculating.
5. If none of the listed formulas fit, say so. Do not invent a formula, and do not use a formula that is absent from [checks/check.md](checks/check.md).

## Respond in one of two ways

**Calculate** when the user gives enough known values to solve and the formula is listed in `checks/check.md`.

- State the formula.
- Define every variable and its unit.
- Compute from that formula's script `expr` when the expr is an ordinary numeric expression.
- If the definition's expr is `partial(...)` or an indefinite `integral(...)`, present the definition. Do not invent a numeric derivative or integral.
- Substitute the user's values in consistent units.
- Give the numeric result with its unit when a numeric expr was used.

**Present** when the user asks for the equation itself, or when known values are missing. Present only a formula listed in `checks/check.md`, including a definition.

- State the formula.
- Define every variable by name.
- Give the unit of every variable.
- Do not invent values or compute a result.
