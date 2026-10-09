/* Trapezoidal planform. Ports wing_geometry.py. */
var Lab = Lab || {};

Lab.SWEEP_LIMIT = Math.PI / 2;
Lab.DEFAULT_SWEEP_AT = 0.25;

Lab.wingArea = function (span, root, tip) {
  return span * (root + tip) / 2;
};

Lab.taperRatio = function (tip, root) {
  return tip / root;
};

Lab.aspectRatio = function (span, area) {
  return span * span / area;
};

Lab.meanAerodynamicChord = function (root, taper) {
  return (2 / 3) * root * (1 + taper + taper * taper) / (1 + taper);
};

Lab.macStation = function (span, taper) {
  return (span / 6) * (1 + 2 * taper) / (1 + taper);
};

Lab.chordFractionSweep = function (sweepLe, fraction, taper, ar) {
  var shift = 4 * fraction * (1 - taper) / (ar * (1 + taper));
  return Math.atan(Math.tan(sweepLe) - shift);
};

Lab.leadingEdgeSweep = function (sweepN, fraction, taper, ar) {
  var shift = 4 * fraction * (1 - taper) / (ar * (1 + taper));
  return Math.atan(Math.tan(sweepN) + shift);
};

Lab.planform = function (span, root, tip, sweep, sweepAt, sweepAtGiven) {
  if (!(span > 0)) throw new Error("span must be > 0");
  if (!(root > 0)) throw new Error("root chord must be > 0");
  if (!(tip >= 0)) throw new Error("tip chord must be >= 0");
  var area = Lab.wingArea(span, root, tip);
  var taper = Lab.taperRatio(tip, root);
  var ar = Lab.aspectRatio(span, area);
  var sweepLe;
  var station = null;
  var stationSource;
  if (sweep == null) {
    sweepLe = 0;
    stationSource = "omitted";
  } else {
    if (!isFinite(sweep) || !(sweep > -Lab.SWEEP_LIMIT) || !(sweep < Lab.SWEEP_LIMIT)) {
      throw new Error("sweep must lie strictly between -pi/2 and pi/2");
    }
    if (sweepAtGiven) {
      if (sweepAt == null || !(sweepAt >= 0) || sweepAt > 1) throw new Error("sweep station must be from 0 to 1");
      station = sweepAt;
      stationSource = "given";
    } else {
      station = Lab.DEFAULT_SWEEP_AT;
      stationSource = "default-quarter-chord";
    }
    sweepLe = Lab.leadingEdgeSweep(sweep, station, taper, ar);
  }
  if (!(sweepLe > -Lab.SWEEP_LIMIT) || !(sweepLe < Lab.SWEEP_LIMIT)) {
    throw new Error("leading-edge sweep must lie strictly between -pi/2 and pi/2");
  }
  var yMac = Lab.macStation(span, taper);
  return {
    span: span,
    root: root,
    tip: tip,
    area: area,
    aspectRatio: ar,
    taper: taper,
    mac: Lab.meanAerodynamicChord(root, taper),
    yMac: yMac,
    sweep: sweep,
    sweepAt: station,
    sweepAtSource: stationSource,
    sweepLe: sweepLe,
    sweepC4: Lab.chordFractionSweep(sweepLe, 0.25, taper, ar),
    xLeMac: yMac * Math.tan(sweepLe)
  };
};

Lab.chordAt = function (y, span, root, tip) {
  return root + (tip - root) * (2 * Math.abs(y) / span);
};
