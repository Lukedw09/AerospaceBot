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
| [`ROCKET - SolidMotorParameters`](skills/ROCKET%20-%20SolidMotorParameters) | Run `solid_motor_parameters.py` for burning-area ratio, equilibrium chamber pressure, burn rate, and solid-propellant mass flow from Saint Robert burn-rate inputs, grain and throat areas, density, and \(c^{*}\). |
| [`ROCKET - CircularPortGrainHistory`](skills/ROCKET%20-%20CircularPortGrainHistory) | Run `circular_port_grain_history.py` for chamber pressure, burning-area ratio, and remaining web versus time of an internal-burning circular grain with inhibited ends. Writes a PNG of the three histories. |
| [`ASTRO - HohmannTransfer`](skills/ASTRO%20-%20HohmannTransfer) | Run `hohmann_transfer.py` for circular speed, escape speed, specific energy, impulsive delta-v, and coast time between two circular orbits. Writes a PNG of the transfer. |
| [`ASTRO - OrbitalParameters`](skills/ASTRO%20-%20OrbitalParameters) | Run `orbital_parameters.py` for classical elements and the inertial state of a Keplerian conic, either direction. Writes a PNG of the orbit and a self-contained HTML viewer. |
| [`ASTRO - PlaneChangeImpulse`](skills/ASTRO%20-%20PlaneChangeImpulse) | Run `plane_change_impulse.py` for the impulsive delta-v of a pure inclination change at the ascending or descending node. Writes a PNG of both planes and a self-contained HTML viewer. |
| [`ASTRO - GroundTrackEarth`](skills/ASTRO%20-%20GroundTrackEarth) | Run `ground_track_earth.py` for the geodetic latitude and longitude of the subsatellite point over ten orbital periods by default, from elements or an inertial state plus the Greenwich angle at epoch. Writes a PNG of the track on a public-domain Natural Earth land map. |
| [`ATMOS - Standard1976`](skills/ATMOS%20-%20Standard1976) | Run `standard_1976.py` for 1976 U.S. Standard Atmosphere temperature, pressure, density, speed of sound, and geometric pressure scale height at one geometric altitude from sea level through 86 km. |
| [`AERO - PrandtlMeyerAndShocks`](skills/AERO%20-%20PrandtlMeyerAndShocks) | Run `prandtl_meyer_and_shocks.py` for the weak oblique-shock angle, downstream Mach, and static-pressure ratio on a two-dimensional wedge, the Prandtl-Meyer expansion through the same deflection, and whether the shock is attached. |
| [`AERO - ConicalShock`](skills/AERO%20-%20ConicalShock) | Run `conical_shock.py` for the attached shock angle, surface Mach, and surface pressure coefficient of a right circular cone at zero incidence. |
| [`AERO - DiamondAirfoilShockExpansion`](skills/AERO%20-%20DiamondAirfoilShockExpansion) | Run `diamond_airfoil_shock_expansion.py` for the four panel pressures and section lift and drag of a symmetric diamond airfoil by shock-expansion theory. Writes a PNG of the waves. |
| [`AERO - AirplanePerformanceParameters`](skills/AERO%20-%20AirplanePerformanceParameters) | Run `airplane_performance.py` for stall speed, maximum lift-to-drag ratio, jet and propeller best-range and best-endurance speeds, and a sea-level climb estimate from a parabolic drag polar. |
| [`AERO - BreguetRangeEndurance`](skills/AERO%20-%20BreguetRangeEndurance) | Run `breguet_range_endurance.py` for jet and propeller Breguet cruise range and endurance from lift-to-drag ratio, specific fuel consumption, cruise speed, propeller efficiency, and start and end weight. |
| [`AERO - WingGeometry`](skills/AERO%20-%20WingGeometry) | Run `wing_geometry.py` for trapezoidal wing area, aspect ratio, taper ratio, mean aerodynamic chord, and the spanwise station of that chord. An optional sweep is drawn on the plan view. |
| [`AERO - V-nDiagram`](skills/AERO%20-%20V-nDiagram) | Run `vn_diagram.py` for the positive stall boundary and corner speed from weight, wing area, \(C_{L,\max}\), limit load factors, and air density. The PNG plots load factor against equivalent airspeed. |
| [`AERO - IncompressibleLevelTurn`](skills/AERO%20-%20IncompressibleLevelTurn) | Run `incompressible_level_turn.py` for coordinated level-turn radius, rate, bank, and load factor from speed, weight, wing area, \(C_{L,\max}\), air density, and either bank, load factor, or a sustained load factor from thrust or power on a parabolic polar. Incompressible \(q=\frac12\rho V^{2}\). The PNG plots radius and rate against true airspeed with the stall limit marked; thrust or power also plots sustained load factor against speed. |
| [`AERO - IdealPropeller`](skills/AERO%20-%20IdealPropeller) | Run `ideal_propeller.py` for ideal actuator-disk thrust, induced velocity, and propulsive efficiency from shaft power, propeller diameter, flight speed, and air density or altitude. The PNG plots those three quantities against true airspeed. Ideal thrust or useful power \(T V\) can feed `AERO - IncompressibleLevelTurn`. |
| [`AERO - FiniteWingLiftCurve`](skills/AERO%20-%20FiniteWingLiftCurve) | Run `finite_wing_lift_curve.py` for the wing lift-curve slope and the induced angle at \(C_{L,\max}\) from a section slope, zero-lift angle, aspect ratio, and span efficiency. The PDF is lift coefficient versus angle of attack up to stall. |
| [`AERO - EquivalentAirspeed`](skills/AERO%20-%20EquivalentAirspeed) | Run `equivalent_airspeed.py` for Mach number, dynamic pressure, equivalent airspeed, and Reynolds number from a geometric altitude and either true airspeed or Mach number on the 1976 standard atmosphere. |
| [`AERO - DensityAndPressureAltitude`](skills/AERO%20-%20DensityAndPressureAltitude) | Run `density_and_pressure_altitude.py` for dry or moist density, speed of sound, and 1976 pressure and density altitudes from station pressure and outside air temperature. Optional relative humidity and equivalent airspeed. |
| [`AERO - LongitudinalStaticMargin`](skills/AERO%20-%20LongitudinalStaticMargin) | Run `longitudinal_static_margin.py` for the stick-fixed neutral point and static margin from the wing-fuselage and tail lift-curve slopes, downwash, tail dynamic-pressure ratio, tail geometry, and center-of-gravity position. |
| [`AERO - RayleighPitotMach`](skills/AERO%20-%20RayleighPitotMach) | Run `rayleigh_pitot_mach.py` for freestream Mach number and dynamic pressure from measured pitot pressure, freestream static pressure, and \(\gamma\). Below Mach 1 uses isentropic stagnation; above Mach 1 uses the Rayleigh-Pitot relation. |
| [`AERO - PrandtGlauertCorrectionandCriticalMach`](skills/AERO%20-%20PrandtGlauertCorrectionandCriticalMach) | Run `prandtl_glauert_correction_and_critical_mach.py` for the two-dimensional Prandtl-Glauert correction of an incompressible lift or minimum pressure coefficient, and the critical Mach number from that suction peak. |
| [`AERO - NACAFourDigitSection`](skills/AERO%20-%20NACAFourDigitSection) | Run `naca_four_digit_section.py` for the mean line, surface ordinates, and NACA Report 824 measured section lift, moment, and drag of a NACA four-digit airfoil. Writes PNGs of the section, coefficients versus angle of attack in degrees, and the drag polar. |

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
  ROCKET - SolidMotorParameters/
    SKILL.md
    solid_motor_parameters.py  # solid-motor K, pc, burn rate, mass flow (key: value stdout)
  ROCKET - CircularPortGrainHistory/
    SKILL.md
    circular_port_grain_history.py  # circular-port pc, K, remaining web versus time (PNG)
  ATMOS - Standard1976/
    SKILL.md
    standard_1976.py     # 1976 temperature, pressure, density, sound speed, scale height
  ASTRO - HohmannTransfer/
    SKILL.md
    hohmann_transfer.py  # Hohmann delta-v and coast (key: value stdout, PNG)
  ASTRO - OrbitalParameters/
    SKILL.md
    orbital_parameters.py  # elements and inertial state (key: value stdout, PNG, HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - PlaneChangeImpulse/
    SKILL.md
    plane_change_impulse.py  # node inclination change (key: value stdout, PNG, HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - GroundTrackEarth/
    SKILL.md
    ground_track_earth.py  # subsatellite lat/lon (key: value stdout, PNG)
    data/                  # Natural Earth 1:110m land shapefile (public domain)
  AERO - AirplanePerformanceParameters/
    SKILL.md
    airplane_performance.py  # stall, L/D, range and endurance speeds, sea-level climb
  AERO - BreguetRangeEndurance/
    SKILL.md
    breguet_range_endurance.py  # jet and propeller Breguet range and endurance
  AERO - PrandtlMeyerAndShocks/
    SKILL.md
    prandtl_meyer_and_shocks.py  # wedge shock and Prandtl-Meyer expansion (key: value stdout, PNG)
  AERO - ConicalShock/
    SKILL.md
    conical_shock.py             # circular-cone Taylor-Maccoll shock (key: value stdout, PNG)
  AERO - DiamondAirfoilShockExpansion/
    SKILL.md
    diamond_airfoil_shock_expansion.py  # diamond panel pressures, cl, cd (key: value stdout, PNG)
  AERO - WingGeometry/
    SKILL.md
    wing_geometry.py     # trapezoidal planform (key: value stdout, PNG)
  AERO - V-nDiagram/
    SKILL.md
    vn_diagram.py        # stall boundary and corner speed (key: value stdout, PNG)
  AERO - IncompressibleLevelTurn/
    SKILL.md
    incompressible_level_turn.py  # coordinated level-turn radius and rate (key: value stdout, PNG)
  AERO - IdealPropeller/
    SKILL.md
    ideal_propeller.py     # actuator-disk thrust, induced velocity, efficiency (key: value stdout, PNG)
  AERO - FiniteWingLiftCurve/
    SKILL.md
    finite_wing_lift_curve.py  # wing slope, induced angle, lift curve to stall (PDF)
  AERO - EquivalentAirspeed/
    SKILL.md
    equivalent_airspeed.py  # Mach, dynamic pressure, equivalent airspeed, Reynolds number
  AERO - DensityAndPressureAltitude/
    SKILL.md
    density_and_pressure_altitude.py  # pressure and density altitude (key: value stdout)
  AERO - LongitudinalStaticMargin/
    SKILL.md
    longitudinal_static_margin.py  # stick-fixed neutral point and static margin (key: value stdout)
  AERO - RayleighPitotMach/
    SKILL.md
    rayleigh_pitot_mach.py  # pitot Mach and dynamic pressure (key: value stdout)
  AERO - PrandtGlauertCorrectionandCriticalMach/
    SKILL.md
    prandtl_glauert_correction_and_critical_mach.py  # PG correction and M_cr (key: value stdout, PNG)
  AERO - NACAFourDigitSection/
    SKILL.md
    naca_four_digit_section.py  # four-digit ordinates and Report 824 cl, cm, cd (key: value stdout, PNGs)
    data/report824_polars.json  # digitized Langley 2-D pressure-tunnel charts
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
- **ROCKET - SolidMotorParameters** — Python 3 standard library only.
- **ROCKET - CircularPortGrainHistory** — Python 3 with `matplotlib`. Reuses `ROCKET - SolidMotorParameters`. Ends inhibited; no erosive burning. An omitted `--sliver` is 0.
- **ASTRO - HohmannTransfer** — Python 3 with `matplotlib`.
- **ASTRO - OrbitalParameters** — Python 3 with `matplotlib`. Element angles are radians. `--elev` and `--azim` are degrees. Flattening is visual only. Each run also writes a self-contained HTML viewer beside the PNG. The viewer opens offline and animates the spacecraft on the same conic.
- **ASTRO - PlaneChangeImpulse** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Element angles and `--di` are radians. `--burn` is `an` or `dn`; the default is the slower node. `--elev` and `--azim` are degrees. Flattening is visual only. The impulse is a pure inclination change, \(\Delta v = 2 v \sin(\Delta i / 2)\). Each run writes a PNG and a self-contained HTML viewer. The viewer flies one revolution on the initial orbit, slows into the node, hinges the inclination, then flies four revolutions on the final orbit. The orbit the spacecraft is on is drawn solid; the other is faded.
- **ASTRO - GroundTrackEarth** — Python 3 with `matplotlib`. Element angles and `--greenwich` are radians. Two-body motion is Keplerian; WGS 84 flattening enters geodetic latitude only. The baseline map is 10 orbital periods. `--span` is seconds from epoch, or pass `--t0` and `--t1`. Ellipse only. The PNG land fill is Natural Earth 1:110m land, public domain.
- **ATMOS - Standard1976** — Python 3 standard library only. Hydrostatic model from sea level through 86 km. It does not use the NASA Glenn three-zone fit.
- **AERO - PrandtlMeyerAndShocks** — Python 3 with `matplotlib`. Deflection is in radians. A two-dimensional wedge, not a cone.
- **AERO - ConicalShock** — Python 3 with `numpy` and `matplotlib`. Half-angle is in radians. A right circular cone at zero incidence, not a wedge. An omitted `--gamma` is \(1.4\).
- **AERO - DiamondAirfoilShockExpansion** — Python 3 with `matplotlib`. Half-angle and angle of attack are radians. Reuses `AERO - PrandtlMeyerAndShocks`. Symmetric diamond only; trailing-edge wake matching is omitted.
- **AERO - AirplanePerformanceParameters** — Python 3 standard library only. Sea-level density and an altitude lookup both come from `ATMOS - Standard1976`. A climb rate needs `--thrust` or `--power`.
- **AERO - BreguetRangeEndurance** — Python 3 standard library only. Weight-based TSFC is `--ct` in \(1/\mathrm{s}\). Weight-based power SFC is `--c` in \(1/\mathrm{m}\). Cruise only; climb, descent, reserves, and wind are omitted.
- **AERO - WingGeometry** — Python 3 with `matplotlib`. Chords are streamwise. Sweep is in radians. An omitted sweep draws an unswept leading edge. An omitted sweep station is the quarter chord.
- **AERO - V-nDiagram** — Python 3 with `matplotlib`. Equivalent airspeed is `stall_speed` at 1976 sea-level density from `ATMOS - Standard1976`. True airspeeds use `--rho`. The negative line is the limit load factor. The plot end is not a dive speed.
- **AERO - IncompressibleLevelTurn** — Python 3 with `matplotlib`. Bank is radians. Pass one of `--bank`, `--n`, `--thrust`, or `--power`. Thrust or power also needs `--cd0`, `--ar`, and `--e`. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Speeds are true airspeed at `--rho`. Dynamic pressure is incompressible \(\frac12\rho V^{2}\). The stall limit is `stall_speed` with \(W\) replaced by \(nW\), the same relation as the V-n stall boundary. Sustained \(n\) is thrust equal to drag at \(L = nW\) on the parabolic polar.
- **AERO - IdealPropeller** — Python 3 with `matplotlib`. Pass `--alt` or `--rho`. `--power` is ideal shaft power, not useful power. An altitude lookup uses `ATMOS - Standard1976`. Incompressible actuator disk; no swirl, tip loss, or blade drag.
- **AERO - FiniteWingLiftCurve** — Python 3 with `matplotlib`. Angles are radians. The section slope is per radian. Span efficiency satisfies \(0 < e \le 1\). The PDF ends at stall.
- **AERO - EquivalentAirspeed** — Python 3 standard library only. Temperature, pressure, density, and sound speed come from `ATMOS - Standard1976`. Equivalent airspeed is `freestream_dynamic_pressure` at 1976 sea-level density. It is not calibrated airspeed. An omitted length is 1 m.
- **AERO - DensityAndPressureAltitude** — Python 3 standard library only. The 1976 layers and sea-level density come from `ATMOS - Standard1976`. An omitted `--rh` is dry air. Station pressure above sea-level pressure extrapolates the troposphere below \(H = 0\). Equivalent airspeed is not calibrated airspeed. It does not use the NASA Glenn three-zone fit.
- **AERO - LongitudinalStaticMargin** — Python 3 standard library only. Stick-fixed TN 1670 equation (6). \(l\) is measured from the neutral point. \(q_T/q\) is the tail dynamic-pressure ratio. Both lift-curve slopes use the same angle unit.
- **AERO - RayleighPitotMach** — Python 3 standard library only. Measured pitot at or above freestream static. An omitted `--gamma` is \(1.4\). The sonic pressure ratio selects isentropic stagnation versus Rayleigh-Pitot.
- **AERO - PrandtGlauertCorrectionandCriticalMach** — Python 3 with `matplotlib`. Freestream Mach is below 1. An omitted `--gamma` is \(1.4\). Pass `--cl-inc` and/or `--cpmin-inc`. Critical Mach needs a negative `--cpmin-inc`. Two-dimensional \(1/\beta\) only.
- **AERO - NACAFourDigitSection** — Python 3 with `matplotlib`. Angle of attack is radians. Geometry is the four-digit family. Coefficients are interpolated from digitized NACA Report 824 charts (smooth) for 0012, 2412, 2415, and 4412. Optional `--re` selects or interpolates among the tabulated Reynolds numbers (about \(3\times10^6\), \(6\times10^6\), and \(9\times10^6\)). An omitted `--re` uses the curve nearest \(6\times10^6\). An omitted `--alpha` still writes the coefficient and polar figures. Coefficient plots use degrees over the measured range. There is no inviscid \(c_d = 0\).

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
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --a 1e-5 --n 0.5 --ab 0.4 --throat 0.002 --rho 1800 --cstar 1550
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --check
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --a 1e-5 --n 0.5 --port 0.02 --length 0.4 --outer 0.05 --throat 0.0005 --rho 1800 --cstar 1550
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --check
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --r1 6774200 --r2 7374200
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --alt 400000 --ecc 0.2
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --check
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --a 10000000 --e 0.3 --i 0.9 --raan 0.6 --aop 1.2 --nu 0.8
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --a=-25000000 --e 1.4 --i 1.1 --raan 0.8 --aop 0.5 --nu 0.6
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --rx 8000000 --ry 0 --rz 0 --vx 0 --vy 7000 --vz 1500
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --check
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --a 10000000 --e 0.3 --i 0.9 --raan 0.6 --aop 1.2 --nu 0.8 --di 0.2
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --rx 8000000 --ry 0 --rz 0 --vx 0 --vy 7000 --vz 1500 --di 0.3
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --check
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --a 7000000 --e 0.05 --i 0.9 --raan 0.4 --aop 0.2 --nu 0.1 --greenwich 0.3
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --check
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --pc 2e6 --gamma 1.25 --alt 0
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --check
python "skills/ATMOS - Standard1976/standard_1976.py" --alt 11000
python "skills/ATMOS - Standard1976/standard_1976.py" --check
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --weight 10000 --area 16 --cd0 0.02 --ar 8 --e 0.8 --clmax 1.6 --alt 0
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --check
python "skills/AERO - BreguetRangeEndurance/breguet_range_endurance.py" --ld 16 --wi 1e5 --wf 8e4 --speed 250 --ct 2e-5 --c 1e-7 --eta 0.85
python "skills/AERO - BreguetRangeEndurance/breguet_range_endurance.py" --check
python "skills/AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py" --mach 2 --delta 0.174533
python "skills/AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py" --check
python "skills/AERO - ConicalShock/conical_shock.py" --mach 2 --delta 0.174533
python "skills/AERO - ConicalShock/conical_shock.py" --check
python "skills/AERO - DiamondAirfoilShockExpansion/diamond_airfoil_shock_expansion.py" --mach 2 --epsilon 0.174533 --alpha 0.087266
python "skills/AERO - DiamondAirfoilShockExpansion/diamond_airfoil_shock_expansion.py" --check
python "skills/AERO - WingGeometry/wing_geometry.py" --span 10 --root 2 --tip 1 --sweep 0.523598775598
python "skills/AERO - WingGeometry/wing_geometry.py" --check
python "skills/AERO - V-nDiagram/vn_diagram.py" --weight 10000 --area 16 --clmax 1.6 --n-pos 3.8 --n-neg -1.52 --rho 1.225
python "skills/AERO - V-nDiagram/vn_diagram.py" --check
python "skills/AERO - IncompressibleLevelTurn/incompressible_level_turn.py" --speed 50 --weight 10000 --area 16 --clmax 1.6 --rho 1.225 --n 2
python "skills/AERO - IncompressibleLevelTurn/incompressible_level_turn.py" --speed 50 --weight 10000 --area 16 --clmax 1.6 --rho 1.225 --cd0 0.02 --ar 8 --e 0.8 --thrust 1500
python "skills/AERO - IncompressibleLevelTurn/incompressible_level_turn.py" --check
python "skills/AERO - IdealPropeller/ideal_propeller.py" --power 150000 --diameter 2 --speed 50 --rho 1.225
python "skills/AERO - IdealPropeller/ideal_propeller.py" --check
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --a0 6.28318530718 --alpha-l0 -0.03490658504 --clmax 1.4 --ar 8 --e 0.8
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --check
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --alt 11000 --mach 0.8
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --check
python "skills/AERO - DensityAndPressureAltitude/density_and_pressure_altitude.py" --pressure 101325 --oat 288.15 --rh 0.5 --eas 50
python "skills/AERO - DensityAndPressureAltitude/density_and_pressure_altitude.py" --check
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --a 5 --at 4 --downwash 0.4 --q-ratio 0.9 --tail-area 2 --tail-length 5 --wing-area 10 --mac 1 --cg 0.1
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --check
python "skills/AERO - RayleighPitotMach/rayleigh_pitot_mach.py" --pitot 120195 --static 101325 --gamma 1.4
python "skills/AERO - RayleighPitotMach/rayleigh_pitot_mach.py" --check
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --mach 0.6 --cl-inc 0.5 --cpmin-inc -0.4
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --check
python "skills/AERO - NACAFourDigitSection/naca_four_digit_section.py" --naca 2412 --chord 1 --alpha 0.0872664625997 --re 5.7e6
python "skills/AERO - NACAFourDigitSection/naca_four_digit_section.py" --check
```

## Units

SI is the working system (Pa, m², N). Skills convert other units before calling programs and state the units used in the reply.

## License

No license file is included yet. Treat the repository as private unless a license is added.
