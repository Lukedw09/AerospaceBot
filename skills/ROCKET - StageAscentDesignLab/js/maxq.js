var Lab = Lab || {};

Lab.peakQ = function (rows) {
  if (!rows.length) throw new Error("table needs at least two rows");
  var best = 0;
  for (var i = 1; i < rows.length; i += 1) {
    if (rows[i].q > rows[best].q) best = i;
  }
  var peak = rows[best];
  return {
    qMax: peak.q,
    tMax: peak.t,
    zMax: peak.z,
    vMax: peak.v,
    interior: rows[0].t < peak.t && peak.t < rows[rows.length - 1].t
  };
};
