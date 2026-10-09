/* Report 824 lookup: nearest 6e6, exact chart, or log-Re blend. Same rules as naca_four_digit_section.py. */
var Lab = Lab || {};

Lab.DEFAULT_RE = 6e6;
Lab.SLOPE_WINDOW_DEG = 6;

Lab.lerp = function (x, xp, fp) {
  if (xp.length !== fp.length || xp.length < 2) throw new Error("interpolation tables must have at least two matching points");
  if (x <= xp[0]) {
    if (x < xp[0]) throw new Error("value " + x + " is below the measured table");
    return fp[0];
  }
  if (x >= xp[xp.length - 1]) {
    if (x > xp[xp.length - 1]) throw new Error("value " + x + " is above the measured table");
    return fp[fp.length - 1];
  }
  for (var i = 1; i < xp.length; i += 1) {
    if (x <= xp[i]) {
      var span = xp[i] - xp[i - 1];
      if (span === 0) return fp[i];
      var w = (x - xp[i - 1]) / span;
      return fp[i - 1] + w * (fp[i] - fp[i - 1]);
    }
  }
  return fp[fp.length - 1];
};

Lab.mixTables = function (weight, xa, fa, xb, fb, xq) {
  var out = [];
  for (var i = 0; i < xq.length; i += 1) {
    out.push((1 - weight) * Lab.lerp(xq[i], xa, fa) + weight * Lab.lerp(xq[i], xb, fb));
  }
  return out;
};

Lab.blendPolars = function (low, high, reynolds) {
  var span = Math.log(high.Re) - Math.log(low.Re);
  if (span === 0) return low;
  var weight = (Math.log(reynolds) - Math.log(low.Re)) / span;
  var a0 = Math.max(low.alpha_deg[0], high.alpha_deg[0]);
  var a1 = Math.min(low.alpha_deg[low.alpha_deg.length - 1], high.alpha_deg[high.alpha_deg.length - 1]);
  var alphas = [];
  low.alpha_deg.concat(high.alpha_deg).forEach(function (x) {
    if (x >= a0 && x <= a1 && alphas.indexOf(x) < 0) alphas.push(x);
  });
  alphas.sort(function (a, b) { return a - b; });
  var c0 = Math.max(Math.min.apply(null, low.cl_polar), Math.min.apply(null, high.cl_polar));
  var c1 = Math.min(Math.max.apply(null, low.cl_polar), Math.max.apply(null, high.cl_polar));
  var lifts = [];
  low.cl_polar.concat(high.cl_polar).forEach(function (x) {
    if (x >= c0 && x <= c1 && lifts.indexOf(x) < 0) lifts.push(x);
  });
  lifts.sort(function (a, b) { return a - b; });
  if (alphas.length < 2 || lifts.length < 2) throw new Error("neighboring Reynolds-number charts do not overlap");
  return {
    Re: reynolds,
    alpha_deg: alphas,
    cl: Lab.mixTables(weight, low.alpha_deg, low.cl, high.alpha_deg, high.cl, alphas),
    cl_polar: lifts,
    cd: Lab.mixTables(weight, low.cl_polar, low.cd, high.cl_polar, high.cd, lifts)
  };
};

Lab.chartList = function (pack, designation) {
  var rows = pack.airfoils[designation];
  if (!rows) return null;
  return rows.slice().sort(function (a, b) { return a.Re - b.Re; });
};

Lab.polarFor = function (pack, designation, reynolds) {
  var curves = Lab.chartList(pack, designation);
  if (!curves) return null;
  if (reynolds == null) {
    var target = pack.defaultRe || Lab.DEFAULT_RE;
    var best = curves[0];
    for (var i = 1; i < curves.length; i += 1) {
      if (Math.abs(curves[i].Re - target) < Math.abs(best.Re - target)) best = curves[i];
    }
    return { polar: best, source: "nearest_6e6" };
  }
  if (!isFinite(reynolds) || !(reynolds > 0)) throw new Error("Reynolds number must be finite and greater than 0");
  for (var k = 0; k < curves.length; k += 1) {
    if (Math.abs(reynolds - curves[k].Re) <= 1e-6 * curves[k].Re) {
      return { polar: curves[k], source: "chart" };
    }
  }
  if (reynolds < curves[0].Re || reynolds > curves[curves.length - 1].Re) {
    throw new Error(
      "Reynolds number " + reynolds + " is outside the Report 824 table for " + designation
    );
  }
  for (var j = 0; j < curves.length - 1; j += 1) {
    if (curves[j].Re <= reynolds && reynolds <= curves[j + 1].Re) {
      return { polar: Lab.blendPolars(curves[j], curves[j + 1], reynolds), source: "log_re_blend" };
    }
  }
  throw new Error("could not place Reynolds number between neighboring charts");
};

Lab.zeroLiftDeg = function (polar) {
  var cl = polar.cl;
  var alpha = polar.alpha_deg;
  for (var i = 1; i < cl.length; i += 1) {
    var lo = cl[i - 1];
    var hi = cl[i];
    if (lo === 0) return alpha[i - 1];
    if (lo < 0 && hi > 0) return Lab.lerp(0, [lo, hi], [alpha[i - 1], alpha[i]]);
    if (lo < 0 && hi === 0) return alpha[i];
  }
  throw new Error("measured lift curve does not cross zero with increasing angle of attack");
};

Lab.clMax = function (polar) {
  var peak = 0;
  for (var i = 1; i < polar.cl.length; i += 1) {
    if (polar.cl[i] > polar.cl[peak]) peak = i;
  }
  return { alphaDeg: polar.alpha_deg[peak], cl: polar.cl[peak] };
};

Lab.measuredA0 = function (polar, alphaL0Deg) {
  var xs = [];
  var ys = [];
  for (var i = 0; i < polar.alpha_deg.length; i += 1) {
    if (Math.abs(polar.alpha_deg[i] - alphaL0Deg) <= Lab.SLOPE_WINDOW_DEG + 1e-9) {
      xs.push((polar.alpha_deg[i] - alphaL0Deg) * Math.PI / 180);
      ys.push(polar.cl[i]);
    }
  }
  if (xs.length < 2) throw new Error("measured lift curve has too few points near zero lift");
  var den = 0;
  var num = 0;
  for (var k = 0; k < xs.length; k += 1) {
    den += xs[k] * xs[k];
    num += xs[k] * ys[k];
  }
  if (den === 0) throw new Error("measured slope is undefined");
  return num / den;
};

Lab.cdAtCl = function (polar, cl) {
  var lo = polar.cl_polar[0];
  var hi = polar.cl_polar[polar.cl_polar.length - 1];
  if (cl < lo || cl > hi) return null;
  return Lab.lerp(cl, polar.cl_polar, polar.cd);
};

Lab.clAt = function (polar, alphaDeg) {
  var lo = polar.alpha_deg[0];
  var hi = polar.alpha_deg[polar.alpha_deg.length - 1];
  if (alphaDeg < lo || alphaDeg > hi) return null;
  return Lab.lerp(alphaDeg, polar.alpha_deg, polar.cl);
};
