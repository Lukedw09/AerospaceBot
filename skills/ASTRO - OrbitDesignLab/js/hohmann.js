/* Hohmann transfer. Keep in step with ASTRO - HohmannTransfer.solve_transfer. */
var Lab = Lab || {};

Lab.biparabolicDeltaV = function (mu, rDepart, rArrive) {
  return (Lab.escapeSpeed(mu, rDepart) - Lab.circularSpeed(mu, rDepart))
    + (Lab.escapeSpeed(mu, rArrive) - Lab.circularSpeed(mu, rArrive));
};

Lab.recommendAgainstBiparabolic = function (dv, dvInfinity) {
  var span = Math.max(Math.abs(dvInfinity), Math.abs(dv), 1.0);
  if (dv > dvInfinity && Math.abs(dv - dvInfinity) > Math.max(1e-12 * Math.max(Math.abs(dv), Math.abs(dvInfinity)), 1e-9 * span)) {
    return "bielliptic";
  }
  return "Hohmann";
};

Lab.radiiFromAltitude = function (bodyRadius, altitude, eccentricity) {
  if (altitude < 0.0) throw new Error("--alt must be >= 0 m");
  if (eccentricity < 0.0 || eccentricity >= 1.0) throw new Error("--ecc must satisfy 0 <= e < 1");
  var rDepart = bodyRadius + altitude;
  var rArrive = rDepart * (1.0 + eccentricity) / (1.0 - eccentricity);
  return { r1: rDepart, r2: rArrive };
};

Lab.hohmann = function (mu, rDepart, rArrive) {
  if (rDepart <= 0.0 || rArrive <= 0.0) throw new Error("orbit radii must be > 0 m");
  var direction;
  var periapsis;
  var apoapsis;
  if (Lab.sameRadius(rDepart, rArrive)) {
    direction = "coast";
    periapsis = rDepart;
    apoapsis = rDepart;
  } else if (rDepart < rArrive) {
    direction = "outward";
    periapsis = rDepart;
    apoapsis = rArrive;
  } else {
    direction = "inward";
    periapsis = rArrive;
    apoapsis = rDepart;
  }
  var semiMajor = 0.5 * (periapsis + apoapsis);
  var eccentricity = direction === "coast" ? 0.0 : (apoapsis - periapsis) / (apoapsis + periapsis);
  var vDepartTransfer = direction === "inward"
    ? Lab.visViva(mu, apoapsis, semiMajor)
    : Lab.visViva(mu, periapsis, semiMajor);
  var vArriveTransfer = direction === "inward"
    ? Lab.visViva(mu, periapsis, semiMajor)
    : Lab.visViva(mu, apoapsis, semiMajor);
  var vCircularDepart = Lab.circularSpeed(mu, rDepart);
  var vCircularArrive = Lab.circularSpeed(mu, rArrive);
  var dvDepart = Math.abs(vDepartTransfer - vCircularDepart);
  var dvArrive = Math.abs(vCircularArrive - vArriveTransfer);
  var period = Lab.orbitalPeriod(mu, semiMajor);
  var dv = dvDepart + dvArrive;
  var dvInfinity = Lab.biparabolicDeltaV(mu, rDepart, rArrive);
  return {
    direction: direction,
    r1: rDepart,
    r2: rArrive,
    a: semiMajor,
    e: eccentricity,
    periapsis: periapsis,
    apoapsis: apoapsis,
    v_depart: vDepartTransfer,
    v_arrive: vArriveTransfer,
    dv_depart: dvDepart,
    dv_arrive: dvArrive,
    sense_depart: Lab.burnSense(vDepartTransfer, vCircularDepart),
    sense_arrive: Lab.burnSense(vCircularArrive, vArriveTransfer),
    dv: dv,
    tof: 0.5 * period,
    period: period,
    r2_over_r1: Math.abs(rArrive) / Math.abs(rDepart),
    dv_biparabolic: dvInfinity,
    recommendation: Lab.recommendAgainstBiparabolic(dv, dvInfinity)
  };
};
