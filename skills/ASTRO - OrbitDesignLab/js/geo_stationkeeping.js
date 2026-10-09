/* GEO station-keeping. Keep in step with ASTRO - GeostationaryStationKeeping. */
var Lab = Lab || {};

Lab.geostationaryRadius = function () {
  var mu = Lab.G0 * Lab.R0_EARTH * Lab.R0_EARTH;
  return Math.pow(mu / (Lab.OMEGA_E * Lab.OMEGA_E), 1.0 / 3.0);
};

Lab.geoStationKeeping = function (diYear, eYear, burns, years) {
  if (diYear < 0.0 || eYear < 0.0) throw new Error("yearly drift must be >= 0");
  if (burns < 1) throw new Error("north-south burn count must be >= 1");
  if (!(years > 0.0)) throw new Error("years must be > 0");
  var radius = Lab.geostationaryRadius();
  var speed = Math.sqrt(Lab.G0 * Lab.R0_EARTH * Lab.R0_EARTH / radius);
  var piece = diYear / burns;
  var dvNsYear = burns * Lab.planeChangeImpulse(speed, piece);
  var dvEwYear = 2.0 * speed * eYear;
  return {
    a: radius,
    v: speed,
    dv_ns_year: dvNsYear,
    dv_ew_year: dvEwYear,
    dv_ns: dvNsYear * years,
    dv_ew: dvEwYear * years,
    dv_total: (dvNsYear + dvEwYear) * years
  };
};
