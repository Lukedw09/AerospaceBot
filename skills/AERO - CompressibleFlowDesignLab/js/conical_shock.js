/* Taylor-Maccoll cone. Mirrors AERO - ConicalShock. */
var Lab = Lab || {};

Lab.CONE_DETACH = 1e-8;
Lab.RK_STEPS = 800;

Lab.limitingSpeedRatio = function (mach, gamma) {
  var gm = 0.5 * (gamma - 1) * mach * mach;
  return Math.sqrt(gm / (1 + gm));
};

Lab.vacuumSoundSpeedSq = function (gamma, u, v) {
  return 0.5 * (gamma - 1) * (1 - u * u - v * v);
};

Lab.taylorMaccollRadialAcceleration = function (gamma, u, v, theta) {
  var sound = Lab.vacuumSoundSpeedSq(gamma, u, v);
  var denom = v * v - sound;
  if (Math.abs(denom) < 1e-18 || Math.abs(Math.sin(theta)) < 1e-18) {
    throw new Error("Taylor-Maccoll denominator vanished");
  }
  var cot = Math.cos(theta) / Math.sin(theta);
  return sound * (u + v * cot) / denom - u;
};

Lab.resultantMach = function (gamma, u, v) {
  var sound = Lab.vacuumSoundSpeedSq(gamma, u, v);
  if (sound <= 0) {
    throw new Error("local sound speed is not positive");
  }
  return Math.sqrt((u * u + v * v) / sound);
};

Lab.conicalCriticalMach = function (gamma, u, v) {
  return Math.sqrt(((gamma + 1) / (gamma - 1)) * (u * u + v * v));
};

Lab.shockWaveTangent = function (gamma, u, v) {
  return ((gamma - 1) / (gamma + 1)) * (u * u - 1) / (u * v);
};

Lab.polarFromCylindrical = function (vx, vr, theta) {
  var cosine = Math.cos(theta);
  var sine = Math.sin(theta);
  return [vx * cosine + vr * sine, -vx * sine + vr * cosine];
};

Lab.postShockPolar = function (mach, gamma, theta) {
  var delta = Lab.deflectionAngle(theta, mach, gamma);
  var down = Lab.shockDownstream(mach, gamma, theta, delta);
  var speed = Lab.limitingSpeedRatio(down.M2, gamma);
  var vx = speed * Math.cos(delta);
  var vr = speed * Math.sin(delta);
  var polar = Lab.polarFromCylindrical(vx, vr, theta);
  return { u: polar[0], v: polar[1], delta: delta, down: down };
};

Lab.rk4Step = function (theta, u, v, step, gamma) {
  function pair(angle, radial, normal) {
    var acc = Lab.taylorMaccollRadialAcceleration(gamma, radial, normal, angle);
    return [normal, acc];
  }
  var k1 = pair(theta, u, v);
  var k2 = pair(theta + 0.5 * step, u + 0.5 * step * k1[0], v + 0.5 * step * k1[1]);
  var k3 = pair(theta + 0.5 * step, u + 0.5 * step * k2[0], v + 0.5 * step * k2[1]);
  var k4 = pair(theta + step, u + step * k3[0], v + step * k3[1]);
  var uNew = u + step * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6;
  var vNew = v + step * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6;
  return [theta + step, uNew, vNew];
};

Lab.integrateToSurface = function (gamma, thetaShock, uShock, vShock) {
  var theta = thetaShock;
  var u = uShock;
  var v = vShock;
  if (v >= 0) {
    return [theta, u];
  }
  var floor = 1e-4;
  var step = -(theta - floor) / Lab.RK_STEPS;
  if (step >= 0) {
    throw new Error("shock angle is inside the cone");
  }
  for (var i = 0; i < Lab.RK_STEPS * 4; i++) {
    if (theta + step <= floor) {
      step = 0.5 * (floor - theta);
      if (Math.abs(step) < 1e-16) {
        break;
      }
    }
    var next;
    try {
      next = Lab.rk4Step(theta, u, v, step, gamma);
    } catch (err) {
      step *= 0.5;
      if (Math.abs(step) < 1e-12) {
        throw err;
      }
      continue;
    }
    if (!isFinite(next[1]) || !isFinite(next[2])) {
      step *= 0.5;
      if (Math.abs(step) < 1e-12) {
        throw new Error("Taylor-Maccoll integration left the real line");
      }
      continue;
    }
    if (next[2] >= 0) {
      var frac = next[2] !== v ? v / (v - next[2]) : 1;
      frac = Math.min(Math.max(frac, 0), 1);
      return [theta + frac * (next[0] - theta), u + frac * (next[1] - u)];
    }
    theta = next[0];
    u = next[1];
    v = next[2];
    if (Math.abs(step) < Math.abs(-(theta - floor) / Lab.RK_STEPS)) {
      step = -(theta - floor) / Lab.RK_STEPS;
    }
  }
  throw new Error("surface condition v = 0 was not reached");
};

Lab.integrateToShock = function (gamma, thetaCone, uSurface) {
  var theta = thetaCone;
  var u = uSurface;
  var v = 0;
  var ceiling = Math.PI / 2 - 1e-6;
  var step = (ceiling - theta) / Lab.RK_STEPS;
  var previous = null;
  for (var i = 0; i < Lab.RK_STEPS * 4; i++) {
    if (theta + step >= ceiling) {
      step = 0.5 * (ceiling - theta);
      if (step <= 0) {
        break;
      }
    }
    var next = Lab.rk4Step(theta, u, v, step, gamma);
    var residual = Math.tan(next[0]) - Lab.shockWaveTangent(gamma, next[1], next[2]);
    if (previous != null) {
      var residualPrev = previous[3];
      if (residualPrev === 0 || residualPrev * residual <= 0) {
        if (residual === residualPrev) {
          return [next[0], next[1], next[2]];
        }
        var frac = residualPrev / (residualPrev - residual);
        frac = Math.min(Math.max(frac, 0), 1);
        return [
          previous[0] + frac * (next[0] - previous[0]),
          previous[1] + frac * (next[1] - previous[1]),
          previous[2] + frac * (next[2] - previous[2])
        ];
      }
    }
    previous = [next[0], next[1], next[2], residual];
    theta = next[0];
    u = next[1];
    v = next[2];
  }
  throw new Error("Rankine-Hugoniot shock condition was not reached");
};

Lab.coneFromShock = function (mach, gamma, theta) {
  var polar = Lab.postShockPolar(mach, gamma, theta);
  var surface = Lab.integrateToSurface(gamma, theta, polar.u, polar.v);
  return {
    theta: theta,
    delta_shock: polar.delta,
    cone: surface[0],
    u_s: surface[1],
    M2: polar.down.M2,
    p2_over_p1: polar.down.p_ratio,
    Mn1: polar.down.Mn1,
    Mc: Lab.resultantMach(gamma, surface[1], 0),
    Mstar_s: Lab.conicalCriticalMach(gamma, surface[1], 0)
  };
};

Lab._coneCache = {};

Lab.maximumConeAngle = function (mach, gamma) {
  var key = mach.toFixed(8) + "|" + gamma.toFixed(8);
  if (Lab._coneCache[key]) {
    return Lab._coneCache[key];
  }
  var mu = Lab.machAngle(mach);
  var lo = mu + 1e-8;
  var hi = Math.PI / 2 - 1e-6;
  var invphi = (Math.sqrt(5) - 1) / 2;
  var left = hi - invphi * (hi - lo);
  var right = lo + invphi * (hi - lo);
  function value(theta) {
    try {
      return Lab.coneFromShock(mach, gamma, theta).cone;
    } catch (err) {
      return -1;
    }
  }
  var leftValue = value(left);
  var rightValue = value(right);
  for (var i = 0; i < 48; i++) {
    if (leftValue < rightValue) {
      lo = left;
      left = right;
      leftValue = rightValue;
      right = lo + invphi * (hi - lo);
      rightValue = value(right);
    } else {
      hi = right;
      right = left;
      rightValue = leftValue;
      left = hi - invphi * (hi - lo);
      leftValue = value(left);
    }
  }
  var theta = 0.5 * (lo + hi);
  var peak;
  try {
    peak = Lab.coneFromShock(mach, gamma, theta);
  } catch (err) {
    throw new Error("could not locate a maximum attached cone angle");
  }
  var result = { theta: peak.theta, cone: peak.cone };
  Lab._coneCache[key] = result;
  return result;
};

Lab.bisectCone = function (lo, hi, target, mach, gamma) {
  for (var i = 0; i < 80; i++) {
    var mid = 0.5 * (lo + hi);
    var cone;
    try {
      cone = Lab.coneFromShock(mach, gamma, mid).cone;
    } catch (err) {
      hi = mid;
      continue;
    }
    if (cone < target) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return 0.5 * (lo + hi);
};

Lab.evaluateCone = function (mach, gamma, delta) {
  if (!isFinite(mach) || mach <= 1 || mach > 1e6) {
    throw new Error("Mach must be greater than 1 and at most 1e6");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be greater than 1");
  }
  if (!isFinite(delta) || delta < 0 || delta >= Math.PI / 2) {
    throw new Error("cone half-angle must be from 0 up to pi/2");
  }
  var mu = Lab.machAngle(mach);
  var peak = Lab.maximumConeAngle(mach, gamma);
  var state = {
    mach: mach,
    gamma: gamma,
    delta: delta,
    mu: mu,
    delta_max: peak.cone,
    theta_at_max: peak.theta,
    attached: false,
    shock: "detached",
    theta: null,
    Mn1: null,
    M2: null,
    p2_over_p1: null,
    Mc: null,
    Mstar_s: null,
    pc_over_p1: null,
    Cp: null,
    theta_strong: null
  };
  if (delta <= 1e-15) {
    var speed = Lab.limitingSpeedRatio(mach, gamma);
    var u = speed * Math.cos(mu);
    state.attached = true;
    state.shock = "mach-wave";
    state.theta = mu;
    state.Mn1 = 1;
    state.M2 = mach;
    state.p2_over_p1 = 1;
    state.Mc = mach;
    state.Mstar_s = Lab.conicalCriticalMach(gamma, u, -speed * Math.sin(mu));
    state.pc_over_p1 = 1;
    state.Cp = 0;
    return state;
  }
  if (delta > peak.cone + Lab.CONE_DETACH) {
    return state;
  }
  var theta;
  var thetaStrong = null;
  if (delta >= peak.cone - Lab.CONE_DETACH) {
    theta = peak.theta;
    state.shock = "maximum-cone";
  } else {
    theta = Lab.bisectCone(mu + 1e-8, peak.theta, delta, mach, gamma);
    thetaStrong = Lab.bisectCone(peak.theta, Math.PI / 2 - 1e-6, delta, mach, gamma);
    if (thetaStrong - theta < Lab.ROOT_SPLIT) {
      state.shock = "maximum-cone";
      thetaStrong = null;
    } else {
      state.shock = "weak";
    }
  }
  var field = Lab.coneFromShock(mach, gamma, theta);
  var surfaceOverShock = Lab.isentropicPressureRatio(field.M2, field.Mc, gamma);
  var pcOverP1 = surfaceOverShock * field.p2_over_p1;
  state.attached = true;
  state.theta = field.theta;
  state.Mn1 = field.Mn1;
  state.M2 = field.M2;
  state.p2_over_p1 = field.p2_over_p1;
  state.Mc = field.Mc;
  state.Mstar_s = field.Mstar_s;
  state.pc_over_p1 = pcOverP1;
  state.Cp = 2 * (pcOverP1 - 1) / (gamma * mach * mach);
  if (thetaStrong != null) {
    try {
      var strong = Lab.coneFromShock(mach, gamma, thetaStrong);
      state.theta_strong = strong.theta;
    } catch (err) {
      state.theta_strong = null;
    }
  }
  return state;
};
