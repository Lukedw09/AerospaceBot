var Lab = Lab || {};

Lab.trim = function (value) {
  if (typeof value !== "number" || !isFinite(value)) return String(value);
  var text = value.toPrecision(8);
  if (text.indexOf("e") !== -1 || text.indexOf("E") !== -1) return text.replace("+", "");
  return String(Number(text));
};

Lab.closeEnough = function (next, prev) {
  var delta = Math.abs(next - prev);
  return delta < 1 || delta <= 0.001 * Math.max(Math.abs(next), Math.abs(prev));
};

Lab.activeStages = function (seed) {
  return seed.stages.slice(0, seed.count);
};

Lab.onePass = function (seed, gravity, drag) {
  var stages = Lab.activeStages(seed);
  var budgetDv = Lab.designDeltaV(
    seed.alt, seed.vRot, gravity, drag, 0, seed.circ, seed.margin, seed.marginFraction
  );
  var splitRows = Lab.splitStages(budgetDv.dv, stages, seed.mode, seed.size, seed.payload, seed.glow);
  var payload = seed.size === "payload" ? seed.payload : splitRows[splitRows.length - 1].payload;
  var flown = splitRows.map(function (row, index) {
    var input = stages[index];
    var inert = row.inert;
    var replaced = Lab.budgetInert(row.mp, input);
    if (replaced !== null) inert = replaced;
    return {
      mp: row.mp,
      inertSplit: row.inert,
      inert: inert,
      isp: input.isp,
      tb: input.tb,
      dv: row.dv
    };
  });
  var mass = payload + flown.reduce(function (sum, stage) { return sum + stage.mp + stage.inert; }, 0);
  var mu = Lab.G0 * Lab.R_EARTH * Lab.R_EARTH;
  var hold = seed.path === "gamma";
  var theta0 = hold ? seed.gamma : Math.PI / 2 - seed.kick;
  if (!isFinite(theta0) || theta0 < 0 || theta0 > Math.PI / 2) {
    throw new Error("flight-path angle is outside 0 to pi/2");
  }
  if (seed.cd > 0 && !(seed.area > 0)) throw new Error("drag coefficient needs area > 0");
  var jet = null;
  if (seed.jettison) {
    if (!(seed.jetMass > 0)) throw new Error("jettison needs mass > 0");
    jet = { mass: seed.jetMass };
    if (seed.jetBy === "time") jet.time = seed.jetTime;
    else jet.alt = seed.jetAlt;
  }
  var state = [Lab.R_EARTH, 0, 0, 0];
  var t0 = 0;
  var rows = [];
  var gravityLoss = 0;
  var dragLoss = 0;
  var ideal = 0;
  var piece = null;
  flown.forEach(function (stage) {
    var m0 = mass;
    if (!(stage.tb > 0)) throw new Error("burn time must be > 0");
    var mdot = stage.mp / stage.tb;
    if (!(mdot > 0) || stage.mp >= m0) throw new Error("stage masses or burn time are not physical");
    var mf = m0 - stage.mp;
    var c = stage.isp * Lab.G0;
    ideal += c * Math.log(m0 / mf);
    var heading = theta0;
    if (!hold && Math.hypot(state[2], state[3]) >= 1e-9) heading = Math.atan2(state[2], state[3]);
    piece = Lab.odeStage({
      m0: m0,
      mdot: mdot,
      tb: stage.tb,
      thrust: mdot * c,
      mu: mu,
      radiusBody: Lab.R_EARTH,
      state: state,
      theta0: heading,
      hold: hold,
      cd: seed.cd,
      area: seed.area,
      t0: t0,
      jettison: jet
    });
    if (piece.dropped) jet = null;
    gravityLoss += piece.dvg;
    dragLoss += piece.dvD;
    rows = rows.concat(piece.rows);
    mass = mf - stage.inert;
    if (!(mass > 0)) throw new Error("staging drops the mass through zero");
    state = piece.state;
    t0 += stage.tb;
    if (!hold) theta0 = piece.thetaBo;
  });
  var peak = Lab.peakQ(rows);
  return {
    ok: true,
    vCirc: budgetDv.vCirc,
    margin: budgetDv.margin,
    marginSource: budgetDv.marginSource,
    dvDesign: budgetDv.dv,
    dvIdeal: ideal,
    gravity: gravityLoss,
    drag: dragLoss,
    steering: 0,
    payload: payload,
    stacked: payload + flown.reduce(function (sum, stage) { return sum + stage.mp + stage.inert; }, 0),
    stages: flown,
    Vbo: piece.Vbo,
    gammaBo: piece.thetaBo,
    rBo: piece.rBo,
    Zbo: piece.rBo - Lab.R_EARTH,
    qMax: peak.qMax,
    tMax: peak.tMax,
    zMax: peak.zMax,
    interior: peak.interior,
    rows: rows
  };
};

Lab.designPoint = function (seed) {
  var gravity = 0;
  var drag = 0;
  var previousMp = null;
  var last = null;
  for (var pass = 1; pass <= 12; pass += 1) {
    var point;
    try {
      point = Lab.onePass(seed, gravity, drag);
    } catch (err) {
      if (!last) return { ok: false, error: err.message || String(err) };
      last.settled = false;
      last.passes = pass - 1;
      last.warning = err.message || String(err);
      return last;
    }
    point.passes = pass;
    var massesMatch = previousMp !== null && point.stages.every(function (stage, index) {
      return Lab.closeEnough(stage.mp, previousMp[index]);
    });
    if (massesMatch && Lab.closeEnough(point.gravity, gravity) && Lab.closeEnough(point.drag, drag)) {
      point.settled = true;
      return point;
    }
    last = point;
    gravity = point.gravity;
    drag = point.drag;
    previousMp = point.stages.map(function (stage) { return stage.mp; });
  }
  last.settled = false;
  return last;
};

Lab.num = function (id) {
  var value = document.getElementById(id).value;
  if (value === "") return null;
  return Number(value);
};

Lab.stageNum = function (fieldset, key) {
  var input = fieldset.querySelector("[data-key='" + key + "']");
  if (!input || input.value === "") return 0;
  return Number(input.value);
};

Lab.readSeed = function () {
  var count = Number(document.getElementById("count").value);
  var stages = [];
  document.querySelectorAll("fieldset[data-stage]").forEach(function (fieldset) {
    stages.push({
      isp: Lab.stageNum(fieldset, "isp"),
      eps: Lab.stageNum(fieldset, "eps"),
      tb: Lab.stageNum(fieldset, "tb"),
      budget: fieldset.querySelector("[data-key='budget']").checked,
      law: fieldset.querySelector("[data-key='law']").value,
      k: Lab.stageNum(fieldset, "k"),
      mH: Lab.stageNum(fieldset, "mH"),
      residuals: Lab.stageNum(fieldset, "residuals"),
      tank: Lab.stageNum(fieldset, "tank"),
      engineMass: Lab.stageNum(fieldset, "engineMass"),
      engineCount: Lab.stageNum(fieldset, "engineCount"),
      fairing: Lab.stageNum(fieldset, "fairing"),
      interstage: Lab.stageNum(fieldset, "interstage"),
      other: Lab.stageNum(fieldset, "other")
    });
  });
  return {
    count: count,
    size: document.querySelector("input[name='size']:checked").value,
    mode: document.getElementById("mode").value,
    payload: Lab.num("payload"),
    glow: Lab.num("glow"),
    alt: Lab.num("alt"),
    vRot: Lab.num("vrot") || 0,
    circ: Lab.num("circ") || 0,
    margin: Lab.num("margin"),
    marginFraction: Lab.num("margin-fraction"),
    path: document.querySelector("input[name='path']:checked").value,
    kick: Lab.num("kick"),
    gamma: Lab.num("gamma"),
    cd: Lab.num("cd") || 0,
    area: Lab.num("area") || 0,
    jettison: document.getElementById("jettison").checked,
    jetMass: Lab.num("jet-mass"),
    jetBy: document.querySelector("input[name='jetBy']:checked").value,
    jetAlt: Lab.num("jet-alt"),
    jetTime: Lab.num("jet-time"),
    stages: stages
  };
};

Lab.writeSeed = function (seed) {
  document.getElementById("count").value = String(seed.count);
  document.querySelector("input[name='size'][value='" + seed.size + "']").checked = true;
  document.getElementById("mode").value = seed.mode;
  document.getElementById("payload").value = seed.payload;
  document.getElementById("glow").value = seed.glow;
  document.getElementById("alt").value = seed.alt;
  document.getElementById("vrot").value = seed.vRot;
  document.getElementById("circ").value = seed.circ;
  document.getElementById("margin").value = seed.margin === null || seed.margin === undefined ? "" : seed.margin;
  document.getElementById("margin-fraction").value = seed.marginFraction === null || seed.marginFraction === undefined ? "" : seed.marginFraction;
  document.querySelector("input[name='path'][value='" + seed.path + "']").checked = true;
  document.getElementById("kick").value = seed.kick;
  document.getElementById("gamma").value = seed.gamma;
  document.getElementById("cd").value = seed.cd;
  document.getElementById("area").value = seed.area;
  document.getElementById("jettison").checked = !!seed.jettison;
  document.getElementById("jet-mass").value = seed.jetMass;
  document.querySelector("input[name='jetBy'][value='" + seed.jetBy + "']").checked = true;
  document.getElementById("jet-alt").value = seed.jetAlt;
  document.getElementById("jet-time").value = seed.jetTime;
  document.querySelectorAll("fieldset[data-stage]").forEach(function (fieldset, index) {
    var stage = seed.stages[index];
    ["isp", "eps", "tb", "k", "mH", "residuals", "tank", "engineMass", "engineCount", "fairing", "interstage", "other"].forEach(function (key) {
      fieldset.querySelector("[data-key='" + key + "']").value = stage[key];
    });
    fieldset.querySelector("[data-key='budget']").checked = !!stage.budget;
    fieldset.querySelector("[data-key='law']").value = stage.law;
  });
};

Lab.applyMode = function (seed) {
  document.body.classList.remove("count-1", "count-2", "count-3", "size-payload", "size-glow", "path-kick", "path-gamma", "jet-on", "jet-off", "jet-alt", "jet-time");
  document.body.classList.add("count-" + seed.count, "size-" + seed.size, "path-" + seed.path, seed.jettison ? "jet-on" : "jet-off", "jet-" + seed.jetBy);
  document.querySelectorAll("fieldset[data-stage]").forEach(function (fieldset) {
    var on = fieldset.querySelector("[data-key='budget']").checked;
    var law = fieldset.querySelector("[data-key='law']").value;
    fieldset.classList.toggle("budget-on", on);
    fieldset.classList.toggle("budget-off", !on);
    fieldset.classList.toggle("law-linear", law === "linear");
    fieldset.classList.toggle("law-explicit", law === "explicit");
  });
};

Lab.fit = function (canvas) {
  var rect = canvas.getBoundingClientRect();
  var width = Math.max(1, rect.width);
  var height = Math.max(1, rect.height);
  var ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  var ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { ctx: ctx, width: width, height: height };
};

Lab.niceTicks = function (lo, hi, count) {
  var span = hi - lo;
  if (!(span > 0)) return [lo];
  var rough = span / count;
  var pow = Math.pow(10, Math.floor(Math.log10(rough)));
  var err = rough / pow;
  var nice = err < 1.5 ? 1 : err < 3 ? 2 : err < 7 ? 5 : 10;
  var step = nice * pow;
  var start = Math.ceil((lo - step * 1e-9) / step) * step;
  var ticks = [];
  for (var value = start; value <= hi + step * 1e-6; value += step) ticks.push(value);
  return ticks;
};

Lab.sampleRows = function (rows) {
  if (rows.length <= 300) return rows;
  var step = Math.ceil(rows.length / 300);
  var sampled = [];
  for (var i = 0; i < rows.length; i += step) sampled.push(rows[i]);
  sampled.push(rows[rows.length - 1]);
  return sampled;
};

Lab.drawSeries = function (canvas, point, spec) {
  var view = Lab.fit(canvas);
  var ctx = view.ctx;
  ctx.clearRect(0, 0, view.width, view.height);
  ctx.fillStyle = "#f7f9fb";
  ctx.fillRect(0, 0, view.width, view.height);
  if (!point.ok) {
    ctx.fillStyle = "#922b21";
    ctx.font = "14px Segoe UI, sans-serif";
    ctx.fillText(point.error, 16, 28);
    return;
  }
  var rows = Lab.sampleRows(point.rows);
  var left = 58;
  var right = view.width - (spec.rightPad || 16);
  var top = spec.legend ? 48 : 36;
  var bottom = view.height - 32;
  var tMax = rows[rows.length - 1].t;
  var yMax = 0;
  var yMax2 = 0;
  rows.forEach(function (row) {
    yMax = Math.max(yMax, spec.y(row));
    if (spec.y2) yMax2 = Math.max(yMax2, spec.y2(row));
  });
  if (!(tMax > 0) || !(yMax > 0)) return;
  var xOf = function (time) { return left + (time / tMax) * (right - left); };
  var yOf = function (value) { return bottom - (value / yMax) * (bottom - top); };
  var yOf2 = function (value) { return bottom - (value / yMax2) * (bottom - top); };
  ctx.strokeStyle = "#d5d8dc";
  ctx.lineWidth = 1;
  ctx.font = "11px Segoe UI, sans-serif";
  ctx.fillStyle = "#34495e";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  Lab.niceTicks(0, yMax, 4).forEach(function (tick) {
    var y = yOf(tick);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
    ctx.stroke();
    ctx.fillText(Lab.trim(tick), left - 6, y);
  });
  if (spec.y2) {
    ctx.textAlign = "left";
    Lab.niceTicks(0, yMax2, 4).forEach(function (tick) {
      ctx.fillText(Lab.trim(tick), right + 6, yOf2(tick));
    });
  }
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  Lab.niceTicks(0, tMax, 5).forEach(function (tick) {
    ctx.fillText(Lab.trim(tick), xOf(tick), bottom + 6);
  });
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(left, top);
  ctx.lineTo(left, bottom);
  ctx.lineTo(right, bottom);
  ctx.stroke();
  ctx.fillStyle = "#1b2631";
  ctx.font = "13px Segoe UI, sans-serif";
  ctx.fillText(spec.title, (left + right) / 2, 8);
  if (spec.legend) {
    ctx.font = "12px Segoe UI, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    var gap = 18;
    var widths = spec.legend.map(function (item) { return ctx.measureText(item.name).width + 22; });
    var total = widths.reduce(function (sum, width) { return sum + width; }, 0) + gap * (spec.legend.length - 1);
    var legendX = (left + right) / 2 - total / 2;
    spec.legend.forEach(function (item, index) {
      ctx.strokeStyle = item.color;
      ctx.lineWidth = 2.4;
      ctx.beginPath();
      ctx.moveTo(legendX, 28);
      ctx.lineTo(legendX + 16, 28);
      ctx.stroke();
      ctx.fillStyle = "#1b2631";
      ctx.fillText(item.name, legendX + 20, 28);
      legendX += widths[index] + gap;
    });
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
  }
  ctx.font = "12px Segoe UI, sans-serif";
  ctx.fillText("time, s", (left + right) / 2, view.height - 14);
  ctx.save();
  ctx.translate(14, (top + bottom) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(spec.ylabel, 0, 0);
  ctx.restore();
  function stroke(color, reader, mapY) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    rows.forEach(function (row, index) {
      var x = xOf(row.t);
      var y = mapY(reader(row));
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  stroke(spec.color, spec.y, yOf);
  if (spec.y2) stroke(spec.color2, spec.y2, yOf2);
  if (spec.mark) {
    var mark = spec.mark(point);
    ctx.fillStyle = "#922b21";
    ctx.beginPath();
    ctx.arc(xOf(mark.t), yOf(mark.y), 4, 0, Math.PI * 2);
    ctx.fill();
  }
};

Lab.drawPath = function (point) {
  Lab.drawSeries(document.getElementById("path"), point, {
    title: "altitude and speed",
    ylabel: "altitude, km",
    color: "#1a5276",
    color2: "#9a7d0a",
    legend: [
      { name: "altitude, km", color: "#1a5276" },
      { name: "speed, km/s", color: "#9a7d0a" }
    ],
    rightPad: 52,
    y: function (row) { return row.z / 1000; },
    y2: function (row) { return row.v / 1000; }
  });
};

Lab.drawQ = function (point) {
  Lab.drawSeries(document.getElementById("qchart"), point, {
    title: "dynamic pressure",
    ylabel: "q, kPa",
    color: "#1a5276",
    y: function (row) { return row.q / 1000; },
    mark: function (item) { return { t: item.tMax, y: item.qMax / 1000 }; }
  });
};

Lab.renderReadout = function (point) {
  var status = document.getElementById("status");
  var readout = document.getElementById("readout");
  if (!point.ok) {
    status.textContent = point.error;
    readout.innerHTML = "";
    return;
  }
  var settled = point.settled ? "Settled in " + point.passes + " passes." : "Stopped after " + point.passes + " passes.";
  status.textContent = settled + " Design delta-v uses the ascent gravity and drag losses. Steering loss is 0. The LEO radius is " +
    Lab.trim(Lab.R0 / 1000) + " km and the ascent radius is " + Lab.trim(Lab.R_EARTH / 1000) + " km." +
    (point.warning ? " " + point.warning : "");
  var stages = point.stages.map(function (stage, index) {
    var replaced = Math.abs(stage.inert - stage.inertSplit) > 1e-6;
    return "<p>mp " + Lab.trim(stage.mp) + " kg</p><p>inert " + Lab.trim(stage.inert) + " kg" +
      (replaced ? " (split " + Lab.trim(stage.inertSplit) + " kg)" : "") + "</p><p>ideal slice " +
      Lab.trim(stage.dv) + " m/s</p>";
  }).map(function (html, index) {
    return "<section><h3>Stage " + (index + 1) + "</h3>" + html + "</section>";
  }).join("");
  readout.innerHTML = "<section><h3>Vehicle</h3>" +
    "<p>design delta-v: " + Lab.trim(point.dvDesign) + " m/s</p>" +
    "<p>flown vacuum delta-v: " + Lab.trim(point.dvIdeal) + " m/s</p>" +
    "<p>circular speed: " + Lab.trim(point.vCirc) + " m/s</p>" +
    "<p>gravity loss: " + Lab.trim(point.gravity) + " m/s</p>" +
    "<p>drag loss: " + Lab.trim(point.drag) + " m/s</p>" +
    "<p>margin: " + Lab.trim(point.margin) + " m/s</p>" +
    "<p>payload: " + Lab.trim(point.payload) + " kg</p>" +
    "<p>stacked mass: " + Lab.trim(point.stacked) + " kg</p>" +
    "<p>burnout altitude: " + Lab.trim(point.Zbo) + " m</p>" +
    "<p>burnout speed: " + Lab.trim(point.Vbo) + " m/s</p>" +
    "<p>q max: " + Lab.trim(point.qMax) + " Pa at " + Lab.trim(point.tMax) + " s, " + Lab.trim(point.zMax) + " m</p>" +
    "</section>" + stages;
};

Lab.line = function (key, value) {
  return key + ": " + (typeof value === "number" ? Lab.trim(value) : value);
};

Lab.parameterText = function (seed, point) {
  if (!point.ok) return point.error;
  var lines = [
    Lab.line("stages", seed.count),
    Lab.line("payload_kg", point.payload),
    Lab.line("path", seed.path)
  ];
  if (seed.path === "gamma") lines.push(Lab.line("gamma_rad", seed.gamma));
  else lines.push(Lab.line("kick_rad", seed.kick));
  if (seed.cd > 0) {
    lines.push(Lab.line("cd", seed.cd));
    lines.push(Lab.line("area_m2", seed.area));
  }
  if (seed.jettison) {
    lines.push(Lab.line("jettison_mass_kg", seed.jetMass));
    if (seed.jetBy === "time") lines.push(Lab.line("jettison_time_s", seed.jetTime));
    else lines.push(Lab.line("jettison_alt_m", seed.jetAlt));
  }
  point.stages.forEach(function (stage, index) {
    lines.push(
      "",
      "stage " + (index + 1),
      Lab.line("mp_kg", stage.mp),
      Lab.line("inert_kg", stage.inert),
      Lab.line("isp_s", stage.isp),
      Lab.line("tb_s", stage.tb)
    );
  });
  return lines.join("\n");
};

Lab.refresh = function () {
  var seed = Lab.readSeed();
  Lab.applyMode(seed);
  var point = Lab.designPoint(seed);
  Lab.renderReadout(point);
  document.getElementById("parameters").value = Lab.parameterText(seed, point);
  Lab.drawPath(point);
  Lab.drawQ(point);
};

Lab.boot = function (seed) {
  Lab.writeSeed(seed);
  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(function () {
      queued = false;
      Lab.refresh();
    });
  }
  document.getElementById("app").addEventListener("input", schedule);
  document.getElementById("app").addEventListener("change", schedule);
  window.addEventListener("resize", schedule);
  Lab.refresh();
};
