# AerospaceBot

Cursor agent skills for aerospace engineering: checked formulas and small physics programs the bot can run and report, instead of reinventing equations or redrawing plots by hand.

## Skills

| Skill | Purpose |
| --- | --- |
| [`FormulaCatalouge`](skills/FormulaCatalouge) | Select and use verified aerospace formulas (compressible flow, atmosphere, rocket propulsion, aerodynamics, structures including Euler column buckling, mass properties, aerothermodynamics including Allen–Eggers peak load, spacecraft power including battery energy budget, space communications, dynamics and control). Only formulas listed in `checks/check.md` are allowed. |
| [`CTRL - SecondOrderResponse`](skills/CTRL%20-%20SecondOrderResponse) | Run `second_order_response.py` for linear second-order unit-step metrics: damped frequency, overshoot, peak time, 10%–90% rise time, settling time, and under/critical/over-damped class from \(\omega_n\) and \(\zeta\), or from mass, stiffness, and viscous damping. Optional settling band (default 2%). Optional PNG of the unit-step response. |
| [`POWER - SolarArrayOutput`](skills/POWER%20-%20SolarArrayOutput) | Run `solar_array_output.py` for flat-plate solar-array beginning-of-life power, end-of-life power, and orbit-average power from area and efficiency or BOL specific power, solar constant, incidence angle, packing, inherent and life degradation, and optional eclipse fraction or circular-orbit beta. Optional PNG of power versus sun angle. |
| [`POWER - BatteryEnergyBudget`](skills/POWER%20-%20BatteryEnergyBudget) | Run `battery_energy_budget.py` for usable battery energy from nameplate watt-hours or amp-hours with bus voltage, depth of discharge, and charge/discharge efficiencies; time at continuous load; whether an eclipse or peak pulse fits; required capacity from load and eclipse; and optional one-orbit SoC PNG with solar orbit-average power from SolarArrayOutput. No cell electrochemistry or Peukert beyond the supplied efficiencies. |
| [`COMMS - FreeSpaceLinkBudget`](skills/COMMS%20-%20FreeSpaceLinkBudget) | Run `free_space_link_budget.py` for vacuum free-space path loss, Friis received power, EIRP, optional \(C/N_0\) or \(C/N\) from system noise temperature and bandwidth, and optional \(E_b/N_0\) and link margin from bit rate and a required \(E_b/N_0\). Antenna gains may be linear or circular diameters with aperture efficiency. Optional PNG of received power versus range. No atmosphere or rain. |
| [`MASS - CenterOfMassAndInertia`](skills/MASS%20-%20CenterOfMassAndInertia) | Run `center_of_mass_and_inertia.py` for total mass, center of mass, and the inertia tensor about the CG (optionally about the body origin) of a rigid assembly of point masses or parts with optional own-CG inertias and parallel-axis transfer. Writes a PNG of the parts and CG in the body frame. |
| [`ROCKET - Area-Mach Graph`](skills/ROCKET%20-%20Area-Mach%20Graph) | Run `area_mach.py` for an isentropic nozzle area-Mach curve, exit Mach from area ratio, exit pressure, ideal thrust, and expansion state. |
| [`ROCKET - PerformanceParameters`](skills/ROCKET%20-%20PerformanceParameters) | Run `performance.py` for frozen-CEA c*, temperature, gamma, ideal Cf, specific impulse, and density impulse. Do not call CEA at reply time. |
| [`ROCKET - ThroatSizingandMassFlow`](skills/ROCKET%20-%20ThroatSizingandMassFlow) | Run `throat_sizing.py` for circular-throat area and diameter from thrust, thrust coefficient, and chamber pressure, and mass flow from characteristic velocity. |
| [`ROCKET - PropellantLoad`](skills/ROCKET%20-%20PropellantLoad) | Run `propellant_load.py` for usable propellant mass and tank volume (total, oxidizer, fuel) from mass flow, burn time, mixture ratio, and liquid densities. |
| [`ROCKET - ExpansionMatchEarth`](skills/ROCKET%20-%20ExpansionMatchEarth) | Run `expansion_match.py` for the altitude-matched nozzle expansion ratio on the 1976 U.S. Standard Atmosphere. Area ratio and ideal \(C_F\) come from Area-Mach. |
| [`ROCKET - PayloadtoDeltaV`](skills/ROCKET%20-%20PayloadtoDeltaV) | Run `payload_to_deltav.py` for useful payload from ideal delta-v, or ideal delta-v from useful payload, for one or more stages. A missing delta-v and payload writes a payload-versus-delta-v PNG. |
| [`ROCKET - LossStack`](skills/ROCKET%20-%20LossStack) | Run `loss_stack.py` for actual thrust, specific impulse, thrust coefficient, c*, and mass flow from ideal \(C_F\), ideal \(c^{*}\), and named efficiencies. With throat area and chamber pressure it also prints the lossless thrust and mass flow. Omitted efficiencies stay 1. |
| [`ROCKET - BasicTrajectoryLossesFromBodySurface`](skills/ROCKET%20-%20BasicTrajectoryLossesFromBodySurface) | Run `basic_trajectory_losses_from_body_surface.py` for vacuum delta-v, gravity, drag, and steering losses, and burnout speed, flight-path angle, and altitude of a simplified powered ascent from a spherical surface. Constant flight-path angle is closed form; a gravity-turn kick integrates the ODE. Writes a PNG of the path on the atmosphere. |
| [`ROCKET - ChamberVolumeAndCaseHoopStress`](skills/ROCKET%20-%20ChamberVolumeAndCaseHoopStress) | Run `chamber_case.py` for chamber volume from throat area and \(L^{*}\), and thin-wall hoop stress and margin of safety from pressure, case radius, wall thickness, and allowable stress. |
| [`STRUCT - BeamBendingStress`](skills/STRUCT%20-%20BeamBendingStress) | Run `beam_bending_stress.py` for pure elastic bending stress of a beam, spar, longeron, or boom from bending moment and either section modulus or second moment of area with extreme-fiber distance. Optional allowable stress prints margin of safety. Optional PNG of stress versus moment for the fixed section. |
| [`STRUCT - EulerColumnBuckling`](skills/STRUCT%20-%20EulerColumnBuckling) | Run `euler_column_buckling.py` for the elastic Euler critical buckling load of a concentrically loaded prismatic column from Young’s modulus, second moment of area, unsupported length, and end-fix factor \(K\) (pinned–pinned default). Optional area prints critical stress and slenderness; optional compressive yield reports whether Euler is valid or the section would yield first. Optional PNG of critical load versus length for the fixed section. |
| [`THERM - SonicStagnationHeatFlux`](skills/THERM%20-%20SonicStagnationHeatFlux) | Run `sonic_stagnation_heat_flux.py` for Sutton–Graves stagnation-point convective heat flux and freestream dynamic pressure from speed, nose radius, and freestream density or 1976 altitude. Optional wall temperature uses the heat-transfer coefficient form; optional emissivity prints radiative-equilibrium wall temperature. Writes a PNG of flux versus speed at fixed density and nose radius. Does not model dissociation beyond the Sutton–Graves air coefficient. |
| [`THERM - BallisticEntryPeakLoad`](skills/THERM%20-%20BallisticEntryPeakLoad) | Run `ballistic_entry_peak_load.py` for Allen–Eggers nonlifting ballistic-entry peak deceleration and the altitude of that peak in an exponential atmosphere from ballistic coefficient (or mass, \(C_D\), and area), entry speed, and entry flight-path angle. Default Earth fit from NACA TN 4047. Optional PNG of peak load versus entry angle. Companion to stagnation heat flux; not a full trajectory. |
| [`ROCKET - SolidMotorParameters`](skills/ROCKET%20-%20SolidMotorParameters) | Run `solid_motor_parameters.py` for burning-area ratio, equilibrium chamber pressure, burn rate, and solid-propellant mass flow from Saint Robert burn-rate inputs, grain and throat areas, density, and \(c^{*}\). |
| [`ROCKET - CircularPortGrainHistory`](skills/ROCKET%20-%20CircularPortGrainHistory) | Run `circular_port_grain_history.py` for chamber pressure, burning-area ratio, and remaining web versus time of an internal-burning circular grain with inhibited ends. Writes a PNG of the three histories. |
| [`ASTRO - HohmannTransfer`](skills/ASTRO%20-%20HohmannTransfer) | Run `hohmann_transfer.py` for circular speed, escape speed, specific energy, impulsive delta-v, coast time, and \(|r_2|/|r_1|\) between two circular orbits. Writes a PNG of the transfer looking down the orbit normal. Optional `--html` writes a self-contained 3D viewer with the two burns. Recommends a bi-elliptic transfer when that ratio is large enough that a path through infinity would be cheaper. |
| [`ASTRO - HyperbolicExcess`](skills/ASTRO%20-%20HyperbolicExcess) | Run `hyperbolic_excess.py` for hyperbolic excess speed, characteristic energy \(C_3\), the periapsis burn from a circular park onto a hyperbola, the turning angle, and the true anomaly of the asymptote. Writes a PNG of the park and the hyperbola. Optional `--html` writes a self-contained 3D viewer of the burn and the morph from the circle onto the hyperbola. |
| [`ASTRO - BiellipticTransfer`](skills/ASTRO%20-%20BiellipticTransfer) | Run `bielliptic_transfer.py` for the three-burn delta-v, time of flight, and \(|r_2|/|r_1|\) of a coplanar bi-elliptic transfer between two circular orbits, from radii, classical elements, NORAD two-line element sets, or inertial states plus an intermediate apoapsis. Writes a PNG looking down the orbit normal. Optional `--html` writes a self-contained 3D viewer with the three burns. Recommends a Hohmann transfer when this apoapsis is not cheaper. |
| [`ASTRO - OrbitalParameters`](skills/ASTRO%20-%20OrbitalParameters) | Run `orbital_parameters.py` for classical elements, a NORAD two-line element set, or the inertial state of a Keplerian conic, plus time of flight for one orbit or between two anomalies on an ellipse. Writes a PNG of the orbit and a self-contained HTML viewer. Optional `--j2` applies first-order \(J_2\) secular rates in the viewer. |
| [`ASTRO - PlaneChangeImpulse`](skills/ASTRO%20-%20PlaneChangeImpulse) | Run `plane_change_impulse.py` for the impulsive delta-v of a pure inclination change at the ascending or descending node, from classical elements, a NORAD two-line element set, or an inertial state. Writes a PNG of both planes and a self-contained HTML viewer. |
| [`ASTRO - GroundTrackEarth`](skills/ASTRO%20-%20GroundTrackEarth) | Run `ground_track_earth.py` for the geodetic latitude and longitude of the subsatellite point over ten orbital periods by default, from elements, a NORAD two-line element set, or an inertial state plus the Greenwich angle at epoch. First-order \(J_2\) advances the node and periapsis. Writes a PNG of the track on a public-domain Natural Earth land map. |
| [`ASTRO - J2SecularRates`](skills/ASTRO%20-%20J2SecularRates) | Run `j2_secular_rates.py` for first-order \(J_2\) nodal and apsidal rates and the sun-synchronous inclination of an Earth ellipse, from the same elements, NORAD two-line element set, or inertial state as GroundTrackEarth or PlaneChangeImpulse. Writes a PNG of those rates against inclination. |
| [`ATMOS - Standard1976`](skills/ATMOS%20-%20Standard1976) | Run `standard_1976.py` for 1976 U.S. Standard Atmosphere temperature, pressure, density, speed of sound, and geometric pressure scale height at one geometric altitude from sea level through 86 km. |
| [`ATMOS - KineticTemperatureAbove86km`](skills/ATMOS%20-%20KineticTemperatureAbove86km) | Run `kinetic_temperature_above_86km.py` for 1976 kinetic temperature and temperature-segment name at one geometric altitude from 86 km through 1000 km. Optional PNG of temperature versus altitude. Does not print pressure or density. |
| [`ATMOS - TransportProperties`](skills/ATMOS%20-%20TransportProperties) | Run `transport_properties.py` for 1976 dry-air dynamic viscosity, thermal conductivity, and mean particle speed from geometric altitude or temperature. With altitude, or temperature plus pressure, also print density, kinematic viscosity, mean free path, collision frequency, and number density. |
| [`AERO - IsentropicStagnation`](skills/AERO%20-%20IsentropicStagnation) | Run `isentropic_stagnation.py` for isentropic total temperature, pressure, and density from Mach number and optional static state, the sonic reference state, and static and stagnation speeds of sound. Optional PNG of \(p_t/p\) and \(T_t/T\) versus Mach (no shock). |
| [`AERO - NormalShock`](skills/AERO%20-%20NormalShock) | Run `normal_shock.py` for downstream Mach, static pressure, temperature, and density ratios, stagnation-pressure ratio, and entropy jump of a simple normal shock. Writes a PNG of those ratios versus upstream Mach. |
| [`AERO - PrandtlMeyerAndShocks`](skills/AERO%20-%20PrandtlMeyerAndShocks) | Run `prandtl_meyer_and_shocks.py` for the weak oblique-shock angle, downstream Mach, and static-pressure ratio on a two-dimensional wedge, the Prandtl-Meyer expansion through the same deflection, and whether the shock is attached. |
| [`AERO - ConicalShock`](skills/AERO%20-%20ConicalShock) | Run `conical_shock.py` for the attached shock angle, surface Mach, and surface pressure coefficient of a right circular cone at zero incidence. |
| [`AERO - DiamondAirfoilShockExpansion`](skills/AERO%20-%20DiamondAirfoilShockExpansion) | Run `diamond_airfoil_shock_expansion.py` for the four panel pressures and section lift and drag of a symmetric diamond airfoil by shock-expansion theory. Writes a PNG of the waves. |
| [`AERO - AirplanePerformanceParameters`](skills/AERO%20-%20AirplanePerformanceParameters) | Run `airplane_performance.py` for stall speed, maximum lift-to-drag ratio, jet and propeller best-range and best-endurance speeds, and a sea-level climb estimate from a parabolic drag polar. |
| [`AERO - ClimbPerformance`](skills/AERO%20-%20ClimbPerformance) | Run `climb_performance.py` for best-rate speed, rate of climb, climb angle, and service and absolute ceilings versus 1976 geometric altitude from a parabolic polar and constant thrust or useful power. Off-nominal temperature or humidity uses `AERO - DensityAndPressureAltitude`. Writes a PNG of rate of climb versus geometric altitude. |
| [`AERO - BreguetRangeEndurance`](skills/AERO%20-%20BreguetRangeEndurance) | Run `breguet_range_endurance.py` for jet and propeller Breguet cruise range and endurance from lift-to-drag ratio, specific fuel consumption, cruise speed, propeller efficiency, and start and end weight. |
| [`AERO - WingGeometry`](skills/AERO%20-%20WingGeometry) | Run `wing_geometry.py` for trapezoidal wing area, aspect ratio, taper ratio, mean aerodynamic chord, and the spanwise station of that chord. An optional sweep is drawn on the plan view. |
| [`AERO - V-nDiagram`](skills/AERO%20-%20V-nDiagram) | Run `vn_diagram.py` for the positive stall boundary and corner speed from weight, wing area, \(C_{L,\max}\), limit load factors, and air density. The PNG plots load factor against equivalent airspeed. |
| [`AERO - IncompressibleLevelTurn`](skills/AERO%20-%20IncompressibleLevelTurn) | Run `incompressible_level_turn.py` for coordinated level-turn radius, rate, bank, and load factor from speed, weight, wing area, \(C_{L,\max}\), air density, and either bank, load factor, or a sustained load factor from thrust or power on a parabolic polar. Incompressible \(q=\frac12\rho V^{2}\). The PNG plots radius and rate against true airspeed with the stall limit marked; thrust or power also plots sustained load factor against speed. |
| [`AERO - SymmetricPullUp`](skills/AERO%20-%20SymmetricPullUp) | Run `symmetric_pull_up.py` for symmetric pull-up radius, pitch rate, and load factor from speed, weight, wing area, \(C_{L,\max}\), air density, and either load factor, pull-up radius, pitch rate, or a sustained load factor from thrust or power on a parabolic polar. Incompressible \(q=\frac12\rho V^{2}\). The PNG plots radius and pitch rate against true airspeed with the stall limit marked; thrust or power also plots sustained load factor against speed. |
| [`AERO - SteadyGlide`](skills/AERO%20-%20SteadyGlide) | Run `steady_glide.py` for best \(L/D\), sink rate, glide angle, and optional unpowered range from a height, from weight, wing area, zero-lift drag, aspect ratio, Oswald efficiency, and 1976 geometric altitude. Optional \(C_{L,\max}\) is a stall check. The PNG plots sink rate against true airspeed. |
| [`AERO - TakeoffGroundRoll`](skills/AERO%20-%20TakeoffGroundRoll) | Run `takeoff_ground_roll.py` for stall speed, lift-off true airspeed, and ground-roll distance and time on a level dry runway from weight, wing area, takeoff lift coefficient, rolling friction, a parabolic polar, and either constant thrust or useful power with a static thrust cap. Density is `--rho`, 1976 `--alt`, or `--alt` with temperature and humidity through `AERO - DensityAndPressureAltitude`. The PNG plots true airspeed against ground distance with lift-off marked. |
| [`AERO - LandingGroundRoll`](skills/AERO%20-%20LandingGroundRoll) | Run `landing_ground_roll.py` for stall speed, touchdown true airspeed, and ground-roll distance and time on a level dry runway from weight, wing area, touchdown lift coefficient, braking friction, a parabolic polar, and optional constant idle or reverse thrust (omitted is 0). Density is `--rho`, 1976 `--alt`, or `--alt` with temperature and humidity through `AERO - DensityAndPressureAltitude`. The PNG plots true airspeed against ground distance with rest marked. |
| [`PROP - IdealPropeller`](skills/PROP%20-%20IdealPropeller) | Run `ideal_propeller.py` for ideal actuator-disk thrust, induced velocity, and propulsive efficiency from shaft power, propeller diameter, flight speed, and air density or altitude. The PNG plots those three quantities against true airspeed. Ideal thrust or useful power \(T V\) can feed `AERO - IncompressibleLevelTurn` or `AERO - SymmetricPullUp`. |
| [`PROP - IdealTurboJet`](skills/PROP%20-%20IdealTurboJet) | Run `ideal_turbojet.py` for ideal Brayton turbojet specific thrust, mass-based TSFC, thermal/propulsive/overall efficiency, and nozzle exit speed and temperature from flight Mach, freestream \(T,p\) or 1976 altitude, turbine inlet temperature, and compressor pressure ratio. The PNG plots specific thrust versus Mach at fixed TIT and OPR. No fan, afterburner, or component maps. |
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
  FormulaCatalouge/
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
  ROCKET - BasicTrajectoryLossesFromBodySurface/
    SKILL.md
    basic_trajectory_losses_from_body_surface.py  # gravity, drag, and steering losses from a spherical surface (key: value stdout, PNG)
  ROCKET - ChamberVolumeAndCaseHoopStress/
    SKILL.md
    chamber_case.py      # chamber volume, hoop stress, margin of safety (key: value stdout)
  STRUCT - BeamBendingStress/
    SKILL.md
    beam_bending_stress.py  # pure bending stress, optional MS and PNG
  STRUCT - EulerColumnBuckling/
    SKILL.md
    euler_column_buckling.py  # elastic Euler buckling load, optional yield check and PNG
  CTRL - SecondOrderResponse/
    SKILL.md
    second_order_response.py  # second-order step metrics and optional PNG
  MASS - CenterOfMassAndInertia/
    SKILL.md
    center_of_mass_and_inertia.py  # CG and inertia tensor of a rigid assembly (PNG)
  THERM - SonicStagnationHeatFlux/
    SKILL.md
    sonic_stagnation_heat_flux.py  # Sutton-Graves stagnation heat flux (PNG)
  THERM - BallisticEntryPeakLoad/
    SKILL.md
    ballistic_entry_peak_load.py  # Allen-Eggers peak deceleration / altitude (optional PNG)
  POWER - SolarArrayOutput/
    SKILL.md
    solar_array_output.py  # flat-plate solar-array BOL/EOL/orbit-average power (optional PNG)
  POWER - BatteryEnergyBudget/
    SKILL.md
    battery_energy_budget.py  # battery usable energy, eclipse/peak fit, required capacity, SoC PNG
  COMMS - FreeSpaceLinkBudget/
    SKILL.md
    free_space_link_budget.py  # vacuum Friis path loss, Pr, optional C/N0 and Eb/N0 margin (optional PNG)
  ROCKET - SolidMotorParameters/
    SKILL.md
    solid_motor_parameters.py  # solid-motor K, pc, burn rate, mass flow (key: value stdout)
  ROCKET - CircularPortGrainHistory/
    SKILL.md
    circular_port_grain_history.py  # circular-port pc, K, remaining web versus time (PNG)
  ATMOS - Standard1976/
    SKILL.md
    standard_1976.py     # 1976 temperature, pressure, density, sound speed, scale height
  ATMOS - KineticTemperatureAbove86km/
    SKILL.md
    kinetic_temperature_above_86km.py  # 1976 kinetic T above 86 km (key: value stdout, optional PNG)
  ATMOS - TransportProperties/
    SKILL.md
    transport_properties.py  # 1976 viscosity, conductivity, mean free path (key: value stdout)
  ASTRO - HohmannTransfer/
    SKILL.md
    hohmann_transfer.py  # Hohmann delta-v and coast (key: value stdout, PNG, optional HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - HyperbolicExcess/
    SKILL.md
    hyperbolic_excess.py  # circular-park escape onto a hyperbola (key: value stdout, PNG, optional HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - BiellipticTransfer/
    SKILL.md
    bielliptic_transfer.py  # three-burn bi-elliptic delta-v and coast (key: value stdout, PNG, optional HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
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
  ASTRO - J2SecularRates/
    SKILL.md
    j2_secular_rates.py    # J2 nodal/apsidal rates and sun-sync inclination (key: value stdout, PNG)
  AERO - AirplanePerformanceParameters/
    SKILL.md
    airplane_performance.py  # stall, L/D, range and endurance speeds, sea-level climb
  AERO - ClimbPerformance/
    SKILL.md
    climb_performance.py     # best-rate climb vs 1976 altitude, ceilings (key: value stdout, PNG)
  AERO - BreguetRangeEndurance/
    SKILL.md
    breguet_range_endurance.py  # jet and propeller Breguet range and endurance
  AERO - IsentropicStagnation/
    SKILL.md
    isentropic_stagnation.py     # isentropic totals, sonic state, sound speeds (optional PNG)
  AERO - NormalShock/
    SKILL.md
    normal_shock.py              # normal-shock jumps (key: value stdout, PNG)
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
  AERO - SymmetricPullUp/
    SKILL.md
    symmetric_pull_up.py          # symmetric pull-up radius and pitch rate (key: value stdout, PNG)
  AERO - SteadyGlide/
    SKILL.md
    steady_glide.py               # best L/D, sink, glide angle, range from height (key: value stdout, PNG)
  AERO - TakeoffGroundRoll/
    SKILL.md
    takeoff_ground_roll.py        # level dry-runway ground roll to lift-off (key: value stdout, PNG)
  AERO - LandingGroundRoll/
    SKILL.md
    landing_ground_roll.py        # level dry-runway ground roll from touchdown to rest (key: value stdout, PNG)
  PROP - IdealPropeller/
    SKILL.md
    ideal_propeller.py     # actuator-disk thrust, induced velocity, efficiency (key: value stdout, PNG)
  PROP - IdealTurboJet/
    SKILL.md
    ideal_turbojet.py      # ideal Brayton turbojet Fs, TSFC, efficiencies (key: value stdout, PNG)
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

- **FormulaCatalouge** — no extra runtime; the agent reads the markdown references.
- **ROCKET - Area-Mach Graph** — Python 3 with `numpy` and `matplotlib`.
- **ROCKET - PerformanceParameters** — Python 3 with `numpy` and `matplotlib`. Frozen tables are produced offline by `scripts/build_table.py` (`rocketcea`). A reply does not call CEA.
- **ROCKET - ThroatSizingandMassFlow** — Python 3 standard library only.
- **ROCKET - PropellantLoad** — Python 3 standard library only. Pair densities are read from `ROCKET - PerformanceParameters` `scripts/pairs.json`.
- **ROCKET - ExpansionMatchEarth** — Python 3 with `numpy` and `matplotlib`, because it calls `ROCKET - Area-Mach Graph`. It does not call CEA.
- **ROCKET - PayloadtoDeltaV** — Python 3 standard library for a point result. A delta-v sweep also needs `matplotlib`.
- **ROCKET - LossStack** — Python 3 standard library only.
- **ROCKET - BasicTrajectoryLossesFromBodySurface** — Python 3 with `matplotlib`. Pass `--gamma` or `--kick`, not both. Pass `--mf` or `--mp`. Pass `--tb` or `--mdot`. Optional `--cd` needs `--area`. Off-nominal `--oat` uses `AERO - DensityAndPressureAltitude`. An omitted planet is the 1976 Earth radius and \(g_0\). Angles are radians. Vacuum thrust does not vary with ambient pressure.
- **ROCKET - ChamberVolumeAndCaseHoopStress** — Python 3 standard library only.
- **STRUCT - BeamBendingStress** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--section-modulus`, or both `--inertia` and `--fiber`. Pure bending only; no axial, shear, or torsion. Optional `--allowable` prints `margin_of_safety`.
- **STRUCT - EulerColumnBuckling** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--E`, `--inertia`, and `--length`. Optional `--k` or `--ends` (default pinned–pinned \(K=1\)). Optional `--area` for stress and slenderness; `--yield` needs `--area`. Elastic Euler only; no short-column curve.
- **CTRL - SecondOrderResponse** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--wn` with `--zeta`, or `--mass` with `--stiffness` and `--damping`. Optional `--settling-percent` (default 2). Linear unity-gain second-order plant only.
- **MASS - CenterOfMassAndInertia** — Needs `matplotlib` for the body-frame PNG. Repeat `--part m,x,y,z` for each mass. Optional own-CG inertias and a trailing parallel-axis flag per part. `--about-origin` also prints the inertia about the body origin.
- **THERM - SonicStagnationHeatFlux** — Python 3 with `matplotlib`. Pass `--speed`, `--nose`, and `--alt` or `--rho`. Optional `--wall-temp` uses the Sutton–Graves coefficient form. Optional `--emissivity` prints radiative-equilibrium wall temperature. Optional `--mach-axis` plots freestream Mach when `--alt` or `--temperature` supplies sound speed. Altitude mode reuses `ATMOS - Standard1976` through 86 km. Earth air only; no dissociation model beyond the TR R-376 air coefficient.
- **THERM - BallisticEntryPeakLoad** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--speed`, `--gamma`, and `--beta` or `--mass`/`--cd`/`--area`. Optional `--scale-height`, `--rho-ref`, and `--z-ref` together override the TN 4047 Earth exponential fit. Nonlifting Allen–Eggers closed form only; not a trajectory integrator.
- **POWER - SolarArrayOutput** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--area`, `--incidence`, and either `--efficiency` or `--specific-power`. Optional packing, inherent degradation, life degradation, years, solar constant, eclipse fraction, or circular-orbit `--a`/`--alt` with `--beta`. Flat-plate cosine law only.
- **POWER - BatteryEnergyBudget** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--dod`, `--eta-c`, and `--eta-d`. Capacity is `--energy` (W·h) or `--ah` with `--voltage`. Omit capacity and pass `--load` with eclipse timing to size required capacity. Optional `--peak`/`--peak-duration`, `--p-avg` from SolarArrayOutput, and orbit timing (`--eclipse` with `--day` or `--orbit`). No cell electrochemistry or Peukert beyond the supplied efficiencies.
- **COMMS - FreeSpaceLinkBudget** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--pt`, `--range`, `--freq` or `--wavelength`, and each antenna as linear gain or diameter with aperture efficiency. Optional `--ts`, `--bandwidth`, `--bitrate`, and `--ebn0-req`. Vacuum free space only; gains are linear ratios, not dBi.
- **ROCKET - SolidMotorParameters** — Python 3 standard library only.
- **ROCKET - CircularPortGrainHistory** — Python 3 with `matplotlib`. Reuses `ROCKET - SolidMotorParameters`. Ends inhibited; no erosive burning. An omitted `--sliver` is 0.
- **ASTRO - HohmannTransfer** — Python 3 with `matplotlib`. The PNG looks down the orbit normal. `--html` writes a self-contained HTML viewer beside the PNG; `--open` opens it. The viewer flies the two burns and the transfer coast. The solid trail is the path already flown; the remaining future path stays faded.
- **ASTRO - HyperbolicExcess** — Python 3 with `matplotlib`. It reuses OrbitalParameters for the planet backdrop. `--rp` is the circular park and the hyperbola periapsis. Pass exactly one of `--vinf`, `--C3`, or `--rinf`. `--rinf` is \(\lvert a\rvert=\mu/v_{\infty}^{2}\), not a station on the path. The PNG is the park, the hyperbola, and the periapsis burn. `--html` writes a self-contained HTML viewer; `--open` opens it. The viewer parks on the circle, morphs through the burn onto the hyperbola, then coasts toward the outgoing asymptote.
- **ASTRO - BiellipticTransfer** — Python 3 with `matplotlib`. It reuses HohmannTransfer and OrbitalParameters. `--rb` is the common apoapsis and must be at least the larger circular radius. Element angles are radians. The burns are coplanar; a plane change is omitted. Epoch radius from elements, a NORAD TLE, or a state is treated as a circular orbit of that radius. A TLE is passed as two 69-character lines and is not propagated with SGP4. The PNG looks down the orbit normal. `--html` writes a self-contained HTML viewer; `--open` opens it. The viewer flies the three burns and both coasts. The solid trail is the path already flown; the remaining future path stays faded.
- **ASTRO - OrbitalParameters** — Python 3 with `matplotlib`. Element angles are radians. `--tle` accepts a NORAD two-line element set as a Keplerian ellipse; line-2 angles stay in degrees, and SGP4 is not applied. On an ellipse, `tof_s` is always printed: one orbit by default, or the forward coast to optional `--nu2` / `--M2`. `--elev` and `--azim` are degrees. Flattening is visual only. Optional `--j2` applies first-order \(J_2\) secular \(\dot{\Omega}\) and \(\dot{\omega}\) in the HTML viewer, matching `ASTRO - J2SecularRates`; omit it for Keplerian motion. Each run also writes a self-contained HTML viewer beside the PNG. The viewer opens offline and animates the spacecraft on the same conic.
- **ASTRO - PlaneChangeImpulse** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Element angles and `--di` are radians. `--tle` accepts a NORAD two-line element set. `--burn` is `an` or `dn`; the default is the slower node. `--elev` and `--azim` are degrees. Flattening is visual only. The impulse is a pure inclination change, \(\Delta v = 2 v \sin(\Delta i / 2)\). Each run writes a PNG and a self-contained HTML viewer. The viewer flies one revolution on the initial orbit, slows into the node, hinges the inclination, then flies four revolutions on the final orbit. The orbit the spacecraft is on is drawn solid; the other is faded.
- **ASTRO - GroundTrackEarth** — Python 3 with `matplotlib`. Element angles and `--greenwich` are radians. `--tle` accepts a NORAD two-line element set; the TLE epoch does not replace `--greenwich`. Mean motion is Keplerian; first-order \(J_2\) advances \(\Omega\) and \(\omega\) with the same rates as `ASTRO - J2SecularRates`. WGS 84 flattening enters geodetic latitude only. Default \(J_2 = 1.08228\times 10^{-3}\). `--j2 0` is Keplerian inertial motion. The baseline map is 10 orbital periods. `--span` is seconds from epoch, or pass `--t0` and `--t1`. Ellipse only. The PNG land fill is Natural Earth 1:110m land, public domain.
- **ASTRO - J2SecularRates** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Element angles are radians. `--tle` accepts a NORAD two-line element set. Ellipse only. First-order \(J_2\) nodal and apsidal rates, plus the sun-synchronous inclination from those rates. `--greenwich` and `--di` are accepted unused so a GroundTrackEarth or PlaneChangeImpulse command can be reused. Default \(R_E\) is WGS 84 \(6378137\,\mathrm{m}\). Default \(J_2 = 1.08228\times 10^{-3}\). The sun-sync year is \(365.2422\) days.
- **ATMOS - Standard1976** — Python 3 standard library only. Hydrostatic model from sea level through 86 km. It does not use the NASA Glenn three-zone fit.
- **ATMOS - KineticTemperatureAbove86km** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Four-segment kinetic temperature from 86 km through 1000 km. Pressure and density are omitted. It does not use the NASA Glenn three-zone fit.
- **ATMOS - TransportProperties** — Python 3 standard library only. Viscosity, conductivity, and mean particle speed from temperature. Altitude mode reuses `ATMOS - Standard1976` through 86 km. Density-dependent lengths need altitude or temperature plus pressure. It does not use the NASA Glenn three-zone fit.
- **AERO - IsentropicStagnation** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. An omitted `--gamma` is \(1.4\). Absolute totals and sonic states only for each static that was given. Sound speed uses \(\sqrt{\gamma p/\rho}\) when pressure and density are both given; with temperature alone it uses 1976 dry-air \(R\). No shock.
- **AERO - NormalShock** — Python 3 with `matplotlib`. An omitted `--gamma` is \(1.4\). Upstream Mach is at least 1. Entropy is reported as \(\Delta s/R\).
- **AERO - PrandtlMeyerAndShocks** — Python 3 with `matplotlib`. Deflection is in radians. A two-dimensional wedge, not a cone.
- **AERO - ConicalShock** — Python 3 with `numpy` and `matplotlib`. Half-angle is in radians. A right circular cone at zero incidence, not a wedge. An omitted `--gamma` is \(1.4\).
- **AERO - DiamondAirfoilShockExpansion** — Python 3 with `matplotlib`. Half-angle and angle of attack are radians. Reuses `AERO - PrandtlMeyerAndShocks`. Symmetric diamond only; trailing-edge wake matching is omitted.
- **AERO - AirplanePerformanceParameters** — Python 3 standard library only. Sea-level density and an altitude lookup both come from `ATMOS - Standard1976`. A climb rate needs `--thrust` or `--power`.
- **AERO - ClimbPerformance** — Python 3 with `matplotlib`. Pass `--thrust` or `--power`, not both. Pass `--alt` or `--rho`, not both. `--oat` needs `--alt` and uses `AERO - DensityAndPressureAltitude`. An omitted `--cutoff` is 100 ft/min (`service_ceiling_rate`). An omitted `--z-end` ends the PNG at 1.1 times the absolute ceiling. `--clmax` is optional. Angles are radians. Thrust and useful power do not fall with altitude.
- **AERO - BreguetRangeEndurance** — Python 3 standard library only. Weight-based TSFC is `--ct` in \(1/\mathrm{s}\). Weight-based power SFC is `--c` in \(1/\mathrm{m}\). Cruise only; climb, descent, reserves, and wind are omitted.
- **AERO - WingGeometry** — Python 3 with `matplotlib`. Chords are streamwise. Sweep is in radians. An omitted sweep draws an unswept leading edge. An omitted sweep station is the quarter chord.
- **AERO - V-nDiagram** — Python 3 with `matplotlib`. Equivalent airspeed is `stall_speed` at 1976 sea-level density from `ATMOS - Standard1976`. True airspeeds use `--rho`. The negative line is the limit load factor. The plot end is not a dive speed.
- **AERO - IncompressibleLevelTurn** — Python 3 with `matplotlib`. Bank is radians. Pass one of `--bank`, `--n`, `--thrust`, or `--power`. Thrust or power also needs `--cd0`, `--ar`, and `--e`. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Speeds are true airspeed at `--rho`. Dynamic pressure is incompressible \(\frac12\rho V^{2}\). The stall limit is `stall_speed` with \(W\) replaced by \(nW\), the same relation as the V-n stall boundary. Sustained \(n\) is thrust equal to drag at \(L = nW\) on the parabolic polar.
- **AERO - SymmetricPullUp** — Python 3 with `matplotlib`. Pass one of `--n`, `--radius`, `--pitch-rate`, `--thrust`, or `--power`. Thrust or power also needs `--cd0`, `--ar`, and `--e`. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Speeds are true airspeed at `--rho`. Dynamic pressure is incompressible \(\frac12\rho V^{2}\). Radius is \(R = V^{2}/(g(n-1))\) and pitch rate is \(\omega = g(n-1)/V\). The stall limit is `stall_speed` with \(W\) replaced by \(nW\). Sustained \(n\) is thrust equal to drag at \(L = nW\) on the parabolic polar.
- **AERO - SteadyGlide** — Python 3 with `matplotlib`. `--alt` is geometric metres on the 1976 atmosphere. `--height` is the height drop for range and is omitted when range is not requested. `--clmax` is optional. Angles are radians. Incompressible polar; density is constant over the height drop.
- **AERO - TakeoffGroundRoll** — Python 3 with `matplotlib`. Pass `--thrust` or `--power`, not both. `--power` needs `--static`. Pass `--alt` or `--rho`, not both. `--oat` needs `--alt` and uses `AERO - DensityAndPressureAltitude`. An omitted `--k-lo` is \(1.2\). `--clmax` is optional. Level dry runway; no wind, slope, obstacle, or rotation segment. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Speeds are true airspeed.
- **AERO - LandingGroundRoll** — Python 3 with `matplotlib`. An omitted `--thrust` is idle \(0\). Pass `--alt` or `--rho`, not both. `--oat` needs `--alt` and uses `AERO - DensityAndPressureAltitude`. An omitted `--k-td` is \(1.3\). `--clmax` is optional. Level dry runway; no flare, float, wind, slope, obstacle, or reverse-thrust schedule. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Speeds are true airspeed.
- **PROP - IdealPropeller** — Python 3 with `matplotlib`. Pass `--alt` or `--rho`. `--power` is ideal shaft power, not useful power. An altitude lookup uses `ATMOS - Standard1976`. Incompressible actuator disk; no swirl, tip loss, or blade drag.
- **PROP - IdealTurboJet** — Python 3 with `matplotlib`. Pass `--alt` or both `--temperature` and `--pressure`. Optional `--heating-value`, `--cp`, and `--gamma`. An altitude lookup uses `ATMOS - Standard1976`. Ideal Brayton turbojet only; no fan, afterburner, or maps.
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
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --m0 10000 --mp 6000 --isp 300 --tb 80 --gamma 1.4
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --m0 10000 --mp 6000 --isp 300 --tb 80 --kick 0.05 --alt 0
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --check
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --throat 0.0005 --lstar 1.2 --pc 2e6 --radius 0.05 --thickness 0.002 --allowable 6.25e7
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --check
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --a 1e-5 --n 0.5 --ab 0.4 --throat 0.002 --rho 1800 --cstar 1550
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --check
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --a 1e-5 --n 0.5 --port 0.02 --length 0.4 --outer 0.05 --throat 0.0005 --rho 1800 --cstar 1550
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --check
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --r1 6774200 --r2 7374200
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --alt 400000 --ecc 0.2 --html
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --check
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --rp 6774200 --vinf 3200 --html
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --check
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --r1 6774200 --r2 42164000 --rb 2e8 --html
python "skills/ASTRO - BiellipticTransfer/bielliptic_transfer.py" --check
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --a 10000000 --e 0.3 --i 0.9 --raan 0.6 --aop 1.2 --nu 0.8
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --tle "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927" "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --a=-25000000 --e 1.4 --i 1.1 --raan 0.8 --aop 0.5 --nu 0.6
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --rx 8000000 --ry 0 --rz 0 --vx 0 --vy 7000 --vz 1500
python "skills/ASTRO - OrbitalParameters/orbital_parameters.py" --check
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --a 10000000 --e 0.3 --i 0.9 --raan 0.6 --aop 1.2 --nu 0.8 --di 0.2
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --rx 8000000 --ry 0 --rz 0 --vx 0 --vy 7000 --vz 1500 --di 0.3
python "skills/ASTRO - PlaneChangeImpulse/plane_change_impulse.py" --check
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --a 7000000 --e 0.05 --i 0.9 --raan 0.4 --aop 0.2 --nu 0.1 --greenwich 0.3
python "skills/ASTRO - GroundTrackEarth/ground_track_earth.py" --check
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --a 7000000 --e 0.05 --i 0.9 --raan 0.4 --aop 0.2 --nu 0.1
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --a 10000000 --e 0.3 --i 0.9 --raan 0.6 --aop 1.2 --nu 0.8 --di 0.2
python "skills/ASTRO - J2SecularRates/j2_secular_rates.py" --check
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --pc 2e6 --gamma 1.25 --alt 0
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --check
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --moment 1200 --section-modulus 0.003 --allowable 500000
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --moment 1200 --inertia 9e-5 --fiber 0.03 --out beam_bending_stress.png
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --check
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --E 2e11 --inertia 1e-6 --length 2 --area 1e-3 --yield 6e8
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --E 2e11 --inertia 1e-6 --length 2 --ends fixed-fixed --out euler_column_buckling.png
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --check
python "skills/CTRL - SecondOrderResponse/second_order_response.py" --wn 2 --zeta 0.5 --out second_order_response.png
python "skills/CTRL - SecondOrderResponse/second_order_response.py" --mass 1 --stiffness 4 --damping 2 --settling-percent 2
python "skills/CTRL - SecondOrderResponse/second_order_response.py" --check
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --part 2,0,0,0 --part 2,2,0,0 --about-origin
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --part 1,0,1,0,0,0,2 --about-origin
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --check
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --alt 60000 --emissivity 0.8
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --alt 60000 --mach-axis
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --rho 3.1459e-4 --wall-temp 300 --temperature 216.65
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --check
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --speed 7000 --gamma 0.5235987755982988 --beta 100
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --speed 7000 --gamma 0.5235987755982988 --mass 500 --cd 0.5 --area 2 --out ballistic_entry_peak_load.png
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --check
python "skills/POWER - SolarArrayOutput/solar_array_output.py" --area 2 --efficiency 0.28 --incidence 0 --packing 0.9 --inherent 0.85 --life-degradation 0.005 --years 5 --alt 400000 --beta 0 --out solar_array_output.png
python "skills/POWER - SolarArrayOutput/solar_array_output.py" --area 2 --specific-power 300 --incidence 0.5235987755982988 --eclipse-fraction 0.35
python "skills/POWER - SolarArrayOutput/solar_array_output.py" --check
python "skills/POWER - BatteryEnergyBudget/battery_energy_budget.py" --energy 100 --dod 0.3 --eta-c 0.9 --eta-d 0.9 --load 50 --eclipse 1800 --day 3600 --out battery_energy_budget.png
python "skills/POWER - BatteryEnergyBudget/battery_energy_budget.py" --load 100 --eclipse 1800 --dod 0.2 --eta-c 0.92 --eta-d 0.88 --voltage 28
python "skills/POWER - BatteryEnergyBudget/battery_energy_budget.py" --ah 12 --voltage 28 --dod 0.25 --eta-c 0.95 --eta-d 0.9 --load 40 --peak 120 --peak-duration 60
python "skills/POWER - BatteryEnergyBudget/battery_energy_budget.py" --check
python "skills/COMMS - FreeSpaceLinkBudget/free_space_link_budget.py" --pt 10 --gt 100 --gr 1000 --freq 2.2e9 --range 1000e3 --ts 290 --bandwidth 1e6 --bitrate 1e6 --ebn0-req 10 --out free_space_link_budget.png
python "skills/COMMS - FreeSpaceLinkBudget/free_space_link_budget.py" --pt 1 --dt 1 --eta-t 0.55 --dr 2 --eta-r 0.6 --wavelength 0.03 --range 50000
python "skills/COMMS - FreeSpaceLinkBudget/free_space_link_budget.py" --check
python "skills/ATMOS - Standard1976/standard_1976.py" --alt 11000
python "skills/ATMOS - Standard1976/standard_1976.py" --check
python "skills/ATMOS - KineticTemperatureAbove86km/kinetic_temperature_above_86km.py" --alt 120000
python "skills/ATMOS - KineticTemperatureAbove86km/kinetic_temperature_above_86km.py" --alt 200000 --out kinetic_temperature_above_86km.png
python "skills/ATMOS - KineticTemperatureAbove86km/kinetic_temperature_above_86km.py" --check
python "skills/ATMOS - TransportProperties/transport_properties.py" --alt 11000
python "skills/ATMOS - TransportProperties/transport_properties.py" --temp 288.15 --pressure 101325
python "skills/ATMOS - TransportProperties/transport_properties.py" --check
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --weight 10000 --area 16 --cd0 0.02 --ar 8 --e 0.8 --clmax 1.6 --alt 0
python "skills/AERO - AirplanePerformanceParameters/airplane_performance.py" --check
python "skills/AERO - ClimbPerformance/climb_performance.py" --weight 10000 --area 16 --cd0 0.02 --ar 8 --e 0.8 --alt 0 --power 50000
python "skills/AERO - ClimbPerformance/climb_performance.py" --check
python "skills/AERO - BreguetRangeEndurance/breguet_range_endurance.py" --ld 16 --wi 1e5 --wf 8e4 --speed 250 --ct 2e-5 --c 1e-7 --eta 0.85
python "skills/AERO - BreguetRangeEndurance/breguet_range_endurance.py" --check
python "skills/AERO - NormalShock/normal_shock.py" --mach 2
python "skills/AERO - NormalShock/normal_shock.py" --check
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
python "skills/AERO - SymmetricPullUp/symmetric_pull_up.py" --speed 50 --weight 10000 --area 16 --clmax 1.6 --rho 1.225 --n 2
python "skills/AERO - SymmetricPullUp/symmetric_pull_up.py" --speed 50 --weight 10000 --area 16 --clmax 1.6 --rho 1.225 --cd0 0.02 --ar 8 --e 0.8 --thrust 1500
python "skills/AERO - SymmetricPullUp/symmetric_pull_up.py" --check
python "skills/AERO - SteadyGlide/steady_glide.py" --weight 10000 --area 16 --cd0 0.02 --ar 8 --e 0.8 --alt 0 --clmax 1.6 --height 1000
python "skills/AERO - SteadyGlide/steady_glide.py" --check
python "skills/AERO - TakeoffGroundRoll/takeoff_ground_roll.py" --weight 10000 --area 16 --clto 0.8 --mu 0.02 --cd0 0.02 --ar 8 --e 0.8 --alt 0 --clmax 1.6 --thrust 2500
python "skills/AERO - TakeoffGroundRoll/takeoff_ground_roll.py" --check
python "skills/AERO - LandingGroundRoll/landing_ground_roll.py" --weight 10000 --area 16 --cltd 0.8 --mu 0.4 --cd0 0.02 --ar 8 --e 0.8 --alt 0 --clmax 1.6
python "skills/AERO - LandingGroundRoll/landing_ground_roll.py" --check
python "skills/PROP - IdealPropeller/ideal_propeller.py" --power 150000 --diameter 2 --speed 50 --rho 1.225
python "skills/PROP - IdealPropeller/ideal_propeller.py" --check
python "skills/PROP - IdealTurboJet/ideal_turbojet.py" --mach 0.8 --alt 11000 --tit 1600 --opr 20
python "skills/PROP - IdealTurboJet/ideal_turbojet.py" --check
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
