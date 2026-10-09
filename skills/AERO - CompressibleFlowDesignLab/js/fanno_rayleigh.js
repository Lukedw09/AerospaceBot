/* Fanno and Rayleigh sonic-reference ratios. Mirrors AERO - FannoAndRayleighFlow. */
var Lab = Lab || {};

Lab.FANNO_MACH_MIN = 1e-3;
Lab.FANNO_MACH_MAX = 50;

Lab.fannoTemperatureRatio = function (mach, gamma) {
  return (gamma + 1) / (2 + (gamma - 1) * mach * mach);
};

Lab.fannoPressureRatio = function (mach, gamma) {
  return (1 / mach) * Math.sqrt(Lab.fannoTemperatureRatio(mach, gamma));
};

Lab.fannoDensityRatio = function (mach, gamma) {
  return (1 / mach) / Math.sqrt(Lab.fannoTemperatureRatio(mach, gamma));
};

Lab.fannoVelocityRatio = function (mach, gamma) {
  return mach * Math.sqrt(Lab.fannoTemperatureRatio(mach, gamma));
};

Lab.fannoStagnationPressureRatio = function (mach, gamma) {
  var base = (2 + (gamma - 1) * mach * mach) / (gamma + 1);
  return (1 / mach) * Math.pow(base, (gamma + 1) / (2 * (gamma - 1)));
};

Lab.fannoFrictionParameter = function (mach, gamma) {
  var argument = ((gamma + 1) * mach * mach) / (2 + (gamma - 1) * mach * mach);
  return (1 - mach * mach) / (gamma * mach * mach) + ((gamma + 1) / (2 * gamma)) * Math.log(argument);
};

Lab.rayleighStagnationTemperatureRatio = function (mach, gamma) {
  return (
    2 * (gamma + 1) * mach * mach * (1 + 0.5 * (gamma - 1) * mach * mach) /
    Math.pow(1 + gamma * mach * mach, 2)
  );
};

Lab.rayleighTemperatureRatio = function (mach, gamma) {
  return Math.pow(gamma + 1, 2) * mach * mach / Math.pow(1 + gamma * mach * mach, 2);
};

Lab.rayleighPressureRatio = function (mach, gamma) {
  return (gamma + 1) / (1 + gamma * mach * mach);
};

Lab.rayleighDensityRatio = function (mach, gamma) {
  return (1 + gamma * mach * mach) / ((gamma + 1) * mach * mach);
};

Lab.rayleighStagnationPressureRatio = function (mach, gamma) {
  return Lab.rayleighPressureRatio(mach, gamma) * Math.pow(
    (2 + (gamma - 1) * mach * mach) / (gamma + 1),
    gamma / (gamma - 1)
  );
};

Lab.rayleighVelocityRatio = function (mach, gamma) {
  return (gamma + 1) * mach * mach / (1 + gamma * mach * mach);
};

Lab._bisectScalar = function (func, lo, hi, target) {
  var flo = func(lo) - target;
  var fhi = func(hi) - target;
  if (!isFinite(flo) || !isFinite(fhi) || flo * fhi > 0) {
    throw new Error("exit Mach is not on this branch");
  }
  for (var i = 0; i < 80; i++) {
    var mid = 0.5 * (lo + hi);
    var fmid = func(mid) - target;
    if (Math.abs(fmid) < 1e-12 || Math.abs(hi - lo) < 1e-12 * Math.max(1, Math.abs(mid))) {
      return mid;
    }
    if (flo * fmid <= 0) {
      hi = mid;
      fhi = fmid;
    } else {
      lo = mid;
      flo = fmid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.fannoExitMach = function (mach, gamma, fld) {
  var remain = Lab.fannoFrictionParameter(mach, gamma);
  var band = 1e-6 * Math.max(1, Math.abs(remain));
  if (fld > remain + band) {
    return { exitMach: null, choked: "yes" };
  }
  if (fld < -1e-12) {
    throw new Error("4fL/D must be >= 0");
  }
  var target = remain - fld;
  if (target <= band) {
    return { exitMach: 1, choked: "no" };
  }
  var lo;
  var hi;
  if (mach < 1) {
    lo = Lab.FANNO_MACH_MIN;
    hi = 1 - 1e-9;
  } else {
    lo = 1 + 1e-9;
    hi = Lab.FANNO_MACH_MAX;
  }
  var exitMach = Lab._bisectScalar(function (value) {
    return Lab.fannoFrictionParameter(value, gamma);
  }, lo, hi, target);
  return { exitMach: exitMach, choked: "no" };
};

Lab.rayleighExitMach = function (mach, gamma, ttRatio) {
  if (ttRatio <= 0 || !isFinite(ttRatio)) {
    throw new Error("Tt2/Tt1 must be finite and > 0");
  }
  var inlet = Lab.rayleighStagnationTemperatureRatio(mach, gamma);
  var target = ttRatio * inlet;
  if (target > 1 + 1e-6) {
    return { exitMach: null, choked: "yes" };
  }
  target = Math.min(target, 1);
  var lo;
  var hi;
  if (mach < 1) {
    lo = Lab.FANNO_MACH_MIN;
    hi = 1 - 1e-9;
  } else {
    lo = 1 + 1e-9;
    hi = Lab.FANNO_MACH_MAX;
  }
  var exitMach = Lab._bisectScalar(function (value) {
    return Lab.rayleighStagnationTemperatureRatio(value, gamma);
  }, lo, hi, target);
  return { exitMach: exitMach, choked: "no" };
};

Lab.ductState = function (mode, mach, gamma) {
  if (!isFinite(mach) || mach < Lab.FANNO_MACH_MIN || mach > Lab.FANNO_MACH_MAX) {
    throw new Error("Mach must satisfy 0.001 <= M <= 50");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be finite and > 1");
  }
  var state;
  if (mode === "fanno") {
    state = {
      T_over_Tstar: Lab.fannoTemperatureRatio(mach, gamma),
      p_over_pstar: Lab.fannoPressureRatio(mach, gamma),
      rho_over_rhostar: Lab.fannoDensityRatio(mach, gamma),
      pt_over_ptstar: Lab.fannoStagnationPressureRatio(mach, gamma),
      V_over_Vstar: Lab.fannoVelocityRatio(mach, gamma),
      four_f_Lmax_over_D: Lab.fannoFrictionParameter(mach, gamma),
      Tt_over_Ttstar: null
    };
  } else if (mode === "rayleigh") {
    state = {
      Tt_over_Ttstar: Lab.rayleighStagnationTemperatureRatio(mach, gamma),
      T_over_Tstar: Lab.rayleighTemperatureRatio(mach, gamma),
      p_over_pstar: Lab.rayleighPressureRatio(mach, gamma),
      rho_over_rhostar: Lab.rayleighDensityRatio(mach, gamma),
      pt_over_ptstar: Lab.rayleighStagnationPressureRatio(mach, gamma),
      V_over_Vstar: Lab.rayleighVelocityRatio(mach, gamma),
      four_f_Lmax_over_D: null
    };
  } else {
    throw new Error("mode must be fanno or rayleigh");
  }
  state.M = mach;
  state.gamma = gamma;
  return state;
};

Lab.machFromFannoFriction = function (target, gamma, supersonic) {
  if (target <= 1e-12) {
    return 1;
  }
  var lo = supersonic ? 1 + 1e-9 : Lab.FANNO_MACH_MIN;
  var hi = supersonic ? Lab.FANNO_MACH_MAX : 1 - 1e-9;
  return Lab._bisectScalar(function (value) {
    return Lab.fannoFrictionParameter(value, gamma);
  }, lo, hi, target);
};
