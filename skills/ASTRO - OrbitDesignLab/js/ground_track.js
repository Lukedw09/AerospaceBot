/* Subsatellite point. Keep in step with ASTRO - GroundTrackEarth. */
var Lab = Lab || {};

Lab.solveKepler = function (meanAnomaly, eccentricity) {
  var mean = Lab.wrapPi(meanAnomaly);
  if (eccentricity === 0.0) return mean;
  var eccentric = mean + eccentricity * Math.sin(mean);
  var i;
  for (i = 0; i < 50; i += 1) {
    var residual = eccentric - eccentricity * Math.sin(eccentric) - mean;
    var slope = 1.0 - eccentricity * Math.cos(eccentric);
    if (Math.abs(residual) <= 1e-14) return eccentric;
    var curve = eccentricity * Math.sin(eccentric);
    var denom = slope - residual * curve / (2.0 * slope);
    var step = residual / denom;
    eccentric -= step;
    if (Math.abs(step) <= 1e-14) return eccentric;
  }
  throw new Error("Kepler equation did not converge");
};

Lab.nuFromEccentric = function (eccentricity, eccentricAnomaly) {
  var cosE = Math.cos(eccentricAnomaly);
  var sinE = Math.sin(eccentricAnomaly);
  var cosNu = (cosE - eccentricity) / (1.0 - eccentricity * cosE);
  var sinNu = Math.sqrt(1.0 - eccentricity * eccentricity) * sinE / (1.0 - eccentricity * cosE);
  return Math.atan2(sinNu, cosNu);
};

Lab.inertialAtTime = function (mu, a, e, inc, omega0, arg0, mean0, time, j2, re) {
  var n = Lab.meanMotion(mu, a);
  var mean = mean0 + n * time;
  var eccentric = Lab.solveKepler(mean, e);
  var nu = Lab.nuFromEccentric(e, eccentric);
  var node = Lab.wrapTwoPi(omega0 + Lab.j2Nodal(n, j2, re, inc, a, e) * time);
  var peri = Lab.wrapTwoPi(arg0 + Lab.j2Apsidal(n, j2, re, inc, a, e) * time);
  var p = a * (1.0 - e * e);
  var radius = p / (1.0 + e * Math.cos(nu));
  var argument = peri + nu;
  var x = radius * (Math.cos(node) * Math.cos(argument) - Math.sin(node) * Math.cos(inc) * Math.sin(argument));
  var y = radius * (Math.sin(node) * Math.cos(argument) + Math.cos(node) * Math.cos(inc) * Math.sin(argument));
  var z = radius * Math.sin(inc) * Math.sin(argument);
  return { x: x, y: y, z: z, radius: radius, n: n };
};

Lab.subsatellite = function (mu, a, e, inc, omega0, arg0, mean0, time, theta0, j2, re, flattening, ae) {
  var state = Lab.inertialAtTime(mu, a, e, inc, omega0, arg0, mean0, time, j2, re);
  var theta = Lab.wrapTwoPi(theta0 + Lab.OMEGA_E * time);
  var xe = state.x * Math.cos(theta) + state.y * Math.sin(theta);
  var ye = -state.x * Math.sin(theta) + state.y * Math.cos(theta);
  var ze = state.z;
  var rho = Math.hypot(xe, ye);
  var sine = ze / state.radius;
  if (sine > 1.0) sine = 1.0;
  if (sine < -1.0) sine = -1.0;
  var cosine = rho / state.radius;
  var phic = Math.atan2(sine, cosine);
  var lon = rho <= 1e-10 * state.radius ? 0.0 : Math.atan2(ye / rho, xe / rho);
  var phig = phic
    + flattening * (ae / state.radius) * Math.sin(2.0 * phic)
    + flattening * flattening * ((ae / state.radius) * (ae / state.radius) - ae / (4.0 * state.radius)) * Math.sin(4.0 * phic);
  return {
    lat: Math.max(-Math.PI / 2.0, Math.min(Math.PI / 2.0, phig)),
    lon: Lab.wrapPi(lon),
    lat_geocentric: phic
  };
};

Lab.groundTrack = function (mu, a, e, inc, omega0, arg0, mean0, span, count, theta0, j2, re) {
  var n = count || 181;
  var pts = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var t = span * (n === 1 ? 0 : i / (n - 1));
    var sub = Lab.subsatellite(mu, a, e, inc, omega0, arg0, mean0, t, theta0 || 0.0, j2, re, Lab.F_WGS84, Lab.AE_WGS84);
    pts.push({ t: t, lat: sub.lat, lon: sub.lon });
  }
  return pts;
};
