/* Wire the design calculation and, in a browser, the 2D lab page. */
var Lab = Lab || {};

Lab.need = function (value, message) {
  if (typeof value !== "number" || !isFinite(value)) throw new Error(message);
  return value;
};

Lab.computeDesign = function (seed, pack) {
  try {
    return Lab.evaluate(seed, pack);
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
};

Lab.evaluate = function (seed, pack) {
  var pc = Lab.need(seed.pc, "chamber pressure must be > 0");
  var pa = Lab.need(seed.pa, "ambient pressure must be >= 0");
  var thrust = Lab.need(seed.thrust, "thrust must be > 0");
  var lstar = Lab.need(seed.lstar, "L* must be > 0");
  var of = Lab.need(seed.of, "mixture ratio must be finite");
  var etaCstar = Lab.need(seed.etaCstar, "efficiencies must be > 0");
  var etaCf = Lab.need(seed.etaCf, "efficiencies must be > 0");
  var kSep = Lab.need(seed.kSep, "k-sep must be > 0");
  var caseThickness = Lab.need(seed.caseThickness, "case thickness must be > 0");
  var allowable = Lab.need(seed.allowable, "allowable stress must be > 0");
  var wallThickness = Lab.need(seed.wallThickness, "nozzle wall thickness must be > 0");
  var rhoMat = Lab.need(seed.rhoMat, "material density must be > 0");
  var halfAngle = Lab.need(seed.halfAngle, "half-angle must be in (0, pi/2) rad");
  var lengthFraction = Lab.need(seed.lengthFraction, "length fraction must be > 0");
  if (!(pc > 0)) throw new Error("chamber pressure must be > 0");
  if (pa < 0) throw new Error("ambient pressure must be >= 0");
  if (!(thrust > 0)) throw new Error("thrust must be > 0");
  if (!(lstar > 0)) throw new Error("L* must be > 0");
  if (!(etaCstar > 0) || !(etaCf > 0)) throw new Error("efficiencies must be > 0");
  if (!(caseThickness > 0)) throw new Error("case thickness must be > 0");
  if (!(allowable > 0)) throw new Error("allowable stress must be > 0");
  if (!(wallThickness > 0)) throw new Error("nozzle wall thickness must be > 0");
  if (!(rhoMat > 0)) throw new Error("material density must be > 0");

  var gas = Lab.lookupPropellant(pack, seed.pair, of, pc);
  var gamma = gas.gammaThroat;
  var gammaSource = "gamma_throat";
  var cstarIdeal = gas.cstar;
  var cstarSource = "table";
  if (seed.gamma != null) {
    gamma = Lab.need(seed.gamma, "gamma must be > 1");
    gammaSource = "input";
  }
  if (seed.cstar != null) {
    cstarIdeal = Lab.need(seed.cstar, "c* must be > 0");
    cstarSource = "input";
  }
  if (!(gamma > 1)) throw new Error("gamma must be > 1");
  if (!(cstarIdeal > 0)) throw new Error("c* must be > 0");

  var design = seed.design === "pe" ? "pe" : "epsilon";
  var Me;
  var epsilon;
  var pe;
  if (design === "pe") {
    if (seed.pe == null) throw new Error("pass epsilon or pe");
    pe = Lab.need(seed.pe, "exit pressure must be > 0");
    if (!(pe > 0)) throw new Error("exit pressure must be > 0");
    Me = Lab.machFromPressure(pc, pe, gamma);
    epsilon = Lab.areaRatio(Me, gamma);
  } else {
    if (seed.epsilon == null) throw new Error("pass epsilon or pe");
    epsilon = Lab.need(seed.epsilon, "epsilon must be >= 1");
    if (epsilon < 1) throw new Error("epsilon must be >= 1");
    Me = Lab.invertSupersonicMach(epsilon, gamma);
    pe = Lab.exitPressure(pc, Me, gamma);
  }
  if (Me < 1 - 1e-8) throw new Error("design exit is subsonic");

  var cfVac = Lab.thrustCoefficientIdeal(gamma, pe, pc, 0, epsilon, 1);
  var cfPa = Lab.thrustCoefficientIdeal(gamma, pe, pc, pa, epsilon, 1);
  var expansion = Lab.expansionFlag(pe, pa);
  var sep = Lab.separationState(pe, pa, kSep);
  var separated = sep.separation === "separated_or_at_risk";
  var deliveredVac = Lab.deliver(cfVac, cstarIdeal, etaCstar, etaCf);
  var deliveredPa = Lab.deliver(cfPa, cstarIdeal, etaCstar, etaCf);
  var cfSize = separated ? deliveredVac.cf : deliveredPa.cf;
  if (!(cfSize > 0)) throw new Error("thrust coefficient must be > 0");
  var at = Lab.throatArea(thrust, cfSize, pc);
  var dt = Lab.throatDiameter(at);
  var rt = dt / 2;
  var chamberSource = "input";
  var rc = seed.chamberRadius;
  if (rc == null) {
    rc = Lab.CHAMBER_FACTOR * rt;
    chamberSource = "default_2.5_Rt";
  } else {
    rc = Lab.need(rc, "chamber radius must be > 0");
    if (!(rc > 0)) throw new Error("chamber radius must be > 0");
  }
  var geom = Lab.conicalGeometry(rt, epsilon, halfAngle, lengthFraction);
  var barrel = Lab.chamberProfile(rc, rt, lstar, at);
  var hoop = Lab.hoopStress(pc, rc, caseThickness);
  var margin = Lab.marginOfSafety(allowable, hoop);
  var mdot = Lab.massFlow(pc, at, deliveredVac.cstar);
  var thrustVac = deliveredVac.cf * pc * at;
  var thrustAmb = separated ? null : deliveredPa.cf * pc * at;
  var ispAmb = separated ? null : deliveredPa.isp;
  var wallAngle = geom.Ldiv === 0 ? 0 : Math.atan((geom.Re - rt) / geom.Ldiv);

  return {
    ok: true,
    error: null,
    pair: seed.pair,
    of: of,
    pc: pc,
    pa: pa,
    gamma: gamma,
    gammaSource: gammaSource,
    gammaChamber: gas.gammaChamber,
    cstarIdeal: cstarIdeal,
    cstarSource: cstarSource,
    Tc: gas.Tc,
    pcTableBar: gas.pcTableBar,
    pcOffsetBar: gas.pcOffsetBar,
    pcWarning: gas.pcWarning,
    designSource: design,
    Me: Me,
    epsilon: epsilon,
    pe: pe,
    expansion: expansion,
    CFIdeal: separated ? null : cfPa,
    CFVac: cfVac,
    etaCstar: etaCstar,
    etaCf: etaCf,
    cstar: deliveredVac.cstar,
    CF: separated ? null : deliveredPa.cf,
    CFVacDelivered: deliveredVac.cf,
    separated: separated,
    separation: sep.separation,
    separationMargin: sep.separationMargin,
    Isp: ispAmb,
    IspVac: deliveredVac.isp,
    At: at,
    Dt: dt,
    Rt: rt,
    Re: geom.Re,
    Ae: epsilon * at,
    mdot: mdot,
    thrust: thrustAmb,
    thrustVac: thrustVac,
    sizing: separated ? "vacuum_because_separated" : "ambient",
    Vc: barrel.Vc,
    Lcyl: barrel.Lcyl,
    Lconv: barrel.Lconv,
    Ldiv: geom.Ldiv,
    Lcone: geom.Lcone,
    Lslant: geom.Lslant,
    Rc: rc,
    chamberRadiusSource: chamberSource,
    hoop: hoop,
    margin: margin,
    thinWall: Lab.thinWall(rc, caseThickness),
    mNozzle: Lab.shellMass(rt, geom.Re, geom.Lslant, wallThickness, rhoMat),
    volumeShort: barrel.volumeShort,
    halfAngle: halfAngle,
    lengthFraction: lengthFraction,
    wallAngle: wallAngle,
    kSep: kSep
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
    "pair: " + result.pair,
    "of: " + result.of,
    "pc_Pa: " + result.pc,
    "pa_Pa: " + result.pa,
    "epsilon: " + result.epsilon,
    "pe_Pa: " + result.pe,
    "gamma: " + result.gamma,
    "cstar_m_s: " + result.cstar,
    "CF: " + (result.CF == null ? "invalid_separated" : result.CF),
    "thrust_N: " + (result.thrust == null ? "invalid_separated" : result.thrust),
    "At_m2: " + result.At,
    "Rc_m: " + result.Rc,
    "Lstar_m: " + seed.lstar,
    "",
    "ROCKET - PerformanceParameters",
    "--pair " + result.pair + " --r " + result.of + " --pc " + result.pc
      + " --pa " + result.pa + " --epsilon " + result.epsilon,
    "",
    "ROCKET - LossStack",
    "--cf " + result.CFVac + " --cstar " + result.cstarIdeal
      + " --eta cstar=" + result.etaCstar + " --eta nozzle=" + result.etaCf
      + " --pc " + result.pc + " --throat " + result.At,
    "",
    "ROCKET - ThroatSizingandMassFlow",
    "--thrust " + (result.thrust == null ? result.thrustVac : result.thrust)
      + " --cf " + (result.CF == null ? result.CFVacDelivered : result.CF)
      + " --pc " + result.pc + " --cstar " + result.cstar,
    "",
    "ROCKET - ChamberVolumeAndCaseHoopStress",
    "--throat " + result.At + " --lstar " + seed.lstar + " --pc " + result.pc
      + " --radius " + result.Rc + " --thickness " + seed.caseThickness
      + " --allowable " + seed.allowable,
    "",
    "ROCKET - KickStageNozzle",
    "--pc " + result.pc + " --epsilon " + result.epsilon + " --pa " + result.pa
      + " --gamma " + result.gamma + " --throat " + result.At
      + " --half-angle " + result.halfAngle + " --length-fraction " + result.lengthFraction
      + " --thickness " + seed.wallThickness + " --rho-mat " + seed.rhoMat
      + " --k-sep " + result.kSep
  ];
  return lines.join("\n");
};

if (typeof document !== "undefined") {
  Lab.boot = function () {
    var pack = JSON.parse(document.getElementById("cea-pack").textContent);
    var seed = JSON.parse(document.getElementById("seed-json").textContent);
    var pairSelect = document.getElementById("pair");
    pack.pairs.forEach(function (pair) {
      var option = document.createElement("option");
      option.value = pair.pair;
      option.textContent = pair.pair;
      pairSelect.appendChild(option);
    });
    pairSelect.value = seed.pair;
    Lab.pack = pack;
    Lab.form = {
      of: document.getElementById("of"),
      ofRange: document.getElementById("of-range"),
      pc: document.getElementById("pc"),
      pcRange: document.getElementById("pc-range"),
      epsilon: document.getElementById("epsilon"),
      epsilonRange: document.getElementById("epsilon-range"),
      pe: document.getElementById("pe"),
      pa: document.getElementById("pa"),
      paRange: document.getElementById("pa-range"),
      thrust: document.getElementById("thrust"),
      thrustRange: document.getElementById("thrust-range"),
      halfDeg: document.getElementById("half-deg"),
      halfRange: document.getElementById("half-range"),
      lengthFraction: document.getElementById("length-fraction"),
      lengthRange: document.getElementById("length-range"),
      lstar: document.getElementById("lstar"),
      chamberRadius: document.getElementById("chamber-radius"),
      caseThickness: document.getElementById("case-thickness"),
      allowable: document.getElementById("allowable"),
      wallThickness: document.getElementById("wall-thickness"),
      rhoMat: document.getElementById("rho-mat"),
      etaCstar: document.getElementById("eta-cstar"),
      etaCf: document.getElementById("eta-cf"),
      kSep: document.getElementById("k-sep"),
      gamma: document.getElementById("gamma"),
      cstar: document.getElementById("cstar"),
      manual: document.getElementById("manual")
    };
    Lab.form.of.value = seed.of;
    Lab.form.pc.value = seed.pc;
    Lab.form.pa.value = seed.pa;
    Lab.form.thrust.value = seed.thrust;
    Lab.form.halfDeg.value = Lab.trim(seed.halfAngle * 180 / Math.PI);
    Lab.form.lengthFraction.value = seed.lengthFraction;
    Lab.form.lstar.value = seed.lstar;
    if (seed.chamberRadius != null) Lab.form.chamberRadius.value = seed.chamberRadius;
    Lab.form.caseThickness.value = seed.caseThickness;
    Lab.form.allowable.value = seed.allowable;
    Lab.form.wallThickness.value = seed.wallThickness;
    Lab.form.rhoMat.value = seed.rhoMat;
    Lab.form.etaCstar.value = seed.etaCstar;
    Lab.form.etaCf.value = seed.etaCf;
    Lab.form.kSep.value = seed.kSep;
    if (seed.design === "pe") document.getElementById("design-pe").checked = true;
    else document.getElementById("design-epsilon").checked = true;
    if (seed.epsilon != null) Lab.form.epsilon.value = seed.epsilon;
    if (seed.pe != null) Lab.form.pe.value = seed.pe;
    if (seed.gamma != null || seed.cstar != null) {
      Lab.form.manual.checked = true;
      if (seed.gamma != null) Lab.form.gamma.value = seed.gamma;
      if (seed.cstar != null) Lab.form.cstar.value = seed.cstar;
    }
    Lab.syncRanges();
    Lab.bind();
    Lab.refresh();
    window.addEventListener("resize", function () { Lab.draw(Lab.last); });
  };

  Lab.pairSpec = function (name) {
    for (var i = 0; i < Lab.pack.pairs.length; i += 1) {
      if (Lab.pack.pairs[i].pair === name) return Lab.pack.pairs[i];
    }
    return null;
  };

  Lab.syncRanges = function () {
    var spec = Lab.pairSpec(document.getElementById("pair").value);
    if (spec) {
      Lab.form.ofRange.min = spec.of_min;
      Lab.form.ofRange.max = spec.of_max;
      Lab.form.ofRange.step = spec.of_step;
    }
    Lab.mirror(Lab.form.ofRange, Lab.form.of);
    Lab.mirror(Lab.form.pcRange, Lab.form.pc);
    Lab.mirror(Lab.form.epsilonRange, Lab.form.epsilon);
    Lab.mirror(Lab.form.paRange, Lab.form.pa);
    Lab.mirror(Lab.form.thrustRange, Lab.form.thrust);
    Lab.mirror(Lab.form.halfRange, Lab.form.halfDeg);
    Lab.mirror(Lab.form.lengthRange, Lab.form.lengthFraction);
  };

  Lab.mirror = function (range, number) {
    var value = Number(number.value);
    if (!isFinite(value)) return;
    var min = Number(range.min);
    var max = Number(range.max);
    range.value = Math.min(max, Math.max(min, value));
  };

  Lab.readSeed = function () {
    var design = document.getElementById("design-pe").checked ? "pe" : "epsilon";
    var manual = Lab.form.manual.checked;
    var radiusText = Lab.form.chamberRadius.value.trim();
    return {
      pair: document.getElementById("pair").value,
      of: Number(Lab.form.of.value),
      pc: Number(Lab.form.pc.value),
      pa: Number(Lab.form.pa.value),
      thrust: Number(Lab.form.thrust.value),
      lstar: Number(Lab.form.lstar.value),
      design: design,
      epsilon: design === "epsilon" ? Number(Lab.form.epsilon.value) : null,
      pe: design === "pe" ? Number(Lab.form.pe.value) : null,
      halfAngle: Number(Lab.form.halfDeg.value) * Math.PI / 180,
      lengthFraction: Number(Lab.form.lengthFraction.value),
      chamberRadius: radiusText === "" ? null : Number(radiusText),
      caseThickness: Number(Lab.form.caseThickness.value),
      allowable: Number(Lab.form.allowable.value),
      wallThickness: Number(Lab.form.wallThickness.value),
      rhoMat: Number(Lab.form.rhoMat.value),
      etaCstar: Number(Lab.form.etaCstar.value),
      etaCf: Number(Lab.form.etaCf.value),
      kSep: Number(Lab.form.kSep.value),
      gamma: manual && Lab.form.gamma.value !== "" ? Number(Lab.form.gamma.value) : null,
      cstar: manual && Lab.form.cstar.value !== "" ? Number(Lab.form.cstar.value) : null
    };
  };

  Lab.refresh = function () {
    Lab.syncRanges();
    var spec = Lab.pairSpec(document.getElementById("pair").value);
    if (spec) {
      var ofNow = Number(Lab.form.of.value);
      if (ofNow < spec.of_min) Lab.form.of.value = spec.of_min;
      if (ofNow > spec.of_max) Lab.form.of.value = spec.of_max;
    }
    var usePe = document.getElementById("design-pe").checked;
    Lab.form.epsilon.disabled = usePe;
    Lab.form.epsilonRange.disabled = usePe;
    Lab.form.pe.disabled = !usePe;
    Lab.form.gamma.disabled = !Lab.form.manual.checked;
    Lab.form.cstar.disabled = !Lab.form.manual.checked;
    var result = Lab.computeDesign(Lab.readSeed(), Lab.pack);
    Lab.last = result;
    Lab.paint(result);
    Lab.draw(result);
    document.getElementById("export").value = Lab.exportText(Lab.readSeed(), result);
    if (result.ok) {
      if (usePe) Lab.form.epsilon.value = Lab.trim(result.epsilon);
      else Lab.form.pe.value = Lab.trim(result.pe);
      if (!Lab.form.manual.checked) {
        Lab.form.gamma.value = Lab.trim(result.gamma);
        Lab.form.cstar.value = Lab.trim(result.cstarIdeal);
      }
    }
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
    if (result.separated) notes.push("Separated or at risk: ambient thrust is invalid. Throat sized on vacuum thrust.");
    if (result.expansion === "overexpanded") notes.push("Overexpanded relative to ambient pressure.");
    if (result.pcWarning) notes.push(result.pcWarning);
    if (result.volumeShort) notes.push("L* is smaller than the convergent frustum; cylinder length is zero.");
    if (result.thinWall === "no") notes.push("Case t/R is not below 0.1; thin-wall hoop stress is outside its usual range.");
    notes.push("Divergent wall is a shortened cone, not a Rao bell. Convergent half-angle is fixed at 30°.");
    status.textContent = notes.join(" ");
    var cf = result.CF == null ? "invalid_separated" : Lab.fmt(result.CF);
    var thrust = result.thrust == null ? "invalid_separated" : Lab.fmt(result.thrust);
    var isp = result.Isp == null ? "invalid_separated" : Lab.fmt(result.Isp);
    var margin = result.separationMargin == null ? "n/a" : Lab.fmt(result.separationMargin);
    readout.innerHTML = [
      Lab.row("Me", Lab.fmt(result.Me)),
      Lab.row("ε", Lab.fmt(result.epsilon)),
      Lab.row("pe [Pa]", Lab.fmt(result.pe)),
      Lab.row("expansion", result.expansion),
      Lab.row("γ", Lab.fmt(result.gamma) + " (" + result.gammaSource + ")"),
      Lab.row("Tc [K]", Lab.fmt(result.Tc)),
      Lab.row("c* ideal [m/s]", Lab.fmt(result.cstarIdeal)),
      Lab.row("c* delivered [m/s]", Lab.fmt(result.cstar)),
      Lab.row("CF ambient", cf),
      Lab.row("CF vacuum", Lab.fmt(result.CFVacDelivered)),
      Lab.row("Isp ambient [s]", isp),
      Lab.row("Isp vacuum [s]", Lab.fmt(result.IspVac)),
      Lab.row("At [m²]", Lab.fmt(result.At)),
      Lab.row("Dt [m]", Lab.fmt(result.Dt)),
      Lab.row("mdot [kg/s]", Lab.fmt(result.mdot)),
      Lab.row("thrust ambient [N]", thrust),
      Lab.row("thrust vacuum [N]", Lab.fmt(result.thrustVac)),
      Lab.row("separation", result.separation),
      Lab.row("separation margin", margin),
      Lab.row("Vc [m³]", Lab.fmt(result.Vc)),
      Lab.row("Rc [m]", Lab.fmt(result.Rc)),
      Lab.row("Rt [m]", Lab.fmt(result.Rt)),
      Lab.row("Re [m]", Lab.fmt(result.Re)),
      Lab.row("L cylinder [m]", Lab.fmt(result.Lcyl)),
      Lab.row("L divergent [m]", Lab.fmt(result.Ldiv)),
      Lab.row("wall angle [deg]", Lab.fmt(result.wallAngle * 180 / Math.PI)),
      Lab.row("hoop [Pa]", Lab.fmt(result.hoop)),
      Lab.row("MS", Lab.fmt(result.margin)),
      Lab.row("thin wall", result.thinWall),
      Lab.row("nozzle mass [kg]", Lab.fmt(result.mNozzle)),
      Lab.row("table pc [bar]", Lab.fmt(result.pcTableBar))
    ].join("");
  };

  Lab.draw = function (result) {
    var canvas = document.getElementById("view");
    var ctx = canvas.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = canvas.clientWidth || 640;
    var h = canvas.clientHeight || 420;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#f7f9fb";
    ctx.fillRect(0, 0, w, h);
    if (!result || !result.ok) return;
    var pts = [
      [0, result.Rc],
      [result.Lcyl, result.Rc],
      [result.Lcyl + result.Lconv, result.Rt],
      [result.Lcyl + result.Lconv + result.Ldiv, result.Re]
    ];
    var length = pts[pts.length - 1][0];
    var radius = Math.max(result.Rc, result.Re);
    var pad = 28;
    var scale = Math.min((w - 2 * pad) / Math.max(length, 1e-9), (h - 2 * pad) / Math.max(2 * radius, 1e-9));
    var ox = (w - length * scale) / 2;
    var oy = h / 2;
    function X(x) { return ox + x * scale; }
    function Y(r) { return oy - r * scale; }
    ctx.beginPath();
    ctx.moveTo(X(pts[0][0]), Y(pts[0][1]));
    for (var i = 1; i < pts.length; i += 1) ctx.lineTo(X(pts[i][0]), Y(pts[i][1]));
    for (var j = pts.length - 1; j >= 0; j -= 1) ctx.lineTo(X(pts[j][0]), Y(-pts[j][1]));
    ctx.closePath();
    ctx.fillStyle = "#d6eaf8";
    ctx.strokeStyle = "#1b2631";
    ctx.lineWidth = 1.6;
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "#7f8c8d";
    ctx.moveTo(X(0), oy);
    ctx.lineTo(X(length), oy);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#1b2631";
    ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.fillText("Rt " + Lab.fmt(result.Rt) + " m", X(result.Lcyl + result.Lconv) + 6, Y(result.Rt) - 8);
    ctx.fillText("Re " + Lab.fmt(result.Re) + " m", Math.min(w - 110, X(length) - 20), Y(result.Re) - 8);
    ctx.fillText("L " + Lab.fmt(length) + " m", X(length / 2), oy + 18);
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
    Lab.bindPair(Lab.form.ofRange, Lab.form.of);
    Lab.bindPair(Lab.form.pcRange, Lab.form.pc);
    Lab.bindPair(Lab.form.epsilonRange, Lab.form.epsilon);
    Lab.bindPair(Lab.form.paRange, Lab.form.pa);
    Lab.bindPair(Lab.form.thrustRange, Lab.form.thrust);
    Lab.bindPair(Lab.form.halfRange, Lab.form.halfDeg);
    Lab.bindPair(Lab.form.lengthRange, Lab.form.lengthFraction);
    [
      "pair", "pe", "lstar", "chamber-radius", "case-thickness", "allowable",
      "wall-thickness", "rho-mat", "eta-cstar", "eta-cf", "k-sep", "gamma", "cstar"
    ].forEach(function (id) {
      document.getElementById(id).addEventListener("input", Lab.refresh);
      document.getElementById(id).addEventListener("change", Lab.refresh);
    });
    document.getElementById("design-epsilon").addEventListener("change", Lab.refresh);
    document.getElementById("design-pe").addEventListener("change", Lab.refresh);
    Lab.form.manual.addEventListener("change", Lab.refresh);
  };

  Lab.boot();
}
