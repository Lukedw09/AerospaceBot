/* Steady normal-shock jumps. Mirrors AERO - NormalShock. */
var Lab = Lab || {};

Lab.normalShockMachSq = function (mach, gamma) {
  return ((gamma - 1) * mach * mach + 2) / (2 * gamma * mach * mach - (gamma - 1));
};

Lab.normalShockPressure = function (mach, gamma) {
  return (2 * gamma * mach * mach - (gamma - 1)) / (gamma + 1);
};

Lab.normalShockDensity = function (mach, gamma) {
  return ((gamma + 1) * mach * mach) / ((gamma - 1) * mach * mach + 2);
};

Lab.normalShockTemperature = function (mach, gamma) {
  return (
    (2 * gamma * mach * mach - (gamma - 1)) *
    ((gamma - 1) * mach * mach + 2) /
    ((gamma + 1) * (gamma + 1) * mach * mach)
  );
};

Lab.normalShockStagnationPressure = function (mach, gamma) {
  return (
    Math.pow(
      ((gamma + 1) * mach * mach) / ((gamma - 1) * mach * mach + 2),
      gamma / (gamma - 1)
    ) *
    Math.pow(
      (gamma + 1) / (2 * gamma * mach * mach - (gamma - 1)),
      1 / (gamma - 1)
    )
  );
};

Lab.shockState = function (mach, gamma) {
  if (!isFinite(mach) || mach < 1 || mach > 1e6) {
    throw new Error("upstream Mach must satisfy 1 <= M1 <= 1e6");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be finite and > 1");
  }
  var m2Sq = Lab.normalShockMachSq(mach, gamma);
  if (m2Sq < 0 || !isFinite(m2Sq)) {
    throw new Error("downstream Mach is not real");
  }
  var ptRatio = Lab.normalShockStagnationPressure(mach, gamma);
  if (!(ptRatio > 0) || !isFinite(ptRatio)) {
    throw new Error("stagnation-pressure ratio is not positive");
  }
  return {
    M1: mach,
    gamma: gamma,
    M2: Math.sqrt(m2Sq),
    p2_over_p1: Lab.normalShockPressure(mach, gamma),
    T2_over_T1: Lab.normalShockTemperature(mach, gamma),
    rho2_over_rho1: Lab.normalShockDensity(mach, gamma),
    pt2_over_pt1: ptRatio,
    ds_over_R: -Math.log(ptRatio)
  };
};
