/* Bi-elliptic transfer. Keep in step with ASTRO - BiellipticTransfer.solve_transfer. */
var Lab = Lab || {};

Lab.apsisSpeed = function (mu, occupied, opposite) {
  if (occupied <= 0.0 || opposite <= 0.0) throw new Error("apsis radii must be > 0 m");
  return Math.sqrt(2.0 * mu * opposite / (occupied * (occupied + opposite)));
};

Lab.ellipseFromApsides = function (periapsis, apoapsis) {
  if (Lab.sameRadius(periapsis, apoapsis)) return { a: periapsis, e: 0.0 };
  if (apoapsis < periapsis) throw new Error("apoapsis must be at least periapsis");
  return {
    a: 0.5 * (apoapsis + periapsis),
    e: (apoapsis - periapsis) / (apoapsis + periapsis)
  };
};

Lab.coastTime = function (mu, periapsis, apoapsis) {
  if (Lab.sameRadius(periapsis, apoapsis)) return 0.0;
  var ellipse = Lab.ellipseFromApsides(periapsis, apoapsis);
  return Math.PI * Math.sqrt(Math.pow(ellipse.a, 3) / mu);
};

Lab.recommendBielliptic = function (dv, dvHohmann) {
  var span = Math.max(Math.abs(dv), Math.abs(dvHohmann), 1.0);
  if (dv < dvHohmann && Math.abs(dv - dvHohmann) > Math.max(1e-12 * Math.max(Math.abs(dv), Math.abs(dvHohmann)), 1e-9 * span)) {
    return "bielliptic";
  }
  return "Hohmann";
};

Lab.bielliptic = function (mu, rDepart, rArrive, rB) {
  if (rDepart <= 0.0 || rArrive <= 0.0 || rB <= 0.0) throw new Error("orbit radii must be > 0 m");
  var outer = Math.max(rDepart, rArrive);
  if (rB < outer && !Lab.sameRadius(rB, outer)) {
    throw new Error("rb must be at least the larger circular radius");
  }
  if (Lab.sameRadius(rB, outer)) rB = outer;
  var e1 = Lab.ellipseFromApsides(Math.min(rDepart, rB), Math.max(rDepart, rB));
  var e2 = Lab.ellipseFromApsides(Math.min(rArrive, rB), Math.max(rArrive, rB));
  var vCirc1 = Lab.circularSpeed(mu, rDepart);
  var vCirc2 = Lab.circularSpeed(mu, rArrive);
  var v1 = Lab.apsisSpeed(mu, rDepart, rB);
  var v1b = Lab.apsisSpeed(mu, rB, rDepart);
  var v2b = Lab.apsisSpeed(mu, rB, rArrive);
  var v2 = Lab.apsisSpeed(mu, rArrive, rB);
  var dv1 = Math.abs(v1 - vCirc1);
  var dv2 = Math.abs(v2b - v1b);
  var dv3 = Math.abs(vCirc2 - v2);
  var hohmann = Lab.hohmann(mu, rDepart, rArrive);
  var dv = dv1 + dv2 + dv3;
  return {
    r1: rDepart,
    r2: rArrive,
    rb: rB,
    a1: e1.a,
    e1: e1.e,
    a2: e2.a,
    e2: e2.e,
    dv1: dv1,
    dv2: dv2,
    dv3: dv3,
    dv: dv,
    tof1: Lab.coastTime(mu, rDepart, rB),
    tof2: Lab.coastTime(mu, rArrive, rB),
    tof: Lab.coastTime(mu, rDepart, rB) + Lab.coastTime(mu, rArrive, rB),
    dv_hohmann: hohmann.dv,
    recommendation: Lab.recommendBielliptic(dv, hohmann.dv)
  };
};
