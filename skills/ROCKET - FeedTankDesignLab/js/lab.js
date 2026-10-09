/* Feed and tank lab. Recomputes the page from the seed. */
var Lab = Lab || {};

Lab.trim = function (value) {
  if (typeof value !== "number" || !isFinite(value)) return String(value);
  return String(Number(value.toPrecision(8)));
};

Lab.designPoint = function (seed) {
  try {
    var flows = Lab.splitFlows(seed.flowMode, seed.mdot, seed.r, seed.ox.mdot, seed.fuel.mdot);
    var g = Lab.G0;
    var names = ["ox", "fuel"];
    var branches = {};
    for (var i = 0; i < names.length; i += 1) {
      var name = names[i];
      var input = seed[name];
      var mdot = name === "ox" ? flows.mdotOx : flows.mdotFuel;
      var feed = Lab.supplyPressure(seed.pc, input.dpInj, seed.dpLine, input.rho, seed.height, g);
      var volume = Lab.loadedVolume(mdot, seed.tb, input.rho, seed.residuals);
      var expelled = (1 - seed.residuals) * volume;
      var shellVolume = volume;
      if (seed.architecture === "pressure") {
        if (!(input.n > 0)) throw new Error(name + " polytropic exponent must be > 0");
        if (!(input.v0 > 0)) throw new Error(name + " initial ullage must be > 0");
        shellVolume = volume + input.v0;
      }
      var orifice = Lab.orificeSolve(mdot, input.rho, input.cd, input.dpInj, input.count);
      var tankPressure = seed.architecture === "pressure" ? input.p0 : input.meop;
      var shell = Lab.tankShell(
        shellVolume, tankPressure, seed.allowable, seed.rhoMat,
        seed.etaWeld, seed.designFactor, seed.shape, seed.radius
      );
      var row = {
        mdot: mdot,
        volume: volume,
        expelled: expelled,
        manifold: feed.manifold,
        head: feed.head,
        supply: feed.supply,
        area: orifice.area,
        speed: orifice.speed,
        diameter: orifice.diameter,
        tankPressure: tankPressure,
        pDesign: shell.pressure,
        radius: shell.radius,
        thickness: shell.thickness,
        tHead: shell.tHead,
        length: shell.length,
        sigma: shell.sigma,
        sigmaLong: shell.sigmaLong,
        margin: shell.margin,
        tOverR: shell.tOverR,
        mass: shell.mass
      };
      if (seed.architecture === "pressure") {
        var end = Lab.blowdown(input.p0, input.v0, expelled, input.n);
        row.p2 = end.p2;
        row.v2 = end.v2;
        row.flagged = end.p2 < feed.supply;
        row.curve = Lab.blowdownCurve(input.p0, input.v0, expelled, input.n, 41);
        row.history = Lab.pressureHistory(input.p0, input.v0, expelled, input.n, seed.tb, 81);
      } else {
        var rise = feed.supply - input.pin;
        if (!(rise > 0)) throw new Error(name + " pump inlet is not below the supply pressure");
        var power = Lab.pumpPower(mdot, input.rho, rise, input.eta, input.etaDrive);
        row.rise = rise;
        row.shaft = power.shaft;
        row.drive = power.drive;
        row.hyd = power.hyd;
      }
      branches[name] = row;
    }
    return {
      ok: true,
      architecture: seed.architecture,
      flowMode: seed.flowMode,
      mdot: flows.mdot,
      r: flows.r,
      ox: branches.ox,
      fuel: branches.fuel
    };
  } catch (err) {
    return { ok: false, error: err.message || String(err) };
  }
};

Lab.num = function (id) {
  return Number(document.getElementById(id).value);
};

Lab.branchInput = function (name, key) {
  var field = document.querySelector('fieldset[data-branch="' + name + '"] [data-key="' + key + '"]');
  return Number(field.value);
};

Lab.readSeed = function () {
  var architecture = document.querySelector('input[name="architecture"]:checked').value;
  var flowMode = document.querySelector('input[name="flowMode"]:checked').value;
  return {
    architecture: architecture,
    flowMode: flowMode,
    pc: Lab.num("pc"),
    dpLine: Lab.num("dp-line"),
    height: Lab.num("height"),
    tb: Lab.num("tb"),
    residuals: Lab.num("residuals"),
    allowable: Lab.num("allowable"),
    rhoMat: Lab.num("rho-mat"),
    etaWeld: 1,
    designFactor: 1,
    shape: document.getElementById("shape").value,
    radius: Lab.num("radius"),
    mdot: Lab.num("mdot"),
    r: Lab.num("ratio"),
    ox: Lab.readBranch("ox"),
    fuel: Lab.readBranch("fuel")
  };
};

Lab.readBranch = function (name) {
  return {
    mdot: Lab.branchInput(name, "mdot"),
    rho: Lab.branchInput(name, "rho"),
    dpInj: Lab.branchInput(name, "dpInj"),
    cd: Lab.branchInput(name, "cd"),
    count: Lab.branchInput(name, "count"),
    p0: Lab.branchInput(name, "p0"),
    v0: Lab.branchInput(name, "v0"),
    n: Lab.branchInput(name, "n"),
    pin: Lab.branchInput(name, "pin"),
    eta: Lab.branchInput(name, "eta"),
    etaDrive: Lab.branchInput(name, "etaDrive"),
    meop: Lab.branchInput(name, "meop")
  };
};

Lab.writeSeed = function (seed) {
  document.querySelector('input[name="architecture"][value="' + seed.architecture + '"]').checked = true;
  document.querySelector('input[name="flowMode"][value="' + seed.flowMode + '"]').checked = true;
  document.getElementById("mdot").value = seed.mdot;
  document.getElementById("ratio").value = seed.r;
  document.getElementById("pc").value = seed.pc;
  document.getElementById("dp-line").value = seed.dpLine;
  document.getElementById("height").value = seed.height;
  document.getElementById("tb").value = seed.tb;
  document.getElementById("residuals").value = seed.residuals;
  document.getElementById("allowable").value = seed.allowable;
  document.getElementById("rho-mat").value = seed.rhoMat;
  document.getElementById("shape").value = seed.shape;
  document.getElementById("radius").value = seed.radius;
  ["ox", "fuel"].forEach(function (name) {
    var input = seed[name];
    Object.keys(input).forEach(function (key) {
      var field = document.querySelector('fieldset[data-branch="' + name + '"] [data-key="' + key + '"]');
      if (field) field.value = input[key];
    });
  });
  Lab.applyMode(seed);
};

Lab.applyMode = function (seed) {
  document.body.classList.toggle("mode-pressure", seed.architecture === "pressure");
  document.body.classList.toggle("mode-electric", seed.architecture === "electric");
  document.body.classList.toggle("flow-ratio", seed.flowMode === "ratio");
  document.body.classList.toggle("flow-branches", seed.flowMode === "branches");
  document.body.classList.toggle("shape-sphere", seed.shape === "sphere");
  document.body.classList.toggle("shape-cylinder", seed.shape === "cylinder");
};

Lab.line = function (label, value, unit) {
  return label + ": " + Lab.trim(value) + (unit ? " " + unit : "");
};

Lab.branchText = function (title, row, architecture, shape) {
  var lines = [
    Lab.line("p_supply", row.supply, "Pa"),
    Lab.line("orifice area", row.area, "m²"),
    Lab.line("orifice diameter", row.diameter, "m"),
    Lab.line("shell mass", row.mass, "kg"),
    Lab.line("design pressure", row.pDesign, "Pa"),
    Lab.line("radius", row.radius, "m"),
    Lab.line("thickness", row.thickness, "m"),
    Lab.line("membrane stress", row.sigma, "Pa"),
    Lab.line("margin", row.margin, "")
  ];
  if (architecture === "pressure") {
    lines.push(Lab.line("blowdown p2", row.p2, "Pa"));
    lines.push(row.flagged ? "flag: p2 is below p_supply" : "flag: clear");
  } else {
    lines.push(Lab.line("pump rise", row.rise, "Pa"));
    lines.push(Lab.line("drive power", row.drive, "W"));
  }
  if (shape === "cylinder") {
    lines.push(Lab.line("hoop stress", row.sigma, "Pa"));
    lines.push(Lab.line("longitudinal stress", row.sigmaLong, "Pa"));
    lines.push(Lab.line("flat-head thickness", row.tHead, "m"));
  }
  return "<h3>" + title + "</h3><p>" + lines.join("</p><p>") + "</p>";
};

Lab.renderReadout = function (seed, point) {
  var box = document.getElementById("readout");
  var status = document.getElementById("status");
  if (!point.ok) {
    status.textContent = point.error;
    box.innerHTML = "";
    return;
  }
  var arch = seed.architecture === "pressure" ? "Pressure-fed" : "Electric pump";
  var flow = seed.flowMode === "ratio" ? "total flow and mixture ratio" : "separate branch flows";
  var stress = seed.architecture === "pressure"
    ? "Shell thickness and membrane stress use each tank's initial pressure."
    : "Shell thickness and membrane stress use each tank MEOP. An electric pump is not a turbine cycle.";
  var flags = "";
  if (seed.architecture === "pressure") {
    flags = " Oxidizer " + (point.ox.flagged ? "is short at burnout." : "clears its supply pressure.") +
      " Fuel " + (point.fuel.flagged ? "is short at burnout." : "clears its supply pressure.");
  }
  status.textContent = arch + ", " + flow + ". " + stress + flags +
    " Chamber pressure is the injector-end pressure. Allowable stress " + Lab.trim(seed.allowable) +
    " Pa and material density " + Lab.trim(seed.rhoMat) + " kg/m³ are assumptions, not a named alloy.";
  box.innerHTML = Lab.branchText("Oxidizer", point.ox, seed.architecture, seed.shape) +
    Lab.branchText("Fuel", point.fuel, seed.architecture, seed.shape);
};

Lab.lineKV = function (key, value) {
  return key + ": " + (typeof value === "number" ? Lab.trim(value) : value);
};

Lab.parameterText = function (seed, point) {
  if (!point.ok) return point.error;
  var lines = [
    Lab.lineKV("architecture", seed.architecture),
    Lab.lineKV("flow_mode", seed.flowMode)
  ];
  if (seed.flowMode === "ratio") {
    lines.push(Lab.lineKV("mdot_kg_s", seed.mdot));
    lines.push(Lab.lineKV("r", seed.r));
  }
  lines.push(
    Lab.lineKV("pc_Pa", seed.pc),
    Lab.lineKV("dp_line_Pa", seed.dpLine),
    Lab.lineKV("height_m", seed.height),
    Lab.lineKV("tb_s", seed.tb),
    Lab.lineKV("residuals", seed.residuals),
    Lab.lineKV("allowable_Pa", seed.allowable),
    Lab.lineKV("rho_mat_kg_m3", seed.rhoMat),
    Lab.lineKV("shape", seed.shape)
  );
  if (seed.shape === "cylinder") lines.push(Lab.lineKV("radius_m", seed.radius));
  ["ox", "fuel"].forEach(function (name) {
    var input = seed[name];
    lines.push(
      "",
      name,
      Lab.lineKV("rho_kg_m3", input.rho),
      Lab.lineKV("dp_injector_Pa", input.dpInj),
      Lab.lineKV("Cd", input.cd),
      Lab.lineKV("orifice_count", input.count)
    );
    if (seed.flowMode === "branches") lines.push(Lab.lineKV("mdot_kg_s", input.mdot));
    if (seed.architecture === "pressure") {
      lines.push(
        Lab.lineKV("p0_Pa", input.p0),
        Lab.lineKV("V0_m3", input.v0),
        Lab.lineKV("n", input.n)
      );
    } else {
      lines.push(
        Lab.lineKV("p_inlet_Pa", input.pin),
        Lab.lineKV("eta_pump", input.eta),
        Lab.lineKV("eta_motor", input.etaDrive),
        Lab.lineKV("tank_meop_Pa", input.meop)
      );
    }
  });
  return lines.join("\n");
};

Lab.fit = function (canvas) {
  var rect = canvas.getBoundingClientRect();
  var width = Math.max(320, Math.floor(rect.width) || 320);
  var height = Math.max(1, Math.floor(rect.height) || 1);
  var scale = window.devicePixelRatio || 1;
  canvas.width = Math.floor(width * scale);
  canvas.height = Math.floor(height * scale);
  var ctx = canvas.getContext("2d");
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  return { ctx: ctx, width: width, height: height };
};

Lab.drawPid = function (seed, point) {
  var canvas = document.getElementById("pid");
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
  var columns = [
    { title: "oxidizer", color: "#1a5276", row: point.ox, x: view.width * 0.28 },
    { title: "fuel", color: "#9a7d0a", row: point.fuel, x: view.width * 0.72 }
  ];
  ctx.font = "12px Segoe UI, sans-serif";
  var labelWidth = 0;
  columns.forEach(function (column) {
    labelWidth = Math.max(labelWidth, Lab.tankLabelWidth(ctx, column.row));
  });
  var tankRadius = Math.max(84, Math.sqrt(Math.pow(labelWidth / 2 + 18, 2) + 26 * 26));
  var chamberY = view.height - 54;
  ctx.strokeStyle = "#1b2631";
  ctx.lineWidth = 2;
  ctx.strokeRect(view.width * 0.18, chamberY, view.width * 0.64, 36);
  ctx.fillStyle = "#1b2631";
  ctx.font = "13px Segoe UI, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("chamber  " + Lab.trim(seed.pc / 1e6) + " MPa", view.width * 0.5, chamberY + 23);
  columns.forEach(function (column) {
    Lab.drawColumn(ctx, seed, column, chamberY, tankRadius);
  });
};

Lab.tankLabelWidth = function (ctx, row) {
  var thickness = ctx.measureText("t " + Lab.trim(row.thickness * 1000) + " mm").width;
  var stress = ctx.measureText(Lab.trim(row.sigma / 1e6) + " MPa").width;
  return Math.max(thickness, stress);
};

Lab.roundRect = function (ctx, x, y, w, h) {
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.stroke();
};

Lab.drawColumn = function (ctx, seed, column, chamberY, tankRadius) {
  var x = column.x;
  var row = column.row;
  ctx.strokeStyle = column.color;
  ctx.fillStyle = column.color;
  ctx.lineWidth = 2;
  ctx.textAlign = "center";
  ctx.font = "12px Segoe UI, sans-serif";
  ctx.fillText(column.title, x, 18);
  var tankTop = 28;
  var thicknessLabel = "t " + Lab.trim(row.thickness * 1000) + " mm";
  var stressLabel = Lab.trim(row.sigma / 1e6) + " MPa";
  var lineTop;
  if (seed.shape === "sphere") {
    var centerY = tankTop + tankRadius;
    ctx.beginPath();
    ctx.arc(x, centerY, tankRadius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillText(thicknessLabel, x, centerY - 2);
    ctx.fillText(stressLabel, x, centerY + 16);
    lineTop = tankTop + tankRadius * 2;
  } else {
    var tankWidth = tankRadius * 2;
    var tankHeight = Math.max(120, tankRadius * 1.7);
    Lab.roundRect(ctx, x - tankWidth / 2, tankTop, tankWidth, tankHeight);
    var mid = tankTop + tankHeight / 2;
    ctx.fillText(thicknessLabel, x, mid - 2);
    ctx.fillText(stressLabel, x, mid + 16);
    lineTop = tankTop + tankHeight;
  }
  var pumpY = lineTop + 28;
  if (seed.architecture === "electric") {
    ctx.beginPath();
    ctx.moveTo(x, pumpY - 12);
    ctx.lineTo(x + 16, pumpY);
    ctx.lineTo(x, pumpY + 12);
    ctx.lineTo(x - 16, pumpY);
    ctx.closePath();
    ctx.stroke();
    ctx.fillText(Lab.trim(row.drive / 1000) + " kW", x + 58, pumpY + 4);
    lineTop = pumpY + 12;
  }
  ctx.beginPath();
  ctx.moveTo(x, lineTop);
  ctx.lineTo(x, chamberY);
  ctx.stroke();
  ctx.textAlign = "left";
  ctx.fillText("supply " + Lab.trim(row.supply / 1e6) + " MPa", x + 10, (lineTop + chamberY) / 2);
  ctx.textAlign = "center";
  if (seed.architecture === "pressure") {
    Lab.drawCurve(ctx, row, x - 70, chamberY - 78, 140, 62);
  }
};

Lab.drawCurve = function (ctx, row, x, y, w, h) {
  ctx.strokeStyle = row.flagged ? "#922b21" : "#1b2631";
  ctx.strokeRect(x, y, w, h);
  var pressures = row.curve.pressures;
  var volumes = row.curve.volumes;
  var pMax = Math.max(pressures[0], row.supply);
  var vMax = Math.max(volumes[volumes.length - 1], 1e-9);
  ctx.beginPath();
  for (var i = 0; i < pressures.length; i += 1) {
    var px = x + (volumes[i] / vMax) * (w - 8) + 4;
    var py = y + h - 4 - (pressures[i] / pMax) * (h - 8);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();
  ctx.setLineDash([3, 3]);
  var floor = y + h - 4 - (row.supply / pMax) * (h - 8);
  ctx.beginPath();
  ctx.moveTo(x + 4, floor);
  ctx.lineTo(x + w - 4, floor);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.font = "11px Segoe UI, sans-serif";
  ctx.fillStyle = row.flagged ? "#922b21" : "#1b2631";
  ctx.textAlign = "center";
  ctx.fillText(row.flagged ? "short" : "clears", x + w / 2, y - 4);
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

Lab.drawHistory = function (seed, point) {
  var canvas = document.getElementById("history");
  if (seed.architecture !== "pressure") return;
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
  var left = 64;
  var right = view.width - 16;
  var top = 48;
  var bottom = view.height - 36;
  var series = [
    { name: "oxidizer", color: "#1a5276", row: point.ox },
    { name: "fuel", color: "#9a7d0a", row: point.fuel }
  ];
  var pMax = 0;
  series.forEach(function (item) {
    pMax = Math.max(pMax, item.row.history.pressures[0], item.row.supply);
  });
  var tMax = seed.tb;
  if (!(pMax > 0) || !(tMax > 0)) return;
  var xOf = function (time) { return left + (time / tMax) * (right - left); };
  var yOf = function (pressure) { return bottom - (pressure / pMax) * (bottom - top); };
  ctx.strokeStyle = "#d5d8dc";
  ctx.lineWidth = 1;
  ctx.font = "11px Segoe UI, sans-serif";
  ctx.fillStyle = "#34495e";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  Lab.niceTicks(0, pMax / 1e6, 5).forEach(function (tick) {
    var y = yOf(tick * 1e6);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
    ctx.stroke();
    ctx.fillText(Lab.trim(tick), left - 8, y);
  });
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  Lab.niceTicks(0, tMax, 5).forEach(function (tick) {
    var x = xOf(tick);
    ctx.fillText(Lab.trim(tick), x, bottom + 6);
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
  ctx.textBaseline = "top";
  ctx.fillText("ullage pressure versus time", (left + right) / 2, 6);
  ctx.font = "12px Segoe UI, sans-serif";
  ctx.fillText("time, s", (left + right) / 2, view.height - 16);
  ctx.save();
  ctx.translate(16, (top + bottom) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("pressure, MPa", 0, 0);
  ctx.restore();
  series.forEach(function (item) {
    var history = item.row.history;
    ctx.strokeStyle = item.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (var i = 0; i < history.times.length; i += 1) {
      var x = xOf(history.times[i]);
      var y = yOf(history.pressures[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(left, yOf(item.row.supply));
    ctx.lineTo(right, yOf(item.row.supply));
    ctx.stroke();
    ctx.setLineDash([]);
  });
  ctx.font = "12px Segoe UI, sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  series.forEach(function (item, index) {
    var x = left + index * 190;
    var y = 28;
    ctx.strokeStyle = item.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + 22, y);
    ctx.stroke();
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(x + 28, y);
    ctx.lineTo(x + 46, y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = item.color;
    ctx.fillText(item.name + "  ·  supply", x + 52, y);
  });
};

Lab.refresh = function () {
  var seed = Lab.readSeed();
  Lab.applyMode(seed);
  var point = Lab.designPoint(seed);
  Lab.renderReadout(seed, point);
  document.getElementById("parameters").value = Lab.parameterText(seed, point);
  Lab.drawPid(seed, point);
  Lab.drawHistory(seed, point);
};

Lab.boot = function (seed) {
  Lab.writeSeed(seed);
  document.getElementById("app").addEventListener("input", Lab.refresh);
  document.getElementById("app").addEventListener("change", Lab.refresh);
  window.addEventListener("resize", Lab.refresh);
  Lab.refresh();
};
