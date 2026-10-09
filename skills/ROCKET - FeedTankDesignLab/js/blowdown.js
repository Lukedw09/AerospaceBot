/* Polytropic ullage blowdown. Default n = 1. */
var Lab = Lab || {};

Lab.blowdown = function (p0, v0, expelled, n) {
  var v2 = v0 + expelled;
  var p2 = p0 * Math.pow(v0 / v2, n);
  return { v2: v2, p2: p2, ratio: p2 / p0 };
};

Lab.blowdownCurve = function (p0, v0, expelled, n, count) {
  var volumes = [];
  var pressures = [];
  var steps = count - 1;
  for (var i = 0; i < count; i += 1) {
    var vex = expelled * i / steps;
    volumes.push(vex);
    pressures.push(Lab.blowdown(p0, v0, vex, n).p2);
  }
  return { volumes: volumes, pressures: pressures };
};

Lab.pressureHistory = function (p0, v0, expelled, n, burnTime, count) {
  var times = [];
  var pressures = [];
  var steps = count - 1;
  for (var i = 0; i < count; i += 1) {
    var fraction = i / steps;
    times.push(burnTime * fraction);
    pressures.push(Lab.blowdown(p0, v0, expelled * fraction, n).p2);
  }
  return { times: times, pressures: pressures };
};
