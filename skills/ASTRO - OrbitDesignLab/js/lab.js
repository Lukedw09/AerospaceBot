/* Orbit design lab UI and the combined evaluate used by --check. */
var Lab = Lab || {};

Lab.eclipseFraction = function (planet, orbit, beta) {
  if (orbit <= planet) return 0.0;
  var ratio = planet / orbit;
  var betaStar = Math.asin(ratio);
  if (Math.abs(beta) >= betaStar) return 0.0;
  var argument = Math.sqrt(1.0 - ratio * ratio) / Math.cos(beta);
  if (argument > 1.0) argument = 1.0;
  if (argument < -1.0) argument = -1.0;
  return Math.acos(argument) / Math.PI;
};

Lab.meanFromNu = function (e, nu) {
  var denom = 1.0 + e * Math.cos(nu);
  var cosE = (e + Math.cos(nu)) / denom;
  var sinE = Math.sin(nu) * Math.sqrt(Math.max(0.0, 1.0 - e * e)) / denom;
  var eccentric = Math.atan2(sinE, cosE);
  return eccentric - e * Math.sin(eccentric);
};

Lab.coastPoints = function (r0, v0, tof, mu, count) {
  var r = r0.slice();
  var v = v0.slice();
  var n = count || 48;
  var dt = tof / n;
  var pts = [r.slice()];
  function deriv(rr, vv) {
    var rad = Lab.vecNorm(rr);
    return [vv, Lab.vecScale(rr, -mu / Math.pow(rad, 3))];
  }
  var i;
  for (i = 0; i < n; i += 1) {
    var k1 = deriv(r, v);
    var k2 = deriv(Lab.vecAdd(r, Lab.vecScale(k1[0], dt / 2)), Lab.vecAdd(v, Lab.vecScale(k1[1], dt / 2)));
    var k3 = deriv(Lab.vecAdd(r, Lab.vecScale(k2[0], dt / 2)), Lab.vecAdd(v, Lab.vecScale(k2[1], dt / 2)));
    var k4 = deriv(Lab.vecAdd(r, Lab.vecScale(k3[0], dt)), Lab.vecAdd(v, Lab.vecScale(k3[1], dt)));
    r = Lab.vecAdd(r, Lab.vecScale(Lab.vecAdd(Lab.vecAdd(k1[0], Lab.vecScale(k2[0], 2)), Lab.vecAdd(Lab.vecScale(k3[0], 2), k4[0])), dt / 6));
    v = Lab.vecAdd(v, Lab.vecScale(Lab.vecAdd(Lab.vecAdd(k1[1], Lab.vecScale(k2[1], 2)), Lab.vecAdd(Lab.vecScale(k3[1], 2), k4[1])), dt / 6));
    pts.push(r.slice());
  }
  return pts;
};

Lab.tangent = function (nu, sense) {
  var dir = [-Math.sin(nu), Math.cos(nu), 0.0];
  if (sense === "retrograde") dir = [-dir[0], -dir[1], -dir[2]];
  if (sense === "none") dir = [0.0, 0.0, 0.0];
  return dir;
};

Lab.compute = function (seed, pack) {
  pack = pack || { density: [] };
  var r0 = seed.R0 || Lab.R0_EARTH;
  var mu = Lab.muOf(r0);
  var r1;
  var r2;
  if (seed.alt !== null && seed.alt !== undefined && seed.ecc !== null && seed.ecc !== undefined) {
    var pair = Lab.radiiFromAltitude(r0, Number(seed.alt), Number(seed.ecc));
    r1 = pair.r1;
    r2 = pair.r2;
  } else {
    r1 = Number(seed.r1);
    r2 = Number(seed.r2);
  }
  var rb = Number(seed.rb);
  var hoh = Lab.hohmann(mu, r1, r2);
  var bi = Lab.bielliptic(mu, r1, r2, rb);
  var strategy = seed.strategy || "auto";
  if (strategy === "auto") strategy = bi.recommendation === "bielliptic" ? "bielliptic" : "hohmann";

  var plane = Lab.planeChange(mu, Number(seed.plane_a || r1), Number(seed.plane_di));
  var geo = Lab.geoStationKeeping(Number(seed.geo_di), Number(seed.geo_e), Number(seed.geo_burns), Number(seed.geo_years));
  var cw = Lab.clohessyWiltshire(
    Number(seed.cw_x), Number(seed.cw_z), Number(seed.cw_xd), Number(seed.cw_zd),
    Number(seed.cw_time), Number(seed.cw_a || r1), mu
  );
  var phase = Lab.phasing(Number(seed.phase_r || r1), Number(seed.phase), seed.phase_lead, Number(seed.phase_revs), mu);
  var lamR1 = [Number(seed.lam_r1x), Number(seed.lam_r1y), Number(seed.lam_r1z)];
  var lamR2 = [Number(seed.lam_r2x), Number(seed.lam_r2y), Number(seed.lam_r2z)];
  var lambert = Lab.lambert(lamR1, lamR2, Number(seed.lam_tof), mu, seed.lam_way || "short");
  var rho = Lab.densityAt(Number(seed.drag_alt), pack.density, seed.drag_rho);
  var drag = Lab.dragDeltaV(Number(seed.drag_alt), Number(seed.drag_mass), Number(seed.drag_cd), Number(seed.drag_area), rho);
  var dragRevs = Number(seed.drag_revs || 1);
  var raise = Lab.leoRaise(mu, Number(seed.raise_r1 || r1), Number(seed.raise_r2 || r2), Number(seed.raise_di || 0));
  var insertion = Lab.orbitInsertion(mu, r0, Number(seed.ins_r), Number(seed.ins_v), Number(seed.ins_gamma));
  var elA = Number(seed.el_a || r1);
  var elE = Number(seed.el_e || 0);
  var elI = Number(seed.el_i || 0);
  var elBeta = Number(seed.el_beta || 0);
  var eclipse = Lab.eclipseFraction(r0, elA, elBeta);
  var periodEl = Lab.orbitalPeriod(mu, elA);
  var gtA = Number(seed.gt_a || r1);
  var gtE = Number(seed.gt_e || 0);
  var gtI = Number(seed.gt_i || 0);
  var gtPeriod = Lab.orbitalPeriod(mu, gtA);
  var gtMean = Lab.meanFromNu(gtE, Number(seed.gt_nu || 0));
  var gtSample = Lab.subsatellite(
    mu, gtA, gtE, gtI, Number(seed.gt_raan || 0), Number(seed.gt_arg || 0), gtMean,
    gtPeriod / 4.0, 0.0, Lab.J2_GSFC, Lab.AE_WGS84, Lab.F_WGS84, Lab.AE_WGS84
  );
  var covAlt = Number(seed.cov_alt);
  var cov = Lab.coverage(Lab.R0_EARTH + covAlt, Number(seed.cov_elev), Lab.R0_EARTH);
  var j2 = Lab.j2Rates(mu, Number(seed.j2_a || r1), Number(seed.j2_e || 0), Number(seed.j2_i || gtI), Lab.J2_GSFC, Lab.AE_WGS84);
  var launch = Lab.launchAzimuth(Number(seed.launch_lat), Number(seed.launch_az), Lab.AE_WGS84, Lab.OMEGA_E);

  var pieces = [];
  var use = seed.budget || {};
  function on(flag, fallback) {
    if (use[flag] === undefined) return fallback;
    return !!use[flag];
  }
  if (on("hohmann", strategy === "hohmann")) pieces.push({ name: "hohmann_depart", dv: hoh.dv_depart }, { name: "hohmann_arrive", dv: hoh.dv_arrive });
  if (on("bielliptic", strategy === "bielliptic")) {
    pieces.push({ name: "bielliptic_1", dv: bi.dv1 }, { name: "bielliptic_2", dv: bi.dv2 }, { name: "bielliptic_3", dv: bi.dv3 });
  }
  if (on("plane", false)) pieces.push({ name: "plane_change", dv: plane.dv });
  if (on("geo", false)) pieces.push({ name: "geo_ns", dv: geo.dv_ns }, { name: "geo_ew", dv: geo.dv_ew });
  if (on("phasing", false)) pieces.push({ name: "phasing", dv: phase.dv_total });
  if (on("lambert", false)) pieces.push({ name: "lambert_depart", dv: lambert.dv1 }, { name: "lambert_arrive", dv: lambert.dv2 });
  if (on("cw", false)) pieces.push({ name: seed.cw_piece || "cw_null", dv: (seed.cw_piece === "cw_hold" ? cw.dv_hold : cw.dv_null) });
  if (on("drag", false)) pieces.push({ name: "drag", dv: drag.dv_per_rev * dragRevs });
  if (on("raise", false)) pieces.push({ name: "leo_raise", dv: raise.dv_total });
  if (on("insertion", false)) pieces.push({ name: "circularization", dv: insertion.dv || 0 });
  var dvTotal = 0;
  var i;
  for (i = 0; i < pieces.length; i += 1) dvTotal += pieces[i].dv;
  var prop = null;
  if (seed.dry && (seed.isp || seed.ve) && pieces.length) {
    prop = Lab.vacuumPropellant(Number(seed.dry), Number(seed.growth || 0), dvTotal, seed.isp, seed.ve);
  }

  return {
    ok: true,
    mu: mu,
    r0: r0,
    r1: r1,
    r2: r2,
    rb: rb,
    strategy: strategy,
    hohmann_dv: hoh.dv,
    hohmann_dv_depart: hoh.dv_depart,
    hohmann_dv_arrive: hoh.dv_arrive,
    hohmann_tof: hoh.tof,
    hohmann_recommendation: hoh.recommendation,
    bielliptic_dv: bi.dv,
    bielliptic_dv1: bi.dv1,
    bielliptic_dv2: bi.dv2,
    bielliptic_dv3: bi.dv3,
    bielliptic_tof: bi.tof,
    bielliptic_recommendation: bi.recommendation,
    plane_dv: plane.dv,
    geo_ns: geo.dv_ns,
    geo_ew: geo.dv_ew,
    geo_total: geo.dv_total,
    geo_a: geo.a,
    cw_x: cw.x,
    cw_z: cw.z,
    cw_null: cw.dv_null,
    cw_hold: cw.dv_hold,
    phase_dv: phase.dv_total,
    lambert_dv1: lambert.dv1,
    lambert_dv2: lambert.dv2,
    drag_dv: drag.dv_per_rev,
    drag_rho: drag.rho,
    raise_dv: raise.dv_total,
    raise_plane: raise.dv_plane,
    raise_gravity: raise.dv_gravity_loss,
    insertion_dv: insertion.dv,
    insertion_where: insertion.where,
    eclipse_fraction: eclipse,
    gt_lat: gtSample.lat,
    gt_lon: gtSample.lon,
    coverage_swath: cov.swath,
    coverage_footprint: cov.footprint,
    coverage_revisit: cov.revisit_periods,
    coverage_lambda: cov.lambda,
    j2_node: j2.node,
    j2_apsis: j2.apsis,
    launch_inc: launch.inc,
    launch_assist: launch.v_assist,
    dv_total: dvTotal,
    m_propellant: prop ? prop.m_propellant : null,
    m_wet: prop ? prop.m_wet : null,
    pieces: pieces,
    _detail: {
      hoh: hoh, bi: bi, plane: plane, geo: geo, cw: cw, phase: phase,
      lambert: lambert, lamR1: lamR1, lamR2: lamR2, drag: drag, raise: raise,
      insertion: insertion, j2: j2, launch: launch, cov: cov,
      elA: elA, elE: elE, elI: elI, periodEl: periodEl,
      gtA: gtA, gtE: gtE, gtI: gtI, gtPeriod: gtPeriod, gtMean: gtMean,
      covAlt: covAlt
    }
  };
};

Lab.atNu = function (radius, nu) {
  return [radius * Math.cos(nu), radius * Math.sin(nu), 0];
};

Lab.resamplePath = function (points, count) {
  var n = count || points.length;
  if (!points.length) return [];
  if (points.length === 1 || n < 2) return [points[0].slice()];
  var out = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var f = (i / (n - 1)) * (points.length - 1);
    var i0 = Math.floor(f);
    var span = f - i0;
    var a = points[Math.min(points.length - 1, i0)];
    var b = points[Math.min(points.length - 1, i0 + 1)];
    out.push([
      a[0] + (b[0] - a[0]) * span,
      a[1] + (b[1] - a[1]) * span,
      a[2] + (b[2] - a[2]) * span
    ]);
  }
  return out;
};

Lab.planeArc = function (r1, r2, radius, a0, a1, count, way) {
  var u = Lab.vecUnit(r1);
  var h = Lab.vecCross(r1, r2);
  if (Lab.vecNorm(h) < 1e-6) h = [0, 0, 1];
  if (way === "long") h = Lab.vecScale(h, -1);
  var tang = Lab.vecUnit(Lab.vecCross(h, r1));
  var n = count || 49;
  var pts = [];
  var i;
  for (i = 0; i < n; i += 1) {
    var th = a0 + (a1 - a0) * (n === 1 ? 0 : i / (n - 1));
    pts.push(Lab.vecAdd(Lab.vecScale(u, radius * Math.cos(th)), Lab.vecScale(tang, radius * Math.sin(th))));
  }
  return pts;
};

Lab.parkingDelta = function (vVec, rVec, mu) {
  var radial = Lab.vecUnit(rVec);
  var normal = Lab.vecCross(rVec, vVec);
  if (Lab.vecNorm(normal) < 1e-8) return vVec.slice();
  var tangential = Lab.vecCross(Lab.vecUnit(normal), radial);
  return Lab.vecSub(vVec, Lab.vecScale(tangential, Lab.circularSpeed(mu, Lab.vecNorm(rVec))));
};

Lab.arcMinRadius = function (r0, v0, tof, mu) {
  var pts = Lab.coastPoints(r0, v0, tof, mu, 96);
  var least = Infinity;
  var i;
  for (i = 0; i < pts.length; i += 1) least = Math.min(least, Lab.vecNorm(pts[i]));
  return least;
};

Lab.lambertOutside = function (r1, r2, tof, mu, way, planet) {
  var margin = planet + 120000.0;
  function trial(flight) {
    var sol = Lab.lambert(r1, r2, flight, mu, way);
    return Lab.arcMinRadius(r1, sol.v1, flight, mu);
  }
  if (trial(tof) >= margin) return { tof: tof, raised: false };
  var lo = tof;
  var hi = tof;
  var guard = 0;
  var clear = false;
  while (guard < 16) {
    hi *= 1.4;
    guard += 1;
    try {
      clear = trial(hi) >= margin;
    } catch (err) {
      return { tof: tof, raised: false };
    }
    if (clear) break;
    lo = hi;
  }
  if (!clear) return { tof: tof, raised: false };
  var i;
  for (i = 0; i < 18; i += 1) {
    var mid = 0.5 * (lo + hi);
    var ok = false;
    try {
      ok = trial(mid) >= margin;
    } catch (err) {
      ok = false;
    }
    if (ok) hi = mid;
    else lo = mid;
  }
  return { tof: hi, raised: true };
};

Lab.launchGeometry = function (lat, az, orbitRadius) {
  var earthR = Lab.AE_WGS84;
  var site = [Math.cos(lat), 0, Math.sin(lat)];
  var north = [-Math.sin(lat), 0, Math.cos(lat)];
  var east = [0, 1, 0];
  var head = [
    Math.cos(az) * north[0] + Math.sin(az) * east[0],
    Math.cos(az) * north[1] + Math.sin(az) * east[1],
    Math.cos(az) * north[2] + Math.sin(az) * east[2]
  ];
  var normal = Lab.vecCross(site, head);
  if (Lab.vecNorm(normal) < 1e-8) normal = [0, 0, 1];
  else normal = Lab.vecUnit(normal);
  var tang = Lab.vecUnit(Lab.vecCross(normal, site));
  var orbit = [];
  var track = [];
  var count = 161;
  var i;
  for (i = 0; i < count; i += 1) {
    var th = 2 * Math.PI * i / (count - 1);
    var point = Lab.vecAdd(Lab.vecScale(site, orbitRadius * Math.cos(th)), Lab.vecScale(tang, orbitRadius * Math.sin(th)));
    orbit.push(point);
    var span = Lab.vecNorm(point);
    track.push({ lat: Math.asin(point[2] / span), lon: Math.atan2(point[1], point[0]) });
  }
  var ascent = [];
  for (i = 0; i <= 28; i += 1) {
    var u = i / 28;
    ascent.push(Lab.vecScale(site, earthR + (orbitRadius - earthR) * u));
  }
  return { pad: Lab.vecScale(site, earthR), ascent: ascent, orbit: orbit, track: track };
};

Lab.sceneFor = function (mode, result, seed) {
  var d = result._detail;
  var layers = [];
  var sequence = [];
  var burns = [];
  var legend = [{ label: "Rotation axis", color: "#1b2631" }];
  function coast(points, wall, focus, label) {
    sequence.push({ kind: "coast", points: points, wall: wall, focus: focus, label: label });
  }
  function hold(pos, wall, index, morph, label) {
    sequence.push({ kind: "burn", pos: pos, wall: wall, burn: index, morph: morph, label: label });
  }
  function layer(id, points, color, label) {
    layers.push({ id: id, points: points, color: color });
    if (label) legend.push({ label: label, color: color });
  }
  function token() {
    return [
      mode, Math.round(result.r1), Math.round(result.r2), Math.round(result.rb), result.strategy,
      seed.plane_di, seed.plane_i, seed.lam_tof, seed.lam_r2x, seed.lam_r2y, seed.lam_r2z, seed.lam_way,
      seed.raise_di, seed.phase, seed.ins_gamma, seed.gt_i, seed.cov_i
    ].join("|");
  }
  function pack() {
    return {
      r0: result.r0,
      token: token(),
      layers: layers,
      sequence: sequence,
      burns: burns,
      legend: legend,
      markers: []
    };
  }
  function hohmannPlay(h, rDepart, rArrive, ids, transferColor, departLabel, arriveLabel, skipTail) {
    var inward = h.direction === "inward";
    var departNu = inward ? Math.PI : 0;
    var arriveNu = inward ? 0 : Math.PI;
    var departPos = Lab.atNu(rDepart, departNu);
    var arrivePos = Lab.atNu(rArrive, arriveNu);
    var transfer = Lab.ellipseSamples(h.periapsis, h.apoapsis, departNu, arriveNu, 90);
    var i0 = burns.length;
    burns.push({ pos: departPos, dir: Lab.tangent(departNu, h.sense_depart) });
    burns.push({ pos: arrivePos, dir: Lab.tangent(arriveNu, h.sense_arrive) });
    coast(Lab.ellipseSamples(rDepart, rDepart, departNu - 1.5, departNu, 36), 3.4, ids.depart, "Coast, " + departLabel);
    hold(departPos, 2.8, i0, {
      rp0: rDepart, ra0: rDepart, i0: 0,
      rp1: h.periapsis, ra1: h.apoapsis, i1: 0,
      color1: transferColor, hide: ids.depart, hide2: ids.transfer
    }, "Burn, departure");
    coast(transfer, 8.5, ids.transfer, "Coast, transfer");
    hold(arrivePos, 2.8, i0 + 1, {
      rp0: h.periapsis, ra0: h.apoapsis, i0: 0,
      rp1: rArrive, ra1: rArrive, i1: 0,
      color1: "#117a65", hide: ids.transfer, hide2: ids.arrive
    }, "Burn, arrival");
    if (!skipTail) coast(Lab.ellipseSamples(rArrive, rArrive, arriveNu, arriveNu + 1.8, 40), 4.2, ids.arrive, "Coast, " + arriveLabel);
  }

  if (mode === "transfer") {
    var hoh = d.hoh;
    layer("c1", Lab.circleSamples(result.r1), "#1a5276", "Initial orbit");
    layer("c2", Lab.circleSamples(result.r2), "#117a65", "Final orbit");
    layer("hoh", Lab.conicSamples(hoh.periapsis, hoh.apoapsis, 0, 161), "#1b4f72", "Hohmann transfer");
    layer("bi1", Lab.conicSamples(result.r1, result.rb, 0, 161), "#6c3483", "Bielliptic, first leg");
    layer("bi2", Lab.conicSamples(result.r2, result.rb, 0, 161), "#922b21", "Bielliptic, second leg");
    if (result.strategy === "bielliptic") {
      var p1 = Lab.atNu(result.r1, 0);
      var pmid = Lab.atNu(result.rb, Math.PI);
      var p2 = Lab.atNu(result.r2, 0);
      var leg1 = Lab.ellipseSamples(result.r1, result.rb, 0, Math.PI, 80);
      var leg2 = Lab.ellipseSamples(result.r2, result.rb, Math.PI, 2 * Math.PI, 80);
      burns.push({ pos: p1, dir: Lab.tangent(0, Lab.burnSense(Lab.apsisSpeed(result.mu, result.r1, result.rb), Lab.circularSpeed(result.mu, result.r1))) });
      burns.push({ pos: pmid, dir: Lab.tangent(Math.PI, Lab.burnSense(Lab.apsisSpeed(result.mu, result.rb, result.r2), Lab.apsisSpeed(result.mu, result.rb, result.r1))) });
      burns.push({ pos: p2, dir: Lab.tangent(0, Lab.burnSense(Lab.circularSpeed(result.mu, result.r2), Lab.apsisSpeed(result.mu, result.r2, result.rb))) });
      coast(Lab.ellipseSamples(result.r1, result.r1, -1.2, 0, 28), 3.2, "c1", "Coast, initial orbit");
      hold(p1, 2.6, 0, {
        rp0: result.r1, ra0: result.r1, i0: 0, rp1: result.r1, ra1: result.rb, i1: 0,
        color1: "#6c3483", hide: "c1", hide2: "bi1"
      }, "Burn 1, onto first ellipse");
      coast(leg1, 7.5, "bi1", "Coast, first leg");
      hold(pmid, 2.6, 1, {
        rp0: result.r1, ra0: result.rb, i0: 0, rp1: result.r2, ra1: result.rb, i1: 0,
        color1: "#922b21", hide: "bi1", hide2: "bi2"
      }, "Burn 2, apoapsis");
      coast(leg2, 7.5, "bi2", "Coast, second leg");
      hold(p2, 2.6, 2, {
        rp0: result.r2, ra0: result.rb, i0: 0, rp1: result.r2, ra1: result.r2, i1: 0,
        color1: "#117a65", hide: "bi2", hide2: "c2"
      }, "Burn 3, circularize");
      coast(Lab.ellipseSamples(result.r2, result.r2, 0, 1.6, 32), 4, "c2", "Coast, final orbit");
    } else {
      hohmannPlay(hoh, result.r1, result.r2, { depart: "c1", transfer: "hoh", arrive: "c2" }, "#1b4f72", "initial orbit", "final orbit");
    }
  } else if (mode === "plane") {
    var inc = Number(seed.plane_i || 0.6);
    var inc2 = inc + Number(seed.plane_di);
    var radiusP = d.plane.radius;
    var node = [radiusP, 0, 0];
    layer("i0", Lab.inclinedCircle(radiusP, inc), "#1a5276", "Initial inclination");
    layer("i1", Lab.inclinedCircle(radiusP, inc2), "#c0392b", "Final inclination");
    burns.push({
      pos: node,
      dir: [0, Math.cos(inc2) - Math.cos(inc), Math.sin(inc2) - Math.sin(inc)]
    });
    coast(Lab.conicSamples(radiusP, radiusP, inc, 40, -1.3, 0), 3.5, "i0", "Coast to the node");
    hold(node, 2.8, 0, {
      rp0: radiusP, ra0: radiusP, i0: inc, rp1: radiusP, ra1: radiusP, i1: inc2,
      color1: "#c0392b", hide: "i0", hide2: "i1"
    }, "Burn, plane change");
    coast(Lab.conicSamples(radiusP, radiusP, inc2, 80, 0, 2.2), 6, "i1", "Coast, new plane");
  } else if (mode === "geo") {
    var geoA = d.geo.a;
    layer("geo", Lab.circleSamples(geoA), "#1a5276", "Geostationary orbit");
    burns.push({ pos: [geoA, 0, 0], dir: [0, 0, 1] });
    burns.push({ pos: [-geoA, 0, 0], dir: [0, -1, 0] });
    coast(Lab.ellipseSamples(geoA, geoA, -1.1, 0, 28), 3.2, "geo", "Coast");
    hold([geoA, 0, 0], 2.4, 0, null, "North-South trim");
    coast(Lab.ellipseSamples(geoA, geoA, 0, Math.PI, 64), 6.5, "geo", "Coast to the east-west node");
    hold([-geoA, 0, 0], 2.4, 1, null, "East-West trim");
    coast(Lab.ellipseSamples(geoA, geoA, Math.PI, Math.PI + 1.5, 32), 3.5, "geo", "Coast");
  } else if (mode === "cw") {
    var chief = Number(seed.cw_a || result.r1);
    var span = 1;
    d.cw.path.forEach(function (p) { span = Math.max(span, Math.hypot(p[0], p[1])); });
    var gain = (0.14 * chief) / span;
    var rel = d.cw.path.map(function (p) {
      return [chief + p[1] * gain, p[0] * gain, 0];
    });
    layer("chief", Lab.circleSamples(chief), "#1a5276", "Chief orbit");
    layer("deputy", rel, "#c0392b", "Deputy path (magnified)");
    var end = rel[rel.length - 1];
    burns.push({ pos: end, dir: [-Number(seed.cw_zd), -Number(seed.cw_xd), 0] });
    coast(rel, 8, "deputy", "Coast, relative motion");
    hold(end, 2.6, 0, null, "Burn, null relative rate");
  } else if (mode === "phasing") {
    var phaseR = Number(seed.phase_r || result.r1);
    var atApo = d.phase.rp < phaseR;
    var phaseNu = atApo ? Math.PI : 0;
    var phasePos = Lab.atNu(phaseR, phaseNu);
    var senseIn = d.phase.a >= phaseR ? "prograde" : "retrograde";
    layer("circ", Lab.circleSamples(phaseR), "#1a5276", "Target orbit");
    layer("ell", Lab.conicSamples(d.phase.rp, d.phase.ra, 0, 161), "#922b21", "Phasing ellipse");
    burns.push({ pos: phasePos, dir: Lab.tangent(phaseNu, senseIn) });
    burns.push({ pos: phasePos, dir: Lab.tangent(phaseNu, senseIn === "prograde" ? "retrograde" : "prograde") });
    coast(Lab.ellipseSamples(phaseR, phaseR, phaseNu - 1.2, phaseNu, 28), 3, "circ", "Coast, circular orbit");
    hold(phasePos, 2.6, 0, {
      rp0: phaseR, ra0: phaseR, i0: 0, rp1: d.phase.rp, ra1: d.phase.ra, i1: 0,
      color1: "#922b21", hide: "circ", hide2: "ell"
    }, "Burn, enter phasing orbit");
    coast(Lab.ellipseSamples(d.phase.rp, d.phase.ra, phaseNu, phaseNu + 2 * Math.PI, 120), 9, "ell", "Coast one phasing revolution");
    hold(phasePos, 2.6, 1, {
      rp0: d.phase.rp, ra0: d.phase.ra, i0: 0, rp1: phaseR, ra1: phaseR, i1: 0,
      color1: "#1a5276", hide: "ell", hide2: "circ"
    }, "Burn, return to the circle");
    coast(Lab.ellipseSamples(phaseR, phaseR, phaseNu, phaseNu + 1.4, 28), 3.2, "circ", "Coast, circular orbit");
  } else if (mode === "lambert") {
    var way = seed.lam_way || "short";
    var angle = d.lambert.angle;
    var nArc = 72;
    var r1n = Lab.vecNorm(d.lamR1);
    var r2n = Lab.vecNorm(d.lamR2);
    var flown = Lab.resamplePath(Lab.coastPoints(d.lamR1, d.lambert.v1, Number(seed.lam_tof), result.mu, 80), nArc);
    var chord1 = Lab.planeArc(d.lamR1, d.lamR2, r1n, 0, angle, nArc, way);
    var chord2 = Lab.planeArc(d.lamR1, d.lamR2, r2n, 0, angle, nArc, way);
    layer("park1", Lab.planeArc(d.lamR1, d.lamR2, r1n, 0, 2 * Math.PI, 97, way), "#1a5276", "Departure parking orbit");
    layer("park2", Lab.planeArc(d.lamR1, d.lamR2, r2n, 0, 2 * Math.PI, 97, way), "#117a65", "Arrival parking orbit");
    layer("xfer", flown, "#6c3483", "Lambert transfer");
    burns.push({ pos: d.lamR1.slice(), dir: Lab.parkingDelta(d.lambert.v1, d.lamR1, result.mu) });
    burns.push({ pos: d.lamR2.slice(), dir: Lab.parkingDelta(d.lambert.v2, d.lamR2, result.mu) });
    coast(Lab.planeArc(d.lamR1, d.lamR2, r1n, -0.7, 0, 24, way), 3, "park1", "Coast, departure orbit");
    hold(d.lamR1.slice(), 2.8, 0, { paths: [chord1, flown], color: "#6c3483", hide: "park1", hide2: "xfer" }, "Burn, depart parking orbit");
    coast(flown, 8, "xfer", "Coast, Lambert arc");
    hold(d.lamR2.slice(), 2.8, 1, { paths: [flown, chord2], color: "#117a65", hide: "xfer", hide2: "park2" }, "Burn, arrive and circularize");
    coast(Lab.planeArc(d.lamR1, d.lamR2, r2n, angle, angle + 0.9, 24, way), 3.4, "park2", "Coast, arrival orbit");
  } else if (mode === "coverage" || mode === "ground" || mode === "elements") {
    var radius = mode === "coverage" ? result.r0 + d.covAlt : (mode === "ground" ? d.gtA : d.elA);
    var incOrbit = mode === "elements" ? d.elI : (mode === "coverage" ? Number(seed.cov_i || 0.9) : d.gtI);
    var names = { coverage: "Coverage orbit", ground: "Ground-track orbit", elements: "Orbit" };
    layer("orb", Lab.inclinedCircle(radius, incOrbit, 161), "#1a5276", names[mode]);
    coast(Lab.inclinedCircle(radius, incOrbit, 160), 12, "orb", "Coast");
  } else if (mode === "j2") {
    var radiusJ = Number(seed.j2_a || result.r1);
    var incJ = Number(seed.j2_i || 0);
    var base = Lab.inclinedCircle(radiusJ, incJ, 161);
    var nodeRate = d.j2.node;
    var target = 25 * Math.PI / 180;
    var days = Math.abs(nodeRate) < 1e-15 ? 1 : Math.min(365, Math.max(0.5, target / (Math.abs(nodeRate) * Lab.DAY_S)));
    var turn = nodeRate * days * Lab.DAY_S;
    var dayLabel = (Math.round(days * 10) / 10) + " days";
    function spin(pts, ang) {
      var c = Math.cos(ang);
      var s = Math.sin(ang);
      return pts.map(function (p) {
        return [c * p[0] - s * p[1], s * p[0] + c * p[1], p[2]];
      });
    }
    layer("now", base, "#1a5276", "Orbit now");
    layer("later", spin(base, turn), "#b9770e", "Node after " + dayLabel);
    coast(base, 12, "now", "Coast");
  } else if (mode === "raise") {
    var rr1 = Number(seed.raise_r1 || result.r1);
    var rr2 = Number(seed.raise_r2 || result.r2);
    var raised = Lab.hohmann(result.mu, rr1, rr2);
    var di = Number(seed.raise_di || 0);
    var slower = Math.max(rr1, rr2);
    var tilt1 = Math.abs(di) > 1e-8 && slower === rr1;
    var tilt2 = Math.abs(di) > 1e-8 && slower === rr2;
    layer("c1", tilt1 ? Lab.inclinedCircle(rr1, di) : Lab.circleSamples(rr1), "#1a5276", "Initial orbit");
    layer("c2", tilt2 ? Lab.inclinedCircle(rr2, di) : Lab.circleSamples(rr2), "#117a65", "Final orbit");
    layer("hoh", Lab.conicSamples(raised.periapsis, raised.apoapsis, 0, 141), "#c0392b", "Hohmann raise");
    if (Math.abs(di) > 1e-8 && slower === rr1) {
      var node1 = Lab.atNu(rr1, raised.direction === "inward" ? Math.PI : 0);
      burns.push({ pos: node1, dir: [0, Math.cos(di) - 1, Math.sin(di)] });
      coast(Lab.ellipseSamples(rr1, rr1, -1.1, 0, 24), 2.8, "c1", "Coast to the node");
      hold(node1, 2.4, 0, {
        rp0: rr1, ra0: rr1, i0: 0, rp1: rr1, ra1: rr1, i1: di,
        color1: "#1a5276", hide: "c1"
      }, "Burn, plane change");
    }
    hohmannPlay(raised, rr1, rr2, { depart: "c1", transfer: "hoh", arrive: "c2" }, "#c0392b", "lower orbit", "higher orbit", tilt2);
    if (Math.abs(di) > 1e-8 && slower === rr2) {
      var arriveNuR = raised.direction === "inward" ? 0 : Math.PI;
      var node2 = Lab.atNu(rr2, arriveNuR);
      burns.push({ pos: node2, dir: [0, Math.cos(di) - 1, Math.sin(di)] });
      hold(node2, 2.4, burns.length - 1, {
        rp0: rr2, ra0: rr2, i0: 0, rp1: rr2, ra1: rr2, i1: di,
        color1: "#117a65", hide: "c2"
      }, "Burn, plane change");
      coast(Lab.conicSamples(rr2, rr2, di, 70, arriveNuR, arriveNuR + 1.8), 4, "c2", "Coast, inclined orbit");
    }
  } else if (mode === "insertion") {
    if (!d.insertion.closed) {
      legend.push({ label: "Open trajectory", color: "#922b21" });
      coast([Lab.atNu(Number(seed.ins_r), 0)], 4, "", "Trajectory is not closed");
    } else if (d.insertion.where === "burnout") {
      var here = Lab.atNu(d.insertion.r_circ, 0);
      layer("circ", Lab.circleSamples(d.insertion.r_circ), "#117a65", "Nearly circular orbit");
      burns.push({ pos: here, dir: [0, 1, 0] });
      coast(Lab.ellipseSamples(d.insertion.r_circ, d.insertion.r_circ, -1.2, 0, 28), 3, "circ", "Coast");
      hold(here, 2.4, 0, null, "Burn at burnout");
      coast(Lab.ellipseSamples(d.insertion.r_circ, d.insertion.r_circ, 0, 1.6, 32), 4, "circ", "Coast");
    } else {
      var eIns = d.insertion.e;
      var pIns = d.insertion.h * d.insertion.h / result.mu;
      var cosNu = eIns < 1e-8 ? 1 : (pIns / Number(seed.ins_r) - 1) / eIns;
      cosNu = Math.max(-1, Math.min(1, cosNu));
      var sinSign = Math.sin(Number(seed.ins_gamma)) >= 0 ? 1 : -1;
      var nuIns = Math.atan2(sinSign * Math.sqrt(Math.max(0, 1 - cosNu * cosNu)), cosNu);
      if (nuIns < 0) nuIns += 2 * Math.PI;
      var apoNu = nuIns > Math.PI + 1e-4 ? Math.PI + 2 * Math.PI : Math.PI;
      var apoPos = Lab.atNu(d.insertion.ra, Math.PI);
      layer("ell", Lab.conicSamples(d.insertion.rp, d.insertion.ra, 0, 161), "#922b21", "Burnout ellipse");
      layer("circ", Lab.circleSamples(d.insertion.r_circ), "#117a65", "Circular orbit");
      burns.push({ pos: apoPos, dir: Lab.tangent(Math.PI, d.insertion.dv >= 0 ? "prograde" : "retrograde") });
      coast(Lab.ellipseSamples(d.insertion.rp, d.insertion.ra, nuIns, apoNu, 80), 6, "ell", "Coast to apoapsis");
      hold(apoPos, 2.8, 0, {
        rp0: d.insertion.rp, ra0: d.insertion.ra, i0: 0,
        rp1: d.insertion.r_circ, ra1: d.insertion.r_circ, i1: 0,
        color1: "#117a65", hide: "ell", hide2: "circ"
      }, "Burn, circularize");
      coast(Lab.ellipseSamples(d.insertion.r_circ, d.insertion.r_circ, Math.PI, Math.PI + 1.8, 36), 4, "circ", "Coast, circular orbit");
      if (d.insertion.atmosphere) legend.push({ label: "Periapsis is inside the atmosphere", color: "#922b21" });
    }
  } else if (mode === "launch") {
    var lat = Number(seed.launch_lat);
    var az = Number(seed.launch_az);
    var flight = Lab.launchGeometry(lat, az, Lab.AE_WGS84 + Number(seed.launch_alt || 400000));
    layer("orb", flight.orbit, "#1a5276", "Launch orbit");
    hold(flight.pad, 1, -1, null, "On the pad");
    coast(flight.ascent, 3.2, "orb", "Ascent");
    coast(flight.orbit, 10, "orb", "Coast, orbit");
  }
  if (burns.length) legend.push({ label: "Burn", color: "#c0392b" });
  legend.push({ label: "Satellite", color: "#e67e22", icon: "dot" });
  return pack();
};

Lab.mapFor = function (mode, result, seed, fraction) {
  var d = result._detail;
  if (mode === "ground" || mode === "coverage") {
    var a = mode === "coverage" ? Lab.R0_EARTH + d.covAlt : d.gtA;
    var e = mode === "coverage" ? 0 : d.gtE;
    var inc = mode === "coverage" ? Number(seed.cov_i || 0.9) : d.gtI;
    var period = Lab.orbitalPeriod(result.mu, a);
    var orbitsN = mode === "coverage"
      ? Math.max(1, Math.min(24, Number(seed.cov_orbits || d.cov.revisit_periods || 1)))
      : Number(seed.gt_orbits || 2);
    var mean0 = mode === "coverage" ? 0 : d.gtMean;
    var track = Lab.groundTrack(result.mu, a, e, inc, Number(seed.gt_raan || 0), Number(seed.gt_arg || 0), mean0, period * orbitsN, 40 * orbitsN, 0, Lab.J2_GSFC, Lab.AE_WGS84);
    return { kind: mode === "coverage" ? "coverage" : "ground", track: track, lambda: d.cov.lambda, fraction: fraction };
  }
  if (mode === "launch") {
    var latL = Number(seed.launch_lat);
    var azL = Number(seed.launch_az);
    var flight = Lab.launchGeometry(latL, azL, Lab.AE_WGS84 + Number(seed.launch_alt || 400000));
    return { kind: "launch", track: flight.track, site: { lat: latL, lon: 0 }, fraction: 1 };
  }
  return null;
};

Lab.exportText = function (result, seed) {
  var lines = [
    "python \"skills/ASTRO - VacuumPropellantMass/vacuum_propellant_mass.py\" \\",
    "  --dry " + Number(seed.dry || 0)
  ];
  if (seed.ve) lines.push("  --ve " + Number(seed.ve));
  else lines.push("  --isp " + Number(seed.isp || 0));
  if (Number(seed.growth)) lines.push("  --growth " + Number(seed.growth));
  var i;
  for (i = 0; i < result.pieces.length; i += 1) {
    lines.push("  --name " + result.pieces[i].name + " --dv " + result.pieces[i].dv);
  }
  lines.push("");
  lines.push("# strategy " + result.strategy + "  hohmann " + result.hohmann_dv + " m/s  bielliptic " + result.bielliptic_dv + " m/s");
  lines.push("# LEO raise is the impulsive reference. Do not also count MultiBurnLeoRaise propellant.");
  if (result.m_propellant !== null) {
    lines.push("# preview m_propellant_kg " + result.m_propellant + "  m_wet_kg " + result.m_wet);
  }
  return lines.join("\n");
};

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", function () {
    var seed0 = JSON.parse(document.getElementById("seed-json").textContent);
    var pack = JSON.parse(document.getElementById("pack-json").textContent);
    var seed = JSON.parse(JSON.stringify(seed0));
    var mode = "transfer";
    var mapFraction = 1;
    var mapPlaying = false;
    var deg = 180 / Math.PI;
    function setv(id, value) {
      var el = document.getElementById(id);
      if (el) el.value = value;
    }
    var bodyR = seed.R0 || Lab.R0_EARTH;
    function km(radius) { return (Number(radius) - bodyR) / 1000; }
    setv("r1", km(seed.r1));
    setv("r2", km(seed.r2));
    setv("rb", km(seed.rb));
    document.getElementById("strategy").value = seed.strategy || "auto";
    setv("plane-a", km(seed.plane_a));
    setv("plane-i", seed.plane_i * deg);
    setv("plane-di", seed.plane_di * deg);
    setv("geo-di", seed.geo_di * deg);
    setv("geo-e", seed.geo_e);
    setv("geo-burns", seed.geo_burns);
    setv("geo-years", seed.geo_years);
    setv("cw-x", seed.cw_x);
    setv("cw-z", seed.cw_z);
    setv("cw-xd", seed.cw_xd);
    setv("cw-zd", seed.cw_zd);
    setv("cw-time", seed.cw_time);
    setv("cw-a", km(seed.cw_a));
    document.getElementById("cw-piece").value = seed.cw_piece || "cw_null";
    setv("phase", seed.phase * deg);
    setv("phase-revs", seed.phase_revs);
    setv("phase-r", km(seed.phase_r));
    document.getElementById("phase-lead").value = seed.phase_lead;
    setv("lam-h1", km(Math.hypot(seed.lam_r1x, seed.lam_r1y, seed.lam_r1z)));
    setv("lam-h2", km(Math.hypot(seed.lam_r2x, seed.lam_r2y, seed.lam_r2z)));
    setv("lam-ang", Math.atan2(seed.lam_r2y, seed.lam_r2x) * deg);
    setv("lam-tof", seed.lam_tof);
    document.getElementById("lam-way").value = seed.lam_way || "short";
    setv("raise-r1", km(seed.raise_r1));
    setv("raise-r2", km(seed.raise_r2));
    setv("raise-di", seed.raise_di * deg);
    setv("ins-r", km(seed.ins_r));
    setv("ins-v", seed.ins_v);
    setv("ins-gamma", seed.ins_gamma * deg);
    setv("el-a", km(seed.el_a));
    setv("el-e", seed.el_e);
    setv("el-i", seed.el_i * deg);
    setv("el-beta", seed.el_beta * deg);
    setv("gt-a", km(seed.gt_a));
    setv("gt-e", seed.gt_e);
    setv("gt-i", seed.gt_i * deg);
    setv("gt-orbits", seed.gt_orbits);
    setv("cov-alt", Number(seed.cov_alt) / 1000);
    setv("cov-elev", seed.cov_elev * deg);
    setv("cov-i", seed.cov_i * deg);
    setv("cov-orbits", seed.cov_orbits || 2);
    setv("j2-a", km(seed.j2_a));
    setv("j2-e", seed.j2_e);
    setv("j2-i", seed.j2_i * deg);
    setv("launch-lat", seed.launch_lat * deg);
    setv("launch-az", seed.launch_az * deg);
    setv("launch-alt", (seed.launch_alt || 400000) / 1000);
    setv("dry", seed.dry);
    setv("isp", seed.isp);
    setv("growth", seed.growth || 0);
    ["hohmann", "bielliptic", "plane", "geo", "phasing", "lambert", "cw", "drag", "raise", "insertion"].forEach(function (key) {
      var box = document.getElementById("bud-" + key);
      if (!box) return;
      if (!seed.budget) seed.budget = {};
      if (seed.budget[key] === undefined) {
        box.checked = key === "hohmann" || key === "bielliptic" ? false : false;
      } else box.checked = !!seed.budget[key];
    });

    function num(id) {
      var el = document.getElementById(id);
      if (!el || el.value === "") return null;
      return Number(el.value);
    }
    function readSeed() {
      function rad(id) { return bodyR + num(id) * 1000; }
      seed.r1 = rad("r1");
      seed.r2 = rad("r2");
      seed.rb = rad("rb");
      seed.strategy = document.getElementById("strategy").value;
      seed.alt = null;
      seed.ecc = null;
      seed.plane_a = rad("plane-a");
      seed.plane_di = num("plane-di") * Math.PI / 180.0;
      seed.plane_i = num("plane-i") * Math.PI / 180.0;
      seed.geo_di = num("geo-di") * Math.PI / 180.0;
      seed.geo_e = num("geo-e");
      seed.geo_burns = num("geo-burns");
      seed.geo_years = num("geo-years");
      seed.cw_x = num("cw-x");
      seed.cw_z = num("cw-z");
      seed.cw_xd = num("cw-xd");
      seed.cw_zd = num("cw-zd");
      seed.cw_time = num("cw-time");
      seed.cw_a = rad("cw-a");
      seed.cw_piece = document.getElementById("cw-piece").value;
      seed.phase = num("phase") * Math.PI / 180.0;
      seed.phase_lead = document.getElementById("phase-lead").value;
      seed.phase_revs = num("phase-revs");
      seed.phase_r = rad("phase-r");
      var departR = rad("lam-h1");
      var arriveR = rad("lam-h2");
      var chord = num("lam-ang") * Math.PI / 180.0;
      seed.lam_r1x = departR;
      seed.lam_r1y = 0;
      seed.lam_r1z = 0;
      seed.lam_r2x = arriveR * Math.cos(chord);
      seed.lam_r2y = arriveR * Math.sin(chord);
      seed.lam_r2z = 0;
      seed.lam_tof = num("lam-tof");
      seed.lam_way = document.getElementById("lam-way").value;
      seed.raise_r1 = rad("raise-r1");
      seed.raise_r2 = rad("raise-r2");
      seed.raise_di = num("raise-di") * Math.PI / 180.0;
      seed.ins_r = rad("ins-r");
      seed.ins_v = num("ins-v");
      seed.ins_gamma = num("ins-gamma") * Math.PI / 180.0;
      seed.el_a = rad("el-a");
      seed.el_e = num("el-e");
      seed.el_i = num("el-i") * Math.PI / 180.0;
      seed.el_beta = num("el-beta") * Math.PI / 180.0;
      seed.gt_a = rad("gt-a");
      seed.gt_e = num("gt-e");
      seed.gt_i = num("gt-i") * Math.PI / 180.0;
      seed.gt_orbits = num("gt-orbits");
      seed.cov_alt = num("cov-alt") * 1000;
      seed.cov_elev = num("cov-elev") * Math.PI / 180.0;
      seed.cov_i = num("cov-i") * Math.PI / 180.0;
      seed.cov_orbits = Math.max(1, num("cov-orbits") || 1);
      seed.j2_a = rad("j2-a");
      seed.j2_e = num("j2-e");
      seed.j2_i = num("j2-i") * Math.PI / 180.0;
      seed.launch_lat = num("launch-lat") * Math.PI / 180.0;
      seed.launch_az = num("launch-az") * Math.PI / 180.0;
      seed.launch_alt = num("launch-alt") * 1000;
      seed.dry = num("dry");
      seed.isp = num("isp");
      seed.growth = num("growth");
      ["hohmann", "bielliptic", "plane", "geo", "phasing", "lambert", "cw", "raise", "insertion"].forEach(function (key) {
        var box = document.getElementById("bud-" + key);
        if (box) seed.budget[key] = box.checked;
      });
    }

    function fmt(value) {
      if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
      if (typeof value === "number") return value.toPrecision(6);
      return String(value);
    }

    function showPanels() {
      var panels = document.querySelectorAll("[data-panel]");
      var i;
      for (i = 0; i < panels.length; i += 1) {
        panels[i].hidden = panels[i].getAttribute("data-panel") !== mode;
      }
      var mapWrap = document.getElementById("map-wrap");
      mapWrap.hidden = !(mode === "ground" || mode === "coverage" || mode === "launch");
      document.getElementById("stage").style.gridTemplateColumns = mapWrap.hidden ? "1fr" : "1.3fr 0.9fr";
    }

    function refresh() {
      readSeed();
      var result;
      var status = document.getElementById("status");
      try {
        result = Lab.compute(seed, pack);
      } catch (err) {
        status.textContent = err.message || String(err);
        return;
      }
      var lambertNote = "";
      if (mode === "lambert") {
        var cleared = Lab.lambertOutside(
          result._detail.lamR1, result._detail.lamR2, Number(seed.lam_tof), result.mu, seed.lam_way || "short", result.r0
        );
        if (cleared.raised) {
          seed.lam_tof = cleared.tof;
          var tofBox = document.getElementById("lam-tof");
          if (tofBox) tofBox.value = String(Math.round(cleared.tof));
          result = Lab.compute(seed, pack);
          lambertNote = " The flight time was lengthened so the long arc stays outside the planet.";
        }
      }
      status.textContent = {
        transfer: "Heights are above the surface. The globe compares Hohmann and bielliptic.",
        plane: "Plane change tilts the circular orbit at the node.",
        geo: "Geostationary station-keeping: north-south and east-west trim impulses.",
        cw: "Relative motion of a deputy about a chief. The deputy path is magnified.",
        phasing: "Phasing closes an angle with a target on this same circular orbit.",
        lambert: "Lambert joins the two heights. Long stays outside the planet.",
        raise: "LEO raise is an impulsive Hohmann plus a plane-change impulse. Gravity loss is left at 0.",
        insertion: "Circularization from the burnout state.",
        elements: "Eclipse fraction for this orbit.",
        ground: "Subsatellite track on the latitude-longitude map.",
        coverage: "The corridor is the elevation-mask swath along the ground track.",
        j2: "Node and apsidal drift from J2. The gold orbit is the node after the labeled interval.",
        launch: "The satellite waits on the pad, then flies the orbit set by latitude and azimuth."
      }[mode] || "Drag the globe.";
      if (lambertNote) status.textContent += lambertNote;
      var rows = [];
      function add(name, value) { rows.push([name, value]); }
      var budgetLine = fmt(result.dv_total) + " m/s";
      var propLine = result.m_propellant === null ? "n/a" : fmt(result.m_propellant) + " kg";
      if (mode === "transfer") {
        add("Strategy", result.strategy);
        add("Hohmann Δv", fmt(result.hohmann_dv) + " m/s");
        add("Bielliptic Δv", fmt(result.bielliptic_dv) + " m/s");
        add("Hohmann TOF", fmt(result.hohmann_tof) + " s");
        add("Bielliptic TOF", fmt(result.bielliptic_tof) + " s");
        add("Recommend", result.bielliptic_recommendation);
        add("Budget Δv", budgetLine);
        add("Propellant", propLine);
      } else if (mode === "plane") {
        add("Plane-change Δv", fmt(result.plane_dv) + " m/s");
      } else if (mode === "geo") {
        add("North-south", fmt(result.geo_ns) + " m/s");
        add("East-west", fmt(result.geo_ew) + " m/s");
        add("Year total", fmt(result.geo_total) + " m/s");
      } else if (mode === "cw") {
        add("Null Δv", fmt(result.cw_null) + " m/s");
        add("Hold Δv", fmt(result.cw_hold) + " m/s");
        add("Along-track x", fmt(result.cw_x) + " m");
        add("Radial z", fmt(result.cw_z) + " m");
      } else if (mode === "phasing") {
        add("Phasing Δv", fmt(result.phase_dv) + " m/s");
      } else if (mode === "lambert") {
        add("Depart Δv", fmt(result.lambert_dv1) + " m/s");
        add("Arrive Δv", fmt(result.lambert_dv2) + " m/s");
      } else if (mode === "raise") {
        add("Raise Δv", fmt(result.raise_dv) + " m/s");
        add("Plane-change share", fmt(result.raise_plane) + " m/s");
      } else if (mode === "insertion") {
        add("Circularization Δv", fmt(result.insertion_dv) + " m/s");
        add("Where", result.insertion_where);
      } else if (mode === "elements") {
        add("Eclipse fraction", fmt(result.eclipse_fraction));
      } else if (mode === "coverage") {
        add("Swath", fmt(result.coverage_swath / 1000) + " km");
        add("Revisit orbits", String(result.coverage_revisit));
        add("Orbits drawn", String(seed.cov_orbits || result.coverage_revisit));
      } else if (mode === "j2") {
        add("Node", fmt(result._detail.j2.node_deg_day) + " deg/day");
        add("Apsis", fmt(result._detail.j2.apsis_deg_day) + " deg/day");
      } else if (mode === "launch") {
        add("Inclination", fmt(result.launch_inc * 180 / Math.PI) + " deg");
        add("Rotational assist", fmt(result.launch_assist) + " m/s");
      } else if (mode === "ground") {
        add("Latitude at T/4", fmt(result.gt_lat * 180 / Math.PI) + " deg");
        add("Longitude at T/4", fmt(result.gt_lon * 180 / Math.PI) + " deg");
      }
      var dl = document.getElementById("readout");
      dl.innerHTML = rows.map(function (row) {
        return "<div><dt>" + row[0] + "</dt><dd>" + row[1] + "</dd></div>";
      }).join("");
      document.getElementById("export").value = Lab.exportText(result, seed);
      Lab.Globe.show(Lab.sceneFor(mode, result, seed));
      var mapSpec = Lab.mapFor(mode, result, seed, mapFraction);
      var canvas = document.getElementById("map");
      if (mapSpec) Lab.Map2d.draw(canvas, mapSpec);
      window.__orbitResult = result;
    }

    document.getElementById("tabs").addEventListener("click", function (event) {
      var button = event.target.closest("button[data-mode]");
      if (!button) return;
      mode = button.getAttribute("data-mode");
      var buttons = document.querySelectorAll("#tabs button");
      var i;
      for (i = 0; i < buttons.length; i += 1) buttons[i].classList.toggle("on", buttons[i] === button);
      showPanels();
      refresh();
    });
    document.getElementById("play").addEventListener("click", function () {
      Lab.Globe.playing = !Lab.Globe.playing;
      this.textContent = Lab.Globe.playing ? "Pause" : "Play";
    });
    document.getElementById("reset-cam").addEventListener("click", function () {
      Lab.Globe.elev = 0.55;
      Lab.Globe.azim = -0.9;
      Lab.Globe.radius = 8;
      Lab.Globe.clock = 0;
      Lab.Globe._aim();
    });
    document.getElementById("trace").addEventListener("click", function () {
      mapPlaying = !mapPlaying;
      this.textContent = mapPlaying ? "Pause trace" : "Play trace";
    });

    var inputs = document.querySelectorAll("input, select");
    var n;
    for (n = 0; n < inputs.length; n += 1) {
      inputs[n].addEventListener("input", refresh);
      inputs[n].addEventListener("change", refresh);
    }

    Lab.Globe.init(document.getElementById("globe"));
    showPanels();
    refresh();
    setInterval(function () {
      if (!mapPlaying || mode !== "coverage") return;
      mapFraction = mapFraction >= 1 ? 0.08 : Math.min(1, mapFraction + 0.04);
      refresh();
    }, 180);
  });
}
