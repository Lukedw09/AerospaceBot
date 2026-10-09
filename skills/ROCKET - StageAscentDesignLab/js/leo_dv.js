var Lab = Lab || {};

Lab.G0 = 9.80665;
Lab.R0 = 6.3742e6;

Lab.designDeltaV = function (alt, vRot, gravity, drag, steering, circ, margin, marginFraction) {
  if (!(alt >= 0)) throw new Error("altitude must be >= 0");
  if (vRot < 0 || gravity < 0 || drag < 0 || steering < 0 || circ < 0) {
    throw new Error("rotation assist, losses, and circularization must be >= 0");
  }
  var radius = Lab.R0 + alt;
  var mu = Lab.G0 * Lab.R0 * Lab.R0;
  var vCirc = Math.sqrt(mu / radius);
  var base = vCirc - vRot + gravity + drag + steering + circ;
  var applied = 0;
  var source = "omitted";
  if (margin !== null && margin !== undefined && marginFraction !== null && marginFraction !== undefined) {
    throw new Error("pass a margin or a margin fraction");
  }
  if (marginFraction !== null && marginFraction !== undefined) {
    if (marginFraction < 0) throw new Error("margin fraction must be >= 0");
    applied = marginFraction * base;
    source = "fraction";
  } else if (margin !== null && margin !== undefined) {
    if (margin < 0) throw new Error("margin must be >= 0");
    applied = margin;
    source = "absolute";
  }
  return { vCirc: vCirc, margin: applied, marginSource: source, dv: base + applied };
};
