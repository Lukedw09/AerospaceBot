/* Oblique shock and Prandtl-Meyer wedge. Mirrors AERO - PrandtlMeyerAndShocks. */
var Lab = Lab || {};

Lab.WEDGE_DETACH = 1e-10;
Lab.ROOT_SPLIT = 1e-8;

Lab.machAngle = function (mach) {
  return Math.asin(1 / mach);
};

Lab.prandtlMeyer = function (mach, gamma) {
  if (mach < 1) {
    throw new Error("Prandtl-Meyer Mach must be at least 1");
  }
  if (mach <= 1 + 1e-15) {
    return 0;
  }
  var gp = gamma + 1;
  var gm = gamma - 1;
  return (
    Math.sqrt(gp / gm) * Math.atan(Math.sqrt((gm / gp) * (mach * mach - 1))) -
    Math.atan(Math.sqrt(mach * mach - 1))
  );
};

Lab.nuMax = function (gamma) {
  return (Math.sqrt((gamma + 1) / (gamma - 1)) - 1) * Math.PI / 2;
};

Lab.invertPrandtlMeyer = function (nu, gamma) {
  if (nu <= 0) {
    return 1;
  }
  var limit = Lab.nuMax(gamma);
  if (nu >= limit - 1e-14) {
    throw new Error("turn exceeds the maximum Prandtl-Meyer angle");
  }
  var lo = 1;
  var hi = 2;
  while (Lab.prandtlMeyer(hi, gamma) < nu) {
    hi *= 2;
    if (hi > 1e6) {
      throw new Error("downstream Mach is unbounded");
    }
  }
  for (var i = 0; i < 80; i++) {
    var mid = 0.5 * (lo + hi);
    if (Lab.prandtlMeyer(mid, gamma) < nu) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.deflectionAngle = function (theta, mach, gamma) {
  if (theta <= 0 || theta >= Math.PI / 2) {
    return 0;
  }
  var mn2 = Math.pow(mach * Math.sin(theta), 2);
  if (mn2 <= 1) {
    return 0;
  }
  var cot = Math.cos(theta) / Math.sin(theta);
  var numer = 2 * cot * (mn2 - 1);
  var denom = 2 + mach * mach * (gamma + Math.cos(2 * theta));
  return Math.atan(numer / denom);
};

Lab.maximumDeflection = function (mach, gamma) {
  var mu = Lab.machAngle(mach);
  var lo = mu + 1e-14;
  var hi = Math.PI / 2 - 1e-14;
  var invphi = (Math.sqrt(5) - 1) / 2;
  var left = hi - invphi * (hi - lo);
  var right = lo + invphi * (hi - lo);
  var leftValue = Lab.deflectionAngle(left, mach, gamma);
  var rightValue = Lab.deflectionAngle(right, mach, gamma);
  for (var i = 0; i < 80; i++) {
    if (leftValue < rightValue) {
      lo = left;
      left = right;
      leftValue = rightValue;
      right = lo + invphi * (hi - lo);
      rightValue = Lab.deflectionAngle(right, mach, gamma);
    } else {
      hi = right;
      right = left;
      rightValue = leftValue;
      left = hi - invphi * (hi - lo);
      leftValue = Lab.deflectionAngle(left, mach, gamma);
    }
  }
  var theta = 0.5 * (lo + hi);
  return { theta: theta, delta: Lab.deflectionAngle(theta, mach, gamma) };
};

Lab.shockDownstream = function (mach, gamma, theta, delta) {
  var mn2 = Math.pow(mach * Math.sin(theta), 2);
  if (mn2 < 1 - 1e-12) {
    throw new Error("normal Mach ahead of the shock is below 1");
  }
  var pressure = (2 * gamma * mn2 - (gamma - 1)) / (gamma + 1);
  var mn2Down = ((gamma - 1) * mn2 + 2) / (2 * gamma * mn2 - (gamma - 1));
  var sine = Math.sin(theta - delta);
  if (sine <= 0 || mn2Down <= 0) {
    throw new Error("downstream Mach is not defined for this wave");
  }
  var m2 = Math.sqrt(mn2Down) / sine;
  if (!isFinite(pressure) || !isFinite(m2) || pressure <= 0 || m2 <= 0) {
    throw new Error("downstream shock state is not finite");
  }
  return { Mn1: Math.sqrt(mn2), Mn2_sq: mn2Down, M2: m2, p_ratio: pressure };
};

Lab.isentropicPressureRatio = function (mach1, mach2, gamma) {
  function totalOverStatic(mach) {
    return Math.pow(1 + 0.5 * (gamma - 1) * mach * mach, gamma / (gamma - 1));
  }
  return totalOverStatic(mach1) / totalOverStatic(mach2);
};

Lab.machRegime = function (mach) {
  if (mach > 1 + 1e-8) {
    return "supersonic";
  }
  if (mach < 1 - 1e-8) {
    return "subsonic";
  }
  return "sonic";
};

Lab.bisectDeflection = function (lo, hi, target, mach, gamma, decreasing) {
  for (var i = 0; i < 80; i++) {
    var mid = 0.5 * (lo + hi);
    var value = Lab.deflectionAngle(mid, mach, gamma);
    if (decreasing) {
      if (value > target) {
        lo = mid;
      } else {
        hi = mid;
      }
    } else if (value < target) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.freestreamExpansion = function (mach, gamma, delta) {
  var nu1 = Lab.prandtlMeyer(mach, gamma);
  var limit = Lab.nuMax(gamma);
  var result = { nu1: nu1, nu_max: limit, expansion: null, pm_M: null, pm_p_ratio: null };
  if (delta > limit - nu1 - 1e-12) {
    result.expansion = "exceeds-maximum-turn";
    return result;
  }
  var pmM = Lab.invertPrandtlMeyer(nu1 + delta, gamma);
  result.expansion = "prandtl-meyer";
  result.pm_M = pmM;
  result.pm_p_ratio = Lab.isentropicPressureRatio(mach, pmM, gamma);
  return result;
};

Lab.shoulderFan = function (mach2, gamma, delta, shockPressure) {
  if (mach2 <= 1) {
    return { fan: "subsonic", fan_M: null, fan_p_ratio: null, fan_p_over_p1: null };
  }
  var nuPost = Lab.prandtlMeyer(mach2, gamma);
  if (delta > Lab.nuMax(gamma) - nuPost - 1e-12) {
    return { fan: "exceeds-maximum-turn", fan_M: null, fan_p_ratio: null, fan_p_over_p1: null };
  }
  var fanM = Lab.invertPrandtlMeyer(nuPost + delta, gamma);
  var fanRatio = Lab.isentropicPressureRatio(mach2, fanM, gamma);
  return {
    fan: "yes",
    fan_M: fanM,
    fan_p_ratio: fanRatio,
    fan_p_over_p1: fanRatio * shockPressure
  };
};

Lab.evaluateWedge = function (mach, gamma, delta) {
  if (!isFinite(mach) || mach <= 1 || mach > 1e6) {
    throw new Error("Mach must be greater than 1 and at most 1e6");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be greater than 1");
  }
  if (!isFinite(delta) || delta < 0 || delta >= Math.PI / 2) {
    throw new Error("deflection must be from 0 up to pi/2");
  }
  var mu = Lab.machAngle(mach);
  var peak = Lab.maximumDeflection(mach, gamma);
  var expansion = Lab.freestreamExpansion(mach, gamma, delta);
  var state = {
    mach: mach,
    gamma: gamma,
    delta: delta,
    mu: mu,
    delta_max: peak.delta,
    theta_at_max: peak.theta,
    nu1: expansion.nu1,
    nu_max: expansion.nu_max,
    expansion: expansion.expansion,
    pm_M: expansion.pm_M,
    pm_p_ratio: expansion.pm_p_ratio,
    attached: false,
    shock: "detached",
    theta: null,
    Mn1: null,
    M2: null,
    p2_over_p1: null,
    M2_regime: null,
    theta_strong: null,
    M2_strong: null,
    p2_over_p1_strong: null,
    fan: null,
    fan_M: null,
    fan_p_ratio: null,
    fan_p_over_p1: null
  };
  if (delta <= 1e-15) {
    var wave = Lab.shockDownstream(mach, gamma, mu, 0);
    state.attached = true;
    state.shock = "mach-wave";
    state.theta = mu;
    state.Mn1 = wave.Mn1;
    state.M2 = wave.M2;
    state.p2_over_p1 = wave.p_ratio;
    state.M2_regime = Lab.machRegime(wave.M2);
    return state;
  }
  if (delta > peak.delta + Lab.WEDGE_DETACH) {
    return state;
  }
  var theta;
  var thetaStrong = null;
  if (delta >= peak.delta - Lab.WEDGE_DETACH) {
    theta = peak.theta;
    state.shock = "maximum-deflection";
  } else {
    theta = Lab.bisectDeflection(mu, peak.theta, delta, mach, gamma, false);
    thetaStrong = Lab.bisectDeflection(peak.theta, Math.PI / 2 - 1e-14, delta, mach, gamma, true);
    if (thetaStrong - theta < Lab.ROOT_SPLIT) {
      state.shock = "maximum-deflection";
      thetaStrong = null;
    } else {
      state.shock = "weak";
    }
  }
  var solved = Lab.deflectionAngle(theta, mach, gamma);
  var down = Lab.shockDownstream(mach, gamma, theta, solved);
  state.attached = true;
  state.theta = theta;
  state.Mn1 = down.Mn1;
  state.M2 = down.M2;
  state.p2_over_p1 = down.p_ratio;
  state.M2_regime = Lab.machRegime(down.M2);
  if (thetaStrong != null) {
    var strongDelta = Lab.deflectionAngle(thetaStrong, mach, gamma);
    try {
      var strong = Lab.shockDownstream(mach, gamma, thetaStrong, strongDelta);
      state.theta_strong = thetaStrong;
      state.M2_strong = strong.M2;
      state.p2_over_p1_strong = strong.p_ratio;
    } catch (err) {
      state.theta_strong = null;
    }
  }
  var fan = Lab.shoulderFan(down.M2, gamma, delta, down.p_ratio);
  state.fan = fan.fan;
  state.fan_M = fan.fan_M;
  state.fan_p_ratio = fan.fan_p_ratio;
  state.fan_p_over_p1 = fan.fan_p_over_p1;
  return state;
};
