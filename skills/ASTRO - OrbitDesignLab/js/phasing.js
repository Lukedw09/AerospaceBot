/* Coplanar phasing. Keep in step with ASTRO - RendezvousPhasing. */
var Lab = Lab || {};

Lab.phasing = function (radius, phase, lead, revs, mu) {
  if (!(radius > 0.0) || !(phase > 0.0) || !(mu > 0.0)) throw new Error("radius, phase, and mu must be > 0");
  if (revs < 1) throw new Error("revs must be >= 1");
  var who = String(lead).toLowerCase();
  if (who !== "target" && who !== "chaser") throw new Error("lead must be target or chaser");
  if (phase >= 2.0 * Math.PI * revs) throw new Error("phase angle must be smaller than 2*pi*revs");
  var motion = Lab.meanMotion(mu, radius);
  var wait = who === "target"
    ? (2.0 * Math.PI * revs - phase) / motion
    : (2.0 * Math.PI * revs + phase) / motion;
  var period = wait / revs;
  var semimajor = Math.pow(mu * Math.pow(period / (2.0 * Math.PI), 2), 1.0 / 3.0);
  var other = 2.0 * semimajor - radius;
  if (other <= 0.0) throw new Error("phasing periapsis is not positive");
  var periapsis = semimajor < radius ? other : radius;
  var apoapsis = semimajor < radius ? radius : other;
  var vc = Lab.circularSpeed(mu, radius);
  var ve = Lab.visViva(mu, radius, semimajor);
  var one = Math.abs(vc - ve);
  return {
    lead: who,
    a: semimajor,
    wait: wait,
    period: period,
    rp: periapsis,
    ra: apoapsis,
    dv_in: one,
    dv_out: one,
    dv_total: 2.0 * one
  };
};
