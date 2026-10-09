/* Planar Clohessy–Wiltshire. Keep in step with ASTRO - RelativeOrbitClohessyWiltshire. */
var Lab = Lab || {};

Lab.cwRadial = function (motion, time, z0, zd0, xd0) {
  var s = Math.sin(motion * time);
  var c = Math.cos(motion * time);
  return (4.0 - 3.0 * c) * z0 + (s / motion) * zd0 + (2.0 / motion) * (1.0 - c) * xd0;
};

Lab.cwAlong = function (motion, time, z0, x0, zd0, xd0) {
  var s = Math.sin(motion * time);
  var c = Math.cos(motion * time);
  return 6.0 * (s - motion * time) * z0 + x0 + (2.0 / motion) * (c - 1.0) * zd0
    + (4.0 * s - 3.0 * motion * time) / motion * xd0;
};

Lab.cwRates = function (motion, time, z0, zd0, xd0) {
  var s = Math.sin(motion * time);
  var c = Math.cos(motion * time);
  var xd = 6.0 * motion * (c - 1.0) * z0 - 2.0 * s * zd0 + (4.0 * c - 3.0) * xd0;
  var zd = 3.0 * motion * s * z0 + c * zd0 + 2.0 * s * xd0;
  return { xd: xd, zd: zd };
};

Lab.clohessyWiltshire = function (x0, z0, xd0, zd0, time, radius, mu) {
  if (time < 0.0) throw new Error("time must be >= 0");
  if (!(radius > 0.0) || !(mu > 0.0)) throw new Error("chief radius and mu must be > 0");
  var motion = Lab.meanMotion(mu, radius);
  var x = Lab.cwAlong(motion, time, z0, x0, zd0, xd0);
  var z = Lab.cwRadial(motion, time, z0, zd0, xd0);
  var rates = Lab.cwRates(motion, time, z0, zd0, xd0);
  var holdX = -2.0 * motion * z0 - xd0;
  var path = [];
  var steps = 80;
  var i;
  for (i = 0; i <= steps; i += 1) {
    var t = time * i / steps;
    path.push([
      Lab.cwAlong(motion, t, z0, x0, zd0, xd0),
      Lab.cwRadial(motion, t, z0, zd0, xd0)
    ]);
  }
  return {
    n: motion,
    period: 2.0 * Math.PI / motion,
    x: x,
    z: z,
    xd: rates.xd,
    zd: rates.zd,
    dv_null_x: -xd0,
    dv_null_z: -zd0,
    dv_hold_x: holdX,
    dv_hold_z: -zd0,
    dv_null: Math.hypot(-xd0, -zd0),
    dv_hold: Math.hypot(holdX, -zd0),
    path: path
  };
};
