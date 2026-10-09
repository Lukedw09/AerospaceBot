var Lab = Lab || {};

Lab.R_EARTH = 6.356766e6;
Lab.N_STEP = 8000;
Lab.V_ALIGN = 50;
Lab.V_MIN = 1e-9;

Lab.densityAt = function (z) {
  var table = Lab.rho;
  if (!table || !table.length) return 0;
  if (z < 0) z = 0;
  if (z > 86000) return 0;
  var index = z / 100;
  var bin = Math.floor(index);
  if (bin >= table.length - 1) return table[table.length - 1];
  var frac = index - bin;
  return table[bin] * (1 - frac) + table[bin + 1] * frac;
};

Lab.derivatives = function (time, state, kw) {
  var radius = state[0];
  var ur = state[2];
  var ut = state[3];
  var mass = kw.m0 - kw.mdot * time;
  if (mass <= 0) throw new Error("mass reached zero during the burn");
  if (radius < kw.radiusBody) radius = kw.radiusBody;
  var gLocal = kw.mu / (radius * radius);
  var sinth;
  var costh;
  var speed = Math.hypot(ur, ut);
  if (kw.hold) {
    sinth = Math.sin(kw.thetaRef);
    costh = Math.cos(kw.thetaRef);
  } else if (speed > Lab.V_ALIGN) {
    sinth = ur / speed;
    costh = ut / speed;
  } else {
    sinth = Math.sin(kw.thetaRef);
    costh = Math.cos(kw.thetaRef);
  }
  var drag = 0;
  if (kw.cd > 0 && kw.area > 0) {
    var rho = Lab.densityAt(radius - kw.radiusBody);
    drag = kw.cd * 0.5 * Math.max(rho, 0) * speed * speed * kw.area;
  }
  var accel = kw.thrust / mass - drag / mass;
  var dur;
  var dut;
  if (kw.hold) {
    var dSpeed = accel - gLocal * sinth;
    if (radius <= kw.radiusBody + 1e-12 && speed <= Lab.V_MIN && dSpeed < 0) dSpeed = 0;
    dur = dSpeed * sinth;
    dut = dSpeed * costh;
  } else {
    dur = accel * sinth - gLocal + (ut * ut) / radius;
    dut = accel * costh - (ur * ut) / radius;
    if (radius <= kw.radiusBody + 1e-12 && dur < 0) dur = 0;
  }
  return [ur, ut / radius, dur, dut, gLocal * sinth, drag / mass];
};

Lab.rk4 = function (time, state, dt, kw) {
  function shift(scale, deriv) {
    return state.map(function (value, index) { return value + scale * deriv[index]; });
  }
  var k1 = Lab.derivatives(time, state, kw);
  var k2 = Lab.derivatives(time + 0.5 * dt, shift(0.5 * dt, k1), kw);
  var k3 = Lab.derivatives(time + 0.5 * dt, shift(0.5 * dt, k2), kw);
  var k4 = Lab.derivatives(time + dt, shift(dt, k3), kw);
  return state.map(function (value, index) {
    return value + dt * (k1[index] + 2 * k2[index] + 2 * k3[index] + k4[index]) / 6;
  });
};

Lab.odeStage = function (kw) {
  var dt = kw.tb / Lab.N_STEP;
  var state = [kw.state[0], kw.state[1], kw.state[2], kw.state[3], 0, 0];
  var m0Live = kw.m0;
  var dropped = false;
  var rows = [];
  var thetaRef = kw.theta0;
  var tLocal = 0;
  function sample(localT, st, theta) {
    var speed = Math.hypot(st[2], st[3]);
    var alt = st[0] - kw.radiusBody;
    var rho = Lab.densityAt(alt);
    rows.push({
      t: kw.t0 + localT,
      z: alt,
      v: speed,
      gamma: theta,
      rho: rho,
      q: 0.5 * rho * speed * speed,
      m: m0Live - kw.mdot * localT
    });
  }
  sample(0, state, kw.theta0);
  for (var step = 0; step < Lab.N_STEP; step += 1) {
    if (kw.hold) thetaRef = kw.theta0;
    var derivKw = {
      m0: m0Live,
      mdot: kw.mdot,
      thrust: kw.thrust,
      mu: kw.mu,
      radiusBody: kw.radiusBody,
      thetaRef: thetaRef,
      cd: kw.cd,
      area: kw.area,
      hold: kw.hold
    };
    state = Lab.rk4(tLocal, state, dt, derivKw);
    tLocal += dt;
    if (state[0] < kw.radiusBody) {
      state[0] = kw.radiusBody;
      if (state[2] < 0) state[2] = 0;
    }
    var speed = Math.hypot(state[2], state[3]);
    var theta;
    if (kw.hold && state[0] > kw.radiusBody + 1e-9) {
      state[2] = speed * Math.sin(kw.theta0);
      state[3] = speed * Math.cos(kw.theta0);
      theta = kw.theta0;
    } else if (speed > Lab.V_ALIGN) {
      theta = Math.atan2(state[2], state[3]);
    } else {
      theta = thetaRef;
    }
    if (!kw.hold && speed > Lab.V_ALIGN) thetaRef = theta;
    var alt = state[0] - kw.radiusBody;
    if (kw.jettison && !dropped) {
      var event = kw.jettison;
      var hit = (event.time !== undefined && kw.t0 + tLocal >= event.time) ||
        (event.alt !== undefined && alt >= event.alt);
      if (hit) {
        m0Live -= event.mass;
        if (m0Live - kw.mdot * tLocal <= 0) throw new Error("jettison drops the mass through zero");
        dropped = true;
      }
    }
    sample(tLocal, state, theta);
  }
  var speedEnd = Math.hypot(state[2], state[3]);
  return {
    Vbo: speedEnd,
    thetaBo: speedEnd > Lab.V_ALIGN ? Math.atan2(state[2], state[3]) : thetaRef,
    rBo: state[0],
    state: [state[0], state[1], state[2], state[3]],
    dvg: state[4],
    dvD: state[5],
    rows: rows,
    dropped: dropped
  };
};
