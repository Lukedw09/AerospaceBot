/* Launch azimuth and inclination. Keep in step with ASTRO - LaunchAzimuthInclination. */
var Lab = Lab || {};

Lab.launchInclination = function (lat, az) {
  var cosine = Math.cos(lat) * Math.sin(az);
  cosine = Math.max(-1.0, Math.min(1.0, cosine));
  return Math.acos(cosine);
};

Lab.launchAzimuths = function (lat, inc) {
  var sine = Math.cos(inc) / Math.cos(lat);
  if (sine > 1.0 + 1e-12 || sine < -1.0 - 1e-12) throw new Error("inclination is below the site latitude");
  sine = Math.max(-1.0, Math.min(1.0, sine));
  var primary = Lab.wrapTwoPi(Math.asin(sine));
  var alternate = Lab.wrapTwoPi(Math.PI - Math.asin(sine));
  return { primary: primary, alternate: alternate };
};

Lab.launchAzimuth = function (lat, az, radius, omega) {
  var r = radius || Lab.AE_WGS84;
  var w = omega || Lab.OMEGA_E;
  var inc = Lab.launchInclination(lat, az);
  return {
    inc: inc,
    v_rot: w * r * Math.cos(lat),
    v_assist: w * r * Math.cos(lat) * Math.sin(az)
  };
};
