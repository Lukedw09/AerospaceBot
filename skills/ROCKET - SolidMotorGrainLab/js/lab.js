/* Wire the grain calculation and, in a browser, the solid-motor lab page. */
var Lab = Lab || {};

Lab.need = function (value, message) {
  if (typeof value !== "number" || !isFinite(value)) throw new Error(message);
  return value;
};

Lab.positive = function (value, message) {
  var number = Lab.need(value, message);
  if (!(number > 0)) throw new Error(message);
  return number;
};

Lab.computeDesign = function (seed) {
  try {
    return Lab.evaluate(seed);
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
};

Lab.evaluate = function (seed) {
  var web = Lab.positive(seed.web, "web must be finite and > 0");
  var port = Lab.positive(seed.port, "port radius must be finite and > 0");
  var kn = Lab.positive(seed.kn, "Kn must be finite and > 0");
  var length = Lab.positive(seed.length, "grain length must be finite and > 0");
  var a = Lab.positive(seed.a, "burn-rate coefficient must be finite and > 0");
  var n = Lab.need(seed.n, "burn-rate exponent n must be finite and < 1");
  var rho = Lab.positive(seed.rho, "propellant density must be finite and > 0");
  var cstar = Lab.positive(seed.cstar, "c* must be finite and > 0");
  var thickness = Lab.positive(seed.thickness, "wall thickness must be finite and > 0");
  var allowable = Lab.positive(seed.allowable, "allowable stress must be finite and > 0");
  var sliverPercent = Lab.need(seed.sliver, "sliver percent must be finite and in [0, 100)");
  if (!(n < 1)) throw new Error("burn-rate exponent n must be finite and < 1");
  if (!(sliverPercent >= 0) || !(sliverPercent < 100)) {
    throw new Error("sliver percent must be finite and in [0, 100)");
  }
  var outer = port + web;
  if (!(outer > port)) throw new Error("outer propellant radius must be > port radius");
  var sliver = sliverPercent / 100;
  var ab0 = Lab.circularPortBurningArea(port, length);
  var throat = ab0 / kn;
  var hist = Lab.grainHistory(a, n, throat, rho, cstar, port, length, outer, sliver);
  var hoop = [];
  var margin = [];
  var iMax = 0;
  for (var i = 0; i < hist.pc.length; i += 1) {
    hoop.push(Lab.hoopStress(hist.pc[i], outer, thickness));
    margin.push(Lab.marginOfSafety(allowable, hoop[i]));
    if (hist.pc[i] > hist.pc[iMax]) iMax = i;
  }
  return {
    ok: true,
    error: null,
    web: web,
    port: port,
    kn: kn,
    length: length,
    a: a,
    n: n,
    rho: rho,
    cstar: cstar,
    thickness: thickness,
    allowable: allowable,
    sliver: sliver,
    sliverPercent: sliverPercent,
    Ro: outer,
    At: throat,
    Ab0: ab0,
    w0: hist.web0,
    tBurn: hist.tBurn,
    KInitial: hist.K[0],
    KBurnout: hist.K[hist.K.length - 1],
    pcInitial: hist.pc[0],
    pcBurnout: hist.pc[hist.pc.length - 1],
    pcMax: hist.pc[iMax],
    wremBurnout: hist.wEnd,
    AbBurnout: hist.Ab[hist.Ab.length - 1],
    rEnd: hist.rEnd,
    hoopMax: hoop[iMax],
    marginMin: margin[iMax],
    thinWall: Lab.thinWall(outer, thickness),
    tOverR: thickness / outer,
    nSamples: hist.times.length,
    times: hist.times,
    pc: hist.pc,
    Ab: hist.Ab,
    wrem: hist.wrem,
    K: hist.K,
    radius: hist.radius,
    hoop: hoop,
    margin: margin
  };
};

Lab.fmt = function (value) {
  if (value == null || !isFinite(value)) return "—";
  var abs = Math.abs(value);
  if (abs !== 0 && (abs < 1e-3 || abs >= 1e5)) return value.toExponential(4);
  return value.toPrecision(6);
};

Lab.trim = function (value) {
  if (!isFinite(value)) return "";
  return String(Number(value.toPrecision(8)));
};

Lab.exportText = function (seed, result) {
  if (!result.ok) return result.error;
  var lines = [
    "Ro_m: " + result.Ro,
    "At_m2: " + result.At,
    "Ab0_m2: " + result.Ab0,
    "Kn: " + result.kn,
    "t_burn_s: " + result.tBurn,
    "pc_initial_Pa: " + result.pcInitial,
    "pc_max_Pa: " + result.pcMax,
    "wrem_burnout_m: " + result.wremBurnout,
    "margin_min: " + result.marginMin,
    "",
    "ROCKET - CircularPortGrainHistory",
    "--a " + Lab.trim(result.a) + " --n " + Lab.trim(result.n)
      + " --port " + Lab.trim(result.port) + " --length " + Lab.trim(result.length)
      + " --outer " + Lab.trim(result.Ro) + " --throat " + Lab.trim(result.At)
      + " --rho " + Lab.trim(result.rho) + " --cstar " + Lab.trim(result.cstar)
      + (result.sliverPercent > 0 ? " --sliver " + Lab.trim(result.sliverPercent) : ""),
    "",
    "ROCKET - SolidMotorParameters",
    "--a " + Lab.trim(result.a) + " --n " + Lab.trim(result.n)
      + " --ab " + Lab.trim(result.Ab0) + " --throat " + Lab.trim(result.At)
      + " --rho " + Lab.trim(result.rho) + " --cstar " + Lab.trim(result.cstar),
    "",
    "ROCKET - ChamberVolumeAndCaseHoopStress",
    "# pc is the peak chamber pressure. Add --lstar; this lab does not compute L*.",
    "--throat " + Lab.trim(result.At) + " --pc " + Lab.trim(result.pcMax)
      + " --radius " + Lab.trim(result.Ro) + " --thickness " + Lab.trim(result.thickness)
      + " --allowable " + Lab.trim(result.allowable)
  ];
  return lines.join("\n");
};

Lab.series = function (canvas, xs, ys, ylabel, color) {
  var ctx = canvas.getContext("2d");
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var w = canvas.clientWidth || 320;
  var h = canvas.clientHeight || 220;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#f7f9fb";
  ctx.fillRect(0, 0, w, h);
  var padL = 58;
  var padR = 12;
  var padT = 16;
  var padB = 32;
  var x0 = xs[0];
  var x1 = xs[xs.length - 1];
  var yMin = ys[0];
  var yMax = ys[0];
  for (var i = 1; i < ys.length; i += 1) {
    if (ys[i] < yMin) yMin = ys[i];
    if (ys[i] > yMax) yMax = ys[i];
  }
  if (yMax === yMin) {
    yMax += 1;
    yMin -= 1;
  }
  var plotW = Math.max(w - padL - padR, 1);
  var plotH = Math.max(h - padT - padB, 1);
  function X(x) { return padL + (x - x0) / Math.max(x1 - x0, 1e-15) * plotW; }
  function Y(y) { return padT + (yMax - y) / (yMax - yMin) * plotH; }
  ctx.strokeStyle = "#d5d8dc";
  ctx.lineWidth = 1;
  ctx.strokeRect(padL, padT, plotW, plotH);
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.8;
  ctx.moveTo(X(xs[0]), Y(ys[0]));
  for (var j = 1; j < xs.length; j += 1) ctx.lineTo(X(xs[j]), Y(ys[j]));
  ctx.stroke();
  ctx.fillStyle = "#1b2631";
  ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
  ctx.fillText(ylabel, 8, 14);
  ctx.fillText("t [s]", padL, h - 8);
  ctx.font = "11px Segoe UI, Helvetica, Arial, sans-serif";
  ctx.fillText(Lab.fmt(yMax), 4, padT + 12);
  ctx.fillText(Lab.fmt(yMin), 4, padT + plotH);
  ctx.fillText(Lab.fmt(x1), padL + plotW - 48, h - 8);
};

Lab.fit = function (canvas) {
  var ctx = canvas.getContext("2d");
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var w = canvas.clientWidth || 320;
  var h = canvas.clientHeight || 220;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#f7f9fb";
  ctx.fillRect(0, 0, w, h);
  return { ctx: ctx, w: w, h: h };
};

Lab.drawLateral = function (canvas, result) {
  var view = Lab.fit(canvas);
  if (!result || !result.ok) return;
  var ctx = view.ctx;
  var outer = result.Ro + result.thickness;
  var pad = 28;
  var scale = Math.min(view.w, view.h) / 2 - pad;
  scale = scale / Math.max(outer, 1e-9);
  var cx = view.w / 2;
  var cy = view.h / 2;
  function circle(radius, fill) {
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(radius * scale, 0), 0, 2 * Math.PI);
    ctx.fillStyle = fill;
    ctx.fill();
  }
  circle(outer, "#1b2631");
  circle(result.Ro, "#c4a574");
  circle(result.port, "#f7f9fb");
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.arc(cx, cy, result.Ro * scale, 0, 2 * Math.PI);
  ctx.stroke();
  ctx.fillStyle = "#1b2631";
  ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
  ctx.fillText("Rp " + Lab.fmt(result.port) + " m", cx + 6, cy - result.port * scale * 0.35);
  ctx.fillText("web " + Lab.fmt(result.web) + " m", cx + 6, cy - (result.port + result.Ro) * scale * 0.5);
};

Lab.drawLongitudinal = function (canvas, result) {
  var view = Lab.fit(canvas);
  if (!result || !result.ok) return;
  var ctx = view.ctx;
  var length = result.length;
  var outer = result.Ro + result.thickness;
  var pad = 24;
  var scale = Math.min(
    (view.w - 2 * pad) / Math.max(length, 1e-9),
    (view.h - 2 * pad) / Math.max(2 * outer, 1e-9)
  );
  var ox = (view.w - length * scale) / 2;
  var oy = view.h / 2;
  function X(x) { return ox + x * scale; }
  function Y(r) { return oy - r * scale; }
  function band(r0, r1, fill) {
    ctx.fillStyle = fill;
    ctx.fillRect(X(0), Y(r1), length * scale, (r1 - r0) * scale);
  }
  band(-outer, outer, "#1b2631");
  band(-result.Ro, result.Ro, "#c4a574");
  band(-result.port, result.port, "#f7f9fb");
  var cap = Math.min(0.03 * length, 0.02);
  ctx.fillStyle = "#7b241c";
  ctx.fillRect(X(0), Y(result.Ro), cap * scale, (result.Ro - result.port) * scale);
  ctx.fillRect(X(0), Y(-result.port), cap * scale, (result.Ro - result.port) * scale);
  ctx.fillRect(X(length - cap), Y(result.Ro), cap * scale, (result.Ro - result.port) * scale);
  ctx.fillRect(X(length - cap), Y(-result.port), cap * scale, (result.Ro - result.port) * scale);
  ctx.strokeStyle = "#7f8c8d";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(X(0), oy);
  ctx.lineTo(X(length), oy);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#1b2631";
  ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
  ctx.fillText("L " + Lab.fmt(length) + " m", X(length * 0.35), Y(-outer) - 6);
  ctx.fillText("inhibited ends", X(0), view.h - 8);
};

if (typeof document !== "undefined") {
  Lab.boot = function () {
    var seed = JSON.parse(document.getElementById("seed-json").textContent);
    Lab.form = {
      web: document.getElementById("web"),
      webRange: document.getElementById("web-range"),
      port: document.getElementById("port"),
      portRange: document.getElementById("port-range"),
      kn: document.getElementById("kn"),
      knRange: document.getElementById("kn-range"),
      length: document.getElementById("length"),
      a: document.getElementById("a"),
      n: document.getElementById("n"),
      rho: document.getElementById("rho"),
      cstar: document.getElementById("cstar"),
      thickness: document.getElementById("thickness"),
      allowable: document.getElementById("allowable"),
      sliver: document.getElementById("sliver")
    };
    Lab.form.web.value = seed.web;
    Lab.form.port.value = seed.port;
    Lab.form.kn.value = seed.kn;
    Lab.form.length.value = seed.length;
    Lab.form.a.value = seed.a;
    Lab.form.n.value = seed.n;
    Lab.form.rho.value = seed.rho;
    Lab.form.cstar.value = seed.cstar;
    Lab.form.thickness.value = seed.thickness;
    Lab.form.allowable.value = seed.allowable;
    Lab.form.sliver.value = seed.sliver;
    Lab.syncRanges();
    Lab.bind();
    Lab.refresh();
    window.addEventListener("resize", function () { Lab.draw(Lab.last); });
  };

  Lab.syncRanges = function () {
    Lab.mirror(Lab.form.webRange, Lab.form.web);
    Lab.mirror(Lab.form.portRange, Lab.form.port);
    Lab.mirror(Lab.form.knRange, Lab.form.kn);
  };

  Lab.mirror = function (range, number) {
    var value = Number(number.value);
    if (!isFinite(value)) return;
    var min = Number(range.min);
    var max = Number(range.max);
    range.value = Math.min(max, Math.max(min, value));
  };

  Lab.readSeed = function () {
    return {
      web: Number(Lab.form.web.value),
      port: Number(Lab.form.port.value),
      kn: Number(Lab.form.kn.value),
      length: Number(Lab.form.length.value),
      a: Number(Lab.form.a.value),
      n: Number(Lab.form.n.value),
      rho: Number(Lab.form.rho.value),
      cstar: Number(Lab.form.cstar.value),
      thickness: Number(Lab.form.thickness.value),
      allowable: Number(Lab.form.allowable.value),
      sliver: Number(Lab.form.sliver.value)
    };
  };

  Lab.refresh = function () {
    Lab.syncRanges();
    var result = Lab.computeDesign(Lab.readSeed());
    Lab.last = result;
    Lab.paint(result);
    Lab.draw(result);
    document.getElementById("export").value = Lab.exportText(Lab.readSeed(), result);
  };

  Lab.row = function (label, value) {
    return "<div><dt>" + label + "</dt><dd>" + value + "</dd></div>";
  };

  Lab.paint = function (result) {
    var status = document.getElementById("status");
    var readout = document.getElementById("readout");
    if (!result.ok) {
      status.textContent = result.error;
      readout.innerHTML = "";
      return;
    }
    var notes = [];
    notes.push("Sections are the ignition geometry. Curves run from ignition to the sliver stop.");
    if (result.thinWall === "no") {
      notes.push("Case t/R is not below 0.1; thin-wall hoop stress is outside its usual range.");
    }
    if (result.marginMin < 0) notes.push("Case margin is negative at peak chamber pressure.");
    status.textContent = notes.join(" ");
    readout.innerHTML = [
      Lab.row("Ro [m]", Lab.fmt(result.Ro)),
      Lab.row("At [m²]", Lab.fmt(result.At)),
      Lab.row("Ab0 [m²]", Lab.fmt(result.Ab0)),
      Lab.row("Kn", Lab.fmt(result.kn)),
      Lab.row("K burnout", Lab.fmt(result.KBurnout)),
      Lab.row("burn time [s]", Lab.fmt(result.tBurn)),
      Lab.row("pc initial [Pa]", Lab.fmt(result.pcInitial)),
      Lab.row("pc max [Pa]", Lab.fmt(result.pcMax)),
      Lab.row("pc burnout [Pa]", Lab.fmt(result.pcBurnout)),
      Lab.row("Ab burnout [m²]", Lab.fmt(result.AbBurnout)),
      Lab.row("web left [m]", Lab.fmt(result.wremBurnout)),
      Lab.row("hoop at pc max [Pa]", Lab.fmt(result.hoopMax)),
      Lab.row("MS at pc max", Lab.fmt(result.marginMin)),
      Lab.row("thin wall", result.thinWall),
      Lab.row("sliver [%]", Lab.fmt(result.sliverPercent))
    ].join("");
  };

  Lab.draw = function (result) {
    Lab.drawLateral(document.getElementById("lateral"), result);
    Lab.drawLongitudinal(document.getElementById("longitudinal"), result);
    var pc = document.getElementById("pc-plot");
    var ab = document.getElementById("ab-plot");
    if (!result || !result.ok) {
      Lab.fit(pc);
      Lab.fit(ab);
      return;
    }
    Lab.series(pc, result.times, result.pc, "pc [Pa]", "#1a5276");
    Lab.series(ab, result.times, result.Ab, "Ab [m²]", "#117a65");
  };

  Lab.bindPair = function (range, number) {
    range.addEventListener("input", function () {
      number.value = range.value;
      Lab.refresh();
    });
    number.addEventListener("input", function () {
      Lab.refresh();
    });
  };

  Lab.bind = function () {
    Lab.bindPair(Lab.form.webRange, Lab.form.web);
    Lab.bindPair(Lab.form.portRange, Lab.form.port);
    Lab.bindPair(Lab.form.knRange, Lab.form.kn);
    ["length", "a", "n", "rho", "cstar", "thickness", "allowable", "sliver"].forEach(function (id) {
      document.getElementById(id).addEventListener("input", Lab.refresh);
    });
  };

  Lab.boot();
}
