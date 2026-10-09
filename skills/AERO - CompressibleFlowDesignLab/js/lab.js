/* Mode dispatch, canvases, and the live page. */
var Lab = Lab || {};

Lab.MODES = [
  "isentropic",
  "normal",
  "wedge",
  "cone",
  "diamond",
  "fanno",
  "rayleigh",
  "prandtl_glauert",
  "rayleigh_pitot"
];

Lab.fail = function (mode, error) {
  return { ok: false, mode: mode, error: String(error && error.message ? error.message : error) };
};

Lab.designPoint = function (seed) {
  var mode = seed.mode;
  var gamma = seed.gamma;
  try {
    if (mode === "isentropic") {
      var iso = Lab.stagnationState(seed.mach, gamma, seed.temperature, seed.pressure, seed.density);
      iso.ok = true;
      iso.mode = mode;
      iso.error = null;
      return iso;
    }
    if (mode === "normal") {
      var shock = Lab.shockState(seed.mach, gamma);
      shock.ok = true;
      shock.mode = mode;
      shock.error = null;
      return shock;
    }
    if (mode === "wedge") {
      var wedge = Lab.evaluateWedge(seed.mach, gamma, seed.delta);
      wedge.ok = true;
      wedge.mode = mode;
      wedge.error = null;
      return wedge;
    }
    if (mode === "cone") {
      var cone = Lab.evaluateCone(seed.mach, gamma, seed.delta);
      cone.ok = true;
      cone.mode = mode;
      cone.error = null;
      return cone;
    }
    if (mode === "diamond") {
      return Lab.packDiamond(Lab.evaluateDiamond(seed.mach, gamma, seed.epsilon, seed.alpha));
    }
    if (mode === "fanno" || mode === "rayleigh") {
      return Lab.packDuct(mode, seed);
    }
    if (mode === "prandtl_glauert") {
      var pg = Lab.correctionState(seed.mach, gamma, seed.clInc, seed.cpminInc, seed.cmInc, seed.cdInc);
      pg.ok = true;
      pg.mode = mode;
      pg.error = null;
      pg.coeff_source = "user";
      return pg;
    }
    if (mode === "rayleigh_pitot") {
      var pitot = Lab.pitotState(seed.pitot, seed.staticPressure, gamma);
      pitot.ok = true;
      pitot.mode = mode;
      pitot.error = null;
      return pitot;
    }
    return Lab.fail(mode, "unknown mode");
  } catch (err) {
    return Lab.fail(mode, err);
  }
};

Lab.packPanel = function (panel) {
  if (!panel) {
    return { wave: null, M: null, p: null, theta: null, delta_max: null };
  }
  return {
    wave: panel.wave,
    M: panel.M == null ? null : panel.M,
    p: panel.p_over_pinf == null ? null : panel.p_over_pinf,
    theta: panel.theta == null ? null : panel.theta,
    delta_max: panel.delta_max == null ? null : panel.delta_max
  };
};

Lab.packDiamond = function (state) {
  var upper = Lab.packPanel(state.u1);
  var lower = Lab.packPanel(state.l1);
  var upperTe = Lab.packPanel(state.u2);
  var lowerTe = Lab.packPanel(state.l2);
  return {
    ok: true,
    mode: "diamond",
    error: null,
    mach: state.mach,
    gamma: state.gamma,
    epsilon: state.epsilon,
    alpha: state.alpha,
    delta_u1: state.delta_u1,
    delta_l1: state.delta_l1,
    shoulder: state.shoulder,
    solution: state.solution,
    wave_u1: upper.wave,
    M_u1: upper.M,
    p_u1: upper.p,
    theta_u1: upper.theta,
    delta_max_u1: upper.delta_max,
    wave_l1: lower.wave,
    M_l1: lower.M,
    p_l1: lower.p,
    theta_l1: lower.theta,
    delta_max_l1: lower.delta_max,
    wave_u2: upperTe.wave,
    M_u2: upperTe.M,
    p_u2: upperTe.p,
    theta_u2: upperTe.theta,
    wave_l2: lowerTe.wave,
    M_l2: lowerTe.M,
    p_l2: lowerTe.p,
    theta_l2: lowerTe.theta,
    Cp_u1: state.Cp_u1,
    Cp_u2: state.Cp_u2,
    Cp_l1: state.Cp_l1,
    Cp_l2: state.Cp_l2,
    cn: state.cn,
    ca: state.ca,
    cl: state.cl,
    cd: state.cd
  };
};

Lab.packDuct = function (mode, seed) {
  var state = Lab.ductState(mode, seed.mach, seed.gamma);
  state.ok = true;
  state.mode = mode;
  state.error = null;
  state.choked = Math.abs(state.M - 1) <= 1e-6 ? "yes" : "no";
  state.fld = null;
  state.four_f_L_remaining_over_D = null;
  state.tt_ratio = null;
  state.exit_mach = null;
  state.choked_by_length = null;
  state.choked_by_heat = null;
  if (mode === "fanno" && seed.fld != null) {
    var length = Lab.fannoExitMach(seed.mach, seed.gamma, seed.fld);
    state.fld = seed.fld;
    state.four_f_L_remaining_over_D = Math.max(0, state.four_f_Lmax_over_D - seed.fld);
    state.choked_by_length = length.choked;
    state.exit_mach = length.exitMach;
  }
  if (mode === "rayleigh" && seed.ttRatio != null) {
    var heat = Lab.rayleighExitMach(seed.mach, seed.gamma, seed.ttRatio);
    state.tt_ratio = seed.ttRatio;
    state.choked_by_heat = heat.choked;
    state.exit_mach = heat.exitMach;
  }
  return state;
};

Lab.fmt = function (value) {
  if (value == null || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  if (typeof value === "string") {
    return value;
  }
  if (!isFinite(value)) {
    return "—";
  }
  var abs = Math.abs(value);
  if (abs !== 0 && (abs >= 1e5 || abs < 1e-3)) {
    return value.toExponential(4);
  }
  return String(Math.round(value * 1e6) / 1e6);
};

Lab.axisNum = function (value) {
  if (!isFinite(value)) {
    return "";
  }
  var text = (Math.round(value * 1000) / 1000).toFixed(3);
  return text.replace(/\.?0+$/, "") || "0";
};

Lab.niceStep = function (span, count) {
  if (!(span > 0) || !isFinite(span)) {
    return 1;
  }
  var raw = span / Math.max(2, count - 1);
  var pow = Math.pow(10, Math.floor(Math.log10(raw)));
  var n = raw / pow;
  var step = n <= 1.5 ? 1 : n <= 3 ? 2 : n <= 7 ? 5 : 10;
  return step * pow;
};

Lab.niceCeil = function (value) {
  if (!(value > 0) || !isFinite(value)) {
    return 1;
  }
  var pow = Math.pow(10, Math.floor(Math.log10(value)));
  var steps = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  for (var index = 0; index < steps.length; index++) {
    var tick = steps[index] * pow;
    if (tick >= value - 1e-9) {
      return tick;
    }
  }
  return 10 * pow;
};

Lab.deg = function (rad) {
  return rad == null ? null : rad * 180 / Math.PI;
};

Lab.rowsFor = function (result) {
  if (!result.ok) {
    return [["Status", result.error || "not solved"]];
  }
  var rows = [];
  function add(label, value) {
    if (value != null) {
      rows.push([label, Lab.fmt(value)]);
    }
  }
  if (result.mode === "isentropic") {
    add("M", result.M);
    add("Tt/T", result.Tt_over_T);
    add("pt/p", result.pt_over_p);
    add("ρt/ρ", result.rhot_over_rho);
    add("at/a", result.at_over_a);
    add("T*/Tt", result.Tstar_over_Tt);
    add("p*/pt", result.pstar_over_pt);
    add("Tt, K", result.Tt);
    add("pt, Pa", result.pt);
    add("a, m/s", result.a);
    add("at, m/s", result.a_t);
  } else if (result.mode === "normal") {
    add("M1", result.M1);
    add("M2", result.M2);
    add("p2/p1", result.p2_over_p1);
    add("T2/T1", result.T2_over_T1);
    add("ρ2/ρ1", result.rho2_over_rho1);
    add("pt2/pt1", result.pt2_over_pt1);
    add("Δs/R", result.ds_over_R);
  } else if (result.mode === "wedge") {
    add("attached", result.attached);
    add("shock", result.shock);
    add("δ, deg", Lab.deg(result.delta));
    add("μ, deg", Lab.deg(result.mu));
    add("δmax, deg", Lab.deg(result.delta_max));
    add("θ, deg", Lab.deg(result.theta));
    add("M2", result.M2);
    add("p2/p1", result.p2_over_p1);
    add("expansion", result.expansion);
    add("PM Mach", result.pm_M);
    add("PM p ratio", result.pm_p_ratio);
    add("fan", result.fan);
    add("fan Mach", result.fan_M);
  } else if (result.mode === "cone") {
    add("attached", result.attached);
    add("shock", result.shock);
    add("δ, deg", Lab.deg(result.delta));
    add("δmax, deg", Lab.deg(result.delta_max));
    add("θ, deg", Lab.deg(result.theta));
    add("M2", result.M2);
    add("Mc", result.Mc);
    add("pc/p1", result.pc_over_p1);
    add("Cp", result.Cp);
  } else if (result.mode === "diamond") {
    add("solution", result.solution);
    add("δ upper, deg", Lab.deg(result.delta_u1));
    add("δ lower, deg", Lab.deg(result.delta_l1));
    add("pu1/p∞", result.p_u1);
    add("pu2/p∞", result.p_u2);
    add("pl1/p∞", result.p_l1);
    add("pl2/p∞", result.p_l2);
    add("cl", result.cl);
    add("cd", result.cd);
  } else if (result.mode === "fanno" || result.mode === "rayleigh") {
    add("M", result.M);
    add("T/T*", result.T_over_Tstar);
    add("p/p*", result.p_over_pstar);
    add("ρ/ρ*", result.rho_over_rhostar);
    add("V/V*", result.V_over_Vstar);
    add("pt/pt*", result.pt_over_ptstar);
    add("Tt/Tt*", result.Tt_over_Ttstar);
    add("4fL*/D", result.four_f_Lmax_over_D);
    add("4fL/D", result.fld);
    add("Tt2/Tt1", result.tt_ratio);
    add("exit M", result.exit_mach);
    add("choked", result.choked);
    add("choked by length", result.choked_by_length);
    add("choked by heat", result.choked_by_heat);
  } else if (result.mode === "prandtl_glauert") {
    add("M", result.M);
    add("β", result.beta);
    add("CL", result.CL);
    add("Cm", result.Cm);
    add("Cd", result.Cd);
    add("Cp,min", result.Cp_min);
    add("Cp,crit", result.Cp_crit);
    add("Mcr", result.M_cr);
    add("supercritical", result.supercritical);
  } else if (result.mode === "rayleigh_pitot") {
    add("branch", result.branch);
    add("relation", result.relation);
    add("pt/p", result.ratio);
    add("sonic pt/p", result.sonic_ratio);
    add("M", result.M);
    add("q, Pa", result.q);
  }
  return rows;
};

Lab.exportText = function (seed) {
  var g = seed.gamma;
  var gamma = Math.abs(g - 1.4) < 1e-12 ? "" : " --gamma " + g;
  var lines = [];
  function push(skill, args) {
    lines.push('python "skills/' + skill + '" ' + args + gamma);
  }
  if (seed.mode === "isentropic") {
    var extra = "";
    if (seed.temperature != null) extra += " --temperature " + seed.temperature;
    if (seed.pressure != null) extra += " --pressure " + seed.pressure;
    if (seed.density != null) extra += " --density " + seed.density;
    push("AERO - IsentropicStagnation/isentropic_stagnation.py", "--mach " + seed.mach + extra);
  } else if (seed.mode === "normal") {
    push("AERO - NormalShock/normal_shock.py", "--mach " + seed.mach);
  } else if (seed.mode === "wedge") {
    push("AERO - PrandtlMeyerAndShocks/prandtl_meyer_and_shocks.py", "--mach " + seed.mach + " --delta " + seed.delta);
  } else if (seed.mode === "cone") {
    push("AERO - ConicalShock/conical_shock.py", "--mach " + seed.mach + " --delta " + seed.delta);
  } else if (seed.mode === "diamond") {
    push(
      "AERO - DiamondAirfoilShockExpansion/diamond_airfoil_shock_expansion.py",
      "--mach " + seed.mach + " --epsilon " + seed.epsilon + " --alpha " + seed.alpha
    );
  } else if (seed.mode === "fanno") {
    var fld = seed.fld == null ? "" : " --fld " + seed.fld;
    push("AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py", "--fanno --mach " + seed.mach + fld);
  } else if (seed.mode === "rayleigh") {
    var tt = seed.ttRatio == null ? "" : " --tt-ratio " + seed.ttRatio;
    push("AERO - FannoAndRayleighFlow/fanno_and_rayleigh_flow.py", "--rayleigh --mach " + seed.mach + tt);
  } else if (seed.mode === "prandtl_glauert") {
    push(
      "AERO - PrandtGlauertCorrectionandCriticalMach/prandtl_glauert_correction_and_critical_mach.py",
      "--mach " + seed.mach +
        " --cl-inc " + seed.clInc +
        " --cm-inc " + seed.cmInc +
        " --cd-inc " + seed.cdInc +
        " --cpmin-inc " + seed.cpminInc
    );
  } else if (seed.mode === "rayleigh_pitot") {
    push(
      "AERO - RayleighPitotMach/rayleigh_pitot_mach.py",
      "--pitot " + seed.pitot + " --static " + seed.staticPressure
    );
  }
  return lines.join("\n");
};

Lab.fit = function (canvas, height) {
  var rect = canvas.getBoundingClientRect();
  var dpr = window.devicePixelRatio || 1;
  var w = Math.max(280, rect.width || 640);
  canvas.style.height = height + "px";
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(height * dpr);
  var ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, height);
  ctx.fillStyle = "#f7f9fb";
  ctx.fillRect(0, 0, w, height);
  return { ctx: ctx, w: w, h: height };
};

Lab.text = function (ctx, x, y, message, color, size) {
  ctx.fillStyle = color || "#1b2631";
  ctx.font = (size || 12) + "px Segoe UI, Helvetica, Arial, sans-serif";
  ctx.fillText(message, x, y);
};

Lab.ductFrame = function (ctx, w, h) {
  var box = { x0: 28, x1: w - 24, y0: 54, y1: Math.min(h - 70, 210) };
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(box.x0, box.y0);
  ctx.lineTo(box.x1, box.y0);
  ctx.moveTo(box.x0, box.y1);
  ctx.lineTo(box.x1, box.y1);
  ctx.stroke();
  return box;
};

Lab.streamFunction = function (ctx, box, flowingAt) {
  var lanes = 5;
  var steps = 48;
  var span = box.x1 - box.x0;
  var height = box.y1 - box.y0;
  for (var lane = 1; lane <= lanes; lane++) {
    var y = box.y1 - height * lane / (lanes + 1);
    ctx.strokeStyle = "#1a5276";
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    var drawing = false;
    var arrowDrawn = false;
    for (var s = 0; s <= steps; s++) {
      var t = s / steps;
      var live = !flowingAt || flowingAt(t);
      var x = box.x0 + span * t;
      if (!live) {
        if (drawing) {
          ctx.stroke();
          drawing = false;
          ctx.beginPath();
        }
        continue;
      }
      if (!drawing) {
        ctx.moveTo(x, y);
        drawing = true;
      } else {
        ctx.lineTo(x, y);
      }
      if (!arrowDrawn && t >= 0.28) {
        ctx.stroke();
        ctx.beginPath();
        ctx.fillStyle = "#1a5276";
        ctx.moveTo(x, y);
        ctx.lineTo(x - 7, y - 3.2);
        ctx.lineTo(x - 7, y + 3.2);
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(x, y);
        drawing = true;
        arrowDrawn = true;
      }
    }
    if (drawing) {
      ctx.stroke();
    }
  }
  Lab.text(ctx, box.x1 - 36, box.y0 + 14, "ψ", "#1a5276", 13);
  Lab.text(ctx, box.x1 - 28, box.y1 - 6, "0", "#1a5276", 11);
};

Lab.stationLine = function (ctx, box, fraction, label) {
  var x = box.x0 + (box.x1 - box.x0) * fraction;
  ctx.save();
  ctx.strokeStyle = "#922b21";
  ctx.setLineDash([4, 3]);
  ctx.beginPath();
  ctx.moveTo(x, box.y0);
  ctx.lineTo(x, box.y1);
  ctx.stroke();
  ctx.restore();
  Lab.text(ctx, x + 4, box.y0 - 8, label, "#922b21", 12);
  return x;
};

Lab.drawNormal = function (ctx, w, h, result) {
  var box = Lab.ductFrame(ctx, w, h);
  var m1 = result.M1;
  var m2 = result.M2;
  Lab.streamFunction(ctx, box, function () {
    return true;
  });
  var x = box.x0 + (box.x1 - box.x0) * 0.5;
  ctx.strokeStyle = "#922b21";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(x, box.y0);
  ctx.lineTo(x, box.y1);
  ctx.stroke();
  Lab.text(ctx, box.x0, 28, "Constant-area duct", "#1b2631", 14);
  Lab.text(ctx, box.x0 + 8, box.y0 + 18, "M1 = " + Lab.fmt(m1), "#1b2631", 13);
  Lab.text(ctx, x + 8, box.y0 + 18, "M2 = " + Lab.fmt(m2), "#1b2631", 13);
  Lab.text(ctx, x - 18, (box.y0 + box.y1) / 2, "shock", "#922b21", 12);
  var notes = [
    "p2/p1 = " + Lab.fmt(result.p2_over_p1),
    "T2/T1 = " + Lab.fmt(result.T2_over_T1),
    "ρ2/ρ1 = " + Lab.fmt(result.rho2_over_rho1),
    "pt2/pt1 = " + Lab.fmt(result.pt2_over_pt1),
    "Δs/R = " + Lab.fmt(result.ds_over_R)
  ];
  notes.forEach(function (line, index) {
    Lab.text(ctx, box.x0, box.y1 + 22 + index * 16, line, "#34495e", 12);
  });
};

Lab.speedSampler = function (result) {
  var gamma = result.gamma;
  var inlet = result.M;
  var supersonic = inlet >= 1;
  var velocity = result.mode === "fanno" ? Lab.fannoVelocityRatio : Lab.rayleighVelocityRatio;
  if (result.mode === "fanno" && result.fld != null && result.choked_by_length === "no" && result.exit_mach != null) {
    var remain = result.four_f_Lmax_over_D;
    return function (t) {
      var target = remain - result.fld * t;
      var mach = Lab.machFromFannoFriction(Math.max(target, 0), gamma, supersonic);
      return velocity(mach, gamma);
    };
  }
  if (result.mode === "fanno" && result.choked_by_length === "yes") {
    var remainChoke = result.four_f_Lmax_over_D;
    var frac = result.fld > 0 ? Math.max(0.05, Math.min(0.95, remainChoke / result.fld)) : 1;
    return function (t) {
      if (t > frac) {
        return null;
      }
      var local = t / frac;
      var target = remainChoke * (1 - local);
      var mach = Lab.machFromFannoFriction(Math.max(target, 0), gamma, supersonic);
      return velocity(mach, gamma);
    };
  }
  var level = velocity(inlet, gamma);
  return function () {
    return level;
  };
};

Lab.drawDuctFlow = function (ctx, w, h, result) {
  var box = Lab.ductFrame(ctx, w, h);
  var sampler = Lab.speedSampler(result);
  Lab.streamFunction(ctx, box, function (t) {
    return sampler(t) != null;
  });
  if (result.mode === "fanno") {
    Lab.text(ctx, box.x0, 28, "Adiabatic duct — wall friction, constant area", "#1b2631", 14);
    ctx.strokeStyle = "#7b241c";
    for (var tick = 0; tick < 14; tick++) {
      var x = box.x0 + (box.x1 - box.x0) * (tick + 0.5) / 14;
      ctx.beginPath();
      ctx.moveTo(x, box.y0);
      ctx.lineTo(x - 7, box.y0 - 8);
      ctx.moveTo(x, box.y1);
      ctx.lineTo(x - 7, box.y1 + 8);
      ctx.stroke();
    }
  } else {
    Lab.text(ctx, box.x0, 28, "Frictionless duct — heat addition, constant area", "#1b2631", 14);
    ctx.strokeStyle = "#b9770e";
    ctx.fillStyle = "#b9770e";
    for (var heat = 0; heat < 8; heat++) {
      var hx = box.x0 + (box.x1 - box.x0) * (heat + 0.5) / 8;
      ctx.beginPath();
      ctx.moveTo(hx, box.y0 - 16);
      ctx.lineTo(hx, box.y0 - 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(hx, box.y0 - 2);
      ctx.lineTo(hx - 4, box.y0 - 8);
      ctx.lineTo(hx + 4, box.y0 - 8);
      ctx.fill();
    }
  }
  Lab.stationLine(ctx, box, 0.18, "M = " + Lab.fmt(result.M));
  var lines = [
    "T/T* = " + Lab.fmt(result.T_over_Tstar),
    "p/p* = " + Lab.fmt(result.p_over_pstar),
    "V/V* = " + Lab.fmt(result.V_over_Vstar),
    "pt/pt* = " + Lab.fmt(result.pt_over_ptstar)
  ];
  if (result.mode === "fanno") {
    lines.push("4fL*/D = " + Lab.fmt(result.four_f_Lmax_over_D));
    if (result.fld != null) {
      lines.push("4fL/D = " + Lab.fmt(result.fld));
    }
  } else {
    lines.push("Tt/Tt* = " + Lab.fmt(result.Tt_over_Ttstar));
    if (result.tt_ratio != null) {
      lines.push("Tt2/Tt1 = " + Lab.fmt(result.tt_ratio));
    }
  }
  if (result.exit_mach != null) {
    lines.push("exit M = " + Lab.fmt(result.exit_mach));
  }
  if (result.choked_by_length === "yes" || result.choked_by_heat === "yes") {
    lines.push("choked");
  }
  lines.forEach(function (line, index) {
    Lab.text(ctx, box.x0, box.y1 + 22 + index * 16, line, "#34495e", 12);
  });
  Lab.text(ctx, box.x0, h - 8, "Contours of the stream function ψ. Equal spacing is the constant mass flux ρV.", "#5d6d7e", 11);
};

Lab.ray = function (ctx, x, y, angle, length, color, width) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width || 1.6;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + length * Math.cos(angle), y + length * Math.sin(angle));
  ctx.stroke();
};

Lab.drawWedge = function (ctx, w, h, result) {
  var originX = w * 0.28;
  var originY = h * 0.62;
  var length = Math.min(w, h) * 0.42;
  var delta = result.delta;
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(originX, originY);
  ctx.lineTo(originX + length, originY);
  ctx.lineTo(originX + length * Math.cos(delta), originY - length * Math.sin(delta));
  ctx.closePath();
  ctx.fillStyle = "#d6eaf8";
  ctx.fill();
  ctx.stroke();
  Lab.text(ctx, 16, 28, "Two-dimensional wedge", "#1b2631", 14);
  if (!result.attached || result.theta == null) {
    ctx.strokeStyle = "#922b21";
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.arc(originX - 8, originY - 10, 36, -0.2, -2.4, true);
    ctx.stroke();
    ctx.setLineDash([]);
    Lab.text(ctx, 16, 52, "Detached shock. δmax = " + Lab.fmt(Lab.deg(result.delta_max)) + " deg", "#922b21", 13);
    return;
  }
  var theta = result.theta;
  Lab.ray(ctx, originX, originY, -theta, length * 1.15, "#922b21", 2);
  Lab.text(ctx, originX + 12, originY - length * 0.55, "θ = " + Lab.fmt(Lab.deg(theta)) + "°", "#922b21", 12);
  if (result.shock !== "mach-wave" && result.fan === "yes") {
    var shoulder = originX + length;
    for (var fan = 0; fan < 5; fan++) {
      var angle = -delta * fan / 4;
      Lab.ray(ctx, shoulder, originY, angle - Math.PI / 2 * 0 + (-0.15 - fan * 0.12), length * 0.45, "#1a5276", 1);
    }
    Lab.text(ctx, shoulder - 10, originY + 28, "shoulder fan", "#1a5276", 12);
  }
  Lab.text(ctx, 16, h - 36, "M2 = " + Lab.fmt(result.M2) + "   p2/p1 = " + Lab.fmt(result.p2_over_p1), "#34495e", 13);
  Lab.text(ctx, 16, h - 16, "Freestream expansion M = " + Lab.fmt(result.pm_M) + "  (" + result.expansion + ")", "#34495e", 13);
};

Lab.drawCone = function (ctx, w, h, result) {
  var noseX = w * 0.22;
  var axis = h * 0.5;
  var length = Math.min(w * 0.5, 280);
  var delta = result.delta;
  ctx.fillStyle = "#d5f5e3";
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(noseX, axis);
  ctx.lineTo(noseX + length, axis - length * Math.tan(delta));
  ctx.lineTo(noseX + length, axis + length * Math.tan(delta));
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  Lab.text(ctx, 16, 28, "Right circular cone, zero incidence", "#1b2631", 14);
  if (!result.attached || result.theta == null) {
    ctx.strokeStyle = "#922b21";
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.arc(noseX, axis, 42, -1.2, 1.2);
    ctx.stroke();
    ctx.setLineDash([]);
    Lab.text(ctx, 16, 52, "Detached. δmax = " + Lab.fmt(Lab.deg(result.delta_max)) + " deg", "#922b21", 13);
    return;
  }
  var theta = result.theta;
  Lab.ray(ctx, noseX, axis, -theta, length * 1.2, "#922b21", 2);
  Lab.ray(ctx, noseX, axis, theta, length * 1.2, "#922b21", 2);
  Lab.text(ctx, noseX + 20, axis - length * 0.45, "θ = " + Lab.fmt(Lab.deg(theta)) + "°", "#922b21", 12);
  Lab.text(ctx, 16, h - 36, "Mc = " + Lab.fmt(result.Mc) + "   pc/p∞ = " + Lab.fmt(result.pc_over_p1), "#34495e", 13);
  Lab.text(ctx, 16, h - 16, "Cp = " + Lab.fmt(result.Cp) + "   shock " + result.shock, "#34495e", 13);
};

Lab.drawDiamond = function (ctx, w, h, result) {
  var chord = Math.min(w * 0.46, 340);
  var midX = w * 0.42;
  var midY = h * 0.48;
  var eps = result.epsilon;
  var alpha = result.alpha;
  function rot(x, y) {
    var c = Math.cos(alpha);
    var s = Math.sin(alpha);
    var xp = x * c + y * s;
    var yp = -x * s + y * c;
    return [midX + xp, midY - yp];
  }
  var le = rot(-chord / 2, 0);
  var top = rot(0, chord / 2 * Math.tan(eps));
  var te = rot(chord / 2, 0);
  var bot = rot(0, -chord / 2 * Math.tan(eps));
  ctx.fillStyle = "#f5e6d3";
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(le[0], le[1]);
  ctx.lineTo(top[0], top[1]);
  ctx.lineTo(te[0], te[1]);
  ctx.lineTo(bot[0], bot[1]);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  function shockRay(origin, mathAngle) {
    if (mathAngle == null || !isFinite(mathAngle)) {
      return;
    }
    Lab.ray(ctx, origin[0], origin[1], -mathAngle, chord * 0.55, "#922b21", 1.8);
  }
  function fanAt(origin, wallIn, machIn, turn, side) {
    if (!(machIn > 1) || !(turn > 0)) {
      return;
    }
    var rays = 6;
    var nu0 = Lab.prandtlMeyer(machIn, result.gamma);
    for (var index = 0; index <= rays; index++) {
      var fraction = index / rays;
      var turned = wallIn - side * fraction * turn;
      var localMach;
      try {
        localMach = Lab.invertPrandtlMeyer(nu0 + fraction * turn, result.gamma);
      } catch (err) {
        continue;
      }
      var mathAngle = turned + side * Lab.machAngle(localMach);
      Lab.ray(
        ctx,
        origin[0],
        origin[1],
        -mathAngle,
        chord * 0.42,
        "#1a5276",
        index === 0 || index === rays ? 1.7 : 0.9
      );
    }
  }
  if (result.wave_u1 === "shock" || result.wave_u1 === "mach-wave") {
    shockRay(le, result.theta_u1);
  } else if (result.wave_u1 === "expansion") {
    fanAt(le, 0, result.mach, Math.abs(result.delta_u1), 1);
  }
  if (result.wave_l1 === "shock" || result.wave_l1 === "mach-wave") {
    shockRay(le, -result.theta_l1);
  } else if (result.wave_l1 === "expansion") {
    fanAt(le, 0, result.mach, Math.abs(result.delta_l1), -1);
  }
  if (result.wave_u2 === "expansion") {
    fanAt(top, result.delta_u1, result.M_u1, result.shoulder, 1);
  } else if (result.wave_u2 === "shock" || result.wave_u2 === "mach-wave") {
    shockRay(top, result.theta_u2);
  }
  if (result.wave_l2 === "expansion") {
    fanAt(bot, -result.delta_l1, result.M_l1, result.shoulder, -1);
  } else if (result.wave_l2 === "shock" || result.wave_l2 === "mach-wave") {
    shockRay(bot, result.theta_l2 == null ? null : -result.theta_l2);
  }
  if (result.solution === "ok") {
    var upperWall = -(result.epsilon + result.alpha);
    var lowerWall = result.epsilon - result.alpha;
    try {
      var upperExit = Lab.weakObliqueShock(result.M_u2, result.gamma, Math.abs(upperWall));
      if (upperExit.ok && upperExit.theta != null) {
        shockRay(te, upperWall + upperExit.theta);
      }
    } catch (err) {
      upperWall = null;
    }
    try {
      var lowerExit = Lab.weakObliqueShock(result.M_l2, result.gamma, Math.abs(lowerWall));
      if (lowerExit.ok && lowerExit.theta != null) {
        shockRay(te, lowerWall - lowerExit.theta);
      }
    } catch (err2) {
      lowerWall = null;
    }
  }
  Lab.text(ctx, 16, 28, "Diamond airfoil  " + result.solution, "#1b2631", 14);
  Lab.text(ctx, 16, h - 36, "cl = " + Lab.fmt(result.cl) + "   cd = " + Lab.fmt(result.cd), "#34495e", 13);
  Lab.text(ctx, 16, h - 16, "Red: nose and trailing-edge shocks. Blue: shoulder fans through 2ε.", "#5d6d7e", 12);
};

Lab.drawPitot = function (ctx, w, h, result) {
  var y = h * 0.42;
  ctx.strokeStyle = "#1a5276";
  ctx.lineWidth = 1.4;
  for (var row = -2; row <= 2; row++) {
    var yy = y + row * 18;
    ctx.beginPath();
    ctx.moveTo(24, yy);
    ctx.lineTo(w * 0.48, yy);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w * 0.48, yy);
    ctx.lineTo(w * 0.48 - 8, yy - 4);
    ctx.lineTo(w * 0.48 - 8, yy + 4);
    ctx.fill();
  }
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.strokeRect(w * 0.5, y - 28, 18, 56);
  ctx.beginPath();
  ctx.moveTo(w * 0.5 + 18, y);
  ctx.lineTo(w * 0.78, y);
  ctx.stroke();
  Lab.text(ctx, w * 0.5, y - 40, "pitot", "#1b2631", 13);
  if (result.branch === "supersonic") {
    ctx.strokeStyle = "#922b21";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(w * 0.5 - 16, y - 40);
    ctx.lineTo(w * 0.5 - 16, y + 40);
    ctx.stroke();
    Lab.text(ctx, w * 0.5 - 70, y - 48, "normal shock", "#922b21", 12);
  }
  Lab.text(ctx, 16, 28, result.relation === "rayleigh_pitot" ? "Rayleigh–Pitot branch" : "Isentropic stagnation branch", "#1b2631", 14);
  Lab.text(ctx, 16, h - 52, "Measured pt/p = " + Lab.fmt(result.ratio), "#34495e", 13);
  Lab.text(ctx, 16, h - 32, "Sonic switch pt/p = " + Lab.fmt(result.sonic_ratio), "#34495e", 13);
  Lab.text(ctx, 16, h - 12, "M = " + Lab.fmt(result.M) + "    q = " + Lab.fmt(result.q) + " Pa", "#34495e", 13);
};

Lab.drawIsentropic = function (ctx, w, h, result) {
  var wall = w * 0.72;
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(wall, 40);
  ctx.lineTo(wall, h - 40);
  ctx.stroke();
  ctx.strokeStyle = "#1a5276";
  ctx.lineWidth = 1.3;
  for (var row = 0; row < 5; row++) {
    var y = 70 + row * ((h - 140) / 4);
    ctx.beginPath();
    ctx.moveTo(30, y + (row - 2) * 10);
    ctx.quadraticCurveTo(wall * 0.55, y, wall - 6, h * 0.5);
    ctx.stroke();
  }
  Lab.text(ctx, wall + 8, h * 0.5, "stagnation", "#922b21", 13);
  Lab.text(ctx, 16, 28, "Isentropic slowdown to a stagnation point", "#1b2631", 14);
  Lab.text(ctx, 16, h - 56, "M = " + Lab.fmt(result.M) + "    Tt/T = " + Lab.fmt(result.Tt_over_T), "#34495e", 13);
  Lab.text(ctx, 16, h - 36, "pt/p = " + Lab.fmt(result.pt_over_p) + "    ρt/ρ = " + Lab.fmt(result.rhot_over_rho), "#34495e", 13);
  Lab.text(ctx, 16, h - 16, "No shock. Totals are the isentropic reservoir state.", "#5d6d7e", 12);
};

Lab.drawGlauert = function (ctx, w, h, result) {
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(w * 0.28, h * 0.48, 90, 16, -0.08, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "#922b21";
  ctx.beginPath();
  ctx.arc(w * 0.22, h * 0.48 - 16, 4, 0, Math.PI * 2);
  ctx.fill();
  Lab.text(ctx, w * 0.22 - 10, h * 0.48 - 28, "Cp,min", "#922b21", 12);
  Lab.text(ctx, 16, 28, "Prandtl–Glauert, two-dimensional", "#1b2631", 14);
  Lab.text(ctx, w * 0.5, h * 0.4, "β = " + Lab.fmt(result.beta), "#1b2631", 16);
  Lab.text(ctx, w * 0.5, h * 0.4 + 22, "CL = CL0 / β = " + Lab.fmt(result.CL), "#34495e", 13);
  Lab.text(ctx, w * 0.5, h * 0.4 + 42, "Cd stays " + Lab.fmt(result.Cd) + " (not divided by β)", "#34495e", 13);
  Lab.text(ctx, 16, h - 16, "Mcr = " + Lab.fmt(result.M_cr) + " from Cp0,min = " + Lab.fmt(result.Cp0_min), "#34495e", 13);
};

Lab.chart = function (ctx, w, h, series, xOf, opts) {
  var axes = opts && opts.axes;
  var pad = { l: axes ? 72 : 54, r: axes ? 28 : 16, t: 28, b: axes ? 52 : 36 };
  var plotW = w - pad.l - pad.r;
  var plotH = h - pad.t - pad.b;
  var xs = [];
  series.forEach(function (entry) {
    entry.points.forEach(function (point) {
      xs.push(point[0]);
    });
  });
  var xMin = Math.min.apply(null, xs);
  var xMax = Math.max.apply(null, xs);
  var yMax = 0.5;
  if (opts && opts.yMax != null && isFinite(opts.yMax)) {
    yMax = opts.yMax;
  } else {
    series.forEach(function (entry) {
      entry.points.forEach(function (point) {
        if (isFinite(point[1]) && point[1] > yMax) {
          yMax = point[1];
        }
      });
      if (entry.mark != null && entry.mark[1] > yMax) {
        yMax = entry.mark[1];
      }
    });
    yMax *= 1.08;
  }
  function X(x) {
    var frac;
    if (opts && opts.log) {
      frac = Math.log(Math.max(x, 1e-6) / xMin) / Math.log(xMax / xMin);
    } else {
      frac = (x - xMin) / (xMax - xMin || 1);
    }
    return pad.l + frac * plotW;
  }
  function Y(y) {
    return pad.t + (1 - Math.max(0, y) / yMax) * plotH;
  }
  ctx.strokeStyle = axes ? "#1b2631" : "#d5d8dc";
  ctx.lineWidth = axes ? 1.2 : 1;
  ctx.strokeRect(pad.l, pad.t, plotW, plotH);
  if (axes) {
    ctx.fillStyle = "#34495e";
    ctx.font = "11px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.strokeStyle = "#1b2631";
    ctx.lineWidth = 1;
    var xStep = Lab.niceStep(xMax - xMin, 5);
    var xv0 = Math.ceil((xMin - xStep * 1e-9) / xStep) * xStep;
    ctx.textAlign = "center";
    for (var xv = xv0; xv <= xMax + xStep * 1e-9; xv += xStep) {
      var px = X(xv);
      ctx.beginPath();
      ctx.moveTo(px, pad.t + plotH);
      ctx.lineTo(px, pad.t + plotH + 5);
      ctx.stroke();
      ctx.fillText(Lab.axisNum(xv), px, pad.t + plotH + 16);
    }
    var yStep = Lab.niceStep(yMax, 5);
    var yv0 = 0;
    ctx.textAlign = "right";
    for (var yv = yv0; yv <= yMax + yStep * 1e-9; yv += yStep) {
      var py = Y(yv);
      ctx.beginPath();
      ctx.moveTo(pad.l - 5, py);
      ctx.lineTo(pad.l, py);
      ctx.stroke();
      ctx.fillText(Lab.axisNum(yv), pad.l - 8, py + 4);
    }
    ctx.textAlign = "left";
    if (opts.ylabel) {
      ctx.save();
      ctx.translate(14, pad.t + plotH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.textAlign = "center";
      ctx.fillText(opts.ylabel, 0, 0);
      ctx.restore();
    }
  }
  series.forEach(function (entry) {
    ctx.strokeStyle = entry.color;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    var started = false;
    entry.points.forEach(function (point) {
      if (!isFinite(point[1]) || point[1] < 0 || point[1] > yMax * 1.02) {
        started = false;
        return;
      }
      var px = X(point[0]);
      var py = Y(point[1]);
      if (!started) {
        ctx.moveTo(px, py);
        started = true;
      } else {
        ctx.lineTo(px, py);
      }
    });
    ctx.stroke();
    if (entry.mark) {
      ctx.fillStyle = entry.color;
      ctx.fillRect(X(entry.mark[0]) - 3, Y(entry.mark[1]) - 3, 6, 6);
    }
  });
  Lab.text(ctx, pad.l, 16, opts && opts.title ? opts.title : "", "#1b2631", 13);
  if (axes && opts && opts.xlabel) {
    ctx.fillStyle = "#34495e";
    ctx.font = "12px Segoe UI, Helvetica, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(opts.xlabel, pad.l + plotW / 2, h - 12);
    ctx.textAlign = "left";
  } else {
    Lab.text(ctx, pad.l, h - 8, opts && opts.xlabel ? opts.xlabel : "Mach", "#5d6d7e", 11);
  }
  var legendX = pad.l + 8;
  series.forEach(function (entry, index) {
    Lab.text(ctx, legendX + index * 92, pad.t + 14, entry.label, entry.color, 11);
  });
};

Lab.sample = function (lo, hi, count, func) {
  var points = [];
  for (var i = 0; i < count; i++) {
    var x = lo + (hi - lo) * i / (count - 1);
    points.push([x, func(x)]);
  }
  return points;
};

Lab.sampleLog = function (lo, hi, count, func) {
  var points = [];
  for (var i = 0; i < count; i++) {
    var x = lo * Math.pow(hi / lo, i / (count - 1));
    points.push([x, func(x)]);
  }
  return points;
};

Lab.drawCurves = function (canvas, result) {
  var fit = Lab.fit(canvas, 280);
  var ctx = fit.ctx;
  var gamma = result.gamma;
  if (!result.ok) {
    Lab.text(ctx, 16, 40, result.error || "No curves", "#922b21", 14);
    return;
  }
  if (result.mode === "isentropic") {
    var hi = Math.max(3, result.M * 1.15 || 3);
    Lab.chart(ctx, fit.w, fit.h, [
      { label: "pt/p", color: "#1a5276", points: Lab.sample(0, hi, 80, function (m) { return Lab.stagnationPressureRatio(m, gamma); }), mark: [result.M, result.pt_over_p] },
      { label: "Tt/T", color: "#922b21", points: Lab.sample(0, hi, 80, function (m) { return Lab.stagnationTemperatureRatio(m, gamma); }), mark: [result.M, result.Tt_over_T] }
    ], null, { title: "Isentropic stagnation ratios", xlabel: "Mach" });
  } else if (result.mode === "normal") {
    var nHi = Math.max(6, result.M1 * 1.15);
    Lab.chart(ctx, fit.w, fit.h, [
      { label: "M2", color: "#1a5276", points: Lab.sample(1, nHi, 80, function (m) { return Math.sqrt(Lab.normalShockMachSq(m, gamma)); }), mark: [result.M1, result.M2] },
      { label: "p2/p1", color: "#922b21", points: Lab.sample(1, nHi, 80, function (m) { return Lab.normalShockPressure(m, gamma); }), mark: [result.M1, result.p2_over_p1] },
      { label: "T2/T1", color: "#b9770e", points: Lab.sample(1, nHi, 80, function (m) { return Lab.normalShockTemperature(m, gamma); }), mark: [result.M1, result.T2_over_T1] },
      { label: "pt2/pt1", color: "#196f3d", points: Lab.sample(1, nHi, 80, function (m) { return Lab.normalShockStagnationPressure(m, gamma); }), mark: [result.M1, result.pt2_over_pt1] }
    ], null, { title: "Normal-shock jumps versus M1", xlabel: "Upstream Mach" });
  } else if (result.mode === "fanno") {
    var fHi = Math.max(5, result.M * 1.25);
    Lab.chart(ctx, fit.w, fit.h, [
      { label: "T/T*", color: "#922b21", points: Lab.sampleLog(0.05, fHi, 80, function (m) { return Lab.fannoTemperatureRatio(m, gamma); }), mark: [result.M, result.T_over_Tstar] },
      { label: "p/p*", color: "#1a5276", points: Lab.sampleLog(0.05, fHi, 80, function (m) { return Lab.fannoPressureRatio(m, gamma); }), mark: [result.M, result.p_over_pstar] },
      { label: "V/V*", color: "#196f3d", points: Lab.sampleLog(0.05, fHi, 80, function (m) { return Lab.fannoVelocityRatio(m, gamma); }), mark: [result.M, result.V_over_Vstar] },
      { label: "pt/pt*", color: "#6c3483", points: Lab.sampleLog(0.05, fHi, 80, function (m) { return Lab.fannoStagnationPressureRatio(m, gamma); }), mark: [result.M, result.pt_over_ptstar] }
    ], null, { title: "Fanno ratios to the sonic state", xlabel: "Mach (log)", log: true });
  } else if (result.mode === "rayleigh") {
    var rHi = Math.max(5, result.M * 1.25);
    Lab.chart(ctx, fit.w, fit.h, [
      { label: "T/T*", color: "#922b21", points: Lab.sampleLog(0.05, rHi, 80, function (m) { return Lab.rayleighTemperatureRatio(m, gamma); }), mark: [result.M, result.T_over_Tstar] },
      { label: "p/p*", color: "#1a5276", points: Lab.sampleLog(0.05, rHi, 80, function (m) { return Lab.rayleighPressureRatio(m, gamma); }), mark: [result.M, result.p_over_pstar] },
      { label: "V/V*", color: "#196f3d", points: Lab.sampleLog(0.05, rHi, 80, function (m) { return Lab.rayleighVelocityRatio(m, gamma); }), mark: [result.M, result.V_over_Vstar] },
      { label: "Tt/Tt*", color: "#b9770e", points: Lab.sampleLog(0.05, rHi, 80, function (m) { return Lab.rayleighStagnationTemperatureRatio(m, gamma); }), mark: [result.M, result.Tt_over_Ttstar] }
    ], null, { title: "Rayleigh ratios to the sonic state", xlabel: "Mach (log)", log: true });
  } else if (result.mode === "prandtl_glauert") {
    var xLo = 0.35;
    var xHi = 0.92;
    var betaPts = Lab.sample(xLo, xHi, 70, function (m) {
      return result.CL0 == null ? 1 / Lab.prandtlGlauertFactor(m) : Lab.prandtlGlauertCoefficient(result.CL0, m);
    });
    var critPts = Lab.sample(xLo, xHi, 70, function (m) {
      return -Lab.criticalPressureCoefficient(gamma, m);
    });
    var yCap = 1;
    betaPts.forEach(function (point) {
      if (isFinite(point[1])) {
        yCap = Math.max(yCap, point[1]);
      }
    });
    critPts.forEach(function (point) {
      if (point[0] >= 0.45 && isFinite(point[1])) {
        yCap = Math.max(yCap, point[1]);
      }
    });
    if (result.CL != null && isFinite(result.CL)) {
      yCap = Math.max(yCap, result.CL);
    }
    if (result.Cp_crit != null && isFinite(result.Cp_crit)) {
      yCap = Math.max(yCap, -result.Cp_crit);
    }
    var series = [
      { label: "CL", color: "#1a5276", points: betaPts, mark: [result.M, result.CL] },
      { label: "−Cp,crit", color: "#922b21", points: critPts, mark: result.Cp_crit == null ? null : [result.M, -result.Cp_crit] }
    ];
    Lab.chart(ctx, fit.w, fit.h, series, null, {
      title: "Compressible lift and critical pressure",
      xlabel: "Freestream Mach",
      ylabel: "Coefficient",
      axes: true,
      yMax: Lab.niceCeil(yCap * 1.05)
    });
  }
};

Lab.drawSchematic = function (canvas, result) {
  var fit = Lab.fit(canvas, result.mode === "normal" || result.mode === "fanno" || result.mode === "rayleigh" ? 360 : 320);
  var ctx = fit.ctx;
  if (!result.ok) {
    Lab.text(ctx, 16, 40, result.error || "Not solved", "#922b21", 14);
    return;
  }
  if (result.mode === "normal") Lab.drawNormal(ctx, fit.w, fit.h, result);
  else if (result.mode === "fanno" || result.mode === "rayleigh") Lab.drawDuctFlow(ctx, fit.w, fit.h, result);
  else if (result.mode === "wedge") Lab.drawWedge(ctx, fit.w, fit.h, result);
  else if (result.mode === "cone") Lab.drawCone(ctx, fit.w, fit.h, result);
  else if (result.mode === "diamond") Lab.drawDiamond(ctx, fit.w, fit.h, result);
  else if (result.mode === "rayleigh_pitot") Lab.drawPitot(ctx, fit.w, fit.h, result);
  else if (result.mode === "isentropic") Lab.drawIsentropic(ctx, fit.w, fit.h, result);
  else if (result.mode === "prandtl_glauert") Lab.drawGlauert(ctx, fit.w, fit.h, result);
};

Lab.CURVE_MODES = {
  isentropic: true,
  normal: true,
  fanno: true,
  rayleigh: true,
  prandtl_glauert: true
};

Lab.render = function (seed) {
  var result = Lab.designPoint(seed);
  var schematic = document.getElementById("schematic");
  var curves = document.getElementById("curves");
  Lab.drawSchematic(schematic, result);
  if (Lab.CURVE_MODES[seed.mode]) {
    curves.hidden = false;
    Lab.drawCurves(curves, result);
  } else {
    curves.hidden = true;
  }
  var status = document.getElementById("status");
  status.textContent = result.ok
    ? "Live " + seed.mode.replace("_", " ") + " solution. Export repeats the one-shot CLI."
    : result.error;
  var readout = document.getElementById("readout");
  readout.innerHTML = "";
  Lab.rowsFor(result).forEach(function (row) {
    var wrap = document.createElement("div");
    var dt = document.createElement("dt");
    var dd = document.createElement("dd");
    dt.textContent = row[0];
    dd.textContent = row[1];
    wrap.appendChild(dt);
    wrap.appendChild(dd);
    readout.appendChild(wrap);
  });
  document.getElementById("export").value = Lab.exportText(seed);
};

Lab.readOptional = function (id) {
  var raw = document.getElementById(id).value.trim();
  if (raw === "") {
    return null;
  }
  var value = Number(raw);
  return isFinite(value) ? value : null;
};

Lab.readSeed = function () {
  return {
    mode: document.getElementById("mode").value,
    mach: Number(document.getElementById("mach").value),
    delta: Number(document.getElementById("delta").value) * Math.PI / 180,
    epsilon: Number(document.getElementById("epsilon").value) * Math.PI / 180,
    alpha: Number(document.getElementById("alpha").value) * Math.PI / 180,
    gamma: Number(document.getElementById("gamma").value),
    fld: Lab.readOptional("fld"),
    ttRatio: Lab.readOptional("tt-ratio"),
    clInc: Number(document.getElementById("cl-inc").value),
    cmInc: Number(document.getElementById("cm-inc").value),
    cdInc: Number(document.getElementById("cd-inc").value),
    cpminInc: Number(document.getElementById("cpmin").value),
    pitot: Number(document.getElementById("pitot").value),
    staticPressure: Number(document.getElementById("static").value),
    temperature: Lab.readOptional("temperature"),
    pressure: Lab.readOptional("pressure"),
    density: Lab.readOptional("density")
  };
};

Lab.showGroups = function (mode) {
  document.querySelectorAll("[data-modes]").forEach(function (node) {
    var modes = node.getAttribute("data-modes").split(/\s+/);
    node.hidden = modes.indexOf(mode) < 0;
  });
};

Lab.syncRange = function (numberId, rangeId) {
  var number = document.getElementById(numberId);
  var range = document.getElementById(rangeId);
  number.addEventListener("input", function () {
    if (number.value !== "") {
      range.value = number.value;
    }
  });
  range.addEventListener("input", function () {
    number.value = range.value;
  });
};

Lab.applySeed = function (seed) {
  document.getElementById("mode").value = seed.mode;
  document.getElementById("mach").value = seed.mach;
  document.getElementById("mach-range").value = seed.mach;
  document.getElementById("delta").value = seed.delta * 180 / Math.PI;
  document.getElementById("delta-range").value = seed.delta * 180 / Math.PI;
  document.getElementById("epsilon").value = seed.epsilon * 180 / Math.PI;
  document.getElementById("epsilon-range").value = seed.epsilon * 180 / Math.PI;
  document.getElementById("alpha").value = seed.alpha * 180 / Math.PI;
  document.getElementById("alpha-range").value = seed.alpha * 180 / Math.PI;
  document.getElementById("gamma").value = seed.gamma;
  document.getElementById("gamma-range").value = seed.gamma;
  document.getElementById("fld").value = seed.fld == null ? "" : seed.fld;
  document.getElementById("tt-ratio").value = seed.ttRatio == null ? "" : seed.ttRatio;
  document.getElementById("cl-inc").value = seed.clInc;
  document.getElementById("cm-inc").value = seed.cmInc;
  document.getElementById("cd-inc").value = seed.cdInc;
  document.getElementById("cpmin").value = seed.cpminInc;
  document.getElementById("pitot").value = seed.pitot;
  document.getElementById("static").value = seed.staticPressure;
  document.getElementById("temperature").value = seed.temperature == null ? "" : seed.temperature;
  document.getElementById("pressure").value = seed.pressure == null ? "" : seed.pressure;
  document.getElementById("density").value = seed.density == null ? "" : seed.density;
  Lab.showGroups(seed.mode);
};

Lab.boot = function (seed) {
  Lab.applySeed(seed);
  ["mach", "delta", "epsilon", "alpha", "gamma"].forEach(function (name) {
    Lab.syncRange(name, name + "-range");
  });
  var machDefaults = {
    isentropic: 2,
    normal: 2,
    wedge: 2,
    cone: 2,
    diamond: 2,
    fanno: 0.5,
    rayleigh: 0.5,
    prandtl_glauert: 0.6
  };
  document.getElementById("mode").addEventListener("change", function () {
    var mode = document.getElementById("mode").value;
    var mach = Number(document.getElementById("mach").value);
    var fallback = machDefaults[mode];
    if (fallback != null) {
      var illegal = (mode === "prandtl_glauert" && !(mach >= 0 && mach < 1)) ||
        ((mode === "normal" || mode === "wedge" || mode === "cone" || mode === "diamond") && !(mach > 1)) ||
        ((mode === "fanno" || mode === "rayleigh") && !(mach >= 0.001 && mach <= 50));
      if (illegal) {
        document.getElementById("mach").value = fallback;
        document.getElementById("mach-range").value = fallback;
      }
    }
    Lab.showGroups(mode);
    Lab.render(Lab.readSeed());
  });
  document.getElementById("app").addEventListener("input", function () {
    Lab.render(Lab.readSeed());
  });
  Lab.render(Lab.readSeed());
};
