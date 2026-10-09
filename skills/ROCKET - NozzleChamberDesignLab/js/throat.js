/* Port of ROCKET - ThroatSizingandMassFlow throat_sizing.py. */
var Lab = Lab || {};

Lab.throatArea = function (thrust, cf, pc) {
  return thrust / (cf * pc);
};

Lab.throatDiameter = function (area) {
  return Math.sqrt(4 * area / Math.PI);
};

Lab.massFlow = function (pc, area, cstar) {
  return pc * area / cstar;
};
