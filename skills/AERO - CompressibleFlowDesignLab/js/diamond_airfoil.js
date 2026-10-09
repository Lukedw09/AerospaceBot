/* Symmetric diamond shock-expansion. Uses the wedge helpers. */
var Lab = Lab || {};

Lab.TURN_TOL = 1e-15;

Lab.pressureCoefficient = function (pOverPinf, mach, gamma) {
  return (2 / (gamma * mach * mach)) * (pOverPinf - 1);
};

Lab.weakObliqueShock = function (mach, gamma, delta) {
  var mu = Lab.machAngle(mach);
  var peak = Lab.maximumDeflection(mach, gamma);
  if (delta <= Lab.TURN_TOL) {
    var wave = Lab.shockDownstream(mach, gamma, mu, 0);
    return {
      ok: true,
      wave: "mach-wave",
      theta: mu,
      M: wave.M2,
      p_ratio: wave.p_ratio,
      delta_max: peak.delta
    };
  }
  if (delta > peak.delta + Lab.WEDGE_DETACH) {
    return {
      ok: false,
      wave: "detached",
      theta: null,
      M: null,
      p_ratio: null,
      delta_max: peak.delta
    };
  }
  var theta;
  if (delta >= peak.delta - Lab.WEDGE_DETACH) {
    theta = peak.theta;
  } else {
    theta = Lab.bisectDeflection(mu, peak.theta, delta, mach, gamma, false);
    var strong = Lab.bisectDeflection(peak.theta, Math.PI / 2 - 1e-14, delta, mach, gamma, true);
    if (strong - theta < Lab.ROOT_SPLIT) {
      theta = peak.theta;
    }
  }
  var solved = Lab.deflectionAngle(theta, mach, gamma);
  var down = Lab.shockDownstream(mach, gamma, theta, solved);
  return {
    ok: true,
    wave: "shock",
    theta: theta,
    M: down.M2,
    p_ratio: down.p_ratio,
    delta_max: peak.delta
  };
};

Lab.expandFlow = function (mach, gamma, turn) {
  if (mach <= 1) {
    return { ok: false, wave: "subsonic", M: null, p_ratio: null };
  }
  if (turn <= Lab.TURN_TOL) {
    return { ok: true, wave: "mach-wave", M: mach, p_ratio: 1 };
  }
  var nu1 = Lab.prandtlMeyer(mach, gamma);
  var limit = Lab.nuMax(gamma);
  if (turn > limit - nu1 - 1e-12) {
    return { ok: false, wave: "exceeds-maximum-turn", M: null, p_ratio: null };
  }
  var m2 = Lab.invertPrandtlMeyer(nu1 + turn, gamma);
  return {
    ok: true,
    wave: "expansion",
    M: m2,
    p_ratio: Lab.isentropicPressureRatio(mach, m2, gamma)
  };
};

Lab.applySurfaceTurn = function (mach, pOverPinf, gamma, turn) {
  if (turn >= -Lab.TURN_TOL) {
    var shock = Lab.weakObliqueShock(mach, gamma, Math.max(0, turn));
    if (!shock.ok) {
      return {
        ok: false,
        wave: shock.wave,
        M: null,
        p_over_pinf: null,
        theta: null,
        delta_max: shock.delta_max
      };
    }
    return {
      ok: true,
      wave: shock.wave,
      M: shock.M,
      p_over_pinf: pOverPinf * shock.p_ratio,
      theta: shock.theta,
      delta_max: shock.delta_max
    };
  }
  var expansion = Lab.expandFlow(mach, gamma, -turn);
  if (!expansion.ok) {
    return {
      ok: false,
      wave: expansion.wave,
      M: null,
      p_over_pinf: null,
      theta: null,
      delta_max: null
    };
  }
  return {
    ok: true,
    wave: expansion.wave,
    M: expansion.M,
    p_over_pinf: pOverPinf * expansion.p_ratio,
    theta: null,
    delta_max: null
  };
};

Lab.evaluateDiamond = function (mach, gamma, epsilon, alpha) {
  if (!isFinite(mach) || mach <= 1 || mach > 1e6) {
    throw new Error("Mach must be greater than 1 and at most 1e6");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be greater than 1");
  }
  if (!isFinite(epsilon) || epsilon <= 0 || epsilon >= Math.PI / 2) {
    throw new Error("diamond half-angle must be strictly between 0 and pi/2");
  }
  if (!isFinite(alpha) || Math.abs(alpha) >= Math.PI / 2) {
    throw new Error("angle of attack must have absolute value less than pi/2");
  }
  var deltaU1 = epsilon - alpha;
  var deltaL1 = epsilon + alpha;
  var shoulder = 2 * epsilon;
  var upperLe = Lab.applySurfaceTurn(mach, 1, gamma, deltaU1);
  var lowerLe = Lab.applySurfaceTurn(mach, 1, gamma, deltaL1);
  var state = {
    mach: mach,
    gamma: gamma,
    epsilon: epsilon,
    alpha: alpha,
    delta_u1: deltaU1,
    delta_l1: deltaL1,
    shoulder: shoulder,
    solution: "ok",
    u1: upperLe,
    l1: lowerLe,
    u2: null,
    l2: null,
    Cp_u1: null,
    Cp_u2: null,
    Cp_l1: null,
    Cp_l2: null,
    cn: null,
    ca: null,
    cl: null,
    cd: null
  };
  if (!upperLe.ok) {
    state.solution = "upper-le-" + upperLe.wave;
    return state;
  }
  if (!lowerLe.ok) {
    state.solution = "lower-le-" + lowerLe.wave;
    return state;
  }
  var upperTe = Lab.applySurfaceTurn(upperLe.M, upperLe.p_over_pinf, gamma, -shoulder);
  var lowerTe = Lab.applySurfaceTurn(lowerLe.M, lowerLe.p_over_pinf, gamma, -shoulder);
  state.u2 = upperTe;
  state.l2 = lowerTe;
  if (!upperTe.ok) {
    state.solution = "upper-te-" + upperTe.wave;
    return state;
  }
  if (!lowerTe.ok) {
    state.solution = "lower-te-" + lowerTe.wave;
    return state;
  }
  var cpU1 = Lab.pressureCoefficient(upperLe.p_over_pinf, mach, gamma);
  var cpU2 = Lab.pressureCoefficient(upperTe.p_over_pinf, mach, gamma);
  var cpL1 = Lab.pressureCoefficient(lowerLe.p_over_pinf, mach, gamma);
  var cpL2 = Lab.pressureCoefficient(lowerTe.p_over_pinf, mach, gamma);
  var cn = 0.5 * (cpL1 + cpL2 - cpU1 - cpU2);
  var ca = 0.5 * Math.tan(epsilon) * (cpU1 + cpL1 - cpU2 - cpL2);
  state.Cp_u1 = cpU1;
  state.Cp_u2 = cpU2;
  state.Cp_l1 = cpL1;
  state.Cp_l2 = cpL2;
  state.cn = cn;
  state.ca = ca;
  state.cl = cn * Math.cos(alpha) - ca * Math.sin(alpha);
  state.cd = cn * Math.sin(alpha) + ca * Math.cos(alpha);
  state.solution = "ok";
  return state;
};
