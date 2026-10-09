/* Thin-wall tank shell and membrane stress. Ports tank_structure_mass.py. */
var Lab = Lab || {};

Lab.THIN_WALL_LIMIT = 0.1;

Lab.tankShell = function (volume, tankPressure, allowable, rhoMat, eta, designFactor, shape, radius) {
  if (!(volume > 0)) throw new Error("propellant volume must be > 0");
  if (!(tankPressure > 0)) throw new Error("tank pressure must be > 0");
  if (!(allowable > 0)) throw new Error("allowable stress must be > 0");
  if (!(rhoMat > 0)) throw new Error("material density must be > 0");
  if (!(eta > 0) || eta > 1) throw new Error("weld efficiency must satisfy 0 < eta <= 1");
  if (!(designFactor > 0)) throw new Error("design factor must be > 0");
  var pressure = designFactor * tankPressure;
  var geomRadius;
  var thickness;
  var tHead = null;
  var length = null;
  var sigma;
  var sigmaLong = null;
  var mass;
  if (shape === "sphere") {
    geomRadius = Math.pow(3 * volume / (4 * Math.PI), 1 / 3);
    thickness = pressure * geomRadius / (2 * allowable * eta);
    sigma = pressure * geomRadius / (2 * thickness);
    mass = 4 * Math.PI * geomRadius * geomRadius * thickness * rhoMat;
  } else if (shape === "cylinder") {
    if (!(radius > 0)) throw new Error("cylinder radius must be > 0");
    geomRadius = radius;
    length = volume / (Math.PI * radius * radius);
    if (!(length > 0)) throw new Error("cylinder barrel length must be > 0");
    thickness = pressure * radius / (allowable * eta);
    tHead = radius * Math.sqrt(pressure / (allowable * eta));
    sigma = pressure * radius / thickness;
    sigmaLong = pressure * radius / (2 * thickness);
    var lateral = 2 * Math.PI * radius * length;
    var heads = 2 * Math.PI * radius * radius;
    mass = (lateral * thickness + heads * tHead) * rhoMat;
  } else {
    throw new Error("shape must be sphere or cylinder");
  }
  var governing = tHead == null ? thickness : Math.max(thickness, tHead);
  var tOverR = governing / geomRadius;
  if (tOverR >= Lab.THIN_WALL_LIMIT) {
    throw new Error(
      "governing t/R = " + tOverR + " >= 0.1; thin-wall tank model is not valid"
    );
  }
  return {
    shape: shape,
    pressure: pressure,
    radius: geomRadius,
    thickness: thickness,
    tHead: tHead,
    length: length,
    tGoverning: governing,
    tOverR: tOverR,
    sigma: sigma,
    sigmaLong: sigmaLong,
    margin: allowable / sigma - 1,
    mass: mass
  };
};
