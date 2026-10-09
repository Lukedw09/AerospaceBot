/* Shared two-body helpers. Keep in step with ASTRO - HohmannTransfer,
   ASTRO - OrbitalParameters, and ASTRO - GroundTrackEarth. */
var Lab = Lab || {};

Lab.G0 = 9.80665;
Lab.R0_EARTH = 6.3742e6;
Lab.OMEGA_E = 7.292115e-5;
Lab.AE_WGS84 = 6378137.0;
Lab.F_WGS84 = 1.0 / 298.257223563;
Lab.J2_GSFC = 1.08228e-3;
Lab.YEAR_DAYS = 365.2422;
Lab.DAY_S = 86400.0;

Lab.muOf = function (r0) {
  return Lab.G0 * r0 * r0;
};

Lab.circularSpeed = function (mu, radius) {
  return Math.sqrt(mu / radius);
};

Lab.escapeSpeed = function (mu, radius) {
  return Math.sqrt(2.0 * mu / radius);
};

Lab.specificEnergy = function (mu, semiMajor) {
  return -mu / (2.0 * semiMajor);
};

Lab.visViva = function (mu, radius, semiMajor) {
  var argument = mu * (2.0 / radius - 1.0 / semiMajor);
  var scale = mu / radius;
  if (argument < 0.0) {
    if (argument > -1e-9 * scale) argument = 0.0;
    else throw new Error("transfer speed is not real at that radius");
  }
  return Math.sqrt(argument);
};

Lab.orbitalPeriod = function (mu, semiMajor) {
  return 2.0 * Math.PI * Math.sqrt(Math.pow(semiMajor, 3) / mu);
};

Lab.meanMotion = function (mu, semiMajor) {
  return Math.sqrt(mu / Math.pow(semiMajor, 3));
};

Lab.burnSense = function (after, before) {
  var span = Math.max(Math.abs(before), Math.abs(after), 1.0);
  if (Math.abs(after - before) <= Math.max(1e-9 * Math.max(Math.abs(after), Math.abs(before)), 1e-6 * span)) {
    return "none";
  }
  return after > before ? "prograde" : "retrograde";
};

Lab.sameRadius = function (left, right) {
  var scale = Math.max(Math.abs(left), Math.abs(right), 1.0);
  return Math.abs(left - right) <= 1e-12 * scale;
};

Lab.wrapTwoPi = function (angle) {
  var twopi = 2.0 * Math.PI;
  var wrapped = angle % twopi;
  if (wrapped < 0.0) wrapped += twopi;
  if (wrapped >= twopi || wrapped < 1e-15) return 0.0;
  return wrapped;
};

Lab.wrapPi = function (angle) {
  var wrapped = Lab.wrapTwoPi(angle);
  if (wrapped > Math.PI) wrapped -= 2.0 * Math.PI;
  return wrapped;
};

Lab.conicRadius = function (semiMajor, eccentricity, nu) {
  return semiMajor * (1.0 - eccentricity * eccentricity) / (1.0 + eccentricity * Math.cos(nu));
};

Lab.ellipseSamples = function (periapsis, apoapsis, nu0, nu1, count) {
  var a = 0.5 * (periapsis + apoapsis);
  var e = Lab.sameRadius(periapsis, apoapsis) ? 0.0 : (apoapsis - periapsis) / (apoapsis + periapsis);
  var n = count || 97;
  var pts = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var nu = nu0 + (nu1 - nu0) * (n === 1 ? 0 : i / (n - 1));
    var r = Lab.conicRadius(a, e, nu);
    pts.push([r * Math.cos(nu), r * Math.sin(nu), 0.0]);
  }
  return pts;
};

Lab.circleSamples = function (radius, count) {
  var n = count || 97;
  var pts = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var nu = 2.0 * Math.PI * i / (n - 1);
    pts.push([radius * Math.cos(nu), radius * Math.sin(nu), 0.0]);
  }
  return pts;
};

Lab.inclinedCircle = function (radius, inc, count) {
  return Lab.conicSamples(radius, radius, inc, count);
};

Lab.conicSamples = function (periapsis, apoapsis, inc, count, nu0, nu1) {
  var a = 0.5 * (periapsis + apoapsis);
  var e = Lab.sameRadius(periapsis, apoapsis) ? 0.0 : (apoapsis - periapsis) / (apoapsis + periapsis);
  var start = nu0 === undefined ? 0.0 : nu0;
  var end = nu1 === undefined ? 2.0 * Math.PI : nu1;
  var n = count || 121;
  var pts = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var nu = start + (end - start) * (n === 1 ? 0 : i / (n - 1));
    var r = Lab.conicRadius(a, e, nu);
    var c = Math.cos(nu);
    var s = Math.sin(nu);
    pts.push([r * c, r * s * Math.cos(inc), r * s * Math.sin(inc)]);
  }
  return pts;
};
