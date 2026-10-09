/* NACA four-digit ordinates. Ports naca4_thickness, camber, and the surface offsets. */
var Lab = Lab || {};

Lab.parseNaca = function (text) {
  var cleaned = String(text || "").trim().replace(/\s+/g, " ");
  var match = /^(?:NACA\s+)?(\d{4})$/i.exec(cleaned);
  if (!match) throw new Error("NACA designation must be four digits, optionally prefixed by NACA");
  var code = match[1];
  var m = Number(code[0]) / 100;
  var p = Number(code[1]) / 10;
  var t = Number(code.slice(2)) / 100;
  if (m > 0 && !(p > 0)) throw new Error("a cambered four-digit section needs a nonzero camber station");
  if (!(t > 0)) throw new Error("thickness digits must be greater than 00");
  return { designation: code, m: m, p: p, t: t };
};

Lab.thicknessRatio = function (t, xi) {
  if (xi <= 0) return 0;
  return (t / 0.2) * (
    0.2969 * Math.sqrt(xi)
    - 0.1260 * xi
    - 0.3516 * xi * xi
    + 0.2843 * xi * xi * xi
    - 0.1015 * xi * xi * xi * xi
  );
};

Lab.camberRatio = function (m, p, xi) {
  if (m === 0) return 0;
  if (xi <= p) return (m / (p * p)) * (2 * p * xi - xi * xi);
  var d = 1 - p;
  return (m / (d * d)) * ((1 - 2 * p) + 2 * p * xi - xi * xi);
};

Lab.camberSlope = function (m, p, xi) {
  if (m === 0) return 0;
  if (xi <= p) return (2 * m / (p * p)) * (p - xi);
  var d = 1 - p;
  return (2 * m / (d * d)) * (p - xi);
};

Lab.sectionStations = function (digits, count) {
  var n = count - 1;
  var rows = [];
  for (var i = 0; i < count; i += 1) {
    var xi = 0.5 * (1 - Math.cos(Math.PI * i / n));
    var yt = Lab.thicknessRatio(digits.t, xi);
    var yc = Lab.camberRatio(digits.m, digits.p, xi);
    var theta = Math.atan(Lab.camberSlope(digits.m, digits.p, xi));
    rows.push({
      x: xi,
      yu: yc + yt * Math.cos(theta),
      yl: yc - yt * Math.cos(theta),
      xu: xi - yt * Math.sin(theta),
      xl: xi + yt * Math.sin(theta)
    });
  }
  return rows;
};

Lab.zeroLiftThin = function (m, p) {
  if (m === 0) return 0;
  if (!(p > 0) || p >= 1) throw new Error("camber station must lie strictly between 0 and 1");
  var theta = 2 * Math.atan(Math.sqrt(p / (1 - p)));
  var s = Math.sqrt(p * (1 - p));
  var B = 2 * p - 1;
  var inner = (B - 0.5) * theta + 2 * s * (1 - B) + B * s;
  var ff = m / (p * p);
  var fa = m / ((1 - p) * (1 - p));
  return (1 / Math.PI) * (ff * inner + fa * ((B - 0.5) * Math.PI - inner));
};
