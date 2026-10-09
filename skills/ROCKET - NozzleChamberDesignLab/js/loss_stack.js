/* Delivered c* and CF from two efficiency products. g0 matches ROCKET - LossStack. */
var Lab = Lab || {};

Lab.G0 = 9.80665;

Lab.deliver = function (cfIdeal, cstarIdeal, etaCstar, etaCf) {
  var cstar = cstarIdeal * etaCstar;
  var cf = cfIdeal * etaCf;
  var c = cstar * cf;
  return { cstar: cstar, cf: cf, c: c, isp: c / Lab.G0 };
};
