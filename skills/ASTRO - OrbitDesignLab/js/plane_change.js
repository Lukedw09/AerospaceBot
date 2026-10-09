/* Pure inclination change. Keep in step with ASTRO - PlaneChangeImpulse. */
var Lab = Lab || {};

Lab.planeChangeImpulse = function (speed, di) {
  return 2.0 * speed * Math.sin(di / 2.0);
};

Lab.planeChange = function (mu, radius, di) {
  if (radius <= 0.0) throw new Error("radius must be > 0");
  var speed = Lab.circularSpeed(mu, radius);
  var dv = Lab.planeChangeImpulse(speed, di);
  return {
    radius: radius,
    speed: speed,
    di: di,
    dv_an: dv,
    dv_dn: dv,
    dv: dv
  };
};
