/* Nearest frozen pc_bar (tie uses the higher pressure) and linear mixture-ratio interpolation.
   Same rules as ROCKET - PerformanceParameters src/load_table.py. */
var Lab = Lab || {};

Lab.COL_R = 0;
Lab.COL_TC = 1;
Lab.COL_CSTAR = 2;
Lab.COL_GAMMA_C = 3;
Lab.COL_GAMMA_T = 4;

Lab.selectPcBar = function (requested, available) {
  if (!available.length) throw new Error("no frozen pressures are available");
  var best = available[0];
  for (var i = 1; i < available.length; i += 1) {
    var pc = available[i];
    var dist = Math.abs(pc - requested);
    var bestDist = Math.abs(best - requested);
    var nearer = dist < bestDist - 1e-9;
    var tieHigher = Math.abs(dist - bestDist) <= 1e-9 && pc > best;
    if (nearer || tieHigher) best = pc;
  }
  return best;
};

Lab.interpolateRow = function (rows, r, pair) {
  var xs = rows.map(function (row) { return row[Lab.COL_R]; });
  var tol = 1e-9 * Math.max(1, Math.abs(r));
  if (r < xs[0] - tol || r > xs[xs.length - 1] + tol) {
    throw new Error(
      "mixture ratio " + r + " is outside " + pair + " frozen rows "
      + xs[0] + " to " + xs[xs.length - 1] + "; not extrapolating"
    );
  }
  var i;
  for (i = 0; i < xs.length; i += 1) {
    if (Math.abs(xs[i] - r) <= tol) return rows[i].slice();
  }
  var hi = 0;
  while (hi < xs.length && xs[hi] < r) hi += 1;
  var lo = hi - 1;
  var t = (r - xs[lo]) / (xs[hi] - xs[lo]);
  var out = [];
  for (var j = 0; j < rows[lo].length; j += 1) {
    if (j === Lab.COL_R) out.push(r);
    else out.push(rows[lo][j] + t * (rows[hi][j] - rows[lo][j]));
  }
  return out;
};

Lab.lookupPropellant = function (pack, pairName, of, pcPa) {
  var pair = null;
  for (var i = 0; i < pack.pairs.length; i += 1) {
    if (pack.pairs[i].pair === pairName) pair = pack.pairs[i];
  }
  if (!pair) throw new Error("pair is not in the frozen CEA pack");
  var pcBar = pcPa / 1e5;
  var available = pair.tables.map(function (table) { return table.pc_bar; });
  var chosen = Lab.selectPcBar(pcBar, available);
  var table = null;
  for (var k = 0; k < pair.tables.length; k += 1) {
    if (Math.abs(pair.tables[k].pc_bar - chosen) <= 1e-6) table = pair.tables[k];
  }
  var row = Lab.interpolateRow(table.rows, of, pairName);
  var offset = pcBar - table.pc_bar;
  var warning = null;
  if (Math.abs(offset) > pack.offset_warn_bar) {
    warning = "requested chamber pressure is " + offset + " bar from the nearest frozen table ("
      + table.pc_bar + " bar) for " + pairName;
  }
  return {
    pcTableBar: table.pc_bar,
    pcOffsetBar: offset,
    pcWarning: warning,
    Tc: row[Lab.COL_TC],
    cstar: row[Lab.COL_CSTAR],
    gammaChamber: row[Lab.COL_GAMMA_C],
    gammaThroat: row[Lab.COL_GAMMA_T]
  };
};
