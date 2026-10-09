/* Live wing and airfoil page. Chart lift when Report 824 has the section; otherwise thin airfoil. */
var Lab = Lab || {};

Lab.N_CURVE = 81;
Lab.TWO_PI = 2 * Math.PI;

Lab.trim = function (value) {
  if (value == null || !isFinite(value)) return "";
  return String(Number(value.toPrecision(8)));
};

Lab.formatRe = function (re) {
  if (re >= 1e6) {
    var millions = Math.round((re / 1e6) * 100) / 100;
    return String(millions) + "e6";
  }
  return Lab.trim(re);
};

Lab.profileAt = function (source, polar, cl, cd0) {
  if (source !== "report824") return { cd: cd0, clamped: false };
  var lo = polar.cl_polar[0];
  var hi = polar.cl_polar[polar.cl_polar.length - 1];
  var clamped = cl < lo || cl > hi;
  var query = Math.min(Math.max(cl, lo), hi);
  return { cd: Lab.lerp(query, polar.cl_polar, polar.cd), clamped: clamped };
};

Lab.designPoint = function (seed, pack) {
  var digits = Lab.parseNaca(seed.naca);
  var found = Lab.polarFor(pack, digits.designation, seed.re == null ? null : seed.re);
  var source = found ? "report824" : "thin_airfoil";
  var polar = found ? found.polar : null;
  var reSource = found ? found.source : "n/a";
  var reValue = found ? found.polar.Re : null;
  var plan = Lab.planform(seed.span, seed.root, seed.tip, seed.sweep, seed.sweepAt, !!seed.sweepAtGiven);
  if (!(seed.e > 0) || seed.e > 1) throw new Error("span efficiency must satisfy 0 < e <= 1");
  if (!isFinite(seed.alpha)) throw new Error("angle of attack must be finite");
  var sweepRad = plan.sweep == null ? 0 : plan.sweep;
  var alphaL0;
  var a0;
  var clmax;
  if (source === "report824") {
    var alphaL0Deg = Lab.zeroLiftDeg(polar);
    alphaL0 = alphaL0Deg * Math.PI / 180;
    a0 = Lab.measuredA0(polar, alphaL0Deg);
    clmax = Lab.clMax(polar).cl;
  } else {
    if (!(seed.cd0 >= 0) || !isFinite(seed.cd0)) throw new Error("zero-lift drag must be finite and >= 0");
    if (!(seed.clmaxTheory > 0) || !isFinite(seed.clmaxTheory)) throw new Error("section CLmax must be finite and > 0");
    alphaL0 = Lab.zeroLiftThin(digits.m, digits.p);
    a0 = Lab.TWO_PI;
    clmax = seed.clmaxTheory;
  }
  if (!(a0 > 0)) throw new Error("section slope must be > 0");
  if (!(clmax > 0)) throw new Error("maximum lift coefficient must be > 0");
  var a0Eff = a0 * Math.cos(sweepRad);
  if (!(a0Eff > 0)) throw new Error("effective section slope must be > 0");
  var a = Lab.wingSlope(a0Eff, plan.aspectRatio, seed.e);
  var alphaStall = Lab.stallAngle(alphaL0, clmax, a);
  var stalled = seed.alpha >= alphaStall;
  var cl = stalled ? clmax : Lab.wingLift(a, seed.alpha, alphaL0);
  var profile = Lab.profileAt(source, polar, cl, seed.cd0);
  var cdi = Lab.inducedDrag(cl, plan.aspectRatio, seed.e);
  var sectionCl = null;
  if (source === "report824") {
    sectionCl = Lab.clAt(polar, seed.alpha * 180 / Math.PI);
  } else {
    sectionCl = Lab.TWO_PI * (seed.alpha - alphaL0);
    if (sectionCl > clmax) sectionCl = clmax;
  }
  var curve = Lab.curves(source, polar, alphaL0, a, clmax, plan.aspectRatio, seed.e, seed.cd0);
  return {
    ok: true,
    data_source: source,
    re_source: reSource,
    designation: digits.designation,
    Re: reValue,
    span: plan.span,
    root: plan.root,
    tip: plan.tip,
    area: plan.area,
    aspectRatio: plan.aspectRatio,
    taper: plan.taper,
    mac: plan.mac,
    yMac: plan.yMac,
    sweep: plan.sweep,
    sweepAt: plan.sweepAt,
    sweepAtSource: plan.sweepAtSource,
    sweepLe: plan.sweepLe,
    xLeMac: plan.xLeMac,
    a0: a0,
    a0Eff: a0Eff,
    a: a,
    alphaL0: alphaL0,
    CLmax: clmax,
    e: seed.e,
    CD0: source === "thin_airfoil" ? seed.cd0 : null,
    alpha: seed.alpha,
    alphaStall: alphaStall,
    stalled: stalled,
    CL: cl,
    CDi: cdi,
    cd: profile.cd,
    CD: profile.cd + cdi,
    cdClamped: profile.clamped,
    alphaI: cl / (Math.PI * plan.aspectRatio * seed.e),
    sectionCl: sectionCl,
    curve: curve,
    stations: Lab.sectionStations(digits, 81)
  };
};

Lab.curves = function (source, polar, alphaL0, slope, clmax, ar, e, cd0) {
  var alphaStall = Lab.stallAngle(alphaL0, clmax, slope);
  var span = alphaStall - alphaL0;
  var alphaDeg = [];
  var lift = [];
  var cd = [];
  var induced = [];
  var total = [];
  var i;
  for (i = 0; i < Lab.N_CURVE; i += 1) {
    var alpha = alphaL0 + span * i / (Lab.N_CURVE - 1);
    var cl = Lab.wingLift(slope, alpha, alphaL0);
    var profile = Lab.profileAt(source, polar, cl, cd0);
    var cdi = Lab.inducedDrag(cl, ar, e);
    alphaDeg.push(alpha * 180 / Math.PI);
    lift.push(cl);
    cd.push(profile.cd);
    induced.push(cdi);
    total.push(profile.cd + cdi);
  }
  var sectionAlpha = [];
  var sectionCl = [];
  if (source === "report824") {
    for (i = 0; i < polar.alpha_deg.length; i += 1) {
      sectionAlpha.push(polar.alpha_deg[i]);
      sectionCl.push(polar.cl[i]);
    }
  } else {
    var sectionStall = alphaL0 + clmax / Lab.TWO_PI;
    var sectionSpan = sectionStall - alphaL0;
    for (i = 0; i < Lab.N_CURVE; i += 1) {
      var sa = alphaL0 + sectionSpan * i / (Lab.N_CURVE - 1);
      sectionAlpha.push(sa * 180 / Math.PI);
      sectionCl.push(Lab.wingLift(Lab.TWO_PI, sa, alphaL0));
    }
  }
  return {
    alphaDeg: alphaDeg,
    CL: lift,
    cd: cd,
    CDi: induced,
    CD: total,
    sectionAlphaDeg: sectionAlpha,
    sectionCl: sectionCl
  };
};

Lab.evaluate = function (seed, pack) {
  try {
    return Lab.designPoint(seed, pack);
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
};

Lab.boot = function (seed, pack) {
  if (typeof document === "undefined") return;
  var naca = document.getElementById("naca");
  var re = document.getElementById("re");
  var reRange = document.getElementById("re-range");
  var reNote = document.getElementById("re-note");
  var sweep = document.getElementById("sweep");
  var sweepAt = document.getElementById("sweep-at");
  var cd0 = document.getElementById("cd0");
  var clmax = document.getElementById("clmax");
  var alpha = document.getElementById("alpha");
  var status = document.getElementById("status");
  var readout = document.getElementById("readout");
  var exportBox = document.getElementById("export");
  var theoryNote = document.getElementById("theory-note");
  var shape = document.getElementById("shape");
  var curves = document.getElementById("curves");
  var reDirty = seed.re != null;
  var writing = false;
  var stops = [];

  var pairs = [
    ["span", "span-range"],
    ["root", "root-range"],
    ["tip", "tip-range"],
    ["sweep", "sweep-range"],
    ["eff", "eff-range"],
    ["cd0", "cd0-range"],
    ["clmax", "clmax-range"],
    ["alpha", "alpha-range"]
  ];

  function setNumber(id, value) {
    document.getElementById(id).value = Lab.trim(value);
  }

  function applySeed() {
    naca.value = seed.naca;
    setNumber("span", seed.span);
    setNumber("root", seed.root);
    setNumber("tip", seed.tip);
    setNumber("sweep", seed.sweep == null ? 0 : seed.sweep * 180 / Math.PI);
    sweepAt.value = seed.sweepAtGiven ? String(seed.sweepAt) : "";
    setNumber("eff", seed.e);
    setNumber("cd0", seed.cd0);
    setNumber("clmax", seed.clmaxTheory);
    setNumber("alpha", seed.alpha * 180 / Math.PI);
    re.value = seed.re == null ? "" : Lab.trim(seed.re);
    pairs.forEach(function (pair) {
      var number = document.getElementById(pair[0]);
      var range = document.getElementById(pair[1]);
      var value = Number(number.value);
      if (isFinite(value)) {
        range.value = String(Math.min(Number(range.max), Math.max(Number(range.min), value)));
      }
    });
  }

  function currentStops(designation) {
    try {
      var digits = Lab.parseNaca(designation);
      var curves = Lab.chartList(pack, digits.designation);
      if (!curves) return null;
      return curves.map(function (item) { return item.Re; });
    } catch (err) {
      return null;
    }
  }

  function log10(value) {
    return Math.log(value) / Math.LN10;
  }

  function snapReynolds(value) {
    if (!stops.length || !isFinite(value) || !(value > 0)) return value;
    var best = stops[0];
    var bestDist = Math.abs(log10(value) - log10(best));
    var i;
    for (i = 1; i < stops.length; i += 1) {
      var dist = Math.abs(log10(value) - log10(stops[i]));
      if (dist < bestDist) {
        bestDist = dist;
        best = stops[i];
      }
    }
    var gap = Infinity;
    for (i = 0; i < stops.length; i += 1) {
      if (stops[i] === best) continue;
      gap = Math.min(gap, Math.abs(log10(stops[i]) - log10(best)));
    }
    var threshold = isFinite(gap) ? 0.22 * gap : 0.03;
    if (bestDist <= threshold) return best;
    return value;
  }

  function placeReSlider(value) {
    if (!stops.length || !isFinite(value) || !(value > 0)) return;
    var pos = log10(value);
    var lo = Number(reRange.min);
    var hi = Number(reRange.max);
    if (pos < lo) pos = lo;
    if (pos > hi) pos = hi;
    reRange.value = String(pos);
  }

  function rebuildStops() {
    var next = currentStops(naca.value);
    var chart = !!next;
    re.disabled = !chart;
    reRange.disabled = !chart;
    if (!chart) {
      stops = [];
      reNote.textContent = "No Report 824 chart. Reynolds number is not used.";
      return;
    }
    stops = next;
    reRange.min = String(log10(stops[0]));
    reRange.max = String(log10(stops[stops.length - 1]));
    reRange.step = "0.001";
    reNote.textContent = "Chart Re: " + stops.map(Lab.formatRe).join(", ");
    var shown = Number(re.value);
    if (!isFinite(shown)) {
      placeReSlider(pack.defaultRe || Lab.DEFAULT_RE);
      return;
    }
    placeReSlider(shown);
  }

  function readSeed() {
    var sweepDeg = Number(sweep.value);
    var station = sweepAt.value;
    var sweepRad = null;
    var stationValue = null;
    var stationGiven = false;
    if (sweepDeg !== 0 || station !== "") {
      sweepRad = sweepDeg * Math.PI / 180;
      if (station !== "") {
        stationValue = Number(station);
        stationGiven = true;
      }
    }
    var reValue = null;
    if (reDirty && !re.disabled) {
      var text = re.value.trim();
      reValue = text === "" ? null : Number(text);
    } else if (!re.disabled) {
      reValue = seed.re == null ? null : seed.re;
    }
    return {
      naca: naca.value,
      re: reValue,
      span: Number(document.getElementById("span").value),
      root: Number(document.getElementById("root").value),
      tip: Number(document.getElementById("tip").value),
      sweep: sweepRad,
      sweepAt: stationValue,
      sweepAtGiven: stationGiven,
      e: Number(document.getElementById("eff").value),
      cd0: Number(cd0.value),
      clmaxTheory: Number(clmax.value),
      alpha: Number(alpha.value) * Math.PI / 180
    };
  }

  function row(name, value) {
    return "<div><dt>" + name + "</dt><dd>" + value + "</dd></div>";
  }

  function showNumber(value) {
    return value == null || !isFinite(value) ? "n/a" : Lab.trim(value);
  }

  function exportText(result) {
    var nacaLine = "python \"skills/AERO - NACAFourDigitSection/naca_four_digit_section.py\" --naca "
      + result.designation + " --chord " + Lab.trim(result.mac) + " --alpha " + Lab.trim(result.alpha);
    if (result.data_source === "report824" && result.Re != null) nacaLine += " --re " + Lab.trim(result.Re);
    if (result.data_source !== "report824") {
      nacaLine += "\n# no Report 824 chart for this designation; do not run that program for coefficients";
    }
    var wingLine = "python \"skills/AERO - WingGeometry/wing_geometry.py\" --span " + Lab.trim(result.span)
      + " --root " + Lab.trim(result.root) + " --tip " + Lab.trim(result.tip);
    if (result.sweep != null) {
      wingLine += " --sweep " + Lab.trim(result.sweep);
      if (result.sweepAtSource === "given") wingLine += " --sweep-at " + Lab.trim(result.sweepAt);
    }
    var finiteLine = "python \"skills/AERO - FiniteWingLiftCurve/finite_wing_lift_curve.py\" --a0 "
      + Lab.trim(result.a0Eff) + " --alpha-l0 " + Lab.trim(result.alphaL0) + " --clmax " + Lab.trim(result.CLmax)
      + " --ar " + Lab.trim(result.aspectRatio) + " --e " + Lab.trim(result.e);
    return "NACAFourDigitSection\n" + nacaLine
      + "\n\nWingGeometry\n" + wingLine
      + "\n\nFiniteWingLiftCurve\n" + finiteLine
      + "\n# --a0 is a0*cos(sweep).";
  }

  function fit(canvas, height) {
    var rect = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    var w = Math.max(320, rect.width || canvas.clientWidth || 640);
    var h = height;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: w, h: h };
  }

  function drawShape(result) {
    var view = fit(shape, 320);
    var ctx = view.ctx;
    ctx.clearRect(0, 0, view.w, view.h);
    ctx.fillStyle = "#f7f9fb";
    ctx.fillRect(0, 0, view.w, view.h);
    var leftW = view.w * 0.62;
    var half = result.span / 2;
    var tipX = half * Math.tan(result.sweepLe);
    var xs = [0, tipX, tipX + result.tip, result.root, tipX + result.tip, tipX, 0];
    var ys = [0, half, half, 0, -half, -half, 0];
    var xMin = Math.min.apply(null, xs);
    var xMax = Math.max.apply(null, xs);
    var yMax = half;
    var gutter = 64;
    var header = 24;
    var usableH = view.h - header - 12;
    var scale = Math.min((leftW - gutter - 12) / (2 * yMax), usableH / Math.max(xMax - xMin, 0.01));
    var cx = gutter + (leftW - gutter - 12) / 2;
    var top = header + (usableH - (xMax - xMin) * scale) / 2;

    function sx(y) { return cx + y * scale; }
    function sy(x) { return top + (x - xMin) * scale; }

    var arrowX = 30;
    var yFront = sy(xMin);
    var yAft = sy(xMax);
    ctx.strokeStyle = "#922b21";
    ctx.fillStyle = "#922b21";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(arrowX, yFront);
    ctx.lineTo(arrowX, yAft - 8);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(arrowX, yAft);
    ctx.lineTo(arrowX - 5, yAft - 10);
    ctx.lineTo(arrowX + 5, yAft - 10);
    ctx.closePath();
    ctx.fill();
    ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("airflow", arrowX, Math.max(14, yFront - 6));
    ctx.textAlign = "left";

    ctx.beginPath();
    ctx.moveTo(sx(ys[0]), sy(xs[0]));
    for (var i = 1; i < xs.length; i += 1) ctx.lineTo(sx(ys[i]), sy(xs[i]));
    ctx.closePath();
    ctx.fillStyle = "#d6eaf8";
    ctx.strokeStyle = "#1b2631";
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(sx(result.yMac), sy(result.xLeMac));
    ctx.lineTo(sx(result.yMac), sy(result.xLeMac + result.mac));
    ctx.strokeStyle = "#1a5276";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = "#1a5276";
    ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.fillText("MAC", sx(result.yMac) + 6, sy(result.xLeMac + result.mac * 0.5));
    ctx.fillStyle = "#34495e";
    ctx.fillText("NACA " + result.designation + "   AR " + Lab.trim(result.aspectRatio), gutter, 16);

    var panelX = leftW + 16;
    var panelW = view.w - panelX - 16;
    var stations = result.stations;
    var minY = 0;
    var maxY = 0;
    stations.forEach(function (row) {
      minY = Math.min(minY, row.yl);
      maxY = Math.max(maxY, row.yu);
    });
    var chordScale = Math.min(panelW - 24, (view.h - 56) / Math.max(maxY - minY, 0.05));
    var ox = panelX + (panelW - chordScale) / 2;
    var oy = view.h * 0.55;
    ctx.beginPath();
    stations.forEach(function (row, index) {
      var px = ox + row.xu * chordScale;
      var py = oy - row.yu * chordScale;
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    for (var k = stations.length - 1; k >= 0; k -= 1) {
      ctx.lineTo(ox + stations[k].xl * chordScale, oy - stations[k].yl * chordScale);
    }
    ctx.closePath();
    ctx.fillStyle = "#eaf2f8";
    ctx.strokeStyle = "#1b2631";
    ctx.lineWidth = 1.4;
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#34495e";
    ctx.fillText("section at MAC  " + Lab.trim(result.mac) + " m", panelX, 18);
  }

  function polyline(ctx, xs, ys, x0, x1, y0, y1, left, right, top, bottom) {
    ctx.beginPath();
    for (var i = 0; i < xs.length; i += 1) {
      var px = left + (xs[i] - x0) / (x1 - x0) * (right - left);
      var py = bottom - (ys[i] - y0) / (y1 - y0) * (bottom - top);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }

  function marker(ctx, x, y, x0, x1, y0, y1, left, right, top, bottom) {
    var px = left + (x - x0) / (x1 - x0) * (right - left);
    var py = bottom - (y - y0) / (y1 - y0) * (bottom - top);
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawCurves(result) {
    var view = fit(curves, 320);
    var ctx = view.ctx;
    ctx.clearRect(0, 0, view.w, view.h);
    ctx.fillStyle = "#f7f9fb";
    ctx.fillRect(0, 0, view.w, view.h);
    var curve = result.curve;
    var alphaMark = result.alpha * 180 / Math.PI;
    var plotTop = 34;
    var plotBottom = view.h - 42;
    drawPanel(ctx, 46, view.w * 0.5 - 16, plotTop, plotBottom, curve.alphaDeg, [
      { ys: curve.sectionCl, xs: curve.sectionAlphaDeg, color: "#6c3483", name: "section cl" },
      { ys: curve.CL, xs: curve.alphaDeg, color: "#1a5276", name: "wing CL" }
    ], alphaMark, result.CL, "CL", result.sectionCl);
    drawPanel(ctx, view.w * 0.5 + 40, view.w - 16, plotTop, plotBottom, curve.alphaDeg, [
      { ys: curve.cd, xs: curve.alphaDeg, color: "#1e8449", name: "profile cd" },
      { ys: curve.CDi, xs: curve.alphaDeg, color: "#b9770e", name: "induced drag" },
      { ys: curve.CD, xs: curve.alphaDeg, color: "#1b2631", name: "total CD" }
    ], alphaMark, result.CD, "CD", null);
    ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.fillStyle = "#34495e";
    ctx.textAlign = "left";
    ctx.fillText("section cl and wing CL versus angle of attack", 16, 18);
    ctx.fillText("drag versus angle of attack", view.w * 0.5 + 8, 18);
  }

  function drawPanel(ctx, left, right, top, bottom, alphas, series, alphaMark, markY, axisName, markExtra) {
    var x0 = Math.min.apply(null, alphas);
    var x1 = Math.max.apply(null, alphas);
    var y0 = 0;
    var y1 = 0.01;
    series.forEach(function (item) {
      x0 = Math.min(x0, Math.min.apply(null, item.xs));
      x1 = Math.max(x1, Math.max.apply(null, item.xs));
      y0 = Math.min(y0, Math.min.apply(null, item.ys));
      y1 = Math.max(y1, Math.max.apply(null, item.ys));
    });
    if (isFinite(alphaMark)) {
      x0 = Math.min(x0, alphaMark);
      x1 = Math.max(x1, alphaMark);
    }
    if (isFinite(markY)) {
      y0 = Math.min(y0, markY);
      y1 = Math.max(y1, markY);
    }
    if (markExtra != null && isFinite(markExtra)) {
      y0 = Math.min(y0, markExtra);
      y1 = Math.max(y1, markExtra);
    }
    var padY = (y1 - y0) * 0.08 || 0.05;
    y0 -= padY;
    y1 += padY;
    if (x1 === x0) x1 = x0 + 1;
    ctx.strokeStyle = "#d5d8dc";
    ctx.lineWidth = 1;
    ctx.strokeRect(left, top, right - left, bottom - top);
    ctx.lineWidth = 1.6;
    series.forEach(function (item) {
      ctx.strokeStyle = item.color;
      polyline(ctx, item.xs, item.ys, x0, x1, y0, y1, left, right, top, bottom);
    });
    ctx.fillStyle = "#1a5276";
    marker(ctx, alphaMark, markY, x0, x1, y0, y1, left, right, top, bottom);
    ctx.fillStyle = "#34495e";
    ctx.font = "11px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.save();
    ctx.translate(left - 14, (top + bottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText(axisName, 0, 0);
    ctx.restore();
    ctx.textAlign = "left";
    ctx.fillText(Lab.trim(x0) + "°", left, bottom + 14);
    ctx.textAlign = "right";
    ctx.fillText(Lab.trim(x1) + "°", right, bottom + 14);
    ctx.textAlign = "center";
    ctx.fillText("angle of attack, deg", (left + right) / 2, bottom + 30);
    ctx.textAlign = "left";
    var legend = series.map(function (item) { return item.name; }).join("   ");
    ctx.fillText(legend, left + 4, top + 14);
    if (markExtra != null && isFinite(markExtra) && axisName === "CL") {
      ctx.fillStyle = "#6c3483";
      marker(ctx, alphaMark, markExtra, x0, x1, y0, y1, left, right, top, bottom);
    }
  }

  function render(result) {
    var theory = result.data_source === "thin_airfoil";
    cd0.disabled = !theory;
    document.getElementById("cd0-range").disabled = !theory;
    clmax.disabled = !theory;
    document.getElementById("clmax-range").disabled = !theory;
    theoryNote.textContent = theory
      ? "Thin-airfoil path. Zero-lift drag and CLmax are inputs. alpha_L0 is naca4_zero_lift_angle and a0 is 2π."
      : "Report 824 path. Zero-lift drag and CLmax sliders are unused. Wing CLmax is the chart cl,max.";
    if (!reDirty && result.Re != null) {
      writing = true;
      re.value = Lab.trim(result.Re);
      writing = false;
    }
    rebuildStops();
    status.textContent = result.data_source === "report824"
      ? "data_source report824. a0,eff = a0·cos(Λ) before wing_lift_curve_slope."
      : "data_source thin_airfoil. a0 = 2π, then a0,eff = a0·cos(Λ).";
    readout.innerHTML = [
      row("data_source", result.data_source),
      row("Re", result.Re == null ? "n/a" : Lab.trim(result.Re)),
      row("S", Lab.trim(result.area) + " m²"),
      row("AR", Lab.trim(result.aspectRatio)),
      row("taper", Lab.trim(result.taper)),
      row("MAC", Lab.trim(result.mac) + " m"),
      row("a", Lab.trim(result.a) + " /rad"),
      row("alpha_L0", Lab.trim(result.alphaL0 * 180 / Math.PI) + " deg"),
      row("CLmax", Lab.trim(result.CLmax)),
      row("CL", Lab.trim(result.CL)),
      row("CDi", Lab.trim(result.CDi)),
      row("CD", Lab.trim(result.CD))
    ].join("");
    exportBox.value = exportText(result);
    drawShape(result);
    drawCurves(result);
  }

  function refresh() {
    var result = Lab.evaluate(readSeed(), pack);
    if (!result.ok) {
      status.textContent = result.error;
      exportBox.value = result.error;
      return;
    }
    render(result);
  }

  applySeed();
  rebuildStops();
  pairs.forEach(function (pair) {
    var number = document.getElementById(pair[0]);
    var range = document.getElementById(pair[1]);
    range.addEventListener("input", function () {
      number.value = range.value;
      refresh();
    });
    number.addEventListener("input", function () {
      var value = Number(number.value);
      if (isFinite(value)) {
        range.value = String(Math.min(Number(range.max), Math.max(Number(range.min), value)));
      }
      refresh();
    });
  });
  reRange.addEventListener("input", function () {
    if (writing || !stops.length) return;
    reDirty = true;
    var raw = Math.pow(10, Number(reRange.value));
    var snapped = snapReynolds(raw);
    writing = true;
    re.value = snapped === raw ? Lab.trim(raw) : String(snapped);
    if (snapped !== raw) reRange.value = String(log10(snapped));
    writing = false;
    refresh();
  });
  re.addEventListener("input", function () {
    if (writing) return;
    reDirty = true;
    placeReSlider(Number(re.value));
    refresh();
  });
  naca.addEventListener("input", function () {
    rebuildStops();
    refresh();
  });
  sweepAt.addEventListener("change", refresh);
  window.addEventListener("resize", refresh);
  refresh();
};
