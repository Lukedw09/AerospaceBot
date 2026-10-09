/* Port of ROCKET - KickStageNozzle conical geometry, Mach-from-pressure, and Summerfield separation. */
var Lab = Lab || {};

Lab.machFromPressure = function (pc, pe, gamma) {
  if (!(pe > 0) || !(pc > 0)) throw new Error("pressures must be positive");
  if (pe >= pc) throw new Error("exit pressure must be below chamber pressure");
  var exponent = (gamma - 1) / gamma;
  var meSq = (2 / (gamma - 1)) * (Math.pow(pc / pe, exponent) - 1);
  if (!(meSq > 0) || !isFinite(meSq)) throw new Error("pressure ratio does not give a real Mach number");
  return Math.sqrt(meSq);
};

Lab.conicalGeometry = function (rt, epsilon, halfAngle, lengthFraction) {
  if (!(halfAngle > 0) || halfAngle >= Math.PI / 2) {
    throw new Error("half-angle must be in (0, pi/2) rad");
  }
  if (!isFinite(lengthFraction) || !(lengthFraction > 0)) {
    throw new Error("length fraction must be > 0");
  }
  var re = rt * Math.sqrt(epsilon);
  var lCone = (re - rt) / Math.tan(halfAngle);
  var axial = lengthFraction * lCone;
  var slant = Math.hypot(axial, re - rt);
  return { Rt: rt, Re: re, Lcone: lCone, Ldiv: axial, Lslant: slant };
};

Lab.shellMass = function (rt, re, slant, thickness, rhoMat) {
  return Math.PI * (rt + re) * slant * thickness * rhoMat;
};

Lab.separationState = function (pe, pa, kSep) {
  if (!(kSep > 0)) throw new Error("k-sep must be > 0");
  if (!(pa > 0)) {
    return { separation: "not_applicable_vacuum", separationMargin: null, peSep: null };
  }
  var peSep = kSep * pa;
  var margin = pe / peSep - 1;
  var separation = pe >= peSep ? "attached" : "separated_or_at_risk";
  return { separation: separation, separationMargin: margin, peSep: peSep };
};
