/* Swath and equatorial revisit. Keep in step with ASTRO - CoverageAndRevisit. */
var Lab = Lab || {};

Lab.coverage = function (orbitRadius, elevation, planetRadius) {
  var r0 = planetRadius || Lab.R0_EARTH;
  if (elevation < 0.0 || elevation >= Math.PI / 2.0) throw new Error("minimum elevation must be in [0, pi/2)");
  var argument = (r0 / orbitRadius) * Math.cos(elevation);
  if (argument > 1.0 || argument < 0.0) throw new Error("elevation is outside the geometric mask");
  var rho = Math.asin(argument);
  var lam = Math.PI / 2.0 - elevation - rho;
  if (lam <= 0.0) throw new Error("the elevation mask leaves no swath");
  var mu = Lab.muOf(r0);
  var p = Lab.orbitalPeriod(mu, orbitRadius);
  var gap = Lab.OMEGA_E * p;
  var passes = Math.ceil(gap / (2.0 * lam) - 1e-12);
  if (passes < 1) passes = 1;
  return {
    lambda: lam,
    swath: 2.0 * r0 * lam,
    footprint: r0 * lam,
    period: p,
    nodal_gap: gap,
    revisit_periods: passes,
    revisit_s: passes * p
  };
};
