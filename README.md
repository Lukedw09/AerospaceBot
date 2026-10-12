# AerospaceBot

Cursor agent skills for aerospace engineering: checked formulas and small physics programs the bot can run and report, instead of reinventing equations or redrawing plots by hand.

## Skills

| Skill | Purpose |
| --- | --- |
| [`FormulaCatalouge`](skills/FormulaCatalouge) | Select and use verified aerospace formulas (compressible flow including Fanno and Rayleigh ducts, atmosphere including 1976 density above 86 km, rocket propulsion including a single-revolution Lambert transfer, in-space propellant, electric-propulsion burn time and power, phasing, and Clohessy–Wiltshire motion, aerodynamics including flat-plate skin friction, thin-airfoil section lift, ideal Brayton turbojet and ramjet, design-point inlet recovery, non-ideal turbojet, afterburner, separate-stream turbofan, airflow sizing, drag delta-v, and phugoid and short-period periods, structures including Euler column buckling and thin-wall membrane stress, mass properties, aerothermodynamics including Allen–Eggers peak load, equilibrium glide, planar lifting entry, lumped thermal capacitance, and spacecraft radiative balance, spacecraft power including battery energy budget and duty-cycled load, space communications including pass data volume and rain attenuation, dynamics and control including second-order response, Bode gain and phase margins, 3-2-1 attitude kinematics, true proportional navigation, disturbance torques, base-excitation transmissibility, reaction-wheel inertia, magnetic moment, and Miles rms acceleration, orbital phase angle, synodic period, inclined excess speed, pressurant blowdown, propellant slosh, simply supported plate buckling, Doppler shift, Dutch-roll frequency, geostationary east–west removal, and elevation-mask swath). Only formulas listed in `checks/check.md` are allowed. |
| [`GNC - SecondOrderResponse`](skills/GNC%20-%20SecondOrderResponse) | Run `second_order_response.py` for linear second-order unit-step metrics: damped frequency, overshoot, peak time, 10%–90% rise time, settling time, and under/critical/over-damped class from \(\omega_n\) and \(\zeta\), or from mass, stiffness, and viscous damping. Optional settling band (default 2%). Optional PNG of the unit-step response. |
| [`GNC - ClassicalControlMargins`](skills/GNC%20-%20ClassicalControlMargins) | Run `classical_control_margins.py` for the gain crossover, phase margin, phase crossover, and gain margin of a polynomial loop transfer. Optional series PID. Writes a Bode PNG. Root-locus geometry is not included. Step metrics stay on SecondOrderResponse. |
| [`GNC - ProportionalNavigation`](skills/GNC%20-%20ProportionalNavigation) | Run `proportional_navigation.py` for planar true proportional navigation: instantaneous commanded acceleration \(a_c=N' V_c\dot{\lambda}\) from navigation constant, closing speed, and LOS rate, or a constant-speed planar engagement with PN steering (intercept time or miss distance). Optional engagement-plane PNG. The family name is GNC, beside SecondOrderResponse. |
| [`ADCS - EnvironmentalTorques`](skills/ADCS%20-%20EnvironmentalTorques) | Run `environmental_torques.py` for gravity-gradient, aerodynamic, solar-pressure, and residual magnetic torque. Density comes from altitude; `--rho` is an override. Optional PNG of the torque magnitudes. |
| [`ADCS - SlewMomentum`](skills/ADCS%20-%20SlewMomentum) | Run `slew_momentum.py` in one mode per call: rest-to-rest slew torque and angular impulse, or disturbance momentum \(H=T\tau\). The two modes are separate runs. Optional PNG. |
| [`ADCS - AttitudeKinematics`](skills/ADCS%20-%20AttitudeKinematics) | Run `attitude_kinematics.py` for one 3-2-1 conversion per call: Euler angles to a direction-cosine matrix, the inverse, a scalar-first quaternion, or body rates into Euler rates or quaternion rates. Writes a PNG of the body axes in the reference frame. Kinematics only. |
| [`ADCS - ReactionWheelSizing`](skills/ADCS%20-%20ReactionWheelSizing) | Run `reaction_wheel_sizing.py` for the single-axis wheel inertia \(I_w=H/\omega_{\max}\) that stores a stated momentum at a maximum wheel speed, plus optional momentum and torque margins. \(H\) and \(\tau\) come from separate SlewMomentum runs. Optional PNG of inertia versus wheel speed. |
| [`ADCS - MagneticTorquerSizing`](skills/ADCS%20-%20MagneticTorquerSizing) | Run `magnetic_torquer_sizing.py` for the dipole \(m=T/(B\sin\psi)\) that produces a stated torque in a stated field, plus optional coil current and margins. The field is an input. Optional PNG of dipole versus field. |
| [`VIBR - CantileverNaturalFrequency`](skills/VIBR%20-%20CantileverNaturalFrequency) | Run `cantilever_natural_frequency.py` for the undamped fundamental bending natural frequency of a uniform Euler–Bernoulli cantilever (fixed–free) from Young’s modulus, second moment of area, length, and mass per length or total beam mass. Optional PNG of frequency versus length. First bending mode only; no tip mass, damping, or forced response. |
| [`VIBR - BaseExcitationTransmissibility`](skills/VIBR%20-%20BaseExcitationTransmissibility) | Run `base_excitation_transmissibility.py` for steady displacement transmissibility of a base-excited single-degree-of-freedom oscillator from natural frequency, damping ratio, and drive frequency. Prints the isolation flag and, for light damping, the frequency ratio of peak transmissibility. Optional PNG. Not force transmissibility and not a shock spectrum. |
| [`VIBR - RandomVibeRms`](skills/VIBR%20-%20RandomVibeRms) | Run `random_vibe_rms.py` for Miles rms acceleration of one resonator under a flat spectrum, and the usual three-sigma peak estimate. Exactly one of quality factor or damping ratio. Optional PNG. Not sine transmissibility and not a shock spectrum. |
| [`POWER - SolarArrayOutput`](skills/POWER%20-%20SolarArrayOutput) | Run `solar_array_output.py` for flat-plate solar-array beginning-of-life power, end-of-life power, and orbit-average power from area and efficiency or BOL specific power, solar constant, incidence angle, packing, inherent and life degradation, and optional eclipse fraction or circular-orbit beta. Optional PNG of power versus sun angle. |
| [`POWER - BatteryEnergyBudget`](skills/POWER%20-%20BatteryEnergyBudget) | Run `battery_energy_budget.py` for usable battery energy from nameplate watt-hours or amp-hours with bus voltage, depth of discharge, and charge/discharge efficiencies; time at continuous load; whether an eclipse or peak pulse fits; required capacity from load and eclipse; and optional one-orbit SoC PNG with solar orbit-average power from SolarArrayOutput. No cell electrochemistry or Peukert beyond the supplied efficiencies. |
| [`POWER - DutyCycleLoad`](skills/POWER%20-%20DutyCycleLoad) | Run `duty_cycle_load.py` for orbit-average power, coincident peak power, and eclipse energy from a list of load powers and on-fractions. Hands the eclipse power and duration to BatteryEnergyBudget and the orbit-average power to the end-of-life array requirement. Optional PNG. |
| [`COMMS - FreeSpaceLinkBudget`](skills/COMMS%20-%20FreeSpaceLinkBudget) | Run `free_space_link_budget.py` for vacuum free-space path loss, Friis received power, EIRP, optional \(C/N_0\) or \(C/N\) from system noise temperature and bandwidth, and optional \(E_b/N_0\) and link margin from bit rate and a required \(E_b/N_0\). Antenna gains may be linear or circular diameters with aperture efficiency. Optional PNG of received power versus range. No atmosphere or rain. |
| [`COMMS - PassDataVolume`](skills/COMMS%20-%20PassDataVolume) | Run `pass_data_volume.py` for the bit rate a stored volume requires over a pass, or the volume a rate delivers, with a coding overhead. Hands the rate to FreeSpaceLinkBudget. Optional PNG. |
| [`COMMS - RainAttenuation`](skills/COMMS%20-%20RainAttenuation) | Run `rain_attenuation.py` for slant-path rain attenuation and the linear power ratio from rain rate, frequency, elevation, and effective rainy path length. Coefficients are the NASA TP-1770 Marshall–Palmer nodes. Optional PNG of attenuation versus rain rate. Vacuum path loss stays on FreeSpaceLinkBudget. |
| [`COMMS - DopplerShiftBudget`](skills/COMMS%20-%20DopplerShiftBudget) | Run `doppler_shift_budget.py` for the carrier shift from a radial speed, or the maximum shift of a circular orbit at an elevation mask, and the two-sided tracking span. Earth rotation is omitted on the orbit path. Optional PNG for that path only. |
| [`MASS - CenterOfMassAndInertia`](skills/MASS%20-%20CenterOfMassAndInertia) | Run `center_of_mass_and_inertia.py` for total mass, center of mass, and the inertia tensor about the CG (optionally about the body origin) of a rigid assembly of point masses or parts with optional own-CG inertias and parallel-axis transfer. Writes a PNG of the parts and CG in the body frame. |
| [`MASS - StageCgTravel`](skills/MASS%20-%20StageCgTravel) | Run `stage_cg_travel.py` for the one-axis center of mass of a burning stage as propellant mass drops and its station moves from full to empty. Optional PNG of stack station versus burn fraction. |
| [`MASS - PropellantSloshFrequency`](skills/MASS%20-%20PropellantSloshFrequency) | Run `propellant_slosh_frequency.py` for the first lateral slosh frequency and equivalent pendulum length of a flat free surface in a rigid upright cylinder. Prints `shallow: yes` when \(h/R<0.2\). Optional PNG of frequency versus fill height. |
| [`ROCKET - Area-Mach Graph`](skills/ROCKET%20-%20Area-Mach%20Graph) | Run `area_mach.py` for an isentropic nozzle area-Mach curve, exit Mach from area ratio, exit pressure, ideal thrust, and expansion state. |
| [`ROCKET - PerformanceParameters`](skills/ROCKET%20-%20PerformanceParameters) | Run `performance.py` for frozen-CEA c*, temperature, gamma, ideal Cf, specific impulse, and density impulse. Do not call CEA at reply time. |
| [`ROCKET - ThroatSizingandMassFlow`](skills/ROCKET%20-%20ThroatSizingandMassFlow) | Run `throat_sizing.py` for circular-throat area and diameter from thrust, thrust coefficient, and chamber pressure, and mass flow from characteristic velocity. |
| [`ROCKET - PropellantLoad`](skills/ROCKET%20-%20PropellantLoad) | Run `propellant_load.py` for usable propellant mass and tank volume (total, oxidizer, fuel) from mass flow, burn time, mixture ratio, and liquid densities. |
| [`ROCKET - TankStructureMass`](skills/ROCKET%20-%20TankStructureMass) | Run `tank_structure_mass.py` for tank shell mass, optional structure mass, residual propellant, and total inert from propellant volume, MEOP, material allowables, and residuals fraction. Prints `mp` and `inert` for PayloadtoDeltaV. |
| [`ROCKET - ExpansionMatchEarth`](skills/ROCKET%20-%20ExpansionMatchEarth) | Run `expansion_match.py` for the altitude-matched nozzle expansion ratio on the 1976 U.S. Standard Atmosphere. Area ratio and ideal \(C_F\) come from Area-Mach. |
| [`ROCKET - KickStageNozzle`](skills/ROCKET%20-%20KickStageNozzle) | Run `kick_stage_nozzle.py` for vacuum / above-86 km kick-stage nozzle synthesis: design \(\epsilon\) or \(p_e\), vacuum \(C_F\), conical or length-fraction length, optional shell mass, and Summerfield separation margin against a supplied ambient. The 1976 hydrostatic table is not used for \(p_a\). Optional PNG of vacuum \(C_F\) and length versus \(\epsilon\). |
| [`ROCKET - NozzleChamberDesignLab`](skills/ROCKET%20-%20NozzleChamberDesignLab) | Run `nozzle_chamber_lab.py` only when the user explicitly asks for the interactive nozzle and chamber page. Writes a PNG and a self-contained 2D HTML lab: frozen CEA gas properties, ambient pressure, and live chamber and conical length-fraction geometry. Not a Rao bell, and not a replacement for the one-shot CLI chain. |
| [`ROCKET - KickStageFeasibility`](skills/ROCKET%20-%20KickStageFeasibility) | Run `kick_stage_feasibility.py` for in-space kick-stage T/W and burn-time feasibility: continuous burn duration, restart count, per-coast duration limit, ACS propellant coast budget (sum of coasts), and equal-split ignition T/W bounds. Writes a PNG of T/W versus burn time per arc. |
| [`ROCKET - PayloadtoDeltaV`](skills/ROCKET%20-%20PayloadtoDeltaV) | Run `payload_to_deltav.py` for useful payload from ideal delta-v, or ideal delta-v from useful payload, for one or more stages. A missing delta-v and payload writes a payload-versus-delta-v PNG. |
| [`ROCKET - LossStack`](skills/ROCKET%20-%20LossStack) | Run `loss_stack.py` for actual thrust, specific impulse, thrust coefficient, c*, and mass flow from ideal \(C_F\), ideal \(c^{*}\), and named efficiencies. With throat area and chamber pressure it also prints the lossless thrust and mass flow. Omitted efficiencies stay 1. |
| [`ROCKET - BasicTrajectoryLossesFromBodySurface`](skills/ROCKET%20-%20BasicTrajectoryLossesFromBodySurface) | Run `basic_trajectory_losses_from_body_surface.py` for vacuum delta-v, gravity, drag, and steering losses, and burnout speed, flight-path angle, and altitude of a simplified powered ascent from a spherical surface. Constant flight-path angle is closed form; a gravity-turn kick integrates the ODE. Writes a PNG of the path on the atmosphere. |
| [`ROCKET - FairingAndInterstageMass`](skills/ROCKET%20-%20FairingAndInterstageMass) | Run `fairing_and_interstage_mass.py` for jettisonable fairing and interstage shell masses from diameter, length, and wall thickness times density or an areal density. Prints the masses. No figure. |
| [`ROCKET - VehicleMassBudget`](skills/ROCKET%20-%20VehicleMassBudget) | Run `vehicle_mass_budget.py` for per-stage inert and stacked mass from tanks, engines, fairing, interstage, residuals, or a linear structure law. Prints `payload_to_deltav_stage` strings. Writes a PNG stacked-mass chart. |
| [`ROCKET - LeoDeltaVBudget`](skills/ROCKET%20-%20LeoDeltaVBudget) | Run `leo_delta_v_budget.py` for the ideal design delta-v of a circular LEO: circular speed minus rotation assist plus gravity, drag, steering, circularization, and margin. Writes a PNG bar chart with every term starting at zero. |
| [`ROCKET - StagePropellantSplit`](skills/ROCKET%20-%20StagePropellantSplit) | Run `stage_propellant_split.py` to allocate propellant and inert across stages for an ideal delta-v at a payload or a gross liftoff mass (`equal_dv`, `equal_mr`, or `max_payload`). Writes a PNG of the split. |
| [`ROCKET - MultiStageAscent`](skills/ROCKET%20-%20MultiStageAscent) | Run `multi_stage_ascent.py` for a powered ascent with staging mass drops and an optional fairing jettison. A one-stage constant-angle case with no quadratic drag matches BasicTrajectoryLosses. Writes a trajectory CSV, a PNG of the vehicle on the pad, and an HTML simulation of the flight from the ground to burnout. |
| [`ROCKET - MaxQAndAeroLoad`](skills/ROCKET%20-%20MaxQAndAeroLoad) | Run `max_q_and_aero_load.py` for peak dynamic pressure and an optional angle-of-attack times \(q\) from an ascent CSV. Writes a PNG and an HTML chart of \(q\) versus time. |
| [`ROCKET - StageAscentDesignLab`](skills/ROCKET%20-%20StageAscentDesignLab) | Run `stage_ascent_lab.py` only when the user explicitly asks for the interactive stage-ascent page. Writes a PNG and a self-contained HTML lab: LEO delta-v, stage split, optional inert replacement, ascent, and peak dynamic pressure. Not a replacement for the one-shot CLI chain. |
| [`ROCKET - ElectricPropulsionDeltaV`](skills/ROCKET%20-%20ElectricPropulsionDeltaV) | Run `electric_propulsion_delta_v.py` for vacuum propellant and wet mass, thrusting and calendar burn time, input electrical power, and specific power from dry mass, thrust, delta-v, and specific impulse or exhaust speed. Optional efficiency and duty cycle. Optional PNG of propellant versus delta-v. |
| [`ROCKET - RocketHallThrusterSizing`](skills/ROCKET%20-%20RocketHallThrusterSizing) | Run `rocket_hall_thruster_sizing.py` for Hall-thruster exhaust speed, thrust, mass flow, input power, and ideal singly charged beam current. Exactly one of thrust or power. Optional PNG of beam current versus thrust. |
| [`ROCKET - PressurantBlowdown`](skills/ROCKET%20-%20PressurantBlowdown) | Run `pressurant_blowdown.py` for polytropic ullage pressure after a stated liquid volume leaves, with optional fixed-charge pressurant mass and a pressure-floor flag. Optional PNG of pressure versus expelled volume. Not a regulator or a tank mass. |
| [`ASTRO - LaunchAzimuthInclination`](skills/ASTRO%20-%20LaunchAzimuthInclination) | Run `launch_azimuth_inclination.py` for inclination from latitude and azimuth, the two azimuths that reach a target inclination, and the Earth-rotation assist along the heading. Writes a PNG and an HTML globe with a rotation axis; strokes behind the planet are dotted. |
| [`ASTRO - OrbitInsertionFromBurnout`](skills/ASTRO%20-%20OrbitInsertionFromBurnout) | Run `orbit_insertion_from_burnout.py` for periapsis, apoapsis, atmosphere intersection, and impulsive circularization delta-v from a burnout radius, speed, and flight-path angle. Writes an HTML viewer that shows the coast outside the planet, then raises it into a circle. No PNG. |
| [`ROCKET - ChamberVolumeAndCaseHoopStress`](skills/ROCKET%20-%20ChamberVolumeAndCaseHoopStress) | Run `chamber_case.py` for chamber volume from throat area and \(L^{*}\), and thin-wall hoop stress and margin of safety from pressure, case radius, wall thickness, and allowable stress. |
| [`ROCKET - InjectorOrificeFlow`](skills/ROCKET%20-%20InjectorOrificeFlow) | Run `injector_orifice_flow.py` for orifice area, geometric-area jet speed, injection pressure drop, and optional circular diameter from mass flow, density, and discharge coefficient. Optional PNG of diameter versus count. |
| [`ROCKET - FeedSystemPressureBudget`](skills/ROCKET%20-%20FeedSystemPressureBudget) | Run `feed_system_pressure_budget.py` for manifold pressure, named line drops, hydrostatic head, supply pressure, and a pressure-fed `meop_Pa`. No PNG. |
| [`ROCKET - PumpHydraulicPower`](skills/ROCKET%20-%20PumpHydraulicPower) | Run `pump_hydraulic_power.py` for pump volume flow, hydraulic power, and shaft power. Optional drive power. Optional PNG of shaft power versus pressure rise. Skip for a pressure-fed engine. |
| [`ROCKET - FeedTankDesignLab`](skills/ROCKET%20-%20FeedTankDesignLab) | Run `feed_tank_lab.py` only when the user explicitly asks for the interactive feed and tank page. Writes a PNG and a self-contained 2D HTML lab: oxidizer and fuel side by side, pressure-fed blowdown or an electric pump, injector orifices, and thin-wall tank membrane stress. Not a turbine cycle, and not a replacement for the one-shot CLI chain. |
| [`ROCKET - ThroatGasSideHeatFlux`](skills/ROCKET%20-%20ThroatGasSideHeatFlux) | Run `throat_gas_side_heat_flux.py` for the Bartz gas-side coefficient and heat flux at the throat. Gas properties are inputs or the SP-125 \(\gamma\), \(M\) fit. Not Sutton–Graves. Optional PNG of flux versus chamber pressure. |
| [`ROCKET - RegenerativeCoolantHeatPickUp`](skills/ROCKET%20-%20RegenerativeCoolantHeatPickUp) | Run `regenerative_coolant_heat_pickup.py` for coolant outlet temperature from mass flow, specific heat, and absorbed heat. Optional bulk-temperature limit. Optional PNG of outlet temperature versus mass flow. |
| [`STRUCT - BeamBendingStress`](skills/STRUCT%20-%20BeamBendingStress) | Run `beam_bending_stress.py` for pure elastic bending stress of a beam, spar, longeron, or boom from bending moment and either section modulus or second moment of area with extreme-fiber distance. Optional allowable stress prints margin of safety. Optional PNG of stress versus moment for the fixed section. |
| [`STRUCT - CombinedStressMohr`](skills/STRUCT%20-%20CombinedStressMohr) | Run `combined_stress_mohr.py` for plane-stress principals and the Mohr circle when bending and torsion act together, or when \(\sigma_x\) and \(\tau_{xy}\) are already known. Optional allowable normal stress prints margin of safety. Writes a PNG of the Mohr circle. |
| [`STRUCT - EulerColumnBuckling`](skills/STRUCT%20-%20EulerColumnBuckling) | Run `euler_column_buckling.py` for the elastic Euler critical buckling load of a concentrically loaded prismatic column from Young’s modulus, second moment of area, unsupported length, and end-fix factor \(K\) (pinned–pinned default). Optional area prints critical stress and slenderness; optional compressive yield reports whether Euler is valid or the section would yield first. Optional PNG of critical load versus length for the fixed section. |
| [`STRUCT - ThinWallPressureVessel`](skills/STRUCT%20-%20ThinWallPressureVessel) | Run `thin_wall_pressure_vessel.py` for thin-wall hoop and longitudinal stress of a closed cylinder, or membrane stress of a sphere. An allowable stress sizes the zero-margin wall or prints margin of safety. Optional PNG of stress versus radius. Distinct from the motor-case hoop program and from tank mass. |
| [`STRUCT - PanelBuckling`](skills/STRUCT%20-%20PanelBuckling) | Run `panel_buckling.py` for the elastic critical compressive stress of a rectangular plate with four simply supported edges. A missing length uses \(k=4\). An applied stress prints margin of safety. Optional PNG of critical stress versus \(b/t\). |
| [`STRUCT - FractureCriticalCrack`](skills/STRUCT%20-%20FractureCriticalCrack) | Run `fracture_critical_crack.py` for the critical half-length of a through crack in a wide plate from \(K_{Ic}\), stress, and geometry factor \(Y\). An actual half-length prints margin of safety. Optional PNG of critical length versus stress. |
| [`STRUCT - FatigueGoodman`](skills/STRUCT%20-%20FatigueGoodman) | Run `fatigue_goodman.py` for an infinite-life Goodman or Soderberg check of one alternating and mean stress. Prints the factor of safety and the allowable alternating stress. Writes a PNG of the constant-life line. Not a Miner sum and not crack growth. |
| [`THERM - SonicStagnationHeatFlux`](skills/THERM%20-%20SonicStagnationHeatFlux) | Run `sonic_stagnation_heat_flux.py` for Sutton–Graves stagnation-point convective heat flux and freestream dynamic pressure from speed, nose radius, and freestream density or 1976 altitude. Optional wall temperature uses the heat-transfer coefficient form; optional emissivity prints radiative-equilibrium wall temperature. Writes a PNG of flux versus speed at fixed density and nose radius. Does not model dissociation beyond the Sutton–Graves air coefficient. |
| [`THERM - BallisticEntryPeakLoad`](skills/THERM%20-%20BallisticEntryPeakLoad) | Run `ballistic_entry_peak_load.py` for Allen–Eggers nonlifting ballistic-entry peak deceleration and the altitude of that peak in an exponential atmosphere from ballistic coefficient (or mass, \(C_D\), and area), entry speed, and entry flight-path angle. Default Earth fit from NACA TN 4047. Optional PNG of peak load versus entry angle. Companion to stagnation heat flux; not a full trajectory. |
| [`THERM - EquilibriumGlideEntry`](skills/THERM%20-%20EquilibriumGlideEntry) | Run `equilibrium_glide_entry.py` for equilibrium-glide peak horizontal deceleration and the characteristic heat-flux scale from entry speed, lift-to-drag ratio, and ballistic coefficient. Default atmosphere matches the ballistic Earth fit. Optional PNG of peak load versus lift-to-drag ratio. Not a 3-degree-of-freedom trajectory. |
| [`THERM - LiftingEntryTrajectory`](skills/THERM%20-%20LiftingEntryTrajectory) | Run `lifting_entry_trajectory.py` for a planar point-mass entry with lift and bank. Reports peak aerodynamic load, where that peak occurs, and whether the path skips out, including above circular speed. Exponential TN 4047 atmosphere or 1976 density. Optional constant latitude and inertial heading from north for a rotating planet; the run also prints the air-relative entry heading. PNG of load versus time and altitude versus speed only when `--out` is passed. |
| [`THERM - LumpedCapacitanceTransient`](skills/THERM%20-%20LumpedCapacitanceTransient) | Run `lumped_capacitance_transient.py` for lumped thermal-capacitance \(T(t)\) under convection to a fixed ambient (or time to a target temperature) from mass, specific heat, surface area, \(h\), \(T_i\), and \(T_{\infty}\). Optional \(k\) and \(L_c\) print Biot number and warn if Bi is not ≪ 1. Optional PNG of temperature versus time. |
| [`THERM - SpacecraftRadiativeBalance`](skills/THERM%20-%20SpacecraftRadiativeBalance) | Run `spacecraft_radiative_balance.py` for single-node equilibrium temperature or the radiator area that holds a temperature, from absorbed solar, albedo, and planet infrared. Optional PNG of temperature versus radiator area. Not entry heating. |
| [`ROCKET - SolidMotorParameters`](skills/ROCKET%20-%20SolidMotorParameters) | Run `solid_motor_parameters.py` for burning-area ratio, equilibrium chamber pressure, burn rate, and solid-propellant mass flow from Saint Robert burn-rate inputs, grain and throat areas, density, and \(c^{*}\). |
| [`ROCKET - CircularPortGrainHistory`](skills/ROCKET%20-%20CircularPortGrainHistory) | Run `circular_port_grain_history.py` for chamber pressure, burning-area ratio, and remaining web versus time of an internal-burning circular grain with inhibited ends. Writes a PNG of the three histories. |
| [`ROCKET - SolidMotorGrainLab`](skills/ROCKET%20-%20SolidMotorGrainLab) | Run `solid_motor_grain_lab.py` only when the user explicitly asks for the interactive grain page. Writes a PNG and a self-contained HTML lab: circular-port history, Saint Robert equilibrium, lateral and longitudinal sections, and case margin. Not a replacement for the one-shot CLI chain. |
| [`ASTRO - MultiBurnLeoRaise`](skills/ASTRO%20-%20MultiBurnLeoRaise) | Run `multi_burn_leo_raise.py` for a finite-thrust multi-burn raise from parking LEO to a higher circular LEO, with gravity loss, steered delta-v, burn arcs, time of flight, and an optional inclination change. Writes a PNG; optional `--html` writes a self-contained 3D viewer. |
| [`ASTRO - HohmannTransfer`](skills/ASTRO%20-%20HohmannTransfer) | Run `hohmann_transfer.py` for circular speed, escape speed, specific energy, impulsive delta-v, coast time, and \(|r_2|/|r_1|\) between two circular orbits. Writes a PNG of the transfer looking down the orbit normal. Optional `--html` writes a self-contained 3D viewer with the two burns. Recommends a bi-elliptic transfer when that ratio is large enough that a path through infinity would be cheaper. |
| [`ASTRO - OrbitDesignLab`](skills/ASTRO%20-%20OrbitDesignLab) | Run `orbit_design_lab.py` only when the user explicitly asks for the interactive orbit page. Writes a PNG and a self-contained HTML lab: Hohmann versus bielliptic on one globe, with the other Earth-orbit tools on secondary tabs and a named delta-v export to VacuumPropellantMass. Not a replacement for the one-shot CLI chain. |
| [`ASTRO - LambertTransfer`](skills/ASTRO%20-%20LambertTransfer) | Run `lambert_transfer.py` for a single-revolution transfer between two inertial position vectors and a time of flight. Prints both velocities and the transfer conic. Writes a PNG in the transfer plane. Optional `--html` writes a self-contained 3D viewer. Multi-revolution branches are not solved. |
| [`ASTRO - RendezvousPhasing`](skills/ASTRO%20-%20RendezvousPhasing) | Run `rendezvous_phasing.py` for the coplanar phasing ellipse that closes a phase angle in an integer number of revolutions on one circular orbit: semi-major axis, wait, and the two equal impulsive burns. Hands the delta-v to VacuumPropellantMass. Optional PNG looking down the orbit normal. Unequal radii are a Hohmann transfer. |
| [`ASTRO - RelativeOrbitClohessyWiltshire`](skills/ASTRO%20-%20RelativeOrbitClohessyWiltshire) | Run `relative_orbit_clohessy_wiltshire.py` for the planar Clohessy–Wiltshire state of a deputy about a circular chief, plus the impulses that null the relative velocity or close the relative ellipse. Optional PNG in the chief frame. Not a six-degree-of-freedom or eccentric solution. |
| [`ASTRO - SolarSystemBody`](skills/ASTRO%20-%20SolarSystemBody) | Run `solar_system_body.py` for the gravitational parameter, radius, and heliocentric semi-major axis, eccentricity, and inclination of the Sun, a planet, or Pluto. Prints mean, perihelion, and aphelion radii. No figure. Earth's radius and \(\mu\) stay the catalogue Earth. |
| [`ASTRO - HeliocentricHohmann`](skills/ASTRO%20-%20HeliocentricHohmann) | Run `heliocentric_hohmann.py` for the Sun-centered Hohmann half-ellipse between two planets or Pluto: transfer elements, coplanar and inclined excess speeds, phase angle, and synodic period. Writes a PNG looking down the ecliptic normal. The excess speeds are not the rocket burns. |
| [`ASTRO - LeoToLowOrbit`](skills/ASTRO%20-%20LeoToLowOrbit) | Run `leo_to_low_orbit.py` for the patched-conic delta-v from a circular LEO to a circular low orbit about another planet or Pluto, including the cheaper placement of the target's ecliptic inclination. Writes a PNG of the heliocentric half-ellipse with the two burns. Does not size a rocket. |
| [`ASTRO - HyperbolicExcess`](skills/ASTRO%20-%20HyperbolicExcess) | Run `hyperbolic_excess.py` for hyperbolic excess speed, characteristic energy \(C_3\), the periapsis burn from a circular park onto a hyperbola, the turning angle, and the true anomaly of the asymptote. Writes a PNG of the park and the hyperbola. Optional `--html` writes a self-contained 3D viewer of the burn and the morph from the circle onto the hyperbola. |
| [`ASTRO - GravityAssistFlyby`](skills/ASTRO%20-%20GravityAssistFlyby) | Run `gravity_assist_flyby.py` for a planar patched-conic flyby: the turned excess velocity, heliocentric speeds, and the unpowered \(\Delta v\). Writes a PNG of the planet-centered hyperbola. Optional `--html` writes the same self-contained animated viewer as OrbitalParameters, with the planet and the spacecraft coast. Not the park-orbit burn. |
| [`ASTRO - BiellipticTransfer`](skills/ASTRO%20-%20BiellipticTransfer) | Run `bielliptic_transfer.py` for the three-burn delta-v, time of flight, and \(|r_2|/|r_1|\) of a coplanar bi-elliptic transfer between two circular orbits, from radii, classical elements, NORAD two-line element sets, or inertial states plus an intermediate apoapsis. Writes a PNG looking down the orbit normal. Optional `--html` writes a self-contained 3D viewer with the three burns. Recommends a Hohmann transfer when this apoapsis is not cheaper. |
| [`ASTRO - OrbitalParameters`](skills/ASTRO%20-%20OrbitalParameters) | Run `orbital_parameters.py` for classical elements, a NORAD two-line element set, or the inertial state of a Keplerian conic, plus time of flight for one orbit or between two anomalies on an ellipse, and optional circular-orbit eclipse duration with `--beta`. Writes a PNG of the orbit and a self-contained HTML viewer. Optional `--j2` applies first-order \(J_2\) secular rates in the viewer. |
| [`ASTRO - PlaneChangeImpulse`](skills/ASTRO%20-%20PlaneChangeImpulse) | Run `plane_change_impulse.py` for the impulsive delta-v of a pure inclination change at the ascending or descending node, from classical elements, a NORAD two-line element set, or an inertial state. Writes a PNG of both planes and a self-contained HTML viewer. |
| [`ASTRO - GeostationaryStationKeeping`](skills/ASTRO%20-%20GeostationaryStationKeeping) | Run `geostationary_station_keeping.py` for the yearly north–south plane-change impulse and the east–west impulse \(2ve\) that remove a stated inclination drift and eccentricity drift. Optional PNG waterfall for one year. Hands the pieces to VacuumPropellantMass. |
| [`ASTRO - CoverageAndRevisit`](skills/ASTRO%20-%20CoverageAndRevisit) | Run `coverage_and_revisit.py` for the swath and footprint of one satellite above an elevation mask, and the equatorial revisit in periods and seconds. Optional PNG of swath versus elevation. Not a Walker constellation. |
| [`ASTRO - ConjunctionMissDistance`](skills/ASTRO%20-%20ConjunctionMissDistance) | Run `conjunction_miss_distance.py` for the geometric miss distance, time of closest approach, and relative speed of two Keplerian states over a forward window. Optional PNG of range versus time. Not a collision probability and not a TLE. |
| [`ASTRO - GroundTrackEarth`](skills/ASTRO%20-%20GroundTrackEarth) | Run `ground_track_earth.py` for the geodetic latitude and longitude of the subsatellite point over ten orbital periods by default, from elements, a NORAD two-line element set, or an inertial state plus the Greenwich angle at epoch. First-order \(J_2\) advances the node and periapsis. Writes a PNG of the track on a public-domain Natural Earth land map. |
| [`ASTRO - J2SecularRates`](skills/ASTRO%20-%20J2SecularRates) | Run `j2_secular_rates.py` for first-order \(J_2\) nodal and apsidal rates and the sun-synchronous inclination of an Earth ellipse, from the same elements, NORAD two-line element set, or inertial state as GroundTrackEarth or PlaneChangeImpulse. Writes a PNG of those rates against inclination. |
| [`ASTRO - AerodynamicDragDeltaV`](skills/ASTRO%20-%20AerodynamicDragDeltaV) | Run `aerodynamic_drag_delta_v.py` for drag acceleration and delta-v over one circular revolution at constant density. Density comes from altitude; `--rho` is an override. Optional PNG of delta-v per revolution versus altitude. |
| [`ASTRO - VacuumPropellantMass`](skills/ASTRO%20-%20VacuumPropellantMass) | Run `vacuum_propellant_mass.py` for propellant and wet mass from a dry mass, one exhaust speed or specific impulse, and a sum of named vacuum delta-v contributions. Optional growth applies only to that dry mass. Optional PNG. |
| [`ATMOS - Standard1976`](skills/ATMOS%20-%20Standard1976) | Run `standard_1976.py` for 1976 U.S. Standard Atmosphere temperature, pressure, density, speed of sound, and geometric pressure scale height at one geometric altitude from sea level through 86 km. |
| [`ATMOS - KineticTemperatureAbove86km`](skills/ATMOS%20-%20KineticTemperatureAbove86km) | Run `kinetic_temperature_above_86km.py` for 1976 kinetic temperature and temperature-segment name at one geometric altitude from 86 km through 1000 km. Optional PNG of temperature versus altitude. Does not print pressure or density. |
| [`ATMOS - DensityAbove86km`](skills/ATMOS%20-%20DensityAbove86km) | Run `density_above_86km.py` for 1976 mass density, pressure, and species number densities from just above 86 km through 1000 km. Mean solar activity. Optional PNG of density versus altitude. At or below 86 km, use Standard1976. |
| [`ATMOS - TransportProperties`](skills/ATMOS%20-%20TransportProperties) | Run `transport_properties.py` for 1976 dry-air dynamic viscosity, thermal conductivity, and mean particle speed from geometric altitude or temperature. With altitude, or temperature plus pressure, also print density, kinematic viscosity, mean free path, collision frequency, and number density. |
| [`AERO - IsentropicStagnation`](skills/AERO%20-%20IsentropicStagnation) | Run `isentropic_stagnation.py` for isentropic total temperature, pressure, and density from Mach number and optional static state, the sonic reference state, and static and stagnation speeds of sound. Optional PNG of \(p_t/p\) and \(T_t/T\) versus Mach (no shock). |
| [`AERO - NormalShock`](skills/AERO%20-%20NormalShock) | Run `normal_shock.py` for downstream Mach, static pressure, temperature, and density ratios, stagnation-pressure ratio, and entropy jump of a simple normal shock. Writes a PNG of those ratios versus upstream Mach. |
| [`AERO - FannoAndRayleighFlow`](skills/AERO%20-%20FannoAndRayleighFlow) | Run `fanno_and_rayleigh_flow.py` for constant-area Fanno or Rayleigh sonic-reference ratios at one Mach number. Exactly one of `--fanno` or `--rayleigh`. Optional Fanno friction length and Rayleigh stagnation-temperature ratio. Writes a PNG of the ratios versus Mach. |
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
| [`PROP - IdealRamjet`](skills/PROP%20-%20IdealRamjet) | Run `ideal_ramjet.py` for ideal Brayton ramjet (ram compression only) specific thrust, mass-based TSFC, thermal/propulsive/overall efficiency, and nozzle exit speed and temperature from flight Mach \(>1\), freestream \(T,p\) or 1976 altitude, and combustor max total temperature. The PNG plots specific thrust versus Mach at fixed \(T_{t4}\). No compressor, turbine, fan, afterburner, scramjet, or inlet map. |
| [`PROP - InletRecovery`](skills/PROP%20-%20InletRecovery) | Run `inlet_recovery.py` for adiabatic inlet recovery from freestream to the compressor face. Pass a supplied \(\pi_d\) or a pitot inlet (one normal shock times a subsonic diffuser factor). The PNG plots recovery versus Mach. Hand \(\pi_d\) to the cycle skills. |
| [`PROP - NonidealTurbojet`](skills/PROP%20-%20NonidealTurbojet) | Run `nonideal_turbojet.py` for design-point turbojet specific thrust, mass-based TSFC, and station totals with inlet recovery and isentropic component efficiencies. The shaft match includes fuel mass unless `--neglect-fuel-match`. The PNG plots specific thrust versus Mach. No fan and no afterburner. |
| [`PROP - AfterburningTurbojet`](skills/PROP%20-%20AfterburningTurbojet) | Run `afterburning_turbojet.py` for dry and reheat specific thrust, afterburner fuel-air ratio, thrust ratio, and both TSFCs. The nozzle is fully expanded unless `--nozzle convergent`. The PNG plots specific thrust versus afterburner temperature. |
| [`PROP - SeparateStreamTurbofan`](skills/PROP%20-%20SeparateStreamTurbofan) | Run `separate_stream_turbofan.py` for an unmixed turbofan: core and fan specific thrust, inlet-airflow specific thrust, and mass-based TSFC from bypass ratio and fan pressure ratio. The PNG plots specific thrust and TSFC versus bypass ratio. No mixer and no afterburner. |
| [`PROP - AfterburningTurbofan`](skills/PROP%20-%20AfterburningTurbofan) | Run `afterburning_turbofan.py` for that unmixed fan with an afterburner on the core only. Prints dry and reheated specific thrust, core and afterburner fuel–air ratios, and TSFC. The PNG is specific thrust versus afterburner temperature. |
| [`PROP - ScramjetIdealCycle`](skills/PROP%20-%20ScramjetIdealCycle) | Run `scramjet_ideal_cycle.py` for an ideal scramjet: ram compression stops at a supersonic combustor Mach, heat addition is at constant pressure, and the nozzle expands to freestream pressure. A combustor Mach at or below 1 is rejected. The PNG is specific thrust versus flight Mach. |
| [`PROP - IdealTurboprop`](skills/PROP%20-%20IdealTurboprop) | Run `ideal_turboprop.py` for a design-point ideal turboprop. Shaft power is the ideal-turbojet nozzle enthalpy. Propeller thrust is \(\eta_p P/V_0\) per unit inlet airflow. Residual jet thrust is omitted. The PNG is thrust and TSFC versus Mach. |
| [`PROP - EngineAirflowSizing`](skills/PROP%20-%20EngineAirflowSizing) | Run `engine_airflow_sizing.py` for inlet airflow, capture area and diameter, optional compressor-face area, and optional equal-stage count from required net thrust and specific thrust. Static flight sizes the face instead of a capture streamtube. The PNG plots airflow and diameter versus thrust. |
| [`AERO - FiniteWingLiftCurve`](skills/AERO%20-%20FiniteWingLiftCurve) | Run `finite_wing_lift_curve.py` for the wing lift-curve slope and the induced angle at \(C_{L,\max}\) from a section slope, zero-lift angle, aspect ratio, and span efficiency. The PDF is lift coefficient versus angle of attack up to stall. |
| [`AERO - EquivalentAirspeed`](skills/AERO%20-%20EquivalentAirspeed) | Run `equivalent_airspeed.py` for Mach number, dynamic pressure, equivalent airspeed, and Reynolds number from a geometric altitude and either true airspeed or Mach number on the 1976 standard atmosphere. |
| [`AERO - DensityAndPressureAltitude`](skills/AERO%20-%20DensityAndPressureAltitude) | Run `density_and_pressure_altitude.py` for dry or moist density, speed of sound, and 1976 pressure and density altitudes from station pressure and outside air temperature. Optional relative humidity and equivalent airspeed. |
| [`AERO - LongitudinalStaticMargin`](skills/AERO%20-%20LongitudinalStaticMargin) | Run `longitudinal_static_margin.py` for the stick-fixed neutral point and static margin from the wing-fuselage and tail lift-curve slopes, downwash, tail dynamic-pressure ratio, tail geometry, and center-of-gravity position. |
| [`AERO - LongitudinalTrim`](skills/AERO%20-%20LongitudinalTrim) | Run `longitudinal_trim.py` for the stick-fixed 1-g angle of attack and elevator that hold level flight. Lift coefficient comes from weight and dynamic pressure, or is supplied. Pitch stiffness comes from \(C_{m\alpha}\), a static-margin fraction, or the same geometry as the neutral-point program. Writes a PNG of \(C_m\) versus angle of attack. |
| [`AERO - PhugoidAndShortPeriod`](skills/AERO%20-%20PhugoidAndShortPeriod) | Run `phugoid_and_short_period.py` for the classical phugoid period and the static short-period frequency from speed, density, wing loading, lift-curve slope, static margin as a fraction of chord, mean chord, and pitch radius of gyration. Optional PNG of the two periods versus speed. Not a fourth-order eigenvalue. |
| [`AERO - DutchRollEstimate`](skills/AERO%20-%20DutchRollEstimate) | Run `dutch_roll_estimate.py` for Dutch-roll frequency, period, and damping from speed, density, wing size, inertias, mass, and the five lateral derivatives. Optional PNG of period and damping versus speed. Not the spiral mode, the roll-subsidence mode, or the full lateral quartic. |
| [`AERO - LateralDirectionalStaticStability`](skills/AERO%20-%20LateralDirectionalStaticStability) | Run `lateral_directional_static_stability.py` for vertical-tail \(C_{n\beta}\) and unswept geometric-dihedral \(C_{l\beta}\), or for stability signs on derivatives the user already has. Writes a PNG of the two derivatives. Not the Dutch-roll oscillation. |
| [`AERO - RayleighPitotMach`](skills/AERO%20-%20RayleighPitotMach) | Run `rayleigh_pitot_mach.py` for freestream Mach number and dynamic pressure from measured pitot pressure, freestream static pressure, and \(\gamma\). Below Mach 1 uses isentropic stagnation; above Mach 1 uses the Rayleigh-Pitot relation. |
| [`AERO - PrandtGlauertCorrectionandCriticalMach`](skills/AERO%20-%20PrandtGlauertCorrectionandCriticalMach) | Run `prandtl_glauert_correction_and_critical_mach.py` for the two-dimensional Prandtl-Glauert correction of an incompressible lift or moment coefficient, an uncorrected drag coefficient, and the critical Mach number from a minimum pressure coefficient. Coefficients may be supplied or taken from a NACA Report 824 chart. |
| [`AERO - ParachuteDescentRate`](skills/AERO%20-%20ParachuteDescentRate) | Run `parachute_descent_rate.py` for the steady open-canopy descent rate from mass, drag coefficient, and area. Density is the 1976 standard at `--alt`, or `--rho`. Repeat `--reef` for reefed canopies. Optional PNG of rate versus altitude. |
| [`AERO - NACAFourDigitSection`](skills/AERO%20-%20NACAFourDigitSection) | Run `naca_four_digit_section.py` for the mean line, surface ordinates, and NACA Report 824 measured section lift, moment, and drag of a NACA four-digit airfoil. Writes PNGs of the section, coefficients versus angle of attack in degrees, and the drag polar. |
| [`AERO - ThinAirfoilTheory`](skills/AERO%20-%20ThinAirfoilTheory) | Run `thin_airfoil_theory.py` for inviscid thin-section lift from an angle of attack, or from a NACA four-digit mean line, plus the quarter-chord moment of that mean line. Writes a PNG of \(c_l\) versus angle of attack. Measured tunnel polars stay on NACAFourDigitSection. |
| [`AERO - FlatPlateBoundaryLayer`](skills/AERO%20-%20FlatPlateBoundaryLayer) | Run `flat_plate_boundary_layer.py` for laminar Blasius or one-seventh-power turbulent skin friction on a smooth zero-incidence plate. `--law` is required. Optional friction drag when density, speed, length, and span are given. Writes a PNG of plate \(C_f\) versus Reynolds number. |
| [`AERO - WindTunnelSimilarity`](skills/AERO%20-%20WindTunnelSimilarity) | Run `wind_tunnel_similarity.py` to compare model and full-scale Reynolds and Mach numbers and, when coefficients are taken as equal, to scale a measured force or moment. A relative mismatch above 0.05 is not matched. Writes a PNG of the two Reynolds numbers and Mach numbers. Not a wall correction. |
| [`AERO - WingAirfoilDesignLab`](skills/AERO%20-%20WingAirfoilDesignLab) | Run `wing_airfoil_lab.py` only when the user explicitly asks for the interactive wing and airfoil page. Writes a PNG and a self-contained 2D HTML lab: NACA section, trapezoidal planform, and a live lift curve with induced drag. |
| [`AERO - CompressibleFlowDesignLab`](skills/AERO%20-%20CompressibleFlowDesignLab) | Run `compressible_flow_lab.py` only when the user explicitly asks for the interactive compressible-flow page. Writes a PNG and a self-contained 2D HTML lab: isentropic stagnation, normal shock, wedge, cone, diamond airfoil, Fanno and Rayleigh ducts, Prandtl–Glauert, and Rayleigh–Pitot. |

`AERO - WingAirfoilDesignLab` is an opt-in interactive view of `AERO - NACAFourDigitSection`, `AERO - WingGeometry`, and `AERO - FiniteWingLiftCurve`. It does not replace those programs.

`AERO - CompressibleFlowDesignLab` is an opt-in interactive view of `AERO - IsentropicStagnation`, `AERO - NormalShock`, `AERO - PrandtlMeyerAndShocks`, `AERO - ConicalShock`, `AERO - DiamondAirfoilShockExpansion`, `AERO - FannoAndRayleighFlow`, `AERO - PrandtGlauertCorrectionandCriticalMach`, and `AERO - RayleighPitotMach`. It does not replace those programs. Prandtl–Glauert on the page uses user coefficients only.

Each skill has a `SKILL.md` that tells the agent when to use it and how to respond.

## Liquid rocket engine design path

Run these in order for a preliminary liquid engine. Quote each program's stdout into the next call. Do not invent a missing input, and do not add an orchestrator.

`ROCKET - NozzleChamberDesignLab` is an interactive 2D HTML alternative for steps 1–5 (performance through nozzle and chamber). Run it only when the user explicitly asks for the lab. It does not replace or orchestrate this CLI chain.

`ROCKET - FeedTankDesignLab` is an opt-in interactive view of `ROCKET - FeedSystemPressureBudget`, `ROCKET - InjectorOrificeFlow`, `ROCKET - PumpHydraulicPower`, `ROCKET - PressurantBlowdown`, `ROCKET - TankStructureMass`, and `ROCKET - PropellantLoad`. It does not replace those programs.

1. `ROCKET - PerformanceParameters` — \(c^{*}\), \(T_c\), \(\gamma\), \(M\), ideal \(C_F\).
2. `ROCKET - LossStack` — delivered \(C_F\), \(c^{*}\), and \(\dot{m}\) when a throat is known.
3. `ROCKET - ThroatSizingandMassFlow` — throat area, diameter, and mass flow.
4. `ROCKET - ChamberVolumeAndCaseHoopStress` — chamber volume and case hoop stress.
5. `ROCKET - Area-Mach Graph`, `ROCKET - ExpansionMatchEarth`, or `ROCKET - KickStageNozzle` — nozzle.
6. `ROCKET - InjectorOrificeFlow` — orifice area and injection \(\Delta p\).
7. `ROCKET - FeedSystemPressureBudget` — supply pressure and pressure-fed `meop_Pa`.
8. `ROCKET - PropellantLoad` — oxidizer and fuel mass, volume, and branch flow.
9. `ROCKET - TankStructureMass` — tank mass from propellant volume and MEOP.
10. `ROCKET - ThroatGasSideHeatFlux` — throat gas-side flux.
11. `ROCKET - RegenerativeCoolantHeatPickUp` — coolant outlet temperature from that flux times a stated area.
12. `ROCKET - PumpHydraulicPower` — only for a pump-fed branch.

The vehicle that uses this engine is the Ground-to-LEO path below. Quote each stdout key into the next call. Do not add an orchestrator.

## Ground-to-LEO vehicle design path

Preliminary liquid LOX/RP stack from the motor through circular LEO. A solid stage replaces the liquid motor block for that stage only. Angles are radians.

`ROCKET - StageAscentDesignLab` is an opt-in interactive view of `ROCKET - LeoDeltaVBudget`, `ROCKET - StagePropellantSplit`, `ROCKET - VehicleMassBudget`, `ROCKET - MultiStageAscent`, and `ROCKET - MaxQAndAeroLoad`. It does not replace those programs.

### A. Liquid motor

1. `ROCKET - PerformanceParameters` — \(c^{*}\), \(T_c\), \(\gamma\), ideal \(C_F\), sea-level and vacuum \(I_{sp}\).
2. `ROCKET - LossStack` — delivered \(C_F\), \(c^{*}\), \(I_{sp}\), and \(\dot{m}\) once a throat is known.
3. `ROCKET - ThroatSizingandMassFlow` — throat area, diameter, and mass flow from thrust, \(C_F\), chamber pressure, and \(c^{*}\).
4. `ROCKET - ChamberVolumeAndCaseHoopStress` — chamber volume and case hoop stress.
5. `ROCKET - Area-Mach Graph` and `ROCKET - ExpansionMatchEarth` — booster nozzle at sea level. `ROCKET - KickStageNozzle` — vacuum upper stage.
6. `ROCKET - InjectorOrificeFlow` — orifice area and injection \(\Delta p\).
7. `ROCKET - FeedSystemPressureBudget` — supply pressure and pressure-fed `meop_Pa`.
8. `ROCKET - PropellantLoad` — usable propellant mass and tank volume.
9. `ROCKET - TankStructureMass` — tank and residual inert from that volume and MEOP.
10. `ROCKET - ThroatGasSideHeatFlux` — throat gas-side flux.
11. `ROCKET - RegenerativeCoolantHeatPickUp` — coolant outlet temperature from that flux times a stated area.
12. `ROCKET - PumpHydraulicPower` — pump-fed branch only.

### B. Vehicle and mission

13. `ASTRO - LaunchAzimuthInclination` — site latitude and azimuth or target inclination. `v_rot_assist_m_s` is the rotation credit. Refuses \(i < |\phi|\).
14. `ROCKET - FairingAndInterstageMass` — `fairing_kg`, `interstage_kg`, and `jettison_kg`.
15. `ROCKET - VehicleMassBudget` — tanks, engines, fairing, and interstage, or \(m_s = m_H + k m_p\). Prints `payload_to_deltav_stage`.
16. `ROCKET - LeoDeltaVBudget` — `dv_design_m_s` for the named circular LEO. First pass may use stated losses; a later pass may replace them with ascent losses and `dv_circ_m_s`.
17. `ROCKET - StagePropellantSplit` — propellant and inert for `dv_design_m_s`.
18. `ROCKET - PayloadtoDeltaV` — verify payload at that ideal delta-v with the split's stage strings.
19. `ROCKET - MultiStageAscent` — powered flight, staging, and the fairing jettison. Writes the trajectory CSV.
20. `ROCKET - MaxQAndAeroLoad` — \(q_\max\) from that CSV.
21. Optional structure: `STRUCT - BeamBendingStress` with a moment formed from `alpha_q_max`, a stated area, and a stated arm, and `STRUCT - EulerColumnBuckling` when the user supplies the section.
22. `ASTRO - OrbitInsertionFromBurnout` — burnout `r`, \(V\), and \(\gamma\), with the ascent body radius and \(\mu\). A parking orbit needs `closed_orbit: yes` and `atmosphere_intersection: no`.
23. `ATMOS - Standard1976` at altitudes through 86 km. `AERO - DensityAndPressureAltitude` when the station is off-nominal.
24. In-space follow-on when requested: `ROCKET - KickStageFeasibility`, `ASTRO - MultiBurnLeoRaise`, `ASTRO - HohmannTransfer`, `ASTRO - PlaneChangeImpulse`, `ASTRO - VacuumPropellantMass`, `ASTRO - AerodynamicDragDeltaV`.

### C. Solid stage

`ROCKET - SolidMotorParameters` and `ROCKET - CircularPortGrainHistory` replace steps 1–12 for that stage. Skip tanks, injector, feed, pump, and regenerative cooling for a solid stage.

`ROCKET - SolidMotorGrainLab` is an interactive HTML alternative for that stage's grain history and case margin. Run it only when the user explicitly asks for the lab. It does not replace the one-shot CLI chain.

`app/tests/test_ground_to_leo.py` runs this chain on several LEO cases and writes a pass/fail summary.

## Air-breathing engine design path

Run these for a preliminary air-breathing engine. Quote each program's stdout into the next call. Do not invent a missing input, and do not add an orchestrator. The ideal Brayton skills stay available when every component efficiency is 1 and the inlet is perfect.

1. `PROP - InletRecovery` — \(\pi_d\), \(T_{t2}\), and \(p_{t2}\). Skip only when the inlet is perfect (\(\pi_d=1\)).
2. `PROP - NonidealTurbojet`, `PROP - AfterburningTurbojet`, `PROP - SeparateStreamTurbofan`, or `PROP - AfterburningTurbofan` — specific thrust and TSFC at the flight condition. Pass \(\pi_d\) from the inlet step. `PROP - IdealTurboprop` and `PROP - ScramjetIdealCycle` are the ideal propeller and supersonic-burner cycles.
3. `PROP - EngineAirflowSizing` — airflow, capture or face diameter, and an optional stage count from the required thrust and that specific thrust.

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
  ROCKET - TankStructureMass/
    SKILL.md
    tank_structure_mass.py  # tank/structure/residual inert for PayloadtoDeltaV (key: value stdout)
  ROCKET - ExpansionMatchEarth/
    SKILL.md
    expansion_match.py   # optimal expansion ratio versus altitude (key: value stdout, optional PNG)
  ROCKET - KickStageNozzle/
    SKILL.md
    kick_stage_nozzle.py # vacuum / above-86 km kick-stage nozzle (key: value stdout, optional PNG)
  ROCKET - NozzleChamberDesignLab/
    SKILL.md
    nozzle_chamber_lab.py  # interactive 2D nozzle and chamber page (key: value stdout, PNG + HTML)
    js/                     # browser recompute of the nozzle, throat, chamber, and CEA lookup
    viewer/template.html
  ROCKET - KickStageFeasibility/
    SKILL.md
    kick_stage_feasibility.py  # T/W, burn-time, restart, ACS coast budget (key: value stdout, PNG)
  ROCKET - PayloadtoDeltaV/
    SKILL.md
    payload_to_deltav.py # payload versus ideal delta-v (key: value stdout, sweep PNG)
  ROCKET - LossStack/
    SKILL.md
    loss_stack.py        # delivered CF, c*, Isp, thrust, and mass flow (key: value stdout)
  ROCKET - BasicTrajectoryLossesFromBodySurface/
    SKILL.md
    basic_trajectory_losses_from_body_surface.py  # gravity, drag, and steering losses from a spherical surface (key: value stdout, PNG)
  ROCKET - FairingAndInterstageMass/
    SKILL.md
    fairing_and_interstage_mass.py  # fairing and interstage shell mass (key: value stdout, PNG)
  ROCKET - VehicleMassBudget/
    SKILL.md
    vehicle_mass_budget.py  # stage inert and stacked mass (key: value stdout, PNG)
  ROCKET - LeoDeltaVBudget/
    SKILL.md
    leo_delta_v_budget.py  # circular-LEO design delta-v (key: value stdout, PNG)
  ROCKET - StagePropellantSplit/
    SKILL.md
    stage_propellant_split.py  # propellant allocation for an ideal delta-v (key: value stdout, PNG)
  ROCKET - MultiStageAscent/
    SKILL.md
    multi_stage_ascent.py  # staged powered ascent (key: value stdout, CSV, PNG + HTML)
  ROCKET - MaxQAndAeroLoad/
    SKILL.md
    max_q_and_aero_load.py  # peak dynamic pressure from an ascent CSV (key: value stdout, PNG + HTML)
  ROCKET - StageAscentDesignLab/
    SKILL.md
    stage_ascent_lab.py  # stage split, mass budget, LEO delta-v, ascent, and max-q (key: value stdout, PNG + HTML)
    js/                  # budget, split, ascent, and peak-q relations
    viewer/template.html # self-contained page; logic is inlined at bake time
  ROCKET - ElectricPropulsionDeltaV/
    SKILL.md
    electric_propulsion_delta_v.py  # propellant, burn time, and input power (optional PNG)
  ROCKET - RocketHallThrusterSizing/
    SKILL.md
    rocket_hall_thruster_sizing.py  # thrust, power, and ideal beam current (optional PNG)
  ROCKET - PressurantBlowdown/
    SKILL.md
    pressurant_blowdown.py  # polytropic ullage pressure (optional PNG)
  ASTRO - LaunchAzimuthInclination/
    SKILL.md
    launch_azimuth_inclination.py  # inclination, azimuth, and rotation assist (key: value stdout, PNG + HTML)
  ASTRO - OrbitInsertionFromBurnout/
    SKILL.md
    orbit_insertion_from_burnout.py  # burnout state to circularization (key: value stdout, PNG + HTML)
  ROCKET - ChamberVolumeAndCaseHoopStress/
    SKILL.md
    chamber_case.py      # chamber volume, hoop stress, margin of safety (key: value stdout)
  ROCKET - InjectorOrificeFlow/
    SKILL.md
    injector_orifice_flow.py  # orifice area, jet speed, injection drop (key: value stdout, optional PNG)
  ROCKET - FeedSystemPressureBudget/
    SKILL.md
    feed_system_pressure_budget.py  # supply pressure and pressure-fed MEOP (key: value stdout)
  ROCKET - PumpHydraulicPower/
    SKILL.md
    pump_hydraulic_power.py  # pump volume flow and shaft power (key: value stdout, optional PNG)
  ROCKET - FeedTankDesignLab/
    SKILL.md
    feed_tank_lab.py     # pressure-fed or electric-pump feed and tanks (key: value stdout, PNG + HTML)
    js/                  # feed, injector, pump, blowdown, tank, and propellant relations
    viewer/template.html # self-contained page; logic is inlined at bake time
  ROCKET - ThroatGasSideHeatFlux/
    SKILL.md
    throat_gas_side_heat_flux.py  # Bartz throat heat flux (key: value stdout, optional PNG)
  ROCKET - RegenerativeCoolantHeatPickUp/
    SKILL.md
    regenerative_coolant_heat_pickup.py  # coolant outlet temperature (key: value stdout, optional PNG)
  STRUCT - BeamBendingStress/
    SKILL.md
    beam_bending_stress.py  # pure bending stress, optional MS and PNG
  STRUCT - CombinedStressMohr/
    SKILL.md
    combined_stress_mohr.py  # bending-plus-torsion principals and Mohr circle (PNG)
  STRUCT - EulerColumnBuckling/
    SKILL.md
    euler_column_buckling.py  # elastic Euler buckling load, optional yield check and PNG
  STRUCT - ThinWallPressureVessel/
    SKILL.md
    thin_wall_pressure_vessel.py  # cylinder hoop/longitudinal or sphere membrane stress (optional PNG)
  STRUCT - PanelBuckling/
    SKILL.md
    panel_buckling.py  # simply supported plate buckling stress (optional PNG)
  STRUCT - FractureCriticalCrack/
    SKILL.md
    fracture_critical_crack.py  # wide-plate critical half-length (optional PNG)
  STRUCT - FatigueGoodman/
    SKILL.md
    fatigue_goodman.py  # Goodman or Soderberg infinite-life line (PNG)
  GNC - SecondOrderResponse/
    SKILL.md
    second_order_response.py  # second-order step metrics and optional PNG
  GNC - ClassicalControlMargins/
    SKILL.md
    classical_control_margins.py  # Bode gain and phase margins, optional series PID (PNG)
  GNC - ProportionalNavigation/
    SKILL.md
    proportional_navigation.py  # true PN a_c and planar engagement (optional PNG)
  ADCS - EnvironmentalTorques/
    SKILL.md
    environmental_torques.py  # gravity-gradient, aero, solar, and magnetic torques (optional PNG)
  ADCS - SlewMomentum/
    SKILL.md
    slew_momentum.py  # rest-to-rest slew or disturbance momentum, one mode per run (optional PNG)
  ADCS - AttitudeKinematics/
    SKILL.md
    attitude_kinematics.py  # 3-2-1 direction cosines, quaternions, and kinematic rates (PNG)
  ADCS - ReactionWheelSizing/
    SKILL.md
    reaction_wheel_sizing.py  # single-axis wheel inertia and optional margins (optional PNG)
  ADCS - MagneticTorquerSizing/
    SKILL.md
    magnetic_torquer_sizing.py  # dipole moment and optional coil current (optional PNG)
  VIBR - CantileverNaturalFrequency/
    SKILL.md
    cantilever_natural_frequency.py  # cantilever fundamental bending frequency (optional PNG)
  VIBR - BaseExcitationTransmissibility/
    SKILL.md
    base_excitation_transmissibility.py  # base-excited displacement transmissibility (optional PNG)
    formulas.md
    checks/
    sources.md
  VIBR - RandomVibeRms/
    SKILL.md
    random_vibe_rms.py  # Miles rms acceleration (optional PNG)
  MASS - StageCgTravel/
    SKILL.md
    stage_cg_travel.py  # one-axis stage CG versus burn fraction (optional PNG)
  MASS - CenterOfMassAndInertia/
    SKILL.md
    center_of_mass_and_inertia.py  # CG and inertia tensor of a rigid assembly (PNG)
  MASS - PropellantSloshFrequency/
    SKILL.md
    propellant_slosh_frequency.py  # first lateral slosh frequency (optional PNG)
  THERM - SonicStagnationHeatFlux/
    SKILL.md
    sonic_stagnation_heat_flux.py  # Sutton-Graves stagnation heat flux (PNG)
  THERM - BallisticEntryPeakLoad/
    SKILL.md
    ballistic_entry_peak_load.py  # Allen-Eggers peak deceleration / altitude (optional PNG)
  THERM - EquilibriumGlideEntry/
    SKILL.md
    equilibrium_glide_entry.py  # equilibrium-glide peak load and heat-flux scale (optional PNG)
  THERM - LiftingEntryTrajectory/
    SKILL.md
    lifting_entry_trajectory.py  # planar lifting entry, peak load, and skip (optional PNG)
  THERM - LumpedCapacitanceTransient/
    SKILL.md
    lumped_capacitance_transient.py  # lumped T(t), time-to-target, optional Biot and PNG
    formulas.md
    checks/
    sources.md
  THERM - SpacecraftRadiativeBalance/
    SKILL.md
    spacecraft_radiative_balance.py  # single-node equilibrium temperature or radiator area (optional PNG)
  POWER - SolarArrayOutput/
    SKILL.md
    solar_array_output.py  # flat-plate solar-array BOL/EOL/orbit-average power (optional PNG)
  POWER - BatteryEnergyBudget/
    SKILL.md
    battery_energy_budget.py  # battery usable energy, eclipse/peak fit, required capacity, SoC PNG
  POWER - DutyCycleLoad/
    SKILL.md
    duty_cycle_load.py  # orbit-average and peak load, eclipse energy (optional PNG)
  COMMS - FreeSpaceLinkBudget/
    SKILL.md
    free_space_link_budget.py  # vacuum Friis path loss, Pr, optional C/N0 and Eb/N0 margin (optional PNG)
  COMMS - PassDataVolume/
    SKILL.md
    pass_data_volume.py  # pass bits or required bit rate (optional PNG)
  COMMS - RainAttenuation/
    SKILL.md
    rain_attenuation.py  # slant-path rain attenuation and power ratio (optional PNG)
  COMMS - DopplerShiftBudget/
    SKILL.md
    doppler_shift_budget.py  # carrier shift and two-sided span (optional PNG)
  ROCKET - SolidMotorParameters/
    SKILL.md
    solid_motor_parameters.py  # solid-motor K, pc, burn rate, mass flow (key: value stdout)
  ROCKET - CircularPortGrainHistory/
    SKILL.md
    circular_port_grain_history.py  # circular-port pc, K, remaining web versus time (PNG)
  ROCKET - SolidMotorGrainLab/
    SKILL.md
    solid_motor_grain_lab.py  # interactive circular-port grain page (key: value stdout, PNG + HTML)
    js/                     # browser recompute of Saint Robert history and case hoop
    viewer/template.html
  ATMOS - Standard1976/
    SKILL.md
    standard_1976.py     # 1976 temperature, pressure, density, sound speed, scale height
  ATMOS - KineticTemperatureAbove86km/
    SKILL.md
    kinetic_temperature_above_86km.py  # 1976 kinetic T above 86 km (key: value stdout, optional PNG)
  ATMOS - DensityAbove86km/
    SKILL.md
    density_above_86km.py  # 1976 density, pressure, and species above 86 km (optional PNG)
  ATMOS - TransportProperties/
    SKILL.md
    transport_properties.py  # 1976 viscosity, conductivity, mean free path (key: value stdout)
  ASTRO - MultiBurnLeoRaise/
    SKILL.md
    multi_burn_leo_raise.py  # finite-thrust multi-burn LEO raise (key: value stdout, PNG, optional HTML)
    example_thrust_profile.csv
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - HohmannTransfer/
    SKILL.md
    hohmann_transfer.py  # Hohmann delta-v and coast (key: value stdout, PNG, optional HTML viewer)
  ASTRO - OrbitDesignLab/
    SKILL.md
    orbit_design_lab.py  # opt-in Earth-orbit studio (PNG plus self-contained HTML)
    js/                    # browser ports of the Earth-orbit programs
    viewer/                # page template and vendored three.min.js
  ASTRO - LambertTransfer/
    SKILL.md
    lambert_transfer.py  # single-revolution Lambert velocities and conic (PNG, optional HTML)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - RendezvousPhasing/
    SKILL.md
    rendezvous_phasing.py  # coplanar phasing wait and delta-v (optional PNG)
  ASTRO - RelativeOrbitClohessyWiltshire/
    SKILL.md
    relative_orbit_clohessy_wiltshire.py  # planar CW state and hold/null impulses (optional PNG)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - SolarSystemBody/
    SKILL.md
    solar_system_body.py  # Sun, planet, and Pluto constants (key: value stdout)
    bodies.json            # screened NSSDCA constants; Earth mu is g0*R0^2
  ASTRO - HeliocentricHohmann/
    SKILL.md
    heliocentric_hohmann.py  # Sun-centered Hohmann coast, excess speeds, phase (key: value stdout, PNG)
  ASTRO - LeoToLowOrbit/
    SKILL.md
    leo_to_low_orbit.py  # LEO to planetary low orbit delta-v (key: value stdout, PNG)
  ASTRO - HyperbolicExcess/
    SKILL.md
    hyperbolic_excess.py  # circular-park escape onto a hyperbola (key: value stdout, PNG, optional HTML viewer)
    viewer/                # Three.js template and vendored three.min.js
  ASTRO - GravityAssistFlyby/
    SKILL.md
    gravity_assist_flyby.py  # planar flyby velocity patch (PNG, optional animated HTML viewer)
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
  ASTRO - GeostationaryStationKeeping/
    SKILL.md
    geostationary_station_keeping.py  # yearly north-south and east-west impulses (optional PNG)
  ASTRO - CoverageAndRevisit/
    SKILL.md
    coverage_and_revisit.py  # swath and equatorial revisit (optional PNG)
  ASTRO - ConjunctionMissDistance/
    SKILL.md
    conjunction_miss_distance.py  # geometric miss distance (optional PNG)
  ASTRO - GroundTrackEarth/
    SKILL.md
    ground_track_earth.py  # subsatellite lat/lon (key: value stdout, PNG)
    data/                  # Natural Earth 1:110m land shapefile (public domain)
  ASTRO - J2SecularRates/
    SKILL.md
    j2_secular_rates.py    # J2 nodal/apsidal rates and sun-sync inclination (key: value stdout, PNG)
  ASTRO - AerodynamicDragDeltaV/
    SKILL.md
    aerodynamic_drag_delta_v.py  # drag delta-v per circular revolution (optional PNG)
  ASTRO - VacuumPropellantMass/
    SKILL.md
    vacuum_propellant_mass.py  # propellant from a sum of vacuum delta-v pieces (optional PNG)
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
  AERO - FannoAndRayleighFlow/
    SKILL.md
    fanno_and_rayleigh_flow.py   # Fanno or Rayleigh sonic-reference ratios (key: value stdout, PNG)
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
  PROP - IdealRamjet/
    SKILL.md
    ideal_ramjet.py        # ideal Brayton ramjet Fs, TSFC, efficiencies (key: value stdout, PNG)
  PROP - InletRecovery/
    SKILL.md
    inlet_recovery.py      # station 0 to 2 recovery (key: value stdout, PNG)
  PROP - NonidealTurbojet/
    SKILL.md
    nonideal_turbojet.py   # design-point turbojet with component efficiencies (key: value stdout, PNG)
  PROP - AfterburningTurbojet/
    SKILL.md
    afterburning_turbojet.py  # dry and reheat turbojet (key: value stdout, PNG)
  PROP - SeparateStreamTurbofan/
    SKILL.md
    separate_stream_turbofan.py  # unmixed turbofan Fs and TSFC (key: value stdout, PNG)
  PROP - AfterburningTurbofan/
    SKILL.md
    afterburning_turbofan.py  # core-only reheat on an unmixed fan (key: value stdout, PNG)
  PROP - ScramjetIdealCycle/
    SKILL.md
    scramjet_ideal_cycle.py  # ideal scramjet Fs and TSFC (key: value stdout, PNG)
  PROP - IdealTurboprop/
    SKILL.md
    ideal_turboprop.py  # ideal turboprop shaft power and thrust (key: value stdout, PNG)
  PROP - EngineAirflowSizing/
    SKILL.md
    engine_airflow_sizing.py  # airflow and diameter from required thrust (key: value stdout, PNG)
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
  AERO - LongitudinalTrim/
    SKILL.md
    longitudinal_trim.py  # stick-fixed 1-g alpha and elevator (PNG)
  AERO - PhugoidAndShortPeriod/
    SKILL.md
    phugoid_and_short_period.py  # phugoid and static short-period periods (optional PNG)
  AERO - DutchRollEstimate/
    SKILL.md
    dutch_roll_estimate.py  # Dutch-roll frequency and damping (optional PNG)
  AERO - LateralDirectionalStaticStability/
    SKILL.md
    lateral_directional_static_stability.py  # Cn_beta and Cl_beta estimates (PNG)
  AERO - RayleighPitotMach/
    SKILL.md
    rayleigh_pitot_mach.py  # pitot Mach and dynamic pressure (key: value stdout)
  AERO - PrandtGlauertCorrectionandCriticalMach/
    SKILL.md
    prandtl_glauert_correction_and_critical_mach.py  # PG correction and M_cr (key: value stdout, PNG)
  AERO - ParachuteDescentRate/
    SKILL.md
    parachute_descent_rate.py  # steady canopy descent rate (optional PNG)
  AERO - NACAFourDigitSection/
    SKILL.md
    naca_four_digit_section.py  # four-digit ordinates and Report 824 cl, cm, cd (key: value stdout, PNGs)
    data/report824_polars.json  # digitized Langley 2-D pressure-tunnel charts
  AERO - ThinAirfoilTheory/
    SKILL.md
    thin_airfoil_theory.py  # inviscid thin-section lift and quarter-chord moment (PNG)
  AERO - FlatPlateBoundaryLayer/
    SKILL.md
    flat_plate_boundary_layer.py  # laminar or 1/7-power turbulent plate friction (PNG)
  AERO - WindTunnelSimilarity/
    SKILL.md
    wind_tunnel_similarity.py  # Reynolds and Mach match, coefficient load scale (PNG)
  AERO - WingAirfoilDesignLab/
    SKILL.md
    wing_airfoil_lab.py  # interactive 2D wing and airfoil page (key: value stdout, PNG + HTML)
    js/                  # browser recompute of the section, planform, and lift curve
    viewer/template.html
  AERO - CompressibleFlowDesignLab/
    SKILL.md
    compressible_flow_lab.py  # interactive compressible-flow classroom page (key: value stdout, PNG + HTML)
    js/                  # browser recompute of the waves, ducts, and ratio curves
    viewer/template.html
```

## Requirements

- **FormulaCatalouge** — no extra runtime; the agent reads the markdown references.
- **ROCKET - Area-Mach Graph** — Python 3 with `numpy` and `matplotlib`.
- **ROCKET - PerformanceParameters** — Python 3 with `numpy` and `matplotlib`. Frozen tables are produced offline by `scripts/build_table.py` (`rocketcea`). A reply does not call CEA.
- **ROCKET - ThroatSizingandMassFlow** — Python 3 standard library only.
- **ROCKET - PropellantLoad** — Python 3 standard library only. Pair densities are read from `ROCKET - PerformanceParameters` `scripts/pairs.json`.
- **ROCKET - TankStructureMass** — Python 3 standard library only. Pass `--volume`, `--rho`, `--residuals`, `--meop`, `--allowable`, and `--rho-mat`. Default shape is a sphere; `--shape cylinder` needs `--radius` and sizes flat heads with \(t_{\mathrm{head}}=R\sqrt{p/(S\eta)}\). Refuses when governing \(t/R\ge 0.1\). Optional `--design-factor`, `--boss-factor`, `--eta`, and `--structure` or `--structure-factor`. Prints `payload_to_deltav_stage` for `ROCKET - PayloadtoDeltaV`.
- **ROCKET - ExpansionMatchEarth** — Python 3 with `numpy` and `matplotlib`, because it calls `ROCKET - Area-Mach Graph`. It does not call CEA.
- **ROCKET - KickStageNozzle** — Python 3 with `numpy` and `matplotlib`, because it calls `ROCKET - Area-Mach Graph`. Pass `--pc` with `--epsilon` or `--pe`. Omit `--pa` for vacuum; pass `--pa` for ambient \(C_F\) and Summerfield separation (default `--k-sep` 0.4). Separated nozzles invalidate ambient `CF`/`thrust_N`. Geometry needs `--throat` or `--rt`; mass needs `--thickness` and `--rho-mat`. `--alt` is a note only and does not set ambient from the 1976 table. It does not call CEA.
- **ROCKET - NozzleChamberDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It reads the frozen PerformanceParameters tables at bake time and writes a PNG plus a self-contained HTML file. The page recomputes in the browser. Default ambient pressure is \(101325\,\mathrm{Pa}\). `--open` opens that file.
- **ROCKET - KickStageFeasibility** — Python 3 with `matplotlib` for the PNG. Pass `--thrust`, `--isp`, `--m0`, one of `--mf`/`--mp`/`--dv`, `--tb-max`, and `--restarts-max`. `--coast-max` is per-coast duration; `--acs-mp`/`--acs-mdot` budget the sum of coasts. T/W bounds apply to every equal-split ignition.
- **ROCKET - PayloadtoDeltaV** — Python 3 standard library for a point result. A delta-v sweep also needs `matplotlib`.
- **ROCKET - LossStack** — Python 3 standard library only.
- **ROCKET - BasicTrajectoryLossesFromBodySurface** — Python 3 with `matplotlib`. Pass `--gamma` or `--kick`, not both. Pass `--mf` or `--mp`. Pass `--tb` or `--mdot`. Optional `--cd` needs `--area`. Off-nominal `--oat` uses `AERO - DensityAndPressureAltitude`. An omitted planet is the 1976 Earth radius and \(g_0\). Angles are radians. Vacuum thrust does not vary with ambient pressure.
- **ROCKET - StageAscentDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It calls the LEO delta-v, propellant-split, vehicle-mass, multi-stage ascent, and max-q programs for the seed and writes a PNG plus a self-contained HTML file. The page recomputes in the browser. Default count is two stages. `--open` opens that file. It is an opt-in view of those programs, not a replacement.
- **Ground-to-LEO skills** — `LaunchAzimuthInclination`, `FairingAndInterstageMass`, `VehicleMassBudget`, `LeoDeltaVBudget`, `StagePropellantSplit`, `MultiStageAscent`, `MaxQAndAeroLoad`, and `OrbitInsertionFromBurnout`. Python 3 with `matplotlib`. Fairing, vehicle mass, propellant split, and the LEO delta-v budget write a PNG. Launch azimuth, multi-stage ascent, max-q, and orbit insertion also write a self-contained HTML viewer; the PNG is the opening frame. The ascent viewer flies the vehicle from the pad to burnout. The insertion viewer keeps the coast outside the planet, then raises it into a circle. `MultiStageAscent` also writes a CSV. Pass the ascent `--radius` and `--mu` into orbit insertion. A parking orbit is `closed_orbit: yes` and `atmosphere_intersection: no`.
- **ROCKET - ChamberVolumeAndCaseHoopStress** — Python 3 standard library only.
- **ROCKET - InjectorOrificeFlow** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--mdot`, `--rho`, `--cd`, and exactly one of `--dp` or `--velocity`. Optional `--count`.
- **ROCKET - FeedSystemPressureBudget** — Python 3 standard library only. Pass `--pc` and `--dp-injector`, or `--pc` with `--dp-injector-ox` and `--dp-injector-fuel`. Repeat `--dp name=Pa` for extra drops. `--height` needs a density. `meop_Pa` is the pressure-fed tank suggestion.
- **ROCKET - PumpHydraulicPower** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--mdot`, `--rho`, `--dp`, and `--eta`. Optional `--eta-drive`. Not for a pressure-fed engine.
- **ROCKET - FeedTankDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It calls the feed, injector, pump, blowdown, tank, and propellant programs for the seed and writes a PNG plus a self-contained HTML file. The page recomputes in the browser. Default architecture is pressure-fed. `--open` opens that file. It is an opt-in view of those programs, not a replacement.
- **ROCKET - ThroatGasSideHeatFlux** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--pc`, `--Tc`, `--cstar`, `--curvature`, `--tw`, and `--throat` or `--rt`. Pass `--mu` `--cp` `--pr`, or `--mw` `--gamma`. Omitted `--sigma` and `--recovery` are 1. Not Sutton–Graves.
- **ROCKET - RegenerativeCoolantHeatPickUp** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--mdot`, `--cp`, `--t-in`, and `--q-dot` or `--flux` with `--area`. Optional `--t-max`.
- **STRUCT - BeamBendingStress** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--section-modulus`, or both `--inertia` and `--fiber`. Pure bending only; no axial, shear, or torsion. Optional `--allowable` prints `margin_of_safety`.
- **STRUCT - CombinedStressMohr** — Python 3 with `matplotlib`. Pass `--sigma` and `--tau`, or bending plus torsion loads. Do not mix the paths. Optional `--allowable` uses the larger principal magnitude. The PNG is the Mohr circle.
- **STRUCT - EulerColumnBuckling** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--E`, `--inertia`, and `--length`. Optional `--k` or `--ends` (default pinned–pinned \(K=1\)). Optional `--area` for stress and slenderness; `--yield` needs `--area`. Elastic Euler only; no short-column curve.
- **STRUCT - ThinWallPressureVessel** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--p`, `--radius`, and `--shape` (`cylinder` or `sphere`). Pass `--thickness`, `--allowable`, or both. The governing stress is hoop on a cylinder and membrane on a sphere. A thickness sized from the allowable has zero margin of safety.
- **STRUCT - PanelBuckling** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--E`, `--nu`, `--width`, and `--thickness`. Omit `--length` for a long plate with \(k=4\). Optional `--stress` prints `margin_of_safety`.
- **GNC - SecondOrderResponse** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--wn` with `--zeta`, or `--mass` with `--stiffness` and `--damping`. Optional `--settling-percent` (default 2). Linear unity-gain second-order plant only.
- **GNC - ClassicalControlMargins** — Python 3 with `matplotlib`. Pass `--num` and `--den`, highest power first. Optional `--kp`, `--ki`, and `--kd` form a series PID; omitted gains are zero. The PNG title is `Classical control margins`. Root-locus geometry is not plotted.
- **GNC - ProportionalNavigation** — Python 3 standard library for Mode 1 and the engagement integrator. Optional `--out` (Mode 2) needs `matplotlib`. Pass `--n-prime` with either Mode 1 (`--vc --los-rate`) or Mode 2 (`--range --los-angle` and speed/heading or velocity components). Planar true PN only; not second-order plant metrics.
- **VIBR - CantileverNaturalFrequency** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--E`, `--inertia`, `--length`, and either `--mu` (primary) or `--mass` (\(\mu = m_{\mathrm{beam}}/L\)). Uniform fixed–free Euler–Bernoulli first bending mode only; no tip mass, damping, or forced response.
- **VIBR - BaseExcitationTransmissibility** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--fn`, `--zeta`, and `--f`, all with frequency in hertz. Isolation is `yes` only for a frequency ratio above \(\sqrt{2}\). `r_peak` is printed only when \(\zeta < 1/\sqrt{2}\). `--fn` may be `f_Hz` from CantileverNaturalFrequency.
- **VIBR - RandomVibeRms** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--fn`, `--psd`, and exactly one of `--q` or `--zeta`. `g_3sigma` is the usual peak estimate, not a probability bound. `--fn` may be `f_Hz` from CantileverNaturalFrequency.
- **MASS - CenterOfMassAndInertia** — Needs `matplotlib` for the body-frame PNG. Repeat `--part m,x,y,z` for each mass. Optional own-CG inertias and a trailing parallel-axis flag per part. `--about-origin` also prints the inertia about the body origin.
- **MASS - PropellantSloshFrequency** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--radius` and `--height`. Optional `--g` defaults to \(9.80665\,\mathrm{m/s}^{2}\). `shallow` is `yes` when \(h/R<0.2\).
- **THERM - SonicStagnationHeatFlux** — Python 3 with `matplotlib`. Pass `--speed`, `--nose`, and `--alt` or `--rho`. Optional `--wall-temp` uses the Sutton–Graves coefficient form. Optional `--emissivity` prints radiative-equilibrium wall temperature. Optional `--mach-axis` plots freestream Mach when `--alt` or `--temperature` supplies sound speed. Altitude mode reuses `ATMOS - Standard1976` through 86 km. Earth air only; no dissociation model beyond the TR R-376 air coefficient.
- **THERM - BallisticEntryPeakLoad** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--speed`, `--gamma`, and `--beta` or `--mass`/`--cd`/`--area`. Optional `--scale-height`, `--rho-ref`, and `--z-ref` together override the TN 4047 Earth exponential fit. Nonlifting Allen–Eggers closed form only; not a trajectory integrator.
- **THERM - EquilibriumGlideEntry** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--ve`, `--lod`, and `--beta`. Entry speed must be below circular speed. Optional `--scale-height`, `--rho-ref`, and `--z-ref` together override the same TN 4047 Earth fit. `q_scale` is \(\sqrt{\rho}\,V^{3}\), not a heat flux in W/m². Peak horizontal load is \(1/(L/D)\) in \(g\).
- **THERM - LiftingEntryTrajectory** — Python 3 standard library for the trajectory. `--out` needs `matplotlib` and is the only way to get the PNG; omit it and there is no figure. Pass `--speed`, `--gamma`, `--altitude`, `--lod`, `--beta` or `--mass`/`--cd`/`--area`, and exactly one of `--bank-deg` or `--bank-schedule` (a list of `{t_s, bank_deg}` objects or that list as JSON). Optional `--atmosphere us1976`. Optional `--latitude-deg` and `--heading-deg` together turn on rotation. `--heading-deg` is the inertial heading from north, held constant; the program also prints `heading_air_deg`. Unknown parameters are rejected. No vehicle or trajectory input has a default.
- **THERM - LumpedCapacitanceTransient** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--mass`, `--c`, `--area`, `--h`, `--ti`, `--t-inf`, and exactly one of `--time` or `--target-temp`. Optional `--k` with `--char-length` prints Biot number and warns if Bi > 0.1. Lumped capacitance only; no radiation unless folded into \(h\).
- **THERM - SpacecraftRadiativeBalance** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--area-sun`, `--alpha`, `--epsilon`, and `--area-rad` or `--temperature`. Albedo and planet infrared are optional user inputs. Not entry heating.
- **POWER - SolarArrayOutput** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--area`, `--incidence`, and either `--efficiency` or `--specific-power`. Optional packing, inherent degradation, life degradation, years, solar constant, eclipse fraction, or circular-orbit `--a`/`--alt` with `--beta`. Flat-plate cosine law only.
- **POWER - BatteryEnergyBudget** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--dod`, `--eta-c`, and `--eta-d`. Capacity is `--energy` (W·h) or `--ah` with `--voltage`. Omit capacity and pass `--load` with eclipse timing to size required capacity. Optional `--peak`/`--peak-duration`, `--p-avg` from SolarArrayOutput, and orbit timing (`--eclipse` with `--day` or `--orbit`). No cell electrochemistry or Peukert beyond the supplied efficiencies.
- **POWER - DutyCycleLoad** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass one `--power` and one `--duty` per load. Optional `--eclipse` and matching `--eclipse-duty`. Hands eclipse power and duration to BatteryEnergyBudget.
- **COMMS - FreeSpaceLinkBudget** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--pt`, `--range`, `--freq` or `--wavelength`, and each antenna as linear gain or diameter with aperture efficiency. Optional `--ts`, `--bandwidth`, `--bitrate`, and `--ebn0-req`. Vacuum free space only; gains are linear ratios, not dBi.
- **COMMS - PassDataVolume** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--duration` and exactly one of `--bits` or `--rate`. Optional `--overhead` at or above 1. Hands the rate to FreeSpaceLinkBudget.
- **COMMS - RainAttenuation** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--rate` in mm/h, `--freq` in hertz (2–94 GHz), `--elevation` in radians, and `--path` in metres. `--path` is the effective rainy length. Elevation below 10 degrees prints a warning and does not change that length.
- **COMMS - DopplerShiftBudget** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib` and is drawn only for the orbit path. Pass `--freq` and either `--v-radial` or `--alt`/`--a` with `--elev-min`. Earth rotation is omitted from the orbit range rate.
- **ROCKET - SolidMotorParameters** — Python 3 standard library only.
- **ROCKET - CircularPortGrainHistory** — Python 3 with `matplotlib`. Reuses `ROCKET - SolidMotorParameters`. Ends inhibited; no erosive burning. An omitted `--sliver` is 0.
- **ROCKET - SolidMotorGrainLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It reuses circular-port history, Saint Robert equilibrium, and case hoop stress, and writes a PNG plus a self-contained HTML file. The page recomputes in the browser. The default grain is an \(80\,\mathrm{mm}\) web, \(50\,\mathrm{mm}\) port, and \(1\,\mathrm{m}\) length at Kn \(120\), with \(a\) set so the burn is \(10\,\mathrm{s}\). `--open` opens that file.
- **ASTRO - MultiBurnLeoRaise** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Pass parking elements or a state, `--alt-target` or `--r-target`, and `--thrust`/`--isp`/`--m0` or `--profile`. Optional `--i-target`, `--burns` (\(\ge 2\)), `--mf`/`--mp`. Finite-thrust raise with gravity loss; coasts are Keplerian. `--html` writes a self-contained HTML viewer; `--open` opens it.
- **ASTRO - HohmannTransfer** — Python 3 with `matplotlib`. The PNG looks down the orbit normal. `--html` writes a self-contained HTML viewer beside the PNG; `--open` opens it. The viewer flies the two burns and the transfer coast. The solid trail is the path already flown; the remaining future path stays faded.
- **ASTRO - OrbitDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It calls the Earth-orbit programs for the seed and writes a PNG plus a self-contained HTML file. The page recomputes in the browser on one globe. The default seed is a 400 km circle to geostationary radius. `--open` opens that file. It is an opt-in view of those programs, not a replacement. The LEO-raise tab is the impulsive reference, not the finite-thrust gravity-loss integral.
- **ASTRO - LambertTransfer** — Python 3 with `matplotlib`. Pass both position vectors in meters and `--tof` in seconds. Omit `--mu` for Earth \(\mu=g_0 R_0^2\). `--way` is `short` or `long` (default short). One revolution only. The PNG is the transfer plane. `--html` writes a self-contained HTML viewer beside the PNG; `--open` opens it. A 180 degree chord uses \(p=2 r_1 r_2/(r_1+r_2)\).
- **ASTRO - RendezvousPhasing** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--phase`, `--lead` (`target` or `chaser`), and one circular radius: `--radius` or `--alt`, or a target/chaser pair that names the same radius. Optional `--revs` defaults to 1. Unequal radii are rejected. The two burns are equal; hand either delta-v to VacuumPropellantMass.
- **ASTRO - RelativeOrbitClohessyWiltshire** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--x`, `--z`, `--xdot`, `--zdot`, `--time`, and `--a` or `--alt`. \(x\) is along-track with the chief velocity; \(z\) is radial outward. One run prints the state at that time and both the null and hold impulses. Planar and circular-chief only.
- **ASTRO - HyperbolicExcess** — Python 3 with `matplotlib`. It reuses OrbitalParameters for the planet backdrop. `--rp` is the circular park and the hyperbola periapsis. Pass exactly one of `--vinf`, `--C3`, or `--rinf`. `--rinf` is \(\lvert a\rvert=\mu/v_{\infty}^{2}\), not a station on the path. The PNG is the park, the hyperbola, and the periapsis burn. `--html` writes a self-contained HTML viewer; `--open` opens it. The viewer parks on the circle, morphs through the burn onto the hyperbola, then coasts toward the outgoing asymptote.
- **ASTRO - GravityAssistFlyby** — Python 3 with `matplotlib`. Pass `--rp`, `--turn`, `--vp-x`, and `--vp-y`. Pass `--mu` or `--R0`, and `--vinf` or `--C3`. Pass `--ux` and `--uy`, or `--psi`. `--html` writes the OrbitalParameters viewer: lit planet, hyperbola, and a coasting spacecraft. That page needs `--radius` or `--R0`. Park-burn sizing stays on HyperbolicExcess.
- **ASTRO - BiellipticTransfer** — Python 3 with `matplotlib`. It reuses HohmannTransfer and OrbitalParameters. `--rb` is the common apoapsis and must be at least the larger circular radius. Element angles are radians. The burns are coplanar; a plane change is omitted. Epoch radius from elements, a NORAD TLE, or a state is treated as a circular orbit of that radius. A TLE is passed as two 69-character lines and is not propagated with SGP4. The PNG looks down the orbit normal. `--html` writes a self-contained HTML viewer; `--open` opens it. The viewer flies the three burns and both coasts. The solid trail is the path already flown; the remaining future path stays faded.
- **ASTRO - OrbitalParameters** — Python 3 with `matplotlib`. Element angles are radians. `--tle` accepts a NORAD two-line element set as a Keplerian ellipse; line-2 angles stay in degrees, and SGP4 is not applied. On an ellipse, `tof_s` is always printed: one orbit by default, or the forward coast to optional `--nu2` / `--M2`. Optional `--beta` prints circular-orbit cylindrical-umbra eclipse fraction and duration (\(t_e=f_e T\)) for near-circular ellipses. `--elev` and `--azim` are degrees. Flattening is visual only. Optional `--j2` applies first-order \(J_2\) secular \(\dot{\Omega}\) and \(\dot{\omega}\) in the HTML viewer, matching `ASTRO - J2SecularRates`; omit it for Keplerian motion. Each run also writes a self-contained HTML viewer beside the PNG. The viewer opens offline and animates the spacecraft on the same conic.
- **ASTRO - PlaneChangeImpulse** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Element angles and `--di` are radians. `--tle` accepts a NORAD two-line element set. `--burn` is `an` or `dn`; the default is the slower node. `--elev` and `--azim` are degrees. Flattening is visual only. The impulse is a pure inclination change, \(\Delta v = 2 v \sin(\Delta i / 2)\). Each run writes a PNG and a self-contained HTML viewer. The viewer flies one revolution on the initial orbit, slows into the node, hinges the inclination, then flies four revolutions on the final orbit. The orbit the spacecraft is on is drawn solid; the other is faded.
- **ASTRO - GeostationaryStationKeeping** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--di-year` and `--e-year` in radians and dimensionless eccentricity. Optional `--ns-burns` defaults to 1. Optional `--years` defaults to 1. The PNG is one year. Hand `dv_ns_m_s` and `dv_ew_m_s` to VacuumPropellantMass.
- **ASTRO - CoverageAndRevisit** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--elev-min` and exactly one of `--alt` or `--a`. Revisit is a single satellite at the equator.
- **ASTRO - ConjunctionMissDistance** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. It reuses OrbitalParameters. Pass both inertial states and `--window`. Optional `--mu` overrides \(g_0 R_0^{2}\). `endpoint_minimum: yes` means the closest approach is on the window edge. Not a TLE and not a probability.
- **ASTRO - GroundTrackEarth** — Python 3 with `matplotlib`. Element angles and `--greenwich` are radians. `--tle` accepts a NORAD two-line element set; the TLE epoch does not replace `--greenwich`. Mean motion is Keplerian; first-order \(J_2\) advances \(\Omega\) and \(\omega\) with the same rates as `ASTRO - J2SecularRates`. WGS 84 flattening enters geodetic latitude only. Default \(J_2 = 1.08228\times 10^{-3}\). `--j2 0` is Keplerian inertial motion. The baseline map is 10 orbital periods. `--span` is seconds from epoch, or pass `--t0` and `--t1`. Ellipse only. The PNG land fill is Natural Earth 1:110m land, public domain.
- **ASTRO - J2SecularRates** — Python 3 with `matplotlib`. It reuses OrbitalParameters. Element angles are radians. `--tle` accepts a NORAD two-line element set. Ellipse only. First-order \(J_2\) nodal and apsidal rates, plus the sun-synchronous inclination from those rates. `--greenwich` and `--di` are accepted unused so a GroundTrackEarth or PlaneChangeImpulse command can be reused. Default \(R_E\) is WGS 84 \(6378137\,\mathrm{m}\). Default \(J_2 = 1.08228\times 10^{-3}\). The sun-sync year is \(365.2422\) days.
- **ATMOS - Standard1976** — Python 3 standard library only. Hydrostatic model from sea level through 86 km. It does not use the NASA Glenn three-zone fit.
- **ATMOS - KineticTemperatureAbove86km** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Four-segment kinetic temperature from 86 km through 1000 km. Pressure and density are omitted. It does not use the NASA Glenn three-zone fit.
- **ATMOS - DensityAbove86km** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--alt` in metres, greater than 86000 and at most 1000000. Mean solar activity, exospheric temperature 1000 K. At or below 86 km, use Standard1976.
- **ADCS - EnvironmentalTorques** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass the flag group for each torque requested. Aerodynamic density comes from altitude unless `--rho` is set.
- **ADCS - SlewMomentum** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. One mode per run: `--inertia`, `--angle`, and `--time`, or `--torque` and `--duration`.
- **ADCS - AttitudeKinematics** — Python 3 with `matplotlib`. One `--mode` per run. Angles and rates are radians. The quaternion is scalar-first. Only the 3-2-1 sequence is supported. Pitch near \(\pm\pi/2\) is gimbal lock. The PNG title is `Attitude kinematics`.
- **ADCS - ReactionWheelSizing** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--H`, `--tau`, and `--omega-max`. Optional `--H-max` and `--tau-max` print margins. Do not add the slew impulse and the disturbance impulse unless the user already added them.
- **ADCS - MagneticTorquerSizing** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--torque` and `--b-field`. Optional `--mag-angle` defaults to \(\pi/2\). Coil current needs both `--turns` and `--area`. Optional `--m-max` and `--i-max` print margins. The field is an input.
- **ASTRO - AerodynamicDragDeltaV** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--alt`, `--mass`, `--cd`, and `--area`. Density comes from altitude unless `--rho` is set.
- **ASTRO - VacuumPropellantMass** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--dry`, at least one `--dv`, and exactly one of `--isp` or `--ve`. Optional `--growth` applies only to the dry mass.
- **ROCKET - ElectricPropulsionDeltaV** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--dry`, `--thrust`, `--dv`, and exactly one of `--isp` or `--ve`. Optional `--eta` and `--duty` default to 1. Propellant uses the same vacuum rocket equation. `tb_s` is calendar time.
- **ROCKET - PressurantBlowdown** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--p0`, `--v0`, and `--v-expelled`. Optional `--n` defaults to 1. Optional `--p-min` prints `above_floor`. Pressurant mass needs both `--temperature` and `--r-specific`.
- **ATMOS - TransportProperties** — Python 3 standard library only. Viscosity, conductivity, and mean particle speed from temperature. Altitude mode reuses `ATMOS - Standard1976` through 86 km. Density-dependent lengths need altitude or temperature plus pressure. It does not use the NASA Glenn three-zone fit.
- **AERO - IsentropicStagnation** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. An omitted `--gamma` is \(1.4\). Absolute totals and sonic states only for each static that was given. Sound speed uses \(\sqrt{\gamma p/\rho}\) when pressure and density are both given; with temperature alone it uses 1976 dry-air \(R\). No shock.
- **AERO - NormalShock** — Python 3 with `matplotlib`. An omitted `--gamma` is \(1.4\). Upstream Mach is at least 1. Entropy is reported as \(\Delta s/R\).
- **AERO - FannoAndRayleighFlow** — Python 3 with `matplotlib`. Exactly one of `--fanno` or `--rayleigh`, plus `--mach`. An omitted `--gamma` is \(1.4\). Optional `--fld` is the Fanno friction parameter \(4fL/D\). Optional `--tt-ratio` is the Rayleigh stagnation-temperature ratio. The PNG title is `Fanno flow ratios` or `Rayleigh flow ratios`.
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
- **PROP - IdealRamjet** — Python 3 with `matplotlib`. Pass `--mach` (\(>1\)), `--tmax`, and `--alt` or both `--temperature` and `--pressure`. Optional `--heating-value`, `--cp`, and `--gamma`. An altitude lookup uses `ATMOS - Standard1976`. Ideal Brayton ramjet only; no compressor, turbine, fan, afterburner, scramjet, or inlet map. Warns for \(M<2\) and \(M>5\).
- **PROP - InletRecovery** — Python 3 with `matplotlib`. Pass `--mach` and `--alt` or both `--temperature` and `--pressure`. Pass `--pi-d` or `--pitot`, not both. `--pi-ds` is only for `--pitot`. An altitude lookup uses `ATMOS - Standard1976`. No military-spec recovery schedule.
- **PROP - NonidealTurbojet** — Python 3 with `matplotlib`. Pass `--mach`, `--tit`, `--opr`, and `--alt` or both `--temperature` and `--pressure`. Omitted efficiencies and loss ratios are 1. The shaft match includes fuel mass unless `--neglect-fuel-match`. An altitude lookup uses `ATMOS - Standard1976`. No fan and no afterburner.
- **PROP - AfterburningTurbojet** — Python 3 with `matplotlib`. Pass `--mach`, `--tit`, `--opr`, `--t7`, and a freestream path. The dry core is `PROP - NonidealTurbojet`. `--nozzle convergent` keeps the pressure term when the exit is choked and warns that a real afterburning nozzle is variable-area.
- **PROP - SeparateStreamTurbofan** — Python 3 with `matplotlib`. Pass `--mach`, `--tit`, `--opr`, `--bpr`, `--fpr`, and a freestream path. Overall pressure ratio must exceed the fan pressure ratio. Unmixed streams; no afterburner.
- **PROP - EngineAirflowSizing** — Python 3 with `matplotlib`. Pass `--thrust` and `--fs`. Flying capture area uses `--alt` with `--mach` or `--speed`, or `--rho` with `--speed`. Static `--speed 0` requires `--face-mach`, `--face-pt`, and `--face-tt`. `--opr` and `--stage-pr` together print a stage count.
- **AERO - FiniteWingLiftCurve** — Python 3 with `matplotlib`. Angles are radians. The section slope is per radian. Span efficiency satisfies \(0 < e \le 1\). The PDF ends at stall.
- **AERO - EquivalentAirspeed** — Python 3 standard library only. Temperature, pressure, density, and sound speed come from `ATMOS - Standard1976`. Equivalent airspeed is `freestream_dynamic_pressure` at 1976 sea-level density. It is not calibrated airspeed. An omitted length is 1 m.
- **AERO - DensityAndPressureAltitude** — Python 3 standard library only. The 1976 layers and sea-level density come from `ATMOS - Standard1976`. An omitted `--rh` is dry air. Station pressure above sea-level pressure extrapolates the troposphere below \(H = 0\). Equivalent airspeed is not calibrated airspeed. It does not use the NASA Glenn three-zone fit.
- **AERO - LongitudinalStaticMargin** — Python 3 standard library only. Stick-fixed TN 1670 equation (6). \(l\) is measured from the neutral point. \(q_T/q\) is the tail dynamic-pressure ratio. Both lift-curve slopes use the same angle unit.
- **AERO - LongitudinalTrim** — Python 3 with `matplotlib`. Pass `--a`, `--cm0`, and `--cm-de`. Pass `--CL` or `--q` `--S` `--W`. Pass `--cm-alpha`, or `--kn` as a fraction of chord, or the neutral-point geometry. The PNG is \(C_m\) versus angle of attack.
- **AERO - DutchRollEstimate** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--speed`, `--rho`, `--span`, `--area`, `--ix`, `--iz`, `--mass`, and `--cn-beta`, `--cl-beta`, `--cy-beta`, `--cn-r`, `--cl-p`, all derivatives per radian. A missing derivative is not invented. Not the spiral or roll-subsidence mode.
- **AERO - LateralDirectionalStaticStability** — Python 3 with `matplotlib`. Pass the tail and dihedral geometry, or `--cn-beta` and `--cl-beta`. Do not mix them. Omitted `--eta-v` is 1. Omitted `--taper` is 1. Positive \(C_{n\beta}\) weathervanes. Negative \(C_{l\beta}\) is positive effective dihedral.
- **AERO - FlatPlateBoundaryLayer** — Python 3 with `matplotlib`. `--law` is `laminar` or `turbulent`. Pass `--re`, or `--rho`, `--V`, `--L`, and `--mu` or `--nu`. `--span` needs density, speed, and length and is one wetted side. There is no transition model.
- **AERO - WindTunnelSimilarity** — Python 3 with `matplotlib`. Pass the four Reynolds and Mach numbers, or lengths, speeds, sound speeds, and a viscosity. A relative mismatch above 0.05 is `mismatch`. `--force-m` and `--moment-m` scale only when the coefficients are taken as equal.
- **AERO - PhugoidAndShortPeriod** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--speed`, `--rho`, `--wing-loading`, `--cla` per radian, `--static-margin` as the fraction \(x/c\) (`x_over_c`, not the percent), `--mac`, and `--ky`. The phugoid period uses speed only. The short-period frequency omits pitch damping.
- **AERO - RayleighPitotMach** — Python 3 standard library only. Measured pitot at or above freestream static. An omitted `--gamma` is \(1.4\). The sonic pressure ratio selects isentropic stagnation versus Rayleigh-Pitot.
- **AERO - PrandtGlauertCorrectionandCriticalMach** — Python 3 with `matplotlib`. Freestream Mach is below 1. An omitted `--gamma` is \(1.4\). Pass any combination of `--cl-inc`, `--cm-inc`, `--cd-inc`, and `--cpmin-inc`, or `--naca` with `--alpha` instead of the lift, moment, and drag coefficients. Drag is not divided by \(\beta\). Critical Mach needs a negative `--cpmin-inc`. Two-dimensional \(1/\beta\) only.
- **AERO - ParachuteDescentRate** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--mass`, `--cd`, `--area`, and `--alt` or `--rho`. Repeat `--reef name=cd,area` for reefed canopies.
- **MASS - StageCgTravel** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Repeat `--stage dry,x_dry,mp,x_full,x_empty`. Pass `--fraction` in \([0, 1]\).
- **STRUCT - FractureCriticalCrack** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--kic` and `--stress`. Optional `--geometry` defaults to 1. Optional `--crack` prints `margin_of_safety`.
- **STRUCT - FatigueGoodman** — Python 3 with `matplotlib`. `--criterion` is `goodman` or `soderberg`. Pass `--sigma-a`, `--sigma-m`, and `--se`. Goodman needs `--sut`. Soderberg needs `--sy`. Optional `--n` is a required factor. The PNG is the intercept line and the load point.
- **PROP - AfterburningTurbofan** — Python 3 with `matplotlib`. Pass `--mach`, `--tit`, `--opr`, `--bpr`, `--fpr`, `--t7`, and a freestream path. Core reheat only. No mixer.
- **PROP - ScramjetIdealCycle** — Python 3 with `matplotlib`. Pass `--mach`, `--combustor-mach` (\(> 1\) and below the flight Mach), `--tmax`, and a freestream path. A subsonic burner is `PROP - IdealRamjet`.
- **PROP - IdealTurboprop** — Python 3 with `matplotlib`. Pass `--mach` (\(> 0\)), `--tit`, `--opr`, `--eta-prop`, and a freestream path. Shaft power and thrust are per 1 kg/s of inlet air.
- **ROCKET - RocketHallThrusterSizing** — Python 3 standard library for the point result. Optional `--out` needs `matplotlib`. Pass `--isp`, `--eta`, and exactly one of `--thrust` or `--power`. Optional `--ion-mass` replaces xenon. Optional `--utilization` is the ionized fraction of the propellant and multiplies the beam current.
- **AERO - NACAFourDigitSection** — Python 3 with `matplotlib`. Angle of attack is radians. Geometry is the four-digit family. Coefficients are interpolated from digitized NACA Report 824 charts (smooth) for 0012, 2412, 2415, and 4412. Optional `--re` selects or interpolates among the tabulated Reynolds numbers (about \(3\times10^6\), \(6\times10^6\), and \(9\times10^6\)). An omitted `--re` uses the curve nearest \(6\times10^6\). An omitted `--alpha` still writes the coefficient and polar figures. Coefficient plots use degrees over the measured range. There is no inviscid \(c_d = 0\).
- **AERO - ThinAirfoilTheory** — Python 3 with `matplotlib`. Angles are radians. Pass `--alpha`, or `--m` and `--p` for a NACA four-digit mean line. Inviscid lift slope is \(2\pi\) per radian. A sealed flap is not included. Measured polars stay on NACAFourDigitSection.
- **AERO - WingAirfoilDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It reads the Report 824 charts at bake time and writes a PNG plus a self-contained HTML file. The page recomputes in the browser. Chart sections use the measured polar. Other four-digit sections use thin-airfoil lift. `--open` opens that file.
- **AERO - CompressibleFlowDesignLab** — Python 3 with `matplotlib`. Run only when the user explicitly asks for the interactive page. It writes a PNG plus a self-contained HTML file. The page recomputes in the browser. Angles are radians on the CLI and degrees on the page. An omitted `--gamma` is \(1.4\). Prandtl–Glauert uses the user-coefficient path only. Duct lines are contours of the stream function. Equal spacing is the constant mass flux \(\rho V\) in a constant-area duct. `--open` opens that file.

Example:

```bash
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --gamma 1.25
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --check
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --thrust 1500 --cf 1.5 --pc 2e6 --cstar 1600
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --check
python "skills/ROCKET - InjectorOrificeFlow/injector_orifice_flow.py" --mdot 0.625 --rho 1000 --cd 0.75 --dp 2e5 --count 20
python "skills/ROCKET - InjectorOrificeFlow/injector_orifice_flow.py" --check
python "skills/ROCKET - FeedSystemPressureBudget/feed_system_pressure_budget.py" --pc 2e6 --dp-injector 2e5 --dp jacket=1e5 --rho 1000 --height 1
python "skills/ROCKET - FeedSystemPressureBudget/feed_system_pressure_budget.py" --check
python "skills/ROCKET - PumpHydraulicPower/pump_hydraulic_power.py" --mdot 0.625 --rho 1000 --dp 2.2e6 --eta 0.7
python "skills/ROCKET - PumpHydraulicPower/pump_hydraulic_power.py" --check
python "skills/ROCKET - FeedTankDesignLab/feed_tank_lab.py" --check
python "skills/ROCKET - FeedTankDesignLab/feed_tank_lab.py" --architecture electric
python "skills/ROCKET - ThroatGasSideHeatFlux/throat_gas_side_heat_flux.py" --pc 2e6 --Tc 3400 --cstar 1600 --throat 0.02523 --curvature 0.02 --tw 800 --mw 22 --gamma 1.22 --recovery 0.95
python "skills/ROCKET - ThroatGasSideHeatFlux/throat_gas_side_heat_flux.py" --check
python "skills/ROCKET - RegenerativeCoolantHeatPickUp/regenerative_coolant_heat_pickup.py" --mdot 0.2 --cp 2000 --t-in 300 --flux 1e7 --area 0.01 --t-max 450
python "skills/ROCKET - RegenerativeCoolantHeatPickUp/regenerative_coolant_heat_pickup.py" --check
python "skills/ROCKET - PropellantLoad/propellant_load.py" --mdot 4 --tb 10 --r 2.3 --pair LOX/RP1
python "skills/ROCKET - PropellantLoad/propellant_load.py" --check
python "skills/ROCKET - TankStructureMass/tank_structure_mass.py" --volume 0.1 --rho 1008 --residuals 0.02 --meop 2e6 --allowable 9e8 --rho-mat 4430
python "skills/ROCKET - TankStructureMass/tank_structure_mass.py" --check
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --stages 1 --stage mp=100,inert=10,isp-vac=300 --payload 5
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --check
python "skills/ROCKET - LossStack/loss_stack.py" --cf 1.5 --cstar 1600 --throat 5e-4 --pc 2e6 --eta combustion=0.98 --eta nozzle=0.97
python "skills/ROCKET - LossStack/loss_stack.py" --check
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --m0 10000 --mp 6000 --isp 300 --tb 80 --gamma 1.4
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --m0 10000 --mp 6000 --isp 300 --tb 80 --kick 0.05 --alt 0
python "skills/ROCKET - BasicTrajectoryLossesFromBodySurface/basic_trajectory_losses_from_body_surface.py" --check
python "skills/ASTRO - LaunchAzimuthInclination/launch_azimuth_inclination.py" --lat 0.49741884 --az 1.5707963
python "skills/ROCKET - FairingAndInterstageMass/fairing_and_interstage_mass.py" --fairing-diameter 1.5 --cylinder-length 3 --nose-length 1 --interstage-diameter 1.5 --interstage-length 0.8 --thickness 0.004 --rho 2700
python "skills/ROCKET - VehicleMassBudget/vehicle_mass_budget.py" --stages 1 --stage mp=100,k=0.1,mH=10 --payload 5
python "skills/ROCKET - LeoDeltaVBudget/leo_delta_v_budget.py" --alt 300000 --v-rot 400 --gravity-loss 1200 --drag-loss 100 --circ 50 --margin 100
python "skills/ROCKET - StagePropellantSplit/stage_propellant_split.py" --stages 2 --stage isp=300,eps=0.1 --stage isp=330,eps=0.12 --dv 9000 --payload 200
python "skills/ROCKET - MultiStageAscent/multi_stage_ascent.py" --stages 2 --stage mp=80000,inert=8000,isp=300,tb=120 --stage mp=15000,inert=2000,isp=330,tb=150 --payload 1500 --gamma 1.05 --cd 0.3 --area 2
python "skills/ROCKET - MaxQAndAeroLoad/max_q_and_aero_load.py" --table "skills/ROCKET - MultiStageAscent/multi_stage_ascent.csv"
python "skills/ROCKET - StageAscentDesignLab/stage_ascent_lab.py" --check
python "skills/ROCKET - StageAscentDesignLab/stage_ascent_lab.py" --stages 3
python "skills/ASTRO - OrbitInsertionFromBurnout/orbit_insertion_from_burnout.py" --r 6774200 --v 7670 --gamma 0
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --throat 0.0005 --lstar 1.2 --pc 2e6 --radius 0.05 --thickness 0.002 --allowable 6.25e7
python "skills/ROCKET - ChamberVolumeAndCaseHoopStress/chamber_case.py" --check
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --a 1e-5 --n 0.5 --ab 0.4 --throat 0.002 --rho 1800 --cstar 1550
python "skills/ROCKET - SolidMotorParameters/solid_motor_parameters.py" --check
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --a 1e-5 --n 0.5 --port 0.02 --length 0.4 --outer 0.05 --throat 0.0005 --rho 1800 --cstar 1550
python "skills/ROCKET - CircularPortGrainHistory/circular_port_grain_history.py" --check
python "skills/ROCKET - SolidMotorGrainLab/solid_motor_grain_lab.py" --check
python "skills/ASTRO - OrbitDesignLab/orbit_design_lab.py" --check
python "skills/ASTRO - OrbitDesignLab/orbit_design_lab.py" --r1 6774200 --r2 42164000
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --r1 6774200 --r2 7374200
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --alt 400000 --ecc 0.2 --html
python "skills/ASTRO - HohmannTransfer/hohmann_transfer.py" --check
python "skills/ASTRO - LambertTransfer/lambert_transfer.py" --r1x 7000000 --r1y 0 --r1z 0 --r2x 0 --r2y 7000000 --r2z 0 --tof 1457.41
python "skills/ASTRO - LambertTransfer/lambert_transfer.py" --check
python "skills/ASTRO - SolarSystemBody/solar_system_body.py" --body mars
python "skills/ASTRO - SolarSystemBody/solar_system_body.py" --check
python "skills/ASTRO - HeliocentricHohmann/heliocentric_hohmann.py" --from earth --to mars
python "skills/ASTRO - HeliocentricHohmann/heliocentric_hohmann.py" --check
python "skills/ASTRO - LeoToLowOrbit/leo_to_low_orbit.py" --to mars --h-leo 400000 --h-arrive 300000
python "skills/ASTRO - LeoToLowOrbit/leo_to_low_orbit.py" --check
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --rp 6774200 --vinf 3200 --html
python "skills/ASTRO - HyperbolicExcess/hyperbolic_excess.py" --check
python "skills/ASTRO - GravityAssistFlyby/gravity_assist_flyby.py" --mu 3.986e14 --rp 6771000 --vinf 3000 --ux 1 --uy 0 --vp-x 29780 --vp-y 0 --turn left --radius 6374200 --html
python "skills/ASTRO - GravityAssistFlyby/gravity_assist_flyby.py" --check
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
python "skills/ROCKET - KickStageNozzle/kick_stage_nozzle.py" --pc 2e6 --gamma 1.25 --pe 5000 --throat 0.001 --thickness 0.002 --rho-mat 2700
python "skills/ROCKET - KickStageNozzle/kick_stage_nozzle.py" --pc 2e6 --gamma 1.25 --epsilon-min 10 --epsilon-max 80 --epsilon 40 --throat 0.001
python "skills/ROCKET - KickStageNozzle/kick_stage_nozzle.py" --check
python "skills/ROCKET - NozzleChamberDesignLab/nozzle_chamber_lab.py" --check
python "skills/ROCKET - NozzleChamberDesignLab/nozzle_chamber_lab.py" --pa 0
python "skills/ROCKET - KickStageFeasibility/kick_stage_feasibility.py" --thrust 1000 --isp 300 --m0 500 --mp 50 --tb-max 200 --restarts-max 5
python "skills/ROCKET - KickStageFeasibility/kick_stage_feasibility.py" --check
python "skills/ASTRO - MultiBurnLeoRaise/multi_burn_leo_raise.py" --a 6674200 --e 0 --i 0.5 --raan 0.2 --aop 0 --nu 0 --alt-target 800000 --thrust 20000 --isp 320 --m0 2000 --mp 600 --burns 2
python "skills/ASTRO - MultiBurnLeoRaise/multi_burn_leo_raise.py" --check
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --moment 1200 --section-modulus 0.003 --allowable 500000
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --moment 1200 --inertia 9e-5 --fiber 0.03 --out beam_bending_stress.png
python "skills/STRUCT - BeamBendingStress/beam_bending_stress.py" --check
python "skills/STRUCT - CombinedStressMohr/combined_stress_mohr.py" --sigma 100e6 --tau 40e6
python "skills/STRUCT - CombinedStressMohr/combined_stress_mohr.py" --check
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --E 2e11 --inertia 1e-6 --length 2 --area 1e-3 --yield 6e8
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --E 2e11 --inertia 1e-6 --length 2 --ends fixed-fixed --out euler_column_buckling.png
python "skills/STRUCT - EulerColumnBuckling/euler_column_buckling.py" --check
python "skills/GNC - SecondOrderResponse/second_order_response.py" --wn 2 --zeta 0.5 --out second_order_response.png
python "skills/GNC - SecondOrderResponse/second_order_response.py" --mass 1 --stiffness 4 --damping 2 --settling-percent 2
python "skills/GNC - SecondOrderResponse/second_order_response.py" --check
python "skills/GNC - ClassicalControlMargins/classical_control_margins.py" --num 1 --den 1 1 0
python "skills/GNC - ClassicalControlMargins/classical_control_margins.py" --check
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --n-prime 3 --vc 1000 --los-rate 0.01
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --n-prime 3 --range 10000 --los-angle 0 --vm 300 --hm 0 --vt 200 --ht 3.141592653589793 --out proportional_navigation.png
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --check
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --E 7e10 --inertia 1e-8 --length 1 --mu 0.5
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --E 7e10 --inertia 1e-8 --length 1 --mass 0.5 --out cantilever_natural_frequency.png
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --check
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --part 2,0,0,0 --part 2,2,0,0 --about-origin
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --part 1,0,1,0,0,0,2 --about-origin
python "skills/MASS - CenterOfMassAndInertia/center_of_mass_and_inertia.py" --check
python "skills/MASS - StageCgTravel/stage_cg_travel.py" --check
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --alt 60000 --emissivity 0.8
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --alt 60000 --mach-axis
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --speed 3535 --nose 1 --rho 3.1459e-4 --wall-temp 300 --temperature 216.65
python "skills/THERM - SonicStagnationHeatFlux/sonic_stagnation_heat_flux.py" --check
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --speed 7000 --gamma 0.5235987755982988 --beta 100
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --speed 7000 --gamma 0.5235987755982988 --mass 500 --cd 0.5 --area 2 --out ballistic_entry_peak_load.png
python "skills/THERM - BallisticEntryPeakLoad/ballistic_entry_peak_load.py" --check
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --mass 2 --c 500 --area 5 --h 10 --ti 400 --t-inf 300 --time 20 --k 200 --char-length 0.01 --out lumped_capacitance_transient.png
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --mass 2 --c 500 --area 5 --h 10 --ti 400 --t-inf 300 --target-temp 336.787944117144
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --check
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
python "skills/ATMOS - DensityAbove86km/density_above_86km.py" --alt 200000
python "skills/ATMOS - DensityAbove86km/density_above_86km.py" --check
python "skills/POWER - DutyCycleLoad/duty_cycle_load.py" --power 10 --duty 1 --power 20 --duty 0.5 --eclipse 1800
python "skills/POWER - DutyCycleLoad/duty_cycle_load.py" --check
python "skills/THERM - SpacecraftRadiativeBalance/spacecraft_radiative_balance.py" --area-sun 0.5 --alpha 0.9 --epsilon 0.8 --area-rad 0.4
python "skills/THERM - SpacecraftRadiativeBalance/spacecraft_radiative_balance.py" --check
python "skills/ADCS - EnvironmentalTorques/environmental_torques.py" --i-z 12 --i-y 10 --theta 0.7853981633974483 --alt 400000 --dipole 0.2 --b-field 3e-5
python "skills/ADCS - EnvironmentalTorques/environmental_torques.py" --check
python "skills/ADCS - SlewMomentum/slew_momentum.py" --inertia 2 --angle 1.5707963267948966 --time 60
python "skills/ADCS - SlewMomentum/slew_momentum.py" --torque 1e-4 --duration 5400
python "skills/ADCS - SlewMomentum/slew_momentum.py" --check
python "skills/ADCS - AttitudeKinematics/attitude_kinematics.py" --mode euler_to_dcm --yaw 1.5707963267948966 --pitch 0 --roll 0
python "skills/ADCS - AttitudeKinematics/attitude_kinematics.py" --check
python "skills/ASTRO - AerodynamicDragDeltaV/aerodynamic_drag_delta_v.py" --alt 400000 --mass 50 --cd 2.2 --area 0.8 --rho 1e-11
python "skills/ASTRO - AerodynamicDragDeltaV/aerodynamic_drag_delta_v.py" --check
python "skills/ASTRO - VacuumPropellantMass/vacuum_propellant_mass.py" --dry 80 --isp 220 --name transfer --dv 120 --name drag --dv 30
python "skills/ASTRO - VacuumPropellantMass/vacuum_propellant_mass.py" --check
python "skills/COMMS - PassDataVolume/pass_data_volume.py" --bits 2e9 --duration 480 --overhead 1.2
python "skills/COMMS - PassDataVolume/pass_data_volume.py" --check
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
python "skills/AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py" --fanno --mach 2
python "skills/AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py" --check
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
python "skills/PROP - IdealRamjet/ideal_ramjet.py" --mach 3 --alt 11000 --tmax 2200
python "skills/PROP - IdealRamjet/ideal_ramjet.py" --check
python "skills/PROP - InletRecovery/inlet_recovery.py" --mach 2 --alt 11000 --pitot --pi-ds 0.98
python "skills/PROP - InletRecovery/inlet_recovery.py" --check
python "skills/PROP - NonidealTurbojet/nonideal_turbojet.py" --mach 0.8 --alt 11000 --tit 1600 --opr 20 --eta-c 0.88 --pi-d 0.98
python "skills/PROP - NonidealTurbojet/nonideal_turbojet.py" --check
python "skills/PROP - AfterburningTurbojet/afterburning_turbojet.py" --mach 0.8 --alt 11000 --tit 1600 --opr 15 --t7 2000
python "skills/PROP - AfterburningTurbojet/afterburning_turbojet.py" --check
python "skills/PROP - SeparateStreamTurbofan/separate_stream_turbofan.py" --mach 0.8 --alt 11000 --tit 1600 --opr 30 --bpr 5 --fpr 1.5
python "skills/PROP - SeparateStreamTurbofan/separate_stream_turbofan.py" --check
python "skills/PROP - AfterburningTurbofan/afterburning_turbofan.py" --check
python "skills/PROP - ScramjetIdealCycle/scramjet_ideal_cycle.py" --check
python "skills/PROP - IdealTurboprop/ideal_turboprop.py" --check
python "skills/PROP - EngineAirflowSizing/engine_airflow_sizing.py" --thrust 20000 --fs 400 --rho 0.3 --speed 250
python "skills/PROP - EngineAirflowSizing/engine_airflow_sizing.py" --check
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --a0 6.28318530718 --alpha-l0 -0.03490658504 --clmax 1.4 --ar 8 --e 0.8
python "skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py" --check
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --alt 11000 --mach 0.8
python "skills/AERO - EquivalentAirspeed/equivalent_airspeed.py" --check
python "skills/AERO - DensityAndPressureAltitude/density_and_pressure_altitude.py" --pressure 101325 --oat 288.15 --rh 0.5 --eas 50
python "skills/AERO - DensityAndPressureAltitude/density_and_pressure_altitude.py" --check
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --a 5 --at 4 --downwash 0.4 --q-ratio 0.9 --tail-area 2 --tail-length 5 --wing-area 10 --mac 1 --cg 0.1
python "skills/AERO - LongitudinalStaticMargin/longitudinal_static_margin.py" --check
python "skills/AERO - LongitudinalTrim/longitudinal_trim.py" --a 5 --cm0 0.05 --cm-de -0.8 --q 500 --S 10 --W 1000 --kn 0.1
python "skills/AERO - LongitudinalTrim/longitudinal_trim.py" --check
python "skills/AERO - RayleighPitotMach/rayleigh_pitot_mach.py" --pitot 120195 --static 101325 --gamma 1.4
python "skills/AERO - RayleighPitotMach/rayleigh_pitot_mach.py" --check
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --mach 0.6 --cl-inc 0.5 --cpmin-inc -0.4
python "skills/AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py" --check
python "skills/AERO - ParachuteDescentRate/parachute_descent_rate.py" --check
python "skills/AERO - NACAFourDigitSection/naca_four_digit_section.py" --naca 2412 --chord 1 --alpha 0.0872664625997 --re 5.7e6
python "skills/AERO - NACAFourDigitSection/naca_four_digit_section.py" --check
python "skills/AERO - ThinAirfoilTheory/thin_airfoil_theory.py" --m 0.02 --p 0.4 --alpha 0.0872664625997
python "skills/AERO - ThinAirfoilTheory/thin_airfoil_theory.py" --check
python "skills/AERO - FlatPlateBoundaryLayer/flat_plate_boundary_layer.py" --law laminar --re 1e5
python "skills/AERO - FlatPlateBoundaryLayer/flat_plate_boundary_layer.py" --check
python "skills/AERO - WindTunnelSimilarity/wind_tunnel_similarity.py" --re-m 1e6 --re-f 2e6 --mach-m 0.2 --mach-f 0.2
python "skills/AERO - WindTunnelSimilarity/wind_tunnel_similarity.py" --check
python "skills/AERO - WingAirfoilDesignLab/wing_airfoil_lab.py" --check
python "skills/AERO - WingAirfoilDesignLab/wing_airfoil_lab.py" --naca 0015
python "skills/AERO - CompressibleFlowDesignLab/compressible_flow_lab.py" --check
python "skills/AERO - CompressibleFlowDesignLab/compressible_flow_lab.py" --mode wedge --mach 2 --delta 0.174532925
python "skills/STRUCT - ThinWallPressureVessel/thin_wall_pressure_vessel.py" --p 1e6 --radius 0.5 --thickness 0.002 --shape cylinder --allowable 2.5e8
python "skills/STRUCT - ThinWallPressureVessel/thin_wall_pressure_vessel.py" --check
python "skills/VIBR - BaseExcitationTransmissibility/base_excitation_transmissibility.py" --fn 20 --zeta 0.05 --f 40
python "skills/VIBR - BaseExcitationTransmissibility/base_excitation_transmissibility.py" --check
python "skills/ADCS - ReactionWheelSizing/reaction_wheel_sizing.py" --H 0.54 --tau 0.01 --omega-max 600 --H-max 1 --tau-max 0.02
python "skills/ADCS - ReactionWheelSizing/reaction_wheel_sizing.py" --check
python "skills/ASTRO - RendezvousPhasing/rendezvous_phasing.py" --alt 400000 --phase 0.2 --lead target --revs 2
python "skills/ASTRO - RendezvousPhasing/rendezvous_phasing.py" --check
python "skills/ASTRO - RelativeOrbitClohessyWiltshire/relative_orbit_clohessy_wiltshire.py" --a 6778000 --x 0 --z 100 --xdot -0.2 --zdot 0 --time 600
python "skills/ASTRO - RelativeOrbitClohessyWiltshire/relative_orbit_clohessy_wiltshire.py" --check
python "skills/ROCKET - ElectricPropulsionDeltaV/electric_propulsion_delta_v.py" --dry 100 --thrust 0.05 --dv 2000 --isp 1600 --eta 0.5 --duty 0.8
python "skills/ROCKET - ElectricPropulsionDeltaV/electric_propulsion_delta_v.py" --check
python "skills/ROCKET - RocketHallThrusterSizing/rocket_hall_thruster_sizing.py" --check
python "skills/COMMS - RainAttenuation/rain_attenuation.py" --rate 50 --freq 20e9 --elevation 0.5235987755982988 --path 4000
python "skills/COMMS - RainAttenuation/rain_attenuation.py" --check
python "skills/AERO - PhugoidAndShortPeriod/phugoid_and_short_period.py" --speed 100 --rho 1.2 --wing-loading 3000 --cla 5 --static-margin 0.05 --mac 2 --ky 1
python "skills/AERO - PhugoidAndShortPeriod/phugoid_and_short_period.py" --check
python "skills/ROCKET - PressurantBlowdown/pressurant_blowdown.py" --p0 2e6 --v0 0.1 --v-expelled 0.1 --p-min 5e5
python "skills/ROCKET - PressurantBlowdown/pressurant_blowdown.py" --check
python "skills/MASS - PropellantSloshFrequency/propellant_slosh_frequency.py" --radius 1 --height 0.5
python "skills/MASS - PropellantSloshFrequency/propellant_slosh_frequency.py" --check
python "skills/STRUCT - PanelBuckling/panel_buckling.py" --E 70e9 --nu 0.3 --width 0.5 --thickness 0.002 --length 1.5
python "skills/STRUCT - PanelBuckling/panel_buckling.py" --check
python "skills/STRUCT - FractureCriticalCrack/fracture_critical_crack.py" --check
python "skills/STRUCT - FatigueGoodman/fatigue_goodman.py" --criterion goodman --sigma-a 100e6 --sigma-m 80e6 --se 200e6 --sut 500e6
python "skills/STRUCT - FatigueGoodman/fatigue_goodman.py" --check
python "skills/VIBR - RandomVibeRms/random_vibe_rms.py" --fn 100 --psd 0.01 --q 10
python "skills/VIBR - RandomVibeRms/random_vibe_rms.py" --check
python "skills/ADCS - MagneticTorquerSizing/magnetic_torquer_sizing.py" --torque 0.01 --b-field 5e-5 --turns 100 --area 0.02
python "skills/ADCS - MagneticTorquerSizing/magnetic_torquer_sizing.py" --check
python "skills/COMMS - DopplerShiftBudget/doppler_shift_budget.py" --freq 2e9 --alt 600000 --elev-min 0.2
python "skills/COMMS - DopplerShiftBudget/doppler_shift_budget.py" --check
python "skills/AERO - DutchRollEstimate/dutch_roll_estimate.py" --speed 150 --rho 1 --span 20 --area 50 --ix 1e5 --iz 2e5 --mass 5000 --cn-beta 0.1 --cl-beta -0.1 --cy-beta -0.5 --cn-r -0.2 --cl-p -0.4
python "skills/AERO - DutchRollEstimate/dutch_roll_estimate.py" --check
python "skills/AERO - LateralDirectionalStaticStability/lateral_directional_static_stability.py" --span 10 --area 20 --cl-alpha 4 --sv 2 --lv 5 --av 2 --gamma 0.1
python "skills/AERO - LateralDirectionalStaticStability/lateral_directional_static_stability.py" --check
python "skills/ASTRO - GeostationaryStationKeeping/geostationary_station_keeping.py" --di-year 0.02 --e-year 0.0001 --ns-burns 2
python "skills/ASTRO - GeostationaryStationKeeping/geostationary_station_keeping.py" --check
python "skills/ASTRO - CoverageAndRevisit/coverage_and_revisit.py" --alt 600000 --elev-min 0.2
python "skills/ASTRO - CoverageAndRevisit/coverage_and_revisit.py" --check
python "skills/ASTRO - ConjunctionMissDistance/conjunction_miss_distance.py" --r1x 6774200 --r1y 0 --r1z 0 --v1x 0 --v1y 7670 --v1z 0 --r2x 6775200 --r2y 0 --r2z 0 --v2x 0 --v2y 7669 --v2z 0 --window 200
python "skills/ASTRO - ConjunctionMissDistance/conjunction_miss_distance.py" --check
python "skills/THERM - EquilibriumGlideEntry/equilibrium_glide_entry.py" --ve 7000 --lod 1 --beta 100
python "skills/THERM - EquilibriumGlideEntry/equilibrium_glide_entry.py" --check
python "skills/THERM - LiftingEntryTrajectory/lifting_entry_trajectory.py" --speed 7500 --gamma 0.02 --altitude 80000 --lod 1 --beta 200 --bank-deg 0
python "skills/THERM - LiftingEntryTrajectory/lifting_entry_trajectory.py" --check
```

## Units

SI is the working system (Pa, m², N). Skills convert other units before calling programs and state the units used in the reply.

## License

Proprietary. See [LICENSE](LICENSE). All rights reserved; no open-source license is granted.
