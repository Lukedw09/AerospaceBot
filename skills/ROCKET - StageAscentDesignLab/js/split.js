var Lab = Lab || {};

Lab.sigmaOf = function (eps) {
  if (eps < 0 || eps >= 1) throw new Error("structural coefficient must lie in [0, 1)");
  return eps / (1 - eps);
};

Lab.sizeFromPayload = function (payload, dv, c, eps) {
  if (!(dv > 0) || !(c > 0) || payload < 0) {
    throw new Error("delta-v, exhaust speed, and payload must be positive");
  }
  var ratio = Math.exp(dv / c);
  var sigma = Lab.sigmaOf(eps);
  var denom = 1 - (ratio - 1) * sigma;
  if (!(denom > 0)) throw new Error("structural coefficient cannot meet this delta-v");
  var mp = (ratio - 1) * payload / denom;
  return { mp: mp, inert: sigma * mp };
};

Lab.payloadFromGlow = function (glow, dv, c, eps) {
  var ratio = Math.exp(dv / c);
  var mf = glow / ratio;
  var mp = glow - mf;
  var ms = Lab.sigmaOf(eps) * mp;
  return { payload: mf - ms, mp: mp, inert: ms };
};

Lab.stackFromPayload = function (payload, dvs, stages) {
  var rows = [];
  var carried = payload;
  for (var i = stages.length - 1; i >= 0; i -= 1) {
    var sized = Lab.sizeFromPayload(carried, dvs[i], stages[i].c, stages[i].eps);
    rows.push({ dv: dvs[i], mp: sized.mp, inert: sized.inert, payload: carried });
    carried = carried + sized.mp + sized.inert;
  }
  rows.reverse();
  return rows;
};

Lab.stackFromGlow = function (glow, dvs, stages) {
  var rows = [];
  var mass = glow;
  for (var i = 0; i < stages.length; i += 1) {
    var sized = Lab.payloadFromGlow(mass, dvs[i], stages[i].c, stages[i].eps);
    if (!(sized.payload > 0)) throw new Error("glow cannot meet this delta-v");
    rows.push({ dv: dvs[i], mp: sized.mp, inert: sized.inert, payload: sized.payload });
    mass = sized.payload;
  }
  return rows;
};

Lab.maxPayloadFractions = function (glow, dv, stages) {
  var n = stages.length;
  var fracs = [];
  var i;
  for (i = 0; i < n; i += 1) fracs.push(1 / n);
  function score(trial) {
    var dvs = trial.map(function (fraction) { return fraction * dv; });
    try {
      return Lab.stackFromGlow(glow, dvs, stages).slice(-1)[0].payload;
    } catch (err) {
      return -1;
    }
  }
  for (var pass = 0; pass < 4; pass += 1) {
    for (var index = 0; index < n - 1; index += 1) {
      var bestF = fracs[index];
      var bestS = score(fracs);
      for (var stepIndex = 1; stepIndex < 40; stepIndex += 1) {
        var step = stepIndex / 40;
        var trial = fracs.slice();
        trial[index] = step;
        var remain = 1 - step;
        var others = [];
        for (i = 0; i < n; i += 1) if (i !== index) others.push(i);
        var share = 0;
        others.forEach(function (j) { share += fracs[j]; });
        if (share <= 0) {
          others.forEach(function (j) { trial[j] = remain / others.length; });
        } else {
          others.forEach(function (j) { trial[j] = fracs[j] / share * remain; });
        }
        var value = score(trial);
        if (value > bestS) {
          bestS = value;
          bestF = step;
          fracs = trial;
        }
      }
      fracs[index] = bestF;
    }
  }
  var total = fracs.reduce(function (sum, value) { return sum + value; }, 0);
  return fracs.map(function (value) { return value / total; });
};

Lab.splitStages = function (dv, stages, mode, size, payload, glow) {
  if (!(dv > 0)) throw new Error("delta-v must be > 0");
  var specs = stages.map(function (stage) {
    if (!(stage.isp > 0)) throw new Error("each stage needs isp");
    return { c: stage.isp * Lab.G0, eps: stage.eps };
  });
  var dvs;
  if (mode === "equal_dv") {
    dvs = specs.map(function () { return dv / specs.length; });
  } else if (mode === "equal_mr") {
    var sumC = specs.reduce(function (sum, stage) { return sum + stage.c; }, 0);
    var ratio = Math.exp(dv / sumC);
    dvs = specs.map(function (stage) { return stage.c * Math.log(ratio); });
  } else if (mode === "max_payload") {
    if (size !== "glow") throw new Error("max_payload needs a gross liftoff mass");
    dvs = Lab.maxPayloadFractions(glow, dv, specs).map(function (fraction) { return fraction * dv; });
  } else {
    throw new Error("unknown mode");
  }
  if (size === "payload") {
    if (!(payload > 0)) throw new Error("payload must be > 0");
    return Lab.stackFromPayload(payload, dvs, specs);
  }
  if (!(glow > 0)) throw new Error("gross liftoff mass must be > 0");
  return Lab.stackFromGlow(glow, dvs, specs);
};
