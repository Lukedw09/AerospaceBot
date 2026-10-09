/* Drag delta-v per revolution. Keep in step with ASTRO - AerodynamicDragDeltaV.
   Density is the baked table unless rho is supplied. */
var Lab = Lab || {};

Lab.densityAt = function (alt, table, rhoOverride) {
  if (rhoOverride !== null && rhoOverride !== undefined && rhoOverride !== "") {
    return Number(rhoOverride);
  }
  if (!table || !table.length) throw new Error("density table is missing");
  if (alt <= table[0][0]) return table[0][1];
  var last = table[table.length - 1];
  if (alt >= last[0]) return last[1];
  var i;
  for (i = 1; i < table.length; i += 1) {
    if (alt <= table[i][0]) {
      var a0 = table[i - 1][0];
      var a1 = table[i][0];
      var span = a1 - a0;
      var w = span === 0.0 ? 0.0 : (alt - a0) / span;
      var rho0 = table[i - 1][1];
      var rho1 = table[i][1];
      if (!(rho0 > 0.0) || !(rho1 > 0.0)) return rho0 + w * (rho1 - rho0);
      return Math.exp(Math.log(rho0) + w * (Math.log(rho1) - Math.log(rho0)));
    }
  }
  return last[1];
};

Lab.dragDeltaV = function (alt, mass, cd, area, rho) {
  if (mass <= 0.0 || cd <= 0.0 || area <= 0.0 || alt < 0.0) {
    throw new Error("mass, Cd, and area must be positive and altitude >= 0");
  }
  var radius = Lab.R0_EARTH + alt;
  var mu = Lab.muOf(Lab.R0_EARTH);
  var speed = Lab.R0_EARTH * Math.sqrt(Lab.G0 / radius);
  var period = Lab.orbitalPeriod(mu, radius);
  var force = cd * 0.5 * rho * speed * speed * area;
  return {
    rho: rho,
    speed: speed,
    period: period,
    force: force,
    dv_per_rev: force / mass * period
  };
};
