/* Pitot Mach from isentropic stagnation or Rayleigh-Pitot. */
var Lab = Lab || {};

Lab.pitotSonicRatio = function (gamma) {
  return Math.pow((gamma + 1) / 2, gamma / (gamma - 1));
};

Lab.rayleighPitotRatio = function (mach, gamma) {
  return (
    Math.pow(((gamma + 1) / 2) * mach * mach, gamma / (gamma - 1)) *
    Math.pow((gamma + 1) / (2 * gamma * mach * mach - (gamma - 1)), 1 / (gamma - 1))
  );
};

Lab.machFromIsentropic = function (ratio, gamma) {
  if (ratio < 1) {
    throw new Error("pitot pressure must be at least freestream static pressure");
  }
  var exponent = (gamma - 1) / gamma;
  var machSq = (2 / (gamma - 1)) * (Math.pow(ratio, exponent) - 1);
  if (machSq < 0 && Math.abs(machSq) <= 1e-15) {
    machSq = 0;
  }
  if (machSq < 0 || !isFinite(machSq)) {
    throw new Error("pressure ratio does not give a real subsonic Mach number");
  }
  return Math.sqrt(machSq);
};

Lab.machFromRayleighPitot = function (ratio, gamma) {
  var sonic = Lab.pitotSonicRatio(gamma);
  if (ratio < sonic - 1e-14) {
    throw new Error("pressure ratio is below the sonic Rayleigh-Pitot value");
  }
  if (Math.abs(ratio - sonic) <= 1e-14) {
    return 1;
  }
  var lo = 1;
  var hi = 2;
  while (Lab.rayleighPitotRatio(hi, gamma) < ratio) {
    hi *= 2;
    if (hi > 1e6) {
      throw new Error("could not bracket a Mach number for the pitot ratio");
    }
  }
  for (var i = 0; i < 200; i++) {
    var mid = 0.5 * (lo + hi);
    if (Lab.rayleighPitotRatio(mid, gamma) < ratio) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.pitotState = function (pitot, staticPressure, gamma) {
  if (!isFinite(pitot) || !isFinite(staticPressure) || !isFinite(gamma)) {
    throw new Error("pitot, static, and gamma must be finite");
  }
  if (pitot <= 0) {
    throw new Error("pitot pressure must be > 0 Pa");
  }
  if (staticPressure <= 0) {
    throw new Error("freestream static pressure must be > 0 Pa");
  }
  if (gamma <= 1) {
    throw new Error("gamma must be > 1");
  }
  if (pitot < staticPressure) {
    throw new Error("pitot pressure must be at least freestream static pressure");
  }
  var ratio = pitot / staticPressure;
  var sonic = Lab.pitotSonicRatio(gamma);
  var mach;
  var branch;
  var relation;
  if (ratio <= sonic + 1e-12) {
    mach = Lab.machFromIsentropic(ratio, gamma);
    if (mach > 1 && Math.abs(mach - 1) <= 1e-12) {
      mach = 1;
    }
    if (mach > 1) {
      throw new Error("isentropic branch returned a Mach number above 1");
    }
    branch = Math.abs(mach - 1) <= 1e-12 ? "sonic" : "subsonic";
    relation = "isentropic_stagnation";
  } else {
    mach = Lab.machFromRayleighPitot(ratio, gamma);
    branch = "supersonic";
    relation = "rayleigh_pitot";
  }
  return {
    pitot: pitot,
    static: staticPressure,
    gamma: gamma,
    ratio: ratio,
    sonic_ratio: sonic,
    branch: branch,
    relation: relation,
    M: mach,
    q: 0.5 * gamma * staticPressure * mach * mach
  };
};
