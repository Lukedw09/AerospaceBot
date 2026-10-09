/* Burnout insertion. Keep in step with ASTRO - OrbitInsertionFromBurnout. */
var Lab = Lab || {};

Lab.insertionEccentric = function (nu, e) {
  return Math.atan2(Math.sqrt(1.0 - e * e) * Math.sin(nu), e + Math.cos(nu));
};

Lab.insertionMean = function (nu, e) {
  var ea = Lab.insertionEccentric(nu, e);
  return ea - e * Math.sin(ea);
};

Lab.orbitInsertion = function (mu, radiusBody, r, v, gamma) {
  var energy = v * v / 2.0 - mu / r;
  var h = r * v * Math.cos(gamma);
  var closed = energy < 0.0 && h > 1.0;
  if (!closed) {
    return { closed: false, dv: null, a: null, e: null, rp: null, ra: null, where: "none" };
  }
  var a = -mu / (2.0 * energy);
  var e = Math.sqrt(Math.max(0.0, 1.0 + 2.0 * energy * h * h / (mu * mu)));
  var rp = a * (1.0 - e);
  var ra = a * (1.0 + e);
  var nearly = e < 1e-4 && Math.abs(gamma) < 1e-3;
  var dv;
  var where;
  var rCirc;
  if (nearly) {
    dv = Math.sqrt(mu / r) - v;
    where = "burnout";
    rCirc = r;
  } else {
    var vA = Math.sqrt(mu * (2.0 / ra - 1.0 / a));
    dv = Math.sqrt(mu / ra) - vA;
    where = "apoapsis";
    rCirc = ra;
  }
  return {
    closed: true,
    energy: energy,
    h: h,
    a: a,
    e: e,
    rp: rp,
    ra: ra,
    dv: dv,
    where: where,
    r_circ: rCirc,
    atmosphere: rp < radiusBody + 120000.0
  };
};
