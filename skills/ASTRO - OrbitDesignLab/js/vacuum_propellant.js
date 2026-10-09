/* Vacuum rocket equation. Keep in step with ASTRO - VacuumPropellantMass. */
var Lab = Lab || {};

Lab.vacuumPropellant = function (dry, growth, deltaV, isp, ve) {
  var exhaust;
  if (ve !== null && ve !== undefined && ve !== "") exhaust = Number(ve);
  else exhaust = Number(isp) * Lab.G0;
  var grow = growth || 0.0;
  var finalMass = dry * (1.0 + grow);
  var wet = finalMass * Math.exp(deltaV / exhaust);
  return {
    ve: exhaust,
    m_final: finalMass,
    m_propellant: wet - finalMass,
    m_wet: wet
  };
};
