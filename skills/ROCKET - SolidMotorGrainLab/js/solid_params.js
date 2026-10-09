/* Port of ROCKET - SolidMotorParameters. */
var Lab = Lab || {};

Lab.burningAreaRatio = function (ab, throat) {
  return ab / throat;
};

Lab.equilibriumChamberPressure = function (k, a, rho, cstar, n) {
  return Math.pow(k * a * rho * cstar, 1 / (1 - n));
};

Lab.burnRate = function (a, pc, n) {
  return a * Math.pow(pc, n);
};
