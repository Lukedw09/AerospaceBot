# AerospaceBot

Cursor agent skills for aerospace engineering: checked formulas and small physics programs the bot can run and report, instead of reinventing equations or redrawing plots by hand.

## Skills

| Skill | Purpose |
| --- | --- |
| [`aero-formulas`](skills/aero-formulas) | Select and use verified aerospace formulas (compressible flow, atmosphere, rocket propulsion, aerodynamics, structures). Only formulas listed in `checks/check.md` are allowed. |
| [`ROCKET - Area-Mach Graph`](skills/ROCKET%20-%20Area-Mach%20Graph) | Run `area_mach.py` for an isentropic nozzle area-Mach curve, exit Mach from area ratio, exit pressure, ideal thrust, and expansion state. |
| [`ROCKET - PerformanceParameters`](skills/ROCKET%20-%20PerformanceParameters) | Run `performance.py` for frozen-CEA c*, temperature, gamma, ideal Cf, specific impulse, and density impulse. Do not call CEA at reply time. |
| [`ROCKET - ThroatSizingandMassFlow`](skills/ROCKET%20-%20ThroatSizingandMassFlow) | Run `throat_sizing.py` for circular-throat area and diameter from thrust, thrust coefficient, and chamber pressure, and mass flow from characteristic velocity. |
| [`ROCKET - PropellantLoad`](skills/ROCKET%20-%20PropellantLoad) | Run `propellant_load.py` for usable propellant mass and tank volume (total, oxidizer, fuel) from mass flow, burn time, mixture ratio, and liquid densities. |
| [`ROCKET - ExpansionMatchEarth`](skills/ROCKET%20-%20ExpansionMatchEarth) | Run `expansion_match.py` for the altitude-matched nozzle expansion ratio on the 1976 U.S. Standard Atmosphere. Area ratio and ideal \(C_F\) come from Area-Mach. |
| [`ROCKET - PayloadtoDeltaV`](skills/ROCKET%20-%20PayloadtoDeltaV) | Run `payload_to_deltav.py` for useful payload from ideal delta-v, or ideal delta-v from useful payload, for one or more stages. A missing delta-v and payload writes a payload-versus-delta-v PNG. |
| [`ROCKET - LossStack`](skills/ROCKET%20-%20LossStack) | Run `loss_stack.py` for actual thrust, specific impulse, thrust coefficient, c*, and mass flow from ideal \(C_F\), ideal \(c^{*}\), and named efficiencies. With throat area and chamber pressure it also prints the lossless thrust and mass flow. Omitted efficiencies stay 1. |
| [`ROCKET - ChamberVolumeAndCaseHoopStress`](skills/ROCKET%20-%20ChamberVolumeAndCaseHoopStress) | Run `chamber_case.py` for chamber volume from throat area and \(L^{*}\), and thin-wall hoop stress and margin of safety from pressure, case radius, wall thickness, and allowable stress. |
| [`ASTRO - HohmannTransfer`](skills/ASTRO%20-%20HohmannTransfer) | Run `hohmann_transfer.py` for circular speed, escape speed, specific energy, impulsive delta-v, and coast time between two circular orbits. Writes a PNG of the transfer. |
| [`ATMOS - Standard1976`](skills/ATMOS%20-%20Standard1976) | Run `standard_1976.py` for 1976 U.S. Standard Atmosphere temperature, pressure, density, speed of sound, and geometric pressure scale height at one geometric altitude from sea level through 86 km. |
| [`AERO - PrandtlMeyerAndShocks`](skills/AERO%20-%20PrandtlMeyerAndShocks) | Run `prandtl_meyer_and_shocks.py` for the weak oblique-shock angle, downstream Mach, and static-pressure ratio on a two-dimensional wedge, the Prandtl-Meyer expansion through the same deflection, and whether the shock is attached. |
| [`AERO - AirplanePerformanceParameters`](skills/AERO%20-%20AirplanePerformanceParameters) | Run `airplane_performance.py` for stall speed, maximum lift-to-drag ratio, jet and propeller best-range and best-endurance speeds, and a sea-level climb estimate from a parabolic drag polar. |
| [`AERO - WingGeometry`](skills/AERO%20-%20WingGeometry) | Run `wing_geometry.py` for trapezoidal wing area, aspect ratio, taper ratio, mean aerodynamic chord, and the spanwise station of that chord. An optional sweep is drawn on the plan view. |
| [`AERO - V-nDiagram`](skills/AERO%20-%20V-nDiagram) | Run `vn_diagram.py` for the positive stall boundary and corner speed from weight, wing area, \(C_{L,\max}\), limit load factors, and air density. The PNG plots load factor against equivalent airspeed. |
| [`AERO - FiniteWingLiftCurve`](skills/AERO%20-%20FiniteWingLiftCurve) | Run `finite_wing_lift_curve.py` for the wing lift-curve slope and the induced angle at \(C_{L,\max}\) from a section slope, zero-lift angle, aspect ratio, and span efficiency. The PDF is lift coefficient versus angle of attack up to stall. |
| [`AERO - EquivalentAirspeed`](skills/AERO%20-%20EquivalentAirspeed) | Run `equivalent_airspeed.py` for Mach number, dynamic pressure, equivalent airspeed, and Reynolds number from a geometric altitude and either true airspeed or Mach number on the 1976 standard atmosphere. |
| [`AERO - LongitudinalStaticMargin`](skills/AERO%20-%20LongitudinalStaticMargin) | Run `longitudinal_static_margin.py` for the stick-fixed neutral point and static margin from the wing-fuselage and tail lift-curve slopes, downwash, tail dynamic-pressure ratio, tail geometry, and center-of-gravity position. |

Each skill has a `SKILL.md` that tells the agent when to use it and how to respond.

## Repository layout

```text
skills/
  aero-formulas/
    SKILL.md
    formulas.md          # formula reference
    checks/              # identity checks and allow-list
  ROCKET - Area-Mach Graph/
    SKILL.md
    area_mach.py         # nozzle area-Mach program (PNG + key: value stdout)
  ROCKET - PerformanceParameters/
    SKILL.md
    scripts/pairs.json   # propellant pairs, OF grids, density constants
    scripts/build_table.py  # offline CEA table builder
    src/load_table.py
    src/performance.py   # performance program (key: value stdout, optional PNG)
  ROCKET - ThroatSizingandMassFlow/
    SKILL.md
    throat_sizing.py     # throat area, diameter, and mass flow (key: value stdout)
  ROCKET - PropellantLoad/
    SKILL.md
    propellant_load.py   # propellant mass and volume (key: value stdout)
  ROCKET - ExpansionMatchEarth/
    SKILL.md
    expansion_match.py   # optimal expansion ratio versus altitude (key: value stdout, optional PNG)
  ROCKET - PayloadtoDeltaV/
    SKILL.md
    payload_to_deltav.py # payload versus ideal delta-v (key: value stdout, sweep PNG)
  ROCKET - LossStack/
    SKILL.md
    loss_stack.py        # delivered CF, c*, Isp, thrust, and mass flow (key: value stdout)
  ROCKET - ChamberVolumeAndCaseHoopStress/
    SKILL.md
    chamber_case.py      # chamber volume, hoop stress, margin of safety (key: value stdout)
  ATMOS - Standard1976/
    SKILL.md
    standard_1976.py     # 1976 temperature, pressure, density, sound speed, scale height
  ASTRO - HohmannTransfer/
    SKILL.md
    hohmann_transfer.py  # Hohmann delta-v and coast (key: value stdout, PNG)
  AERO - AirplanePerformanceParameters/
    SKILL.md
    airplane_performance.py  # stall, L/D, range and endurance speeds, sea-level climb
  AERO - PrandtlMeyerAndShocks/
    SKILL.md
    prandtl_meyer_and_shocks.py  # wedge shock and Prandtl-Meyer expansion (key: value stdout, PNG)
  AERO - WingGeometry/
    SKILL.md
    wing_geometry.py     # trapezoidal planform (key: value stdout, PNG)
  AERO - V-nDiagram/
    SKILL.md
    vn_diagram.py        # stall boundary and corner speed (key: value stdout, PNG)
  AERO - FiniteWingLiftCurve/
    SKILL.md
    finite_wing_lift_curve.py  # wing slope, induced angle, lift curve to stall (PDF)
  AERO - EquivalentAirspeed/
    SKILL.md
    equivalent_airspeed.py  # Mach, dynamic pressure, equivalent airspeed, Reynolds number
  AERO - LongitudinalStaticMargin/
    SKILL.md
    longitudinal_static_margin.py  # stick-fixed neutral point and static margin (key: value stdout)
```

## Requirements

- **aero-formulas** — no extra runtime; the agent reads the markdown references.
- **ROCKET - Area-Mach Graph** — Python 3 with `numpy` and `matplotlib`.
- **ROCKET - PerformanceParameters** — Python 3 with `numpy` and `matplotlib`. Frozen tables are produced offline by `scripts/build_table.py` (`rocketcea`). A reply does not call CEA.
- **ROCKET - ThroatSizingandMassFlow** — Python 3 standard library only.
- **ROCKET - PropellantLoad** — Python 3 standard library only. Pair densities are read from `ROCKET - PerformanceParameters` `scripts/pairs.json`.
- **ROCKET - ExpansionMatchEarth** — Python 3 with `numpy` and `matplotlib`, because it calls `ROCKET - Area-Mach Graph`. It does not call CEA.
- **ROCKET - PayloadtoDeltaV** — Python 3 standard library for a point result. A delta-v sweep also needs `matplotlib`.
- **ROCKET - LossStack** — Python 3 standard library only.
- **ROCKET - ChamberVolumeAndCaseHoopStress** — Python 3 standard library only.
- **ASTRO - HohmannTransfer** — Python 3 with `matplotlib`.
- **ATMOS - Standard1976** — Python 3 standard library only. Hydrostatic model from sea level through 86 km. It does not use the NASA Glenn three-zone fit.
- **AERO - PrandtlMeyerAndShocks** — Python 3 with `matplotlib`. Deflection is in radians. A two-dimensional wedge, not a cone.
- **AERO - AirplanePerformanceParameters** — Python 3 standard library only. Sea-level density and an altitude lookup both come from `ATMOS - Standard1976`. A climb rate needs `--thrust` or `--power`.
- **AERO - WingGeometry** — Python 3 with `matplotlib`. Chords are streamwise. Sweep is in radians. An omitted sweep draws an unswept leading edge. An omitted sweep station is the quarter chord.
- **AERO - V-nDiagram** — Python 3 with `matplotlib`. Equivalent airspeed is `stall_speed` at 1976 sea-level density from `ATMOS - Standard1976`. True airspeeds use `--rho`. The negative line is the limit load factor. The plot end is not a dive speed.
- **AERO - FiniteWingLiftCurve** — Python 3 with `matplotlib`. Angles are radians. The section slope is per radian. Span efficiency satisfies \(0 < e \le 1\). The PDF ends at stall.
- **AERO - EquivalentAirspeed** — Python 3 standard library only. Temperature, pressure, density, and sound speed come from `ATMOS - Standard1976`. Equivalent airspeed is `freestream_dynamic_pressure` at 1976 sea-level density. It is not calibrated airspeed. An omitted length is 1 m.
- **AERO - LongitudinalStaticMargin** — Python 3 standard library only. Stick-fixed TN 1670 equation (6). \(l\) is measured from the neutral point. \(q_T/q\) is the tail dynamic-pressure ratio. Both lift-curve slopes use the same angle unit.

Example:

```bash
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --gamma 1.25
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --check
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --thrust 1500 --cf 1.5 --pc 2e6 --cstar 1600
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --check
python "skills/ROCKET - PropellantLoad/propellant_load.py" --mdot 4 --tb 10 --r 2.3 --pair LOX/RP1
python "skills/ROCKET - PropellantLoad/propellant_load.py" --check
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --stages 1 --stage mp=100,inert=10,isp-vac=300 --payload 5
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --check
python "skills/ROCKET - LossStack/loss_stack.py" --cf 1.5 --cstar 1600 --throat 5e-4 --pc 2e6 --eta combustion=0.98 --eta nozzle=0.97
python "skills/ROCKET - LossStack/loss_stack.py" --check
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --throat 0.0005 --lstar 1.2 --pc 2e6 --radius 0.05 --thickness 0.002 --allowable 6.25e7
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --check
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --r1 6774200 --r2 7374200
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --alt 400000 --ecc 0.2
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --check
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --pc 2e6 --gamma 1.25 --alt 0
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --check
python "skills/ATMOS - Standard1976/standard_1976.py" --alt 11000
python "skills/ATMOS - Standard1976/standard_1976.py" --check
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --weight 10000 --area 16 --cd0 0.02 --ar 8 --e 0.8 --clmax 1.6 --alt 0
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --check
python "skills/AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py" --mach 2 --delta 0.174533
python "skills/AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py" --check
python "skills/AERO - WingGeometry/wing_geometry.py" --span 10 --root 2 --tip 1 --sweep 0.523598775598
python "skills/AERO - WingGeometry/wing_geometry.py" --check
python "skills/AERO - V-nDiagram/vn_diagram.py" --weight 10000 --area 16 --clmax 1.6 --n-pos 3.8 --n-neg -1.52 --rho 1.225
python "skills/AERO - V-nDiagram/vn_diagram.py" --check
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --a0 6.28318530718 --alpha-l0 -0.03490658504 --clmax 1.4 --ar 8 --e 0.8
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --check
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --alt 11000 --mach 0.8
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --check
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --a 5 --at 4 --downwash 0.4 --q-ratio 0.9 --tail-area 2 --tail-length 5 --wing-area 10 --mac 1 --cg 0.1
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --check
```

## Units

SI is the working system (Pa, m², N). Skills convert other units before calling programs and state the units used in the reply.

## License

No license file is included yet. Treat the repository as private unless a license is added.
