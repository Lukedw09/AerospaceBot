/* Port of ROCKET - CircularPortGrainHistory geometry, rate law, and samples. */
var Lab = Lab || {};

Lab.N_CURVE = 201;

Lab.circularPortBurningArea = function (radius, length) {
  return 2 * Math.PI * radius * length;
};

Lab.initialWeb = function (outer, port) {
  return outer - port;
};

Lab.remainingWeb = function (outer, radius) {
  return outer - radius;
};

Lab.circularPortFromRemainingWeb = function (outer, wrem) {
  return outer - wrem;
};

Lab.sliverPortRadius = function (outer, sliver, port) {
  return Math.sqrt(outer * outer - sliver * (outer * outer - port * port));
};

Lab.rateLaw = function (a, n, length, throat, rho, cstar) {
  var alpha = n / (1 - n);
  var scale = (2 * Math.PI * length / throat) * a * rho * cstar;
  var prefactor = a * Math.pow(scale, alpha);
  return { alpha: alpha, prefactor: prefactor };
};

Lab.timeFromPort = function (radius, port, alpha, prefactor) {
  if (radius < port) throw new Error("port radius cannot shrink");
  if (radius === port) return 0;
  if (Math.abs(alpha - 1) <= 1e-14) return Math.log(radius / port) / prefactor;
  return (Math.pow(radius, 1 - alpha) - Math.pow(port, 1 - alpha)) / (prefactor * (1 - alpha));
};

Lab.grainHistory = function (a, n, throat, rho, cstar, port, length, outer, sliver) {
  var web0 = Lab.initialWeb(outer, port);
  var rEnd = Lab.sliverPortRadius(outer, sliver, port);
  var wEnd = Lab.remainingWeb(outer, rEnd);
  if (!(rEnd > port)) throw new Error("sliver fraction leaves no web to burn");
  var law = Lab.rateLaw(a, n, length, throat, rho, cstar);
  if (!(isFinite(law.prefactor) && law.prefactor > 0)) {
    throw new Error("burn-rate prefactor must be finite and > 0");
  }
  var tBurn = Lab.timeFromPort(rEnd, port, law.alpha, law.prefactor);
  var times = [];
  var kHist = [];
  var pcHist = [];
  var wremHist = [];
  var abHist = [];
  var radiusHist = [];
  var last = Lab.N_CURVE - 1;
  for (var i = 0; i < Lab.N_CURVE; i += 1) {
    var wrem = web0 + (wEnd - web0) * i / last;
    var radius = Lab.circularPortFromRemainingWeb(outer, wrem);
    var ab = Lab.circularPortBurningArea(radius, length);
    var k = Lab.burningAreaRatio(ab, throat);
    var pc = Lab.equilibriumChamberPressure(k, a, rho, cstar, n);
    var rburn = Lab.burnRate(a, pc, n);
    var expected = law.prefactor * Math.pow(radius, law.alpha);
    var scale = Math.max(Math.abs(expected), 1);
    if (!(Math.abs(rburn - expected) <= 1e-8 * scale)) {
      throw new Error("composed burn rate does not match Saint Robert at this port");
    }
    times.push(Lab.timeFromPort(radius, port, law.alpha, law.prefactor));
    kHist.push(k);
    pcHist.push(pc);
    wremHist.push(wrem);
    abHist.push(ab);
    radiusHist.push(radius);
  }
  return {
    web0: web0,
    rEnd: rEnd,
    wEnd: wEnd,
    tBurn: tBurn,
    times: times,
    K: kHist,
    pc: pcHist,
    wrem: wremHist,
    Ab: abHist,
    radius: radiusHist
  };
};
