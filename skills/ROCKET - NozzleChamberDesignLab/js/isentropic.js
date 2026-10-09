/* Port of ROCKET - Area-Mach Graph area_mach.py. Keep the bisection in step with that file. */
var Lab = Lab || {};

Lab.EXPANSION_REL_TOL = 0.005;

Lab.areaRatio = function (M, gamma) {
  if (!(M > 0)) throw new Error("Mach number must be positive");
  var g = gamma;
  return (1 / M) * Math.pow(
    (2 / (g + 1)) * (1 + ((g - 1) / 2) * M * M),
    (g + 1) / (2 * (g - 1))
  );
};

Lab.exitPressure = function (pc, Me, gamma) {
  var g = gamma;
  return pc * Math.pow(1 + ((g - 1) / 2) * Me * Me, -g / (g - 1));
};

Lab.thrustCoefficientIdeal = function (gamma, pe, pc, pa, Ae, At) {
  var k = gamma;
  var momentum = Math.sqrt(
    (2 * k * k / (k - 1))
    * Math.pow(2 / (k + 1), (k + 1) / (k - 1))
    * (1 - Math.pow(pe / pc, (k - 1) / k))
  );
  return momentum + (pe - pa) / pc * (Ae / At);
};

Lab.invertSupersonicMach = function (epsilon, gamma) {
  if (epsilon < 1) throw new Error("epsilon must be >= 1");
  if (Math.abs(epsilon - 1) < 1e-14) return 1;
  var lo = 1 + 1e-12;
  var hi = 2;
  while (Lab.areaRatio(hi, gamma) < epsilon) {
    hi *= 2;
    if (hi > 1e6) throw new Error("could not bracket supersonic Mach for given epsilon");
  }
  for (var n = 0; n < 200; n += 1) {
    var mid = 0.5 * (lo + hi);
    if (Lab.areaRatio(mid, gamma) > epsilon) hi = mid;
    else lo = mid;
  }
  return 0.5 * (lo + hi);
};

Lab.expansionFlag = function (pe, pa) {
  if (!(pa > 0)) return "vacuum_underexpanded";
  var rel = Math.abs(pe - pa) / Math.max(pa, pe, 1e-30);
  if (rel <= Lab.EXPANSION_REL_TOL) return "perfectly expanded";
  if (pe > pa) return "underexpanded";
  return "overexpanded";
};
