/* Single-revolution Lambert. Keep in step with ASTRO - LambertTransfer. */
var Lab = Lab || {};

Lab.LAMBERT_Z_MIN = -40.0;
Lab.LAMBERT_Z_MAX = Math.pow(2.0 * Math.PI, 2) * (1.0 - 1e-8);

Lab.vecNorm = function (a) {
  return Math.hypot(a[0], a[1], a[2]);
};

Lab.vecDot = function (a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
};

Lab.vecCross = function (a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0]
  ];
};

Lab.vecScale = function (a, s) {
  return [a[0] * s, a[1] * s, a[2] * s];
};

Lab.vecAdd = function (a, b) {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
};

Lab.vecSub = function (a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
};

Lab.vecUnit = function (a) {
  var n = Lab.vecNorm(a);
  if (n === 0.0) throw new Error("zero vector");
  return Lab.vecScale(a, 1.0 / n);
};

Lab.stumpff = function (z) {
  if (Math.abs(z) < 1.0e-4) {
    return [0.5 - z / 24.0 + z * z / 720.0, 1.0 / 6.0 - z / 120.0 + z * z / 5040.0];
  }
  if (z > 0.0) {
    var root = Math.sqrt(z);
    return [(1.0 - Math.cos(root)) / z, (root - Math.sin(root)) / Math.pow(root, 3)];
  }
  var hyp = Math.sqrt(-z);
  return [(Math.cosh(hyp) - 1.0) / (-z), (Math.sinh(hyp) - hyp) / Math.pow(hyp, 3)];
};

Lab.yParameter = function (z, r1, r2, geometric) {
  var cs = Lab.stumpff(z);
  if (cs[0] <= 0.0) return null;
  var y = r1 + r2 + geometric * (z * cs[1] - 1.0) / Math.sqrt(cs[0]);
  if (y <= 0.0) return null;
  return [y, cs[0], cs[1]];
};

Lab.lambertTof = function (z, r1, r2, geometric, mu) {
  var packed = Lab.yParameter(z, r1, r2, geometric);
  if (!packed) return null;
  return (Math.pow(packed[0] / packed[1], 1.5) * packed[2] + geometric * Math.sqrt(packed[0])) / Math.sqrt(mu);
};

Lab.lambertBisect = function (func, lo, hi, yLo) {
  var i;
  for (i = 0; i < 80; i += 1) {
    var mid = 0.5 * (lo + hi);
    var value = func(mid);
    if (value === null) {
      hi = mid;
      continue;
    }
    if (yLo * value <= 0.0) hi = mid;
    else {
      lo = mid;
      yLo = value;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.findUniversalZ = function (r1, r2, geometric, mu, tof) {
  var samples = [];
  var index;
  for (index = 0; index < 160; index += 1) {
    var z = Lab.LAMBERT_Z_MIN + (Lab.LAMBERT_Z_MAX - Lab.LAMBERT_Z_MIN) * index / 159.0;
    var flight = Lab.lambertTof(z, r1, r2, geometric, mu);
    if (flight !== null && isFinite(flight)) samples.push([z, flight - tof]);
  }
  var k;
  for (k = 0; k < samples.length - 1; k += 1) {
    var z0 = samples[k][0];
    var y0 = samples[k][1];
    var z1 = samples[k + 1][0];
    var y1 = samples[k + 1][1];
    if (y0 === 0.0) return z0;
    if (y0 * y1 < 0.0) {
      return Lab.lambertBisect(function (zVal) {
        var flight = Lab.lambertTof(zVal, r1, r2, geometric, mu);
        return flight === null ? null : flight - tof;
      }, z0, z1, y0);
    }
  }
  throw new Error("time of flight is outside the single-revolution range");
};

Lab.transferAngle = function (r1, r2, way) {
  var cosine = Lab.vecDot(r1, r2) / (Lab.vecNorm(r1) * Lab.vecNorm(r2));
  cosine = Math.max(-1.0, Math.min(1.0, cosine));
  var short = Math.acos(cosine);
  return way === "short" ? short : 2.0 * Math.PI - short;
};

Lab.collinearNormal = function (r1, way) {
  var normal = Lab.vecCross(r1, [0.0, 0.0, 1.0]);
  if (Lab.vecNorm(normal) < 1.0e-8 * Lab.vecNorm(r1)) normal = Lab.vecCross(r1, [0.0, 1.0, 0.0]);
  if (way === "long") normal = Lab.vecScale(normal, -1.0);
  return Lab.vecUnit(normal);
};

Lab.ellipticHalfTof = function (eccentricity, r1, r2, mu) {
  var parameter = 2.0 * r1 * r2 / (r1 + r2);
  var kappa = (parameter / 2.0) * (1.0 / r1 - 1.0 / r2);
  var semimajor = parameter / (1.0 - eccentricity * eccentricity);
  var cos1 = Math.max(-1.0, Math.min(1.0, kappa / eccentricity));
  var sin1 = Math.sqrt(Math.max(0.0, 1.0 - cos1 * cos1));
  function anomaly(cosNu, sinNu) {
    var denom = 1.0 + eccentricity * cosNu;
    var sinE = sinNu * Math.sqrt(1.0 - eccentricity * eccentricity) / denom;
    var cosE = (eccentricity + cosNu) / denom;
    return Math.atan2(sinE, cosE);
  }
  var first = anomaly(cos1, sin1);
  var second = anomaly(-cos1, -sin1);
  if (second <= first) second += 2.0 * Math.PI;
  var mean = (second - eccentricity * Math.sin(second)) - (first - eccentricity * Math.sin(first));
  return Math.sqrt(Math.pow(semimajor, 3) / mu) * mean;
};

Lab.solveCollinear = function (r1, r2, tof, mu, way) {
  var r1n = Lab.vecNorm(r1);
  var r2n = Lab.vecNorm(r2);
  if (Math.abs(r1n - r2n) <= 1.0e-9 * Math.max(r1n, r2n)) {
    var half = Math.PI * Math.sqrt(Math.pow(r1n, 3) / mu);
    if (Math.abs(tof - half) <= 1.0e-6 * half) {
      var hCirc = Math.sqrt(mu * r1n);
      var normalCirc = Lab.collinearNormal(r1, way);
      var v1c = Lab.vecScale(Lab.vecCross(normalCirc, Lab.vecUnit(r1)), hCirc / r1n);
      var v2c = Lab.vecScale(Lab.vecCross(normalCirc, Lab.vecUnit(r2)), hCirc / r2n);
      return { v1: v1c, v2: v2c, eccentricity: 0.0 };
    }
  }
  var parameter = 2.0 * r1n * r2n / (r1n + r2n);
  var kappa = (parameter / 2.0) * (1.0 / r1n - 1.0 / r2n);
  var eMin = Math.max(Math.abs(kappa), 1.0e-8);
  if (eMin >= 1.0) throw new Error("the 180 degree chord has no elliptic solution");
  var targetMin = Lab.ellipticHalfTof(eMin, r1n, r2n, mu);
  var eccentricity = null;
  if (Math.abs(targetMin - tof) <= 1.0e-8 * Math.max(1.0, Math.abs(tof))) eccentricity = eMin;
  else {
    var samples = [];
    var index;
    for (index = 1; index < 80; index += 1) {
      var trial = eMin + (0.999 - eMin) * index / 79.0;
      samples.push([trial, Lab.ellipticHalfTof(trial, r1n, r2n, mu) - tof]);
    }
    var chain = [[eMin, targetMin - tof]].concat(samples);
    var k;
    for (k = 0; k < chain.length - 1; k += 1) {
      var e0 = chain[k][0];
      var y0 = chain[k][1];
      var e1 = chain[k + 1][0];
      var y1 = chain[k + 1][1];
      if (y0 === 0.0) {
        eccentricity = e0;
        break;
      }
      if (y0 * y1 < 0.0) {
        eccentricity = Lab.lambertBisect(function (ecc) {
          return Lab.ellipticHalfTof(ecc, r1n, r2n, mu) - tof;
        }, e0, e1, y0);
        break;
      }
    }
  }
  if (eccentricity === null) {
    throw new Error("time of flight is outside the single-revolution elliptic range for a 180 degree chord");
  }
  var specificH = Math.sqrt(mu * parameter);
  var cos1 = Math.max(-1.0, Math.min(1.0, kappa / eccentricity));
  var sin1 = Math.sqrt(Math.max(0.0, 1.0 - cos1 * cos1));
  var normal = Lab.collinearNormal(r1, way);
  var r1Hat = Lab.vecUnit(r1);
  var r2Hat = Lab.vecUnit(r2);
  var v1 = Lab.vecAdd(
    Lab.vecScale(r1Hat, mu / specificH * eccentricity * sin1),
    Lab.vecScale(Lab.vecCross(normal, r1Hat), specificH / r1n)
  );
  var v2 = Lab.vecAdd(
    Lab.vecScale(r2Hat, mu / specificH * eccentricity * (-sin1)),
    Lab.vecScale(Lab.vecCross(normal, r2Hat), specificH / r2n)
  );
  return { v1: v1, v2: v2, eccentricity: eccentricity };
};

Lab.lambertVelocities = function (r1, r2, tof, mu, way) {
  var r1n = Lab.vecNorm(r1);
  var r2n = Lab.vecNorm(r2);
  var angle = Lab.transferAngle(r1, r2, way);
  if (Math.abs(Math.sin(angle)) < 1.0e-8) {
    var collinear = Lab.solveCollinear(r1, r2, tof, mu, way);
    return { v1: collinear.v1, v2: collinear.v2, angle: angle };
  }
  var geometric = Math.sin(angle) * Math.sqrt(r1n * r2n / (1.0 - Math.cos(angle)));
  var zRoot = Lab.findUniversalZ(r1n, r2n, geometric, mu, tof);
  var packed = Lab.yParameter(zRoot, r1n, r2n, geometric);
  if (!packed) throw new Error("the universal-variable root has no positive y");
  var y = packed[0];
  var f = 1.0 - y / r1n;
  var g = geometric * Math.sqrt(y / mu);
  var gdot = 1.0 - y / r2n;
  var v1 = Lab.vecScale(Lab.vecSub(r2, Lab.vecScale(r1, f)), 1.0 / g);
  var v2 = Lab.vecScale(Lab.vecSub(Lab.vecScale(r2, gdot), r1), 1.0 / g);
  return { v1: v1, v2: v2, angle: angle };
};

Lab.parkingDeltaMag = function (vVec, rVec, speed) {
  var normal = Lab.vecUnit(Lab.vecCross(rVec, vVec));
  var tangential = Lab.vecCross(normal, Lab.vecUnit(rVec));
  var dv = Lab.vecSub(vVec, Lab.vecScale(tangential, speed));
  return Lab.vecNorm(dv);
};

Lab.lambert = function (r1, r2, tof, mu, way) {
  var vel = Lab.lambertVelocities(r1, r2, tof, mu, way || "short");
  var dv1 = Lab.parkingDeltaMag(vel.v1, r1, Lab.circularSpeed(mu, Lab.vecNorm(r1)));
  var dv2 = Lab.parkingDeltaMag(vel.v2, r2, Lab.circularSpeed(mu, Lab.vecNorm(r2)));
  return {
    v1: vel.v1,
    v2: vel.v2,
    angle: vel.angle,
    dv1: dv1,
    dv2: dv2,
    dv: dv1 + dv2
  };
};
