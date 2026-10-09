/* Two-dimensional Prandtl-Glauert correction. User coefficients only. */
var Lab = Lab || {};

Lab.PG_LO = 1e-8;
Lab.PG_HI = 1 - 1e-10;

Lab.prandtlGlauertFactor = function (mach) {
  if (mach < 0 || mach >= 1) {
    throw new Error("freestream Mach must satisfy 0 <= M < 1");
  }
  return Math.sqrt(1 - mach * mach);
};

Lab.prandtlGlauertCoefficient = function (incompressible, mach) {
  return incompressible / Lab.prandtlGlauertFactor(mach);
};

Lab.criticalPressureCoefficient = function (gamma, mach) {
  if (mach <= 0) {
    throw new Error("critical pressure coefficient requires M > 0");
  }
  var inner = (2 / (gamma + 1)) * (1 + 0.5 * (gamma - 1) * mach * mach);
  return 2 * (Math.pow(inner, gamma / (gamma - 1)) - 1) / (gamma * mach * mach);
};

Lab.criticalMach = function (cp0Min, gamma) {
  if (cp0Min >= 0) {
    throw new Error("incompressible minimum pressure coefficient must be < 0");
  }
  function residual(mach) {
    return Lab.prandtlGlauertCoefficient(cp0Min, mach) - Lab.criticalPressureCoefficient(gamma, mach);
  }
  var lo = Lab.PG_LO;
  var hi = Lab.PG_HI;
  var fLo = residual(lo);
  var fHi = residual(hi);
  if (fLo === 0) {
    return lo;
  }
  if (fHi === 0) {
    return hi;
  }
  if (fLo * fHi > 0) {
    throw new Error("could not bracket a critical Mach number");
  }
  for (var i = 0; i < 200; i++) {
    var mid = 0.5 * (lo + hi);
    var fMid = residual(mid);
    if (fMid === 0 || Math.abs(hi - lo) <= 1e-14) {
      return mid;
    }
    if (fLo * fMid <= 0) {
      hi = mid;
      fHi = fMid;
    } else {
      lo = mid;
      fLo = fMid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.correctionState = function (mach, gamma, cl0, cp0Min, cm0, cd0) {
  if (!isFinite(mach) || !isFinite(gamma)) {
    throw new Error("Mach and gamma must be finite");
  }
  if (mach < 0 || mach >= 1) {
    throw new Error("freestream Mach must satisfy 0 <= M < 1");
  }
  if (gamma <= 1) {
    throw new Error("gamma must be > 1");
  }
  if (cl0 == null && cp0Min == null && cm0 == null && cd0 == null) {
    throw new Error("requires a coefficient");
  }
  var beta = Lab.prandtlGlauertFactor(mach);
  var cpCrit = mach > 0 ? Lab.criticalPressureCoefficient(gamma, mach) : null;
  var cl = cl0 == null ? null : Lab.prandtlGlauertCoefficient(cl0, mach);
  var cm = cm0 == null ? null : Lab.prandtlGlauertCoefficient(cm0, mach);
  var cpMin = cp0Min == null ? null : Lab.prandtlGlauertCoefficient(cp0Min, mach);
  var mCr = null;
  var supercritical = null;
  if (cp0Min != null && cp0Min < 0) {
    mCr = Lab.criticalMach(cp0Min, gamma);
    if (cpMin != null && cpCrit != null) {
      supercritical = cpMin < cpCrit ? "yes" : "no";
    }
  } else if (cp0Min != null && cp0Min >= 0) {
    supercritical = "n/a";
  }
  return {
    M: mach,
    gamma: gamma,
    beta: beta,
    CL0: cl0,
    CL: cl,
    Cm0: cm0,
    Cm: cm,
    Cd0: cd0,
    Cd: cd0,
    Cp0_min: cp0Min,
    Cp_min: cpMin,
    Cp_crit: cpCrit,
    M_cr: mCr,
    supercritical: supercritical
  };
};
